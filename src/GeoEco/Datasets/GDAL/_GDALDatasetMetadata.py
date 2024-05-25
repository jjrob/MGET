# _GDALDatasetMetadata.py - Metadata for classes defined in
# _GDALDataset.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from ..Collections import FileDatasetCollection
from ._GDALDataset import GDALDataset


###############################################################################
# Metadata: GDALDataset class
###############################################################################

AddClassMetadata(GDALDataset,
    module=__package__,
    shortDescription=_('A 2D raster dataset represented as a :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` of :class:`GDALRasterBand`\\ s.'),
    longDescription=_(
"""The `Geospatial Data Abstraction Library (GDAL) <https://www.gdal.org>`_ is
a free open-source library for accessing geospatial data in a variety of
`raster formats <https://www.gdal.org/formats_list.html>`_ and `vector formats
<https://gdal.org/drivers/vector/index.html>`_ through a common interface.
The fundamental elements of GDAL's raster object model are the
:class:`osgeo.gdal.Dataset` and :class:`osgeo.gdal.Band` classes, wrapped here by
:class:`GDALDataset` and :class:`GDALRasterBand`. A :class:`osgeo.gdal.Dataset`
is an assembly of related :class:`osgeo.gdal.Band`\\ s, typically contained in
the same file, and some information common to them all, such as their
dimensions, coordinate system, spatial extent, and cell size. 

Note:
	The wrapper implemented here may not fully support all of GDAL's formats.
	Also, although GDAL provides some support for bands having more than two
	dimensions and for accessing hierarchical data formats such as HDF and
	NetCDF, those capabilities are not supported by the wrapper implemented
	here. Separate GeoEco classes are provided for accessing HDF, NetCDF, and
	OPeNDAP datasets.
"""))

# Public properties

AddPropertyMetadata(GDALDataset.IsUpdatable,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('Indicates whether the dataset should be opened in update mode, allowing the data within its bands to be changed.'))

# Public constructor: GDALDataset.__init__

AddMethodMetadata(GDALDataset.__init__,
    shortDescription=_('GDALDataset constructor.'))

AddArgumentMetadata(GDALDataset.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALDataset),
    description=_(':class:`%s` instance.') % GDALDataset.__name__)

AddArgumentMetadata(GDALDataset.__init__, 'path',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('path').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('path').Description)

AddArgumentMetadata(GDALDataset.__init__, 'updatable',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""Indicates whether the dataset should be opened in update mode, allowing the
data within its bands to be changed.

GDAL does not allow all formats to be opened in update mode. For more about
this, please see https://www.gdal.org/formats_list.html."""))

AddArgumentMetadata(GDALDataset.__init__, 'decompressedFileToReturn',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('decompressedFileToReturn').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('decompressedFileToReturn').Description)

AddArgumentMetadata(GDALDataset.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name for this dataset to be displayed to the user. If a display
name is not provided, a generic one will be generated
automatically."""))

AddArgumentMetadata(GDALDataset.__init__, 'parentCollection',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('parentCollection').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('parentCollection').Description)

AddArgumentMetadata(GDALDataset.__init__, 'queryableAttributeValues',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Description)

AddArgumentMetadata(GDALDataset.__init__, 'lazyPropertyValues',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('lazyPropertyValues').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('lazyPropertyValues').Description)

AddArgumentMetadata(GDALDataset.__init__, 'cacheDirectory',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('cacheDirectory').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('cacheDirectory').Description)

AddResultMetadata(GDALDataset.__init__, 'gdalDataset',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALDataset),
    description=_(':class:`%s` instance.') % GDALDataset.__name__)


########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.GDAL instead.
########################################################################################

__all__ = []
