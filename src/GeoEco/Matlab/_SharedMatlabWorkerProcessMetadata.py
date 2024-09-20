# _SharedMatlabWorkerProcessMetadata.py - Metadata for classes defined in
# _SharedMatlabWorkerProcess.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from ._SharedMatlabWorkerProcess import SharedMatlabWorkerProcess


###############################################################################
# Metadata: SharedMatlabWorkerProcess class
###############################################################################

AddClassMetadata(SharedMatlabWorkerProcess,
    module=__package__,
    shortDescription=_('Manages a singleton instance of :class:`MatlabWorkerProcess` that may be shared by multiple callers.'),
    longDescription=_(
"""Certain functions in GeoEco are implemented in MATLAB code. In order for
these functions to run, either MATLAB R2024b or the MATLAB Runtime R2024b must
be installed. The MATLAB Runtime is free and may be downloaded from
https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html.
Please follow the installation instructions carefully. Version R2024b must be
used; other versions will not work. MATLAB Runtime allows multiple versions
can be installed at the same time.

To avoid `dependency hell <https://en.wikipedia.org/wiki/Dependency_hell>`_,
:class:`MatlabWorkerProcess` hosts MATLAB or the MATLAB Runtime in a separate
process. Starting and initializing this process can take several seconds. To
avoid having to do this over and over again,
:class:`SharedMatlabWorkerProcess` starts and manages a single
:class:`MatlabWorkerProcess` instance that can be used throughout the GeoEco
library. Once instantiated, it will run until it is explicitly stopped or
until the Python interpreter exits (:py:mod:`atexit` is used for this.)

If a GeoEco component needs its own private worker process, rather than using
the shared one, it can instantiate and use its own instance of
:class:`MatlabWorkerProcess` rather than using
:class:`SharedMatlabWorkerProcess`. An unlimited number of worker processes
can be started and run simultaneously. A given worker process may only be used
by one thread of the Python interpreter at a time. While a call into a worker
process is executing, :class:`MatlabWorkerProcess` blocks new callers until
the current call completes.

Here's how to use :class:`SharedMatlabWorkerProcess`:

.. code-block:: python

    # Start the MatlabWorkerProcess if it is not already running and get a
    # weakref to it.

    from GeoEco.Matlab import SharedMatlabWorkerProcess
    matlab = SharedMatlabWorkerProcess.GetWorkerProcess()

    # Now call methods of the matlab object, e.g.:

    a = [1,2,3]
    b = matlab.TestParameterType(a)
    assert b == a

    # Optionally, shut down the shared worker process. If this is not done
    # explicitly, it will be done automatically when the Python interpreter
    # exits. After the process is shut down, you can call GetWorkerProcess()
    # to start it back up again, if desired.

    SharedMatlabWorkerProcess.Shutdown()

In the example above, the ``TestParameterType`` function simply accepts one
argument and returns it back to the caller. We use it in GeoEco's automated
tests to verify that we can exchange different data types with MATLAB
properly.

Note:
    GeoEco's MATLAB functions are part of GeoEco's internal API and are not
    recommended for external callers. Because of this, we do not formally
    document them. But you can find them in GeoEco's source code repository,
    or by unzipping the ``.ctf`` file found inside GeoEco's Python package
    directory and digging around in the resulting directory structure.

"""))

# Public method: GetWorkerProcess

AddMethodMetadata(SharedMatlabWorkerProcess.GetWorkerProcess,
    shortDescription=_('Instantiate and start the shared :class:`MatlabWorkerProcess` (if not already instantiated) and return :py:mod:`weakref` to it.'))

AddArgumentMetadata(SharedMatlabWorkerProcess.GetWorkerProcess, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=SharedMatlabWorkerProcess),
    description=_(':class:`%s` or an instance of it.') % SharedMatlabWorkerProcess.__name__)

AddArgumentMetadata(SharedMatlabWorkerProcess.GetWorkerProcess, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_('Number of seconds to wait when starting MATLAB before failing.'))

AddResultMetadata(SharedMatlabWorkerProcess.GetWorkerProcess, 'obj',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('A :py:mod:`weakref` to the shared :class:`MatlabWorkerProcess`.'))

# Public method: Shutdown

AddMethodMetadata(SharedMatlabWorkerProcess.Shutdown,
    shortDescription=_('Stop and delete the :class:`MatlabWorkerProcess`, if it has been instantiated.'))

CopyArgumentMetadata(SharedMatlabWorkerProcess.GetWorkerProcess, 'cls', SharedMatlabWorkerProcess.Shutdown, 'cls')

AddArgumentMetadata(SharedMatlabWorkerProcess.Shutdown, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_('Number of seconds to wait when stopping the MATLAB worker process before failing. Because the process will be idle when :func:`Stop` is called, a long timeout should not be necessary, but we use a relatively long default in case the machine is busy.'))


#################################################################################
# This module is not meant to be imported directly. Import GeoEco.Matlab instead.
#################################################################################

__all__ = []
