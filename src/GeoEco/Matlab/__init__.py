# Matlab/__init__.py - GeoEco functions implemented in MATLAB.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import functools
import io
import logging
import os
import packaging.version
import re
import subprocess
import sys
import threading

from ..Dependencies import Dependency, PythonModuleDependency, SoftwareNotInstalledError, UnsupportedPlatformError
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger


class MatlabDependency(Dependency):
    __doc__ = DynamicDocString()

    _Initialized = False
    _MatlabModuleHandle = None
    _MatlabFunctions = None

    def Initialize(self):

        # Return successfully if we have already been initalized.

        if MatlabDependency._Initialized:
            return

        # We require numpy. Make sure it is available.

        d = PythonModuleDependency('numpy', cheeseShopName='numpy')
        d.Initialize()

        # Check that the MATLAB Runtime has been installed and configured. If
        # we're running on Linux, check LD_LIBRARY_PATH for the needed .so
        # files.

        foundMatlab = False
        weSetLdLibraryPath = False

        if sys.platform == 'linux':
            fileToFind = 'libmwmclmcrrt.so.24.1'
            defaultDirs = ['/usr/local/MATLAB/R2024a', '/usr/local/MATLAB/MATLAB_Runtime/R2024a']

            Logger.Debug('MATLAB is required. Searching for %s in LD_LIBRARY_PATH.', fileToFind)

            ldLibraryPath = os.environ.get('LD_LIBRARY_PATH', '')
            if len(ldLibraryPath.strip()) > 0:
                Logger.Debug('LD_LIBRARY_PATH = %s', ldLibraryPath)
                for dir in ldLibraryPath.split(':'):
                    if os.path.isfile(os.path.join(dir, fileToFind)):
                        Logger.Debug('Found %s.' % os.path.join(dir, fileToFind))
                        foundMatlab = True

            if not foundMatlab:
                Logger.Debug('Did not find %s in LD_LIBRARY_PATH.' % fileToFind)
                for defaultDir in defaultDirs:
                    defaultFile = os.path.join(defaultDir, 'runtime', 'glnxa64', fileToFind)
                    Logger.Debug('Checking for %s.' % defaultFile)
                    if os.path.isfile(defaultFile):
                        Logger.Debug('Found it.')
                        foundMatlab = True

                        # We found it but LD_LIBRARY_PATH was not set. The
                        # user may have forgotten this step. Set it for them.

                        ldLibraryPath = [ldLibraryPath] if len(ldLibraryPath) > 0 else []
                        ldLibraryPath.append(defaultDir + '/runtime/glnxa64')
                        ldLibraryPath.append(defaultDir + '/bin/glnxa64')
                        ldLibraryPath.append(defaultDir + '/sys/os/glnxa64')
                        ldLibraryPath.append(defaultDir + '/extern/bin/glnxa64')
                        ldLibraryPath = ':'.join(ldLibraryPath)

                        Logger.Debug('Setting LD_LIBRARY_PATH = %s' % ldLibraryPath)

                        os.environ['LD_LIBRARY_PATH'] = ldLibraryPath
                        weSetLdLibraryPath = True

            # At this point, LD_LIBRARY_PATH is set, either by the user or by
            # us. But before proceeding, we need to check something:
            #
            # MATLAB includes shared libraries that are commonly considered
            # part of the operating system in its sys/os/glnxa64 directory. If
            # allowed, MATLAB will explicitly load these, e.g. using paths like
            # /usr/local/MATLAB/R2024a/bin/glnxa64/../../sys/os/glnxa64/libstdc++.so.6.
            # Then, if we try to later load something else such as GDAL that
            # depends on those libraries, it may fail if MATLAB's version is
            # too old.
            #
            # To try to avoid this, try to determine whether the system
            # libstdc++.so.6 is newer or older than the copy that MATLAB has.
            # If the system one is newer, import GDAL now, which will force
            # the system one to be loaded. Hopefully it will be backward
            # compatible with MATLAB.

            Logger.Debug(_('Comparing the system\'s version of libstdc++.so.6 to MATLAB\'s.'))

            systemLibstdcppPath = None
            systemLibstdcppMaxVer = None
            matlabLibstdcppPath = None
            matlabLibstdcppMaxVer = None

            def _GetMaxGLIBCXXVer(libstdcppPath):
                result = result = subprocess.run(f'strings {libstdcppPath} | grep GLIBCXX_', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if result.returncode != 0 or not isinstance(result.stdout, str) or len(result.stdout) <= 0:
                    return None

                maxVersion = None

                for line in result.stdout.split('\n'):
                    mobj = re.match(r'^\d+(\.\d+){0,2}$', line[8:])
                    if mobj is not None:
                        version = packaging.version.parse(mobj.string)
                        if maxVersion is None or version > maxVersion:
                            maxVersion = version

                return maxVersion

            result = subprocess.run('/sbin/ldconfig -p | grep libstdc++.so.6', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0 and isinstance(result.stdout, str) and len(result.stdout) > 0:
                for line in result.stdout.split('\n'):
                    if '64' in line:
                        path = line.split(' ')[-1]
                        if os.path.isfile(path):
                            systemLibstdcppPath = path
                            break

                systemLibstdcppMaxVer = _GetMaxGLIBCXXVer(systemLibstdcppPath)

            for dir in os.environ['LD_LIBRARY_PATH'].split(':'):
                path = os.path.join(dir, 'libstdc++.so.6')
                if os.path.isfile(path):
                    matlabLibstdcppPath = path
                    break

            if matlabLibstdcppPath is not None:
                matlabLibstdcppMaxVer = _GetMaxGLIBCXXVer(matlabLibstdcppPath)

            if systemLibstdcppPath is not None:
                if systemLibstdcppMaxVer is not None:
                    Logger.Debug(_('The maximum supported GLIBCXX version in the system %(lib)s is %(ver)s.') % {'lib': systemLibstdcppPath, 'ver': systemLibstdcppMaxVer})
                else:
                    Logger.Debug(_('The maximum supported GLIBCXX version in the system %(lib)s could not be determined.') % {'lib': systemLibstdcppPath})
            else:
                Logger.Debug(_('The system libstdc++.so.6 could not be located.'))

            if matlabLibstdcppPath is not None:
                if matlabLibstdcppMaxVer is not None:
                    Logger.Debug(_('The maximum supported GLIBCXX version in MATLAB\'s %(lib)s is %(ver)s.') % {'lib': matlabLibstdcppPath, 'ver': matlabLibstdcppMaxVer})
                else:
                    Logger.Debug(_('The maximum supported GLIBCXX version in MATLAB\'s %(lib)s could not be determined.') % {'lib': matlabLibstdcppPath})
            else:
                Logger.Debug(_('MATLAB\'s copy of libstdc++.so.6 could not be located.'))

            if systemLibstdcppMaxVer is not None and (matlabLibstdcppMaxVer is None or systemLibstdcppMaxVer > matlabLibstdcppMaxVer):
                Logger.Debug(_('The system\'s copy of libstdc++.so.6 appears to be newer. Importing the osgeo.gdal module before initializing MATLAB, so that the system\'s copy is used.'))
                Logger.Debug(_('First unsetting LD_LIBRARY_PATH.'))
                ldLibraryPath = os.environ['LD_LIBRARY_PATH']
                try:
                    try:
                        import osgeo.gdal
                    except Exception as e:
                        Logger.Debug(_('osgeo.gdal failed to import. Proceeding with MATLAB initialization anyway. The failure was: %(error)s: %(msg)s') % {'error': e.__class__.__name__, 'msg': e})
                    else:
                        Logger.Debug(_('osgeo.gdal imported successfully.'))
                finally:
                    Logger.Debug(_('Setting LD_LIBRARY_PATH again.'))
                    os.environ['LD_LIBRARY_PATH'] = ldLibraryPath
            else:
                Logger.Debug(_('The system does not have a newer copy of libstdc++.so.6. Proceeding with MATLAB initialization without pre-loading the system\'s copy.'))

        # Fail if this is an unsupported platform:

        else:
            raise UnsupportedPlatformError(_('This tool rquires MATLAB 2024a or the MATLAB Runtime 2024a, support for accessing MATLAB when running on the %r platform has not been implemented yet. Please contact the developer of this tool for assistance.') % sys.platform)

        # Fail if we did not find MATLAB.

        if not foundMatlab:
            raise SoftwareNotInstalledError(_('This tool requires that MATLAB 2024a or the MATLAB Runtime 2024a be installed. The MATLAB Runtime is free and may be downloaded https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html. Please follow the installation instructions carefully. Please be sure to set the LD_LIBRARY_PATH environment variable, as instructed by https://www.mathworks.com/help/compiler/mcr-path-settings-for-run-time-deployment.html.'))

        try:
            # We found MATLAB. Import the packages.

            Logger.Debug(_('Importing GeoEco.Matlab._Matlab.'))
            try:
                import GeoEco.Matlab._Matlab
            except Exception as e:
                Logger.RaiseException(RuntimeError(_('Failed to import the GeoEco.Logger._Matlab Python module. This may indicate an installation or configuration problem with MATLAB 2024a or the MATLAB Runtime 2024a. "import GeoEco.Matlab._Matlab" failed with %(e)s: %(msg)s') % {'e': e.__class__.__name__, 'msg': e}))

            Logger.Debug(_('Importing matlab.'))
            try:
                import matlab
            except Exception as e:
                Logger.RaiseException(RuntimeError(_('Failed to import the matlab Python module. This may indicate an installation or configuration problem with MATLAB 2024a or the MATLAB Runtime 2024a. "import matlab" failed with %(e)s: %(msg)s') % {'e': e.__class__.__name__, 'msg': e}))

            # Initialize MATLAB. Store the resulting handle as a class attribute.
            # Currently, we never call terminate on this handle, but rely on
            # _Matlab/__init__.py to do it with atexit.

            Logger.Debug(_('Invoking GeoEco.Matlab._Matlab.initialize().'))
            try:
                MatlabDependency._MatlabModuleHandle = GeoEco.Matlab._Matlab.initialize()
            except Exception as e:
                Logger.RaiseException(RuntimeError(_('Failed to initialize the GeoEco.Matlab._Matlab Python module. This may indicate an installation or configuration problem with MATLAB 2024a or the MATLAB Runtime 2024a. "GeoEco.Matlab._Matlab.initialize()" failed with %(e)s: %(msg)s') % {'e': e.__class__.__name__, 'msg': e}))

            # For each MATLAB function implemented in GeoEco.Matlab._Matlab,
            # create a wrapper that performs logging and conversion.

            for funcName in MatlabDependency._MatlabFunctions:
                Logger.Debug('Wrapping GeoEco.Matlab.MatlabDependency._MatlabModuleHandle.%s.__call__', funcName)

                func = getattr(MatlabDependency._MatlabModuleHandle, funcName)    # Returns a matlab_pysdk.runtime.deployablefunc.DeployableFunc instance, which we must call like a function
                func = getattr(func, '__call__')

                globals()[funcName] = MatlabDependency._DefineWrapperFunction(func, funcName)

        finally:
            # If we set LD_LIBRARY_PATH, unset it now, so that other libraries
            # we use, such as GDAL, do not try to load things from it.

            if weSetLdLibraryPath:
                del os.environ['LD_LIBRARY_PATH']

        # We initialized successfully.

        Logger.Debug(_('MATLAB initialized successfully.'))

        _Initialized = True

    @staticmethod
    def _DefineWrapperFunction(func, funcName):

        # This definition must be kept here, in _DefineWrapperFunction, and
        # not moved directly up into the loop where _DefineWrapperFunction is
        # called. If it is moved up there, then the function will only be
        # defined once, and all methods will get the same wrapper.

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return MatlabDependency._CallWrappedFunction(func, 'GeoEco.Matlab.%s' % funcName, args, kwargs)

        return wrapper

    @staticmethod
    def _CallWrappedFunction(func, funcName, args, kwargs):

        # Convert the arguments to MATLAB's preferred types.

        if args is not None:
            args = tuple([MatlabDependency._ToMatlabPreferredType(arg) for arg in args])

        if kwargs is not None:
            kwargs = {param: MatlabDependency._ToMatlabPreferredType(arg) for param, arg in kwargs.items()}

        # Log a message indicating we're calling the function.

        try:
            sig = inspect.signature(func)
            boundArgs = sig.bind(*args, **kwargs)
            argsStr = ', '.join(f'{key}={value!r:.255}' for key, value in boundArgs.arguments.items())
        except:
            argsStr = ', '.join([repr(arg) for arg in args] + ['%s=%.255r' % (key, value) for key, value in kwargs.items()])

        Logger.Debug('Calling %.255s(%s)', funcName, argsStr)

        # Call the function.

        try:
            result = MatlabDependency._CallMatlabAndLogStdout(func, args, kwargs)
        except Exception as e:
            if len(argsStr) <= 0:
                Logger.Error(_('Execution of %(funcName).255s() failed. This may result from a problem with your inputs or it may indicate a programming mistake in this tool. Please review any preceding error messages, check your inputs, and try again. If you suspect a programming mistake in this tool, please contact the author of this tool for assistance. The following error was reported: %(error)s: %(msg)s') % {'funcName': funcName, 'error': e.__class__.__name__, 'msg': e})
            else:
                Logger.Error(_('Execution of %(funcName).255s() failed when given the inputs %(args)s. This may result from a problem with your inputs or it may indicate a programming mistake in this tool. Please review any preceding error messages, check your inputs, and try again. If you suspect a programming mistake in this tool, please contact the author of this tool for assistance. The following error was reported: %(error)s: %(msg)s') % {'funcName': funcName, 'args': argsStr, 'error': e.__class__.__name__, 'msg': e})
            raise

        # Log a message reporting the result.

        if isinstance(result, (tuple, list)):
            resultStr = ', '.join([f'{value!r:.255}' for value in result])
            if len(result) == 1:
                resultStr += ','
            if isinstance(result, tuple):
                resultStr = '(' + resultStr + ')'
            else:
                resultStr = '[' + resultStr + ']'
        else:
            resultStr = f'{result!r:.255}'

        Logger.Debug('%.255s() returned %s', funcName, resultStr)

        # Convert the result from MATLAB's preferred type to our preferred
        # type and return it to the caller.

        return MatlabDependency._FromMatlabPreferredType(result)

    @staticmethod
    def _CallMatlabAndLogStdout(func, args, kwargs):

        # Save references to the current sys.stdout and sys.stderr objects. In
        # Python 3, these are instances of io.TextIOWrapper. We will restore
        # sys.stdout and sys.stderr to these when the MATLAB function returns.

        savedStdout = sys.stdout
        savedStderr = sys.stderr

        # In order to redirect the writes to stdout and stderr done by the
        # MATLAB function, we have to point the original file descriptors for
        # stdout and stderr to pipes that we will create. When the MATLAB
        # function returns, we need to point those descriptors back to the
        # original stdout and stderr streams. To facilitate this, duplicate
        # the current file descriptors; we'll use these duplicates to copy
        # back the streams to the original descriptors.

        savedStdoutFD = os.dup(sys.stdout.fileno())
        savedStderrFD = os.dup(sys.stderr.fileno())

        try:
            # Use the duplicate file descriptors to create io.TextIOWrapper
            # instances, and set sys.stdout and sys.stderr to those instances.
            # Now, Python code that writes to sys.stdout and sys.stderr will
            # write to the same underlying output streams as before, just
            # through the duplicate file descriptors.

            sys.stdout = io.TextIOWrapper(os.fdopen(savedStdoutFD, 'wb', closefd=False))   # Do not close the FD we pass in
            sys.stderr = io.TextIOWrapper(os.fdopen(savedStderrFD, 'wb', closefd=False))   # Do not close the FD we pass in

            try:
                # Iterate through the logging handlers and change any
                # StreamHandlers that are currently using the original
                # sys.stdout or sys.stderr to the replacements we created
                # above.

                for h in logging.getLogger().handlers:
                    if isinstance(h, logging.StreamHandler):
                        if h.stream == savedStdout:
                            h.setStream(sys.stdout)
                        if h.stream == savedStderr:
                            h.setStream(sys.stderr)
                try:
                    # Create pipes that we will use to capture stdout and
                    # stderr from clib and send it to our logging function.

                    stdoutReadPipe, stdoutWritePipe = os.pipe()
                    stderrReadPipe, stderrWritePipe = os.pipe()

                    # Point the original stdout and stderr file descriptors at
                    # the write ends of the pipes. The Python documentations
                    # says this will close the latter FDs if necessary. So I'm
                    # not going to explicitly close sys.stdout.fileno() or
                    # sys.stderr.fileno(). At this point, writers to the
                    # original file descriptors, which should be C programs,
                    # should write to the pipes instead.

                    os.dup2(stdoutWritePipe, savedStdout.fileno())
                    os.dup2(stderrWritePipe, savedStderr.fileno())

                    try:
                        # Above, we duplicated the write ends of the pipes. We
                        # no longer need the left-over copies. Close them.

                        os.close(stdoutWritePipe)
                        os.close(stderrWritePipe)

                        # Start the threads that log the outputs of the pipes.

                        def _LogPipe(readPipe, logLevel):
                            with os.fdopen(readPipe, 'r') as p:     # os.fdopen() closes readPipe for us
                                gotWarning = False
                                while True:
                                    line = p.readline()
                                    if line == '':
                                        break
                                    if logLevel == logging.INFO:
                                        if gotWarning and line.strip().startswith('>'):
                                            level = logging.DEBUG
                                            gotWarning = False
                                        elif line.strip().lower().startswith('warning:'):
                                            level = logging.WARNING
                                            line = line[8:].strip()
                                            gotWarning = True
                                        else:
                                            level = logging.INFO
                                            gotWarning = False
                                    else:
                                        level = logLevel
                                    logging.getLogger('GeoEco').log(level, line.rstrip())

                        stdoutThread = threading.Thread(target=_LogPipe, args=(stdoutReadPipe, logging.INFO))
                        stderrThread = threading.Thread(target=_LogPipe, args=(stderrReadPipe, logging.ERROR))
                        
                        stdoutThread.start()
                        stderrThread.start()

                        # Call the MATLAB function.

                        result = func(*args, **kwargs)

                    finally:

                        # Point the original stdout and stderr file
                        # descriptors back to the original stdout and stderr
                        # streams.

                        os.dup2(savedStdoutFD, savedStdout.fileno())
                        os.dup2(savedStderrFD, savedStderr.fileno())

                finally:

                    # Iterate through the logging handlers and change any
                    # StreamHandlers that are using our replacements back to
                    # sys.stdout or sys.stderr.

                    for h in logging.getLogger().handlers:
                        if isinstance(h, logging.StreamHandler):
                            if h.stream == sys.stdout:
                                h.setStream(savedStdout)
                            if h.stream == sys.stderr:
                                h.setStream(savedStderr)
            finally:

                # Set sys.stdout and sys.stderr back to the original objects.

                sys.stdout = savedStdout
                sys.stderr = savedStderr

        finally:

            # Close the duplicate file descriptors we used for saving the
            # original streams.

            os.close(savedStdoutFD)
            os.close(savedStderrFD)

        return result

    @staticmethod
    def _ToMatlabPreferredType(value):
        # Currently, no conversion is needed when sending data to Matlab.
        return value

    @staticmethod
    def _FromMatlabPreferredType(value):

        # If we got a simple type back, just return it.

        if value is None or isinstance(value, (bool, int, float, complex, str, datetime.datetime, bytearray)):
            return value

        # If the value is a list, tuple, or dict, process every item with it.

        if isinstance(value, list):
            return [MatlabDependency._FromMatlabPreferredType(item) for item in value]

        if isinstance(value, tuple):
            return tuple([MatlabDependency._FromMatlabPreferredType(item) for item in value])

        if isinstance(value, dict):
            return {MatlabDependency._FromMatlabPreferredType(k): MatlabDependency._FromMatlabPreferredType(v) for k, v in value.items()}

        # If it is a MATLAB array type, convert it to a numpy array. Starting
        # with MATLAB 2022a, the types in the matlab Python package support
        # the Python buffer protocol, which allows us to pass them directly to
        # the numpy.array() constructor.

        import numpy
        import matlab

        if isinstance(value, (matlab.int8, matlab.uint8, matlab.int16, matlab.uint16, matlab.int32, matlab.uint32, matlab.int64, matlab.uint64, matlab.single, matlab.double, matlab.logical)):
            return numpy.array(value)

        # If we got to here, we don't have a preferred type we want to convert
        # it to. Just return it as-is.

        return value

    @staticmethod
    def _UninitializedWrapper(*args, **kwargs):
        raise RuntimeError(_('This function is implemented in MATLAB but the MatlabDependency class has not been successfully initialized yet. Please instantiate MatlabDependency and call its Initialize() function before trying to use functions implemented in MATLAB.'))


# Enumerate the GeoEco functions implemented in MATLAB by the
# GeoEco.Matlab._Matlab module and create a module global for each one that
# points to MatlabDependency._UninitializedWrapper.
# MatlabDependency.Initialize() will replace this with a real wrapper that
# does logging and conversion.

with open(os.path.join(os.path.dirname(__file__), '_Matlab', 'MatlabFunctions.txt'), 'rt') as f:
    MatlabDependency._MatlabFunctions = [funcName.strip() for funcName in f.read().strip().split('\n') if not funcName.startswith('#')]

for funcName in MatlabDependency._MatlabFunctions:
    globals()[funcName] = MatlabDependency._UninitializedWrapper

__all__ = ['MatlabDependency'] + MatlabDependency._MatlabFunctions
