# ArcGISRasters_test.py - pytest tests for GeoEco.DataManagement.ArcGISRasters.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import operator
import os

import numpy
from pathlib import Path
import pytest

from GeoEco.ArcGIS import GeoprocessorManager
from GeoEco.Datasets import Dataset, QueryableAttribute
from GeoEco.Datasets.ArcGIS import ArcGISWorkspace, ArcGISTable, ArcGISRaster as ArcGISRaster2
from GeoEco.DataManagement.ArcGISRasters import ArcGISRaster
from GeoEco.Logging import Logger
from GeoEco.Types import UnicodeStringTypeMetadata

Logger.Initialize()


def isArcPyInstalled():
    success = False
    try:
        import arcpy
        success = True
    except:
        pass
    return success


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


def exampleRastersWithDatesList():
    rasters = [['sst_20100102_123456.img', datetime.datetime(2010, 1, 2, 12, 34, 56)],
               ['sst_20100304_123456.img', datetime.datetime(2010, 3, 4, 12, 34, 56)],
               ['sst_20100506_123456.img', datetime.datetime(2010, 5, 6, 12, 34, 56)],
               ['sst_20100708_123456.img', datetime.datetime(2010, 7, 8, 12, 34, 56)],
               ['sst_20100910_123456.img', datetime.datetime(2010, 9, 10, 12, 34, 56)],
               ['sst_20101112_123456.img', datetime.datetime(2010, 11, 12, 12, 34, 56)]]
    return rasters


@pytest.fixture
def exampleRastersWithDatesPath(tmp_path):
    rasters = [tmp_path / p[0] for p in exampleRastersWithDatesList()]
    for rasterPath in rasters:
        ArcGISRaster.FromNumpyArray(numpyArray=numpy.zeros((180,360)),
                                    raster=str(rasterPath),
                                    xLowerLeftCorner=-180,
                                    yLowerLeftCorner=-90,
                                    cellSize=1)
    return tmp_path


