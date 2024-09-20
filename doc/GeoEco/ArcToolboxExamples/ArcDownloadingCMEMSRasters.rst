.. _arcgis-downloading-cmems-rasters:

Downloading data from Copernicus Marine Service (CMEMS) as rasters
==================================================================

`Copernicus Marine Service <https://marine.copernicus.eu>`_, also known as
Copernicus Marine Environmental Monitoring Service (CMEMS), is a distribution
point for a lot of marine data produced in Europe. All Copernicus data is
free, but accessing it requires you register for an account, which you should
do before trying this example.

In this example, we'll show how to use MGET's **Create Rasters for CMEMS
Dataset** geoprocessing tool to download time slices of a 3D chlorophyll
concentration dataset and a 4D ocean temperature model as GIS-compatible
raster files. We also have an example showing :ref:`how to do this in Python
<python-downloading-cmems-rasters>`.


Create a project and add MGET
-----------------------------

1. Start ArcGIS Pro and create a new Map project. I'll call mine CMEMS.

2. Click **Project** and go to the **Package Manager**. Make sure the **Active
   Environment** is set to the one that has MGET installed into it. Note that
   if you change your active environment, you have to restart ArcGIS Pro for
   it to take effect. For more on activating environments, `click here
   <https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/activate-an-environment.htm>`_.

3. :doc:`Add the MGET toolbox <AddToolboxToArcPro>` to the project's list of
   toolboxes, using the environment you activated above.


Download chlorophyll concentration data
---------------------------------------

