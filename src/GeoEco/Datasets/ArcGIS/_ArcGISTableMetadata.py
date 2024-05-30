# _ArcGISTableMetadata.py - Metadata for classes defined in _ArcGISTable.py.
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

from .. import CollectibleObject, DatasetCollection
from ._ArcGISTable import ArcGISCopyableTable, ArcGISTable, _ArcPyDASelectCursor, _ArcPyDAUpdateCursor, _ArcPyDAInsertCursor


###############################################################################
# Metadata: ArcGISCopyableTable class
###############################################################################

AddClassMetadata(ArcGISCopyableTable,
    module=__package__,
    shortDescription=_('Mixin that classes representing tables inherit to indicate they can be copied with the :arcpy_management:`Copy` geoprocessing tool.'),
    longDescription=_(
"""The purpose of this mixin is to enable an optimization when calling 
:func:`GeoEco.Datasets.ArcGIS.ArcGISWorkspace.ImportDatasets`: the import will
be substantially faster if
:func:`~GeoEco.Datasets.ArcGIS.ArcGISWorkspace.ImportDatasets` can just copy it
with :arcpy_management:`Copy`. If :arcpy_management:`Copy` cannot be used, then
:func:`~GeoEco.Datasets.ArcGIS.ArcGISWorkspace.ImportDatasets` must create an
empty destination table and import the rows one by one, which is usually
substantially slower.

To enable the use of :arcpy_management:`Copy`, the class representing a table
must inherit this mixin and then implement :func:`GetArcGISCopyablePath`."""))

# Public method: ArcGISCopyableTable.GetArcGISCopyablePath

AddMethodMetadata(ArcGISCopyableTable.GetArcGISCopyablePath,
    shortDescription=_('Called by :func:`~GeoEco.Datasets.ArcGIS.ArcGISWorkspace.ImportDatasets` to get the path to copy.'),
    longDescription=_('Derived classes must implement this function.'))

AddArgumentMetadata(ArcGISCopyableTable.GetArcGISCopyablePath, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISCopyableTable),
    description=_(':class:`%s` instance.') % ArcGISCopyableTable.__name__)

AddResultMetadata(ArcGISCopyableTable.GetArcGISCopyablePath, 'path',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_('Path to the table that should be passed to the :arcpy_management:`Copy` geoprocessing tool to copy the table.'))


###############################################################################
# Metadata: ArcGISTable class
###############################################################################

AddClassMetadata(ArcGISTable,
    module=__package__,
    shortDescription=_('A table, feature class, or other tabular dataset or layer represented as a :class:`~GeoEco.Datasets.Table`.'))

# Public properties

AddPropertyMetadata(ArcGISTable.Path,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('ArcGIS catalog path to the table-like object to open. This can be a table, table view, shapefile, ArcInfo coverage, geodatabase feature class, feature layer, raster dataset, raster layer, or anything else that has fields and that may be accessed through arcpy.'))

AddPropertyMetadata(ArcGISTable.ArcGISDataType,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Data type of the table. Obtained with ``arcpy.Describe(path).DataType``.'))

AddPropertyMetadata(ArcGISTable.ArcGISPhysicalDataType,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Data type of the table\'s catalog path. This will be the same as :attr:`ArcGISDataType` unless the :attr:`Path` is a table view, feature layer, or some other virtual object. Obtained with ``arcpy.Describe(arcpy.Describe(path).CatalogPath).DataType``.'))

AddPropertyMetadata(ArcGISTable.AutoDeleteFieldAddedByArcGIS,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True and :attr:`Path` is a shapefile or dBASE table (.DBF file), the "Id" field (if a shapefile) or "Field1" (if a dBASE table) that was added by ArcGIS when the shapefile or table was created will be automatically deleted the first time :func:`AddField` is called. This parameter is ignored if :attr:`Path` is not a shapefile or dBASE table.'))

# Public method: ArcGISTable.__init__

AddMethodMetadata(ArcGISTable.__init__,
    shortDescription=_('ArcGISTable constructor.'),
    dependencies=[ArcGISDependency()])

AddArgumentMetadata(ArcGISTable.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISTable),
    description=_(':class:`%s` instance.') % ArcGISTable.__name__)

AddArgumentMetadata(ArcGISTable.__init__, 'path',
    typeMetadata=ArcGISTable.Path.__doc__.Obj.Type,
    description=ArcGISTable.Path.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISTable.__init__, 'autoDeleteFieldAddedByArcGIS',
    typeMetadata=ArcGISTable.AutoDeleteFieldAddedByArcGIS.__doc__.Obj.Type,
    description=ArcGISTable.AutoDeleteFieldAddedByArcGIS.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(CollectibleObject.__init__, 'parentCollection', ArcGISTable.__init__, 'parentCollection')
CopyArgumentMetadata(CollectibleObject.__init__, 'queryableAttributeValues', ArcGISTable.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(CollectibleObject.__init__, 'lazyPropertyValues', ArcGISTable.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(DatasetCollection.__init__, 'cacheDirectory', ArcGISTable.__init__, 'cacheDirectory')

AddResultMetadata(ArcGISTable.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISTable),
    description=_(':class:`%s` instance.') % ArcGISTable.__name__)

# In order for the validation code to work for _ArcPyDASelectCursor,
# _ArcPyDAUpdateCursor, and _ArcPyDAInsertCursor, they must have a
# ClassMetadata defined for them. Because we don't export them from the
# GeoEco.Datasets.ArcGIS package, we must attach their metadata to the
# _ArcGISTable module itself.

AddModuleMetadata(
    module='GeoEco.Datasets.ArcGIS._ArcGISTable',
    shortDescription=_('Private module that implements ArcGISTable and related classes.'))

AddClassMetadata(_ArcPyDASelectCursor,
    module='GeoEco.Datasets.ArcGIS._ArcGISTable',
    shortDescription=_('Private class representing a :class:`~GeoEco.Datasets.SelectCursor` implemented with ``arcpy.da.SearchCursor``. Not intended to be instantiated by callers outside GeoEco.'))

AddClassMetadata(_ArcPyDAUpdateCursor,
    module='GeoEco.Datasets.ArcGIS._ArcGISTable',
    shortDescription=_('Private class representing a :class:`~GeoEco.Datasets.UpdateCursor` implemented with ``arcpy.da.SearchCursor``. Not intended to be instantiated by callers outside GeoEco.'))

AddClassMetadata(_ArcPyDAInsertCursor,
    module='GeoEco.Datasets.ArcGIS._ArcGISTable',
    shortDescription=_('Private class representing a :class:`~GeoEco.Datasets.InsertCursor` implemented with ``arcpy.da.SearchCursor``. Not intended to be instantiated by callers outside GeoEco.'))


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