@pytest.mark.skipif(not isArcPyInstalled(), reason='ArcGIS arcpy module is not installed')
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


    def test_Delete(self, generateExampleRasters):
        extensionsAndDTypes = {'.img': ['int8',],
                               '.tif': ['int8'],
                               '': ['int32']}  # ArcInfo Binary Grid a.k.a Esri Grid

        rastersDir, exampleRasters = generateExampleRasters(extensionsAndDTypes)

        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    rasterPath, numpyArray, noDataValue = exampleRasters[extension][dtype][arrayType]

                    assert extension != '' and rasterPath.is_file() or extension == '' and rasterPath.is_dir()
                    ArcGISRaster.Delete(rasterPath)
                    assert not rasterPath.is_file() and not rasterPath.is_dir()


    def test_Copy(self, generateExampleRasters):
        extensionsAndDTypes = {'.img': ['int16',],
                               '.tif': ['int16'],
                               '': ['float32']}  # ArcInfo Binary Grid a.k.a Esri Grid

        rastersDir, exampleRasters = generateExampleRasters(extensionsAndDTypes)

        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    rasterPath, numpyArray, noDataValue = exampleRasters[extension][dtype][arrayType]

                    assert extension != '' and rasterPath.is_file() or extension == '' and rasterPath.is_dir()
                    destRasterPath = Path(f'{rasterPath.parent}_copies') / rasterPath.name
                    ArcGISRaster.Copy(rasterPath, destRasterPath)
                    assert extension != '' and destRasterPath.is_file() or extension == '' and destRasterPath.is_dir()

                    # Test overwrite

                    ArcGISRaster.Copy(rasterPath, destRasterPath, overwriteExisting=True)

                    # Test that overwriteExisting=False fails

                    with pytest.raises(ValueError, match='.*already exists.*'):
                        ArcGISRaster.Copy(rasterPath, destRasterPath)


    def test_Move(self, generateExampleRasters):
        extensionsAndDTypes = {'.img': ['int32',],
                               '.tif': ['int32'],
                               '': ['float32']}  # ArcInfo Binary Grid a.k.a Esri Grid

        rastersDir, exampleRasters = generateExampleRasters(extensionsAndDTypes)

        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    rasterPath, numpyArray, noDataValue = exampleRasters[extension][dtype][arrayType]

                    assert extension != '' and rasterPath.is_file() or extension == '' and rasterPath.is_dir()
                    destRasterPath = Path(f'{rasterPath.parent}_copies') / rasterPath.name
                    ArcGISRaster.Move(rasterPath, destRasterPath)
                    assert not rasterPath.is_file() and not rasterPath.is_dir()
                    assert extension != '' and destRasterPath.is_file() or extension == '' and destRasterPath.is_dir()


    def test_Move_overwrite(self, generateExampleRasters):
        extensionsAndDTypes = {'.img': ['int32',],
                               '.tif': ['int32'],
                               '': ['float32']}  # ArcInfo Binary Grid a.k.a Esri Grid

        rastersDir, exampleRasters = generateExampleRasters(extensionsAndDTypes)

        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    rasterPath, numpyArray, noDataValue = exampleRasters[extension][dtype][arrayType]

                    assert extension != '' and rasterPath.is_file() or extension == '' and rasterPath.is_dir()
                    destRasterPath = Path(f'{rasterPath.parent}_copies') / rasterPath.name
                    ArcGISRaster.Copy(rasterPath, destRasterPath)
                    with pytest.raises(ValueError, match='.*already exists.*'):
                        ArcGISRaster.Move(rasterPath, destRasterPath)
                    ArcGISRaster.Move(rasterPath, destRasterPath, overwriteExisting=True)
                    assert not rasterPath.is_file() and not rasterPath.is_dir()
                    assert extension != '' and destRasterPath.is_file() or extension == '' and destRasterPath.is_dir()


    def test_FindAndCreateArcGISTable_filegdb(self, generateExampleRasters, tmp_path):

        # Create a file geodatabase.

        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        gdbPath = tmp_path / 'Temp.gdb'
        gp.CreateFileGDB_management(str(gdbPath.parent), gdbPath.name)

        # Define an ArcGISWorkspace for the file GDB. We'll use this to
        # examine the tables we create there.

        ws = ArcGISWorkspace(path=gdbPath,
                             datasetType=ArcGISTable,
                             pathParsingExpressions=[r'(?P<TableName>.+)'],
                             queryableAttributes=(QueryableAttribute('TableName', 'Table name', UnicodeStringTypeMetadata()),))

        # Generate some rasters.

        extensionsAndDTypes = {'.img': ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64'],
                               '.tif': ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64'],
                               '': ['int32', 'float32']}  # ArcInfo Binary Grid a.k.a Esri Grid

        rastersDir, exampleRasters = generateExampleRasters(extensionsAndDTypes)

        # Find at the root level without recursion: zero rasters.

        expectedCount = 0

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table1')
        assert ws.QueryDatasets("TableName = 'Table1'", reportProgress=False)[0].GetRowCount() == expectedCount

        # Test that we can overwrite a table.

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table1',
                                              overwriteExisting=True)

        # Test that overwriteExisting=False fails

        with pytest.raises(ValueError, match='.*already exists.*'):
            ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                                  outputWorkspace=gdbPath,
                                                  table='Table1')

        # Find at the root level with recursion: all the rasters.

        expectedCount = 0
        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    expectedCount += 1
        assert expectedCount > 0

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table2',
                                              searchTree=True)
        assert ws.QueryDatasets("TableName = 'Table2'", reportProgress=False)[0].GetRowCount() == expectedCount

        # Find at the root level with recursion: all starting with 'int32'

        expectedCount = 0
        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    if dtype.startswith('int32'):
                        expectedCount += 1
        assert expectedCount > 0

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table3',
                                              wildcard="int32*",
                                              searchTree=True)
        assert ws.QueryDatasets("TableName = 'Table3'", reportProgress=False)[0].GetRowCount() == expectedCount

        # Find at the root level with recursion: rasterType = 'IMG'

        expectedCount = 0
        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    if extension == '.img':
                        expectedCount += 1
        assert expectedCount > 0

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table4',
                                              searchTree=True,
                                              rasterType='IMG')
        assert ws.QueryDatasets("TableName = 'Table4'", reportProgress=False)[0].GetRowCount() == expectedCount

        # Find at the root level with recursion: rasterType = 'TIF'

        expectedCount = 0
        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    if extension == '.tif':
                        expectedCount += 1
        assert expectedCount > 0

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table5',
                                              searchTree=True,
                                              rasterType='TIF')
        assert ws.QueryDatasets("TableName = 'Table5'", reportProgress=False)[0].GetRowCount() == expectedCount

        # Find at the root level with recursion: rasterType = 'GRID'

        expectedCount = 0
        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    if extension == '':
                        expectedCount += 1
        assert expectedCount > 0

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table6',
                                              searchTree=True,
                                              rasterType='GRID')
        assert ws.QueryDatasets("TableName = 'Table6'", reportProgress=False)[0].GetRowCount() == expectedCount

        # Extent fields being populated correctly

        expectedCount = 0
        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    expectedCount += 1
        assert expectedCount > 0

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table7',
                                              searchTree=True,
                                              populateExtentFields=True)
        table = ws.QueryDatasets("TableName = 'Table7'", reportProgress=False)[0]
        results = table.Query(orderBy='Image ASC')

        assert len(results['XMin']) == expectedCount
        assert all([results['XMin'][i] == -180 for i in range(expectedCount)])
        assert len(results['YMin']) == expectedCount
        assert all([results['YMin'][i] == -90 for i in range(expectedCount)])
        assert len(results['XMax']) == expectedCount
        assert all([results['XMax'][i] == 180 for i in range(expectedCount)])
        assert len(results['YMax']) == expectedCount
        assert all([results['YMax'][i] == 90 for i in range(expectedCount)])

        # Relative path being populated correctly

        rasterPaths = []
        for extension in exampleRasters:
            for dtype in exampleRasters[extension]:
                for arrayType in exampleRasters[extension][dtype]:
                    rasterPaths.append(exampleRasters[extension][dtype][arrayType][0])
        assert len(rasterPaths) > 0
        rasterPaths.sort()

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=rastersDir,
                                              outputWorkspace=gdbPath,
                                              table='Table8',
                                              searchTree=True,
                                              relativePathField='RelativePath')
        table = ws.QueryDatasets("TableName = 'Table8'", reportProgress=False)[0]
        results = table.Query(orderBy='Image ASC')

        for i, p in enumerate(rasterPaths):
            assert results['Image'][i] == str(p)
            assert results['RelativePath'][i] == os.path.relpath(p, ws.Path)


    def test_FindAndCreateArcGISTable_ParseDates(self, exampleRastersWithDatesPath):

        # Create a file geodatabase.

        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        gdbPath = exampleRastersWithDatesPath / 'Temp.gdb'
        gp.CreateFileGDB_management(str(gdbPath.parent), gdbPath.name)

        # Define an ArcGISWorkspace for the file GDB. We'll use this to
        # examine the tables we create there.

        ws = ArcGISWorkspace(path=gdbPath,
                             datasetType=ArcGISTable,
                             pathParsingExpressions=[r'(?P<TableName>.+)'],
                             queryableAttributes=(QueryableAttribute('TableName', 'Table name', UnicodeStringTypeMetadata()),))

        # Find rasters.

        ArcGISRaster.FindAndCreateArcGISTable(inputWorkspace=exampleRastersWithDatesPath,
                                              outputWorkspace=gdbPath,
                                              table='Table1',
                                              parsedDateField='ParsedDate',
                                              dateParsingExpression='%Y%m%d_%H%M%S')
        table = ws.QueryDatasets("TableName = 'Table1'", reportProgress=False)[0]
        results = table.Query(orderBy='Image ASC')
        expectedDates = [expectedDate for [p, expectedDate] in exampleRastersWithDatesList()]

        assert all([results['ParsedDate'][i] == expectedDates[i] for i in range(len(expectedDates))])


    def test_CreateXRaster(self, tmp_path):
        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        coordinateSystem = Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'arcgis')
        cellSize = 0.25

        raster = tmp_path / 'test1.img'
        ArcGISRaster.CreateXRaster(raster=raster, extent='-180 -90 180 90', cellSize=cellSize, cellValue='Center', coordinateSystem=coordinateSystem)
        ex = gp.Describe(str(raster)).extent
        assert ex.XMin == -180 and ex.YMin == -90 and ex.XMax == 180 and ex.YMax == 90
        data, noDataValue = ArcGISRaster.ToNumpyArray(raster)
        assert data.min() == -180. + cellSize / 2
        assert data.max() == 180. - cellSize / 2
        assert all(data[:,0] == data.min())
        assert all(data[:,-1] == data.max())

        raster = tmp_path / 'test2.img'
        ArcGISRaster.CreateXRaster(raster=raster, extent='-180 -90 180 90', cellSize=cellSize, cellValue='Left', coordinateSystem=coordinateSystem)
        ex = gp.Describe(str(raster)).extent
        assert ex.XMin == -180 and ex.YMin == -90 and ex.XMax == 180 and ex.YMax == 90
        data, noDataValue = ArcGISRaster.ToNumpyArray(raster)
        assert data.min() == -180.
        assert data.max() == 180. - cellSize
        assert all(data[:,0] == data.min())
        assert all(data[:,-1] == data.max())

        raster = tmp_path / 'test3.img'
        ArcGISRaster.CreateXRaster(raster=raster, extent='-180 -90 180 90', cellSize=cellSize, cellValue='Right', coordinateSystem=coordinateSystem)
        ex = gp.Describe(str(raster)).extent
        assert ex.XMin == -180 and ex.YMin == -90 and ex.XMax == 180 and ex.YMax == 90
        data, noDataValue = ArcGISRaster.ToNumpyArray(raster)
        assert data.min() == -180. + cellSize
        assert data.max() == 180.
        assert all(data[:,0] == data.min())
        assert all(data[:,-1] == data.max())


    def test_CreateYRaster(self, tmp_path):
        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        coordinateSystem = Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'arcgis')
        cellSize = 0.25

        raster = tmp_path / 'test1.img'
        ArcGISRaster.CreateYRaster(raster=raster, extent='-180 -90 180 90', cellSize=cellSize, cellValue='Center', coordinateSystem=coordinateSystem)
        ex = gp.Describe(str(raster)).extent
        assert ex.XMin == -180 and ex.YMin == -90 and ex.XMax == 180 and ex.YMax == 90
        data, noDataValue = ArcGISRaster.ToNumpyArray(raster)
        assert data.min() == -90. + cellSize / 2
        assert data.max() == 90. - cellSize / 2
        assert all(data[0,:] == data.min())
        assert all(data[-1,:] == data.max())

        raster = tmp_path / 'test2.img'
        ArcGISRaster.CreateYRaster(raster=raster, extent='-180 -90 180 90', cellSize=cellSize, cellValue='Bottom', coordinateSystem=coordinateSystem)
        ex = gp.Describe(str(raster)).extent
        assert ex.XMin == -180 and ex.YMin == -90 and ex.XMax == 180 and ex.YMax == 90
        data, noDataValue = ArcGISRaster.ToNumpyArray(raster)
        assert data.min() == -90.
        assert data.max() == 90. - cellSize
        assert all(data[0,:] == data.min())
        assert all(data[-1,:] == data.max())

        raster = tmp_path / 'test3.img'
        ArcGISRaster.CreateYRaster(raster=raster, extent='-180 -90 180 90', cellSize=cellSize, cellValue='Top', coordinateSystem=coordinateSystem)
        ex = gp.Describe(str(raster)).extent
        assert ex.XMin == -180 and ex.YMin == -90 and ex.XMax == 180 and ex.YMax == 90
        data, noDataValue = ArcGISRaster.ToNumpyArray(raster)
        assert data.min() == -90. + cellSize
        assert data.max() == 90.
        assert all(data[0,:] == data.min())
        assert all(data[-1,:] == data.max())


    def test_ExtractByMask(self, tmp_path):
        dataRaster = tmp_path / 'data.img'
        ArcGISRaster.FromNumpyArray(numpyArray=numpy.ones((180,360))*2, raster=dataRaster, xLowerLeftCorner=-180, yLowerLeftCorner=-90, cellSize=1)

        maskRaster = tmp_path / 'mask.img'
        mask = numpy.ones((180,360))
        mask[0:90, 0:90] = 0
        ArcGISRaster.FromNumpyArray(numpyArray=mask, raster=maskRaster, xLowerLeftCorner=-180, yLowerLeftCorner=-90, cellSize=1, noDataValue=0)

        outputRaster = tmp_path / 'output.img'
        ArcGISRaster.ExtractByMask(dataRaster, maskRaster, outputRaster)

        data, noDataValue = ArcGISRaster.ToNumpyArray(outputRaster)
        assert noDataValue is not None
        assert (data[0:90, 0:90] == noDataValue).all()
        assert (data[90:, :] == 2).all()
        assert (data[:, 90:] == 2).all()


    def test_ToLines(self, tmp_path):
        data = numpy.zeros((180,360), dtype='int16')
        data[45, 0:180] = 1
        data[135, 180:360] = 2

        raster = tmp_path / 'raster1.img'
        shp = tmp_path / 'features1.shp'
        ArcGISRaster.FromNumpyArray(numpyArray=data, raster=raster, xLowerLeftCorner=-180, yLowerLeftCorner=-90, cellSize=1, noDataValue=0)
        assert ArcGISRaster.ToNumpyArray(raster)[0].dtype == 'int16'
        ArcGISRaster.ToLines(inputRaster=raster, outputFeatureClass=shp, backgroundValue='NODATA', field='Value')
        table = ArcGISTable(str(shp))
        assert table.GeometryType == 'MultiLineString'
        with pytest.raises(RuntimeError, match='.*does not support ORDER BY.*'):
            results = table.Query(orderBy='grid_code ASC', reportProgress=False)
        results = table.Query(reportProgress=False)
        assert sorted(results['grid_code']) == [1, 2]

        data[45, 0:180] = 3
        data[135, 180:360] = 4

        raster = tmp_path / 'raster2.img'
        ArcGISRaster.FromNumpyArray(numpyArray=data, raster=raster, xLowerLeftCorner=-180, yLowerLeftCorner=-90, cellSize=1)
        assert ArcGISRaster.ToNumpyArray(raster)[0].dtype == 'int16'
        ArcGISRaster.ToLines(inputRaster=raster, outputFeatureClass=shp, backgroundValue='ZERO', field='Value', overwriteExisting=True)
        table = ArcGISTable(str(shp))
        assert table.GeometryType == 'MultiLineString'
        results = table.Query(reportProgress=False)
        assert sorted(results['grid_code']) == [3,4]


    def test_ToPoints(self, tmp_path):
        data = numpy.zeros((180,360), dtype='int32')
        data[170, 200] = 3
        data[45, 45] = 1
        data[135, 60] = 2
        data[12, 300] = 2

        raster = tmp_path / 'raster1.img'
        shp = tmp_path / 'features1.shp'
        ArcGISRaster.FromNumpyArray(numpyArray=data, raster=raster, xLowerLeftCorner=-180, yLowerLeftCorner=-90, cellSize=1, noDataValue=0)
        assert ArcGISRaster.ToNumpyArray(raster)[0].dtype == 'int32'
        ArcGISRaster.ToPoints(inputRaster=raster, outputFeatureClass=shp, field='Value')
        table = ArcGISTable(str(shp))
        assert table.GeometryType == 'Point'
        results = table.Query(reportProgress=False)
        assert sorted(results['grid_code']) == [1, 2, 2, 3]


    def test_ToPolygons(self, tmp_path):
        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        data = numpy.zeros((2000,2000), dtype='int8')
        data[0:1000, 0:1000] = 1
        data[1000:2000, 1000:2000] = 2
        data[1100:1200, 100:200] = 3
        data[1140:1160, 140:160] = 0

        raster = tmp_path / 'raster1.img'
        shp = tmp_path / 'features1.shp'
        ArcGISRaster.FromNumpyArray(numpyArray=data, raster=raster, xLowerLeftCorner=-1000, yLowerLeftCorner=-1000, cellSize=1, noDataValue=0)
        assert ArcGISRaster.ToNumpyArray(raster)[0].dtype == 'int8'
        ArcGISRaster.ToPolygons(inputRaster=raster, outputFeatureClass=shp, simplify=False, field='Value')
        gp.CalculateGeometryAttributes_management(str(shp), [['ShapeArea', 'AREA']])
        table = ArcGISTable(str(shp))
        assert table.GeometryType == 'MultiPolygon'
        results = table.Query(reportProgress=False)
        assert sorted(results['gridcode']) == [1, 2, 3]
        assert sorted(results['ShapeArea']) == [9600, 1000000, 1000000]


    def test_ToPolygonOutlines(self, tmp_path):
        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        data = numpy.zeros((2000,2000), dtype='int8')
        data[0:1000, 0:1000] = 1
        data[1000:2000, 1000:2000] = 2
        data[1100:1200, 100:200] = 3
        data[1140:1160, 140:160] = 0

        raster = tmp_path / 'raster1.img'
        shp = tmp_path / 'features1.shp'
        ArcGISRaster.FromNumpyArray(numpyArray=data, raster=raster, xLowerLeftCorner=-1000, yLowerLeftCorner=-1000, cellSize=1, noDataValue=0)
        assert ArcGISRaster.ToNumpyArray(raster)[0].dtype == 'int8'
        ArcGISRaster.ToPolygonOutlines(inputRaster=raster, outputFeatureClass=shp, simplify=False, field='Value')
        gp.CalculateGeometryAttributes_management(str(shp), [['ShapeLen', 'LENGTH']])
        table = ArcGISTable(str(shp))
        assert table.GeometryType == 'MultiLineString'
        results = table.Query(reportProgress=False)
        assert sorted(results['gridcode']) == [1, 2, 3, 3]
        assert sorted(results['ShapeLen']) == [80, 400, 4000, 4000]


    def test_ProjectClipAndOrExecuteMapAlgebra(self, tmp_path):

        # Test clipping from coordinates we specify.

        sr1 = Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'obj')
        arcWKT1 = Dataset.ConvertSpatialReference('obj', sr1, 'arcgis')

        data = numpy.zeros((180,360), dtype='float32')
        data[0:90, 0:180] = 1
        data[90:180, 0:180] = 2
        data[0:90, 180:360] = 3

        inputRaster = tmp_path / 'raster1.img'
        outputRaster = tmp_path / 'output1.img'
        ArcGISRaster.FromNumpyArray(numpyArray=data, raster=inputRaster, xLowerLeftCorner=-180, yLowerLeftCorner=-90, cellSize=1, noDataValue=0, coordinateSystem=arcWKT1)
        assert ArcGISRaster.ToNumpyArray(inputRaster)[0].dtype == 'float32'

        ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra(inputRaster=inputRaster, outputRaster=outputRaster, clippingRectangle="-180 -90 0 0", overwriteExisting=True)
        band = ArcGISRaster2(outputRaster).QueryDatasets(reportProgress=False)[0]
        assert band.MinCoords['x', 0] == -180
        assert band.MaxCoords['x', -1] == 0
        assert band.MinCoords['y', 0] == -90
        assert band.MaxCoords['y', -1] == 0
        assert (band.Data[:] == 1).all()
        del band

        ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra(inputRaster=inputRaster, outputRaster=outputRaster, clippingRectangle="-180 0 0 90", overwriteExisting=True)
        band = ArcGISRaster2(outputRaster).QueryDatasets(reportProgress=False)[0]
        assert band.MinCoords['x', 0] == -180
        assert band.MaxCoords['x', -1] == 0
        assert band.MinCoords['y', 0] == 0
        assert band.MaxCoords['y', -1] == 90
        assert (band.Data[:] == 2).all()
        del band

        ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra(inputRaster=inputRaster, outputRaster=outputRaster, clippingRectangle="0 -90 180 0", overwriteExisting=True)
        band = ArcGISRaster2(outputRaster).QueryDatasets(reportProgress=False)[0]
        assert band.MinCoords['x', 0] == 0
        assert band.MaxCoords['x', -1] == 180
        assert band.MinCoords['y', 0] == -90
        assert band.MaxCoords['y', -1] == 0
        assert (band.Data[:] == 3).all()
        del band

        ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra(inputRaster=inputRaster, outputRaster=outputRaster, clippingRectangle="0 0 180 90", overwriteExisting=True)
        band = ArcGISRaster2(outputRaster).QueryDatasets(reportProgress=False)[0]
        assert band.MinCoords['x', 0] == 0
        assert band.MaxCoords['x', -1] == 180
        assert band.MinCoords['y', 0] == 0
        assert band.MaxCoords['y', -1] == 90
        assert (band.Data[:] == band.NoDataValue).all()
        del band

        # Test clipping from a shapefile.

        ws = ArcGISWorkspace(path=tmp_path,
                             datasetType=ArcGISTable,
                             pathParsingExpressions=[r'(?P<TableName>.+)'],
                             queryableAttributes=(QueryableAttribute('TableName', 'Table name', UnicodeStringTypeMetadata()),))

        table = ws.CreateTable('polygon1.shp', geometryType='MultiPolygon', spatialReference=sr1)
        with table.OpenInsertCursor(reportProgress=False) as cursor:
            geom = ws._ogr().CreateGeometryFromWkt('POLYGON((0 0, -10 0, -10 -5, 0 -5, 0 0))')
            cursor.SetGeometry(geom)
            cursor.SetValue('Id', 1)    # This field is autocreated by ArcGIS
            cursor.InsertRow()

        ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra(inputRaster=inputRaster, outputRaster=outputRaster, clippingDataset=table.Path, overwriteExisting=True)

        band = ArcGISRaster2(outputRaster).QueryDatasets(reportProgress=False)[0]
        assert band.MinCoords['x', 0] == -10
        assert band.MaxCoords['x', -1] == 0
        assert band.MinCoords['y', 0] == -5
        assert band.MaxCoords['y', -1] == 0
        assert (band.Data[:] == 1).all()
        del band

        # Test map algebra.

        rng = numpy.random.default_rng(12345)
        data = rng.random((180,360), dtype='float64') * 2 - 1
        inputRaster = tmp_path / 'mapalg_raster.img'
        outputRaster = tmp_path / 'mapalg_raster_output.img'
        ArcGISRaster.FromNumpyArray(numpyArray=data, raster=inputRaster, xLowerLeftCorner=-180, yLowerLeftCorner=-90, cellSize=1)

        ArcGISRaster.ProjectClipAndOrExecuteMapAlgebra(inputRaster=inputRaster, outputRaster=outputRaster, mapAlgebraExpression='Con(inputRaster < 0, -999, inputRaster * 2)', overwriteExisting=True)

        result, noDataValue = ArcGISRaster.ToNumpyArray(outputRaster)
        assert data.shape == result.shape
        assert ((data < 0) == (result == -999)).all()
        assert numpy.allclose(data[data >= 0] * 2, result[data >= 0])
