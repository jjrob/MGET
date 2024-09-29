# DataManagement/ArcGISRasters.py - Methods for performing common operations
# with ArcGIS rasters.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import math
import os
import re

from ..ArcGIS import GeoprocessorManager
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger
from ..Types import EnvelopeTypeMetadata


class ArcGISRaster(object):
    __doc__ = DynamicDocString()

    @classmethod
    def Copy(cls, sourceRaster, destinationRaster, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Copying ArcGIS raster %(in)s to %(out)s...') % {'in' : sourceRaster, 'out' : destinationRaster})
        try:
            try:
                cls._Copy(sourceRaster, destinationRaster)
            except:
                Logger.LogExceptionAsError(_('Could not copy ArcGIS raster %(source)s to %(dest)s') % {'source' :  sourceRaster, 'dest' : destinationRaster})
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def _Copy(cls, sourceRaster, destinationRaster):

        # This function used to perform some additional steps to workaround
        # some bugs in old versions of ArcGIS, but these are no longer
        # necessary, so all we need to do is call gp.CopyRaster_management().

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        gp.CopyRaster_management(sourceRaster, destinationRaster)

    @classmethod
    def CopySilent(cls, sourceRaster, destinationRaster, overwriteExisting=False):
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            cls.Copy(sourceRaster, destinationRaster, overwriteExisting)
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def CreateXRaster(cls, raster, extent, cellSize, cellValue='Center', coordinateSystem=None, buildPyramids=False, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        left, bottom, right, top = EnvelopeTypeMetadata.ParseFromArcGISString(extent)

        if right - left <= 0:
            Logger.RaiseException(ValueError(_('The horizontal extent must be greater than zero.')))

        if top - bottom <= 0:
            Logger.RaiseException(ValueError(_('The vertical extent must be greater than zero.')))

        if cellSize <= 0.0:
            Logger.RaiseException(ValueError(_('The cell size must be greater than zero.')))

        # Determine the number of rows and columns of the raster.

        rows = int(math.ceil((top - bottom) / cellSize))
        cols = int(math.ceil((right - left) / cellSize))

        # Create a numpy array that contains the raster values.

        if cellValue == 'center':
            increment = cellSize / 2
        elif cellValue == 'right':
            increment = cellSize
        else:
            increment = 0

        import numpy
        values = numpy.arange(left + increment, right + increment, cellSize) * numpy.ones((rows, cols))

        # Create the raster.

        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Creating X coordinate raster %(out)s...') % {'out' : raster})
        try:
            cls.FromNumpyArray(numpyArray=values, 
                               raster=raster, 
                               xLowerLeftCorner=left, 
                               yLowerLeftCorner=bottom, 
                               cellSize=cellSize, 
                               coordinateSystem=coordinateSystem, 
                               buildPyramids=buildPyramids, 
                               overwriteExisting=overwriteExisting)
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def CreateYRaster(cls, raster, extent, cellSize, cellValue='Center', coordinateSystem=None, buildPyramids=False, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        left, bottom, right, top = EnvelopeTypeMetadata.ParseFromArcGISString(extent)

        if right - left <= 0:
            Logger.RaiseException(ValueError(_('The horizontal extent must be greater than zero.')))

        if top - bottom <= 0:
            Logger.RaiseException(ValueError(_('The vertical extent must be greater than zero.')))

        if cellSize <= 0.0:
            Logger.RaiseException(ValueError(_('The cell size must be greater than zero.')))

        # Determine the number of rows and columns of the raster.

        rows = int(math.ceil((top - bottom) / cellSize))
        cols = int(math.ceil((right - left) / cellSize))

        # Create a numpy array that contains the raster values.

        if cellValue == 'center':
            increment = cellSize / 2
        elif cellValue == 'top':
            increment = cellSize
        else:
            increment = 0

        import numpy
        values = numpy.arange(bottom + increment, top + increment, cellSize).reshape(rows,1) * numpy.ones((rows, cols))

        # Create the raster.

        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Creating Y coordinate raster %(out)s...') % {'out' : raster})
        try:
            cls.FromNumpyArray(numpyArray=values, 
                               raster=raster, 
                               xLowerLeftCorner=left, 
                               yLowerLeftCorner=bottom, 
                               cellSize=cellSize, 
                               coordinateSystem=coordinateSystem, 
                               buildPyramids=buildPyramids, 
                               overwriteExisting=overwriteExisting)
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def Delete(cls, raster):
        cls.__doc__.Obj.ValidateMethodInvocation()
        GeoprocessorManager.DeleteArcGISObject(raster, ['rasterdataset'], _('ArcGIS raster'))

    @classmethod
    def Exists(cls, path):
        cls.__doc__.Obj.ValidateMethodInvocation()
        return GeoprocessorManager.ArcGISObjectExists(path, ['rasterdataset'], 'ArcGIS raster')

    @classmethod
    def Find(cls, workspace, wildcard='*', searchTree=False, rasterType=None, basePath=None, getExtent=False, dateParsingExpression=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        Logger.Info(_('Finding ArcGIS rasters: workspace="%(workspace)s", wildcard="%(wildcard)s", searchTree=%(tree)s, rasterType="%(type)s"') % {'workspace': workspace, 'wildcard': wildcard, 'tree': searchTree, 'type': rasterType})
        return cls._Find(workspace,
                         wildcard,
                         searchTree,
                         rasterType,
                         basePath,
                         getExtent,
                         dateParsingExpression)

    @classmethod
    def _Find(cls, workspace, wildcard, searchTree, rasterType, basePath, getExtent, dateParsingExpression, searchPattern=None, strptimePattern=None):

        # If the caller provided a dateParsingExpression, parse it into a
        # pattern we can pass the re.search() and a corresponding pattern we
        # can subsequently pass to time.strptime().

        from .Files import File        

        if dateParsingExpression is not None and searchPattern is None:
            searchPattern, strptimePattern = File.ValidateDateParsingExpression(dateParsingExpression)

        # Change the current workspace to that specified by the caller.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        oldWorkspace = gp.env.workspace
        gp.env.workspace = workspace

        # Find matching rasters in the specified workspace.

        results = []

        if basePath is not None:
            os.path.normpath(basePath)
            baseParts = basePath.split(os.sep)

        try:
            for raster in gp.ListRasters(wildcard, rasterType):
                raster = os.path.join(workspace, raster)

                # Append the absolute path to the result row.
                
                Logger.Debug(_('Found raster %s'), raster)

                result = [raster]

                # If requested, append the relative path to the result row.

                if basePath is not None:
                    rasterParts = raster.split(os.sep)
                    i = 0
                    while i < len(baseParts) and i < len(rasterParts) and os.path.normcase(baseParts[i]) == os.path.normcase(rasterParts[i]):
                        i += 1
                    if i == 0:
                        result.append(raster)
                    else:
                        result.append(os.path.join(('..' + os.sep) * (len(baseParts) - i), os.sep.join(rasterParts[i:])))

                # If requested, append the other optional fields to the result row.
                    
                if getExtent:
                    (xMin, yMin, xMax, yMax) = EnvelopeTypeMetadata.ParseFromArcGISString(gp.Describe(raster).Extent)
                    result.append(xMin)
                    result.append(yMin)
                    result.append(xMax)
                    result.append(yMax)

                # If requested, parse a date from the absolute path and append it
                # to the result row, in both datetime and UNIX time formats.

                if dateParsingExpression is not None:
                    dateTime, unixTime = File.ParseDateFromPath(raster, dateParsingExpression, searchPattern, strptimePattern)
                    result.append(dateTime)
                    result.append(unixTime)

                # Append this result row to the list of results to return.

                results.append(result)

            # Search child workspaces, if requested.
            
            if searchTree:
                childWorkspaces = []
                for childWorkspace in gp.ListWorkspaces('*'):
                    dataType = gp.Describe(os.path.join(workspace, childWorkspace)).DataType.lower()
                    if dataType == 'workspace' or dataType == 'folder' and (childWorkspace.lower() != 'info' or not os.path.exists(os.path.join(workspace, childWorkspace, 'arc.dir'))):
                        childWorkspaces.append(childWorkspace)

                for childWorkspace in childWorkspaces:
                    results.extend(cls._Find(os.path.join(workspace, childWorkspace),
                                             wildcard,
                                             searchTree,
                                             rasterType,
                                             basePath,
                                             getExtent,
                                             dateParsingExpression,
                                             searchPattern,
                                             strptimePattern))

        # Change the current workspace back to what it was.                    

        finally:
            gp.env.workspace = oldWorkspace

        # Return successfully.

        return results        

    @classmethod
    def FindAndFillTable(cls, workspace, insertCursor, rasterField, wildcard='*', searchTree=False, rasterType=None, relativePathField=None, basePath=None, populateExtentFields=False, parsedDateField=None, dateParsingExpression=None, unixTimeField=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        fields = [rasterField, relativePathField, parsedDateField, unixTimeField]
        fieldsDict = {}
        for f in fields:
            if f is not None:
                if f.lower() in fieldsDict:
                    Logger.RaiseException(ValueError(_('The same field "%(field)s" is specified for two different parameters. Please specify a unique field name for each parameter.') % {'field': f}))
                fieldsDict[f] = True

        if populateExtentFields:
            for f in fields:
                if f is not None:
                    if f.lower() in ['xmin', 'xmax', 'ymin', 'ymax']:
                        Logger.RaiseException(ValueError(_('The field "%(field)s" is reserved for storing the raster extent. Please specify a different field name') % {'field': f}))

        if parsedDateField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive parsed dates, you must also specify a date parsing expression.')))

        if unixTimeField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive UNIX times, you must also specify a date parsing expression.')))

        if relativePathField is None:
            basePath = None

        # Find the rasters.

        Logger.Info(_('Finding ArcGIS rasters and inserting rows into table "%(table)s": workspace="%(workspace)s", wildcard="%(wildcard)s", searchTree=%(tree)s, rasterType="%(type)s"') % {'table': insertCursor.Table, 'workspace': workspace, 'wildcard': wildcard, 'tree': searchTree, 'type': rasterType})
        results = cls._Find(workspace,
                            wildcard,
                            searchTree,
                            rasterType,
                            basePath,
                            populateExtentFields,
                            dateParsingExpression)

        # Insert the rows.

        if len(results) > 0:
            insertCursor.SetRowCount(len(results))

            for result in results:
                value = result.pop(0)
                insertCursor.SetValue(rasterField, value)

                if relativePathField is not None:
                    value = result.pop(0)
                    insertCursor.SetValue(relativePathField, value)

                if populateExtentFields:
                    value = result.pop(0)
                    insertCursor.SetValue('XMin', value)
                    value = result.pop(0)
                    insertCursor.SetValue('YMin', value)
                    value = result.pop(0)
                    insertCursor.SetValue('XMax', value)
                    value = result.pop(0)
                    insertCursor.SetValue('YMax', value)

                if parsedDateField is not None or unixTimeField is not None:
                    value = result.pop(0)
                    if parsedDateField is not None:
                        insertCursor.SetValue(parsedDateField, value)

                    value = result.pop(0)
                    if unixTimeField is not None:
                        insertCursor.SetValue(unixTimeField, value)

                insertCursor.InsertRow()

    @classmethod
    def FindAndCreateTable(cls, workspace, database, table, rasterField, wildcard='*', searchTree=False, rasterType=None, relativePathField=None, basePath=None, populateExtentFields=False, parsedDateField=None, dateParsingExpression=None, unixTimeField=None, pathFieldsDataType='string', extentFieldsDataType='float64', dateFieldsDataType='datetime', unixTimeFieldDataType='int32', maxPathLength=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        fields = [rasterField, relativePathField, parsedDateField, unixTimeField]
        fieldsDict = {}
        for f in fields:
            if f is not None:
                if f.lower() in fieldsDict:
                    Logger.RaiseException(ValueError(_('The same field "%(field)s" is specified for two different parameters. Please specify a unique field name for each parameter.') % {'field': f}))
                fieldsDict[f] = True

        if populateExtentFields:
            for f in fields:
                if f is not None:
                    if f.lower() in ['xmin', 'xmax', 'ymin', 'ymax']:
                        Logger.RaiseException(ValueError(_('The field "%(field)s" is reserved for storing the raster extent. Please specify a different field name') % {'field': f}))

        if parsedDateField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive parsed dates, you must also specify a date parsing expression.')))

        if unixTimeField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive UNIX times, you must also specify a date parsing expression.')))

        if relativePathField is None:
            basePath = None

        # If requested, delete the table if it already exists.
        
        if database.TableExists(table):
            if overwriteExisting:
                database.DeleteTable(table)
            else:
                Logger.RaiseException(ValueError(_('Cannot create table %s because it already exists.') % table))

        # Create the table and add the fields.

        tableObj = database.CreateTable(table)
        
        try:
            tableObj.AddField(rasterField, pathFieldsDataType, length=maxPathLength)

            if relativePathField is not None:
                tableObj.AddField(relativePathField, pathFieldsDataType, length=maxPathLength)

            if populateExtentFields:
                tableObj.AddField('XMin', extentFieldsDataType)
                tableObj.AddField('YMin', extentFieldsDataType)
                tableObj.AddField('XMax', extentFieldsDataType)
                tableObj.AddField('YMax', extentFieldsDataType)

            if parsedDateField is not None:
                tableObj.AddField(parsedDateField, dateFieldsDataType)

            if unixTimeField is not None:
                tableObj.AddField(unixTimeField, unixTimeFieldDataType)

            # Create an insert cursor and fill the table.

            cursor = tableObj.OpenInsertCursor()
            try:
                cls.FindAndFillTable(workspace,
                                     cursor,
                                     rasterField,
                                     wildcard,
                                     searchTree,
                                     rasterType,
                                     relativePathField,
                                     basePath,
                                     populateExtentFields,
                                     parsedDateField,
                                     dateParsingExpression,
                                     unixTimeField)
            finally:
                del cursor

        # If an exception was raised, delete the table.
        
        except:
            try:
                database.DeleteTable(table)
            except:
                pass
            raise

        # Return successfully.

        return table        

    @classmethod
    def FindAndCreateArcGISTable(cls, inputWorkspace, outputWorkspace, table, rasterField='Image', wildcard='*', searchTree=False, rasterType=None, relativePathField=None, populateExtentFields=True, parsedDateField=None, dateParsingExpression=None, unixTimeField=None, maxPathLength=255, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # If the caller's output workspace is a directory (rather than a database),
        # the geoprocessor's CreateTable tool will create a DBF table,
        # regardless of what file extension the caller placed on the table. Even
        # if the caller's extension is .csv or .txt, the geoprocessor will
        # replace it with .dbf. If the caller does not provide an extension, the
        # geoprocessor will tack on .dbf.
        #
        # Because we know the geoprocessor will do this, we do it here
        # preemptively, so we can check for and delete the existing table, if
        # desired by the caller.

        if os.path.isdir(outputWorkspace) and not outputWorkspace.lower().endswith('.gdb') and not table.lower().endswith('.dbf'):
            if table.find('.') >= 0:
                newTable = table[:table.find('.')] + '.dbf'
                Logger.Warning('When creating tables in the file system, the ArcGIS CreateTable tool ignores the extension you specify and always creates a dBASE table with the extension .dbf. It will create the table %(new)s even though you asked for %(old)s.' % {'new': newTable, 'old': table})
            else:
                newTable = table + '.dbf'
                Logger.Warning('The ArcGIS CreateTable tool always creates dBASE tables in the file system. Even though you did not specify a file extension for your table, .dbf will be used.')
            table = newTable

        # Create the table.
        
        from ..Datasets import QueryableAttribute
        from ..Datasets.ArcGIS import ArcGISWorkspace, ArcGISTable
        
        database = ArcGISWorkspace(path=outputWorkspace, 
                                   datasetType=ArcGISTable,
                                   pathParsingExpressions=[r'(?P<TableName>.+)'], 
                                   queryableAttributes=(QueryableAttribute('TableName', _('Table name'), UnicodeStringTypeMetadata()),))

        table = cls.FindAndCreateTable(inputWorkspace,
                                       database,
                                       table,
                                       rasterField,
                                       wildcard,
                                       searchTree,
                                       rasterType,
                                       relativePathField,
                                       outputWorkspace,
                                       populateExtentFields,
                                       parsedDateField,
                                       dateParsingExpression,
                                       unixTimeField,
                                       'string',
                                       'float64',
                                       'datetime',
                                       'int32',
                                       maxPathLength,
                                       overwriteExisting)

        # If it is a DBF table, delete the Field1 field. ArcGIS always creates
        # this field because, according to the documentation, DBF files must
        # always have at least one field, and it is not possible to give a field
        # to the geoprocessor's CreateTable tool. Also delete the M_S_O_F_T
        # field if it exists; this is created by the Microsoft ODBC dBASE
        # driver, which ArcGIS could conceivably use in the future.
        
        if os.path.isdir(outputWorkspace) and not outputWorkspace.lower().endswith('.gdb') and table.lower().endswith('.dbf'):
            tableObj = database.QueryDatasets(expression="TableName = '%s'" % table, reportProgress=False)[0]
            if tableObj.GetFieldByName('Field1') is not None:
                tableObj.DeleteField('Field1')
            if tableObj.GetFieldByName('M_S_O_F_T') is not None:
                tableObj.DeleteField('M_S_O_F_T')

        # Return successfully.
        
        return table

    @classmethod
    def Move(cls, sourceRaster, destinationRaster, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Moving ArcGIS raster %(in)s to %(out)s...') % {'in' : sourceRaster, 'out' : destinationRaster})
        try:
            try:
                cls._Copy(sourceRaster, destinationRaster)
                GeoprocessorManager.DeleteArcGISObject(sourceRaster, ['rasterdataset'], _('ArcGIS raster'))
            except:
                Logger.LogExceptionAsError(_('Could not move ArcGIS raster %(source)s to %(dest)s') % {'source' :  sourceRaster, 'dest' : destinationRaster})
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def MoveSilent(cls, sourceRaster, destinationRaster, overwriteExisting=False):
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            cls.Move(sourceRaster, destinationRaster, overwriteExisting)
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def FromNumpyArray(cls, numpyArray, raster, xLowerLeftCorner, yLowerLeftCorner, cellSize, noDataValue=None, coordinateSystem=None, calculateStatistics=True, buildPyramids=False, buildRAT=True, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Creating ArcGIS raster %(out)s...') % {'out' : raster})
        try:
            try:
                # Create a NumpyGrid for the numpy array.

                from ..Datasets import Dataset, NumpyGrid

                grid = NumpyGrid(numpyArray=numpyArray, 
                                 displayName='NumPy grid', 
                                 spatialReference=Dataset.ConvertSpatialReference('ArcGIS', coordinateSystem, 'Obj'),
                                 dimensions='yx', 
                                 coordIncrements=(cellSize, cellSize), 
                                 cornerCoords=(yLowerLeftCorner + cellSize/2, xLowerLeftCorner + cellSize/2), 
                                 unscaledNoDataValue=noDataValue)

                # Create the raster.

                from ..Datasets.ArcGIS import ArcGISRaster as ArcGISRaster2

                ArcGISRaster2.CreateRaster(path=raster, 
                                           grid=grid, 
                                           overwriteExisting=overwriteExisting, 
                                           calculateStatistics=calculateStatistics,
                                           buildPyramids=buildPyramids,
                                           buildRAT=buildRAT)
            except:
                Logger.LogExceptionAsError()
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def ToNumpyArray(cls, raster, band=1):
        cls.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            try:
                from ..Datasets.ArcGIS import ArcGISRaster as ArcGISRaster2

                grid = ArcGISRaster2.GetRasterBand(raster, band)

                return grid.Data[:], grid.NoDataValue
            except:
                Logger.LogExceptionAsError()
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def ExtractByMask(cls, inputRaster, mask, outputRaster, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        try:
            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            extractedRaster = gp.sa.ExtractByMask(inputRaster, mask)
            extractedRaster.save(outputRaster)
        except:
            Logger.LogExceptionAsError()
            raise

    @classmethod
    def ProjectClipAndOrExecuteMapAlgebra(cls, inputRaster, outputRaster, projectedCoordinateSystem=None, geographicTransformation=None, resamplingTechnique=None, projectedCellSize=None, registrationPoint=None, clippingDataset=None, clippingRectangle=None, mapAlgebraExpression=None, buildPyramids=False, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        cls._ValidateProjectClipAndOrExecuteMapAlgebraParameters(projectedCoordinateSystem, geographicTransformation, resamplingTechnique, projectedCellSize, registrationPoint, clippingDataset, clippingRectangle, mapAlgebraExpression)
        Logger.Info(_('Processing ArcGIS raster %(in)s into raster %(out)s...') % {'in' : inputRaster, 'out' : outputRaster})
        try:
            from .Directories import TemporaryDirectory
            tempDir = TemporaryDirectory()
            
            outputRasterTemp = cls._ProjectClipAndOrExecuteMapAlgebraInTempDir(inputRaster, tempDir.Path,
                                                                               projectedCoordinateSystem=projectedCoordinateSystem,
                                                                               geographicTransformation=geographicTransformation,
                                                                               resamplingTechnique=resamplingTechnique,
                                                                               projectedCellSize=projectedCellSize,
                                                                               registrationPoint=registrationPoint,
                                                                               clippingDataset=clippingDataset,
                                                                               clippingRectangle=clippingRectangle,
                                                                               mapAlgebraExpression=mapAlgebraExpression,
                                                                               buildPyramids=buildPyramids)
            
            cls.MoveSilent(outputRasterTemp, outputRaster, overwriteExisting=overwriteExisting)
        except:
            Logger.LogExceptionAsError()
            raise

    @classmethod
    def _ValidateProjectClipAndOrExecuteMapAlgebraParameters(cls, projectedCoordinateSystem=None, geographicTransformation=None, resamplingTechnique=None, projectedCellSize=None, registrationPoint=None, clippingDataset=None, clippingRectangle=None, mapAlgebraExpression=None):
        if projectedCoordinateSystem is None and clippingDataset is None and clippingRectangle is None and mapAlgebraExpression is None:
            Logger.RaiseException(ValueError(_('You did not specify a projected coordinate system, clipping dataset/rectangle, or map algebra expression. To use this tool, you must specify at least one of these three parameters.')))
        if projectedCoordinateSystem is not None and resamplingTechnique is None:
            Logger.RaiseException(ValueError(_('To project the converted raster to a new coordinate system, you must specify the resampling technique.')))
        if clippingDataset is not None and clippingRectangle is not None:
            Logger.RaiseException(ValueError(_('You cannot specify both a dataset for clipping and a rectangle for clipping. Please specify just one of these parameters.')))
        if projectedCoordinateSystem is None and geographicTransformation is not None:
            Logger.Warning(_('The geographic transformation will be ignored because no projected coordinate system was specified.'))
        if projectedCoordinateSystem is None and resamplingTechnique is not None:
            Logger.Warning(_('The resampling technique will be ignored because no projected coordinate system was specified.'))
        if projectedCoordinateSystem is None and projectedCellSize is not None:
            Logger.Warning(_('The projected cell size will be ignored because no projected coordinate system was specified.'))
        if projectedCoordinateSystem is None and registrationPoint is not None:
            Logger.Warning(_('The registration point will be ignored because no projected coordinate system was specified.'))

    @classmethod
    def _ProjectClipAndOrExecuteMapAlgebraInTempDir(cls, inputRaster, tempDir, projectedCoordinateSystem=None, geographicTransformation=None, resamplingTechnique=None, projectedCellSize=None, registrationPoint=None, clippingDataset=None, clippingRectangle=None, mapAlgebraExpression=None, buildPyramids=False, overwriteExisting=False):
        import tempfile
        
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        outputRaster = inputRaster

        # Project the raster, if requested.
        
        if projectedCoordinateSystem is not None:
            outputRaster = tempfile.mktemp(suffix='.img', dir=tempDir)

            Logger.Debug(_('Projecting...'))
            if geographicTransformation is not None or registrationPoint is not None:
                gp.ProjectRaster_management(inputRaster, outputRaster, projectedCoordinateSystem, resamplingTechnique, projectedCellSize, geographicTransformation, registrationPoint)
            else:
                gp.ProjectRaster_management(inputRaster, outputRaster, projectedCoordinateSystem, resamplingTechnique, projectedCellSize)

            inputRaster = outputRaster

        # Clip the raster, if requested.

        if clippingDataset is not None or clippingRectangle is not None:
            outputRaster = tempfile.mktemp(suffix='.img', dir=tempDir)

            Logger.Debug(_('Clipping...'))

            # If the caller provided a clipping dataset, use it rather than
            # the clippingRectangle.

            if clippingDataset is not None:
                clippingRectangle = clippingDataset

            # Clip it.

            gp.Clip_management(inputRaster, clippingRectangle, outputRaster)
            inputRaster = outputRaster

        # Evaluate the map algebra expression, if requested.

        if mapAlgebraExpression is not None:
            outputRaster = tempfile.mktemp(suffix='.img', dir=tempDir)

            Logger.Debug(_('Evaluating map algebra expression: %(expr)s') % {'expr': mapAlgebraExpression})

            import arcpy.sa

            _globals = dict(arcpy.sa.__dict__)                      # Duplicate the arcpy.sa module dictionary, which contains all the Spatial Analyst functions
            _globals['inputRaster'] = arcpy.sa.Raster(inputRaster)  # Add a Raster object for our inputRaster to the dictionary

            try:
                outputRasterObject = eval(mapAlgebraExpression, _globals)   # Pass our custom dictionary for globals
            except:
                Logger.Error(_('Failed to evaluate map algebra expression: %(expr)s') % {'expr': mapAlgebraExpression})
                raise

            try:
                outputRasterObject.save(outputRaster)
            except:
                Logger.Error(_('The raster resulting from map algebra expression "%(expr)s" could not be saved to file %()') % {'expr': mapAlgebraExpression})
                raise

        # Build pyramids, if requested.

        if buildPyramids:
            Logger.Debug(_('Building pyramids...'))
            gp.BuildPyramids_management(outputRaster)

        # Return the path to the last raster we created in the temp
        # directory.

        return outputRaster

    @classmethod
    def ProjectToTemplate(cls, inputRaster, templateRaster, outputRaster, resamplingTechnique, interpolationMethod=None, maxHoleSize=None, mask=False, minValue=None, maxValue=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        try:
            # Perform additional validation.

            if interpolationMethod is not None and resamplingTechnique.lower() not in ['bilinear', 'cubic']:
                raise ValueError(_('Values cannot be interpolated for NoData cells if the NEAREST or MAJORITY resampling technique is used. Please select the BILINEAR or CUBIC resampling technique instead.'))

            # Look up the coordinate system, extent, and cell size of the
            # template raster.

            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            d = gp.Describe(templateRaster)
            coordinateSystem = gp.CreateSpatialReference_management(d.SpatialReference).getOutput(0).split(';')[0]
            extent = d.Extent
            cellSize = d.MeanCellWidth

            # Below, we will set the Extent, OutputCoordinateSystem, and
            # SnapRaster environment variables and then call ArcGIS's Resample
            # tool to simultaneously project and resample the input raster to
            # the coordinate system, extent, and cell size of the template
            # raster. But, unfortunately, it appears that the Extent
            # environment variable must be in the coordinate system of the
            # input raster, not the output coordinate system. So if the two
            # rasters do not have the same coordinate system, get the
            # coordinates of the template raster's extent in the coordinate
            # system of the input raster.

            dInput = gp.Describe(inputRaster)
            inputCoordinateSystem = gp.CreateSpatialReference_management(dInput.SpatialReference).getOutput(0).split(';')[0]
            inputExtent = dInput.Extent
            inputCellSize = dInput.MeanCellWidth

            csWithoutName = re.sub(r"projcs\['[^']+'", "projcs[''", coordinateSystem.lower())
            csWithoutName = re.sub(r"geogcs\['[^']+'", "geogcs[''", csWithoutName)

            icsWithoutName = re.sub(r"projcs\['[^']+'", "projcs[''", inputCoordinateSystem.lower())
            icsWithoutName = re.sub(r"geogcs\['[^']+'", "geogcs[''", icsWithoutName)

            from .Directories import TemporaryDirectory
            tempDir = TemporaryDirectory()

            try:
                if csWithoutName != icsWithoutName:
                    Logger.Debug(_('The template raster\'s coordinate system is not the same as the input raster\'s. Setting gp.env.extent to the extent of the template in the input raster\'s coordinate system.'))

                    # Transform all of the cells along the bottom, top, left, and
                    # right edges of the template raster to the input raster's
                    # coordinate system, and pick edge value that is the most
                    # extreme along each of the four sides.

                    from ..Datasets import Dataset
                    from ..Datasets.ArcGIS import ArcGISRaster as ArcGISRaster2

                    ogr = Dataset._osr()
                    inputSR = Dataset.ConvertSpatialReference('ArcGIS', inputCoordinateSystem, 'Obj')
                    templateSR = Dataset.ConvertSpatialReference('ArcGIS', coordinateSystem, 'Obj')
                    transformer = Dataset._osr().CoordinateTransformation(templateSR, inputSR)
                    templateRasterBand = ArcGISRaster2.GetRasterBand(templateRaster)

                    bottom = min([transformer.TransformPoint(x, templateRasterBand.MinCoords['y',0])[1] for x in templateRasterBand.CenterCoords['x']])
                    top = max([transformer.TransformPoint(x, templateRasterBand.MaxCoords['y',-1])[1] for x in templateRasterBand.CenterCoords['x']])

                    def zeroTo360(x):
                        if inputSR.IsGeographic():
                            return x if x >= 0 else x + 360.
                        return x

                    left = min([zeroTo360(transformer.TransformPoint(templateRasterBand.MinCoords['x',0], y)[0]) for y in templateRasterBand.CenterCoords['y']])
                    right = max([zeroTo360(transformer.TransformPoint(templateRasterBand.MaxCoords['x',-1], y)[0]) for y in templateRasterBand.CenterCoords['y']])

                    # If the inputSR is a geographic coordinate system, adjust the
                    # left and right coordinates to be on a -180 to +180 system
                    # if possible.

                    if inputSR.IsGeographic():
                        if right > 360.:    # This should not happen
                            left -= 360.
                            right -= 360.

                        if left >= right:
                            left -= 360.

                        if left >= 180 and right >= 180:
                            left -= 360.
                            right -= 360.

                        # If the left and right coordinates span the 180th
                        # meridian but the input raster uses a -180 to +180
                        # extent, ArcGIS won't be able to handle the
                        # reprojection (at least my experiments with ArcGIS
                        # Pro 3.2.2 failed.) To work around this, rotate the
                        # input raster by 180 degrees. Note: this logic does
                        # not test whether the input raster spans
                        # exactly -180 to +180. If it does not, this approach
                        # might not work, but we will try it anyway.

                        from ..Datasets.Virtual import RotatedGlobalGrid

                        if inputExtent.XMax - inputExtent.XMin == 360 and inputExtent.XMin < 0 and right > inputExtent.XMax:
                            inputRasterBand = ArcGISRaster2.GetRasterBand(inputRaster)
                            rotatedGrid = RotatedGlobalGrid(inputRasterBand, 180.)
                            Logger.Debug(_('Rotating the input raster by +180 degrees, so its extent encloses the template raster.'))
                            rotatedInputRaster = os.path.join(tempDir.Path, 'rotated.img')
                            ArcGISRaster2.CreateRaster(rotatedInputRaster, rotatedGrid)
                            inputRaster = rotatedInputRaster

                        # Similarly, if the left and right coordinates span
                        # the Prime Meridian and the input raster uses a 0 to
                        # 360 extent, the same problem can happen. In this
                        # case, we rotate the input raster by -180 degrees.

                        elif inputExtent.XMax - inputExtent.XMin == 360 and inputExtent.XMin >= 0 and left < inputExtent.XMin:
                            inputRasterBand = ArcGISRaster2.GetRasterBand(inputRaster)
                            rotatedGrid = RotatedGlobalGrid(inputRasterBand, -180.)
                            Logger.Debug(_('Rotating the input raster by -180 degrees, so its extent encloses the template raster.'))
                            rotatedInputRaster = os.path.join(tempDir.Path, 'rotated.img')
                            ArcGISRaster2.CreateRaster(rotatedInputRaster, rotatedGrid)
                            inputRaster = rotatedInputRaster

                    clipToInputExtent = '%r %r %r %r' % (left, bottom, right, top)
                else:
                    clipToInputExtent = extent
                
                # Unfortunately Project Raster will not necessarily create a
                # raster that has exactly the desired extent. It may be one cell
                # larger or smaller in any of the four directions. Different
                # versions of ArcGIS seem to work differently in this respect.
                #
                # To deal with this annoyance, we will expand the extent in all
                # four directions by 10 cells--guaranteeing that we have a raster
                # that is larger than the desired extent--and then use
                # gp.sa.ExtractByMask to obtain a raster of the desired extent.
                #
                # We use 10 cells rather than 1 cell because of a different
                # problem: if the caller requested that we interpolate values for
                # NoData cells, the most accurate values can be obtained if each
                # NoData region is completely surrounded by cells with data. In
                # the event that the template raster extent bisects a NoData
                # region, the 10 cell buffer increases the chance that we will
                # interpolate that region using cells from both sides of the
                # extent line: the side that is within the template extent and
                # also the side that is outside the extent but within the buffer.
                #
                # Update: Dec 2016: It appears that ArcGIS 10.1 cannot handle
                # setting the extent. Special case the 10 cell buffer to ArcGIS
                # 10.2 and later.
                #
                # Update: June 2017: There is a bug, or at least an odd and
                # undesirable behavior in ProjectRaster that occurs when the
                # output cell size is larger than that of the input raster. In
                # this situation we would expect the values for the (larger)
                # output cells to be obtained from the (smaller) input cells that
                # surround the center of the output cells. But it appears that the
                # output values are taken from a different location, such as the
                # upper left of the output cell. To work around this, I changed
                # the code to use the Resample tool instead, which does not
                # exhibit this behavior.

                [left, bottom, right, top] = EnvelopeTypeMetadata.ParseFromArcGISString(clipToInputExtent)
                oldExtent = gp.env.extent
                gp.env.extent = '%r %r %r %r' % (left - inputCellSize*10, bottom - inputCellSize*10, right + inputCellSize*10, top + inputCellSize*10)

                try:
                    oldSnapRaster = gp.env.snapRaster
                    gp.env.snapRaster = templateRaster
                    try:
                        oldOutputCoordinateSystem = gp.env.outputCoordinateSystem
                        gp.env.outputCoordinateSystem = coordinateSystem
                        try:
                            projectedRaster = os.path.join(tempDir.Path, 'projected.img')
                            gp.Resample_management(inputRaster, projectedRaster, cellSize, resamplingTechnique)
                        finally:
                            gp.env.outputCoordinateSystem = oldOutputCoordinateSystem
                    finally:
                        gp.env.snapRaster = oldSnapRaster

                # Reset the Extent ArcGIS environment variable to what it was
                # before.
                
                finally:
                    gp.env.extent = oldExtent

                # If the caller requested that we interpolate values for NoData
                # regions, do it now.

                if interpolationMethod is not None:
                    from ..Datasets.ArcGIS import ArcGISRaster as ArcGISRaster2
                    from ..Datasets.Virtual import InpaintedGrid

                    grid = ArcGISRaster2.GetRasterBand(projectedRaster)
                    grid = InpaintedGrid(grid, method=interpolationMethod, maxHoleSize=maxHoleSize, minValue=minValue, maxValue=maxValue)
                    inpaintedRaster = os.path.join(tempDir.Path, 'inpainted.img')
                    ArcGISRaster2.CreateRaster(inpaintedRaster, grid)
                    projectedRaster = inpaintedRaster

                # We are about to use gp.sa.ExtractByMask to extract a raster of the
                # desired extent from the projected raster in the temp directory.
                # But gp.sa.ExtractByMask also has a side effect that we might not
                # want: it sets cells that are NoData in the mask to NoData in
                # the output raster. If the caller did not request that to happen
                # (using the template raster as the mask), create a constant
                # raster that has the same coordinate system, extent, and cell
                # size as the template raster. We'll use it instead.

                if not mask:
                    oldOutputCoordinateSystem = gp.env.outputCoordinateSystem
                    gp.env.outputCoordinateSystem = coordinateSystem
                    try:
                        maskRaster = gp.sa.CreateConstantRaster(0, 'INTEGER', cellSize, extent)    # No need to save it
                    finally:
                        gp.env.outputCoordinateSystem = oldOutputCoordinateSystem

                    # For safety, verify that the output raster has the
                    # expected number of columns and rows.
                    
                    d2 = gp.Describe(maskRaster)
                    if d2.Width != d.Width or d2.Height != d.Height:
                        raise RuntimeError(_('Programming error in this tool: the constant raster does not have the same number of rows or columns as the template raster. Please contact the author of this tool for assistance.'))

                else:
                    maskRaster = templateRaster

                # Extract the raster.

                extractedRaster = gp.sa.ExtractByMask(projectedRaster, maskRaster)
                extractedRaster.save(outputRaster)

                # Safety check: validate that the output raster has the same
                # extent as the template.

                outputExtent = gp.Describe(outputRaster).Extent
                [templateLeft, templateBottom, templateRight, templateTop] = EnvelopeTypeMetadata.ParseFromArcGISString(extent)
                [outputLeft, outputBottom, outputRight, outputTop] = EnvelopeTypeMetadata.ParseFromArcGISString(outputExtent)

                if abs(outputLeft/templateLeft - 1) > 0.000001 or abs(outputBottom/templateBottom - 1) > 0.000001 or abs(outputRight/templateRight - 1) > 0.000001 or abs(outputTop/templateTop - 1) > 0.000001:
                    raise RuntimeError(_('The extent of the output raster %(output)s (%(ol)g, %(ob)g, %(or)g, %(ot)g) does not match the extent of the template raster %(template)s (%(tl)g, %(tb)g, %(tr)g, %(tt)g). This should not happen and indicates there may be a bug in this tool or ArcGIS. Please contact the author of this tool for assistance.') % {'output': outputRaster, 'template': templateRaster, 'ol': outputLeft, 'ob': outputBottom, 'or': outputRight, 'ot': outputTop, 'tl': templateLeft, 'tb': templateBottom, 'tr': templateRight, 'tt': templateTop})

            finally:
                del tempDir
        except:
            Logger.LogExceptionAsError()
            raise

    @classmethod
    def ToPolygons(cls, inputRaster, outputFeatureClass, simplify=True, field=None, projectedCoordinateSystem=None, geographicTransformation=None, resamplingTechnique=None, projectedCellSize=None, registrationPoint=None, clippingDataset=None, clippingRectangle=None, mapAlgebraExpression=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        
        # Perform additional validation.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        if mapAlgebraExpression is None and gp.Describe(inputRaster).PixelType.upper() not in ['U1', 'U2', 'U4', 'S8', 'U8', 'S16', 'U16', 'S32', 'U32', 'S64', 'U64']:
            Logger.RaiseException(RuntimeError(_('The input raster %(in)s is a floating-point raster. Only integer rasters can be converted to polygons. Please specify an integer raster or provide a map algebra expression that converts this one to an integer raster.') % {'in': inputRaster}))
        
        Logger.Info(_('Converting ArcGIS raster %(in)s to polygon feature class %(out)s...') % {'in' : inputRaster, 'out' : outputFeatureClass})
        try:
            # Perform requested pre-conversion processing in a temp directory.
            
            if projectedCoordinateSystem is not None or clippingRectangle is not None or mapAlgebraExpression is not None:
                cls._ValidateProjectClipAndOrExecuteMapAlgebraParameters(projectedCoordinateSystem, geographicTransformation, resamplingTechnique, projectedCellSize, registrationPoint, clippingDataset, clippingRectangle, mapAlgebraExpression)
                from .Directories import TemporaryDirectory
                tempDir = TemporaryDirectory()
                inputRaster = cls._ProjectClipAndOrExecuteMapAlgebraInTempDir(inputRaster, tempDir.Path,
                                                                              projectedCoordinateSystem=projectedCoordinateSystem,
                                                                              geographicTransformation=geographicTransformation,
                                                                              resamplingTechnique=resamplingTechnique,
                                                                              projectedCellSize=projectedCellSize,
                                                                              registrationPoint=registrationPoint,
                                                                              clippingDataset=clippingDataset,
                                                                              clippingRectangle=clippingRectangle,
                                                                              mapAlgebraExpression=mapAlgebraExpression)

                if mapAlgebraExpression is not None and gp.Describe(inputRaster).PixelType.upper() not in ['U1', 'U2', 'U4', 'S8', 'U8', 'S16', 'U16', 'S32', 'U32', 'S64', 'U64']:
                    Logger.RaiseException(RuntimeError(_('The map algebra expression yielded a floating-point raster. Only integer rasters can be converted to polygons. Please provide a map algebra expression that yields an integer raster.')))

            # Convert the raster to a polygon feature class.
            
            gp.RasterToPolygon_conversion(inputRaster, outputFeatureClass, 'SIMPLIFY' if simplify else 'NO_SIMPLIFY', field)

        except:
            Logger.LogExceptionAsError()
            raise

    @classmethod
    def ToPolygonOutlines(cls, inputRaster, outputFeatureClass, simplify=True, field=None, projectedCoordinateSystem=None, geographicTransformation=None, resamplingTechnique=None, projectedCellSize=None, registrationPoint=None, clippingDataset=None, clippingRectangle=None, mapAlgebraExpression=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Converting ArcGIS raster %(in)s to outlines in line feature class %(out)s...') % {'in' : inputRaster, 'out' : outputFeatureClass})
        try:
            try:
                # Convert the raster to a polygon feature class in a temp
                # directory.
                
                from .Directories import TemporaryDirectory
                tempDir = TemporaryDirectory()
                tempFeatureClass = os.path.join(tempDir.Path, 'polygons.shp')
                cls.ToPolygons(inputRaster,
                               tempFeatureClass,
                               simplify=simplify,
                               field=field,
                               projectedCoordinateSystem=projectedCoordinateSystem,
                               geographicTransformation=geographicTransformation,
                               resamplingTechnique=resamplingTechnique,
                               projectedCellSize=projectedCellSize,
                               registrationPoint=registrationPoint,
                               clippingDataset=clippingDataset,
                               clippingRectangle=clippingRectangle,
                               mapAlgebraExpression=mapAlgebraExpression,
                               overwriteExisting=overwriteExisting)

                # Convert the polygon feature class to a line feature class.

                gp = GeoprocessorManager.GetWrappedGeoprocessor()
                gp.FeatureToLine_management(tempFeatureClass, outputFeatureClass)

            except:
                Logger.LogExceptionAsError()
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def ToLines(cls, inputRaster, outputFeatureClass, backgroundValue='ZERO', minDangleLength=0.0, simplify=True, field=None, projectedCoordinateSystem=None, geographicTransformation=None, resamplingTechnique=None, projectedCellSize=None, registrationPoint=None, clippingDataset=None, clippingRectangle=None, mapAlgebraExpression=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        Logger.Info(_('Converting ArcGIS raster %(in)s to line feature class %(out)s...') % {'in' : inputRaster, 'out' : outputFeatureClass})
        try:
            # Perform requested pre-conversion processing in a temp directory.
            
            if projectedCoordinateSystem is not None or clippingRectangle is not None or mapAlgebraExpression is not None:
                cls._ValidateProjectClipAndOrExecuteMapAlgebraParameters(projectedCoordinateSystem, geographicTransformation, resamplingTechnique, projectedCellSize, registrationPoint, clippingDataset, clippingRectangle, mapAlgebraExpression)
                from .Directories import TemporaryDirectory
                tempDir = TemporaryDirectory()
                inputRaster = cls._ProjectClipAndOrExecuteMapAlgebraInTempDir(inputRaster, tempDir.Path,
                                                                              projectedCoordinateSystem=projectedCoordinateSystem,
                                                                              geographicTransformation=geographicTransformation,
                                                                              resamplingTechnique=resamplingTechnique,
                                                                              projectedCellSize=projectedCellSize,
                                                                              registrationPoint=registrationPoint,
                                                                              clippingDataset=clippingDataset,
                                                                              clippingRectangle=clippingRectangle,
                                                                              mapAlgebraExpression=mapAlgebraExpression)

            # Convert the raster to a line feature class.

            try:
                gp.RasterToPolyline_conversion(inputRaster, outputFeatureClass, backgroundValue, minDangleLength, 'SIMPLIFY' if simplify else 'NO_SIMPLIFY', field)
            except Exception as e:
                if str(e).lower().find('empty feature class') >= 0:
                    Logger.Warning(_('The raster %(raster)s is empty, so no lines can be created from it. Line feature class %(fc)s will be empty.') % {'raster': inputRaster, 'fc': outputFeatureClass})
                else:
                    raise

        except:
            Logger.LogExceptionAsError()
            raise

    @classmethod
    def ToPoints(cls, inputRaster, outputFeatureClass, field=None, projectedCoordinateSystem=None, geographicTransformation=None, resamplingTechnique=None, projectedCellSize=None, registrationPoint=None, clippingDataset=None, clippingRectangle=None, mapAlgebraExpression=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        Logger.Info(_('Converting ArcGIS raster %(in)s to point feature class %(out)s...') % {'in' : inputRaster, 'out' : outputFeatureClass})
        try:
            # Perform requested pre-conversion processing in a temp directory.
            
            if projectedCoordinateSystem is not None or clippingRectangle is not None or mapAlgebraExpression is not None:
                cls._ValidateProjectClipAndOrExecuteMapAlgebraParameters(projectedCoordinateSystem, geographicTransformation, resamplingTechnique, projectedCellSize, registrationPoint, clippingDataset, clippingRectangle, mapAlgebraExpression)
                from .Directories import TemporaryDirectory
                tempDir = TemporaryDirectory()
                inputRaster = cls._ProjectClipAndOrExecuteMapAlgebraInTempDir(inputRaster, tempDir.Path,
                                                                              projectedCoordinateSystem=projectedCoordinateSystem,
                                                                              geographicTransformation=geographicTransformation,
                                                                              resamplingTechnique=resamplingTechnique,
                                                                              projectedCellSize=projectedCellSize,
                                                                              registrationPoint=registrationPoint,
                                                                              clippingDataset=clippingDataset,
                                                                              clippingRectangle=clippingRectangle,
                                                                              mapAlgebraExpression=mapAlgebraExpression)

            # Convert the raster to a point feature class.
            
            gp.RasterToPoint_conversion(inputRaster, outputFeatureClass, field)

        except:
            Logger.LogExceptionAsError()
            raise


###############################################################################
# Metadata: module
###############################################################################

from ..ArcGIS import ArcGISDependency, ArcGISExtensionDependency
from ..Dependencies import PythonModuleDependency
from ..Datasets import Database, InsertCursor
from ..Metadata import *
from ..Types import *

AddModuleMetadata(shortDescription=_('Functions for common operations with rasters, implemented using ArcGIS\'s `arcpy <https://www.esri.com/en-us/arcgis/products/arcgis-python-libraries/libraries/arcpy>`__ Python package.'))

###############################################################################
# Metadata: ArcGISRaster class
###############################################################################

AddClassMetadata(ArcGISRaster,
    shortDescription=_('Functions for common operations with rasters, implemented using ArcGIS\'s `arcpy <https://www.esri.com/en-us/arcgis/products/arcgis-python-libraries/libraries/arcpy>`__ Python package.'))

# Public method: ArcGISRaster.Copy

AddMethodMetadata(ArcGISRaster.Copy,
    shortDescription=_('Copies an ArcGIS raster.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Copy Raster'),
    arcGISToolCategory=_('Data Management\\ArcGIS Rasters\\Copy'),
    dependencies=[ArcGISDependency()])

AddArgumentMetadata(ArcGISRaster.Copy, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=ArcGISRaster),
    description=_(':class:`%s` class or an instance of it.') % ArcGISRaster.__name__)

AddArgumentMetadata(ArcGISRaster.Copy, 'sourceRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_('Raster to copy.'),
    arcGISDisplayName=_('Source raster'))

AddArgumentMetadata(ArcGISRaster.Copy, 'destinationRaster',
    typeMetadata=ArcGISRasterTypeMetadata(mustBeDifferentThanArguments=['sourceRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Copy to create. If this is a file system path, missing directories in the
path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Destination raster'))

AddArgumentMetadata(ArcGISRaster.Copy, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the destination raster will be overwritten, if it exists. If
False, a :exc:`ValueError` will be raised if the destination raster
exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: ArcGISRaster.CopySilent

AddMethodMetadata(ArcGISRaster.CopySilent,
    shortDescription=_('Copies an ArcGIS raster and logs a debug message rather than an informational message.'),
    longDescription=_(
"""This method does the same thing as the :py:func:`ArcGISRaster.Copy` method,
except it logs a debug message rather than an informational message. It is
intended for use when the raster-copy operation is not imporant enough to
warrent notifying the user (for example, when an output raster is extracted
from a temporary directory to the final location)."""),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.CopySilent, 'cls')
CopyArgumentMetadata(ArcGISRaster.Copy, 'sourceRaster', ArcGISRaster.CopySilent, 'sourceRaster')
CopyArgumentMetadata(ArcGISRaster.Copy, 'destinationRaster', ArcGISRaster.CopySilent, 'destinationRaster')
CopyArgumentMetadata(ArcGISRaster.Copy, 'overwriteExisting', ArcGISRaster.CopySilent, 'overwriteExisting')

# Public method: ArcGISRaster.CreateXRaster

AddMethodMetadata(ArcGISRaster.CreateXRaster,
    shortDescription=_('Creates an ArcGIS raster where the value of each cell is the X coordinate of the cell.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create X Coordinate Raster'),
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Create Rasters'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy')])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.CreateXRaster, 'cls')

AddArgumentMetadata(ArcGISRaster.CreateXRaster, 'raster',
    typeMetadata=ArcGISRasterTypeMetadata(deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Raster to create. If this is a file system path, missing directories in the
path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output raster'))

AddArgumentMetadata(ArcGISRaster.CreateXRaster, 'extent',
    typeMetadata=EnvelopeTypeMetadata(),
    description=_("""Extent of the output raster."""),
    arcGISDisplayName=_('Extent'))

AddArgumentMetadata(ArcGISRaster.CreateXRaster, 'cellSize',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.0),
    description=_(
"""Cell size of the output raster. If the horizontal or vertical extents of
the raster are not evenly divisble by the cell size, the extents will be
increased right or up by the smallest amount needed to make them evenly
divisible. For example, if the horizontal extent runs from 0 to 25 and the
cell size is 2, the right extent will be increased to 26."""),
    arcGISDisplayName=_('Cell size'))

AddArgumentMetadata(ArcGISRaster.CreateXRaster, 'cellValue',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Center', 'Left', 'Right'], makeLowercase=True),
    description=_(
"""Value of the raster cells, either:

* ``Center`` - the X coordinate of the center of the cell.

* ``Left`` - the X coordinate of the left edge of the cell.

* ``Right`` - the X coordinate of the right edge of the cell.

"""),
    arcGISDisplayName=_('Cell value'))

AddArgumentMetadata(ArcGISRaster.CreateXRaster, 'coordinateSystem',
    typeMetadata=CoordinateSystemTypeMetadata(canBeNone=True),
    description=_(
"""Coordinate system to define for the raster. If not specified, a
coordinate system will not be defined."""),
    arcGISDisplayName=_('Coordinate system'))

AddArgumentMetadata(ArcGISRaster.CreateXRaster, 'buildPyramids',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, pyramids will be built for the raster, which will improve its
display speed in the ArcGIS user interface. Pyramids are built with the ArcGIS
:arcpy_management:`Build-Pyramids` tool."""),
    arcGISDisplayName=_('Build pyramids'))

AddArgumentMetadata(ArcGISRaster.CreateXRaster, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the raster will be overwritten, if it exists. If False, a
ValueError will be raised if the raster exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: ArcGISRaster.CreateYRaster

AddMethodMetadata(ArcGISRaster.CreateYRaster,
    shortDescription=_('Creates an ArcGIS raster where the value of each cell is the Y coordinate of the cell.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Y Coordinate Raster'),
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Create Rasters'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy')])

CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'cls', ArcGISRaster.CreateYRaster, 'cls')
CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'raster', ArcGISRaster.CreateYRaster, 'raster')
CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'extent', ArcGISRaster.CreateYRaster, 'extent')
CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'cellSize', ArcGISRaster.CreateYRaster, 'cellSize')

AddArgumentMetadata(ArcGISRaster.CreateYRaster, 'cellValue',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Center', 'Bottom', 'Top'], makeLowercase=True),
    description=_(
"""Value of the raster cells, either:

* ``Center`` - the X coordinate of the center of the cell.

* ``Bottom`` - the Y coordinate of the bottom edge of the cell.

* ``Top`` - the X coordinate of the top edge of the cell.

"""),
    arcGISDisplayName=_('Cell value'))

CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'coordinateSystem', ArcGISRaster.CreateYRaster, 'coordinateSystem')
CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'buildPyramids', ArcGISRaster.CreateYRaster, 'buildPyramids')
CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'overwriteExisting', ArcGISRaster.CreateYRaster, 'overwriteExisting')

# Public method: ArcGISRaster.Delete

AddMethodMetadata(ArcGISRaster.Delete,
    shortDescription=_('Deletes an ArcGIS raster.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Delete Raster'),
    arcGISToolCategory=_('Data Management\\ArcGIS Rasters\\Delete'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.Delete, 'cls')

AddArgumentMetadata(ArcGISRaster.Delete, 'raster',
    typeMetadata=ArcGISRasterTypeMetadata(),
    description=_("""Raster to delete."""),
    arcGISDisplayName=_('Raster'))

# Public method: ArcGISRaster.Exists

AddMethodMetadata(ArcGISRaster.Exists,
    shortDescription=_('Tests that a specified path exists and is recognized by ArcGIS as a raster.'))

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.Exists, 'cls')

AddArgumentMetadata(ArcGISRaster.Exists, 'path',
    typeMetadata=ArcGISRasterTypeMetadata(),
    description=_('Path to test.'))

AddResultMetadata(ArcGISRaster.Exists, 'result',
    typeMetadata=TupleTypeMetadata(elementType=BooleanTypeMetadata(), minLength=2, maxLength=2),
    description=_('A two-item :py:class:`tuple`, where the first item is True if the specified path exists, and the second is True if the specified path exists and is recognized by ArcGIS as a raster.'))

# Public method: ArcGISRaster.Find

AddMethodMetadata(ArcGISRaster.Find,
    shortDescription=_('Finds rasters in an ArcGIS workspace.'),
    longDescription=_(
"""Rasters are returned in an arbitrary order determined by ArcGIS."""),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.Find, 'cls')

AddArgumentMetadata(ArcGISRaster.Find, 'workspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(mustExist=True),
    description=_('Workspace to search.'),
    arcGISDisplayName=_('Workspace to search'))

AddArgumentMetadata(ArcGISRaster.Find, 'wildcard',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Wildcard expression specifying the rasters to find. Please see the
documentation for the ArcGIS :arcpy:`ListRasters` function for more
information about the syntax. At the time of this writing, only the ``*``
wildcard character was supported, which would match zero or more of any
character."""),
    arcGISDisplayName=_('Wildcard expression'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(ArcGISRaster.Find, 'searchTree',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, child workspaces will be searched.'),
    arcGISDisplayName=_('Search workspace tree'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(ArcGISRaster.Find, 'rasterType',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Type of rasters to find. If provided, only rasters of this type will be
found. At the time of this writing, the ArcGIS Pro 3.2 documentation specified
that any of the following strings would be accepted: ``All`` (the default),
``BMP``, ``GIF``, ``GRID``, ``IMG``, ``JP2``, ``JPG``, ``PNG``, ``TIFF``."""),
    arcGISDisplayName=_('Raster type'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(ArcGISRaster.Find, 'basePath',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Absolute path from which relative paths to the rasters will be calculated.
If provided, relative paths will be calculated and returned by this function.

For example, if the base path was::

    C:\\Data\\Rasters

the relative paths for the rasters::

    C:\\Data\\Rasters\\Group1\\r1
    C:\\Data\\Rasters\\r1
    C:\\Data\\r1
    C:\\r1
    D:\\r1
    \\\\MyServer\\Data\\r1

would be::    

    Group1\\r1
    r1
    ..\\r1
    ..\\..\\r1
    D:\\r1
    \\\\MyServer\\Data\\r1

"""))

AddArgumentMetadata(ArcGISRaster.Find, 'getExtent',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""'If True, the extent of each raster will be returned by this function. The
extent is represented by four floating point numbers: XMin, YMin, XMax, and
YMax."""))

_DateParsingExpressionSyntaxDocumentation = _(
"""The expression is a standard Python :py:ref:`re-syntax` with additional
codes for matching fragments of dates:

    ``%d`` - Day of the month as a decimal number (range: ``01`` to ``31``)

    ``%H`` - Hour (24-hour clock) as a decimal number (range: ``00`` to ``23``)

    ``%j`` - Day of the year as a decimal number (range: ``001`` to ``366``)

    ``%m`` - Month as a decimal number (range: ``01`` to ``12``)

    ``%M`` - Minute as a decimal number (range: ``00`` to ``59``)

    ``%S`` - Second as a decimal number (range: ``00`` to ``61``)

    ``%y`` - Year without century as a decimal number (range: ``00`` to ``99``)

    ``%Y`` - Year with century as a decimal number (range: ``0001`` to ``9999``)

    ``%%`` - A literal ``%`` character

A date is parsed from a path as follows:

1. The date fragment codes in your expression are replaced by regular
   expression groups to produce a true regular expression. For example, if
   your expression is ``%Y_%m_%d``, it is converted to the regular expression
   ``(\\d\\d\\d\\d)_(\\d\\d)_(\\d\\d)``.

2. :py:func:`re.search` is invoked to find the first occurrence of the regular
   expression in the path. The search proceeds from left to right.

3. If an occurrence is found, the regular expression groups are extracted and
   :py:func:`time.strptime` is invoked to parse a date from the groups.

Notes:

* Your expression must include at least one date fragment code, but it need
  not include all of them. If a particular code is missing, the following
  default values will be used: year ``1900``, month ``01``, day ``01``, hour
  ``00``, minute ``00``, second ``00``.

* You cannot specify a given date fragment code more than once.

* You cannot specify date fragment codes that might conflict. For example, you
  cannot specify both ``%j`` and ``%d`` because this could result in
  conflicting values for the day.

* For ``%y``, values ``00`` to ``68`` are interpreted as years ``2000``
  through ``2068``, while ``69`` through ``99`` are interpreted as years
  ``1969`` through ``1999``.

* Remember that the entire path is searched for your expression, from left to
  right. The first occurrence of it may be in the parent directories.

* The date fragment codes are case-sensitive.

* If the underlying storage format can hold the time as well as the date in a
  single field, the time will be stored along with the date. If the table
  cannot hold the time and date in a single field, then only the date will be
  stored. This is the case, for example, with dBASE III and IV tables (.dbf
  files), often used by ArcGIS.

* The timezone of the parsed date is assumed to be UTC.

Examples:

The expression::

    %Y%j

will parse dates from rasters namd with the year and day of year::

    C:\\SST\\Rasters\\2006\\sst2006001
    C:\\SST\\Rasters\\2006\\sst2006002
    C:\\SST\\Rasters\\2006\\sst2006003

Note that, in this example, the ``2006`` is parsed from the raster name, not
the ``2006`` directory, because the directory is not followed by a day of
year, it is followed by a backslash. The date parsing expression will only
match a year followed by a day of year.

""")

AddArgumentMetadata(ArcGISRaster.Find, 'dateParsingExpression',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""'Expression for parsing dates from the paths of each raster. If provided,
dates will be parsed from the paths of each raster using this expression and
returned by this function.

""") +
_DateParsingExpressionSyntaxDocumentation)

AddResultMetadata(ArcGISRaster.Find, 'rasters',
    typeMetadata=ListTypeMetadata(ListTypeMetadata(elementType=AnyObjectTypeMetadata())),
    description=_(
""":py:class:`list` of :py:class:`list`\\ s of the rasters that were found and
the requested metadata about them. The items of the inner :py:class:`list`\\ s
are:

* Path (:py:class:`str`) - always returned.

* Relative path (:py:class:`str`) - only returned if `basePath` is provided.

* XMin, YMin, XMax, YMax (:py:class:`float`) - only returned if `getExtent` is
  true.

* Parsed date (:py:class:`~datetime.datetime`) - only returned if
  `dateParsingExpression` is provided.

* Parsed UNIX time (:py:class:`int`) - only returned if
  `dateParsingExpression` is provided. It is the same value as the previous
  column, but in UNIX time format. UNIX times are 32-bit signed integers that
  are the number of seconds since 1970-01-01 00:00:00 UTC. This tool assumes
  the date that was parsed is in the UTC timezone. The UNIX time values
  produced by this tool do not include leap seconds; this tool assumes that a
  regular year is 31536000 seconds and a leap year is 31622400 seconds.

"""))

# Public method: ArcGISRaster.FindAndFillTable

AddMethodMetadata(ArcGISRaster.FindAndFillTable,
    shortDescription=_('Finds rasters within an ArcGIS workspace and inserts a row for each one into an existing table.'),
    longDescription=ArcGISRaster.Find.__doc__.Obj.LongDescription,
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.FindAndFillTable, 'cls')
CopyArgumentMetadata(ArcGISRaster.Find, 'workspace', ArcGISRaster.FindAndFillTable, 'workspace')

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'insertCursor',
    typeMetadata=ClassInstanceTypeMetadata(cls=InsertCursor),
    description=_('Insert cursor opened to the table that will receive the rows. The cursor will still be open when this function returns.'))

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'rasterField',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the field to receive absolute paths to the rasters that were found.'),
    arcGISDisplayName=_('File path field'))

CopyArgumentMetadata(ArcGISRaster.Find, 'wildcard', ArcGISRaster.FindAndFillTable, 'wildcard')
CopyArgumentMetadata(ArcGISRaster.Find, 'searchTree', ArcGISRaster.FindAndFillTable, 'searchTree')
CopyArgumentMetadata(ArcGISRaster.Find, 'rasterType', ArcGISRaster.FindAndFillTable, 'rasterType')

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'relativePathField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive paths of the rasters that were found, relative
to `basePath`. For example, if `basePath` was::

    C:\\Data\\Rasters

the relative paths for the rasters::

    C:\\Data\\Rasters\\Group1\\r1
    C:\\Data\\Rasters\\r1
    C:\\Data\\r1
    C:\\r1
    D:\\r1
    \\\\MyServer\\Data\\r1

would be::    

    Group1\\r1
    r1
    ..\\r1
    ..\\..\\r1
    D:\\r1
    \\\\MyServer\\Data\\r1

"""))

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'basePath',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Absolute path from which relative paths will be calculated and stored in
the `relativePathField`. Please see the documentation for that field for more
information."""))

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'populateExtentFields',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the fields named ``XMin``, ``YMin``, ``XMax``, and ``YMax`` will
be populated with the rasters' extents. If you populate these fields and store
the rasters' paths in a field named ``Image``, ArcGIS will treat your table as
an unmanaged raster catalog and enable additional functionality from the
ArcGIS user interface, such as time series animations."""),
    arcGISDisplayName=_('Populate XMin, YMin, XMax, and YMax fields'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'parsedDateField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive dates parsed from the paths of the rasters
that were found. You must also specify a date parsing expression."""),
    arcGISDisplayName=_('Parsed date field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'dateParsingExpression',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Expression for parsing dates from the paths of the rasters that were found.
The expression will be ignored if you do not also specify a field to receive
the dates or the equivalent UNIX time.

""") + _DateParsingExpressionSyntaxDocumentation,
    arcGISDisplayName=_('Date parsing expression'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(ArcGISRaster.FindAndFillTable, 'unixTimeField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive dates, in "UNIX time" format, parsed from the
paths of the rasters that were found. You must also specify a date parsing
expression.

UNIX times are 32-bit signed integers that are the number of seconds since
1970-01-01 00:00:00 UTC. This tool assumes the date that was parsed is in the
UTC timezone. The UNIX time values produced by this tool do not include leap
seconds; this tool assumes that a regular year is 31536000 seconds and a leap
year is 31622400 seconds."""),
    arcGISDisplayName=_('UNIX time field'),
    arcGISCategory=_('Output table options'))

# Public method: ArcGISRaster.FindAndCreateTable

AddMethodMetadata(ArcGISRaster.FindAndCreateTable,
    shortDescription=_('Finds rasters within an ArcGIS workspace and creates a table that lists them.'),
    longDescription=ArcGISRaster.Find.__doc__.Obj.LongDescription,
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.FindAndCreateTable, 'cls')
CopyArgumentMetadata(ArcGISRaster.Find, 'workspace', ArcGISRaster.FindAndCreateTable, 'workspace')

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'database',
    typeMetadata=ClassInstanceTypeMetadata(cls=Database),
    description=_('Database that will receive the new table.'))

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'table',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the table to create. The table must not exist.'))

CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'rasterField', ArcGISRaster.FindAndCreateTable, 'rasterField')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'wildcard', ArcGISRaster.FindAndCreateTable, 'wildcard')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'searchTree', ArcGISRaster.FindAndCreateTable, 'searchTree')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'rasterType', ArcGISRaster.FindAndCreateTable, 'rasterType')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'relativePathField', ArcGISRaster.FindAndCreateTable, 'relativePathField')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'basePath', ArcGISRaster.FindAndCreateTable, 'basePath')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'populateExtentFields', ArcGISRaster.FindAndCreateTable, 'populateExtentFields')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'parsedDateField', ArcGISRaster.FindAndCreateTable, 'parsedDateField')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'dateParsingExpression', ArcGISRaster.FindAndCreateTable, 'dateParsingExpression')
CopyArgumentMetadata(ArcGISRaster.FindAndFillTable, 'unixTimeField', ArcGISRaster.FindAndCreateTable, 'unixTimeField')

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'pathFieldsDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the file path fields. This should be
``string`` unless you have a specific reason to choose something else."""))

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'extentFieldsDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the raster extent fields (``XMin``,
``YMin``, ``XMax``, and ``YMax``). The fields will contain floating point
numbers, so the data type should either be ``float32`` or ``float64``,
depending on the range and precision required."""))

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'dateFieldsDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the file creation date, file modification
date, and parsed date fields. This should be ``datetime`` if the underlying
storage format supports dates with times, or ``date`` if only dates are
supported."""))

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'unixTimeFieldDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the UNIX date field. Because UNIX dates are
32-bit signed integers, this should be ``int32`` or ``int64``."""))

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'maxPathLength',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=1),
    description=_(
"""Maximum length of a path for this operating system. This value is used to
specify the width of the field that is created. You should provide a value
only if the underlying database requires that you specify a width for string
fields. If you provide a value that is too small to hold one of the paths that
is found, this function will fail when it finds that path."""))

AddArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output table will be overwritten, if it exists. If False, a
:py:exc:`ValueError` will be raised if the output table exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

AddResultMetadata(ArcGISRaster.FindAndCreateTable, 'createdTable',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the table that was created.'))

# Public method: ArcGISRaster.FindAndCreateArcGISTable

AddMethodMetadata(ArcGISRaster.FindAndCreateArcGISTable,
    shortDescription=_('Finds rasters within an ArcGIS workspace and creates a table that lists them.'),
    longDescription=ArcGISRaster.FindAndCreateTable.__doc__.Obj.LongDescription,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Find Rasters'),
    arcGISToolCategory=_('Data Management\\ArcGIS Rasters'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.FindAndCreateArcGISTable, 'cls')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'workspace', ArcGISRaster.FindAndCreateArcGISTable, 'inputWorkspace')

AddArgumentMetadata(ArcGISRaster.FindAndCreateArcGISTable, 'outputWorkspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(mustExist=True),
    description=_('Workspace in which the table should be created.'),
    arcGISDisplayName=_('Output workspace'))

AddArgumentMetadata(ArcGISRaster.FindAndCreateArcGISTable, 'table',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the table to create.

If the output workspace is a directory (rather than a database) a dBASE table
(.dbf file) will be created. It is not possible to create other types of
tables in the file system (e.g. comma or space-delimited text files). This
restriction is imposed by the ArcGIS :arcpy_management:`Create-Table` tool,
which is used to create the table. If you omit an extension from the table
name, .dbf will be added automatically. If you specify another extension, such
as .csv or .txt, it will be replaced with .dbf."""),
    arcGISDisplayName=_('Output table name'))

CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'rasterField', ArcGISRaster.FindAndCreateArcGISTable, 'rasterField')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'wildcard', ArcGISRaster.FindAndCreateArcGISTable, 'wildcard')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'searchTree', ArcGISRaster.FindAndCreateArcGISTable, 'searchTree')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'rasterType', ArcGISRaster.FindAndCreateArcGISTable, 'rasterType')

AddArgumentMetadata(ArcGISRaster.FindAndCreateArcGISTable, 'relativePathField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive paths of the rasters that were found, relative
to the database or directory that contains the output table. For example, if
the path to the table is::

    C:\\Data\\Rasters\\FoundRasters.dbf

the relative paths for the rasters::

    C:\\Data\\Rasters\\Group1\\r1
    C:\\Data\\Rasters\\r1
    C:\\Data\\r1
    C:\\r1
    D:\\r1
    \\\\MyServer\\Data\\r1

would be::    

    Group1\\r1
    r1
    ..\\r1
    ..\\..\\r1
    D:\\r1
    \\\\MyServer\\Data\\r1

If the table is in a File geodatabase::

    C:\\Data\\Rasters\\RasterInfo.gdb\\FoundRasters

the relative paths would be::    

    ..\\Group1\\r1
    ..\\r1
    ..\\..\\r1
    ..\\..\\..\\r1
    D:\\r1
    \\\\MyServer\\Data\\r1

"""),
    arcGISDisplayName=_('Relative path field'),
    arcGISCategory=_('Output table options'))

CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'populateExtentFields', ArcGISRaster.FindAndCreateArcGISTable, 'populateExtentFields')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'parsedDateField', ArcGISRaster.FindAndCreateArcGISTable, 'parsedDateField')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'dateParsingExpression', ArcGISRaster.FindAndCreateArcGISTable, 'dateParsingExpression')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'unixTimeField', ArcGISRaster.FindAndCreateArcGISTable, 'unixTimeField')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'maxPathLength', ArcGISRaster.FindAndCreateArcGISTable, 'maxPathLength')
CopyArgumentMetadata(ArcGISRaster.FindAndCreateTable, 'overwriteExisting', ArcGISRaster.FindAndCreateArcGISTable, 'overwriteExisting')

AddResultMetadata(ArcGISRaster.FindAndCreateArcGISTable, 'createdTable',
    typeMetadata=ArcGISTableTypeMetadata(),
    description=_('Table that was created.'),
    arcGISDisplayName=_('Output table'))

# Public method: ArcGISRaster.Move

AddMethodMetadata(ArcGISRaster.Move,
    shortDescription=_('Moves an ArcGIS raster.'),
    longDescription=ArcGISRaster.Copy.__doc__.Obj.LongDescription,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Move Raster'),
    arcGISToolCategory=_('Data Management\\ArcGIS Rasters\\Move'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.Move, 'cls')

AddArgumentMetadata(ArcGISRaster.Move, 'sourceRaster',
    typeMetadata=ArcGISRasterTypeMetadata(mustExist=True),
    description=_('Raster to move.'),
    arcGISDisplayName=_('Source raster'))

AddArgumentMetadata(ArcGISRaster.Move, 'destinationRaster',
    typeMetadata=ArcGISRasterTypeMetadata(mustBeDifferentThanArguments=['sourceRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""New path for the raster. If this is a file system path, missing directories
in the path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Destination raster'))

CopyArgumentMetadata(ArcGISRaster.Copy, 'overwriteExisting', ArcGISRaster.Move, 'overwriteExisting')

# Public method: ArcGISRaster.MoveSilent

AddMethodMetadata(ArcGISRaster.MoveSilent,
    shortDescription=_('Moves an ArcGIS raster and logs a debug message rather than an informational message.'),
    longDescription=_(
"""This method does the same thing as the :py:func:`ArcGISRaster.Move` method,
except it logs a debug message rather than an informational message. It is
intended for use when the raster-move operation is not imporant enough to
warrent notifying the user (for example, when an output raster is extracted
from a temporary directory to the final location)."""),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Move, 'cls', ArcGISRaster.MoveSilent, 'cls')
CopyArgumentMetadata(ArcGISRaster.Move, 'sourceRaster', ArcGISRaster.MoveSilent, 'sourceRaster')
CopyArgumentMetadata(ArcGISRaster.Move, 'destinationRaster', ArcGISRaster.MoveSilent, 'destinationRaster')
CopyArgumentMetadata(ArcGISRaster.Move, 'overwriteExisting', ArcGISRaster.MoveSilent, 'overwriteExisting')

# Public method: ArcGISRaster.FromNumpyArray

AddMethodMetadata(ArcGISRaster.FromNumpyArray,
    shortDescription=_('Creates an ArcGIS raster from a numpy array.'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy')])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.FromNumpyArray, 'cls')

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'numpyArray',
    typeMetadata=NumPyArrayTypeMetadata(dimensions=2, minShape=[1,1], allowedDTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']),
    description=_('Numpy array to write out as an ArcGIS raster.'))

CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'raster', ArcGISRaster.FromNumpyArray, 'raster')

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'xLowerLeftCorner',
    typeMetadata=FloatTypeMetadata(),
    description=_('X coordinate of the lower-left corner of the lower-left corner cell of the raster.'),
    arcGISDisplayName=_('X coordinate of lower-left corner'))

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'yLowerLeftCorner',
    typeMetadata=FloatTypeMetadata(),
    description=_('Y coordinate of the lower-left corner of the lower-left corner cell of the raster.'),
    arcGISDisplayName=_('Y coordinate of lower-left corner'))

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'cellSize',
    typeMetadata=FloatTypeMetadata(),
    description=_('Length and width of each cell, in the units of the raster\'s coordinate system. (ArcGIS requires the cells be square. It is not possible to specify a cell size for each dimension.)'),
    arcGISDisplayName=_('Cell size'))

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'noDataValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_('Value that indicates a cell has no data. If not specified, all cells are assumed to have data.'),
    arcGISDisplayName=_('NoData value'))

CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'coordinateSystem', ArcGISRaster.FromNumpyArray, 'coordinateSystem')

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'calculateStatistics',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, statistics will be calculated with GDAL. Calculating statistics is
usually a good idea for most raster formats because ArcGIS may only
display them with helpful colors and gradients if statistics have been
calculated. For certain formats, the explicit calculation of statistics is
not necessary because it happens automatically when the rasters are
created. If you're using one of those formats, you can set this option to
False to speed up the creation of the output rasters."""),
    arcGISDisplayName=_('Calculate statistics'))

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'buildRAT',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True and the raster uses an integer data type, raster attribute tables
(RATs) will be built for the output rasters using the ArcGIS
:arcpy_management:`Build Raster Attribute Table` tool. This option is ignored
if the output rasters use a floating point data type. Raster attribute tables
are essentially histograms: they store the counts of cells having each value.
If you do not need this information, you can skip the building of raster
attribute tables to speed up the creation of the output rasters. Note that for
certain raster formats, such as ArcInfo Binary Grid, the explicit buliding of
raster attribute tables is not necessary because it happens automatically when
the rasters are created."""),
    arcGISDisplayName=_('Build raster attribute tables'))

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'buildPyramids',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, pyramids will be built for the raster, which will improve its
display speed in the ArcGIS user interface. Pyramids are built with the ArcGIS
:arcpy_management:`Build-Pyramids` tool."""),
    arcGISDisplayName=_('Build pyramids'))

AddArgumentMetadata(ArcGISRaster.FromNumpyArray, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output raster will be overwritten, if it exists. If False, a
:exc:`ValueError` will be raised if the output raster exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: ArcGISRaster.ToNumpyArray

AddMethodMetadata(ArcGISRaster.ToNumpyArray,
    shortDescription=_('Reads an ArcGIS raster or raster layer into a numpy array.'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy')])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ToNumpyArray, 'cls')

AddArgumentMetadata(ArcGISRaster.ToNumpyArray, 'raster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_('Raster to read.'))

AddArgumentMetadata(ArcGISRaster.ToNumpyArray, 'band',
    typeMetadata=IntegerTypeMetadata(minValue=1),
    description=_('Band number to read, starting with 1.'))

AddResultMetadata(ArcGISRaster.ToNumpyArray, 'numpyArray',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(), minLength=2, maxLength=2),
    description=_(
"""A two-item tuple consisting of the numpy array read from the raster and the
value in that array that represents NoData.

