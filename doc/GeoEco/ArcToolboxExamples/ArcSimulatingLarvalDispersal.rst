.. _arcgis-simulating-larval-dispersal:

Simulating larval dispersal and analyzing connectivity
======================================================

Many marine animal species have a life cycle where the adult form is
relatively stationary, while the larval stage is planktonic. This allows
populations to spread and genetic material to be exchanged over large
distances through a process called `larval dispersal`. MGET contains tools for
modeling larval dispersal with Eulerian hydrodynamics based on the work of
Eric A. Treml. Eric earned his doctorate with our laboratory developing the
foundational approach (Treml et al. 2008) and has continued to evolve and
apply the method as his career progresses (e.g. Treml et al. 2012, 2015; Mora
et al. 2012; Schill et al. 2015). The tools in MGET are based on the methods
of Treml et al. (2012).

These tools allow you produce results similar to Figure 5 of Treml et al.
(2008), shown below. That analysis investigated connectivity between coral
reefs in the Tropical Pacific. Here we can see the difference in connectivity
between years for larvae circulated for 30 days during the coral mass spawning
season of October through December. Dispersal connections common to 3
simulated years are highlighted in yellow. Unique connections occurring in
only 1 year are plotted for the El Niño (1997), La Niña (1999), and neutral
year (2001).

.. container:: spaced-image

    .. image:: images/LarvalDispersal0.png
       :align: center
       :width: 80%

The tools use a four-step workflow:

1. Create a simulation using three rasters that define the study area and
   habitat patches.

2. Load ocean currents into the simulation for dates of interest.

3. Run the dispersal algorithm for the patches and the pelagic larval duration
   (PLD), pre-competency model, and settlement parameters you desire.

4. Visualize the results as a series of rasters showing larvae density through
   time and a line feature class showing connections between patches. If
   desired, you apply mortality at this step.

You can repeat steps 2–4 to simulate different dates, biological parameters,
etc. as needed.

Here's the toolbox in ArcGIS Pro:

.. container:: spaced-image

    .. image:: images/LarvalDispersal1.png
       :align: center

Here's an example model in ArcGIS Pro 3.6:

.. container:: spaced-image

    .. image:: images/LarvalDispersal2.png
       :align: center


Example analysis
----------------

For this example, we'll examine connectivity of coral reefs within the central
and western Gulf of Mexico. We chose this region because it is relatively
small, allowing our example simulation to run quickly, and because we had data
readily available from a paper we coauthored, `Schill et al. (2015)
<https://dx.doi.org/10.1371/journal.pone.0144199>`__. Although this example
covers a specific dataset and region, we'll offer hints for how you can best
configure the tools for your own data and region. (But please, do not contact
us asking for step-by-step instructions on how to do basic GIS tasks, such as
how produce a water mask from publicly available GIS data. If you do not
already have the GIS skills to do these kinds of things yourself, you are not
ready to use the connectivity tools.)


Step 1: Create the simulation
-----------------------------

The first step is to create the simulation. To do that, we need three rasters:
a water mask raster, a patch IDs raster, and a patch cover raster. The rasters
must all have the same coordinate system, cell size, extent, and number of
rows and columns. Before discussing each raster in detail, we'll discuss their
coordinate system, cell size, and extent. You should select these parameters
very carefully. Not only do they affect the ecological relevance and
plausibility of the results, they strongly influence the length of time
required to run the simulation and the likelihood that you'll encounter "OUT
OF MEMORY" errors and similar problems.

Coordinate system
~~~~~~~~~~~~~~~~~

The rasters must use a projected coordinate system such as Mercator, with
meters as the linear unit.  The coordinate system should, as much as possible,
be configured such that its rows and columns run parallel to lines of
longitude and latitude.

When MGET loads ocean currents data into the simulation, it reprojects the
original data into the coordinate system of your rasters. The original data
come as vector components—pairs of ``u`` and ``v`` images giving current speed
in the north/south and east/west directions. When MGET reprojects them, it
does not know how to adjust the results to account for the fact that
north/south/east/west may no longer be up/down/right/left on portions of your
map. Projections in which north/south/east/west deviate strongly from
up/down/right/left will not have accurate results. This problem is easy to
avoid for study areas near the equator but is increasingly difficult as
latitude increases.

If you do not know what to choose, we recommend ArcGIS's "WGS 1984 Mercator"
projection. Feel free to contact us for advice.

.. note::
    We do not recommend any of the "Web Mercator" projections, due to the
    difficulty in properly reprojecting ocean currents data to these
    projections. Be careful, because ArcGIS Pro may choose one of those by
    default when creating a new "map project".


Cell size, extent, and number of rows and columns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choosing a cell size is difficult. Often you are working with coral reef data
at resolutions of 1 km or higher. High resolution maps are nice, so you should
just use the cell size of your reef data for the connectivity analysis, right?
There are three reasons why this is probably not a good idea:

1. Most ocean currents data are much coarser resolution. Most of global
   currents datasets are derived from remote sensing observations reported by
   satellite altimeters which have along-track resolutions on the order of 10
   km. The resulting gridded products typically range in resolution from 5–25
   km at the equator. If you use a very fine scale such as 1 km, MGET will
   interpolate these products to that resolution but that does not mean the
   results will be accurate at that scale. Indeed, it is not possible to know
   whether or not the results are accurate because the ocean currents datasets
   are not able to resolve phenomena at that scale.

2. Simulation run time increases dramatically as cell size decreases.
   Decreasing the cell size increases the number of cells in the study area;
   halving the cell size quadruples the number of cells. When you reduce cell
   size, you must also reduce the time step of the simulation so that the
   hydrodynamic algorithm remains numerically stable. This means that more
   time steps are needed to span a given simulation length. The increased
   number of cells and time steps can greatly lengthen the time it takes to
   complete the simulation.

3. The tool's memory requirements also increase similarly. The tool must fit
   all of the ocean currents images needed to run a simulation into memory
   simultaneously, along with other arrays of similar dimensions. Selecting a
   small cell size can easily push memory requirements beyond the capabilities
   of your computer, leading to an ``OUT OF MEMORY`` error when you try to run
   the simulation.

We recommend that you:

* First research ocean currents datasets and select one. As you will see in
  the next bullet, we recommend that you limit the resolution of your analysis
  to that of the ocean currents data. To follow this advice, you need to
  select an ocean currents dataset that matches your region and time period of
  interest. We discuss this further in the Step 2 section below.

* Choose a cell size that is not smaller than half the resolution of your
  ocean currents. For example, if you're using the default ocean currents
  dataset, the `Copernicus Global Ocean Physics Reanalysis
  <https://doi.org/10.48670/moi-00021>`__, the resolution is 1/12°, or
  approximately 9 km at the equator, do not use a cell size smaller than 4.5
  km. Working at a finer scale than that does not seem likely to produce
  results that will be highly accurate at that scale, owing to the simple
  bilinear or cubic interpolation used to achieve the increase in resolution.
  (We have not tested this assertion, however.)

