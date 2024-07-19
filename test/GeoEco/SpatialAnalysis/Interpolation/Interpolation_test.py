# Interpolation_test.py - pytest tests for GeoEco.DataManagement.Interpolation.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os
import pathlib

import numpy
import pytest

from GeoEco.Datasets import Dataset, NumpyGrid
from GeoEco.Datasets.ArcGIS import ArcGISRaster
from GeoEco.Datasets.SQLite import SQLiteDatabase
from GeoEco.Logging import Logger
from GeoEco.SpatialAnalysis.Interpolation import Interpolator

Logger.Initialize()


def isArcPyInstalled():
    success = False
    try:
        import arcpy
        success = True
    except:
        pass
    return success


@pytest.fixture
def testInpaintRasterPath():
    return pathlib.Path(__file__).parent / 'GSMChl_gaussian_2006160.img'


@pytest.mark.skipif(not isArcPyInstalled(), reason='ArcGIS arcpy module is not installed')
class TestInpaintArcGISRaster():

    def test_InpaintFull(self, testInpaintRasterPath, tmp_path):
        assert testInpaintRasterPath.is_file()
        outputRaster = tmp_path / 'output.img'
        Interpolator.InpaintArcGISRaster(testInpaintRasterPath, outputRaster)
        inpaintedGrid = ArcGISRaster.GetRasterBand(outputRaster)
        expectedGrid = ArcGISRaster.GetRasterBand(pathlib.Path(__file__).parent / 'Inpainted_full.img')
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

    def test_InpaintSmallHoles(self, testInpaintRasterPath, tmp_path):
        assert testInpaintRasterPath.is_file()
        outputRaster = tmp_path / 'output.img'
        Interpolator.InpaintArcGISRaster(testInpaintRasterPath, outputRaster, maxHoleSize=200)
        inpaintedGrid = ArcGISRaster.GetRasterBand(outputRaster)
        expectedGrid = ArcGISRaster.GetRasterBand(pathlib.Path(__file__).parent / 'Inpainted_small_holes.img')
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

    def test_InpaintSmallHolesMinMax(self, testInpaintRasterPath, tmp_path):
        assert testInpaintRasterPath.is_file()
        outputRaster = tmp_path / 'output.img'
        Interpolator.InpaintArcGISRaster(testInpaintRasterPath, outputRaster, maxHoleSize=200, minValue=-1.3, maxValue=-0.2)
        inpaintedGrid = ArcGISRaster.GetRasterBand(outputRaster)
        expectedGrid = ArcGISRaster.GetRasterBand(pathlib.Path(__file__).parent / 'Inpainted_min_max.img')
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)


