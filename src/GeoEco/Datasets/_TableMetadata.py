# _TableMetadata.py - Metadata for classes defined in _Table.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from ._Table import Table, Field
from ._Cursors import SelectCursor, UpdateCursor, InsertCursor


###############################################################################
# Metadata: Table class
###############################################################################

AddClassMetadata(Table,
    module=__package__,
    shortDescription=_('Base class for classes representing tabular :class:`Dataset`\\ s, such as ArcGIS feature classes and database tables.'),
    longDescription=_(
""":class:`Table` is a base class that should not be instantiated directly;
instead, users should instantiate one of the many derived classes representing
the type of tabular dataset they're interested in."""))

# Public properties

AddPropertyMetadata(Table.HasOID,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if this table has an ArcGIS-style "object ID" field.'),
    longDescription=_(
"""ArcGIS usually requires tabular datasets to have an auto-incrementing
integer field that uniquely identifies each row. This method returns True if
such a field has been defined and the underlying programming library used to
access the table identifies the field the object ID field."""))

AddPropertyMetadata(Table.OIDFieldName,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    shortDescription=_('Name of the ArcGIS-style "object ID" field, or :py:data:`None` if there is no object ID field.'),
    longDescription=_(
"""The object ID field name usually depends on the underlying storage format.
For example, it may be named ``OID`` or ``FID`` in .DBF files or shapefiles,
or ``OBJECTID`` or ``ESRI_OID`` in geodatabase feature classes and tables. If
the underlying format or programming library used to access it does not define
or identify an object ID field, this property will be :py:data:`None`."""))

AddPropertyMetadata(Table.GeometryType,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection', 'Point25D', 'LineString25D', 'Polygon25D', 'MultiPoint25D', 'MultiLineString25D', 'MultiPolygon25D', 'GeometryCollection25D']),
    shortDescription=_('Geometry type for the table, or :py:data:`None` if the table does not have geometry.'))

AddPropertyMetadata(Table.GeometryFieldName,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    shortDescription=_('Name of the geometry field, or :py:data:`None` if the table does not have geometry, or the geometry is not stored in a named field (as with shapefiles).'))

AddPropertyMetadata(Table.MaxStringLength,
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=1),
    shortDescription=_('Maximum allowed length of string fields, or :py:data:`None` if there is no maximum or it is unknown.'))

AddPropertyMetadata(Table.Fields,
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=Field), canBeNone=True),
    shortDescription=_(':py:class:`list` of :class:`~GeoEco.Datasets.Field`\\ s representing the fields of the table. :py:data:`None` or an empty list if the table has no fields (this is unusual).'))

# Public method: Table.GetFieldByName

AddMethodMetadata(Table.GetFieldByName,
    shortDescription=_('Returns the :class:`~GeoEco.Datasets.Field` for the specified field name, or :py:data:`None` if no field exists with that name.'),
    isExposedToPythonCallers=True)

AddArgumentMetadata(Table.GetFieldByName, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(':class:`%s` instance.') % Table.__name__)

AddArgumentMetadata(Table.GetFieldByName, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_('Name of the field.'))

AddResultMetadata(Table.GetFieldByName, 'field',
    typeMetadata=ClassInstanceTypeMetadata(cls=Field, canBeNone=True),
    description=_(':class:`~GeoEco.Datasets.Field` for `name`, or :py:data:`None` if no field exists with that name.'))

# Public method: Table.AddField

