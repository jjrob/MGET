Building MGET as a Python wheel
===============================

If you just want to install and use MGET, you do not need to build it first;
please see the :ref:`installation instructions <installing-mget>`. These
instructions assume you have intermediate level competence in developing
Python packages. You should be familiar with working from the command line,
cloning git repos from GitHub with ssh, and building Python packages with
`setuptools <https://pypi.org/project/setuptools/>`_ or similar software.


Building a wheel on Linux
-------------------------

Prerequisites
~~~~~~~~~~~~~

These instructions assume you have the following programs that are usually
already installed as part of your Linux distribution: 

* Git
* Python 3.9 or later
* The C compiler suitable for your version of Python, typically GCC

We suggest you use whatever versions of these programs were provided with your
Linux distribution unless you have a specific reason not to.

.. _building-linux-matlab:

**MATLAB**

MGET includes some functions written in MATLAB. These are the ``.m`` files in
``src/GeoEco/Matlab/_Matlab``. MGET's ``setup.py`` uses the `MATLAB Compiler
<https://www.mathworks.com/products/compiler.html>`_ to compile these
functions into the file ``src/GeoEco/Matlab/_Matlab/_Matlab.ctf``. Performing
this compilation requires that a full (non-free) version of MATLAB R2024b be
`installed <https://www.mathworks.com/help/install/install-products.html>`_.
However, if you do change any of the ``.m`` files, you shouldn't need MATLAB
to build MGET. We keep the compiled ``_Matlab.ctf`` in the source tree, rather
than generating it every time. At build time, ``setup.py`` computes sha256
hashes of all of the ``.m`` files and compares them to the previous values
maintained in ``src/GeoEco/Matlab/_Matlab/MatlabFunctions.txt`` If no files
have changed, ``setup.py`` skips the MATLAB compilation.

Clone the MGET repo and prepare a Python virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, from your shell, clone the MGET repo::

    git clone git@github.com:jjrob/MGET.git

Now create and activate a virtual environment::

    cd MGET
    python3 -m venv .venv
    source .venv/bin/activate

Your shell prompt should now indicate the environment is activated and look
something like ``(.venv) ~/MGET$``, assuming you cloned the repo directly into
your home directory.

Now install the packages needed to build MGET into your virtual environment::

    python3 -m pip install -U pip setuptools setuptools_scm build wheel sphinx sphinx_rtd_theme

Build MGET
~~~~~~~~~~

Now, continuing from your virtual environment::

    python3 -m build

If successful, this will produce a new source distribution
(``mget3-*.tar.gz``) and wheel (``mget3-*.whl``) in the the ``dist``
directory.


Building a wheel on Windows
---------------------------

Typically, Windows users of MGET will also be ArcGIS Pro users. ArcGIS Pro
uses Anaconda Python rather than the reference implementation of Python
released on `python.org <https://python.org>`_. The best experience for ArcGIS
Pro users would be to provide them with a conda package rather than a wheel,
but we have not yet done the work needed to build MGET as a conda package.
Until then, we are building a wheel instead, which can be safely installed
into an ArcGIS Pro conda environment (:doc:`see here <../WindowsWithArc>`).
However, to avoid complications that might arise if we tried to build wheels
with setuptools from within a conda environment, we will not use ArcGIS's
Anaconda Python to build MGET. Instead, we'll install our own copy of Python
from python.org.

Prerequisites
~~~~~~~~~~~~~

Install the following, if they are not installed already:

* `Git for Windows <https://git-scm.com/download/win>`_. This is necessary
  because the build process needs to use git command line tools. `GitHub
  Desktop <https://desktop.github.com/>`_ will not work, although you may
  install it in addition to Git for Windows.

