# _CursorsMetadata.py - Metadata for classes defined in _Cursors.py.
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

from ._Table import Table
from ._Cursors import _Cursor, SelectCursor, UpdateCursor, InsertCursor


###############################################################################
# Metadata: _Cursor class
###############################################################################

# We do not want to export _Cursor from GeoEco.Datasets, but we do want to
# write some metadata on members inherited by derived classes that we do
# export. To accomplish this, we attach the metadata to the _Cursors module
# rather than the GeoEco.Datasets package (which is referenced by
# __package__).

AddModuleMetadata(
    module='GeoEco.Datasets._Cursors',
	shortDescription=_('Private module that implements the cursor classes.'))

AddClassMetadata(_Cursor,
    module='GeoEco.Datasets._Cursors',
    shortDescription=_('Base class for classes that provide methods for accessing :class:`Table`\\ s in a sequential manner, inspired by ArcGIS\'s Python API.'))

# Public properties

AddPropertyMetadata(_Cursor.Table,
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    shortDescription=_(':class:`~GeoEco.Datasets.Table` the cursor is accessing.'))

AddPropertyMetadata(_Cursor.RowDescriptionSingular,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_(
"""Word to use in progress and error messages for a single row. If not
supplied when the cursor was opened, an appropriate generic word will be
automatically selected based on the table's geometry type, such as "point",
"line", "polygon", and so on. If the table does not have geometry, "row" will
be used."""))

AddPropertyMetadata(_Cursor.RowDescriptionPlural,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_(
"""Word to use in progress and error messages for plural rows. If not supplied
when the cursor was opened, an appropriate generic word will be automatically
selected based on table's geometry type, such as "points", "lines",
"polygons", and so on. If the table does not have geometry, "rows" will be
used."""))

AddPropertyMetadata(_Cursor.IsOpen,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if the cursor is open, False if it is closed. '))

# Public method: _Cursor.Close

AddMethodMetadata(_Cursor.Close,
    shortDescription=_('Closes the cursor.'),
    longDescription=_(
"""After :func:`Close` is called, the cursor's methods for interacting with
the table will not work and will raise exceptions if called. However, there is
no harm in calling :func:`Close` again; if the cursor is already closed, then
:func:`Close` will silently succeed. Once the cursor is closed, there is no
way to reopen it; open a new cursor if you need to interact with the table
again."""),
    isExposedToPythonCallers=True)

AddArgumentMetadata(_Cursor.Close, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=_Cursor),
    description=_(':class:`%s` instance.') % _Cursor.__name__)

# Public method: _Cursor.SetRowCount

