Windows without ArcGIS
======================

Although parts of MGET require ArcGIS, you can still install MGET and use its
much of its Python API without ArcGIS. MGET will report an error message if
you try to use a function that requires ArcGIS and it is not available.


Prerequisites
-------------

- 64-bit x86 processor (ARM is not currently supported)

- Microsoft Windows 10 or later, or Windows Server 2016 or later

- Python 3.9 or later; we have only tested the reference implementations of
  Python released on python.org (known as CPython)


Optional software
-----------------

These are required to run certain parts of MGET. You can wait to install them
later if desired. MGET will report detailed error messages when missing
optional software is needed. Be sure to shut down all ArcGIS programs before
installing them.

 - `MATLAB Runtime R2024b
   <https://www.mathworks.com/products/compiler/matlab-runtime.html>`_ (free)
   or the full version of MATLAB R2024b (not free). Either one is OK. These are
   required for front detection, larval dispersal simulation, and certain
   interpolation tools. You must install version R2024b; other versions will
   not work. Multiple versions can be installed at the same time, so if you
   use a different version of MATLAB for your own work, you can continue to do
   so, providing you install the R2024b Runtime for MGET's use.


Step 1: Verify your Python version
----------------------------------

Start a Command Prompt and verify you can run Python. If Python's installation
directory is in your PATH, then you can simply run::

    python --version

If Windows reports that it is not a recognized command or program, then try
the full path to your Python installation, which is usually something like
this::

    C:\PythonXXX\python.exe --version

where ``XXX`` is something like ``39`` for Python 3.9, ``310`` for Python 3.10,
and so on. Anyway, once you get it working, verify that Python reports version
3.9.0 or later.


Step 2: Create a Python virtual environment (or activate an existing one)
-------------------------------------------------------------------------

We strongly recommend you not install MGET into the site-packages directory of
your Python installation. Instead, create a `virtual environment
<https://docs.python.org/3/library/venv.html>`_ and install it there. If you
don't know about virtual environments, you should read up on them now.

When you're ready, from your Command Prompt, change directory to the location
where you want the virtual environment to live, and run::

    python -m venv .venv
    .venv\Scripts\activate

Replace ``python`` with the full path to your Python executable, if Python's
installation directory is not in your PATH. Replace ``.venv`` with a different
name, if you prefer.

Your prompt should change to something like this::

    (.venv) C:\...>

The critical thing is that you now see ``(.venv)`` at the beginning of the
prompt.


Step 3: Install GDAL and its Python bindings
--------------------------------------------

MGET depends heavily on `GDAL <https://gdal.org/>`_. GDAL 3.8.0 or later is
required, along with the GDAL Python bindings. GDAL can be tricky to install.
If you have already installed it and know it works with your virtual
environment, skip this step.

.. Note::
    If you installed GDAL with conda and want to continue with Anaconda
    Python, please start over with our instructions for :doc:`installing MGET
    on Windows with ArcGIS Pro <WindowsWithArc>` and follow steps 1, 3, and 4
    of those instructions, and ignore the stuff that relates to ArcGIS. Those
    instructions describe how to install MGET with conda. To continue instead
    with a reference implementation of Python released on python.org
    (CPython), read on below.

The easiest way we know of to install GDAL on Windows is to use Christoph
Gohlke's collection of `geospatial library wheels
<https://github.com/cgohlke/geospatial-wheels>`_. As far as we can determine,
Gohlke's wheels statically link most of GDAL's many dependencies and include
the necessary GDAL binaries directly with the Python bindings. This greatly
simplifies installation for users who want to access GDAL from Python.

1. Install the `latest Microsoft Visual C++ Redistributable
   <https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist>`_
   for X64. This is required by Gohlke's wheels. If you already have a recent
   version of Visual Studio installed, you can skip this step. If you are
   unsure, go ahead with the installation; it will let you know if it is
   already installed.

2. Go to the `releases page
   <https://github.com/cgohlke/geospatial-wheels/releases>`_ for Gohlke's
   geospatial-wheels repository. Locate the **Latest** release, which should
   be at the top of the page. Open the **Assets** drop-down, if it is not
   already open. Click the **Show all XXX assets** link. Scroll down until you
   find a file ``GDAL-X.Y.Z-cpVVV-cpVVV-win_amd64.whl`` where ``X.Y.Z`` is the
   GDAL version (must be at least 3.8.0) and ``VVV`` is your Python version
   (e.g. ``39`` for 3.9, ``310`` for 3.10, ...). Download this file.

3. From the same Command Prompt with the activated virtual environment,
   install the downloaded ``.whl`` file using pip::

       python -m pip install -U pip setuptools wheel C:\...\XXXXX.whl

   Replace ``C:\...\XXXXX.whl`` with the full path to the downloaded file.

   .. important::
       Do not replace ``python`` with the full path to your Python executable
       here, or anywhere in the rest of the instructions below. When you
       activated the virtual environment, it added its directory to the PATH,
       and we need invoke Python from there from now on.


Step 4: Install MGET
--------------------

From the same Command Prompt with the activated virtual environment, run::

    python -m pip install mget3

This will install MGET and the other packages it depends upon.

:doc:`Click here <PythonExamples>` for some examples of accessing MGET from
Python.
