# _Database.py - Defines Database, a mixin class that defines methods for
# creating and deleting tables, and importing tables from one Database into
# another.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _


class Database(object):
    __doc__ = DynamicDocString()

    # Public interface.

    def TableExists(self, tableName):
        self.__doc__.Obj.ValidateMethodInvocation()

        exists = self._TableExists(tableName)
        if exists:
            self._LogDebug(_('%(class)s 0x%(id)016X: The %(objectType)s %(table)s exists in %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName})
        else:
            self._LogDebug(_('%(class)s 0x%(id)016X: The %(objectType)s %(table)s does not exist in %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName})

        return exists

    def CreateTable(self, tableName, geometryType=None, spatialReference=None, geometryFieldName=None, **options):
        self.__doc__.Obj.ValidateMethodInvocation()

        self._RequireCapability('CreateTable')
        if geometryType is not None:
            self._RequireCapability('GeometryType %s %s' % (geometryType, tableName))
            if geometryFieldName is not None:
                self._RequireCapability('GeometryFieldName')
        
        if self.TableExists(tableName):
            raise RuntimeError(_('Cannot create %(objectType)s %(table)s in %(dn)s because that %(objectType)s already exists.') % {'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName})

        if geometryType is None:        
            self._LogDebug(_('%(class)s 0x%(id)016X: Creating %(objectType)s %(table)s in %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName})
        else:
            if spatialReference is None:
                wkt = None
            else:
                wkt = spatialReference.ExportToWkt()
            self._LogDebug(_('%(class)s 0x%(id)016X: Creating %(objectType)s %(table)s in %(dn)s with geometryType=%(geometryType)s, spatialReference=%(wkt)s.'), {'class': self.__class__.__name__, 'id': id(self), 'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName, 'geometryType': geometryType, 'wkt': repr(wkt)})

        try:
            return self._CreateTable(tableName, geometryType, spatialReference, geometryFieldName, options)
        except Exception as e:
            raise RuntimeError(_('Failed to create %(objectType)s %(tableName)s in %(dn)s due to %(e)s: %(msg)s.') % {'objectType': self._GetObjectTypeDisplayName(tableName), 'tableName': tableName, 'dn': self._DisplayName, 'e': e.__class__.__name__, 'msg': e})

    def CreateTableFromTemplate(self, tableName, templateTable, fields=None, allowSafeCoercions=True, **options):
        self.__doc__.Obj.ValidateMethodInvocation()

        # If the caller specified a list of fields to use, make sure
        # all of those fields exist.

        createGeometryField = False

        if fields is not None:
            sourceFields = []
            for name in fields:
                if name == templateTable.OIDFieldName:          # Skip the OID field, if the caller specified it.
                    continue
                
                if name == templateTable.GeometryFieldName:     # Also skip the geometry field.
                    createGeometryField = True
                    continue
                
                field = templateTable.GetFieldByName(name)
                if field is None:
                    raise ValueError(_('Cannot create a field named %(field)s in new table %(table)s because that field does not exist in %(template)s.') % {'field': name, 'table': tableName, 'template': templateTable.DisplayName})
                
                sourceFields.append(field)

        # Otherwise, use all of the fields except the OID and geometry
        # field.

        else:
            createGeometryField = True
            sourceFields = list(templateTable.Fields)
            i = 0
            while i < len(sourceFields):
                if sourceFields[i].Name in [templateTable.OIDFieldName, templateTable.GeometryFieldName]:
                    del sourceFields[i]
                else:
                    i += 1

        # Create the table.

        if createGeometryField:

            # If we support assigning the name of the geometry field,
            # try to use the same name as the template table. If not,
            # do not try to assign the geometry field name (it will
            # likely fail).
            
            if self._TestCapability('GeometryFieldName') is None:
                geometryFieldName = templateTable.GeometryFieldName
            else:
                geometryFieldName = None
                
            table = self.CreateTable(tableName, templateTable.GeometryType, templateTable.GetSpatialReference('Obj'), geometryFieldName, **options)
        else:
            table = self.CreateTable(tableName, options=options)

        # Add the fields.

        for field in sourceFields:
            table.AddField(field.Name, field.DataType, field.Length, field.Precision, field.IsNullable, allowSafeCoercions, False)

        # Return successfully.

        return table

    def ImportTable(self, destTableName, sourceTable, fields=None, where=None, orderBy=None, rowCount=None, reportProgress=True, rowDescriptionSingular=None, rowDescriptionPlural=None, copiedOIDFieldName=None, allowSafeCoercions=True, **options):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Create the destination table.
        
        destTable = self.CreateTableFromTemplate(destTableName, sourceTable, fields, allowSafeCoercions, **options)

        # If the caller requested that the OID field be copied from
        # the source table to a new field in the destination table,
        # add a field for that.

        if copiedOIDFieldName is not None:
            destTable.AddField(copiedOIDFieldName, 'int32', None, None, False, allowSafeCoercions, False)

        # If the caller specified a list of fields to copy, make sure
        # the list includes the OID and/or geometry fields, if they
        # are needed.

        if fields is not None:
            if copiedOIDFieldName is not None and sourceTable.OIDFieldName not in fields:
                fields.append(sourceTable.OIDFieldName)
            if destTable.GeometryType is not None and sourceTable.GeometryFieldName not in fields:
                fields.append(sourceTable.GeometryFieldName)

        # Otherwise create a list of fields to copy, removing the OID
        # and/or geometry fields, if they are not needed.

        else:
            fields = [field.Name for field in sourceTable.Fields]
            if copiedOIDFieldName is None and sourceTable.OIDFieldName is not None:
                fields.remove(sourceTable.OIDFieldName)
            if destTable.GeometryType is None and sourceTable.GeometryFieldName is not None:
                fields.remove(sourceTable.GeometryFieldName)

        # Open a select cursor on the source table and an insert
        # cursor on the destination table, and copy the rows.

        if rowCount is not None and rowCount == 0:
            message = _('Not copying any %(desc)s from %(dn1)s to %(dn2)s. The row count in %(dn1)s was 0.') % {'desc': selectCursor.RowDescriptionPlural, 'dn1': sourceTable.DisplayName, 'dn2': destTable.DisplayName}
            if reportProgress:
                self._LogInfo(message)
            else:
                self._LogDebug(message)

        else:
            selectCursor = sourceTable.OpenSelectCursor(fields, where, orderBy, rowCount, False, rowDescriptionSingular, rowDescriptionPlural)
            try:
                insertCursor = destTable.OpenInsertCursor(rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)
                try:
                    if rowCount is not None:
                        message = _('Copying %(rowCount)i %(desc)s from %(dn1)s to %(dn2)s.') % {'rowCount': rowCount, 'desc': selectCursor.RowDescriptionPlural, 'dn1': sourceTable.DisplayName, 'dn2': destTable.DisplayName}
                    else:
                        message = _('Copying %(desc)s from %(dn1)s to %(dn2)s.') % {'desc': selectCursor.RowDescriptionPlural, 'dn1': sourceTable.DisplayName, 'dn2': destTable.DisplayName}
                    if reportProgress:
                        self._LogInfo(message)
                    else:
                        self._LogDebug(message)
                    
                    while selectCursor.NextRow():
                        for field in fields:
                            if field == sourceTable.OIDFieldName:
                                insertCursor.SetValue(copiedOIDFieldName, selectCursor.GetOID())
                            elif field == sourceTable.GeometryFieldName:
                                insertCursor.SetGeometry(selectCursor.GetGeometry())
                            else:
                                insertCursor.SetValue(field, selectCursor.GetValue(field))
                        insertCursor.InsertRow()
                finally:
                    del insertCursor
            finally:
                del selectCursor

        # Return successfully.

        return destTable

    def DeleteTable(self, tableName, failIfNotExists=False):
        self.__doc__.Obj.ValidateMethodInvocation()

        self._RequireCapability('DeleteTable')

        if not self.TableExists(tableName):
            if failIfNotExists:
                raise RuntimeError(_('Cannot create %(objectType)s %(table)s in %(dn)s because that %(objectType)s already exists.') % {'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName})
            self._LogDebug(_('%(class)s 0x%(id)016X: Not deleting %(objectType)s %(table)s from %(dn)s because that %(objectType)s does not exist.'), {'class': self.__class__.__name__, 'id': id(self), 'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName})
            return

        self._LogDebug(_('%(class)s 0x%(id)016X: Deleting %(objectType)s %(table)s from %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'objectType': self._GetObjectTypeDisplayName(tableName), 'table': tableName, 'dn': self.DisplayName})

        try:
            self._DeleteTable(tableName)
        except Exception as e:
            raise RuntimeError(_('Failed to delete %(objectType)s %(tableName)s from %(dn)s due to %(e)s: %(msg)s.') % {'objectType': self._GetObjectTypeDisplayName(tableName), 'tableName': tableName, 'dn': self._DisplayName, 'e': e.__class__.__name__, 'msg': e})

    # Private members that the derived class must implement.

    def _GetObjectTypeDisplayName(self, tableName):
        return _('table')
    
    def _TableExists(self, tableName):
        raise RuntimeError(_('Programming error in this tool: The %(cls)s class does not define the Database._TableExists method. Please contact the author of this tool for assistance.') % {'cls': self.__class__.__name__})

    def _CreateTable(self, tableName, geometryType, spatialReference, geometryFieldName, options):
        raise RuntimeError(_('Programming error in this tool: The %(cls)s class does not define the Database._CreateTable method. Please contact the author of this tool for assistance.') % {'cls': self.__class__.__name__})

    def _DeleteTable(self, tableName):
        raise RuntimeError(_('Programming error in this tool: The %(cls)s class does not define the Database._DeleteTable method. Please contact the author of this tool for assistance.') % {'cls': self.__class__.__name__})


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