AddMethodMetadata(_Cursor.SetRowCount,
    shortDescription=_('Sets the number of rows that this cursor is expected to process.'),
    longDescription=_(
"""The row count is only used in progress reporting and is ignored if the
`reportProgress` parameter was False when the cursor was opened. If a row
count is provided, the progress reports will include the number of rows
remaining and an estimated time of completion. If a row count is not provided,
the progress reports will only include the number of rows processed so far.

Typically, if the row count is known ahead of time, you should provide it to
the method used to open the cursor. Use :func:`SetRowCount` when you want to
revise the row count after opening the cursor. Do not decrease the row count
to a value smaller than the number of rows processed so far."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(_Cursor.Close, 'self', _Cursor.SetRowCount, 'self')

AddArgumentMetadata(_Cursor.SetRowCount, 'rowCount',
    typeMetadata=IntegerTypeMetadata(minValue=0),
    description=_('New row count for this cursor.'))


###############################################################################
# Metadata: SelectCursor class
###############################################################################

AddClassMetadata(SelectCursor,
    module=__package__,
    shortDescription=_('Base class for forward-only cursors used to read rows from a :class:`Table`.'),
    longDescription=_(
"""This class is not meant to be instantiated directly. Instead call
:func:`Table.OpenSelectCursor()`. After obtaining a :class:`SelectCursor`
instance, call :func:`NextRow` to advance the cursor to the first row. If
:func:`NextRow` returns True, use :func:`GetValue` and :func:`GetGeometry` to
access fields of the row and its geometry. Call :func:`NextRow` again to
advance to the next row. When :func:`NextRow` returns False, no rows remain
and the cursor is closed. The cursor is also closed automatically if the 
:class:`SelectCursor` instance is deleted, and you can explicitly close it
with :func:`Close`.

The typical pattern for using :class:`SelectCursor` looks like this:

.. code-block:: python

    with table.OpenSelectCursor(...) as cursor:
        while cursor.NextRow():
            value = cursor.GetXXXXX(...)
            ...
"""))

# Public properties

AddPropertyMetadata(SelectCursor.AtEnd,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, no more rows are available (and :attr:`IsOpen` will also be False). If False, more rows may be available.'))

# Public method: SelectCursor.NextRow

AddMethodMetadata(SelectCursor.NextRow,
    shortDescription=_('Advances the cursor to the next row.'),
    isExposedToPythonCallers=True)

AddArgumentMetadata(SelectCursor.NextRow, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=SelectCursor),
    description=_(':class:`%s` instance.') % SelectCursor.__name__)

AddResultMetadata(SelectCursor.NextRow, 'rowAvailable',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""True if a row is available. False if no more rows are available.

After opening the cursor, you must call :func:`NextRow` prior to accessing the
first row, and call it again prior to accessing each subsequent row. Once
:func:`NextRow` returns False, no more rows are available, row-access
functions such as :func:`GetValue` will fail, the cursor is automatically
closed, and :attr:`IsOpen` will be False.

If :func:`NextRow` has not been called yet, or the last time it was called it
returned True, :attr:`AtEnd` will be False. Once :func:`NextRow` returns
False, :attr:`AtEnd` will be True."""))

# Public method: SelectCursor.GetValue

