# _ArcGISTable.py - Defines ArcGISTable, a Table for accessing ArcGIS tabular
# and vector datasets through arcpy.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import os

from ...ArcGIS import GeoprocessorManager
from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Types import UnicodeStringTypeMetadata

from .. import Dataset, QueryableAttribute, Table, Field, SelectCursor, UpdateCursor, InsertCursor


class ArcGISCopyableTable(object):
    __doc__ = DynamicDocString()

    def GetArcGISCopyablePath(self):
        raise NotImplementedError(_('The GetArcGISCopyablePath method of class %s has not been implemented.') % self.__class__.__name__)


class ArcGISTable(Table, ArcGISCopyableTable):
    __doc__ = DynamicDocString()
 
    def _GetPath(self):
        return self._Path

    Path = property(_GetPath, doc=DynamicDocString())

    def _GetArcGISDataType(self):
        return self.GetLazyPropertyValue('ArcGISDataType')

    ArcGISDataType = property(_GetArcGISDataType, doc=DynamicDocString())

    def _GetArcGISPhysicalDataType(self):
        return self.GetLazyPropertyValue('ArcGISPhysicalDataType')

    ArcGISPhysicalDataType = property(_GetArcGISPhysicalDataType, doc=DynamicDocString())

    def _GetAutoDeleteFieldAddedByArcGIS(self):
        return self._AutoDeleteFieldAddedByArcGIS

    AutoDeleteFieldAddedByArcGIS = property(_GetAutoDeleteFieldAddedByArcGIS, doc=DynamicDocString())

    def __init__(self, path, autoDeleteFieldAddedByArcGIS=False, parentCollection=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Path = path
        
        if parentCollection is None:
            self._DisplayName = _('ArcGIS table "%(path)s"') % {'path': path}
        else:
            self._DisplayName = _('ArcGIS table "%(path)s"') % {'path': os.path.join(parentCollection.Path, path)}

        self._AutoDeleteFieldAddedByArcGIS = autoDeleteFieldAddedByArcGIS
        self._DeletedFieldAddedByArcGIS = False

        # Assign values to known queryable attributes.

        queryableAttributes = (QueryableAttribute('TableName', _('Table name'), UnicodeStringTypeMetadata()),) if parentCollection is None or parentCollection.GetQueryableAttribute('TableName') is None else None

        qav = {}
        if queryableAttributeValues is not None:
            qav.update(queryableAttributeValues)

        qav['TableName'] = os.path.split(path)[-1]

        # Initialize the base class.
        
        super(ArcGISTable, self).__init__(parentCollection=parentCollection, queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues)

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetFullPath(self):
        if self.ParentCollection is None:
            return self._Path
        return os.path.join(self.ParentCollection.Path, self._Path)

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known lazy property, return None.

        if name not in ['SpatialReference', 'HasOID', 'OIDFieldName', 'GeometryType', 'GeometryFieldName', 'MaxStringLength', 'Fields', 'ArcGISDataType', 'ArcGISPhysicalDataType']:
            return None

        # Get the geoprocessor Describe object for this dataset and verify
        # that it is a table.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        path = self._GetFullPath()
        
        if not gp.Exists(path):
            if os.path.splitext(path)[1].lower() not in ['.shp', '.dbf'] and os.path.isdir(os.path.dirname(path)) and gp.Describe(os.path.dirname(path)).DataType.lower() in ['workspace', 'folder']:
                if gp.Exists(path + '.shp'):
                    path = path + '.shp'
                    self._Path = self._Path + '.shp'
                elif gp.Exists(path + '.dbf'):
                    path = path + '.dbf'
                    self._Path = self._Path + '.dbf'
                else:
                    raise ValueError(_('Failed to open ArcGIS table "%(path)s". ArcGIS reports that it does not exist.') % {'path': path})
            else:
                raise ValueError(_('Failed to open ArcGIS table "%(path)s". ArcGIS reports that it does not exist.') % {'path': path})

        d = gp.Describe(path)
        if not hasattr(d, 'Fields') or d.Fields is None or len(d.Fields) <= 0:
            raise ValueError(_('Failed to open ArcGIS dataset "%(path)s" as a table. ArcGIS reports that this object does not have any fields, therefore it cannot be accessed as a table.') % {'path': path})

        # Get the ArcGIS data type of this table and the data type of its
        # catalog path and set the display name to something more descriptive.

        arcGISDataType = d.DataType
        if gp.Exists(d.CatalogPath):
            arcGISPhysicalDataType = gp.Describe(d.CatalogPath).DataType
        else:
            arcGISPhysicalDataType = arcGISDataType
        
        self.SetLazyPropertyValue('ArcGISDataType', arcGISDataType)
        self.SetLazyPropertyValue('ArcGISPhysicalDataType', arcGISPhysicalDataType)

        if arcGISDataType == arcGISPhysicalDataType:
            self._DisplayName = _('ArcGIS %(dt)s "%(path)s"') % {'dt': arcGISDataType, 'path': path}
        else:
            self._DisplayName = _('ArcGIS %(dt)s "%(path)s" of %(pdt)s "%(cp)s"') % {'dt': arcGISDataType, 'path': path, 'pdt': arcGISPhysicalDataType, 'cp': d.CatalogPath}

        # Try to determine properties of the workspace that contains this
        # table. This allows us to implement certain hacks based on the
        # workspace.

        workspacePath = os.path.dirname(d.CatalogPath)
        try:
            dWorkspace = gp.Describe(workspacePath)
            if dWorkspace.DataType.lower() == 'workspace':
                self.SetLazyPropertyValue('workspaceType', dWorkspace.workspaceType)
                self.SetLazyPropertyValue('workspaceFactoryProgID', dWorkspace.workspaceFactoryProgID)
        except:
            pass

        # Get the rest of the lazy properties.

        if hasattr(d, 'OIDFieldName') and isinstance(d.OIDFieldName, str) and len(d.OIDFieldName) > 0:
            self.SetLazyPropertyValue('HasOID', True)
            self.SetLazyPropertyValue('OIDFieldName', d.OIDFieldName)
        else:
            self.SetLazyPropertyValue('HasOID', False)
            self.SetLazyPropertyValue('OIDFieldName', None)

        geometryType = None
        geometryFieldName = None
        
        if hasattr(d, 'ShapeFieldName') and isinstance(d.ShapeFieldName, str) and len(d.ShapeFieldName) > 0:
            geometryFieldName = d.ShapeFieldName
            shapeType = d.ShapeType.lower()
            if shapeType == 'point':
                if hasattr(d, 'HasZ') and bool(d.HasZ):
                    geometryType = 'Point25D'
                else:
                    geometryType = 'Point'
            elif shapeType == 'multipoint':
                if hasattr(d, 'HasZ') and bool(d.HasZ):
                    geometryType = 'MultiPoint25D'
                else:
                    geometryType = 'MultiPoint'
            elif shapeType == 'polyline':
                if hasattr(d, 'HasZ') and bool(d.HasZ):
                    geometryType = 'MultiLineString25D'
                else:
                    geometryType = 'MultiLineString'
            elif shapeType == 'polygon':
                if hasattr(d, 'HasZ') and bool(d.HasZ):
                    geometryType = 'MultiPolygon25D'
                else:
                    geometryType = 'MultiPolygon'
            else:
                self._LogWarning(_('The %(dn)s has an unsupported shape type "%(st)s". Geometry will not be available for this dataset.'), {'dn': self._DisplayName, 'st': d.ShapeType})
                geometryFieldName = None

        self.SetLazyPropertyValue('GeometryType', geometryType)
        self.SetLazyPropertyValue('GeometryFieldName', geometryFieldName)
        
        if geometryType is not None:
            self.SetLazyPropertyValue('SpatialReference', Dataset.ConvertSpatialReference('arcgis', gp.CreateSpatialReference_management(d.SpatialReference).getOutput(0).split(';')[0], 'obj'))
        else:
            self.SetLazyPropertyValue('SpatialReference', None)

        if arcGISDataType.lower() in ['dbasetable', 'textfile', 'shapefile']:
            self.SetLazyPropertyValue('MaxStringLength', 254)
        elif arcGISDataType.lower() == 'arcinfotable':
            self.SetLazyPropertyValue('MaxStringLength', 320)
        else:
            self.SetLazyPropertyValue('MaxStringLength', None)

        # Get the fields.

        fields = []

        for f in d.Fields:
            fields.append(self._ConstructFieldObject(f))

        self.SetLazyPropertyValue('Fields', tuple(fields))

        # Log a debug message.
        
        if self._DebugLoggingEnabled():
            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: ArcGISDataType=%(ArcGISDataType)s, ArcGISPhysicalDataType=%(ArcGISPhysicalDataType)s, MaxStringLength=%(MaxStringLength)s, HasOID=%(HasOID)s, OIDFieldName=%(OIDFieldName)s, GeometryType=%(GeometryType)s, GeometryFieldName=%(GeometryFieldName)s, SpatialReference=%(SpatialReference)s.'),
                           {'class': self.__class__.__name__,
                            'id': id(self),
                            'dn': self.DisplayName,
                            'ArcGISDataType': self.GetLazyPropertyValue('ArcGISDataType'),
                            'ArcGISPhysicalDataType': self.GetLazyPropertyValue('ArcGISPhysicalDataType'),
                            'MaxStringLength': repr(self.GetLazyPropertyValue('MaxStringLength')),
                            'HasOID': repr(self.GetLazyPropertyValue('HasOID')),
                            'OIDFieldName': repr(self.GetLazyPropertyValue('OIDFieldName')),
                            'GeometryType': repr(self.GetLazyPropertyValue('GeometryType')),
                            'GeometryFieldName': repr(self.GetLazyPropertyValue('GeometryFieldName')),
                            'SpatialReference': repr(Dataset.ConvertSpatialReference('obj', self.GetLazyPropertyValue('SpatialReference'), 'arcgis'))})

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

    def _ConstructFieldObject(self, f):
        dataType = f.type.lower()
        if dataType == 'oid':
            dataType = 'oid'
        elif dataType == 'geometry':
            dataType = 'geometry'
        elif dataType == 'smallinteger':
            dataType = 'int16'
        elif dataType == 'integer':
            dataType = 'int32'
        elif dataType == 'single':
            dataType = 'float32'
        elif dataType == 'double':
            dataType = 'float64'
        elif dataType == 'string':
            dataType = 'string'
        elif dataType == 'date':
            if self.ArcGISDataType.lower() in ['dbasetable', 'shapefile', 'arcinfotable']:
                dataType = 'date'
            else:
                dataType = 'datetime'
        elif dataType == 'blob':
            dataType = 'binary'
        else:
            dataType = 'unknown'
        isNullable = f.isNullable
        isNullable = isinstance(isNullable, (bool, int)) and bool(isNullable) or isinstance(isNullable, str) and isNullable.lower() == 'true'
        isSettable = dataType != 'oid' and not (f.name.lower() in ['shape_length', 'shape.stlength()'] and self.GetLazyPropertyValue('GeometryType') in ['MultiLineString', 'MultiLineString25D', 'MultiPolygon', 'MultiPolygon25D']) and not (f.name.lower() in ['shape_area', 'shape.starea()'] and self.GetLazyPropertyValue('GeometryType') in ['MultiPolygon', 'MultiPolygon25D'])
        return Field(f.name, dataType, f.length, f.precision, isNullable, isSettable)

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['setspatialreference', 'addfield', 'deletefield', 'createindex', 'deleteindex', 'selectcursor', 'updatecursor', 'insertcursor', 'updaterow', 'deleterow']:
            return None

        if capability in ['int16 datatype', 'int32 datatype', 'float32 datatype', 'float64 datatype', 'string datatype']:
            return None

        if capability == 'date datatype':
            if isinstance(cls, ArcGISTable) and cls.ArcGISPhysicalDataType.lower() not in ['shapefile', 'dbftable', 'arcinfotable']:
                return TypeError(_('Cannot create a field of data type "date" in %(dn)s because that data type is not supported by the ArcGIS %(dt)s data format. The ArcGIS %(dt)s data format can store dates with times, but not dates without times. Try the data type "datetime" instead.') % {'dn': cls.DisplayName, 'dt': cls.ArcGISPhysicalDataType})
            return None

        if capability == 'datetime datatype':
            if isinstance(cls, ArcGISTable) and cls.ArcGISPhysicalDataType.lower() in ['shapefile', 'dbftable', 'arcinfotable']:
                return TypeError(_('Cannot create a field of data type "datetime" in %(dn)s because that data type is not supported by the ArcGIS %(dt)s data format. The ArcGIS %(dt)s can store dates, but not dates with times. Try the data type "date" instead.') % {'dn': cls.DisplayName, 'dt': cls.ArcGISPhysicalDataType})
            return None

        if capability == 'binary datatype':
            if isinstance(cls, ArcGISTable) and cls.ArcGISPhysicalDataType.lower() in ['shapefile', 'dbftable', 'arcinfotable']:
                return TypeError(_('Cannot create a field of data type "binary" in %(dn)s because that data type is not supported by the ArcGIS %(dt)s data format.') % {'dn': cls.DisplayName, 'dt': cls.ArcGISPhysicalDataType})
            return None

        if capability.endswith(' datatype'):
            if isinstance(cls, ArcGISTable):
                return TypeError(_('Cannot create a field of data type "%(dt)s" in %(dn)s because that data type is not supported by the ArcGIS %(dt2)s data format.') % {'dt': capability.split()[0], 'dn': cls.DisplayName, 'dt2': cls.ArcGISPhysicalDataType})
            else:
                return TypeError(_('Cannot create a field of data type "%(dt)s" because that data type is not supported by ArcGIS.') % {'dt': capability.split()[0]})

        if capability.endswith(' isnullable'):
            if isinstance(cls, ArcGISTable) and cls.ArcGISPhysicalDataType.lower() in ['shapefile', 'dbftable'] and not capability.startswith('date '):
                return TypeError(_('Cannot create a nullable field in %(dn)s because the ArcGIS %(dt)s data format does not support null values, except in date fields.') % {'dn': cls.DisplayName, 'dt': cls.ArcGISPhysicalDataType})
            return None

        if isinstance(cls, ArcGISTable):
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__name__, 'cap': capability})

    @classmethod
    def _GetSRTypeForSetting(cls):
        return 'ArcGIS'

    def _SetSpatialReference(self, sr):
        GeoprocessorManager.GetWrappedGeoprocessor().DefineProjection_management(self._GetFullPath(), sr)

    def GetArcGISCopyablePath(self):
        return self._GetFullPath()

    def _AddField(self, name, dataType, length, precision, isNullable):
        if dataType == 'int16':
            dataType = 'SHORT'
        elif dataType == 'int32':
            dataType = 'LONG'
        elif dataType == 'float32':
            dataType = 'FLOAT'
        elif dataType == 'float64':
            dataType = 'DOUBLE'
        elif dataType == 'string':
            dataType = 'TEXT'
        elif dataType == 'date' or dataType == 'datetime':
            dataType = 'DATE'
        elif dataType == 'binary':
            dataType = 'BLOB'
        else:
            raise NotImplementedError(_('The _AddField method of class %(cls)s does not support the %(dt)s data type.') % {'cls': self.__class__.__name__, 'dt': dataType})

        if dataType not in ['SHORT', 'LONG', 'FLOAT', 'DOUBLE']:
            precision = None

        if dataType not in ['TEXT', 'BLOB']:
            length = None

        if isNullable:
            isNullable = 'NULLABLE'
        else:
            isNullable = 'NON_NULLABLE'

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        newName = gp.ValidateFieldName(name, os.path.dirname(self._GetFullPath()))
        if newName != name:
            raise ValueError(_('The name "%(name)s" is prohibited by either ArcGIS or the underlying database or file format. ArcGIS suggested the name "%(newName)s" instead.') % {'name': name, 'newName': newName})

        # If the caller requested that we automatically delete the Id field
        # added to shapefiles or the Field1 field added to dBase tables, we
        # need to do special processing.

        if self.AutoDeleteFieldAddedByArcGIS and not self._DeletedFieldAddedByArcGIS and self.ArcGISPhysicalDataType.lower() in ['shapefile', 'dbasetable']:
            if self.ArcGISPhysicalDataType.lower() == 'shapefile':
                fieldAddedByArcGIS = 'Id'
            else:
                fieldAddedByArcGIS = 'Field1'

            # Check whether the automatically-added field exists. 

            fieldAddedByArcGIS = self.GetFieldByName(fieldAddedByArcGIS)
            if fieldAddedByArcGIS is not None:

                # It exists. If the caller is adding a field with a different
                # name, just add the caller's field and delete the
                # automatically-added field.
                
                if name != fieldAddedByArcGIS.Name:
                    gp.AddField_management(self._GetFullPath(), name, dataType, precision, None, length, None, isNullable)
                    self.DeleteField(fieldAddedByArcGIS.Name)
                else:
                    gp.AddField_management(self._GetFullPath(), 'xMGETxTMPx', 'LONG')
                    self.DeleteField(fieldAddedByArcGIS.Name)
                    gp.AddField_management(self._GetFullPath(), name, dataType, precision, None, length, None, isNullable)
                    gp.DeleteField_management('xMGETxTMPx')

            # Otherwise (the automatically added field does not exist), just
            # add the caller's field.

            else:
                gp.AddField_management(self._GetFullPath(), name, dataType, precision, None, length, None, isNullable)

            self._DeletedFieldAddedByArcGIS = True

        # Otherwise, just add the caller's field.

        else:
            gp.AddField_management(self._GetFullPath(), name, dataType, precision, None, length, None, isNullable)

        return self._ConstructFieldObject(gp.ListFields(self._GetFullPath(), name)[0])

    def _DeleteField(self, name):
        GeoprocessorManager.GetWrappedGeoprocessor().DeleteField_management(self._GetFullPath(), name)

    def _CreateIndex(self, fields, indexName, unique, ascending):

        # If it is not a shapefile, make sure the caller specified an index
        # name. If it is, set the index name to None.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        if self.ArcGISPhysicalDataType.lower() == 'shapefile':
            indexName = None
        elif indexName is None:
            raise ValueError(_('The index name must be provided.'))

        # It is not a shapefile. Remove the existing index, if it exists.

        if len(gp.ListIndexes(self._GetFullPath(), indexName)) > 0:
            gp.RemoveIndex_management(self._GetFullPath(), indexName)

        # Create the new index.

        gp.AddIndex_management(self._GetFullPath(), ';'.join(fields), indexName, {False: 'NON_UNIQUE', True: 'UNIQUE'}[unique], {False: 'NON_ASCENDING', True: 'ASCENDING'}[ascending])

    def _DeleteIndex(self, indexName):

        # If it is a shapefile, just call RemoveIndex.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        if self.ArcGISPhysicalDataType.lower() == 'shapefile':
            gp.RemoveIndex_management(self._GetFullPath())

        # Otherwise make sure the caller specified an index name. If that
        # index exists, remove it.
            
        else:
            if indexName is None:
                raise ValueError(_('The index name must be provided.'))

            if len(gp.ListIndexes(self._GetFullPath(), indexName)) > 0:
                gp.RemoveIndex_management(self._GetFullPath(), indexName)

    def _GetRowCount(self):
        return int(GeoprocessorManager.GetWrappedGeoprocessor().GetCount_management(self._GetFullPath()).getOutput(0))

    def _OpenSelectCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        return _ArcPyDASelectCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    def _OpenUpdateCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        return _ArcPyDAUpdateCursor(self, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    def _OpenInsertCursor(self, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural):
        return _ArcPyDAInsertCursor(self, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural)

    @classmethod
    def _RemoveExistingDatasetsFromList(cls, path, datasets, progressReporter):
        numDatasets = len(datasets)
        if GeoprocessorManager.GetWrappedGeoprocessor().Exists(path):
            cls._LogDebug(_('%(class)s: ArcGIS table or feature class "%(path)s" exists.'), {'class': cls.__name__, 'path': path})
            while len(datasets) > 0:
                del datasets[0]
        else:
            cls._LogDebug(_('%(class)s: ArcGIS table or feature class "%(path)s" does not exist.'), {'class': cls.__name__, 'path': path})

        if progressReporter is not None:
            progressReporter.ReportProgress(numDatasets)

    @classmethod
    def _ImportDatasetsToPath(cls, path, sourceDatasets, mode, progressReporter, options):

        # Validate that there is only one source dataset. We do not currently
        # support importing multiple source datasets into a single destination
        # dataset. (This could theoretically be supported in the future by
        # appending multiple datasets into the same destination.)

        if len(sourceDatasets) > 1:
            raise ValueError(_('Cannot import %(count)i datasets into ArcGIS table or feature class "%(path)s". Importing of multiple datasets into a single table or feature class is not currently supported. If you are receiving this error from a tool that has a parameter that is a list of expressions that define the output dataset namen, you may have made a mistake in your expressions that caused the same output dataset name to be generated for multiple input datasets. If that is the problem, you can fix it by modifying the expressions to generate a unique output dataset name for each input dataset.') % {'count': len(sourceDatasets), 'path': path})

        # If the mode is 'replace' and the destination dataset exists,
        # delete it.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        if mode == 'replace' and gp.Exists(path):
            cls._LogDebug(_('%(class)s: Deleting existing ArcGIS dataset "%(path)s".'), {'class': cls.__name__, 'path': path})
            try:
                gp.Delete_management(path)
            except Exception as e:
                raise RuntimeError(_('Failed to delete the existing ArcGIS dataset "%(path)s" due to %(e)s: %(msg)s') % {'path': path, 'e': e.__class__.__name__, 'msg': e})

        # Otherwise, make sure all the parent levels in the destination path
        # exist (directories, geodatabase, feature dataset), creating them if
        # necessary. Use ArcGIS tools such as CreateFolder_management to
        # create them, so the ArcGIS catalog is aware of them.

        elif not gp.Exists(os.path.dirname(path)):

            # If the destination path is in the file system, figure out
            # whether it contains levels for a geodatabase and a feature
            # dataset. If neither, it must be a shapefile, DBF table, or
            # something similar.

            if path[0] in ['/', '\\'] or hasattr(os.path, 'splitdrive') and os.path.splitdrive(path)[0] != '':
                if os.path.splitext(os.path.dirname(path))[1].lower() in ['.gdb']:
                    featureDataset = None
                    geodatabase = os.path.dirname(path)
                    directory = os.path.dirname(geodatabase)
                elif os.path.splitext(os.path.dirname(os.path.dirname(path)))[1].lower() in ['.gdb']:
                    featureDataset = os.path.dirname(path)
                    geodatabase = os.path.dirname(featureDataset)
                    directory = os.path.dirname(geodatabase)
                else:
                    featureDataset = None
                    geodatabase = None
                    directory = os.path.dirname(path)

                # Create the directory if it does not exist.

                if not os.path.exists(directory):
                    cls._LogDebug(_('%(class)s: Creating directory "%(path)s".'), {'class': cls.__name__, 'path': directory})

                    if hasattr(os.path, 'splitdrive') and os.path.splitdrive(directory)[0] != '':
                        root, subdirs = os.path.splitdrive(directory)
                        root = root + os.path.sep
                    else:
                        root, subdirs = directory[0], directory[1:]

                    subdirsList = []
                    while len(subdirs) > 1:
                        subdirsList.insert(0, os.path.basename(subdirs))
                        subdirs = os.path.dirname(subdirs)

                    dirToCheck = root
                    for subdir in subdirsList:
                        if not os.path.isdir(os.path.join(dirToCheck, subdir)):
                            try:
                                gp.CreateFolder_management(dirToCheck, subdir)
                            except Exception as e:
                                raise RuntimeError(_('Failed to create the directory "%(path)s" due to %(e)s: %(msg)s') % {'path': os.path.join(dirToCheck, subdir), 'e': e.__class__.__name__, 'msg': e})
                        dirToCheck = os.path.join(dirToCheck, subdir)

                # If the path includes a geodatabase and it does not exist,
                # create it.

                if geodatabase is not None and not gp.Exists(geodatabase):
                    gp.CreateFileGDB_management(directory, os.path.basename(geodatabase))

                # If the path includes a feature dataset and it does not
                # exist, create it.

                if featureDataset is not None and not gp.Exists(featureDataset):
                    gp.CreateFeatureDataset_management(geodatabase, os.path.basename(featureDataset))
                    
            # Otherwise (the desination path is not in the file system), make
            # sure the destination exists and create the feature dataset. I'm
            # not willing to code this without having an ArcSDE geodatabase to
            # test it with.

            else:
                raise NotImplementedError(_('Cannot import %(dn)s into destination ArcGIS table or feature class "%(path)s" because that destination is not a folder, personal geodatabase, or file geodatabase. Other destinations (e.g. ArcSDE geodatabases) are not fully supported. Please contact the author of this tool for assistance.') % {'dn': sourceDatasets[0].DisplayName, 'path': path})

        # At this point, the parent workspace of the destination dataset
        # exists, and the destination dataset does not exist. If the source
        # dataset is copyable with ArcGIS's Copy_management tool, use it
        # because it will be much faster than manually copying each row.

        if isinstance(sourceDatasets[0], ArcGISCopyableTable) and (options is None or len(options) <= 0):
            arcGISCopyablePath = sourceDatasets[0].GetArcGISCopyablePath()
            try:
                cls._LogDebug(_('%(class)s: Copying "%(src)s" to ArcGIS dataset "%(path)s".'), {'class': cls.__name__, 'src': arcGISCopyablePath, 'path': path})
                gp.Copy_management(arcGISCopyablePath, path)
            finally:
                sourceDatasets[0].Close()       # This will make sure it deletes temporary files, if it had to create any in order to make itself ArcGIS-copyable.

        # Otherwise copy the rows manually. This will work with any Table
        # instance.

        else:
            from . import ArcGISWorkspace
            workspace = ArcGISWorkspace(os.path.dirname(path), ArcGISTable, pathParsingExpressions=[r'(?P<TableName>.+)'], queryableAttributes=(QueryableAttribute('TableName', _('Table name'), UnicodeStringTypeMetadata()),))
            workspace.ImportTable(os.path.basename(path), sourceDatasets[0], reportProgress=False, options=options)

        # Report progress.
            
        if progressReporter is not None:
            progressReporter.ReportProgress()


class _ArcPyDAReadableCursor(object):

    def _NextRow(self):
        try:
            self._Row = next(self._Cursor)
        except StopIteration:
            self._Row = None
        return self._Row is not None

    def _GetValue(self, field):
        if self._Table.HasOID and field == self._Table.OIDFieldName:
            return self._GetOID()

        value = self._Row[self._FieldIndex[field]]

        # As of ArcGIS 3.2.2, file geodatabases do not support microsecond
        # values of date times, but arcpy will sometimes return a datetime
        # with microsecond set to 1. So if this value a datetime, and the
        # we're reading from a file GDB, set the microsecond to zero.

        if isinstance(value, datetime.datetime):
            progID = self._Table.GetLazyPropertyValue('workspaceFactoryProgID')
            if progID is not None and progID.startswith('esriDataSourcesGDB.FileGDBWorkspaceFactory'):
                value = datetime.datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)

        return value

    def _GetOID(self):
        if 'OID@' in self._FieldIndex:
            return self._Row[self._FieldIndex['OID@']]

    def _GetGeometry(self):
        ogr = self._Table._ogr()

        # If it is a Point or Point25D, we requested the SHAPE@XY and SHAPE@Z
        # tokens from the cursor, because the arcpy documentation states that
        # this is faster than requesting the full geometry object (via the
        # SHAPE@ token). Extract the x, y, and z coordinates and construct an
        # OGR Geometry object.

        if self._Table.GeometryType == 'Point':
            xy = self._Row[self._FieldIndex['SHAPE@XY']]
            if xy is not None and xy[0] is not None and xy[1] is not None:
                geometry = ogr.Geometry(ogr.wkbPoint)
                geometry.AddPoint_2D(xy[0], xy[1])
                return geometry

            if 'OID@' in self._FieldIndex:
                self._Table._LogWarning(_('The %(singular)s of %(dn)s with %(field)s = %(value)s has a null geometry.'), {'singular': self._RowDescriptionSingular, 'dn': self.Table.DisplayName, 'field': self.Table.OIDFieldName, 'value': repr(self._Row[self._FieldIndex['OID@']])})
            return None

        if self._Table.GeometryType == 'Point25D':
            xy = self._Row[self._FieldIndex['SHAPE@XY']]
            z = self._Row[self._FieldIndex['SHAPE@Z']]
            if xy is not None and xy[0] is not None and xy[1] is not None and z is not None:
                geometry = ogr.Geometry(ogr.wkbPoint25D)
                geometry.AddPoint(xy[0], xy[1], z)
                return geometry
            
            if 'OID@' in self._FieldIndex:
                self._Table._LogWarning(_('The %(singular)s of %(dn)s with %(field)s = %(value)s has a null geometry.'), {'singular': self._RowDescriptionSingular, 'dn': self.Table.DisplayName, 'field': self.Table.OIDFieldName, 'value': repr(self._Row[self._FieldIndex['OID@']])})
            return None

        # It is some other kind of geometry and we requested the full
        # geometry object via the SHAPE@ token. Extract the WKB and
        # construct an OGR object with it.

        g = self._Row[self._FieldIndex['SHAPE@']]
        if g is not None:
            wkb = g.WKB
            if len(wkb) > 0:
                return ogr.CreateGeometryFromWkb(g.WKB)

        if 'OID@' in self._FieldIndex:
            self._Table._LogWarning(_('The %(singular)s of %(dn)s with %(field)s = %(value)s has a null geometry.'), {'singular': self._RowDescriptionSingular, 'dn': self.Table.DisplayName, 'field': self.Table.OIDFieldName, 'value': repr(self._Row[self._FieldIndex['OID@']])})
        return None


