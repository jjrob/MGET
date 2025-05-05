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

    def __init__(self, path, datasetType, pathParsingExpressions=None, pathCreationExpressions=None, cacheTree=False, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
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

        # Set lazy properties for the Describe object's workspace properties.
        # This allows us to implement certain hacks based on the workspace.

        if d.DataType.lower() == 'workspace':
            self.SetLazyPropertyValue('workspaceType', d.workspaceType)
            self.SetLazyPropertyValue('workspaceFactoryProgID', d.workspaceFactoryProgID)

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

                    for dirpath, dirnames, relClasses in gp.da.Walk(gp.env.workspace, datatype='RelationshipClass')._Object:    # _ArcGISObjectWrapper does not currently support iteration so we have to extract _Object
                        for relClass in relClasses:
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
            if isinstance(options, dict) and not 'warpOptions' in options:
                gp = GeoprocessorManager.GetWrappedGeoprocessor()
                try:
                    sr = gp.CreateSpatialReference_management(gp.Describe(os.path.join(self.Path, *pathComponents)).SpatialReference).getOutput(0).split(';')[0]
                except:
                    sr = gp.CreateSpatialReference_management(gp.Describe(os.path.join(self.Path, *pathComponents)).SpatialReference).getOutput(0).split(';')[0]     # Sometimes Arc 10 fails randomly with RuntimeError: DescribeData: Method SpatialReference does not exist. Try again.
                lazyPropertyValues = {'SpatialReference': Dataset.ConvertSpatialReference('arcgis', sr, 'obj')}
            else:
                lazyPropertyValues = None

            return GDALDataset(os.path.join(*pathComponents), parentCollection=self, queryableAttributeValues=attrValues, lazyPropertyValues=lazyPropertyValues, cacheDirectory=self.CacheDirectory, **options)
            
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

            if os.path.splitext(tableName)[1].lower() != '.dbf' and os.path.isdir(self._Path) and gp.Describe(self._Path).DataType.lower() in ['workspace', 'folder'] and not self._Path.lower().endswith('.gdb'):
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

            gp.CreateFeatureclass_management(self._Path, tableName, geometryType, None, 'DISABLED', hasZ, srString, config_keyword, 0, 0, 0)

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
