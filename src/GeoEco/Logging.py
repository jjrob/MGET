# Logging.py - Implements the Logger class, which other classes in the GeoEco
# Python package use to report activity to the user.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import logging
import logging.config       # Do not remove this statement, even though it seems redundant after importing the logging module above. Removing it will break something.
import math
import os
import sys
import time
import traceback

from .DynamicDocString import DynamicDocString
from .Internationalization import _


# Public classes exposed by this module

class Logger(object):
    __doc__ = DynamicDocString()

    _GeoEcoLogger = logging.getLogger('GeoEco')
    _LogInfoAsDebug = False    
    _LogErrorsAsWarnings = False    
    
    @classmethod
    def Debug(cls, format, *args):
        try:
            Logger._GeoEcoLogger.debug(format.rstrip(), *args)
        except:
            pass

    @classmethod
    def Info(cls, format, *args):
        try:
            if cls.GetLogInfoAsDebug():
                Logger._GeoEcoLogger.debug(format.rstrip(), *args)
            else:
                Logger._GeoEcoLogger.info(format.rstrip(), *args)
        except:
            pass

    @classmethod
    def Warning(cls, format, *args):
        try:
            Logger._GeoEcoLogger.warning(format.rstrip(), *args)
        except:
            pass

    @classmethod
    def Error(cls, format, *args):
        try:
            if cls.GetLogErrorsAsWarnings():
                Logger._GeoEcoLogger.warning(format.rstrip(), *args)
            else:
                Logger._GeoEcoLogger.error(format.rstrip(), *args)
        except:
            pass

    @classmethod
    def RaiseException(cls, exception):
        try:
            raise exception
        except:
            if cls.GetLogErrorsAsWarnings():
                cls.LogExceptionAsWarning()
            else:
                cls.LogExceptionAsError()
            raise

    @classmethod
    def GetLogInfoAsDebug(cls):
        return Logger._LogInfoAsDebug

    @classmethod
    def SetLogInfoAsDebug(cls, logInfoAsDebug):
        if not isinstance(logInfoAsDebug, bool):
            cls.RaiseException(TypeError(_('The value provided for the logInfoAsDebug parameter is an invalid type ("%(badType)s" in Python). Please provide a value having the Python type "bool".') % {'badType' : type(logInfoAsDebug).__name__}))
        oldValue = Logger._LogInfoAsDebug
        Logger._LogInfoAsDebug = logInfoAsDebug
        return oldValue

    @classmethod
    def GetLogErrorsAsWarnings(cls):
        return Logger._LogErrorsAsWarnings

    @classmethod
    def SetLogErrorsAsWarnings(cls, logErrorsAsWarnings):
        if not isinstance(logErrorsAsWarnings, bool):
            cls.RaiseException(TypeError(_('The value provided for the logErrorsAsWarnings parameter is an invalid type ("%(badType)s" in Python). Please provide a value having the Python type "bool".') % {'badType' : type(logErrorsAsWarnings).__name__}))
        oldValue = Logger._LogErrorsAsWarnings
        Logger._LogErrorsAsWarnings = logErrorsAsWarnings
        return oldValue

    @classmethod
    def LogInfoAndSetInfoToDebug(cls, format, *args):
        cls.Info(format, *args)
        oldValue = cls.SetLogInfoAsDebug(True)
        return oldValue

    @classmethod
    def LogExceptionAsWarning(cls, format=None, *args):
        cls._LogExceptionAndMessage(logging.WARNING, format, *args)

    @classmethod
    def LogExceptionAsError(cls, format=None, *args):
        if cls.GetLogErrorsAsWarnings():
            cls._LogExceptionAndMessage(logging.WARNING, format, *args)
        else:
            cls._LogExceptionAndMessage(logging.ERROR, format, *args)

    _ExceptionTracebackID = None
    _ReportedSubsequentErrors = False
    
    @classmethod
    def _LogExceptionAndMessage(cls, level, format=None, *args):
        try:
            logger = Logger._GeoEcoLogger

            # Log the exception, if it has not been done already.

            tb = sys.exc_info()[2]
            if tb is not None:
                try:

                    # Obtain the inner-most traceback object.
                    
                    while tb.tb_next is not None:
                        tb = tb.tb_next

                    # If we have not logged a traceback yet, or this is a
                    # different one than last time, log it.
                    
                    if cls._ExceptionTracebackID != id(tb):
                        cls._ExceptionTracebackID = id(tb)
                        cls._ReportedSubsequentErrors = False
                        logger.log(level, '%s: %s', sys.exc_info()[0].__name__, str(sys.exc_info()[1]).rstrip())

                        # Log useful debugging information, starting with a stack
                        # trace. To log the stack trace, we could just call
                        # logger.debug(exc_info=True), but that function ultimately
                        # calls traceback.print_exception(), which only prints the
                        # stack frames from the exception back to the frame that
                        # handled the exception. It does NOT go all the way back up
                        # the stack. That is is not good enough for us, because we
                        # need to see how we got to the problem, all the way from
                        # the program entry point. So we have to use the
                        # traceback.extract_stack() function to get those outer
                        # frames.

                        logger.debug(_('---------- BEGINNING OF DEBUGGING INFORMATION ----------'))
                        logger.debug(_('Traceback (most recent call last):'))
                        stackTraceEntries = traceback.extract_stack(tb.tb_frame.f_back) + traceback.extract_tb(tb)
                        for entry in traceback.format_list(stackTraceEntries):
                            for line in entry.split('\n'):
                                if len(line) > 0:
                                    logger.debug(line.rstrip())
                        logger.debug('%s: %s', sys.exc_info()[0].__name__, str(sys.exc_info()[1]).rstrip())

                        # Log the local and global variables of the most recent
                        # GeoEco call, unless it is RaiseException.

                        frame = tb.tb_frame
                        try:
                            while frame is not None and (frame.f_code.co_filename.find('GeoEco') == -1 or frame.f_code.co_filename.endswith('Logging.py') and frame.f_code.co_name == 'RaiseException' or frame.f_code.co_filename.endswith('R.py') and frame.f_code.co_name in ['__call__', '__getitem__', '__setitem__', '__delitem__', '__getattr__', '__setattr__', '__delattr__']):
                                frame = frame.f_back
                            if frame is None:
                                frame = tb.tb_frame
                            logger.debug(_('Local variables for stack frame: File "%(file)s", line %(line)i, in %(func)s:') % {'file' : frame.f_code.co_filename, 'line' : frame.f_lineno, 'func' : frame.f_code.co_name})
                            keys = list(frame.f_locals.keys())
                            keys.sort()
                            for key in keys:
                                logger.debug('  %s = %s', key, repr(frame.f_locals[key]))

                            logger.debug(_('Global variables for stack frame: File "%(file)s", line %(line)i, in %(func)s:') % {'file' : frame.f_code.co_filename, 'line' : frame.f_lineno, 'func' : frame.f_code.co_name})
                            keys = list(frame.f_globals.keys())
                            keys.sort()
                            for key in keys:
                                if key != '__builtins__':       # Don't bother dumping __builtins__
                                    logger.debug('  %s = %s', key, repr(frame.f_globals[key]))
                        finally:
                            del frame            # Avoid memory cycle by explicitly deleting frame object; see Python documentation for discussion of this problem.

                        # Log other useful info.                                

                        logger.debug(_('Environment variables:'))
                        keys =  list(os.environ.keys())
                        keys.sort()
                        for key in keys:
                            logger.debug('  %s = %s', key, repr(os.environ[key]))

                        logger.debug(_('Other variables:'))
                        import GeoEco
                        logger.debug('  GeoEco.__version__ = %s', repr(GeoEco.__version__))
                        logger.debug('  sys.argv = %s', repr(sys.argv))
                        logger.debug('  sys.version = %s', str(sys.version))
                        logger.debug('  sys.version_info = %s', repr(sys.version_info))
                        logger.debug('  sys.platform = %s', str(sys.platform))
                        if isinstance(sys.platform, str) and sys.platform.lower() == 'win32':
                            logger.debug('  sys.getwindowsversion() = %s', repr(sys.getwindowsversion()))
                        logger.debug('  os.getcwd() = %s', str(os.getcwd()))
                        logger.debug('  sys.path = %s', repr(sys.path))

                        keys =  list(sys.modules.keys())
                        keys.sort()
                        logger.debug(_('Loaded modules: ') + ', '.join(keys))

                        logger.debug(_('---------- END OF DEBUGGING INFORMATION ----------'))
                finally:
                    del tb          # Avoid memory cycle by explicitly deleting traceback object; see Python documentation for discussion of this problem.
            else:
                cls._ExceptionTracebackID = None

            # If the caller provided a message, log it.

            if format is not None:
                
                # If this is the first message to be logged after the exception,
                # first log a message indicating that the following messages are
                # consequences of the original exception.

                if cls._ExceptionTracebackID is not None and not cls._ReportedSubsequentErrors:
                    logger.log(level, _('The following consequences resulted from the original error:'))
                    cls._ReportedSubsequentErrors = True

                # Log the message.
                
                logger.log(level, format.rstrip(), *args)
            
        except:
            pass

    @classmethod
    def Initialize(cls, activateArcGISLogging=False, loggingConfigFile=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Hack: this module (GeoEco.Logging) defines a class _ArcGISLoggingHandler
        # which derives from logging.Handler. We want the user to be able to
        # reference this handler in a logging configuration file. But the logging.config
        # module offers no way to import this module into its namespace, which
        # prevents it from being able to instantiate our class. So we must manually
        # import ourself into the logging namespace (! not logging.config !).

        if 'GeoEco' not in sys.modules['logging'].__dict__:
            sys.modules['logging'].__dict__['GeoEco'] = sys.modules['GeoEco']
        if 'GeoEco.Logging' not in sys.modules['logging'].__dict__:
            sys.modules['logging'].__dict__['GeoEco.Logging'] = sys.modules['GeoEco.Logging']

        # If the caller provided a file, try to initialize the logging system
        # from it.

        callersFileWarning = None
        if loggingConfigFile is not None:
            callersFileWarning = cls._InitializeLoggingFromFile(loggingConfigFile)

        # If the caller did not provide a file, or the logging system could not
        # be initialized from it, try the user's default logging config file.

        userDefaultFile = None
        userDefaultFileWarning = None
        if loggingConfigFile is None or callersFileWarning is not None:
            if sys.platform.lower() == 'win32':
                if 'APPDATA' in os.environ:
                    userDefaultFile = os.path.join(os.environ['APPDATA'], 'GeoEco', 'Logging.ini')
            else:
                userDefaultFile = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), 'GeoEco', 'Logging.ini')

            if userDefaultFile is not None:
                if os.path.isfile(userDefaultFile):
                    userDefaultFileWarning = cls._InitializeLoggingFromFile(userDefaultFile)
                else:
                    userDefaultFile = None

        # If if the caller's file or the user's default file did not work, try
        # the system default logging file.

        if sys.platform.lower() != 'win32' and os.path.isfile(os.path.join('/', 'etc', 'GeoEco', 'Logging.ini')):
            systemDefaultFile = os.path.join('/', 'etc', 'GeoEco', 'Logging.ini')
        else:
            systemDefaultFile = os.path.join(os.path.dirname(sys.modules['GeoEco.Logging'].__file__), 'Configuration', 'Logging.ini')
        systemDefaultFileWarning = None
        if (loggingConfigFile is None or callersFileWarning is not None) and (userDefaultFile is None or userDefaultFileWarning is not None):
            systemDefaultFileWarning = cls._InitializeLoggingFromFile(systemDefaultFile)

        # If all of the above failed, initialize using a hard-coded
        # configuration.

        manualInitializationWarning = None        
        if (loggingConfigFile is None or callersFileWarning is not None) and (userDefaultFile is None or userDefaultFileWarning is not None) and systemDefaultFileWarning is not None:
            try:
                stdout_handler = logging.StreamHandler(sys.stdout)
                stdout_handler.level = logging.INFO
                logging.getLogger('').addHandler(stdout_handler)
                logging.getLogger('').setLevel(logging.INFO)
            except Exception as e:
                manualInitializationWarning = _('Failed to initialize the logging system from hard-coded settings. One of the logging functions reported the error: %s: %s') % (e.__class__.__name__, e)

        # Change the milliseconds delimiter from a comma (Python's default) to
        # a period.

        for h in logging.getLogger().handlers:
            h.formatter.default_msec_format = '%s.%03d'

        # Log warning messages, if any, and a success message. We have to delay of
        # all this until now, because until this point, the logging system may not
        # have been initialized. If we were able to initialize it, we want any
        # warning messages to be logged using the best possible settings.

        if manualInitializationWarning is not None:
            if callersFileWarning is not None:
                print(callersFileWarning)
            if userDefaultFileWarning is not None:
                print(userDefaultFileWarning)
            print(systemDefaultFileWarning)
            print(manualInitializationWarning)
            print(_('The logging system could not be initialized. Log messages will not be reported.'))

        elif loggingConfigFile is not None and callersFileWarning is None:
            cls.Debug(_('Logging system successfully initialized from config file "%s".'), loggingConfigFile)

        elif userDefaultFile is not None and userDefaultFileWarning is None:
            if callersFileWarning is not None:
                cls.Warning(callersFileWarning)
            cls.Debug(_('Logging system successfully initialized from config file "%s".'), userDefaultFile)

        elif systemDefaultFileWarning is None:
            if callersFileWarning is not None:
                cls.Warning(callersFileWarning)
            if userDefaultFileWarning is not None:
                cls.Warning(userDefaultFileWarning)
            cls.Debug(_('Logging system successfully initialized from config file "%s".'), systemDefaultFile)

        elif manualInitializationWarning is None:
            if callersFileWarning is not None:
                cls.Warning(callersFileWarning)
            if userDefaultFileWarning is not None:
                cls.Warning(userDefaultFileWarning)
            cls.Warning(systemDefaultFileWarning)
            cls.Info(_('Log messages will only be sent to the console output (stdout).'))

        # Activate ArcGIS logging if requested.

        if activateArcGISLogging and (loggingConfigFile is not None and callersFileWarning is None or userDefaultFile is not None and userDefaultFileWarning is None or systemDefaultFileWarning is None):
            cls.ActivateArcGISLogging()

    @classmethod
    def ActivateArcGISLogging(cls):
        _ArcGISLoggingHandler.Activate()

    @classmethod
    def _InitializeLoggingFromFile(cls, loggingConfigFile=None):
        assert isinstance(loggingConfigFile, str), 'loggingConfigFile must be a string'

        # Try to open the file for reading, so we know it is accessible.

        try:
            f = open(loggingConfigFile, 'r')
        except Exception as e:
            return(_('Failed to initialize logging from the config file "%(file)s". The file could not be opened. The operating system reported: %(error)s: %(msg)s') % {'file': loggingConfigFile, 'error': e.__class__.__name__, 'msg': e})
        try:
            f.close()
        except:
            pass

        # If that was successful, try to initialize logging.
        #
        # If the logging config file is improperly formatted, the logging
        # initialization function can fail in two ways. First, it may raise an
        # exception. In this case, catch it as usual and return a failure
        # message.
        #
        # In the second failure mode, it simply prints an exception trace to
        # stderr, but does not raise an exception or return a value indicating
        # failure. This would be ok, except that it can leave the logging system
        # in an inconsistent state: subsequent calls to logging functions such
        # as logging.debug() will fail. Again, these failed calls swallow
        # exceptions, just printing their traces to stderr.
        #
        # Because we don't want stderr to be spammed when logging fails to
        # initialize, we detect the failure in the logging configuration
        # function by capturing stderr, and return a failure message.

        cap = _StderrCapturer()
        cap.Start()
        try:
            try:
                # First handle a bug in logging.config.fileConfig that causes the
                # logging Handler class to raise an exception at shutdown. This bug
                # was reported in Aug 2006 and exists in Python 2.4.4 but is
                # supposedly fixed in Python 2.5.
                
                if '_TempHandler' in globals() and globals()['_TempHandler'] is not None:
                    Logger._GeoEcoLogger.removeHandler(globals()['_TempHandler'])
                    globals()['_TempHandler'].close()
                    del globals()['_TempHandler']

                # Now read the config file.
                
                logging.config.fileConfig(loggingConfigFile)
                
            except Exception as e:
                return _('Failed to initialize logging from the config file "%(file)s". Please verify that the contents of the config file are valid. Search the Python documentation for "logging configuration file format". In Python 2.4, the article is titled "6.29.10.2 Configuration file format". Python\'s log configuration file parser (logging.config.fileConfig) reported: %(error)s: %(msg)s') % {'file': loggingConfigFile, 'error': e.__class__.__name__, 'msg': e}
        finally:
            result = cap.Stop()

        if result is not None and len(result.strip()) > 0:
            result_lines = result.strip().split('\n')
            i = 1
            while i < len(result_lines) and (len(result_lines[i]) == 0 or result_lines[i][0] == ' '):
                i = i + 1
            message = ''
            for j in range(i, len(result_lines)):
                message = message + result_lines[j] + '\n'
            message = message.strip()
            return _('Failed to initialize logging from the config file "%s". Please verify that the contents of the config file are valid. Search the Python documentation for "logging configuration file format". In Python 2.4, the article is titled "6.29.10.2 Configuration file format". Python\'s log configuration file parser (logging.config.fileConfig) reported the error: %s') % (loggingConfigFile, message)

        # Return successfully.

        return None


