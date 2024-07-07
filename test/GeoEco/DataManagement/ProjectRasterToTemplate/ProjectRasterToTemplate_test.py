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

import pytest

from GeoEco.Logging import Logger
from GeoEco.DataManagement.ArcGISRasters import ArcGISRaster
from GeoEco.Datasets.ArcGIS import ArcGISRaster2



class TestProjectToTemplate():

    def test_Project(self, tmp_path):
        inputRaster = pathlib.Path(__file__).parent / '20100101_sst.img'
        templateRaster = pathlib.Path(__file__).parent / 'EC22_Study_Area_5km.img'
        outputRaster = tmp_path / 'output.img'
        Logger.Initialize()
        ArcGISRaster.ProjectToTemplate(inputRaster, templateRaster, outputRaster, resamplingTechnique='bilinear')
        assert outputRaster.is_file()

        # expectedGrid = GDALDataset.GetRasterBand(str(pathlib.Path(__file__).parent / 'Inpainted_full.img'))
        # assert numpy.allclose(inpaintedGrid.Data[:], expectedGrid.Data[:], equal_nan=True)