Note: 
    For integer rasters, the numpy array will use the most compact data type
    that can represent all of the values in the raster. Normally, ArcGIS
    automatically selects the most compact data type, but this does not always
    happen. For example, I have seen ArcGIS store data ranging from 0 to 65535
    (with no NoData value) as an int32 raster even though a uint16 is the most
    compact data type for that range. If the numpy array is compacted, the
    NoData value may be different than what ArcGIS used when it created the
    raster.
"""))

# Public method: ArcGISRaster.ExtractByMask

AddMethodMetadata(ArcGISRaster.ExtractByMask,
    shortDescription=_('Extracts the cells of a raster that correspond to the areas defined by a mask.'),
    longDescription=_(
"""This function just calls the ArcGIS Spatial Analyst's
:arcpy_sa:`Extract-by-Mask` tool with the `extraction_area` set to ``INSIDE``.
This function only exists so that we can easily create a batched version of
that tool."""),
    isExposedAsArcGISTool=False,
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Extract By Mask'),
    dependencies=[ArcGISDependency(), ArcGISExtensionDependency('spatial')])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ExtractByMask, 'cls')

AddArgumentMetadata(ArcGISRaster.ExtractByMask, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_('The input raster from which cells will be extracted.'),
    arcGISDisplayName=_('Input raster'))

AddArgumentMetadata(ArcGISRaster.ExtractByMask, 'mask',
    typeMetadata=ArcGISGeoDatasetTypeMetadata(mustExist=True),
    description=_(
"""Input mask data defining areas to extract. This can be a raster or feature
dataset. When it is is a raster, NoData cells on it will be assigned NoData
values on the output raster."""),
    arcGISDisplayName=_('Input raster or feature mask data'))

AddArgumentMetadata(ArcGISRaster.ExtractByMask, 'outputRaster',
    typeMetadata=ArcGISRasterTypeMetadata(mustBeDifferentThanArguments=['inputRaster', 'mask'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""The output raster containing the cell values extracted from the input
raster. If this path refers to the file system, missing directories in the
path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output raster'))

CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'overwriteExisting', ArcGISRaster.ExtractByMask, 'overwriteExisting')

# Public method: ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra

AddMethodMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra,
    shortDescription=_('Projects, clips, and/or performs map algebra on an ArcGIS raster. You must request at least one of these three operations. If you request multiple operations, the tool performs them in the order they are listed.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Project, Clip, and/or Execute Map Algebra'),
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Project, Clip and/or Execute Map Algebra'),
    dependencies=[ArcGISDependency(), ArcGISExtensionDependency('spatial')])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'cls')

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_('Input raster.'),
    arcGISDisplayName=_('Input raster'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'outputRaster',
    typeMetadata=ArcGISRasterTypeMetadata(mustBeDifferentThanArguments=['inputRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output raster to create. If this path refers to the file system, missing
directories in the path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output raster'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'projectedCoordinateSystem',
    typeMetadata=CoordinateSystemTypeMetadata(canBeNone=True),
    description=_(
"""New coordinate system to project the raster to. The raster may only be
projected to a new coordinate system if the original projection is defined. An
error will be raised if you specify a new coordinate system without defining
the original coordinate system. The ArcGIS :arcpy_management:`Project-Raster`
tool is used to perform the projection. The documentation for that tool
recommends that you also specify a cell size for the new coordinate
system."""),
    arcGISDisplayName=_('Project to new coordinate system'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'geographicTransformation',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""A transformation method used to convert between the original coordinate
system and the new coordinate system.

This parameter is only needed when you specify that the raster should be
projected to a new coordinate system and that new system uses a different
datum than the original coordinate system, or there is some other difference
between the two coordinate systems that requires a transformation. To
determine if a transformation is needed:

* First, run this tool without specifying a new coordinate system, to obtain
  the raster in the original coordinate system.

* Next, use the ArcGIS :arcpy_management:`Project-Raster` tool on the raster
  to project it to the desired coordinate system. If a geographic
  transformation is needed, that tool will prompt you for one. Write down the
  exact name of the transformation you used.

* Finally, if a transformation was needed, type in the exact name into this
  tool, rerun it, and verify that the raster was projected as you desired.

"""),
    arcGISDisplayName=_('Geographic transformation'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'resamplingTechnique',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['NEAREST', 'BILINEAR', 'CUBIC'], canBeNone=True),
    description=_(
"""The resampling algorithm to be used to project the original raster to a new
coordinate system. The ArcGIS :arcpy_management:`Project-Raster` tool is used
to perform the projection and accepts the following values:

* ``NEAREST`` - `Nearest neighbor assignment
  <http://en.wikipedia.org/wiki/Nearest-neighbor_interpolation>`__.

* ``BILINEAR`` - `Bilinear interpolation
  <http://en.wikipedia.org/wiki/Bilinear_interpolation>`__.

* ``CUBIC`` - Cubic convolution, also known as `bicubic interpolation
  <http://en.wikipedia.org/wiki/Bicubic_interpolation>`__.

You must specify one of these algorithms to project to a new coordinate
system. An error will be raised if you specify a new coordinate system without
selecting an algorithm.

"""),
    arcGISDisplayName=_('Projection resampling technique'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'projectedCellSize',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""The cell size of the projected coordinate system. Although this parameter
is optional, to receive the best results, the ArcGIS documentation recommends
you always specify it when projecting to a new coordinate system."""),
    arcGISDisplayName=_('Cell size for projected coordinate system'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'registrationPoint',
    typeMetadata=PointTypeMetadata(canBeNone=True),
    description=_(
"""The x and y coordinates (in the projected coordinate system) used for cell
alignment. This parameter is ignored if you do not specify that the raster
should be projected to a new coordinate system."""),
    arcGISDisplayName=_('Registration point for projected coordinate system'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'clippingDataset',
    typeMetadata=ArcGISGeoDatasetTypeMetadata(mustExist=True, canBeNone=True),
    description=_(
"""Existing feature class, raster, or other geographic dataset having
the extent to which the raster should be clipped."""),
    arcGISDisplayName=_('Clip to extent of geographic dataset'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'clippingRectangle',
    typeMetadata=EnvelopeTypeMetadata(canBeNone=True),
    description=_(
"""Rectangle to which the raster should be clipped. This should only be given
if the clipping dataset parameter is omitted.

If a projected coordinate system was specified, the clipping is performed
after the projection and the rectangle's coordinates should be specified in
the projected coordinate system. If no projected coordinate system was
specified, the coordinates should be specified in the original coordinate
system.

The ArcGIS :arcpy_management:`Clip` tool is used to perform the clip. The
clipping rectangle must be passed to this tool as a string of four numbers
separated by spaces. The ArcGIS user interface automatically formats the
string properly; when invoking this tool from the ArcGIS UI, you need not
worry about the format. But when invoking it programmatically, take care to
provide a properly-formatted string. The numbers are ordered LEFT, BOTTOM,
RIGHT, TOP. For example, if the raster is in a geographic coordinate system,
it may be clipped to 10 W, 15 S, 20 E, and 25 N with the string ``'10 15 20 25'``.
Integers or decimal numbers may be provided.

"""),
    arcGISDisplayName=_('Clip to rectangle'))

AddArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'mapAlgebraExpression',
    typeMetadata=MapAlgebraExpressionTypeMetadata(canBeNone=True),
    description=_(
"""`Map algebra expression
<https://pro.arcgis.com/en/pro-app/latest/help/analysis/spatial-analyst/mapalgebra/what-is-map-algebra.htm>`__
to execute on the raster. The expression is executed after the converted
raster is projected and clipped (if those options are specified). Use
``inputRaster`` to represent the raster that you now want to perform map
algebra upon. For example, to convert the raster to an integer raster and add
1 to all of the cells, use the expression ``Int(inputRaster) + 1``. """),
    arcGISDisplayName=_('Execute map algebra expression'),
    dependencies=[ArcGISExtensionDependency('spatial')])

CopyArgumentMetadata(ArcGISRaster.FromNumpyArray, 'buildPyramids', ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'buildPyramids')
CopyArgumentMetadata(ArcGISRaster.FromNumpyArray, 'overwriteExisting', ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'overwriteExisting')

# Public method: ArcGISRaster.ProjectToTemplate

AddMethodMetadata(ArcGISRaster.ProjectToTemplate,
    shortDescription=_('Projects a raster to the coordinate system, cell size, and extent of a template raster.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Project Raster to Template'),
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Project Raster to Template'),
    dependencies=[ArcGISDependency(), ArcGISExtensionDependency('spatial')])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ProjectToTemplate, 'cls')

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Raster to project to the template raster's coordinate system, cell size,
and extent."""),
    arcGISDisplayName=_('Raster to project'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'templateRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Raster defining the coordinate system, cell size, and extent of the output
raster."""),
    arcGISDisplayName=_('Template raster'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'outputRaster',
    typeMetadata=ArcGISRasterTypeMetadata(mustBeDifferentThanArguments=['inputRaster', 'templateRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output raster to create. If this path refers to the file system, missing
directories in the path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output raster'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'resamplingTechnique',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True, allowedValues=['NEAREST', 'BILINEAR', 'CUBIC', 'MAJORITY']),
    description=_(
"""Resampling algorithm to be used to project the input raster to the template
raster's coordinate system. One of:

* ``NEAREST`` - `Nearest neighbor assignment
  <http://en.wikipedia.org/wiki/Nearest-neighbor_interpolation>`__.

* ``BILINEAR`` - `Bilinear interpolation
  <http://en.wikipedia.org/wiki/Bilinear_interpolation>`__.

* ``CUBIC`` - Cubic convolution, also known as `bicubic interpolation
  <http://en.wikipedia.org/wiki/Bicubic_interpolation>`__.

* ``MAJORITY`` - Majority resampling. This method requires ArcGIS 9.3 or
  later.

The ``NEAREST`` and ``MAJORITY`` algorithms should be used for categorical
data, such as a land use classification. It is not recommended that ``NEAREST`` or
``MAJORITY`` be used for continuous data, such as elevation surfaces.

The ``BILINEAR`` and ``CUBIC`` options are most appropriate for continuous
data. Do not use ``BILINEAR`` or ``CUBIC`` with categorical data.

The projection is accomplished with the ArcGIS
:arcpy_management:`Project-Raster` tool. Please see the documentation for that
tool for more information."""),
    arcGISDisplayName=_('Resampling technique'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'interpolationMethod',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True, allowedValues=['Del2a', 'Del2b', 'Del2c', 'Del4', 'Spring'], canBeNone=True),
    description=_(
"""Method to use to guess values for NoData cells.

Use this option to "fill in" clusters of NoData cells with values obtained by
interpolation and extrapolation. This option is appropriate for rasters
representing continuous surfaces, e.g. images of sea surface temperature in
which cloudy cells contain NoData. It uses algorithms based on differential
calculus that may provide more accurate guesses than traditional ArcGIS
approaches, such as computing the focal mean of a 3x3 neighborhood.

This option is not appropriate for rasters representing categorical data, such
as land cover classifications. Therefore, in order to use this option, you
must select ``BILINEAR`` or ``CUBIC`` for the Resampling Technique parameter.

The available algorithms are:

* ``Del2a`` - Laplacian interpolation and linear extrapolation.

* ``Del2b`` - Same as ``Del2a`` but does not build as large a linear system of
  equations. May be faster than ``Del2a`` at the cost of some accuracy.

* ``Del2c`` - Same as ``Del2a`` but solves a direct linear system of equations
  for the NoData values. Faster than both ``Del2a`` and ``Del2b`` but is the
  least robust to noise on the boundaries of NoData cells and least able to
  interpolate accurately for smooth surfaces.

* ``Del4`` - Same as ``Del2a`` but instead of the Laplace operator (also
  called the ∇\\ :sup:`2` operator) it uses the biharmonic operator (also
  called the ∇\\ :sup:`4` operator). May result in more accurate
  interpolations, at some cost in speed.

* ``Spring`` - Uses a spring metaphor. Assumes springs (with a nominal length
  of zero) connect each cell with every neighbor (horizontally, vertically and
  diagonally). Since each cell tries to be like its neighbors, extrapolation
  is as a constant function where this is consistent with the neighboring
  nodes.

This option is applied after the input raster has been projected to the
coordinate system and cell size of the template raster.

Although this tool can fill NoData clusters of any size, you should apply
common sense when using it. The larger the cluster, the less accurate the
guessed values will be, especially for rasters that represent a noisy surface.

Thanks to John D'Errico for providing the code that implements the
mathematical algorithms described here (click `here
<http://www.mathworks.com/matlabcentral/fileexchange/4551>`__ for more
information)."""),
    arcGISDisplayName=_('Method for interpolating NoData cells'),
    arcGISCategory=_('Interpolation and masking options'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'maxHoleSize',
    typeMetadata=IntegerTypeMetadata(mustBeGreaterThan=0, canBeNone=True),
    description=_(
"""Maximum size, in cells of the template raster, that a region of 4-connected
NoData cells may be for it to be filled in. Use this option to prevent the
filling of large NoData regions (e.g. large clouds in remote sensing images)
when you are concerned that values cannot be accurately guessed for those
regions. If this option is omitted, all regions will be filled, regardless of
size."""),
    arcGISDisplayName=_('Maximum size of NoData regions to interpolate'),
    arcGISCategory=_('Interpolation and masking options'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'mask',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the template raster will be used to mask the input raster after it
has been projected to the template raster's coordinate system and values have
been interpolated for NoData cells (if your requested that). Cells of the
template raster that are NoData will be set to NoData in the output raster,
even if you requested that values be interpolated for NoData cells. This is
appropriate in situations where the template defines the areas for which you
want to retain data; for example, when you are analyzing the ocean and you
have a mask in which ocean cells have data and land cells are set to NoData.

If False, the template raster will only be used to define the coordinate
system, cell size, and rectangular extent of the output raster, and no masking
will be done."""),
    arcGISDisplayName=_('Use template raster as mask'),
    arcGISCategory=_('Interpolation and masking options'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'minValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Minimum allowed value to use when NoData cells are interpolated (or
extrapolated). This parameter is ignored if an interpolation method is not
specified.

