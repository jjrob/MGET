# Matlab/_MatlabWorkerProcess.py - Defines MatlabWorkerProcess, a class that
# hosts MatlabFunctions in a child process and proxies calls to it, so that
# MATLAB can be hosted in a different process and thereby avoid shared library
# conflicts (a.k.a "DLL Hell") with other software hosted in the parent
# process, such as ArcGIS's arcpy library.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from dataclasses import dataclass
import logging
import multiprocessing
import multiprocessing.shared_memory
import multiprocessing.spawn
import os
import queue
import subprocess
import sys
import threading
import time
import traceback
import types

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger
from ._MatlabFunctions import MatlabFunctions


@dataclass
class _SharedNumpyArray:
    name: str
    dtype: str
    shape: tuple
    sharedMemory: object = None


class MatlabWorkerProcess(object):
    __doc__ = DynamicDocString()

    _TimeoutExitCode = 987654321

    def __init__(self, timeout=30., idle=60.):
        self.__doc__.Obj.ValidateMethodInvocation()

        self._Timeout = timeout
        self._Idle = idle
        self._State = 'STOPPED'
        self._WorkerProcess = None
        self._InputQueue = None
        self._OutputQueue = None
        self._MatlabFunctions = None
        self._Lock = threading.Lock()

        # Enumerate the GeoEco functions implemented in MATLAB by the
        # GeoEco.Matlab._Matlab module.

        with open(os.path.join(os.path.dirname(__file__), '_Matlab', 'MatlabFunctions.txt'), 'rt') as f:
            self._MatlabFunctions = [line.strip().split()[0] for line in f.read().strip().split('\n') if not line.startswith('#')]

        # For each MATLAB function implemented in GeoEco.Matlab._Matlab,
        # create a wrapper that calls the worker process and bind it as an
        # instance method.

        for funcName in self._MatlabFunctions:
            Logger.Debug('%(class)s 0x%(id)016X: Binding instance method %(funcName)s.', {'class': self.__class__.__name__, 'id': id(self), 'funcName': funcName})
            self._DefineWrapperFunction(funcName)

    def _DefineWrapperFunction(self, funcName):

        # Define the wrapper function.

        def wrapper(self, *args, **kwargs):

            # Only allow one thread to interact with the worker process at a time.

            with self._Lock:

                # If necessary, start the worker process.

                if self._State != 'READY':
                    self._Start()

                # If it was supposed to be already running but is not, it
                # might have exited after being idle for too long, or the
                # user might have killed it manually. Handle this gracefully
                # by silently starting it again.

                elif self._WorkerProcess.exitcode is not None:
                    if self._WorkerProcess.exitcode == self._TimeoutExitCode:
                        Logger.Debug('%(class)s 0x%(id)016X: Worker process %(pid)s was idle for more than %(idle)s seconds and shut down. Starting a new worker process.', {'class': self.__class__.__name__, 'id': id(self), 'funcName': funcName, 'pid': self._WorkerProcess.pid, 'idle': self._Idle})
                    else:
                        Logger.Debug('%(class)s 0x%(id)016X: Worker process %(pid)s unexpectedly stopped with exit code %(exitcode)i. Starting a new worker process.', {'class': self.__class__.__name__, 'id': id(self), 'funcName': funcName, 'pid': self._WorkerProcess.pid, 'exitcode': self._WorkerProcess.exitcode})

                    self._State = 'STOPPED'
                    self._InputQueue = None
                    self._OutputQueue = None
                    self._WorkerProcess = None

                    self._Start()

                Logger.Debug('%(class)s 0x%(id)016X: Calling function %(funcName)s in worker process %(pid)s.', {'class': self.__class__.__name__, 'id': id(self), 'funcName': funcName, 'pid': self._WorkerProcess.pid})

                # IMPORTANT NOTE:
                #
                # MatlabWorkerProcess uses
                # multiprocessing.shared_memory.SharedMemory to pass numpy arrays
                # to the worker process and receive them back.
                # https://docs.python.org/3/library/multiprocessing.shared_memory.html
                # implies that a shared memory block is not destroyed until some
                # process calls unlink() on it. This is true on Linux but is not
                # true on Windows. See the comments under
                # https://stackoverflow.com/a/74194875. unlink() actually doesn't
                # do anything on Windows, and in order to keep the shared memory
                # block allocated, it is necessary to keep a SharedMemory
                # instance alive in at least one process.
                #
                # The implication of this is: to work on Windows, we cannot adopt
                # a design whereby one process (either the parent or worker)
                # allocates a SharedMemory and calls close() but not unlink(),
                # then passes its name to the other process, which eventually
                # calls close() and then unlink() to destroy the shared memory
                # block. Instead, after the first process passes the SharedMemory
                # name to the other process, it waits for a message back before
                # closing it. It is unfortunate that the Python documentation does
                # not match the actual behavior on Windows, and that we have to 
                # employ this overly complicated design.
                #
                # First, copy any numpy arrays in args and kwargs to shared
                # memory. Then tell the worker process to call the MATLAB
                # function. If copying the arrays or enqueuing the message fails,
                # close and unlink the shared memory instances.

                sharedMemoryInstances = []    # _NumpyArraysToSHM populates this with SharedMemory instances we will close after the worker messages us.

                try:
                    newArgs = MatlabWorkerProcess._NumpyArraysToSHM(args, sharedMemoryInstances)
                    newKWargs = MatlabWorkerProcess._NumpyArraysToSHM(kwargs, sharedMemoryInstances)
                    try:
                        self._InputQueue.put((funcName, newArgs, newKWargs), block=False, timeout=self._Timeout)
                    except Exception as e:
                        raise RuntimeError(_('Failed to put a message into the input queue of MATLAB worker process %(pid)i. The queue did not become available after %(timeout)s seconds of waiting. This may indicate the system is excessively busy, or there may be a bug in this tool. If you suspect the latter, please contact the tool\'s developer for assistance.') % {'pid': self._WorkerProcess.pid, 'timeout': self._Timeout})
                except:
                    while len(sharedMemoryInstances) > 0:
                        sharedMemoryInstances[0].close()
                        sharedMemoryInstances[0].unlink()
                        del sharedMemoryInstances[0]
                    raise

                # Wait for the worker process to tell us it has received arguments
                # and intialized its shared memory instances. Once that is done,
                # close our instances but but do not unlink them. We rely on the
                # worker process to unlink them.

                try:
                    message = self._WaitForMessage(['EXECUTING'], timeout=self._Timeout)

                    if message is None:
                        if self._WorkerProcess.exitcode is not None:
                            try:
                                raise RuntimeError(_('MATLAB worker process %(pid)s unexpectedly exited with exit code %(exitcode)i. If this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'exitcode': self._WorkerProcess.exitcode })
                            finally:
                                self._State = 'STOPPED'
                                self._InputQueue = None
                                self._OutputQueue = None
                                self._WorkerProcess = None

                        raise RuntimeError(_('MATLAB worker process %(pid)s did not respond within %(timeout)s seconds. Verify that the system is not overloaded by other processes. If the system seems idle and this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'timeout': self._Timeout})

                    if isinstance(message, (list, tuple)) and len(message) == 2 and message[0] == 'EXCEPTION':
                        raise message[1]

                    if message != 'EXECUTING':
                        raise RuntimeError(_('MATLAB worker process %(pid)s responded with unknown message %(message)r. If this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'message': message})
                finally:
                    while len(sharedMemoryInstances) > 0:
                        sharedMemoryInstances[0].close()
                        del sharedMemoryInstances[0]

                # Wait for the function to complete. Use timeout=None, because the
                # function may take a very long time.

                message = self._WaitForMessage(['RESULT', 'EXCEPTION'], timeout=None)

                if message is None:
                    try:
                        raise RuntimeError(_('MATLAB worker process %(pid)s unexpectedly exited with exit code %(exitcode)i. If this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'exitcode': self._WorkerProcess.exitcode })
                    finally:
                        self._State = 'STOPPED'
                        self._InputQueue = None
                        self._OutputQueue = None
                        self._WorkerProcess = None

                if isinstance(message, (list, tuple)) and len(message) == 2 and message[0] == 'EXCEPTION':
                    raise message[1]

                if not isinstance(message, (list, tuple)) or len(message) != 2 or message[0] != 'RESULT':
                    raise RuntimeError(_('MATLAB worker process %(pid)s responded with unknown message %(message)r. If this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'message': message})

                # Extract any returned numpy arrays from shared memory.

                try:
                    result = MatlabWorkerProcess._SHMToNumpyArrays(message[1], copy=True)
                finally:
                    MatlabWorkerProcess._CloseAndUnlinkSHM(message[1])

                # Tell the worker process that we received the result.

                try:
                    self._InputQueue.put('RECEIVED', block=False, timeout=self._Timeout)
                except Exception as e:
                    raise RuntimeError(_('Failed to put a message into the input queue of MATLAB worker process %(pid)i. The queue did not become available after %(timeout)s seconds of waiting. This may indicate the system is excessively busy, or there may be a bug in this tool. If you suspect the latter, please contact the tool\'s developer for assistance.') % {'pid': self._WorkerProcess.pid, 'timeout': self._Timeout})

                # Return successfully.

                return result

        # Bind the wrapper to ourselves as an instance method.

        setattr(self, funcName, types.MethodType(wrapper, self))

    def _Start(self):
        Logger.Debug('%(class)s 0x%(id)016X: _Start() called.', {'class': self.__class__.__name__, 'id': id(self)})

        if self._State != 'STOPPED':
            raise RuntimeError('MatlabWorkerProcess._Start() called while in state %s. This method should only be called while in state STOPPED.' % self._State)

        # Allocate queues for sending input to the worker process and
        # receiving output from it.

        try:
            ctx = self._GetMultiprocessingContext()

            self._InputQueue = ctx.Queue(maxsize=100)     # maxsizes chosen to be larger than ever reasonably expected, but low enough to have a chance of avoiding running out of memory if a bug prevents prompt dequeueing 
            self._OutputQueue = ctx.Queue(maxsize=10000)

            # If we're running on Windows and the current executable is not
            # python.exe, instruct multiprocessing.spawn to use python.exe.
            # When we're running as a geoprocessing tool within ArcGIS Pro,
            # the executable is ArcGISPro.exe. If we allow spawn to proceed
            # with that, it will start another copy of ArcGISPro.exe, which
            # will come up as a GUI and not execute the Python interpreter as
            # expected. We need to prevent that from happening and have
            # python.exe start instead.
            #
            # Note: we must use python.exe, not pythonw.exe, because
            # multiprocessing communicates with the child process via the
            # stdin/stdout pipes, and pythonw.exe immediately closes them.
            # However, python.exe does start a console window. To avoid
            # having it displayed, we define a custom class derived from
            # multiprocessing.context.BaseContext.
            # See _GetMultiprocessingContext() defined below.

            oldExecutable = None

            if sys.platform == 'win32' and os.path.basename(multiprocessing.spawn.get_executable()).lower() != 'python.exe':
                oldExecutable = multiprocessing.spawn.get_executable()
                newExecutable = os.path.join(sys.exec_prefix, 'python.exe')
                Logger.Debug('%(class)s 0x%(id)016X: multiprocessing.spawn.get_executable() returned %(old)s. Calling multiprocessing.spawn.set_executable(%(new)s).', {'class': self.__class__.__name__, 'id': id(self), 'old': oldExecutable, 'new': newExecutable})
                multiprocessing.spawn.set_executable(newExecutable)

            try:
                # Create and start the worker process.

                self._WorkerProcess = ctx.Process(target=MatlabWorkerProcess._Worker, args=(self._InputQueue, self._OutputQueue, self._Idle), daemon=True)
                self._WorkerProcess.start()

            # Revert the multiprocessing.spawn executable, if needed.

            finally:
                if oldExecutable is not None:
                    Logger.Debug('%(class)s 0x%(id)016X: Calling multiprocessing.spawn.set_executable() with previous value %(old)s.', {'class': self.__class__.__name__, 'id': id(self), 'old': oldExecutable})
                    multiprocessing.spawn.set_executable(oldExecutable)

            Logger.Debug('%(class)s 0x%(id)016X: Worker process %(pid)i started.', {'class': self.__class__.__name__, 'id': id(self), 'pid': self._WorkerProcess.pid})

            # Wait up to self._Timeout seconds until it is ready.

            message = self._WaitForMessage(['READY', 'EXCEPTION'], timeout=self._Timeout)

            if self._WorkerProcess.exitcode is not None:
                raise RuntimeError(_('MATLAB worker process %(pid)s unexpectedly exited with exit code %(exitcode)i. If this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'exitcode': self._WorkerProcess.exitcode })

            try:
                if message is None:
                    raise RuntimeError(_('MATLAB worker process %(pid)s did not respond within %(timeout)s seconds of being started. Verify that the system is not overloaded by other processes. If the system seems idle and this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'timeout': self._Timeout})

                if isinstance(message, (list, tuple)) and len(message) == 2 and message[0] == 'EXCEPTION':
                    Logger.Error(_('MATLAB worker process %(pid)s failed while trying to initialize MATLAB. Please review the preceding and following log messages for more information.') % {'pid': self._WorkerProcess.pid})
                    raise message[1]

                if message != 'READY':
                    raise RuntimeError(_('MATLAB worker process %(pid)s responded with unknown message %(message)r after being started. Please contact the developer of this tool for assistance.') % {'pid': self._WorkerProcess.pid, 'message': message})
            except:
                try:
                    self._WorkerProcess.terminate()
                except:
                    pass
                raise

        except:
            self._InputQueue = None
            self._OutputQueue = None
            self._WorkerProcess = None
            raise

        self._State = 'READY'

    @classmethod
    def _GetMultiprocessingContext(cls):

        # If we are not on win32, we can get a 'spawn' context as implemented
        # by the Python Standard Library. This context will allow creation of
        # a child process with no GUI, within which we'll run the MATLAB
        # Runtime via its Python API.

        if sys.platform != 'win32':
            return multiprocessing.get_context('spawn')

        # Othewise (we're on win32), we have a problem. The 'spawn' context as
        # implemented by the Python Standard Library
        # calls _winapi.CreateProcess() without specifying the creation flag
        # needed to hide the window. Define a new 'spawnhidden' context that
        # the Standard Library's multiprocessing.context module can use, and
        # add 'spawnhidden' to that module's _concrete_contexts dictonary.
        # Now get the 'spawnhidden' context and return it.

        return multiprocessing.get_context('spawnhidden')

    def _WaitForMessage(self, desiredMessages, timeout):
        started = time.perf_counter()
        while self._WorkerProcess.exitcode is None and (timeout is None or time.perf_counter() - started < timeout):
            try:
                message = self._OutputQueue.get(timeout=1)   # Wait at a shorter interval than timeout, so we will notice if the worker exits.
            except queue.Empty:
                pass
            else:
                if message in desiredMessages or isinstance(message, (tuple, list)) and len(message) > 0 and message[0] in desiredMessages:
                    return message
                elif isinstance(message, (tuple, list)) and len(message) > 0 and message[0] == 'LOG':
                    logging.getLogger('GeoEco').log(message[1], message[2] if message[1] > logging.DEBUG else 'MATLAB worker process %i: %s' % (self._WorkerProcess.pid, message[2]))
                else:
                    logging.getLogger('GeoEco').warning(_('Received an unexpected message MATLAB worker process %(pid)s. This may indicate a programming error in this tool. The message will be ignored. The message was: %(msg)r') % {'pid': self._WorkerProcess.pid, 'msg': message})
        return None

    def Stop(self, timeout=30.):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Only allow one thread to interact with the worker process at a time.

        with self._Lock:
            if self._State != 'READY':
                Logger.Debug('%(class)s 0x%(id)016X: Stop() called while in state %(state)s. There is no process to stop.', {'class': self.__class__.__name__, 'id': id(self), 'state': self._State})
                return

            Logger.Debug('%(class)s 0x%(id)016X: Stop() called.', {'class': self.__class__.__name__, 'id': id(self)})

            try:
                self._InputQueue.put('STOP', block=False, timeout=timeout)
            except Exception as e:
                Logger.LogExceptionAsWarning(_('Failed to put the message "STOP" into the input queue of MATLAB worker process %(pid)i. You may need to stop the process manually.') % {'pid': self._WorkerProcess.pid})
                return

            Logger.Debug('%(class)s 0x%(id)016X: STOP message sent; waiting for process %(pid)i to exit.', {'class': self.__class__.__name__, 'id': id(self), 'pid': self._WorkerProcess.pid})

            started = time.perf_counter()

            while self._WorkerProcess.exitcode is None and (timeout is None or time.perf_counter() - started < timeout):
                while not self._OutputQueue.empty() and time.perf_counter() - started < 0.250:
                    try:
                        self._OutputQueue.get_nowait()
                    except:
                        pass
                time.sleep(0.250)

            if self._WorkerProcess.exitcode is None:
                Logger.Warning(_('Failed to stop MATLAB worker process %(pid)i after trying for %(timeout)s seconds. You may need to stop the process manually.') % {'pid': self._WorkerProcess.pid, 'timeout': timeout})
            else:
                Logger.Debug('%(class)s 0x%(id)016X: Worker process %(pid)i exited with code %(exitcode)s.', {'class': self.__class__.__name__, 'id': id(self), 'pid': self._WorkerProcess.pid, 'exitcode': self._WorkerProcess.exitcode})

            self._State = 'STOPPED'
            self._InputQueue = None
            self._OutputQueue = None
            self._WorkerProcess = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Stop()
        return False  # Ensure any exceptions are propagated

    def __del__(self):

        # Do not try to call self.Stop() here. self.Stop() calls
        # self._InputQueue.put(), which seems to cause Python to deadlock when
        # Python is shutting down, for reasons I don't understand. Plus, under
        # normal operation, __del__() is called by the garbage collector after
        # an unpredictable delay, making it an unreliable way to control the
        # lifetime of the worker process. Instead, use the context manager
        # protocol (a.k.a. the "with" statement), or call self.Stop()
        # explicitly from a try/finally block.

        pass

    @staticmethod
    def _NumpyArraysToSHM(value, sharedMemoryInstances):

        # If the value is a list, tuple, or dict, process every item with it.

        if isinstance(value, list):
            return [MatlabWorkerProcess._NumpyArraysToSHM(item, sharedMemoryInstances) for item in value]

        if isinstance(value, tuple):
            return tuple([MatlabWorkerProcess._NumpyArraysToSHM(item, sharedMemoryInstances) for item in value])

        if isinstance(value, dict):
            return {k: MatlabWorkerProcess._NumpyArraysToSHM(v, sharedMemoryInstances) for k, v in value.items()}

        # If it is a numpy array, store it in shared memory and replace it
        # with a _SharedNumpyArray object.

        import numpy

        if isinstance(value, numpy.ndarray):
            return MatlabWorkerProcess._StoreNumpyArrayInSHM(value, sharedMemoryInstances)

        # If we got to here, it is not a list, tuple, dict, or numpy array.
        # Return it as-is.

        return value

    @staticmethod
    def _StoreNumpyArrayInSHM(a, sharedMemoryInstances):
        import numpy
        shm = multiprocessing.shared_memory.SharedMemory(create=True, size=a.nbytes)
        sharedMemoryInstances.append(shm)
        b = numpy.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)
        b[:] = a[:]
        return _SharedNumpyArray(name=shm.name, dtype=a.dtype, shape=a.shape)

    @staticmethod
    def _SHMToNumpyArrays(value, copy):

        # If the value is a list, tuple, or dict, process every item with it.

        if isinstance(value, list):
            return [MatlabWorkerProcess._SHMToNumpyArrays(item, copy=copy) for item in value]

        if isinstance(value, tuple):
            return tuple([MatlabWorkerProcess._SHMToNumpyArrays(item, copy=copy) for item in value])

        if isinstance(value, dict):
            return {k: MatlabWorkerProcess._SHMToNumpyArrays(v, copy=copy) for k, v in value.items()}

        # If it is a _SharedNumpyArray, construct a numpy array for it.

        if isinstance(value, _SharedNumpyArray):
            return MatlabWorkerProcess._GetNumpyArrayFromSHM(value, copy=copy)

        # If we got to here, it is not a list, tuple, dict, or numpy array.
        # Return it as-is.

        return value

    @staticmethod
    def _GetNumpyArrayFromSHM(sharedNumpyArray, copy):
        import numpy
        sharedNumpyArray.sharedMemory = multiprocessing.shared_memory.SharedMemory(name=sharedNumpyArray.name)
        try:
            a = numpy.ndarray(sharedNumpyArray.shape, dtype=sharedNumpyArray.dtype, buffer=sharedNumpyArray.sharedMemory.buf)
            if not copy:
                return a
            b = numpy.zeros(sharedNumpyArray.shape, dtype=sharedNumpyArray.dtype)   # I'm not 100% confident copy.deepcopy() will allocate a new buffer, so I'm explicitly creating a new array and copying its values
            b[:] = a[:]
            return b
        except:
            sharedNumpyArray.sharedMemory.close()
            sharedNumpyArray.sharedMemory = None
            raise

    @staticmethod
    def _CloseSHM(value):

        # If the value is a list, tuple, or dict, process every item with it.

        if isinstance(value, (list, tuple, dict)):
            for item in value:
                MatlabWorkerProcess._CloseSHM(item)

        elif isinstance(value, dict):
            for key in value:
                MatlabWorkerProcess._CloseSHM(value[key])

        # If it is a _SharedNumpyArray, close the shared_memory.

        elif isinstance(value, _SharedNumpyArray) and value.sharedMemory is not None:
            value.sharedMemory.close()
            value.sharedMemory = None

    @staticmethod
    def _CloseAndUnlinkSHM(value):

        # If the value is a list, tuple, or dict, process every item with it.

        if isinstance(value, (list, tuple, dict)):
            for item in value:
                MatlabWorkerProcess._CloseAndUnlinkSHM(item)

        elif isinstance(value, dict):
            for key in value:
                MatlabWorkerProcess._CloseAndUnlinkSHM(value[key])

        # If it is a _SharedNumpyArray, unlink the shared_memory.

        elif isinstance(value, _SharedNumpyArray):
            if value.sharedMemory is None:
                value.sharedMemory = multiprocessing.shared_memory.SharedMemory(name=value.name)
            value.sharedMemory.close()
            value.sharedMemory.unlink()
            value.sharedMemory = None

    @staticmethod
    def _Worker(inputQueue, outputQueue, idle):

        # Initialize MatlabFunctions and import numpy

        try:
            MatlabFunctions.Initialize(loggingQueue=outputQueue)
            import numpy
        except Exception as e:
            MatlabWorkerProcess._ReportWorkerException(e, outputQueue)
            return    # This will cause the process to exit with exit code 0.

        # Tell the parent process we're ready.

        outputQueue.put('READY')

        # Now loop, servicing requests to call methods of MatlabFunctions
        # until we're told to stop.

        while True:
            try:
                request = inputQueue.get(block=True, timeout=idle)
            except queue.Empty:
                sys.exit(MatlabWorkerProcess._TimeoutExitCode)   # This will cause the process to exit with the timeout exit code.

            if request == 'STOP':
                return    # This will cause the process to exit with exit code 0.

            try:
                (funcName, args, kwargs) = request

                try:
                    func = getattr(MatlabFunctions, funcName)
                    newArgs = MatlabWorkerProcess._SHMToNumpyArrays(args, copy=False)
                    newKWargs = MatlabWorkerProcess._SHMToNumpyArrays(kwargs, copy=False)
                    outputQueue.put('EXECUTING')
                    result = func(*newArgs, **newKWargs)
                finally:
                    MatlabWorkerProcess._CloseAndUnlinkSHM(args)
                    MatlabWorkerProcess._CloseAndUnlinkSHM(kwargs)

                sharedMemoryInstances = []
                result = MatlabWorkerProcess._NumpyArraysToSHM(result, sharedMemoryInstances)

                outputQueue.put(('RESULT', result))
                message = inputQueue.get()

                while len(sharedMemoryInstances) > 0:
                    sharedMemoryInstances[0].close()
                    try:
                        sharedMemoryInstances[0].unlink()
                    except:
                        pass
                    del sharedMemoryInstances[0]

                if message != 'RECEIVED':
                    raise RuntimeError(_('The MATLAB worker process %(pid)s received an unexpected message %(message)r from the parent process. If this problem keeps happening, please contact the developer of this tool for assistance.') % {'pid': os.getpid(), 'message': message})

            except Exception as e:
                MatlabWorkerProcess._ReportWorkerException(e, outputQueue)

    @staticmethod
    def _ReportWorkerException(e, outputQueue):
        excType, excValue, excTraceback = sys.exc_info()
        stackTrace = ''.join(traceback.format_exception(excType, excValue, excTraceback))
        outputQueue.put(('LOG', logging.DEBUG, stackTrace))
        outputQueue.put(('EXCEPTION', e))


# If we're on win32, we need to define a custom
# multiprocessing.context.BaseContext class so that we can spawn hidden child
# processes. See the comment in
# MatlabWorkerProcess._GetMultiprocessingContext() for more information. Note
# that the _SpawnHiddenProcess class we define below must be pickable, which
# is why we define it at module level here rather than privately within
# MatlabWorkerProcess._GetMultiprocessingContext(). 

if sys.platform == 'win32':
    import multiprocessing.context
    import multiprocessing.popen_spawn_win32
    import multiprocessing.process
    import multiprocessing.spawn
    import multiprocessing.util

    class _PopenHidden(multiprocessing.popen_spawn_win32.Popen):
        '''
        Start a hidden subprocess to run the code of a process object
        '''
        method = 'spawnhidden'

        def __init__(self, process_obj):

            # The following implementation of __init__ was duplicated from
            # multiprocessing.popen_spawn_win32.Popen and then modified.

            import ctypes
            import msvcrt
            import _winapi

            prep_data = multiprocessing.spawn.get_preparation_data(process_obj._name)

            # read end of pipe will be duplicated by the child process
            # -- see spawn_main() in spawn.py.
            #
            # bpo-33929: Previously, the read end of pipe was "stolen" by the child
            # process, but it leaked a handle if the child process had been
            # terminated before it could steal the handle from the parent process.
            rhandle, whandle = _winapi.CreatePipe(None, 0)
            wfd = msvcrt.open_osfhandle(whandle, 0)
            cmd = multiprocessing.spawn.get_command_line(parent_pid=os.getpid(),
                                                         pipe_handle=rhandle)
            cmd = ' '.join('"%s"' % x for x in cmd)

            python_exe = multiprocessing.spawn.get_executable()

            # bpo-35797: When running in a venv, we bypass the redirect
            # executor and launch our base Python.
            if multiprocessing.popen_spawn_win32.WINENV and multiprocessing.popen_spawn_win32._path_eq(python_exe, sys.executable):
                python_exe = sys._base_executable
                env = os.environ.copy()
                env["__PYVENV_LAUNCHER__"] = sys.executable
            else:
                env = None

            with open(wfd, 'wb', closefd=True) as to_child:

                ##### Beginning of main modifications

                try:
                    # After the child process is started (below), it will
                    # remain running until MatlabWorkerProcess.Stop() sends
                    # a 'STOP' message to it and it exits of its own accord.
                    # But if this never happens, by default it will keep
                    # running, even if the parent process exits. We do not
                    # want to do this; we want the child to be terminated if
                    # the parent exits. To accomplish this, we add the child
                    # process to a win32 Job object with the
                    # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE flag, so that when
                    # the parent releases the job's handle automatically when
                    # the parent exits, the child will be terminated.
                    # 
                    # Thanks to the author of https://stackoverflow.com/a/16791778
                    # for the example code working with Job objects.
                    #
                    # Also, configure STARTUPINFO and the creation flags to
                    # hide the child process's window.

                    JobObjectExtendedLimitInformation = 9
                    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
                    CREATE_BREAKAWAY_FROM_JOB = 0x01000000
                    CREATE_NO_WINDOW = 0x08000000

                    class IO_COUNTERS(ctypes.Structure):
                        _fields_ = [('ReadOperationCount', ctypes.c_uint64),
                                    ('WriteOperationCount', ctypes.c_uint64),
                                    ('OtherOperationCount', ctypes.c_uint64),
                                    ('ReadTransferCount', ctypes.c_uint64),
                                    ('WriteTransferCount', ctypes.c_uint64),
                                    ('OtherTransferCount', ctypes.c_uint64)]

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

                    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
                        _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                                    ('IoInfo', IO_COUNTERS),
                                    ('ProcessMemoryLimit', ctypes.c_void_p),
                                    ('JobMemoryLimit', ctypes.c_void_p),
                                    ('PeakProcessMemoryUsed', ctypes.c_void_p),
                                    ('PeakJobMemoryUsed', ctypes.c_void_p)]

                    jobInfo = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                    outSize = ctypes.c_uint32()

                    hJob = ctypes.windll.kernel32.CreateJobObjectW(None, None)
                    if hJob == 0:
                        raise RuntimeError('Failed to create Win32 Job object: ctypes.windll.kernel32.CreateJobObjectW() failed.')

                    try:
                        success = ctypes.windll.kernel32.QueryInformationJobObject(hJob,
                                                                                   JobObjectExtendedLimitInformation,
                                                                                   ctypes.POINTER(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)(jobInfo),
                                                                                   ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION),
                                                                                   ctypes.POINTER(ctypes.c_uint32)(outSize))
                        if success == 0:
                            raise RuntimeError('Failed to create Win32 Job object: ctypes.windll.kernel32.CreateJobObjectW() failed.')

                        jobInfo.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

                        success = ctypes.windll.kernel32.SetInformationJobObject(hJob,
                                                                                 JobObjectExtendedLimitInformation,
                                                                                 ctypes.POINTER(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)(jobInfo),
                                                                                 ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION))
                        if success == 0:
                            raise RuntimeError('Failed to set LimitFlags on Win32 Job object: ctypes.windll.kernel32.SetInformationJobObject() failed.')

                        flags = CREATE_BREAKAWAY_FROM_JOB | CREATE_NO_WINDOW

                        startupInfo = subprocess.STARTUPINFO()
                        startupInfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                        startupInfo.wShowWindow = subprocess.SW_HIDE

                        hp, ht, pid, tid = _winapi.CreateProcess(python_exe,    # Application name
                                                                 cmd,           # Command line
                                                                 None,          # Proces security attributes
                                                                 None,          # Thread security attributes
                                                                 False,         # Inherit handles
                                                                 flags,         # Creation flags
                                                                 env,           # Environment 
                                                                 None,          # Current directory
                                                                 startupInfo)   # Startup information
                        _winapi.CloseHandle(ht)

                        success = ctypes.windll.kernel32.AssignProcessToJobObject(hJob, hp)
                        if success == 0:
                            raise RuntimeError('Failed to assign the child process to a Win32 Job object: ctypes.windll.kernel32.AssignProcessToJobObject() failed.')

                    except:
                        try:
                            _winapi.CloseHandle(hJob)
                        except:
                            pass
                        raise
                except:
                    try:
                        _winapi.CloseHandle(rhandle)
                    except:
                        pass
                    raise

                # set attributes of self
                self.pid = pid
                self.returncode = None
                self._handle = hp
                self.sentinel = int(hp)
                self.finalizer = multiprocessing.util.Finalize(self, multiprocessing.popen_spawn_win32._close_handles,
                                                               (self.sentinel, int(rhandle), hJob))

                ##### End of main modifications

                # send information to child
                multiprocessing.context.set_spawning_popen(self)
                try:
                    multiprocessing.context.reduction.dump(prep_data, to_child)
                    multiprocessing.context.reduction.dump(process_obj, to_child)
                finally:
                    multiprocessing.context.set_spawning_popen(None)

    class _SpawnHiddenProcess(multiprocessing.process.BaseProcess):
        _start_method = 'spawnhidden'
        @staticmethod
        def _Popen(process_obj):
            return _PopenHidden(process_obj)

    class _SpawnHiddenContext(multiprocessing.context.BaseContext):
        _name = 'spawnhidden'
        Process = _SpawnHiddenProcess

    multiprocessing.context._concrete_contexts['spawnhidden'] = _SpawnHiddenContext()



#################################################################################
# This module is not meant to be imported directly. Import GeoEco.Matlab instead.
#################################################################################

__all__ = []