class _ArcPyDAWritableCursor(object):

    def _SetValue(self, field, value):
        if isinstance(value, int) and self._Table.ArcGISPhysicalDataType in ['shapefile', 'dbftable']:
            length = self._Table.GetFieldByName(field).Length
            if value >= 10**length or value <= -1 * 10**(length-1):
                raise ValueError(_('Cannot set the value of field %(field)s of this %(singular) of %(dn)s to %(value)s because that value is outside of the allowed range of values for the field (%(r1)i to %(r2)i).') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName, 'field': field, 'value': repr(value), 'r1': -1 * 10**(length-1) + 1, 'r2': 10**length - 1})

        # As of ArcGIS 3.2.2, file geodatabases do not support microsecond
        # values of date times. If this value a datetime, and the we're
        # writing to a file GDB, set the microsecond to zero.

        if isinstance(value, datetime.datetime):
            progID = self._Table.GetLazyPropertyValue('workspaceFactoryProgID')
            if progID is not None and progID.startswith('esriDataSourcesGDB.FileGDBWorkspaceFactory'):
                value = datetime.datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)

        self._Row[self._FieldIndex[field]] = value

    def _SetGeometry(self, geometry):
        if geometry.IsEmpty():
            raise ValueError(_('Cannot set the geometry of this %(singular)s of %(dn)s because the provided Geometry object is empty. ArcGIS does not support empty geometries.') % {'singular': self._RowDescriptionSingular, 'dn': self._Table.DisplayName})
        
        ogr = self._Table._ogr()
        geometryType = geometry.GetGeometryType()

        # If it is a Point or Point25D, we requested the SHAPE@XY and SHAPE@Z
        # tokens from the cursor, because the arcpy documentation states that
        # this is faster than accessing the full geometry object (via the
        # SHAPE@ token). Extract the coordinates from the OGR Geometry object
        # and set the tokens.

        if geometryType in [ogr.wkbPoint, ogr.wkbPoint25D]:
            self._Row[self._FieldIndex['SHAPE@XY']] = (geometry.GetX(), geometry.GetY())
            if geometryType == ogr.wkbPoint25D:
                self._Row[self._FieldIndex['SHAPE@Z']] = geometry.GetZ()

        # Otherwise, we requested the full geometry object via the SHAPE@
        # token. Convert the OGR Geometry object to the appropriate arcpy
        # object and set SHAPE@ to it.

        else:
            gp = GeoprocessorManager.GetGeoprocessor()      # Do not changed to GetWrappedGeoprocessor(); we want the result of gp.FromWKB below to not be a wrapped object, because we're not wrapping the cursor objects, so they need unwrapped parameters when we call their functions
            self._Row[self._FieldIndex['SHAPE@']] = gp.FromWKB(bytearray(geometry.ExportToWkb()))        # This is super convenient. Kudos to ESRI for providing arcpy.FromWKB.


