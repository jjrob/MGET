# _RWorkerProcessMetadata.py - Metadata for classes defined in
# _RWorkerProcess.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Dependencies import PythonModuleDependency
from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from ._RWorkerProcess import RWorkerProcess


###############################################################################
# Metadata: RWorkerProcess class
###############################################################################

AddClassMetadata(RWorkerProcess,
    module=__package__,
    shortDescription=_('Starts and manages an R child process and provides methods for interacting with it.'),
    longDescription=_("""TODO: Write long description."""))

# TODO: document the issue with None being translated to JSON null and then R NULL
# See https://github.com/jeroen/jsonlite/issues/70

# Constructor

AddMethodMetadata(RWorkerProcess.__init__,
    shortDescription=_('RWorkerProcess constructor.'),
    dependencies=[PythonModuleDependency('pandas', cheeseShopName='pandas'), 
                  PythonModuleDependency('pyarrow', cheeseShopName='pyarrow'), 
                  PythonModuleDependency('requests', cheeseShopName='requests')])

AddArgumentMetadata(RWorkerProcess.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=RWorkerProcess),
    description=_(':class:`%s` instance.') % RWorkerProcess.__name__)

AddArgumentMetadata(RWorkerProcess.__init__, 'rInstallDir',
    typeMetadata=DirectoryTypeMetadata(mustExist=True, canBeNone=True),
    description=_(
"""On Windows: the path to the directory where R is installed, if do not want
R's installation directory to be discovered automatically. You can determine
the installation directory from within R by executing the function 
``R.home()``. On other operating systems: this parameter is ignored, and R's
executables are expected to be available through via the PATH environment
variable.

If this parameter is not provided, the installation directory will be located
automatically (on Windows). Three methods will be tried, in this order:

1. If the R_HOME environment variable has been set, it will be used. The 
   program Rscript.exe must exist in the `bin\\x64` subdirectory of R_HOME or
   a :exp:`FileNotFoundError`: exception will be raised.

2. Otherwise, if R_HOME has not been set, the Registry will be checked,
   starting with the ``HKEY_CURRENT_USER\\Software\\R-core`` key and falling
   back to ``HKEY_LOCAL_MACHINE\\Software\\R-core`` only if the former does
   not exist. For whichever exists, the value of ``R64\\InstallPath`` will be
   used. The program Rscript.exe must exist in the `bin\\x64` subdirectory of
   that directory or a :exp:`FileNotFoundError`: exception will be raised.

3. Otherwise, if neither of those registry keys exist, the PATH environment
   variable will be checked for the program Rscript.exe. If it does not
   exist, :exp:`FileNotFoundError`: exception will be raised.

Raises:
    :exp:`FileNotFoundError`: The R executable files were not found at the
        specified/expected location.

"""),
    arcGISDisplayName=_('R home directory'))

AddArgumentMetadata(RWorkerProcess.__init__, 'rLibDir',
    typeMetadata=DirectoryTypeMetadata(canBeNone=True),
    description=_(
"""Path to the R library directory where R packages should be stored. When a
package is needed, it will be loaded from this directory if it exists there,
and downloaded there it does not exist.

If not provided, R's default will be used. See the `R documentation
<https://cran.r-project.org/doc/manuals/r-release/R-admin.html#Managing-libraries>`__
for details.

You should provide a custom directory if you want MGET to maintain its own set
of R packages, rather than those you use when running R yourself. For
example, when running MGET, you may want to use only packages that have been
released to CRAN, while when running R yourself, you may want to use newer or
experimental versions that you obtained elsewhere."""),
    arcGISDisplayName=_('R package library directory'))

AddArgumentMetadata(RWorkerProcess.__init__, 'rRepository',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""R repository to use when downloading packages. If not provided,
https://cloud.r-project.org will be used."""), 
    arcGISDisplayName=_('R repository for downloading packages'))

AddArgumentMetadata(RWorkerProcess.__init__, 'updateRPackages',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the R ``update.packages()`` function will be called automatically
when R starts up, to update all R packages to their latest versions. If False,
the default, this will not be done, and once a package has been installed, it
will remain at that version until it is updated via some other mechanism.

Use this option to ensure your R package library is automatically kept up to
date. It is set to False by default to prevent MGET from updating your
already-installed packages without your explicit permission. However, even if
this option is set to False, MGET will still automatically install any
packages that it needs that are missing."""), 
    arcGISDisplayName=_('Update packages automatically'))

AddArgumentMetadata(RWorkerProcess.__init__, 'port',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""TCP port to use for communicating with R via the R plumber package. If not
specified, an unused port will be selected automatically."""), 
    arcGISDisplayName=_('Port'))

