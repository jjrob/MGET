# MaskedGrid_test.py - pytest tests for GeoEco.Datasets.Virtual.MaskedGrid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from collections import namedtuple

import numpy
import pytest

from GeoEco.Datasets import NumpyGrid
from GeoEco.Datasets.Virtual import MaskedGrid


class TestMaskedGrid():

    def test_Operators(self):

        # Allocate a NumpyGrid with some test data.

        data = numpy.arange(20, dtype='int32').reshape(5,4) * 100
        grid = NumpyGrid(numpyArray=data, 
                         displayName='test data',
                         spatialReference=None,
                         dimensions='yx',
                         coordIncrements=(1.,1.),
                         cornerCoords=(0.,0.),
                         unscaledNoDataValue=-1)

        # Allocate some NumpyGrids to serve as masks.

        mask1 = NumpyGrid.CreateFromGrid(grid)
        mask1.Data[:] = numpy.arange(20, dtype='int32').reshape(5,4)

        # Define test cases.

        TestCase = namedtuple('TestCase', 'masks, operators, values, result')

        testCases = []
        testCases.append(TestCase(masks=[mask1], 
                                  operators=['='], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] == 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['=='], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] == 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['!='], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] != 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['<>'], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] != 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['<'], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] < 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['<='], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] <= 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['>'], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] > 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['>='], 
                                  values=[5], 
                                  result=numpy.where(mask1.Data[:] >= 5, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['any'],
                                  values=[1], 
                                  result=numpy.where(numpy.bitwise_and(mask1.Data[:], 1) > 0, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['any'],
                                  values=[7], 
                                  result=numpy.where(numpy.bitwise_and(mask1.Data[:], 7) > 0, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['any'],
                                  values=[0], 
                                  result=numpy.where(numpy.bitwise_and(mask1.Data[:], 0) > 0, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['all'],
                                  values=[1], 
                                  result=numpy.where(numpy.bitwise_and(mask1.Data[:], 1) == 1, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['all'],
                                  values=[7], 
                                  result=numpy.where(numpy.bitwise_and(mask1.Data[:], 7) == 7, grid.NoDataValue, grid.Data[:])))

        testCases.append(TestCase(masks=[mask1], 
                                  operators=['all'],
                                  values=[0],
                                  result=numpy.where(numpy.bitwise_and(mask1.Data[:], 0) == 0, grid.NoDataValue, grid.Data[:])))

        # Define some cases with two masks.

        for i in range(len(testCases) - 1):
            testCases.append(TestCase(masks=testCases[i].masks + testCases[i+1].masks,
                                      operators=testCases[i].operators + testCases[i+1].operators,
                                      values=testCases[i].values + testCases[i+1].values,
                                      result=numpy.where(testCases[i].result == grid.NoDataValue, grid.NoDataValue, testCases[i+1].result)))

        # Test the cases.

        for i, tc in enumerate(testCases):
            maskedGrid = MaskedGrid(grid=grid,
                                    masks=tc.masks,
                                    operators=tc.operators,
                                    values=tc.values)

            assert (maskedGrid.Data[:] == tc.result).all(), 'case %i failed: %s' % (i, tc)