class _ArcPyDASelectCursor(_ArcPyDAReadableCursor, SelectCursor):
    __doc__ = DynamicDocString()

    def _Open(self, fields, where, orderBy):

        # If the caller did not specify a list of fields, request all of them.
        # If the caller did specify a list, eliminate any duplicates in it.

        if fields is None:
            fields = [field.Name for field in self.Table.Fields if field.DataType != 'unknown']
        else:
            fields = list(set(fields))

        # If the caller requested the OID or geometry field, replace that
        # field name with the appropriate token preferred by arcpy.da.

        if self.Table.HasOID and self.Table.OIDFieldName in fields:
            fields[fields.index(self.Table.OIDFieldName)] = 'OID@'

        if self.Table.GeometryType is not None and self.Table.GeometryFieldName in fields:
            del fields[fields.index(self.Table.GeometryFieldName)]

            # For points, request the SHAPE@XY and SHAPE@Z tokens, which are
            # faster than the full geometry, SHAPE@, according to the
            # documentation. For other geometry types, we must request the
            # full geometry object.
            
            if self.Table.GeometryType == 'Point':
                fields.append('SHAPE@XY')
            elif self.Table.GeometryType == 'Point25D':
                fields.extend(['SHAPE@XY', 'SHAPE@Z'])
            else:
                fields.append('SHAPE@')

        # Fail if orderBy is given and this is a shapefile or DBase table.

        if orderBy is not None:
            orderBy = 'ORDER BY ' + orderBy

            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            if gp.Describe(self._Table._GetFullPath()).DataType.lower() in ['shapefile', 'dbasetable'] or \
               gp.Describe(self._Table._GetFullPath()).DataType.lower() in ['featurelayer', 'tableview'] and gp.Describe(gp.Describe(self._Table._GetFullPath()).CatalogPath).DataType.lower() in ['shapefile', 'dbasetable']:
                raise ValueError(_('Cannot query %(dn)s with ORDER BY expression %(orderBy)r because ArcGIS does not support ORDER BY expressions for that data format.') % {'dn': self.Table.DisplayName, 'orderBy': orderBy})

        # Open the cursor. We do this with GetGeoprocessor() rather than
        # GetWrappedGeoprocessor() so that the arcpy.da.SearchCursor object
        # is not wrapped. Because that object has no explicit "close"
        # function, the only way to ensure it is closed is for it to be
        # destructed. Apparently, under certain scenarios, our wrapper may
        # not be destructed for a while; or possibly we were leaking a
        # reference to it (e.g. by logging it). In any case, the
        # arcpy.da.SearchCursor instance was staying alive, which was keeping
        # the cursor open, which was keeping transactions open and also
        # preventing other cursors from being opened. So we gave up on
        # wrapping the arcpy.da.SearchCursor. This also speeds things up.

        gp = GeoprocessorManager.GetGeoprocessor()  # Do not changed to GetWrappedGeoprocessor(); see above
        
        self._Row = None
        self._Cursor = gp.da.SearchCursor(self._Table._GetFullPath(), fields, where, sql_clause=(None, orderBy))
        try:
            self._FieldIndex = dict(zip(self._Cursor.fields, range(len(self._Cursor.fields))))
        except:
            self._Cursor = None
            raise

    def _Close(self):
        self._Row = None
        self._Cursor = None
        self._FieldIndex = None
        super(_ArcPyDASelectCursor, self)._Close()


