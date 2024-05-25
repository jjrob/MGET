# _ArcGISRasterBandMetadata.py - Metadata for classes defined in
# _ArcGISRasterBand.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...ArcGIS import ArcGISDependency
from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from .. import Grid
from ._ArcGISRaster import ArcGISRaster
from ._ArcGISRasterBand import ArcGISRasterBand


###############################################################################
# Metadata: ArcGISRasterBand class
###############################################################################

AddClassMetadata(ArcGISRasterBand,
    module=__package__,
    shortDescription=_('A 2D raster band represented as a :class:`~GeoEco.Datasets.Grid`.'))

# Public properties

AddPropertyMetadata(ArcGISRasterBand.Band,
    typeMetadata=IntegerTypeMetadata(minValue=1),
    shortDescription=_('The band number.'))

# Public constructor: ArcGISRasterBand.__init__

AddMethodMetadata(ArcGISRasterBand.__init__,
    shortDescription=_('ArcGISRasterBand constructor.'),
    dependencies=[ArcGISDependency()])

AddArgumentMetadata(ArcGISRasterBand.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRasterBand),
    description=_(':class:`%s` instance.') % ArcGISRasterBand.__name__)

AddArgumentMetadata(ArcGISRasterBand.__init__, 'arcGISRaster',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRaster),
    description=_(':class:`%s` instance that is the parent of this :class:`%s` instance.') % (ArcGISRaster.__name__, ArcGISRasterBand.__name__))

AddArgumentMetadata(ArcGISRasterBand.__init__, 'band',
    typeMetadata=ArcGISRasterBand.Band.__doc__.Obj.Type,
    description=ArcGISRasterBand.Band.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(Grid.__init__, 'queryableAttributeValues', ArcGISRasterBand.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(Grid.__init__, 'lazyPropertyValues', ArcGISRasterBand.__init__, 'lazyPropertyValues')

AddResultMetadata(ArcGISRasterBand.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRasterBand),
    description=_(':class:`%s` instance.') % ArcGISRasterBand.__name__)

# Public method: ArcGISRasterBand.ConstructFromArcGISPath

AddMethodMetadata(ArcGISRasterBand.ConstructFromArcGISPath,
    shortDescription=_('Given a path to a raster, returns an :class:`ArcGISRasterBand`.'),
    longDescription=_(
"""This is a convenience function that allows an :class:`ArcGISRasterBand` to
be instantiated with a single function call, rather than instantiating an
:class:`ArcGISRaster` and then querying it to get the
:class:`ArcGISRasterBand`, which is how this function is implemented. The
:class:`ArcGISRaster` is not returned but is referenced as the parent
collection of the :class:`ArcGISRasterBand` that is returned. It will be
garbage collected automatically when the :class:`ArcGISRasterBand` is
deleted."""))

AddArgumentMetadata(ArcGISRasterBand.ConstructFromArcGISPath, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=ArcGISRasterBand),
    description=_(':class:`%s` or an instance of it.') % ArcGISRasterBand.__name__,
    dependencies=[ArcGISDependency()])

AddArgumentMetadata(ArcGISRasterBand.ConstructFromArcGISPath, 'path',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_('ArcGIS catalog path to the raster or a raster band. If a path to a raster is given, the first band will be opened. If a path to a band is given, that band will be opened.'))

CopyArgumentMetadata(ArcGISRaster.__init__, 'decompressedFileToReturn', ArcGISRasterBand.ConstructFromArcGISPath, 'decompressedFileToReturn')
CopyArgumentMetadata(ArcGISRaster.__init__, 'queryableAttributeValues', ArcGISRasterBand.ConstructFromArcGISPath, 'queryableAttributeValues')
CopyArgumentMetadata(ArcGISRaster.__init__, 'lazyPropertyValues', ArcGISRasterBand.ConstructFromArcGISPath, 'lazyPropertyValues')
CopyArgumentMetadata(ArcGISRaster.__init__, 'cacheDirectory', ArcGISRasterBand.ConstructFromArcGISPath, 'cacheDirectory')

CopyResultMetadata(ArcGISRasterBand.__init__, 'obj', ArcGISRasterBand.ConstructFromArcGISPath, 'obj')


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
