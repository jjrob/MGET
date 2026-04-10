Linux with ArcGIS Enterprise
============================

.. Warning::
    We have not tested MGET on Linux with ArcGIS Enterprise yet, so we cannot
    say for certain how best to install it. `ESRI's documentation
    <https://enterprise.arcgis.com/en/server/latest/develop/linux/linux-python.htm>`_
    suggests that ``arcpy`` on Linux runs within conda. Our best guess is that
    getting MGET working with ArcGIS Enterprise requires installing `MGET's
    conda package from conda-forge
    <https://anaconda.org/conda-forge/mget3>`__, known as ``mget3``.

Prerequisites
-------------

- 64-bit x86 processor

- Recent build of a Debian-based distribution; we have only tested Ubuntu and Mint

You may be able to get MGET working on other processors or distributions if
you build MGET from scratch, but we are not currently able to support this.
These instructions are written as if you are running an Ubuntu derivative and
installing the conda package we built.


Optional software
-----------------

These are required to run certain parts of MGET. You can wait to install them
later if desired. MGET will report detailed error messages when missing
optional software is needed.

 - `MATLAB Runtime R2026a
   <https://www.mathworks.com/products/compiler/matlab-runtime.html>`_ (free)
   or the full version of MATLAB R2026a (not free). Either one is OK. These are
   required for front detection, larval dispersal simulation, and certain
   interpolation tools. You must install version R2026a; other versions will
   not work. Multiple versions can be installed at the same time, so if you
   use a different version of MATLAB for your own work, you can continue to do
   so, providing you install the R2026a Runtime for MGET's use.


Step 1: Install Python 3 Runtime for ArcGIS Server on Linux
-----------------------------------------------------------

Install the `Python 3 runtime for ArcGIS Server on Linux
<https://enterprise.arcgis.com/en/server/latest/develop/linux/linux-python.htm>`_
according to ESRI's instructions. This may involve installing conda or
miniconda first.


Step 2: Install MGET from conda-forge
-------------------------------------

We assume that in Step 1, you created and activated a conda environment. We
also assume that ESRI's procedure installed GDAL, the GDAL Python bindings,
numpy, and the numerous other packages that come with ArcGIS Pro into that
environment. Now you can install MGET from conda-forge. From a terminal in
which the conda environment is activated, run::

    conda install --channel esri --channel conda-forge mget3

In our experience on Windows with ArcGIS Pro, this gets stuck with the message
``Solving environment`` for at least 10 minutes, owing to ArcGIS coming with
an old version of conda that had a slow dependency solver. If that happens to
you and you don't want to wait, or if conda can't solve the enviorment, you
could try mamba or micromamba instead.


Uninstalling MGET
-----------------

To uninstall MGET from your conda environment::

    conda remove --yes mget3
