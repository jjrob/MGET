# R/_RWorkerProcess.py - Defines RWorkerProcess, a class that starts R as a
# child process and facilitates interaction with it over HTTP with plumber.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import base64
import collections.abc
import ctypes
import datetime
import functools
import io
import json
import logging
import math
import os
import queue
import random
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import zoneinfo

from ..Dependencies import SoftwareNotInstalledError
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger
from ..Types import DateTimeTypeMetadata, FloatTypeMetadata


# The R plumber package uses jsonlite for deserialization. jsonlite will
# deserialize datetimes in "mongo" format, e.g. '{"$date": 1393193680926}',
# to R POSIXct objects (see https://github.com/jeroen/jsonlite/issues/8).
# Here, we define our own Python json.JSONEncoder that formats Python
# datetimes in "mongo" format.

class _CustomJSONEncoder(json.JSONEncoder):

    def __init__(self, *args, default_tzinfo=datetime.timezone.utc, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_tzinfo = default_tzinfo 

    def default(self, obj):

        # If it's a datetime, convert to milliseconds since the UNIX epoch (in
        # UTC) and return a dict with a '$date' key, which is "mongo" format
        # according to the R jsonlite package.

        if isinstance(obj, datetime.datetime):
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=self.default_tzinfo)
            millis = int(obj.timestamp() * 1000)
            return {'$date': millis}

        # Otherwise, just use the JSONEncoder default.

        return super().default(obj)

    # Also define a custom iterencode, based on Python's, but that encodes
    # NaN, Inf, and -Inf as "NaN", "Inf", "-Inf" (including the doublequotes),
    # which are recognized by R's jsonlite package.

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = json.encoder.encode_basestring_ascii
        else:
            _encoder = json.encoder.encode_basestring

        def floatstr(o, allow_nan=self.allow_nan,
                _repr=float.__repr__, _inf=float('inf'), _neginf=-float('inf')):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = '"NaN"'
            elif o == _inf:
                text = '"Inf"'
            elif o == _neginf:
                text = '"-Inf"'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        _iterencode = json.encoder._make_iterencode(
            markers, self.default, _encoder, self.indent, floatstr,
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)
        return _iterencode(o, 0)


class _MongoDateTimeDecoder(json.JSONDecoder):
    def __init__(self, *args, default_tzinfo=datetime.timezone.utc, **kwargs):
        if 'object_hook' not in kwargs or kwargs['object_hook'] is None:
            kwargs['object_hook'] = self._DecodeMongoDates
        super().__init__(*args, **kwargs)
        self.default_tzinfo = default_tzinfo
        self.parse_array = self._UnboxMongoDates
        self.scan_once = json.scanner.py_make_scanner(self)

    # Times are serialized by R in "mongo" format, which is a dict with a
    # single $date key and POSIX time value (in UTC) that includes
    # milliseconds, e.g. {'$date': 1738270573145}. If we find a dictionary
    # that looks like that, convert it to a datetime.datetime instance (in
    # the requested time zone).

    def _DecodeMongoDates(self, obj):
        if len(obj) == 1 and '$date' in obj and isinstance(obj['$date'], (int, float)):
            return datetime.datetime.fromtimestamp(obj['$date'] / 1000., tz=self.default_tzinfo)
        return obj

    # Unfortunately, R plumber does not automatically unbox a length 1 POSIXct
    # vector that have been serialized as mongo dates. dates. E.g.,
    # c(Sys.time()) is serialized to JSON as [{'$date': 1738270573145}].
    # However, POSIXct vectors of length 2 or more do not wrap each mongo date
    # in a list. E.g., c(Sys.time(), Sys.time()) is serialized to JSON as
    # [{'$date': 1738270573145}, {'$date': 1738270573145}]. So, after decoding,
    # if we find a list with a single datetime instance in it, just return the
    # datetime instance.

    def _UnboxMongoDates(self, s, idx):
        result, end = json.decoder.JSONArray(s, idx)
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], datetime.datetime):
            return result[0], end
        return result, end


