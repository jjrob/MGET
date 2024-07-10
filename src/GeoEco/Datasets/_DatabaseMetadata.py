# _DatabaseMetadata.py - Metadata for classes defined in _Database.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Dependencies import PythonModuleDependency
from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from ._Database import Database
from ._Table import Table


###############################################################################
# Metadata: Database class
###############################################################################

AddClassMetadata(Database,
    module=__package__,
    shortDescription=_('Mixin class that defines methods for creating and deleting tables, and importing tables from one :class:`Database` into another.'),
    longDescription=_(
"""This class is not intended to be instantiated directly. Instead, it is
inherited by classes that need the functionality it provides. In addition to
inheriting this class, those classes must implement several private functions.
Please see the :class:`Database` source code for more information."""))

# Public method: Database.TableExists

AddMethodMetadata(Database.TableExists,
    shortDescription=_('Returns True if the specified table exists.'),
    isExposedToPythonCallers=True)

AddArgumentMetadata(Database.TableExists, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Database),
    description=_(':class:`%s` instance.') % Database.__name__)

AddArgumentMetadata(Database.TableExists, 'tableName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_('Name of the table.'))

AddResultMetadata(Database.TableExists, 'datasets',
    typeMetadata=BooleanTypeMetadata(),
    description=_('True if the table exists, False if it does not.'))

# Public method: Database.CreateTable

AddMethodMetadata(Database.CreateTable,
    shortDescription=_('Creates a table.'),
    longDescription=_(
"""This method does not add any fields to the table, other than the geometry
field if specified. Use the :func:`~Table.AddField` method of the returned
object to add fields.

Raises:
    :exc:`RuntimeError`: The table already exists, or some other problem
        occurred when creating it.
"""),
    isExposedToPythonCallers=True,
    dependencies=[PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')])

CopyArgumentMetadata(Database.TableExists, 'self', Database.CreateTable, 'self')

AddArgumentMetadata(Database.CreateTable, 'tableName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_('Name of the table to create.'))

AddArgumentMetadata(Database.CreateTable, 'geometryType',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection', 'Point25D', 'LineString25D', 'Polygon25D', 'MultiPoint25D', 'MultiLineString25D', 'MultiPolygon25D', 'GeometryCollection25D']),
    description=_('Geometry type for the table. If omitted, the table will not have geometry. Depending on the underlying storage format, not all geometry types may be supported.'))

AddArgumentMetadata(Database.CreateTable, 'spatialReference',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(':py:class:`osgeo.osr.SpatialReference` instance defining the spatial reference for the table. If omitted, the spatial reference for the table will remain undefined.'))

AddArgumentMetadata(Database.CreateTable, 'geometryFieldName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Name of the geometry field to create. If omitted, the table will not have geometry. The underlying storage format, depending on what it is, may determine the geometry field name, in which case the value provided here will be ignored.'))

AddArgumentMetadata(Database.CreateTable, 'options',
    typeMetadata=DictionaryTypeMetadata(keyType=ClassInstanceTypeMetadata(cls=str), valueType=AnyObjectTypeMetadata(canBeNone=True)),
    description=_('Additional options specific to the underlying storage format.'))

AddResultMetadata(Database.CreateTable, 'table',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(':class:`~GeoEco.Datasets.Table` representing the new table.'))

# Public method: Database.CreateTableFromTemplate

AddMethodMetadata(Database.CreateTableFromTemplate,
    shortDescription=_('Creates a table and adds to it the fields present another table (the template).'),
    longDescription=_(
"""Raises:
    :exc:`RuntimeError`: The table already exists, or some other problem
        occurred when creating it or adding fields.
"""),
    isExposedToPythonCallers=True,
    dependencies=[PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')])

CopyArgumentMetadata(Database.TableExists, 'self', Database.CreateTableFromTemplate, 'self')
CopyArgumentMetadata(Database.CreateTable, 'tableName', Database.CreateTableFromTemplate, 'tableName')

AddArgumentMetadata(Database.CreateTableFromTemplate, 'templateTable',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(':class:`~GeoEco.Datasets.Table` representing the template.'))

AddArgumentMetadata(Database.CreateTableFromTemplate, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), canBeNone=True),
    description=_('Names of the fields in `templateTable` to add to the new table. If omitted, all the fields in `templateTable` will be added.'))

AddArgumentMetadata(Database.CreateTableFromTemplate, 'allowSafeCoercions',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, when the underlying storage format does not support the data type of a field of `templateTable`, the most compact alternative data type will be chosen, so long as it can represent all possible values allowed by the template table\'s data type. If False, coercions of this kind will not be allowed and an exception will be raised.'))

CopyArgumentMetadata(Database.CreateTable, 'options', Database.CreateTableFromTemplate, 'options')
CopyResultMetadata(Database.CreateTable, 'table', Database.CreateTableFromTemplate, 'table')

# Public method: Database.ImportTable

AddMethodMetadata(Database.ImportTable,
    shortDescription=_('Creates a new table from an existing :class:`Table`, copying some or all of its fields and rows.'),
    longDescription=_(
"""Raises:
    :exc:`RuntimeError`: The table already exists, or some other problem
        occurred when creating it, adding fields, or copying rows.
"""),
    isExposedToPythonCallers=True,
    dependencies=[PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')])

CopyArgumentMetadata(Database.TableExists, 'self', Database.ImportTable, 'self')
CopyArgumentMetadata(Database.CreateTable, 'tableName', Database.ImportTable, 'destTableName')

AddArgumentMetadata(Database.ImportTable, 'sourceTable',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(':class:`~GeoEco.Datasets.Table` to copy.'))

AddArgumentMetadata(Database.ImportTable, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), canBeNone=True),
    description=_('Names of the fields in `sourceTable` to copy to the new table. If omitted, all the fields in `sourceTable` will be copied.'))

AddArgumentMetadata(Database.ImportTable, 'where',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""SQL WHERE clause expression that specifies the subset of rows to copy. If
not provided, all of the rows will be copied. If provided but the underlying
storage format does not support WHERE clauses, an exception will be raised.
The exact syntax of this expression depends on the underlying storage format.
If the underlying data store will be accessed through ArcGIS, `this article
<https://pro.arcgis.com/en/pro-app/latest/help/mapping/navigation/sql-reference-for-elements-used-in-query-expressions.htm>`_
may document some of the possible syntax, but not all of it may be supported
through ArcGIS's underlying Python API."""))

AddArgumentMetadata(Database.ImportTable, 'orderBy',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, mustMatchRegEx=r'\s*\S+(\s+([aA][sS][cC]|[dD][eE][sS][cC]))?\s*(,\s*\S+(\s+([aA][sS][cC]|[dD][eE][sS][cC]))?\s*)*'),
    description=_(
"""SQL ORDER BY clause that specifies the order in which the rows should be
copied. If not provided, the rows will copied according to the default
behavior of the underlying storage format and the programming library used to
access it.

The ORDER BY clause must be a comma-separated list of fields. Each field can
optionally be followed by a space and the word ``ASC`` to indicate ascending
order or ``DESC`` to indicate descending order. If neither is specified,
``ASC`` is assumed.

The underlying storage format and library perform the actual evaluation of
this parameter and determine the rules of sorting, such as whether string
comparisons are case-sensitive or case-insensitive. At present, there is no
mechanism to interrogate or manipulate these rules; you must live with the
default behavior of the underlying format and library.

"""))

AddArgumentMetadata(Database.ImportTable, 'rowCount',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    description=_(
"""Number of rows that will be copied, if it is known ahead of time. If the
number of rows is not known, omit this parameter.

This parameter is only used in progress reporting and is ignored if
`reportProgress` is False. If this parameter is provided, the progress reports
will include the number of rows remaining and an estimated time of completion.
If not provided, the progress reports will only include the number of rows
copied so far.

If you omit both this and the `where` parameter, and the underlying storage
format and programming library support retrieval of row counts, then the row
count will be obtained automatically when the copy is started.

"""))

AddArgumentMetadata(Database.ImportTable, 'reportProgress',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, progress messages will be logged periodically as the import proceeds.'))

AddArgumentMetadata(Database.ImportTable, 'rowDescriptionSingular',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
"""Word to use in progress and error messages for a single row. If omitted, an
appropriate generic word will be automatically selected based on the table's
geometry type, such as "point", "line", "polygon", and so on. If the table
does not have geometry, "row" will be used."""))

AddArgumentMetadata(Database.ImportTable, 'rowDescriptionPlural',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
"""Word to use in progress and error messages for plural rows. If omitted, an
appropriate generic word will be automatically selected based on table's
geometry type, such as "points", "lines", "polygons", and so on. If the
table does not have geometry, "rows" will be used."""))

AddArgumentMetadata(Database.ImportTable, 'copiedOIDFieldName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
"""Name of a field to create in the new table that will receive a copy of the
"object IDs" from `sourceTable` (e.g. the ``OBJECTID`` field of a geodatabase
or ``FID`` field of a shapefile). If not provided, the object IDs will not be
copied.

Note that, depending on the underlying storage format, the new table will
likely have its own object ID field that contains the IDs of the new rows.
Because the object IDs are automatically assigned by the underlying data
store, they are not guaranteed to be the same as those in `sourceTable`. The
purpose of `copiedOIDFieldName` is to allow you to retain a copy of object IDs
as they existed in `sourceTable`."""))

AddArgumentMetadata(Database.ImportTable, 'allowSafeCoercions',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, when the underlying storage format does not support the data type of a field of `sourceTable`, the most compact alternative data type will be chosen, so long as it can represent all possible values allowed by the source table\'s data type. If False, coercions of this kind will not be allowed and an exception will be raised.'))

CopyArgumentMetadata(Database.CreateTable, 'options', Database.ImportTable, 'options')
CopyResultMetadata(Database.CreateTable, 'table', Database.ImportTable, 'table')

# Public method: Database.DeleteTable

AddMethodMetadata(Database.DeleteTable,
    shortDescription=_('Deletes a table.'),
    longDescription=_(
"""Raises:
    :exc:`RuntimeError`: The table does not exist and `failIfNotExists` is
        True, or some other problem occurred when deleting the table.
"""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Database.TableExists, 'self', Database.DeleteTable, 'self')
CopyArgumentMetadata(Database.TableExists, 'tableName', Database.DeleteTable, 'tableName')

AddArgumentMetadata(Database.DeleteTable, 'failIfNotExists',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, :exc:`RuntimeError` will be raised if the table does not exist. If False, the default, this method will silently succeed if the table does not exist.'))


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