* Keep your rasters to less than 200,000 cells in total. For example, 500
  columns x 400 rows = 200,000 cells. If fewer would work, by all means make
  your rasters smaller! The fewer cells you have, the faster your simulation
  will run. If you have a powerful computer with lots of RAM, it can handle
  more.

* Do not clip your rasters to the smallest rectangle that can tightly enclose
  all of your habitat patches. Leave a buffer between habitat patches and the
  edges of your rasters, to allow currents to circulate in this area and
  perhaps return larvae to the patches after moving beyond them. Once larvae
  move beyond the edge of the raster, they are lost and cannot return.

Finally, if you are trying to model fine scale processes around small
extents–e.g. nearshore movements of larvae around a small island or atoll–this
may not be the tool for you. The tool is intended for use at regional scales
where dominant mesoscale circulation features connect patches over 10s to 100s
of km.

The Gulf of Mexico example
~~~~~~~~~~~~~~~~~~~~~~~~~~

The Gulf of Mexico example uses data from `Schill et al. (2015)
<https://dx.doi.org/10.1371/journal.pone.0144199>`__. In that analysis, we
were interested in coral reef connectivity throughout the entire Caribbean,
Gulf of Mexico, southeastern U.S., and Bermuda. We used currents data from
NOAA's `Atlantic Real-Time Ocean Forecast System (RTOFS)
<https://www.ncei.noaa.gov/products/weather-climate-models/ncep-atlantic-real-time-ocean-forecast>`__,
a basin-scale ocean forecast system based on the HYbrid Coordinate Ocean Model
(HYCOM). Atlantic RTOFS used a variably-spaced grid that ranged from about 4
km resolution in the western Gulf of Mexico to about 17 km near Africa. We
resampled RTOFS to an 8 km cell size, the coarsest resolution in our study
area (which occurred in the eastern Caribbean). We used the WGS 1984 Mercator
projection. The rasters were 594 columns by 413 rows.

For the example here, we clipped the Schill et al. (2015) data to the central
and western Gulf of Mexico and the Yucatán Peninsula (see below). We
maintained the same coordinate system, but clipped the rasters to 180 columns
by 198 rows. We focused on the smaller region to limit the run time of the
tool. At this extent, the simulation takes about 4 minutes to run on my
circa-2023 laptop, vs. about 20 hours for the full Schill et al. (2015)
extent, with all of its reefs, on a circa-2013 server-class machine at the
time.

That particular RTOFS product is no longer in production, so instead we'll
obtain currents data from the `Copernicus Global Ocean Physics Reanalysis
<https://doi.org/10.48670/moi-00021>`__, which has a resolution of 1/12°, or
approximately 9 km at the equator, which is only slightly coarser than the 8
km we'll use for this analysis.

Now we will discuss the details of the three rasters needed to create the
simulation. If you want to run the simulation yourself, you can download the
rasters `here
<https://github.com/jjrob/MGET/raw/refs/heads/main/test/GeoEco/Connectivity/Gulf_of_Mexico_Patches.zip>`__.

Water mask raster
~~~~~~~~~~~~~~~~~

The water mask indicates which cells are land and which are water. It must
have an integer data type. The value 0 or No Data indicates land, all other
values indicate water. During the simulation, larvae are allowed to move
between water cells but cannot enter land cells. Larvae that are moved in the
direction of land are "blocked" and remain in the adjacent water cell. Larvae
that are moved beyond the edge of the raster are lost.

You can produce water masks from bathymetry datasets, which are usually given
in raster form. SRTM30_PLUS, ETOPO, and GEBCO are widely used global
bathymetries. Depending on your study area, you may also be able to find a
regional bathymetry. Assuming you followed our advice about selecting a cell
size that is not too small relative to your ocean currents data, it is very
likely that the bathymetry also has a smaller cell size than you should to
use. 

One way to produce a lower-resolution water mask from a high resolution
bathymetry is:

1. If the bathymetry is substantially larger than your study area, e.g. it is
   a global product, clip it so it roughly encloses your study area. For now,
   keep the bathymetry in its original coordinate system.

2. Use ArcGIS Spatial Analyst tools such as Con or Raster Calculator to
   classify cells as either land (0) or water (1) based on their depth.

3. Use the Resample tool to produce a raster with the desired coordinate
   system and cell size. Use the Output Coordinate System environment setting
   to specify the coordinate system you want to use for your analysis (e.g.
   Mercator). Use the tool's Cell Size parameter to specify the analysis cell
   size (e.g. 8000 m in the Gulf of Mexico example). Set Resampling Technique
   to MAJORITY so that cells along the coastline are classified as land or
   water according to which is more frequent.

4. The resampled raster should be in the desired coordinate system and cell
   size, but may still be larger than you'd like. Clip it down to the desired
   extent.

If you have reefs along coastlines, this procedure may not be exacting enough
along shore to give you what you'd like. You may need to use a more
sophisticated procedure or even manually edit the final raster, e.g. with
ArcGIS Pro's Pixel Editor.

You can also build water masks from shoreline databases, such as GSHHG. These
are often distributed as land polygons. You'll have to use a tool like Polygon
to Raster, then manipulate the raster with Spatial Analyst tools.

Here's the water mask for the Gulf of Mexico example. Blue is water (1) and
dark gray is land (0):

.. container:: spaced-image

    .. image:: images/LarvalDispersal3.png
       :align: center
       :width: 80%

Patch IDs raster
~~~~~~~~~~~~~~~~

This raster specifies the locations and numeric IDs of habitat patches from
which larvae will be released and upon which larvae can settle. It must have
an integer data type. Each patch is defined as one or more cells having the
same integer ID value. Patch IDs may range from 1 to 65535, inclusive. The
value 0 may not be used. NoData indicates that the cell is not part of a patch
(regardless of whether that cell is land or water).

Typically, each patch's cells form a single contiguous region, but this is not
required. For example, a patch may be composed of multiple clusters of cells
that are separated by land, unoccupied water, or even other patches (with
different IDs). All cells marked as patches must occur in cells marked as
water by the water mask. If your patches occur close to land, you may need to
carefully edit the patch IDs and water mask rasters at the same time to ensure
no desired habitat is missed.

If you want to have different source and sink patches, do not worry about that
now. The patch IDs raster should include all patches, whether they will be
sources, sinks, or both. Later, when you run the simulation, you can specify
which patches are sources and sinks.

Here's the patch IDs raster for the Gulf of Mexico example overlaid on the
water mask, with each patch a different color and NoData as fully transparent,
so the water mask shows through.

.. container:: spaced-image

    .. image:: images/LarvalDispersal4.png
       :align: center
       :width: 60%

