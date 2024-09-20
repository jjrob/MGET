# _MatlabDependencyMetadata.py - Metadata for classes defined in
# _MatlabDependency.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import multiprocessing.queues

from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from ._MatlabDependency import MatlabDependency


###############################################################################
# Metadata: MatlabDependency class
###############################################################################

AddClassMetadata(MatlabDependency,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Dependencies.Dependency` that checks that MATLAB or the MATLAB Runtime is installed.'),
    longDescription=_(
"""Certain functions in GeoEco are implemented in MATLAB code. In order for
these functions to run, either MATLAB R2024b or the MATLAB Runtime R2024b must
be installed. The MATLAB Runtime is free and may be downloaded from
https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html.
Please follow the installation instructions carefully. Version R2024b must be
used; other versions will not work. MATLAB Runtime allows multiple versions
can be installed at the same time."""))

# Public method: FindMatlab

AddMethodMetadata(MatlabDependency.FindMatlab,
    shortDescription=_('Finds where MATLAB or the MATLAB Runtime is installed.'))

AddArgumentMetadata(MatlabDependency.FindMatlab, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=MatlabDependency),
    description=_(':class:`%s` or an instance of it.') % MatlabDependency.__name__)

AddArgumentMetadata(MatlabDependency.FindMatlab, 'setPath',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, this function will set the the LD_LIBRARY_PATH (on Linux) or PATH (on Windows) environment variable as necessary to allow MATLAB to be accessed from Python.'))

AddArgumentMetadata(MatlabDependency.FindMatlab, 'loggingQueue',
    typeMetadata=ClassInstanceTypeMetadata(cls=multiprocessing.queues.Queue, canBeNone=True),
    description=_(':py:class:`multiprocessing.queues.Queue` object to which logging messages should be posted. If not given, messages will be logged to the ``GeoEco`` logger with Python\'s :py:mod:`logging` module.'))

AddResultMetadata(MatlabDependency.FindMatlab, 'oldPath',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Old value of the environment variable, when `setPath` is True. An empty string if the variable was not defined. Always :py:data:`None` if `setPath` is False.'))


#################################################################################
# This module is not meant to be imported directly. Import GeoEco.Matlab instead.
#################################################################################

__all__ = []
