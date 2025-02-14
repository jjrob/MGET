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
   less secure than that used by rpy2; see **Security** below.

2. :class:`~GeoEco.R.RWorkerProcess` does not allow as full a range of data
   types to be exchanged between Python and R as rpy2. With
   :class:`~GeoEco.R.RWorkerProcess`, the communication between Python and R
   uses `JSON <https://www.json.org/json-en.html>`__ for exchanging basic
   types and `Apache feather
   <https://arrow.apache.org/docs/python/feather.html>`__ for exchanging data
   frames. These choices simplified implementation but placed some limitations
   on what can be exchanged. Most notably, Python numpy arrays cannot be
   translated to R matrices (although support for this could be added in the
   future). By contrast, rpy2 calls R's C API directly and has implemented
   translation code for more data types, including numpy arrays to R matrices.

3. :class:`~GeoEco.R.RWorkerProcess` does not need to be compiled against a
   specific version of R, and can therefore work with any version of R that
   you have installed, while rpy2 must be recompiled for the R version you
   have, whenever you change it.

4. :class:`~GeoEco.R.RWorkerProcess` supports Microsoft Windows, while rpy2
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
:class:`~GeoEco.R.RWorkerProcess` instance to interact with R. We recommend
you use the ``with`` statement to automatically control the child
process's lifetime:

.. code-block:: python

    from GeoEco.R import RWorkerProcess
    with RWorkerProcess() as r:
        ...
        x = r.Eval('1+1')       # Worker process started here, at the first use of the RWorkerProcess instance
        ...
    print(x)                    # Worker process stopped before this line is executed, after the block above exits

This will start the child process when it is first needed and automatically
stop it when the ``with`` block is exited, even if an exception is raised. 

If desired, you can call :func:`~GeoEco.R.RWorkerProcess.Start` to start it
manually or :func:`~GeoEco.R.RWorkerProcess.Stop` to stop it. We recommend
you use a ``try``/``finally`` block to do it:

.. code-block:: python

    r = RWorkerProcess()
    r.Start()                   # Worker process started here
    try:
        ...
    finally:
        r.Stop()                # Worker process stopped here

Regardless of which style you use, if the R child process is still running
when the Python process exits, the operating system will stop the child
process, even if Python dies without exiting properly.

.. Warning::
    :class:`~GeoEco.R.RWorkerProcess` must install the R plumber package the
    first time it interacts with R, unless the package is already installed.
    Plumber depends on a number of R packages. Installing plumber and its
    dependencies may take several minutes on Windows. On Linux, where R
    package installations typically requiring from C source code, it can take
    20 minutes or more. After this has been done for the first time, it will
    not be necessary to do again, unless you uninstall plumber.

**Evaluating R expressions from Python**

:func:`~GeoEco.R.RWorkerProcess.Eval` accepts a string representing an R
expression, passes it to the R interpreter for evaluation, and returns the
result, translating R types into suitable Python types. You can supply
multiple expressions in a single call, separated by newline characters or
semicolons. The last value of the last expression will be returned:

.. code-block:: python

    >>> from GeoEco.R import RWorkerProcess
    >>> r = RWorkerProcess()
    >>> r.Eval('x <- 6; y <- 7; x * y')
    42      

A variety of R types can be translated into Python types. The rules of
translation are governed by the serialization formats used to marshal data
between Python and R. For most types, JSON is used as the serialization
format, with the `requests <https://pypi.org/project/requests/>`__ package
handling it on the Python side and `plumber <https://www.rplumber.io/>`__ on
the R side. In general, R vectors, lists, and data frames are supported, as
follows:

* R vectors of length 1, sometimes known as atomic values, with the type
  ``logical``, ``integer``, ``double``, or ``character`` are returned as
  Python :py:class:`bool`, :py:class:`int`, :py:class:`float`, and
  :py:class:`str`, respectively:

  .. code-block:: python

    >>> r.Eval('TRUE')
    True
    >>> r.Eval('123')
    123
    >>> r.Eval('pi')
    3.141592653589793
    >>> r.Eval('"Hello, world"')
    'Hello, world'

  Those atomic types are also returned even if you use R's ``c()`` function to
  create a length 1 vector. (It does not matter how you construct it; if the
  vector has length 1, the atomic types are returned.)

    >>> r.Eval('c(TRUE)')
    True
    >>> r.Eval('c(123)')
    123
    >>> r.Eval('c(pi)')
    3.141592653589793
    >>> r.Eval('c("Hello, world")')
    'Hello, world'

* R vectors of length 2 or more are returned as a Python :py:class:`list`:

  .. code-block:: python

    >>> r.Eval('c(1,2,3)')
    [1, 2, 3]

* R unnamed lists are also returned as a :py:class:`list`. In this case, a
  list of length 1 is *not* returned as an atomic type, but as a
  :py:class:`list` with one item:

  .. code-block:: python

    >>> r.Eval('list(1)')
    [1]
    >>> r.Eval('list(1,2,3)')
    [1, 2, 3]
    >>> r.Eval('list(c(1, 2, 3))')
    [[1, 2, 3]]
    >>> r.Eval('list(c(1,2,3), c("A", "B", "C"))')
    [[1, 2, 3], ['A', 'B', 'C']]