Note that this does not fully follow our recommendation above to buffer
patches near the edge of the study area: in the southeast, the barrier reef
along the Yucatán Peninsula extends all the way to the bottom edge of raster.
The real reason for this is laziness; we clipped the Caribbean-wide data from
Schill et al. (2015) and did not bother to edit out the southeastern-most
reefs. But we can also offer some reasonable justifications. In this example,
we're not very interested in self recruitment and connectivity between those
southeastern reefs. Also, the dominant current patterns flow from south to
north here, so there is reduced risk that larvae will be carried off the
southern edge of the study area.

Frequently asked questions about the patch IDs raster
.....................................................

**How should patches be defined?**

That long barrier reef prompts the questions: how big should patches be?
Should long runs of continuous habitat cells be grouped into a single patch or
split into multiple patches? If they are split into multiple patches, how
should it be done? Would it be better to have each cell of the raster have a
unique patch ID?

The answers to these questions depend on the question you're seeking to
answer, and also on practical a trade-off between level of detail and speed of
execution. Adjacent areas of suitable habitat are usually highly connected.
There is usually no benefit to treating each cell as a distinct patch. This
usually results in a very large number of patches, greatly increasing
execution time. Also, the connectivity network that results is usually very
dense and must be further summarized to clearly communicate the results.

On the other hand, it may not be sufficiently informative to create a single
patch for all the cells of a reef that extends for hundreds of kilometers.
This is especially true when the reef spans multiple political jurisdictions
or management zones and the purpose of your study is to investigate
connectivity in the context of human uses of the ocean. In this situation, it
may be best to break up the reef into multiple patches at political or
management boundaries.

It is also appropriate to split patches up at locations where physiography or
oceanography might strongly affect the flow of larvae. For example, if a reef
extends around both sides of a peninsula, it might be appropriate to split the
reef into two patches–one for either side of the peninsula–or three–one for
either side and one for the tip.

There are no hard-and-fast rules for grouping cells into patches. We recommend
you take the approach that seems most appropriate for your situation and
document it accordingly. That said, we prefer to to have no more than a few
hundred patches in a large analysis, or a few dozen in a small analysis, as is
presented here. Once you exceed a few hundred patches, the simulation time
stretches into hours or even days for little apparent benefit. When the number
of patches is limited to a few dozen, the number of connections is often in
the low hundreds, which is not too difficult to visualize on a map.

**I followed your advice and selected a coarse cell size commensurate with the ocean currents I'm using. But these cells are much larger than the amount of reef within them. Is that OK?**

You may be thinking: "When a cell has only a tiny amount of reef, it seems
wrong to mark the cell as being part of a patch. That makes the patch extend
over a much larger area than occurs in reality. But if I don't mark the cell
as being part of patch, that reef will be lost. How do I resolve this
dilemma?""

Mark the cell as being part of a patch, then use the patch cover raster to
specify how much of the cell is covered by suitable habitat. See below for
details.

Alternatively, you can increase the resolution of your analysis. If you have a
powerful computer with lots of RAM and a fast processor, it may be able to
handle a resolution that is high enough to address your concern. But keep in
mind our recommendation that you not increase resolution too much beyond that
of your ocean currents data.

**Where can I get coral reef data for my own analysis?**

`UNEP-WCMC Global Distribution of Coral Reefs
<https://data-gis.unep-wcmc.org/portal/home/item.html?id=0613604367334836863f5c0c10e452bf>`__
is a good place to start. (If the link is stale, just search the Internet for
the dataset.)

Patch cover raster
~~~~~~~~~~~~~~~~~~

The patch cover raster specifies the proportion of each cell's area that is
occupied by habitat from which larvae can be released or upon which larvae can
settle. It must have a floating point data type, with values greater than or
equal to 0 and less than or equal to 1. The value 1 indicates that the entire
cell is occupied by suitable habitat, while 0.5 indicates that only half of it
is. For example, if the cell size is 8 km, the values 1 and 0.5 mean the cell
contains 64 and 32 square km of suitable habitat, respectively.

The patch cover raster should have values greater than 0 wherever the patch ID
raster has a value. It should have value 0 or NoData wherever the patch ID
raster is NoData, indicating that there is no suitable habitat.

Use the patch cover raster to account for the loss of resolution you
experienced when you rescaled your high resolution reef data to a lower
resolution that better matches the ocean currents. In essence, this raster
lets you express that some of the low resolution cells are completely covered
by habitat, while others are only partially covered.

At the start of the simulation, cells are allocated quantities of larvae
according to the patch cover raster. A cell with a patch cover of 1 receives 1
unit of larvae; a cell with a patch cover of 0.2 receives 0.2 units of larvae.
The simulator assumes that both suitable habitat and larvae are distributed
uniformly across the cell at all times. By default, as the simulation
progresses and larvae that are competent to settle drift over suitable
habitat, only the fraction of the cell that is occupied by suitable habitat
receives settlers. (This behavior can be modified by the Use Sensory Zone
parameter, described further below.)

Here is the patch cover raster for the Gulf of Mexico example, with values
near 0 as dark purple and near 1 as light orange. The value 0 is symbolized as
"no color", allowing the background water mask to show through.

.. container:: spaced-image

    .. image:: images/LarvalDispersal5.png
       :align: center
       :width: 60%

Running the tool
~~~~~~~~~~~~~~~~

Once you have the rasters created, running the Create Larval Dispersal
Simulation From Rasters tool is simple, shown here for the Gulf of Mexico
example:

.. container:: spaced-image

    .. image:: images/LarvalDispersal6.png
       :align: center
       :width: 40%

You must specify a simulation directory that the tool will create, as well as
your three rasters. The tool will create the directory, initialize it with
some private files and directories, and make copies of your three rasters. Do
not manually tamper with the contents of the simulation directory. It is not
intended to be read or modified directly.


Step 2: Load ocean currents into the simulation
-----------------------------------------------

After creating the simulation, you must load ocean currents data into the
simulation directory. These will be used in Step 3 to run the simulation. But
before you load currents, you must determine which ocean currents product you
will use.

Selecting an ocean currents product
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At the time of this writing, MGET 3.x only included a single tool for
acquiring currents data, called Load CMEMS Currents into Larval Dispersal
Simulation. This tool downloads data offered by `Copernicus Marine Service
(CMEMS) <https://marine.copernicus.eu/>`__. CMEMS is free, but you must
register and obtain a username and password. At the time of this writing, the
ocean currents products on offer could be browsed `here
<https://data.marine.copernicus.eu/products?facets=specificVariables%7EVelocity>`__.


When considering the available products, you should first eliminate those that
do not match the spatial extents and time ranges of interest to you. Next,
consider the spatial resolution. If you are performing a regional simulation,
you probably want as high spatial resolution as possible, e.g. 1/12° or
higher. For a global simulation, you might accept something lower, such as
1/4°, to keep the required memory and run-time requirements within the
capabilities of your hardware.

