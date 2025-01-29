# MGET Release Notes

## v3.2.0 - Under construction

### Added
- RWorkerProcess class, for invoking R from Python as a child process

### Fixed
- NameError raised by ArcGISWorkspace.QueryDatasets() when the workspace is an ArcGIS geodatabase that contains relationship classes ([#23](https://github.com/jjrob/MGET/issues/23))

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
  - Python 3.9-3.12 
  - ArcGIS Pro 3.2.2 and later is optional but required for full functionality
- Python wheels installable from https://pypi.org/project/mget3
- Dropped support for Python 2.x, ArcGIS Desktop, and 32-bit platforms
- Most tools from the last release of MGET 0.8 for Python 2.x and ArcGIS Desktop have not been ported to MGET 3.x yet