class ProgressReporter(object):    
    __doc__ = DynamicDocString()

    def __init__(self,
                 progressMessage1=_('Progress report: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                 progressMessage2=_('Progress report: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation.'),
                 completionMessage=_('Processing complete: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation.'),
                 abortedMessage=_('Processing stopped before all operations were completed: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation, %(opsIncomplete)i operations not completed.'),
                 loggingChannel='GeoEco',
                 arcGISProgressorLabel=None):

        self.ProgressMessage1 = progressMessage1
        self.ProgressMessage2 = progressMessage2
        self.CompletionMessage = completionMessage
        self.AbortedMessage = abortedMessage
        self.LoggingChannel = loggingChannel
        self._ArcGISProgressorLabel = arcGISProgressorLabel
        self._TotalOperations = None
        self._OperationsCompleted = 0
        self._TimeStarted = None
        self._TimeCompleted = None
        self._ClockStarted = None
        self._ClockNextReportTime = None
        self._TimeFirstOpCompleted = None

    def _GetProgressMessage1(self):
        return self._ProgressMessage1

    def _SetProgressMessage1(self, value):
        assert isinstance(value, (type(None), str)), 'ProgressMessage1 must be a string, or None.'
        self._ProgressMessage1 = value
    
    ProgressMessage1 = property(_GetProgressMessage1, _SetProgressMessage1, doc=DynamicDocString())

    def _GetProgressMessage2(self):
        return self._ProgressMessage2

    def _SetProgressMessage2(self, value):
        assert isinstance(value, (type(None), str)), 'ProgressMessage2 must be a string, or None.'
        self._ProgressMessage2 = value
    
    ProgressMessage2 = property(_GetProgressMessage2, _SetProgressMessage2, doc=DynamicDocString())

    def _GetCompletionMessage(self):
        return self._CompletionMessage

    def _SetCompletionMessage(self, value):
        assert isinstance(value, (type(None), str)), 'CompletionMessage must be a string, or None.'
        self._CompletionMessage = value
    
    CompletionMessage = property(_GetCompletionMessage, _SetCompletionMessage, doc=DynamicDocString())

    def _GetAbortedMessage(self):
        return self._AbortedMessage

    def _SetAbortedMessage(self, value):
        assert isinstance(value, (type(None), str)), 'AbortedMessage must be a string, or None.'
        self._AbortedMessage = value
    
    AbortedMessage = property(_GetAbortedMessage, _SetAbortedMessage, doc=DynamicDocString())

    def _GetArcGISProgressorLabel(self):
        return self._ArcGISProgressorLabel
    
    ArcGISProgressorLabel = property(_GetArcGISProgressorLabel, None, doc=DynamicDocString())

    def _UseArcGISProgressor(self):
        from .ArcGIS import GeoprocessorManager
        return self._TotalOperations is not None and self.ArcGISProgressorLabel is not None and GeoprocessorManager.GetGeoprocessor() is not None

    def _GetLoggingChannel(self):
        return self._LoggingChannel

    def _SetLoggingChannel(self, value):
        assert isinstance(value, (type(None), str)), 'LoggingChannel must be a string, or None.'
        self._LoggingChannel = value
    
    LoggingChannel = property(_GetLoggingChannel, _SetLoggingChannel, doc=DynamicDocString())

    def _GetTotalOperations(self):
        return self._TotalOperations

    def _SetTotalOperations(self, value):
        assert value is None or (isinstance(value, int) and value >= 0), 'totalOperations must be a non-negative integer, or None'

        if value is not None:
            self._TotalOperations = int(value)      # Explicitly cast to int, in case the caller passes in a numpy.int32 or similar numpy type
        else:
            self._TotalOperations = None

        if self._UseArcGISProgressor():
            from .ArcGIS import GeoprocessorManager
            gp = GeoprocessorManager.GetGeoprocessor()
            if self.HasStarted:
                try:
                    gp.ResetProgressor()
                except:
                    pass
            try:
                gp.SetProgressor('step', self.ArcGISProgressorLabel, 0, 1000, 1)
                if self.HasStarted:
                    gp.SetProgressorPosition(min(1000, int(math.floor(float(self._OperationsCompleted) / float(self._TotalOperations) * 1000.))))
            except:
                pass
        
        if self._TotalOperations is not None and self.HasStarted and self._OperationsCompleted >= self._TotalOperations:
            self.Stop()
    
    TotalOperations = property(_GetTotalOperations, _SetTotalOperations, doc=DynamicDocString())

    def _GetOperationsCompleted(self):
        return self._OperationsCompleted
    
    OperationsCompleted = property(_GetOperationsCompleted, doc=DynamicDocString())

    def _GetTimeStarted(self):
        return self._TimeStarted
    
    TimeStarted = property(_GetTimeStarted, doc=DynamicDocString())

    def _GetTimeCompleted(self):
        return self._TimeCompleted
    
    TimeCompleted = property(_GetTimeCompleted, doc=DynamicDocString())

    def _GetHasStarted(self):
        return self._TimeStarted is not None
    
    HasStarted = property(_GetHasStarted, doc=DynamicDocString())

    def _GetHasCompleted(self):
        return self._TimeCompleted is not None
    
    HasCompleted = property(_GetHasCompleted, doc=DynamicDocString())

    def _GetTimeElapsed(self):
        if self._TimeStarted is None:
            return None
        if self._TimeCompleted is None:
            return datetime.timedelta(seconds = time.perf_counter() - self._ClockStarted)
        return self._TimeCompleted - self._TimeStarted

    TimeElapsed = property(_GetTimeElapsed, doc=DynamicDocString())

    def Start(self, totalOperations=None):
        assert not self.HasStarted, 'This ProgressReporter was already started and cannot be started a second time'
        
        self.TotalOperations = totalOperations
        self._OperationsCompleted = 0
        self._TimeStarted = datetime.datetime.now()
        self._ClockStarted = time.perf_counter()
        self._ClockNextReportTime = self._ClockStarted + 60.0

        if totalOperations == 0:
            self.Stop()

    def ReportProgress(self, operationsCompleted=1, reinitializeArcGISProgressor=False):
        assert self.HasStarted, 'This ProgressReporter has not been started'
        
        self._OperationsCompleted += int(operationsCompleted)       # Explicitly cast to int, in case the caller passes in a numpy.int32 or similar numpy type
        if self._OperationsCompleted <= 0:
            return
        
        if self._TotalOperations is not None and self._OperationsCompleted >= self._TotalOperations:
            self.Stop()
            return
        
        clockNow = time.perf_counter()
        if clockNow >= self._ClockNextReportTime:
            timeElapsed = self.TimeElapsed
            timePerOp = timeElapsed / self._OperationsCompleted

            if self._TotalOperations is not None:
                if self._ProgressMessage1 is not None:

                    # If the first operation took a really long time,
                    # the following operations might go much faster
                    # (e.g. the first operation might require
                    # downloading a file and subsequent operations
                    # would reuse the downloaded file). So if this is
                    # the first operation, do not estimate the
                    # completion time.
                    
                    if self._OperationsCompleted == 1:
                        self._TimeFirstOpCompleted = clockNow
                        etc = _('unknown; more progress needed')
                    else:

                        # This is the second or subsequent operation.
                        # If the first operation took a really long
                        # time, estimate the completion time, ignore
                        # it when estimating the completion time.
                        
                        now = datetime.datetime.now()
                        if self._TimeFirstOpCompleted is not None:
                            timeOfCompletion = now + datetime.timedelta(seconds = clockNow - self._TimeFirstOpCompleted) / (self._OperationsCompleted - 1) * (self._TotalOperations - self._OperationsCompleted - 1)
                        else:
                            timeOfCompletion = now + timePerOp * (self._TotalOperations - self._OperationsCompleted)

                        if now.day == timeOfCompletion.day:
                            etc = timeOfCompletion.strftime('%X')
                        else:
                            etc = timeOfCompletion.strftime('%c')

                    self._Log(self._FormatProgressMessage1(timeElapsed, self._OperationsCompleted, timePerOp, self._TotalOperations - self._OperationsCompleted, etc))

            elif self._ProgressMessage2 is not None:
                self._Log(self._FormatProgressMessage2(timeElapsed, self._OperationsCompleted, timePerOp))

            # If the first operation took a really long time, report
            # again after 60 seconds rather than 300.

            if self._TimeFirstOpCompleted is None or self._OperationsCompleted > 1:
                self._ClockNextReportTime = clockNow + 300.0
            else:
                self._ClockNextReportTime = clockNow + 60.0

        if self._UseArcGISProgressor() and (reinitializeArcGISProgressor or int(math.floor(float(self._OperationsCompleted) / float(self._TotalOperations) * 1000.)) > int(math.floor(float(self._OperationsCompleted - 1) / float(self._TotalOperations) * 1000.))):
            from .ArcGIS import GeoprocessorManager
            gp = GeoprocessorManager.GetGeoprocessor()
            try:
                if reinitializeArcGISProgressor:
                    gp.SetProgressor('step', self.ArcGISProgressorLabel, 0, 1000, 1)
                gp.SetProgressorPosition(min(1000, int(math.floor(float(self._OperationsCompleted) / float(self._TotalOperations) * 1000.))))
            except:
                pass

    def Stop(self):
        assert self.HasStarted, 'This ProgressReporter has not been started'
        if self.HasCompleted:
            return
        
        self._TimeCompleted = datetime.datetime.now()
        timeElapsed = self.TimeElapsed
        if self._OperationsCompleted > 0:
            timePerOp = timeElapsed / self._OperationsCompleted
        else:
            timePerOp = datetime.timedelta()
        if self._TotalOperations is None or self._OperationsCompleted >= self._TotalOperations:
            if self._CompletionMessage is not None:
                self._Log(self._FormatCompletionMessage(timeElapsed, self._OperationsCompleted, timePerOp))
        elif self._AbortedMessage is not None:
            self._Log(self._FormatAbortedMessage(timeElapsed, self._OperationsCompleted, timePerOp, self._TotalOperations - self._OperationsCompleted))

        if self._UseArcGISProgressor():
            from .ArcGIS import GeoprocessorManager
            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            try:
                gp.ResetProgressor()
            except:
                pass

    def _Log(self, message):
        try:
            if self._LoggingChannel == 'GeoEco':
                Logger.Info(message)
            else:
                logging.getLogger(self._LoggingChannel).info(message)
        except:
            pass

    # Private methods intended to be overridden by derived classes
    # that need to do custom formatting of the progress messages.

    def _FormatProgressMessage1(self, timeElapsed, opsCompleted, timePerOp, opsRemaining, estimatedTimeOfCompletionString):
        return self._ProgressMessage1 % {'elapsed' : datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds), 'opsCompleted': opsCompleted, 'perOp': timePerOp, 'opsRemaining': opsRemaining, 'etc': estimatedTimeOfCompletionString}

    def _FormatProgressMessage2(self, timeElapsed, opsCompleted, timePerOp):
        return self._ProgressMessage2 % {'elapsed' : datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds), 'opsCompleted': opsCompleted, 'perOp': timePerOp}

    def _FormatCompletionMessage(self, timeElapsed, opsCompleted, timePerOp):
        return self._CompletionMessage % {'elapsed' : datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds), 'opsCompleted': opsCompleted, 'perOp': timePerOp}

    def _FormatAbortedMessage(self, timeElapsed, opsCompleted, timePerOp, opsIncomplete):
        return self._AbortedMessage % {'elapsed' : datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds), 'opsCompleted': opsCompleted, 'perOp': timePerOp, 'opsIncomplete': opsIncomplete}