You should consider temporal resolution at the same time. Larval dispersal
processes often occur over a period of 10s of days. Therefore, you should
probably select a product that has daily resolution or higher. If tides are an
important process for your species of interest, you should consider hourly or
even sub-hourly resolution, if available. However, most of the products
available from Copernicus are fairly large scale and may not incorporate
tides. You'll have to research their processing details to know for sure. 

Be sure to read up your thoroughly on your final candidate datasets to build a
solid understanding about how they work. Your final choice can strongly
influence the results, especially at small scales. For an illustration of this
in practice, see `Choukroun et al. (2025)
<https://doi.org/10.1007/s00338-024-02563-z>`__.

By default, the tool is configured to access the `Global Ocean Physics
Reanalysis <https://doi.org/10.48670/moi-00021>`__. This is a good
general-purpose global ocean model with 1/12° spatial resolution and daily
temporal resolution. It runs from 1993 to close to the present day, making it
suitable for a wide variety of analyses. If you're not sure what to choose,
you can try this one to start with.

Running the tool
~~~~~~~~~~~~~~~~

Here's what we did for the Gulf of Mexico example:

.. container:: spaced-image

    .. image:: images/LarvalDispersal7.png
       :align: center
       :width: 40%

The purpose of this tool is to download currents data for a specified range of
dates and add them to the simulation directory, thereby making it possible to
run simulations for dates within that range. The values you provide for Start
date and End date do not control when a simulation starts and ends. You'll
decide that during Step 3, below, when you actually run simulations. The load
currents tool performs the job of downloading the currents, storing them
locally, and making them ready for use by the simulator so that when it needs
them they can be retrieved quickly. The Start date and End date tell the tool
the range of dates for which the currents data should be prepared.

You can run this tool multiple times to load different ranges of dates into
the same simulation directory. For example, if you want to run simulations
during the August-October periods of three different years, you could run the
tool three times, once for each year, providing 1 August as the Start date and
31 October as the End date. If your Internet connection is slow, the tool can
take a long time to run. If speed matters it is better to run the tool
multiple times for short ranges of dates (e.g. August-October for three
different years), rather than once for a single long range (e.g. August of
year 1 through October of year 3).

In the Gulf of Mexico example, we wanted to simulate dispersal of larvae for
30 days; this is known as a 30 day pelagic larval duration (PLD). Repeating
what was done by Schill et al. (2015), we wanted the larvae to be released on
the last quarter moon of September 2011, which fell on 20 September. So we put
in 20 September 2011 as the Start date and 21 October 2011 as the End date.

Because these dates are just those for loading data, not for running the
simulation, we could have put in an earlier start date or later end date and
obtained more data while still covering the focal period. For example, if we
wanted to simulate August 2011 last quarter moon as well, as was done by
Schill et al. (2015), we could have used 21 August as the start date and
loaded two months of currents, which we would use to run two consecutive
30-day simulations (in Step 3 below).

In this particular case, each day of currents was centered on midnight, and
extended from noon the previous day until noon on focal date. Because we
planned to run my simulation starting at midnight, we actually needed 31 days
of currents to completely span the period of the simulation. There is no harm
in downloading more currents data than you ultimately need.

You can see my Copernicus user name and the password is hidden by asterisks.
You will have to obtain your own Copernicus user name and password.

We left the CMEMS Dataset ID set to that of the `Global Ocean Physics
Reanalysis <https://doi.org/10.48670/moi-00021>`__. Look at the documentation
of that parameter for instructions on finding the Dataset ID for your product
of interest.

We assumed larvae occupied the surface, so we left the depth set to that of
the shallowest layer of the Global Ocean Physics Reanalysis. Note that this
depth is slightly below the surface, not 0. When you enter the depth, it must
be at full precision without any rounding. For your convenience, when you run
the tool it outputs a list of depths at full precision. Please see the
documentation for the Depth parameter for more information.

We used the default resampling technique of ``CUBIC`` for projecting the ocean
currents to the coordinate system of the analysis.

We selected ``Del2a`` for the Method for estimating missing currents values.
This parameter tells the tool how to fill in cells that are marked as water by
the water mask but are missing currents data. It is important that you do
this; if the cells are left as NoData, then larvae cannot leave the cells by
advection, only by diffusion. Then when you run the simulation in Step 3, the
tool will report a warning (see Step 3 below for what this looks like). If you
select a method for estimating missing currents, the tool will interpolate
values for those missing cells using values from nearby cells that do have
data. Please see the documentation for the that parameter for more
information. (Thanks to John D'Errico for the `MATLAB implementation
<https://www.mathworks.com/matlabcentral/fileexchange/4551-inpaint_nans>`__ of
the algorithms underlying this parameter.)

In our experience, the results of the various ``Del2`` methods are fairly
similar. We recommend ``Del2a`` as a default. All of them can take a
significant amount of time to execute for large rasters. The ``Del4`` method,
while more numerically accurate is much slower and can require significantly
more memory, so we tend not to use it. If you receive an ``OUT OF MEMORY``
error while loading currents, switch to the ``Del2c`` method. If you still
receive the error, you'll probably have to recreate the simulation at a
coarser cell size to reduce the number of cells. You are welcome to contact us
for advice.

Finally, this parameter is intended to fill in small areas of missing data for
which these interpolation algorithms are reasonable. If your currents product
always lacks data in a certain area–e.g. a nearshore environment or at shallow
depths–you should not blindly assume that this interpolation procedure will
produce correct results! Instead, you should try to find another currents
product that offers estimates for your areas of interest. Most likely the
developer of the currents data will have a better way of estimating currents
values than the simple interpolation algorithms offered by this tool.

The Rotate By parameter should be used when the study area spans the 180th
Meridian, so that the currents data also span it. If you don't rotate the
currents, it may not be possible to reproject them to the geographic
characteristics of the patch rasters.

Frequently asked questions about loading ocean currents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Can I run the tool multiple times, to load currents from different periods of time?**

Yes, you may load as many time ranges as you like. They need not be
contiguous: for example, you could load three months from every year, to just
focus on a specific spawning season. The tool will skip time slices that have
already been loaded.

**Can I load several different products into a single simulation directory, e.g. for different time ranges? Can I load in multiple depths from the same product?**

No. At the time of this writing, you can only load currents from a single
depth from a single product into a given simulation directory. When you run
the tool for the first time, it establishes the product and depth that are
allowed in that simulation directory going forward. If you need to use a
different product or depth, create another simulation directory.

**Can I load my own ocean currents data in the Simulation Directory rather than using MGET's tool?**

At this time, we do not provide a tool for loading your own currents data into
the simulation. If this is something that is absolutely critical for your
project, please inquire with us and maybe we can collaborate on it.

You may also try to do it yourself by reverse engineering the format that
currents are stored in the simulation directory. The currents go into a
subdirectory named ``Currents``. In it, there are subdirectories ``u`` and
``v`` for the horizontal and vertical vector components rasters. In each of
those, there are subdirectories by year. In the year directories, the currents
rasters appear as ``.img`` files with the name ``uYYYYmmdd_HHMM.img`` or
``vYYYYmmdd_HHMM.img``, where ``YYYY`` is the four-digit year, ``mm`` is the
two-digit month, ``dd`` is the two-digit day of the month, ``HH`` is the hour
(00 to 23) and ``MM`` is the minute (00 to 59). (The second is assumed to be
0.)