First, we'll access the dataset known as `Global Ocean Colour
(Copernicus-GlobColour), Bio-Geo-Chemical, L4 (monthly and interpolated) from
Satellite Observations (1997-ongoing)
<https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L4_MY_009_104>`_.
We've utilized this dataset frequently in our own work. We like it because it's
global, it extends back to the launch of SeaWiFS in 1997, it integrates data
from whichever satellites were available during a given era, and it
interpolates values for cells that were obscured by clouds or were missing
data for some other reason.

1. In the geoprocessing pane, search for the tool named **Create Rasters for
   CMEMS Dataset** and open it.

2. Enter your **Copernicus user name** and **Copernicus password**.

3. On the Copernicus web page for the chlorophyll data, click on `Data access
   <https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L4_MY_009_104/services>`__.
   You'll can see a list of datasets. You have to read their User Manual to
   understand the differences between them. For our example, we'll use the one
   called ``cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M``, which
   contains various phytoplankton-related variables, integrated from multiple
   satellites, with 4 km spatial resolution and monthly temporal resolution:

   .. image:: ../PythonExamples/images/PythonDownloadingCMEMSRasters1.png
       :width: 80%
       :align: center

   Hover your mouse cursor over that one and click the "copy" icon that comes
   up, or just highlight the dataset ID and copy it. Then paste it into the
   **Copernicus dataset ID** parameter of the geoprocessing tool.

4. On the web page, click the **Form** link for that dataset. This takes you
   to the list of variables included in the dataset. Look through the list of
   variables until you find the one we want: *Mass concentration of
   chlorophyll a in sea water*. It is probably the first one in the list. We
   need to know the "short name" of this variable as it occurs in the
   underlying netCDF files stored in Copernicus's cloud. This is the light
   gray text that occurs just to the left of the full variable name. For the
   variable we want, it is **CHL**:

   .. image:: ../PythonExamples/images/PythonDownloadingCMEMSRasters2.png
       :width: 80%
       :align: center

   Now that we know what it is, enter **CHL** for the **Variable short name**
   parameter of the geoprocessing tool.

5. For **Output workspace** choose a folder or geodatabase to receive the
   rasters.

6. We could run the tool at this point, but it would download the entire
   dataset, which is hundreds of rasters. Let's restrict it to a shorter
   period. Open the **Spatiotemporal extent** options and enter a **Start
   date** of **1/1/2020** and an **End date** of **12/31/2020**. (If your
   operating system locale is not set to US English, your date format might be
   different.)

   If desired, you can also set a **Spatial extent** to your area of interest,
   or leave it unspecified to download global rasters. If you specify a small
   area of interest, the tool will run much faster, particularly if you have a
   slow internet connection.

   Leave **Rotate by** unspecified, unless you want to rotate the global
   rasters. Leave **Minimum depth** and **Maximum depth** unspecified; this
   chlorophyll dataset does not have depth layers.

7. The tool should look similar to this:

   .. image:: images/ArcDownloadingCMEMSRasters1.png
       :align: center

   Click Run.

8. The tool will take a few minutes to run, unless you specified a small study
   area or have an extremely fast internet connection. While it is running, if
   you click **View Details** at the bottom of the geoprocessing pane, you
   should see output similar to this::

       Start Time: Thursday, September 19, 2024 1:50:53 PM
       Querying Copernicus Marine Service catalogue for dataset ID "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M".
       Importing 12 datasets into ArcGIS Folder C:\Users\Jason\Documents\ArcGIS\Projects\CMEMS with mode "add".
       Checking for existing destination datasets.
       Finished checking: 0:00:00 elapsed, 12 datasets checked, 0:00:00.000084 per dataset.
       0 destination datasets already exist. Importing 12 datasets.
       Import in progress: 0:01:04 elapsed, 3 datasets imported, 0:00:21.384343 per dataset, 9 remaining, estimated completion time: 1:55:39 PM.
       Import complete: 0:03:44 elapsed, 12 datasets imported, 0:00:18.687666 per dataset.
       Succeeded at Thursday, September 19, 2024 1:55:07 PM (Elapsed Time: 4 minutes 13 seconds)

   .. Note::
       If you're running ArcGIS 3.2.x and the tool fails with ``RuntimeError:
       Failed to query the Copernicus Marine Service catalogue for dataset ID
       "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M". The
       copernicusmarine.describe() function failed with RuntimeError: no
       running event loop.``, please see `this issue
       <https://github.com/jjrob/MGET/issues/1>`_.

   The ArcGIS catalog pane should show this directory structure:

   .. image:: images/ArcDownloadingCMEMSRasters2.png
       :align: center

   The tool uses ``.img`` format by default, and chooses a default directory
   structure and file naming scheme based on characteristics of the dataset
   you access. You can override these defaults under **Output raster
   options**. There's also an option for instructing the tool to build
   pyramids automatically after creating the rasters.

   Here's what the first time slice looks like in ArcGIS, symbolized with the
   "Spectrum By Wavelength-Full Bright" color scheme and NoData set to black:

   .. image:: images/ArcDownloadingCMEMSRasters3.png
       :align: center
       :width: 80%

   The distribution of chlorophyll values is strongly skewed toward small
   values, so most of this image looks purple. You can enable the **Apply
   log10 transform** option to apply a base 10 logarithm before creating the
   rasters, as is often done when visualizing chlorophyll data. Note that if
   you rerun the tool now with this option, it will skip all of the rasters
   because they already exist. Change **Overwrite mode** to **Replace** if you
   want to overwrite the existing rasters.

   Here's what the same time slice looks like with the log10 transform
   applied:

   .. image:: images/ArcDownloadingCMEMSRasters4.png
       :align: center
       :width: 80%


Downloading 4D ocean model temperature data
-------------------------------------------

New, we'll access the dataset known as `Global Ocean Physics Reanalysis
<https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030>`_, a
1/12° horizontal resolution 4D ocean model with 50 depth levels, also known as
GLORYS12. We like this dataset because it extends back to 1993 (roughly to the
launch of TOPEX/Poseidon) and because it scored very well in an evaluation of
how eight global ocean models performed for the northeast U.S. continental
shelf (`Castillo-Trujillo et al. 2023
<https://doi.org/10.1016/j.pocean.2023.103126>`_), a region that our lab
frequently works in.

Under their `Data access
<https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030/services>`__
page, we want the ``cmems_mod_glo_phy_my_0.083deg_P1M-m`` dataset, which has a
temporal resolution of 1 month, and at the time of this writing contained data
ranging from 1993 to mid-2021. The corresponding ``_myint_`` dataset
contained data from mid-2021 forward, known as the "interim period". After
clicking on the **Form** link, we determined we wanted ``thetao`` variable,
which is the sea water potential temperature.

1. Open the **Create Rasters for CMEMS Dataset** tool again.

2. Enter your **Copernicus user name** and **Copernicus password**.

