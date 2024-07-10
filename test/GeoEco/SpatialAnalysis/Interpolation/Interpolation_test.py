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

from GeoEco.Logging import Logger
from GeoEco.SpatialAnalysis.Interpolation import Interpolator
from GeoEco.Datasets.ArcGIS import ArcGISRaster

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
        Interpolator.InpaintArcGISRaster(testInpaintRasterPath, outputRaster, maxHoleSize=200)
        inpaintedGrid = ArcGISRaster.GetRasterBand(outputRaster)
        expectedGrid = ArcGISRaster.GetRasterBand(pathlib.Path(__file__).parent / 'Inpainted_full.img')
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

    def test_InpaintSmallHoles(self, testInpaintRasterPath):
        assert testInpaintRasterPath.is_file()
        outputRaster = tmp_path / 'output.img'
        Interpolator.InpaintArcGISRaster(testInpaintRasterPath, outputRaster)
        inpaintedGrid = ArcGISRaster.GetRasterBand(outputRaster)
        expectedGrid = ArcGISRaster.GetRasterBand(pathlib.Path(__file__).parent / 'Inpainted_small_holes.img')
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)

    def test_InpaintSmallHolesMinMax(self, testInpaintRasterPath):
        assert testInpaintRasterPath.is_file()
        outputRaster = tmp_path / 'output.img'
        Interpolator.InpaintArcGISRaster(testInpaintRasterPath, outputRaster, maxHoleSize=200, minValue=-1.3, maxValue=-0.2)
        inpaintedGrid = ArcGISRaster.GetRasterBand(outputRaster)
        expectedGrid = ArcGISRaster.GetRasterBand(pathlib.Path(__file__).parent / 'Inpainted_min_max.img')
        assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)
