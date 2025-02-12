Windows with ArcGIS Pro or Server
=================================


Prerequisites
-------------

- 64-bit x86 processor (ARM is not currently supported)

- Microsoft Windows 10 or later, or Windows Server 2016 or later

- ArcGIS Pro 3.2.2 or later, or ArcGIS Server 11.2 or later


Optional software
-----------------

These are required to run certain parts of MGET. You can wait to install them
later if desired. MGET will report detailed error messages when missing
optional software is needed. Be sure to shut down all ArcGIS programs before
installing them.

- `ArcGIS Spatial Analyst extension <https://www.esri.com/spatialanalyst>`__.
  This is required by a number of MGET tools produce rasters. If your ArcGIS
  license includes this extension but you did not install it, you can re-run
  the ArcGIS setup program to add it to your installation.

- `MATLAB Runtime R2024b
  <https://www.mathworks.com/products/compiler/matlab-runtime.html>`__ (free)
  or the full version of MATLAB R2024b (not free). Either one is OK. These are
  required for front detection, larval dispersal simulation, and certain
  interpolation tools. You must install version R2024b; other versions will
  not work. Multiple versions can be installed at the same time, so if you
  use a different version of MATLAB for your own work, you can continue to do
  so, providing you install the R2024b Runtime for MGET's use.


.. _arcgis-pro-install:

Windows with ArcGIS Pro installation instructions
-------------------------------------------------

MGET is a Python package. ArcGIS Pro utilizes `conda
<https://docs.conda.io/>`__ to manage Python packages, which works best for
projects that have been specifically packaged for deployment with conda. We
have packaged MGET as the `mget3 package on conda-forge
<https://anaconda.org/conda-forge/mget3>`__. We recommend that ArcGIS Pro
users install the conda-forge package rather than installing the
corresponding `mget3 package on the Python Package Index
<https://pypi.org/project/mget3/>`__ with `pip
<https://pypi.org/project/pip/>`__.

Step 1. Install micromamba
~~~~~~~~~~~~~~~~~~~~~~~~~~

At least up through ArcGIS Pro 3.4, trying to use the conda that comes with
ArcGIS Pro to install MGET is problematic. Pro 3.2 and 3.3 shipped with conda
4.14.0, which gets stuck forever at the message "Solving environment" (for
more, see the article `introduction of the libmamba solver
<https://conda.org/blog/2023-07-05-conda-libmamba-solver-rollout/>`__). Pro
3.4 shipped with an updated version of conda, but it contains a buggy
dependency checker that cannot install MGET (see `issue #18
<https://github.com/jjrob/MGET/issues/18>`__.)

You can work around these problems by using `micromamba
<https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html>`__
instead. Micromamba is a stand-alone, drop-in replacement for conda.
Installing it does not make any changes to your conda installation.

To install micromamba:

1. Start Windows PowerShell.

2. Open micromamba `Automatic installation
   <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#automatic-install>`__
   in your browser and copy the Windows PowerShell installation expression. It
   begins with ``Invoke-Expression``.

3. Paste that into PowerShell and run it. If are asked "Do you want to
   initialize micromamba for the shell activate command?", enter ``n`` unless
   you know what it means and want to do it.

4. Close PowerShell.

It is possible that an improved version of conda will be introduced into
ArcGIS Pro after 3.4, but until that happens, you should use micromamba.


Step 2. Clone the ``arcgispro-py3`` environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We strongly advise you not to install MGET or its dependencies into the
default ``arcgispro-py3`` environment that ArcGIS Pro creates when it
installs. Instead:

1. Follow `ESRI's instructions
   <https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/clone-an-environment.htm>`_
   to clone ``arcgispro-py3`` to a new environment. In these instructions,
   we'll assume your copy is called ``arcgispro-py3-mget``. Alternatively, if
   you already have another environment you wish to use, you can skip this
   step.

2. `Activate
   <https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/activate-an-environment.htm>`_
   the new environment you created, or the existing one you want to use.


Step 3. Install MGET
~~~~~~~~~~~~~~~~~~~~

1. Click Start, open the ArcGIS folder, and start the Python Command Prompt.
   It should show your desired environment as part of the command prompt,
   similar to this::

    (arcgispro-py3-mget) C:\Users\Jason\AppData\Local\ESRI\conda\envs\arcgispro-py3-mget>

2. Run the following command to install the packages. Replace ``micromamba``
   with ``conda`` if you did not install micromamba in step 1 and want to try
   the conda that comes with ArcGIS Pro (we don't recommend this)::

      micromamba install --channel conda-forge --yes mget3


Step 4. Add the MGET toolbox to ArcGIS Pro
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _add-toolbox-to-arcpro:

To use MGET's geoprocessing tools from ArcGIS Pro, you need to add the toolbox
to an ArcGIS Pro project:

1. Select the **Insert** ribbon and find the **Toolbox** drop-down menu. Then
   select **Add Toolbox**:

.. image:: static/ArcProAddToolbox1.png

2. In the Add Toolbox dialog box, navigate to the folder that contains your
   Python environment. Typically this is a subfolder of the
   ``C:\Users\<username>\AppData\Local\ESRI\conda\envs`` folder. In the
   example below, the environment subfolder is named ``arcgispro-py3-mget``.
   Inside that subfolder, navigate to
   ``Lib\site-packages\GeoEco\ArcGISToolbox``. Select the file ``Marine
   Geospatial Ecology Tools.tbx`` and click **OK**:

.. image:: static/ArcProAddToolbox2.png

3. Now you can access the toolbox from the Geoprocessing pane. After opening
   the Geoprocessing pane, click on **Toolboxes** and then drill into the
   toolbox to find tools of interest. Alternatively, you can search for tools
   by name in the **Find Tools** box:

.. image:: static/ArcProAddToolbox3.png

:doc:`Click here <ArcGISToolboxExamples>` for some examples of using MGET's
geoprocessing tools.


Uninstalling MGET
-----------------

MGET may be uninstalled like any other conda package:

1. Close all ArcGIS programs.

2. If necessary, `activate
   <https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/activate-an-environment.htm>`__
   the environment you want to uninstall MGET from. If that environment is
   already activated, you can skip this step.

3. Click Start, open the ArcGIS folder, and start the Python Command Prompt.
   It should show your desired environment as part of the command prompt,
   similar to this::

    (arcgispro-py3-mget) C:\Users\Jason\AppData\Local\ESRI\conda\envs\arcgispro-py3-mget>

4. Run the following command to uninstall MGET. Replace ``conda`` with
   ``micromamba`` if you installed it in Step 1::

    conda remove --yes mget3

Alternatively, if you no longer need the conda environment, you can just
`delete the environment <https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/delete-an-environment.htm>`__.
There is no need to uninstall MGET from it first.


Windows with ArcGIS Server installation instructions
----------------------------------------------------

In principle, MGET should work on ArcGIS Server so long as the prerequisite
Python packages have been installed, as described above in the 
:ref:`arcgis-pro-install`. ESRI provides some guidance on installing Python
packages on ArcGIS Server for Windows in `this article
<https://enterprise.arcgis.com/en/server/latest/publish-services/windows/deploying-custom-python-packages.htm>`__
But we have not tested this yet so we don't know for sure. We'll update this
documentation once we have the opportunity to try it.
