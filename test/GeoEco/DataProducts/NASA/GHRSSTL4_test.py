# GHRSSTL4_test.py - pytest tests for GHRSSTLevel4 classes in
# GeoEco.DataProducts.NASA.PODAAC.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import os
from pathlib import Path
import re
import sys

import numpy
import pytest

from GeoEco.ArcGIS import GeoprocessorManager
from GeoEco.Datasets import Dataset, QueryableAttribute
from GeoEco.Datasets.ArcGIS import ArcGISWorkspace, ArcGISTable
from GeoEco.Logging import Logger
from GeoEco.DataProducts.NASA.PODAAC import GHRSSTLevel4Granules, GHRSSTLevel4
from GeoEco.Matlab import MatlabDependency
from GeoEco.Types import UnicodeStringTypeMetadata

Logger.Initialize()


def getEarthdataCredentials():
    try:
        import dotenv
        dotenv.load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')
        return (os.getenv('NASA_EARTHDATA_USERNAME'), os.getenv('NASA_EARTHDATA_PASSWORD'))
    except:
        return None, None


def isArcPyInstalled():
    try:
        import arcpy
    except:
        return False
    return True


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


@pytest.mark.skipif(None in getEarthdataCredentials(), reason='NASA_EARTHDATA_USERNAME or NASA_EARTHDATA_PASSWORD environment variables not defined')
class TestGHRSSTLevel4Granules():

    # Test that we can access each dataset.

    @pytest.mark.parametrize("shortName", GHRSSTLevel4Granules._Metadata)
    def test_GHRSSTLevel4Dataset(self, shortName, tmp_path):

        # Define the collection and query it for datasets.

        username, password = getEarthdataCredentials()
        collection = GHRSSTLevel4Granules(username=username, 
                                          password=password, 
                                          shortName=shortName, 
                                          datasetType='netcdf', 
                                          timeout=60, 
                                          maxRetryTime=300, 
                                          cacheDirectory=None)
        datasets = collection.QueryDatasets()
        assert len(datasets) > 0

        # Retrieve the most recent dataset and get some data from it. This
        # will cause a netCDF to be downloaded and opened.

        assert datasets[-1].Dimensions == 'tyx'
        assert datasets[-1].Shape[0] == 1
        assert datasets[-1].Shape[1] > 1
        assert datasets[-1].Shape[2] > 1

        yStart = int(datasets[-1].Shape[1] * 0.25)
        yStop = yStart + yStart*2

        xStart = int(datasets[-1].Shape[2] * 0.25)
        xStop = xStart + xStart*2

        slices = (0, slice(yStart, yStop), slice(xStart, xStop))

        Logger.Info(f'From {datasets[-1].DisplayName}, getting slice {slices}')

        data = datasets[-1].Data.__getitem__(slices)

        assert len(data.shape) == 2   # the t dimension automatically gets droppped because it has length 1
        assert data.shape[0] > 1
        assert data.shape[1] > 1