# Private classes and functions global to this module

class _ArcGISLoggingHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)

    def emit(self, record):
        if self.__class__._Instance != self:
            self.__class__._Instance = self
        if not isinstance(record, logging.LogRecord):
            return
        try:
            if self.__class__._PreactivationQueue is not None:
                if len(self.__class__._PreactivationQueue) == 1000:
                    del self.__class__._PreactivationQueue[0]
                self.__class__._PreactivationQueue.append(record)
            else:
                self._Emit(record)
        except:
            pass

    def _Emit(self, record):
        try:
            from .ArcGIS import GeoprocessorManager
            message = self.format(record)
            if record.levelno >= logging.ERROR:
                GeoprocessorManager.GetGeoprocessor().AddError(message)
            elif record.levelno >= logging.WARNING:
                GeoprocessorManager.GetGeoprocessor().AddWarning(message)
            else:
                GeoprocessorManager.GetGeoprocessor().AddMessage(message)
        except:
            pass

    @classmethod
    def GetInstance(cls):
        return _ArcGISLoggingHandler._Instance

    @classmethod
    def Activate(cls):
        if cls._PreactivationQueue is not None:
            from .ArcGIS import GeoprocessorManager
            if GeoprocessorManager.GetGeoprocessor() is None:
                GeoprocessorManager.InitializeGeoprocessor()
            while len(cls._PreactivationQueue) > 0:
                record = cls._PreactivationQueue.pop(0)
                cls._Instance._Emit(record)
                del record
            cls._PreactivationQueue = None

    _Instance = None
    _PreactivationQueue = []


