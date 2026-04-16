# LarvalDispersal_test.py - pytest tests for GeoEco.Connectivity.LarvalDispersal.
#
# Copyright (C) 2026 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import importlib
import os
from pathlib import Path
import sys

import pytest

from test.helpers.matlab import isMatlabInstalled

from GeoEco.Logging import Logger
from GeoEco.Connectivity.LarvalDispersal import LarvalDispersal

Logger.Initialize()


def getCMEMSCredentials():
    try:
        import dotenv
        dotenv.load_dotenv(Path(__file__).parent.parent.parent / '.env')
        return (os.getenv('CMEMS_USERNAME'), os.getenv('CMEMS_PASSWORD'))
    except:
        return None, None

def isArcPyInstalled():
    return importlib.util.find_spec("arcpy") is not None


@pytest.mark.skipif(not isArcPyInstalled(), reason='ArcGIS arcpy module is not installed')
class TestLarvalDispersal():

    _PatchIDsRaster = os.path.join(os.path.dirname(__file__), 'Gulf_of_Mexico_Patches', 'Reef_Rasters', 'reef_ids.img')
    _PatchCoverRaster = os.path.join(os.path.dirname(__file__), 'Gulf_of_Mexico_Patches', 'Reef_Rasters', 'reef_cover_proportion.img')
    _WaterMaskRaster = os.path.join(os.path.dirname(__file__), 'Gulf_of_Mexico_Patches', 'Reef_Rasters', 'water_mask.img')

    def test_CreateSimulationFromArcGISRasters(self, tmp_path):
        simDir = os.path.join(tmp_path, 'SimDir')

        LarvalDispersal.CreateSimulationFromArcGISRasters(
            simulationDirectory=simDir, 
            patchIDsRaster=self._PatchIDsRaster, 
            patchCoverRaster=self._PatchCoverRaster, 
            waterMaskRaster=self._WaterMaskRaster
        )

    @pytest.mark.skipif(None in getCMEMSCredentials(), reason='CMEMS_USERNAME or CMEMS_PASSWORD environment variables not defined')
    @pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
    def test_RunGulfOfMexicoSimulation(self, tmp_path):

        # Create the simulation.

        simDir = os.path.join(tmp_path, 'SimDir')

        LarvalDispersal.CreateSimulationFromArcGISRasters(
            simulationDirectory=simDir, 
            patchIDsRaster=self._PatchIDsRaster, 
            patchCoverRaster=self._PatchCoverRaster, 
            waterMaskRaster=self._WaterMaskRaster
        )

        # Load one month of currents.

        username, password = getCMEMSCredentials()

        LarvalDispersal.LoadCMEMSCurrentsIntoSimulation(
            simulationDirectory=simDir, 
            startDate=datetime.datetime(2011, 9, 20), 
            endDate=datetime.datetime(2011, 10, 21), 
            username=username, 
            password=password, 
            interpolationMethod='Del2a')

        # Simulate dispersal with no competency curve or mortality.

        startDate = datetime.datetime(2011, 9, 20)
        duration = 5
        simulationTimeStep = 0.5 
        summarizationPeriod = 48
        settlementRate = 0.80
        mortalityRate = 0.10

        resultsDir1 = os.path.join(tmp_path, 'ResultsDir1')
        if not os.path.isdir(resultsDir1):
            os.makedirs(resultsDir1)

        LarvalDispersal.RunSimulation2012(
            simulationDirectory=simDir, 
            resultsDirectory=resultsDir1, 
            startDate=startDate, 
            duration=duration, 
            simulationTimeStep=simulationTimeStep, 
            summarizationPeriod=summarizationPeriod,
            settlementRate=settlementRate,
            overwriteExisting=True
        )

        # Test competency and mortality.

        resultsDir2 = os.path.join(tmp_path, 'ResultsDir2')
        if not os.path.isdir(resultsDir2):
            os.makedirs(resultsDir2)

        LarvalDispersal.RunSimulation2012(
            simulationDirectory=simDir, 
            resultsDirectory=resultsDir2, 
            startDate=startDate, 
            duration=duration, 
            simulationTimeStep=simulationTimeStep, 
            summarizationPeriod=summarizationPeriod,
            a=10, 
            b=0.25, 
            settlementRate=settlementRate,
            overwriteExisting=True
        )

        # Test sensory zone.

        resultsDir3 = os.path.join(tmp_path, 'ResultsDir3')
        if not os.path.isdir(resultsDir3):
            os.makedirs(resultsDir3)

        LarvalDispersal.RunSimulation2012(
            simulationDirectory=simDir, 
            resultsDirectory=resultsDir3, 
            startDate=startDate, 
            duration=duration, 
            simulationTimeStep=simulationTimeStep, 
            summarizationPeriod=summarizationPeriod,
            a=10, 
            b=0.25, 
            settlementRate=1, 
            useSensoryZone=True, 
            overwriteExisting=True
        )

        # Visualize the results

        minimumDensity = 0.00001
        minimumDispersal = 0.0001
        minimumDispersalType = 'Quantity'

        LarvalDispersal.VisualizeResults2012(
            simulationDirectory=simDir, 
            resultsDirectory=resultsDir1, 
            outputGDBName='Results.gdb', 
            minimumDensity=minimumDensity, 
            minimumDispersal=minimumDispersal, 
            minimumDispersalType=minimumDispersalType, 
            overwriteExisting=True
        )

        LarvalDispersal.VisualizeResults2012(
            simulationDirectory=simDir, 
            resultsDirectory=resultsDir2, 
            outputGDBName='Results.gdb', 
            mortalityRate=mortalityRate, 
            mortalityMethod='A', 
            useCompetencyForDensityRasters=True, 
            minimumDensity=minimumDensity, 
            minimumDispersal=minimumDispersal, 
            minimumDispersalType=minimumDispersalType, 
            overwriteExisting=True
        )

        LarvalDispersal.VisualizeResults2012(
            simulationDirectory=simDir, 
            resultsDirectory=resultsDir3, 
            outputGDBName='Results.gdb', 
            mortalityRate=mortalityRate, 
            mortalityMethod='A', 
            useCompetencyForDensityRasters=True, 
            minimumDensity=minimumDensity, 
            minimumDispersal=minimumDispersal, 
            minimumDispersalType=minimumDispersalType, 
            overwriteExisting=True
        )

        # Visualize all results together. Note that this applies mortality to
        # all three simulations, while above we did not apply mortality to
        # the first one. VisualizeMultipleResults2012 is mainly intended to
        # compute summary statistics for simulations of the same biological
        # parameters across multiple time periods. Here, we are varying the
        # biological parameters across the same time period, simply for the
        # purpose of verifying that the tool runs.

        resultsDirAll = os.path.join(tmp_path, 'ResultsDirAll')
        if not os.path.isdir(resultsDirAll):
            os.makedirs(resultsDirAll)

        import arcpy

        arcpy.CreateFileGDB_management(resultsDirAll, 'Results.gdb')

        LarvalDispersal.VisualizeMultipleResults2012(
            simulationDirectory=simDir, 
            resultsDirectories=[resultsDir1, resultsDir2, resultsDir3], 
            outputConnections=os.path.join(resultsDirAll, 'Results.gdb', 'Connectivity'), 
            summaryStatistic='Maximum', 
            mortalityRate=mortalityRate, 
            mortalityMethod='A', 
            minimumDispersal=minimumDispersal, 
            overwriteExisting=True
        )
