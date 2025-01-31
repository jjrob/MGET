# _RWorkerProcessMetadata.py - Metadata for classes defined in
# _RWorkerProcess.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime

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
    longDescription=_(
"""Similar to the `rpy2 <https://rpy2.github.io/>`__ package,
:class:`~GeoEco.R.RWorkerProcess` starts the R interpreter and provides
mechanisms for Python code to get and set R variables and evaluate R
expressions. :class:`~GeoEco.R.RWorkerProcess` is not as fully-featured as
rpy2 and has several important differences in how it is implemented:

1. :class:`~GeoEco.R.RWorkerProcess` hosts the R interpreter in a child
   process (using the Rscript program), while rpy2 hosts it within the same
   process as the Python interpreter. :class:`~GeoEco.R.RWorkerProcess` is
   therefore less likely to encounter "DLL Hell" conflicts, in which Python
   and R try to load different versions of the same shared library, which can
   cause the process to crash. However, :class:`~GeoEco.R.RWorkerProcess` is
   slower than rpy2, because interactions with R have to occur via
   interprocess communication. :class:`~GeoEco.R.RWorkerProcess` implements
   this with the R `plumber <https://www.rplumber.io/>`__ package, which
   allows R functions to be exposed as HTTP endpoints. This mechanism is also
   less secure than that used by rpy2. The HTTP endpoints are only accessible
   by processes running on the local machine (IPv4 address 127.0.0.1), use a
   randomly-selected TCP point, and require callers to provide a
   randomly-generated token that only the Python process knows, but a
   malicious party who can run processes on the local machine could still
   mount a denial of service attack on the Python/R interface by flooding the
   HTTP endpoints with bogus requests.

2. :class:`~GeoEco.R.RWorkerProcess` does not need to be compiled against a
   specific version of R, and can therefore work with any version of R that
   you have installed, while rpy2 must be recompiled for the R version you
   have, whenever you change it.

3. :class:`~GeoEco.R.RWorkerProcess` supports Microsoft Windows, while rpy2
   historically has lacked a Windows maintainer. While it can be possible to
   get rpy2 working on Windows, there are usually no binary distributions
   (Python wheels) for Windows on the `Python Package Index
   <https://pypi.org/project/rpy2>`__. For Conda users, which generally
   includes users of ArcGIS, there is a release of `rpy2 on conda-forge
   <https://anaconda.org/conda-forge/rpy2>`__, but it can be out of date by a
   year or more and may not be compatible with recent R versions. To work
   around this, Windows users can try to build rpy2 from source, but
   installing the correct compiler and required libraries can be challenging
   and time consuming.

If rpy2 works for you, we recommend you continue to use it. But if not, or
some of the issues mentioned above affect you,
:class:`~GeoEco.R.RWorkerProcess` could provide an effective alternative.

**Using RWorkerProcess**

:class:`~GeoEco.R.RWorkerProcess` represents the child R process. When you
instantiate :class:`~GeoEco.R.RWorkerProcess`, nothing happens at first. The
child process is started automatically when you start using the
:class:`~GeoEco.R.RWorkerProcess` instance to interact with R. If desired, you
can call :func:`~GeoEco.R.RWorkerProcess.Start` to start it manually or
:func:`~GeoEco.R.RWorkerProcess.Stop` to stop it. We recommend you use the
``with`` statement to automatically control the child process's lifetime:

.. code-block:: python

    from GeoEco.R import RWorkerProcess
    with RWorkerProcess() as r:
        # do stuff with the r instance

This will start the child process when it is first needed and automatically
stop it when the ``with`` block is exited, even if an exception is raised. If
the Python process dies without Python exiting properly, the operating system
will stop the child process automatically.

**Evaluating R expressions from Python**

func:`~GeoEco.R.RWorkerProcess.Eval` accepts a string representing an R
expression, passes it to the R interpreter for evaluation, and returns the
result, translating R types into suitable Python types. You can supply
multiple expressions in a single call, separated by newline characters or
semicolons. The last value of the last expression will be returned:

.. code-block:: python

    >>> from GeoEco.R import RWorkerProcess
    >>> r = RWorkerProcess()
    >>> r.Eval('x <- 6; y <- 7; x * y')
    42      

A limited number of R types can be translated into Python types. The rules of
translation are governed by the serialization formats used to marshal data
between Python and R. For most types, JSON is used as the serialization
format, with the `requests <https://pypi.org/project/requests/>`__ package
handling it on the Python side and `plumber <https://www.rplumber.io/>`__ on
the R side. In general, R vectors, lists, and data frames are supported, as
follows:

* R vectors of length 1, sometimes known as atomic values, with the type
  ``logical``, ``integer``, ``double``, or ``character`` are returned as
  Python :py:class:`bool`, :py:class:`int`, :py:class:`float`, and
  :py:class:`str`, respectively.

* R vectors of length 2 or more are returned as Python :py:class:`list`.

* R lists are returned as Python :py:class:`dict`.

* If all of the elements of an R ``double`` vector happen to be integers,
  Python :py:class:`int`\\s will be returned rather than :py:class:`float`\\s.

  .. code-block:: python

      >>> r.Eval('typeof(2)')     # R's interpreter parses double, even if mathematically it is an integer
      'double'
      >>> type(r.Eval('2'))       # R does not include a decimal point when serializing to JSON, so Python deserializes an integer
      <class 'int'>
      >>> r.Eval('typeof(2.5)')   # This one includes a decimal
      'double'
      >>> type(r.Eval('2.5'))     # The JSON includes the decimal point, so now a float is returned
      <class 'float'>
      >>> 
      >>> r.Eval('c(1,2,3.7)')
      [1, 2, 3.7]
      >>> [type(x) for x in r.Eval('c(1,2,3.7)')]
      [<class 'int'>, <class 'int'>, <class 'float'>]

* R ``complex`` is not supported (because JSON does not support complex
  numbers) and is returned as Python :py:class:`str`:

  .. code-block:: python

      >>> r.Eval('c(1+2i, 3-5i, 6)')
      ['1+2i', '3-5i', '6+0i']

* R ``NA`` and R ``NULL`` are often returned as Python :py:data:`None`, but
  not always, owing to there being no perfect way to handle ``NA`` and
  ``NULL`` with JSON serialization (e.g. `see here
  <https://github.com/jeroen/jsonlite/issues/70>`__). You should not make any
  assumptions about how ``NA`` or ``NULL`` will be returned in Python, and
  should always test your specific scenario. Here are some illustrative
  examples:

  .. code-block:: python

      >>> from GeoEco.R import RWorkerProcess
      >>> r = RWorkerProcess()

**Getting and setting R variables from Python**

You can get and set variables in the R interpreter through the dictionary
interface of the :class:`~GeoEco.R.RWorkerProcess` instance:

.. code-block:: python

    from GeoEco.R import RWorkerProcess
    with RWorkerProcess() as r:
        r['my_variable'] = 42     # Set my_variable to 42 in the R interpreter
        print(r['my_variable'])   # Get back the value of my_variable and print it
        print(dir(r))             # Print a list of the variables defined in the R interpreter
        del r['my_variable']      # Delete my_variable from the R interpreter

Python types will be automatically translated to and from R types. A limited
number of types are supported. For types other than data frames, JSON is
exchanged between Python and R, and the rules of translation are governed by
the JSON serializers used in each environment (in Python, the serializer used
by the `requests <https://pypi.org/project/requests/>`__ package; in R, the
serializer used by the `plumber <https://www.rplumber.io/>`__ package). For
data frames, the feather format is exchanged.

In general:

* Python :py:class:`bool`, :py:class:`int`, :py:class:`float`, and
  :py:class:`str` are translated to/from R length 1 vectors of the type
  ``logical``, ``integer``, ``double``, and ``character``, respectively.

* A Python :py:class:`list` of length two or more of the types above will be
  translated to/from an R vector of the same length. If the items in the
  Python :py:class:`list` are all the same type, the R vector will be the
  corresponding type. If the Python :py:class:`list` contains a mix of types,
  they will all be coerced into ``integer``, ``double``, or ``character`` as
  appropriate so that an R vector can be constructed.

  .. note::
      When R returns ``logical``, ``integer``, ``double``, and ``character``
      vectors that have a length of 1, they are translated to Python
      :py:class:`bool`, :py:class:`int`, :py:class:`float`, and
      :py:class:`str` instances, not to a :py:class:`list` with a single
      instance of those types within it.

* Python :py:data:`None` is often translated to/from an R ``NA`` if it is
  contained in a list, but not always. This is a consequence of R supporting
  ``NA`` and ``NULL`` as distinct concepts, while Python supports just
  :py:data:`None` and JSON just ``null``.

"""))