If this parameter is provided, all cells with less than the minimum value will
be rounded up to the minimum. This includes not just the cells that had NoData
in the input raster and were then interpolated or extrapolated, but also the
cells that did have values in the input raster.

Use this parameter when the interpolation/extrapolation algorithm produces
impossibly low values. For example, consider a situation in which a
chlorophyll concentration raster coincidentally shows a negative gradient
approaching a cloud that straddles the edge of the raster. Missing cells at
the edge of the raster will be filled by extrapolation. If the negative
gradient is strong enough, the algorithm might extrapolate negative
concentrations for the cloudy cells. This should be impossible; chlorophyll
concentration must be zero or higher. To enforce that, you could specify a
minimum value of zero (or a very small non-zero number, if exactly zero would
be problematic, as might occur if the values were in a log scale)."""),
    arcGISDisplayName=_('Minimum value'),
    arcGISCategory=_('Interpolation and masking options'))

AddArgumentMetadata(ArcGISRaster.ProjectToTemplate, 'maxValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Maximum allowed value to use when NoData cells are interpolated (or
extrapolated). This parameter is ignored if an interpolation method is not
specified.

If this parameter is provided, all cells with greater than the maximum value
will be rounded up to the maximum. This includes not just the cells that had
NoData in the input raster and were then interpolated or extrapolated, but
also the cells that did have values in the input raster.

Use this parameter when the interpolation/extrapolation algorithm produces
impossibly high values. For example, consider a situation in which a percent
sea ice concentration raster shows a positive gradient approaching the
coastline but does not provide data right up to shore. Say you wanted to fill
the missing cells close to shore and were willing to assume that whatever
gradient occurred nearby was reasonable for filling them in. If the positive
gradient is strong enough, the algorithm might extrapolate ice concentration
values greater than 100 percent, which is impossible. To prevent values from
exceeding 100 percent, you could specify a maximum value of 100."""),
    arcGISDisplayName=_('Maximum value'),
    arcGISCategory=_('Interpolation and masking options'))

