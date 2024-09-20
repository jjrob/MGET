# _MatlabWorkerProcessMetadata.py - Metadata for classes defined in
# _MatlabWorkerProcess.py.
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

from ._MatlabDependency import MatlabDependency
from ._MatlabWorkerProcess import MatlabWorkerProcess


###############################################################################
# Metadata: MatlabWorkerProcess class
###############################################################################

AddClassMetadata(MatlabWorkerProcess,
    module=__package__,
    shortDescription=_('Allows GeoEco functions implemented in MATLAB to be called as Python functions, with MATLAB hosted in a separate process.'),
    longDescription=_(
"""Certain functions in GeoEco are implemented in MATLAB code. In order for
these functions to run, either MATLAB R2024b or the MATLAB Runtime R2024b must
be installed. The MATLAB Runtime is free and may be downloaded from
https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html.
Please follow the installation instructions carefully. Version R2024b must be
used; other versions will not work. MATLAB Runtime allows multiple versions
can be installed at the same time.

MATLAB is large and complex program that utilizes a lot of third-party
programming libraries (.so files on Linux and .DLL files on Windows). Other
large and complex programs such as ArcGIS may utilize some of the same
libraries. Loading both MATLAB and ArcGIS into the same process can result in
a situation known as `dependency hell
<https://en.wikipedia.org/wiki/Dependency_hell>`_, in which one program
requires version A of a third-party library but the other program requires
version B, but both versions cannot be loaded into the same process at the
same time. When these version conflicts occur, the first program may run
successfully but the second one may fail. :class:`MatlabWorkerProcess` solves
this problem by loading MATLAB in a separate process. Because GeoEco often
involves utilizing ArcGIS, we recommend accessing GeoEco's MATLAB functions
with :class:`MatlabWorkerProcess` rather than
:class:`~GeoEco.Matlab.MatlabFunctions`. which loads them into the caller's
process.

Note:
    Because starting MATLAB or MATLAB Runtime can take several seconds, most
    parts of the GeoEco package use :class:`SharedMatlabWorkerProcess` to
    share a single instance of :class:`MatlabWorkerProcess`, to avoid having
    to start the worker process over and over again. If you are implementing a
    GeoEco component, consider using :class:`SharedMatlabWorkerProcess`.

To use :class:`MatlabWorkerProcess`, you must first instantiate it, then call
the GeoEco MATLAB functions of interest as methods of that instance. The first
time you call a method, a worker process will be created and MATLAB will be
loaded inside it. Your call will then be proxied to that process. Because
starting MATLAB can take several seconds, the process will then be kept alive
in anticipation of you making another call. When you are done, call
:func:`Stop` to stop the worker process. For example:

.. code-block:: python

    from GeoEco.Matlab import MatlabWorkerProcess
    matlab = MatlabWorkerProcess()
    try:
        a = [1,2,3]
        b = matlab.TestParameterType(a)
        assert b == a
        ...
    finally:
        matlab.Stop()

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

:class:`MatlabWorkerProcess` supports the Python context manager protocol,
which allows you to use :py:ref:`with` to ensure :func:`Stop` is called
automatically when your block exits:

.. code-block:: python

    from GeoEco.Matlab import MatlabWorkerProcess
    with MatlabWorkerProcess() as matlab:
        a = [1,2,3]
        b = matlab.TestParameterType(a)
        assert b == a
        ...

Warning:
    If you do not use :py:ref:`with` or manually call :func:`Stop`, the worker
    process will remain running until your main process exits. During this
    time, it will remain idle but it may occupy a not-insignificant amount of
    RAM. Also, the worker process is not stopped automatically when the
    :class:`MatlabWorkerProcess` instance is deleted. You must use
    :py:ref:`with` or :func:`Stop` to stop the worker process.

Although the MATLAB function is executed in another process, the call into the
:class:`MatlabWorkerProcess` instance method representing it blocks until it
is complete. Currently, there is no way to execute MATLAB functions 
asynchronously with :class:`MatlabWorkerProcess`."""))

# Constructor

AddMethodMetadata(MatlabWorkerProcess.__init__,
    shortDescription=_('MatlabWorkerProcess constructor.'),
    dependencies=[MatlabDependency()])

AddArgumentMetadata(MatlabWorkerProcess.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=MatlabWorkerProcess),
    description=_(':class:`%s` instance.') % MatlabWorkerProcess.__name__)

AddArgumentMetadata(MatlabWorkerProcess.__init__, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_('Number of seconds to wait for MATLAB to start before assuming it has failed.'))

AddArgumentMetadata(MatlabWorkerProcess.__init__, 'idle',
    typeMetadata=FloatTypeMetadata(minValue=0., canBeNone=True),
    description=_(
"""Number of seconds to the worker process should wait after completing the
execution of a MATLAB function to be commanded to execute another function. If
it does not receive a new command after this idle time, it will shut down to
save memory. If a new command is issued after it is shut down, it will be
restared automatically."""))

AddResultMetadata(MatlabWorkerProcess.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=MatlabWorkerProcess),
    description=_(':class:`%s` instance.') % MatlabWorkerProcess.__name__)

# Public method: Stop

AddMethodMetadata(MatlabWorkerProcess.Stop,
    shortDescription=_('Stops the MATLAB worker process.'),
    longDescription=_(
"""The MATLAB functions remain bound to the :class:`MatlabWorkerProcess`
instance. If one is subsequently called, a new MATLAB worker process will be
started."""))

AddArgumentMetadata(MatlabWorkerProcess.Stop, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=MatlabWorkerProcess),
    description=_(':class:`%s` instance.') % MatlabWorkerProcess.__name__)

AddArgumentMetadata(MatlabWorkerProcess.Stop, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Number of seconds to wait when stopping the MATLAB worker process before
failing. Because the process will be idle when :func:`Stop` is called, a long
timeout should not be necessary, but we use a relatively long default
in case the machine is busy."""))


#################################################################################
# This module is not meant to be imported directly. Import GeoEco.Matlab instead.
#################################################################################

__all__ = []
