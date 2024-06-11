import logging

import pytest

# When running pytest, it may conclude with errors similar to this:
#
# --- Logging error ---
# Traceback (most recent call last):
#   File "/usr/lib/python3.10/logging/__init__.py", line 1103, in emit
#     stream.write(msg + self.terminator)
# ValueError: I/O operation on closed file.
# Call stack:
#   File "/home/jason/Development/MGET/src/GeoEco/Datasets/SQLite.py", line 123, in __del__
#     self._LogDebug(_('%(class)s 0x%(id)016X: Closing %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
#   File "/home/jason/Development/MGET/src/GeoEco/Datasets/_CollectibleObject.py", line 383, in _LogDebug
#     logging.getLogger(CollectibleObject._LoggingChannel).debug(format, *args, **kwargs)
#   File "/usr/lib/python3.10/logging/__init__.py", line 1465, in debug
#     self._log(DEBUG, msg, args, **kwargs)
#   File "/usr/lib/python3.10/logging/__init__.py", line 1624, in _log
#     self.handle(record)
#   File "/usr/lib/python3.10/logging/__init__.py", line 1634, in handle
#     self.callHandlers(record)
#   File "/usr/lib/python3.10/logging/__init__.py", line 1696, in callHandlers
#     hdlr.handle(record)
#   File "/usr/lib/python3.10/logging/__init__.py", line 968, in handle
#     self.emit(record)
#   File "/home/jason/Development/MGET/src/GeoEco/Logging.py", line 767, in emit
#     logging.StreamHandler.emit(self, record)
#
# This happens because pytest replaces stdout with a buffer to capture
# logging, and then closes it before atexit() is called. GeoEco uses atexit()
# to destroy certain objects that are not freed during normal operation, and
# this can log debug messages, which will then be emitted to the closed
# buffer. 
#
# To work around this, we register the following session fixture that yields
# and then removes all instances of logging.StreamHandler from the GeoEco
# logger and any of its descendants, so that they do not try to emit to the
# closed buffer. For more info, see
# https://github.com/pytest-dev/pytest/issues/5502.

@pytest.fixture(scope='session', autouse=True)
def cleanup_logging_handlers():
    try:
        yield
    finally:
        if logging.getLogger('GeoEco') is not None:
            loggers = [logging.getLogger('GeoEco')]
            while len(loggers) > 0:
                logger = loggers.pop()

                # Add the child loggers of this logger, so they will be
                # processed. Unfortunately, Logger.getChildren() was not added
                # until Python 3.12 but we need to be compatible back to
                # Python 3.9, so we copy its implementation here.

                if hasattr(logger, 'getChildren'):
                    loggers.extend(logger.getChildren())

                else:
                    def _hierlevel(logger):
                        if logger is logger.manager.root:
                            return 0
                        return 1 + logger.name.count('.')

                    loggers.extend(set([item for item in logging.root.manager.loggerDict.values() if isinstance(item, logging.Logger) and item.parent is logger and _hierlevel(item) == 1 + _hierlevel(item.parent)]))

                # Remove all stream handlers from this logger.

                for handler in logger.handlers:
                    if isinstance(handler, logging.StreamHandler):
                        logger.removeHandler(handler)
