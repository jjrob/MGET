# _GDALRasterBandMetadata.py - Metadata for classes defined in
# _GDALRasterBand.py.
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

from .. import Grid
from ._GDALDataset import GDALDataset
from ._GDALRasterBand import GDALRasterBand


###############################################################################
# Metadata: GDALRasterBand class
###############################################################################

AddClassMetadata(GDALRasterBand,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing a band of a 2D GDAL raster dataset represented by a :class:`GDALDataset`.'))

# Public properties

AddPropertyMetadata(GDALRasterBand.Band,
    typeMetadata=IntegerTypeMetadata(minValue=1),
    shortDescription=_('The band number.'))

# Public constructor: GDALRasterBand.__init__

AddMethodMetadata(GDALRasterBand.__init__,
    shortDescription=_('GDALRasterBand constructor.'))

AddArgumentMetadata(GDALRasterBand.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALRasterBand),
    description=_(':class:`%s` instance.') % GDALRasterBand.__name__)

AddArgumentMetadata(GDALRasterBand.__init__, 'gdalDataset',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALDataset),
    description=_(':class:`%s` instance that is the parent of this :class:`%s` instance.') % (GDALDataset.__name__, GDALRasterBand.__name__))

AddArgumentMetadata(GDALRasterBand.__init__, 'band',
    typeMetadata=GDALRasterBand.Band.__doc__.Obj.Type,
    description=GDALRasterBand.Band.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(Grid.__init__, 'queryableAttributeValues', GDALRasterBand.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(Grid.__init__, 'lazyPropertyValues', GDALRasterBand.__init__, 'lazyPropertyValues')

AddResultMetadata(GDALRasterBand.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALRasterBand),
    description=_(':class:`%s` instance.') % GDALRasterBand.__name__)


########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.GDAL instead.
########################################################################################

__all__ = []