AddArgumentMetadata(RWorkerProcess.__init__, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Maximum amount of time, in seconds, that a call into R is allowed to take
to start responding when getting, setting, or deleting variable values. If
this time elapses without the R worker process beginning to send its
response, an error will be raised. In general, a very short value such as 5
seconds is appropriate here.

.. Warning::
    If you set `timeout` to :py:data:`None` and R never responds, your Python
    program will be blocked forever. Use :py:data:`None` with caution.

"""), 
    arcGISDisplayName=_('Timeout'))

AddArgumentMetadata(RWorkerProcess.__init__, 'startupTimeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Maximum amount of time, in seconds, that R is allowed to take to initialize
itself and begin servicing requests. If all necessary R packages are already
installed, this time may be only a second or two. But if packages must be
installed, as occurs the first time you use MGET to interact with R, or if
you request that R packages be updated automatically, then this can take many
seconds. For this reason, the default is set to 300 seconds. If this time
elapses without the R process indicating that it is ready, an error will be
raised.

.. Warning::
    If you set `timeout` to :py:data:`None` and R never responds, your Python
    program will be blocked forever. Use :py:data:`None` with caution.

"""), 
    arcGISDisplayName=_('Startup timeout'))

AddResultMetadata(RWorkerProcess.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=RWorkerProcess),
    description=_(':class:`%s` instance.') % RWorkerProcess.__name__)

# Public method: Start

AddMethodMetadata(RWorkerProcess.Start,
    shortDescription=_('Start the R worker process.'),
    longDescription=_(
"""It is not necessary to explicitly start the R worker process. It will be
started automatically when a method is called that requires interaction with
R, if it is not running already. :func:`Start` is provided in case there is a
need to start the process before it is needed, e.g. for debugging, to ensure
it will work prior to embarking on a complicated workflow.

If :func:`Start` returns successfully, the worker process was started
successfully. If it failed, :func:`Start` will raise an exception."""))

CopyArgumentMetadata(RWorkerProcess.__init__, 'self', RWorkerProcess.Start, 'self')

# Public method: Stop

AddMethodMetadata(RWorkerProcess.Stop,
    shortDescription=_('Stop the R worker process.'),
    longDescription=_(
"""When you instantiate :class:`~GeoEco.R.RWorkerProcess` as part of a
``with`` statement, :func:`Stop` will be called automatically when the code
block is exited:

.. code-block:: python

    with RWorkerProcess(...) as r:
        ...

Otherwise, you should call :func:`Stop` yourself when the R worker process is
no longer needed.

.. note::
    :func:`Stop` is not automatically called when the
    :class:`~GeoEco.R.RWorkerProcess` goes out of scope or otherwise is
    deleted. So if it is important to stop the R worker process before the
    process hosting the Python interpreter exits, you should use the
    ``with`` statement or manually call :func:`Stop`. The R worker process
    will be stopped automatically when the Python process exits, though.

"""))

AddArgumentMetadata(RWorkerProcess.Stop, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Maximum amount of time, in seconds, to wait for R to shut down. In
general, R should shut down quickly. During normal operation, all interactions
with R are blocking, so R should be idle when this function is called.

.. Warning::
    If you set `timeout` to :py:data:`None` and your R expression never
    completes, your Python program will be blocked forever.
    Use :py:data:`None` with caution.

"""), 
    arcGISDisplayName=_('Timeout')) 

CopyArgumentMetadata(RWorkerProcess.__init__, 'self', RWorkerProcess.Stop, 'self')

# Public method: Eval

AddMethodMetadata(RWorkerProcess.Eval,
    shortDescription=_('Evaluate an R expression and return the result.'),
    longDescription=_(
"""The expression can be anything that may be evaluated by the R ``eval``
function. Multiple expressions can be separated by semicolons or newlines.
The value of the last expression is returned.

TODO: Write warning about what kinds of objects can be returned."""))

CopyArgumentMetadata(RWorkerProcess.__init__, 'self', RWorkerProcess.Eval, 'self')

AddArgumentMetadata(RWorkerProcess.Eval, 'expr',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_(
"""R expression to evaluate. It can be anything that may be evaluated by the R
``eval`` function. Multiple expressions can be separated by semicolons or
newlines. The value of the last expression is returned."""), 
    arcGISDisplayName=_('R expression'))

AddArgumentMetadata(RWorkerProcess.Eval, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Maximum amount of time, in seconds, that R is permitted to return a
result. If this time elapses without the R worker process beginning to send
its response, an error will be raised.

The default timeout was selected to allow all but the most time consuming
expressions to complete. You should increase it for very long running jobs.
If you're unsure how long it will take, you may set it to :py:data:`None`,
which allows an infinite amount of time.

.. Warning::
    If you set `timeout` to :py:data:`None` and your R expression never
    completes, your Python program will be blocked forever.
    Use :py:data:`None` with caution.

"""), 
    arcGISDisplayName=_('Timeout'))


############################################################################
# This module is not meant to be imported directly. Import GeoEco.R instead.
############################################################################

__all__ = []
