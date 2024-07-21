# SQLite.py - Defines SQLiteDatabase and SQLiteTable.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import os
import sqlite3

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Types import UnicodeStringTypeMetadata

from . import QueryableAttribute, Database, Table, Field, SelectCursor, UpdateCursor, InsertCursor
from .Collections import DirectoryTree, FileDatasetCollection


class SQLiteDatabase(FileDatasetCollection, Database):
    __doc__ = DynamicDocString()

    def _GetConnection(self):
        self._Open()
        return self._Connection

    Connection = property(_GetConnection, doc=DynamicDocString())

    def __init__(self, path, timeout=5., isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES, decompressedFileToReturn=None, displayName=None, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Timeout = timeout
        self._IsolationLevel = isolation_level
        self._DetectTypes = detect_types
        self._CallerProvidedDisplayName = displayName is not None
        self._Connection = None

        if displayName is not None:
            self._DisplayName = displayName
        elif parentCollection is None:
            if path == ':memory:':
                self._DisplayName = _('SQLite in-memory database')
            else:
                self._DisplayName = _('SQLite database %(path)s') % {'path': path}
        elif isinstance(parentCollection, DirectoryTree):
            self._DisplayName = _('SQLite database %(path)s') % {'path': os.path.join(parentCollection.Path, path)}
        else:
            self._DisplayName = _('SQLite database %(path)s from %(parent)s') % {'path': path, 'parent': parentCollection.DisplayName}

        # We allow querying for tables by name. If the parent collection(s) or
        # the caller did not define the TableName queryable attributes, we
        # must define them.

        qa = []
        if queryableAttributes is not None:
            qa.extend(queryableAttributes)

        varNameAttr = None
        if parentCollection is not None:
            varNameAttr = parentCollection.GetQueryableAttribute('TableName')
        if varNameAttr is None:
            for attr in qa:
                if attr.Name == 'TableName':
                    varNameAttr = attr
                    break
        if varNameAttr is None:
            varNameAttr = QueryableAttribute('TableName', _('Table name'), UnicodeStringTypeMetadata())
            qa.append(varNameAttr)

        # Initialize the base class.
        
        super(SQLiteDatabase, self).__init__(path, decompressedFileToReturn, parentCollection, tuple(qa), queryableAttributeValues, lazyPropertyValues, cacheDirectory)

        # Validate that the caller has not assigned a value to the TableName
        # queryable attribute, either directly to us or to our parent
        # collection(s).

        if self.GetQueryableAttributeValue('TableName') is not None:
            raise ValueError(_('This SQLiteDatabase instance or its parent collection(s) specify a value for the TableName queryable attribute. This is not allowed, as the value of that queryable attribute is assigned by the SQLiteDatabase instance.'))

    # Overridden methods of CollectiableObject

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):
        return None

    def _Close(self):

        # If there is a connection open and it is NOT an in-memory database,
        # close it now. We close in-memory databases when the SQLiteDatabase
        # is destroyed rather than when _Close is called. This is because the
        # in-memory database only exists while the connection is open. We
        # allow our Close() to be called at any time, with the philosophy that
        # doing so will free up allocated resources but WITHOUT deleting the
        # underlying data. To prevent that from happening, we have to keep the
        # connection open.

        if hasattr(self, '_Connection') and self._Connection is not None and self._Path != ':memory:':
            self._LogDebug(_('%(class)s 0x%(id)016X: Closing %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
            self._Connection.close()
            self._Connection = None

        super(SQLiteDatabase, self)._Close()

    def __del__(self):

        # If there is a connection open, close it. Normally, we wouldn't need
        # to implement a __del__() to do this: CollectibleObject.__del__()
        # calls Close() automatically. But our _Close() does not close
        # connections to in-memory databases, so that their lifetimes are tied
        # to the SQLiteDatabase instance rather than the connection, allowing
        # our user to call Close() at any time without deleting the in-memory
        # database. So we have to explicitly close the connection here, which
        # will finally delete the in-memory database.

        if hasattr(self, '_Connection') and self._Connection is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Closing %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
            self._Connection.close()
            self._Connection = None

        super(SQLiteDatabase, self).__del__()

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['createtable', 'deletetable']:
            return None
        if isinstance(cls, SQLiteDatabase):
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__name__, 'cap': capability})

    # Private methods that DatasetCollectionTree expects us to implement

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):

        # Go through the list of tables available in this database, testing
        # whether each one matches the query expression. For each match,
        # construct a SQLiteTable instance. Ignore known system tables created
        # by SQLite or SpatiaLite.

        self._Open()
        tableNames = [row['name'] for row in self._Connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT GLOB 'idx_?*_?*' AND name NOT LIKE 'sqlite?_%' ESCAPE '?' AND name NOT IN ('spatial_ref_sys', 'spatialite_history', 'geometry_columns', 'views_geometry_columns', 'virts_geometry_columns', 'geometry_columns_auth', 'SpatialIndex')")]
        datasetsFound = []

        for i in range(len(tableNames)):
            if parsedExpression is not None:
                attrValues = {'TableName': tableNames[i]}
                attrValues.update(parentAttrValues)
                try:
                    result = parsedExpression.eval(attrValues)
                except Exception as e:
                    continue
            else:
                result = True

            if result is None or result:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for table %(tableName)s of %(dn)s: %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 'tableName': tableNames[i], 'dn': self.DisplayName, 'result': repr(result)})

            if result:
                datasetsFound.append(SQLiteTable(self, tableNames[i]))
                if progressReporter is not None:
                    progressReporter.ReportProgress()

        return datasetsFound

    def _ImportDatasets(self, datasets, mode, reportProgress, options):
        raise NotImplementedError(_('The _ImportDatasets method of class %s has not been implemented.') % self.__class__.__name__)

    # Private methods that DirectoryTree expects us to implement

    @classmethod
    def _RemoveExistingDatasetsFromList(cls, path, datasets, progressReporter):
        numDatasets = len(datasets)

        if path != ':memory:' and not os.path.exists(path):
            cls._LogDebug(_('%(class)s: SQLite database "%(path)s" does not exist.'), {'class': cls.__name__, 'path': path})
            while len(datasets) > 0:
                del datasets[0]
        else:
            try:
                conn = sqlite3.connect(path)
            except Exception as e:
                raise RuntimeError(_('The file %(path)s exists but it could not be opened as a SQLite database. Detailed error information: sqlite3.connect failed with %(e)s: %(msg)s.') % {'path': path, 'e': e.__class__.__name__, 'msg': e})

            try:
                i = 0
                while i < len(datasets):
                    tableName = datasets[i].GetQueryableAttributeValue('TableName')
                    if tableName is None:
                        if path == ':memory:':
                            raise RuntimeError(_('Cannot import %(dn)s into a SQLite in-memory database because that dataset does not have a value for the TableName queryable attribute. In order to import a dataset into a SQLite database, the dataset must have a value for that queryable attribute.') % {'dn': datasets[i].DisplayName})
                        raise RuntimeError(_('Cannot import %(dn)s into SQLite database %(path)s because that dataset does not have a value for the TableName queryable attribute. In order to import a dataset into a SQLite database, the dataset must have a value for that queryable attribute.') % {'dn': datasets[i].DisplayName, 'path': path})
                    
                    if conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name=?;", (tableName,)).fetchone()[0] > 0:
                        if path != ':memory:':
                            cls._LogDebug(_('%(class)s: Table %(table)s exists in SQLite database %(path)s.'), {'class': cls.__name__, 'table': tableName, 'path': path})
                        del datasets[i]
                    else:
                        i += 1
            finally:
                conn.close()

        if progressReporter is not None:
            progressReporter.ReportProgress(numDatasets)

    @classmethod
    def _ImportDatasetsToPath(cls, path, sourceDatasets, mode, progressReporter, options):

        # If path is not ":memory:" it is a file. If that file does not exist,
        # create the parent directories, if they do not exist already.

        if path != ':memory:' and not os.path.isfile(path) and (path[0] in ['/', '\\'] or hasattr(os.path, 'splitdrive') and os.path.splitdrive(path)[0] != '') and not os.path.isdir(os.path.dirname(path)):
            cls._LogDebug(_('%(class)s: Creating directory "%(path)s".'), {'class': cls.__name__, 'path': os.path.dirname(path)})
            try:
                os.makedirs(os.path.dirname(path))
            except Exception as e:
                raise RuntimeError(_('Failed to create directory "%(path)s". Python\'s os.makedirs function failed and reported %(e)s: %(msg)s') % {'path': os.path.dirname(path), 'e': e.__class__.__name__, 'msg': e})

        # Open the SQLite database. This will create it if it doesn't exist
        # already. Then import each dataset into it.

        database = SQLiteDatabase(path)
        try:
            for sourceTable in sourceDatasets:

                # Get the name of the table from the TableName queryable
                # attribute of the source table.

                tableName = sourceTable.GetQueryableAttributeValue('TableName')
                if tableName is None:
                    raise NotImplementedError(_('Cannot import %(src)s into %(dest)s because %(src)s does not have a queryable attribute named "TableName". Please contact the developer of this tool for assistance.') % {'src': dataset.DisplayName, 'dest': database.DisplayName})

                # If the mode is 'replace' and the table exists, delete it.
                # Note that if mode is 'add', our caller already removed
                # existing tables by calling _RemoveExistingDatasetsFromList.

                if mode == 'replace' and database.TableExists(tableName):
                    database.DeleteTable(tableName)

                # Our _CreateTable creates an auto-incrementing ObjectID field.
                # We can't populate this with the caller's ObjectID field. So
                # if the source table has an OID field called ObjectID, we
                # will rename it during the copy.

                fields = None
                copiedOIDFieldName = None

                if sourceTable.HasOID and (sourceTable.OIDFieldName is None or sourceTable.OIDFieldName.upper() == 'OBJECTID'):
                    copiedOIDFieldName = 'OriginalObjectID'
                    tries = 1
                    while sourceTable.GetFieldByName(copiedOIDFieldName) is not None:
                        copiedOIDFieldName = 'OriginalObjectID_%i' % tries
                        tries += 1

                # Otherwise, if the caller has a field named ObjectID that is
                # NOT the OID field, we can't copy it. Report a warning.

                elif sourceTable.GetFieldByName('ObjectID') is not None:
                    fieldsToCopy = [field.Name for field in sourceTable.Fields if field.Name.upper() != 'OBJECTID' and (sourceTable.GeometryFieldName is None or field.Name.upper() != sourceTable.GeometryFieldName.upper())]
                    self._LogWarning(('The field "%(field)s" from %(src)s will not be imported into the table %(tn)s in %(dest)s because that field name is already in use. This problem is a limitation of this tool; please contact the developer of this tool for assistance.') % {'field': sourceTable.GetFieldByName('ObjectID').Name, 'src': dataset.DisplayName, 'tn': tableName, 'dest': database.DisplayName})

                # Import the table.

                database.ImportTable(tableName, sourceTable, fields=fields, copiedOIDFieldName=copiedOIDFieldName, reportProgress=False, options=options)

                if progressReporter is not None:
                    progressReporter.ReportProgress()
        finally:
            database.Close()

    # Overridden methods of Database

    def _TableExists(self, tableName):
        self._Open()
        return self._Connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE name=?;", (tableName,)).fetchone()[0] > 0

    def _CreateTable(self, tableName, geometryType, spatialReference, geometryFieldName, options):

        # Create the table. The CREATE TABLE statement requires at least one
        # field to be specified but we do not know the names of any of the
        # fields the caller intends to create. We also do not know which
        # field--or fields--if any--will be the primary key. To work around
        # all of that, we take the same strategy as SpatiaLite does with FIDs
        # and OBJECTIDs: we define our own ObjectID field and make it an
        # autonumbering primary key.

        self._Open()
        sql = "CREATE TABLE %s (ObjectID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT);" % tableName
        self._LogDebug(_('%(class)s 0x%(id)016X: Executing: %(sql)s'), {'class': self.__class__.__name__, 'id': id(self), 'sql': sql})
        self._Connection.execute(sql)

        # Return a SQLiteTable instance for the new table.

        return SQLiteTable(self, tableName)

    def _DeleteTable(self, tableName):

        # Drop the table.
        
        self._Open()
        sql = "DROP TABLE %s;" % tableName
        self._LogDebug(_('%(class)s 0x%(id)016X: Executing: %(sql)s'), {'class': self.__class__.__name__, 'id': id(self), 'sql': sql})
        self._Connection.execute(sql)

    # Private methods

    def _Open(self):
        if self._Connection is None:

            # If the path is ':memory:', it references the in-memory database,
            # which is directly openable. If otherwise, it references a
            # database in a file. Get the openable path for this file. If the
            # file is part of a remote collection and/or compressed, this will
            # cause it to be downloaded and/or decompressed.

            if self.Path == ':memory:' or not os.path.exists(self.Path):
                path = self.Path
                isOriginalFile = True
            else:
                path, isOriginalFile = self._GetOpenableFile()

            # If the openable path is not the same as our original path,
            # update our display name to reflect it.

            if not isOriginalFile and not self._CallerProvidedDisplayName:
                if self.ParentCollection is None:
                    self._DisplayName = _('SQLite database %(path)s (decompressed from %(oldpath)s)') % {'path': path, 'oldpath': self.Path}
                elif isinstance(self.ParentCollection, DirectoryTree):
                    self._DisplayName = _('SQLite database %(path)s (decompressed from %(oldpath)s)') % {'path': path, 'oldpath': os.path.join(self.ParentCollection.Path, self.Path)}
                else:
                    self._DisplayName = _('SQLite database %(path)s (a local copy of %(oldpath)s from %(parent)s)') % {'path': path, 'oldpath': self.Path, 'parent': self.ParentCollection.DisplayName}

            # Open the database.

            self._LogDebug(_('%(class)s 0x%(id)016X: Opening %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})

            try:
                self._Connection = sqlite3.connect(path, timeout=self._Timeout, isolation_level=self._IsolationLevel, detect_types=self._DetectTypes)
            except Exception as e:
                raise RuntimeError(_('Failed to open %(dn)s. The file may not be in SQLite format. Detailed error information: sqlite3.connect failed with %(e)s: %(msg)s.') % {'dn': self._DisplayName, 'e': e.__class__.__name__, 'msg': e})

            self._RegisterForCloseAtExit()

            if self.Path == ':memory:':
                if not self._CallerProvidedDisplayName:
                    self._DisplayName = _('SQLite in-memory database 0x%(id)016X') % {'id': id(self._Connection)}
                    self._LogDebug(_('%(class)s 0x%(id)016X: Created new %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
                else:
                    self._LogDebug(_('%(class)s 0x%(id)016X: Created new SQLite in-memory database 0x%(id2)08X, hereafter referred to as "%(dn)s".'), {'class': self.__class__.__name__, 'id': id(self), 'id2': id(self._Connection), 'dn': self._DisplayName})

            # Use the SQLite Row class for the row_factory.
            
            self._Connection.row_factory = sqlite3.Row


class SQLiteTable(Table):
    __doc__ = DynamicDocString()

    def _GetTableName(self):
        return self._TableName

    TableName = property(_GetTableName, doc=DynamicDocString())

    def __init__(self, database, tableName, queryableAttributeValues=None, lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._TableName = tableName
        self._DisplayName = _('table %(name)s of %(dn)s') % {'name': tableName, 'dn': database.DisplayName}

        # Assign values to known queryable attributes.

        qav = {}
        if queryableAttributeValues is not None:
            qav.update(queryableAttributeValues)

        qav['TableName'] = tableName

        # Initialize the base class.

        super(SQLiteTable, self).__init__(database, queryableAttributeValues=qav, lazyPropertyValues=lazyPropertyValues)

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known lazy property, return None.

        if name not in ['HasOID', 'OIDFieldName', 'Fields']:
            return None

        # Enumerate the fields. If we find an integer field called ObjectID,
        # use it as the OID field.

        self.ParentCollection._Open()

        oidFieldName = None
        fields = []
        
        for row in self.ParentCollection._Connection.execute("PRAGMA table_info(%s);" % self._TableName):
            field = self._ConstructFieldObject(row)
            if field is not None:
                fields.append(field)
                if field.DataType == 'oid':
                    oidFieldName = field.Name
        
        self.SetLazyPropertyValue('HasOID', oidFieldName is not None)
        self.SetLazyPropertyValue('OIDFieldName', oidFieldName)
        self.SetLazyPropertyValue('Fields', fields)

        # Log a debug message.
        
        if self._DebugLoggingEnabled():
            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: HasOID=%(HasOID)s, OIDFieldName=%(OIDFieldName)s.'),
                           {'class': self.__class__.__name__,
                            'id': id(self),
                            'dn': self.DisplayName,
                            'HasOID': repr(self.GetLazyPropertyValue('HasOID')),
                            'OIDFieldName': repr(self.GetLazyPropertyValue('OIDFieldName'))})

            for i, f in enumerate(fields):
                self._LogDebug(_('%(class)s 0x%(id)016X: Field %(i)i: Name=%(Name)s, DataType=%(DataType)s, Length=%(Length)s, Precision=%(Precision)s, IsNullable=%(IsNullable)s, IsSettable=%(IsSettable)s.'),
                               {'class': self.__class__.__name__,
                                'id': id(self),
                                'i': i,
                                'Name': f.Name,
                                'DataType': f.DataType,
                                'Length': repr(f.Length),
                                'Precision': repr(f.Precision),
                                'IsNullable': repr(f.IsNullable),
                                'IsSettable': repr(f.IsSettable)})

        # Return the value of the requested property.

        return self.GetLazyPropertyValue(name)

    def _ConstructFieldObject(self, row):
        dataType = row['type'].lower()
        if dataType == 'integer':
            if row['name'].lower() == 'objectid':
                dataType = 'oid'
            else:
                dataType = 'int32'
        elif dataType == 'real':
            dataType = 'float64'
        elif dataType == 'text':
            dataType = 'string'
        elif dataType == 'blob':
            dataType = 'binary'
        elif dataType == 'date':
            dataType = 'date'
        elif dataType == 'timestamp':
            dataType = 'datetime'
        else:
            self._LogWarning(_('Field %(field)s of %(dn)s will be ignored because has the unknown data type "%(dt)s".') % {'field': row['name'], 'dn': self.DisplayName, 'dt': dataType})
            return None

        return Field(row['name'], dataType, None, None, isinstance(row['notnull'], (bool, int)) and not bool(row['notnull']), row['name'].lower() != 'objectid')

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['addfield', 'createindex', 'deleteindex', 'selectcursor', 'updatecursor', 'insertcursor', 'updaterow', 'deleterow']:
            return None

        if capability in ['int32 datatype', 'float64 datatype', 'string datatype', 'binary datatype', 'date datatype', 'datetime datatype']:
            return None

        if capability in ['int32 isnullable', 'float64 isnullable', 'string isnullable', 'binary isnullable', 'date isnullable', 'datetime isnullable']:
            return None

        if capability == 'deletefield':
            if isinstance(cls, SQLiteTable):
                return RuntimeError(_('Cannot delete a field from %(dn)s because SQLite does not allow fields to be deleted.') % {'dn': cls.DisplayName})
            return RuntimeError(_('Cannot delete fields from OGR layers because SQLite does not allow fields to be deleted.'))

        if isinstance(cls, SQLiteTable):
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__name__, 'cap': capability})

    def _AddField(self, name, dataType, length, precision, isNullable):
        if dataType == 'int32':
            sqlDataType = 'integer'
            default = '0'
        elif dataType == 'float64':
            sqlDataType = 'real'
            default = '0'
        elif dataType == 'string':
            sqlDataType = 'text'
            default = "''"
        elif dataType == 'binary':
            sqlDataType = 'blob'
            default = "X''"
        elif dataType == 'date':
            sqlDataType = 'date'
            default = "'0001-01-01'";
        elif dataType == 'datetime':
            sqlDataType = 'timestamp'
            default = "'0001-01-01 00:00:00'"
        else:
            raise NotImplementedError(_('The _AddField method of class %(cls)s does not support the %(dt)s data type.') % {'cls': self.__class__.__name__, 'dt': dataType})

        self.ParentCollection._Open()

        # If the field is not nullable we have to create it with a DEFAULT
        # constraint, regardless of whether there are any rows in the table.
        
        if isNullable:
            self.ParentCollection._Connection.execute("ALTER TABLE %s ADD COLUMN %s %s;" % (self._TableName, name, sqlDataType.upper()))
        else:
            self.ParentCollection._Connection.execute("ALTER TABLE %s ADD COLUMN %s %s NOT NULL DEFAULT %s;" % (self._TableName, name, sqlDataType.upper(), default))

        return Field(name, dataType, None, None, isNullable, True)

    def _CreateIndex(self, fields, indexName, unique, ascending):

        # Make sure the caller specified an index name.

        if indexName is None:
            raise ValueError(_('The index name must be provided.'))

        # Drop the existing index, if it exists.
        
        self.ParentCollection._Open()
        self.ParentCollection._Connection.execute("DROP INDEX IF EXISTS %s;" % (indexName))

        # Create the new index.

        self.ParentCollection._Connection.execute("CREATE %s INDEX %s ON %s (%s);" % ({False: '', True: 'UNIQUE'}[unique], indexName, self._TableName, ', '.join([field + {False: ' DESC', True: ' ASC'}[ascending] for field in fields])))

    def _DeleteIndex(self, indexName):

        # Make sure the caller specified an index name.

        if indexName is None:
            raise ValueError(_('The index name must be provided.'))

        # Drop the existing index, if it exists.
        
        self.ParentCollection._Open()
        self.ParentCollection._Connection.execute("DROP INDEX IF EXISTS %s;" % (indexName))

    def _GetRowCount(self):
        self.ParentCollection._Open()
        return self.ParentCollection._Connection.execute("SELECT COUNT(*) FROM %s;" % self._TableName).fetchone()[0]

    def _OpenSelectCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        return _SQLiteSelectCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    def _OpenUpdateCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        return _SQLiteUpdateCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    def _OpenInsertCursor(self, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        return _SQLiteInsertCursor(self, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)


class _SQLiteReadableCursor(object):

    def _NextRow(self):
        self._Row = self._Cursor.fetchone()
        self._RowValues = {}
        if hasattr(self, '_SetFields'):
            self._SetFields = set()
        return self._Row is not None

    def _GetValue(self, field):
        if field not in self._RowValues:
            value = self._Row[str(field)]
            self._RowValues[field] = value
        return self._RowValues[field]

    def _GetOID(self):
        return self._GetValue(self._Table.OIDFieldName)


class _SQLiteWritableCursor(object):

    def _SetValue(self, field, value):
        self._RowValues[field] = value
        self._SetFields.add(field)
        

class _SQLiteSelectCursor(_SQLiteReadableCursor, SelectCursor):
    __doc__ = DynamicDocString()

    def _Open(self, fields, where, orderBy):
        self._Cursor = None
        self._Row = None
        self._RowValues = None

        # Build the SQL SELECT statement from the caller's parameters.

        if fields is None:
            sql = 'SELECT *'
        else:
            sql = 'SELECT %s' % ', '.join(fields)

        sql += ' FROM %s' % self._Table.TableName

        if where is not None:
            sql += ' WHERE ' + where

        if orderBy is not None:
            sql += ' ORDER BY ' + orderBy
            
        # Open the cursor.

        self._Cursor = self._Table.ParentCollection._Connection.execute(sql)

    def _Close(self):
        self._Row = None
        self._RowValues = None
        if hasattr(self, '_Cursor') and self._Cursor is not None:
            try:
                self._Cursor.close()
            except:
                pass
        self._Cursor = None
        super(_SQLiteSelectCursor, self)._Close()


class _SQLiteUpdateCursor(_SQLiteReadableCursor, _SQLiteWritableCursor, UpdateCursor):
    __doc__ = DynamicDocString()

    def _Open(self, fields, where, orderBy):
        self._Cursor = None
        self._Row = None
        self._RowValues = None
        self._SetFields = None

        # Build the SQL SELECT statement from the caller's parameters.
        #
        # In order to update the current row returned by the SELECT, we need
        # the ObjectID. (Note that this is an alias for SQLite's special ROWID
        # column; see the SQLite documentation for CREATE TABLE, under the
        # heading "ROWIDs and the INTEGER PRIMARY KEY".

        if fields is None:
            sql = 'SELECT *'
        else:
            if self._Table.OIDFieldName not in fields:
                fields = fields + [self._Table.OIDFieldName]
            sql = 'SELECT %s' % ', '.join(fields)

        sql += ' FROM %s' % self._Table.TableName

        if where is not None:
            sql += ' WHERE ' + where

        if orderBy is not None:
            sql += ' ORDER BY ' + orderBy
            
        # Open the cursor.

        self._Cursor = self._Table.ParentCollection._Connection.execute(sql)

    def _Close(self):
        self._Row = None
        self._RowValues = None
        self._SetFields = None
        if hasattr(self, '_Cursor') and self._Cursor is not None:
            try:
                self._Cursor.close()
            except:
                pass
        self._Cursor = None
        super(_SQLiteSelectCursor, self)._Close()

    def _UpdateRow(self):

        # Only execute the UPDATE statement some fields have been set.

        if len(self._SetFields) > 0:

            # Build the SQL UPDATE statement.

            fieldsToSet = list(self._SetFields)
            valueStrings = ['?'] * len(self._SetFields)

            sql = 'UPDATE %s SET %s WHERE ObjectID = %s' % (self._Table.TableName, ', '.join([fieldsToSet[i] + ' = ' + valueStrings[i] for i in range(len(fieldsToSet))]), self._GetValue(self._Table.OIDFieldName))

            # Update the row.

            self._Table.ParentCollection._Connection.execute(sql, [self._RowValues[field] for field in fieldsToSet])

        self._Row = None

    def _DeleteRow(self):
        self._Table.ParentCollection._Connection.execute('DELETE FROM %s WHERE %s = %s' % (self._Table.TableName, self._Table.OIDFieldName, self._Row[self._Table.OIDFieldName]))
        self._Row = None


class _SQLiteInsertCursor(_SQLiteWritableCursor, InsertCursor):
    __doc__ = DynamicDocString()

    def _Open(self):
        self._RowValues = {}
        self._SetFields = set()

    def _Close(self):
        self._RowValues = None
        self._SetFields = None
        super(_SQLiteInsertCursor, self)._Close()

    def _InsertRow(self):

        # Build the SQL INSERT statement. If no fields have been set, try the
        # DEFAULT VALUES syntax. This will succeed if all of the fields are
        # nullable.
        
        if len(self._SetFields) <= 0:
            sql = 'INSERT INTO %s DEFAULT VALUES' % self._Table.TableName

        # Otherwise, we have to use the normal INSERT syntax.

        else:
            fieldsToSet = list(self._SetFields)
            valueStrings = ['?'] * len(self._SetFields)

            sql = 'INSERT INTO %s (%s) VALUES (%s)' % (self._Table.TableName, ', '.join(fieldsToSet), ', '.join(valueStrings))

        # Insert the row.
        
        self._Table.ParentCollection._Connection.execute(sql, [self._RowValues[field] for field in fieldsToSet])
        self._RowValues = {}
        self._SetFields = set()


###############################################################################
# Metadata: module
###############################################################################

from ..Metadata import *
from ..Types import *

AddModuleMetadata(shortDescription=_('A :class:`~GeoEco.Datasets.Table` for accessing SQLite tables accessible through Python\'s built in :py:mod:`sqlite3` module.'),
    longDescription=(
"""
This example shows how to create an in-memory database, create a table within
it, and add some fields:

.. code-block:: python

    from GeoEco.Datasets.SQLite import SQLiteDatabase

    db = SQLiteDatabase(':memory:')
    table = db.CreateTable('TempTable1')

    table.AddField('FloatField', 'float64')
    table.AddField('IntField', 'int32')
    table.AddField('StrField', 'string', isNullable=True)
    table.AddField('DateTimeField', 'datetime')

    for field in table.Fields:
        print(field.Name, field.DataType, field.IsNullable)

Output:

.. code-block:: text

    ObjectID oid False
    FloatField float64 False
    IntField int32 False
    StrField string True
    DateTimeField datetime False

Continuing from above, let's insert some data with
:meth:`SQLiteTable.OpenInsertCursor`:

.. code-block:: python

    from datetime import datetime

    with table.OpenInsertCursor() as cursor:
        cursor.SetValue('FloatField', 1.1)
        cursor.SetValue('IntField', 1)
        cursor.SetValue('StrField', 'abc')
        cursor.SetValue('DateTimeField', datetime(2000, 1, 2, 3, 4, 5))
        cursor.InsertRow()
        cursor.SetValue('FloatField', 2.2)
        cursor.SetValue('IntField', 2)
        cursor.SetValue('StrField', 'def')
        cursor.SetValue('DateTimeField', datetime(2000, 6, 7, 8, 9, 10))
        cursor.InsertRow()
        cursor.SetValue('FloatField', 3.3)
        cursor.SetValue('IntField', 3)
        cursor.SetValue('StrField', None)
        cursor.SetValue('DateTimeField', datetime(2000, 11, 12, 13, 14, 15))
        cursor.InsertRow()

And read it back using :meth:`SQLiteTable.OpenSelectCursor`:

.. code-block:: python

    with table.OpenSelectCursor() as cursor:
        while cursor.NextRow():
            print(', '.join([f'{field.Name} = {cursor.GetValue(field.Name)}' for field in table.Fields]))

Output:

.. code-block:: text

    ObjectID = 1, FloatField = 1.1, IntField = 1, StrField = abc, DateTimeField = 2000-01-02 03:04:05
    ObjectID = 2, FloatField = 2.2, IntField = 2, StrField = def, DateTimeField = 2000-06-07 08:09:10
    ObjectID = 3, FloatField = 3.3, IntField = 3, StrField = None, DateTimeField = 2000-11-12 13:14:15

Read it back using :meth:`SQLiteTable.Query()`, which returns a :py:class:`dict`:

.. code-block:: python

    for field, values in table.Query().items():
        print(f'{field}: {values!r}')

Output:

.. code-block:: text

    ObjectID: [1, 2, 3]
    FloatField: [1.1, 2.2, 3.3]
    IntField: [1, 2, 3]
    StrField: ['abc', 'def', None]
    DateTimeField: [datetime.datetime(2000, 1, 2, 3, 4, 5), datetime.datetime(2000, 6, 7, 8, 9, 10), datetime.datetime(2000, 11, 12, 13, 14, 15)]

Read it back into a :class:`pandas.DataFrame`:

.. code-block:: python

    import pandas as pd

    df = pd.DataFrame(table.Query())
    print(df)
    print('')

Output:

.. code-block:: python

       ObjectID  FloatField  IntField StrField       DateTimeField
    0         1         1.1         1      abc 2000-01-02 03:04:05
    1         2         2.2         2      def 2000-06-07 08:09:10
    2         3         3.3         3     None 2000-11-12 13:14:15

Let's use :meth:`SQLiteTable.OpenUpdateCursor()` to delete the second row and 
update the values of the third row. :meth:`~SQLiteTable.OpenUpdateCursor()`,
:meth:`~SQLiteTable.OpenSelectCursor()`, and :meth:`~SQLiteTable.Query()`, all
support "where" and "order by" expressions to filter and order the rows. We'll
use "where" here to skip the first row.

.. code-block:: python

    with table.OpenUpdateCursor(where='ObjectID >= 2') as cursor:
        cursor.NextRow()
        cursor.DeleteRow()

        cursor.NextRow()
        cursor.SetValue('FloatField', 3.333)
        cursor.SetValue('StrField', 'ghi')
        cursor.UpdateRow()

    print(pd.DataFrame(table.Query()))

Output:

.. code-block:: text

       ObjectID  FloatField  IntField StrField       DateTimeField
    0         1       1.100         1      abc 2000-01-02 03:04:05
    1         3       3.333         3      ghi 2000-11-12 13:14:15
"""))

###############################################################################
# Metadata: SQLiteDatabase class
###############################################################################

AddClassMetadata(SQLiteDatabase,
    shortDescription=_('A :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` and :class:`~GeoEco.Datasets.Database` representing a SQLite database.'))

# Public properties

AddPropertyMetadata(SQLiteDatabase.Connection, 
    typeMetadata=ClassInstanceTypeMetadata(cls=sqlite3.Connection),
    shortDescription=_(':py:class:`sqlite3.Connection` object that :class:`SQLiteDatabase` is using to interact with the database.'))

# Public constructor: SQLiteDatabase.__init__

AddMethodMetadata(SQLiteDatabase.__init__,
    shortDescription=_('SQLiteDatabase constructor.'))

AddArgumentMetadata(SQLiteDatabase.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=SQLiteDatabase),
    description=_(':class:`%s` instance.') % SQLiteDatabase.__name__)

AddArgumentMetadata(SQLiteDatabase.__init__, 'path',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Database to open. This can either be ':memory:', indicating that a new
in-memory database should be opened, or a file.

If it is a file and and there is no parent collection, this is the full path
to the file. It will be opened as stand-alone collection.

If there is a parent collection, this path is relative to it. For example, if
the parent collection is a :class:`~GeoEco.Datasets.Collections.DirectoryTree`,
this path is relative to a leaf directory of the
:class:`~GeoEco.Datasets.Collections.DirectoryTree`. Often, the leaf directory
will be the one containing the file, in which case the path provided here will
simply be the name of the file.

If the path points to compressed file, it will be decompressed automatically.
If a cache directory is provided, it will be checked first for an existing
decompressed file. If none is found the file will be decompressed there.

If the compressed file is an archive (e.g. .zip or .tar), you must also
specify a decompressed file to return.

"""))

AddArgumentMetadata(SQLiteDatabase.__init__, 'timeout',
    typeMetadata=FloatTypeMetadata(minValue=0.),
    description=_(
"""When a database is accessed by multiple connections, and one of the
processes modifies the database, the SQLite database is locked until that
transaction is committed. This parameter specifies how long the connection
should wait for the lock to go away until raising an exception."""))

AddArgumentMetadata(SQLiteDatabase.__init__, 'isolation_level',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['DEFERRED', 'IMMEDIATE', 'EXCLUSIVE']),
    description=_(
"""SQLite isolation level to use, either :py:data:`None` for autocommit mode
(the default), or ``'DEFERRED'``, ``'IMMEDIATE'``, or ``'EXCLUSIVE'``. If you
specify one of these, a transaction will be started for you automatically
according to `SQLite's rules
<https://www.sqlite.org/lang_transaction.html#deferred_immediate_and_exclusive_transactions>`_.
Performing many updates or inserts in a transaction rather than with
autocommit mode can result in higher performance. However, when you are done,
you must explicitly commit the transaction by calling
:py:meth:`~sqlite3.Connection.commit` on :attr:`Connection`. To rollback the
transaction, call :py:meth:`~sqlite3.Connection.rollback`.

Warning:
    Neither :class:`SQLiteDatabase` nor :class:`SQLiteTable` will ever commit
    a transaction for you. If you open a connection with an `isolation_level`
    other than :py:data:`None`, and you do not explicitly commit the
    transaction, it will be implicitly rolled back by Python when the
    connection is closed, and your changes will be lost.

"""))

AddArgumentMetadata(SQLiteDatabase.__init__, 'detect_types',
    typeMetadata=IntegerTypeMetadata(),
    description=_(
"""Controls whether SQLite will detect and convert custom types other than the
natively-supported types TEXT, INTEGER, FLOAT, BLOB and NULL.

By default, this is set to :py:data:`sqlite3.PARSE_DECLTYPES` |
:py:data:`sqlite3.PARSE_COLNAMES`, which enables type detection and
conversion. The underlying Python :py:mod:`sqlite3` module automatically
supports conversion of the "date" datatype to :py:class:`datetime.date` and
"timestamp" data type to :py:class:`datetime.datetime`. You can enable
detection and conversion of additional types by registering adapters and
convertors with :py:mod:`sqlite3` prior to connecting to the database. See the
:py:mod:`sqlite3` documentation for more information.

Set this to ``0`` to disable type detection and conversion."""))

CopyArgumentMetadata(FileDatasetCollection.__init__, 'decompressedFileToReturn', SQLiteDatabase.__init__, 'decompressedFileToReturn')

AddArgumentMetadata(SQLiteDatabase.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Informal name of this database to be displayed to the user. If you
do not provide a name, a suitable name will be created
automatically."""))

CopyArgumentMetadata(FileDatasetCollection.__init__, 'parentCollection', SQLiteDatabase.__init__, 'parentCollection')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributes', SQLiteDatabase.__init__, 'queryableAttributes')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributeValues', SQLiteDatabase.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'lazyPropertyValues', SQLiteDatabase.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'cacheDirectory', SQLiteDatabase.__init__, 'cacheDirectory')