class _ArcPyDAUpdateCursor(_ArcPyDAReadableCursor, _ArcPyDAWritableCursor, UpdateCursor):
    __doc__ = DynamicDocString()

    def _Open(self, fields, where, orderBy):

        # If the caller did not specify a list of fields, request all of them.
        # If the caller did specify a list, eliminate any duplicates in it.

        if fields is None:
            fields = [field.Name for field in self.Table.Fields if field.DataType != 'unknown']
        else:
            fields = list(set(fields))

        # If the caller requested the OID or geometry field, replace that
        # field name with the appropriate token preferred by arcpy.da.

        if self.Table.HasOID and self.Table.OIDFieldName in fields:
            fields[fields.index(self.Table.OIDFieldName)] = 'OID@'

        if self.Table.GeometryType is not None and self.Table.GeometryFieldName in fields:
            del fields[fields.index(self.Table.GeometryFieldName)]

            # For points, request the SHAPE@XY and SHAPE@Z tokens, which are
            # faster than the full geometry, SHAPE@, according to the
            # documentation. For other geometry types, we must request the
            # full geometry object.
            
            if self.Table.GeometryType == 'Point':
                fields.append('SHAPE@XY')
            elif self.Table.GeometryType == 'Point25D':
                fields.extend(['SHAPE@XY', 'SHAPE@Z'])
            else:
                fields.append('SHAPE@')

        # Fail if orderBy is given and this is a shapefile or DBase table.

        if orderBy is not None:
            orderBy = 'ORDER BY ' + orderBy

            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            if gp.Describe(self._Table._GetFullPath()).DataType.lower() in ['shapefile', 'dbasetable'] or \
               gp.Describe(self._Table._GetFullPath()).DataType.lower() in ['featurelayer', 'tableview'] and gp.Describe(gp.Describe(self._Table._GetFullPath()).CatalogPath).DataType.lower() in ['shapefile', 'dbasetable']:
                raise ValueError(_('Cannot query %(dn)s with ORDER BY expression %(orderBy)r because ArcGIS does not support ORDER BY expressions for that data format.') % {'dn': self.Table.DisplayName, 'orderBy': orderBy})

        # Open the cursor. We do this with GetGeoprocessor() rather than
        # GetWrappedGeoprocessor() so that the arcpy.da.UpdateCursor object
        # is not wrapped. Because that object has no explicit "close"
        # function, the only way to ensure it is closed is for it to be
        # destructed. Apparently, under certain scenarios, our wrapper may
        # not be destructed for a while; or possibly we were leaking a
        # reference to it (e.g. by logging it). In any case, the
        # arcpy.da.UpdateCursor instance was staying alive, which was keeping
        # the cursor open, which was keeping transactions open and also
        # preventing other cursors from being opened. So we gave up on
        # wrapping the arcpy.da.UpdateCursor. This also speeds things up.
        
        gp = GeoprocessorManager.GetGeoprocessor()  # Do not changed to GetWrappedGeoprocessor(); see above

        self._Row = None
        self._Cursor = gp.da.UpdateCursor(self._Table._GetFullPath(), fields, where, sql_clause=(None, orderBy))
        try:
            self._FieldIndex = dict(zip(self._Cursor.fields, range(len(self._Cursor.fields))))
        except:
            self._Cursor = None
            raise

    def _Close(self):
        self._Row = None
        self._Cursor = None
        self._FieldIndex = None
        super(_ArcPyDAUpdateCursor, self)._Close()

    def _UpdateRow(self):
        self._Cursor.updateRow(self._Row)
        self._Row = None

    def _DeleteRow(self):
        self._Cursor.deleteRow()
        self._Row = None