AddMethodMetadata(Table.AddField,
    shortDescription=_('Adds a field to the table.'),
    longDescription=_(
"""If the field cannot be added, an appropriate exception will be raised. This
can happen for a variety of reasons, which may include:

* The underlying storage format or programming library used to access it does
  not support the addition of fields.

* The table is not empty, and the format or library only allows fields to be
  added when it is empty.

* The format or library does not support the requested parameters. For
  example, it may not support the requested data type.

* The table is read-only, or the caller does not have sufficient privileges to
  add fields.
"""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.GetFieldByName, 'self', Table.AddField, 'self')

AddArgumentMetadata(Table.AddField, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the field to add.

The name must conform to all rules imposed by the underlying storage format
and programming library used to access it. The caller is expected to be aware
of these rules and this method attempts to fail if any rule is violated.
Certain libraries are designed to automatically modify the caller's illegal
name to a legal name. Where possible, this function overrides that behavior
and tries to fail anyway.

This function treats names as case-insensitive, even if the underlying format
and library support case-sensitive names. This behavior should be of little
consequence to most callers; this function will pass the name to the library
without changing the case. The only callers that will be affected are those
who require the ability to create multiple fields with the same name but
different case. That scenario is not supported, regardless of whether the
format and library may support it.

"""))

AddArgumentMetadata(Table.AddField, 'dataType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['binary', 'date', 'datetime', 'float32', 'float64', 'int16', 'int32', 'string'], makeLowercase=True),
    description=_(
"""Data type of the field to add.

The underlying storage format and programming library may only support a
subset of the possible data types. To test whether a data type is supported,
pass the string ``'t DataType'`` to :func:`~CollectibleObject.TestCapability`,
replacing ``t`` with the data type you want to test.

If `allowSafeCoercions` is True (the default) and the format or library does
not support the requested data type but does support an alternative data type
that can fully represent the values of the requested data type, the field will
be created with that alternative data type. See the `allowSafeCoercions`
parameter for more information.

"""))

AddArgumentMetadata(Table.AddField, 'length',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_(
"""Length of the field to add.

The caller is expected to be aware of the appropriate values for this
parameter, based on the underlying storage format and programming library used
to access it. If this parameter is provided, it will be passed without any
validation to the library. Typically, this parameter should only be provided
when creating fields that have the ``'string'`` or ``'binary'`` data type.

Most formats and libraries impose upper limits on the length of string fields.
For some of these, :attr:`MaxStringLength` will return the upper limit."""))

AddArgumentMetadata(Table.AddField, 'precision',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_(
"""Precision of the field to add.

The caller is expected to be aware of the appropriate values for this
parameter, based on the underlying storage format and programming library used
to access it. If this parameter is provided, it will be passed without any
validation to the library. Typically, this parameter should only be provided
when creating fields that have the ``'float32'`` or ``'float64'`` data
type."""))

AddArgumentMetadata(Table.AddField, 'isNullable',
    typeMetadata=BooleanTypeMetadata(canBeNone=True),
    description=_(
"""Indicates whether or not the added field should be nullable.

The default value of this parameter, :py:data:`None`, indicates that the
nullability should be decided by the default behavior of the underlying
storage format and programming library used to access it. The value True
indicates that the library should be instructed to create a nullable field;
False indicates that it should be instructed to create a non-nullable field.

If True or False is provided and the underlying format or library does not
support nullable fields, this function attempts recognize the condition and
raise an exception. Some libraries will allow nullable fields to be created
even though the underlying format does not truly support them. For example, at
the time of this writing, OGR did not recognize the concept of nullability and
essentially treated all fields as nullable. In situations like this, we try
not to rely on the underlying library to decide whether nullability is
supported but detect it independently."""))

AddArgumentMetadata(Table.AddField, 'allowSafeCoercions',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True and the underlying storage format or programming library does not
support the requested data type but does support an alternative data type that
can fully represent the values of the requested data type, the field will be
added with the alternative data type. If False and the requested data type is
not supported, an exception will be raised.

If True is provided, this function will try the following alternative data
types in the order listed and use the first one that is supported:

===================  =======================
Requested Data Type  Alternate Data Types
===================  =======================
date                 datetime
int16                int32, float32, float64
int32                float64
float32              float64
===================  =======================
"""))

