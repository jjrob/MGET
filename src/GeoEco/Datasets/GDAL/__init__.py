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

from ._OGRTabularLayer import OGRTabularLayer
# from ._GDALDataset import GDALDataset
# from ._GDALRasterBand import GDALRasterBand


###############################################################################
# Metadata: module
###############################################################################

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_(':class:`Dataset`\\ s and :class:`DatasetCollection`\\ s that wrap the `Geospatial Data Abstraction Library (GDAL) <https://gdal.org>`_.'))

from . import _OGRTabularLayer
# from . import _GDALDataset
# from . import _GDALRasterBand


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['OGRTabularLayer']
#           'GDALDataset',
#           'GDALRasterBand']
