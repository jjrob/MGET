# Matlab/_SharedMatlabWorkerProcess.py - Defines SharedMatlabWorkerProcess, a
# class that manages a singleton instance of MatlabWorkerProcess that may be
# shared by multiple callers, to avoid the costs of starting up and shutting
# down their own individual worker processes.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import atexit
import threading
import weakref

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger
from ._MatlabWorkerProcess import MatlabWorkerProcess


class SharedMatlabWorkerProcess(object):
    __doc__ = DynamicDocString()

    _WorkerProcess = None
    _Lock = threading.Lock()

    @classmethod
    def GetWorkerProcess(cls, timeout=30.):
        Logger.Debug('%(class)s 0x%(id)016X: GetWorkerProcess() called.', {'class': cls.__name__, 'id': id(cls)})
        with cls._Lock:
            if cls._WorkerProcess is None:
                Logger.Debug('%(class)s 0x%(id)016X: Instantiating new MatlabWorkerProcess(timeout=%(timeout)s.', {'class': cls.__name__, 'id': id(cls), 'timeout': timeout})
                cls._WorkerProcess = MatlabWorkerProcess(timeout)
            return weakref.proxy(cls._WorkerProcess)

    @classmethod
    def Shutdown(cls, timeout=30.):
        Logger.Debug('%(class)s 0x%(id)016X: Shutdown() called.', {'class': cls.__name__, 'id': id(cls)})
        with cls._Lock:
            if cls._WorkerProcess is not None:
                Logger.Debug('%(class)s 0x%(id)016X: Calling _WorkerProcess.Stop(timeout=%(timeout)s.', {'class': cls.__name__, 'id': id(cls), 'timeout': timeout})
                try:
                    cls._WorkerProcess.Stop(timeout)
                except:
                    pass
                cls._WorkerProcess = None
            else:
                Logger.Debug('%(class)s 0x%(id)016X: No worker process is running.', {'class': cls.__name__, 'id': id(cls)})


atexit.register(SharedMatlabWorkerProcess.Shutdown)