CopyArgumentMetadata(ArcGISRaster.CreateXRaster, 'overwriteExisting', ArcGISRaster.ProjectToTemplate, 'overwriteExisting')

# Public method: ArcGISRaster.ToPolygons

AddMethodMetadata(ArcGISRaster.ToPolygons,
    shortDescription=_('Converts an ArcGIS raster to polygons that encompass groups of adjacent raster cells having the same value.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Convert ArcGIS Raster to Polygons'),
    arcGISToolCategory=_('Conversion\\To Table, Shapefile, or Feature Class\\To Polygons\\From ArcGIS Raster'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ToPolygons, 'cls')

AddArgumentMetadata(ArcGISRaster.ToPolygons, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Raster to convert. The raster will be converted to a polygon feature class
using the ArcGIS :arcpy_conversion:`Raster-to-Polygon` tool. That tool can
only convert integer rasters to polygons. If the input raster is a
floating-point raster, you must use the Map Algebra Expression parameter to
convert it to an integer raster."""),
    arcGISDisplayName=_('Input raster'))

AddArgumentMetadata(ArcGISRaster.ToPolygons, 'outputFeatureClass',
    typeMetadata=ArcGISFeatureClassTypeMetadata(allowedShapeTypes=['polygon'], mustBeDifferentThanArguments=['inputRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output polygon feature class that will contain the converted polygons.
Missing directories in this path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output polygon feature class'))

AddArgumentMetadata(ArcGISRaster.ToPolygons, 'simplify',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""Determines if the output polygons will be smoothed into simpler shapes or
conform to the input raster's cell edges.

* True - The polygons will be smoothed into simpler shapes. This is the
  default.

* False - The polygons will conform to the input raster's cell edges.

"""),
    arcGISDisplayName=_('Simplify polygons'))

