# MGET Release Notes

## [v3.4.0](https://github.com/jjrob/MGET/releases/tag/v3.4.0) - 2025-07-14

### Added
- Add a tolerance parameter to MaskedGrid ([#40](https://github.com/jjrob/MGET/issues/40))
- Port HDF4.py module from MGET 0.8 to MGET 3 ([#44](https://github.com/jjrob/MGET/issues/44))

### Fixed
- When opening ERDAS (.img) float32 files with nan as the NoData value, "Warning 1: NaN converted to INT_MAX" is printed ([#37](https://github.com/jjrob/MGET/issues/37))
- MGET functions that require MATLAB fail on Windows with UnboundLocalError: cannot access local variable 'oldLdLibraryPath' where it is not associated with a value ([#38](https://github.com/jjrob/MGET/issues/38))
- pyparsing ParserElement.enable_packrat() unexpectedly deletes MGET objects and should no longer be used ([#39](https://github.com/jjrob/MGET/issues/39))
- Using RWorkerProcess to send a Python range() object to R results in TypeError: Object of type range is not JSON serializable ([#42](https://github.com/jjrob/MGET/issues/42))
- Copernicus functions and tools fail with TypeError: open_dataset_from_arco_series() got an unexpected keyword argument 'opening_dask_chunks'. ([#43](https://github.com/jjrob/MGET/issues/43))

## [v3.3.0](https://github.com/jjrob/MGET/releases/tag/v3.3.0) - 2025-05-06

### Added
- WindFetchGrid: add "maximum distance per direction" and "report progress" parameters ([#33](https://github.com/jjrob/MGET/issues/33))
- Add gdalWarp option to GDALDataset constructor ([#35](https://github.com/jjrob/MGET/issues/35))
- Add BlockStatisticsGrid, which partitions an input Grid into non-overlapping blocks of cells and computes a summary statistic for each block, yielding a reduced resolution representation of it

### Fixed
- RWorkerProcess.Start fails with WARNING Error in findPort(port) : Port must be an integer in the range of 1024 to 49151 ([#27](https://github.com/jjrob/MGET/issues/27))
- Create Rasters for CMEMS Dataset invoked from ArcGIS fails with `TypeError: The value provided for the outputWorkspace parameter is an instance of <class 'GeoEco.ArcGIS._ArcGISObjectWrapper'>, an invalid type. Please provide an instance of <class 'str'>.` ([#30](https://github.com/jjrob/MGET/issues/30))
- To improve performance, FileTypeMetadata.Exists() should use base Python rather than DataManagement.Files.File.Exists() ([#31](https://github.com/jjrob/MGET/issues/31))
- RuntimeError: Failed to open a variable named "sea_ice_fraction" in netCDF file ... from NASA Earthdata GHRSST GAMSSA_28km-ABOM-L4-GLOB-v01 granules. Detailed error information: KeyError: 'sea_ice_fraction'. ([#32](https://github.com/jjrob/MGET/issues/32))
- FastMarchingDistanceGrid fails with NameError: name 'GridSlice' is not defined ([#34](https://github.com/jjrob/MGET/issues/34))
- When copernicusmarine 2.1.0 is installed, MGET functions fail with ModuleNotFoundError: No module named 'copernicusmarine.download_functions.download_arco_series' ([#36](https://github.com/jjrob/MGET/issues/36))
- MGET functions that require MATLAB fail on Windows with UnboundLocalError: cannot access local variable 'oldLdLibraryPath' where it is not associated with a value ([#38](https://github.com/jjrob/MGET/issues/38))
- pyparsing ParserElement.enable_packrat() unexpectedly deletes MGET objects and should no longer be used ([#39](https://github.com/jjrob/MGET/issues/39))

## [v3.2.0](https://github.com/jjrob/MGET/releases/tag/v3.2.0) - 2025-02-16

### Added
- RWorkerProcess class, for invoking R from Python as a child process
- Start building MGET for Python 3.13 ([#15](https://github.com/jjrob/MGET/issues/15))

### Fixed
- In ArcGIS toolbox, Find and XXXXX tools fail with SyntaxError: invalid syntax (<string>, line 1) and the message: Could not import Python module ""['os.path']"" ([#21](https://github.com/jjrob/MGET/issues/21))
- NameError raised by ArcGISWorkspace.QueryDatasets() when the workspace is an ArcGIS geodatabase that contains relationship classes ([#23](https://github.com/jjrob/MGET/issues/23))
- Update build-wheels.yml to use GDAL 3.10.1 from cgholke's geospatial-wheels v2025.1.20, when testing on Windows ([#24](https://github.com/jjrob/MGET/issues/24))
- Re-enable scikit-fmm dependency on Python 3.12+ for Windows ([#25](https://github.com/jjrob/MGET/issues/25))

## [v3.1.1](https://github.com/jjrob/MGET/releases/tag/v3.1.1) - 2025-01-11

### Fixed
- Datasets/ArcGIS/_ArcGISWorkspace.py: remove ArcGISWorkspace.ToRasterCatalog ([#4](https://github.com/jjrob/MGET/issues/4))
- "Build and test wheels" action should not skip Copernicus tests ([#9](https://github.com/jjrob/MGET/issues/9))
- Metadata.py: remove AppendXMLNodes() and associated functions ([#12](https://github.com/jjrob/MGET/issues/12))
- Update MGET to be compatible with Copernicus Marine Toolbox 2.0.0 ([#17](https://github.com/jjrob/MGET/issues/17))
- On Windows + ArcGIS Pro 3.4, installing MGET with conda fails with: vs2015_runtime 14.27.29016.* is not installable because it conflicts with any installable versions previously repor.  ([#18](https://github.com/jjrob/MGET/issues/18))
- CMEMSARCOArray constructor accepts a lazyPropertyValues parameter but does not use it ([#19](https://github.com/jjrob/MGET/issues/19))
- MaskedGrid fails with AttributeError: np.cast was removed in the NumPy 2.0 release. Use np.asarray(arr, dtype=dtype) instead. ([#20](https://github.com/jjrob/MGET/issues/20))

## [v3.1.0](https://github.com/jjrob/MGET/releases/tag/v3.1.0) - 2024-10-10

### Added
- CMRGranuleSearcher class for querying NASA Earthdata for granules
- GHRSSTLevel4Granules class for querying NASA Earthdata for GHRSST Level 4 granules
- GHRSSTLevel4 class for representing GHRSST Level 4 product as a 3D Grid
- Geoprocessing tools for GHRSST Level 4 products
- InterpolateAtArcGISPoints() function to CMEMSARCOArray ([#13](https://github.com/jjrob/MGET/issues/13))
- More classes to GeoEco.Datasets.Virtual: DerivedGrid, MaskedGrid, MemoryCachedGrid
- GitHub action to test downloading of all data products daily
- Support for numpy 2.x ([#11](https://github.com/jjrob/MGET/issues/11))
- Update ArcGIS Pro installation instructions to use conda-forge package ([#14](https://github.com/jjrob/MGET/issues/14))
- Badges to README.txt giving build, docs, and data products status

### Fixed
- On PublicAPI page, the description is not showing up for GeoEco.DataManagement.ArcGISRasters ([#3](https://github.com/jjrob/MGET/issues/3))

## [v3.0.3](https://github.com/jjrob/MGET/releases/tag/v3.0.3) - 2024-09-25

### Added
- Released docs to https://mget.readthedocs.io/
- Updated README.md to link to relevent docs pages
- Release MGET as a conda package on conda-forge ([#8](https://github.com/jjrob/MGET/issues/8))

## [v3.0.2](https://github.com/jjrob/MGET/releases/tag/v3.0.2) - 2024-09-25

- First public release of MGET for Python 3.x and ArcGIS Pro
  - 64-bit Windows or 64-bit Linux
  - Python 3.9-3.13 
  - ArcGIS Pro 3.2.2 and later is optional but required for full functionality
- Python wheels installable from https://pypi.org/project/mget3
- Dropped support for Python 2.x, ArcGIS Desktop, and 32-bit platforms
- Most tools from the last release of MGET 0.8 for Python 2.x and ArcGIS Desktop have not been ported to MGET 3.x yet
