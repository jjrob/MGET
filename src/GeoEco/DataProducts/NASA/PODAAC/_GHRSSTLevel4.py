# _GHRSSTLevel4.py - Defines GHRSSTLevel4, a Grid for accessing GHRSST L4 data
# published by NASA JPL PODAAC via NASA Earthdata.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import os

from ....ArcGIS import GeoprocessorManager
from ....Datasets import QueryableAttribute, Grid
from ....Datasets.ArcGIS import ArcGISWorkspace, ArcGISRaster, ArcGISTable
from ....Datasets.Virtual import TimeSeriesGridStack, MaskedGrid, DerivedGrid, RotatedGlobalGrid, ClippedGrid, CannyEdgeGrid, GridSliceCollection, ClimatologicalGridCollection
from ....DynamicDocString import DynamicDocString
from ....Internationalization import _
from ....SpatialAnalysis.Interpolation import Interpolator
from ....Types import *

from . import GHRSSTLevel4Granules


class GHRSSTLevel4(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, username, password, shortName, variableName, datasetType='netcdf', applyMask=False, maskBitsToCheck=None, convertToCelsius=True, timeout=60, maxRetryTime=300, cacheDirectory=None, metadataCacheLifetime=86400.):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Construct a GHRSSTLevel4Granules and wrap it in a
        # TimeSeriesGridStack to create a 3D grid with dimensions tyx.

        collection = GHRSSTLevel4Granules(username=username, password=password, shortName=shortName, datasetType=datasetType, timeout=timeout, maxRetryTime=maxRetryTime, cacheDirectory=cacheDirectory, metadataCacheLifetime=metadataCacheLifetime)
        grid = TimeSeriesGridStack(collection, expression = "VariableName = '%s'" % variableName, reportProgress=False)

        # If the caller requested that we apply the mask, wrap the grid.

        if applyMask:
            if maskBitsToCheck is not None:
                op = 'any'
                value = maskBitsToCheck     # If any of these bits are 1, the cell will be masked
            else:
                op = '!='
                value = 1                   # If the mask has a value other than 1 (meaning the cell is water), the cell will be masked

            grid = MaskedGrid(grid,
                              masks=[TimeSeriesGridStack(collection, expression = "VariableName = 'mask'", reportProgress=False)],
                              operators=[op],
                              values=[value])

        # If the caller requested that we convert Kelvin temperatures to
        # Celsius, wrap the grid.

        if convertToCelsius:
            grid = DerivedGrid(grids=[grid],
                               func=lambda grids, slices: grids[0].Data.__getitem__(slices) - 273.15,
                               displayName=grid.DisplayName,
                               noDataValue=-100.,
                               queryableAttributes=tuple(grid.GetAllQueryableAttributes()),
                               queryableAttributeValues={qa.Name: grid.GetQueryableAttributeValue(qa.Name) for qa in grid.GetAllQueryableAttributes()})

        # Assign our _WrappedGrid instance variable.

        self._WrappedGrid = grid

    def __getattribute__(self, name):
        if name.startswith('__') or name in ['_WrappedGrid', '_GetRasterNameExpressions', '_RotateAndClip', 'CreateArcGISRasters', 'CreateClimatologicalArcGISRasters', 'InterpolateAtArcGISPoints', 'CannyEdgesAsArcGISRasters']:
            return object.__getattribute__(self, name)
        return object.__getattribute__(object.__getattribute__(self, '_WrappedGrid'), name)

    def __setattr__(self, name, value):
        if name.startswith('__') or name in ['_WrappedGrid', '_GetRasterNameExpressions', '_RotateAndClip', 'CreateArcGISRasters', 'CreateClimatologicalArcGISRasters', 'InterpolateAtArcGISPoints', 'CannyEdgesAsArcGISRasters']:
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, '_WrappedGrid'), name, value)

    @classmethod
    def _GetRasterNameExpressions(cls, outputWorkspace, rasterExtension, defaultExprForDir, defaultExprForGDB):
        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        d = gp.Describe(outputWorkspace)
        outputWorkspaceIsDir = os.path.isdir(outputWorkspace) and (str(d.DataType).lower() != 'workspace' or str(d.DataType).lower() == 'filesystem')
        rasterNameExpressions = defaultExprForDir if outputWorkspaceIsDir else defaultExprForGDB

        if outputWorkspaceIsDir and rasterExtension is not None:
            if not rasterExtension.startswith('.') and not rasterNameExpressions[-1].endswith('.'):
                rasterNameExpressions[-1] += '.' 
            rasterNameExpressions[-1] += rasterExtension

        return rasterNameExpressions

    @classmethod
    def _RotateAndClip(cls, grid, rotationOffset, spatialExtent, startDate, endDate):
        if rotationOffset is not None:
            grid = RotatedGlobalGrid(grid, rotationOffset, 'Map units')

        xMin, yMin, xMax, yMax = None, None, None, None
        if spatialExtent is not None:
            from GeoEco.Types import EnvelopeTypeMetadata
            xMin, yMin, xMax, yMax = EnvelopeTypeMetadata.ParseFromArcGISString(spatialExtent)

        if spatialExtent is not None or startDate is not None or endDate is not None:
            if startDate is not None:
                startDate = datetime.datetime(startDate.year, startDate.month, startDate.day, 0, 0, 0)
            if endDate is not None:
                endDate = datetime.datetime(endDate.year, endDate.month, endDate.day, 23, 59, 59)
                
            grid = ClippedGrid(grid, 'Map coordinates', xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax, tMin=startDate, tMax=endDate)
            
        return grid

    @classmethod
    def CreateArcGISRasters(cls, username, password, shortName, variableName,
                            outputWorkspace, mode='add',
                            rotationOffset=None, spatialExtent=None, startDate=None, endDate=None, 
                            datasetType='netcdf', timeout=60, maxRetryTime=300, cacheDirectory=None, metadataCacheLifetime=86400.,
                            rasterExtension='.img', rasterNameExpressions=None, convertToCelsius=True, useUnscaledData=False, calculateStatistics=True, buildRAT=False, buildPyramids=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        if rasterNameExpressions is None:
            rasterNameExpressions = cls._GetRasterNameExpressions(outputWorkspace, rasterExtension, 
                                                                  defaultExprForDir=['%(ShortName)s', '%(VariableName)s', '%%Y', '%(VariableName)s_%%Y%%m%%d%%H%%M%%S'], 
                                                                  defaultExprForGDB=['%(ShortName)s_%(VariableName)s_%%Y%%m%%d%%H%%M%%S'])
        grid = cls(username=username, password=password, shortName=shortName, variableName=variableName, 
                   applyMask=GHRSSTLevel4Granules._Metadata[shortName]['ApplyMask'], 
                   convertToCelsius=convertToCelsius and variableName == 'analysed_sst' and not useUnscaledData, 
                   datasetType=datasetType, timeout=timeout, maxRetryTime=maxRetryTime, cacheDirectory=cacheDirectory, metadataCacheLifetime=metadataCacheLifetime)
        try:
            grid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, startDate, endDate)
            workspace = ArcGISWorkspace(outputWorkspace, ArcGISRaster, pathCreationExpressions=rasterNameExpressions, cacheTree=True, queryableAttributes=tuple(grid.GetAllQueryableAttributes() + [QueryableAttribute('DateTime', _('Date'), DateTimeTypeMetadata())]))
            workspace.ImportDatasets(GridSliceCollection(grid, tQACoordType=grid.GetLazyPropertyValue('TCornerCoordType')).QueryDatasets(), mode, useUnscaledData=useUnscaledData, calculateStatistics=calculateStatistics, buildRAT=buildRAT, buildPyramids=buildPyramids, suppressRenameWarning=True)
        finally:
            grid.Close()
        return outputWorkspace

    @classmethod
    def CreateClimatologicalArcGISRasters(cls, username, password, shortName, variableName,
                                          statistic, binType,
                                          outputWorkspace, mode='add',
                                          binDuration=1, startDayOfYear=1,
                                          rotationOffset=None, spatialExtent=None, startDate=None, endDate=None,
                                          datasetType='netcdf', timeout=60, maxRetryTime=300, cacheDirectory=None, metadataCacheLifetime=86400.,
                                          rasterExtension='.img', rasterNameExpressions=None, convertToCelsius=True, calculateStatistics=True, buildPyramids=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        if rasterNameExpressions is None:
            rasterNameExpressions = cls._GetRasterNameExpressions(outputWorkspace, rasterExtension, 
                                                                  defaultExprForDir=['%(ShortName)s', '%(VariableName)s', '%(ClimatologyBinType)s_Climatology', '%(VariableName)s_%(ClimatologyBinName)s_%(Statistic)s'], 
                                                                  defaultExprForGDB=['%(ShortName)s_%(VariableName)s_%(ClimatologyBinType)s_Climatology_%%Y%%m%%d%%H%%M%%S'])
        grid = cls(username=username, password=password, shortName=shortName, variableName=variableName, 
                   applyMask=GHRSSTLevel4Granules._Metadata[shortName]['ApplyMask'], 
                   convertToCelsius=convertToCelsius and variableName == 'analysed_sst', 
                   datasetType=datasetType, timeout=timeout, maxRetryTime=maxRetryTime, cacheDirectory=cacheDirectory, metadataCacheLifetime=metadataCacheLifetime)
        try:
            grid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, startDate, endDate)
            collection = ClimatologicalGridCollection(grid, statistic, binType, binDuration, startDayOfYear, reportProgress=True)
            workspace = ArcGISWorkspace(outputWorkspace, ArcGISRaster, pathCreationExpressions=rasterNameExpressions, cacheTree=True, queryableAttributes=tuple(collection.GetAllQueryableAttributes()))
            workspace.ImportDatasets(collection.QueryDatasets(), mode, calculateStatistics=calculateStatistics, buildPyramids=buildPyramids)
        finally:
            grid.Close()
        return outputWorkspace

    @classmethod
    def InterpolateAtArcGISPoints(cls, username, password, shortName, variableName,
                                  points, tField, valueField, method='Nearest', where=None, noDataValue=None, convertToCelsius=True,
                                  datasetType='netcdf', timeout=60, maxRetryTime=300, cacheDirectory=None, metadataCacheLifetime=86400.,
                                  orderByFields=None, numBlocksToCacheInMemory=256, xBlockSize=64, yBlockSize=64, tBlockSize=1):
        cls.__doc__.Obj.ValidateMethodInvocation()
        grid = cls(username=username, password=password, shortName=shortName, variableName=variableName, 
                   applyMask=GHRSSTLevel4Granules._Metadata[shortName]['ApplyMask'], 
                   convertToCelsius=convertToCelsius and variableName == 'analysed_sst', 
                   datasetType=datasetType, timeout=timeout, maxRetryTime=maxRetryTime, cacheDirectory=cacheDirectory)
        try:
            Interpolator.InterpolateGridsValuesForTableOfPoints(grids=[grid], 
                                                                table=ArcGISTable(points), 
                                                                fields=[valueField], 
                                                                tField=tField, 
                                                                where=where, 
                                                                orderBy=', '.join([f + ' ASC' for f in orderByFields]) if orderByFields is not None else tField + ' ASC', 
                                                                method=method, 
                                                                noDataValue=noDataValue, 
                                                                gridsWrap=GHRSSTLevel4Granules._Metadata[shortName]['IsGlobal'], 
                                                                numBlocksToCacheInMemory=numBlocksToCacheInMemory, 
                                                                xBlockSize=xBlockSize, 
                                                                yBlockSize=yBlockSize, 
                                                                tBlockSize=tBlockSize)
        finally:
            grid.Close()
        return points

    @classmethod
    def CannyEdgesAsArcGISRasters(cls, username, password, shortName,
                                  outputWorkspace, mode='add',
                                  highThreshold=None, lowThreshold=None, sigma=1.4, minSize=4,
                                  rotationOffset=None, spatialExtent=None, startDate=None, endDate=None,
                                  datasetType='netcdf', timeout=60, maxRetryTime=300, cacheDirectory=None, metadataCacheLifetime=86400.,
                                  rasterExtension='.img', rasterNameExpressions=None, calculateStatistics=True, buildRAT=False, buildPyramids=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        if rasterNameExpressions is None:
            rasterNameExpressions = cls._GetRasterNameExpressions(outputWorkspace, rasterExtension, 
                                                                  defaultExprForDir=['%(ShortName)s', 'canny_fronts', '%%Y', 'canny_fronts_%%Y%%m%%d%%H%%M%%S'], 
                                                                  defaultExprForGDB=['%(ShortName)s_canny_fronts_%%Y%%m%%d%%H%%M%%S'])
        grid = cls(username=username, password=password, shortName=shortName, variableName='analysed_sst', 
                   applyMask=GHRSSTLevel4Granules._Metadata[shortName]['ApplyMask'], 
                   datasetType=datasetType, timeout=timeout, maxRetryTime=maxRetryTime, cacheDirectory=cacheDirectory, metadataCacheLifetime=metadataCacheLifetime)
        try:
            grid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, startDate, endDate)
            grid = CannyEdgeGrid(grid, highThreshold, lowThreshold, sigma, minSize)
            workspace = ArcGISWorkspace(outputWorkspace, ArcGISRaster, pathCreationExpressions=rasterNameExpressions, cacheTree=True, queryableAttributes=tuple(grid.GetAllQueryableAttributes() + [QueryableAttribute('DateTime', _('Date'), DateTimeTypeMetadata())]))
            workspace.ImportDatasets(GridSliceCollection(grid, tQACoordType=grid.GetLazyPropertyValue('TCornerCoordType')).QueryDatasets(), mode, calculateStatistics=calculateStatistics, buildRAT=buildRAT, buildPyramids=buildPyramids)
        finally:
            grid.Close()
        return outputWorkspace


###################################################################################################
# This module is not meant to be imported directly. Import GeoEco.DataProducts.NASA.PODAAC instead.
###################################################################################################

__all__ = []