* R vectors and lists of length 0 are returned as an empty :py:class:`list`:

  .. code-block:: python

    >>> r.Eval('logical(0)')
    []
    >>> r.Eval('integer(0)')
    []
    >>> r.Eval('numeric(0)')
    []
    >>> r.Eval('character(0)')
    []
    >>> r.Eval('list()')
    []

* R named lists are returned as a Python :py:class:`dict`:

  .. code-block:: python

    >>> r.Eval('list(a=1, b=2, c=3)')
    {'a': 1, 'b': 2, 'c': 3}
    >>> r.Eval('list(a=c(1,2,3), b=4, c=c("A", "B", "C"))')
    {'a': [1, 2, 3], 'b': 4, 'c': ['A', 'B', 'C']}

* R vectors of ``POSIXt`` (i.e. ``POSIXct`` or ``POSIXlt``) are returned as
  Python :py:class:`~datetime.datetime` instances:

  .. code-block:: python

    >>> r.Eval('Sys.time()')
    datetime.datetime(2025, 2, 5, 15, 13, 47, 641000, tzinfo=zoneinfo.ZoneInfo(key='America/New_York'))

  Time values obtained from R will have millisecond precision, even if R
  itself has higher precision. The millisecond limitation results from the
  format used by the R plumber package to represent times in JSON.

  The `defaultTZ` parameter of the :class:`~GeoEco.R.RWorkerProcess`
  constructor determines the time zone that all ``POSIXt`` objects will be
  converted to when they are returned to Python. By default, it is the time
  zone of the Python process, as returned by ``get_localzone()`` from the
  `tzlocal <https://pypi.org/project/tzlocal/>`__ package. To specify a
  different timezone, provide it to the :class:`~GeoEco.R.RWorkerProcess`
  constructor:

  .. code-block:: python

    >>> r = RWorkerProcess(defaultTZ='America/Los_Angeles')
    >>> r.Eval('Sys.time()')
    datetime.datetime(2025, 2, 5, 12, 13, 47, 641000, tzinfo=zoneinfo.ZoneInfo(key='America/Los_Angeles'))

  See the documentation for `defaultTZ` for more information.

* R ``NA`` is returned as a Python :py:data:`None`:

  .. code-block:: python

    >>> r.Eval('NA') is None
    True
    >>> r.Eval('c(1, 2, NA, 3)')
    [1, 2, None, 3]

* R data frames are returned as Python pandas DataFrames:

  .. code-block:: python

    >>> df = r.Eval('iris')
    >>> df.info()
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 150 entries, 0 to 149
    Data columns (total 5 columns):
     #   Column        Non-Null Count  Dtype   
    ---  ------        --------------  -----   
     0   Sepal.Length  150 non-null    float64 
     1   Sepal.Width   150 non-null    float64 
     2   Petal.Length  150 non-null    float64 
     3   Petal.Width   150 non-null    float64 
     4   Species       150 non-null    category
    dtypes: category(1), float64(4)
    memory usage: 5.1 KB
    >>> df.head()
       Sepal.Length  Sepal.Width  Petal.Length  Petal.Width Species
    0           5.1          3.5           1.4          0.2  setosa
    1           4.9          3.0           1.4          0.2  setosa
    2           4.7          3.2           1.3          0.2  setosa
    3           4.6          3.1           1.5          0.2  setosa
    4           5.0          3.6           1.4          0.2  setosa

