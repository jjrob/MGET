# Matlab/_MatlabFunctions.py - Defines MatlabFunctions, a wrapper around
# GeoEco functions implemented in MATLAB that allows them to be called as
# Python functions.
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
import sys
import threading

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ._MatlabDependency import MatlabDependency


class MatlabFunctions(object):
    __doc__ = DynamicDocString()

    _Initialized = False
    _MatlabFunctions = None
    _MatlabModuleHandle = None

    @classmethod
    def Initialize(cls, loggingQueue=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # If we've already been initialized, return immediately.

        if MatlabFunctions._Initialized:
            return

        # Define a helper function for logging debug messages.

        def _LogDebug(fmt, *args):
            MatlabFunctions._Log(logging.DEBUG, fmt % args, loggingQueue)

        # Use MatlabDependency to verify that MATLAB is installed and set
        # LD_LIBRARY_PATH (on Linux) or PATH (on Windows) as necessary in
        # order for the MATLAB Python modules to be importable.

        oldPath = MatlabDependency.FindMatlab(setPath=True, loggingQueue=loggingQueue)

        # We found MATLAB. Import the modules.

        try:
            _LogDebug('Importing GeoEco.Matlab._Matlab.')
            try:
                import GeoEco.Matlab._Matlab
            except Exception as e:
                raise RuntimeError(_('Failed to import the GeoEco.Matlab._Matlab Python module. This may indicate an installation or configuration problem with MATLAB R2024b or the MATLAB Runtime R2024b. "import GeoEco.Matlab._Matlab" failed with %(e)s: %(msg)s') % {'e': e.__class__.__name__, 'msg': e})

            _LogDebug('Importing matlab.')
            try:
                import matlab
            except Exception as e:
                raise RuntimeError(_('Failed to import the matlab Python module. This may indicate an installation or configuration problem with MATLAB R2024b or the MATLAB Runtime R2024b. "import matlab" failed with %(e)s: %(msg)s') % {'e': e.__class__.__name__, 'msg': e})

            # Initialize MATLAB. Store the resulting handle as a class
            # attribute. Currently, we never call terminate on this handle,
            # but rely on atexit to do it.

            _LogDebug('Invoking GeoEco.Matlab._Matlab.initialize().')
            try:
                MatlabFunctions._MatlabModuleHandle = GeoEco.Matlab._Matlab.initialize()
            except Exception as e:
                raise RuntimeError(_('Failed to initialize the GeoEco.Matlab._Matlab Python module. This may indicate an installation or configuration problem with MATLAB R2024b or the MATLAB Runtime R2024b. "GeoEco.Matlab._Matlab.initialize()" failed with %(e)s: %(msg)s') % {'e': e.__class__.__name__, 'msg': e})

            # Enumerate the GeoEco functions implemented in MATLAB by the
            # GeoEco.Matlab._Matlab module.

            with open(os.path.join(os.path.dirname(__file__), '_Matlab', 'MatlabFunctions.txt'), 'rt') as f:
                MatlabFunctions._MatlabFunctions = [line.strip().split()[0] for line in f.read().strip().split('\n') if not line.startswith('#')]

            # For each MATLAB function implemented in GeoEco.Matlab._Matlab,
            # create a wrapper that performs logging and conversion and bind
            # it as a staticmethod of MatlabFunctions.

            for funcName in MatlabFunctions._MatlabFunctions:
                _LogDebug('Wrapping GeoEco.Matlab.MatlabFunctions._MatlabModuleHandle.%s.__call__', funcName)

                func = getattr(MatlabFunctions._MatlabModuleHandle, funcName)    # Returns a matlab_pysdk.runtime.deployablefunc.DeployableFunc instance, which we must call like a function
                func = getattr(func, '__call__')
                meth = staticmethod(MatlabFunctions._DefineWrapperFunction(func, funcName, loggingQueue=loggingQueue))

                setattr(MatlabFunctions, funcName, meth)

        finally:
            # If we set the path, unset it now.

            if oldPath is not None:
                if sys.platform == 'linux':
                    if len(oldPath) > 0:
                        _LogDebug('Changing LD_LIBRARY_PATH back to %s', oldPath)
                        os.environ['LD_LIBRARY_PATH'] = oldPath
                    else:
                        _LogDebug('Deleting the LD_LIBRARY_PATH environment variable')
                        del os.environ['LD_LIBRARY_PATH']

                elif sys.platform == 'win32':
                    _LogDebug('Changing PATH back to %s', oldPath)
                    os.environ['PATH'] = oldPath

        # We initialized successfully.

        _LogDebug('MATLAB initialized successfully.')

        MatlabFunctions._Initialized = True

    @staticmethod
    def _DefineWrapperFunction(func, funcName, loggingQueue):

        # This definition must be kept here, in _DefineWrapperFunction, and
        # not moved directly up into the loop where _DefineWrapperFunction is
        # called. If it is moved up there, then the function will only be
        # defined once, and all methods will get the same wrapper.

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return MatlabFunctions._CallWrappedFunction(func, 'GeoEco.Matlab.MatlabFunctions.%s' % funcName, args, kwargs, loggingQueue)

        return wrapper

    @staticmethod
    def _CallWrappedFunction(func, funcName, args, kwargs, loggingQueue):

        # Convert the arguments to MATLAB's preferred types.

        if args is not None:
            args = tuple([MatlabFunctions._ToMatlabPreferredType(arg) for arg in args])

        if kwargs is not None:
            kwargs = {param: MatlabFunctions._ToMatlabPreferredType(arg) for param, arg in kwargs.items()}

        # Log a message indicating we're calling the function.

        try:
            sig = inspect.signature(func)
            boundArgs = sig.bind(*args, **kwargs)
            argsStr = ', '.join(f'{key}={value!r:.255}' for key, value in boundArgs.arguments.items())
        except:
            argsStr = ', '.join([repr(arg) for arg in args] + ['%s=%.255r' % (key, value) for key, value in kwargs.items()])

        MatlabFunctions._Log(logging.DEBUG, 'Calling %.255s(%s)' % (funcName, argsStr), loggingQueue)

        # Call the function.

        try:
            result = MatlabFunctions._CallMatlabAndLogStdout(func, args, kwargs, loggingQueue)
        except Exception as e:
            if len(argsStr) <= 0:
                msg = _('Execution of %(funcName).255s() failed. This may result from a problem with your inputs or it may indicate a programming mistake in this tool. Please review any preceding or following error messages, check your inputs, and try again. If you suspect a programming mistake in this tool, please contact the author of this tool for assistance.') % {'funcName': funcName}
            else:
                msg = _('Execution of %(funcName).255s() failed when given the inputs: %(args)s. This may result from a problem with your inputs or it may indicate a programming mistake in this tool. Please review any preceding or following error messages, check your inputs, and try again. If you suspect a programming mistake in this tool, please contact the author of this tool for assistance.') % {'funcName': funcName, 'args': argsStr}
            MatlabFunctions._Log(logging.ERROR, msg, loggingQueue)
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

        MatlabFunctions._Log(logging.DEBUG, '%.255s() returned %s' % (funcName, resultStr), loggingQueue)

        # Convert the result from MATLAB's preferred type to our preferred
        # type and return it to the caller.

        return MatlabFunctions._FromMatlabPreferredType(result)

    @staticmethod
    def _CallMatlabAndLogStdout(func, args, kwargs, loggingQueue):

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

                        def _LogPipe(readPipe, logLevel, loggingQueue):
                            MatlabFunctions._Log(logging.DEBUG, '_LogPipe %s thread started' % ('stdout' if logLevel == logging.INFO else 'stderr' if logLevel == logging.ERROR else 'unknown'), loggingQueue)
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
                                    MatlabFunctions._Log(level, line.rstrip(), loggingQueue)
                            MatlabFunctions._Log(logging.DEBUG, '_LogPipe %s thread exiting' % ('stdout' if logLevel == logging.INFO else 'stderr' if logLevel == logging.ERROR else 'unknown'), loggingQueue)

                        stdoutThread = threading.Thread(target=_LogPipe, args=(stdoutReadPipe, logging.INFO, loggingQueue))
                        stderrThread = threading.Thread(target=_LogPipe, args=(stderrReadPipe, logging.ERROR, loggingQueue))
                        
                        stdoutThread.start()
                        stderrThread.start()

                        # Call the MATLAB function.

                        result = func(*args, **kwargs)

                    finally:

                        # Point the original stdout and stderr file
                        # descriptors back to the original stdout and stderr
                        # streams. When os.dup2 is called, the file
                        # descriptors are currently pointing to the write
                        # pipes; os.dup2 will close the write pipes
                        # automatically before we 

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
    def _Log(level, msg, loggingQueue):
        MatlabDependency._Log(level, msg, loggingQueue)

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
            return [MatlabFunctions._FromMatlabPreferredType(item) for item in value]

        if isinstance(value, tuple):
            return tuple([MatlabFunctions._FromMatlabPreferredType(item) for item in value])

        if isinstance(value, dict):
            return {MatlabFunctions._FromMatlabPreferredType(k): MatlabFunctions._FromMatlabPreferredType(v) for k, v in value.items()}

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


#################################################################################
# This module is not meant to be imported directly. Import GeoEco.Matlab instead.
#################################################################################

__all__ = []
