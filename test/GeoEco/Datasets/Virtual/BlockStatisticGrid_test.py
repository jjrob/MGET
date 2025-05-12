# BlockStatisticGrid_test.py - pytest tests for
# GeoEco.Datasets.Virtual.BlockStatisticGrid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import functools
import math
import warnings

from dateutil.relativedelta import relativedelta
import numpy
import pytest

from GeoEco.Datasets import NumpyGrid
from GeoEco.Datasets.Virtual import BlockStatisticGrid


class TestBlockStatisticGrid():

    def test_DataType_NoDataValue(self):

        # Allocate a small NumpyGrid with some test data and test that
        # DataType and NoDataValue are correct for various statistics.

        data = numpy.arange(6*8, dtype='int32').reshape(6,8)
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(1.,1.), cornerCoords=(0.,0.), unscaledNoDataValue=-1)

        for statistic in ['count']:
            grid2 = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=2)
            assert grid2.DataType == 'int32'
            assert grid2.NoDataValue == 0

        for statistic in ['minimum', 'maximum']:
            grid2 = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=2)
            assert grid2.DataType == 'int32'
            assert grid2.NoDataValue == -1

        for statistic in ['range']:
            grid2 = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=2)
            assert grid2.DataType == 'uint32'
            assert grid2.NoDataValue == 4294967295

            data2 = numpy.arange(6*8, dtype='uint8').reshape(6,8)
            grid2 = NumpyGrid(numpyArray=data2, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(1.,1.), cornerCoords=(0.,0.), unscaledNoDataValue=200)
            grid3 = BlockStatisticGrid(grid=grid2, statistic=statistic, xySize=2)
            assert grid2.DataType == 'uint8'
            assert grid2.NoDataValue == 200

        for statistic in ['mean', 'standard_deviation', 'sum']:
            grid2 = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=2)
            assert grid2.DataType == 'float64'
            assert grid2.NoDataValue == float(numpy.finfo('float64').min)

        for dtype in ['float32', 'float64']:
            data = numpy.arange(6*8, dtype=dtype).reshape(6,8)
            grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(1.,1.), cornerCoords=(0.,0.), unscaledNoDataValue=-1.5)

            for statistic in ['count']:
                grid2 = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=2)
                assert grid2.DataType == 'int32'
                assert grid2.NoDataValue == 0

            for statistic in ['minimum', 'maximum', 'range']:
                grid2 = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=2)
                assert grid2.DataType == dtype
                assert grid2.NoDataValue == -1.5

            for statistic in ['mean', 'standard_deviation', 'sum']:
                grid2 = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=2)
                assert grid2.DataType == dtype
                assert grid2.NoDataValue == float(numpy.finfo(dtype).min)

        # Allocate large grids to test DataType for the count statistic.

        data = numpy.zeros(2**32, dtype='int8').reshape(2**16,2**16)
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(1.,1.), cornerCoords=(0.,0.), unscaledNoDataValue=-1)
        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=int(2**15.5))
        assert grid2.DataType == 'int32'
        assert grid2.NoDataValue == 0

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=int(2**15.6))
        assert grid2.DataType == 'uint32'
        assert grid2.NoDataValue == 0

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2**16)
        assert grid2.DataType == 'int64'

    # The following test works if I run this .py file in isolation but not
    # when I run pytest across GeoEco's entire suite of tests. I could not
    # figure out why so I commented this out. But I did verify it manually.

    # def test_Warnings(self, caplog):
    #     data = numpy.arange(6*8, dtype='int32').reshape(6,8)
    #     grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(0.5,0.3), cornerCoords=(0.,0.))
    #     grid2 = BlockStatisticGrid(grid=grid, statistic='count')
    #     assert 'Neither xySize, nor zSize, nor tSize was provided' in caplog.text
    #     assert grid2.NoDataValue == 0


    def test_CoordIncrements(self):

        # Allocate a small NumpyGrid with some test data and test that
        # CoordIncrements comes out correctly.

        data = numpy.arange(6*8, dtype='int32').reshape(6,8)
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(0.5,0.3), cornerCoords=(0.,0.))

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=1)
        assert len(grid2.CoordIncrements) == 2
        assert grid2.CoordIncrements[0] == 0.5
        assert grid2.CoordIncrements[1] == 0.3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2)
        assert len(grid2.CoordIncrements) == 2
        assert grid2.CoordIncrements[0] == 0.5 * 2
        assert grid2.CoordIncrements[1] == 0.3 * 2

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=3)
        assert len(grid2.CoordIncrements) == 2
        assert grid2.CoordIncrements[0] == 0.5 * 3
        assert grid2.CoordIncrements[1] == 0.3 * 3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=10)
        assert len(grid2.CoordIncrements) == 2
        assert grid2.CoordIncrements[0] == 0.5 * 10
        assert grid2.CoordIncrements[1] == 0.3 * 10

        # Test with z coordinates.

        data = numpy.arange(3*6*8, dtype='int32').reshape(3,6,8)
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='zyx', coordIncrements=(0.7,0.5,0.3), cornerCoords=(0.,0.,0.))

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=1)
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 0.7
        assert grid2.CoordIncrements[1] == 0.5
        assert grid2.CoordIncrements[2] == 0.3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=3)
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 0.7
        assert grid2.CoordIncrements[1] == 0.5 * 3
        assert grid2.CoordIncrements[2] == 0.3 * 3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', zSize=3)
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 0.7 * 3
        assert grid2.CoordIncrements[1] == 0.5
        assert grid2.CoordIncrements[2] == 0.3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2, zSize=3)
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 0.7 * 3
        assert grid2.CoordIncrements[1] == 0.5 * 2
        assert grid2.CoordIncrements[2] == 0.3 * 2

        # Test with t coordinates.

        data = numpy.arange(3*6*8, dtype='int32').reshape(3,6,8)
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='tyx', coordIncrements=(1.0,0.5,0.3), tIncrementUnit='month', tCornerCoordType='min', cornerCoords=(datetime.datetime(2001,1,1),0.,0.))

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=1)
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 1.0
        assert grid2.CoordIncrements[1] == 0.5
        assert grid2.CoordIncrements[2] == 0.3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=3)
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 1.0
        assert grid2.CoordIncrements[1] == 0.5 * 3
        assert grid2.CoordIncrements[2] == 0.3 * 3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=3, tUnit='month')
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 1.0 * 3
        assert grid2.CoordIncrements[1] == 0.5
        assert grid2.CoordIncrements[2] == 0.3

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2, tSize=3, tUnit='month')
        assert len(grid2.CoordIncrements) == 3
        assert grid2.CoordIncrements[0] == 1.0 * 3
        assert grid2.CoordIncrements[1] == 0.5 * 2
        assert grid2.CoordIncrements[2] == 0.3 * 2


    def test_Shape_CornerCoords(self):

        # Allocate a small NumpyGrid with some test data and test that
        # MinCoords, CenterCords, and MaxCoords come out correctly.

        data = numpy.arange(6*8, dtype='int32').reshape(6,8)
        yCI, xCI = 0.5, 0.3
        yCC, xCC = 100., 0.
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(yCI,xCI), cornerCoords=(yCC,xCC))

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=1)
        self._CheckShapeAndXYZCoords(grid2, [6,8], xCI, xCC, yCI, yCC, 1)

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2)
        self._CheckShapeAndXYZCoords(grid2, [3,4], xCI, xCC, yCI, yCC, 2)

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=3)
        self._CheckShapeAndXYZCoords(grid2, [2,3], xCI, xCC, yCI, yCC, 3)

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=6)
        self._CheckShapeAndXYZCoords(grid2, [1,2], xCI, xCC, yCI, yCC, 6)

        # Scenarios involving a z coordinate.

        data = numpy.arange(3*6*8, dtype='int32').reshape(3,6,8)
        zCI, yCI, xCI = 2., 0.5, 0.3
        zCC, yCC, xCC = 0., 100., 10.
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='zyx', coordIncrements=(zCI,yCI,xCI), cornerCoords=(zCC,yCC,xCC))

        for xySize, zSize in [[1, None], [None, 1], [1, 1]]:
            grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=xySize, zSize=zSize)

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2)
        self._CheckShapeAndXYZCoords(grid2, [3,3,4], xCI, xCC, yCI, yCC, 2, zCI, zCC, None)

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', zSize=2)
        self._CheckShapeAndXYZCoords(grid2, [2,6,8], xCI, xCC, yCI, yCC, 1, zCI, zCC, 2)

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2, zSize=3)
        self._CheckShapeAndXYZCoords(grid2, [1,3,4], xCI, xCC, yCI, yCC, 2, zCI, zCC, 3)


    @pytest.mark.parametrize('tCornerCoord, tCoordIncr, tIncrUnit, tShape, tBlockSize, tExpectedShape, tBlockStart', [
        # ValueError is raised if the grid to be summarized has TIncrementUnit of 'year'
        (datetime.datetime(2000,1,1), 1, 'year', 3, 1, 1, None),

        # ValueError is raised if tStart is later than the grid's start
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 24, datetime.datetime(2000,2,1)),

        # ValueError is raised if tStart is invalid for tUnit == 'month'
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 24, datetime.datetime(1999,1,2)),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 24, datetime.datetime(1999,1,1,1)),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 24, datetime.datetime(1999,1,1,0,1)),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 24, datetime.datetime(1999,1,1,0,0,1)),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 24, datetime.datetime(1999,1,1,0,0,0,1)),

        # We get the correct number of blocks when starting or ending at the beginning or end of the month
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 24, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+364, 1, 24, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+366, 1, 25, None),
        (datetime.datetime(2000,1,31), 1, 'day', 336+364, 1, 24, None),
        (datetime.datetime(2000,1,31), 1, 'day', 336+366, 1, 25, None),

        # Blocks start in later months even when tStart is None
        (datetime.datetime(2000,2,1), 1, 'day', 335+364, 1, 23, None),
        (datetime.datetime(2000,2,1), 1, 'day', 335+366, 1, 24, None),
        (datetime.datetime(2000,3,1), 1, 'day', 306+364, 1, 22, None),
        (datetime.datetime(2000,3,1), 1, 'day', 306+366, 1, 23, None),
        (datetime.datetime(2000,3,2), 1, 'day', 305+364, 1, 22, None),
        (datetime.datetime(2000,3,2), 1, 'day', 305+366, 1, 23, None),

        # Multi-month blocks start and end at the correct month
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 2, 12, None),
        (datetime.datetime(2000,2,1), 1, 'day', 335+365, 2, 12, None),
        (datetime.datetime(2000,3,1), 1, 'day', 306+365, 2, 11, None),
        (datetime.datetime(2000,2,1), 1, 'day', 335+365, 2, 12, datetime.datetime(2000,2,1)),
        (datetime.datetime(2000,3,1), 1, 'day', 306+365, 2, 12, datetime.datetime(2000,2,1)),

        # Blocks with long t increments work
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 3, 8, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 4, 6, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 5, 5, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 6, 4, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 7, 4, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 8, 3, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 9, 3, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 10, 3, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 11, 3, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 12, 2, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 13, 2, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 23, 2, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 24, 1, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 100, 1, None),

        # Hours work
        (datetime.datetime(2000,1,1), 24, 'hour', 366+365,   1, 24, None),
        (datetime.datetime(2000,1,1), 24, 'hour', 366+365+1, 1, 25, None),
        (datetime.datetime(2000,1,1), 24, 'hour', 366+365-1, 1, 24, None),
        (datetime.datetime(2000,1,1), 24, 'hour', 366+365-31,1, 23, None),

        (datetime.datetime(2000,1,1), 6, 'hour', 4*(366+365),      1, 24, None),
        (datetime.datetime(2000,1,1), 6, 'hour', 4*(366+365)+1,    1, 25, None),
        (datetime.datetime(2000,1,1), 6, 'hour', 4*(366+365)-1,    1, 24, None),
        (datetime.datetime(2000,1,1), 6, 'hour', 4*(366+365-31),   1, 23, None),
        (datetime.datetime(2000,1,1), 6, 'hour', 4*(366+365-31)+1, 1, 24, None),

        (datetime.datetime(2000,1,1), 1, 'hour', 24*(366+365),      1, 24, None),
        (datetime.datetime(2000,1,1), 1, 'hour', 24*(366+365)+1,    1, 25, None),
        (datetime.datetime(2000,1,1), 1, 'hour', 24*(366+365)-1,    1, 24, None),
        (datetime.datetime(2000,1,1), 1, 'hour', 24*(366+365-31),   1, 23, None),
        (datetime.datetime(2000,1,1), 1, 'hour', 24*(366+365-31)+1, 1, 24, None),

        # Minutes work
        (datetime.datetime(2000,1,1), 24*60, 'minute', 366+365,   1, 24, None),
        (datetime.datetime(2000,1,1), 24*60, 'minute', 366+365+1, 1, 25, None),
        (datetime.datetime(2000,1,1), 24*60, 'minute', 366+365-1, 1, 24, None),
        (datetime.datetime(2000,1,1), 24*60, 'minute', 366+365-31,1, 23, None),

        (datetime.datetime(2000,1,1), 6*60, 'minute', 4*(366+365),      1, 24, None),
        (datetime.datetime(2000,1,1), 6*60, 'minute', 4*(366+365)+1,    1, 25, None),
        (datetime.datetime(2000,1,1), 6*60, 'minute', 4*(366+365)-1,    1, 24, None),
        (datetime.datetime(2000,1,1), 6*60, 'minute', 4*(366+365-31),   1, 23, None),
        (datetime.datetime(2000,1,1), 6*60, 'minute', 4*(366+365-31)+1, 1, 24, None),

        # Seconds work
        (datetime.datetime(2000,1,1), 24*60*60, 'second', 366+365,   1, 24, None),
        (datetime.datetime(2000,1,1), 24*60*60, 'second', 366+365+1, 1, 25, None),
        (datetime.datetime(2000,1,1), 24*60*60, 'second', 366+365-1, 1, 24, None),
        (datetime.datetime(2000,1,1), 24*60*60, 'second', 366+365-31,1, 23, None),

        (datetime.datetime(2000,1,1), 6*60*60, 'second', 4*(366+365),      1, 24, None),
        (datetime.datetime(2000,1,1), 6*60*60, 'second', 4*(366+365)+1,    1, 25, None),
        (datetime.datetime(2000,1,1), 6*60*60, 'second', 4*(366+365)-1,    1, 24, None),
        (datetime.datetime(2000,1,1), 6*60*60, 'second', 4*(366+365-31),   1, 23, None),
        (datetime.datetime(2000,1,1), 6*60*60, 'second', 4*(366+365-31)+1, 1, 24, None),
    ])
    def test_Shape_CornerCoords_t_month(self, tCornerCoord, tCoordIncr, tIncrUnit, tShape, tBlockSize, tExpectedShape, tBlockStart):

        # Allocate a small NumpyGrid with some test data and test that
        # MinCoords, CenterCords, and MaxCoords come out correctly.

        data = numpy.arange(tShape*6*8, dtype='int32').reshape(tShape,6,8)
        yCI, xCI = 0.5, 0.3
        yCC, xCC = 100., 10.
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='tyx', coordIncrements=(tCoordIncr,yCI,xCI), cornerCoords=(tCornerCoord,yCC,xCC), tIncrementUnit=tIncrUnit, tCornerCoordType='min')

        if tIncrUnit == 'year':
            with pytest.raises(ValueError, match='.*tUnit must be year when TIncrementUnit is year.*'):
                grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='month', tStart=tBlockStart)
            return

        if tBlockStart is not None and (tBlockStart.day != 1 or tBlockStart.hour != 0 or tBlockStart.minute != 0 or tBlockStart.second != 0 or tBlockStart.microsecond != 0):
            with pytest.raises(ValueError, match='.*tStart must start on midnight of the first day a month.*'):
                grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='month', tStart=tBlockStart)
            return

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='month', tStart=tBlockStart)

        if tBlockStart is not None and tBlockStart > tCornerCoord:
            with pytest.raises(ValueError, match='.*that start time occurs after the grid starts.*'):
                grid2.Shape
            return

        self._CheckShapeAndXYZCoords(grid2, [tExpectedShape,6,8], xCI, xCC, yCI, yCC, 1)
        self._CheckTCoords(grid, grid2, tBlockStart, tBlockSize, tExpectedShape)

        # Repeat the test with z coordinates.

        data = numpy.arange(tShape*3*6*8, dtype='int32').reshape(tShape,3,6,8)
        zCI = 2.0
        zCC = 0.
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='tzyx', coordIncrements=(tCoordIncr,zCI,yCI,xCI), cornerCoords=(tCornerCoord,zCC,yCC,xCC), tIncrementUnit=tIncrUnit, tCornerCoordType='min')
        grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='month', tStart=tBlockStart)
        self._CheckTCoords(grid, grid2, tBlockStart, tBlockSize, tExpectedShape)
        self._CheckShapeAndXYZCoords(grid2, [tExpectedShape,3,6,8], xCI, xCC, yCI, yCC, 1, zCI, zCC, 1)

        # Repeat the test but also summarizing blocks in the x, y, and z directions.

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', xySize=2, zSize=3, tSize=tBlockSize, tUnit='month', tStart=tBlockStart)
        self._CheckTCoords(grid, grid2, tBlockStart, tBlockSize, tExpectedShape)
        self._CheckShapeAndXYZCoords(grid2, [tExpectedShape,1,3,4], xCI, xCC, yCI, yCC, 2, zCI, zCC, 3)


    @pytest.mark.parametrize('tCornerCoord, tCoordIncr, tIncrUnit, tShape, tBlockSize, tExpectedShape, tSemiRegularity, expectedTCountPerSemiRegularPeriod, tBlockStart', [
        # ValueError is raised if the grid to be summarized has TIncrementUnit of 'year' or 'month'
        (datetime.datetime(2000,1,1), 1, 'year', 1, 1, 1, None, None, None),
        (datetime.datetime(2000,1,1), 1, 'month', 1, 1, 1, None, None, None),

        # ValueError is raised if tStart is later than the grid's start
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1, 1, None, None, datetime.datetime(2000,1,2)),

        # ValueError is raised if tBlockSize > 365
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 366,  2,       None, None, None),

        # We get the correct number of blocks when not using semiregularity
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1,    366+365, None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 2,    366,     None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 3,    244,     None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 4,    183,     None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 5,    147,     None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 6,    122,     None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 7,    105,     None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 8,    92,      None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 9,    82,      None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 10,   74,      None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 15,   49,      None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 30,   25,      None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 60,   13,      None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 90,   9,       None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 182,  5,       None, None, None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 365,  3,       None, None, None),

        # We get the correct number of blocks when we are using semiregularity
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 1,    366+365, 'annual', None, None),      # No blocks overlap Dec-Jan transition, so BlockStatisticGrid does not have semiregularity
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 2,    183*2,   'annual', 183,  None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 3,    122*2,   'annual', 122,  None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 4,    91*2,    'annual', 91,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 5,    73*2,    'annual', 73,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 6,    61*2,    'annual', 61,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 7,    52*2,    'annual', 52,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 8,    46*2,    'annual', 46,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 9,    41*2,    'annual', 41,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 10,   37*2,    'annual', 37,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 15,   24*2,    'annual', 24,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 30,   12*2,    'annual', 12,   None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 60,   6*2,     'annual', 6,    None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 90,   4*2,     'annual', 4,    None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 182,  2*2,     'annual', 2,    None),
        (datetime.datetime(2000,1,1), 1, 'day', 366+365, 365,  1*2,     'annual', 1,    None),
    ])
    def test_Shape_CornerCoords_t_day(self, tCornerCoord, tCoordIncr, tIncrUnit, tShape, tBlockSize, tExpectedShape, tSemiRegularity, expectedTCountPerSemiRegularPeriod, tBlockStart):

        # Allocate a small NumpyGrid with some test data and test that
        # MinCoords, CenterCords, and MaxCoords come out correctly.

        data = numpy.arange(tShape*6*8, dtype='int32').reshape(tShape,6,8)
        yCI, xCI = 0.5, 0.3
        yCC, xCC = 100., 10.
        grid = NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='tyx', coordIncrements=(tCoordIncr,yCI,xCI), cornerCoords=(tCornerCoord,yCC,xCC), tIncrementUnit=tIncrUnit, tCornerCoordType='min')

        if tIncrUnit == 'year':
            with pytest.raises(ValueError, match='.*tUnit must be year when TIncrementUnit is year.*'):
                grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='day', tStart=tBlockStart, tSemiRegularity=tSemiRegularity)
            return

        if tIncrUnit == 'month':
            with pytest.raises(ValueError, match='.*tUnit must be the same as TIncrementUnit or a coarser unit.*'):
                grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='day', tStart=tBlockStart, tSemiRegularity=tSemiRegularity)
            return

        if tBlockSize > 365:
            with pytest.raises(ValueError, match='.*This exceeds 365 days.*'):
                grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='day', tStart=tBlockStart, tSemiRegularity=tSemiRegularity)
            return

        grid2 = BlockStatisticGrid(grid=grid, statistic='count', tSize=tBlockSize, tUnit='day', tStart=tBlockStart, tSemiRegularity=tSemiRegularity)

        if tBlockStart is not None and tBlockStart > tCornerCoord:
            with pytest.raises(ValueError, match='.*that start time occurs after the grid starts.*'):
                grid2.Shape
            return

        self._CheckShapeAndXYZCoords(grid2, [tExpectedShape,6,8], xCI, xCC, yCI, yCC, 1)
        self._CheckTCoords(grid, grid2, tBlockStart, tBlockSize, tExpectedShape, tSemiRegularity, expectedTCountPerSemiRegularPeriod)


    def test_Statistics_xy(self):

        # Define a grid shape and which cells of it will have NoData. Make the
        # total count of cells is less than 127, so that numpy.arange will
        # yield values all representable by int8.

        shape = (10,12)
        rng = numpy.random.default_rng(424242)
        noDataCells = rng.choice(math.prod(shape), size=math.prod(shape) // 5, replace=False)   # 20% of cells will have NoData

        # Test all of the supported dtypes.

        for dtype in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:

            # Generate a 2D array of test data. If the dtype supports negative
            # numbers, make the odd numbers negative.

            data = numpy.arange(math.prod(shape), dtype=dtype).reshape(shape)

            if not dtype.startswith('u'):
                data[(data % 2).astype(bool)] *= -1

            # Create a second array that sets the random cells above to
            # NoData. Use 0 as the NoData value.

            noDataValue = 0
            data2 = data.copy()
            r, c = numpy.unravel_index(noDataCells, shape)
            data2[r,c] = noDataValue

            # Also set an entire 5x5 block and 2x5 edge block to NoData to
            # ensure stats work in those situations.

            data2[0:5,5:10] = noDataValue
            data2[5:10,10:12] = noDataValue

            # Test a grid without any NoData values and one with them.

            grids = [NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(1.,1.), cornerCoords=(0.,0.)),
                     NumpyGrid(numpyArray=data2, displayName='test data', spatialReference=None, dimensions='yx', coordIncrements=(1.,1.), cornerCoords=(0.,0.), unscaledNoDataValue=noDataValue)]

            for grid in grids:

                # Count

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[25, 25, 10], 
                                                  [25, 25, 10]])
                else:
                    expectedValues = numpy.array([[(grid.Data[0:5,0:5] != grid.NoDataValue).sum(), (grid.Data[0:5,5:10] != grid.NoDataValue).sum(), (grid.Data[0:5,10:12] != grid.NoDataValue).sum()], 
                                                  [(grid.Data[5:10,0:5] != grid.NoDataValue).sum(), (grid.Data[5:10,5:10] != grid.NoDataValue).sum(), (grid.Data[5:10,10:12] != grid.NoDataValue).sum()]])

                bg = BlockStatisticGrid(grid=grid, statistic='count', xySize=5)
                result = bg.Data[:]
                assert result.dtype == numpy.dtype('int32')
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Minimum

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[grid.Data[0:5,0:5].min(), grid.Data[0:5,5:10].min(), grid.Data[0:5,10:12].min()], 
                                                  [grid.Data[5:10,0:5].min(), grid.Data[5:10,5:10].min(), grid.Data[5:10,10:12].min()]])
                else:
                    extremum = numpy.finfo(grid.DataType).max if grid.DataType[0] == 'f' else numpy.iinfo(grid.DataType).max
                    data3 = numpy.where(data2 == noDataValue, extremum, data2)

                    expectedValues = [[numpy.where((data3[0:5,0:5] == extremum).all(), noDataValue, data3[0:5,0:5].min()),
                                       numpy.where((data3[0:5,5:10] == extremum).all(), noDataValue, data3[0:5,5:10].min()),
                                       numpy.where((data3[0:5,10:12] == extremum).all(), noDataValue, data3[0:5,10:12].min())],

                                      [numpy.where((data3[5:10,0:5] == extremum).all(), noDataValue, data3[5:10,0:5].min()),
                                       numpy.where((data3[5:10,5:10] == extremum).all(), noDataValue, data3[5:10,5:10].min()),
                                       numpy.where((data3[5:10,10:12] == extremum).all(), noDataValue, data3[5:10,10:12].min())]]

                    expectedValues = numpy.array(expectedValues, dtype=grid.DataType)

                bg = BlockStatisticGrid(grid=grid, statistic='minimum', xySize=5)
                result = bg.Data[:]
                assert result.dtype == expectedValues.dtype
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Maximum

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[grid.Data[0:5,0:5].max(), grid.Data[0:5,5:10].max(), grid.Data[0:5,10:12].max()], 
                                                  [grid.Data[5:10,0:5].max(), grid.Data[5:10,5:10].max(), grid.Data[5:10,10:12].max()]])
                else:
                    extremum = numpy.finfo(grid.DataType).min if grid.DataType[0] == 'f' else numpy.iinfo(grid.DataType).min
                    data3 = numpy.where(data2 == noDataValue, extremum, data2)

                    expectedValues = [[numpy.where((data3[0:5,0:5] == extremum).all(), noDataValue, data3[0:5,0:5].max()),
                                       numpy.where((data3[0:5,5:10] == extremum).all(), noDataValue, data3[0:5,5:10].max()),
                                       numpy.where((data3[0:5,10:12] == extremum).all(), noDataValue, data3[0:5,10:12].max())],

                                      [numpy.where((data3[5:10,0:5] == extremum).all(), noDataValue, data3[5:10,0:5].max()),
                                       numpy.where((data3[5:10,5:10] == extremum).all(), noDataValue, data3[5:10,5:10].max()),
                                       numpy.where((data3[5:10,10:12] == extremum).all(), noDataValue, data3[5:10,10:12].max())]]

                    expectedValues = numpy.array(expectedValues, dtype=grid.DataType)

                bg = BlockStatisticGrid(grid=grid, statistic='maximum', xySize=5)
                result = bg.Data[:]
                assert result.dtype == expectedValues.dtype
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Range

                bg = BlockStatisticGrid(grid=grid, statistic='range', xySize=5)

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[numpy.ptp(grid.Data[0:5,0:5]), numpy.ptp(grid.Data[0:5,5:10]), numpy.ptp(grid.Data[0:5,10:12])], 
                                                  [numpy.ptp(grid.Data[5:10,0:5]), numpy.ptp(grid.Data[5:10,5:10]), numpy.ptp(grid.Data[5:10,10:12])]])
                    if grid.DataType.startswith('i'):
                        expectedValues = expectedValues.view('u' + grid.DataType)    # Treat the signed ints as unsigned, reversing two's complement; see numpy docs on numpy.ptp()
                else:
                    data3 = data2.astype('float64')
                    data3 = numpy.where(data2 == noDataValue, numpy.nan, data3)

                    expectedValues = numpy.array([[self._nanptp(data3[0:5,0:5]), self._nanptp(data3[0:5,5:10]), self._nanptp(data3[0:5,10:12])],
                                                  [self._nanptp(data3[5:10,0:5]), self._nanptp(data3[5:10,5:10]), self._nanptp(data3[5:10,10:12])]])

                    expectedValues[numpy.isnan(expectedValues)] = bg.NoDataValue

                    if grid.DataType.startswith('i'):
                        expectedValues = expectedValues.astype('u' + grid.DataType)
                    else:
                        expectedValues = expectedValues.astype(grid.DataType)

                result = bg.Data[:]
                assert result.dtype == expectedValues.dtype
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Mean, median, standard_deviation, sum

                for statistic, func in [['mean', numpy.nanmean],
                                        ['median', numpy.nanmedian],
                                        ['standard_deviation', functools.partial(numpy.nanstd, ddof=1)],
                                        ['sum', numpy.nansum]]:

                    bg = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=5)

                    expectedDataType = 'float64' if dtype != 'float32' else 'float32'
                    assert bg.DataType == expectedDataType

                    if grid.NoDataValue is None:
                        expectedValues = numpy.array([[func(grid.Data[0:5,0:5]), func(grid.Data[0:5,5:10]), func(grid.Data[0:5,10:12])], 
                                                      [func(grid.Data[5:10,0:5]), func(grid.Data[5:10,5:10]), func(grid.Data[5:10,10:12])]],
                                                     dtype=expectedDataType)
                    else:
                        data3 = data2.astype(expectedDataType)
                        data3 = numpy.where(data2 == noDataValue, numpy.nan, data3)

                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", category=RuntimeWarning)
                            expectedValues = numpy.array([[func(data3[0:5,0:5]), func(data3[0:5,5:10]), func(data3[0:5,10:12])],
                                                          [func(data3[5:10,0:5]), func(data3[5:10,5:10]), func(data3[5:10,10:12])]],
                                                         dtype=expectedDataType)

                        expectedValues[numpy.isnan(expectedValues)] = bg.NoDataValue

                    result = bg.Data[:]

                    assert result.dtype == expectedValues.dtype
                    assert result.shape == expectedValues.shape

                    # For reasons I could not figure out, occasionally
                    # numpy.nanstd returns slightly different values. So for
                    # 'standard_deviation', we relax our equality requirement
                    # slightly.

                    if statistic == 'standard_deviation':
                        if bg.DataType == 'float32':
                            assert numpy.allclose(result, expectedValues, rtol=1e-7, atol=1e-7)
                        else:   # float64
                            assert numpy.allclose(result, expectedValues, rtol=1e-15, atol=1e-15)
                    else:
                        assert (result == expectedValues).all()


    def test_Statistics_xyz(self):

        # Test all of the supported dtypes.

        for dtype in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:

            # Define a 3D grid shape and which cells of it will have NoData. 

            shape = (3,10,12)
            rng = numpy.random.default_rng(424242)
            noDataCells = rng.choice(math.prod(shape), size=math.prod(shape) // 5, replace=False)   # 20% of cells will have NoData

            # Generate a 3D array of test data. Make sure all values are less
            # than 128, so they can be represented with int8. If the dtype
            # supports negative numbers, make the odd numbers negative.

            data2D = numpy.arange(math.prod(shape[1:]), dtype=dtype).reshape(shape[1:])
            data = numpy.stack([data2D, data2D+1, data2D+2], axis=0)

            if not dtype.startswith('u'):
                data[(data % 2).astype(bool)] *= -1

            # Create a second array that sets the random cells above to
            # NoData. Use 0 as the NoData value.

            noDataValue = 0
            data2 = data.copy()
            z, y, x = numpy.unravel_index(noDataCells, shape)
            data2[z, y, x] = noDataValue

            # Also set entire 2x5x5 block, 2x5x2, 1x5x5, and 1x5x2 edge blocks
            # to NoData to ensure stats work in those situations.

            data2[0:2,0:5,0:5] = noDataValue
            data2[0:2,0:5,10:12] = noDataValue
            data2[2,5:10,0:5] = noDataValue
            data2[2,5:10,10:12] = noDataValue

            # Test a grid without any NoData values and one with them.

            grids = [NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='zyx', coordIncrements=(1.,1.,1.), cornerCoords=(0.,0.,0.)),
                     NumpyGrid(numpyArray=data2, displayName='test data', spatialReference=None, dimensions='zyx', coordIncrements=(1.,1.,1.), cornerCoords=(0.,0.,0.), unscaledNoDataValue=noDataValue)]

            for grid in grids:

                # Count

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[[50, 50, 20], 
                                                   [50, 50, 20]],
                                                  [[25, 25, 10], 
                                                   [25, 25, 10]]])
                else:
                    expectedValues = numpy.array([[[(grid.Data[0:2,0:5,0:5] != grid.NoDataValue).sum(), (grid.Data[0:2,0:5,5:10] != grid.NoDataValue).sum(), (grid.Data[0:2,0:5,10:12] != grid.NoDataValue).sum()], 
                                                   [(grid.Data[0:2,5:10,0:5] != grid.NoDataValue).sum(), (grid.Data[0:2,5:10,5:10] != grid.NoDataValue).sum(), (grid.Data[0:2,5:10,10:12] != grid.NoDataValue).sum()]],
                                                  [[(grid.Data[2:3,0:5,0:5] != grid.NoDataValue).sum(), (grid.Data[2:3,0:5,5:10] != grid.NoDataValue).sum(), (grid.Data[2:3,0:5,10:12] != grid.NoDataValue).sum()], 
                                                   [(grid.Data[2:3,5:10,0:5] != grid.NoDataValue).sum(), (grid.Data[2:3,5:10,5:10] != grid.NoDataValue).sum(), (grid.Data[2:3,5:10,10:12] != grid.NoDataValue).sum()]]])

                bg = BlockStatisticGrid(grid=grid, statistic='count', xySize=5, zSize=2)
                result = bg.Data[:]
                assert result.dtype == numpy.dtype('int32')
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Minimum

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[[grid.Data[0:2,0:5,0:5].min(), grid.Data[0:2,0:5,5:10].min(), grid.Data[0:2,0:5,10:12].min()], 
                                                   [grid.Data[0:2,5:10,0:5].min(), grid.Data[0:2,5:10,5:10].min(), grid.Data[0:2,5:10,10:12].min()]],
                                                  [[grid.Data[2:3,0:5,0:5].min(), grid.Data[2:3,0:5,5:10].min(), grid.Data[2:3,0:5,10:12].min()], 
                                                   [grid.Data[2:3,5:10,0:5].min(), grid.Data[2:3,5:10,5:10].min(), grid.Data[2:3,5:10,10:12].min()]]])
                else:
                    extremum = numpy.finfo(grid.DataType).max if grid.DataType[0] == 'f' else numpy.iinfo(grid.DataType).max
                    data3 = numpy.where(data2 == noDataValue, extremum, data2)

                    expectedValues = [[[numpy.where((data3[0:2,0:5,0:5] == extremum).all(), noDataValue, data3[0:2,0:5,0:5].min()),
                                        numpy.where((data3[0:2,0:5,5:10] == extremum).all(), noDataValue, data3[0:2,0:5,5:10].min()),
                                        numpy.where((data3[0:2,0:5,10:12] == extremum).all(), noDataValue, data3[0:2,0:5,10:12].min())],

                                       [numpy.where((data3[0:2,5:10,0:5] == extremum).all(), noDataValue, data3[0:2,5:10,0:5].min()),
                                        numpy.where((data3[0:2,5:10,5:10] == extremum).all(), noDataValue, data3[0:2,5:10,5:10].min()),
                                        numpy.where((data3[0:2,5:10,10:12] == extremum).all(), noDataValue, data3[0:2,5:10,10:12].min())]],

                                      [[numpy.where((data3[2:3,0:5,0:5] == extremum).all(), noDataValue, data3[2:3,0:5,0:5].min()),
                                        numpy.where((data3[2:3,0:5,5:10] == extremum).all(), noDataValue, data3[2:3,0:5,5:10].min()),
                                        numpy.where((data3[2:3,0:5,10:12] == extremum).all(), noDataValue, data3[2:3,0:5,10:12].min())],

                                       [numpy.where((data3[2:3,5:10,0:5] == extremum).all(), noDataValue, data3[2:3,5:10,0:5].min()),
                                        numpy.where((data3[2:3,5:10,5:10] == extremum).all(), noDataValue, data3[2:3,5:10,5:10].min()),
                                        numpy.where((data3[2:3,5:10,10:12] == extremum).all(), noDataValue, data3[2:3,5:10,10:12].min())]]]

                    expectedValues = numpy.array(expectedValues, dtype=grid.DataType)

                bg = BlockStatisticGrid(grid=grid, statistic='minimum', xySize=5, zSize=2)
                result = bg.Data[:]
                assert result.dtype == expectedValues.dtype
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Maximum

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[[grid.Data[0:2,0:5,0:5].max(), grid.Data[0:2,0:5,5:10].max(), grid.Data[0:2,0:5,10:12].max()], 
                                                   [grid.Data[0:2,5:10,0:5].max(), grid.Data[0:2,5:10,5:10].max(), grid.Data[0:2,5:10,10:12].max()]],
                                                  [[grid.Data[2:3,0:5,0:5].max(), grid.Data[2:3,0:5,5:10].max(), grid.Data[2:3,0:5,10:12].max()], 
                                                   [grid.Data[2:3,5:10,0:5].max(), grid.Data[2:3,5:10,5:10].max(), grid.Data[2:3,5:10,10:12].max()]]])
                else:
                    extremum = numpy.finfo(grid.DataType).min if grid.DataType[0] == 'f' else numpy.iinfo(grid.DataType).min
                    data3 = numpy.where(data2 == noDataValue, extremum, data2)

                    expectedValues = [[[numpy.where((data3[0:2,0:5,0:5] == extremum).all(), noDataValue, data3[0:2,0:5,0:5].max()),
                                        numpy.where((data3[0:2,0:5,5:10] == extremum).all(), noDataValue, data3[0:2,0:5,5:10].max()),
                                        numpy.where((data3[0:2,0:5,10:12] == extremum).all(), noDataValue, data3[0:2,0:5,10:12].max())],

                                       [numpy.where((data3[0:2,5:10,0:5] == extremum).all(), noDataValue, data3[0:2,5:10,0:5].max()),
                                        numpy.where((data3[0:2,5:10,5:10] == extremum).all(), noDataValue, data3[0:2,5:10,5:10].max()),
                                        numpy.where((data3[0:2,5:10,10:12] == extremum).all(), noDataValue, data3[0:2,5:10,10:12].max())]],

                                      [[numpy.where((data3[2:3,0:5,0:5] == extremum).all(), noDataValue, data3[2:3,0:5,0:5].max()),
                                        numpy.where((data3[2:3,0:5,5:10] == extremum).all(), noDataValue, data3[2:3,0:5,5:10].max()),
                                        numpy.where((data3[2:3,0:5,10:12] == extremum).all(), noDataValue, data3[2:3,0:5,10:12].max())],

                                       [numpy.where((data3[2:3,5:10,0:5] == extremum).all(), noDataValue, data3[2:3,5:10,0:5].max()),
                                        numpy.where((data3[2:3,5:10,5:10] == extremum).all(), noDataValue, data3[2:3,5:10,5:10].max()),
                                        numpy.where((data3[2:3,5:10,10:12] == extremum).all(), noDataValue, data3[2:3,5:10,10:12].max())]]]

                    expectedValues = numpy.array(expectedValues, dtype=grid.DataType)

                bg = BlockStatisticGrid(grid=grid, statistic='maximum', xySize=5, zSize=2)
                result = bg.Data[:]
                assert result.dtype == expectedValues.dtype
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Range

                bg = BlockStatisticGrid(grid=grid, statistic='range', xySize=5, zSize=2)

                if grid.NoDataValue is None:
                    expectedValues = numpy.array([[[numpy.ptp(grid.Data[0:2,0:5,0:5]), numpy.ptp(grid.Data[0:2,0:5,5:10]), numpy.ptp(grid.Data[0:2,0:5,10:12])], 
                                                   [numpy.ptp(grid.Data[0:2,5:10,0:5]), numpy.ptp(grid.Data[0:2,5:10,5:10]), numpy.ptp(grid.Data[0:2,5:10,10:12])]],
                                                  [[numpy.ptp(grid.Data[2:3,0:5,0:5]), numpy.ptp(grid.Data[2:3,0:5,5:10]), numpy.ptp(grid.Data[2:3,0:5,10:12])], 
                                                   [numpy.ptp(grid.Data[2:3,5:10,0:5]), numpy.ptp(grid.Data[2:3,5:10,5:10]), numpy.ptp(grid.Data[2:3,5:10,10:12])]]])

                    if grid.DataType.startswith('i'):
                        expectedValues = expectedValues.view('u' + grid.DataType)    # Treat the signed ints as unsigned, reversing two's complement; see numpy docs on numpy.ptp()
                else:
                    data3 = data2.astype('float64')
                    data3 = numpy.where(data2 == noDataValue, numpy.nan, data3)

                    expectedValues = numpy.array([[[self._nanptp(data3[0:2,0:5,0:5]), self._nanptp(data3[0:2,0:5,5:10]), self._nanptp(data3[0:2,0:5,10:12])],
                                                   [self._nanptp(data3[0:2,5:10,0:5]), self._nanptp(data3[0:2,5:10,5:10]), self._nanptp(data3[0:2,5:10,10:12])]],
                                                  [[self._nanptp(data3[2:3,0:5,0:5]), self._nanptp(data3[2:3,0:5,5:10]), self._nanptp(data3[2:3,0:5,10:12])],
                                                   [self._nanptp(data3[2:3,5:10,0:5]), self._nanptp(data3[2:3,5:10,5:10]), self._nanptp(data3[2:3,5:10,10:12])]]])

                    expectedValues[numpy.isnan(expectedValues)] = bg.NoDataValue

                    if grid.DataType.startswith('i'):
                        expectedValues = expectedValues.astype('u' + grid.DataType)
                    else:
                        expectedValues = expectedValues.astype(grid.DataType)

                result = bg.Data[:]
                assert result.dtype == expectedValues.dtype
                assert result.shape == expectedValues.shape
                assert (result == expectedValues).all()

                # Mean, median, standard_deviation, sum

                for statistic, func in [['mean', numpy.nanmean],
                                        ['median', numpy.nanmedian],
                                        ['standard_deviation', functools.partial(numpy.nanstd, ddof=1)],
                                        ['sum', numpy.nansum]]:

                    bg = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=5, zSize=2)

                    expectedDataType = 'float64' if dtype != 'float32' else 'float32'
                    assert bg.DataType == expectedDataType

                    if grid.NoDataValue is None:
                        expectedValues = numpy.array([[[func(grid.Data[0:2,0:5,0:5]), func(grid.Data[0:2,0:5,5:10]), func(grid.Data[0:2,0:5,10:12])], 
                                                       [func(grid.Data[0:2,5:10,0:5]), func(grid.Data[0:2,5:10,5:10]), func(grid.Data[0:2,5:10,10:12])]],
                                                      [[func(grid.Data[2:3,0:5,0:5]), func(grid.Data[2:3,0:5,5:10]), func(grid.Data[2:3,0:5,10:12])], 
                                                       [func(grid.Data[2:3,5:10,0:5]), func(grid.Data[2:3,5:10,5:10]), func(grid.Data[2:3,5:10,10:12])]]],
                                                     dtype=expectedDataType)
                    else:
                        data3 = data2.astype(expectedDataType)
                        data3 = numpy.where(data2 == noDataValue, numpy.nan, data3)

                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", category=RuntimeWarning)
                            expectedValues = numpy.array([[[func(data3[0:2,0:5,0:5]), func(data3[0:2,0:5,5:10]), func(data3[0:2,0:5,10:12])],
                                                           [func(data3[0:2,5:10,0:5]), func(data3[0:2,5:10,5:10]), func(data3[0:2,5:10,10:12])]],
                                                          [[func(data3[2:3,0:5,0:5]), func(data3[2:3,0:5,5:10]), func(data3[2:3,0:5,10:12])],
                                                           [func(data3[2:3,5:10,0:5]), func(data3[2:3,5:10,5:10]), func(data3[2:3,5:10,10:12])]]],
                                                         dtype=expectedDataType)

                        expectedValues[numpy.isnan(expectedValues)] = bg.NoDataValue

                    result = bg.Data[:]

                    assert result.dtype == expectedValues.dtype
                    assert result.shape == expectedValues.shape

                    # For reasons I could not figure out, occasionally
                    # numpy.nanstd returns slightly different values. So for
                    # 'standard_deviation', we relax our equality requirement
                    # slightly.

                    if statistic == 'standard_deviation':
                        if bg.DataType == 'float32':
                            assert numpy.allclose(result, expectedValues, rtol=1e-7, atol=1e-7)
                        else:   # float64
                            assert numpy.allclose(result, expectedValues, rtol=1e-15, atol=1e-15)
                    else:
                        assert (result == expectedValues).all()


    def test_Statistics_xyt(self):

        # Test all of the supported dtypes.

        tFirst = datetime.datetime(2000, 1, 10)
        tLast = datetime.datetime(2002, 1, 20)

        for dtype in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:

            # Create a 3D tyx grid with daily time slices running from 10
            # January 2000 to 20 January 2002, with random integers between
            # 0-120. If the dtype supports negative numbers, make the odd
            # numbers negative.
            
            rng = numpy.random.default_rng(424242)

            tSlices = []
            month = tFirst.month
            tDaysInMonthlySlice = [0]
            tDaysIn8DaySlice = [0]
            tDaysIn8DaySliceWithSemiRegularity = [0]

            t = tFirst
            while t <= tLast:
                data1D = numpy.arange(120, dtype=dtype)
                numpy.random.shuffle(data1D)
                data2D = data1D.reshape((10,12))
                tSlices.append(data2D)

                if t.month == month:
                    tDaysInMonthlySlice[-1] += 1
                else:
                    tDaysInMonthlySlice.append(1)
                    month = t.month

                if tDaysIn8DaySlice[-1] < 8:
                    tDaysIn8DaySlice[-1] += 1
                else:
                    tDaysIn8DaySlice.append(1)

                doy = int(t.strftime('%j'))
                if (doy - 1) % 8 == 0:
                    tDaysIn8DaySliceWithSemiRegularity.append(1)
                else:
                    tDaysIn8DaySliceWithSemiRegularity[-1] += 1

                t += datetime.timedelta(days=1)

            data = numpy.stack(tSlices, axis=0)
            assert data.shape == (365-9+366+20, 10, 12)

            if not dtype.startswith('u'):
                data[(data % 2).astype(bool)] *= -1

            # Create a second array that sets the random cells above to
            # NoData. Use 0 as the NoData value.

            noDataValue = 0
            noDataCells = rng.choice(math.prod(data.shape), size=math.prod(data.shape) // 5, replace=False)   # 20% of cells will have NoData
            data2 = data.copy()
            z, y, x = numpy.unravel_index(noDataCells, data.shape)
            data2[z, y, x] = noDataValue

            # Test a grid without any NoData values and one with them.

            grids = [NumpyGrid(numpyArray=data, displayName='test data', spatialReference=None, dimensions='tyx', coordIncrements=(1.,1.,1.), cornerCoords=(tFirst,0.,0.), tIncrementUnit='day', tCornerCoordType='min'),
                     NumpyGrid(numpyArray=data2, displayName='test data', spatialReference=None, dimensions='tyx', coordIncrements=(1.,1.,1.), cornerCoords=(tFirst,0.,0.), tIncrementUnit='day', tCornerCoordType='min', unscaledNoDataValue=noDataValue)]

            for grid in grids:

                # Test for different summarization periods.

                for tSize, tUnit, tStart, tDaysInSlice, tSemiRegularity in [[1, 'month', None, tDaysInMonthlySlice, None],
                                                                            [8, 'day', tFirst, tDaysIn8DaySlice, None],
                                                                            [8, 'day', None, tDaysIn8DaySliceWithSemiRegularity, 'annual']]:

                    # Count

                    if grid.NoDataValue is None:
                        evSlices = [numpy.array([[25*days, 25*days, 10*days], 
                                                 [25*days, 25*days, 10*days]]) for days in tDaysInSlice]
                        expectedValues = numpy.stack(evSlices, axis= 0)
                    else:
                        evSlices = []
                        i = 0
                        daysFromStart = 0
                        while i < len(tDaysInSlice):
                            ti1 = daysFromStart
                            ti2 = ti1 + tDaysInSlice[i]
                            evSlices.append(numpy.array([[(grid.Data[ti1:ti2,0:5,0:5] != grid.NoDataValue).sum(), (grid.Data[ti1:ti2,0:5,5:10] != grid.NoDataValue).sum(), (grid.Data[ti1:ti2,0:5,10:12] != grid.NoDataValue).sum()], 
                                                         [(grid.Data[ti1:ti2,5:10,0:5] != grid.NoDataValue).sum(), (grid.Data[ti1:ti2,5:10,5:10] != grid.NoDataValue).sum(), (grid.Data[ti1:ti2,5:10,10:12] != grid.NoDataValue).sum()]]))
                            daysFromStart = ti2
                            i += 1
                        expectedValues = numpy.stack(evSlices, axis=0)

                    bg = BlockStatisticGrid(grid=grid, statistic='count', xySize=5, tSize=tSize, tUnit=tUnit, tStart=tStart, tSemiRegularity=tSemiRegularity)
                    result = bg.Data[:]
                    assert result.dtype == numpy.dtype('int32')
                    assert result.shape == expectedValues.shape
                    assert (result == expectedValues).all()

                    # Minimum

                    if grid.NoDataValue is not None:
                        extremum = numpy.finfo(grid.DataType).max if grid.DataType[0] == 'f' else numpy.iinfo(grid.DataType).max
                        data3 = numpy.where(data2 == noDataValue, extremum, data2)

                    evSlices = []
                    i = 0
                    daysFromStart = 0
                    while i < len(tDaysInSlice):
                        ti1 = daysFromStart
                        ti2 = ti1 + tDaysInSlice[i]
                        if grid.NoDataValue is None:
                            evSlices.append(numpy.array([[grid.Data[ti1:ti2,0:5,0:5].min(), grid.Data[ti1:ti2,0:5,5:10].min(), grid.Data[ti1:ti2,0:5,10:12].min()], 
                                                         [grid.Data[ti1:ti2,5:10,0:5].min(), grid.Data[ti1:ti2,5:10,5:10].min(), grid.Data[ti1:ti2,5:10,10:12].min()]], 
                                                        dtype=grid.DataType))
                        else:
                            evSlices.append(numpy.array([[numpy.where((data3[ti1:ti2,0:5,0:5] == extremum).all(), noDataValue, data3[ti1:ti2,0:5,0:5].min()),
                                                          numpy.where((data3[ti1:ti2,0:5,5:10] == extremum).all(), noDataValue, data3[ti1:ti2,0:5,5:10].min()),
                                                          numpy.where((data3[ti1:ti2,0:5,10:12] == extremum).all(), noDataValue, data3[ti1:ti2,0:5,10:12].min())], 

                                                         [numpy.where((data3[ti1:ti2,5:10,0:5] == extremum).all(), noDataValue, data3[ti1:ti2,5:10,0:5].min()),
                                                          numpy.where((data3[ti1:ti2,5:10,5:10] == extremum).all(), noDataValue, data3[ti1:ti2,5:10,5:10].min()),
                                                          numpy.where((data3[ti1:ti2,5:10,10:12] == extremum).all(), noDataValue, data3[ti1:ti2,5:10,10:12].min())]], 
                                                        dtype=grid.DataType))
                        daysFromStart = ti2
                        i += 1
                    expectedValues = numpy.stack(evSlices, axis=0).astype(data.dtype)

                    bg = BlockStatisticGrid(grid=grid, statistic='minimum', xySize=5, tSize=tSize, tUnit=tUnit, tStart=tStart, tSemiRegularity=tSemiRegularity)
                    result = bg.Data[:]
                    assert result.dtype == expectedValues.dtype
                    assert result.shape == expectedValues.shape
                    assert (result == expectedValues).all()

                    # Maximum

                    if grid.NoDataValue is not None:
                        extremum = numpy.finfo(grid.DataType).min if grid.DataType[0] == 'f' else numpy.iinfo(grid.DataType).min
                        data3 = numpy.where(data2 == noDataValue, extremum, data2)

                    evSlices = []
                    i = 0
                    daysFromStart = 0
                    while i < len(tDaysInSlice):
                        ti1 = daysFromStart
                        ti2 = ti1 + tDaysInSlice[i]
                        if grid.NoDataValue is None:
                            evSlices.append(numpy.array([[grid.Data[ti1:ti2,0:5,0:5].max(), grid.Data[ti1:ti2,0:5,5:10].max(), grid.Data[ti1:ti2,0:5,10:12].max()], 
                                                         [grid.Data[ti1:ti2,5:10,0:5].max(), grid.Data[ti1:ti2,5:10,5:10].max(), grid.Data[ti1:ti2,5:10,10:12].max()]], 
                                                        dtype=grid.DataType))
                        else:
                            evSlices.append(numpy.array([[numpy.where((data3[ti1:ti2,0:5,0:5] == extremum).all(), noDataValue, data3[ti1:ti2,0:5,0:5].max()),
                                                          numpy.where((data3[ti1:ti2,0:5,5:10] == extremum).all(), noDataValue, data3[ti1:ti2,0:5,5:10].max()),
                                                          numpy.where((data3[ti1:ti2,0:5,10:12] == extremum).all(), noDataValue, data3[ti1:ti2,0:5,10:12].max())], 

                                                         [numpy.where((data3[ti1:ti2,5:10,0:5] == extremum).all(), noDataValue, data3[ti1:ti2,5:10,0:5].max()),
                                                          numpy.where((data3[ti1:ti2,5:10,5:10] == extremum).all(), noDataValue, data3[ti1:ti2,5:10,5:10].max()),
                                                          numpy.where((data3[ti1:ti2,5:10,10:12] == extremum).all(), noDataValue, data3[ti1:ti2,5:10,10:12].max())]], 
                                                        dtype=grid.DataType))
                        daysFromStart = ti2
                        i += 1

                    expectedValues = numpy.stack(evSlices, axis=0).astype(data.dtype)

                    bg = BlockStatisticGrid(grid=grid, statistic='maximum', xySize=5, tSize=tSize, tUnit=tUnit, tStart=tStart, tSemiRegularity=tSemiRegularity)
                    result = bg.Data[:]
                    assert result.dtype == expectedValues.dtype
                    assert result.shape == expectedValues.shape
                    assert (result == expectedValues).all()

                    # Range

                    bg = BlockStatisticGrid(grid=grid, statistic='range', xySize=5, tSize=tSize, tUnit=tUnit, tStart=tStart, tSemiRegularity=tSemiRegularity)

                    if grid.NoDataValue is not None:
                        data3 = data2.astype('float64')
                        data3 = numpy.where(data2 == noDataValue, numpy.nan, data3)

                    evSlices = []
                    i = 0
                    daysFromStart = 0
                    while i < len(tDaysInSlice):
                        ti1 = daysFromStart
                        ti2 = ti1 + tDaysInSlice[i]
                        if grid.NoDataValue is None:
                            evSlices.append(numpy.array([[numpy.ptp(grid.Data[ti1:ti2,0:5,0:5]), numpy.ptp(grid.Data[ti1:ti2,0:5,5:10]), numpy.ptp(grid.Data[ti1:ti2,0:5,10:12])], 
                                                         [numpy.ptp(grid.Data[ti1:ti2,5:10,0:5]), numpy.ptp(grid.Data[ti1:ti2,5:10,5:10]), numpy.ptp(grid.Data[ti1:ti2,5:10,10:12])]]))
                        else:
                            evSlices.append(numpy.array([[self._nanptp(data3[ti1:ti2,0:5,0:5]), self._nanptp(data3[ti1:ti2,0:5,5:10]), self._nanptp(data3[ti1:ti2,0:5,10:12])],
                                                         [self._nanptp(data3[ti1:ti2,5:10,0:5]), self._nanptp(data3[ti1:ti2,5:10,5:10]), self._nanptp(data3[ti1:ti2,5:10,10:12])]]))
                        daysFromStart = ti2
                        i += 1

                    expectedValues = numpy.stack(evSlices, axis=0)

                    if grid.NoDataValue is None:
                        if grid.DataType.startswith('i'):
                            expectedValues = expectedValues.view('u' + grid.DataType)    # Treat the signed ints as unsigned, reversing two's complement; see numpy docs on numpy.ptp()
                    else:
                        expectedValues[numpy.isnan(expectedValues)] = bg.NoDataValue

                        if grid.DataType.startswith('i'):
                            expectedValues = expectedValues.astype('u' + grid.DataType)
                        else:
                            expectedValues = expectedValues.astype(grid.DataType)

                    result = bg.Data[:]
                    assert result.dtype == expectedValues.dtype
                    assert result.shape == expectedValues.shape
                    assert (result == expectedValues).all()

                    # Mean, median, standard_deviation, sum

                    for statistic, func in [['mean', numpy.nanmean],
                                            ['median', numpy.nanmedian],
                                            ['standard_deviation', functools.partial(numpy.nanstd, ddof=1)],
                                            ['sum', numpy.nansum]]:

                        bg = BlockStatisticGrid(grid=grid, statistic=statistic, xySize=5, tSize=tSize, tUnit=tUnit, tStart=tStart, tSemiRegularity=tSemiRegularity)

                        expectedDataType = 'float64' if dtype != 'float32' else 'float32'
                        assert bg.DataType == expectedDataType

                        if grid.NoDataValue is not None:
                            data3 = data2.astype('float64')
                            data3 = numpy.where(data2 == noDataValue, numpy.nan, data3)

                        evSlices = []
                        i = 0
                        daysFromStart = 0
                        while i < len(tDaysInSlice):
                            ti1 = daysFromStart
                            ti2 = ti1 + tDaysInSlice[i]
                            if grid.NoDataValue is None:
                                evSlices.append(numpy.array([[func(grid.Data[ti1:ti2,0:5,0:5]), func(grid.Data[ti1:ti2,0:5,5:10]), func(grid.Data[ti1:ti2,0:5,10:12])], 
                                                             [func(grid.Data[ti1:ti2,5:10,0:5]), func(grid.Data[ti1:ti2,5:10,5:10]), func(grid.Data[ti1:ti2,5:10,10:12])]],
                                                            dtype=expectedDataType))
                            else:
                                with warnings.catch_warnings():
                                    warnings.filterwarnings("ignore", category=RuntimeWarning)
                                    evSlices.append(numpy.array([[func(data3[ti1:ti2,0:5,0:5]), func(data3[ti1:ti2,0:5,5:10]), func(data3[ti1:ti2,0:5,10:12])],
                                                                 [func(data3[ti1:ti2,5:10,0:5]), func(data3[ti1:ti2,5:10,5:10]), func(data3[ti1:ti2,5:10,10:12])]],
                                                                dtype=expectedDataType))
                            daysFromStart = ti2
                            i += 1

                        expectedValues = numpy.stack(evSlices, axis=0)

                        if grid.NoDataValue is not None:
                            expectedValues[numpy.isnan(expectedValues)] = bg.NoDataValue

                        result = bg.Data[:]

                        assert result.dtype == expectedValues.dtype
                        assert result.shape == expectedValues.shape

                        # For reasons I could not figure out, occasionally
                        # numpy.nanstd returns slightly different values. So for
                        # 'standard_deviation', we relax our equality requirement
                        # slightly.

                        if statistic == 'standard_deviation':
                            if bg.DataType == 'float32':
                                assert numpy.allclose(result, expectedValues, rtol=1e-6, atol=1e-6)
                            else:   # float64
                                assert numpy.allclose(result, expectedValues, rtol=1e-14, atol=1e-14)
                        else:
                            assert (result == expectedValues).all()


    # Helper functions

    def _CheckShapeAndXYZCoords(self, grid2, expectedShape, xCI, xCC, yCI, yCC, xySize, zCI=None, zCC=None, zSize=None):
        if xySize is None:
            xySize = 1
        assert all(numpy.equal(grid2.Shape, expectedShape))
        assert numpy.allclose(grid2.MinCoords   ['x'], [xCC + xCI*(-0.5)         + i*xCI*xySize for i in range(expectedShape[-1])], rtol=1e-15, atol=1e-15)
        assert numpy.allclose(grid2.CenterCoords['x'], [xCC + xCI*(xySize/2-0.5) + i*xCI*xySize for i in range(expectedShape[-1])], rtol=1e-15, atol=1e-15)
        assert numpy.allclose(grid2.MaxCoords   ['x'], [xCC + xCI*(xySize-0.5)   + i*xCI*xySize for i in range(expectedShape[-1])], rtol=1e-15, atol=1e-15)
        assert numpy.allclose(grid2.MinCoords   ['y'], [yCC + yCI*(-0.5)         + i*yCI*xySize for i in range(expectedShape[-2])], rtol=1e-15, atol=1e-15)
        assert numpy.allclose(grid2.CenterCoords['y'], [yCC + yCI*(xySize/2-0.5) + i*yCI*xySize for i in range(expectedShape[-2])], rtol=1e-15, atol=1e-15)
        assert numpy.allclose(grid2.MaxCoords   ['y'], [yCC + yCI*(xySize-0.5)   + i*yCI*xySize for i in range(expectedShape[-2])], rtol=1e-15, atol=1e-15)
        if zCI is not None:
            if zSize is None:
                zSize = 1
            assert numpy.allclose(grid2.MinCoords   ['z'], [zCC + zCI*(-0.5)        + i*zCI*zSize for i in range(expectedShape[-3])], rtol=1e-15, atol=1e-15)
            assert numpy.allclose(grid2.CenterCoords['z'], [zCC + zCI*(zSize/2-0.5) + i*zCI*zSize for i in range(expectedShape[-3])], rtol=1e-15, atol=1e-15)
            assert numpy.allclose(grid2.MaxCoords   ['z'], [zCC + zCI*(zSize-0.5)   + i*zCI*zSize for i in range(expectedShape[-3])], rtol=1e-15, atol=1e-15)


    def _CheckTCoords(self, grid, grid2, tBlockStart, tBlockSize, tExpectedShape, tSemiRegularity=None, expectedTCountPerSemiRegularPeriod=None):
        if expectedTCountPerSemiRegularPeriod is not None:
            self._CheckSemiRegularTCoords(grid, grid2, tBlockStart, tBlockSize, tExpectedShape, tSemiRegularity, expectedTCountPerSemiRegularPeriod)
        else:
            assert grid2.CoordIncrements[0] == tBlockSize
            assert grid2.TSemiRegularity is None
            assert grid2.TCountPerSemiRegularPeriod is None

            deltaUnit = grid2.TIncrementUnit + 's'
            delta = relativedelta(**{deltaUnit: tBlockSize})
            t = tBlockStart if tBlockStart is not None else datetime.datetime(grid.MinCoords['t', 0].year, 1, 1)

            while (t + delta) <= grid.MinCoords['t', 0]:
                t += delta

            expectedTMinCoords = [t + relativedelta(**{deltaUnit: tBlockSize*i}) for i in range(tExpectedShape)]
            assert len(expectedTMinCoords) == len(grid2.MinCoords['t'])
            assert all([expectedTMinCoords[i] == grid2.MinCoords['t', i] for i in range(len(expectedTMinCoords))])

            expectedTMaxCoords = [t + relativedelta(**{deltaUnit: tBlockSize*(i+1)}) for i in range(tExpectedShape)]
            assert len(expectedTMaxCoords) == len(grid2.MaxCoords['t'])
            assert all([expectedTMaxCoords[i] == grid2.MaxCoords['t', i] for i in range(len(expectedTMaxCoords))])


    def _CheckSemiRegularTCoords(self, grid, grid2, tBlockStart, tBlockSize, tExpectedShape, tSemiRegularity, expectedTCountPerSemiRegularPeriod):
        assert grid2.CoordIncrements[0] == tBlockSize
        assert grid2.TSemiRegularity == tSemiRegularity
        assert grid2.TCountPerSemiRegularPeriod == expectedTCountPerSemiRegularPeriod

        deltaUnit = grid2.TIncrementUnit + 's'
        delta = relativedelta(**{deltaUnit: tBlockSize})
        t = datetime.datetime(grid.MinCoords['t', 0].year, 1, 1)
        yearlySlice = 1

        while (t + delta) <= grid.MinCoords['t', 0]:
            t += delta
            yearlySlice += 1

        expectedTMinCoords = []
        expectedTMaxCoords = []

        for i in range(tExpectedShape):
            expectedTMinCoords.append(t)

            if yearlySlice < expectedTCountPerSemiRegularPeriod:
                t += delta
                yearlySlice += 1 
            else:
                t = datetime.datetime(t.year+1, 1, 1)
                yearlySlice = 1

            expectedTMaxCoords.append(t)

        assert len(expectedTMinCoords) == len(grid2.MinCoords['t'])
        assert all([expectedTMinCoords[i] == grid2.MinCoords['t', i] for i in range(len(expectedTMinCoords))])

        assert len(expectedTMaxCoords) == len(grid2.MaxCoords['t'])
        assert all([expectedTMaxCoords[i] == grid2.MaxCoords['t', i] for i in range(len(expectedTMaxCoords))])


    def _nanptp(self, a, axis=None):
        """
        Peak-to-peak (max–min) ignoring NaNs, with no warning if the whole array is NaN.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            return numpy.nanmax(a, axis=axis) - numpy.nanmin(a, axis=axis)
