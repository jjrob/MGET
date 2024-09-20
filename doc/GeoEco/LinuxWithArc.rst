Linux with ArcGIS Server
========================

.. Warning::
    We have not tested MGET on Linux with ArcGIS Server yet, so we cannot say
    for certain how best to install it. `ESRI's documentation
    <https://enterprise.arcgis.com/en/server/latest/develop/linux/linux-python.htm>`_
    suggests that ArcPy on Linux runs within conda. However, we have not yet
    developed a conda package for MGET, so our best guess is to configure a
    conda environment needed for MGET and then install MGET with pip as the
    last step. Below is our best current guess on how to accomplish this,
    without having tested it yet ourselves. We will update this documentation
    when we are actually able to test this.


Prerequisites
-------------

- 64-bit x86 processor

- Recent build of a Debian-based distribution; we have only tested Ubuntu and Mint

You may be able to get MGET working on other processors or distributions if
you build MGET from scratch, but we are not currently able to support this.
These instructions are written as if you are running an Ubuntu derivative and
use bash as your shell.


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


Step 1: Install Python 3 Runtime for ArcGIS Server on Linux
-----------------------------------------------------------

Install the `Python 3 runtime for ArcGIS Server on Linux
<https://enterprise.arcgis.com/en/server/latest/develop/linux/linux-python.htm>`_
according to ESRI's instructions. This may involve installing conda or
miniconda first.


Step 2: Install packages needed by MGET from conda-forge
--------------------------------------------------------

We assume that in Step 1, you created and activated a conda environment. We
also assume that ESRI's procedure installed GDAL, the GDAL Python bindings,
numpy 1.x, and the numerous other packages that come with ArcGIS Pro into that
environment. Now we need to install a few more Python packages that probably
weren't installed by ESRI's procedure (because they're not part of ArcGIS
Pro's default conda environment).

From a terminal in which the conda environment is activated, run::

    conda install --channel conda-forge --yes copernicusmarine docutils scikit-fmm

In our experience on Windows with ArcGIS Pro 3.2.2, this hung with the message
``Solving environment`` for a very long time, owing to Pro coming with an old
version of conda that had a slow solver. We anticipate the conda or miniconda
you installed in Step 1 contained the improved solver. But if not, you could
try mamba or micromamba instead of conda or miniconda and it might run faster.

Step 3. Install MGET with pip
-----------------------------

Assuming that Step 2 completed successfully, from the same terminal, run::

    python3 -m pip install mget3


Uninstalling MGET
-----------------

To uninstall MGET from your conda environment::

    python -m pip uninstall mget3

Or, if you don't need the virtual environment anymore, you can delete its
directory entirely.