class _GeoEcoStreamHandler(logging.StreamHandler):

    def __init__(self, strm=None):
        logging.StreamHandler.__init__(self, strm)

    def emit(self, record):
        if not _GeoEcoStreamHandler._Deactivated:
            logging.StreamHandler.emit(self, record)

    @classmethod
    def Deactivate(cls):
        _GeoEcoStreamHandler._Deactivated = True

    _Deactivated = False


class _StderrCapturer(object):

    def __init__(self):
        self._Buffer = None
        self._OriginalStderr = None

    def Start(self):
        if self._OriginalStderr is None:
            self._Buffer = None
            self._OriginalStderr = sys.stderr
            sys.stderr = self

    def write(self, obj):
        if self._OriginalStderr is not None:
            if self._Buffer is None:
                self._Buffer = obj
            else:
                self._Buffer = self._Buffer + obj

    def Stop(self):
        if self._OriginalStderr is not None:
            sys.stderr = self._OriginalStderr
            self._OriginalStderr = None
            return self._Buffer
        else:
            return None


# Initialize, but do not activate, the ArcGIS logging handler. Until the
# handler is activated by an external caller (by calling
# GeoEco.Logging.ActivateArcGISLogging) the handler will just queue log
# messages in memory. Then, when it is activated, it will dump the queue to
# ArcGIS. This ensures that all log messages are reported to the ArcGIS UI
# when GeoEco is used from an Arc geoprocessing script, even those generated
# before the Activate call is made.

