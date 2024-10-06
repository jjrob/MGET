# MGET Release Notes

## v3.1.0 - Under Development

### Added
- CMRGranuleSearcher class for querying NASA Earthdata for granules
- GHRSSTLevel4Granules class for querying NASA Earthdata for GHRSST Level 4 granules
- GHRSSTLevel4 class for representing GHRSST Level 4 product as a 3D Grid
- Geoprocessing tools for GHRSST Level 4 products
- More classes to GeoEco.Datasets.Virtual: DerivedGrid, MaskedGrid, MemoryCachedGrid
- GitHub action to test downloading of all data products daily
- Support for numpy 2.x ([#11](https://github.com/jjrob/MGET/issues/11))
- Update ArcGIS Pro installation instructions to use conda-forge package ([#14](https://github.com/jjrob/MGET/issues/11))
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
