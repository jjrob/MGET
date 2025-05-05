# FMDG_test.py - pytest tests for GeoEco.Datasets.Virtual.FastMarchingDistanceGrid.
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
import sys

from GeoEco.Logging import Logger
from GeoEco.Datasets import NumpyGrid
from GeoEco.Datasets.Collections import DirectoryTree
from GeoEco.Datasets.GDAL import GDALDataset
from GeoEco.Datasets.Virtual import FastMarchingDistanceGrid
from GeoEco.Dependencies import PythonModuleDependency


def isSkfmmInstalled():
    d = PythonModuleDependency('skfmm')
    try:
        d.Initialize()
    except:
        return False
    return True

@pytest.fixture
def medSeaStudyAreaRasterPath():
    return pathlib.Path(__file__).parent / 'Med_studyAreaRaster_corr.img'

@pytest.fixture
def expectedOuptutRasterPath():
    return pathlib.Path(__file__).parent / 'DistToAtl.img'


@pytest.mark.skipif(not isSkfmmInstalled(), reason='The skfmm package is required by FastMarchingDistanceGrid but it is not installed')
class TestFMDG():

    def test_FMDG(self, medSeaStudyAreaRasterPath, expectedOuptutRasterPath, tmp_path):
        assert medSeaStudyAreaRasterPath.is_file()

        # Initialize MGET's logging.

        Logger.Initialize()

        # Load the study area raster and get the first band as a
        # GDALRasterGrid.

        dataset = GDALDataset(str(medSeaStudyAreaRasterPath))
        grid = dataset.QueryDatasets(reportProgress=False)[0]

        # This band uses an int32 data type and has values of 0 for land and 1
        # for water. Every cell has data. First, extract the band's data as a
        # numpy array. Then, in that array, set land (0) to NoData. Note that
        # we do not want set values of grid.Data itself (e.g. grid.Data[...] =
        # ...) because this will write values into the raster file, which we
        # do not want to change. Also, Grid does not support indexing with
        # numpy arrays (e.g. data == 0).

        data = grid.Data[:]
        data[data == 0] = grid.NoDataValue

        # We are now representing land as NoData, which
        # FastMarchingDistanceGrid expects. Now set several cells that are
        # currently marked as 1 to -1. These new -1 cells represent the feature
        # we will computing distances to. We know the approximate coordinates
        # of the centers of these cells and use a Grid function to look up
        # their integer indices, and then use those to set the cell values.
        # (These are in a projected coordinate system with meters as the
        # linear unit, which is why they are very large.)

        cellCoordsYX = [(1607000, 2882000),
                        (1602000, 2882000),
                        (1597000, 2882000),
                        (1592000, 2882000),
                        (1587000, 2882000),
                        (1582000, 2882000),
                        (1577000, 2877000),
                        (1572000, 2877000),
                        (1567000, 2877000),
                        (1562000, 2877000),]

        cellIndicesYX = [grid.GetIndicesForCoords(coords) for coords in cellCoordsYX]

        for indices in cellIndicesYX:
            data[indices[0], indices[1]] = -1

        # Create a NumpyGrid from the original band, then write our new data
        # into it.

        numpyGrid = NumpyGrid.CreateFromGrid(grid)
        numpyGrid.Data[:] = data

        # Construct the FastMarchingDistanceGrid. Set minDist to 0, so that
        # cells within the feature we defined above will have a distance of 0,
        # rather than a negative distance (from the cell center to the edge).
        # Constructing this grid does not perform the calculation; that is
        # deferred until the grid's Data property is accessed.

        fmdGrid = FastMarchingDistanceGrid(numpyGrid, minDist=0)

        # We want to write the FastMarchingDistanceGrid out as a raster with
        # GDAL. Construct a DirectoryTree that we can import it into. Note
        # that because we are just going to import this single raster, we can
        # specify the destination file name in pathCreationExpressions, and
        # not have to define a QueryableAttribute that gives the file name.

        dirTree = DirectoryTree(path=str(tmp_path),
                                datasetType=GDALDataset,
                                pathCreationExpressions=['DistToAtl.img'])

        # Import the grid into the DirectoryTree.

        dirTree.ImportDatasets([fmdGrid], mode='Replace', calculateStatistics=True)

        assert (tmp_path / 'DistToAtl.img').is_file()

        # Compare the grid we created to the grid we expect.

        dataset = GDALDataset(str(expectedOuptutRasterPath))
        expectedGrid = dataset.QueryDatasets(reportProgress=False)[0]

        expectedData = expectedGrid.Data[:]
        actualData = fmdGrid.Data[:]

        assert (expectedData == actualData).all()