_TempHandler = None         # This is required to address in Python's logging.config.fileConfig function: it calls logging._handlers.clear() but does not also remove the handlers from logging._handlerList
try:
    if _ArcGISLoggingHandler.GetInstance() is None:         # I'm fairly sure this will always return None, since nobody can instantiate _ArcGISLoggingHandler without importing the module first, causing the code below to execute first.
        _TempHandler = _ArcGISLoggingHandler(logging.INFO)
        _logger = logging.getLogger('GeoEco')
        if _logger is not None:
            _logger.addHandler(_TempHandler)
        del _logger
except:
    pass


###############################################################################
# Metadata: module
###############################################################################

from .Metadata import *
from .Types import *

AddModuleMetadata(shortDescription=_('Classes and functions that the GeoEco package uses to report activity to the user.'))

###############################################################################
# Metadata: Logger class
###############################################################################

AddClassMetadata(Logger,
    shortDescription=_('Provides functions for reporting messages to the user from the GeoEco package.'),
    longDescription=(
"""This class wraps the Python :mod:`logging` module. Callers outside of the
GeoEco package may use this class but we recommend they use :mod:`logging`
directly instead.

This class logs all messages to the ``GeoEco`` logging channel. Parts of the
GeoEco package log to other channels. To see what these are, consult the file
``GeoEco/Configuration/Logging.ini``.

Note:
    Do not instantiate this class. It is a collection of classmethods intended
    to be invoked on the class rather than an instance of it, like this:

    .. code-block:: python

        from GeoEco.Logging import Logger

        Logger.Info('Hello, world!')
"""))

# Public method: Debug

AddMethodMetadata(Logger.Debug,
    shortDescription=_('Reports a debugging message to the user.'),
    longDescription=_(
"""Like the C printf function or the Python % operator, this method generates a
message string by merging in the optional arguments into the format string.

Debugging messages describe processing details that are usually not interesting
unless the user is diagnosing a problem. The default configuration of the
logging system causes debugging messages to be discarded."""))

AddArgumentMetadata(Logger.Debug, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=_(':class:`%s` or an instance of it.') % Logger.__name__)