@pytest.mark.skipif(None in getEarthdataCredentials(), reason='NASA_EARTHDATA_USERNAME or NASA_EARTHDATA_PASSWORD environment variables not defined')
@pytest.mark.skipif(not isArcPyInstalled(), reason='ArcGIS arcpy module is not installed')
class TestGHRSSTLevel4ArcGIS():

    def test_CreateArcGISRasters(self, tmp_path):
        username, password = getEarthdataCredentials()
        shortName = 'MUR25-JPL-L4-GLOB-v04.2'
        for variableName in ['analysed_sst', 'analysis_error']:
            GHRSSTLevel4.CreateArcGISRasters(username=username, 
                                             password=password, 
                                             shortName=shortName, 
                                             variableName=variableName, 
                                             outputWorkspace=tmp_path,
                                             startDate=datetime.datetime(2020,1,1),
                                             endDate=datetime.datetime(2020,1,3,23,59,59))
            for day in [1,2,3]:
                assert (tmp_path / shortName / variableName / '2020' / ('%s_202001%02i090000.img' % (variableName, day))).is_file()

    def test_CreateArcGISRastersInGDB(self, tmp_path):
        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        outputGDB = tmp_path / 'test.gdb'
        gp.CreateFileGDB_management(str(tmp_path), 'test.gdb')
        username, password = getEarthdataCredentials()
        shortName = 'MUR25-JPL-L4-GLOB-v04.2'
        for variableName in ['analysed_sst', 'analysis_error']:
            GHRSSTLevel4.CreateArcGISRasters(username=username, 
                                             password=password, 
                                             shortName=shortName, 
                                             variableName=variableName, 
                                             outputWorkspace=outputGDB,
                                             startDate=datetime.datetime(2020,1,1),
                                             endDate=datetime.datetime(2020,1,3,23,59,59))
            for day in [1,2,3]:
                assert gp.Exists(str(outputGDB / ('%s_%s_202001%02i090000' % (re.sub('[^A-Za-z0-9_]', '_', shortName), variableName, day))))

    def test_CreateClimatologicalArcGISRasters(self, tmp_path):
        username, password = getEarthdataCredentials()
        shortName = 'MUR25-JPL-L4-GLOB-v04.2'
        variableName = 'analysed_sst'
        cacheDir = tmp_path / 'Cache'
        os.makedirs(cacheDir)
        for statistic in ['Count', 'Maximum', 'Mean', 'Minimum', 'Range', 'Standard_Deviation', 'Sum']:
            GHRSSTLevel4.CreateClimatologicalArcGISRasters(username=username, 
                                                           password=password, 
                                                           shortName=shortName, 
                                                           variableName=variableName,
                                                           statistic=statistic, 
                                                           binType='monthly',
                                                           outputWorkspace=tmp_path,
                                                           cacheDirectory=cacheDir,
                                                           startDate=datetime.datetime(2020,1,1),
                                                           endDate=datetime.datetime(2020,12,31,23,59,59))
            for month in range(1, 13):
                assert (tmp_path / shortName / variableName / 'Monthly_Climatology' / ('%s_month%02i_%s.img' % (variableName, month, statistic.lower()))).is_file()

    @pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
    def test_InterpolateAtArcGISPoints(self, tmp_path):

        # Create a geodatabase of test data.

        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        gp.CreateFileGDB_management(str(tmp_path), 'Test.gdb')

        ws = ArcGISWorkspace(path=tmp_path / 'Test.gdb',
                             datasetType=ArcGISTable,
                             pathParsingExpressions=[r'(?P<TableName>.+)'], 
                             queryableAttributes=(QueryableAttribute('TableName', 'Table name', UnicodeStringTypeMetadata()),))

        table = ws.CreateTable(tableName='TestPoints',
                               geometryType='point',
                               spatialReference=Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'obj'))

        table.AddField('t', 'datetime')
        table.AddField('ExpectedSST', 'string', isNullable=True)
        table.AddField('SST', 'float64', isNullable=True)

        points = [[-100, 40, datetime.datetime(2020,1,1), None],      # USA (land)
                  [3, 25, datetime.datetime(2020,1,1), None],         # Algeria (land)
                  [-65, -35, datetime.datetime(2020,1,1), None],      # Argentina (land)
                  [135, -25, datetime.datetime(2020,1,1), None],      # Australia (land)
                  [0, 0, datetime.datetime(2020,6,30), 'hot'],        # Null Island
                  [-70, 30, datetime.datetime(2020,6,30), 'hot'],     # Sargasso Sea
                  [155, -15, datetime.datetime(2020,10,31), 'hot'],   # Coral Sea
                  [155, 20, datetime.datetime(2020,9,1), 'hot'],      # east North Pacific
                  [-175, -5, datetime.datetime(2020,9,1), 'hot'],     # south Central Pacific
                  [-55, 60, datetime.datetime(2020,6,30), 'cold'],    # Labrador Sea
                  [40, 75, datetime.datetime(2020,6,30), 'cold'],     # Berants Sea
                  [-65, -60, datetime.datetime(2020,6,30), 'cold'],   # Drake Passage
                  [145, -50, datetime.datetime(2020,6,30), 'cold'],   # Tasmania
                 ]

        with table.OpenInsertCursor() as cursor:
            for x, y, t, expectedSST in points:
                cursor.SetGeometry(table._ogr().CreateGeometryFromWkt(f'POINT({x} {y})'))
                cursor.SetValue('t', t)
                cursor.SetValue('ExpectedSST', expectedSST)
                cursor.InsertRow()

        # Test iterpolation.

        username, password = getEarthdataCredentials()
        shortName = 'MUR25-JPL-L4-GLOB-v04.2'
        GHRSSTLevel4.InterpolateAtArcGISPoints(username=username, 
                                               password=password, 
                                               shortName=shortName, 
                                               variableName='analysed_sst',
                                               points=os.path.join(table.Path), 
                                               tField='t', 
                                               valueField='SST')

        with table.OpenSelectCursor(reportProgress=False) as cursor:
            while cursor.NextRow():
                expectedSST = cursor.GetValue('ExpectedSST')
                sst = cursor.GetValue('SST')
                if expectedSST is None:
                    assert sst is None
                elif expectedSST == 'hot':
                    assert sst > 20
                elif expectedSST == 'cold':
                    assert sst < 10
                else:
                    raise ValueError('Unknown ExpectedSST value %r' % expectedSST)

        # Test the where clause.

        with table.OpenUpdateCursor(reportProgress=False) as cursor:
            while cursor.NextRow():
                cursor.SetValue('SST', None)
                cursor.UpdateRow()

        GHRSSTLevel4.InterpolateAtArcGISPoints(username=username, 
                                               password=password, 
                                               shortName=shortName, 
                                               variableName='analysed_sst',
                                               points=os.path.join(table.Path), 
                                               tField='t', 
                                               valueField='SST',
                                               where="ExpectedSST <> 'cold'")

        with table.OpenSelectCursor(reportProgress=False) as cursor:
            while cursor.NextRow():
                expectedSST = cursor.GetValue('ExpectedSST')
                sst = cursor.GetValue('SST')
                if expectedSST is None or expectedSST == 'cold':
                    assert sst is None
                elif expectedSST == 'hot':
                    assert sst > 20
                else:
                    raise ValueError('Unknown ExpectedSST value %r' % expectedSST)

    @pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
    def test_CannyEdgesAsArcGISRasters(self, tmp_path):
        username, password = getEarthdataCredentials()
        shortName = 'MUR25-JPL-L4-GLOB-v04.2'
        GHRSSTLevel4.CannyEdgesAsArcGISRasters(username=username, 
                                               password=password, 
                                               shortName=shortName, 
                                               outputWorkspace=tmp_path,
                                               spatialExtent='-82 25 -52 50',
                                               startDate=datetime.datetime(2020,1,1),
                                               endDate=datetime.datetime(2020,1,3,23,59,59))
        for day in [1,2,3]:
            assert (tmp_path / shortName / 'canny_fronts' / '2020' / ('canny_fronts_202001%02i090000.img' % day)).is_file()
