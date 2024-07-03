# Matlab/__init__.py - GeoEco functions implemented in MATLAB.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ._MatlabDependency import MatlabDependency
from ._MatlabFunctions import MatlabFunctions
from ._MatlabWorkerProcess import MatlabWorkerProcess


###############################################################################
# Metadata: module
###############################################################################

from ..Internationalization import _
from ..Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Classes that wrap GeoEco functions written in MATLAB and expose them as Python functions.'))

from . import _MatlabDependencyMetadata
from . import _MatlabFunctionsMetadata
from . import _MatlabWorkerProcessMetadata


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['MatlabDependency',
           'MatlabFunctions',
           'MatlabWorkerProcess']