class TestInterpolatePointsInTable():

    def test_yx(self):

        # Define a global geographic grid with a cell size of 45 degrees.

        a = numpy.arange(32, dtype='int32').reshape((4,8))
        sr = Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'obj')
        grid1 = NumpyGrid(numpyArray=a,
                          displayName="global 45 test grid",
                          spatialReference=sr,
                          dimensions='yx',
                          coordIncrements=(45.,45.),
                          cornerCoords=(-90.+45./2, -180.+45./2))

        b = a * 2
        grid2 = NumpyGrid(numpyArray=b,
                          displayName="global 45 test grid 2",
                          spatialReference=sr,
                          dimensions='yx',
                          coordIncrements=(45.,45.),
                          cornerCoords=(-90.+45./2, -180.+45./2))

        # Define and populate an in-memory SQLite table to hold test points.

        db = SQLiteDatabase(':memory:')
        table = db.CreateTable('TempTable1')
        table.AddField('x', 'float64')
        table.AddField('y', 'float64')
        table.AddField('ExpectedNN', 'float64')
        table.AddField('ExpectedLinear', 'float64')
        table.AddField('InterpNN', 'float64', isNullable=True)
        table.AddField('InterpLinear', 'float64', isNullable=True)
        table.AddField('ExpectedNN2', 'float64')
        table.AddField('ExpectedLinear2', 'float64')
        table.AddField('InterpNN2', 'float64', isNullable=True)
        table.AddField('InterpLinear2', 'float64', isNullable=True)

        # Define test points at cell centers.

        points = []
        for xi in range(8):
            for yi in range(4):
                points.append([-180. + xi*45. + 45./2, -90 + yi*45. + 45./2, float(xi + 8*yi), float(xi + 8*yi)])

        # Define test points at lower-left corners.

        for yi in range(4):
            for xi in range(8):
                expectedLinear = []
                if yi > 0:
                    expectedLinear.append(float((xi-1 if xi > 0 else 7) + 8*(yi-1)))    # lower-left cell
                    expectedLinear.append(float(xi + 8*(yi-1)))                         # lower-right cell
                expectedLinear.append(float((xi-1 if xi > 0 else 7) + 8*yi))            # upper-left cell
                expectedLinear.append(float(xi + 8*yi))                                 # upper-right cell

                points.append([-180. + xi*45., 
                               -90 + yi*45., 
                               float(xi + 8*yi), 
                               sum(expectedLinear) / len(expectedLinear)])

        # Define test points that are vertically centered and halfway right of center.

        for xi in range(8):
            for yi in range(4):
                points.append([-180. + xi*45. + 45.*0.75, 
                               -90 + yi*45. + 45.*0.5, 
                               float(xi + 8*yi), 
                               0.75*float(xi + 8*yi) + 0.25*((xi+1 if xi < 7 else 0) + 8*yi)])

        # Define test points that are halfway up and right of center.

        for xi in range(8):
            for yi in range(4):
                weight = 16. if yi < 3 else 12.
                expectedLinear = 9/weight * float(xi + 8*yi)                                 # lower-left cell
                expectedLinear += 3/weight * float((xi+1 if xi < 7 else 0) + 8*yi)           # lower-right cell
                if yi < 3:
                    expectedLinear += 3/weight * float(xi + 8*(yi+1))                        # upper-left cell
                    expectedLinear += 1/weight * float((xi+1 if xi < 7 else 0) + 8*(yi+1))   # upper-right cell

                points.append([-180. + xi*45. + 45.*0.75, 
                               -90 + yi*45. + 45.*0.75, 
                               float(xi + 8*yi), 
                               expectedLinear])

        # Insert the test points.

        i = 1
        with table.OpenInsertCursor() as cursor:
            for x, y, expectedNN, expectedLinear in points:
                Logger.Debug('***** Row %i', i)
                cursor.SetValue('x', x)
                cursor.SetValue('y', y)
                cursor.SetValue('ExpectedNN', expectedNN)
                cursor.SetValue('ExpectedLinear', expectedLinear)
                cursor.SetValue('ExpectedNN2', expectedNN*2)
                cursor.SetValue('ExpectedLinear2', expectedLinear*2)
                cursor.InsertRow()
                i += 1

        # Run nearest neighbor and linear interpolations.

        Interpolator.InterpolateGridsValuesForTableOfPoints(grids=[grid1, grid2], 
                                                            table=table,
                                                            fields=['InterpNN', 'InterpNN2'],
                                                            xField='x',
                                                            yField='y',
                                                            spatialReference=sr,
                                                            method='Nearest',
                                                            gridsWrap=True,
                                                            orderBy='ObjectID ASC')

        Interpolator.InterpolateGridsValuesForTableOfPoints(grids=[grid1, grid2], 
                                                            table=table,
                                                            fields=['InterpLinear', 'InterpLinear2'],
                                                            xField='x',
                                                            yField='y',
                                                            spatialReference=sr,
                                                            method='Linear',
                                                            gridsWrap=True,
                                                            orderBy='ObjectID ASC')

        # Compare the results.

        fieldNames = [field.Name for field in table.Fields]

        with table.OpenSelectCursor(orderBy='ObjectID ASC') as cursor:
            while cursor.NextRow():
                row = {name: cursor.GetValue(name) for name in fieldNames}
                Logger.Debug('Row: %r', row)
                assert row['ExpectedNN'] == row['InterpNN']
                assert row['ExpectedLinear'] == row['InterpLinear']
                assert row['ExpectedNN2'] == row['InterpNN2']
                assert row['ExpectedLinear2'] == row['InterpLinear2']

    def test_yx_nodata_cases(self):

        # Define a geographic grid that is not global.

        a = numpy.arange(100, dtype='int32').reshape((10,10))
        sr = Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'obj')
        grid = NumpyGrid(numpyArray=a,
                         displayName="1 degree test grid",
                         spatialReference=sr,
                         dimensions='yx',
                         coordIncrements=(1.,1.),
                         cornerCoords=(0.5, 0.5),
                         unscaledNoDataValue=-1.)

        # Add some NoData values.

        noDataCoords = [[2,2],
                        [2,7],
                        [3,7],
                        [7,2],
                        [7,3],
                        [8,2],
                        [7,7],
                        [7,8],
                        [8,7],
                        [8,8]]

        for y, x in noDataCoords:
            grid.Data[y,x] = -1

        # Define and populate an in-memory SQLite table to hold test points.

        db = SQLiteDatabase(':memory:')
        table = db.CreateTable('TempTable1')
        table.AddField('x', 'float64')
        table.AddField('y', 'float64')
        table.AddField('ExpectedNN', 'float64', isNullable=True)
        table.AddField('ExpectedLinear', 'float64', isNullable=True)
        table.AddField('InterpNN', 'float64', isNullable=True)
        table.AddField('InterpLinear', 'float64', isNullable=True)

        # Define test points at cell centers.

        points = []
        for xi in range(10):
            for yi in range(10):
                isNoData = [yi,xi] in noDataCoords
                points.append([0. + xi*1 + 0.5, 
                               0. + yi*1 + 0.5, 
                               float(xi + 10*yi) if not isNoData else None, 
                               float(xi + 10*yi) if not isNoData else None])

        # Define test points around the edges of the grid, at cell centers.

        for xi in [0, 9]:
            for yi in range(10):
                isNoData = [yi,xi] in noDataCoords
                points.append([0. if xi == 0 else 9.999999999999998,            # Largest IEEE 764 64-bit float smaller than 10.0. We can't pick 10.0 or it will be considered outside the cell.
                               0. + yi*1 + 0.5, 
                               float(xi + 10*yi) if not isNoData else None, 
                               float(xi + 10*yi) if not isNoData else None])

        for xi in range(10):
            for yi in [0,9]:
                isNoData = [yi,xi] in noDataCoords
                points.append([0. + xi*1 + 0.5,
                               0. if yi == 0 else 9.999999999999998,            # See note above
                               float(xi + 10*yi) if not isNoData else None, 
                               float(xi + 10*yi) if not isNoData else None])

        # Define test points around the edges of the grid, at lower / left corners.

        for xi in [0, 9]:
            for yi in range(10):
                isNoData = [yi,xi] in noDataCoords
                points.append([0. if xi == 0 else 9.999999999999998,            # See note above
                               0. + yi*1, 
                               float(xi + 10*yi) if not isNoData else None, 
                               (xi if yi == 0 else (float(xi + 10*yi) + float(xi + 10*(yi-1)))/2) if not isNoData else None])

        for xi in range(10):
            for yi in [0,9]:
                isNoData = [yi,xi] in noDataCoords
                points.append([0. + xi*1,
                               0. if yi == 0 else 9.999999999999998,            # See note above
                               float(xi + 10*yi) if not isNoData else None, 
                               (10*yi if xi == 0 else (float(xi + 10*yi) + float((xi-1) + 10*yi))/2) if not isNoData else None])

        # Define test points around the NoData cell at 2,2.

        points.append([2.50, 1.75, 2+10*1, 2+10*1])                                             # directly below
        points.append([2.50, 3.25, 2+10*3, 2+10*3])                                             # directly below
        points.append([1.75, 2.50, 1+10*2, 1+10*2])                                             # directly left
        points.append([3.25, 2.50, 3+10*2, 3+10*2])                                             # directly right

        points.append([1.75, 1.75, 1+10*1, 9/15*(1+10*1) + 3/15*(2+10*1) + 3/15*(1+10*2)])      # below left
        points.append([3.25, 1.75, 3+10*1, 9/15*(3+10*1) + 3/15*(2+10*1) + 3/15*(3+10*2)])      # below right
        points.append([1.75, 3.25, 1+10*3, 9/15*(1+10*3) + 3/15*(2+10*3) + 3/15*(1+10*2)])      # above left
        points.append([3.25, 3.25, 3+10*3, 9/15*(3+10*3) + 3/15*(2+10*3) + 3/15*(3+10*2)])      # above right

        # Insert the test points.

        i = 1
        with table.OpenInsertCursor() as cursor:
            for x, y, expectedNN, expectedLinear in points:
                Logger.Debug('***** Row %i', i)
                cursor.SetValue('x', x)
                cursor.SetValue('y', y)
                cursor.SetValue('ExpectedNN', expectedNN)
                cursor.SetValue('ExpectedLinear', expectedLinear)
                cursor.InsertRow()
                i += 1

        # Run nearest neighbor and linear interpolations.

        Interpolator.InterpolateGridsValuesForTableOfPoints(grids=[grid], 
                                                            table=table,
                                                            fields=['InterpNN'],
                                                            xField='x',
                                                            yField='y',
                                                            spatialReference=sr,
                                                            method='Nearest',
                                                            orderBy='ObjectID ASC')

        Interpolator.InterpolateGridsValuesForTableOfPoints(grids=[grid], 
                                                            table=table,
                                                            fields=['InterpLinear'],
                                                            xField='x',
                                                            yField='y',
                                                            spatialReference=sr,
                                                            method='Linear',
                                                            orderBy='ObjectID ASC')

        # Compare the results.

        fieldNames = [field.Name for field in table.Fields]

        with table.OpenSelectCursor(orderBy='ObjectID ASC') as cursor:
            while cursor.NextRow():
                row = {name: cursor.GetValue(name) for name in fieldNames}
                Logger.Debug('Row: %r', row)
                assert row['ExpectedNN'] == row['InterpNN']
                assert row['ExpectedNN'] is None and row['InterpNN'] is None or abs(row['ExpectedLinear'] - row['InterpLinear']) < 1e-14      # Extremely small errors due IEEE 754 precision issues

