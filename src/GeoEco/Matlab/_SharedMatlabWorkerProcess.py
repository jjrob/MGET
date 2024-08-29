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
        with cls._Lock:
            if cls._WorkerProcess is None:
                cls._WorkerProcess = MatlabWorkerProcess(timeout)
            return weakref.proxy(cls._WorkerProcess)

    @classmethod
    def Shutdown(cls, timeout=30.):
        with cls._Lock:
            if cls._WorkerProcess is not None:
                try:
                    cls._WorkerProcess.Stop(timeout)
                except:
                    pass
                cls._WorkerProcess = None


atexit.register(SharedMatlabWorkerProcess.Shutdown)