* Arbitrary R objects not covered above are usually converted to an R list
  with R's ``unclass()`` and then returned as Python :py:class:`dict`\\ s: 

  .. code-block:: python

    >>> model = r.Eval('lm(dist ~ speed, data = cars)')
    >>> from pprint import pprint
    >>> pprint(model, width=150, compact=True)
    {'assign': [0, 1],
     'call': {},
     'coefficients': [-17.579094890510934, 3.932408759124087],
     'df.residual': 48,
     'effects': [-303.9144945539781, 145.55225504575705, -8.115439504379111, 9.884560495620892, 0.194114676507422, -9.49633114260605, -5.186776961719519,
                 2.8132230382804804, 10.81322303828048, -9.87722278083299, 1.1227772191670096, -16.56766859994646, -10.56766859994646, -6.56766859994646,
                 -2.5676685999464604, -8.25811441905993, -0.2581144190599315, -0.2581144190599315, 11.74188558094007, -11.948560238173402,
                 -1.948560238173402, 22.0514397618266, 42.05143976182659, -21.63900605728687, -15.639006057286872, 12.360993942713128,
                 -13.329451876400343, -5.329451876400342, -17.019897695513812, -9.019897695513812, 0.9801023044861885, -10.710343514627283,
                 3.2896564853727175, 23.289656485372713, 31.289656485372713, -20.400789333740754, -10.400789333740754, 11.599210666259246,
                 -28.091235152854225, -12.091235152854225, -8.091235152854225, -4.091235152854224, 3.908764847145776, -1.4721267910811655,
                 -17.162572610194637, -4.853018429308115, 17.146981570691885, 18.146981570691885, 45.146981570691885, 6.456535751578421],
     'fitted.values': [-1.8494598540146354, -1.8494598540145883, 9.94776642335767, 9.947766423357667, 13.880175182481754, 17.81258394160584,
                       21.74499270072993, 21.74499270072993, 21.74499270072993, 25.677401459854018, 25.677401459854018, 29.609810218978105,
                       29.6098102189781, 29.609810218978105, 29.609810218978105, 33.54221897810219, 33.54221897810219, 33.54221897810219,
                       33.54221897810219, 37.47462773722628, 37.47462773722628, 37.47462773722627, 37.474627737226285, 41.40703649635036,
                       41.407036496350365, 41.407036496350365, 45.33944525547445, 45.33944525547445, 49.27185401459854, 49.27185401459854,
                       49.27185401459854, 53.204262773722625, 53.204262773722625, 53.20426277372263, 53.20426277372263, 57.13667153284671,
                       57.13667153284671, 57.13667153284671, 61.0690802919708, 61.0690802919708, 61.0690802919708, 61.0690802919708, 61.0690802919708,
                       68.93389781021898, 72.86630656934307, 76.79871532846715, 76.79871532846715, 76.79871532846715, 76.79871532846715,
                       80.73112408759124],
     'model': [{'dist': 2, 'speed': 4}, {'dist': 10, 'speed': 4}, {'dist': 4, 'speed': 7}, {'dist': 22, 'speed': 7}, {'dist': 16, 'speed': 8},
               {'dist': 10, 'speed': 9}, {'dist': 18, 'speed': 10}, {'dist': 26, 'speed': 10}, {'dist': 34, 'speed': 10}, {'dist': 17, 'speed': 11},
               {'dist': 28, 'speed': 11}, {'dist': 14, 'speed': 12}, {'dist': 20, 'speed': 12}, {'dist': 24, 'speed': 12}, {'dist': 28, 'speed': 12},
               {'dist': 26, 'speed': 13}, {'dist': 34, 'speed': 13}, {'dist': 34, 'speed': 13}, {'dist': 46, 'speed': 13}, {'dist': 26, 'speed': 14},
               {'dist': 36, 'speed': 14}, {'dist': 60, 'speed': 14}, {'dist': 80, 'speed': 14}, {'dist': 20, 'speed': 15}, {'dist': 26, 'speed': 15},
               {'dist': 54, 'speed': 15}, {'dist': 32, 'speed': 16}, {'dist': 40, 'speed': 16}, {'dist': 32, 'speed': 17}, {'dist': 40, 'speed': 17},
               {'dist': 50, 'speed': 17}, {'dist': 42, 'speed': 18}, {'dist': 56, 'speed': 18}, {'dist': 76, 'speed': 18}, {'dist': 84, 'speed': 18},
               {'dist': 36, 'speed': 19}, {'dist': 46, 'speed': 19}, {'dist': 68, 'speed': 19}, {'dist': 32, 'speed': 20}, {'dist': 48, 'speed': 20},
               {'dist': 52, 'speed': 20}, {'dist': 56, 'speed': 20}, {'dist': 64, 'speed': 20}, {'dist': 66, 'speed': 22}, {'dist': 54, 'speed': 23},
               {'dist': 70, 'speed': 24}, {'dist': 92, 'speed': 24}, {'dist': 93, 'speed': 24}, {'dist': 120, 'speed': 24}, {'dist': 85, 'speed': 25}],
     'qr': {'pivot': [1, 2],
            'qr': [[-7.0710678118654755, -108.8944443027283], [0.1414213562373095, 37.0135110466435], [0.1414213562373095, 0.18878369792756214],
                   [0.1414213562373095, 0.18878369792756214], [0.1414213562373095, 0.16176653657964718], [0.1414213562373095, 0.13474937523173222],
                   [0.1414213562373095, 0.10773221388381726], [0.1414213562373095, 0.10773221388381726], [0.1414213562373095, 0.10773221388381726],
                   [0.1414213562373095, 0.0807150525359023], [0.1414213562373095, 0.0807150525359023], [0.1414213562373095, 0.05369789118798735],
                   [0.1414213562373095, 0.05369789118798735], [0.1414213562373095, 0.05369789118798735], [0.1414213562373095, 0.05369789118798735],
                   [0.1414213562373095, 0.026680729840072397], [0.1414213562373095, 0.026680729840072397], [0.1414213562373095, 0.026680729840072397],
                   [0.1414213562373095, 0.026680729840072397], [0.1414213562373095, -0.00033643150784255907],
                   [0.1414213562373095, -0.00033643150784255907], [0.1414213562373095, -0.00033643150784255907],
                   [0.1414213562373095, -0.00033643150784255907], [0.1414213562373095, -0.027353592855757516],
                   [0.1414213562373095, -0.027353592855757516], [0.1414213562373095, -0.027353592855757516], [0.1414213562373095, -0.05437075420367247],
                   [0.1414213562373095, -0.05437075420367247], [0.1414213562373095, -0.08138791555158742], [0.1414213562373095, -0.08138791555158742],
                   [0.1414213562373095, -0.08138791555158742], [0.1414213562373095, -0.10840507689950238], [0.1414213562373095, -0.10840507689950238],
                   [0.1414213562373095, -0.10840507689950238], [0.1414213562373095, -0.10840507689950238], [0.1414213562373095, -0.13542223824741734],
                   [0.1414213562373095, -0.13542223824741734], [0.1414213562373095, -0.13542223824741734], [0.1414213562373095, -0.1624393995953323],
                   [0.1414213562373095, -0.1624393995953323], [0.1414213562373095, -0.1624393995953323], [0.1414213562373095, -0.1624393995953323],
                   [0.1414213562373095, -0.1624393995953323], [0.1414213562373095, -0.2164737222911622], [0.1414213562373095, -0.24349088363907717],
                   [0.1414213562373095, -0.27050804498699216], [0.1414213562373095, -0.27050804498699216], [0.1414213562373095, -0.27050804498699216],
                   [0.1414213562373095, -0.27050804498699216], [0.1414213562373095, -0.2975252063349071]],
            'qraux': [1.1414213562373094, 1.269835181971307],
            'rank': 2,
            'tol': 1e-07},
     'rank': 2,
     'residuals': [3.8494598540146354, 11.849459854014588, -5.94776642335767, 12.052233576642333, 2.119824817518246, -7.812583941605841,
                   -3.744992700729929, 4.255007299270071, 12.255007299270071, -8.677401459854016, 2.3225985401459837, -15.609810218978105,
                   -9.609810218978101, -5.609810218978103, -1.609810218978103, -7.54221897810219, 0.4577810218978093, 0.4577810218978093,
                   12.45778102189781, -11.474627737226276, -1.474627737226278, 22.525372262773725, 42.525372262773715, -21.40703649635036,
                   -15.407036496350365, 12.592963503649635, -13.339445255474452, -5.339445255474452, -17.27185401459854, -9.271854014598537,
                   0.7281459854014627, -11.204262773722625, 2.795737226277375, 22.79573722627737, 30.79573722627737, -21.136671532846712,
                   -11.136671532846712, 10.863328467153288, -29.0690802919708, -13.0690802919708, -9.0690802919708, -5.0690802919708, 2.9309197080292,
                   -2.933897810218975, -18.866306569343063, -6.798715328467158, 15.201284671532843, 16.201284671532843, 43.20128467153284,
                   4.268875912408762],
     'terms': {},
     'xlevels': {}}

