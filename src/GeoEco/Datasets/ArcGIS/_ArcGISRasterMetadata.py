# _ArcGISRasterMetadata.py - Metadata for classes defined in _ArcGISRaster.py.
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
from ._ArcGISRaster import ArcGISRaster


###############################################################################
# Metadata: ArcGISRaster class
###############################################################################

AddClassMetadata(ArcGISRaster,
    module=__package__,
    shortDescription=_('A 2D raster dataset represented as a :class:`~GeoEco.Datasets.DatasetCollection` of :class:`ArcGISRasterBand`\\ s.'))

# Public properties

AddPropertyMetadata(ArcGISRaster.Path,
    typeMetadata=ArcGISRasterTypeMetadata(mustExist=True),
    shortDescription=_('ArcGIS catalog path to the raster.'))

CopyPropertyMetadata(FileDatasetCollection.DecompressedFileToReturn, ArcGISRaster.DecompressedFileToReturn)

AddPropertyMetadata(ArcGISRaster.ArcGISDataType,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Data type of the raster. Obtained from the ``DataType`` property returned by arcpy\'s :arcpy:`Describe`.'))

# Public constructor: ArcGISRaster.__init__

AddMethodMetadata(ArcGISRaster.__init__,
    shortDescription=_('ArcGISRaster constructor.'))

AddArgumentMetadata(ArcGISRaster.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRaster),
    description=_(':class:`%s` instance.') % ArcGISRaster.__name__)

AddArgumentMetadata(ArcGISRaster.__init__, 'path',
    typeMetadata=ArcGISRaster.Path.__doc__.Obj.Type,
    description=ArcGISRaster.Path.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISRaster.__init__, 'decompressedFileToReturn',
    typeMetadata=ArcGISRaster.DecompressedFileToReturn.__doc__.Obj.Type,
    description=ArcGISRaster.DecompressedFileToReturn.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(FileDatasetCollection.__init__, 'parentCollection', ArcGISRaster.__init__, 'parentCollection')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributeValues', ArcGISRaster.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'lazyPropertyValues', ArcGISRaster.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'cacheDirectory', ArcGISRaster.__init__, 'cacheDirectory')

AddResultMetadata(ArcGISRaster.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRaster),
    description=_(':class:`%s` instance.') % ArcGISRaster.__name__)


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
