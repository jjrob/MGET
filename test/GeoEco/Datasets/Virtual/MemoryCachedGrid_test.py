# MemoryCachedGrid_test.py - pytest tests for
# GeoEco.Datasets.Virtual.MemoryCachedGrid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import numpy
import pytest

from GeoEco.Datasets import NumpyGrid
from GeoEco.Datasets.Virtual import MemoryCachedGrid


class TestMemoryCachedGrid():

    def test_MCG(self):

        # Allocate a 100x100 NumpyGrid representing a grid that we want to
        # cache.

        data = numpy.arange(10000, dtype='float64').reshape(100,100) + 1
        grid = NumpyGrid(numpyArray=data, 
                         displayName='test data',
                         spatialReference=None,
                         dimensions='yx',
                         coordIncrements=(1.,1.),
                         cornerCoords=(0.,0.),
                         unscaledNoDataValue=-1)

        # Create a MemoryCachedGrid of effectively unlimited size that caches
        # 9x9 blocks.

        cachedGrid = MemoryCachedGrid(grid=grid, 
                                      maxCacheSize=1000000000, 
                                      xMinBlockSize=9,
                                      yMinBlockSize=9)

        # Retrieve a value at 4,4. This will cache one 9x9 block.

        x = cachedGrid.Data[4,4]
        assert x > 0

        # Zero out the original grid.

        grid.Data[:] = 0.
        assert (grid.Data[:] == 0).all()

        # Validate that we can read from [0:9, 0:9] from the cachedGrid and
        # not get any zeros.

        x = cachedGrid.Data[0:9,0:9]
        assert (x > 0).all()

        # Validate that if we read from some other location, we get zeros.

        x = cachedGrid.Data[10:,10:]
        assert (x == 0).all()


    def test_MCG_cache_all(self):

        # Allocate a 100x100 NumpyGrid representing a grid that we want to
        # cache.

        data = numpy.arange(10000, dtype='float64').reshape(100,100) + 1
        grid = NumpyGrid(numpyArray=data, 
                         displayName='test data',
                         spatialReference=None,
                         dimensions='yx',
                         coordIncrements=(1.,1.),
                         cornerCoords=(0.,0.),
                         unscaledNoDataValue=-1)

        # Create a MemoryCachedGrid of effectively unlimited size that caches
        # 1000x1000 blocks.

        cachedGrid = MemoryCachedGrid(grid=grid, 
                                      maxCacheSize=1000000000, 
                                      xMinBlockSize=1000,
                                      yMinBlockSize=1000)

        # Retrieve a value at 4,4. This will cache the entire grid.

        x = cachedGrid.Data[4,4]
        assert x > 0

        # Zero out the original grid.

        grid.Data[:] = 0.
        assert (grid.Data[:] == 0).all()

        # Validate that we can read from the entire cachedGrid and not get any
        # zeros.

        x = cachedGrid.Data[:]
        assert (x > 0).all()


    def test_MCG_cache_expiry(self):

        # Allocate a 100x100 NumpyGrid representing a grid that we want to
        # cache.

        data = numpy.arange(10000, dtype='float64').reshape(100,100) + 1
        grid = NumpyGrid(numpyArray=data, 
                         displayName='test data',
                         spatialReference=None,
                         dimensions='yx',
                         coordIncrements=(1.,1.),
                         cornerCoords=(0.,0.),
                         unscaledNoDataValue=-1)

        # Create a MemoryCachedGrid that caches 10x10 blocks but is limited to
        # 3 of them.

        cachedGrid = MemoryCachedGrid(grid=grid, 
                                      maxCacheSize=10*10*8*3, 
                                      xMinBlockSize=10,
                                      yMinBlockSize=10)

        # Retrieve three blocks. This should fill the cache.

        x = cachedGrid.Data[5,5]
        assert x > 0

        x = cachedGrid.Data[15,15]
        assert x > 0

        x = cachedGrid.Data[25,25]
        assert x > 0

        # Retrieve a fourth blocks. This should drop the first one.

        x = cachedGrid.Data[35,35]
        assert x > 0

        # Zero out the original grid.

        grid.Data[:] = 0.
        assert (grid.Data[:] == 0).all()

        # Validate that the most recent three blocks read as non-zero but
        # reading the oldest one returns zero.

        x = cachedGrid.Data[15,15]
        assert x > 0

        x = cachedGrid.Data[25,25]
        assert x > 0

        x = cachedGrid.Data[35,35]
        assert x > 0

        x = cachedGrid.Data[5,5]
        assert x == 0

        # Validate that the second, third, and fourth oldest one return zero
        # as they get knocked out of the cache.

        x = cachedGrid.Data[15,15]
        assert x == 0

        x = cachedGrid.Data[25,25]
        assert x == 0

        x = cachedGrid.Data[35,35]
        assert x == 0
