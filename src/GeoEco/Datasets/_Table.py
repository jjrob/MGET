# _Table.py - Defines Table, the base class for classes representing tabular
# datasets.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from ._Dataset import Dataset


class Table(Dataset):
    __doc__ = DynamicDocString()
    
    # Public properties and instance methods

    def _GetHasOID(self):
        return self.GetLazyPropertyValue('HasOID')

    HasOID = property(_GetHasOID, doc=DynamicDocString())

    def _GetOIDFieldName(self):
        return self.GetLazyPropertyValue('OIDFieldName')

    OIDFieldName = property(_GetOIDFieldName, doc=DynamicDocString())

    def _GetGeometryType(self):
        return self.GetLazyPropertyValue('GeometryType')

    GeometryType = property(_GetGeometryType, doc=DynamicDocString())

    def _GetGeometryFieldName(self):
        return self.GetLazyPropertyValue('GeometryFieldName')

    GeometryFieldName = property(_GetGeometryFieldName, doc=DynamicDocString())

    def _GetMaxStringLength(self):
        return self.GetLazyPropertyValue('MaxStringLength')

    MaxStringLength = property(_GetMaxStringLength, doc=DynamicDocString())

    def _GetFields(self):
        return self.GetLazyPropertyValue('Fields')

    Fields = property(_GetFields, doc=DynamicDocString())

    def GetFieldByName(self, name):
        self.__doc__.Obj.ValidateMethodInvocation()
        if not hasattr(self, '_FieldsDict') or self._FieldsDict is None:
            self._FieldsDict = {}
            for field in self.Fields:
                self._FieldsDict[field.Name.upper()] = field
        if name.upper() not in self._FieldsDict:
            return None
        return self._FieldsDict[name.upper()]

    def AddField(self, name, dataType, length=None, precision=None, isNullable=None, allowSafeCoercions=True, failIfExists=False):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Verify that we have the required capabilities. If needed and allowed
        # by the caller, coerce unsupported data types to supported ones.

        self._RequireCapability('AddField')

        if allowSafeCoercions and dataType in ['date', 'int8', 'int16', 'int32', 'float32']:
            if self._TestCapability(dataType + ' datatype') is not None:
                if dataType == 'date':
                    newDataType = 'datetime'
                    if self._TestCapability(newDataType + ' datatype') is not None:
                        self._RequireCapability(dataType + ' DataType')

                elif dataType == 'int16':
                    newDataType = 'int32'
                    if self._TestCapability(newDataType + ' datatype') is not None:
                        newDataType = 'float32'
                        if self._TestCapability(newDataType + ' datatype') is not None:
                            newDataType = 'float64'
                            if self._TestCapability(newDataType + ' datatype') is not None:
                                self._RequireCapability(dataType + ' DataType')

                elif dataType == 'int8':
                    newDataType = 'int16'
                    if self._TestCapability(newDataType + ' datatype') is not None:
	                    newDataType = 'int32'
	                    if self._TestCapability(newDataType + ' datatype') is not None:
	                        newDataType = 'float32'
	                        if self._TestCapability(newDataType + ' datatype') is not None:
	                            newDataType = 'float64'
	                            if self._TestCapability(newDataType + ' datatype') is not None:
	                                self._RequireCapability(dataType + ' DataType')

                else:
                    newDataType = 'float64'
                    if self._TestCapability(newDataType + ' datatype') is not None:
                        self._RequireCapability(dataType + ' DataType')

                dataType = newDataType
        else:
            self._RequireCapability(dataType + ' DataType')
        
        if isNullable:
            self._RequireCapability(dataType + ' IsNullable')

        # If the data type is 'string' and length was supplied, verify that it
        # does not exceed the maximum allowed length.
        #
        # As a special case, if the requested length is 255 and the allowed
        # length is 254, adjust the requested length down to 254 and do not
        # report an error. This is a carefully considered hack to address a
        # common scenario: exporting ArcGIS personal geodatabase tables to DBF
        # files. Personal GDB fields are created with a length of 255 unless
        # the user overrides the default. It is probably rare for actual data
        # to use all 255 characters. Rather than prevent the user from
        # converting their GDB table to a DBF file, we assume that their data
        # will actually fit within a 254 character field and allow the
        # conversion to proceed.

        if dataType == 'string' and length is not None and self.MaxStringLength is not None and length > self.MaxStringLength:
            if length == 255 and self.MaxStringLength == 254:
                self._LogWarning(_('Adding text field %(name)s to %(dn)s with a maximum length of 254 instead of the requested length of 255. The maximum length of text fields permitted by this data format is 254.')  % {'name': name, 'dn': self.DisplayName})
                length = 254
            else:
                raise ValueError(_('Cannot add string field %(name)s to %(dn)s because the field length (%(length)i) exceeds the maximum allowed for this dataset (%(max)i).') % {'name': name, 'length': length, 'dn': self.DisplayName, 'max': self.MaxStringLength})

        # If the field already exists with the exact parameters requested by
        # the caller and the caller does not want us to fail in that
        # situation, return silently now.

        existingField = self.GetFieldByName(name)
        if existingField is not None:
            if not failIfExists:
                if existingField.DataType == dataType and (length is None or existingField.Length >= length) and (precision is None or existingField.Precision >= precision) and (isNullable is None or existingField.IsNullable == isNullable):
                    self._LogDebug(_('%(class)s 0x%(id)016X: Not adding field with name %(Name)s because it already exists.'), {'class': self.__class__.__name__, 'id': id(self), 'Name': name})
                    return
                raise ValueError(_('Cannot add field %(name)s to %(dn)s because a field with that name already exists and it has different characteristics than those you requested.') % {'name': name, 'dn': self.DisplayName})
            raise ValueError(_('Cannot add field %(name)s to %(dn)s because a field with that name already exists.') % {'name': name, 'dn': self.DisplayName})

        # Call the derived class to add the field.

        self._LogDebug(_('%(class)s 0x%(id)016X: Adding field %(i)i: Name=%(Name)s, DataType=%(DataType)s, Length=%(Length)s, Precision=%(Precision)s, IsNullable=%(IsNullable)s.'),
                       {'class': self.__class__.__name__, 'id': id(self), 'i': len(self.Fields), 'Name': name, 'DataType': dataType, 'Length': repr(length), 'Precision': repr(precision), 'IsNullable': repr(isNullable)})

        try:
            field = self._AddField(name, dataType, length, precision, isNullable)
        except Exception as e:
            raise RuntimeError(_('Failed to add a field named %(name)s to %(dn)s due to %(e)s: %(msg)s') % {'name': name, 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        # If we succeeded, throw out the existing Fields lazy property and our
        # _FieldsDict cache. This will cause the lazy property and cache to be
        # reloaded the next time they are needed, so we get the default values
        # for properties of the new field (e.g. length, precision, or
        # isNullable).

        self.DeleteLazyPropertyValue('Fields')
        del self._FieldsDict

    def DeleteField(self, name, failIfDoesNotExist=False):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Verify that we have the required capabilities.

        self._RequireCapability('DeleteField')

        # If the field does not already exist and the caller does not
        # want us to fail in that situation, return silently now.

        existingField = self.GetFieldByName(name)
        if existingField is None:
            if not failIfDoesNotExist:
                self._LogDebug(_('%(class)s 0x%(id)016X: Not deleting field with name %(Name)s because it does not exist.'), {'class': self.__class__.__name__, 'id': id(self), 'Name': name})
                return
            raise ValueError(_('Cannot delete field %(name)s from %(dn)s because that field does not exist.') % {'name': name, 'dn': self.DisplayName})

        # Call the derived class to delete the field.

        for i, f in enumerate(self.Fields):
            if f.Name == existingField.Name:
                break

        self._LogDebug(_('%(class)s 0x%(id)016X: Deleting field %(i)i: Name=%(Name)s, DataType=%(DataType)s, Length=%(Length)s, Precision=%(Precision)s, IsNullable=%(IsNullable)s.'),
                       {'class': self.__class__.__name__, 'id': id(self), 'i': i, 'Name': existingField.Name, 'DataType': existingField.DataType, 'Length': repr(existingField.Length), 'Precision': repr(existingField.Precision), 'IsNullable': repr(existingField.IsNullable)})

        try:
            self._DeleteField(name)
        except Exception as e:
            raise RuntimeError(_('Failed to delete field %(name)s from %(dn)s due to %(e)s: %(msg)s') % {'name': name, 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        # If we succeeded, remove the field from the Fields lazy property and
        # our cached list of fields.

        fields = list(self.GetLazyPropertyValue('Fields'))
        del fields[i]
        self.SetLazyPropertyValue('Fields', tuple(fields))

        del self._FieldsDict[existingField.Name.upper()]

    def CreateIndex(self, fields, indexName, unique=False, ascending=True):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Verify that we have the required capabilities.

        self._RequireCapability('CreateIndex')

        # Verify that all of the fields exist and that they are not
        # trying to create an index on the geometry field.

        for name in fields:
            field = self.GetFieldByName(name)
            if field is None:
                raise ValueError(_('Cannot create an index on field %(name)s of %(dn)s because that field does not exist.') % {'name': name, 'dn': self.DisplayName})
            if field.DataType == 'geometry':
                raise ValueError(_('Cannot create a non-spatial index on field %(name)s of %(dn)s because that is the geometry field. Only spatial indexes can be created on the geometry field.') % {'name': name, 'dn': self.DisplayName})

        # Call the derived class to create the index.

        if indexName is None:
            name = ''
        else:
            name = ' ' + indexName
            
        self._LogDebug(_('%(class)s 0x%(id)016X: Creating %(unique)s %(ascending)s index%(name)s on fields [%(fields)s] of %(dn)s.'),
                       {'class': self.__class__.__name__, 'id': id(self), 'unique': {False: _('non-unique'), True: _('unique')}[unique], 'ascending': {False: _('descending'), True: _('ascending')}[ascending], 'name': name, 'fields': ', '.join(fields), 'dn': self.DisplayName})

        try:
            self._CreateIndex(fields, indexName, unique, ascending)
        except Exception as e:
            raise RuntimeError(_('Failed to create %(unique)s %(ascending)s index%(name)s on fields [%(fields)s] of %(dn)s due to %(e)s: %(msg)s') % {'unique': {False: _('non-unique'), True: _('unique')}[unique], 'ascending': {False: _('descending'), True: _('ascending')}[ascending], 'name': name, 'fields': ', '.join(fields), 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})

    def DeleteIndex(self, indexName):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Verify that we have the required capabilities.

        self._RequireCapability('DeleteIndex')

        # Call the derived class to delete the index.

        if indexName is None:
            name = ''
        else:
            name = ' ' + indexName
            
        self._LogDebug(_('%(class)s 0x%(id)016X: Deleting index%(name)s.'), {'class': self.__class__.__name__, 'id': id(self), 'name': name})

        try:
            self._DeleteIndex(indexName)
        except Exception as e:
            raise RuntimeError(_('Failed to delete index%(name)s of %(dn)s due to %(e)s: %(msg)s') % {'name': name, 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})

    def GetRowCount(self):
        try:
            rowCount = self._GetRowCount()
        except Exception as e:
            raise RuntimeError(_('Failed to obtain the count of rows in %(dn)s due to %(e)s: %(msg)s') % {'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})
        self._LogDebug(_('%(class)s 0x%(id)016X: GetRowCount returned %(rc)s.'), {'class': self.__class__.__name__, 'id': id(self), 'rc': repr(rowCount)})
        return rowCount

    def Query(self, fields=None, where=None, orderBy=None, rowCount=None, reportProgress=True, rowDescriptionSingular=None, rowDescriptionPlural=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # If the caller did not specify a list of fields, use all of
        # the fields.

        if fields is None or len(fields) <= 0:
            fields = [field.Name for field in self.Fields]

        # Determine which of the fields are the OID or geometry
        # fields.

        isOIDField = [self.OIDFieldName is not None and field.lower() == self.OIDFieldName.lower() for field in fields]
        isGeometryField = [self.GeometryFieldName is not None and field.lower() == self.GeometryFieldName.lower() for field in fields]

        # Initialize a dictionary to hold the results:

        result = {}
        for field in fields:
            result[field] = []

        # Query the table and populate the dictionary.

        cursor = self.OpenSelectCursor(fields=fields, where=where, orderBy=orderBy, rowCount=rowCount, reportProgress=reportProgress, rowDescriptionSingular=rowDescriptionSingular, rowDescriptionPlural=rowDescriptionPlural)
        try:
            while cursor.NextRow():
                for i, field in enumerate(fields):
                    if isOIDField[i]:
                        result[field].append(cursor.GetOID())
                    elif isGeometryField[i]:
                        result[field].append(cursor.GetGeometry())
                    else:
                        result[field].append(cursor.GetValue(field))
        finally:
            del cursor

        # Return the dictionary.

        return result

    def OpenSelectCursor(self, fields=None, where=None, orderBy=None, rowCount=None, reportProgress=True, rowDescriptionSingular=None, rowDescriptionPlural=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        self._RequireCapability('SelectCursor')
        return self._OpenSelectCursor(fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    def OpenUpdateCursor(self, fields=None, where=None, orderBy=None, rowCount=None, reportProgress=True, rowDescriptionSingular=None, rowDescriptionPlural=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        self._RequireCapability('UpdateCursor')
        return self._OpenUpdateCursor(fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    def OpenInsertCursor(self, rowCount=None, reportProgress=True, rowDescriptionSingular=None, rowDescriptionPlural=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        self._RequireCapability('InsertCursor')
        return self._OpenInsertCursor(rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    # Private instance methods that the derived class should override
    # if the capability is supported

    def _AddField(self, name, dataType, length, precision, isNullable):
        raise NotImplementedError(_('The _AddField method of class %s has not been implemented.') % self.__class__.__name__)

    def _DeleteField(self, name):
        raise NotImplementedError(_('The _DeleteField method of class %s has not been implemented.') % self.__class__.__name__)

    def _CreateIndex(self, fields, indexName, unique, ascending):
        raise NotImplementedError(_('The _CreateIndex method of class %s has not been implemented.') % self.__class__.__name__)

    def _DeleteIndex(self, indexName):
        raise NotImplementedError(_('The _DeleteIndex method of class %s has not been implemented.') % self.__class__.__name__)

    def _GetRowCount(self):
        raise NotImplementedError(_('The _GetRowCount method of class %s has not been implemented.') % self.__class__.__name__)

    def _OpenSelectCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        raise NotImplementedError(_('The _OpenSelectCursor method of class %s has not been implemented.') % self.__class__.__name__)

    def _OpenUpdateCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        raise NotImplementedError(_('The _OpenUpdateCursor method of class %s has not been implemented.') % self.__class__.__name__)

    def _OpenInsertCursor(self, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        raise NotImplementedError(_('The _OpenInsertCursor method of class %s has not been implemented.') % self.__class__.__name__)


class Field(object):
    __doc__ = DynamicDocString()

    def _GetName(self):
        return self._Name

    def _GetDataType(self):
        return self._DataType

    def _GetLength(self):
        return self._Length

    def _GetPrecision(self):
        return self._Precision

    def _GetIsNullable(self):
        return self._IsNullable

    def _GetIsSettable(self):
        return self._IsSettable

    Name = property(_GetName, doc=DynamicDocString())
    DataType = property(_GetDataType, doc=DynamicDocString())
    Length = property(_GetLength, doc=DynamicDocString())
    Precision = property(_GetPrecision, doc=DynamicDocString())
    IsNullable = property(_GetIsNullable, doc=DynamicDocString())
    IsSettable = property(_GetIsSettable, doc=DynamicDocString())

    def __init__(self, name, dataType, length=None, precision=None, isNullable=None, isSettable=True):
        self.__doc__.Obj.ValidateMethodInvocation()
        self._Name = name
        self._DataType = dataType
        self._Length = length
        self._Precision = precision
        self._IsNullable = isNullable
        self._IsSettable = isSettable


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