* When an R expression evaluates to ``NULL`` in R, a :py:data:`None` is
  returned. Note that this includes the R expression ``c()``:

  .. code-block:: python

    >>> r.Eval('NULL') is None
    True
    >>> r.Eval('c()') is None
    True

  However, the usual R rules about how ``NULL`` is handled by R still apply.
  For example, R removes ``NULL`` elements from R vectors. This can yield
  results that may be unexpected by Python developers:

  .. code-block:: python

    >>> r.Eval('c(1, 2)')
    [1, 2]
    >>> r.Eval('c(1, NULL)')
    1
    >>> r.Eval('c(1, NULL, NULL)')
    1
    >>> r.Eval('c(1, NULL, NULL, 2)')
    [1, 2]
    >>> r.Eval('c(NULL, NULL, NULL, NULL)') is None
    True

  But R does not remove ``NULL`` from R lists, and it will be translated to
  :py:data:`None`:

  .. code-block:: python

    >>> r.Eval('list(NULL)')
    [None]
    >>> r.Eval('list(NULL, NULL, NULL)')
    [None, None, None]
    >>> r.Eval('list(a=NULL, b=NULL, c=NULL)')
    {'a': None, 'b': None, 'c': None}

**Getting and setting R variables from Python**

You can get and set variables in the R interpreter through the dictionary
interface of the :class:`~GeoEco.R.RWorkerProcess` instance:

.. code-block:: python

    >>> r['my_variable'] = 42     # Set my_variable to 42 in the R interpreter
    >>> print(r['my_variable'])   # Get back the value of my_variable and print it
    42
    >>> print(list(r.keys()))     # Print a list of the variables defined in the R interpreter
    ['my_variable']
    >>> del r['my_variable']      # Delete my_variable from the R interpreter

Python types will be automatically translated to and from R types as described
above.

**Unexpected behaviors**

Because of differences between R and Python and the imperfectness of JSON and
feather as data marshaling formats, there some unexpected behaviors,
including:

* In an R ``double`` vector, any value that happens to be an integer is
  returned to Python as an :py:class:`int`:

  .. code-block:: python

    >>> r.Eval('typeof(1.0)')
    'double'
    >>> type(r.Eval('1.0'))
    <class 'int'>
    >>> r.Eval('typeof(c(1,2,3.3))')
    'double'
    >>> [type(x) for x in r.Eval('c(1,2,3.3)')]
    [<class 'int'>, <class 'int'>, <class 'float'>]

