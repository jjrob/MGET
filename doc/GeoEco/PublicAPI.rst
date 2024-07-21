Public API
==========

TODO: Write introduction

Datasets
--------

Classes that provide a common wrapper around tabular and gridded datasets
accessible through various software frameworks. These were developed in the
2000s for GeoEco's internal use and predate more recent, widely-used
frameworks that may provide similar functionality with additional features or
a more polished interface. When GeoEco was ported to Python 3, we decided to
expose these to external callers in case they were useful. While we do not
want to discourage you from taking advantage of these classes, if you are
building a complex project that must be maintained long-term (rather than a
one-off script or scientific analysis), we encourage you to consider similar
frameworks that have greater adoption and a robust, well-funded developer
community that supports their long-term maintenance.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.Datasets
    GeoEco.Datasets.ArcGIS
    GeoEco.Datasets.Collections
    GeoEco.Datasets.GDAL
    GeoEco.Datasets.NetCDF
    GeoEco.Datasets.SQLite
    GeoEco.Datasets.Virtual

Data Management
---------------

Utility classes and methods for basic manipulation of different kinds of data.
Much of the functionality provided here is available in modules in Python's
Standard Library or official third-party libraries for specific data formats.
For basic functionality, we encourage you to use those rather than taking a
dependency on the classes and functions provided here, unless they are
particularly convenient or provide something the standard libraries are
missing. The purpose of these is to expose some basic operations as ArcGIS
geoprocessing tools, to fill in what we considered to be gaps in ArcGIS's
collection of tools circa 2010 or so. These functions also wrap these basic
operations with logging, so that other modules in the GeoEco library can
use them and gain automatic logging of basic operations.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.DataManagement.ArcGISRasters
    GeoEco.DataManagement.Directories
    GeoEco.DataManagement.Fields
    GeoEco.DataManagement.Files

Spatial and Temporal Analysis
-----------------------------

Classes with functions that perform various spatial and temporal analysis
tasks.

.. autosummary::
    :toctree: _autodoc/GeoEco
    :template: autosummary/module.rst
    :recursive:

    GeoEco.SpatialAnalysis.Interpolation