3. For **Copernicus dataset ID** enter ``cmems_mod_glo_phy_my_0.083deg_P1M-m``.

4. For **Variable short name** enter ``thetao``.

5. For **Output workspace**, pick the same workspace as before.

6. Make sure **Apply log10 transform** is not checked. It shouldn't be if you
   opened a fresh instance of the tool. But if you recycled your run from
   chlorophyll above, you might have checked it.

7. Because this is a 4D dataset with depth layers, we're going to download
   many more rasters than last time. Because of that, we're going to limit the
   spatial extent of the rasters, to speed up the downloading. (You can skip
   this step if you really want to download global rasters, but it will be
   slower.) 

   Open the **Spatiotemporal extent** options and then open **X and Y
   Extent**. Set the four boundaries to the latitudes and longitudes enclosing
   a small region of interest. I'm going to use an area off the U.S. east
   coast, and area our lab frequently works in:

   * **Top**: 50
   * **Left**: -82
   * **Right**: -52
   * **Bottom**: 25

   Leave **Rotate by** unspecified.

8. This ocean model has 50 depth layers. To speed up the example, we're going
   to limit the download to a maximum depth of 100 meters. Enter a **Maximum
   depth** of 100.

9. We're also going to limit this to one year of data, like we did with
   chlorophyll. Enter a **Start date** of **1/1/2020** and an **End date** of
   **12/31/2020**

10. The tool should look similar to this:

    .. image:: images/ArcDownloadingCMEMSRasters1.png
        :align: center

    Click Run.

11. Because there are so many depth levels, the tool will still take a few
    minutes to run, even though we specified a small area of interest. If you
    only need depths at one level such as the surface, you can really speed
    things up by specifying a **Minimum depth** and **Maximum depth** that
    isolate just your depth of interest. Anyway, while the tool is running, if
    you click **View Details** at the bottom of the geoprocessing pane, you
    should see output similar to this::

        Start Time: Friday, September 20, 2024 9:04:09 AM
        Querying Copernicus Marine Service catalogue for dataset ID "cmems_mod_glo_phy_my_0.083deg_P1M-m".
        Importing 264 datasets into ArcGIS Folder C:\Users\Jason\Documents\ArcGIS\Projects\CMEMS with mode "add".
        Checking for existing destination datasets.
        Finished checking: 0:00:00 elapsed, 264 datasets checked, 0:00:00.000068 per dataset.
        0 destination datasets already exist. Importing 264 datasets.
        Import in progress: 0:01:00 elapsed, 68 datasets imported, 0:00:00.896551 per dataset, 196 remaining, estimated completion time: 9:08:09 AM.
        Import complete: 0:04:05 elapsed, 264 datasets imported, 0:00:00.929576 per dataset.
        Succeeded at Friday, September 20, 2024 9:08:18 AM (Elapsed Time: 4 minutes 8 seconds)

    .. Note::
        If you're running ArcGIS 3.2.x and the tool fails with ``RuntimeError:
        Failed to query the Copernicus Marine Service catalogue for dataset ID
        "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M". The
        copernicusmarine.describe() function failed with RuntimeError: no
        running event loop.``, please see `this issue
        <https://github.com/jjrob/MGET/issues/1>`_.

    The ArcGIS catalog pane should show this directory structure:

    .. image:: images/ArcDownloadingCMEMSRasters6.png
        :align: center

    The depth levels used by the Global Ocean Physics Reanalysis products are
    not rounded to simple values like 10, 20, 50, and 100. Instead, the
    dataset appears to use some algorithmic spacing. Reflecting this, the tool
    automatically includes enough decimal points in the depth levels in order
    for them to be different from each other. You can specify your own naming
    scheme under **Output raster options** with the **Raster name
    expressions** parameter. For this dataset, the tool automatically selected
    the following expressions::

        %(DatasetID)s
        %(VariableShortName)s
        Depth_%(Depth)06.01f
        %(VariableShortName)s_%(Depth)06.01f_%%Y%%m.img

    Here's the surface layer (depth 0.5 m) for the first time slice (2020-01)
    symbolized with the "Plasma" color scheme:

    .. image:: images/ArcDownloadingCMEMSRasters7.png
        :align: center
