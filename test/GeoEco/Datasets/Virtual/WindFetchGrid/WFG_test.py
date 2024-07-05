# WFG_test.py - pytest tests for GeoEco.Datasets.Virtual.WindFetchGrid.
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
from GeoEco.Datasets import NumpyGrid
from GeoEco.Datasets.Collections import DirectoryTree
from GeoEco.Datasets.GDAL import GDALDataset
from GeoEco.Datasets.Virtual import WindFetchGrid


@pytest.fixture
def medSeaStudyAreaRasterPath():
    return pathlib.Path(__file__).parent / 'Med_studyAreaRaster_corr.img'

@pytest.fixture
def expectedOuptutRasterPath():
    return pathlib.Path(__file__).parent / 'WindFetch.img'


class TestFMDG():

    def test_FMDG(self, medSeaStudyAreaRasterPath, expectedOuptutRasterPath, tmp_path):
        assert medSeaStudyAreaRasterPath.is_file()

        # Initialize MGET's logging.

        Logger.Initialize()

        # Load the study area raster and get the first band as a
        # GDALRasterGrid.

        grid = GDALDataset.GetRasterBand(str(medSeaStudyAreaRasterPath))

        # This band uses an int32 data type and has values of 0 for land and 1
        # for water. Every cell has data. First, extract the band's data as a
        # numpy array. Then, in that array, set land (0) to NoData. Note that
        # we do not want set values of grid.Data itself (e.g. grid.Data[...] =
        # ...) because this will write values into the raster file, which we
        # do not want to change. Also, Grid does not support indexing with
        # numpy arrays (e.g. data == 0).

        data = grid.Data[:]
        data[data == 0] = grid.NoDataValue

        numpyGrid = NumpyGrid.CreateFromGrid(grid)
        numpyGrid.Data[:] = data

        # Construct the WindFetchGrid

        directions = list(range(0, 360, 10))

        wfGrid = WindFetchGrid(numpyGrid, directions=directions)

        # Write the WindFetchGrid out as a raster with GDAL. This isn't really
        # necessary for testing WindFetchGrid, but helps test GDALDataset.

        grid = GDALDataset.CreateRaster(str(tmp_path / 'WindFetch.img'), wfGrid, overwriteExisting=True, calculateStatistics=True)

        assert (tmp_path / 'WindFetch.img').is_file()

        # Compare the grid we created to the grid we expect.

        dataset = GDALDataset(str(expectedOuptutRasterPath))
        expectedGrid = dataset.QueryDatasets(reportProgress=False)[0]

        expectedData = expectedGrid.Data[:]
        actualData = wfGrid.Data[:]

        assert (expectedData == actualData).all()