class RWorkerProcess(collections.abc.MutableMapping):
    __doc__ = DynamicDocString()

    def __init__(self, rInstallDir=None, rLibDir=None, rRepository='https://cloud.r-project.org', rPackages=None, updateRPackages=False, port=None, timeout=5., startupTimeout=15., defaultTZ=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        self._RInstallDir = rInstallDir
        self._RLibDir = rLibDir
        self._RRepository = rRepository
        self._RPackages = rPackages
        self._UpdateRPackages = updateRPackages
        self._RequestedPort = port
        self._Port = None
        self._Timeout = timeout
        self._StartupTimeout = startupTimeout
        self._WorkerProcess = None
        self._Session = None
        self._Lock = threading.RLock()
        self._MainThreadQueue = None
        self._StdoutThread = None
        self._StderrThread = None
        self._HTTPThread = None
        self._HTTPThreadQueue = None
        self._RLogger = logging.getLogger('GeoEco.R')
        self._LogWaitLoop = False

        if defaultTZ is None:
            import tzlocal
            self._TZInfo = tzlocal.get_localzone()
        else:
            self._TZInfo = zoneinfo.ZoneInfo(defaultTZ)

        self._AuthenticationToken = base64.b64encode(secrets.token_bytes(64), b'+-').decode('utf-8')

    def Start(self):
        import requests

        with self._Lock:
            if self._WorkerProcess is not None:
                return
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Start() called.')

            # On Linux, the R plumber package requires libsodium. Check that
            # it is installed.

            if sys.platform == 'linux':
                try:
                    ctypes.CDLL("libsodium.so")
                except Exception as e:
                    raise SoftwareNotInstalledError(_('MGET interacts with R using the R plumber package, which requires libsodium, which is not installed. On Debian-based systems such as Ubuntu, you can probably install it with "sudo apt-get install libsodium-dev". Error details: %(error)s: %(msg)s') % {'error': e.__class__.__name__, 'msg': e})

            # Sometimes the plumber HTTP server does not respond to the first
            # connection request. Configure a requests.Session to issue five
            # retries, with the first coming after 250 ms. Only retry on
            # connection failures, not HTTP status codes that represent
            # failures. When those occur, we want to raise exceptions to
            # notify the caller.

            from requests.adapters import HTTPAdapter
            from requests.packages.urllib3.util.retry import Retry

            session = requests.Session()
            session.mount('http://', HTTPAdapter(max_retries=Retry(total=5, backoff_factor=0.5)))
            self._Session = session

            try:
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Opened requests.Session 0x{id(self._Session):016X}.')

                # Locate the Rscript executable.

                if sys.platform == 'win32':
                    rscriptPath = self._LocateRscriptOnWin32()
                elif sys.platform == 'linux':
                    rscriptPath = self._LocateRscriptOnLinux()
                else:
                    raise NotImplementedError(_('RWorkerProcess is only supported on the "%(plat)s" platform, only on win32 and linux.') % {'plat': sys.platform})

                # Unfortunately, there is no way to have plumber itself find a free
                # TCP port to use. So we find one here, unless the caller
                # specified one. Note that this creates a small race condition in
                # which some other process could grab the free port before we can
                # start plumber. We do not handle that case, and leave it to the
                # caller to try again.

                if self._RequestedPort is None:
                    for i in range(1000):
                        port = random.randint(1024, 49151)   # R or plumber only supports listening to ports in this range, even if the operation system is willing to issue a port higher than 49151; see https://en.wikipedia.org/wiki/Registered_port 
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            try:
                                s.bind(('127.0.0.1', port))
                            except OSError:
                                port = None
                                continue
                            else:
                                break
                    if port is None:
                        raise RuntimeError(_('Could not find an available TCP port for Python/R communication. Please try this operation again. If it continues to fail, please contact the MGET development team for assistance.'))
                    self._Port = port

                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Using TCP port {self._Port}.')

                # Create the args we will pass to subprocess.Popen.

                args = [rscriptPath,
                        '--vanilla',
                        os.path.join(os.path.dirname(__file__), 'RunPlumber.R'),
                        str(self._Port),
                        os.path.join(os.path.dirname(__file__), 'PlumberAPI.R'),
                        str(self._RLibDir),
                        str(self._RRepository),
                        'None' if self._RPackages is None or len(self._RPackages) <= 0 else ','.join(self._RPackages),
                        str(self._UpdateRPackages),
                        self._AuthenticationToken]

                # Start Rscript with subprocess.Popen. Exactly how do do this is
                # platform-specific.

                if sys.platform == 'win32':
                    rscriptPath = self._StartProcessOnWin32(args)
                elif sys.platform == 'linux':
                    rscriptPath = self._StartProcessOnLinux(args)
                else:
                    raise NotImplementedError(_('RWorkerProcess is only supported on the "%(plat)s" platform, only on win32 and linux.') % {'plat': sys.platform})

                # Allocate self._MainThreadQueue, which we will use to receive
                # messages from the threads we start below, and
                # self._HTTPThreadQueue, which we will use to send messages
                # to the HTTP thread that places HTTP requets.

                self._MainThreadQueue = queue.SimpleQueue()
                self._HTTPThreadQueue = queue.SimpleQueue()

                # Start the threads that monitor the stdout and stderr streams
                # of the child process and post lines of output back to the
                # main thread.

                self._StdoutThread = threading.Thread(target=RWorkerProcess._StreamThreadEntryPoint, args=(self._WorkerProcess.stdout, 'StdoutThread', self._MainThreadQueue), daemon=True)
                self._StderrThread = threading.Thread(target=RWorkerProcess._StreamThreadEntryPoint, args=(self._WorkerProcess.stderr, 'StderrThread', self._MainThreadQueue), daemon=True)
                self._StdoutThread.start()
                self._StderrThread.start()

                # Start the HTTP thread.

                self._HTTPThread = threading.Thread(target=RWorkerProcess._HTTPThreadEntryPoint, args=(self._Session, self._HTTPThreadQueue, self._MainThreadQueue), daemon=True)
                self._HTTPThread.start()

                # Process messages we receive on self._MainThreadQueue,
                # waiting for R plumber to write a line to stdout saying that
                # it has started. 

                waitingStarted = datetime.datetime.now()
                installingRPackages = False

                while True:
                    elapsed = (datetime.datetime.now() - waitingStarted).total_seconds()
                    timeout = None if installingRPackages else max(0.1, self._StartupTimeout - elapsed)
                    try:
                        msg = self._MainThreadQueue.get(timeout=timeout)
                    except queue.Empty:
                        raise RuntimeError(_('%(startupTimeout)s seconds have elapsed after starting MGET\'s R worker process without the process indicating it is ready. Please check preceding log messages to determine if there is a problem with R. If not, consider increasing the Startup Timeout to allow R more time to initialize.') % {'startupTimeout': self._StartupTimeout})

                    if msg[1] == 'started':
                        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: {msg[0]} started.')

                    elif msg[1] == 'exited':
                        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: {msg[0]} exited.')   # This should not happen under normal operation

                    elif msg[0] in ['StdoutThread', 'StderrThread']:
                        assert msg[1] == 'log'
                        if msg[2].startswith('INSTALLING_R_PACKAGES'):
                            installingRPackages = True

                        elif msg[2].startswith('DONE_INSTALLING_R_PACKAGES'):
                            installingRPackages = False
                            waitingStarted = datetime.datetime.now()   # Restart the wait now that packages have been installed

                        elif msg[2].startswith('Running plumber API at'):
                            break   # R plumber is ready

                        elif msg[2].startswith('Running swagger Docs at'):
                            pass    # This usually is reported after "Running plumber API at", but swallow it here if we get it first

                        elif msg[2].startswith('DEBUG:'):
                            self._RLogger.debug(msg[2][6:])

                        elif msg[0] == 'StdoutThread':
                            self._RLogger.info(msg[2])

                        else:
                            self._RLogger.warning(msg[2])

            # If we raised an exception after allocating the session, close
            # the various objects that were opened.

            except:
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: An exception was raised during one of the steps of starting the Rscript worker process.')

                if self._WorkerProcess is not None:
                    Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: The worker process was actually started but a subsequent step did not complete successfully. Killing the worker process.')
                    try:
                        self._WorkerProcess.kill()
                    except Exception as e:
                        Logger.Warning(_('MGET\'s Rscript worker process was started successfully (PID = %(pid)s), but a subsequent problem occurred. We tried to stop worker process but that failed. The process may still be running and need to be stopped manually. The error we encountered stopping the process was: %(error)s: %(msg)s') % {'pid': self._WorkerProcess.pid, 'error': e.__class__.__name__, 'msg': e})
                    else:
                        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Stopped the worker process.')
                    self._WorkerProcess = None

                if self._HTTPThread is not None:
                    if self._HTTPThread.is_alive():
                        try:
                            self._HTTPThreadQueue.put(('stop',), timeout=1)
                            self._HTTPThread.join(timeout=1)
                        except:
                            pass
                    self._HTTPThread = None

                if self._StdoutThread is not None:
                    if self._StdoutThread.is_alive():
                        try:
                            self._StdoutThread.join(timeout=1)
                        except:
                            pass
                    self._StdoutThread = None

                if self._StderrThread is not None:
                    if self._StderrThread.is_alive():
                        try:
                            self._StderrThread.join(timeout=1)
                        except:
                            pass
                    self._StderrThread = None

                self._MainThreadQueue = None
                self._HTTPThreadQueue = None

                try:
                    self._Session.close()
                except:
                    pass
                self._Session = None
                raise

        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: R plumber reported that it is ready.')

        # On Linux, it seems that if we now immediately issue a request to
        # plumber, it usually fails with "connection refused" for the first
        # two attempts and then succeeds. This is ok, except that requests or
        # httplib3 logs warnings. To try to avoid this, sleep for 100 ms to
        # allow plumber to become truly ready.

        if sys.platform == 'linux':
            time.sleep(0.1)

    def _LocateRscriptOnWin32(self):

        # Locate the Rscript.exe excutable. First, if self._RInstallDir was
        # provided by the caller, try it.

        rscriptPath = None

        if self._RInstallDir is not None:
            rscriptPath = os.path.join(self._RInstallDir, 'bin', 'x64', 'Rscript.exe')
            if not os.path.isfile(rscriptPath):
                raise FileNotFoundError(_('The R installation directory "%(rInstallDir)s" was provided but the file "%(rscriptPath)s" does not exist.') % {'rInstallDir': self._RInstallDir, 'rscriptPath': rscriptPath})
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Found path to {rscriptPath} in the rInstallDir provided by the caller.')

        # Otherwise, check for the R_HOME environment variable.

        elif os.getenv('R_HOME', None) is not None and len(os.getenv('R_HOME').strip()) > 0:
            rscriptPath = os.path.join(os.getenv('R_HOME').strip(), 'bin', 'x64', 'Rscript.exe')
            if not os.path.isfile(rscriptPath):
                raise FileNotFoundError(_('The R_HOME environment variable was set to "%(R_HOME)s" but the file "%(rscriptPath)s" does not exist.') % {'R_HOME': os.getenv('R_HOME').strip(), 'rscriptPath': rscriptPath})
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Found path to {rscriptPath} via the R_HOME environment variable.')

        # Otherwise, check the registry.

        else:
            import winreg
            for hkey, hkeyName in [[winreg.HKEY_CURRENT_USER, 'HKEY_CURRENT_USER'], [winreg.HKEY_LOCAL_MACHINE, 'HKEY_LOCAL_MACHINE']]:
                try:
                    key = winreg.OpenKey(hkey, r'SOFTWARE\R-Core\R64')
                except FileNotFoundError:
                    continue
                except Exception as e:
                    Logger.Warning(_('Failed to open the Windows Registry key %(hkeyName)s\\SOFTWARE\\R-Core\\R64. As a consequence, the R installation directory cannot be obtained from this key. Detailed error information: %(e)s: %(msg)s.') % {'hkeyName': hkeyName, 'e': e.__class__.__name__, 'msg': e})
                    continue
                try:
                    try:
                        installPath, valueType = winreg.QueryValueEx(key, 'InstallPath')
                    except FileNotFoundError:
                        continue
                    except Exception as e:
                        Logger.Warning(_('Failed to query the value of InstallPath in the Windows Registry key %(hkeyName)s\\SOFTWARE\\R-Core\\R64. As a consequence, the R installation directory cannot be obtained from this key. Detailed error information: %(e)s: %(msg)s.') % {'hkeyName': hkeyName, 'e': e.__class__.__name__, 'msg': e})
                        continue
                finally:
                    winreg.CloseKey(key)

                rscriptPath = os.path.join(installPath, 'bin', 'x64', 'Rscript.exe')
                if os.path.isfile(rscriptPath):
                    Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Found path to {rscriptPath} via the {hkeyName}\\SOFTWARE\\R-Core\\R64 registry key.')
                    break

                rscriptPath = None
                Logger.Warning(_('Failed to find the file bin\\x64\\Rscript.exe in the InstallDir given by Windows Registry key %(hkeyName)s\\SOFTWARE\\R-Core\\R64. That version of R may no longer be installed.') % {'hkeyName': hkeyName})

        # If we still haven't found it, check the PATH.

        if rscriptPath is None:
            rscriptPath = shutil.which('Rscript.exe')
            if rscriptPath is None:
                raise SoftwareNotInstalledError(_('Failed to find the program Rscript.exe via the the Windows Registry or R_HOME or PATH environment variables. Is R installed?'))
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Found path to {rscriptPath} via the PATH environment variable.')

        return rscriptPath

    def _StartProcessOnWin32(self, args):

        # After the child process is started (below), until we signal it to
        # stop and it exits of its own accord. But if this never happens, by
        # default it will keep running, even if the parent process exits. We
        # do not want to do this; we want the child to be terminated if the
        # parent exits. To accomplish this, we add the child process to a
        # win32 Job object with the JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE flag
        # set, so that when the parent (us) releases the job's handle
        # automatically when the parent exits, the child will be terminated.
        # Thanks to the author of https://stackoverflow.com/a/16791778 for
        # the example code working with Job objects.
        #
        # First check whether the current process is already in a job.

        kernel32 = ctypes.windll.kernel32
        import _winapi

        isInJob = ctypes.c_bool()
        success = kernel32.IsProcessInJob(ctypes.c_void_p(kernel32.GetCurrentProcess()),
                                          ctypes.c_void_p(0),   # Use NULL to check whether the process is running under any job
                                          ctypes.POINTER(ctypes.c_bool)(isInJob))
        if success == 0:
            raise RuntimeError(_('Failed to determine if the current process is within a Win32 Job: ctypes.windll.kernel32.IsProcessInJob() failed with error 0x%(error)08X.') % {'error': _winapi.GetLastError()})
        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: The current process {"is" if isInJob else "is not"} already in a Win32 job.')

        # If it is already in a job, query it to determine if
        # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE is set. If so, then we don't
        # need to do anything, because our parent process has already
        # configured things the way we want.

        needToCreateJob = True
        JobObjectBasicLimitInformation = 2
        JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64),
                        ('PerJobUserTimeLimit', ctypes.c_int64),
                        ('LimitFlags', ctypes.c_uint32),
                        ('MinimumWorkingSetSize', ctypes.c_void_p),
                        ('MaximumWorkingSetSize', ctypes.c_void_p),
                        ('ActiveProcessLimit', ctypes.c_uint32),
                        ('Affinity', ctypes.c_void_p),
                        ('PriorityClass', ctypes.c_uint32),
                        ('SchedulingClass', ctypes.c_uint32)]

        if isInJob:
            jobInfo = JOBOBJECT_BASIC_LIMIT_INFORMATION()
            outSize = ctypes.c_uint32()

            success = kernel32.QueryInformationJobObject(ctypes.c_void_p(0),    # Use NULL to query the job associated with the current process
                                                         JobObjectBasicLimitInformation,
                                                         ctypes.POINTER(JOBOBJECT_BASIC_LIMIT_INFORMATION)(jobInfo),
                                                         ctypes.sizeof(JOBOBJECT_BASIC_LIMIT_INFORMATION),
                                                         ctypes.POINTER(ctypes.c_uint32)(outSize))
            if success == 0:
                raise RuntimeError(_('Failed to query Win32 Job object for the current process: ctypes.windll.kernel32.QueryInformationJobObject() failed with error 0x%(error)08X.') % {'error': _winapi.GetLastError()})

            needToCreateJob = not(jobInfo.LimitFlags & JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: The current process\'s Win32 job {"does not have" if needToCreateJob else "already has"} JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE set.')

            # If JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE is not set, check whether
            # JOB_OBJECT_LIMIT_BREAKAWAY_OK is set. If it is not, it means
            # that we cannot create our own job to put the child process
            # into. In that case, report a warning, but do not try to create
            # a job. The R child process can still be started, but will not
            # be terminated automatically if we do not explicitly stop it
            # before our process exits.

            if needToCreateJob and not(jobInfo.LimitFlags & JOB_OBJECT_LIMIT_BREAKAWAY_OK):
                Logger.Warning(_('MGET was unable to instruct Windows to automatically terminate its Rscript worker process when MGET\'s process exits. MGET\'s process is already part of a Win32 job that does not allow child processes to be placed into a different job (JOB_OBJECT_LIMIT_BREAKAWAY_OK is FALSE). As a consequence, if MGET\'s process exits abnormally, the Rscript worker process may not be automatically terminated.'))
                needToCreateJob = False

        # If we determined above that we need to create a job for the child
        # process, do it and set JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE. Note:
        # for some reason, we have to use
        # JOBOBJECT_EXTENDED_LIMIT_INFORMATION when calling
        # SetInformationJobObject. I could not get it to work when I tried
        # JOBOBJECT_BASIC_LIMIT_INFORMATION.

        hJob = 0
        try:
            if needToCreateJob:
                JobObjectExtendedLimitInformation = 9

                class IO_COUNTERS(ctypes.Structure):
                    _fields_ = [('ReadOperationCount', ctypes.c_uint64),
                                ('WriteOperationCount', ctypes.c_uint64),
                                ('OtherOperationCount', ctypes.c_uint64),
                                ('ReadTransferCount', ctypes.c_uint64),
                                ('WriteTransferCount', ctypes.c_uint64),
                                ('OtherTransferCount', ctypes.c_uint64)]

                class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
                    _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                                ('IoInfo', IO_COUNTERS),
                                ('ProcessMemoryLimit', ctypes.c_void_p),
                                ('JobMemoryLimit', ctypes.c_void_p),
                                ('PeakProcessMemoryUsed', ctypes.c_void_p),
                                ('PeakJobMemoryUsed', ctypes.c_void_p)]

                jobInfo = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                outSize = ctypes.c_uint32()

                hJob = kernel32.CreateJobObjectW(None, None)
                if hJob == 0:
                    raise RuntimeError(_('Failed to create Win32 Job object: ctypes.windll.kernel32.CreateJobObjectW() failed with error 0x%(error)08X.') % {'error': _winapi.GetLastError()})

                success = kernel32.QueryInformationJobObject(hJob,
                                                             JobObjectExtendedLimitInformation,
                                                             ctypes.POINTER(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)(jobInfo),
                                                             ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION),
                                                             ctypes.POINTER(ctypes.c_uint32)(outSize))
                if success == 0:
                    raise RuntimeError(_('Failed to query newly-created Win32 Job object: ctypes.windll.kernel32.QueryInformationJobObject() failed with error 0x%(error)08X.') % {'error': _winapi.GetLastError()})

                jobInfo.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

                success = kernel32.SetInformationJobObject(hJob,
                                                           JobObjectExtendedLimitInformation,
                                                           ctypes.POINTER(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)(jobInfo),
                                                           ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION))
                if success == 0:
                    raise RuntimeError(_('Failed to set LimitFlags on Win32 Job object: ctypes.windll.kernel32.SetInformationJobObject() failed with error 0x%(error)08X.') % {'error': _winapi.GetLastError()})

                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Created Win32 Job object for the child Rscript process with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE set.')

            # Start the child process.

            startupInfo = subprocess.STARTUPINFO()
            startupInfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupInfo.wShowWindow = subprocess.SW_HIDE

            creationFlags = subprocess.CREATE_NO_WINDOW
            if needToCreateJob:
                creationFlags += subprocess.CREATE_BREAKAWAY_FROM_JOB

            argsStr = subprocess.list2cmdline(args)
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Starting worker process with creation flags 0x{creationFlags:08X}: {argsStr}')

            try:
                self._WorkerProcess = subprocess.Popen(args=args,
                                                       stdin=subprocess.DEVNULL,
                                                       stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE,
                                                       startupinfo=startupInfo,
                                                       creationflags=creationFlags,
                                                       encoding='utf-8',
                                                       text=True)
            except Exception as e:
                Logger.Error(_('MGET failed to start an Rscript worker process with creation flags 0x%(creationFlags)08X and the command line: %(argsStr)s') % {'creationFlags': creationFlags, 'argsStr': argsStr})
                raise

            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Worker process {self._WorkerProcess.pid} started.')

            # Assign the child process to the job object.

            if needToCreateJob:
                success = kernel32.AssignProcessToJobObject(hJob, self._WorkerProcess._handle)
                if success == 0:
                    raise RuntimeError(_('Failed to assign the worker process to a Win32 Job object: ctypes.windll.kernel32.AssignProcessToJobObject() failed with error 0x%(error)08X.') % {'error': _winapi.GetLastError()})

                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Assigned worker process {self._WorkerProcess.pid} to the Win32 Job object.')

        # If we got an exception and we created a job, close the job handle.
        # But if we did not, do NOT close the job handle. If we do, it will
        # end the job and kill the child process. Instead we allow Windows to
        # close it automatically when we exit. When that happens, if the
        # child process is still running, Windows will kill it.

        except:
            try:
                if hJob != 0:
                    kernel32.CloseHandle(hJob)
            except:
                pass
            raise

    def _LocateRscriptOnLinux(self):

        # On Linux, the R executables are expected to be available via the
        # PATH.

        rscriptPath = shutil.which('Rscript')
        if rscriptPath is None:
            raise SoftwareNotInstalledError(_('Failed to find the program Rscript. Is R installed and accessible through the PATH environment variable?'))
        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Found path to {rscriptPath} via the PATH environment variable.')

        return rscriptPath

    def _StartProcessOnLinux(self, args):

        # Define a subprocess preexec_fn that configures the child process to
        # be sent SIGKILL when the thread that created the child (i.e. the
        # thread right here that's about to call subprocess.Popen) exits. This
        # will help ensure the child process will exit if we exit without
        # explicitly stopping it.

        libc = ctypes.CDLL("libc.so.6")
        PR_SET_PDEATHSIG = 1  # Option to set signal on parent death
        SIGKILL = 9

        def setDeathSignal():
            libc.prctl(PR_SET_PDEATHSIG, SIGKILL)

        # Start the child process.

        argsStr = subprocess.list2cmdline(args)
        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Starting worker process: {argsStr}')

        try:
            self._WorkerProcess = subprocess.Popen(args=args,
                                                   stdin=subprocess.DEVNULL,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE,
                                                   preexec_fn=setDeathSignal,
                                                   encoding='utf-8',
                                                   text=True)
        except Exception as e:
            Logger.Error(_('MGET failed to start an Rscript worker process with the command line: %(argsStr)s') % {'argsStr': argsStr})
            raise

        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Worker process {self._WorkerProcess.pid} started.')

    @staticmethod
    def _StreamThreadEntryPoint(stream, threadName, outputQueue):
        outputQueue.put((threadName, 'started'))
        try:
            for line in iter(stream.readline, ''):
                outputQueue.put((threadName, 'log', line.rstrip()))
        finally:
            stream.close()
            outputQueue.put((threadName, 'exited'))

    @staticmethod
    def _HTTPThreadEntryPoint(session, inputQueue, outputQueue):
        outputQueue.put(('HTTPThread', 'started'))
        try:
            while True:
                msg = inputQueue.get()
                if msg[0] == 'stop':
                    return
                else:
                    assert msg[0] == 'request'
                    try:
                        response = getattr(session, msg[1])(**msg[2])
                    except Exception as e:
                        outputQueue.put(('HTTPThread', 'exception', e))
                    else:
                        outputQueue.put(('HTTPThread', 'response', response))
        finally:
            outputQueue.put(('HTTPThread', 'exited'))

    def _SendHTTPRequest(self, method, args):

        # Send the request to the HTTP thread.

        if self._LogWaitLoop:
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Issuing the request from the HTTPThread.')

        self._HTTPThreadQueue.put(('request', method, args), timeout=5)

        # Loop, processing outputs from the stream threads and the response
        # from the HTTP thread. Exit the loop when all three have signalled
        # they are done.

        if self._LogWaitLoop:
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Waiting for the HTTPThread and stdout and stderr of the child process all to be done.')

        httpThreadDone = False
        stdoutDone = False
        stderrDone = False
        response = None

        while not (httpThreadDone and stdoutDone and stderrDone):
            try:
                msg = self._MainThreadQueue.get(timeout=None if not httpThreadDone else 10.)
            except queue.Empty:
                raise RuntimeError(_('In RWorkerProcess, the MainThreadQueue timed out after 10 seconds, even though the HTTPThread was done. This is an unexpected error. Please contact the MGET development team for assistance.'))

            if msg[1] == 'started':
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: {msg[0]} started.')  # This should not happen under normal operation
                stdoutDone = True

            elif msg[1] == 'exited':
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: {msg[0]} exited.')   # This should not happen under normal operation
                stderrDone = True

            elif msg[0] in ['StdoutThread', 'StderrThread']:
                assert msg[1] == 'log'

                if msg[2].startswith('Running swagger Docs at'):
                    pass

                elif msg[2].startswith('API_CALL_DONE'):
                    if self._LogWaitLoop:
                        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: {msg[0][:6]} is done for this HTTP request.')
                    if msg[0][:6] == 'Stdout':
                        stdoutDone = True
                    else:
                        stderrDone = True

                elif msg[2].startswith('DEBUG:'):
                    self._RLogger.debug(msg[2][6:])

                elif msg[0] == 'StdoutThread':
                    self._RLogger.info(msg[2])

                else:
                    self._RLogger.warning(msg[2])

            else:
                assert msg[1] in ['response', 'exception']
                assert not httpThreadDone

                # If we got an exception here, it means we failed to even make
                # the HTTP request, or the request timed out. It does not
                # mean that the request completed with HTTP status code 500
                # (meaning an error from plumber or R). Therefore, we should
                # not wait around for API_CALL_DONE on the streams, because
                # it's most likely not going to come. Just raise the
                # exception immediately.

                if msg[1] == 'exception':
                    raise msg[2]

                # Otherwise, save the response but continue waiting for
                # API_CALL_DONE on the streams, as needed.

                response = msg[2]
                httpThreadDone = True

                # As a special case, if HTTP status code 401 (Unauthorized) was

                # returned, nothing will be logged to stdout or stderr. This
                # will only happen if we present the wrong authentication
                # token, which is basically impossible. But to allow an
                # authentication exception to be raised rather than timing
                # out, set stdoutDone and stderrDone to True.

                if response.status_code == 401:
                    stdoutDone = True
                    stderrDone = True

        # Return the response.

        return response

    def Stop(self, timeout=5.):
        with self._Lock:
            if self._WorkerProcess is None:
                return
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Stop() called.')

            # Send a request to R to shut down. The R function we call invokes
            # R's quit() function, which ultimately causes the TCP connection
            # to be aborted before we can get a response. Therefore, we
            # expect to catch an exception here. Ignore it.

            url = f'http://127.0.0.1:{self._Port}/shutdown'
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Sending POST to {url}')
            try:
                self._SendHTTPRequest('post', {'url': url, 
                                               'headers': {'Authentication-Token': self._AuthenticationToken},
                                               'allow_redirects': False, 
                                               'timeout': timeout})
            except:
                pass

            # Wait for the child process to exit.

            needToKill = True

            try:
                self._WorkerProcess.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                Logger.Warning(_('MGET\'s Rscript worker process %(pid)s did not exit within %(timeout)s seconds.') % {'pid': self._WorkerProcess.pid, 'timeout': timeout})
            except Exception as e:
                Logger.Warning(_('Failed to wait for MGET\'s Rscript worker process %(pid)s to exit: %(error)s: %(msg)s') % {'pid': self._WorkerProcess.pid, 'error': e.__class__.__name__, 'msg': e})
            else:
                needToKill = False
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Rscript worker process {self._WorkerProcess.pid} exited with code {self._WorkerProcess.returncode}.')

            if needToKill:
                try:
                    self._WorkerProcess.kill()
                except Exception as e:
                    Logger.Warning(_('Failed to kill MGET\'s Rscript worker process %(pid)s: %(error)s: %(msg)s') % {'pid': self._WorkerProcess.pid, 'error': e.__class__.__name__, 'msg': e})
                else:
                    Logger.Warning(_('Killed MGET\'s Rscript worker process %(pid)s.') % {'pid': self._WorkerProcess.pid})

            self._WorkerProcess = None

            # Close the other stuff we opened.

            if self._HTTPThread is not None:
                if self._HTTPThread.is_alive():
                    try:
                        self._HTTPThreadQueue.put(('stop',), timeout=1)
                        self._HTTPThread.join(timeout=1)
                    except:
                        pass
                self._HTTPThread = None

            if self._StdoutThread is not None:
                if self._StdoutThread.is_alive():
                    try:
                        self._StdoutThread.join(timeout=1)
                    except:
                        pass
                self._StdoutThread = None

            if self._StderrThread is not None:
                if self._StderrThread.is_alive():
                    try:
                        self._StderrThread.join(timeout=1)
                    except:
                        pass
                self._StderrThread = None

            self._MainThreadQueue = None
            self._HTTPThreadQueue = None

            try:
                self._Session.close()
            except:
                pass
            self._Session = None

            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Closed requests.Session 0x{id(self._Session):016X}.')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._Lock:
            self.Stop()
        return False

    def __del__(self):

        # Do not try to call self.Stop() here. Under normal operation,
        # __del__() is called by the garbage collector after an unpredictable
        # delay, making it an unreliable way to control the lifetime of the
        # worker process. Instead, use the context manager protocol
        # (a.k.a. the "with" statement), or call self.Stop() explicitly from
        # a try/finally block.

        pass

    def _ProcessResponse(self, resp, parseReturnValue=False):

        # If we got HTTP 500 and the response body is a JSON dict with a
        # "message" string, it means the error was raised by R. Log the call
        # stack tree and raise a RuntimeError with the message.

        if resp.status_code == 500:
            try:
                respJSON = resp.json()
            except:
                pass
            else:
                if isinstance(respJSON, dict) and 'message' in respJSON and isinstance(respJSON['message'], str):
                    Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Recieved HTTP 500 with an error message from R: {respJSON["message"]}')
                    if 'cst' in respJSON and isinstance(respJSON['cst'], list):
                        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: The following R call stack tree was captured:')
                        for line in respJSON['cst']:
                            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: {line.rstrip()}')
                    raise RuntimeError(f'From R: {respJSON["message"]}')

        # If we received anything other than HTTP 200, ask the requests
        # package to raise an error. If it does not, raise a RuntimeError
        # ourself.

        if resp.status_code != 200:
            raise RuntimeError(f'MGET placed a call to R through HTTP and the R plumber package, but the HTTP call unexpectedly failed with status code {resp.status_code}: {resp.reason}')

        # If we're not supposed to parse the response body, just return None.

        if not parseReturnValue:
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Recieved HTTP 200, ignoring response body.')
            return(None)

        # The HTTP response code was 200: OK. If requested, parse and return
        # the response body.

        if 'Content-Type' in resp.headers:
            if resp.headers['Content-Type'] == 'application/json':
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Recieved HTTP 200, parsing JSON.')
                try:
                    respJSON = json.loads(resp.text, cls=functools.partial(_MongoDateTimeDecoder, default_tzinfo=self._TZInfo))
                except:
                    Logger.Error('MGET placed a call to R through HTTP and the R plumber package and was supposed receive a JSON response but JSON parser failed. The following exception contains the details.')
                    raise
                return respJSON

            elif resp.headers['Content-Type'] in ['application/vnd.apache.arrow.file', 'application/x-feather']:
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Recieved HTTP 200, parsing feather.')
                import pyarrow.feather
                try:
                    featherData = io.BytesIO(resp.content)
                    table = pyarrow.feather.read_feather(featherData)
                except:
                    Logger.Error('MGET placed a call to R through HTTP and the R plumber package and was supposed receive a data frame as a feather table but a pandas DataFrame could not be parsed from the HTTP response. The following exception contains the details.')
                    raise
                return table

            raise RuntimeError(f'MGET placed a call to R through HTTP and the R plumber package and received a response with an unknown Content-Type "{resp.headers["Content-Type"]}". Please try this operation again, and if it continues to fail, contact the MGET development team for assistance.')

        # Otherwise, just return None.

        Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Recieved HTTP 200 with no Content-Type header; ignoring response body.')

        return None

    def _PollWorkerProcess(self):
        with self._Lock:
            if self._WorkerProcess is not None:
                try:
                    exitcode = self._WorkerProcess.poll()
                except:
                    Logger.Warning(_('Failed to poll the status of MGET\'s Rscript worker process %(pid)s. MGET will assume it is still running. Detailed error information: %(error)s: %(msg)s') % {'pid': self._WorkerProcess.pid, 'error': e.__class__.__name__, 'msg': e})
                    exitcode = None
                if exitcode is not None:
                    raise RuntimeError(_('MGET\'s Rscript worker process exited unexpectedly with exit code %(exitcode)s. Please call Stop() on this RWorkerProcess object and try again, or instantiate a new RWorkerProcess.') % {'exitcode': exitcode})

    def _GetVariableNames(self):
        with self._Lock:
            self.Start()
            self._PollWorkerProcess()
            url = f'http://127.0.0.1:{self._Port}/list'
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Sending POST to {url}')

            resp = self._SendHTTPRequest('post', {'url': url, 
                                                  'headers': {'Authentication-Token': self._AuthenticationToken},
                                                  'allow_redirects': False, 
                                                  'timeout': self._Timeout})

            return(self._ProcessResponse(resp, parseReturnValue=True))

    def _SerializeValueToJSON(self, obj):

        # This function must be called on a dict with a single item that has
        # the key 'value'.

        if not isinstance(obj, dict) or len(obj) != 1 or 'value' not in obj:
            raise RuntimeError(_('RWorkerProcess._SerializeToJSON() must be called with a dict with a single item that has the key \'value\'. This error is unexpected. Please contact the MGET development team for assistance.'))

        value = obj['value']

        # It turns out that with the latest versions of R jsonlite(1.8.9) and
        # plumber (1.2.2), if it's an atomic datetime (i.e. a single datetime
        # instance, rather than several in a list or tuple) and we then
        # serialize it in "mongo" format with _CustomJSONEncoder, our plumbed
        # "set" function in PlumberAPI.R will receive R NULL as the value
        # instead of a POSIXct. This appears to be a bug in those packages,
        # but the deserialization of mongo format is not a documented feature
        # (it is only mentioned in
        # https://github.com/jeroen/jsonlite/issues/8), so it's hard to say.
        # In any case, we work around it by constructing a special dict that
        # is recognized by our "set" function, which then extracts an atomic
        # POSIXct.

        if isinstance(value, datetime.datetime):
            value = {'value': value, 'RWorkerProcess_IsAtomicDatetime': True}

        # Similarly, if it is a length 1 list or tuple with a single
        # datetime.datetime in it, the same thing will happen. Note that in
        # R, atomic values are just length 1 vectors, so we can use the same
        # mechanism as above.

        elif isinstance(value, (list, tuple)) and len(value) == 1 and isinstance(value[0], datetime.datetime):
            value = {'value': value, 'RWorkerProcess_IsAtomicDatetime': True}

        # Similarly, if value is a dictionary where all the values are
        # datetimes or length 1 lists or tuples of datetimes, the list will
        # be flattened to a vector by jsonlite. We can prevent this by adding
        # a dummy value to the list that is some other type, and then having
        # our "set" function remove it.

        elif isinstance(value, collections.abc.Mapping) and all([isinstance(v, datetime.datetime) or isinstance(v, (list, tuple)) and len(v) == 1 and isinstance(v[0], datetime.datetime) for k, v in value.items()]):
            value = {**value, **{'RWorkerProcess_IsDatetimeList': True}}

        # If it is an atomic float that is NaN, Inf, or -Inf, our encoder will
        # use the strings "NaN", "Inf", or "-Inf", respectively. R's jsonlite
        # will parse those as Nan, Inf, or -Inf, but not if they appear as
        # atomic values; in that case, it will parse them as strings. To work
        # around this, enclose them in a list. R will then parse them as
        # desired, and in R an atomic value is the same as a length 1 vector.

        elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            value = [value]

        # If it's a range, convert it to a list.

        elif isinstance(value, range):
            value = list(value)

        # If it's a dict, recurse down through its values and replace atomic
        # NaN/Inf/-Inf as immediately above.

        elif isinstance(value, collections.abc.Mapping):
            value = self._PrepareDictForJSON(value)

        # If it's a list or tuple, recurse into it and process dicts as
        # immediately above.

        elif isinstance(value, (list, tuple)):
            value = self._PrepareListForJSON(value)

        # Now serialize the value with _CustomJSONEncoder. It has to be
        # inside a dict with the key 'value' so that plumber will use it for
        # the value parameter of the "set" function in PlumberAPI.R.

        return json.dumps({'value': value}, cls=functools.partial(_CustomJSONEncoder, default_tzinfo=self._TZInfo))

    def _PrepareDictForJSON(self, d):
        return {k: [v] if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else \
                   self._PrepareDictForJSON(v) if isinstance(v, collections.abc.Mapping) else \
                   self._PrepareListForJSON(v) if isinstance(v, (list, tuple)) else \
                   list(v) if isinstance(v, range) else \
                   v for k, v in d.items()}

    def _PrepareListForJSON(self, lst):
        return [self._PrepareDictForJSON(item) if isinstance(item, collections.abc.Mapping) else \
                self._PrepareListForJSON(item) if isinstance(item, (list, tuple)) else \
                range(item) if isinstance(item, range) else \
                item for item in lst]

    def __len__(self):
        return(len(self._GetVariableNames()))

    def __iter__(self):
        return(iter(self._GetVariableNames()))

    def __getitem__(self, key):
        if not isinstance(key, str) or len(key.strip()) <= 0:
            raise ValueError('key must be a str with length > 0')
        with self._Lock:
            self.Start()
            self._PollWorkerProcess()
            url = f'http://127.0.0.1:{self._Port}/get'
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Sending POST to {url}')

            resp = self._SendHTTPRequest('post', {'url': url, 
                                                  'params': {'name': key.strip()},
                                                  'headers': {'Authentication-Token': self._AuthenticationToken},
                                                  'allow_redirects': False, 
                                                  'timeout': self._Timeout})

            return(self._ProcessResponse(resp, parseReturnValue=True))

    def __setitem__(self, key, value):
        if not isinstance(key, str) or len(key.strip()) <= 0:
            raise ValueError('key must be a str with length > 0')

        import pandas
        import pyarrow.feather

        with self._Lock:
            self.Start()
            self._PollWorkerProcess()

            # If its a feather Table or pandas DataFrame, serialize it with
            # pyarrow.feather.write_feather, which can handle both types.

            url = f'http://127.0.0.1:{self._Port}/set'

            if isinstance(value, pyarrow.feather.Table) or isinstance(value, pandas.DataFrame):
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Sending PUT to {url} with feather table.')
                buffer = io.BytesIO()
                pyarrow.feather.write_feather(value, buffer)
                buffer.seek(0)
                resp = self._SendHTTPRequest('put', {'url': url, 
                                                     'params': {'name': key.strip()},
                                                     'files': {'value': (None, buffer, 'application/vnd.apache.arrow.file')},
                                                     'headers': {'Authentication-Token': self._AuthenticationToken},
                                                     'allow_redirects': False, 
                                                     'timeout': self._Timeout})

            # Otherwise serialize it to JSON.

            else:
                Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Sending PUT to {url} with JSON.')
                resp = self._SendHTTPRequest('put', {'url': url, 
                                                     'params': {'name': key.strip()},
                                                     'data': self._SerializeValueToJSON({'value': value}),
                                                     'headers': {'Authentication-Token': self._AuthenticationToken},
                                                     'allow_redirects': False, 
                                                     'timeout': self._Timeout})
            
            self._ProcessResponse(resp)

    def __delitem__(self, key):
        if not isinstance(key, str) or len(key.strip()) <= 0:
            raise ValueError('key must be a str with length > 0')
        with self._Lock:
            self.Start()
            self._PollWorkerProcess()
            url = f'http://127.0.0.1:{self._Port}/delete'
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Sending DELETE to {url}')

            resp = self._SendHTTPRequest('delete', {'url': url, 
                                                    'params': {'name': key.strip()},
                                                    'headers': {'Authentication-Token': self._AuthenticationToken},
                                                    'allow_redirects': False, 
                                                    'timeout': self._Timeout})

            self._ProcessResponse(resp)

    def Eval(self, expr, timeout=60.):
        self.__doc__.Obj.ValidateMethodInvocation()
        with self._Lock:
            self.Start()
            self._PollWorkerProcess()
            url = f'http://127.0.0.1:{self._Port}/eval'
            Logger.Debug(f'{self.__class__.__name__} 0x{id(self):016X}: Sending POST to {url}')

            resp = self._SendHTTPRequest('post', {'url': url, 
                                                  'json': {'expr': expr}, 
                                                  'headers': {'Authentication-Token': self._AuthenticationToken},
                                                  'allow_redirects': False, 
                                                  'timeout': timeout})

            return(self._ProcessResponse(resp, parseReturnValue=True))

    @classmethod
    def ExecuteRAndEvaluateExpressions(cls, expressions, returnResult=False, timeout=60., rPackages=None, rInstallDir=None, rLibDir=None, rRepository='https://cloud.r-project.org', updateRPackages=False, port=None, startupTimeout=15., defaultTZ=None, variableNames=None, variableValues=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if variableNames is not None and variableValues is None or variableNames is None and variableValues is not None:
            Logger.RaiseException(ValueError(_('The variableNames and variableValues parameters must both be provided, or neither must be provided.')))

        uniqueNames = {}
        if variableNames is not None:
            for name in variableNames:
                if name in uniqueNames:
                    Logger.RaiseException(ValueError(_('The name "%(name)s" appears more than once in the list of variable names to define in the R interpreter. This is not allowed. Please rename or remove the duplicates.') % {'name': name}))
                uniqueNames[name] = None

        # If the caller provided variable values, parse strings into None,
        # boolean, integer, float, and datetime, so that ArcGIS users can pass
        # in these types (instead of just being able to pass in strings).

        if variableNames is not None:
            for i in range(len(variableValues)):
                if isinstance(variableValues[i], str):
                    if len(variableValues[i]) <= 0:
                        variableValues[i] = None
                    else:
                        oldValue = variableValues[i].strip().lower()
                        if oldValue == 'true':
                            variableValues[i] = True
                        elif oldValue == 'false':
                            variableValues[i] = False
                        else:
                            newValue = None
                            try:
                                newValue = int(oldValue)
                            except:
                                try:
                                    newValue = FloatTypeMetadata.ParseFromArcGISString(oldValue)
                                except:
                                    try:
                                        newValue = DateTimeTypeMetadata.ParseDatetimeFromString(variableValues[i].strip())
                                    except:
                                        pass
                            if newValue is not None:
                                variableValues[i] = newValue

        # Instantiate RWorkerProcess using the caller's parameters.

        with RWorkerProcess(rInstallDir=rInstallDir, rLibDir=rLibDir, rRepository=rRepository, rPackages=rPackages, updateRPackages=updateRPackages, port=port, startupTimeout=startupTimeout, defaultTZ=defaultTZ) as r:

            # If the caller passed us variables to assign, assign them now.

            if variableNames is not None:
                for i in range(len(variableNames)):
                    if isinstance(variableValues[i], datetime.datetime) and variableValues[i].tzinfo is None:
                        r[variableNames[i]] = variableValues[i].replace(tzinfo=r._TZInfo)
                    else:
                        r[variableNames[i]] = variableValues[i]

            # Iterate through the lines, evaluate each one, and return the
            # result of the last one.

            result = None
            for i, expr in enumerate(expressions):
                if returnResult and i == len(expressions) - 1:
                    result = r.Eval(expr, timeout=timeout)
                else:
                    r.Eval(expr + '; NULL', timeout=timeout)
            return result


#################################################################################
# This module is not meant to be imported directly. Import GeoEco.R instead.
#################################################################################

__all__ = []