class _ArcPyDAInsertCursor(_ArcPyDAWritableCursor, InsertCursor):
    __doc__ = DynamicDocString()

    def _Open(self):

        # The arcpy.da.InsertCursor method requires that we provide a list of
        # fields that we will provide values for. The
        # GeoEco.Datasets.InsertCursor abstraction does not support this idea.
        # Thus we have no knowledge of which fields our caller might wish to
        # set. As a workaround, we'll open the cursor with the assumption that
        # the caller will provide values for ALL of the fields that it is
        # possible for us to set, and if they do not provide a value for it,
        # we'll try to set it to NULL.

        fields = [field.Name for field in self.Table.Fields if field.IsSettable and field.DataType != 'unknown']

        # Replace the geometry field by the appropriate token preferred by
        # arcpy.da.

        if self.Table.GeometryType is not None and self.Table.GeometryFieldName in fields:
            del fields[fields.index(self.Table.GeometryFieldName)]

            # For points, use the SHAPE@XY and SHAPE@Z tokens, which are
            # faster than the full geometry, SHAPE@, according to the
            # documentation. For other geometry types, we must use the full
            # geometry object.
            
            if self.Table.GeometryType == 'Point':
                fields.append('SHAPE@XY')
            elif self.Table.GeometryType == 'Point25D':
                fields.extend(['SHAPE@XY', 'SHAPE@Z'])
            else:
                fields.append('SHAPE@')

        # Open the cursor. We do this with GetGeoprocessor() rather than
        # GetWrappedGeoprocessor() so that the arcpy.da.InsertCursor object
        # is not wrapped. Because that object has no explicit "close"
        # function, the only way to ensure it is closed is for it to be
        # destructed. Apparently, under certain scenarios, our wrapper may
        # not be destructed for a while; or possibly we were leaking a
        # reference to it (e.g. by logging it). In any case, the
        # arcpy.da.InsertCursor instance was staying alive, which was keeping
        # the cursor open, which was keeping transactions open and also
        # preventing other cursors from being opened. So we gave up on
        # wrapping the arcpy.da.InsertCursor. This also speeds things up.
        
        gp = GeoprocessorManager.GetGeoprocessor()  # Do not changed to GetWrappedGeoprocessor(); see above

        self._Row = None
        self._Cursor = gp.da.InsertCursor(self._Table._GetFullPath(), fields)
        try:
            self._FieldIndex = dict(zip(self._Cursor.fields, range(len(self._Cursor.fields))))
        except:
            self._Cursor = None
            raise

    def _Close(self):
        self._Row = None
        self._Cursor = None
        self._FieldIndex = None
        super(_ArcPyDAInsertCursor, self)._Close()

    def _SetValue(self, field, value):
        if self._Row is None:
            self._Row = [None] * len(self._FieldIndex)
        super(_ArcPyDAInsertCursor, self)._SetValue(field, value)

    def _SetGeometry(self, geometry):
        if self._Row is None:
            self._Row = [None] * len(self._FieldIndex)
        super(_ArcPyDAInsertCursor, self)._SetGeometry(geometry)

    def _InsertRow(self):
        self._Cursor.insertRow(self._Row)
        self._Row = None


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