AddArgumentMetadata(ArcGISRaster.ToPolygons, 'field',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'string'], canBeNone=True),
    description=_(
"""The field used to assign values from the cells in the input raster to the
polygons in the output dataset. It can be an integer or a string field."""),
    arcGISParameterDependencies=['inputRaster'],
    arcGISDisplayName=_('Field'))

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'projectedCoordinateSystem', ArcGISRaster.ToPolygons, 'projectedCoordinateSystem')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('projectedCoordinateSystem').ArcGISCategory = _('Pre-conversion processing')

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'geographicTransformation', ArcGISRaster.ToPolygons, 'geographicTransformation')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('geographicTransformation').ArcGISCategory = _('Pre-conversion processing')

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'resamplingTechnique', ArcGISRaster.ToPolygons, 'resamplingTechnique')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('resamplingTechnique').ArcGISCategory = _('Pre-conversion processing')

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'projectedCellSize', ArcGISRaster.ToPolygons, 'projectedCellSize')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('projectedCellSize').ArcGISCategory = _('Pre-conversion processing')

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'registrationPoint', ArcGISRaster.ToPolygons, 'registrationPoint')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('registrationPoint').ArcGISCategory = _('Pre-conversion processing')

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'clippingDataset', ArcGISRaster.ToPolygons, 'clippingDataset')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('clippingDataset').ArcGISCategory = _('Pre-conversion processing')

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'clippingRectangle', ArcGISRaster.ToPolygons, 'clippingRectangle')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('clippingRectangle').ArcGISCategory = _('Pre-conversion processing')

CopyArgumentMetadata(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra, 'mapAlgebraExpression', ArcGISRaster.ToPolygons, 'mapAlgebraExpression')
ArcGISRaster.ToPolygons.__doc__.Obj.GetArgumentByName('mapAlgebraExpression').ArcGISCategory = _('Pre-conversion processing')

