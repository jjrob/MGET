Adding MGET's toolbox to ArcGIS Pro
===================================

To access MGET's geoprocessing tools from ArcGIS Pro, you need to add the
toolbox to an ArcGIS Pro project:

1. Select the **Insert** ribbon and find the **Toolbox** drop-down menu. Then
   select **Add Toolbox**:

.. image:: ../static/ArcProAddToolbox1.png

2. In the Add Toolbox dialog box, navigate to the folder that contains your
   Python environment. Typically this is a subfolder of the
   ``C:\Users\<username>\AppData\Local\ESRI\conda\envs`` folder. In the
   example below, the environment subfolder is named ``arcgispro-py3-mget``.
   Inside that subfolder, navigate to
   ``Lib\site-packages\GeoEco\ArcGISToolbox``. Select the file ``Marine
   Geospatial Ecology Tools.tbx`` and click **OK**:

.. image:: ../static/ArcProAddToolbox2.png

3. Now you can access the toolbox from the Geoproessing pane. After opening
   the Geoprocessing pane, click on **Toolboxes** and then drill into the
   toolbox to find tools of interest. Alternatively, you can search for tools
   by name in the **Find Tools** box:

.. image:: ../static/ArcProAddToolbox3.png