AddMethodMetadata(SelectCursor.GetValue,
    shortDescription=_('Retrieves the value of a field of the current row, given the name of the field.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(SelectCursor.NextRow, 'self', SelectCursor.GetValue, 'self')

AddArgumentMetadata(SelectCursor.GetValue, 'field',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the field to get the value of.

If you specified a list of fields to retrieve when you opened the cursor, you
will only be able to retrieve the values of those fields. If you did not
specify such a list, then you will be able to retrieve all of the fields of
the table.

This method cannot be used to get the geometry of the row, even if the
underlying data format stores the geometry in a named field. To get the
geometry, use :func:`GetGeometry`."""))

AddResultMetadata(SelectCursor.GetValue, 'value',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Value of the field for the current row.

If the value of the field is a database NULL, :py:data:`None` will be
returned. Otherwise the Python data type of the returned value will depend on
the data type of the field:

=================  =============================
Field Data Type    Returned Python Type
=================  =============================
binary             :py:class:`str`
date, datetime     :py:class:`datetime.datetime`
float32, float64   :py:class:`float`
int16, int32, oid  :py:class:`int`
string             :py:class:`str`
=================  =============================

For fields with the :py:class:`datetime.date` data type, the time of the returned
:py:class:`datetime.datetime` instance will be 00:00:00."""))

# Public method: SelectCursor.GetGeometry

AddMethodMetadata(SelectCursor.GetGeometry,
    shortDescription=_('Retrieves the geometry of the current row.'),
    longDescription=_(
"""This method will fail if the table does not have geometry. To determine if
it has geometry, check the :attr:`~Table.GeometryType` of the cursor's
:class:`~GeoEco.Datasets.Table`."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(SelectCursor.NextRow, 'self', SelectCursor.GetGeometry, 'self')

AddResultMetadata(SelectCursor.GetGeometry, 'geometry',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Instance of the OGR `Geometry
<https://gdal.org/api/python/vector_api.html#osgeo.ogr.Geometry>`_ class
representing the geometry of the current row. If the row has "null geometry",
:py:data:`None` will be returned."""))

# Public method: SelectCursor.GetOID

AddMethodMetadata(SelectCursor.GetOID,
    shortDescription=_('Retrieves the ArcGIS "object ID" of the current row.'),
    longDescription=_(
"""This method will fail if the table does not have an ArcGIS object ID. To
determine if it does, check the :attr:`~Table.HasOID` property of the cursor's
:class:`~GeoEco.Datasets.Table`."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(SelectCursor.NextRow, 'self', SelectCursor.GetOID, 'self')

AddResultMetadata(SelectCursor.GetOID, 'oid',
    typeMetadata=IntegerTypeMetadata(),
    description=_('Object ID of the current row.'))


###############################################################################
# Metadata: UpdateCursor class
###############################################################################

AddClassMetadata(UpdateCursor,
    module=__package__,
    shortDescription=_('Base class for forward-only cursors used to read, update, or delete rows in a :class:`Table`.'),
    longDescription=_(
"""Not all :class:`Table`\\ s support update cursors. To determine if a
:class:`Table` instance supports update cursors, call its
:func:`~Table.TestCapability` method with a `capability` of ``'UpdateCursor'``.
Some :class:`Table`\\ s that support update cursors only support updating rows,
not deleting them, or visa versa. To check this, test the ``'UpdateRow'`` and
``'DeleteRow'`` capabilities of the :class:`Table` instance.

This class is not meant to be instantiated directly. Instead call
:func:`Table.OpenUpdateCursor()`. After obtaining a :class:`UpdateCursor`
instance, call :func:`NextRow` to advance the cursor to the first row. If
:func:`NextRow` returns True, use the functions discussed below to read, update, 
or delete the row. Call :func:`NextRow` again to advance to the next row. When
:func:`NextRow` returns False, no rows remain and the cursor is closed. The
cursor is also closed automatically if the :class:`UpdateCursor` instance is
deleted, and you can explicitly close it with :func:`Close`.

To read values from the row, use :func:`GetValue`, :func:`GetGeometry`, and
:func:`GetOID`. To update values, use :func:`SetValue` and :func:`SetGeometry`
and then, after updating all fields of interest, call :func:`UpdateRow`. After
calling :func:`UpdateRow`, do not do anything else with the row, just call
:func:`NextRow` to go on to the next one. To delete a row, call
:func:`DeleteRow` and then :func:`NextRow`.

Certain storage formats may implement a transactional updating scheme in which
changes will not be committed to the underlying data store until the cursor
has been closed. For more information, please see the documentation for the
particular kind of :class:`Table` you are working with.

The typical pattern for using :class:`UpdateCursor` looks like this:

.. code-block:: python

    with table.OpenUpdateCursor(...) as cursor:
        while cursor.NextRow():
            value = cursor.GetXXXXX(...)
            ...
            if <need to update this row>:
                cursor.SetXXXXX(...)
                ...
                cursor.UpdateRow()
            elif <need to delete this row>:
                cursor.DeleteRow()
"""))

# Public method: UpdateCursor.SetValue

AddMethodMetadata(UpdateCursor.SetValue,
    shortDescription=_('Sets the value of a field of the current row, given the name of the field and its new value.'),
    longDescription=_(
"""Note:
    Changes to the row are not actually submitted through the underlying
    programming library to the underlying data store until :func:`UpdateRow`
    is called. If you call :func:`SetValue` but then neglect to call
    :func:`UpdateRow` before calling :func:`NextRow`, your changes will be
    lost.
"""),
    isExposedToPythonCallers=True)

AddArgumentMetadata(UpdateCursor.SetValue, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=UpdateCursor),
    description=_(':class:`%s` instance.') % UpdateCursor.__name__)

AddArgumentMetadata(UpdateCursor.SetValue, 'field',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the field to set the value of.

If you specified a list of fields to retrieve when you opened the cursor, you
will only be able to set the values of those fields. If you did not specify
such a list, then you will be able to set all of the fields of the
:class:`~GeoEco.Datasets.Table`.

This function cannot be used to set the geometry of the row, even if the
underlying data format stores the geometry in a named field. Use 
:func:`SetGeometry` instead.

This function cannot be used to set the ArcGIS "object ID" field. That field
is read-only and managed by the underlying data store or programming library
used to access it.

The underlying data store or programming library may expose other read-only
fields. For example, some versions of ArcGIS maintain fields called
``Shape_Length`` and ``Shape_Area`` in feature classes of ArcGIS geodatabases.
These may not be set either. To determine if a field may be set, call
:func:`~GeoEco.Datasets.Table.GetFieldByName` on the
:class:`~GeoEco.Datasets.Table` and examine the 
:attr:`~GeoEco.Datasets.Field.IsSettable` property of the returned
:class:`~GeoEco.Datasets.Field` instance."""))

AddArgumentMetadata(UpdateCursor.SetValue, 'value',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Value of the field.

To set the field to a database NULL, use :py:data:`None`. Otherwise, you must
provide an instance of the Python type that is appropriate for the data type
of the field:

=================  =============================
Field Data Type    Appropriate Python Type
=================  =============================
binary             :py:class:`str`
date, datetime     :py:class:`datetime.datetime`
float32, float64   :py:class:`float`
int16, int32       :py:class:`int`
string             :py:class:`str`
=================  =============================

To determine the data type of a field, call 
:func:`~GeoEco.Datasets.Table.GetFieldByName` on the
:class:`~GeoEco.Datasets.Table` and examine the 
:attr:`~GeoEco.Datasets.Field.DataType`
property of the returned :class:`~GeoEco.Datasets.Field` instance."""))

# Public method: UpdateCursor.SetGeometry

AddMethodMetadata(UpdateCursor.SetGeometry,
    shortDescription=_('Sets the geometry of the current row.'),
    longDescription=_(
"""This method will fail if the cursor's :class:`~GeoEco.Datasets.Table` does
not have geometry. To determine if it has geometry, check the
:attr:`~GeoEco.Datasets.Table.GeometryType` property of the 
:class:`~GeoEco.Datasets.Table` instance.

Note:
    Changes to the row are not actually submitted through the underlying
    programming library to the underlying data store until 
    :func:`~GeoEco.Datasets.UpdateCursor.UpdateRow` is called. If you call
    :func:`~GeoEco.Datasets.UpdateCursor.SetGeometry` but then neglect to call
    :func:`~GeoEco.Datasets.UpdateCursor.UpdateRow` before calling 
    :func:`~GeoEco.Datasets.UpdateCursor.NextRow`, your changes will be lost.
"""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(UpdateCursor.SetValue, 'self', UpdateCursor.SetGeometry, 'self')

AddArgumentMetadata(UpdateCursor.SetGeometry, 'geometry',
    typeMetadata=AnyObjectTypeMetadata(),
    description=_(
"""Instance of the OGR `Geometry
<https://gdal.org/api/python/vector_api.html#osgeo.ogr.Geometry>`_ class
representing the geometry of the row."""))

# Public method: UpdateCursor.UpdateRow

AddMethodMetadata(UpdateCursor.UpdateRow,
    shortDescription=_('Submits any changes made to the current row to the underlying data store.'),
    longDescription=_(
"""You cannot access a row after calling :func:`UpdateRow`; :func:`GetValue`,
:func:`SetValue`, and so on will not work. You cannot delete it. You must call
:func:`NextRow` to advance the cursor to the next row.

Certain storage formats may implement a transactional updating scheme in which
the change will not be committed to the underlying data store until the cursor
has been closed. For more information, please see the documentation for the
particular kind of :class:`~GeoEco.Datasets.Table` you are working with."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(UpdateCursor.SetValue, 'self', UpdateCursor.UpdateRow, 'self')

# Public method: UpdateCursor.DeleteRow

AddMethodMetadata(UpdateCursor.DeleteRow,
    shortDescription=_('Deletes the current row.'),
    longDescription=_(
"""You cannot access a row after calling :func:`DeleteRow`; :func:`GetValue`,
:func:`SetValue`, and so on will not work. You cannot update it. You must call
:func:`NextRow` to advance the cursor to the next row.

Certain storage formats may implement a transactional updating scheme in which
the delete will not be committed to the underlying data store until the cursor
has been closed. For more information, please see the documentation for the
particular kind of :class:`~GeoEco.Datasets.Table` you are working with."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(UpdateCursor.SetValue, 'self', UpdateCursor.DeleteRow, 'self')

# We also need to define metadata for GetValue, GetGeometry, and GetOID
# because, unfortunately, we implement a very short wrapper for each that
# essentially just performs a check and calls the base class (SelectCursor).
# It seems cumbersome that we have to write metadata, but because we overrode
# the base class's implementation, we do. So we just copy it from there.

AddMethodMetadata(UpdateCursor.GetValue, shortDescription=SelectCursor.GetValue.__doc__.Obj._ShortDescription, longDescription=SelectCursor.GetValue.__doc__.Obj._LongDescription)
CopyArgumentMetadata(UpdateCursor.SetValue, 'self', UpdateCursor.GetValue, 'self')
CopyArgumentMetadata(SelectCursor.GetValue, 'field', UpdateCursor.GetValue, 'field')
CopyResultMetadata(SelectCursor.GetValue, 'value', UpdateCursor.GetValue, 'value')

AddMethodMetadata(UpdateCursor.GetGeometry, shortDescription=SelectCursor.GetGeometry.__doc__.Obj._ShortDescription, longDescription=SelectCursor.GetGeometry.__doc__.Obj._LongDescription)
CopyArgumentMetadata(UpdateCursor.SetValue, 'self', UpdateCursor.GetGeometry, 'self')
CopyResultMetadata(SelectCursor.GetGeometry, 'geometry', UpdateCursor.GetGeometry, 'geometry')

AddMethodMetadata(UpdateCursor.GetOID, shortDescription=SelectCursor.GetOID.__doc__.Obj._ShortDescription, longDescription=SelectCursor.GetOID.__doc__.Obj._LongDescription)
CopyArgumentMetadata(UpdateCursor.SetValue, 'self', UpdateCursor.GetOID, 'self')
CopyResultMetadata(SelectCursor.GetOID, 'oid', UpdateCursor.GetOID, 'oid')


###############################################################################
# Metadata: InsertCursor class
###############################################################################

AddClassMetadata(InsertCursor,
    module=__package__,
    shortDescription=_('Base class for forward-only cursors used to insert rows into a :class:`Table`.'),
    longDescription=_(
"""Not all :class:`Table`\\ s support insert cursors. To determine if a
:class:`Table` instance supports insert cursors, call its
:func:`~Table.TestCapability` method with a `capability` of ``'InsertCursor'``.

This class is not meant to be instantiated directly. Instead call
:func:`Table.OpenInsertCursor()`. After obtaining an :class:`InsertCursor`
instance, call :func:`SetValue` and :func:`SetGeometry` to set the values of
the first row and then call :func:`InsertRow` to insert it. Repeat this
pattern until you are finished inserting rows. Then close the cursor either by
releasing all references to the :class:`InsertCursor` instance or by
explicitly calling its :func:`~InsertCursor.Close` method.

If you do not explicitly set values of all of a new row's fields by calling
:func:`SetValue` prior to calling :func:`InsertRow`, those fields will be set to
database NULL (if they are not read-only). If a field that has not been set is
not nullable, :func:`InsertRow` will report an error. To determine if a field is
nullable, call :func:`~Table.GetFieldByName` on the :class:`Table` and examine the
:attr:`~Field.IsNullable` property of the returned :class:`Field` instance.

Certain storage formats may implement a transactional updating scheme in which
changes will not be committed to the underlying data store until the cursor
has been closed. For more information, please see the documentation for the
particular kind of :class:`Table` you are working with.

The typical pattern for using :class:`InsertCursor` looks like this:

.. code-block:: python

    with table.OpenInsertCursor(...) as cursor:
        for ...:                    # Loop over new rows, inserting one at a time
            cursor.SetValue(...)
            ...
            cursor.InsertRow()
"""))

AddMethodMetadata(InsertCursor.SetValue,
    shortDescription=_('Sets the value of a field of the new row, given the name of the field and its value.'),
    longDescription=_(
"""Note:
    The new row is not actually submitted through the underlying programming
    library to the underlying data store until :func:`InsertRow` is called. If
    you call :func:`SetValue` but then neglect to call :func:`InsertRow`
    before closing the cursor, your row will not be inserted.
"""),
    isExposedToPythonCallers=True)

AddArgumentMetadata(InsertCursor.SetValue, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=InsertCursor),
    description=_(':class:`%s` instance.') % InsertCursor.__name__)

AddArgumentMetadata(InsertCursor.SetValue, 'field',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the field to set the value of.

This function cannot be used to set the geometry of the row, even if the
underlying data format stores the geometry in a named field. Use 
:func:`SetGeometry` instead.

This function cannot be used to set the ArcGIS "object ID" field. That field
is read-only and managed by the underlying data store or programming library
used to access it.

The underlying data store or programming library may expose other read-only
fields. For example, some versions of ArcGIS maintain fields called
``Shape_Length`` and ``Shape_Area`` in feature classes of ArcGIS geodatabases.
These may not be set either. To determine if a field may be set, call
:func:`~GeoEco.Datasets.Table.GetFieldByName` on the 
:class:`~GeoEco.Datasets.Table` and examine the
:attr:`~GeoEco.Datasets.Field.IsSettable` property of the returned 
:class:`~GeoEco.Datasets.Field` instance."""))

CopyArgumentMetadata(UpdateCursor.SetValue, 'value', InsertCursor.SetValue, 'value')

# Public method: InsertCursor.SetGeometry

AddMethodMetadata(InsertCursor.SetGeometry,
    shortDescription=_('Sets the geometry of the new row.'),
    longDescription=_(
"""This method will fail if the cursor's :class:`~GeoEco.Datasets.Table` does
not have geometry. To determine if it has geometry, check the
:attr:`~GeoEco.Datasets.Table.GeometryType` property of the
:class:`~GeoEco.Datasets.Table` instance.

Note:
    The new row is not actually submitted through the underlying programming
    library to the underlying data store until 
    :func:`~GeoEco.Datasets.InsertCursor.InsertRow` is called. If you call 
    :func:`~GeoEco.Datasets.InsertCursor.SetGeometry` but then neglect to call
    :func:`~GeoEco.Datasets.InsertCursor.InsertRow` before closing the cursor,
    your row will not be inserted.
"""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(InsertCursor.SetValue, 'self', InsertCursor.SetGeometry, 'self')
CopyArgumentMetadata(UpdateCursor.SetGeometry, 'geometry', InsertCursor.SetGeometry, 'geometry')

# Public method: InsertCursor.InsertRow

AddMethodMetadata(InsertCursor.InsertRow,
    shortDescription=_('Submits the new row to the underlying data store.'),
    longDescription=_(
"""If you do not explicitly set values of all of the new row's fields by calling
:func:`~GeoEco.Datasets.InsertCursor.SetValue` prior to calling 
:func:`~GeoEco.Datasets.InsertCursor.InsertRow`, those fields will be set to
database NULL (if they are not read-only). If a field that has not been set is
not nullable, :func:`~GeoEco.Datasets.InsertCursor.InsertRow` will report an
error. To determine if a field is nullable, call 
:func:`~GeoEco.Datasets.Table.GetFieldByName` on the 
:class:`~GeoEco.Datasets.Table` and examine the
:attr:`~GeoEco.Datasets.Field.IsNullable` property of the returned 
:class:`~GeoEco.Datasets.Field` instance.

Certain storage formats may implement a transactional updating scheme in which
changes will not be committed to the underlying data store until the cursor
has been closed. For more information, please see the documentation for the
particular kind of :class:`~GeoEco.Datasets.Table` you are working with."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(InsertCursor.SetValue, 'self', InsertCursor.InsertRow, 'self')


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