The currents rasters must use the same coordinate system, cell size, extent,
and number of rows and columns as the three rasters used to initialize the
simulation. The MGET tool Project Raster To Template can help transform your
original data to meet those requirements. MGET's Load Currents tool uses this
internally to convert the original currents data to the geographic
characteristics of your simulation rasters.

The images must use a constant time increment. There must be no gaps in the
series of time slices for periods for which you want to run a simulation. For
example, if want to conduct a simulation for the month of September 2015 and
you have a daily currents product, you must provide images for all 30 days of
September 2015. There must not be any missing days.

You must also modify the file ``Simulation.ini`` at the root of the simulation
directory to set four variables:

* ``currentsloaded`` – set this to ``True``

* ``currentsproduct`` – set this to some arbitrary string describing your
  product; it does not matter what it is

* ``currentsdatetype`` – you probably want to set this to ``Center``,
  indicating that the date/time of the file indicates the center of the time
  window that the image applies to

* ``maxsecondsbetweencurrentsimages`` – set this to the number of seconds
  between each image, e.g. 86400 for daily images


Step 3: Run the simulation
--------------------------

After loading currents for a range of dates you want to simulate, you can run
the simulation using the Run Larval Dispersal Simulation tool. This step will
disperse the larvae using the ocean currents and track where they settle. This
step takes a long time to run, ranging from a under a minute for a simulation
spanning a few days for a few patches in a moderately sized study area, to
hours or even days for a 90-day simulation for hundreds of patches in a large
study area.

In addition to specifying the date and duration of the simulation, you'll also
specify the parameters that govern larval settlement behavior, such as the
pre-competency period and settlement rate. Crucially, you do not specify
mortality here, nor anything about how many larvae must disperse between
patches for them to be considered connected. Mortality and the connectivity
threshold are part of Step 4, visualizing the results.

The Run Larval Dispersal Simulation tool has many parameters. To obtain good
results, you must choose values carefully. Let's walk through them in detail.
Here's how the tool looks with you first open it:

.. container:: spaced-image

    .. image:: images/LarvalDispersal8.png
       :align: center
       :width: 40%

Simulation directory
~~~~~~~~~~~~~~~~~~~~

The directory you created with the Create Larval Dispersal Simulation tool and
then loaded with ocean currents.

Results directory
~~~~~~~~~~~~~~~~~

An existing directory to receive the results. You must create it before
running the tool. The tool will create a bunch of outputs within it. If the
outputs already exist, they will be overwritten if the ArcGIS
`overwriteOutput` environment setting is enabled; otherwise the tool will
fail. The documentation for this parameter describes the outputs in detail. We
discuss them more below.

We suggest you make this directory a peer of the simulation directory.
Alternatively you can put it inside the simulation directory, but be careful:
if you run the Create Larval Dispersal Simulation tool again (e.g. by
accidentally rerunning your geoprocessing model) it will delete and recreate
the simulation directory and your results will be lost. If you plan to run
simulations using multiple parameters–e.g. different start dates, durations,
settlement parameters–you should name the directory in a way that lets you
remember those values. However, if you forget to do this, the tool creates a
text file within the results directory that lists the parameter values for
that run. 

Start date
~~~~~~~~~~

The start date for your simulation. If desired, you may also include a time;
if you don't, midnight (00:00:00) will be used. Given the typical resolutions
of ocean currents data products, specifying the time is not likely to be
important.

The time zone is whatever the ocean currents data used. For many products,
this is UTC.

Duration
~~~~~~~~

The number of days to simulate. The first time you run your simulation, We
highly recommend you use a short duration such as 2-5 days and limit the
simulation to just a few patches (using the Patches that Disperse Larvae
parameter). This will let you check whether there are any basic problems, such
as the Time Step being too large or too small (see below), or some cells
missing ocean currents values. You can also quickly check the results to see
if the tool is doing what you thought it would do.