* If you set an R variable to a Python :py:class:`list` that has a length of 1
  and then get it back from R, it will no longer be a :py:class:`list`:

  .. code-block:: python

    >>> r['x'] = [1]
    >>> r['x']
    1

  This is because in R, atomic values are actually stored as length 1 vectors,
  while Python distinguishes between the two. When returning a length 1 vector
  to Python, we can't determine if it would be best represented as an atomic
  value (e.g. :py:class:`int`) or as a :py:class:`list` with a single value in
  it. We judged that an atomic value would be appropriate more of the time,
  and lacking any way to determine otherwise, we designed
  :class:`~GeoEco.R.RWorkerProcess` to always translate length 1 vectors into
  atomic values.

* R ``complex`` is not supported (because JSON does not support complex
  numbers) and is returned as Python :py:class:`str`:

  .. code-block:: python

      >>> r.Eval('c(1+2i, 3-5i, 6)')
      ['1+2i', '3-5i', '6+0i']

**Character encoding**

Data are exchanged with R in UTF-8:

.. code-block:: python

    >>> r.Eval('"Café, résumé, naïve, jalapeño"')
    'Café, résumé, naïve, jalapeño'
    >>> r.Eval('"Python 🐍 is awesome! 你好! Привет!"')
    'Python 🐍 is awesome! 你好! Привет!'

**Logging and error handling**

Messages written by R to R's stdout pipe, e.g. with the the R ``cat()``
function, are logged to the Python ``GeoEco.R`` logger as INFO messages.
Messages written by R to its stderr pipe, e.g. with the R ``message()``
function, are logged to the ``GeoEco.R`` logger as WARNING messages.

  .. code-block:: python

    >>> from GeoEco.Logging import Logger
    >>> Logger.Initialize()
    >>> from GeoEco.R import RWorkerProcess
    >>> r = RWorkerProcess()
    >>> x = r.Eval('print(pi)')
    2025-02-05 16:19:09.213 INFO [1] 3.141593
    >>> r.Eval('cat("Hello, world!\\n")')
    2025-02-05 16:19:56.232 INFO Hello, world!
    >>> r.Eval('message("Something might be wrong")')
    2025-02-05 16:20:19.721 WARNING Something might be wrong

If an error is signaled in R and not caught before the signal propagates back
up to the plumber API, it is sent back to Python and :exc:`RuntimeError` will
be raised:

  .. code-block:: python

    >>> r.Eval('stop("There is a problem!")')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/jason/Development/MGET/src/GeoEco/R/_RWorkerProcess.py", line 994, in Eval
        return(self._ProcessResponse(resp, parseReturnValue=True))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/home/jason/Development/MGET/src/GeoEco/R/_RWorkerProcess.py", line 745, in _ProcessResponse
        raise RuntimeError(f'From R: {respJSON["message"]}')
    RuntimeError: From R: Error in eval(parsedExpr, envir = clientEnv, enclos = baseenv()): There is a problem!

You can get a detailed view of the exchange of data between Python and R by
turning on DEBUG logging for the `GeoEco.R` logger, either programmatically as
shown below or by configuring GeoEco's logging configuration file (see
:func:`GeoEco.Logging.Logger.Initialize`).

  .. code-block:: python

    >>> from GeoEco.Logging import Logger
    >>> Logger.Initialize()
    >>> import logging
    >>> logging.getLogger('GeoEco.R').setLevel(logging.DEBUG)
    >>> from GeoEco.R import RWorkerProcess
    >>> r = RWorkerProcess()
    >>> r['x'] = [1,2,3,4,5]
    2025-02-05 16:55:14.946 DEBUG R: SET: x <- length 5 integer:
    2025-02-05 16:55:14.946 DEBUG R:   [1] 1 2 3 4 5
    >>> r.Eval('x*2')
    2025-02-05 16:55:31.475 DEBUG R: EVAL: x*2
    2025-02-05 16:55:31.475 DEBUG R: RESULT: length 5 numeric:
    2025-02-05 16:55:31.475 DEBUG R:           [1]  2  4  6  8 10
    [2, 4, 6, 8, 10]
    >>> df = r.Eval('iris')
    2025-02-05 17:00:02.296 DEBUG R: EVAL: iris
    2025-02-05 17:00:02.296 DEBUG R: RESULT: data.frame with 150 rows, 5 columns

**Security**

As noted, communication between Python and R occurs over HTTP over TCP/IP.
This raises the possibility of a malicious party exploiting the communication
channel. To mitigate this, R listens on the loopback interface (IPv4 address
127.0.0.1), which is only accessible to processes running on the local
machine, and uses a randomly-selected TCP port. If a local process does
discover the port (e.g. via scanning all local ports) and tries to invoke the
REST APIs exposed by R, to succeed it must guess a 512-bit randomly-generated
token, which is extremely improbable. However, a malicious local process could
still mount a denial of service attack on the R interface by flooding it with
bogus requests. Because R is single-threaded, such an attack might starve
Python of the opportunity to place its own calls. It would also maximize
utilization of one processor.

**Constructor**
"""))

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
"""On Windows: the path to the directory where R is installed, if you do not
want R's installation directory to be discovered automatically. You can
determine the installation directory from within R by executing the function
``R.home()``. If this parameter is not provided, the installation directory
will be located automatically. Three methods will be tried, in this order:

1. If the R_HOME environment variable has been set, it will be used. The
   program Rscript.exe must exist in the ``bin\\x64`` subdirectory of R_HOME
   or a :py:exc:`FileNotFoundError` exception will be raised.

2. Otherwise (R_HOME has not been set), the Registry will be checked, starting
   with the ``HKEY_CURRENT_USER\\Software\\R-core`` key and falling back to
   ``HKEY_LOCAL_MACHINE\\Software\\R-core`` only if the former does not exist.
   For whichever exists, the value of ``R64\\InstallPath`` will be used. The
   program Rscript.exe must exist in the ``bin\\x64`` subdirectory of that
   directory or a :py:exc:`FileNotFoundError` exception will be raised.

3. Otherwise (neither of those registry keys exist), the PATH environment
   variable will be checked for the program Rscript.exe. If it does not exist,
   :py:exc:`FileNotFoundError` exception will be raised.

On other operating systems: this parameter is ignored, and R's executables are
expected to be available through via the PATH environment variable."""),
    arcGISDisplayName=_('R home directory'),
    arcGISCategory=_('R options'))

AddArgumentMetadata(RWorkerProcess.__init__, 'rLibDir',
    typeMetadata=DirectoryTypeMetadata(canBeNone=True),
    description=_(
"""Path to the R library directory where R packages should be stored. When a
package is needed, it will be loaded from this directory if it exists there,
and downloaded there it does not exist. If not provided, R's default will be
used. See the `R documentation
<https://cran.r-project.org/doc/manuals/r-release/R-admin.html#Managing-libraries>`__
for details.

You should provide a custom directory if you want MGET to maintain its own set
of R packages, rather than those you use when running R yourself. For
example, when running MGET, you may want to use only packages that have been
released to CRAN, while when running R yourself, you may want to use newer or
experimental versions that you obtained elsewhere."""),
    arcGISDisplayName=_('R package library directory'),
    arcGISCategory=_('R options'))

AddArgumentMetadata(RWorkerProcess.__init__, 'rRepository',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""R repository to use when downloading packages. If not provided,
https://cloud.r-project.org will be used."""), 
    arcGISDisplayName=_('R repository for downloading packages'),
    arcGISCategory=_('R options'))

AddArgumentMetadata(RWorkerProcess.__init__, 'rPackages',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx=r'^[a-zA-Z][a-zA-Z0-9_\.]*$'), canBeNone=True),
    description=_(
"""List of R packages to ensure are installed. For each package that is
provided, MGET will check whether it is installed. If it is not, MGET will
install it. If it is, MGET will do nothing. To update already-installed
packages, use the `updateRPackages` parameter.

MGET does not automatically "load" the packages given here. If you need to
load them, make sure the expressions include a call to ``load()``, or
another suitable function."""),
    arcGISDisplayName=_('Required R packages'))   # Note that this does not have an arcGISCategory by default

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
    arcGISDisplayName=_('Update R packages automatically'),
    arcGISCategory=_('R options'))

AddArgumentMetadata(RWorkerProcess.__init__, 'port',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""TCP port to use for communicating with R via the R plumber package. If not
specified, an unused port will be selected automatically."""), 
    arcGISDisplayName=_('Port'),
    arcGISCategory=_('R options'))

AddArgumentMetadata(RWorkerProcess.__init__, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Maximum amount of time, in seconds, that a call into R is allowed to take
to start responding when getting, setting, or deleting variable values. If
this time elapses without the R worker process beginning to send its
response, an error will be raised. In general, a very short value such as 5
seconds is appropriate here. To allow an infinite amount of time, provide 
:py:data:`None` from Python or delete all text from this text box in the
ArcGIS user interface.

.. Warning::
    If you allow an infinite amount of time and R never responds, your program
    will be blocked forever. Use caution.

"""), 
    arcGISDisplayName=_('Timeout'),
    arcGISCategory=_('R options'))