AddArgumentMetadata(Logger.Debug, 'format',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""A :ref:`printf-style format string <python:old-string-formatting>`."""))

AddArgumentMetadata(Logger.Debug, 'args',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True)),
    description=_('Values to merge into the format string.'))

# Public method: Info

AddMethodMetadata(Logger.Info,
    shortDescription=_('Reports an informational message to the user.'),
    longDescription=_(
"""Like the C printf function or the Python % operator, this method generates a
message string by merging in the optional arguments into the format string.

Informational messages describe major processing steps that may be interesting to
the user but do not require the user to take any action. For example, a method
that performs three major processing tasks might report an informational message
after each step is finished. Do not report too many informational messages or
you may overwhelm the user. Report processing details as debug messages."""))

AddArgumentMetadata(Logger.Info, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.Info, 'format',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=Logger.Debug.__doc__.Obj.Arguments[1].Description)

AddArgumentMetadata(Logger.Info, 'args',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True)),
    description=Logger.Debug.__doc__.Obj.Arguments[2].Description)

# Public method: Warning

AddMethodMetadata(Logger.Warning,
    shortDescription=_('Reports a warning message to the user.'),
    longDescription=_(
"""Like the C printf function or the Python % operator, this method generates a
message string by merging in the optional arguments into the format string.

Warning messages describe important events that should be brought to the user's
attention but do not necessarily indicate that processing will fail. To draw the
user's attention, ArcGIS highlights warning messages in green in its user
interface.

Note:
    Do not call this method to report exceptions caught inside methods of
    GeoEco classes. Call :func:`LogExceptionAsWarning` instead.
"""))

AddArgumentMetadata(Logger.Warning, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.Warning, 'format',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=Logger.Debug.__doc__.Obj.Arguments[1].Description)

AddArgumentMetadata(Logger.Warning, 'args',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True)),
    description=Logger.Debug.__doc__.Obj.Arguments[2].Description)

# Public method: Error

AddMethodMetadata(Logger.Error,
    shortDescription=_('Reports an error message to the user.'),
    longDescription=_(
"""Like the C printf function or the Python % operator, this method generates a
message string by merging in the optional arguments into the format string.

Error messages describe failures that halt processing and require the user to
fix a problem and restart processing. ArcGIS highlights error messages in red in
its user interface, and fails geoprocessing if even one error is reported.
Because of this, do not report error messages unless the problem is serious
enough to stop processing. For problems that may or may not be of consequence to
the user, report warning messages.

If :func:`SetLogErrorsAsWarnings` has been called with :py:data:`True`, the
message will be reported as a warning rather than an error.

Note:
    Do not call this method to report exceptions caught inside methods of
    GeoEco classes. Call :func:`LogExceptionAsError` instead.
"""))

AddArgumentMetadata(Logger.Error, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.Error, 'format',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=Logger.Debug.__doc__.Obj.Arguments[1].Description)

AddArgumentMetadata(Logger.Error, 'args',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True)),
    description=Logger.Debug.__doc__.Obj.Arguments[2].Description)

# Public method: GetLogInfoAsDebug

AddMethodMetadata(Logger.GetLogInfoAsDebug,
    shortDescription=_('Returns True if informational messages are currently set to be logged as debug messages. See :func:`SetLogInfoAsDebug`.'))

AddArgumentMetadata(Logger.GetLogInfoAsDebug, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddResultMetadata(Logger.GetLogInfoAsDebug, 'logInfoAsDebug',
    typeMetadata=BooleanTypeMetadata(),
    description=_('True if informational messages are currently set to be logged as debug messages. False, if informational messages are set to be logged as informational.'))

# Public method: SetLogInfoAsDebug

AddMethodMetadata(Logger.SetLogInfoAsDebug,
    shortDescription=_('Enable or disable the logging of informational messages as debug messages.'),
    longDescription=_(
"""Informational messages describe major processing steps that may be
interesting to the user but do not require the user to take any action. For
example, a function that performs three major processing tasks might report an
informational message after each step is finished.

Sometimes your function may repeatedly call another function to accomplish some
processing that you consider to be relatively unimportant. For example, your
function may copy a bunch of files, and you might want to inform the user that
you are performing the copying but do not want to inform them about every
file. To avoid overwhelming the user with informational messages, you can force
them to be logged as debug messages like this:

.. code-block:: python

    oldValue = Logger.SetLogInfoAsDebug(True)
    try:
        # Do your work here
    finally:
        Logger.SetLogInfoAsDebug(oldValue)
"""))

AddArgumentMetadata(Logger.SetLogInfoAsDebug, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.SetLogInfoAsDebug, 'logInfoAsDebug',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, informational messages will now be logged as debug messages. If False, informational messages will be logged as informational.'))

AddResultMetadata(Logger.SetLogInfoAsDebug, 'oldLogInfoAsDebug',
    typeMetadata=BooleanTypeMetadata(),
    description=_('Value of `logInfoAsDebug` prior to this function being called. Capture this if you want to call :func:`SetLogInfoAsDebug` again to restore the old value.'))

# Public method: GetLogErrorsAsWarnings

AddMethodMetadata(Logger.GetLogErrorsAsWarnings,
    shortDescription=_('Returns True if errors are currently set to be logged as warnings. See :func:`SetLogErrorsAsWarnings`.'))

AddArgumentMetadata(Logger.GetLogErrorsAsWarnings, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddResultMetadata(Logger.GetLogErrorsAsWarnings, 'logErrorsAsWarnings',
    typeMetadata=BooleanTypeMetadata(),
    description=_('True if errors are currently set to be logged as warnings. False, if errors are set to be logged as errors.'))

# Public method: SetLogErrorsAsWarnings

AddMethodMetadata(Logger.SetLogErrorsAsWarnings,
    shortDescription=_('Enable or disable the logging of errors as warnings.'),
    longDescription=_(
"""Error messages describe failures that halt processing and require the user
to fix a problem and restart processing. ArcGIS highlights error messages in
red in its user interface, and fails geoprocessing if even one error is
reported.

Sometimes you don't want to halt processing when an unimportant operation
fails. For example, you may not care that a temporary file could not be
deleted. To prevent that unimportant failure from being logged as an error and
potentially stopping processing, you can force errors to be logged as warnings
like this:

.. code-block:: python

    oldValue = Logger.SetLogErrorsAsWarnings(True)
    try:
        # Do your work here
    finally:
        Logger.SetLogErrorsAsWarnings(oldValue)
"""))

AddArgumentMetadata(Logger.SetLogErrorsAsWarnings, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.SetLogErrorsAsWarnings, 'logErrorsAsWarnings',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, errors will now be logged as warnings. If False, errors will be logged as errors.'))

AddResultMetadata(Logger.SetLogErrorsAsWarnings, 'oldLogErrorsAsWarnings',
    typeMetadata=BooleanTypeMetadata(),
    description=_('Value of `logErrorsAsWarnings` prior to this function being called. Capture this if you want to call :func:`SetLogErrorsAsWarnings` again to restore the old value.'))

# Public method: LogInfoAndSetInfoToDebug

AddMethodMetadata(Logger.LogInfoAndSetInfoToDebug,
    shortDescription=_('Reports an informational message and then calls ``Logger.LogInfoAsDebug(True)`` and returns its value.'),
    longDescription=_(
"""This function is used to efficiently implement a common logging
scenario: a function wants to log one informational message announcing
the processing it is doing and report everything else as debug
messages, including informational messages reported by nested
functions. The Python pattern for implementing this scenario is:

.. code-block:: python

    from GeoEco.Logging import Logger

    def MyFunc(...):
        oldValue = Logger.LogInfoAndSetInfoToDebug('Doing my processing...')
        try:
            # Do your work here
        finally:
            Logger.SetLogInfoAsDebug(oldValue)
"""))

CopyArgumentMetadata(Logger.Info, 'cls', Logger.LogInfoAndSetInfoToDebug, 'cls')
CopyArgumentMetadata(Logger.Info, 'format', Logger.LogInfoAndSetInfoToDebug, 'format')
CopyArgumentMetadata(Logger.Info, 'args', Logger.LogInfoAndSetInfoToDebug, 'args')

AddResultMetadata(Logger.LogInfoAndSetInfoToDebug, 'oldLogInfoAsDebug',
    typeMetadata=BooleanTypeMetadata(),
    description=_("""The value returned by :func:`LogInfoAsDebug`, indicating whether or not informational messages were being logged as debug messages prior to this call."""))

# Public method: RaiseException

AddMethodMetadata(Logger.RaiseException,
    shortDescription=_('Raises a Python exception and logs it as an error message and additional information as debug messages.'),
    longDescription=_(
"""Rather than raising excpetions with the Python ``raise`` statement, code in
the GeoEco package can use :func:`RaiseException` instead. This method will
raise the exception, log it as an error (or warning, if
:func:`SetLogErrorsAsWarnings` has been called with :py:data:`True`), and also
log a bunch of debugging information as debug messages."""))

AddArgumentMetadata(Logger.RaiseException, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.RaiseException, 'exception',
    typeMetadata=ClassInstanceTypeMetadata(cls=Exception),
    description=_('The Python exception instance to raise.'))

# Public method: LogExceptionAsWarning

AddMethodMetadata(Logger.LogExceptionAsWarning,
    shortDescription=_('Logs a Python exception caught by a GeoEco class as a warning message and additional information as debug messages.'),
    longDescription=_(
"""GeoEco classes should use :func:`LogExceptionAsWarning` or
:func:`LogExceptionAsError` to report exceptions caught by except clauses of
try statements, like this:

.. code-block:: python

    Logger.Debug(_(u'Copying file %s to %s.') % (sourceFile, destinationFile))
    try:
        shutil.copy2(sourceFile, destinationFile)
    except:
        Logger.LogExceptionAsError(_(u'Could not copy file %(source)s to %(dest)s.') % \\
                                   {u'source' :  sourceFile, u'dest' : destinationFile})
        raise

As shown, the except clause should re-raise the exception (if appropriate)
using a raise statement with no parameters. :func:`LogExceptionAsWarning` and
:func:`LogExceptionAsError` will log the exception and some debugging information,
including a stack trace. If the caller provides the optional format string, it
is logged as a "consequence" of the original error. For example the code above
produces the following output when the caller does not have permission to write
the destination file::

    DEBUG Copying file c:\\foo.txt to c:\\bar.txt.
    ERROR IOError: [Errno 13] Permission denied: u'c:\\\\bar.txt'
    DEBUG ---------- BEGINNING OF DEBUGGING INFORMATION ----------
    DEBUG Traceback (most recent call last):
    DEBUG   File "<stdin>", line 1, in ?
    DEBUG   File "<stdin>", line 2, in tryit
    DEBUG   File "C:\\Python24\\Lib\\site-packages\\GeoEco\\FileSystemUtils.py", line 47, in CopyFile
    DEBUG     shutil.copy2(sourceFile, destinationFile)
    DEBUG   File "C:\\Python24\\lib\\shutil.py", line 92, in copy2
    DEBUG     copyfile(src, dst)
    DEBUG   File "C:\\Python24\\lib\\shutil.py", line 48, in copyfile
    DEBUG     fdst = open(dst, 'wb')
    DEBUG IOError: [Errno 13] Permission denied: u'c:\\\\bar.txt'
    DEBUG End of traceback. Logging other useful debugging information...
    DEBUG sys.argv = ['']
    DEBUG sys.version = 2.4.4 (#71, Oct 18 2006, 08:34:43) [MSC v.1310 32 bit (Intel)]
    DEBUG sys.version_info = (2, 4, 4, 'final', 0)
    DEBUG sys.platform = win32
    DEBUG sys.getwindowsversion() = (5, 1, 2600, 2, 'Service Pack 2')
    DEBUG ...
    DEBUG ---------- END OF DEBUGGING INFORMATION ----------
    ERROR The following consequences resulted from the original error:
    ERROR Could not copy file c:\\foo.txt to c:\\bar.txt.

Unless the user has debugging messages turned on, they will only see the warning
and error messages in the log::

    ERROR IOError: [Errno 13] Permission denied: u'c:\\\\bar.txt'
    ERROR The following consequences resulted from the original error:
    ERROR Could not copy file c:\\foo.txt to c:\\bar2\\bar.txt.

Except clauses higher on the stack can also call :func:`LogExceptionAsWarning`
and :func:`LogExceptionAsError`. The methods keep track of whether the
original exception was logged and will not log it a second time. Instead they
will just log the optional format string, if provided, as a subsequent
"consequence" of the original exception. This allows nested methods to
illustrate how the low-level failure causes a problem in the high-level
operation the user actually cares about. For example, if the output file from
a function cannot be copied from a temporary location because a directory
cannot be created, the log might look like this::

    ERROR IOError: [Errno 13] Permission denied: u'c:\\\\output'
    ERROR The following consequences resulted from the original error:
    ERROR Could create directory c:\\output.
    ERROR Could not copy file c:\\processing\\results.txt to c:\\output\\results.txt.
    ERROR Could not copy the results to the output directory."""))

AddArgumentMetadata(Logger.LogExceptionAsWarning, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.LogExceptionAsWarning, 'format',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Logger.Debug.__doc__.Obj.Arguments[1].Description)

AddArgumentMetadata(Logger.LogExceptionAsWarning, 'args',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True)),
    description=Logger.Debug.__doc__.Obj.Arguments[2].Description)

# Public method: LogExceptionAsError

AddMethodMetadata(Logger.LogExceptionAsError,
    shortDescription=_('Logs a Python exception caught by a GeoEco class as an error message and additional information as debug messages.'),
    longDescription=Logger.LogExceptionAsWarning.__doc__.Obj.LongDescription)

AddArgumentMetadata(Logger.LogExceptionAsError, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.LogExceptionAsWarning.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.LogExceptionAsError, 'format',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Logger.LogExceptionAsWarning.__doc__.Obj.Arguments[1].Description)

AddArgumentMetadata(Logger.LogExceptionAsError, 'args',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True)),
    description=Logger.LogExceptionAsWarning.__doc__.Obj.Arguments[2].Description)

# Public method: Initialize

AddMethodMetadata(Logger.Initialize,
    shortDescription=_('Initializes the logging system.'))

AddArgumentMetadata(Logger.Initialize, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

AddArgumentMetadata(Logger.Initialize, 'activateArcGISLogging',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If true, logging messages will be delivered to the ArcGIS geoprocessing
system and appear in the ArcGIS user interface. If false, they will be reported
to other logging destinations but will be queued in memory for ArcGIS until the
:func:`ActivateArcGISLogging` method is called. To limit memory consumption in
the event that the method is never called, the queue retains only the most
recent 1000 messages. If you are calling :func:`Initialize` but not running as
part of an ArcGIS geoprocessing *do not* pass True for this parameter. Passing
True will decrease performance by initializing the ArcGIS geoprocessor when it
might not be necessary to do so. (The memory used by the queue is
negligible.)"""))