AddArgumentMetadata(Table.AddField, 'failIfExists',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True and a field already exists with the name requested by the caller,
an exception will raised. If False and a field already exists with the name
requested by the caller, an exception will not be raised as long as that the
field has the exact characteristics requested by the caller (data type,
length, and so on).

As noted above, this function treats field names as case-insensitive, even if
the underlying storage format or programming library treat them as
case-sensitive."""))

# Public method: Table.DeleteField

AddMethodMetadata(Table.DeleteField,
    shortDescription=_('Deletes a field from the table.'),
    longDescription=_(
"""If the field cannot be deleted, an appropriate exception will be raised.
This can happen for a variety of reasons, which may include:

* The field does not exist.

* The underlying storage format or programming library used to access it does
  not support the deletion of fields.

* The table is not empty, and the format or library only allow fields to be
  deleted when it is empty.

* The table is read-only, or the caller does not have sufficient privileges to
  delete fields.
"""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.GetFieldByName, 'self', Table.DeleteField, 'self')

AddArgumentMetadata(Table.DeleteField, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_(
"""Name of the field to delete.

The name must conform to all rules imposed by the underlying storage format
and programming library used to access it. The caller is expected to be aware
of these rules and this function attempts to fail if any rule is violated.
Certain libraries are designed to automatically modify the caller's illegal
name to a legal name. Where possible, this function overrides that behavior
and tries to fail anyway.

This function treats names as case-insensitive, even if the underlying format
and library support case-sensitive names. This behavior should be of little
consequence to most callers. The only callers that will be affected are those
who require the ability to have multiple fields with the same name but
different case. That scenario is not supported, regardless of whether the
format and library may support it, and the behavior of this function in that
scenario is undefined.

"""))

AddArgumentMetadata(Table.DeleteField, 'failIfDoesNotExist',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True and the field does not exist with the name requested by the caller,
an exception will raised. If False and the field does not exist, this function
will silently succeed."""))

# Public method: Table.CreateIndex

AddMethodMetadata(Table.CreateIndex,
    shortDescription=_('Creates an index on one or more fields of the table.'),
    longDescription=_(
"""This function does not support creation of spatial indexes. It only
supports creation of indexes on non-spatial fields.

If the index cannot be created, an appropriate exception will be raised.
This can happen for a variety of reasons, which may include:

* The underlying storage format or programming library used to access it does
  not support indexes.

* The caller requested that an index be created on more than one field (a
  "composite index") but the format or library only supports single-field
  indexes.

* The table is read-only, or the caller does not have sufficient privileges to
  create indexes.
"""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.GetFieldByName, 'self', Table.CreateIndex, 'self')

AddArgumentMetadata(Table.CreateIndex, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1),
    description=_('List of fields to form the index.'))

AddArgumentMetadata(Table.CreateIndex, 'indexName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Name of the index to create.

Many storage formats require indexes to be named. However, if :py:data:`None`
is provided, this function will attempt to create the index without a name,
which is suitable for certain formats that only support a single index, or
those that allow multiple single-field indexes.

The name must conform to all rules imposed by the underlying storage format and
programming library used to access it. The caller is expected to be aware of
these rules and this function attempts to fail if any rule is violated.
Certain libraries are designed to automatically modify the caller's illegal
name to a legal name. Where possible, this function overrides that behavior
and tries to fail anyway.

"""))

AddArgumentMetadata(Table.CreateIndex, 'unique',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, a unique index will be created. This requires each row to have a
unique combination of values for the fields in the index. If the existing rows
in the table do not satisfy this constraint, an exception will probably be
raised, but it is up to the underlying storage format or programming library
to raise it (this function itself does not enforce this constraint). If False,
rows will be permitted to have duplicate combinations of values."""))

AddArgumentMetadata(Table.CreateIndex, 'ascending',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the index will be in ascending order. If False, it will be in
descending order. Not all underlying storage formats and programming libraries
my support this capability."""))

# Public method: Table.DeleteIndex

AddMethodMetadata(Table.DeleteIndex,
    shortDescription=_('Deletes an index from the table.'),
    longDescription=_(
"""If the index cannot be deleted, an appropriate exception will be raised.
This can happen for a variety of reasons, which may include:

* The index does not exist.

* The underlying storage format or programming library used to access it does
  not support the deletion of indexes.

* The table is read-only, or the caller does not have sufficient privileges to
  delete indexes.
"""),
   isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.GetFieldByName, 'self', Table.DeleteIndex, 'self')

AddArgumentMetadata(Table.DeleteIndex, 'indexName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Name of the index to delete.

Many storage formats require indexes to be named. However, if :py:data:`None`
is provided, this function will attempt to delete the index without a name,
which is suitable for certain formats that only support a single index.

The name must conform to all rules imposed by the underlying storage format and
programming library used to access it. The caller is expected to be aware of
these rules and this function attempts to fail if any rule is violated.
Certain libraries are designed to automatically modify the caller's illegal
name to a legal name. Where possible, this function overrides that behavior
and tries to fail anyway.

"""))

