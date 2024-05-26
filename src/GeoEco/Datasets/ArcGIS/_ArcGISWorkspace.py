# _ArcGISWorkspace.py - Defines ArcGISWorkspace, a DatasetCollectionTree and
# Database for accessing ArcGIS tabular, vector, and raster datasets through
# arcpy.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import inspect
import os
import re

from ...ArcGIS import GeoprocessorManager
from ...DynamicDocString import DynamicDocString
from ...Internationalization import _

from .. import Dataset, Database
from ..Collections import DatasetCollectionTree
from ..GDAL import GDALDataset

from ._ArcGISRaster import ArcGISRaster
from ._ArcGISTable import ArcGISTable


class ArcGISWorkspace(DatasetCollectionTree, Database):
    __doc__ = DynamicDocString()

    def _GetPath(self):
        return self._Path

    Path = property(_GetPath, doc=DynamicDocString())

    def _GetDatasetType(self):
        return self._DatasetType

    DatasetType = property(_GetDatasetType, doc=DynamicDocString())

    def _GetCacheTree(self):
        return self._CacheTree

    CacheTree = property(_GetCacheTree, doc=DynamicDocString())

    def __init__(self, path, datasetType, pathParsingExpressions=None, pathCreationExpressions=None, cacheTree=True, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Validate datasetType.

        if not inspect.isclass(datasetType) or not issubclass(datasetType, (ArcGISRaster, ArcGISTable)):
            raise TypeError(_('datasetType must be an ArcGISRaster or ArcGISTable, or a subclass of one of them.'))

        # Set the display name based on the type of workspace it is.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        d = gp.Describe(path)
        if d.DataType.lower() == 'file' and path.lower().endswith('.sde'):
            self._DisplayName = _('ArcGIS database connection %(path)s') % {'path': path}
        else:
            if not(d.DataType.lower() in ['workspace', 'folder'] or
                   issubclass(datasetType, ArcGISRaster) and d.DataType.lower() == 'rastercatalog' or
                   issubclass(datasetType, ArcGISTable) and d.DataType.lower() == 'featuredataset'):
                raise ValueError(_('Failed to open "%(path)s" as an ArcGIS workspace. ArcGIS reports that it is a %(dt)s, which cannot be opened as a workspace.') % {'path': path, 'dt': d.DataType})
            self._DisplayName = _('ArcGIS %(dt)s %(path)s') % {'dt': d.DataType, 'path': path}

        # Initialize our properties.

        self._Path = path
        self._DatasetType = datasetType
        self._CacheTree = cacheTree
        if self._CacheTree:
            self._TreeContentsCache = {}
        else:
            self._TreeContentsCache = None
        self._TreeDataTypeCache = {}

        # Initialize the base class.

        super(ArcGISWorkspace, self).__init__(pathParsingExpressions, pathCreationExpressions, queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues, cacheDirectory=cacheDirectory)

    def ToRasterCatalog(self, rasterCatalog, arcGISSpatialRefString, tQACoordType=None, tCoordFunction=None, managed=False, projectOnTheFly=False, overwriteExisting=False):
        # TODO: self.__doc__.Obj.ValidateMethodInvocation()

        # Create the raster catalog.

        self._LogInfo(_('Creating raster catalog %(path)s.') % {'path': rasterCatalog})
        
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        
        gp.CreateRasterCatalog_management(os.path.dirname(rasterCatalog),
                                          os.path.basename(rasterCatalog),
                                          gp.CreateSpatialReference_management(arcGISSpatialRefString).getOutput(0),
                                          gp.CreateSpatialReference_management(arcGISSpatialRefString).getOutput(0),
                                          None,
                                          None,
                                          None,
                                          None,
                                          {True: 'MANAGED', False: 'UNMANAGED'}[managed])

        # Add fields for each queryable attribute that can be parsed from the
        # raster paths.

        catalogTable = ArcGISTable(rasterCatalog)
        qaToFieldName = {}

        for level in self._AttrsForExpr:
            for item in level:
                qa = item[1]
                if qa.Name not in qaToFieldName and qa.Name.lower() not in ['startdate', 'centerdate', 'enddate']:
                    qaToFieldName[qa.Name] = qa.Name
                    
                    if isinstance(qa.DataType, BooleanTypeMetadata):
                        catalogTable.AddField(qa.Name, 'int16', isNullable=True)
                    elif isinstance(qa.DataType, FloatTypeMetadata):
                        catalogTable.AddField(qa.Name, 'float64', isNullable=True)
                    elif isinstance(qa.DataType, IntegerTypeMetadata):
                        catalogTable.AddField(qa.Name, 'int32', isNullable=True)

                    # If it is a string, check whether a MaxLength has been
                    # defined. If it is shorter than 250 characters, use it.
                    # If it is longer, use 250. The operating system probably
                    # does not allow paths much longer than 250 characters, so
                    # it is probably safe to use 250 even if MaxLength is
                    # larger (because if a very large value was used, the
                    # raster couldn't have been created anyway).
                    
                    elif isinstance(qa.DataType, UnicodeStringTypeMetadata):
                        if qa.DataType.MaxLength is not None and qa.DataType.MaxLength < 250:
                            catalogTable.AddField(qa.Name, 'string', length=qa.DataType.MaxLength, isNullable=True)
                        else:
                            catalogTable.AddField(qa.Name, 'string', length=250, isNullable=True)

                    # If it is a datetime, check whether it is named DateTime.
                    # If it is, then check whether it is the min, center, or
                    # max date and create a field with the proper name. If it
                    # is named something else, just create a field with that
                    # name.

                    elif isinstance(qa.DataType, DateTimeTypeMetadata):
                        if qa.Name.lower() == 'datetime':
                            if tQACoordType is None:
                                raise ValueError(_('The rasters stored in workspace %(ws)s include dates in their paths. In order to create a raster catalog from these, the tQACoordType parameter must also be specified.') % {'ws': self.Path})

                            dateFieldName = {'center': 'CenterDate', 'min': 'StartDate', 'max': 'EndDate'}[tQACoordType.lower()]
                            qaToFieldName[qa.Name] = dateFieldName
                            catalogTable.AddField(dateFieldName, 'datetime', isNullable=True)
                            catalogTable.CreateIndex([dateFieldName], dateFieldName + '_idx')

                            # If the caller provided a function that can
                            # calculate the other two dates given this one,
                            # add fields for the other two dates.

                            if tCoordFunction is not None:
                                otherFields = ['StartDate', 'CenterDate', 'EndDate']
                                otherFields.remove(dateFieldName)
                                for field in otherFields:
                                    catalogTable.AddField(field, 'datetime', isNullable=True)
                                    catalogTable.CreateIndex([field], field + '_idx')
                        else:
                            catalogTable.AddField(qa.Name, 'datetime', isNullable=True)

                    else:
                        del qaToFieldName[qa.Name]      # Should not happen, but if it does, we don't create a field.
        
        # Load all of the rasters in the workspace into the raster catalog.

        self._LogInfo(_('Loading rasters into the raster catalog.'))
        
        gp.WorkspaceToRasterCatalog_management(self.Path, rasterCatalog, 'INCLUDE_SUBDIRECTORIES', {True: 'PROJECT_ONFLY', False: 'NONE'}[projectOnTheFly])

        # Export the raster catalog paths to a temporary .DBF file and read
        # the file into dictionaries that map the OIDs in the raster catalog
        # to and from the paths to the rasters.

        self._LogInfo(_('Retrieving raster paths from the raster catalog.'))
        
        tempDir = self._CreateTempDirectory()
        catalogPathsFile = os.path.join(tempDir, 'Paths.dbf')
        gp.ExportRasterCatalogPaths_management(rasterCatalog, 'ALL', catalogPathsFile)

        oidToPath = {}
        pathToOID = {}
        pathsTable = ArcGISTable(catalogPathsFile)
        cur = pathsTable.OpenSelectCursor(rowDescriptionSingular=_('path'), rowDescriptionPlural=_('paths'))
        try:
            while cur.NextRow():
                oid = cur.GetValue('SourceOID')
                path = cur.GetValue('Path').lower()
                oidToPath[oid] = path
                pathToOID[path] = oid
        finally:
            del cur

        # For each raster, we need to determine the values of the queryable
        # attributes. To do that, we need to parse the values from the
        # raster's path. If we were not constructed with path parsing
        # expressions, create those expressions from the path creation
        # expressions.

        if self.PathParsingExpressions is None:
            ppeList = []
            for pce in self.PathCreationExpressions:
                ppe = ''
                i = 0
                while i < len(pce):

                    # If this character is the beginning of a strftime time
                    # expression, convert it to a regex.

                    if i+2 < len(pce) and pce[i] == '%' and pce[i+1] == '%' and pce[i+2] in 'YmdjHMS':
                        if pce[i+2] == 'Y':
                            ppe += r'(?P<Year>\d\d\d\d)'
                        elif pce[i+2] == 'm':
                            ppe += r'(?P<Month>\d\d)'
                        elif pce[i+2] == 'd':
                            ppe += r'(?P<Day>\d\d)'
                        elif pce[i+2] == 'j':
                            ppe += r'(?P<DayOfYear>\d\d\d)'
                        elif pce[i+2] == 'H':
                            ppe += r'(?P<Hour>\d\d)'
                        elif pce[i+2] == 'M':
                            ppe += r'(?P<Minute>\d\d)'
                        elif pce[i+2] == 'S':
                            ppe += r'(?P<Second>\d\d)'
                        i += 3

                    # Otherwise, if this character is the beginning of a
                    # printf-style formatter, convert it to a regex. Note that
                    # not all printf syntax is supported.

                    elif re.match(r'%\([^\)]+\)[#0\- +]?[\d]*(?:\.[\d]+)?[hlL]?[diouxXeEfFgGcrs]', pce[i:]) is not None:

                        # Parse components of the formatter.
                        
                        j = i + 2
                        while pce[j] != ')':
                            j += 1
                        qaName = pce[i+2:j]
                        j += 1

                        if pce[j] in '#0\\- +':
                            flag = pce[j]
                            j += 1
                        else:
                            flag = None

                        if pce[j] in '0123456789':
                            width = ''
                            while pce[j] in '0123456789':
                                width += pce[j]
                                j += 1
                            width = int(width)
                        else:
                            width = None

                        if pce[j] == '.':
                            j += 1
                            precision = ''
                            while pce[j] in '0123456789':
                                precision += pce[j]
                                j += 1
                            precision = int(precision)
                        else:
                            precision = None

                        if pce[j] in 'hlL':
                            j += 1

                        conversion = pce[j]
                        j += 1

                        # Generate the corresponding regex. Some of these are
                        # probably less strict than they should be.

                        if conversion in 'di':
                            ppe += r'(?P<' + qaName + r'>[+\- ]*\d+)'

                        elif conversion in 'eE':
                            ppe += r'(?P<' + qaName + r'>[+\- ]*\d+\.\d*[eE][+\-]\d+)'

                        elif conversion in 'fF':
                            if precision is not None:
                                if precision > 0:
                                    ppe += r'(?P<' + qaName + r'>[+\- ]*\d+\.\d{' + str(precision) + '})'
                                else:
                                    ppe += r'(?P<' + qaName + r'>[+\- ]*\d+)'
                            else:
                                ppe += r'(?P<' + qaName + r'>[+\- ]*\d+\.?\d*)'

                        elif conversion in 's':
                            if precision is not None:       # For NASA OceanColor L3 data, we need the ability to specify the maximum string length
                                ppe += r'(?P<' + qaName + '>.{0,' + str(precision) + '})'
                            else:
                                ppe += r'(?P<' + qaName + '>.*)'

                        else:
                            matchobj = re.match(r'%\([^\)]+\)[#0\- +]?[\d]*(?:\\\.[\d]+)?[hlL]?[diouxXeEfFgGcrs]', pce[i:])
                            raise ValueError(_('Cannot create parse paths from the raster catalog. The expression "%(expr)s" is not supported. Please contact the MGET development team for assistance.') % {'expr': matchobj.group(0)})

                        i = j

                    # Otherwise, if it is a special regex character, escape
                    # it.
                        
                    elif pce[i] in r'.^$*+?{}[]\|':
                        ppe += '\\' + pce[i]
                        i += 1

                    # Otherwise copy the character.
                    
                    else:
                        ppe += pce[i]
                        i += 1

                ppeList.append(ppe + '$')
                
            self._PathParsingExpressions = ppeList

        self._LogDebug(_('Using path parsing expressions: %(ppe)s') % {'ppe': repr(self._PathParsingExpressions)})

        # Populate our _TreeContentsCache with the values read from the .DBF
        # file.

        oldCacheTree = self._CacheTree
        oldTreeContentsCache = self._TreeContentsCache
        oldTreeDataTypeCache = self._TreeDataTypeCache

        try:
            self._CacheTree = True
            self._TreeContentsCache = {}
            self._TreeDataTypeCache = {}

            for path in sorted(pathToOID.keys()):
                parent = os.path.dirname(path)
                while parent not in self._TreeDataTypeCache:
                    self._TreeDataTypeCache[parent] = gp.Describe(parent).DataType
                    
                    newParent = os.path.dirname(parent)
                    if newParent == parent:
                        break
                    
                    if newParent not in self._TreeContentsCache:
                        self._TreeContentsCache[newParent] = []
                    if os.path.basename(parent) not in self._TreeContentsCache[newParent]:
                        self._TreeContentsCache[newParent].append(os.path.basename(parent))
                    
                    parent = newParent
                    
                parent = os.path.dirname(path)
                if parent not in self._TreeContentsCache:
                    self._TreeContentsCache[parent] = []
                self._TreeContentsCache[parent].append(os.path.basename(path))

            # Query ourself for the paths and their queryable attribute
            # values. This call returns a list, where each element is a list
            # having two elements: the first is a list of the path components,
            # the second is a dictionary of the queryable attribute values for
            # that path (key = queryable attribute name, value = queryable
            # attribute value). Convert this to a dictionary that maps paths
            # to the queryable attribute dictionaries.

            pathsAndQAVsList = self.QueryDatasets(getQueryableAttributesOnly=True)
            
            pathToQAVs = {}
            for result in pathsAndQAVsList:
                pathToQAVs[os.path.join(self.Path, *result[0]).lower()] = result[1]

            # Open an update cursor on the raster catalog. For each row,
            # update the fields using the queryable attribute values.

            self._LogInfo(_('Updating the fields of each row of the raster catalog.'))

            cur = catalogTable.OpenUpdateCursor(rowCount=catalogTable.GetRowCount(), rowDescriptionSingular=_('row'), rowDescriptionPlural=_('rows'))
            try:
                while cur.NextRow():
                    path = oidToPath[cur.GetOID()]
                    if path not in pathToQAVs:
                        continue

                    qav = pathToQAVs[path]
                    for qaName, fieldName in qaToFieldName.items():

                        # If this is queryable attribute is named 'DateTime'
                        # and the caller provided a function that can
                        # calculate the dates from the queryable attribute
                        # values, calculate the dates and set the fields.

                        if qaName.lower() == 'datetime' and tCoordFunction is not None:
                            values = tCoordFunction(qav)
                            cur.SetValue('StartDate', values[0])
                            cur.SetValue('CenterDate', values[1])
                            cur.SetValue('EndDate', values[2])
                        else:
                            cur.SetValue(fieldName, qav[qaName])

                    cur.UpdateRow()
            finally:
                del cur
            
        finally:
            self._CacheTree = oldCacheTree
            self._TreeContentsCache = oldTreeContentsCache
            self._TreeDataTypeCache = oldTreeDataTypeCache

    def _GetDisplayName(self):
        return self._DisplayName

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['createtable', 'deletetable']:
            return None

        capList = capability.split(' ', 2)
        if len(capList) == 3 and capList[0] == 'geometrytype':
            if capList[1] in ['point', 'point25d', 'linestring', 'linestring25d', 'polygon', 'polygon25d', 'multipoint', 'multipoint25d', 'multilinestring', 'multilinestring25d', 'multipolygon', 'multipolygon25d']:
                return None
            return RuntimeError(_('Cannot create table %(table)s with "%(geom)s" geometry. ArcGIS does not support that geometry type.') % {'table': capList[2], 'geom': capList[1]})
        
        if isinstance(cls, ArcGISWorkspace):
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__name__, 'cap': capability})

    def _ListContents(self, pathComponents):

        # If we are supposed to cache the tree, probe our cache for the
        # contents of this path.

        path = os.path.join(self.Path, *pathComponents)

        if self._CacheTree and path in self._TreeContentsCache:
            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved cached contents of %(dt)s %(path)s'), {'class': self.__class__.__name__, 'id': id(self), 'dt': self._TreeDataTypeCache[path], 'path': path})
            return self._TreeContentsCache[path]

        # We did not retrieve the contents of this path from the cache. Get
        # the contents from ArcGIS.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        
        d = gp.Describe(path)
        self._TreeDataTypeCache[path] = d.DataType
        
        self._LogDebug(_('%(class)s 0x%(id)016X: Listing contents of %(dt)s %(path)s'), {'class': self.__class__.__name__, 'id': id(self), 'dt': d.DataType, 'path': path})

        contents = []

        # Change the geoprocessor's workspace to the path, so we can use the
        # geoprocessor's List functions.

        oldWorkspace = gp.env.workspace
        gp.env.workspace = path

        try:
            # If we have not reached the lowest-level path component,
            # enumerate ArcGIS objects that are containers.

            if len(pathComponents) < len(self.PathParsingExpressions) - 1:
                if d.DataType.lower() == 'folder':
                    for workspace in gp.ListWorkspaces('*'):
                        d = gp.Describe(workspace)
                        if d.DataType.lower() == 'workspace' or d.DataType.lower() == 'folder' and (os.path.basename(workspace) != 'info' or not os.path.exists(os.path.join(path, workspace, 'arc.dir'))):
                            workspace = os.path.basename(workspace)
                            contents.append(workspace)
                            self._TreeDataTypeCache[os.path.join(path, workspace)] = d.DataType

                elif d.DataType.lower() == 'workspace':        # If the current path is a workspace, then enumerate raster catalogs or feature datasets in the workspace
                    for dataset in gp.ListDatasets('*'):
                        d = gp.Describe(dataset)
                        if issubclass(self._DatasetType, ArcGISRaster) and d.DataType.lower() == 'rastercatalog' or issubclass(self._DatasetType, ArcGISTable) and d.DataType.lower() == 'featuredataset':
                            dataset = os.path.basename(dataset)
                            contents.append(dataset)
                            self._TreeDataTypeCache[os.path.join(path, dataset)] = d.DataType

            # Otherwise (we have reached the lowest-level path component),
            # enumerate the type of object we're ultimately looking for.

            elif issubclass(self._DatasetType, ArcGISRaster):

                # Raster catalogs require special processing.
                
                if d.DataType.lower() == 'rastercatalog':
                    for raster in gp.ListDatasets('*'):
                        if raster.startswith(os.path.basename(path) + os.path.sep) or raster.startswith(os.path.basename(path) + '/'):     # Delete redundant raster catalog name from beginning of raster name, if present. Looks like an ArcGIS bug. Found in 9.3.1; other versions not tested. Causes problems later with multiband rasters.
                            raster = raster[len(os.path.basename(path))+1:]
                        contents.append(raster)

                # Other containers of rasters (directories, geodatabases) do
                # not require special processing.
                
                else:
                    for raster in gp.ListRasters('*'):
                        contents.append(os.path.basename(raster))

            elif issubclass(self._DatasetType, ArcGISTable):

                # If the caller is looking for ArcGISTables, enumerate the
                # feature classes. Additionally, if the path does not resolve
                # to a FeatureDataset, enumerate the tables.
                
                for featureClass in gp.ListFeatureClasses('*'):
                    contents.append(os.path.basename(featureClass))

                if d.DataType.lower() != 'featuredataset':
                    for table in gp.ListTables('*'):
                        contents.append(os.path.basename(table))

                    # Unfortunately, ListTables does not return attributed
                    # relationship classes, which are essentially tables.
                    # Enumerate these using the arcpy.da module.

                    import arcpy.da

                    for dirpath, dirnames, relClass in arcpy.da.Walk(gp.env.workspace, datatype='RelationshipClass'):
                        d = gp.Describe(os.path.join(gp.env.workspace, relClass))
                        if d.DataType.lower() == 'relationshipclass' and bool(d.isAttributed):
                            contents.append(os.path.basename(relClass))

        # Change the geoprocessor's workspace back to what it was.

        finally:
            gp.env.workspace = oldWorkspace

        # Sort the contents and add them to the cache, if required.
        
        contents.sort()
        
        if self._CacheTree:
            self._TreeContentsCache[path] = contents

        return contents

    def _ConstructFoundObject(self, pathComponents, attrValues, options):

        # If we're looking for rasters and the path components point
        # to a file system object that is not inside a file
        # geodatabase, construct and return a GDALDataset. Accessing
        # rasters with GDAL is much faster than the ArcGIS
        # geoprocessor, and is the only way we can read and write data
        # (at least prior to ArcGIS 10, which theoretically allows it
        # via the geoprocessor).
        #
        # Note that we retrieve the raster's SpatialReference using
        # the ArcGIS geoprocessor to work around the unfortunate fact
        # that GDAL does not know how to recognize some of the
        # ESRI-specific WKT strings that ArcGIS stores in rasters.

        if issubclass(self._DatasetType, ArcGISRaster) and os.path.exists(os.path.join(self.Path, *pathComponents)) and self._TreeDataTypeCache[os.path.join(self.Path, *pathComponents[:-1])].lower() == 'folder':
            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            try:
                sr = gp.CreateSpatialReference_management(gp.Describe(os.path.join(self.Path, *pathComponents)).SpatialReference).getOutput(0).split(';')[0]
            except:
                sr = gp.CreateSpatialReference_management(gp.Describe(os.path.join(self.Path, *pathComponents)).SpatialReference).getOutput(0).split(';')[0]     # Sometimes Arc 10 fails randomly with RuntimeError: DescribeData: Method SpatialReference does not exist. Try again.
            spatialReference = Dataset.ConvertSpatialReference('arcgis', sr, 'obj')
            return GDALDataset(os.path.join(*pathComponents), parentCollection=self, queryableAttributeValues=attrValues, lazyPropertyValues={'SpatialReference': spatialReference}, cacheDirectory=self.CacheDirectory, **options)
            
        # Otherwise construct and return an object of the type
        # specified to our own constructor.
        
        return self.DatasetType(os.path.join(*pathComponents), parentCollection=self, queryableAttributeValues=attrValues, cacheDirectory=self.CacheDirectory, **options)

    def _GetLocalFile(self, pathComponents):
        return os.path.join(self.Path, *pathComponents), False      # False indicates that it is NOT ok for the caller to delete the file after decompressing it, to save space

    def _RemoveExistingDatasetsFromList(self, pathComponents, datasets, progressReporter):
        self.DatasetType._RemoveExistingDatasetsFromList(os.path.join(self.Path, *pathComponents), datasets, progressReporter)

    def _ImportDatasetsToPath(self, pathComponents, sourceDatasets, mode, progressReporter, options):
        self.DatasetType._ImportDatasetsToPath(os.path.join(self.Path, *pathComponents), sourceDatasets, mode, progressReporter, options)

    # Overridden methods of Database

    def ImportTable(self, destTableName, sourceTable, fields=None, where=None, orderBy=None, rowCount=None, reportProgress=True, rowDescriptionSingular=None, rowDescriptionPlural=None, copiedOIDFieldName=None, allowSafeCoercions=True, **options):

        # First call the base class method to actually do the import.

        table = super(ArcGISWorkspace, self).ImportTable(destTableName, sourceTable, fields, where, orderBy, rowCount, reportProgress, rowDescriptionSingular, rowDescriptionPlural, copiedOIDFieldName, allowSafeCoercions, **options)

        # Now, if the resulting table has a geometry column, check
        # whether it has a spatial index. If not, create one. We do
        # this specifically because I have noticed that sometimes for
        # shapefiles, ArcGIS appears to discard the spatial index that
        # was requested in the call to CreateFeatureClass_management.
        # I have not determined whether it is caused by subsequently
        # adding fields, by adding records, or what.

        if table.GeometryType is not None:
            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            d = gp.Describe(table._GetFullPath())

            if hasattr(d, 'HasSpatialIndex') and not d.HasSpatialIndex:
                if reportProgress:
                    self._LogInfo(_('Adding a spatial index to %(dn)s.') % {'dn': table.DisplayName})
                else:
                    self._LogDebug(_('Adding a spatial index to %(dn)s.') % {'dn': table.DisplayName})
                    
                gp.AddSpatialIndex_management(table._GetFullPath(), 0, 0, 0)

        # Return successfully.

        return table

    def _TableExists(self, tableName):
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        return gp.Exists(os.path.join(self._Path, tableName)) or os.path.splitext(tableName)[1].lower() not in ['.shp', '.dbf'] and os.path.isdir(self._Path) and gp.Describe(self._Path).DataType.lower() in ['workspace', 'folder'] and (gp.Exists(os.path.join(self._Path, tableName + '.shp')) or gp.Exists(os.path.join(self._Path, tableName + '.dbf')))

    def _CreateTable(self, tableName, geometryType, spatialReference, geometryFieldName, options):

        # If the caller did not specify a geometryType, create a
        # regular table.

        if options is not None and 'config_keyword' in options:
            config_keyword = options['config_keyword']
        else:
            config_keyword = None

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        if geometryType is None:

            # If self._Path is a directory and tableName does not have
            # an extension, gp.CreateTable_management() will create an
            # ArcInfo table, rather than a dBase table (.dbf file). We
            # don't want that. Add an extension to the caller's table.

            if os.path.splitext(tableName)[1].lower() != '.dbf' and os.path.isdir(self._Path) and gp.Describe(self._Path).DataType.lower() in ['workspace', 'folder']:
                tableName = tableName + '.dbf'

            gp.CreateTable_management(self._Path, tableName, None, config_keyword)

        # Otherwise create a feature class.

        else:
            geometryType = geometryType.upper()

            hasZ = {False: 'DISABLED', True: 'ENABLED'}[geometryType[-3:] == '25D']
            
            if geometryType in ['POINT', 'POINT25D']:
                geometryType = 'POINT'
            elif geometryType in ['MULTIPOINT', 'MULTIPOINT25D']:
                geometryType = 'MULTIPOINT'
            elif geometryType in ['LINESTRING', 'MULTILINESTRING', 'LINESTRING25D', 'MULTILINESTRING25D']:
                geometryType = 'POLYLINE'
            elif geometryType in ['POLYGON', 'MULTIPOLYGON', 'POLYGON25D', 'MULTIPOLYGON25D']:
                geometryType = 'POLYGON'

            srString = Dataset.ConvertSpatialReference('Obj', spatialReference, 'ArcGIS')

            gp.CreateFeatureClass_management(self._Path, tableName, geometryType, None, 'DISABLED', hasZ, srString, config_keyword, 0, 0, 0)

        # If we're caching the workspace contents, clear the cache so that the
        # new table will be discovered if the workspace is queried again.

        if self._CacheTree:
            self._TreeContentsCache = {}
            self._TreeDataTypeCache = {}

        # Return an ArcGISTable instance for the new table.

        return ArcGISTable(os.path.join(self._Path, tableName), autoDeleteFieldAddedByArcGIS=True)

    def _DeleteTable(self, tableName):
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        if not gp.Exists(os.path.join(self._Path, tableName)) and os.path.splitext(tableName)[1].lower() not in ['.shp', '.dbf'] and os.path.isdir(self._Path) and gp.Describe(self._Path).DataType.lower() in ['workspace', 'folder']:
            if gp.Exists(os.path.join(self._Path, tableName + '.shp')):
                return gp.Delete_management(os.path.join(self._Path, tableName + '.shp'))
            elif gp.Exists(os.path.join(self._Path, tableName + '.dbf')):
                return gp.Delete_management(os.path.join(self._Path, tableName + '.dbf'))
        return gp.Delete_management(os.path.join(self._Path, tableName))


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
