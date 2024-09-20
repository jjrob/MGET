Linux without ArcGIS
====================


Prerequisites
-------------

- 64-bit x86 processor

- Recent build of a Debian-based distribution; we have only tested Ubuntu and Mint

- Python 3.9 or later; we have only tested CPython (i.e. the reference
  implementations of Python released on python.org)

- `GDAL <https://gdal.org/>`_ 3.8.0 or later

You may be able to get MGET working on other processors, distributions, or
Python implementations if you build MGET from scratch, but we are not
currently able to support this. These instructions are written as if you are
running an Ubuntu derivative and use bash as your shell.


Optional software
-----------------

These are required to run certain parts of MGET. You can wait to install them
later if desired. MGET will report detailed error messages when missing
optional software is needed.

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

Start a terminal and run::

    python3 --version

It should report Python 3.9 or later. If you need to install a new version of
Python instead of using what comes with your Linux distribution, we recommend
`pyenv <https://github.com/pyenv/pyenv>`_ for managing additional
installations.


Step 2: Verify your GDAL version
--------------------------------

MGET depends heavily on `GDAL <https://gdal.org/>`_. GDAL 3.8.0 or later must
be installed. To validate this, start a terminal and run::

    gdalinfo --version

If this doesn't work or reports that GDAL is older than 3.8.0, please install
3.8.0 or later using the package management system appropriate for your Linux
distribution.


Step 3: Create a Python virtual environment (or activate an existing one)
-------------------------------------------------------------------------

We strongly recommend you not install MGET into the site-packages directory of
your system's default Python installation. Instead, create a `virtual
environment <https://docs.python.org/3/library/venv.html>`_ and install it
there. If you don't know about virtual environments, you should read up on
them now.

When you're ready, start a terminal, change directory to the location where
you want the virtual environment to live, and run::

    python3 -m venv .venv
    source .venv/bin/activate

Replace ``.venv`` with a different name, if you prefer.

Your bash prompt should change to something like this::

    (.venv) user@hostname:~$

assuming you created the virtual environment in your home directory. The
critical thing is that you now see ``(.venv)`` at the beginning of the command
prompt.


Step 4: Install Python packages needed for GDAL's Python bindings
-----------------------------------------------------------------

MGET requires GDAL's Python bindings (a.k.a. the ``osgeo`` package), and
GDAL's Python bindings require `numpy <https://numpy.org/>`_ and a couple of
other packages. In order for GDAL's Python bindings to install properly, those
packages *must be installed first*; you cannot rely on pip to install them
when you install GDAL's Python bindings. A second issue is that MGET is not
yet compatible with numpy 2.x. Therefore we need to install numpy 1.x instead.

From the virtual environment you created above::

    python3 -m pip cache purge
    python3 -m pip install -U pip "numpy<2" setuptools wheel

That will install the most recent release of numpy 1.x along with the other
packages needed to install GDAL's Python bindings. Prior to doing this, we use
``pip cache purge`` to force the packages to be redownloaded. (Some users
reported a problem with stale packages and solved it by doing this, so we do
it as precaution.)


Step 5: Install GDAL's Python bindings
--------------------------------------

From the same virtual environment::

    python3 -m pip install gdal==X.Y.Z

where ``X.Y.Z`` is the GDAL version you looked up in Step 2. After this
installation completes successfully, run::

    python3 -c "from osgeo import _gdal_array"

This command should complete with no error. If it fails, you need to debug why
before proceeding to the MGET installation in the next step.


Step 6: Install MGET
--------------------

From the same virtual environment::

    python -m pip install mget3

This will install MGET and the other packages it depends upon.

:doc:`Click here <PythonExamples>` for some examples of accessing MGET from
Python.


Uninstalling MGET
-----------------

To uninstall MGET from your virtual environment::

    python -m pip uninstall mget3

Or, if you don't need the virtual environment anymore, you can delete its
directory entirely.
