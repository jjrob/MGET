# _Cursors.py - Defines base classes for table cursors.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import atexit
import datetime
import sys
import weakref

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import ProgressReporter

from ._Dataset import Dataset


class _Cursor(object):
    __doc__ = DynamicDocString()
    
    # Public properties and instance methods

    def _GetTable(self):
        return self._Table

    Table = property(_GetTable, doc=DynamicDocString())

    def _GetRowDescriptionSingular(self):
        return self._RowDescriptionSingular

    RowDescriptionSingular = property(_GetRowDescriptionSingular, doc=DynamicDocString())

    def _GetRowDescriptionPlural(self):
        return self._RowDescriptionPlural

    RowDescriptionPlural = property(_GetRowDescriptionPlural, doc=DynamicDocString())

    def _GetIsOpen(self):
        return self._IsOpen

    IsOpen = property(_GetIsOpen, doc=DynamicDocString())

    def Close(self):
        if hasattr(self, '_IsOpen') and self._IsOpen:
            if hasattr(self, '_ProgressReporter') and self._ProgressReporter is not None and self._ProgressReporter.HasStarted and not self._ProgressReporter.HasCompleted:
                self._ProgressReporter.Stop()
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Closing cursor on %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._Table.DisplayName})
            try:
                self._Close()
            except:
                pass

            self._IsOpen = False

            for i, r in enumerate(_Cursor._CursorsToCloseAtExit):
                if r() == self:
                    del _Cursor._CursorsToCloseAtExit[i]
                    break

        self._Table = None

    def SetRowCount(self, rowCount):
        self.__doc__.Obj.ValidateMethodInvocation()

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        if hasattr(self, '_ProgressReporter') and self._ProgressReporter is not None and not self._ProgressReporter.HasCompleted:
            self._ProgressReporter.TotalOperations = rowCount

    # The rest of the methods of this class are private and are not
    # intended to be invoked by external callers.

    def __init__(self, table, rowDescriptionSingular, rowDescriptionPlural):
        # Do not call self.__doc__.Obj.ValidateMethodInvocation() here. The
        # various Table.OpenXXXXXCursor() functions handle validation for us.

        self._Table = table
        self._IsOpen = False

        if rowDescriptionSingular is None and rowDescriptionPlural is None:
            if self._Table.GeometryType in ['Point', 'Point25D']:
                self._RowDescriptionSingular = _('point')
                self._RowDescriptionPlural = _('points')
            elif self._Table.GeometryType in ['LineString', 'LineString25D', 'MultiLineString', 'MultiLineString25D']:
                self._RowDescriptionSingular = _('line')
                self._RowDescriptionPlural = _('lines')
            elif self._Table.GeometryType in ['Polygon', 'Polygon25D', 'MultiPolygon', 'MultiPolygon25D']:
                self._RowDescriptionSingular = _('polygon')
                self._RowDescriptionPlural = _('polygons')
            elif self._Table.GeometryType in ['MultiPoint', 'MultiPoint25D']:
                self._RowDescriptionSingular = _('multipoint')
                self._RowDescriptionPlural = _('multipoints')
            elif self._Table.GeometryType in ['GeometryCollection', 'GeometryCollection25D']:
                self._RowDescriptionSingular = _('geometry collection')
                self._RowDescriptionPlural = _('geometry collections')
            else:
                self._RowDescriptionSingular = _('row')
                self._RowDescriptionPlural = _('rows')
        else:
            self._RowDescriptionSingular = rowDescriptionSingular
            self._RowDescriptionPlural = rowDescriptionPlural

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Close()
        return False  # Ensure any exceptions are propagated

    def __del__(self):
        self.Close()

    def _Close(self):
        pass    # Base class implementation does nothing

    def _SetValue_Base(self, field, value, requestedFields=None):

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        # Validate that field exists and that it is not the OID or
        # geometry field.

        if not isinstance(field, str):
            raise TypeError(_('The field parameter must be a string.'))

        f = self._Table.GetFieldByName(field)
        if f is None:
            raise RuntimeError(_('Cannot set the value of the "%(field)s" field of this %(singular)s of %(dn)s to %(value)s because the field does not exist.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': field, 'value': repr(value)})

        if requestedFields is not None and f.Name not in requestedFields:
            raise RuntimeError(_('Cannot retrieve the value of the %(field)s field of this %(singular)s of %(dn)s. The field exists but was not included in the list of requested fields when the cursor was opened.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name})

        if f.Name == self._Table.OIDFieldName:
            raise RuntimeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because that field is the object ID (OID) or feature ID (FID) field, which is read-only.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value)})

        if f.Name == self._Table.GeometryFieldName:
            raise RuntimeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because that field is the geometry field. To set the geometry field, call SetGeometry() rather than SetValue().') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value)})

        # Validate that the field is settable. Non-settable fields are
        # those managed by the underlying data format or programming
        # library. These include the OID field (which is handled
        # above) as well as the ArcGIS SHAPE_Length and SHAPE_Area
        # fields, which are set by ArcGIS.

        if not f.IsSettable:
            raise RuntimeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because that field is read-only; its values are managed by the underlying data format.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value)})

        # If the caller is trying to set the field to null, validate
        # that the field is nullable.

        if value is None:
            if not f.IsNullable:
                raise RuntimeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to None because that field is not nullable. You must provide a value for that field.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name})

        # Otherwise, validate that the value's data type matches that
        # of the field, that it is within an acceptable range, etc.

        else:
            if f.DataType == 'int16' or f.DataType == 'int32':
                if not isinstance(value, int):
                    raise TypeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because the data type of that field is %(dt)s. To set %(dt)s fields, you must provide an instance of %(type1)s.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value), 'dt': f.DataType, 'type1': str(int)})
                if f.DataType == 'int16' and (value < -32768 or value > 32767):
                    raise ValueError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because that value is outside of the allowed range of values for the field (-32768 to 32767).') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value)})
                if f.DataType == 'int32' and (value < -2147483648 or value > 2147483647):
                    raise ValueError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because that value is outside of the allowed range of values for the field (-2147483648 to 2147483647).') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value)})
                value = int(value)

            elif f.DataType == 'float32' or f.DataType == 'float64':
                if isinstance(value, int):
                    if f.DataType == 'float32' and (value < -2**24+1 or value > 2**24-1):
                        raise ValueError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to integer %(value)s because %(field)s uses the 32-bit floating point data type, which can only exactly represent integers between -2^24 + 1 and 2^24 - 1, and %(value)s is outside of that range.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value)})
                    elif f.DataType == 'float64' and (value < -2**53+1 or value > 2**53-1):
                        raise ValueError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to integer %(value)s because %(field)s uses the 64-bit floating point data type, which can only exactly represent integers between -2^53 + 1 and 2^53 - 1, and %(value)s is outside of that range.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value)})
                elif not isinstance(value, float):
                    raise TypeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because the data type of that field is %(dt)s. To set %(dt)s fields, you must provide an instance of %(type)s.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value), 'dt': f.DataType, 'type': str(float)})

                # I'm not doing a range check on float32 because it is too
                # complicated to implement correctly and it seems unlikely
                # that anyone would exceed the range of float32 in normal
                # circumstances. If they do, the underlying programming
                # library will hopefully catch the problem.

                value = float(value)

            elif f.DataType == 'string':
                if not isinstance(value, str):
                    raise TypeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because the data type of that field is %(dt)s. To set %(dt)s fields, you must provide an instance of %(type1)s.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value), 'dt': f.DataType, 'type1': str(str)})
                if f.Length is not None and len(value) > f.Length:
                    raise TypeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because the length of that string (%(len1)i) exceeds the maximum allowed by the field (%(len2)i).') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value), 'len1': len(value), 'len2': f.Length})

            elif f.DataType == 'date' or f.DataType == 'datetime':
                if not isinstance(value, (datetime.date, datetime.datetime)):
                    raise TypeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because the data type of that field is %(dt)s. To set %(dt)s fields, you must provide an instance of %(type1)s or %(type2)s.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value), 'dt': f.DataType, 'type1': str(datetime.date), 'type2': str(datetime.datetime)})

            elif f.DataType == 'binary':
                if not isinstance(value, str):
                    raise TypeError(_('Cannot set the value of the %(field)s field of this %(singular)s of %(dn)s to %(value)s because the data type of that field is binary. To set binary fields, you must provide an instance of %(type)s.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name, 'value': repr(value), 'type': str(str)})

        # Set the field.

        if Dataset._DebugLoggingEnabled():
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Setting field %(field)s to %(value)s.'), {'class': self.__class__.__name__, 'id': id(self), 'field': f.Name, 'value': repr(value)})

        try:
            self._SetValue(f.Name, value)
        except Exception as e:
            raise RuntimeError(_('Failed to set the value of the %(field)s field of a %(singular)s from %(dn)s to %(value)s due to %(e)s: %(msg)s') % {'field': f.Name, 'value': repr(value), 'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

    def _SetGeometry_Base(self, geometry, requestedFields=None):

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        # Validate that the dataset has geometry and that the caller's
        # geometry type matches the dataset's geometry type.

        if self._Table.GeometryType is None:
            raise RuntimeError(_('Cannot set the geometry of this %(singular)s of %(dn)s because the %(singular)s does not have geometry.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})

        if requestedFields is not None and self._Table.GeometryFieldName is not None and self._Table.GeometryFieldName not in requestedFields:
            raise RuntimeError(_('Cannot retrieve the geometry of this %(singular)s of %(dn)s. The %(singular)s has geometry but the geometry field (%(field)s) was not included in the list of requested fields when the cursor was opened.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': self._Table.GeometryFieldName})

        if geometry is None:
            raise ValueError(_('Cannot set the geometry of this %(singular)s of %(dn)s to None because null geometries are not supported.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})

        if not hasattr(geometry, '__class__') or geometry.__class__.__name__ != 'Geometry':   # Test by name rather than isinstance to allow caller to pass in Geometry instances allocated by their own OGR module rather than MGET's assimilated copy
            raise TypeError(_('The geometry parameter must be an instance of the OGR Geometry class.'))

        Dataset._ogr()
        if geometry.GetGeometryType() not in Dataset._GeometryTypeForOGRGeometry:
            raise ValueError(_('Cannot set the geometry of this %(singular)s of %(dn)s because the provided Geometry object has the geometry type %(gt)i ("%(gtname)s"), which is not currently supported.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'gt': geometry.GetGeometryType(), 'gtname': geometry.GetGeometryName()})

        geometryType = Dataset._GeometryTypeForOGRGeometry[geometry.GetGeometryType()]
        if geometryType != self._Table.GeometryType:
            if self._Table.GeometryType in ['Point', 'LineString', 'Polygon', 'Point25D', 'LineString25D', 'Polygon25D']:
                raise ValueError(_('Cannot set the geometry of this %(singular)s of %(dn)s because the provided Geometry object has the incompatible geometry type %(gt1)s. The Geometry object must have a geometry type of %(gt2)s.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'gt1': geometryType, 'gt2': self._Table.GeometryType})
            elif self._Table.GeometryType.startswith('Multi') and geometryType != self._Table.GeometryType[5:]:
                raise ValueError(_('Cannot set the geometry of this %(singular)s of %(dn)s because the provided Geometry object has the incompatible geometry type %(gt1)s. The Geometry object must have a geometry type of %(gt2)s or %(gt3)s.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'gt1': geometryType, 'gt2': self._Table.GeometryType[5:], 'gt3': self._Table.GeometryType})
            elif self._Table.GeometryType == 'GeometryCollection' and geometryType.endswith('25D'):
                raise ValueError(_('Cannot set the geometry of this %(singular)s of %(dn)s because the provided Geometry object has Z coordinates but the dataset does not.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})
            elif self._Table.GeometryType == 'GeometryCollection25D' and not geometryType.endswith('25D'):
                raise ValueError(_('Cannot set the geometry of this %(singular)s of %(dn)s because the provided Geometry object does not have Z coordinates but the dataset requires them.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})
        
        # Set the geometry.

        if Dataset._DebugLoggingEnabled():
            wkt = geometry.ExportToWkt()
            if len(wkt) > 256:
                wkt = wkt[:256] + '...'
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Setting geometry to WKT "%(wkt)s".'), {'class': self.__class__.__name__, 'id': id(self), 'wkt': wkt})

        try:
            self._SetGeometry(geometry)
        except Exception as e:
            wkt = geometry.ExportToWkt()
            if len(wkt) > 256:
                wkt = wkt[:256] + '...'
            raise RuntimeError(_('Failed to set the geometry of a %(singular)s from %(dn)s to the equivalent of WKT "%(wkt)s" due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'wkt': wkt, 'e': e.__class__.__name__, 'msg': e})

    @staticmethod
    def _CloseCursorsAtExit():
        if hasattr(_Cursor, '_CursorsToCloseAtExit'):
            while len(_Cursor._CursorsToCloseAtExit) > 0:
                if _Cursor._CursorsToCloseAtExit[0]() is None:      # Should never happen because _Cursor.__del__() removes the object from the list
                    del _Cursor._CursorsToCloseAtExit[0]
                else:
                    _Cursor._CursorsToCloseAtExit[0]().Close()      # This will remove it from the list.

atexit.register(_Cursor._CloseCursorsAtExit)


class SelectCursor(_Cursor):
    __doc__ = DynamicDocString()
    
    # Public properties and instance methods

    def _GetAtEnd(self):
        return bool(self._AtEnd)

    AtEnd = property(_GetAtEnd, doc=DynamicDocString())

    def NextRow(self):
        if self._AtEnd:
            raise IndexError(_('The last %(singular)s has already been retrieved.') % {'singular': self._RowDescriptionSingular})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        if Dataset._DebugLoggingEnabled():
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Retrieving a %(singular)s.'), {'class': self.__class__.__name__, 'id': id(self), 'singular': self._RowDescriptionSingular})

        try:
            rowAvailable = self._NextRow()
        except Exception as e:
            raise RuntimeError(_('Failed to retrieve a %(singular)s from %(dn)s due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        if rowAvailable:
            self._AtEnd = False
            if self._ProgressReporter is not None:
                self._ProgressReporter.ReportProgress()
        else:
            self._AtEnd = True
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: No more %(plural)s available.'), {'class': self.__class__.__name__, 'id': id(self), 'plural': self._RowDescriptionPlural})
            self.Close()

        return rowAvailable

    def GetValue(self, field):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Validate that a row has been retrieved and that we're not at
        # the end.
        
        if self._IsOpen and self._AtEnd is None:
            raise RuntimeError(_('The first %(singular)s has not been retrieved yet. Call NextRow() before calling GetValue().') % {'singular': self._RowDescriptionSingular})
        
        if self._AtEnd:
            raise RuntimeError(_('All of the %(plural)s have already been retrieved. Do not call GetValue() after NextRow() has returned False.') % {'plural': self._RowDescriptionPlural})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        # Validate that the field exists and that the caller requested
        # it when opening the cursor.

        if not isinstance(field, str):
            raise TypeError(_('The field parameter must be a string.'))

        f = self._Table.GetFieldByName(field)
        if f is None:
            raise RuntimeError(_('Cannot retrieve the value of field "%(field)s" of this %(singular)s of %(dn)s because the field does not exist.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': field})

        if self._RequestedFields is not None and f.Name not in self._RequestedFields:
            raise RuntimeError(_('Cannot retrieve the value of the %(field)s field of this %(singular)s of %(dn)s. The field exists but was not included in the list of requested fields when the cursor was opened.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name})

        # Validate that it is not the geometry field.

        if f.Name == self._Table.GeometryFieldName:
            raise RuntimeError(_('Cannot retrieve the value of the %(field)s field of this %(singular)s of %(dn)s because that field is the geometry field. To get the geometry field, call GetGeometry() rather than GetValue().') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name})

        # Get and return the value of the field.

        try:
            value = self._GetValue(f.Name)
        except Exception as e:
            raise RuntimeError(_('Failed to retrieve the value of the %(field)s field of a %(singular)s from %(dn)s due to %(e)s: %(msg)s') % {'field': f.Name, 'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        # If it is a memoryview or bytearray object convert it to a str.

        if isinstance(value, memoryview):
            value = value.tobytes()
        elif isinstance(value, bytearray):
            value = str(value)

        if Dataset._DebugLoggingEnabled():
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Get field %(field)s returned %(value)s.'), {'class': self.__class__.__name__, 'id': id(self), 'field': f.Name, 'value': repr(value)})

        return value

    def GetOID(self):

        # Validate that a row has been retrieved and that we're not at
        # the end.
        
        if self._IsOpen and self._AtEnd is None:
            raise RuntimeError(_('The first %(singular)s has not been retrieved yet. Call NextRow() before calling GetOID().') % {'singular': self._RowDescriptionSingular})
        
        if self._AtEnd:
            raise RuntimeError(_('All of the %(plural)s have already been retrieved. Do not call GetOID() after NextRow() has returned False.') % {'plural': self._RowDescriptionPlural})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        # Validate that the dataset has an OID, and if it has an OID
        # field, that the caller requested that field when opening the
        # cursor.

        if self._Table.HasOID is None:
            raise RuntimeError(_('Cannot retrieve the object ID (OID) of this %(singular)s of %(dn)s because the %(singular)s does not have an OID.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})

        if self._RequestedFields is not None and self._Table.OIDFieldName is not None and self._Table.OIDFieldName not in self._RequestedFields:
            raise RuntimeError(_('Cannot retrieve the object ID (OID) of this %(singular)s of %(dn)s. The %(singular)s has an OID but the OID field (%(field)s) was not included in the list of requested fields when the cursor was opened.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': self._Table.OIDFieldName})

        # Get and return the OID.

        try:
            oid = self._GetOID()
        except Exception as e:
            raise RuntimeError(_('Failed to retrieve the object ID (OID) of a %(singular)s from %(dn)s due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        if Dataset._DebugLoggingEnabled():
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Get OID returned "%(oid)s".'), {'class': self.__class__.__name__, 'id': id(self), 'oid': repr(oid)})

        return oid

    def GetGeometry(self):

        # Validate that a row has been retrieved and that we're not at
        # the end.
        
        if self._IsOpen and self._AtEnd is None:
            raise RuntimeError(_('The first %(singular)s has not been retrieved yet. Call NextRow() before calling GetGeometry().') % {'singular': self._RowDescriptionSingular})
        
        if self._AtEnd:
            raise RuntimeError(_('All of the %(plural)s have already been retrieved. Do not call GetGeometry() after NextRow() has returned False.') % {'plural': self._RowDescriptionPlural})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        # Validate that the dataset has geometry, and if it has a
        # geometry field, that the caller requested that field when
        # opening the cursor.

        if self._Table.GeometryType is None:
            raise RuntimeError(_('Cannot retrieve the geometry of this %(singular)s of %(dn)s because the %(singular)s does not have geometry.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})

        if self._RequestedFields is not None and self._Table.GeometryFieldName is not None and self._Table.GeometryFieldName not in self._RequestedFields:
            raise RuntimeError(_('Cannot retrieve the geometry of this %(singular)s of %(dn)s. The %(singular)s has geometry but the geometry field (%(field)s) was not included in the list of requested fields when the cursor was opened.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': self._Table.GeometryFieldName})

        # Get and return the geometry.

        try:
            geometry = self._GetGeometry()
        except Exception as e:
            raise RuntimeError(_('Failed to retrieve the geometry of a %(singular)s from %(dn)s due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        if Dataset._DebugLoggingEnabled():
            wkt = geometry.ExportToWkt()
            if len(wkt) > 256:
                wkt = wkt[:256] + '...'
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Get geometry returned WKT "%(wkt)s".'), {'class': self.__class__.__name__, 'id': id(self), 'wkt': wkt})

        return geometry

    # Private base class constructor. Do not invoke directly; use
    # Table.OpenSelectCursor instead. Do not override; put
    # your initialization code the derived class's _Open method.

    def __init__(self, dataset, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        # Do not call self.__doc__.Obj.ValidateMethodInvocation() here.
        # Table.OpenSelectCursor() handles validation for us.

        # Initialize the base class and our attributes.

        super(SelectCursor, self).__init__(dataset, rowDescriptionSingular, rowDescriptionPlural)
        
        self._AtEnd = None
        self._RequestedFields = None

        # Validate that the caller is requesting existing fields.

        if fields is not None:
            self._RequestedFields = set()
            for field in fields:
                f = self._Table.GetFieldByName(field)
                if f is None:
                    raise ValueError(_('Cannot retrieve field "%(field)s" of %(dn)s because the field does not exist.') % {'dn': self._Table.DisplayName, 'field': field})
                self._RequestedFields.add(f.Name)
            fields = list(self._RequestedFields)

        # Validate that the orderBy expression references valid fields
        # and includes valid sort orders.

        if orderBy is not None:
            orderByList = [s.strip() for s in orderBy.split(',')]
            for i in range(len(orderByList)):
                parts = orderByList[i].split()
                if len(parts) not in [1, 2] or len(parts) == 2 and parts[1].upper() not in ['A', 'ASC', 'ASCENDING', 'D', 'DESC', 'DESCENDING']:
                    raise ValueError(_('Cannot retrieve %(plural)s from %(dn)s using the ORDER BY expression "%(orderBy)s". The expression is invalid.') % {'plural': self._RowDescriptionPlural, 'dn': dataset.DisplayName, 'orderBy': orderBy})
                f = self._Table.GetFieldByName(parts[0])
                if f is None:
                    raise ValueError(_('Cannot retrieve %(plural)s from %(dn)s using the ORDER BY expression "%(orderBy)s". The expression refers to a field "%(field)s" that does not exist.') % {'plural': self._RowDescriptionPlural, 'dn': dataset.DisplayName, 'orderBy': orderBy, 'field': parts[0]})
                if len(parts) == 1 or parts[1][0].upper() == 'A':
                    orderByList[i] = f.Name + ' ASC'
                else:
                    orderByList[i] = f.Name + ' DESC'
            orderBy = ', '.join(orderByList)

        # Call the derived class to open the cursor.

        if isinstance(self, UpdateCursor):
            cursorType = _('update')
        else:
            cursorType = _('select')
        
        self._Table._LogDebug(_('%(class)s 0x%(id)016X: Opening %(curtype)s cursor on %(dn)s, fields=%(fields)s, where=%(where)s, orderBy=%(orderBy)s, rowCount=%(rc)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': dataset.DisplayName, 'curtype': cursorType, 'fields': repr(fields), 'where': repr(where), 'orderBy': repr(orderBy), 'rc': repr(rowCount)})
        try:
            self._Open(fields, where, orderBy)
        except Exception as e:
            self._Table = None
            raise RuntimeError(_('Cannot retrieve %(plural)s from %(dn)s. Failed to open a %(curtype)s cursor due to %(e)s: %(msg)s') % {'plural': self._RowDescriptionPlural, 'dn': dataset.DisplayName, 'curtype': cursorType, 'e': e.__class__.__name__, 'msg': e})

        self._IsOpen = True

        if not hasattr(_Cursor, '_CursorsToCloseAtExit'):
            _Cursor._CursorsToCloseAtExit = []
        _Cursor._CursorsToCloseAtExit.insert(0, weakref.ref(self))

        # If the caller wants progress to be reported, start a
        # progress reporter.

        if reportProgress:
            if rowCount is not None:
                arcGISProgressorLabel = _('Retrieving %(rowCount)i %(plural)s') % {'rowCount': rowCount, 'plural': self._RowDescriptionPlural}
            else:
                arcGISProgressorLabel = None

            self._ProgressReporter = ProgressReporter(progressMessage1=_('Still retrieving %(plural)s: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s retrieved, %%(perOp)s per %(singular)s, %%(opsRemaining)i remaining, estimated completion time: %%(etc)s.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      progressMessage2=_('Still retrieving %(plural)s: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s retrieved, %%(perOp)s per %(singular)s.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      completionMessage=_('Finished retrieving %(plural)s: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s retrieved, %%(perOp)s per %(singular)s.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      abortedMessage=_('Query operation stopped before all %(plural)s were retrieved: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s retrieved, %%(perOp)s per %(singular)s, %%(opsIncomplete)i %(plural)s not retrieved.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      arcGISProgressorLabel=arcGISProgressorLabel)
            self._ProgressReporter.Start(rowCount)
        else:
            self._ProgressReporter = None

    # Private methods that the derived class must override (except
    # _GetOID and _GetGeometry, if appropriate).

    def _Open(self, fields, where, orderBy):
        raise NotImplementedError(_('The _Open method of class %s has not been implemented.') % self.__class__.__name__)

    def _NextRow(self):
        raise NotImplementedError(_('The _NextRow method of class %s has not been implemented.') % self.__class__.__name__)

    def _GetValue(self, field):
        raise NotImplementedError(_('The _GetValue method of class %s has not been implemented.') % self.__class__.__name__)

    def _GetOID(self):
        raise NotImplementedError(_('The _GetOID method of class %s has not been implemented.') % self.__class__.__name__)

    def _GetGeometry(self):
        raise NotImplementedError(_('The _GetGeometry method of class %s has not been implemented.') % self.__class__.__name__)


class UpdateCursor(SelectCursor):
    __doc__ = DynamicDocString()
    
    # Public properties and instance methods

    def NextRow(self):
        if self._AtEnd:
            raise IndexError(_('The last %(singular)s has already been retrieved.') % {'singular': self._RowDescriptionSingular})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        if self._ProgressReporter is not None and self._NeedToReportProgress:
            self._ProgressReporter.ReportProgress()
            self._NeedToReportProgress = False

        if Dataset._DebugLoggingEnabled():
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Retrieving a %(singular)s.'), {'class': self.__class__.__name__, 'id': id(self), 'singular': self._RowDescriptionSingular})

        self._RowUpdatedOrDeleted = False

        try:
            rowAvailable = self._NextRow()
        except Exception as e:
            raise RuntimeError(_('Failed to retrieve a %(singular)s from %(dn)s due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        if rowAvailable:
            self._AtEnd = False
            self._NeedToReportProgress = self._ProgressReporter is not None
        else:
            self._AtEnd = True
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: No more %(plural)s available.'), {'class': self.__class__.__name__, 'id': id(self), 'plural': self._RowDescriptionPlural})
            self.Close()

        return rowAvailable

    def GetValue(self, field):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Validate that we haven't updated or deleted this row yet and
        # call the base class method. The base class will take care of
        # the other validation.

        if self._RowUpdatedOrDeleted:
            raise RuntimeError(_('This %(singular)s has already been updated or deleted. Do not call GetValue() after calling UpdateRow() or DeleteRow(). Call NextRow() after calling UpdateRow() or DeleteRow().') % {'singular': self._RowDescriptionSingular})
        
        return super(UpdateCursor, self).GetValue(field)

    def GetOID(self):

        # Validate that we haven't updated or deleted this row yet and
        # call the base class method. The base class will take care of
        # the other validation.

        if self._RowUpdatedOrDeleted:
            raise RuntimeError(_('This %(singular)s has already been updated or deleted. Do not call GetOID() after calling UpdateRow() or DeleteRow(). Call NextRow() after calling UpdateRow() or DeleteRow().') % {'singular': self._RowDescriptionSingular})
        
        return super(UpdateCursor, self).GetOID()

    def GetGeometry(self):

        # Validate that we haven't updated or deleted this row yet and
        # call the base class method. The base class will take care of
        # the other validation.

        if self._RowUpdatedOrDeleted:
            raise RuntimeError(_('This %(singular)s has already been updated or deleted. Do not call GetGeometry() after calling UpdateRow() or DeleteRow(). Call NextRow() after calling UpdateRow() or DeleteRow().') % {'singular': self._RowDescriptionSingular})
        
        return super(UpdateCursor, self).GetGeometry()

    def SetValue(self, field, value):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Validate that a row has been retrieved, that we're not at
        # the end, and that we haven't updated or deleted this row
        # yet.
        
        if self._IsOpen and self._AtEnd is None:
            raise RuntimeError(_('The first %(singular)s has not been retrieved yet. Call NextRow() before calling SetValue().') % {'singular': self._RowDescriptionSingular})
        
        if self._AtEnd:
            raise RuntimeError(_('All of the %(plural)s have already been retrieved. Do not call SetValue() after NextRow() has returned False.') % {'plural': self._RowDescriptionPlural})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        if self._RowUpdatedOrDeleted:
            raise RuntimeError(_('This %(singular)s has already been updated or deleted. Do not call SetValue() after calling UpdateRow() or DeleteRow(). Call NextRow() after calling UpdateRow() or DeleteRow().') % {'singular': self._RowDescriptionSingular})

        # Set the field.
        
        self._SetValue_Base(field, value, self._RequestedFields)

    def SetGeometry(self, geometry):

        # Validate that a row has been retrieved, that we're not at
        # the end, and that we haven't updated or deleted this row
        # yet.
        
        if self._IsOpen and self._AtEnd is None:
            raise RuntimeError(_('The first %(singular)s has not been retrieved yet. Call NextRow() before calling SetGeometry().') % {'singular': self._RowDescriptionSingular})
        
        if self._AtEnd:
            raise RuntimeError(_('All of the %(plural)s have already been retrieved. Do not call SetGeometry() after NextRow() has returned False.') % {'plural': self._RowDescriptionPlural})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        if self._RowUpdatedOrDeleted:
            raise RuntimeError(_('This %(singular)s has already been updated or deleted. Do not call SetGeometry() after calling UpdateRow() or DeleteRow(). Call NextRow() after calling UpdateRow() or DeleteRow().') % {'singular': self._RowDescriptionSingular})

        # Set the geometry.
        
        self._SetGeometry_Base(geometry, self._RequestedFields)

    def UpdateRow(self):

        # Validate that this dataset supports row updating, that a row
        # has been retrieved, that we're not at the end, and that we
        # haven't updated or deleted this row yet.

        if self._UpdateRowCapabilityError is not None:
            raise self._UpdateRowCapabilityError
        
        if self._IsOpen and self._AtEnd is None:
            raise RuntimeError(_('The first %(singular)s has not been retrieved yet. Call NextRow() before calling UpdateRow().') % {'singular': self._RowDescriptionSingular})
        
        if self._AtEnd:
            raise RuntimeError(_('All of the %(plural)s have already been retrieved. Do not call UpdateRow() after NextRow() has returned False.') % {'plural': self._RowDescriptionPlural})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        if self._RowUpdatedOrDeleted:
            raise RuntimeError(_('This %(singular)s has already been updated or deleted. Do not call UpdateRow() after calling UpdateRow() or DeleteRow(). Call NextRow() after calling UpdateRow() or DeleteRow().') % {'singular': self._RowDescriptionSingular})

        # Update the row and report progress.

        if Dataset._DebugLoggingEnabled():
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Updating this %(singular)s.'), {'class': self.__class__.__name__, 'id': id(self), 'singular': self._RowDescriptionSingular})

        try:
            self._UpdateRow()
        except Exception as e:
            raise RuntimeError(_('Failed to update a %(singular)s in %(dn)s due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        self._RowUpdatedOrDeleted = True
        if self._ProgressReporter is not None:
            self._ProgressReporter.RowsUpdated += 1
            self._ProgressReporter.ReportProgress()
            self._NeedToReportProgress = False

    def DeleteRow(self):

        # Validate that this dataset supports row deletion, that a row
        # has been retrieved, that we're not at the end, and that we
        # haven't updated or deleted this row yet.

        if self._DeleteRowCapabilityError is not None:
            raise self._DeleteRowCapabilityError
        
        if self._IsOpen and self._AtEnd is None:
            raise RuntimeError(_('The first %(singular)s has not been retrieved yet. Call NextRow() before calling DeleteRow().') % {'singular': self._RowDescriptionSingular})
        
        if self._AtEnd:
            raise RuntimeError(_('All of the %(plural)s have already been retrieved. Do not call DeleteRow() after NextRow() has returned False.') % {'plural': self._RowDescriptionPlural})

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        if self._RowUpdatedOrDeleted:
            raise RuntimeError(_('This %(singular)s has already been updated or deleted. Do not call DeleteRow() after calling UpdateRow() or DeleteRow(). Call NextRow() after calling UpdateRow() or DeleteRow().') % {'singular': self._RowDescriptionSingular})

        # Update the row and report progress.

        if Dataset._DebugLoggingEnabled():
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Deleting this %(singular)s.'), {'class': self.__class__.__name__, 'id': id(self), 'singular': self._RowDescriptionSingular})

        try:
            self._DeleteRow()
        except Exception as e:
            raise RuntimeError(_('Failed to delete a %(singular)s from %(dn)s due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        self._RowUpdatedOrDeleted = True
        if self._ProgressReporter is not None:
            self._ProgressReporter.RowsDeleted += 1
            self._ProgressReporter.ReportProgress()
            self._NeedToReportProgress = False

    # Private base class constructor. Do not invoke directly; use
    # Table.OpenUpdateCursor instead. Do not override; put
    # your initialization code the derive class's _Open method.

    def __init__(self, dataset, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        # Do not call self.__doc__.Obj.ValidateMethodInvocation() here.
        # Table.OpenUpdateCursor() handles validation for us.

        super(UpdateCursor, self).__init__(dataset, fields, where, orderBy, rowCount, False, rowDescriptionSingular, rowDescriptionPlural)

        self._UpdateRowCapabilityError = self._Table._TestCapability('updaterow')
        self._DeleteRowCapabilityError = self._Table._TestCapability('deleterow')
        self._RowUpdatedOrDeleted = False
        self._NeedToReportProgress = False

        if reportProgress:
            if rowCount is not None:
                arcGISProgressorLabel = _('Updating %(rowCount)i %(plural)s') % {'rowCount': rowCount, 'plural': self._RowDescriptionPlural}
            else:
                arcGISProgressorLabel = None

            self._ProgressReporter = _UpdateCursorProgressReporter(self._RowDescriptionSingular, self._RowDescriptionPlural, arcGISProgressorLabel)
            self._ProgressReporter.Start(rowCount)

    # Private methods that the derived class must override (except
    # _SetGeometry when the derived class does not support geometry).
    # These are in addition to those defined by SelectCursor.

    def _Close(self):
        try:
            if hasattr(self, '_ProgressReporter') and self._ProgressReporter is not None and hasattr(self, '_NeedToReportProgress') and self._NeedToReportProgress:
                self._ProgressReporter.ReportProgress()
                self._NeedToReportProgress = False
        finally:
            super(UpdateCursor, self)._Close()

    def _SetValue(self, field, value):
        raise NotImplementedError(_('The _SetValue method of class %s has not been implemented.') % self.__class__.__name__)

    def _SetGeometry(self, geometry):
        raise NotImplementedError(_('The _SetGeometry method of class %s has not been implemented.') % self.__class__.__name__)

    def _UpdateRow(self):
        raise NotImplementedError(_('The _UpdateRow method of class %s has not been implemented.') % self.__class__.__name__)

    def _DeleteRow(self):
        raise NotImplementedError(_('The _DeleteRow method of class %s has not been implemented.') % self.__class__.__name__)


class _UpdateCursorProgressReporter(ProgressReporter):

    def __init__(self, rowDescriptionSingular, rowDescriptionPlural, arcGISProgressorLabel):
        self.RowsUpdated = 0
        self.RowsDeleted = 0
        super(_UpdateCursorProgressReporter, self).__init__(
            progressMessage1=_('Update in progress: %%(elapsed)s elapsed, %%(updated)i %(plural)s updated, %%(deleted)i deleted, %%(unchanged)i unchanged, %%(perOp)s per %(singular)s, %%(opsRemaining)i remaining, estimated completion time: %%(etc)s.') % {'singular': rowDescriptionSingular, 'plural': rowDescriptionPlural},
            progressMessage2=_('Update in progress: %%(elapsed)s elapsed, %%(updated)i %(plural)s updated, %%(deleted)i deleted, %%(unchanged)i unchanged, %%(perOp)s per %(singular)s.') % {'singular': rowDescriptionSingular, 'plural': rowDescriptionPlural},
            completionMessage=_('Update complete: %%(elapsed)s elapsed, %%(updated)i %(plural)s updated, %%(deleted)i deleted, %%(unchanged)i unchanged, %%(perOp)s per %(singular)s.') % {'singular': rowDescriptionSingular, 'plural': rowDescriptionPlural},
            abortedMessage=_('Update stopped before all %(plural)s were processed: %%(elapsed)s elapsed, %%(updated)i %(plural)s updated, %%(deleted)i deleted, %%(unchanged)i unchanged, %%(perOp)s per %(singular)s, %%(opsIncomplete)i %(plural)s not processed.') % {'singular': rowDescriptionSingular, 'plural': rowDescriptionPlural},
            arcGISProgressorLabel=arcGISProgressorLabel)

    def _FormatProgressMessage1(self, timeElapsed, opsCompleted, timePerOp, opsRemaining, estimatedTimeOfCompletionString):
        return self._ProgressMessage1 % {'elapsed' : str(datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds)), 'updated': self.RowsUpdated, 'deleted': self.RowsDeleted, 'unchanged': opsCompleted - self.RowsUpdated - self.RowsDeleted, 'perOp': str(timePerOp), 'opsRemaining': opsRemaining, 'etc': estimatedTimeOfCompletionString}

    def _FormatProgressMessage2(self, timeElapsed, opsCompleted, timePerOp):
        return self._ProgressMessage2 % {'elapsed' : str(datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds)), 'updated': self.RowsUpdated, 'deleted': self.RowsDeleted, 'unchanged': opsCompleted - self.RowsUpdated - self.RowsDeleted, 'perOp': str(timePerOp)}

    def _FormatCompletionMessage(self, timeElapsed, opsCompleted, timePerOp):
        return self._CompletionMessage % {'elapsed' : str(datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds)), 'updated': self.RowsUpdated, 'deleted': self.RowsDeleted, 'unchanged': opsCompleted - self.RowsUpdated - self.RowsDeleted, 'perOp': str(timePerOp)}

    def _FormatAbortedMessage(self, timeElapsed, opsCompleted, timePerOp, opsIncomplete):
        return self._AbortedMessage % {'elapsed' : str(datetime.timedelta(days=timeElapsed.days, seconds=timeElapsed.seconds)), 'updated': self.RowsUpdated, 'deleted': self.RowsDeleted, 'unchanged': opsCompleted - self.RowsUpdated - self.RowsDeleted, 'perOp': str(timePerOp), 'opsIncomplete': opsIncomplete}


class InsertCursor(_Cursor):
    __doc__ = DynamicDocString()
    
    # Public properties and instance methods

    def SetValue(self, field, value):
        self.__doc__.Obj.ValidateMethodInvocation()
        self._SetValue_Base(field, value)
        self._FieldSet[field] = True

    def SetGeometry(self, geometry):
        self._SetGeometry_Base(geometry)
        self._GeometrySet = True

    def InsertRow(self):

        if not self._IsOpen:
            raise RuntimeError(_('The cursor is closed.'))

        # For datasets with geometry, validate that the caller has
        # set the geometry.

        if self._Table.GeometryType is not None and not self._GeometrySet:
            raise RuntimeError(_('This %(singular)s cannot be inserted into %(dn)s because its geometry has not been set.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})

        # Set to null all settable nullable fields that were not set
        # by the caller.

        debug = Dataset._DebugLoggingEnabled()
        
        for f in self._Table.Fields:
            if f.Name != self._Table.OIDFieldName and f.Name != self._Table.GeometryFieldName and f.IsSettable and f.Name not in self._FieldSet:
                if f.IsNullable:
                    if debug:
                        self._Table._LogDebug(_('%(class)s 0x%(id)016X: Setting field %(field)s to None.'), {'class': self.__class__.__name__, 'id': id(self), 'field': f.Name})
                    self._SetValue(f.Name, None)
                    self._FieldSet[f.Name] = True
                else:
                    raise RuntimeError(_('This %(singular)s cannot be inserted into %(dn)s because field %(field)s has not been assigned a value and it is not nullable. You must provide a value for this field.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': f.Name})

        # Insert the row and report progress.

        if debug:
            self._Table._LogDebug(_('%(class)s 0x%(id)016X: Inserting this %(singular)s.'), {'class': self.__class__.__name__, 'id': id(self), 'singular': self._RowDescriptionSingular})

        try:
            self._InsertRow()
        except Exception as e:
            raise RuntimeError(_('Failed to insert a %(singular)s into %(dn)s due to %(e)s: %(msg)s') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        self._FieldSet = {}
        self._GeometrySet = False

        if self._ProgressReporter is not None:
            self._ProgressReporter.ReportProgress()

    # Private base class constructor. Do not invoke directly; use
    # Table.OpenInsertCursor instead. Do not override; put
    # your initialization code the derive class's _Open method.

    def __init__(self, dataset, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        # Do not call self.__doc__.Obj.ValidateMethodInvocation() here.
        # Table.OpenInsertCursor() handles validation for us.

        # Initialize the base class and our attributes.

        super(InsertCursor, self).__init__(dataset, rowDescriptionSingular, rowDescriptionPlural)

        self._FieldSet = {}
        self._GeometrySet = False

        # Call the derived class to open the cursor.
        
        self._Table._LogDebug(_('%(class)s 0x%(id)016X: Opening insert cursor on %(dn)s, rowCount=%(rc)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': dataset.DisplayName, 'rc': repr(rowCount)})
        try:
            self._Open()
        except Exception as e:
            self._Table = None    # Set this to None to make sure a reference is not leaked due when this constructor fails.
            raise RuntimeError(_('Cannot insert %(plural)s into %(dn)s. Failed to open an insert cursor due to %(e)s: %(msg)s') % {'plural': self._RowDescriptionPlural, 'dn': dataset.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        self._IsOpen = True

        if not hasattr(_Cursor, '_CursorsToCloseAtExit'):
            _Cursor._CursorsToCloseAtExit = []
        _Cursor._CursorsToCloseAtExit.insert(0, weakref.ref(self))

        # If the caller wants progress to be reported, start a
        # progress reporter.

        if reportProgress:
            if rowCount is not None:
                arcGISProgressorLabel = _('Inserting %(rowCount)i %(plural)s') % {'rowCount': rowCount, 'plural': self._RowDescriptionPlural}
            else:
                arcGISProgressorLabel = None
                
            self._ProgressReporter = ProgressReporter(progressMessage1=_('Still inserting %(plural)s: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s inserted, %%(perOp)s per %(singular)s, %%(opsRemaining)i remaining, estimated completion time: %%(etc)s.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      progressMessage2=_('Still inserting %(plural)s: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s inserted, %%(perOp)s per %(singular)s.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      completionMessage=_('Finished inserting %(plural)s: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s inserted, %%(perOp)s per %(singular)s.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      abortedMessage=_('Insert operation stopped before all %(plural)s were inserted: %%(elapsed)s elapsed, %%(opsCompleted)i %(plural)s inserted, %%(perOp)s per %(singular)s, %%(opsIncomplete)i %(plural)s not inserted.') % {'singular': self._RowDescriptionSingular, 'plural': self._RowDescriptionPlural},
                                                      arcGISProgressorLabel=arcGISProgressorLabel)
            self._ProgressReporter.Start(rowCount)
        else:
            self._ProgressReporter = None

    # Private methods that the derived class must override (except
    # _SetGeometry when the derived class does not support geometry).

    def _Open(self):
        raise NotImplementedError(_('The _Open method of class %s has not been implemented.') % self.__class__.__name__)

    def _SetValue(self, field, value):
        raise NotImplementedError(_('The _SetValue method of class %s has not been implemented.') % self.__class__.__name__)

    def _SetGeometry(self, geometry):
        raise NotImplementedError(_('The _SetGeometry method of class %s has not been implemented.') % self.__class__.__name__)

    def _InsertRow(self):
        raise NotImplementedError(_('The _InsertRow method of class %s has not been implemented.') % self.__class__.__name__)


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