# TODO: document the issue with None being translated to JSON null and then R NULL
# See https://github.com/jeroen/jsonlite/issues/70

# Constructor

AddMethodMetadata(RWorkerProcess.__init__,
    shortDescription=_('RWorkerProcess constructor.'),
    dependencies=[PythonModuleDependency('pandas', cheeseShopName='pandas'), 
                  PythonModuleDependency('pyarrow', cheeseShopName='pyarrow'), 
                  PythonModuleDependency('requests', cheeseShopName='requests'),
                  PythonModuleDependency('tzlocal', cheeseShopName='tzlocal')])

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
   a :exc:`FileNotFoundError`: exception will be raised.

2. Otherwise, if R_HOME has not been set, the Registry will be checked,
   starting with the ``HKEY_CURRENT_USER\\Software\\R-core`` key and falling
   back to ``HKEY_LOCAL_MACHINE\\Software\\R-core`` only if the former does
   not exist. For whichever exists, the value of ``R64\\InstallPath`` will be
   used. The program Rscript.exe must exist in the `bin\\x64` subdirectory of
   that directory or a :exc:`FileNotFoundError`: exception will be raised.

3. Otherwise, if neither of those registry keys exist, the PATH environment
   variable will be checked for the program Rscript.exe. If it does not
   exist, :exc:`FileNotFoundError`: exception will be raised.