# Public method: Table.GetRowCount

AddMethodMetadata(Table.GetRowCount,
    shortDescription=_('Returns the number of rows in the table.'),
    longDescription=_(
"""For certain storage formats, calling this function might require the
underlying programming library used to access the data to read the entire
table, a potentially lengthy operation. If this behavior is undesirable, the
caller is expected to know that it will occur and not call this function."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.GetFieldByName, 'self', Table.GetRowCount, 'self')

AddResultMetadata(Table.GetRowCount, 'count',
    typeMetadata=IntegerTypeMetadata(minValue=0),
    description=_('Number of rows in the table.'))

# Public method: Table.Query

AddMethodMetadata(Table.Query,
    shortDescription=_('Queries the table and returns a :py:class:`dict` mapping field names to parallel lists of result values.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.GetFieldByName, 'self', Table.Query, 'self')

AddArgumentMetadata(Table.Query, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    description=_(
"""List of fields to include in the results. If :py:data:`None`, the default,
all fields will be included. Do not provide ``*``, as would be done in a SQL
SELECT statement that wanted to retrieve all fields.

This usual reason to not retrieve all of the fields is to minimize database
and network load. If you do not have these concerns, there is no reason to
provide a value for this parameter.

"""))

AddArgumentMetadata(Table.Query, 'where',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""SQL WHERE clause expression that specifies the rows to include. If not
provided, all of the rows will be included. If provided but the underlying
storage format does not support WHERE clauses, an exception will be raised.

The exact syntax of this expression depends on the underlying storage format.
If the underlying data store will be accessed through ArcGIS, `this article
<https://pro.arcgis.com/en/pro-app/latest/help/mapping/navigation/sql-reference-for-elements-used-in-query-expressions.htm>`_
may document some of the possible syntax, but not all of it may be supported
through ArcGIS's underlying Python API.

"""))

