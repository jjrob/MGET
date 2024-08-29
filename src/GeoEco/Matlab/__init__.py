# Matlab/__init__.py - GeoEco functions implemented in MATLAB.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Classes that wrap GeoEco functions written in MATLAB and expose them as Python functions.'))

from ._MatlabDependency import MatlabDependency
from . import _MatlabDependencyMetadata

from ._MatlabFunctions import MatlabFunctions
from . import _MatlabFunctionsMetadata

from ._MatlabWorkerProcess import MatlabWorkerProcess
from . import _MatlabWorkerProcessMetadata

from ._SharedMatlabWorkerProcess import SharedMatlabWorkerProcess
from . import _SharedMatlabWorkerProcessMetadata

__all__ = ['MatlabDependency',
           'MatlabFunctions',
           'MatlabWorkerProcess',
           'SharedMatlabWorkerProcess']
