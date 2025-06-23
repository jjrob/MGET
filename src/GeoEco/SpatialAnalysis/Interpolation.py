# SpatialAnalysis/Interpolation.py - Interpolation functions.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import functools
import logging
import os

from ..Datasets import Dataset, QueryableAttribute, Table, Grid
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger
from ..Types import *


class Interpolator(object):
    __doc__ = DynamicDocString()

    @classmethod
    def _InterpolatePointOnGrid_NearestNeighbor(cls, grid, coords, noDataValue, loggingEnabled):
        if loggingEnabled:
            Logger.Debug(_('Performing nearest neighbor interpolation at %(dim)s coordinates %(coords)s on %(grid)s.') % {'dim': grid.Dimensions, 'coords': repr(coords), 'grid': grid.DisplayName})

        # Get the grid indices for the nearest cell, i.e. the cell that
        # contains these coordinates. If the are no indices, it means the
        # coordinates are outside the extent of the grid; return noDataValue.
        
        nearestIndices = grid.GetIndicesForCoords(coords)
        if None in nearestIndices:
            if loggingEnabled:
                Logger.Debug(_('Interpolated value = %(value)s. The coordinates are outside the extent of the grid.') % {'value': repr(noDataValue)})
            return noDataValue

        # Get the value of the cell. If it is the NoData value, return the
        # noDataValue requested by the caller.
        
        value = grid.Data.__getitem__(tuple(nearestIndices))

        import numpy

        if value is None or value == grid.NoDataValue or numpy.isnan(value):
            if loggingEnabled:
                Logger.Debug(_('Nearest cell indices = %(nearestIndices)s, interpolated value = %(value)s. The cell nearest the coordinates has no data.') % {'nearestIndices': repr(nearestIndices), 'value': repr(noDataValue)})
            return noDataValue

        # Otherwise cast the value from the numpy type we got back to a
        # standard Python type and return it.
        
        value = float(value) if grid.DataType[0] == 'f' else int(value)
 
        if loggingEnabled:
            Logger.Debug(_('Nearest cell indices = %(nearestIndices)s, interpolated value = %(value)s.') % {'nearestIndices': repr(nearestIndices), 'value': repr(value)})

        return value

    @classmethod
    def _InterpolatePointOnGrid_Linear(cls, grid, coords, noDataValue, gridWraps, coordIncrements, loggingEnabled):
        if loggingEnabled:
            Logger.Debug(_('Performing linear interpolation at %(dim)s coordinates %(coords)s on %(grid)s.') % {'dim': grid.Dimensions, 'coords': repr(coords), 'grid': grid.DisplayName})

        # Get the grid indices for the nearest cell, i.e. the cell that
        # contains these coordinates. If the are no indices, it means the
        # coordinates are outside the extent of the grid; return noDataValue.
        
        nearestIndices = grid.GetIndicesForCoords(coords)
        if None in nearestIndices:
            if loggingEnabled:
                Logger.Debug(_('Interpolated value = %(value)s. The coordinates are outside the extent of the grid.') % {'value': repr(noDataValue)})
            return noDataValue

        # Get the value of the cell. If it is the NoData value, return the
        # noDataValue requested by the caller.
        
        value = grid.Data.__getitem__(tuple(nearestIndices))

        if loggingEnabled:
            Logger.Debug(_('Nearest cell indices = %(nearestIndices)s, value = %(value)s.') % {'nearestIndices': repr(nearestIndices), 'value': repr(value)})

        import numpy

        if value is None or value == grid.NoDataValue or numpy.isnan(value):
            if loggingEnabled:
                Logger.Debug(_('Interpolated value = %(value)s. The cell nearest the coordinates has no data.') % {'value': repr(noDataValue)})
            return noDataValue

        # For each dimension, calculate the fraction of the cell size
        # that is within the nearest cell; this is the cell weight for
        # that dimension. Also determine the indices of the cell that
        # is most diagonal to the nearest cell, and the weight for
        # that cell. Cells that are outside the extent of the grid
        # receive a weight of zero.

        nearestWeights = []
        diagonalIndices = []
        diagonalWeights = []

        for i, d in enumerate(grid.Dimensions):
            nearestIndicesForDim = [d]
            indicesForFirstItem = [d]
            indicesForLastItem = [d]

            if grid.CoordDependencies[i] is None:
                nearestIndicesForDim.append(nearestIndices[i])
                indicesForFirstItem.append(0)
                indicesForLastItem.append(-1)
            else:
                for j in range(len(grid.Dimensions)):
                    if grid.Dimensions[j] == d:
                        nearestIndicesForDim.append(nearestIndices[j])
                        indicesForFirstItem.append(0)
                        indicesForLastItem.append(-1)

                    elif grid.Dimensions[j] in grid.CoordDependencies[i]:
                        nearestIndicesForDim.append(nearestIndices[j])
                        indicesForFirstItem.append(nearestIndices[j])
                        indicesForLastItem.append(nearestIndices[j])

            nearestIndicesForDim = tuple(nearestIndicesForDim)
            indicesForFirstItem = tuple(indicesForFirstItem)
            indicesForLastItem = tuple(indicesForLastItem)
            
            nearestCenter = grid.CenterCoords[nearestIndicesForDim]
            
            if coords[i] >= nearestCenter:
                if nearestIndices[i] + 1 < grid.Shape[i]:
                    diagonalIndices.append(nearestIndices[i] + 1)
                elif d == 'x' and gridWraps:
                    diagonalIndices.append(0)
                else:
                    diagonalIndices.append(None)

                if diagonalIndices[i] is None:
                    nearestWeights.append(1.)       # There is no diagonal cell, so we just give the nearest cell an arbitrary non-zero weight
                else:
                    if coordIncrements[i] is not None:
                        cellSize = coordIncrements[i]
                    elif diagonalIndices[i] > 0:
                        if grid.CoordDependencies[i] is None:
                            cellSize = grid.CenterCoords[d, diagonalIndices[i]] - nearestCenter
                        else:
                            diagonalIndicesForDim = [d]
                            for j in range(len(grid.Dimensions)):
                                if grid.Dimensions[j] == d:
                                    diagonalIndicesForDim.append(diagonalIndices[j])
                                elif grid.Dimensions[j] in grid.CoordDependencies[i]:       # When computing cell size for a dimension that has coordinate dependencies, use the nearestIndices for all depended-upon coordinates.
                                    diagonalIndicesForDim.append(nearestIndices[j])
                            cellSize = grid.CenterCoords[tuple(diagonalIndicesForDim)] - nearestCenter
                    else:
                        cellSize = grid.MaxCoords[nearestIndicesForDim] - nearestCenter + grid.CenterCoords[indicesForFirstItem] - grid.MinCoords[indicesForFirstItem]        # This should be extremely rare; it can only happen for the x coordinate when it is >= the center of the right-most cell of a wrapping grid that does not use a constant increment
                    nearestWeights.append(cellSize - (coords[i] - nearestCenter))
            else:
                if nearestIndices[i] - 1 >= 0:
                    diagonalIndices.append(nearestIndices[i] - 1)
                elif d == 'x' and gridWraps:
                    diagonalIndices.append(-1)
                else:
                    diagonalIndices.append(None)

                if diagonalIndices[i] is None:
                    nearestWeights.append(1.)       # There is no diagonal cell, so we just give the nearest cell an arbitrary non-zero weight
                else:
                    if coordIncrements[i] is not None:
                        cellSize = coordIncrements[i]
                    elif diagonalIndices[i] >= 0:
                        if grid.CoordDependencies[i] is None:
                            cellSize = nearestCenter - grid.CenterCoords[d, diagonalIndices[i]]
                        else:
                            diagonalIndicesForDim = [d]
                            for j in range(len(grid.Dimensions)):
                                if grid.Dimensions[j] == d:
                                    diagonalIndicesForDim.append(diagonalIndices[j])
                                elif grid.Dimensions[j] in grid.CoordDependencies[i]:       # When computing cell size for a dimension that has coordinate dependencies, use the nearestIndices for all depended-upon coordinates.
                                    diagonalIndicesForDim.append(nearestIndices[j])
                            cellSize = nearestCenter - grid.CenterCoords[tuple(diagonalIndicesForDim)]
                    else:
                        cellSize = nearestCenter - grid.MinCoords[nearestIndicesForDim] + grid.MaxCoords[indicesForLastItem] - grid.CenterCoords[indicesForLastItem]      # This should be extremely rare; it can only happen for the x coordinate when it is < the center of the left-most cell of a wrapping grid that does not use a constant increment
                    nearestWeights.append(cellSize - (nearestCenter - coords[i]))

            if isinstance(nearestWeights[i], datetime.timedelta):
                nearestWeights[i] = nearestWeights[i].days*86400. + float(nearestWeights[i].seconds) + nearestWeights[i].microseconds*0.000001
                if isinstance(cellSize, datetime.timedelta):
                    cellSize = cellSize.days*86400. + float(cellSize.seconds) + cellSize.microseconds*0.000001

            if diagonalIndices[i] is not None:
                diagonalWeights.append(cellSize - nearestWeights[i])
            else:
                diagonalWeights.append(0.)

        if loggingEnabled:
            Logger.Debug(_('Nearest cell weights = %(nearestWeights)s, diagonal cell indices = %(diagonalIndices)s, diagonal cell weights = %(diagonalWeights)s.') % {'nearestWeights': repr(nearestWeights), 'diagonalIndices': repr(diagonalIndices), 'diagonalWeights': repr(diagonalWeights)})

        # Permute the nearest indices with the diagonal indices. The resulting
        # list identifies all of the cells we will use in the interpolation.
        # If the grid has 2 dimensions, this will be 4 cells; if 3 dimensions,
        # 8 cells; if 4 dimensions, 16 cells. The right-most coordinate (x)
        # varies first, followed by the next-right-most (y), and so on.
        #
        # Do the same permutation for the cell weights.

        cellIndices = functools.reduce(lambda a, b: [m + [n] for m in a for n in b], zip(nearestIndices, diagonalIndices), [[]])
        cellWeights = functools.reduce(lambda a, b: [m + [n] for m in a for n in b], zip(nearestWeights, diagonalWeights), [[]])

        # Loop through all the cells. If a cell's weight is greater than zero
        # (i.e. it is within the extent of the grid), get its value. If the
        # value is not NoData, add that weight to the total weight, and add
        # its weighted sum to the total weighted sum.

        weightedSum = None
        totalWeight = 0.

        for i in range(len(cellIndices)):
            cellWeight = functools.reduce(lambda a, b: a*b, cellWeights[i])
            if cellWeight > 0:
                value = grid.Data.__getitem__(tuple(cellIndices[i]))
                if value is not None and value != grid.NoDataValue and not numpy.isnan(value):
                    totalWeight += cellWeight
                    if weightedSum is None:
                        weightedSum = value * cellWeight
                    else:
                        weightedSum += value * cellWeight
                    if loggingEnabled:
                        Logger.Debug(_('Cell %(indices)s: value = %(value)s, weight = %(weight1)s = %(weight2)s, totalWeight = %(totalWeight)s, weightedSum = %(ws1)s (delta = %(ws2)s)') % {'indices': repr(cellIndices[i]), 'value': repr(float(value)), 'weight1': repr(cellWeights[i]), 'weight2': repr(cellWeight), 'totalWeight': repr(totalWeight), 'ws1': repr(weightedSum), 'ws2': repr(value * cellWeight)})
                elif loggingEnabled:
                    if value is not None:
                        value = float(value)
                    Logger.Debug(_('Cell %(indices)s: value = %(value)s (NODATA)') % {'indices': repr(cellIndices[i]), 'value': repr(value)})
            elif loggingEnabled:
                Logger.Debug(_('Cell %(indices)s: weight = %(weight1)s = %(weight2)s') % {'indices': repr(cellIndices[i]), 'weight1': repr(cellWeights[i]), 'weight2': repr(cellWeight)})

        # Calculate and return the interpolated value, as the weighted sum
        # divided by the total weight. This is the same technique as the
        # bilinear algorithm implemented ArcGIS Spatial Analyst's "Extract
        # Values to Points" and "Sample" tools.

        if weightedSum is not None:
            value = weightedSum / totalWeight
        else:
            value = noDataValue
            
        if loggingEnabled:
            Logger.Debug(_('Interpolated value = %(value)s.') % {'value': repr(value)})
        
        return value

    @classmethod
    def InterpolateGridsValuesForTableOfPoints(cls, grids, table, fields, 
                                               xField=None, yField=None, zField=None, tField=None, 
                                               xValue=None, yValue=None, zValue=None, tValue=None, 
                                               spatialReference=None, where=None, orderBy=None, method='Automatic', noDataValue=None, gridsWrap=False, useAbsZ=False, seafloorZValue=None, 
                                               numBlocksToCacheInMemory=None, xBlockSize=None, yBlockSize=None, zBlockSize=None, tBlockSize=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        try:

            # Validate that all of the grids have the same dimensions.

            grids[0].Dimensions
            for i in range(1, len(grids)):
                if grids[i].Dimensions != grids[0].Dimensions:
                    raise ValueError(_('%(g1)s has dimensions %(dim1)s but %(g2)s has dimensions %(dim2)s. All grids must have the same dimensions.') %{'g1': grids[i].DisplayName, 'dim1': grids[i].Dimensions, 'g2': grids[0].DisplayName, 'dim2': grids[0].Dimensions})

            # Validate that the caller provided appropriate coordinate
            # fields and/or a table with the appropriate geometry.

            coordinateFields = [None, None, None, None]
            
            if xField is not None and yField is not None:
                coordinateFields[2:] = [xField, yField]
            elif table.GeometryType not in ['Point', 'Point25D'] and (xValue is None or yValue is None):
                raise ValueError(_('%(table)s has %(gt)s geometry. It must have Point or Point25D geometry, or you must specify the fields that should be used as point coordinates or specify the values of the x and y coordinates.') % {'table': table.DisplayName, 'gt': table.GeometryType})
                
            if 'z' in grids[0].Dimensions:
                if zField is not None:
                    coordinateFields[1] = zField
                elif table.GeometryType != 'Point25D' and zValue is None:
                    raise ValueError(_('%(grid)s has a z dimension but %(table)s has %(gt)s geometry and a z-coordinate field was not specified. It must have Point25D geometry or you must specify a z-coordinate field or specify the value of the z coordinate.') % {'grid': grids[0].DisplayName, 'table': table.DisplayName, 'gt': table.GeometryType})

            if grids[0].Dimensions[0] == 't':
                if tField is not None:
                    coordinateFields[0] = tField
                elif tValue is None:
                    raise ValueError(_('%(grid)s has a t dimension but a t-coordinate field of %(table)s was not specified. You must specify a t-coordinate field or the value of the t coordinate.') % {'grid': grids[0].DisplayName, 'table': table.DisplayName})
            else:
                tField = None

            for i in range(len(coordinateFields)):
                if coordinateFields[i] is not None:
                    field = table.GetFieldByName(coordinateFields[i])
                    if field is None:
                        raise ValueError(_('%(table)s does not have a field named "%(field)s".') % {'table': table.DisplayName, 'field': coordinateFields[i]})
                    if i == 0:
                        if field.DataType not in ['date', 'datetime']:
                            raise ValueError(_('The field %(field)s of %(table)s has the data type %(dt)s, which cannot be used as a t-coordinate. To be used as a t-coordinate, the field must have a date or datetime data type.') % {'table': table.DisplayName, 'field': field.Name, 'dt': field.DataType})
                    elif field.DataType not in ['int16', 'int32', 'float32', 'float64']:
                        raise ValueError(_('The field %(field)s of %(table)s has the data type %(dt)s, which cannot be used as a coordinate. To be used as a coordinate, it must have a floating-point or integer data type.') % {'table': table.DisplayName, 'field': field.Name, 'dt': field.DataType})
                    if coordinateFields[i] in fields:
                        raise ValueError(_('The field %(field)s is specified both as a coordinate and as a field to store interpolated values. It can only be used as one or the other.') % {'field': field.Name})

            # If the caller did not provide xField or yField and did not
            # provide xValue or yValue (i.e. we're using the geometry of the
            # table), use the spatial reference of the table.

            if (xField is None or yField is None) and (xValue is None or yValue is None):
                spatialReference = table.GetSpatialReference('obj')

            # Validate that the destination fields exist and warn the user if
            # there will be rounding or loss of precision. Also set the
            # noDataValues, determine the coordinate increments, and determine
            # the interpolation method.

            fieldDataTypes = []
            noDataValues = []
            gridCoordIncrements = []
            gridInterpolationMethods = []

            for i in range(len(fields)):
                field = table.GetFieldByName(fields[i])
                if field is None:
                    raise ValueError(_('%(table)s does not have a field named "%(field)s".') % {'table': table.DisplayName, 'field': field.Name})
                if field.DataType not in ['int16', 'int32', 'float32', 'float64']:
                    raise ValueError(_('The field %(field)s of %(table)s has the data type %(dt)s, which cannot be used to store interpolated values. To store interpolated values, it must have a floating-point or integer data type.') % {'table': table.DisplayName, 'field': field.Name, 'dt': field.DataType})
                if grids[i].DataType not in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:
                    raise ValueError(_('%(grid)s has the data type %(dt)s, which is not supported by this tool. It must have a floating-point or integer data type.') % {'grid': grids[i].DisplayName, 'dt': grids[i].DataType})
                if field.DataType == 'float32' and grids[i].DataType == 'float64':
                    Logger.Warning(_('%(grid)s has the data type float64 but the field %(field)s of %(table)s has the data type float32. Some loss of precision may result. An error will be raised if an interpolated value exceeds the range of the float32 data type.') % {'grid': grids[i].DisplayName, 'table': table.DisplayName, 'field': field.Name})
                elif field.DataType[0] in ['i', ''] and grids[i].DataType[0] == 'f':
                    Logger.Warning(_('%(grid)s has a floating-point data type but the field %(field)s of %(table)s has an integer data type. Interpolated point values will be rounded to the closest integer before they are stored. An error will be raised if an interpolated value exceeds the range of the field\'s integer data type.') % {'grid': grids[i].DisplayName, 'table': table.DisplayName, 'field': field.Name})
                elif field.DataType == 'int8' and grids[i].DataType != 'int8' or \
                     field.DataType == 'uint8' and grids[i].DataType != 'uint8' or \
                     field.DataType == 'int16' and grids[i].DataType not in ['int8', 'uint8', 'int16'] or \
                     field.DataType == 'uint16' and grids[i].DataType not in ['int8', 'uint8', 'uint16'] or \
                     field.DataType == 'int32' and grids[i].DataType not in ['int8', 'uint8', 'int16', 'uint16', 'int32'] or \
                     field.DataType == 'uint32' and grids[i].DataType not in ['int8', 'uint8', 'int16', 'uint16', 'uint32']:
                    Logger.Warning(_('%(grid)s has the data type %(dt1)s but the field %(field)s of %(table)s has the data type %(dt2)s, which does not support the full range of values of %(dt1)s. An error will be raised if an interpolated value exceeds the range of %(dt2)s.') % {'grid': grids[i].DisplayName, 'table': table.DisplayName, 'field': field.Name, 'dt1': grids[i].DataType, 'dt2': field.DataType})
                fieldDataTypes.append(field.DataType)

                if noDataValue is not None:
                    noDataValues.append(float(noDataValue) if field.DataType.startswith('float') else int(noDataValue))
                elif not field.IsNullable:
                    noDataValues.append(-9999. if field.DataType.startswith('float') else -9999)
                else:
                    noDataValues.append(None)
                
                gridCoordIncrements.append(list(grids[i].CoordIncrements))
                if grids[i].Dimensions[0] == 't' and grids[i].CoordIncrements[0] is not None:
                    if grids[i].TSemiRegularity is not None:
                        gridCoordIncrements[i][0] = None
                    elif grids[i].TIncrementUnit.lower() == 'day':
                        gridCoordIncrements[i][0] = datetime.timedelta(gridCoordIncrements[i][0])
                    elif grids[i].TIncrementUnit.lower() == 'hour':
                        gridCoordIncrements[i][0] = datetime.timedelta(gridCoordIncrements[i][0] / 24.)
                    elif grids[i].TIncrementUnit.lower() == 'minute':
                        gridCoordIncrements[i][0] = datetime.timedelta(gridCoordIncrements[i][0] / 1440.)
                    elif grids[i].TIncrementUnit.lower() == 'second':
                        gridCoordIncrements[i][0] = datetime.timedelta(gridCoordIncrements[i][0] / 86400.)
                    else:
                        gridCoordIncrements[i][0] = None

                gridInterpolationMethods.append(method if method != 'automatic' else 'linear' if grids[i].DataType[0] == 'f' else 'nearest')

            # If the caller requested in-memory caching, construct caching
            # wrappers for the grids.

            if numBlocksToCacheInMemory is not None and numBlocksToCacheInMemory > 0 and \
               xBlockSize is not None and xBlockSize > 0 and \
               yBlockSize is not None and yBlockSize > 0 and \
               ('z' not in grids[0].Dimensions or zBlockSize is not None and zBlockSize > 0) and \
               ('t' not in grids[0].Dimensions or tBlockSize is not None and tBlockSize > 0):

                maxCells = numBlocksToCacheInMemory * xBlockSize * yBlockSize
                if 'z' in grids[0].Dimensions:
                    maxCells *= zBlockSize
                if 't' in grids[0].Dimensions:
                    maxCells *= tBlockSize
                    
                from ..Datasets.Virtual import MemoryCachedGrid
                grids = [MemoryCachedGrid(grid, maxCacheSize=maxCells * {'int8': 1, 'uint8': 1, 'int16': 2, 'uint16': 2, 'int32': 4, 'uint32': 4, 'float32': 4, 'float64': 8}[grid.UnscaledDataType], xMinBlockSize=xBlockSize, yMinBlockSize=yBlockSize, zMinBlockSize=zBlockSize, tMinBlockSize=tBlockSize) for grid in grids]

            # If the table uses a different coordinate system than the grids,
            # create OSR CoordinateTransformation instances for transforming
            # the tables' coordinates to the grids' coordinates.

            coordinateTransforms = [None] * len(grids)
            if spatialReference is not None:
                for i in range(len(grids)):
                    gridSR = grids[i].GetSpatialReference('obj')
                    if gridSR is not None and not spatialReference.IsSame(gridSR):
                        try:
                            coordinateTransforms[i] = Dataset._osr().CoordinateTransformation(spatialReference, gridSR)
                        except Exception as e:
                            Dataset._gdal().ErrorReset()
                            raise RuntimeError(_('Cannot transform coordinates from the coordinate system of %(table)s ((%(cs1)s) to the coordinate system of %(grid)s ((%(cs2)s). Try projecting the coordinates manually and try again. Error details: The osr.CoordinateTransformation() function failed with %(e)s: %(msg)s') % {'table': table.DisplayName, 'grid': grids[i].DisplayName, 'cs1': Dataset.ConvertSpatialReference('obj', spatialReference, 'wkt'), 'cs2': grids[i].GetSpatialReference('wkt'), 'e': e.__class__.__name__, 'msg': e})

            # Open an update cursor on the table and process the points.

            import numpy

            debugLoggingEnabled = logging.getLogger('GeoEco').isEnabledFor(logging.DEBUG)

            if where is None:
                rowCount = table.GetRowCount()
                cursor = table.OpenUpdateCursor(orderBy=orderBy, rowCount=rowCount)
                Logger.Info(_('Interpolating values for %(rowCount)i %(obj)s of %(table)s.') % {'rowCount': rowCount, 'obj': cursor.RowDescriptionPlural, 'table': table.DisplayName})
            else:
                cursor = table.OpenUpdateCursor(where=where, orderBy=orderBy)
                Logger.Info(_('Interpolating values for %(obj)s of %(table)s where %(where)s.') % {'obj': cursor.RowDescriptionPlural, 'table': table.DisplayName, 'where': where})

            try:
                while cursor.NextRow():

                    # Get the coordinates of this point.
                    
                    if tField is not None:
                        value = cursor.GetValue(tField)
                        if value is None:
                            cls._WarnAboutNullField(table, cursor, tField)
                            continue
                        coordinates = [value]
                    elif tValue is not None:
                        coordinates = [tValue]
                    else:
                        coordinates = []

                    if (xField is None or yField is None) and (xValue is None or yValue is None) or 'z' in grids[0].Dimensions and (zField is None and zValue is None):
                        geometry = cursor.GetGeometry()
                        if geometry is not None:
                            point = geometry.GetPoint()     # point is x,y,z or x,y
                        if geometry is None or numpy.isnan(point[0]) or numpy.isnan(point[1]) or (zField is None and 'z' in grids[0].Dimensions and numpy.isnan(point[2])):
                            if table.HasOID:
                                if table.OIDFieldName is not None:
                                    Logger.Warning(_('The %(obj)s of %(table)s with %(field)s = %(value)s has a null geometry. This %(obj)s will be ignored.') % {'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName, 'field': table.OIDFieldName, 'value': repr(cursor.GetOID())})
                                else:
                                    Logger.Warning(_('The %(obj)s of %(table)s with the object ID (OID) of %(value)s has a null geometry. This %(obj)s will be ignored.') % {'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName, 'value': repr(cursor.GetOID())})
                            else:
                                Logger.Warning(_('A %(obj)s of %(table)s has a null geometry. This row will be ignored.') % {'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName})
                            continue

                    if 'z' in grids[0].Dimensions:
                        if zField is not None:
                            value = cursor.GetValue(zField)
                            if value is None:
                                cls._WarnAboutNullField(table, cursor, zField)
                                continue
                            coordinates.append(float(value))
                        elif zValue is not None:
                            coordinates.append(zValue)
                        else:
                            coordinates.append(point[2])
                        if useAbsZ:
                            coordinates[-1] = abs(coordinates[-1])

                    if xField is not None and yField is not None:
                        value = cursor.GetValue(yField)
                        if value is None:
                            cls._WarnAboutNullField(table, cursor, yField)
                            continue
                        coordinates.append(float(value))
                        value = cursor.GetValue(xField)
                        if value is None:
                            cls._WarnAboutNullField(table, cursor, xField)
                            continue
                        coordinates.append(float(value))
                    elif xValue is not None and yValue is not None:
                        coordinates.append(yValue)
                        coordinates.append(xValue)
                    else:
                        coordinates.append(point[1])
                        coordinates.append(point[0])

                    # Interpolate a value for each grid.

                    for i in range(len(grids)):

                        # If we created an OSR CoordinateTransformation
                        # instance for this grid, transform the x, y, and
                        # z coordinates.

                        if coordinateTransforms[i] is not None:
                            if 't' in grids[0].Dimensions:
                                coordsToTransform = list(reversed(coordinates[1:]))
                            else:
                                coordsToTransform = list(reversed(coordinates))

                            try:
                                transformedCoords = list(coordinateTransforms[i].TransformPoint(*coordsToTransform))        # coordsToTransform is x,y or x,y,z. transformedCoords is always x,y,z
                            except Exception as e:
                                Dataset._gdal().ErrorReset()
                                if len(coordsToTransform) == 2:
                                    Logger.Warning(_('Failed to transform coordinates x = %(x)g, y = %(x)g from the coordinate system of %(table)s ((%(cs1)s) to the coordinate system of %(grid)s ((%(cs2)s). The NoData value will be stored in the %(field)s of the %(obj)s having these coordinates. Error details: The osr.CoordinateTransformation.TransformPoint() function failed with %(e)s: %(msg)s') %
                                                     {'x': float(coordsToTransform[0]), 'y': float(coordsToTransform[1]), 'table': table.DisplayName, 'grid': grids[i].DisplayName, 'cs1': Dataset.ConvertSpatialReference('obj', spatialReference, 'wkt'), 'cs2': grids[i].GetSpatialReference('wkt'), 'field': fields[i], 'obj': cursor.RowDescriptionSingular, 'e': e.__class__.__name__, 'msg': e})
                                else:
                                    Logger.Warning(_('Failed to transform coordinates x = %(x)g, y = %(y)g, z = %(z)g from the coordinate system of %(table)s ((%(cs1)s) to the coordinate system of %(grid)s ((%(cs2)s). The NoData value will be stored in the %(field)s of the %(obj)s having these coordinates. Error details: The osr.CoordinateTransformation.TransformPoint() function failed with %(e)s: %(msg)s') %
                                                     {'x': float(coordsToTransform[0]), 'y': float(coordsToTransform[1]), 'z': float(coordsToTransform[2]), 'table': table.DisplayName, 'grid': grids[i].DisplayName, 'cs1': Dataset.ConvertSpatialReference('obj', spatialReference, 'wkt'), 'cs2': grids[i].GetSpatialReference('wkt'), 'field': fields[i], 'obj': cursor.RowDescriptionSingular, 'e': e.__class__.__name__, 'msg': e})
                                cursor.SetValue(fields[i], noDataValues[i])
                                continue

                            if 'z' in grids[0].Dimensions:
                                transformedCoords = list(reversed(transformedCoords))       # Change transformedCoords to z,y,x
                            else:
                                transformedCoords = list(reversed(transformedCoords))[1:]   # Change transformedCoords to y,x

                            if 't' in grids[0].Dimensions:
                                transformedCoords.insert(0, coordinates[0])                 # transformedCoords is now either t,z,y,x or t,y,x
                        else:
                            transformedCoords = []
                            transformedCoords.extend(coordinates)

                        # If the caller provided a seafloorZValue and
                        # the z coordinate is equal to it, set the z
                        # coordinate to the center of the deepest
                        # layer that has data.

                        if 'z' in grids[0].Dimensions and seafloorZValue is not None and coordinates[-3] == seafloorZValue:
                            indices = grids[i].GetIndicesForCoords(transformedCoords)
                            indices[-3] = slice(None)
                            if None not in indices:
                                dataForAllDepths = grids[i].Data.__getitem__(tuple(indices))
                                zIndicesWithoutData = numpy.where(Grid.numpy_equal_nan(dataForAllDepths, grids[i].NoDataValue))[0]
                                if len(zIndicesWithoutData) > 0:
                                    zIndexOfDeepestWithData = max(0, zIndicesWithoutData[0] - 1)
                                else:
                                    zIndexOfDeepestWithData = len(dataForAllDepths) - 1

                                if grids[i].CoordDependencies[-3] is None:
                                    transformedCoords[-3] = grids[i].CenterCoords['z', zIndexOfDeepestWithData]
                                else:
                                    indicesOfZ = ['z']
                                    for j, d in enumerate(grids[i].Dimensions):
                                        if d == 'z':
                                            indicesOfZ.append(zIndexOfDeepestWithData)
                                        elif d in grids[i].CoordDependencies[-3]:
                                            indicesOfZ.append(indices[j])
                                            
                                    transformedCoords[-3] = grids[i].CenterCoords[tuple(indicesOfZ)]

                        # Do the interpolation.
                        
                        if gridInterpolationMethods[i] == 'nearest':
                            value = cls._InterpolatePointOnGrid_NearestNeighbor(grids[i], transformedCoords, noDataValues[i], debugLoggingEnabled)
                        elif gridInterpolationMethods[i] == 'linear':
                            value = cls._InterpolatePointOnGrid_Linear(grids[i], transformedCoords, noDataValues[i], gridsWrap, gridCoordIncrements[i], debugLoggingEnabled)
                        else:
                            raise NotImplementedError(_('The "%(method)s" interpolation method has not been implemented yet. Please choose a different method and try again. We apologize for the inconvenience.') % {'method': gridInterpolationMethods[i]})

                        # If necessary, coerce the interpolated value to
                        # the field's data type and check for overflow.

                        if value != noDataValues[i]:
                            originalValue = value
                            overflow = False

                            if fieldDataTypes[i][0] == 'i' or fieldDataTypes[i][0] == '':
                                if isinstance(value, float):
                                    value = int(round(value))
                                if fieldDataTypes[i] == 'int8' and (value < -128 or value > 127) or \
                                   fieldDataTypes[i] == 'uint8' and (value < 0 or value > 255) or \
                                   fieldDataTypes[i] == 'int16' and (value < -32768 or value > 32767) or \
                                   fieldDataTypes[i] == 'uint16' and (value < 0 or value > 65535) or \
                                   fieldDataTypes[i] == 'int32' and (value < -2147483648 or value > 2147483647) or \
                                   fieldDataTypes[i] == 'uint32' and (value < 0 or value > 4294967295):
                                    overflow = True
                            else:
                                if isinstance(value, int):
                                    value = float(value)
                                if fieldDataTypes[i] == 'float32' and numpy.isinf(numpy.asarray(value, dtype='float32')):
                                    overflow = True

                            if overflow:
                                if table.HasOID:
                                    if table.OIDFieldName is not None:
                                        raise OverflowError(_('The value %(value)s interpolated for the %(obj)s of %(table)s with %(oidField)s = %(oidValue)s exceeds the range of the field %(field2)s, which has the data type %(dt)s. Please try again using a field that has a data type that can hold this value.') % {'value': repr(originalValue), 'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName, 'oidField': table.OIDFieldName, 'oidValue': repr(cursor.GetOID()), 'field2': fields[i], 'dt': fieldDataTypes[i]})
                                    else:
                                        raise OverflowError(_('The value %(value)s interpolated for the %(obj)s of %(table)s with the object ID (OID) of %(oidValue)s exceeds the range of the field %(field2)s, which has the data type %(dt)s. Please try again using a field that has a data type that can hold this value.') % {'value': repr(originalValue), 'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName, 'oidValue': repr(cursor.GetOID()), 'field2': fields[i], 'dt': fieldDataTypes[i]})
                                else:
                                    raise OverflowError(_('The value %(value)s interpolated for a %(obj)s of %(table)s exceeds the range of the field %(field2)s, which has the data type %(dt)s. Please try again using a field that has a data type that can hold this value.') % {'value': repr(originalValue), 'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName, 'field2': fields[i], 'dt': fieldDataTypes[i]})

                        # Store the value in the field.

                        cursor.SetValue(fields[i], value)

                    # Update the row.

                    cursor.UpdateRow()
            finally:
                cursor.Close()

        # Close all of the grids before returning.

        finally:
            for grid in grids:
                grid.Close()

    @classmethod
    def _WarnAboutNullField(cls, table, cursor, field):
        if table.HasOID:
            if table.OIDFieldName is not None:
                Logger.Warning(_('Field %(field)s of the %(obj)s of %(table)s with %(oidField)s = %(value)s is NULL. This %(obj)s will be ignored.') % {'field': field, 'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName, 'oidField': table.OIDFieldName, 'value': repr(cursor.GetOID())})
            else:
                Logger.Warning(_('Field %(field)s of the %(obj)s of %(table)s with the object ID (OID) of %(value)s is NULL. This %(obj)s will be ignored.') % {'field': field, 'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName, 'value': repr(cursor.GetOID())})
        else:
            Logger.Warning(_('Field %(field)s of a %(obj)s of %(table)s is NULL. This %(obj)s will be ignored.') % {'field': field, 'obj': cursor.RowDescriptionSingular, 'table': table.DisplayName})
    
    @classmethod
    def InterpolateArcGISRasterValuesAtPoints(cls, rasters, points, fields, method='Automatic',
                                               where=None, noDataValue=None, rastersWrap=False,
                                               orderByFields=None, numBlocksToCacheInMemory=None, xBlockSize=None, yBlockSize=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        if orderByFields is not None:
            orderByFields = ', '.join([field + ' ASC' for field in orderByFields])

        from ..Datasets.ArcGIS import ArcGISRasterBand, ArcGISTable

        rasterBands = []
        try:
            for raster in rasters:
                rasterBands.append(ArcGISRasterBand.ConstructFromArcGISPath(raster))
                
            cls.InterpolateGridsValuesForTableOfPoints(rasterBands,
                                                       ArcGISTable(points),
                                                       fields,
                                                       where=where,
                                                       orderBy=orderByFields,
                                                       method=method,
                                                       noDataValue=noDataValue,
                                                       gridsWrap=rastersWrap,
                                                       numBlocksToCacheInMemory=numBlocksToCacheInMemory,
                                                       xBlockSize=xBlockSize,
                                                       yBlockSize=yBlockSize)
        finally:
            for rasterBand in rasterBands:
                rasterBand.Close()
            
        return points        
    
    @classmethod
    def InterpolateTimeSeriesOfArcGISRastersValuesAtPoints(cls, points, tField, valueField,
                                                           workspace, rasterNameExpressions, tCornerCoordType, tIncrement, tIncrementUnit, tSemiRegularity=None, tCountPerSemiRegularPeriod=None, method='Automatic',
                                                           where=None, noDataValue=None, rastersWrap=False,
                                                           orderByFields=None, numBlocksToCacheInMemory=256, xBlockSize=128, yBlockSize=128, tBlockSize=1):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # If the caller did not specify any order by fields, order by
        # the tField by default.

        if orderByFields is not None:
            orderByFields = ', '.join([field + ' ASC' for field in orderByFields])
        else:
            orderByFields = tField + ' ASC'

        # Construct a 3D TimeSeriesGridStack from the rasters in the
        # ArcGIS workspace that match the caller's
        # rasterNameExpressions. The DateTime queryable attribute will
        # be parsed from the raster names.

        from ..Datasets.ArcGIS import ArcGISWorkspace, ArcGISTable, ArcGISRaster
        from ..Datasets.Virtual import TimeSeriesGridStack

        grid = TimeSeriesGridStack(ArcGISWorkspace(workspace,
                                                   ArcGISRaster,
                                                   pathParsingExpressions=rasterNameExpressions,
                                                   queryableAttributes=(QueryableAttribute('DateTime', _('Raster date'), DateTimeTypeMetadata()),),
                                                   lazyPropertyValues={'TIncrement': tIncrement,
                                                                       'TIncrementUnit': tIncrementUnit,
                                                                       'TSemiRegularity': tSemiRegularity,
                                                                       'TCountPerSemiRegularPeriod': tCountPerSemiRegularPeriod,
                                                                       'TCornerCoordType': tCornerCoordType}),
                                   reportProgress=False)

        # Sample the 3D TimeSeriesGridStack using the caller's points.

        cls.InterpolateGridsValuesForTableOfPoints([grid],
                                                   ArcGISTable(points),
                                                   [valueField],
                                                   tField=tField,
                                                   where=where,
                                                   orderBy=orderByFields,
                                                   method=method,
                                                   noDataValue=noDataValue,
                                                   gridsWrap=True,
                                                   numBlocksToCacheInMemory=numBlocksToCacheInMemory,
                                                   xBlockSize=xBlockSize,
                                                   yBlockSize=yBlockSize,
                                                   tBlockSize=tBlockSize)

    @classmethod
    def InpaintArcGISRaster(cls, inputRaster, outputRaster, method='Del2a', maxHoleSize=None, xEdgesWrap=False, minValue=None, maxValue=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        from ..Datasets.ArcGIS import ArcGISWorkspace, ArcGISRaster, ArcGISRasterBand
        from ..Datasets.Virtual import InpaintedGrid
        
        ArcGISWorkspace(os.path.dirname(outputRaster), ArcGISRaster, pathCreationExpressions=[os.path.basename(outputRaster)]).ImportDatasets([InpaintedGrid(ArcGISRasterBand.ConstructFromArcGISPath(inputRaster), method, maxHoleSize, xEdgesWrap, minValue, maxValue)], {False: 'Add', True: 'Replace'}[overwriteExisting], reportProgress=False)


###############################################################################
# Metadata: module
###############################################################################

from ..ArcGIS import ArcGISDependency
from ..Dependencies import PythonModuleDependency
from ..Matlab import MatlabDependency
from ..Metadata import *

AddModuleMetadata(shortDescription=_('Functions for interpolating in space and time.'))

###############################################################################
# Metadata: Interpolator class
###############################################################################

AddClassMetadata(Interpolator,
    shortDescription=_('Functions for interpolating in space and time.'))

# Public method: Interpolator.InterpolateGridsValuesForTableOfPoints

AddMethodMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints,
    shortDescription=_('Interpolates the values of :class:`~GeoEco.Datasets.Grid`\\ s at points represented as rows of a :class:`~GeoEco.Datasets.Table`.'),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')])

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Interpolator),
    description=_(':class:`%s` class or an instance of it.') % Interpolator.__name__)

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'grids',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=Grid), minLength=1),
    description=_(
"""List of :class:`~GeoEco.Datasets.Grid`\\ s to interpolate values from. The
grids must all have the same dimensions (i.e. all ``yz``, all ``zyx``, all
``tyx``, or all ``tzyx``), but are allowed to have different coordinate
systems, spatial extents, cell sizes, shapes, data types, and NoData
values."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'table',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(
""":class:`~GeoEco.Datasets.Table` containing the points at which values
should be interpolated. It is recommended but not required that the points and
grids use the same coordinate system. If they do not, this tool will attempt
to project the points to the coordinate systems of the grids prior to doing the
interpolations. This may fail if a datum transformation is required, in which
case you will have to manually project the points and grids to the same
coordinate system before using this function."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, mustBeSameLengthAsArgument='grids'),
    description=_(
"""Fields of the :class:`~GeoEco.Datasets.Table` to receive the interpolated
values. You must provide a field for each grid. The fields must have
floating-point or integer data types. If a field cannot represent the
interpolated value at full precision, the closest approximation will be stored
and a warning will be issued. This will happen, for example, when the grid
uses a floating point data type but the field uses an integer data type."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'xField',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Field from which the ``x`` coordinate should be taken. The field must have
a floating point or integer data types. If provided, `yField` must also be
provided. If not provided, the ``x`` coordinate will be taken from `xValue`.
If that is not provided, the ``x`` coordinate will be taken from the geometry
field. If the table has no geometry field, an exception will be raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'yField',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Field from which the ``y`` coordinate should be taken. The field must have
a floating point or integer data types. If provided, `xField` must also be
provided. If not provided, the ``y`` coordinate will be taken from `yValue`.
If that is not provided, the ``y`` coordinate will be taken from the geometry
field. If the table has no geometry field, an exception will be raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'zField',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Field from which the ``z`` coordinate (depth) should be taken. Ignored if
the grids do not have a ``z`` dimension. The field must have a floating point
or integer data type. If not provided, the ``z`` coordinate will be taken
from `zValue`. If that is not provided, the ``z`` coordinate will be taken
from the geometry field. If the table has no geometry field, or the geometry
field does not include a ``z`` coordinate, an exception will be raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'tField',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""Field from which the ``t`` coordinate (time) should be taken. Ignored if
the grids do not have a ``t`` dimension. The field must have a datetime data
type. (If the field can only represent dates with no time component, the time
will assumed to be 00:00:00.) If not provided, the ``t`` coordinate will be
taken from `tValue`. If that is not provided, an exception will be
raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'xValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Value to use for the ``x`` coordinate. Ignored if `xField` is provided. If
provided, `yValue` must also be provided. If neither `xField` nor `xValue` are
provided, the ``x`` coordinate will be taken from the geometry field. If the
table has no geometry field, an exception will be raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'yValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Value to use for the ``y`` coordinate. Ignored if `yField` is provided. If
provided, `xValue` must also be provided. If neither `yField` nor `yValue` are
provided, the ``y`` coordinate will be taken from the geometry field. If the
table has no geometry field, an exception will be raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'zValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Value to use for the ``z`` coordinate. Ignored if the grids do not have a
``z`` dimension or `zField` is provided. Otherwise, if neither `zField` nor
`zValue` are provided, the ``z`` coordinate will be taken from the geometry
field. If the table has no geometry field, or the geometry field does not
include a ``z`` coordinate, an exception will be raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'tValue',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Value to use for the ``t`` coordinate. Ignored if the grids do not have a
``t`` dimension or `tField` is provided. Otherwise, if neither `tField` nor
`tValue` are provided, an exception will be raised."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'spatialReference',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
""":py:class:`osgeo.osr.SpatialReference` instance defining the spatial
reference for the table. Ignored if neither `xField` nor `xValue` are provided
or neither `yField` nor `yValue` are provided, in which case the spatial
reference will be extracted from the table's geometry field. Otherwise, if
`spatialReference` is not provided, the values present in `xField`/`xValue`
and `yField`/`yValue` are assumed to be in the same coordinate system as the
grids."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'where',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""SQL WHERE clause expression that specifies the subset of rows to process. If
not provided, all of the rows will be processed. If provided but the underlying
storage format does not support WHERE clauses, an exception will be raised.
The exact syntax of this expression depends on the underlying storage format.
If the underlying data store will be accessed through ArcGIS, `this article
<https://pro.arcgis.com/en/pro-app/latest/help/mapping/navigation/sql-reference-for-elements-used-in-query-expressions.htm>`_
may document some of the possible syntax, but not all of it may be supported
through ArcGIS's underlying Python API."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'orderBy',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, mustMatchRegEx=r'\s*\S+(\s+([aA][sS][cC]|[dD][eE][sS][cC]))?\s*(,\s*\S+(\s+([aA][sS][cC]|[dD][eE][sS][cC]))?\s*)*'),
    description=_(
"""SQL ORDER BY clause that specifies the order in which the rows should be
processed. If not provided, the rows will processed according to the default
behavior of the underlying storage format and the programming library used to
access it.

The ORDER BY clause must be a comma-separated list of fields. Each field can
optionally be followed by a space and the word ``ASC`` to indicate ascending
order or ``DESC`` to indicate descending order. If neither is specified,
``ASC`` is assumed.

The underlying storage format and library perform the actual evaluation of
this parameter and determine the rules of sorting, such as whether string
comparisons are case-sensitive or case-insensitive. At present, there is no
mechanism to interrogate or manipulate these rules; you must live with the
default behavior of the underlying format and library.

"""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'method',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Automatic', 'Nearest', 'Linear'], makeLowercase=True),
    description=_(
"""Interpolation method to use, one of:

* ``Automatic`` - the tool will automatically select the interpolation method
  based on each grid's data type: for integer grids, nearest neighbor
  interpolation; for floating-point grids, linear interpolation. This is the
  default.

* ``Nearest`` - nearest neighbor interpolation. The interpolated value will
  simply be the value of the cell that contains the point.

* ``Linear`` - linear interpolation. If the grid has two dimensions (``yx``),
  this method averages the values of the four nearest cells, weighting the
  contribution of each cell by the area of it that would be covered by a
  hypothetical cell centered on the point being interpolated. If the grid has
  three dimensions (``zyx`` or ``tyx``), the eight nearest cells will be used
  (a cube). If the grid has four dimensions (``tzyx``), the 16 nearest cells
  will be used (a hypercube). If the cell containing the point contains
  NoData, the result is NoData. If any of the other cells to be averaged
  contain NoData, they are omitted from the average, and the result is based
  on the weighted average of the cells that do contain data.

"""),
    arcGISDisplayName=_('Interpolation method'))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'noDataValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Value to use when the interpolated value is NoData. If a value is not
provided for this parameter, a database NULL value will be stored in the field
when the interpolated value is NoData. If the field cannot store NULL values,
as is the case with shapefiles, the value -9999 will be used."""),
    arcGISDisplayName=_('Value to use when the interpolated value is NoData'),
    arcGISCategory=_('Interpolation options'))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'gridsWrap',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""Indicates whether or not the left and right edges of the grids should be
treated as connected. Enable this option when you have grids that span 360
degrees of longitude and you wish the interpolator to consider cells on the
opposite side of the grid when interpolating values for points very close to
the left or right edge. This option has no effect if nearest neighbor
interpolation is used, because the interpolated value will be based on the
value of the single nearest cell."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'useAbsZ',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the absolute value of the ``z`` coordinate (depth) will be used
when extracting values from the grids. Use this option if depths in your table
are represented with negative numbers but depths in the grids are represented
with positive numbers."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'seafloorZValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Value of the table's ``z`` coordinate indicating that grid values should be
extracted from the deepest cell with data, representing the seafloor. Use this
as a convenience when you want to extract values along the seafloor but don't
want to bother with first looking up the seafloor's depth at each point of
interest. Instead, set the depth coordinate to a value such as -20000 (e.g. by
passing -20000 for `zValue`), and then pass -20000 for `seafloorZValue`. The
values for each point will then be extracted from the deepest cell with data
at the point's horizontal location."""))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'numBlocksToCacheInMemory',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Maximum number of blocks of data to cache in memory.

To minimize the number of times that the disk or network must be accessed,
this tool employs a simple caching strategy. When it processes the first
point, it reads a square block of cells centered on that point and caches it
in memory. When it processes the second and subsequent points, it first checks
whether the cells needed for that point are contained by the block cached in
memory. If so, it processes that point using the in-memory block, rather than
reading from disk or the network again. If not, it reads another square block
centered on that point and adds it to the cache.

The tool processes the remaining points, adding additional blocks to the
cache, as needed. To prevent the cache from exhausting all memory, it is only
permitted to grow to the size specified by this parameter. When the cache is
full but a new block is needed, the oldest block is discarded to make room for
the newest block.

If this parameter is 0, no blocks will be cached in memory."""),
    arcGISDisplayName=_('Number of blocks of data to cache in memory'),
    arcGISCategory=_('Performance tuning options'))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'xBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``x`` direction. The
size is given as the number of cells. If this parameter is 0, no blocks will
be cached in memory."""),
    arcGISDisplayName=_('In-memory cache block size, in X direction'),
    arcGISCategory=_('Performance tuning options'))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'yBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``y`` direction. The
size is given as the number of cells. If this parameter is 0, no blocks will
be cached in memory."""),
    arcGISDisplayName=_('In-memory cache block size, in Y direction'),
    arcGISCategory=_('Performance tuning options'))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'zBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``z`` (depth)
direction. The size is given as the number of cells. If this parameter is 0,
no blocks will be cached in memory. This parameter is ignored if the grids do
not have a ``z`` dimension."""),
    arcGISDisplayName=_('In-memory cache block size, in Z direction'),
    arcGISCategory=_('Performance tuning options'))

AddArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'tBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``t`` (time)
direction. The size is given as the number of cells. If this parameter is 0,
no blocks will be cached in memory. This parameter is ignored if the grids do
not have a ``t`` dimension."""),
    arcGISDisplayName=_('In-memory cache block size, in T direction'),
    arcGISCategory=_('Performance tuning options'))

# Public method: Interpolator.InterpolateArcGISRasterValuesAtPoints

AddMethodMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints,
    shortDescription=_('Interpolates the values of rasters at points.'),
    longDescription=_(
"""This tool provides the same capability as the ArcGIS Spatial Analyst's
Extract Values to Points tool, but offers some additional options and does not
require a Spatial Analyst license to run."""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Interpolate Raster Values at Points'),
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Interpolate\\Raster Values at Points'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')])

CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'cls', Interpolator.InterpolateArcGISRasterValuesAtPoints, 'cls')

AddArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'rasters',
    typeMetadata=ListTypeMetadata(elementType=ArcGISRasterLayerTypeMetadata(mustExist=True), minLength=1),
    description=_("""Rasters or raster layers to interpolate values from."""),
    arcGISDisplayName=_('Rasters'))

AddArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'points',
    typeMetadata=ArcGISFeatureLayerTypeMetadata(mustExist=True, allowedShapeTypes=['Point']),
    description=_(
"""Feature class or layer containing the points at which values should be
interpolated. It is recommended but not required that the points and rasters
use the same coordinate system. If they do not, this tool will attempt to
project the points to the coordinate system of the rasters prior to doing the
interpolation. This may fail if a datum transformation is required, in which
case you will have to manually project the points and rasters to the same
coordinate system before using this tool."""),
    arcGISDisplayName=_('Point features'))

AddArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'fields',
    typeMetadata=ListTypeMetadata(elementType=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64']), minLength=1, mustBeSameLengthAsArgument='rasters'),
    description=_(
"""Fields of the points to receive the interpolated values. You must provide a
field for each raster. The fields must have floating-point or integer data
types. If a field cannot represent the interpolated value at full precision,
the closest approximation will be stored and a warning will be issued. This
will happen, for example, when the raster uses a floating point data type but
the field uses an integer data type."""),
    arcGISDisplayName=_('Fields to receive the interpolated values'),
    arcGISParameterDependencies=['points'])

AddArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'method',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Automatic', 'Nearest', 'Linear'], makeLowercase=True),
    description=_(
"""Interpolation method to use, one of:

* ``Automatic`` - the tool will automatically select the interpolation method
  based on the data type of the raster: for integer rasters, nearest neighbor
  interpolation will be used; for floating-point rasters, linear
  interpolation will be used. This is the default.

* ``Nearest`` - nearest neighbor interpolation. The interpolated value will
  simply be the value of the cell that contains the point.

* ``Linear`` - linear interpolation (also known as bilinear interpolation).
  This method is suitable for continuous data, such as sea surface
  temperatures, but is not appropriate for categorical data (use nearest
  neighbor for categorical data). This method averages the values of the four
  nearest cells, weighting the contribution of each cell by the area of it
  that would be covered by a hypothetical cell centered on the point being
  interpolated. If the cell containing the point contains NoData, the result
  is NoData. Otherwise, and the result is based on the weighted average of the
  four nearest cells that do contain data, including the one that contains the
  cell. If any of the other three cells contain NoData, they are omitted from
  the average. This is the same algorithm implemented by the ArcGIS Spatial
  Analyst's :arcpy_sa:`Extract-Values-to-Points` tool.

"""),
    arcGISDisplayName=_('Interpolation method'))

AddArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'where',
    typeMetadata=SQLWhereClauseTypeMetadata(canBeNone=True),
    description=_(
"""SQL WHERE clause expression that specifies the subset of points to process.
If not provided, all of the points will be processed. If provided but the
underlying storage format does not support WHERE clauses, an exception will be
raised.

The exact syntax of this expression depends on the underlying storage format.
If the underlying data store will be accessed through ArcGIS, `this article
<https://pro.arcgis.com/en/pro-app/latest/help/mapping/navigation/sql-reference-for-elements-used-in-query-expressions.htm>`_
may document some of the possible syntax, but not all of it may be supported
through ArcGIS's underlying Python API.

"""),
    arcGISDisplayName=_('Where clause'),
    arcGISCategory=_('Interpolation options'),
    arcGISParameterDependencies=['points'])

CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'noDataValue', Interpolator.InterpolateArcGISRasterValuesAtPoints, 'noDataValue')

AddArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'rastersWrap',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""Indicates whether or not the left and right edges of the rasters should be
treated as connected. Enable this option when you have rasters that span 360
degrees of longitude and you wish the interpolator to consider cells on the
opposite side of the raster when interpolating values for points very close to
the left or right edge. This option has no effect if nearest neighbor
interpolation is used, because the interpolated value will be based on the
value of the single nearest cell."""),
    arcGISDisplayName=_('Left and right edges of rasters are connected'),
    arcGISCategory=_('Interpolation options'))

AddArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'orderByFields',
    typeMetadata=ListTypeMetadata(elementType=ArcGISFieldTypeMetadata(mustExist=True), minLength=1, canBeNone=True),
    description=_(
"""Fields for defining the order in which the points are processed. The points
may be processed faster if they are ordered geographically, such that points
that are close in geographic space are processed sequentially. Ordering the
points this way increases the probability that the value of a given point can
be interpolated from data that is cached in memory, rather than from data that
must be read from the disk or network, which is much slower. Choose fields
that facilitate this. For example, if your points represent the locations of
animals tracked by satellite telemetry, order the processing first by the
animal ID and then by the transmission date or number."""),
    arcGISDisplayName=_('Order by fields'),
    arcGISCategory=_('Performance tuning options'),
    arcGISParameterDependencies=['points'])

CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'numBlocksToCacheInMemory', Interpolator.InterpolateArcGISRasterValuesAtPoints, 'numBlocksToCacheInMemory')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'xBlockSize', Interpolator.InterpolateArcGISRasterValuesAtPoints, 'xBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'yBlockSize', Interpolator.InterpolateArcGISRasterValuesAtPoints, 'yBlockSize')

AddResultMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'updatedPoints',
    typeMetadata=ArcGISFeatureLayerTypeMetadata(),
    description=_('Updated points.'),
    arcGISDisplayName=_('Updated points'),
    arcGISParameterDependencies=['points'])

# Public method: Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints

AddMethodMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints,
    shortDescription=_('Interpolates values of a time series of rasters at a time series of points.'),
    longDescription=_(
"""Given points that have a date field and a workspace containing a time
series of rasters with dates in their file names, this tool matches the points
to the rasters by date, interpolates values of the rasters at the points, and
stores the result in a field of the points. To be used with this tool, the
rasters must meet several constraints:

* The rasters must all have the same coordinate system, spatial extent, cell
  size, number of rows and columns, data type, and NoData value.

* There must only be one raster for any given date.

* The rasters must occur at a regular time step (e.g. one per day). Many
  "level 3" and "level 4" gridded remote sensing products conform to this
  requirement. For example, level 3 NASA MODIS products are often published at
  daily, 8-day, monthly, and yearly averages. Most "level 1" and "level 2"
  products do not conform to this requirement. Those products usually have
  irregular time spacing between each image. This tool cannot currently handle
  such products.

* It is OK for rasters to be missing from the time series. For example, if the
  rasters are from a satellite remote sensor that failed for a time, and no
  images were published during that period, it is OK for those rasters to not
  exist. The tool will detect this, report a warning, and assume that the
  values of those rasters were NoData.
"""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Interpolate Time Series of Rasters at Points'),
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Interpolate\\Raster Values at Points'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')])

CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'cls', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'cls')

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'points',
    typeMetadata=ArcGISFeatureLayerTypeMetadata(mustExist=True, allowedShapeTypes=['Point']),
    description=_(
"""Feature class or layer containing the points at which values should be
interpolated. The points must have a field that contains the date of each
point and a field to receive the value interpolated from the raster.

It is recommended but not required that the points and rasters use the same
coordinate system. If they do not, this tool will attempt to project the
points to the coordinate system of the rasters prior to doing the
interpolation. This may fail if a datum transformation is required, in which
case you will have to manually project the points and rasters to the same
coordinate system before using this tool."""),
    arcGISDisplayName=_('Point features'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tField',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['date', 'datetime']),
    description=_(
"""Field of the points that specifies the date and time of the point. The
field must have a datetime data type. If the field can only represent dates
with no time component, the time will assumed to be 00:00:00."""),
    arcGISDisplayName=_('Date field'),
    arcGISParameterDependencies=['points'])

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'valueField',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64']),
    description=_(
"""Field of the points to receive the interpolated values. The field must have
a floating-point or integer data type. If the field cannot represent the
interpolated value at full precision, the closest approximation will be stored
and a warning will be issued. This will happen, for example, when you
interpolate floating-point values into an integer field."""),
    arcGISDisplayName=_('Field to receive the interpolated values'),
    arcGISParameterDependencies=['points'])

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'workspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    description=_(
"""Directory or geodatabase containing the time series of rasters. If the
workspace is a directory, the rasters may be stored all at the root level or
they may be nested in a tree that may be multiple levels deep.
`rasterNameExpressions` must reflect the tree structure."""),
    arcGISDisplayName=_('Workspace containing rasters'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'rasterNameExpressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), minLength=1),
    description=_(
"""List of regular expressions specifying how the rasters are named. If the
raster workspace is a geodatabase, the list should have just one entry
corresponding to the raster name. If the raster workspace is a directory, the
list should have one entry for each subdirectory level plus an entry for the
file name. If all of the rasters are contained at the root level, there should
only be the single entry for the file name.

Each entry is a regular expression conforming to Python :py:ref:`re-syntax`.
These expressions have two purposes. First, similar to "wildcard" expressions,
they identify which rasters should be included in the time series and which
should be ignored. For example, if you have both SST and chlorophyll rasters
stored in the same workspace and want to sample values of SST, the expressions
should match on the SST rasters but not match on the chlorophyll rasters. On
the other hand, if you just have one kind of raster in your workspace and
don't have any that you need to ignore, your expressions can be simpler.

The second purpose of the expressions is to parse the date and time components
from the raster names into named regular expression groups. This allows the
tool to determine the date of each raster from its name. The table below lists
the allowed group names, the typical regular expression syntax for parsing
that group from a raster name, and an example fragment from a raster name:

+---------------+------------------------------+------------------------------+
| Group Name    | Typical RegEx Syntax         | Example Raster Name Fragment |
+===============+==============================+==============================+
| ``Year``      | ``(?P<Year>\\d\\d\\d\\d)``       | ``2005``                     |
+---------------+------------------------------+------------------------------+
| ``Month``     | ``(?P<Month>\\d\\d)``          | ``03``                       |
+---------------+------------------------------+------------------------------+
| ``Day``       | ``(?P<Day>\\d\\d)``            | ``28``                       |
+---------------+------------------------------+------------------------------+
| ``DayOfYear`` | ``(?P<DayOfYear>\\d\\d\\d)``    | ``265``                      |
+---------------+------------------------------+------------------------------+
| ``Hour``      | ``(?P<Hour>\\d\\d)``           | ``14``                       |
+---------------+------------------------------+------------------------------+
| ``Minute``    | ``(?P<Minute>\\d\\d)``         | ``52``                       |
+---------------+------------------------------+------------------------------+
| ``Second``    | ``(?P<Second>\\d\\d)``         | ``08``                       |
+---------------+------------------------------+------------------------------+

At minimum, the `rasterNameExpressions` must include the ``Year``. If this is
the only date component included, the date will assumed to be January 1. If
``Month`` is also included but ``Day`` is not, ``Day`` will assumed to be 1.
If ``Day`` is included, ``Month`` must also be included. Do not include both
``Month`` and ``DayOfYear``, just one or the other. If ``Hour``, ``Minute``,
or ``Second`` is not included, they will be assumed to be ``00``.

Here are some examples. If you have any questions, please feel free to email
the MGET development team.

**Example 1: Monthly SST rasters all in the same workspace**

In this example, there is a single workspace with rasters named::

    sst_199801
    sst_199802
    sst_199803
    ...

Here, you just need one expression::

    sst_(?P<Year>\\d\\d\\d\\d)(?P<Month>\\d\\d)

This regular expression means "the characters ``sst\\_`` followed by four
numeric digits representing the ``Year`` followed by two numeric digits
representing the ``Month``". The following expression is more flexible and
will match any raster that ends in six digits::

    .+(?P<Year>\\d\\d\\d\\d)(?P<Month>\\d\\d)

This regular expression means "one or more of any character followed
by four numeric digits representing the ``Year`` followed by two numeric
digits representing the ``Month``".

**Example 2: Daily SST rasters stored in yearly subdirectories**

In this example, the workspace, a directory, contains a subdirectory for each
year of data. The rasters are named with the year and day of year and have a
.img file suffix::

    1998
        sst_1998_001.img
        sst_1998_002.img
        ...
        sst_1998_365.img
    1999
        sst_1999_001.img
        sst_1999_002.img
        ...
        sst_1999_365.img
    ...

Here, you need two expressions, one for the year subdirectory and one for the
raster name::

    (?P<Year>\\d\\d\\d\\d)
    sst_(?P<Year>\\d\\d\\d\\d)_(?P<DayOfYear>\\d\\d\\d).img

**Example 3: Daily SST rasters with month and day of month**

This is the same as the example above, but the rasters are named with month
and day of the month instead of the day of the year::

    1998
        sst_1998_01_01.img
        sst_1998_01_02.img
        ...
        sst_1998_01_31.img
        sst_1998_02_01.img
        ...
        sst_1998_12_31.img
    1999
        sst_1999_01_01.img
        sst_1999_01_02.img
        ...
        sst_1999_12_31.img
    ...

Suitable expressions are::

    (?P<Year>\\d\\d\\d\\d)
    sst_(?P<Year>\\d\\d\\d\\d)_(?P<Month>\\d\\d)_(?P<Day>\\d\\d).img

"""),
    arcGISDisplayName=_('Raster name expressions'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tCornerCoordType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_(
"""Type of time coordinate that is parsed from the raster name:

* ``min`` - The time coordinate represents the beginning of the window of time
  for which the raster is valid. Most data providers publish their images
  using this convention. For example, the monthly files from the NOAA AVHRR
  Pathfinder SST version 5.0/5.1 dataset include the four-digit year and
  two-digit month, but no day of the month. These images represent the mean
  SST over the focal month. Since the file name does not include a day of the
  month, hour, minute, or second, the tool assumes the parsed time coordinate
  is for day 1 of the month, at time 00:00:00. This is the beginning of the
  one-month window to which the image applies, so "min" is the appropriate
  type of time coordinate.

* ``center`` - The time coordinate represents the center of the window of time
  for which the raster is valid. This is the next-most-popular type of time
  coordinate used by data providers. One example of this are the sea surface
  height (SSH) images published by Aviso in the 2010s (prior to Aviso
  releasing their data through Copernicus Marine Service). These files were
  published with a 7-day time step, but each image incorporated satellite
  altimeter observations before and after the focal date. Thus, the focal date
  occurred at the center of these observations.

* ``max`` - The time coordinate represents the end of the window of time for
  which the raster is valid. So far, the MGET development team has not
  encountered a data provider that uses this convention, but we have included
  it for completeness, in case such data do exist.

"""),
    arcGISDisplayName=_('Time coordinate type'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tIncrement',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.),
    description=_(
"""Time step of the rasters, in the units of specified by the `tIncrementUnit`
parameter.

Some examples:

+-----------------------+-----------+----------------+
| For Rasters Occurring | Time Step | Time Step Unit |
+=======================+===========+================+
| Every day             |     1     | day            |
+-----------------------+-----------+----------------+
| Every week            |     7     | day            |
+-----------------------+-----------+----------------+
| Every 8 days          |     8     | day            |
+-----------------------+-----------+----------------+
| Every month           |     1     | month          |
+-----------------------+-----------+----------------+
| Every year            |     1     | year           |
+-----------------------+-----------+----------------+

"""),
    arcGISDisplayName=_('Time step'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tIncrementUnit',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['year', 'month', 'day', 'hour', 'minute', 'second'], makeLowercase=True),
    description=_(
"""Unit of the `tIncrement` parameter."""),
    arcGISDisplayName=_('Time step unit'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tSemiRegularity',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['annual'], makeLowercase=True, canBeNone=True),
    description=_(
"""Use this parameter when your rasters always start on January 1, advance at
a constant time step that does not add up to a full year, and the last raster
covers only part of the normal time step.

For example, NASA and NOAA frequently publish rasters that have 8-day time
steps but always start on January 1 of each year. The first 45 rasters of each
year cover the full 8 days but the 46th raster only covers 5 or 6 days
(depending on whether it is a leap year). For these datasets, you should set
`tSemiregularity` to ``annual`` and `tCountPerSemiRegularPeriod` to ``46``.

Please consult the MGET development team for more help with this
parameter."""),
    arcGISDisplayName=_('Temporal semiregularity'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tCountPerSemiRegularPeriod',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Number of rasters per semiregular period. This parameter is ignored if
`tSemiRegularity` is omitted. Please see the documentation for that parameter
for more information."""),
    arcGISDisplayName=_('Rasters per semiregular period'))

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'method',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Automatic', 'Nearest', 'Linear'], makeLowercase=True),
    description=_(
"""Interpolation method to use, one of:

* ``Automatic`` - the tool will automatically select the interpolation method
  based on the raster's data type: for integer rasters, nearest neighbor
  interpolation; for floating-point rasters, linear interpolation. This is the
  default.

* ``Nearest`` - nearest neighbor interpolation. The interpolated value will
  simply be the value of the cell that contains the point.

* ``Linear`` - linear interpolation (also known as trilinear interpolation).
  This method is suitable for continuous data such as sea surface temperature,
  but not for categorical data such as sediment type classifications (use
  nearest neighbor instead). This method averages the values of the eight
  nearest cells in the x, y, and time dimensions, weighting the contribution
  of each cell by the area of it that would be covered by a hypothetical cell
  centered on the point being interpolated. If the cell containing the point
  contains NoData, the result is NoData. Otherwise, and the result is based on
  the weighted average of the eight nearest cells that do contain data,
  including the one that contains the cell. If any of the other seven cells
  contain NoData, they are omitted from the average. This is a 3D version of
  the bilinear interpolation implemented by the ArcGIS Spatial Analyst's
  :arcpy_sa:`Extract-Values-to-Points` tool.

"""),
    arcGISDisplayName=_('Interpolation method'))

CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'where', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'where')
CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'noDataValue', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'noDataValue')
CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'rastersWrap', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'rastersWrap')

AddArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'orderByFields',
    typeMetadata=ListTypeMetadata(elementType=ArcGISFieldTypeMetadata(mustExist=True), minLength=1, canBeNone=True),
    description=_(
"""Fields for defining the order in which the points are processed. The points
may be processed faster if they are ordered temporally and geographically,
such that points that are close in time and space are processed sequentially.
Ordering the points this way increases the probability that the value of a
given point can be interpolated from data that is cached in memory, rather
than from data that must be read from the disk or network, which is much
slower. Choose fields that facilitate this. For example, if your points
represent the locations of animals tracked by satellite telemetry, order the
processing first by the animal ID and then by the transmission date or number.

By default, if you do not specify anything for this parameter, the
points will be ordered by the points' Date Field."""),
    arcGISDisplayName=_('Order by fields'),
    arcGISCategory=_('Performance tuning options'),
    arcGISParameterDependencies=['points'])

CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'numBlocksToCacheInMemory', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'numBlocksToCacheInMemory')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'xBlockSize', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'xBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'yBlockSize', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'yBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'tBlockSize', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tBlockSize')

CopyResultMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'updatedPoints', Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'updatedPoints')

# Public method: Interpolator.InpaintArcGISRaster

AddMethodMetadata(Interpolator.InpaintArcGISRaster,
    shortDescription=_('Interpolates values for the NoData cells of a raster.'),
    longDescription=_(
"""To run this tool, you either must have MATLAB R2024b or MATLAB Runtime R2024b
installed. The MATLAB Runtime is free and may be downloaded from
https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html.
Please follow the installation instructions carefully. Version R2024b must be
used; other versions will not work. MATLAB Runtime allows multiple versions
can be installed at the same time.

Use this tool to guess values for small clusters of NoData cells in rasters
representing continuous surfaces, e.g. images of sea surface temperature in
which cloudy pixels contain NoData. This tool provides several advantages over
traditional moving-window methods provided by ArcGIS, such as the Focal
Statistics tool of the ArcGIS Spatial Analyst:

* It uses methods based on differential calculus that may provide more
  accurate guesses than traditional approaches, such as computing the focal
  mean of a 3x3 neighborhood.

* It accurately handles rasters with global longitudinal extent, for which the
  east and west edges are connected.

* It can fill NoData clusters of any size.

Although this tool can fill NoData clusters of any size, you should apply
common sense when using it. The larger the cluster, the less accurate the
guessed values will be, especially for rasters that represent a noisy
surface.

This tool is implemented in MATLAB using the `inpaint_nans
<https://www.mathworks.com/matlabcentral/fileexchange/4551-inpaint_nans>`_
function developed by John D'Errico. Many thanks to him for developing and
sharing this function. Please see GeoEco's LICENSE file for the relevant
copyright statement."""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Interpolate NoData Cells'),
    arcGISToolCategory=_('Spatial and Temporal Analysis\\Interpolate\\Raster Values for NoData Cells'),
    dependencies=[ArcGISDependency(), MatlabDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')])

CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'cls', Interpolator.InpaintArcGISRaster, 'cls')

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'inputRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_("""Raster containing NoData cells to be filled."""),
    arcGISDisplayName=_('Input raster'))

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'outputRaster',
    typeMetadata=ArcGISRasterTypeMetadata(mustBeDifferentThanArguments=['inputRaster'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""The output raster will be identical to the input raster where the input
raster has data. For cells of the input raster that do not have data, the
output raster will contain values interpolated according to parameters of this
tool.

If this is a file system path, missing directories in the path will be
created."""),
    direction='Output',
    arcGISDisplayName=_('Output raster'))

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'method',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True, allowedValues=['Del2a', 'Del2b', 'Del2c', 'Del4', 'Spring']),
    description=_(
"""Method to use for interpolation and extrapolation of NoData values. One of:

* ``Del2a`` - Performs Laplacian interpolation and linear extrapolation.

* ``Del2b`` - Same as ``Del2a`` but does not build as large a linear system of
  equations. May use less memory and be faster than ``Del2a``, at the cost of
  some accuracy. Use this method if ``Del2a`` fails due to insufficient memory
  or if it is too slow.

* ``Del2c`` - Same as ``Del2a`` but solves a direct linear system of equations
  for the NoData values. Faster than both ``Del2a`` and ``Del2b`` but is the
  least robust to noise on the boundaries of NoData cells and least able to
  interpolate accurately for smooth surfaces. Use this method if ``Del2a`` and
  ``Del2b`` both fail due to insufficient memory or are too slow.

* ``Del4`` - Same as ``Del2a`` but instead of the Laplace operator (also
  called the ∇\\ :sup:`2` operator) it uses the biharmoic operator (also
  called the ∇\\ :sup:`4` operator). May result in more accurate
  interpolations, at some cost in speed.

* ``Spring`` - Uses a spring metaphor. Assumes springs (with a nominal length
  of zero) connect each cell with every neighbor (horizontally, vertically and
  diagonally). Since each cell tries to be like its neighbors, extrapolation
  is as a constant function where this is consistent with the neighboring
  nodes.

"""),
    arcGISDisplayName=_('Method'))

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'maxHoleSize',
    typeMetadata=IntegerTypeMetadata(mustBeGreaterThan=0, canBeNone=True),
    description=_(
"""Maximum size, in cells, that a region of 4-connected NoData cells may be
for it to be filled in. Use this option to prevent the filling of large NoData
regions (e.g. large clouds in remote sensing images) when you are concerned
that values cannot be accurately guessed for those regions. If this option is
omitted, all regions will be filled, regardless of size."""),
    arcGISDisplayName=_('Maximum size of NoData regions'))

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'xEdgesWrap',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the left and right edges of the raster are assumed to be connected
and computations along those edges will consider the values on the opposite
side of the raster."""),
    arcGISDisplayName=_('East and west edges are connected'))

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'minValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Minimum allowed value to use when NoData cells are interpolated (or
extrapolated). If this parameter is provided, all cells with less than the
minimum value will be rounded up to the minimum. This includes not just the
cells that had NoData in the original raster and were then interpolated or
extrapolated, but also the cells that had values in the original raster.

Use this parameter when the interpolation/extrapolation algorithm produces
impossibly low values. For example, consider a situation in which a
chlorophyll concentration raster coincidentally shows a negative gradient
approaching a cloud that straddles the edge of the raster. Missing pixels at
the edge of the raster will be filled by extrapolation. If the negative
gradient is strong enough, the algorithm might extrapolate negative
concentrations for the cloudy pixels. This should be impossible; chlorophyll
concentration must be zero or higher. To enforce that, you could specify a
minimum value of zero (or a very small non-zero number, if exactly zero would
be problematic, as might occur if the values were in a log scale)."""),
    arcGISDisplayName=_('Minimum value'))

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'maxValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Maximum allowed value to use when NoData cells are interpolated (or
extrapolated). If this parameter is provided, all cells with greater than the
maximum value will be rounded up to the maximum. This includes not just the
cells that had NoData in the original raster and were then interpolated or
extrapolated, but also the cells that had values in the original raster.

Use this parameter when the interpolation/extrapolation algorithm produces
impossibly high values. For example, consider a situation in which a percent
sea ice concentration raster shows a positive gradient approaching the
coastline but does not provide data right up to shore. Say you wanted to fill
the missing cells close to shore and were willing to assume that whatever
gradient occurred nearby was reasonable for filling them in. If the positive
gradient is strong enough, the algorithm might extrapolate ice concentration
values greater than 100 percent, which is impossible. To prevent values from
exceeding 100 percent, you could specify a maximum value of 100."""),
    arcGISDisplayName=_('Maximum value'))

AddArgumentMetadata(Interpolator.InpaintArcGISRaster, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output raster will be overwritten, if it exists. If False, a
:exc:`ValueError` will be raised if the output raster exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

###############################################################################
# Batch processing versions of methods
###############################################################################

from GeoEco.BatchProcessing import BatchProcessing
from GeoEco.DataManagement.ArcGISRasters import ArcGISRaster
from GeoEco.DataManagement.Fields import Field

BatchProcessing.GenerateForMethod(Interpolator.InpaintArcGISRaster,
    inputParamNames=['inputRaster'],
    inputParamFieldArcGISDisplayNames=[_('Input raster field')],
    inputParamDescriptions=[_('%s input rasters.')],
    outputParamNames=['outputRaster'],
    outputParamFieldArcGISDisplayNames=[_('Output raster field')],
    outputParamExpressionArcGISDisplayNames=[_('Output raster Python expression')],
    outputParamDescriptions=[_(
"""%s output rasters.

The output rasters will be identical to the input rasters where the input
rasters have data. For cells of the input rasters that do not have data, the
output rasters will contain values interpolated according to parameters of
this tool.

If these paths refers to the file system, missing directories in the paths
will be created if they do not exist.""")],
    outputParamExpressionDescriptions=[
"""Python expression used to calculate the absolute path of an output raster.
The expression may be any Python statement appropriate for passing to the
:py:func:`eval` function and must return a string. The expression may
reference the following variables:


* ``workspaceToSearch`` - the value provided for the workspace to search
  parameter

* ``destinationWorkspace`` - the value provided for the destination workspace
  parameter

* ``inputRaster`` - the absolute path to the input raster

The default expression,
``os.path.join(destinationWorkspace, inputRaster[len(workspaceToSearch)+1:])``,
stores the raster in the destination workspace at the same relative location
it appears in the workspace to search. The destination path is calculated by
stripping the workspace to search from the source path and replacing it with
the destination workspace."""],
    outputParamDefaultExpressions=['os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])'],
    constantParamNames=['method', 'maxHoleSize', 'xEdgesWrap', 'minValue', 'maxValue'],
    processListMethodName='InpaintArcGISRasterList',
    processListMethodShortDescription=_('Interpolates values for the NoData cells for each ArcGIS raster in a list.'),
    processTableMethodName='InpaintArcGISRasterTable',
    processTableMethodShortDescription=_('Interpolates values for the NoData cells for each ArcGIS raster in a table.'),
    processArcGISTableMethodName='InpaintArcGISRasterArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Interpolate NoData Cells for ArcGIS Rasters Listed in Table'),
    findAndProcessMethodName='FindAndInpaintArcGISRasters',
    findAndProcessMethodArcGISDisplayName='Find ArcGIS Rasters and Interpolate NoData Cells',
    findAndProcessMethodShortDescription=_('Finds rasters in an ArcGIS workspace and interpolates values for the NoData cells.'),
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

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['Interpolator']