* Git for Windows must be configured to access GitHub over SSH. This used to
  require also installing a separate SSH client such as PuTTY, but with
  Windows 10 and other modern versions of Windows you can use the built-in
  OpenSSH:

  * `Enable the *ssh-agent* service <https://stackoverflow.com/a/68386656>`_,
    start it, and set it to start automatically when Windows starts. This
    service is needed by SSH during authentication but it is disabled by
    default.

  * If you do not already have an SSH key installed in your GitHub account,
    `generate one <https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key>`_
    with *ssh-keygen*, which is part of OpenSSH and should run fine on modern
    versions of Windows. You can run *ssh-keygen* and other SSH utilities from
    a regular Windows Command Prompt or PowerShell. You do not need to use Git
    Bash. After generating the key, extract the public part from the ``.pub``
    file and use it to add a new SSH key in your user settings on github.com.

    * If you already have an SSH key set up in GitHub, you should not generate
      a new key. Instead, you need to find out where your existing key is
      stored (perhaps on a different machine) and copy the private key file
      into ``C:\Users\<name>\.ssh``.

  * At this point, the newly-generated or copied private key should be in
    ``C:\Users\<name>\.ssh``. Now add it to the *ssh-agent*::

        ssh-add <path to private key file>

  * Now instruct Git to use Windows's copy of OpenSSH for SSH access from now
    on::

        git config --global core.sshCommand C:/Windows/System32/OpenSSH/ssh.exe

    This may not be necessary if you instructed the Git for Windows Installer
    to do this for you. But there's no harm in running this command anyway.

* `Python <https://python.org>`_ 3.9 or later. We use this rather than
  ArcGIS's Anaconda Python to build the wheel.

  * Use the "Windows installer (64-bit)" to install it.

  * If you already have ArcGIS installed, be careful about accepting the
    installer's defaults. For example, you may not want to associate this new
    copy of Python with ``.py`` files if ArcGIS's Anaconda Python is already
    associated with them.

* The C/C++ compiler `recommended by Python
  <https://wiki.python.org/moin/WindowsCompilers>`_ for compiling C/C++
  extension modules for Python 3.9 and later. At the time of this writing, the
  recommended compiler was Microsoft Visual C++ version 14.x. For our own
  builds, we used the most recent compiler available, version 14.3, which was
  that included with Visual Studio 2022. (We used the free Visual Studio 2022
  Community Edition.) However, it was also acceptable to use version 14.2
  which was available in the "Build Tools for Visual Studio 2019" (also free),
  which did not require installing a the full release of Visual Studio. For
  those looking to minimize installation time and complexity, that may be a
  better option than Visual Studio.

**MATLAB**

:ref:`As on Linux <building-linux-matlab>`, MATLAB R2024b must be installed in
order to rebuild MGET when any of the ``.m`` files in
``src/GeoEco/Matlab/_Matlab`` have changed. If they have not changed, you
don't need MATLAB.

Clone the MGET repo and prepare a Python virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, start a Command Prompt or the shell you prefer, change directory to the
place where you want to download the MGET repo, and clone it::

    git clone git@github.com:jjrob/MGET.git

If you have not configured Git to access GitHub with SSH, please see the
instructions above first.

Now create and activate a Python virtual environment::

    cd MGET
    C:\Python39\python.exe -m venv .venv
    .venv\Scripts\activate

This example specifically invoked ``python.exe`` using the full path to the
typical installation directory of Python 3.9. You may have installed a
different version or installed it to a different place, or you may have your
Python installation directory in your PATH environment variable, making it
unnecessary to specify the full path to the executable. Adjust the example
accordingly.

Your command prompt should now indicate the environment is activated and look
something like ``(.venv) C:\Users\Jason\Documents\dev\MGET>``.

Now install the packages needed to build MGET into your virtual environment::

    python -m pip install -U pip setuptools setuptools_scm build wheel sphinx sphinx_rtd_theme

Build MGET
~~~~~~~~~~

Now, continuing from your virtual environment::

    python -m build

If successful, this will produce a new source distribution
(``mget3-*.tar.gz``) and wheel (``mget3-*.whl``) in the the ``dist``
directory.


Build warnings and errors you can safely ignore
-----------------------------------------------

On both Linux or Windows, during the building of the wheel, you may see the
following error one or more times::

    ERROR setuptools_scm._file_finders.git listing git files failed - pretending there aren't any

Apparently, this is OK to ignore. See `setuptools_scm issue #997
<https://github.com/pypa/setuptools-scm/issues/997>`_ and `packaging-problems
issue #742 <https://github.com/pypa/packaging-problems/issues/742>`_ for more
information.

You may also ignore the following warning, which appears to occur because the
source tree includes ``.gitignore`` but we use ``MANIFEST.in`` to prune it from
the distribution:: 

    warning: no previously-included files matching '.gitignore' found anywhere in distribution

The build process first excludes it from the sdist, and then seems to complain
when it can't be found when the wheels are built from the sdist.
