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
    shortDescription=_(':class:`Table` the cursor is accessing.'))

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

    with dataset.OpenSelectCursor(...) as cursor:
        while cursor.NextRow():
            value = cursor.GetValue(...)
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
the dataset.

This method cannot be used to get the geometry of the row, even if the
underlying data format stores the geometry in a named field. To get the
geometry, use :func:`GetGeometry`."""))

AddResultMetadata(SelectCursor.GetValue, 'value',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Value of the field.

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
:class:`Table`."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(SelectCursor.NextRow, 'self', SelectCursor.GetGeometry, 'self')

AddResultMetadata(SelectCursor.GetGeometry, 'geometry',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Instance of the OGR `Geometry
<https://gdal.org/api/python/vector_api.html#osgeo.ogr.Geometry>`_ class
representing the geometry of the row. If the row has "null geometry",
:py:data:`None` will be returned."""))


###############################################################################
# This module is not meant to be imported directly. Import Datasets.py instead.
###############################################################################

__all__ = []
