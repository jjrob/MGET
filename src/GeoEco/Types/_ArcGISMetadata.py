# _ArcGISMetadata.py - Metadata for classes defined in _ArcGIS.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import AddClassMetadata


###############################################################################
# Metadata: ArcGISGeoDatasetTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISGeoDatasetTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the path to or name of an ArcGIS geographic dataset.'))

###############################################################################
# Metadata: ArcGISRasterTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISRasterTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the path to or name of a raster dataset.'))

###############################################################################
# Metadata: ArcGISRasterLayerTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISRasterLayerTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the name of an ArcGIS raster layer.'))

###############################################################################
# Metadata: ArcGISRasterCatalogTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISRasterCatalogTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the path to or name of an ArcGIS raster catalog.'))

###############################################################################
# Metadata: ArcGISFeatureClassTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISFeatureClassTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the path to or name of an ArcGIS feature class.'))

###############################################################################
# Metadata: ArcGISFeatureLayerTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISFeatureLayerTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the name of an ArcGIS feature layer.'))

###############################################################################
# Metadata: ShapefileTypeMetadata class
###############################################################################

AddClassMetadata('ShapefileTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the path to or name of a shapefile.'))

###############################################################################
# Metadata: ArcGISWorkspaceTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISWorkspaceTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the path to or name of an ArcGIS workspace.'))

###############################################################################
# Metadata: ArcGISTableTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISTableTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the path to or name of a table.'))

###############################################################################
# Metadata: ArcGISTableViewTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISTableViewTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is the name of an ArcGIS table view.'))

###############################################################################
# Metadata: ArcGISFieldTypeMetadata class
###############################################################################

AddClassMetadata('ArcGISFieldTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is a table field.'))

###############################################################################
# Metadata: CoordinateSystemTypeMetadata class
###############################################################################

AddClassMetadata('CoordinateSystemTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is a coordinate system.'))

###############################################################################
# Metadata: EnvelopeTypeMetadata class
###############################################################################

AddClassMetadata('EnvelopeTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value that must be a geographic envelope represented as a comma-delimited :py:class:`str` of four coordinates ordered LEFT, BOTTOM, RIGHT, TOP.'))

###############################################################################
# Metadata: LinearUnitTypeMetadata class
###############################################################################

AddClassMetadata('LinearUnitTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is a linear unit.'))

###############################################################################
# Metadata: MapAlgebraExpressionTypeMetadata class
###############################################################################

AddClassMetadata('MapAlgebraExpressionTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is an ArcGIS-Desktop-style map algebra expression.'))

###############################################################################
# Metadata: PointTypeMetadata class
###############################################################################

AddClassMetadata('PointTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a 2D point represented as a comma-delimited :py:class:`str` of two coordinates ordered X, Y.'))

###############################################################################
# Metadata: SpatialReferenceTypeMetadata class
###############################################################################

AddClassMetadata('SpatialReferenceTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is an ArcGIS spatial reference.'))

###############################################################################
# Metadata: SQLWhereClauseTypeMetadata class
###############################################################################

AddClassMetadata('SQLWhereClauseTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is a SQL where clause expression.'))

__all__ = []