AddArgumentMetadata(RWorkerProcess.__init__, 'startupTimeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Maximum amount of time, in seconds, that R is allowed to take to initialize
itself and begin servicing requests. This time is usually only a second or
two, but can be longer if the machine is busy. Because of this, the default
is set to 15 seconds. If the timeout elapses without the R process indicating
that it is ready, an error will be raised. To allow an infinite amount of
time, provide :py:data:`None` from Python or delete all text from this text
box in the ArcGIS user interface.

If packages must be installed or updated, as usually occurs the first time you
use MGET to interact with R, the delay is automatically extended to allow
package installation to complete.

.. Warning::
    If you allow an infinite amount of time and R never responds, your program
    will be blocked forever. Use caution.

"""), 
    arcGISDisplayName=_('Startup timeout'),
    arcGISCategory=_('R options'))

AddArgumentMetadata(RWorkerProcess.__init__, 'defaultTZ',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Name of the time zone to use when 1) setting R variables from time-zone
naive :py:class:`~datetime.datetime` instances, 2) returning
:py:class:`~datetime.datetime` instances from R. The time zone names are those
from the `IANA Time Zone Database <https://www.iana.org/time-zones>`__. At the
time of this writing, many of the names were `conveniently listed in Wikipedia
<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`__

**Setting R variables using naive datetime instances**

When a :py:class:`~datetime.datetime` instance is sent to R, it is converted
to an R ``POSIXct`` object, which represents time as the number of seconds
since the UNIX epoch, which is defined as 1970-01-01 00:00:00 UTC. Because of
this, MGET needs to know which time zone the :py:class:`~datetime.datetime`
instance is in so that it can be converted to UTC for R.

If a :py:class:`~datetime.datetime` instance has a time zone defined (meaning
that its `tzinfo` attribute is not :py:data:`None`), then MGET will apply that
time zone when computing UTC times to send to R. But if it does not have a
time zone defined, it is known as a "naive" :py:class:`~datetime.datetime`. In
this case, this default time zone parameter (`defaultTZ`) determines the time
zone to use, as follows:

If `defaultTZ` is :py:data:`None` (the default), MGET will assume that naive
:py:class:`~datetime.datetime` instances are in the local time zone,
consistent with how many of the Python :py:class:`~datetime.datetime` methods
treat naive instances. MGET will then look up the local time zone using the
Python `tzlocal <https://pypi.org/project/tzlocal/>`__ package and apply it
when computing UTC times to send to R.

If `defaultTZ` is a string, a :py:class:`~zoneinfo.ZoneInfo` will be
instantiated from it and used instead. For example, if you want all naive
:py:class:`~datetime.datetime` instances to be treated as UTC, provide
``'UTC'`` for `defaultTZ`.

**Getting datetime instances back from R**

For consistency with the behavior described above, if `defaultTZ` is
:py:data:`None` (the default), MGET will look up the local time zone using the
Python `tzlocal <https://pypi.org/project/tzlocal/>`__ package and convert all
:py:class:`~datetime.datetime` instances to that time zone before returning
them. The returned instances will have that time zone defined (they will not
be naive).

If `defaultTZ` is a string, a :py:class:`~zoneinfo.ZoneInfo` will be
instantiated and used instead."""), 
    arcGISDisplayName=_('Default time zone'),
    arcGISCategory=_('R options'))

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

CopyArgumentMetadata(RWorkerProcess.__init__, 'self', RWorkerProcess.Stop, 'self')

AddArgumentMetadata(RWorkerProcess.Stop, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Maximum amount of time, in seconds, to wait for R to shut down. In
general, R should shut down quickly. During normal operation, all interactions
with R are blocking, so R should be idle when this function is called. To
allow an infinite amount of time, provide :py:data:`None` from Python or
delete all text from this text box in the ArcGIS user interface.

.. Warning::
    If you allow an infinite amount of time and R never stops, your program
    will be blocked forever. Use caution.

"""), 
    arcGISDisplayName=_('Timeout')) 

# Public method: Eval

AddMethodMetadata(RWorkerProcess.Eval,
    shortDescription=_('Evaluate an R expression and return the result.'),
    longDescription=_(
"""The expression can be anything that may be evaluated by the R ``eval``
function. Multiple expressions can be separated by semicolons or newlines.
The value of the last expression is returned. Please see the
:class:`~GeoEco.R.RWorkerProcess` class documentation for details on how R
data types are translated into Python data types."""))

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
"""Maximum amount of time, in seconds, that R is permitted to run while
evaluating the expressions before it must return a result. If this time
elapses without the R worker process beginning to send its response, an error
will be raised.

The default timeout was selected to allow all but the most time consuming
expressions to complete. You should increase it for very long running jobs.
If you're unsure how long it will take, you may allow an infinite amount of
time by providing :py:data:`None` from Python or deleting all text from this
text box in the ArcGIS user interface.

.. Warning::
    If you allow an infinite amount of time and your R expression never
    completes, your program will be blocked forever. Use caution.

"""), 
    arcGISDisplayName=_('Timeout'))

# Public method: ExecuteRAndEvaluateExpressions

AddMethodMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions,
    shortDescription=_('Start R, evaluate one or more R expressions, stop R, and optionally return the result of the last expression.'),
    longDescription=_(
"""The R statistics program version 3.3 or later must be installed. R can be
downloaded from https://cran.r-project.org/.

The Rscript program from R will be started as a child worker process with
no visible user interface and MGET will communicate through it with HTTP over
TCP/IP. Rscript will listen on the loopback interface (IPv4 address
127.0.0.1), and therefore will only be accessible to processes running on the
local machine. To prevent anything other than the intended parent process from
interacting with the Rscript worker process, it requires all callers to
provide a randomly-generated 512 bit token only known by the parent process.
After the final expression is executed, Rscript will be shut down.

For more information about how this works, please see the documentation for
the RWorkerProcess class in MGET's documentation."""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Evaluate R Expressions'),
    arcGISToolCategory=_('Statistics'))

AddArgumentMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=RWorkerProcess),
    description=_(':class:`%s` or an instance of it.') % RWorkerProcess.__name__)

AddArgumentMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions, 'expressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1),
    description=_(
"""List of R expressions to evaluate. Each expression can be anything that may
be evaluated by the R ``eval`` function. Empty strings or strings composed
only of whitespace characters are not allowed."""),
    arcGISDisplayName=_('R expressions'))

AddArgumentMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions, 'returnResult',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the value of the last expression will be returned. If False, the
default, a Python :py:data:`None` will be returned, regardless of what the
last expression evaluated to."""),
    arcGISDisplayName=_('Return result'))

AddArgumentMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions, 'timeout',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""After R has started up and installed any necessary packages, this is the
maximum amount of time, in seconds, that it is permitted to run while
evaluating the expressions before it must return a result. If this time
elapses without the R worker process beginning to send its response, an error
will be raised.

The default timeout was selected to allow all but the most time consuming
expressions to complete. You should increase it for very long running jobs.
If you're unsure how long it will take, you may allow an infinite amount of
time by providing :py:data:`None` from Python or deleting all text from this
text box in the ArcGIS user interface.

.. Warning::
    If you allow an infinite amount of time and your R expression never
    completes, your program will be blocked forever. Use caution.

"""), 
    arcGISDisplayName=_('Timeout'))

CopyArgumentMetadata(RWorkerProcess.__init__, 'rPackages', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'rPackages')
CopyArgumentMetadata(RWorkerProcess.__init__, 'rInstallDir', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'rInstallDir')
CopyArgumentMetadata(RWorkerProcess.__init__, 'rLibDir', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'rLibDir')
CopyArgumentMetadata(RWorkerProcess.__init__, 'rRepository', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'rRepository')
CopyArgumentMetadata(RWorkerProcess.__init__, 'updateRPackages', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'updateRPackages')
CopyArgumentMetadata(RWorkerProcess.__init__, 'port', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'port')
CopyArgumentMetadata(RWorkerProcess.__init__, 'startupTimeout', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'startupTimeout')
CopyArgumentMetadata(RWorkerProcess.__init__, 'defaultTZ', RWorkerProcess.ExecuteRAndEvaluateExpressions, 'defaultTZ')

AddArgumentMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions, 'variableNames',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), canBeNone=True),
    description=_(
"""A list of names of variables to define in the R interpreter before the R
expressions are evaluated.

This list must have the same number of entries as the Variable Values
parameter. This list specifies the names of the variables that will be defined
and that list specifies their values.

These two parameters are useful when you need to pass input data that will be
used in your R expressions. You can initialize variables to values you
specify, and then refer to the variables in the R expressions. For example,
you might define a variable named ``inputCSVFile`` and then include the
following R expressions to read the table and print a summary::

    x = read.csv(inputCSVFile)
    print(summary(x))

"""),
    arcGISDisplayName=_('Variable names'),
    arcGISCategory=_('R variables to define'))

AddArgumentMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions, 'variableValues',
    typeMetadata=ListTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True), canBeNone=True, mustBeSameLengthAsArgument='variableNames'),
    description=_(
"""A list of values of variables to define in the R interpreter before the R
expressions are evaluated.

This list must have the same number of entries as the Variable Names
parameter. That list specifies the names of the variables that will be
defined and this list specifies their values.

The values you provide are automatically converted to the most appropriate R
data types. Please see the MGET documentation for the RWorkerProcess class for
details. However, because this function is intended to be invoked as an ArcGIS
geoprocessing tool, it handles strings differently that described in that
documentation.

The reason this is necessary is because the ArcGIS geoprocessing framework
passes all parameters to Python tools (such as this one) as strings, making it
impossible to determine the original data type of each parameter simply from
its value. For example, given the string "123", it is impossible to determine
if it was supposed to represent the string "123", the integer 123, or the
floating point number 123.0.

To address this limitation, this function attempts to parse strings into
booleans, integers, floating point numbers, and datetimes, in that order. If a
parsing attempt succeeds, the parsed value is used. If all parsing attempts
fail, it is converted to a string as normal. If a string is empty (it has a
length of zero), it is converted to ``NA`` in R. (If a string contains one or
more whitespace characters, it is not considered empty.)

For example:

* "True" is converted to an R ``logical``
* "5" is converted to an R ``integer``
* "1.05" is converted to an R ``double``
* "2007-12-31 12:34:56" is converted to an R ``POSIXct``.
* "1.05 days" is converted to an R ``character``
* "" is converted to R ``NA``

This tool parses booleans as "true" or "false" (case insensitive). It attempts
to parse dates using a large number of formats, starting with what appears to
be the appropriate formats for the operating system's current locale. If no
time zone is included in the string itself, the time zone is specified by the
`defaultTZ` parameter.

This special parsing logic only applies to atomic string values. It does NOT
apply to collections of strings, such as lists or dictionaries of strings. (It
is only possible to provide such collections when calling this function from
Python; it cannot be done from ArcGIS geoprocessing.)"""),
    arcGISDisplayName=_('Variable values'),
    arcGISCategory=_('R variables to define'))

AddResultMetadata(RWorkerProcess.ExecuteRAndEvaluateExpressions, 'result',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Result returned from the R interpreter. If the evaluated R code contained
multiple expressions, the value of the last expressions is returned. The type
of the returned value depends on the expressions that is evaluated."""),
    arcGISDisplayName=_('Last expression result'))


############################################################################
# This module is not meant to be imported directly. Import GeoEco.R instead.
############################################################################

__all__ = []