AddResultMetadata(SQLiteDatabase.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=SQLiteDatabase),
    description=_(':class:`%s` instance.') % SQLiteDatabase.__name__)


###############################################################################
# Metadata: SQLiteTable class
###############################################################################

AddClassMetadata(SQLiteTable,
    shortDescription=_('A :class:`~GeoEco.Datasets.Table` representing a SQLite table.'))

# Public properties

AddPropertyMetadata(SQLiteTable.TableName, 
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Name of the table.'))

# Public constructor: SQLiteTable.__init__

AddMethodMetadata(SQLiteTable.__init__,
    shortDescription=_('SQLiteTable constructor.'))

AddArgumentMetadata(SQLiteTable.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=SQLiteTable),
    description=_(':class:`%s` instance.') % SQLiteTable.__name__)

AddArgumentMetadata(SQLiteTable.__init__, 'database',
    typeMetadata=ClassInstanceTypeMetadata(cls=SQLiteDatabase),
    description=_(':class:`%s` instance that is the parent of this :class:`%s` instance.') % (SQLiteDatabase.__name__, SQLiteTable.__name__))

AddArgumentMetadata(SQLiteTable.__init__, 'tableName',
    typeMetadata=SQLiteTable.TableName.__doc__.Obj.Type,
    description=SQLiteTable.TableName.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(Table.__init__, 'queryableAttributeValues', SQLiteTable.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(Table.__init__, 'lazyPropertyValues', SQLiteTable.__init__, 'lazyPropertyValues')

AddResultMetadata(SQLiteTable.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=SQLiteTable),
    description=_(':class:`%s` instance.') % SQLiteTable.__name__)


# In order for the validation code to work for _SQLiteSelectCursor,
# _SQLiteUpdateCursor, and _SQLiteInsertCursor, they must have a ClassMetadata
# defined for them.

AddClassMetadata(_SQLiteSelectCursor,
    shortDescription=_('Private class representing a :class:`~GeoEco.Datasets.SelectCursor` for a :class:`SQLiteTable`. Not intended to be instantiated by callers outside GeoEco.'))

AddClassMetadata(_SQLiteUpdateCursor,
    shortDescription=_('Private class representing an :class:`~GeoEco.Datasets.UpdateCursor` for a :class:`SQLiteTable`. Not intended to be instantiated by callers outside GeoEco.'))

AddClassMetadata(_SQLiteInsertCursor,
    shortDescription=_('Private class representing an :class:`~GeoEco.Datasets.InsertCursor` for a :class:`SQLiteTable`. Not intended to be instantiated by callers outside GeoEco.'))


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['SQLiteDatabase',
           'SQLiteTable']