Raises:
    :exc:`FileNotFoundError`: The R executable files were not found at the
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

AddArgumentMetadata(RWorkerProcess.__init__, 'defaultTZ',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Name of the time zone to use when 1) setting R variables from time-zone
naive :py:class:`~datetime.datetime` instances, 2) getting the values of R
variables that return :py:class:`~datetime.datetime` instances, and 3) 
returning :py:class:`~datetime.datetime` instances from :py:func:`Eval`.
This time zone only applies when dealing with data types other than data
frames. 

**Setting R variables using naive :py:class:`~datetime.datetime` instances**

When a :py:class:`~datetime.datetime` instance is sent to R, it is converted
to an R ``POSIXct`` object, which represents time as the number of seconds
since the UNIX epoch, which is defined as 1970-01-01 00:00:00 UTC. Because of
this, :class:`~GeoEco.R.RWorkerProcess` needs to know which time zone
the :py:class:`~datetime.datetime` instance is in so that it can be converted
to UTC for R.

If a :py:class:`~datetime.datetime` instance has a time zone defined (meaning
that its `tzinfo` attribute is not :py:data:`None`), then
:class:`~GeoEco.R.RWorkerProcess` will apply that time zone when computing UTC
times to send to R. But if it does not have a time zone defined, it is known
as a "naive" :py:class:`~datetime.datetime`. In this case, the `defaultTZ`
parameter determines the time zone to use, as follows:

If `defaultTZ` is :py:data:`None` (the default), 
:class:`~GeoEco.R.RWorkerProcess` will assume that naive 
:py:class:`~datetime.datetime` instances are in the local time zone,
consistent with how many of the Python :py:class:`~datetime.datetime` methods
treat naive instances. :class:`~GeoEco.R.RWorkerProcess` will then look up the
local time zone using the Python `tzlocal
<https://pypi.org/project/tzlocal/>`__ package and apply it when computing
UTC times to send to R.

If `defaultTZ` is a string, a :py:class:`~zoneinfo.ZoneInfo` will be
instantiated and used instead. For example, if you want all naive 
:py:class:`~datetime.datetime` instances to be treated as UTC, provide
``"UTC"`` for `defaultTZ`.

**Getting :py:class:`~datetime.datetime` instances back from R**

For consistency with the behavior described above, if `defaultTZ`
is :py:data:`None` (the default), :class:`~GeoEco.R.RWorkerProcess` will look
up the local time zone using the Python `tzlocal
<https://pypi.org/project/tzlocal/>`__ package and convert all 
:py:class:`~datetime.datetime` instances to that time zone before returning
them. The returned instances will have that time zone defined (they will not
be naive).

If `defaultTZ` is a string, a :py:class:`~zoneinfo.ZoneInfo` will be
instantiated and used instead."""))

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