AddArgumentMetadata(Logger.Initialize, 'loggingConfigFile',
    typeMetadata=FileTypeMetadata(canBeNone=True, mustExist=True),
    description=_(
"""Path to the logging configuration file. If not provided, this function
first attempts to load a configuration file from a user-specific location that
depends on the operating system:

* On Microsoft Windows: ``%APPDATA%\\GeoEco\\Logging.ini`` (e.g.
  ``C:\\Users\\Jason\\AppData\\Roaming\\GeoEco\\Logging.ini``.)

* On Linux: ``~/.config/GeoEco/Logging.ini``. The location of ``~/.config``
  can be overridden with the ``XDG_CONFIG_HOME`` environment variable.

If the user-specific file does not exist or fails to be loaded, a system-wide
location will be tried:

* On Microsoft Windows: ``GeoEco\\Configuration\\Logging.ini`` in the
  ``site-packages`` directory of the Python installation. This file is created
  when GeoEco is installed.

* On Linux: ``/etc/GeoEco/Logging.ini``, if it exists. It is not created there
  when GeoEco is installed, and if an administrator has not created it, then
  ``GeoEco\\Configuration\\Logging.ini`` in the ``site-packages``
  directory of the Python installation will be used instead. This file is
  created when GeoEco is installed.

If neither is found (which would only occur if the GeoEco package installation
is corrupt), then all informational, warning, and error messages will be
logged to the console (i.e. the stdout stream)."""))

# Public method: ActivateArcGISLogging

AddMethodMetadata(Logger.ActivateArcGISLogging,
    shortDescription=_('Instructs :class:`Logger` to stop queuing messages destined for ArcGIS and release any that are currently queued up.'),
    longDescription=_(
"""This method is intended to be called only by the GeoEco package itself,
from code that wraps GeoEco Python functions and exposes them as ArcGIS
geoprocessing tools."""))

AddArgumentMetadata(Logger.ActivateArcGISLogging, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Logger),
    description=Logger.Debug.__doc__.Obj.Arguments[0].Description)

###############################################################################
# Metadata: ProgressReporter class
###############################################################################

AddClassMetadata(ProgressReporter,
    shortDescription=_('Provides a simple mechanism to periodically report progress to the user during iterative operations.'),
    longDescription=_(
"""This class provides progress-reporting capability for two kinds of
iterative operations: those for which the total number of iterations is known
when the operation is started, and those for which the total number of
iterations cannot be determined. In both cases, this class periodically
reports the elapsed time, the number of iterations completed, and the
average time per iteration. If the number of iterations is known, this
class also reports the number of iterations remaining and the estimated
time of completion.

When the total number of iterations is known, use this pattern:

.. code-block:: python

    operations = [...]                          # List of operations to perform
    progressReporter = ProgressReporter()
    progressReporter.Start(len(operations))
    for op in operations:
        ...                                     # Do one operation
        progressReporter.ReportProgress()

But when the total number of iterations is not known, use this pattern:

.. code-block:: python

    progressReporter = ProgressReporter()
    progressReporter.Start()
    while True:
        ...                                     # Do one operation or exit loop if done
        progressReporter.ReportProgress()
    progressReporter.Stop()

:func:`ReportProgress` will report the first message after one minute and an
additional message every five minutes thereafter. A message will also be
reported when processing is complete, by :func:`ReportProgress` in the first
scenario and :func:`Stop` in the second scenario. You can configure the format
of the progress messages by setting :attr:`ProgressMessage1`,
:attr:`ProgressMessage2`, and :attr:`CompletionMessage`. All messages are
reported as Informational log messages. You can configure the logging channel
that is used to report the messages by setting :attr:`LoggingChannel`."""))

# Public properties

AddPropertyMetadata(ProgressReporter.ProgressMessage1,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_(':ref:`printf-style format string <python:old-string-formatting>` for periodically reporting progress when the total number of iterations is known a priori.'),
    longDescription=_(
"""Your string must include all five format specifiers, as in this example:

.. code-block:: python

    'Progress report: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'

"""))

AddPropertyMetadata(ProgressReporter.ProgressMessage2,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_(':ref:`printf-style format string <python:old-string-formatting>` for periodically reporting progress when the total number of iterations is not known a priori.'),
    longDescription=_(
"""Your string must include all three format specifiers, as in this example:

.. code-block:: python

    'Progress report: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation.'

"""))

AddPropertyMetadata(ProgressReporter.CompletionMessage,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_(':ref:`printf-style format string <python:old-string-formatting>` for reporting that processing is complete.'),
    longDescription=_(
"""Your string must include all three format specifiers, as in this example:

.. code-block:: python

    'Processing complete: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation.'

"""))

AddPropertyMetadata(ProgressReporter.AbortedMessage,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_(':ref:`printf-style format string <python:old-string-formatting>` for reporting that processing was stopped prematurely (i.e. that :func:`Stop` was called before :attr:`OperationsCompleted` == :attr:`TotalOperations`).'),
    longDescription=_(
"""Your string must include all four format specifiers, as in this example:

.. code-block:: python

    'Processing stopped before all operations were completed: %(elapsed)s elapsed, %(opsCompleted)i operations completed, %(perOp)s per operation, %(opsIncomplete)i operations not completed.'

"""))

AddPropertyMetadata(ProgressReporter.LoggingChannel,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Logging channel that progress messages should be reported to.'),
    longDescription=_(
"""Please see the documentation for the Python :mod:`logging` module for more
information about logging channels. All progress messages are reported at the
Info logging level."""))

