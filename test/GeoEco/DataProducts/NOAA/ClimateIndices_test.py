# ClimateIndices_test.py - pytest tests for
# GeoEco.DataProducts.NOAA.ClimateIndices.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os
from pathlib import Path

import pytest

from GeoEco.ArcGIS import GeoprocessorManager
from GeoEco.Datasets import QueryableAttribute
from GeoEco.Datasets.ArcGIS import ArcGISWorkspace, ArcGISTable
from GeoEco.Datasets.SQLite import SQLiteDatabase
from GeoEco.Logging import Logger
from GeoEco.DataProducts.NOAA.ClimateIndices import PSLClimateIndices
from GeoEco.Types import UnicodeStringTypeMetadata

Logger.Initialize()


def isArcPyInstalled():
    try:
        import arcpy
    except:
        return False
    return True


class TestPSLClimateIndices():

    @pytest.mark.skipif(not isArcPyInstalled(), reason='ArcGIS arcpy module is not installed')
    def test_ClassifyONIEpisodesInTimeSeriesArcGISTable(self, tmp_path):

        # Create a file geodatabase.

        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        gdbPath = tmp_path / 'Temp.gdb'
        gp.CreateFileGDB_management(str(gdbPath.parent), gdbPath.name)

        # Define an ArcGISWorkspace for the file GDB. 

        ws = ArcGISWorkspace(path=gdbPath,
                             datasetType=ArcGISTable,
                             pathParsingExpressions=[r'(?P<TableName>.+)'],
                             queryableAttributes=(QueryableAttribute('TableName', 'Table name', UnicodeStringTypeMetadata()),))

        # Download the ONI climate index time series to a GDB table.

        PSLClimateIndices.UrlToArcGISTable(url='https://psl.noaa.gov/data/correlation/oni.data',
                                           table=gdbPath / 'ONITable',
                                           field='ONI')

        # Add a field for the ENSO episode.

        table = ws.QueryDatasets("TableName = 'ONITable'", reportProgress=False)[0]
        table.AddField('Episode', 'int32', isNullable=True)

        # Classify the ONI values.

        PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable(table=gdbPath / 'ONITable',
                                                                     dateField='IndexDate',
                                                                     oniField='ONI',
                                                                     episodeField='Episode')


    def test_ClassifyONIEpisodesInTimeSeriesTable(self, tmp_path):

        # Create an in-memory SQLite database.

        db = SQLiteDatabase(':memory:')

        # Download the ONI climate index time series to a SQLite table.

        PSLClimateIndices.UrlToTable(url='https://psl.noaa.gov/data/correlation/oni.data',
                                     database=db,
                                     table='ONITable',
                                     field='ONI')

        # Add a field for the ENSO episode.

        table = db.QueryDatasets("TableName = 'ONITable'", reportProgress=False)[0]
        table.AddField('Episode', 'int32', isNullable=True)

        # Classify the ONI values.

        PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable(table=table,
                                                               dateField='IndexDate',
                                                               oniField='ONI',
                                                               episodeField='Episode')
