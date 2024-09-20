# _MatlabFunctionsMetadata.py - Metadata for classes defined in
# _MatlabFunctions.py.
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

from ._MatlabFunctions import MatlabFunctions


###############################################################################
# Metadata: MatlabFunctions class
###############################################################################

AddClassMetadata(MatlabFunctions,
    module=__package__,
    shortDescription=_('Allows GeoEco functions implemented in MATLAB to be called as Python functions.'),
    longDescription=_(
"""Certain functions in GeoEco are implemented in MATLAB code. In order for
these functions to run, either MATLAB R2024b or the MATLAB Runtime R2024b must
be installed. The MATLAB Runtime is free and may be downloaded from
https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html.
Please follow the installation instructions carefully. Version R2024b must be
used; other versions will not work. MATLAB Runtime allows multiple versions
can be installed at the same time.

To call MATLAB functions using :class:`MatlabFunctions`, it is first necessary
to call :func:`Initialize`, which loads the necessary MATLAB libraries into
the current process and binds a :py:func:`staticmethod` to
:class:`MatlabFunctions` for each MATLAB function implemented by GeoEco. For
example:

.. code-block:: python

    from GeoEco.Matlab import MatlabFunctions
    MatlabFunctions.Initialize()
    a = [1,2,3]
    b = MatlabFunctions.TestParameterType(a)
    assert b == a

The ``TestParameterType`` function simply accepts one argument and returns it
back to the caller. We use it in GeoEco's automated tests to verify that we
can exchange different data types with MATLAB properly.

Note:
    GeoEco's MATLAB functions are part of GeoEco's internal API and are not
    recommended for external callers. Because of this, we do not formally
    document them. But you can find them in GeoEco's source code repository,
    or by unzipping the ``.ctf`` file found inside GeoEco's Python package
    directory and digging around in the resulting directory structure.

Warning:
    MATLAB is large and complex program that utilizes a lot of third-party
    programming libraries (.so files on Linux and .DLL files on Windows).
    Other large and complex programs such as ArcGIS may utilize some of the
    same libraries. Loading both MATLAB and ArcGIS into the same process can
    result in a situation known as `dependency hell
    <https://en.wikipedia.org/wiki/Dependency_hell>`_, in which one program
    requires version A of a third-party library but the other program requires
    version B, but both versions cannot be loaded into the same process at the
    same time. When these version conflicts occur, the first program may run
    successfully but the second one may fail. Because GeoEco often involves
    utilizing ArcGIS, we recommend accessing GeoEco's MATLAB functions with
    the :class:`~GeoEco.Matlab.MatlabWorkerProcess` class rather than
    :class:`MatlabFunctions`. :class:`~GeoEco.Matlab.MatlabWorkerProcess` also
    exposes GeoEco's MATLAB functions as :py:func:`staticmethod`\\ s, but
    loads :class:`MatlabFunctions` in a separate process and proxies function
    calls to it. By keeping MATLAB in a separate process, dependency hell is
    avoided.
"""))

# Public method: Initialize

AddMethodMetadata(MatlabFunctions.Initialize,
    shortDescription=_('Initializes MATLAB and binds a :py:func:`staticmethod` to :class:`MatlabFunctions` for each GeoEco MATLAB function.'))

AddArgumentMetadata(MatlabFunctions.Initialize, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=MatlabFunctions),
    description=_(':class:`%s` or an instance of it.') % MatlabFunctions.__name__)

AddArgumentMetadata(MatlabFunctions.Initialize, 'loggingQueue',
    typeMetadata=ClassInstanceTypeMetadata(cls=multiprocessing.queues.Queue, canBeNone=True),
    description=_(':py:class:`multiprocessing.queues.Queue` object to which logging messages should be posted. If not given, messages will be logged to the ``GeoEco`` logger with Python\'s :py:mod:`logging` module.'))


#################################################################################
# This module is not meant to be imported directly. Import GeoEco.Matlab instead.
#################################################################################

__all__ = []
