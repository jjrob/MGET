# CannyEdgeGrid_test.py - pytest tests for GeoEco.Datasets.Virtual.CannyEdgeGrid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os
import pathlib
import sys

import numpy
import pytest

from GeoEco.Logging import Logger
from GeoEco.Datasets.GDAL import GDALDataset
from GeoEco.Datasets.Virtual import CannyEdgeGrid
from GeoEco.Matlab import MatlabDependency

Logger.Initialize()


def isMatlabInstalled():

    # Currently, we only support MGET's MATLAB functionality on Python 3.12 or
    # lower, because the MATLAB Compiler only supports that, and we can only
    # execute MATLAB code packaged by it on Python versions it supports.

    if sys.version_info.minor > 12:
        return False

    d = MatlabDependency()
    try:
        d.Initialize()
    except:
        return False
    return True


@pytest.fixture
def testRasterPath():
    return pathlib.Path(__file__).parent / 'thetao_0000.5_20210101.img'


@pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
class TestCannyEdgeGrid():

    def test_Canny(self, testRasterPath):
        assert testRasterPath.is_file()
        grid = GDALDataset.GetRasterBand(testRasterPath)

        cannyGrid = CannyEdgeGrid(grid)
        assert(numpy.unique(cannyGrid.Data[:]).tolist() == [0,1,255])
        expectedGrid = GDALDataset.GetRasterBand(pathlib.Path(__file__).parent / 'thetao_0000.5_20210101_fronts.img')
        assert numpy.allclose(cannyGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

        cannyGrid = CannyEdgeGrid(grid, minSize=5)
        expectedGrid = GDALDataset.GetRasterBand(pathlib.Path(__file__).parent / 'thetao_0000.5_20210101_fronts_minsize5.img')
        assert numpy.allclose(cannyGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

        cannyGrid = CannyEdgeGrid(grid, highThreshold=0.2)
        expectedGrid = GDALDataset.GetRasterBand(pathlib.Path(__file__).parent / 'thetao_0000.5_20210101_fronts_highThreshold02.img')
        assert numpy.allclose(cannyGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

        cannyGrid = CannyEdgeGrid(grid, highThreshold=0.2, lowThreshold=0.15)
        expectedGrid = GDALDataset.GetRasterBand(pathlib.Path(__file__).parent / 'thetao_0000.5_20210101_fronts_highThreshold02_lowThreshold015.img')
        assert numpy.allclose(cannyGrid.Data[:], expectedGrid.Data[:], equal_nan=True)
