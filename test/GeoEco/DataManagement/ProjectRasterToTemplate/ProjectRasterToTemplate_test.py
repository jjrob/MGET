# ProjectRasterToTemplate_test.py - pytest tests for
# GeoEco.Datasets.ArcGISRasters.ProjectToTemplate().
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
from GeoEco.DataManagement.ArcGISRasters import ArcGISRaster
from GeoEco.Datasets.ArcGIS import ArcGISRaster as ArcGISRaster2
from GeoEco.Matlab import MatlabDependency

Logger.Initialize()


def isArcPyInstalled():
    success = False
    try:
        import arcpy
        success = True
    except:
        pass
    return success


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


@pytest.mark.skipif(not isArcPyInstalled(), reason='ArcGIS arcpy module is not installed')
class TestProjectToTemplate():

    def test_Project(self, tmp_path):
        inputRaster = pathlib.Path(__file__).parent / '20100101_sst.img'
        templateRaster = pathlib.Path(__file__).parent / 'EC22_Study_Area_5km.img'
        outputRaster = tmp_path / 'project.img'
        ArcGISRaster.ProjectToTemplate(inputRaster, templateRaster, outputRaster, resamplingTechnique='bilinear')
        assert outputRaster.is_file()

    def test_ProjectAndMask(self, tmp_path):
        inputRaster = pathlib.Path(__file__).parent / '20100101_sst.img'
        templateRaster = pathlib.Path(__file__).parent / 'EC22_Study_Area_5km.img'
        outputRaster = tmp_path / 'project_and_mask.img'
        ArcGISRaster.ProjectToTemplate(inputRaster, templateRaster, outputRaster, resamplingTechnique='bilinear', mask=True)
        assert outputRaster.is_file()

    @pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
    def test_ProjectAndInterpAndMask(self, tmp_path):
        inputRaster = pathlib.Path(__file__).parent / '20100101_sst.img'
        templateRaster = pathlib.Path(__file__).parent / 'EC22_Study_Area_5km.img'
        outputRaster = tmp_path / 'project_and_interp_and_mask.img'
        ArcGISRaster.ProjectToTemplate(inputRaster, templateRaster, outputRaster, resamplingTechnique='bilinear', interpolationMethod='del2a', mask=True)
        assert outputRaster.is_file()
        expectedRaster = pathlib.Path(__file__).parent / '20100101_sst_5km.img'
        outputData, outputNoDataValue = ArcGISRaster.ToNumpyArray(outputRaster)
        expectedData, expectedNoDataValue = ArcGISRaster.ToNumpyArray(expectedRaster)
        outputData[outputData == outputNoDataValue] = numpy.nan
        expectedData[expectedData == expectedNoDataValue] = numpy.nan
        assert numpy.allclose(outputData, expectedData, equal_nan=True)

    def test_Crosses180_FromZeroTo360(self, tmp_path):
        inputRaster = pathlib.Path(__file__).parent / 'topo30_Clip.tif'
        templateRaster = pathlib.Path(__file__).parent / 'Arc26_Study_Area_10km.img'
        outputRaster = tmp_path / 'Arc26_depth.img'
        ArcGISRaster.ProjectToTemplate(inputRaster, templateRaster, outputRaster, resamplingTechnique='bilinear', mask=True)
        assert outputRaster.is_file()
        expectedRaster = pathlib.Path(__file__).parent / 'topo30_Clip_10km.img'
        outputData, outputNoDataValue = ArcGISRaster.ToNumpyArray(outputRaster)
        expectedData, expectedNoDataValue = ArcGISRaster.ToNumpyArray(expectedRaster)
        outputData[outputData == outputNoDataValue] = -999999           # These are integer rasters, so we can't use numpy.nan here, so we use -999999 to represent NoData in both rasters
        expectedData[expectedData == expectedNoDataValue] = -999999
        assert numpy.allclose(outputData, expectedData)

    def test_Crosses180_FromNeg180ToPos180(self, tmp_path):
        inputRaster = pathlib.Path(__file__).parent / 'ETOPO_2022_v1_60s_N90W180_bed_clipped_resampled.tif'
        templateRaster = pathlib.Path(__file__).parent / 'Arc26_Study_Area_10km.img'
        outputRaster = tmp_path / 'Arc26_depth2.img'
        ArcGISRaster.ProjectToTemplate(inputRaster, templateRaster, outputRaster, resamplingTechnique='bilinear', mask=True)
        assert outputRaster.is_file()
        expectedRaster = pathlib.Path(__file__).parent / 'ETOPO_2022_v1_60s_N90W180_bed_clipped_resampled_10km.img'
        outputData, outputNoDataValue = ArcGISRaster.ToNumpyArray(outputRaster)
        expectedData, expectedNoDataValue = ArcGISRaster.ToNumpyArray(expectedRaster)
        outputData[outputData == outputNoDataValue] = numpy.nan
        expectedData[expectedData == expectedNoDataValue] = numpy.nan
        assert numpy.allclose(outputData, expectedData, equal_nan=True)
