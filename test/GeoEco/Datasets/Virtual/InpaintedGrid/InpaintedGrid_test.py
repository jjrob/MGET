# InpaintedGrid_test.py - pytest tests for GeoEco.Datasets.Virtual.InpaintedGrid.
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
from GeoEco.Datasets.Virtual import InpaintedGrid
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
    return pathlib.Path(__file__).parent / 'GSMChl_gaussian_2006160.img'


@pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
class TestInpaintedGrid():

    def test_InpaintFull(self, testRasterPath):
        assert testRasterPath.is_file()
        grid = GDALDataset.GetRasterBand(str(testRasterPath))
        inpaintedGrid = InpaintedGrid(grid)
        expectedGrid = GDALDataset.GetRasterBand(str(pathlib.Path(__file__).parent / 'Inpainted_full.img'))
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

    def test_InpaintSmallHoles(self, testRasterPath):
        assert testRasterPath.is_file()
        grid = GDALDataset.GetRasterBand(str(testRasterPath))
        inpaintedGrid = InpaintedGrid(grid, maxHoleSize=200)
        expectedGrid = GDALDataset.GetRasterBand(str(pathlib.Path(__file__).parent / 'Inpainted_small_holes.img'))
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

    def test_InpaintSmallHolesMinMax(self, testRasterPath):
        assert testRasterPath.is_file()
        grid = GDALDataset.GetRasterBand(str(testRasterPath))
        inpaintedGrid = InpaintedGrid(grid, maxHoleSize=200, minValue=-1.3, maxValue=-0.2)
        expectedGrid = GDALDataset.GetRasterBand(str(pathlib.Path(__file__).parent / 'Inpainted_min_max.img'))
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)
