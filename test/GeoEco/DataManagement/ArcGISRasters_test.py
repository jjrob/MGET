# ArcGISRasters_test.py - pytest tests for GeoEco.DataManagement.ArcGISRasters.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import operator
import os

import numpy
import pytest

from GeoEco.Datasets import Dataset
from GeoEco.DataManagement.ArcGISRasters import ArcGISRaster
from GeoEco.Logging import Logger


def generateExampleArrays(dtypes, shape, numUniqueIntegers):
    """Generate numpy arrays representing rasters of the range of dtypes we support, both without and with a noDataValue."""

    seed = 4242424242
    arrays = {}

    for dtype in dtypes:
        rng = numpy.random.default_rng(seed)
        mask = rng.random(size=shape) > 0.75

        if dtype[0] == 'f':
            a1 = (rng.random(size=shape, dtype=dtype) - 1) * (numpy.finfo('float32').max - 1)
        elif numUniqueIntegers is None:
            a1 = rng.integers(size=shape, dtype=dtype, low=numpy.iinfo(dtype).min, high=numpy.iinfo(dtype).max)
        else:
            low = 0 if numpy.iinfo(dtype).min == 0 else 0 - (numUniqueIntegers // 2)
            high = low + numUniqueIntegers
            a1 = rng.integers(size=shape, dtype=dtype, low=low, high=high)

        noDataValue = a1[0,0] if dtype[0] == 'f' or numUniqueIntegers is None else high + 1
        a2 = numpy.choose(mask, [a1, noDataValue])

        arrays[dtype] = {'a1': a1, 'a2': a2, 'noDataValue': noDataValue}

    return arrays


@pytest.fixture
def generateExampleRasters(tmp_path):
    """Return a generator function that creates example rasters in a directory structure."""

    def _generateExampleRasters(extensionsAndDTypes={'.img': ['int32', 'float32']}, shape=(90, 180), numUniqueIntegers=None):
        dtypes = set([dtype for dtypes in extensionsAndDTypes.values() for dtype in dtypes])
        arrays = generateExampleArrays(dtypes, shape, numUniqueIntegers)
        coordinateSystem = Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'arcgis')
        exampleRasters = {}

        for extension, dtypes in extensionsAndDTypes.items():
            if extension not in exampleRasters:
                exampleRasters[extension] = {}

            for dtype in dtypes:
                if dtype not in exampleRasters[extension]:
                    exampleRasters[extension][dtype] = {}

                for arrayType in ['a1', 'a2']:
                    rasterPath = tmp_path / \
                                 (extension.split('.')[-1] if len(extension) > 0 else 'aig') / \
                                 ('float' if dtype[0] == 'f' else 'integer') / \
                                 (dtype + '_' + arrayType + extension)

                    numpyArray = arrays[dtype][arrayType]
                    noDataValue = arrays[dtype]['noDataValue'] if arrayType == 'a2' else None

                    ArcGISRaster.FromNumpyArray(numpyArray=numpyArray,
                                                raster=str(rasterPath),
                                                xLowerLeftCorner=-180.,
                                                yLowerLeftCorner=-90.,
                                                cellSize=360. / numpyArray.shape[1],
                                                noDataValue=noDataValue,
                                                coordinateSystem=coordinateSystem,
                                                calculateStatistics=True,
                                                buildRAT=dtype[0] != 'f' and dtype != 'uint32',     # Build Raster Attribute Table in ArcGIS Pro 3.2.2 fails for uint32
                                                buildPyramids=shape[0] >= 1024)

                    exampleRasters[extension][dtype][arrayType] = [rasterPath, numpyArray, noDataValue]

        return (tmp_path, exampleRasters)

    return _generateExampleRasters


class TestArcGISRaster():

    def test_FromNumpyArray_all_dtypes(self, generateExampleRasters):
        extensionsAndDTypes = {'.img': ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64'],
                               '.tif': ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64'],
                               '': ['int32', 'float32']}  # ArcInfo Binary Grid a.k.a Esri Grid

        rastersDir, exampleRasters = generateExampleRasters(extensionsAndDTypes)

        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    rasterPath, numpyArray, noDataValue = exampleRasters[extension][dtype][arrayType]

                    numpyArray2, noDataValue2 = ArcGISRaster.ToNumpyArray(rasterPath)

                    try:
                        # If a format other than ArcInfo Binary Grid, both
                        # should have noDataValues, or neither should.

                        if extension != '':
                            assert not operator.xor(noDataValue is None, noDataValue2 is None)

                        # Both have data in the same cells.

                        if noDataValue is not None:
                            assert numpy.logical_not(numpy.logical_xor(numpyArray == noDataValue, numpyArray2 == noDataValue2)).all()

                        # If a format other than floating point ArcInfo Binary
                        # Grid, we should read exactly the same values that
                        # we wrote.

                        if dtype[0] != 'f' or extension != '':
                            assert numpy.logical_or(numpyArray == numpyArray2, numpy.logical_and(numpyArray == noDataValue, numpyArray2 == noDataValue2)).all()

                        # For ArcInfo Binary Grid, there is some loss of
                        # precision in the round trip. Check that the ratio
                        # of the values is 1 +/- 0.0000001, which we will
                        # consider equal. ArcInfo Binary Grid is bad for many
                        # reasons, and we avoid it, but it used to be the
                        # default for ArcGIS, so we still want to test it.

                        else:
                            ratio = numpy.abs(numpyArray / numpyArray2)
                            if noDataValue is not None:
                                ratio[numpyArray2 == noDataValue2] = 0.
                            assert numpy.logical_or((ratio - 1 < 0.0000001).all(), numpy.logical_and(numpyArray == noDataValue, numpyArray2 == noDataValue2)).all()

                    except AssertionError as e:
                        Logger.Error('AssertionError for extension=%s, dtype=%s, arrayType=%s, raster=%s' % (extension, dtype, arrayType, rasterPath))
                        raise


    def test_FromNumpyArray_integer_symbology_check(self, generateExampleRasters):
        """Create integer rasters with just a few values, so we can view them
           in ArcGIS to see if the appropriate default symbology is
           chosen."""

        extensionsAndDTypes = {'.img': ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32'],
                               '.tif': ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32'],
                               '': ['int32']}  # ArcInfo Binary Grid a.k.a Esri Grid

        rastersDir, exampleRasters = generateExampleRasters(extensionsAndDTypes, numUniqueIntegers=4)

