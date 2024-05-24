# _OGRTabularLayerMetadata.py - Metadata for classes defined in
# _OGRTabularLayer.py.
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

from .. import Dataset
from ._OGRTabularLayer import OGRTabularLayer


###############################################################################
# Metadata: OGRTabularLayer class
###############################################################################

AddClassMetadata(OGRTabularLayer,
    module=__package__,
    shortDescription=_('A :class:`Table` representing a tabular dataset accessed through GDAL\'s :py:class:`osgeo.ogr.Layer` class.'),
    longDescription=_(
"""
Warning:
    This class is not fully implemented yet and should not be used at this time.
"""))

# Public properties

AddPropertyMetadata(OGRTabularLayer.DataSourceName,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Name or path to the GDAL data source. For example, for a shapefile, this is the directory containing it.'))

AddPropertyMetadata(OGRTabularLayer.LayerName,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Name of the layer in the GDAL data source. For example, for a shapefile, this is the filename including the ``.shp`` extension.'))

AddPropertyMetadata(OGRTabularLayer.DriverName,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    shortDescription=_('Name of the GDAL driver to use. If not provided, GDAL will try to guess it from the data source and layer names. For a list of supported drivers, see the `GDAL documentation <https://gdal.org/drivers/vector/index.html>`_.'))

AddPropertyMetadata(OGRTabularLayer.IsUpdatable,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, the GDAL data source will be opened in update mode. If False, it will be opened in read-only mode. Not all GDAL drivers support updating. Please see the GDAL documentation for more information.'))

# Public constructor: OGRTabularLayer.__init__

AddMethodMetadata(OGRTabularLayer.__init__,
    shortDescription=_('OGRTabularLayer constructor.'))

AddArgumentMetadata(OGRTabularLayer.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=OGRTabularLayer),
    description=_(':class:`%s` instance.') % OGRTabularLayer.__name__)

AddArgumentMetadata(OGRTabularLayer.__init__, 'dataSourceName',
    typeMetadata=OGRTabularLayer.DataSourceName.__doc__.Obj.Type,
    description=OGRTabularLayer.DataSourceName.__doc__.Obj.ShortDescription)

AddArgumentMetadata(OGRTabularLayer.__init__, 'layerName',
    typeMetadata=OGRTabularLayer.LayerName.__doc__.Obj.Type,
    description=OGRTabularLayer.LayerName.__doc__.Obj.ShortDescription)

AddArgumentMetadata(OGRTabularLayer.__init__, 'update',
    typeMetadata=OGRTabularLayer.IsUpdatable.__doc__.Obj.Type,
    description=OGRTabularLayer.IsUpdatable.__doc__.Obj.ShortDescription)

AddArgumentMetadata(OGRTabularLayer.__init__, 'driverName',
    typeMetadata=OGRTabularLayer.DriverName.__doc__.Obj.Type,
    description=OGRTabularLayer.DriverName.__doc__.Obj.ShortDescription)

AddResultMetadata(OGRTabularLayer.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=OGRTabularLayer),
    description=_(':class:`%s` instance.') % OGRTabularLayer.__name__)

# Public method: OGRTabularLayer.Open

AddMethodMetadata(OGRTabularLayer.Open,
    shortDescription=_('Opens a tabular layer in a GDAL data source.'))

AddArgumentMetadata(OGRTabularLayer.Open, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=OGRTabularLayer),
    description=_(':class:`%s` or an instance of it.') % OGRTabularLayer.__name__)

CopyArgumentMetadata(OGRTabularLayer.__init__, 'dataSourceName', OGRTabularLayer.Open, 'dataSourceName')
CopyArgumentMetadata(OGRTabularLayer.__init__, 'layerName', OGRTabularLayer.Open, 'layerName')
CopyArgumentMetadata(OGRTabularLayer.__init__, 'update', OGRTabularLayer.Open, 'update')
CopyArgumentMetadata(OGRTabularLayer.__init__, 'driverName', OGRTabularLayer.Open, 'driverName')

CopyResultMetadata(OGRTabularLayer.__init__, 'obj', OGRTabularLayer.Open, 'obj')

# Public method: OGRTabularLayer.Create

AddMethodMetadata(OGRTabularLayer.Create,
    shortDescription=_('Create a new tabular layer in a GDAL data source.'))

CopyArgumentMetadata(OGRTabularLayer.Open, 'cls', OGRTabularLayer.Create, 'cls')
CopyArgumentMetadata(OGRTabularLayer.Open, 'dataSourceName', OGRTabularLayer.Create, 'dataSourceName')
CopyArgumentMetadata(OGRTabularLayer.Open, 'layerName', OGRTabularLayer.Create, 'layerName')

AddArgumentMetadata(OGRTabularLayer.Create, 'geometryType',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection', 'Point25D', 'LineString25D', 'Polygon25D', 'MultiPoint25D', 'MultiLineString25D', 'MultiPolygon25D', 'GeometryCollection25D']),
    description=_('Geometry type for the layer. If omitted, the layer will not have geometry. Depending on the underlying format, not all geometry types may be supported. See the GDAL documentation for more information.'))

AddArgumentMetadata(OGRTabularLayer.Create, 'srType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['WKT', 'ArcGIS', 'Proj4', 'Obj'], makeLowercase=True, canBeNone=True),
    description=Dataset.ConvertSpatialReference.__doc__.Obj.Arguments[1].Description + ' If :py:data:`None`, the spatial reference of the layer will remain unset.')

CopyArgumentMetadata(Dataset.ConvertSpatialReference, 'sr', OGRTabularLayer.Create, 'sr')

AddArgumentMetadata(OGRTabularLayer.Create, 'options',
    typeMetadata=DictionaryTypeMetadata(keyType=UnicodeStringTypeMetadata(minLength=1), valueType=AnyObjectTypeMetadata(), canBeNone=True),
    description=_('Driver-specific dictionary of GDAL options and their values.'))

CopyArgumentMetadata(OGRTabularLayer.Open, 'driverName', OGRTabularLayer.Create, 'driverName')

CopyResultMetadata(OGRTabularLayer.Open, 'obj', OGRTabularLayer.Create, 'obj')

########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.GDAL instead.
########################################################################################

__all__ = []