AddPropertyMetadata(ProgressReporter.ArcGISProgressorLabel,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    shortDescription=_('Label to use for the ArcGIS geoprocessor progressor.'),
    longDescription=_(
"""If this property is not :py:data:`None` and :func:`Start` is called with a
total number of operations, the value of this property will be used as the
progressor label (the text that appears above the progress bar) and the
:class:`ProgressReporter` instance will automatically call the geoprocessor's
:arcpy:`SetProgressorPosition` function when :func:`ReportProgress` is called.

If this property is :py:data:`None` or :func:`Start` is called without a total
number of operations, the :class:`ProgressReporter` instance will not
manipulate the geoprocessor's progress bar."""))

AddPropertyMetadata(ProgressReporter.TotalOperations,
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    shortDescription=_('Total number of iterations in this iterative operation, or :py:data:`None` if the number of iterations is not known a priori.'),
    longDescription=_('This property is initialized by the :func:`Start` method.'))

AddPropertyMetadata(ProgressReporter.OperationsCompleted,
    typeMetadata=IntegerTypeMetadata(),
    shortDescription=_('Total number of iterations that have been completed so far.'),
    longDescription=_('This property is updated when :func:`ReportProgress` is called.'))

AddPropertyMetadata(ProgressReporter.TimeStarted,
    typeMetadata=ClassInstanceTypeMetadata(cls=datetime.datetime, canBeNone=True),
    shortDescription=_('The time processing was started.'),
    longDescription=_(
"""This property is set to the current system time when :func:`Start` is
called, using the :py:meth:`datetime.datetime.now` method."""))

AddPropertyMetadata(ProgressReporter.TimeCompleted,
    typeMetadata=ClassInstanceTypeMetadata(cls=datetime.datetime, canBeNone=True),
    shortDescription=_('The time processing was completed.'),
    longDescription=_(
"""This property is set to the current system time when
:func:`ReportProgress` is called for the last iteration (when the total
number of iterations is known a priori) or when :func:`Stop` is called (when
the the total number of iterations is not known a priori), using the
:py:meth:`datetime.datetime.now` method."""))

AddPropertyMetadata(ProgressReporter.HasStarted,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if processing has started (i.e. if :func:`Start` was called).'))

AddPropertyMetadata(ProgressReporter.HasCompleted,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if processing has completed (i.e. the last operation was reported to :func:`ReportProgress` or :func:`Stop` was called).'))

AddPropertyMetadata(ProgressReporter.TimeElapsed,
    typeMetadata=ClassInstanceTypeMetadata(cls=datetime.timedelta, canBeNone=True),
    shortDescription=_('The time elapsed since processing was started, or :py:data:`None` if processing has not started yet.'),
    longDescription=_(
"""Processing starts when :func:`Start` is called and stops when
:func:`ReportProgress` is called for the last iteration (when the total
number of iterations is known a priori) or when :func:`Stop` is called (when
the the total number of iterations is not known a priori). After processing
has stopped, this property will consistently return the total time required
for processing (it will not keep increasing as additional time passes)."""))

# Constructor

AddMethodMetadata(ProgressReporter.__init__,
    shortDescription=_('Constructs a new %s instance.') % ProgressReporter.__name__)

AddArgumentMetadata(ProgressReporter.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ProgressReporter),
    description=_(':class:`%s` instance.') % ProgressReporter.__name__)

AddArgumentMetadata(ProgressReporter.__init__, 'progressMessage1',
    typeMetadata=ProgressReporter.ProgressMessage1.__doc__.Obj.Type,
    description=ProgressReporter.ProgressMessage1.__doc__.Obj.ShortDescription + '\n\n' + ProgressReporter.ProgressMessage1.__doc__.Obj.LongDescription)

AddArgumentMetadata(ProgressReporter.__init__, 'progressMessage2',
    typeMetadata=ProgressReporter.ProgressMessage2.__doc__.Obj.Type,
    description=ProgressReporter.ProgressMessage2.__doc__.Obj.ShortDescription + '\n\n' + ProgressReporter.ProgressMessage2.__doc__.Obj.LongDescription)

AddArgumentMetadata(ProgressReporter.__init__, 'completionMessage',
    typeMetadata=ProgressReporter.CompletionMessage.__doc__.Obj.Type,
    description=ProgressReporter.CompletionMessage.__doc__.Obj.ShortDescription + '\n\n' + ProgressReporter.CompletionMessage.__doc__.Obj.LongDescription)

AddArgumentMetadata(ProgressReporter.__init__, 'abortedMessage',
    typeMetadata=ProgressReporter.AbortedMessage.__doc__.Obj.Type,
    description=ProgressReporter.AbortedMessage.__doc__.Obj.ShortDescription + '\n\n' + ProgressReporter.AbortedMessage.__doc__.Obj.LongDescription)

AddArgumentMetadata(ProgressReporter.__init__, 'loggingChannel',
    typeMetadata=ProgressReporter.LoggingChannel.__doc__.Obj.Type,
    description=ProgressReporter.LoggingChannel.__doc__.Obj.ShortDescription + '\n\n' + ProgressReporter.LoggingChannel.__doc__.Obj.LongDescription)

AddArgumentMetadata(ProgressReporter.__init__, 'arcGISProgressorLabel',
    typeMetadata=ProgressReporter.ArcGISProgressorLabel.__doc__.Obj.Type,
    description=ProgressReporter.ArcGISProgressorLabel.__doc__.Obj.ShortDescription + '\n\n' + ProgressReporter.ArcGISProgressorLabel.__doc__.Obj.LongDescription)

AddResultMetadata(ProgressReporter.__init__, 'progressReporter',
    typeMetadata=ClassInstanceTypeMetadata(cls=ProgressReporter),
    description=_('New :class:`%s` instance.') % ProgressReporter.__name__)

# Public method: Start

AddMethodMetadata(ProgressReporter.Start,
    shortDescription=_('Signals the :class:`ProgressReporter` that processing has started.'))

CopyArgumentMetadata(ProgressReporter.__init__, 'self', ProgressReporter.Start, 'self')

AddArgumentMetadata(ProgressReporter.Start, 'totalOperations',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=1),
    description=_('Total number of iterations that will be performed, or :py:data:`None` if the number of iterations is not known.'))

# Public method: ReportProgress

AddMethodMetadata(ProgressReporter.ReportProgress,
    shortDescription=_('Signals the :class:`ProgressReporter` that another one or more iterations just completed.'),
    longDescription=_(
"""This method will periodically report progress messages as described in the
class-level documentation. You must call :func:`Start` before calling this
method."""))

CopyArgumentMetadata(ProgressReporter.__init__, 'self', ProgressReporter.ReportProgress, 'self')

AddArgumentMetadata(ProgressReporter.ReportProgress, 'operationsCompleted',
    typeMetadata=IntegerTypeMetadata(minValue=1),
    description=_(
"""Total number of iterations that just completed, typically 1.
You should provide the number of iterations that have completed
since you last called this method. Do not pass in a cumulative total."""))

AddArgumentMetadata(ProgressReporter.ReportProgress, 'reinitializeArcGISProgressor',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True and the ArcGIS progressor is being controlled by this
:class:`ProgressReporter` instance, the ArcGIS progressor will be
reinitialized as part of this call. Use this option to change control of the
progressor back to the ProgressReporter instance after some built-in ArcGIS
tool used the progressor for to report its own progress."""))

# Public method: Stop

AddMethodMetadata(ProgressReporter.Stop,
    shortDescription=_('Signals the ProgressReporter that processing is complete.'),
    longDescription=_(
"""This method will report a completion message as described in the
class-level documentation. You must call :func:`Start` before calling this
method. If provided a value for `totalOperations` when you called
:func:`Start`, and the number of completed operations has not reached this
total, :func:`Stop` will report :attr:`AbortedMessage`."""))

CopyArgumentMetadata(ProgressReporter.__init__, 'self', ProgressReporter.Stop, 'self')


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['Logger',
           'ProgressReporter']
