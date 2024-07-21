# Datasets/GDAL.py - Datasets and DatasetCollections that wrap the Geospatial
# Data Abstraction Library (GDAL).
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

# To keep file sizes managable, we split the names defined by this package
# across several files.

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('A :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` and :class:`~GeoEco.Datasets.Grid` for accessing rasters and raster bands through the `Geospatial Data Abstraction Library (GDAL) <https://gdal.org>`_.'))

from ._GDALDataset import GDALDataset
from . import _GDALDatasetMetadata

from ._GDALRasterBand import GDALRasterBand
from . import _GDALRasterBandMetadata

# from ._OGRTabularLayer import OGRTabularLayer     # OGRTabularLayer is not fully implemented yet
# from . import _OGRTabularLayerMetadata            # OGRTabularLayer is not fully implemented yet

__all__ = ['GDALDataset',
           'GDALRasterBand']