AddArgumentMetadata(ArcGISRaster.ToPolygons, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output feature class will be overwritten, if it exists. If
False, a :exc:`ValueError` will be raised if the output feature class
exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: ArcGISRaster.ToPolygonOutlines

AddMethodMetadata(ArcGISRaster.ToPolygonOutlines,
    shortDescription=_('Converts an ArcGIS raster to lines that outline groups of adjacent raster cells having the same value.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Convert ArcGIS Raster to Polygon Outlines'),
    arcGISToolCategory=_('Conversion\\To Table, Shapefile, or Feature Class\\To Polygon Outlines\\From ArcGIS Raster'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ToPolygonOutlines, 'cls')

AddArgumentMetadata(ArcGISRaster.ToPolygonOutlines, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Raster to convert. The raster will be converted to a polygon feature class
using the ArcGIS :arcpy_conversion:`Raster-to-Polygon` tool, and then to line
features using the :arcpy_management:`Feature-to-Line` tool. The Raster to
Polygon tool can only convert integer rasters to polygons. If the input raster
is a floating-point raster, you must use the Map Algebra Expression parameter
to convert it to an integer raster."""),
    arcGISDisplayName=_('Input raster'))

AddArgumentMetadata(ArcGISRaster.ToPolygonOutlines, 'outputFeatureClass',
    typeMetadata=ArcGISFeatureClassTypeMetadata(allowedShapeTypes=['polyline'], mustBeDifferentThanArguments=['inputRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output line feature class. If this is a file system path, missing
directories in the path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output line feature class'))

CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'simplify', ArcGISRaster.ToPolygonOutlines, 'simplify')

AddArgumentMetadata(ArcGISRaster.ToPolygonOutlines, 'field',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'string'], canBeNone=True),
    description=_(
"""The field used to assign values from the cells in the input raster to the
lines in the output dataset. It can be an integer or a string field."""),
    arcGISParameterDependencies=['inputRaster'],
    arcGISDisplayName=_('Field'))

CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'projectedCoordinateSystem', ArcGISRaster.ToPolygonOutlines, 'projectedCoordinateSystem')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'geographicTransformation', ArcGISRaster.ToPolygonOutlines, 'geographicTransformation')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'resamplingTechnique', ArcGISRaster.ToPolygonOutlines, 'resamplingTechnique')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'projectedCellSize', ArcGISRaster.ToPolygonOutlines, 'projectedCellSize')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'registrationPoint', ArcGISRaster.ToPolygonOutlines, 'registrationPoint')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'clippingDataset', ArcGISRaster.ToPolygonOutlines, 'clippingDataset')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'clippingRectangle', ArcGISRaster.ToPolygonOutlines, 'clippingRectangle')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'mapAlgebraExpression', ArcGISRaster.ToPolygonOutlines, 'mapAlgebraExpression')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'overwriteExisting', ArcGISRaster.ToPolygonOutlines, 'overwriteExisting')

# Public method: ArcGISRaster.ToLines

AddMethodMetadata(ArcGISRaster.ToLines,
    shortDescription=_('Converts an ArcGIS raster to a feature class of lines that connect adjacent foreground raster cells.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Convert ArcGIS Raster to Lines'),
    arcGISToolCategory=_('Conversion\\To Table, Shapefile, or Feature Class\\To Lines\\From ArcGIS Raster'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ToLines, 'cls')

AddArgumentMetadata(ArcGISRaster.ToLines, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Raster to convert. The raster will be converted to a line feature class
using the ArcGIS Raster to Polyline tool. For each pair of adjacent foreground
raster cells, the tool draws a line connecting their centers. This algorithm
is appropriate for converting line-like raster features, such as sea surface
temperature fronts or other boundary data, into vector features."""),
    arcGISDisplayName=_('Input raster'))

AddArgumentMetadata(ArcGISRaster.ToLines, 'outputFeatureClass',
    typeMetadata=ArcGISFeatureClassTypeMetadata(allowedShapeTypes=['polyline'], mustBeDifferentThanArguments=['inputRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output polygon feature class that will contain the converted lines. If this
is a file system path, missing directories in the path will be created if they
do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output line feature class'))

AddArgumentMetadata(ArcGISRaster.ToLines, 'backgroundValue',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['ZERO', 'NODATA'], makeLowercase=True),
    description=_(
"""Specifies the cell value that will identify the background cells. The
raster dataset is viewed as a set of foreground cells and background cells.
The linear features are formed from the foreground cells.

* ``ZERO`` - The background is composed of cells of zero or less or NoData.
  All cells with a value greater than zero are considered a foreground value.

* ``NODATA`` - The background is composed of NoData cells. All cells with
  valid values belong to the foreground.

"""),
    arcGISDisplayName=_('Background value'))

AddArgumentMetadata(ArcGISRaster.ToLines, 'minDangleLength',
    typeMetadata=FloatTypeMetadata(minValue=0.0),
    description=_(
"""Minimum length of dangling lines that will be retained. The default is
zero."""),
    arcGISDisplayName=_('Minimum dangle length'))

AddArgumentMetadata(ArcGISRaster.ToLines, 'simplify',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True (the default) the output lines will be smoothed according to an
undocumented algorithm implemented by the ArcGIS
:arcpy_conversion:`Raster-to-Polyline` tool."""),
    arcGISDisplayName=_('Simplify lines'))

CopyArgumentMetadata(ArcGISRaster.ToPolygonOutlines, 'field', ArcGISRaster.ToLines, 'field')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'projectedCoordinateSystem', ArcGISRaster.ToLines, 'projectedCoordinateSystem')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'geographicTransformation', ArcGISRaster.ToLines, 'geographicTransformation')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'resamplingTechnique', ArcGISRaster.ToLines, 'resamplingTechnique')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'projectedCellSize', ArcGISRaster.ToLines, 'projectedCellSize')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'registrationPoint', ArcGISRaster.ToLines, 'registrationPoint')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'clippingDataset', ArcGISRaster.ToLines, 'clippingDataset')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'clippingRectangle', ArcGISRaster.ToLines, 'clippingRectangle')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'mapAlgebraExpression', ArcGISRaster.ToLines, 'mapAlgebraExpression')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'overwriteExisting', ArcGISRaster.ToLines, 'overwriteExisting')

# Public method: ArcGISRaster.ToPoints

AddMethodMetadata(ArcGISRaster.ToPoints,
    shortDescription=_('Converts an ArcGIS raster to a feature class of points that occur at the centers of the raster cells.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Convert ArcGIS Raster to Points'),
    arcGISToolCategory=_('Conversion\\To Table, Shapefile, or Feature Class\\To Points\\From ArcGIS Raster'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(ArcGISRaster.Copy, 'cls', ArcGISRaster.ToPoints, 'cls')

AddArgumentMetadata(ArcGISRaster.ToPoints, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Raster to convert. The raster will be converted to a point feature class
using the ArcGIS :arcpy_conversion:`Raster-to-Point` tool. This tool creates a
point at the center of each raster cell, except noData cells."""),
    arcGISDisplayName=_('Input raster'))

AddArgumentMetadata(ArcGISRaster.ToPoints, 'outputFeatureClass',
    typeMetadata=ArcGISFeatureClassTypeMetadata(allowedShapeTypes=['point'], mustBeDifferentThanArguments=['inputRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output point feature class. If this is a file system path, missing
directories in the path will be created if they do not exist."""),
    direction='Output',
    arcGISDisplayName=_('Output point feature class'))

AddArgumentMetadata(ArcGISRaster.ToPoints, 'field',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'string'], canBeNone=True),
    description=_(
"""The field used to assign values from the cells in the input raster to the
points in the output dataset. It can be an integer, floating-point, or string
field."""),
    arcGISParameterDependencies=['inputRaster'],
    arcGISDisplayName=_('Field'))

CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'projectedCoordinateSystem', ArcGISRaster.ToPoints, 'projectedCoordinateSystem')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'geographicTransformation', ArcGISRaster.ToPoints, 'geographicTransformation')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'resamplingTechnique', ArcGISRaster.ToPoints, 'resamplingTechnique')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'projectedCellSize', ArcGISRaster.ToPoints, 'projectedCellSize')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'registrationPoint', ArcGISRaster.ToPoints, 'registrationPoint')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'clippingDataset', ArcGISRaster.ToPoints, 'clippingDataset')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'clippingRectangle', ArcGISRaster.ToPoints, 'clippingRectangle')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'mapAlgebraExpression', ArcGISRaster.ToPoints, 'mapAlgebraExpression')
CopyArgumentMetadata(ArcGISRaster.ToPolygons, 'overwriteExisting', ArcGISRaster.ToPoints, 'overwriteExisting')

###############################################################################
# Batch processing versions of methods
###############################################################################

from GeoEco.BatchProcessing import BatchProcessing
from GeoEco.DataManagement.Fields import Field

BatchProcessing.GenerateForMethod(ArcGISRaster.Copy,
    inputParamNames=['sourceRaster'],
    inputParamFieldArcGISDisplayNames=[_('Source raster field')],
    inputParamDescriptions=[_('%s rasters to copy.')],
    outputParamNames=['destinationRaster'],
    outputParamFieldArcGISDisplayNames=[_('Destination raster field')],
    outputParamExpressionArcGISDisplayNames=[_('Destination raster Python expression')],
    outputParamDescriptions=[_('%s destination rasters.')],
    outputParamExpressionDescriptions=[
"""Python expression used to calculate the absolute path of a destination
raster. The expression may be any Python statement appropriate for passing to
the eval function and must return a string. The expression may reference the
following variables:

* ``workspaceToSearch`` - the value provided for the workspace to search
  parameter

* ``destinationWorkspace`` - the value provided for the destination workspace
  parameter

* ``sourceRaster`` - the absolute path to the source raster

The default expression,
``os.path.join(destinationWorkspace, sourceRaster[len(workspaceToSearch)+1:])``,
stores the raster in the destination workspace at the same relative location
it appears in the workspace to search. The destination path is calculated by
stripping the workspace to search from the source path and replacing it with
the destination workspace.

For more information on Python syntax, please see the `Python documentation
<http://www.python.org/doc/>`__."""],
    outputParamDefaultExpressions=['os.path.join(destinationWorkspace, sourceRaster[len(workspaceToSearch)+1:])'],
    processListMethodName='CopyList',
    processListMethodShortDescription=_('Copies a list of ArcGIS rasters.'),
    processTableMethodName='CopyTable',
    processTableMethodShortDescription=_('Copies the ArcGIS rasters listed in a table.'),
    processArcGISTableMethodName='CopyArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Copy Rasters Listed in Table'),
    findAndProcessMethodName='FindAndCopy',
    findAndProcessMethodArcGISDisplayName='Find and Copy Rasters',
    findAndProcessMethodShortDescription=_('Finds and copies rasters in an ArcGIS workspace.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive copies of the rasters.'),
    outputLocationParamArcGISDisplayName=_('Destination workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    destinationWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['sourceRaster = row.sourceRaster']],
    calculatedOutputsArcGISCategory=_('Destination raster name options'),
    skipExistingDescription=_('If True, copying will be skipped for destination rasters that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing destination rasters will be overwritten.'))

BatchProcessing.GenerateForMethod(ArcGISRaster.Delete,
    inputParamNames=['raster'],
    inputParamFieldArcGISDisplayNames=[_('Raster field')],
    inputParamDescriptions=[_('%s rasters to delete.')],
    processListMethodName='DeleteList',
    processListMethodShortDescription=_('Deletes a list of ArcGIS rasters.'),
    processTableMethodName='DeleteTable',
    processTableMethodShortDescription=_('Deletes the ArcGIS rasters listed in a table.'),
    processArcGISTableMethodName='DeleteArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Delete Rasters Listed in Table'),
    findAndProcessMethodName='FindAndDelete',
    findAndProcessMethodArcGISDisplayName='Find and Delete Rasters',
    findAndProcessMethodShortDescription=_('Finds and deletes rasters in an ArcGIS workspace.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'])

BatchProcessing.GenerateForMethod(ArcGISRaster.Move,
    inputParamNames=['sourceRaster'],
    inputParamFieldArcGISDisplayNames=[_('Source raster field')],
    inputParamDescriptions=[_('%s rasters to move.')],
    outputParamNames=['destinationRaster'],
    outputParamFieldArcGISDisplayNames=[_('Destination raster field')],
    outputParamExpressionArcGISDisplayNames=[_('Destination raster Python expression')],
    outputParamDescriptions=[_('%s destination rasters.')],
    outputParamExpressionDescriptions=[ArcGISRaster.FindAndCopy.__doc__.Obj.GetArgumentByName('destinationRasterPythonExpression').Description],
    outputParamDefaultExpressions=[ArcGISRaster.FindAndCopy.__doc__.Obj.GetArgumentByName('destinationRasterPythonExpression').Default],
    processListMethodName='MoveList',
    processListMethodShortDescription=_('Moves a list of ArcGIS rasters.'),
    processTableMethodName='MoveTable',
    processTableMethodShortDescription=_('Moves the ArcGIS rasters listed in a table.'),
    processArcGISTableMethodName='MoveArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Move Rasters Listed in Table'),
    findAndProcessMethodName='FindAndMove',
    findAndProcessMethodArcGISDisplayName='Find and Move Rasters',
    findAndProcessMethodShortDescription=_('Finds and moves rasters in an ArcGIS workspace.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the rasters.'),
    outputLocationParamArcGISDisplayName=_('Destination workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    destinationWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['sourceRaster = row.sourceRaster']],
    calculatedOutputsArcGISCategory=_('Destination raster name options'),
    skipExistingDescription=_('If True, moving will be skipped for destination rasters that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing destination rasters will be overwritten.'))

_OutputRasterParamExpressionDescription = _(
"""Python expression used to calculate the absolute path of an output raster.
The expression may be any Python statement appropriate for passing to the eval
function and must return a string. The expression may reference the following
variables:

* ``workspaceToSearch`` - the value provided for the workspace to search
  parameter

* ``outputWorkspace`` - the value provided for the output workspace parameter

* ``inputRaster`` - the absolute path to the input raster

The default expression,
``os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])``,
stores the output rasters in the output workspace at the same relative
location as the input rasters appear in the workspace to search. The output
raster path is calculated by stripping the workspace to search from the input
raster path and replacing it with the output workspace.

For more information on Python syntax, please see the `Python documentation
<http://www.python.org/doc/>`__.""")

BatchProcessing.GenerateForMethod(ArcGISRaster.ExtractByMask,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_('%s input rasters.')],
    outputParamNames=['outputRaster'],
    outputParamFieldArcGISDisplayNames=[_('Output raster field')],
    outputParamExpressionArcGISDisplayNames=[_('Output raster Python expression')],
    outputParamDescriptions=[_(
"""%s output rasters to receive the cell values extracted from the input
rasters. If these paths refers to the file system, missing directories in the
paths will be created if they do not exist.""")],
    outputParamExpressionDescriptions=[_OutputRasterParamExpressionDescription],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['mask'],
    processListMethodName='ExtractByMaskList',
    processListMethodShortDescription=_('For each ArcGIS raster in a list, extracts the cells that correspond to the areas defined by a mask.'),
    processTableMethodName='ExtractByMaskTable',
    processTableMethodShortDescription=_('For each ArcGIS raster in a table, extracts the cells that correspond to the areas defined by a mask.'),
    processArcGISTableMethodName='ExtractByMaskArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Extract By Mask for ArcGIS Rasters Listed in Table'),
    findAndProcessMethodName='FindAndExtractByMask',
    findAndProcessMethodArcGISDisplayName='Find ArcGIS Rasters and Extract By Mask',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and extracts the cells that correspond to the areas defined by a mask.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the output rasters.'),
    outputLocationParamArcGISDisplayName=_('Output workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    outputWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['inputRaster = row.inputRaster']],
    calculatedOutputsArcGISCategory=_('Output raster name options'),
    skipExistingDescription=_('If True, processing will be skipped for output rasters that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing output rasters will be overwritten.'))

BatchProcessing.GenerateForMethod(ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_('%s input rasters.')],
    outputParamNames=['outputRaster'],
    outputParamFieldArcGISDisplayNames=[_('Output raster field')],
    outputParamExpressionArcGISDisplayNames=[_('Output raster Python expression')],
    outputParamDescriptions=[_(
"""%s output rasters. If these paths refers to the file system, missing
directories in the paths will be created if they do not exist.""")],
    outputParamExpressionDescriptions=[_OutputRasterParamExpressionDescription],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['projectedCoordinateSystem', 'geographicTransformation', 'resamplingTechnique', 'projectedCellSize', 'registrationPoint', 'clippingDataset', 'clippingRectangle', 'mapAlgebraExpression', 'buildPyramids'],
    processListMethodName='ProjectClipAndOrExecuteMapAlgebraList',
    processListMethodShortDescription=_('Projects, clips, and/or performs map algebra on the ArcGIS rasters in a list. You must request at least one of these three operations. If you request multiple operations, the tool performs them in the order they are listed.'),
    processTableMethodName='ProjectClipAndOrExecuteMapAlgebraTable',
    processTableMethodShortDescription=_('Projects, clips, and/or performs map algebra on the ArcGIS rasters listed in a table. You must request at least one of these three operations. If you request multiple operations, the tool performs them in the order they are listed.'),
    processArcGISTableMethodName='ProjectClipAndOrExecuteMapAlgebraArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Project, Clip, and/or Execute Map Algebra on ArcGIS Rasters Listed in Table'),
    findAndProcessMethodName='FindAndProjectClipAndOrExecuteMapAlgebra',
    findAndProcessMethodArcGISDisplayName='Find ArcGIS Rasters and Project, Clip, and/or Execute Map Algebra',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and projects, clips, and/or performs map algebra on them. You must request at least one of these three operations. If you request multiple operations, the tool performs them in the order they are listed.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the output rasters.'),
    outputLocationParamArcGISDisplayName=_('Output workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    outputWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['inputRaster = row.inputRaster']],
    calculatedOutputsArcGISCategory=_('Output raster name options'),
    skipExistingDescription=_('If True, processing will be skipped for output rasters that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing output rasters will be overwritten.'))

BatchProcessing.GenerateForMethod(ArcGISRaster.ProjectToTemplate,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_('%s input rasters to project to the template raster\'s coordinate system, cell size, and extent.')],
    outputParamNames=['outputRaster'],
    outputParamFieldArcGISDisplayNames=[_('Output raster field')],
    outputParamExpressionArcGISDisplayNames=[_('Output raster Python expression')],
    outputParamDescriptions=[_(
"""%s output rasters to create. If these paths refers to the file system,
missing directories in the paths will be created if they do not exist.""")],
    outputParamExpressionDescriptions=[_OutputRasterParamExpressionDescription],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['templateRaster', 'resamplingTechnique', 'interpolationMethod', 'maxHoleSize', 'mask', 'minValue', 'maxValue'],
    processListMethodName='ProjectToTemplateList',
    processListMethodShortDescription=_('Projects a list of rasters to the coordinate system, cell size, and extent of a template raster.'),
    processTableMethodName='ProjectToTemplateTable',
    processTableMethodShortDescription=_('Projects a table of rasters to the coordinate system, cell size, and extent of a template raster.'),
    processArcGISTableMethodName='ProjectToTemplateArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Project Rasters Listed in Table to Template'),
    findAndProcessMethodName='FindAndProjectRastersToTemplate',
    findAndProcessMethodArcGISDisplayName='Find ArcGIS Rasters and Project to Template',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and projects them to the coordinate system, cell size, and extent of a template raster.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the output rasters.'),
    outputLocationParamArcGISDisplayName=_('Output workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    outputWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['inputRaster = row.inputRaster']],
    calculatedOutputsArcGISCategory=_('Output raster name options'),
    skipExistingDescription=_('If True, processing will be skipped for output rasters that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing output rasters will be overwritten.'))

_OutputFeatureClassParamExpressionDescription = _(
"""Python expression used to calculate the absolute path of an output feature
class. The expression may be any Python statement appropriate for passing to
the eval function and must return a string. The expression may reference the
following variables:

* ``workspaceToSearch`` - the value provided for the workspace to search
  parameter

* ``outputWorkspace`` - the value provided for the output workspace parameter

* ``inputRaster`` - the absolute path to the input raster

The default expression,
``os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])``,
stores the feature classes in the output workspace at the same relative
location as the input rasters in the workspace to search. The feature class
path is calculated by stripping the workspace to search from the input raster
path and replacing it with the output workspace.

For more information on Python syntax, please see the `Python documentation
<http://www.python.org/doc/>`__.""")

BatchProcessing.GenerateForMethod(ArcGISRaster.ToPolygons,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_(
"""%s rasters to convert. The rasters will be converted to polygon feature
classes using the ArcGIS :arcpy_conversion:`Raster-to-Polygon` tool. That tool
can only convert integer rasters to polygons. If the input rasters are
floating-point rasters, you must use the Map Algebra Expression parameter to
convert them to integer rasters.""")],
    outputParamNames=['outputFeatureClass'],
    outputParamFieldArcGISDisplayNames=[_('Output polygon feature class field')],
    outputParamExpressionArcGISDisplayNames=[_('Output polygon feature class Python expression')],
    outputParamDescriptions=[_(
"""%s output polygon feature classes. One feature class will be created per
raster. Missing directories the output paths will be created if they do not
exist.""")],
    outputParamExpressionDescriptions=[_OutputFeatureClassParamExpressionDescription],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['simplify', 'field', 'projectedCoordinateSystem', 'geographicTransformation', 'resamplingTechnique', 'projectedCellSize', 'registrationPoint', 'clippingDataset', 'clippingRectangle', 'mapAlgebraExpression'],
    processListMethodName='ToPolygonsList',
    processListMethodShortDescription=_('Converts a list of ArcGIS rasters to polygons that encompass groups of adjacent raster cells having the same value.'),
    processTableMethodName='ToPolygonsTable',
    processTableMethodShortDescription=_('Converts the ArcGIS rasters listed in a table to polygons that encompass groups of adjacent raster cells having the same value.'),
    processArcGISTableMethodName='ToPolygonsArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Convert ArcGIS Rasters Listed in Table to Polygons'),
    findAndProcessMethodName='FindAndConvertToPolygons',
    findAndProcessMethodArcGISDisplayName='Find and Convert ArcGIS Rasters to Polygons',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and converts them to polygons that encompass groups of adjacent raster cells having the same value.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the polygon feature classes.'),
    outputLocationParamArcGISDisplayName=_('Output workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    outputWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['inputRaster = row.inputRaster']],
    calculatedOutputsArcGISCategory=_('Output feature class name options'),
    skipExistingDescription=_('If True, conversion will be skipped for feature classes that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing feature classes will be overwritten.'))

BatchProcessing.GenerateForMethod(ArcGISRaster.ToPolygonOutlines,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_(
"""%s rasters to convert. The rasters will be converted to polygon feature
classes using the ArcGIS :arcpy_conversion:`Raster-to-Polygon` tool, and then
to line features using the :arcpy_management:`Feature-to-Line` tool. The
Raster to Polygon tool can only convert integer rasters to polygons. If the
input rasters are floating-point rasters, you must use the Map Algebra
Expression parameter to convert them to integer rasters.""")],
    outputParamNames=['outputFeatureClass'],
    outputParamFieldArcGISDisplayNames=[_('Output line feature class field')],
    outputParamExpressionArcGISDisplayNames=[_('Output line feature class Python expression')],
    outputParamDescriptions=[_(
"""%s output line feature classes. One feature class will be created per
raster. Missing directories the output paths will be created if they do not
exist.""")],
    outputParamExpressionDescriptions=[_OutputFeatureClassParamExpressionDescription],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['simplify', 'field', 'projectedCoordinateSystem', 'geographicTransformation', 'resamplingTechnique', 'projectedCellSize', 'registrationPoint', 'clippingDataset', 'clippingRectangle', 'mapAlgebraExpression'],
    processListMethodName='ToPolygonOutlinesList',
    processListMethodShortDescription=_('Converts a list of ArcGIS rasters to lines that outline groups of adjacent raster cells having the same value.'),
    processTableMethodName='ToPolygonOutlinesTable',
    processTableMethodShortDescription=_('Converts the ArcGIS rasters listed in a table to lines that outline groups of adjacent raster cells having the same value.'),
    processArcGISTableMethodName='ToPolygonOutlinesArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Convert ArcGIS Rasters Listed in Table to Polygon Outlines'),
    findAndProcessMethodName='FindAndConvertToPolygonOutlines',
    findAndProcessMethodArcGISDisplayName='Find and Convert ArcGIS Rasters to Polygon Outlines',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and converts them to lines that outline groups of adjacent raster cells having the same value.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the line feature classes.'),
    outputLocationParamArcGISDisplayName=_('Output workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    outputWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['inputRaster = row.inputRaster']],
    calculatedOutputsArcGISCategory=_('Output feature class name options'),
    skipExistingDescription=_('If True, conversion will be skipped for feature classes that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing feature classes will be overwritten.'))

BatchProcessing.GenerateForMethod(ArcGISRaster.ToLines,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_(
"""%s rasters to convert.

The rasters will be converted to line feature classes using the ArcGIS
:arcpy_conversion:`Raster-to-Polyline` tool. For each pair of adjacent
foreground raster cells, the tool draws a line connecting their centers. This
algorithm is appropriate for converting line-like raster features, such as sea
surface temperature fronts or other boundary data, into vector features.""")],
    outputParamNames=['outputFeatureClass'],
    outputParamFieldArcGISDisplayNames=[_('Output line feature class field')],
    outputParamExpressionArcGISDisplayNames=[_('Output line feature class Python expression')],
    outputParamDescriptions=[_(
"""%s output line feature classes. One feature class will be created per
raster. Missing directories the output paths will be created if they do not
exist.""")],
    outputParamExpressionDescriptions=[_OutputFeatureClassParamExpressionDescription],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['backgroundValue', 'minDangleLength', 'simplify', 'field', 'projectedCoordinateSystem', 'geographicTransformation', 'resamplingTechnique', 'projectedCellSize', 'registrationPoint', 'clippingDataset', 'clippingRectangle', 'mapAlgebraExpression'],
    processListMethodName='ToLinesList',
    processListMethodShortDescription=_('Converts a list of ArcGIS rasters to lines that outline groups of adjacent raster cells having the same value.'),
    processTableMethodName='ToLinesTable',
    processTableMethodShortDescription=_('Converts the ArcGIS rasters listed in a table to lines that outline groups of adjacent raster cells having the same value.'),
    processArcGISTableMethodName='ToLinesArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Convert ArcGIS Rasters Listed in Table to Lines'),
    findAndProcessMethodName='FindAndConvertToLines',
    findAndProcessMethodArcGISDisplayName='Find and Convert ArcGIS Rasters to Lines',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and converts them to lines that outline groups of adjacent raster cells having the same value.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the line feature classes.'),
    outputLocationParamArcGISDisplayName=_('Output workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    outputWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['inputRaster = row.inputRaster']],
    calculatedOutputsArcGISCategory=_('Output feature class name options'),
    skipExistingDescription=_('If True, conversion will be skipped for feature classes that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing feature classes will be overwritten.'))

BatchProcessing.GenerateForMethod(ArcGISRaster.ToPoints,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_(
"""%s rasters to convert. The rasters will be converted to point feature
classes using the ArcGIS :arcpy_conversion:`Raster-to-Point` tool. This tool
creates a point at the center of each raster cell, except NoData cells.""")],
    outputParamNames=['outputFeatureClass'],
    outputParamFieldArcGISDisplayNames=[_('Output point feature class field')],
    outputParamExpressionArcGISDisplayNames=[_('Output point feature class Python expression')],
    outputParamDescriptions=[_(
"""%s output point feature classes. One feature class will be created per
raster. Missing directories the output paths will be created if they do not
exist.""")],
    outputParamExpressionDescriptions=[_OutputFeatureClassParamExpressionDescription],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['field', 'projectedCoordinateSystem', 'geographicTransformation', 'resamplingTechnique', 'projectedCellSize', 'registrationPoint', 'clippingDataset', 'clippingRectangle', 'mapAlgebraExpression'],
    processListMethodName='ToPointsList',
    processListMethodShortDescription=_('Converts a list of ArcGIS rasters to points that occur at the centers of the raster cells.'),
    processTableMethodName='ToPointsTable',
    processTableMethodShortDescription=_('Converts the ArcGIS rasters listed in a table to points that occur at the centers of the raster cells.'),
    processArcGISTableMethodName='ToPointsArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Convert ArcGIS Rasters Listed in Table to Points'),
    findAndProcessMethodName='FindAndConvertToPoints',
    findAndProcessMethodArcGISDisplayName='Find and Convert ArcGIS Rasters to Points',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and converts them to points that occur at the centers of the raster cells.'),
    findMethod=ArcGISRaster.FindAndCreateTable,
    findOutputFieldParams=['rasterField'],
    findAdditionalParams=['wildcard', 'searchTree', 'rasterType'],
    outputLocationTypeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Workspace to receive the point feature classes.'),
    outputLocationParamArcGISDisplayName=_('Output workspace'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    workspaceToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    outputWorkspace = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['inputRaster = row.inputRaster']],
    calculatedOutputsArcGISCategory=_('Output feature class name options'),
    skipExistingDescription=_('If True, conversion will be skipped for feature classes that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing feature classes will be overwritten.'))

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['ArcGISRaster']