Next, increase the duration to the full amount you'd like to simulate. Usually
this is the pelagic larval duration (PLD) value for the species you are
modeling. If you are testing multiple PLD values, use the shortest one. Again,
do this for just a few patches and check that the output looks reasonable.
This will demonstrate that the tool can run for a few patches without failing
due to insufficient memory. It will also give you an idea how long the full
simulation takes, per patch, so you can plan when to run the full simulation
(e.g. overnight or while you're away from work).

Finally, when you're ready for the complete simulation, use the full duration
with all of the patches.

Time step
~~~~~~~~~

Number of hours the simulator should advance its clock after recalculating
larval movements and settlement. This is an important parameter that directly
affects both the accuracy of the results and how long the tool will take to
run. Although we provided a default of 1 hour, this may not be an appropriate
value. Depending on your cell size and the maximum speed of your ocean
currents, you might need a smaller value for the simulation to be numerically
stable. Fortunately it is not difficult to determine an appropriate value,
using the following procedure.

First run the tool using default time step of 1 hour. Use a short duration
(2-5 days) and just one patch so it runs very quickly. Every time the tool
runs it performs a numerical stability check. If you get this warning:

.. container:: wrapped-code

    The stability condition is 1.566760, which is greater than 2 ^ -1/2 =
    0.707106. The simulation MAY NOT be numerically stable and the output
    results MAY NOT be correct. To fix this problem, reduce the simulation
    time step to 0.037610 days or less.

It may be followed by one or more warnings about negative density:

.. container:: wrapped-code

    During simulation of patch 137, a negative density was detected during
    step 8 of the simulation. This indicates a numerical stability problem
    with the MPDATA algorithm. You should reduce the simulation time step to a
    lower value and try again. If this does not resolve the problem, please
    contact the MGET development team for assistance.

The presence of either of these messages indicates that the time step is too
long. When the cell size is small or the ocean currents are fast, a shorter
time step is needed. Reduce the time step to the value recommended in the
first warning, or something shorter. 

Note that the warning message reports the time step in days but the tool
requires you input it hours. We are sorry for the inconvenience. To convert
days to hours, multiply by 24.

Later, when the results are visualized, it will be inconvenient if the time
step cannot be divided evenly into 24 hours. So don't just convert the
recommended value reported by the warning to hours and plug it into the tool.
For example, in the example above, don't use 0.90264 hours. Use something like
0.5 hours instead, so exactly 48 time steps occur per day.

Now run the tool again and verify that the warning goes away. Instead you
should get this message:

.. container:: wrapped-code

    The stability condition is 0.391690, which is less than or equal to 2 ^
    -1/2 = 0.707106. The simulation will be numerically stable.

Now run the tool again for the full simulation duration (e.g. 30 days). If you
get the warning again, it means that during the full period there was a faster
current than you encountered during the initial shorter simulation. Reduce the
time step further and rerun the full simulation again until the warning goes
away.

If you see that the stability condition is very low, e.g. below 0.1, it
indicates that the time step is shorter than it needs to be. This may happen,
for instance, when you use the default time step of 1 hour with relatively
coarse resolution currents or your study area has relatively slow currents.
There is no harm in simulating using a very short time step. But the length of
time the tool requires to run is directly proportional to the time step. If
you increase the time step the tool will complete in a shorter time, which can
be advantageous.

The amount of memory required to run the simulation does not depend on the
time step. If you receive an ``OUT OF MEMORY`` error while running the
simulation, increasing the time step will generally not solve the problem (but
increasing the Simulation Summarization Period might; see below).

Whenever you change the time step, after you settle on a final value always
adjust the Simulation Summarization Period as well (see below).

Simulation summarization period
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of simulation time steps at which the simulation results should be
"summarized". This parameter affects two important aspects of the simulation
and directly influences the amount of memory required to execute the
simulation, so it should be chosen carefully.

The first thing this parameter influences concerns the production of
visualizations (Step 4 below) that summarize the results of the simulation. As
the simulation runs, each time the summary period elapses the tool records an
image of larval density at that point in the simulation, among other things.
The first summarization occurs at the moment larvae are released but before
any time has elapsed. The subsequent summarizations occur after the specified
number of time steps elapse. For example, if the time step is 0.5 hours and
the summarization period is 24, a summarization will occur every 12 hours.

Using the summary records, the visualization tool in Step 4 produces a time
series of larval density rasters–one raster each time a summary occurs. The
date and time of the summarization are stamped into each raster's name. It is
therefore convenient to choose a time step and summarization period that
produce rasters at human-friendly summarization times, such as once per day,
once per 6 hours, etc. In this respect, your choice of the summarization
period is mainly an aesthetic choice: do you want many frequent larval density
rasters, or just a few infrequent rasters?

The second thing this parameter influences concerns larval mortality, an
optional process that you apply in Step 4 below. The summarization period
determines the frequency at which mortality will be applied during that step.

Settlement parameters
~~~~~~~~~~~~~~~~~~~~~

As the simulation progresses and larvae circulate through the study area, they
may drift through cells labeled as being part of a patch, including the patch
that released them. The settlement parameters determine the rate at which
larvae settle on those cells. Larvae that have settled remain there for the
remainder of the simulation and are counted as having successfully dispersed
from their source patch to the patch they settled on.

Competency gamma a and b
........................

These parameters define a `gamma cumulative distribution function (CDF)
<https://en.wikipedia.org/wiki/Gamma_distribution>`__ that governs the
fraction of larvae that are able to settle given the time that has passed
since they were released at the beginning of the simulation. The ``a``
parameter is also known as alpha, and ``b`` as theta. In the literature, the
period before larvae are able to settle is known as the *precompetency
period*. See Randall et al. (2025) for examples.

By default, these parameters are not provided and all larvae will be
immediately competent: that is, 100% of larvae that drift over a habitat patch
cell will be competent to settle, right from the start of the simulation.

Otherwise, when the competency gamma parameters are provided, all larvae will
initially be incompetent. As time passes the fraction that are competent will
rise according to the gamma CDF defined by the parameters, eventually reaching
100%. When it is still less than 100%, the fraction that are incompetent will
drift through habitat patch cells without settling, while the fraction that
are competent will be eligible to settle.

The tool will generate a plot ``CompetencyCurve.png`` in the results directory
showing the proportion competent for the duration of the simulation. The
figure below shows two examples. The left shows the plot that results if the
gamma parameters are omitted and larvae are immediately competent. The right
right shows a plot with ``a = 10`` and ``b = 0.25``.

.. container:: spaced-image

    .. image:: images/LarvalCompetencyCurve.png
       :align: center
       :width: 80%

To determine these parameters for your species of interest, search the
literature for an assessment of precompetency for it or its closest analogue.
Then choose parameters that best reproduce what you find.

Settlement rate
...............

Two additional parameters beyond the competency function affect settlement.
The first, Settlement Rate, defines the fraction of competent larvae suspended
over suitable habitat that will settle per day. Put anther way, if a competent
larva is suspended over suitable habitat for a day, the Settlement Rate
defines the probability it will settle.

The current implementation of the tool assumes the Settlement Rate is constant
throughout the simulation. It has a default of 0.8, meaning that 80% of the
competent larvae will settle per day they are over suitable habitat. You
should replace this default with a value appropriate for your species of
interest developed from your own research or the literature.

Use sensory zone
................

This is the final parameter that affects settlement. By default it is
disabled. Under this configuration, the fraction of larvae that are considered
"over suitable habitat" and therefore able to settle is based on the patch
cover raster. If a patch is 100% covered, then all of the competent larvae in
that cell will settle according to the Settlement Rate. But if, say, only 30%
of the patch is covered, then only 30% are able to settle. The rest will
continue drifting.

If Use Sensory Zone is enabled, then 100% of the competent larvae within the
cell are able to settle, and the patch cover raster is disregarded (it is
still used to determine how many are released at start of the simulation). The
idea here is that once larvae enter the cell, they can sense the habitat and
effect their settlement upon it, e.g. by vertical movement, controlling their
orientation, actively swimming, etc.

Whether this is realistic depends on the species and the cell size of the
analysis, with plausibility being higher when cells are smaller. If your study
area is filled with patches that have low patch cover values, this parameter
can play a major role in how many larvae settle on small patches. You should
consider the biology of your species carefully before enabling it.

Note that this parameter only affects larvae within a cell, not adjacent cells
or cells further away. Advection and diffusion are the only processes that
affect movement of larvae between cells.

Additional parameters
~~~~~~~~~~~~~~~~~~~~~

Patches that disperse larvae
............................

By default, this parameter is empty, and all patches will release larvae at
the start of the simulation. Use this parameter to limit the release of larvae
to specific patches. 

The length of time required to run the simulation scales linearly with this
parameter, so you can use it to make a quick check that the simulation
functions as you expected.

Patches that larvae can settle on
.................................

By default, this parameter is empty, and all patches are eligible to receive
larvae. Use this parameter to limit settlement to specific patches. Larvae
that drift over patches that are not listed will continue drifting rather than
settling.

This parameter has no effect on the length of time required to run the
simulation.

Diffusivity
...........

The horizontal diffusivity coefficient, in meters squared per second, to
use in the simulation.

It is recommended that you consult an oceanographer to determine this value.
The original study from which this tool was developed (Treml et al. 2012) used
the value 50. If you specify zero or omit this value, diffusion will not be
performed, which will greatly reduce the simulation run time.

Common warning and error messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ocean currents images are missing data
..........................................

If you receive the warning:

.. container:: wrapped-code

    The ocean currents images are missing data for some cells flagged as water
    by your water mask. This will affect the accuracy of the simulation. The
    simulator will assume the ocean currents have a velocity of zero in these
    cells. Larvae that enter these cells can only exit via diffusion. These
    cells may retain larvae in a manner that is not realistic.

or:

.. container:: wrapped-code

    The ocean currents images are missing data for some cells flagged as
    habitat patches. This will affect the accuracy of the simulation. The
    simulator will assume the ocean currents have a velocity of zero in these
    cells. Larvae can only exit these cells via diffusion. These cells may
    retain larvae in a a manner that is not realistic. The IDs of the affected
    patches are: <a list of patch IDs>

Fix this by recreating the simulation and then, when you run the Load Currents
tool, use the Method For Estimating Missing Currents parameter to fill in the
missing values. See the discussion of that parameter in Step 3 above.

The stability condition is <some value>, which is greater than 2 ^ -1/2
.......................................................................

.. container:: wrapped-code

    The stability condition is 1.566760, which is greater than 2 ^ -1/2 =
    0.707106. The simulation MAY NOT be numerically stable and the output
    results MAY NOT be correct. To fix this problem, reduce the simulation
    time step to 0.037610 days or less.

Fix this by decreasing the Time Step parameter. See above for further discussion.

During simulation of patch <some value>, a negative density was detected
........................................................................

.. container:: wrapped-code

    During simulation of patch 137, a negative density was detected during
    step 7 of the simulation. This indicates a numerical stability problem
    with the MPDATA algorithm. You should reduce the simulation time step to a
    lower value and try again. If this does not resolve the problem, please
    contact the MGET development team for assistance.

This should only happen when the Time Step is much too large, and will be
preceded by the stability condition warning. Fix this by decreasing the Time
Step parameter. See above for further discussion.

The start date / end date occurs too far before / after ...
...........................................................

The simulation may fail with this error:

.. container:: wrapped-code

    ValueError: The start date of the simulation (2010-09-20 00:00:00) occurs
    too far before the date of the first ocean currents image (2011-09-20
    00:00:00) that is loaded in the larval dispersal simulation in directory
    C:\GOM_Connectivity\Simulation. To fix this problem, either move the start
    date forward or load some older ocean currents data into the simulation,
    so that the start date matches up with the currents data.

or:

.. container:: wrapped-code

    ValueError: The end date of the simulation (2011-11-19 00:00:00) occurs
    too far after the date of the last ocean currents image (2011-10-20
    00:00:00) that is loaded in the larval dispersal simulation in directory
    C:\GOM_Connectivity\Simulation. To fix this problem, either move the start
    date backward, reduce the duration of the simulation, or load some more
    recent ocean currents data into the simulation, so that the end date
    matches up with the currents data.

The usual reason for these messages is that you that changed your dates or
duration but forgot to load additional ocean currents into the simulation. The
messages suggest solutions.


Step 4: Visualize the results
-----------------------------

The Run Larval Dispersal Simulation tool writes the results of the simulation
to the file ``Results.pickle`` as Python `numpy <https://numpy.org/>`__
arrays. If you are a Python programmer, you can unpickle this file and work
with them directly. For more information about the arrays, see the
documentation for the Results Directory parameter of the Run tool.

Alternatively, you can use the Visualize Larval Dispersal Simulation tool to
create a geodatabase with three outputs: a time series of rasters showing the
density of larvae across the study area through time, a time-enabled mosaic of
the density rasters, and a line feature class showing the connections between
patches that resulted from the simulation.

Time series of density rasters and time-enabled mosaic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The rasters are named by date and time. The first raster will be at the start
of the simulation, when all larvae have been released but before any have
moved. After that, one raster will be generated each time the summarization
period elapses. The unit of these rasters is the quantity of larvae per grid
cell.

The ``DensityMosaic`` contains all of the rasters, in order, with
``StartTime`` and ``EndTime`` fields for each. When you add ``DensityMosaic``
to a map, you should see the ArcGIS Time Slider appear, along with a Time tab.
Press play on the time slider to see how the distribution of larvae evolves
through time. You will have to configure the symbology to show the density
using color ranges suitable for your dispersal scenario.

Connectivity feature class
~~~~~~~~~~~~~~~~~~~~~~~~~~

The Connectivity feature class contains lines between all pairs of patches
that have sufficiently strong connections. The lines are directional,
originating at a source patch centroid and terminating at a destination patch
(or "sink patch") centroid. You can add the feature class to a map and
symbolize the lines with an arrow at the end to see the direction of flow.

The Minimum Dispersal Threshold parameter controls how strong the connection
must be for a line to be drawn. If sufficient larvae flowed in both directions
between two patches, one line will be drawn in each direction; the two lines
will exactly overlap. If a patch experienced sufficient self recruitment
(larvae released by the patch settled at that same patch), a circular line
will be drawn from the patch's centroid to itself. For convenience of
visualization, the size of the circle is scaled to the length of the "minor
axis" of the zonal geometry of the patch; the size does not relate to the
degree of connectivity.

Each line has four attributes:

* ``FromPatchID`` - source patch that released larvae.

* ``ToPatchID`` - destination patch that larvae settled on.

* ``Quantity`` - quantity of larvae that settled. The units are relative to
  the maximum possible quantity that can occupy a cell at the start of the
  simulation when larvae are first released. The value 1.0 corresponds to the
  quantity of larvae released at the start of the simulation in one cell that
  is fully covered by suitable habitat (i.e. the Patch Cover Raster has the
  value 1.0 in that cell).

* ``Probability`` - probability that a larva released by the source patch
  settled on the destination patch. This is computed by dividing the Quantity
  (above) by the total amount of larvae released by the source patch at the
  start of the simulation.

Tool parameters
~~~~~~~~~~~~~~~

Now let's look at the tool parameters:

.. container:: spaced-image

    .. image:: images/LarvalDispersal9.png
       :align: center
       :width: 40%

Simulation directory and Results directory
..........................................

These are the same directories you used above.

Output geodatabase name
.......................

Give the output geodatabase a sensible name. If you don't know what to choose,
use ``Results``.

The tool supports storing multiple output geodatabases for the same simulation
run in the same results directory. This is mainly useful when you want to vary
some of the visualization parameters below to see how they change the results.
For example, you may want to try different mortality rates and see how they
affect the resulting connectivity network. To do that, run the Visualize tool
once for each mortality rate, setting the output geodatabase name to a
different value each time.

If you re-execute the Run Simulation tool with different parameters, you
should create a different results directory.

Mortality rate and mortality method
...................................

This is proportion of larvae that are still alive that die per day. For
example, the value 0.1 means that 10% will die per day. If omitted, the
default, larvae will not be subject to mortality.

The Mortality Method parameter determines which of two equations from the
literature will be used to compute mortality. The equations yield slightly
different results. Please see the documentation for this parameter for
details.

When mortality is used, the tool will create a plot named
``X_SurvivorshipCurve.png`` that shows the proportion of larvae alive over
time, assuming all drift without settling. ``X`` is the name of the output
geodatabase. If competency was used, the tool also creates a plot called
``X_SurvivorshipCurveWithCompetency.png`` that multiplies the survivorship
curve by the competency curve, giving the number of larvae alive that are
competent to settle at each point in time. Below are examples of these plots,
using a mortality rate of 0.1, competency a of 10 and b of 0.25.

.. container:: spaced-image

    .. image:: images/LarvalSurvivorshipCurves.png
       :align: center
       :width: 80%

.. note::
    The tool applies mortality at each summarization period, after larvae have
    moved but before they settle. For plausible results, it is therefore
    important to ensure the summarization period is small relative to
    between-patch transit times, or an unrealistically large fraction of
    larvae will be killed by mortality before they have the chance to settle.

The plot on the right above shows a similar issue, in which competency changed
rapidly between 0 and 5 days, but summarization occurred only once per day, so
mortality was only assessed once per day. As a result, the curve does not
appear very smooth between these days. To address this, you could reduce the
summarization period, e.g. to once per 6 hours.

Create density rasters
......................

Disabling Create Density Rasters will prevent the tool from creating density
rasters in the output geodatabase. If you don't care about the density
rasters, you can disable their creation to speed the tool up and reduce the
size and clutter of the output geodatabase.

Minimum density value
.....................

When density rasters are created, cells that have less than the Minimum
Density Value will be set to NoData. By default, it is set to 0.00001, or
1/100,000 of the amount of larvae released by a cell that is fully covered by
suitable habitat.

This is mainly an aesthetic parameter. If you increase it, the "blobs" of
density shown in the rasters will be smaller. Do this if you want to the
rasters to highlight the flow of distinct concentrations of density as the
simulation progresses.


Exclude incompetent larvae from density rasters
...............................................

This is another aesthetic parameter. If you enable it and your simulation uses
competency, then initially the density rasters will be empty, when all of the
larvae are incompetent. Density concentrations will appear as time passes and
the pre-competency period elapses.

Create connections feature class
................................

Disable the creation of the connections feature class (``Connectivity`` in the
output geodatabase) if you're only interested in the density rasters. The
connections feature class can take a long time to produce if there are many
connections.

Minimum dispersal threshold
...........................

The Minimum Dispersal Threshold that must be met or exceeded for the tool to
draw a line connecting the source patch to a destination patch. By default, it
is set to 0.00001, or 1/100,000 of the amount of larvae released by a cell
that is fully covered by suitable habitat. Increase it to show just the
strongest connections, or reduce it to show even weaker connections. In the
Gulf of Mexico example, if we increase it from the default (below left) to
0.001 (below right), many fewer connections are drawn.

.. container:: spaced-image

    .. image:: images/LarvalDispersal10.png
       :align: center
       :width: 90%

The threshold can be specified as either a minimum quantity of larvae released
by the source that must settle at the destination, or as the minimum
probability that a larva released by the source will settle at the
destination. The Minimum Dispersal Threshold Type parameter specifies which
kind of threshold is used.

This parameter must be greater than zero. If you set it to a very small value,
almost all patches will have lines drawn between them. This result may seem
surprising. For most simulations, larvae will have spread throughout the
entire study area, albeit in very small quantities for most cells, via the
diffusion component of the hydrodynamic calculations. Diffusion occurs
equally in all directions at the rate specified by the Diffusivity parameter.
Given enough time, an infinitesimal fraction of larvae from any given patch
can theoretically spread throughout the entire ocean simply by diffusion.

.. note::
    An important question is: why not set this parameter to a very small value
    and then filter weak connections later, e.g. in the map itself by applying
    a Definition Query to the layer? This is a valid approach. The main reason
    not to do this is it may take the tool a long time to create so many lines
    in the feature class. Whether or not this is a problem depends on the
    number of patches you have. Assuming each patch can be both a source and
    sink for larvae, the number of possible connections is ``2 * P^2``, where
    ``P`` is the number of patches. So if you only have 20 patches, at most
    800 lines will be created, a relatively small number. But if you have 500
    patches, as many as 500,000 lines will be created, which can take a
    considerable amount of time.

Minimum threshold dispersal type
................................

The type of minimum dispersal threshold that will be used to determine whether
a line should be drawn from a source patch to a destination patch. One of:

* ``Quantity`` - the minimum absolute quantity of larvae released by the
  source patch that must settle at the destination patch. A cell that is 100%
  covered by suitable habitat will release 1 unit of larvae, while one that is
  only 50% covered will release 0.5 units of larvae.

* ``Probability`` - the minimum probability that a larva released by the
  source patch will settle at the destination patch. For each
  source-destination pair, the probability is computed by dividing the
  absolute quantity of larvae from the source that settled on the destination
  by the total absolute quantity of larvae released by the source. For
  example, consider a source comprised of 5 cells that are 100% covered and 3
  cells that are 50% covered. The total quantity of larvae released will be
  6.5 units. If a destination patch receives in 0.52 units of larvae, totaled
  across all of its cells, then the probability is 0.52 / 6.5 = 0.08.


References
----------

Choukroun S, Stewart OB, Mason LB, Bode M. (2025) Larval dispersal predictions
are highly sensitive to hydrodynamic modelling choices. Coral Reefs 44: 1–13.

Mora C, Treml EA, Roberts J, Crosby K, Roy D, Tittensor DP (2012) High
connectivity among habitats precludes the relationship between dispersal and
range size in tropical reef fishes. Ecography 35: 89–96.

Schill SR, Raber GT, Roberts JJ, Treml EA, Brenner J, Halpin PN (2015) No Reef
Is an Island: Integrating Coral Reef Connectivity Data into the Design of
Regional-Scale Marine Protected Area Networks. PLoS ONE 10(12): e0144199.

Smolarkiewicz PK (1983) A simple positive definite advection scheme with small
implicit diffusion. Monthly Weather Review 111: 479–86.

Smolarkiewicz PK (2006) Multidimensional positive definite advection transport
algorithm: an overview. International Journal for Numerical Methods in Fluids
50: 1123–44.

Smolarkiewicz PK, Margolin LG (1998) MPDATA: a finite difference solver for
geophysical flows. Journal of Computational Physics 140: 459–80.

Treml E, Halpin P, Urban D, Pratson L (2008) Modeling population connectivity
by ocean currents, a graph-theoretic approach for marine conservation.
Landscape Ecology 23:19–36.

Treml EA, Roberts JJ, Chao Y, Halpin P, Possingham HP, Riginos C (2012a)
Reproductive output and duration of the pelagic larval stage determine
seascape-wide connectivity of marine populations. Integrative and Comparative
Biology 52(4): 525-537.

Treml EA, Roberts J, Halpin PN, Possingham HP, Riginos C (2015) The emergent
geography of biophysical dispersal barriers across the Indo-West Pacific.
Diversity and Distributions 21: 465-476.
