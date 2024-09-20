Installing the new wheel
========================

After :doc:`building MGET as a Python wheel <BuildingWheels>`, you can build
MGET's documentation or run MGET's tests. Before doing so, you must install
the new wheel. You have two options for doing this.


Option 1: Install the wheel in the traditional way
--------------------------------------------------

With this option, you install the newly-built wheel using pip. Just follow the
:ref:`installation instructions on the home page <installing-mget>` to install
MGET into the virtual environment of your choice. If MGET is already
installed, you'll need to uninstall it first as described in those
instructions. When it comes time to install the new wheel, rather than
referencing the ``mget3`` package in the ``pip install`` command, put the path
to the new ``.whl`` file instead.

You must use this option if you're on Windows with ArcGIS and want to test
MGET with ArcGIS. This is because you built the wheel in a virtual environment
created by the Python you installed from python.org but now need to install
MGET into a virtual environment created with ArcGIS's copy of conda. If you're
not on Windows, or you are but don't want to test MGET with ArcGIS, you can
use Option 2 instead, if desired.


Option 2: Install MGET as an "editable install"
-----------------------------------------------

With an `editable install
<https://setuptools.pypa.io/en/latest/userguide/development_mode.html>`_, pip
configures your virtual environment to be able import MGET's package
(``GeoEco``) directly from the source tree. The advantage of this approach is
that you can make changes to Python files in the source tree and then
immediately build MGET's documentation or run MGET's tests without building
and installing the wheel again. It is faster to develop, document, and test
code this way than with Option 1. But it requires that you install MGET into
the same virtual environment that you used to build it. That will not be
possible if you're trying to test MGET with ArcGIS, which requires installing
MGET to an ArcGIS conda environment. In that case, you must use Option 1.

To proceed with an editable install, you first need to ensure that all of the
software prerequisites are met, as listed in the :ref:`installation
instructions on the home page <installing-mget>` for your platform. Then,
rather than using the ``pip install`` command shown in those instructions, run
the following command instead. Do it from the same virtual environment you
used to build MGET. You must be in the MGET root directory. On Linux::

    python3 -m pip install -e .

On Windows, replace ``python3`` with ``python``.

You only need to do this once after creating your virtual environment; after
doing it the first time, any changes you make to the source tree are
automatically visible the next time you import the package.