AddArgumentMetadata(Table.Query, 'orderBy',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, mustMatchRegEx=r'\s*\S+(\s+([aA][sS][cC]|[dD][eE][sS][cC]))?\s*(,\s*\S+(\s+([aA][sS][cC]|[dD][eE][sS][cC]))?\s*)*'),
    description=_(
"""SQL ORDER BY clause that specifies the order in which the rows should be
accessed. If not provided, the rows will accessed according to the default
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

AddArgumentMetadata(Table.Query, 'rowCount',
   typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
   description=_(
"""Number of rows that will be accessed, if it is known ahead of time. If the
number of rows is not known, omit this parameter.

This parameter is only used in progress reporting and is ignored if
`reportProgress` is False. If this parameter is provided, the progress reports
will include the number of rows remaining and an estimated time of completion.
If not provided, the progress reports will only include the number of rows
accessed so far.

"""))

AddArgumentMetadata(Table.Query, 'reportProgress',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, progress messages will be logged periodically as the query proceeds.'))

AddArgumentMetadata(Table.Query, 'rowDescriptionSingular',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
"""Word to use in progress and error messages for a single row. If omitted, an
appropriate generic word will be automatically selected based on the table's
geometry type, such as "point", "line", "polygon", and so on. If the table
does not have geometry, "row" will be used."""))

AddArgumentMetadata(Table.Query, 'rowDescriptionPlural',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
"""Word to use in progress and error messages for plural rows. If omitted, an
appropriate generic word will be automatically selected based on table's
geometry type, such as "points", "lines", "polygons", and so on. If the
table does not have geometry, "rows" will be used."""))

AddResultMetadata(Table.Query, 'results',
    typeMetadata=DictionaryTypeMetadata(keyType=UnicodeStringTypeMetadata(minLength=1),
    valueType=ListTypeMetadata(elementType=AnyObjectTypeMetadata())),
    description=_(
""":py:class:`dict` where each key is a field name and each value is a
:py:class:`list` of values. All lists are the same length. The values for the
first row occur at index 0 of each list, the second occur at index 1, and so
on. ``NULL`` values are represented by :py:data:`None`."""))

# Public method: Table.OpenSelectCursor

AddMethodMetadata(Table.OpenSelectCursor,
    shortDescription=_('Opens and returns a :class:`~GeoEco.Datasets.SelectCursor` for reading rows from the table.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.GetFieldByName, 'self', Table.OpenSelectCursor, 'self')

AddArgumentMetadata(Table.OpenSelectCursor, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    description=_(
"""List of fields to retrieve. If :py:data:`None`, the default, all fields
will be retrieved. Do not provide ``'*'``, as would be done in a SQL SELECT
statement that wanted to retrieve all fields.

This usual reason to not retrieve all of the fields is to minimize database
and network load. If you do not have these concerns, there is no reason to
provide a value for this parameter.

If you do provide a list of fields and the table has a geometry field and you
want it to be able to access it (e.g. with :func:`GetGeometry`), be sure you
include the geometry field in your list. The :attr:`GeometryFieldName`
property gives the name of the geometry field.

"""))

CopyArgumentMetadata(Table.Query, 'where', Table.OpenSelectCursor, 'where')
CopyArgumentMetadata(Table.Query, 'orderBy', Table.OpenSelectCursor, 'orderBy')
CopyArgumentMetadata(Table.Query, 'rowCount', Table.OpenSelectCursor, 'rowCount')
CopyArgumentMetadata(Table.Query, 'reportProgress', Table.OpenSelectCursor, 'reportProgress')
CopyArgumentMetadata(Table.Query, 'rowDescriptionSingular', Table.OpenSelectCursor, 'rowDescriptionSingular')
CopyArgumentMetadata(Table.Query, 'rowDescriptionPlural', Table.OpenSelectCursor, 'rowDescriptionPlural')

AddResultMetadata(Table.OpenSelectCursor, 'cursor',
    typeMetadata=ClassInstanceTypeMetadata(cls=SelectCursor),
    description=_('Opened :class:`~GeoEco.Datasets.SelectCursor` positioned on the first row (if any rows were returned).'))

# Public method: Table.OpenUpdateCursor

AddMethodMetadata(Table.OpenUpdateCursor,
    shortDescription=_('Opens and returns an :class:`~GeoEco.Datasets.UpdateCursor` for reading, updating, and deleting rows from the table.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.OpenSelectCursor, 'self', Table.OpenUpdateCursor, 'self')
CopyArgumentMetadata(Table.OpenSelectCursor, 'fields', Table.OpenUpdateCursor, 'fields')
CopyArgumentMetadata(Table.OpenSelectCursor, 'where', Table.OpenUpdateCursor, 'where')
CopyArgumentMetadata(Table.OpenSelectCursor, 'orderBy', Table.OpenUpdateCursor, 'orderBy')
CopyArgumentMetadata(Table.OpenSelectCursor, 'rowCount', Table.OpenUpdateCursor, 'rowCount')
CopyArgumentMetadata(Table.OpenSelectCursor, 'reportProgress', Table.OpenUpdateCursor, 'reportProgress')
CopyArgumentMetadata(Table.OpenSelectCursor, 'rowDescriptionSingular', Table.OpenUpdateCursor, 'rowDescriptionSingular')
CopyArgumentMetadata(Table.OpenSelectCursor, 'rowDescriptionPlural', Table.OpenUpdateCursor, 'rowDescriptionPlural')

AddResultMetadata(Table.OpenUpdateCursor, 'cursor',
   typeMetadata=ClassInstanceTypeMetadata(cls=UpdateCursor),
    description=_('Opened :class:`~GeoEco.Datasets.UpdateCursor` positioned on the first row (if any rows were returned).'))

# Public method: Table.OpenInsertCursor

AddMethodMetadata(Table.OpenInsertCursor,
    shortDescription=_('Opens and returns an :class:`~GeoEco.Datasets.InsertCursor` for adding rows to the table.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Table.OpenSelectCursor, 'self', Table.OpenInsertCursor, 'self')

AddArgumentMetadata(Table.OpenInsertCursor, 'rowCount',
   typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
   description=_(
"""Number of rows that will be inserted, if it is known ahead of time. If the
number of rows is not known, omit this parameter.

This parameter is only used in progress reporting and is ignored if
`reportProgress` is False. If this parameter is provided, the progress reports
will include the number of rows remaining and an estimated time of completion.
If not provided, the progress reports will only include the number of rows
accessed so far.

"""))

CopyArgumentMetadata(Table.OpenSelectCursor, 'reportProgress', Table.OpenInsertCursor, 'reportProgress')
CopyArgumentMetadata(Table.OpenSelectCursor, 'rowDescriptionSingular', Table.OpenInsertCursor, 'rowDescriptionSingular')
CopyArgumentMetadata(Table.OpenSelectCursor, 'rowDescriptionPlural', Table.OpenInsertCursor, 'rowDescriptionPlural')

AddResultMetadata(Table.OpenInsertCursor, 'cursor',
   typeMetadata=ClassInstanceTypeMetadata(cls=InsertCursor),
    description=_('Opened :class:`~GeoEco.Datasets.InsertCursor` positioned on the first row (if any rows were returned).'))


###############################################################################
# Metadata: Field class
###############################################################################

AddClassMetadata(Field,
    module=__package__,
    shortDescription=_('Describes a field in a :class:`Table`.'))

# Public properties

AddPropertyMetadata(Field.Name,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Name of the field.'))

AddPropertyMetadata(Field.DataType,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_("Data type of the field. Usually one of ``'binary'``, ``'date'``, ``'datetime'``, ``'float32'``, ``'float64'``, '``int16'``, ``'int32'``, or ``'string'``."))

AddPropertyMetadata(Field.Length,
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    shortDescription=_('Maximum length of the field, if known. :py:data:`None` if unknown or not applicable to the :attr:`DataType`.'))

AddPropertyMetadata(Field.Precision,
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    shortDescription=_('Precision of the field, if known. :py:data:`None` if unknown or not applicable to the :attr:`DataType`.'))

AddPropertyMetadata(Field.IsNullable,
    typeMetadata=BooleanTypeMetadata(canBeNone=True),
    shortDescription=_('True if values of the field can be ``NULL``, False if they cannot, and :py:data:`None` if it is unknown whether they can be ``NULL``.'))

AddPropertyMetadata(Field.IsSettable,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if values of the field can be set, False if they cannot, e.g. because they are automatically assigned by the underlying storage system, as with ArcGIS "object IDs".'))

# Public constructor: Field.__init__

AddMethodMetadata(Field.__init__,
    shortDescription=_('Field constructor.'))

AddArgumentMetadata(Field.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Field),
    description=_(':class:`%s` instance.') % Field.__name__)

AddArgumentMetadata(Field.__init__, 'name',
    typeMetadata=Field.Name.__doc__.Obj.Type,
    description=Field.Name.__doc__.Obj.ShortDescription)

AddArgumentMetadata(Field.__init__, 'dataType',
    typeMetadata=Field.DataType.__doc__.Obj.Type,
    description=Field.DataType.__doc__.Obj.ShortDescription)

AddArgumentMetadata(Field.__init__, 'length',
    typeMetadata=Field.Length.__doc__.Obj.Type,
    description=Field.Length.__doc__.Obj.ShortDescription)

AddArgumentMetadata(Field.__init__, 'precision',
    typeMetadata=Field.Precision.__doc__.Obj.Type,
    description=Field.Precision.__doc__.Obj.ShortDescription)

AddArgumentMetadata(Field.__init__, 'isNullable',
    typeMetadata=Field.IsNullable.__doc__.Obj.Type,
    description=Field.IsNullable.__doc__.Obj.ShortDescription)

AddArgumentMetadata(Field.__init__, 'isSettable',
    typeMetadata=Field.IsSettable.__doc__.Obj.Type,
    description=Field.IsSettable.__doc__.Obj.ShortDescription)

AddResultMetadata(Field.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=Field),
    description=_(':class:`%s` instance.') % Field.__name__)


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
