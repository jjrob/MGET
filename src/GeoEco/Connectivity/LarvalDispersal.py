# Connectivity/LarvalDispersal.py - Interpolation functions.
#
# Copyright (C) 2026 Jason J. Roberts and Eric A. Treml
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from configparser import ConfigParser
import datetime
import glob
import math
import os
import pickle

from ..ArcGIS import GeoprocessorManager
from ..DataManagement.ArcGISRasters import ArcGISRaster as ArcGISRaster2
from ..DataManagement.Directories import Directory, TemporaryDirectory
from ..DataManagement.Fields import Field
from ..DataManagement.Files import File
from ..DataProducts.CMEMS import CMEMSARCOArray
from ..Datasets import Grid, NumpyGrid, QueryableAttribute
from ..Datasets.ArcGIS import ArcGISWorkspace, ArcGISRaster, ArcGISTable
from ..Datasets.Virtual import GridSliceCollection, MaskedGrid
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger, ProgressReporter
from ..Types import *
from ..Matlab import MatlabDependency, MatlabWorkerProcess

class LarvalDispersal(object):
    __doc__ = DynamicDocString()

    @classmethod
    def CreateSimulationFromArcGISRasters(cls, simulationDirectory, patchIDsRaster, patchCoverRaster, waterMaskRaster, crosses180=False, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Validate the coordinate systems, extents, and cell sizes of
        # the input rasters.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        describePatchIDsRaster = gp.Describe(patchIDsRaster)
        describePatchCoverRaster = gp.Describe(patchCoverRaster)
        describeWaterMaskRaster = gp.Describe(waterMaskRaster)

        if describePatchIDsRaster.SpatialReference.Type.lower() != 'projected':
            Logger.RaiseException(ValueError(_('ArcGIS reports that the patch IDs raster %(raster)s uses a %(type)s coordinate system. It must use a projected coordinate system. Please project it and try again.') % {'raster': patchIDsRaster, 'type': describePatchIDsRaster.SpatialReference.Type.lower()}))
        if describePatchIDsRaster.SpatialReference.LinearUnitName.lower() != 'meter':
            Logger.RaiseException(ValueError(_('ArcGIS reports that the patch IDs raster %(raster)s uses the linear unit "%(unit)s". It must use a coordinate system that has meters as its linear unit.  Please project it to a coordinate system that uses meters and try again.') % {'raster': patchIDsRaster, 'unit': describePatchIDsRaster.SpatialReference.LinearUnitName.lower()}))

        patchIDsRasterCS = gp.CreateSpatialReference_management(describePatchIDsRaster.SpatialReference).getOutput(0).split(';')[0]
        patchCoverRasterCS = gp.CreateSpatialReference_management(describePatchCoverRaster.SpatialReference).getOutput(0).split(';')[0]
        waterMaskRasterCS = gp.CreateSpatialReference_management(describeWaterMaskRaster.SpatialReference).getOutput(0).split(';')[0]

        if patchCoverRasterCS.lower() != patchIDsRasterCS.lower():
            Logger.RaiseException(ValueError(_('The patch cover raster %(raster1)s uses a different coordinate system than the patch IDs raster, %(raster2)s. Please project the patch cover raster to the patch IDs raster\'s coordinate system and try again.') % {'raster1': patchCoverRaster, 'raster2': patchIDsRaster}))
        if waterMaskRasterCS.lower() != patchIDsRasterCS.lower():
            Logger.RaiseException(ValueError(_('The water mask raster %(raster1)s uses a different coordinate system than the patch IDs raster, %(raster2)s. Please project the water mask raster to the patch IDs raster\'s coordinate system and try again.') % {'raster1': waterMaskRaster, 'raster2': patchIDsRaster}))

        patchIDsRasterLeft, patchIDsRasterBottom, patchIDsRasterRight, patchIDsRasterTop = EnvelopeTypeMetadata.ParseFromArcGISString(describePatchIDsRaster.Extent)
        patchCoverRasterLeft, patchCoverRasterBottom, patchCoverRasterRight, patchCoverRasterTop = EnvelopeTypeMetadata.ParseFromArcGISString(describePatchCoverRaster.Extent)
        waterMaskRasterLeft, waterMaskRasterBottom, waterMaskRasterRight, waterMaskRasterTop = EnvelopeTypeMetadata.ParseFromArcGISString(describeWaterMaskRaster.Extent)

        if abs(patchCoverRasterLeft - patchIDsRasterLeft) > 0.001 or abs(patchCoverRasterBottom - patchIDsRasterBottom) > 0.001 or abs(patchCoverRasterRight - patchIDsRasterRight) > 0.001 or abs(patchCoverRasterTop - patchIDsRasterTop) > 0.001 or abs(describePatchCoverRaster.MeanCellWidth - describePatchIDsRaster.MeanCellWidth) > 0.001 or abs(describePatchCoverRaster.MeanCellHeight - describePatchIDsRaster.MeanCellHeight) > 0.001:
            Logger.RaiseException(ValueError(_('The patch cover raster %(raster1)s has a different extent or cell size than the patch IDs raster, %(raster2)s. Please prepare a patch cover raster that has the same extent and cell size as the patch IDs raster and try again.') % {'raster1': patchCoverRaster, 'raster2': patchIDsRaster}))
        if abs(waterMaskRasterLeft - patchIDsRasterLeft) > 0.001 or abs(waterMaskRasterBottom - patchIDsRasterBottom) > 0.001 or abs(waterMaskRasterRight - patchIDsRasterRight) > 0.001 or abs(waterMaskRasterTop - patchIDsRasterTop) > 0.001 or abs(describeWaterMaskRaster.MeanCellWidth - describePatchIDsRaster.MeanCellWidth) > 0.001 or abs(describeWaterMaskRaster.MeanCellHeight - describePatchIDsRaster.MeanCellHeight) > 0.001:
            Logger.RaiseException(ValueError(_('The water mask raster %(raster1)s has a different extent or cell size than the patch IDs raster, %(raster2)s. Please prepare a water mask raster that has the same extent and cell size as the patch IDs raster and try again.') % {'raster1': patchCoverRaster, 'raster2': waterMaskRaster}))

        # Validate that 0 is not used as a patch ID. The MATLAB code
        # uses 0 to represent cells where no patches are present.

        import numpy

        tempDir = TemporaryDirectory()
        patchIDsImage, patchIDsNoDataValue = ArcGISRaster2.ToNumpyArray(patchIDsRaster)
        if numpy.any(patchIDsImage == 0) and patchIDsNoDataValue != 0:
            Logger.RaiseException(ValueError(_('The patch IDs raster %(raster)s uses 0 as a patch ID. This is not allowed.  Please remove the value 0 from the patch IDs raster and try again.')  % {'raster': patchIDsRaster}))

        # Validate that patch cover raster ranges between 0.0 and 1.0.

        patchCoverImage, noDataValue = ArcGISRaster2.ToNumpyArray(patchCoverRaster)
        if noDataValue is not None:
            patchCoverImage[Grid.numpy_equal_nan(patchCoverImage, noDataValue)] = 0
        if numpy.any(patchCoverImage < 0) or numpy.any(patchCoverImage > 1):
            Logger.RaiseException(ValueError(_('The patch cover raster %(raster)s includes values that are less than 0 or are greater than 1. The values of a cell of this raster is supposed to represent the proportion of the cell\'s area that is occupied by suitable habitat, thus the value is supposed to be between 0 and 1. Please prepare a raster that has the correct values and try again.')  % {'raster': patchCoverRaster}))

        # Create the simulation directory and the PatchData
        # subdirectory.

        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Creating and initializing the simulation directory %(dir)s...') % {'dir': simulationDirectory})
        Logger.SetLogInfoAsDebug(True)
        try:
            Directory.Create(simulationDirectory)
            Directory.Create(os.path.join(simulationDirectory, 'PatchData'))

            # Copy the patch IDs raster into the PatchData directory.

            ArcGISRaster2.Copy(patchIDsRaster, os.path.join(simulationDirectory, 'PatchData', 'patch_ids.img'))

            # Copy the patch cover raster into the PatchData directory,
            # setting the NoData values and non-patch cells to 0 in the
            # process.

            import arcpy.sa

            r1 = arcpy.sa.Raster(patchCoverRaster)
            r2 = arcpy.sa.Raster(patchIDsRaster)
            r3 = arcpy.sa.Raster(waterMaskRaster)

            r4 = arcpy.sa.Con(arcpy.sa.IsNull(r1) | arcpy.sa.IsNull(r2), 0.0, r1)
            r4.save(os.path.join(simulationDirectory, 'PatchData', 'patch_areas.img'))

            # Copy the water mask raster into the PatchData directory,
            # normalizing it to integer values where 1 is water, 0 is land.

            r5 = arcpy.sa.Con(arcpy.sa.IsNull(r3) | r3 == 0, 0, 1)
            r5.save(os.path.join(simulationDirectory, 'PatchData', 'water_mask.img'))

            # Create the patch_geometry file by calling Spatial Analyst's
            # Zonal Geometry As Table tool. (Note that this tool will create
            # a .dbf file no matter what, even if we give it a .csv or .txt
            # extension. This is very annoying, because we can't read it
            # easily without going through a database API, which is slow.)

            arcpy.sa.ZonalGeometryAsTable(os.path.join(simulationDirectory, 'PatchData', 'patch_ids.img'), 'Value', os.path.join(simulationDirectory, 'PatchData', 'patch_geometry.dbf'), describePatchIDsRaster.MeanCellWidth)

            # Create the directories that will hold the currents rasters.

            Directory.Create(os.path.join(simulationDirectory, 'Currents'))
            Directory.Create(os.path.join(simulationDirectory, 'Currents', 'u'))
            Directory.Create(os.path.join(simulationDirectory, 'Currents', 'v'))

            # Create the config file that stores properties of the
            # simulation.

            scp = ConfigParser()
            scp.add_section('Simulation')
            scp.set('Simulation', 'Crosses180', str(crosses180))
            scp.set('Simulation', 'CurrentsLoaded', str(False))
            scp.set('Simulation', 'CurrentsProduct', '')
            with open(os.path.join(simulationDirectory, 'Simulation.ini'), 'w') as f:
                scp.write(f)

        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def LoadCMEMSCurrentsIntoSimulation(cls, simulationDirectory, startDate, endDate, username, password, datasetID='cmems_mod_glo_phy_my_0.083deg_P1D-m', depth=0.49402499198913574, rotationOffset=None, resamplingTechnique='CUBIC', interpolationMethod=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Parse and validate the Simulation.ini file.

        scp, crosses180, currentsLoaded, currentsProduct = cls._ReadCurrentsInfoFromSimulationINI(simulationDirectory)

        # If the simulation already has currents loaded in it from a different
        # product, report an error.

        thisCurrentsProduct = 'CMEMS %s %r m (resampling=%s, interpolation=%s)' % (datasetID, depth, resamplingTechnique.lower(), interpolationMethod.lower())

        if currentsLoaded and currentsProduct != thisCurrentsProduct:
            Logger.RaiseException(ValueError(_('Cannot load %(prod1)s currents data into the simulation in directory %(dir)s because that simulation already has %(prod2)s currents data loaded into it. You can load additional %(prod2)s data, if you like, but to use %(prod1)s data, you must create a new simulation.') % {'dir': simulationDirectory, 'prod1': thisCurrentsProduct, 'prod2': currentsProduct}))

        # First, log some helpful information about this dataset.

        grid = CMEMSARCOArray(username=username, password=password, datasetID=datasetID, variableShortName='uo')

        if grid.Dimensions != 'tzyx':
            raise ValueError(_('CMEMS dataset %(datasetID)s has the dimensions "%(dim)s". It must have the dimensions "tzyx". Please check the Copernicus website and select 4D ocean currents dataset.') % {'datasetID': datasetID, 'dim': grid.Dimensions})

        Logger.Info(_('CMEMS dataset %(datasetID)s has a cell size of %(cellSize)r and a temporal resolution of %(TIncrement)g %(TIncrementUnit)ss') % {'datasetID': datasetID, 'cellSize': grid.GetLazyPropertyValue('CoordIncrements')[-1], 'TIncrement': grid.GetLazyPropertyValue('TIncrement'), 'TIncrementUnit': grid.GetLazyPropertyValue('TIncrementUnit')})
        Logger.Info(_('The spatial extent is: left = %(left)r, right = %(right)r, bottom = %(bottom)r, top = %(top)r') % {'left': float(grid.MinCoords['x', 0]), 'right': float(grid.MaxCoords['x', -1]), 'bottom': float(grid.MinCoords['y', 0]), 'top': float(grid.MaxCoords['y', -1])})
        Logger.Info(_('The first time slice starts on %(first)s, the last slice starts on %(last)s') % {'first': grid.MinCoords['t', 0].strftime('%Y-%m-%d %H:%M:%S'), 'last': grid.MinCoords['t', -1].strftime('%Y-%m-%d %H:%M:%S')})
        Logger.Info(_('The vertical layers of this dataset have the depths: %(depths)s') % {'depths': ', '.join(repr(float(depth)) for depth in grid.CenterCoords['z',:])})

        # Now download and create CMEMS current rasters in a CMEMS-specific
        # directory. These will have the CMEMS projection, extent, and cell
        # size. We still need to project them to the simulation's projection,
        # extent, and cell size.

        currentsDirectory = os.path.join(simulationDirectory, 'OriginalCMEMSCurrents')
        Directory.Create(currentsDirectory)

        CMEMSARCOArray.CreateArcGISRasters(username=username, password=password, datasetID=datasetID, variableShortName='uo', outputWorkspace=currentsDirectory,
                                           rotationOffset=rotationOffset, minDepth=depth, maxDepth=depth, startDate=startDate, endDate=endDate,
                                           rasterNameExpressions=['u', '%%Y', 'u%%Y%%m%%d_%%H%%M.img'])

        CMEMSARCOArray.CreateArcGISRasters(username=username, password=password, datasetID=datasetID, variableShortName='vo', outputWorkspace=currentsDirectory,
                                           rotationOffset=rotationOffset, minDepth=depth, maxDepth=depth, startDate=startDate, endDate=endDate,
                                           rasterNameExpressions=['v', '%%Y', 'v%%Y%%m%%d_%%H%%M.img'])

        # Record in the Simulation.ini file that we downloaded some currents
        # and then project, snap, and clip them to the projection, extent,
        # and cell size of the patch IDs raster.

        maxSecondsBetweenCurrentsImages = (grid.MinCoords['t', 1] - grid.MinCoords['t', 0]).total_seconds()

        cls._FinishLoadingCurrents(simulationDirectory, scp, thisCurrentsProduct, 'Center', maxSecondsBetweenCurrentsImages, currentsDirectory, resamplingTechnique, interpolationMethod)

        # Return successfully.

        return simulationDirectory


    @classmethod
    def _FinishLoadingCurrents(cls, simulationDirectory, scp, currentsProduct, currentsDateType, maxSecondsBetweenCurrentsImages, originalCurrentsDirectory, resamplingTechnique, interpolationMethod):

        # Write the Simulation.ini file, so that any new rasters
        # loaded into the simulation must be from the same product and
        # depth.
            
        scp.set('Simulation', 'CurrentsLoaded', str(True))
        scp.set('Simulation', 'CurrentsProduct', currentsProduct)
        scp.set('Simulation', 'CurrentsDateType', currentsDateType)
        scp.set('Simulation', 'MaxSecondsBetweenCurrentsImages', repr(maxSecondsBetweenCurrentsImages))
        with open(os.path.join(simulationDirectory, 'Simulation.ini'), 'w') as f:
            scp.write(f)

        # Create a temporary copy of the water mask with land set to No Data.

        import arcpy.sa

        r1 = arcpy.sa.Raster(os.path.join(simulationDirectory, 'PatchData', 'water_mask.img'))
        r2 = arcpy.sa.SetNull(r1 == 0, r1)

        tempDir = TemporaryDirectory()
        newWaterMask = os.path.join(tempDir.Path, 'water_mask.img')
        r2.save(newWaterMask)

        # Using the new water mask as a template, project and clip the current
        # rasters to the patch rasters' coordinate system, cell size, and
        # extent.

        ArcGISRaster2.FindAndProjectRastersToTemplate(inputWorkspace=originalCurrentsDirectory,
                                                      outputWorkspace=os.path.join(simulationDirectory, 'Currents'),
                                                      templateRaster=newWaterMask,
                                                      resamplingTechnique=resamplingTechnique,
                                                      wildcard='*.img',
                                                      searchTree=True,
                                                      interpolationMethod=interpolationMethod,
                                                      mask=True,
                                                      outputRasterPythonExpression='os.path.join(outputWorkspace, inputRaster[len(workspaceToSearch)+1:])',
                                                      modulesToImport=['os'],
                                                      skipExisting=True)

    @classmethod
    def _ReadCurrentsInfoFromSimulationINI(cls, simulationDirectory):
        if not os.path.isfile(os.path.join(simulationDirectory, 'Simulation.ini')):
            Logger.RaiseException(ValueError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: it does not contain a file called Simulation.ini. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory}))

        scp = ConfigParser()
        try: 
            scp.read([os.path.join(simulationDirectory, 'Simulation.ini')])
        except:
            Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: the file Simulation.ini in that directory could not be parsed. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory})
            raise

        try:
            crosses180 = scp.getboolean('Simulation', 'Crosses180')
        except:
            Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse a boolean option named Crosses180 from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory})
            raise

        try:
            currentsLoaded = scp.getboolean('Simulation', 'CurrentsLoaded')
        except:
            Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse a boolean option named CurrentsLoaded from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory})
            raise

        try:
            currentsProduct = str(scp.get('Simulation', 'CurrentsProduct'))
        except:
            Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse a string option named CurrentsProduct from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory})
            raise

        return scp, crosses180, currentsLoaded, currentsProduct

    @classmethod
    def RunSimulation2012(cls, simulationDirectory, resultsDirectory, startDate, duration, simulationTimeStep=1.0, summarizationPeriod=24, a=None, b=None, settlementRate=0.80, useSensoryZone=False, sourcePatchIDs=None, destPatchIDs=None, excludePatchIDs=None, diffusivity=50.0, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Check for existing outputs.

        resultsFile = os.path.join(resultsDirectory, 'Results.pickle')
        parametersINIFile = os.path.join(resultsDirectory, 'Parameters.ini')
        competencyCurveFile = os.path.join(resultsDirectory, 'CompetencyCurve.png')

        for outputFile in [resultsFile, parametersINIFile, competencyCurveFile]:
            if os.path.isfile(outputFile):
                if not overwriteExisting:
                    raise ValueError(_('The output file "%(output)s" already exists. Please delete the file and try again. If you are running this tool from ArcGIS, you can enable the Overwrite Outputs option and the file will be deleted automatically.') % {'output': outputFile})
                File.DeleteSilent(outputFile)

        # If the caller did not supply a or b, use values that will make the
        # larvae immediately competent.

        if a is None or b is None:
            if a is not None or b is not None:
                Logger.Warning(_('For competency to be used, the gamma a and b parameters must both be specified. Only one was specified. Because one was missing, competency will not be used and the tool will assume that the larvae should be immediately competent.'))
            a = 1e-30
            b = 1.

        # Validate the sourcePatchIDs, destPatchIDs, and excludePatchIDs.

        if sourcePatchIDs is not None and excludePatchIDs is not None and len(set(sourcePatchIDs).intersection(set(excludePatchIDs))) > 0:
            Logger.RaiseException(ValueError(_('At least one patch appears in both the list of Patches That Disperse Larvae and the list of Excluded Patches. This is not allowed. Please edit the lists so that the following patches only appear in list one or the other: %(IDs)s') % {'IDs': ', '.join([str(patchID) for patchID in set(sourcePatchIDs).intersection(set(excludePatchIDs))])}))

        if destPatchIDs is not None and excludePatchIDs is not None and len(set(destPatchIDs).intersection(set(excludePatchIDs))) > 0:
            Logger.RaiseException(ValueError(_('At least one patch appears in both the list of Patches That Larvae Can Settle On and the list of Excluded Patches. This is not allowed. Please edit the lists so that the following patches only appear in list one or the other: %(IDs)s') % {'IDs': ', '.join([str(patchID) for patchID in set(destPatchIDs).intersection(set(excludePatchIDs))])}))

        table = ArcGISTable(os.path.join(simulationDirectory, 'PatchData', 'patch_geometry.dbf'))
        patchIDs = table.Query(fields=['VALUE'], reportProgress=False)['VALUE']
        patchIDs.sort()

        if len(patchIDs) <= 0:
            Logger.RaiseException(ValueError(_('The patch data in simulation directory %(dir)s does not contain any patches. Please recreate the simulation using input rasters that contain at least one patch.') % {'dir': simulationDirectory}))

        if sourcePatchIDs is not None and len(set(sourcePatchIDs) - set(patchIDs)) > 0:
            existingPatchIDs = list(set(sourcePatchIDs).intersection(set(patchIDs)))
            if len(existingPatchIDs) <= 0:
                Logger.RaiseException(ValueError(_('None of the patches listed as Patches That Disperse Larvae exist in this simulation. Please edit the list to include existing patches.')))
            
            Logger.Warning(_('The following patch IDs, listed as Patches That Disperse Larvae, do not exist. These patch IDs will be ignored: %(IDs)s') % {'IDs': ', '.join([str(patchID) for patchID in set(sourcePatchIDs) - set(patchIDs)])})
            sourcePatchIDs = existingPatchIDs

        elif sourcePatchIDs is None:
            if excludePatchIDs is not None:
                sourcePatchIDs = list(set(patchIDs) - set(excludePatchIDs))
            else:
                sourcePatchIDs = patchIDs

        if destPatchIDs is not None and len(set(destPatchIDs) - set(patchIDs)) > 0:
            existingPatchIDs = list(set(destPatchIDs).intersection(set(patchIDs)))
            if len(existingPatchIDs) <= 0:
                Logger.RaiseException(ValueError(_('None of the patches listed as Patches That Larvae Can Settle On exist in this simulation. Please edit the list to include existing patches.')))
            
            Logger.Warning(_('The following patch IDs, listed as Patches That Larvae Can Settle On, do not exist. These patch IDs will be ignored: %(IDs)s') % {'IDs': ', '.join([str(patchID) for patchID in set(destPatchIDs) - set(patchIDs)])})
            destPatchIDs = existingPatchIDs

        elif destPatchIDs is None:
            if excludePatchIDs is not None:
                destPatchIDs = list(set(patchIDs) - set(excludePatchIDs))
            else:
                destPatchIDs = patchIDs

        if excludePatchIDs is not None and len(set(excludePatchIDs) - set(patchIDs)) > 0:
            Logger.Warning(_('The following patch IDs, listed as Excluded Patches, do not exist. These patch IDs will be ignored: %(IDs)s') % {'IDs': ', '.join([str(patchID) for patchID in set(excludePatchIDs) - set(patchIDs)])})

        # Ensure that both a and b are provided or neither are provided.

        if a is None and b is not None or a is not None and b is None:
            Logger.RaiseException(ValueError(_('Either both the Gamma Competency A and Gamma Competency B parameters must be provided, or neither provided. Please provide both, or provide neither.')))

        # Read the Simulation.ini file, the patch rasters, the current
        # rasters, etc.

        describePatchIDsRaster, patchIDsImage, patchCoverImage, waterMaskImage, waterMaskNoDataValue, uImages, vImages, uvIndexForTimestep, cellSize, maxSecondsBetweenCurrentsImages, currentsStartDate = cls._PrepareToRunSimulation(simulationDirectory, duration, simulationTimeStep, startDate)

        waterMaskImage[Grid.numpy_equal_nan(waterMaskImage, waterMaskNoDataValue)] = 0

        # Start MATLAB and run the simulation. Because the simulation is
        # likely to run for a long time and require a lot of memory, we start
        # our own MatlabWorkerProcess and ensure it exits when we are done,
        # rather than using SharedMatlabWorkerProcess, which might stick
        # around and hold memory that is no longer needed.

        import numpy

        Logger.Info('Preparing to run the larval dispersal simulation.')

        with MatlabWorkerProcess() as matlab:
            (competencyCurve, 
             dispersalMatrix, 
             settledDensityMatrix, 
             suspendedDensityMatrix, 
             metadata) = matlab.DisperseLarvae2012(    # Note: it seems we can't use keyword arguments below (except nargout)
                'A',
                startDate,
                duration,
                simulationTimeStep / 24.,    # Convert from hours to days
                summarizationPeriod,
                a,
                b,
                settlementRate,
                useSensoryZone,
                diffusivity,
                numpy.array(sourcePatchIDs, dtype="uint16"),
                numpy.array(destPatchIDs, dtype="uint16"),
                numpy.array(patchIDsImage, dtype="uint16"),
                patchCoverImage,
                waterMaskImage,
                cellSize,
                uImages,
                vImages,
                numpy.array([]),
                numpy.array([]),
                currentsStartDate,
                maxSecondsBetweenCurrentsImages / 86400.,    # Convert from seconds to days
                nargout=5     # This is a required keyword argument; if we omit it, only the first output will be returned.
            )

        # MATLAB returns some things as 2D arrays that should actually have
        # fewer dimensions. Flatten them.

        competencyCurve = competencyCurve.flatten()

        for key in metadata:
            if isinstance(metadata[key], numpy.ndarray):
                metadata[key] = metadata[key].flatten().tolist()

        # The MATLAB code that produces the competencyCurve creates that array
        # starting at t=1, i.e. after one time step has elapsed. Prepend an
        # element for t=0, when the larvae have just been released. If
        # competency is 1 at t=1, it indicates that compentency was not used
        # for the simulation. In this case, use 1 for t=0. Otherwise
        # (if competency was used), use 0 for t=0.

        if competencyCurve[0] == 1:
            competencyCurve = numpy.insert(competencyCurve, 0, 1)
        else:
            competencyCurve = numpy.insert(competencyCurve, 0, 0)

        # Write the Parameters.ini file.

        scp = ConfigParser()
        scp.add_section('Parameters')
        scp.add_section('Results')

        for key in sorted(metadata.keys()):
            section = 'Parameters' if key in ['cellSize', 'competencyGammaA', 'competencyGammaB', 'currentsTimeStep', 'destIDs', 'diffusivity', 'releaseDate', 'releaseModel', 'settlementRate', 'simulationDuration', 'simulationTimeStep', 'sourceIDs', 'summarizationPeriod', 'useSensoryZone'] else 'Results'
            value = repr(metadata[key]) if not isinstance(metadata[key], numpy.ndarray) else repr(metadata[key].flatten().tolist())
            scp.set(section, key, value)

        with open(parametersINIFile, 'w') as f:
            scp.write(f)

        # Write the competency plot.

        figSize = (4., 2.5)
        dpi = 1000.
        fontSize = 10.

        import numpy
        import matplotlib
        import matplotlib.pyplot as plt

        matplotlib.rcParams.update({'font.size': fontSize})
        
        fig = plt.figure(figsize=figSize, dpi=dpi)
        try:
            ax = fig.add_subplot(111)
            days = numpy.arange(len(competencyCurve)) * simulationTimeStep / 24
            ax.plot(days, competencyCurve, 'k')
            ax.set_xlabel('Elapsed time (days)')
            ax.set_ylabel('Competency')
            ax.set_ylim([-0.03,1.03])
            ax.set_xlim([0-max(days)*0.03,max(days)*1.03])
            ax.grid(True, which='major', linewidth=0.3, alpha=0.25)
            plt.tight_layout()
            plt.savefig(competencyCurveFile, dpi=dpi)
        finally:
            plt.close(fig)

        # Write the results file.

        with open(resultsFile, 'wb') as f:
            pickle.dump([competencyCurve, dispersalMatrix, settledDensityMatrix, suspendedDensityMatrix, metadata], f)

        # Return successfully.

        return resultsDirectory

    @classmethod
    def _PrepareToRunSimulation(cls, simulationDirectory, duration, simulationTimeStep, startDate):

        # Parse and validate the Simulation.ini file.

        if not os.path.isfile(os.path.join(simulationDirectory, 'Simulation.ini')):
            Logger.RaiseException(ValueError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: it does not contain a file called Simulation.ini. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory}))

        scp = ConfigParser()

        with open(os.path.join(simulationDirectory, 'Simulation.ini'), 'r') as f:
            try: 
                scp.read([os.path.join(simulationDirectory, 'Simulation.ini')])
            except:
                Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: the file Simulation.ini in that directory could not be parsed. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory})
                raise

            try:
                crosses180 = scp.getboolean('Simulation', 'Crosses180')
            except:
                Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse a boolean option named Crosses180 from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory})
                raise

            try:
                currentsLoaded = scp.getboolean('Simulation', 'CurrentsLoaded')
            except:
                Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse a boolean option named CurrentsLoaded from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool and try again.') % {'dir': simulationDirectory})
                raise
            if not currentsLoaded:
                Logger.RaiseException(ValueError(_('The larval dispersal simulation in directory %(dir)s does not contain any ocean currents data. Please load ocean currents into it using a tool designed for this purpose, and try again.') % {'dir': simulationDirectory}))

            try:
                currentsProduct = str(scp.get('Simulation', 'CurrentsProduct'))
            except:
                Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse a string option named CurrentsProduct from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool, load ocean currents into it using a tool designed for this purpose, and try again.') % {'dir': simulationDirectory})
                raise

            try:
                currentsDateType = str(scp.get('Simulation', 'CurrentsDateType'))
            except:
                Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse a string option named CurrentsProduct from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool, load ocean currents into it using a tool designed for this purpose, and try again.') % {'dir': simulationDirectory})
                raise
            if currentsDateType.lower() not in ['center']:
                Logger.RaiseException(ValueError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: the CurrentsDataType option in the Simulation.ini file has the unknown value %(val)s. Please create a simulation directory using the Create Larval Dispersal Simulation tool, load ocean currents into it using a tool designed for this purpose, and try again.') % {'dir': simulationDirectory, 'val': currentsDateType}))

            try:
                maxSecondsBetweenCurrentsImages = scp.getfloat('Simulation', 'MaxSecondsBetweenCurrentsImages')
            except:
                Logger.LogExceptionAsError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: failed to parse an integer option named MaxSecondsBetweenCurrentsImages from the file Simulation.ini in that directory. Please create a simulation directory using the Create Larval Dispersal Simulation tool, load ocean currents into it using a tool designed for this purpose, and try again.') % {'dir': simulationDirectory})
                raise
            if maxSecondsBetweenCurrentsImages <= 0:
                Logger.RaiseException(ValueError(_('The directory %(dir)s does not appear to be a properly-initialized larval dispersal simulation directory: the MaxSecondsBetweenCurrentsImages option in the Simulation.ini file is less than or equal to zero. It must be greater than zero. Please create a simulation directory using the Create Larval Dispersal Simulation tool, load ocean currents into it using a tool designed for this purpose, and try again.') % {'dir': simulationDirectory}))

        # Validate other input parameters.

        if duration - simulationTimeStep/24 <= 0:
            Logger.RaiseException(ValueError(_('The time step must be shorter than or equal to the simulation duration.')))

        # Build lists of the currents rasters that are loaded into the
        # simulation, and validate that we have currents for the start date
        # and duration specified by the caller.

        uRasters = glob.glob(os.path.join(simulationDirectory, 'Currents', 'u', '*', 'u[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9].img'))
        uRasters.sort()
        vRasters = glob.glob(os.path.join(simulationDirectory, 'Currents', 'v', '*', 'v[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9].img'))
        vRasters.sort()

        if len(uRasters) <= 0:
            Logger.RaiseException(ValueError(_('The larval dispersal simulation in directory %(dir)s does not contain any ocean currents data. Please load ocean currents into it using a tool designed for this purpose, and try again.') % {'dir': simulationDirectory}))
        if len(uRasters) != len(vRasters):
            Logger.RaiseException(ValueError(_('The ocean currents data in the larval dispersal simulation in directory %(dir)s appears to be incompletely loaded. The number of "" rasters does not equal the number of "v" rasters, indicating that the load operation did not complete successfully. Please try loading ocean currents again, and then try to run the simulation.') % {'dir': simulationDirectory}))

        rasterDates = []

        for i in range(len(uRasters)):
            uRasterName = os.path.basename(uRasters[i])
            if uRasterName[1:] != os.path.basename(vRasters[i])[1:]:
                Logger.RaiseException(ValueError(_('The ocean currents data in the larval dispersal simulation in directory %(dir)s appears to be incompletely loaded. The "" raster %(r1)s could not be matched up with a "v" raster with the same date (the next available "v" raster is %(r2)s). Please try loading ocean currents again, and then try to run the simulation.') % {'dir': simulationDirectory, 'r1': uRasters[i], 'r2': vRasters[i]}))
            rasterDates.append(datetime.datetime(int(uRasterName[1:5]), int(uRasterName[5:7]), int(uRasterName[7:9]), int(uRasterName[10:12]), int(uRasterName[12:14]), 0))

        if currentsDateType.lower() == 'center':
            currentsDateStartDelta = datetime.timedelta(seconds=maxSecondsBetweenCurrentsImages / 2)
            currentsDateEndDelta = datetime.timedelta(seconds=maxSecondsBetweenCurrentsImages / 2)
        else:
            Logger.RaiseException(NotImplementedError(_('This tool does not currently support a CurrentsDateType of "%(type)s". Please contact the author of this tool for assistance.') % {'type': currentsDateType}))

        if startDate < rasterDates[0] - currentsDateStartDelta:
            Logger.RaiseException(ValueError(_('The start date of the simulation (%(start)s) occurs too far before the date of the first ocean currents image (%(date)s) that is loaded in the larval dispersal simulation in directory %(dir)s. To fix this problem, either move the start date forward or load some older ocean currents data into the simulation, so that the start date matches up with the currents data.') % {'dir': simulationDirectory, 'start': str(startDate), 'date': str(rasterDates[0])}))

        if startDate > rasterDates[-1] + currentsDateEndDelta:
            Logger.RaiseException(ValueError(_('The start date of the simulation (%(start)s) occurs too far after the date of the last ocean currents image (%(date)s) that is loaded in the larval dispersal simulation in directory %(dir)s. To fix this problem, either move the start date backward or load some more recent ocean currents data into the simulation, so that the start date matches up with the currents data.') % {'dir': simulationDirectory, 'start': str(startDate), 'date': str(rasterDates[-1])}))

        endDate = startDate + datetime.timedelta(days=duration)

        if endDate > rasterDates[-1] + currentsDateEndDelta:
            Logger.RaiseException(ValueError(_('The end date of the simulation (%(end)s) occurs too far after the date of the last ocean currents image (%(date)s) that is loaded in the larval dispersal simulation in directory %(dir)s. To fix this problem, either move the start date backward, reduce the duration of the simulation, or load some more recent ocean currents data into the simulation, so that the end date matches up with the currents data.') % {'dir': simulationDirectory, 'end': str(endDate), 'date': str(rasterDates[-1])}))

        startRasterIndex = 0
        while startDate > rasterDates[startRasterIndex] + currentsDateEndDelta:
            startRasterIndex += 1

        endRasterIndex = startRasterIndex
        while endDate > rasterDates[endRasterIndex] + currentsDateEndDelta:
            endRasterIndex += 1
            if rasterDates[endRasterIndex] - rasterDates[endRasterIndex-1] > datetime.timedelta(seconds=maxSecondsBetweenCurrentsImages):
                Logger.RaiseException(ValueError(_('The ocean currents data that is loaded in the larval dispersal simulation in directory %(dir)s has a data gap in the range of dates between the simulation start date (%(start)s) and end date (%(end)s). A gap of %(gap)s occurs between %(d1)s and %(d2)s, which is larger than the maximum time permitted between images (%(max)s) for %(prod)s data. To fix this problem, either adjust the start date or duration, or load ocean currents data into the simulation that fills the gap.') % {'dir': simulationDirectory, 'start': str(startDate), 'end': str(endDate), 'gap': str(rasterDates[endRasterIndex] - rasterDates[endRasterIndex-1]), 'd1': rasterDates[endRasterIndex-1], 'd2': rasterDates[endRasterIndex], 'max': datetime.timedelta(seconds=maxSecondsBetweenCurrentsImages), 'prod': currentsProduct}))

        # Read the patch rasters into 2D numpy arrays.

        Logger.Info(_('Reading habitat patch data...'))

        patchIDsImage, patchIDsNoDataValue = ArcGISRaster2.ToNumpyArray(os.path.join(simulationDirectory, 'PatchData', 'patch_ids.img'))
        patchIDsNoDataValue = int(patchIDsNoDataValue)
        patchCoverImage = ArcGISRaster2.ToNumpyArray(os.path.join(simulationDirectory, 'PatchData', 'patch_areas.img'))[0]
        waterMaskImage, waterMaskNoDataValue = ArcGISRaster2.ToNumpyArray(os.path.join(simulationDirectory, 'PatchData', 'water_mask.img'))

        # Read the ocean currents into parallel lists of 2D numpy arrays.

        import numpy

        imagesToRead = (endRasterIndex - startRasterIndex + 1) * 2
        Logger.Info(_('Reading %i ocean currents images...') % imagesToRead)
        progressReporter = ProgressReporter(progressMessage1=_('Still reading: %(elapsed)s elapsed, %(opsCompleted)i images read, %(perOp)s per image, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                            completionMessage=_('Finished reading: %(elapsed)s elapsed, %(opsCompleted)i images read, %(perOp)s per image.'))
        progressReporter.Start(imagesToRead)

        uImageList = []
        vImageList = []
        uvDateList = []

        i = startRasterIndex
        while i >= startRasterIndex and i <= endRasterIndex:
            imageDate = rasterDates[i]
            uvDateList.append(imageDate)
            
            image, noDataValue = ArcGISRaster2.ToNumpyArray(os.path.join(simulationDirectory, 'Currents', 'u', str(imageDate.year), imageDate.strftime('u%Y%m%d_%H%M.img')))
            image[Grid.numpy_equal_nan(image, noDataValue)] = numpy.nan
            uImageList.append(image)
            progressReporter.ReportProgress()
            
            image, noDataValue = ArcGISRaster2.ToNumpyArray(os.path.join(simulationDirectory, 'Currents', 'v', str(imageDate.year), imageDate.strftime('v%Y%m%d_%H%M.img')))
            image[Grid.numpy_equal_nan(image, noDataValue)] = numpy.nan
            vImageList.append(image)
            progressReporter.ReportProgress()
            
            i += 1

        # Stack the numpy arrays into two 3D arrays that we will pass to the
        # MATLAB function.
        #
        # Note that with numpy, it appears that 2D arrays are traditionally
        # indexed [y,x] but that 3D arrays are [y,x,t]. This is what is
        # output by numpy's dstack function. This is kind of screwy, because
        # when you print a 3D numpy array, it looks much better if ordered
        # [t,y,x] than [y,x,t]. But MATLAB was the inspiration for numpy and
        # [y,x,t] is traditional in MATLAB as well. Finally, Eric Treml's
        # original MATLAB code used [y,x,z].

        uImages = numpy.dstack(tuple(uImageList))
        del uImageList
        
        vImages = numpy.dstack(tuple(vImageList))
        del vImageList

        # Build a list that specifies the t index into the 3D arrays for each
        # time step. Note that when we pass this list to MATLAB, we must
        # increment all of the indices by 1, because MATLAB uses 1-based
        # indexing (Python uses 0-based).

        numTimeSteps = int(math.ceil(duration / (simulationTimeStep/24)))
        uvIndexForTimestep = [0]
        for i in range(1, numTimeSteps):
            if startDate + datetime.timedelta(hours=simulationTimeStep*i) <= uvDateList[uvIndexForTimestep[-1]] + currentsDateEndDelta:
                uvIndexForTimestep.append(uvIndexForTimestep[-1])
            else:
                uvIndexForTimestep.append(uvIndexForTimestep[-1] + 1)

        # Look up the cell size of the rasters.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        describePatchIDsRaster = gp.Describe(os.path.join(simulationDirectory, 'PatchData', 'patch_ids.img'))
        cellSize = describePatchIDsRaster.MeanCellWidth

        # Return successfully.

        return describePatchIDsRaster, patchIDsImage, patchCoverImage, waterMaskImage, waterMaskNoDataValue, uImages, vImages, uvIndexForTimestep, cellSize, maxSecondsBetweenCurrentsImages, uvDateList[0] - currentsDateStartDelta

    @classmethod
    def VisualizeResults2012(cls, simulationDirectory, resultsDirectory, outputGDBName, mortalityRate=None, mortalityMethod='A', createDensityRasters=True, minimumDensity=0.00001, useCompetencyForDensityRasters=False, createConnectionsFeatureClass=True, minimumDispersal=0.00001, minimumDispersalType='Quantity', overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additinal validation.

        if not createDensityRasters and not createConnectionsFeatureClass:
            Logger.Warning(_('You requested that neither density rasters nor a connections feature class be generated. There is nothing to do. An output geodatabase was not created.'))
            return outputDirectory

        resultsFile = os.path.join(resultsDirectory, 'Results.pickle')
        if not os.path.isfile(resultsFile):
            raise ValueError(_('The file Results.pickle does not exist in the results directory "%(dir)s". Did you run the simulation yet?') % {'dir': resultsDirectory})

        if not outputGDBName.lower().endswith('.gdb'):
            outputGDBName = outputGDBName + '.gdb'

        # Read the Results.pickle.

        Logger.Info(_('Reading the simulation results from %s.') % resultsFile)

        with open(resultsFile, 'rb') as f:
            competencyCurve, dispersalMatrix, settledDensityMatrix, suspendedDensityMatrix, metadata = pickle.load(f)

        # If the caller provided a mortality rate, compute the fraction of
        # larvae that will be alive at each summarization step of the
        # simulation.

        if mortalityRate is not None:
            fractionAlive = cls._ComputeFractionAlive(mortalityMethod, mortalityRate, metadata, dispersalMatrix.shape[-1])

            # Also create a plot of the survivorship curve in the results
            # directory.

            outputPNG = os.path.join(resultsDirectory, os.path.splitext(outputGDBName)[0] + '_SurvivorshipCurve.png')

            figSize = (4., 2.5)
            dpi = 1000.
            fontSize = 10.

            import numpy
            import matplotlib
            import matplotlib.pyplot as plt

            matplotlib.rcParams.update({'font.size': fontSize})
            
            fig = plt.figure(figsize=figSize, dpi=dpi)
            try:
                ax = fig.add_subplot(111)
                days = numpy.arange(len(fractionAlive)) * metadata['simulationTimeStep'] * metadata['summarizationPeriod']
                ax.plot(days, fractionAlive, 'k')
                ax.set_xlabel('Elapsed time (days)')
                ax.set_ylabel('Proportion Surviving')
                ax.set_ylim([-0.03,1.03])
                ax.set_xlim([0-max(days)*0.03,max(days)*1.03])
                ax.grid(True, which='major', linewidth=0.3, alpha=0.25)
                plt.tight_layout()
                plt.savefig(outputPNG, dpi=dpi)
            finally:
                plt.close(fig)

            # If the simulation included a competency curve, create a plot
            # that multiplies the survivorship curve by the competency curve.

            if not (metadata['competencyGammaA'] == 1e-30 and metadata['competencyGammaB'] == 1.):

                outputPNG = os.path.join(resultsDirectory, os.path.splitext(outputGDBName)[0] + '_SurvivorshipCurveWithCompetency.png')

                survivingAndCompetent = numpy.array(fractionAlive, dtype='float32') * competencyCurve[[i * int(metadata['summarizationPeriod']) for i in range(len(fractionAlive))]]

                fig = plt.figure(figsize=figSize, dpi=dpi)
                try:
                    ax = fig.add_subplot(111)
                    ax.plot(days, survivingAndCompetent, 'k')
                    ax.set_xlabel('Elapsed time (days)')
                    ax.set_ylabel('Proportion Surviving\nand Competent')
                    ax.set_ylim([-0.03,1.03])
                    ax.set_xlim([0-max(days)*0.03,max(days)*1.03])
                    ax.grid(True, which='major', linewidth=0.3, alpha=0.25)
                    plt.tight_layout()
                    plt.savefig(outputPNG, dpi=dpi)
                finally:
                    plt.close(fig)

        # Create the output geodatabase.

        outputGDB = os.path.join(resultsDirectory, outputGDBName)

        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        if gp.Exists(outputGDB):
            if not overwriteExisting:
                Logger.RaiseException(ValueError(_('The output geodatabase %s already exists. Please delete it or specify that existing outputs should be overwritten and try again.') % outputGDB))
            gp.Delete_management(outputGDB)

        Logger.Info(_('Creating the output geodatabase %s.') % outputGDB)
        gp.CreateFileGDB_management(resultsDirectory, outputGDBName)

        # Look up the properties of the patch IDs raster, so we can
        # use them when producing our outputs.

        describePatchIDsRaster = gp.Describe(os.path.join(simulationDirectory, 'PatchData', 'patch_ids.img'))
        coordinateSystem = gp.CreateSpatialReference_management(describePatchIDsRaster.SpatialReference).getOutput(0).split(';')[0]
        cellSize = describePatchIDsRaster.MeanCellWidth
        left, bottom, right, top = EnvelopeTypeMetadata.ParseFromArcGISString(describePatchIDsRaster.Extent)

        # If requested, write the density rasters to the output
        # geodatabase.

        import numpy

        if createDensityRasters:

            # Apply mortality, if requested.

            if mortalityRate is not None:
                original = numpy.copy(settledDensityMatrix)

                for i in range(1, dispersalMatrix.shape[-1]):
                    suspendedDensityMatrix[:,:,i] *= fractionAlive[i]
                    settledDensityMatrix[:,:,i] = settledDensityMatrix[:,:,i-1] + (original[:,:,i] - original[:,:,i-1]) * fractionAlive[i]

                del original

            # If the caller requested that we apply the competency curve when
            # creating the density rasters, apply it to the suspended density
            # matrix.

            if useCompetencyForDensityRasters and not (metadata['competencyGammaA'] == 1e-30 and metadata['competencyGammaB'] == 1.):

                # The first time slice is at t=0, at which time no larvae are
                # competent. Set density to 0 for this time slice.

                suspendedDensityMatrix[:,:,0] = 0

                # Multiply the remaining time slices by the competency value
                # indexed by that time.

                for i in range(1, suspendedDensityMatrix.shape[-1]):
                    suspendedDensityMatrix[:,:,i] *= competencyCurve[i * int(metadata['summarizationPeriod'])]

            # Combine the settledDensityMatrix and suspendedDensityMatrix to
            # get a matrix of all larvae.

            totalDensityMatrix = settledDensityMatrix + suspendedDensityMatrix

            # Apply the minimum density.

            if minimumDensity is not None:
                totalDensityMatrix[numpy.logical_and(totalDensityMatrix > -1, totalDensityMatrix < minimumDensity)] = -1        # We will use -1 as the NoData value

            # Write time slices of the total density matrix to the geodatabase
            # as rasters.

            totalDensityGrid = NumpyGrid(numpyArray=totalDensityMatrix,
                                         displayName=_('larval density matrix'),
                                         spatialReference=NumpyGrid.ConvertSpatialReference('ArcGIS', coordinateSystem, 'Obj'),
                                         dimensions='tyx',
                                         coordIncrements=(metadata['simulationTimeStep'] * metadata['summarizationPeriod'], cellSize, cellSize),
                                         cornerCoords=(datetime.datetime.strptime(metadata['releaseDate'], '%Y-%m-%d %H:%M:%S'), bottom + cellSize/2., left + cellSize/2.),
                                         unscaledNoDataValue=-1.,
                                         tIncrementUnit='day',
                                         tCornerCoordType='center',
                                         physicalDimensions='yxt',
                                         physicalDimensionsFlipped=(False, False, False))

            waterMaskGrid = ArcGISRaster(os.path.join(simulationDirectory, 'PatchData', 'water_mask.img')).QueryDatasets(reportProgress=False)[0]

            totalDensityGrid = MaskedGrid(totalDensityGrid, [waterMaskGrid], ['!='], [1])

            outputWorkspace = ArcGISWorkspace(outputGDB,
                                              ArcGISRaster,
                                              pathParsingExpressions=[r'Density_(?P<Year>\d\d\d\d)(?P<Month>\d\d)(?P<Day>\d\d)_(?P<Hour>\d\d)(?P<Minute>\d\d)'],
                                              pathCreationExpressions=['Density_%%Y%%m%%d_%%H%%M'],
                                              queryableAttributes=(QueryableAttribute('DateTime', 'DateTime', DateTimeTypeMetadata()),))

            outputWorkspace.ImportDatasets(GridSliceCollection(totalDensityGrid, tQACoordType='center').QueryDatasets(reportProgress=False),
                                           'Replace',
                                           buildPyramids=totalDensityMatrix.shape[0] > 1024 or totalDensityMatrix.shape[2] > 1024)

            del outputWorkspace, waterMaskGrid, totalDensityGrid, totalDensityMatrix

        # If requested, write the connectivity feature class.
        #
        # The dispersal matrix is indexed [FromPatchID, ToPatchID, TimeStep].
        # The last time slice represents the cumulative quantity of larvae
        # released by FromPatchID that settled on ToPatchID, not accounting
        # for mortality. If the caller did not supply a mortality rate, just
        # use this time slice for determining which patches are connected.
        # Otherwise apply the mortality rate.
        #
        # In Treml et al. (2012), this is called the settlement matrix.

        if createConnectionsFeatureClass:
            if mortalityRate is None:
                settlementMatrix = dispersalMatrix[:,:,-1]
            else:
                settlementMatrix = cls._ComputeSettlementMatrixWithMortality(dispersalMatrix, fractionAlive)

            probabilityMatrix = cls._ComputeProbabilityMatrix(simulationDirectory, settlementMatrix, metadata)[0]

            cls._CreateConnectivityFeatureClass(simulationDirectory, metadata, minimumDispersal, minimumDispersalType, settlementMatrix, probabilityMatrix, outputGDB, 'Connectivity')

        # Return successfully.

        return resultsDirectory

    @classmethod
    def VisualizeMultipleResults2012(cls, simulationDirectory, resultsDirectories, outputConnections, summaryStatistic, mortalityRate=None, mortalityMethod='A', minimumDispersal=0.00001, minimumDispersalType='Quantity', overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Iterate through the results directory, reading each Results.pickle,
        # and populating a slice of a 3D matrix we'll use to compute the
        # requested summary statistic.

        import numpy

        settlementMatrices = None
        probabilityMatrices = None
        larvaeReleasedForPatch = None
        sourceIDs = None
        destIDs = None

        Logger.Info(_('Reading %i result directories...') % len(resultsDirectories))
        progressReporter = ProgressReporter(progressMessage1=_('Still reading result directories: %(elapsed)s elapsed, %(opsCompleted)i directories read, %(perOp)s per directory, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                            completionMessage=_('Finished reading result directories: %(elapsed)s elapsed, %(opsCompleted)i directories read, %(perOp)s per directory.'))
        progressReporter.Start(len(resultsDirectories))

        try:
            for resultIndex, resultsDirectory in enumerate(resultsDirectories):

                # Read the Results.pickle.

                resultsFile = os.path.join(resultsDirectory, 'Results.pickle')
                if not os.path.isfile(resultsFile):
                    raise ValueError(_('The file Results.pickle does not exist in the results directory "%(dir)s". Did you run the simulation yet?') % {'dir': resultsDirectory})

                Logger.Debug(_('Reading the simulation results from %s.') % resultsFile)

                with open(resultsFile, 'rb') as f:
                    competencyCurve, dispersalMatrix, settledDensityMatrix, suspendedDensityMatrix, metadata = pickle.load(f)

                del competencyCurve, settledDensityMatrix, suspendedDensityMatrix

                # If this is the first result, allocate the settlementMatrices
                # array, indexed [FromPatchID, ToPatchID, resultIndex].

                if settlementMatrices is None:
                    settlementMatrices = numpy.zeros((dispersalMatrix.shape[0], dispersalMatrix.shape[1], len(resultsDirectories)), dispersalMatrix.dtype)
                    probabilityMatrices = numpy.zeros((dispersalMatrix.shape[0], dispersalMatrix.shape[1], len(resultsDirectories)), dispersalMatrix.dtype)
                    sourceIDs = metadata['sourceIDs']
                    destIDs = metadata['destIDs']

                # Otherwise validate that this result used the same source and
                # destination patches.

                else:
                    if metadata['sourceIDs'] != sourceIDs:
                        raise ValueError(_('The simulation in "%(dir2)s" did not use the same source patches as the simulation in "%(dir1)s". This is not allowed. All of the simulations provided to this tool must use the same source and destination patches. Please rerun the simulations again, keeping to this constraint.') % {'dir1': resultsDirectories[0], 'dir2': resultsDirectory})

                    if metadata['destIDs'] != destIDs:
                        raise ValueError(_('The simulation in "%(dir2)s" did not use the same source patches as the simulation in "%(dir1)s". This is not allowed. All of the simulations provided to this tool must use the same source and destination patches. Please rerun the simulations again, keeping to this constraint.') % {'dir1': resultsDirectories[0], 'dir2': resultsDirectory})

                    assert dispersalMatrix.shape[0] == settlementMatrices.shape[0] and dispersalMatrix.shape[1] == settlementMatrices.shape[1]      # The checks above should guarantee this

                # The dispersal matrix is indexed [FromPatchID, ToPatchID,
                # TimeStep]. The last time slice represents the cumulative
                # quantity of larvae released by FromPatchID that settled on
                # ToPatchID, not accounting for mortality. If the caller did
                # not supply a mortality rate, just use this time slice as
                # the settlement matrix for this result directory. Otherwise
                # apply the mortality rate.

                if mortalityRate is None:
                    settlementMatrices[:,:,resultIndex] = dispersalMatrix[:,:,-1]
                else:
                    fractionAlive = cls._ComputeFractionAlive(mortalityMethod, mortalityRate, metadata, dispersalMatrix.shape[-1])
                    settlementMatrices[:,:,resultIndex] = cls._ComputeSettlementMatrixWithMortality(dispersalMatrix, fractionAlive)

                # Compute the probability matrix.

                probabilityMatrix, larvaeReleasedForPatch = cls._ComputeProbabilityMatrix(simulationDirectory, settlementMatrices[:,:,resultIndex], metadata, larvaeReleasedForPatch)
                probabilityMatrices[:,:,resultIndex] = probabilityMatrix

                del dispersalMatrix
                        
                progressReporter.ReportProgress()

            # Compute the desired summary statistic on both the
            # settlementMatrices and probabilityMatrices.

            if summaryStatistic == 'maximum':
                settlementSummaryMatrix = numpy.nanmax(settlementMatrices, axis=2)
                probabilitySummaryMatrix = numpy.nanmax(probabilityMatrices, axis=2)

            elif summaryStatistic == 'mean':
                settlementSummaryMatrix = numpy.nanmean(settlementMatrices, axis=2)
                probabilitySummaryMatrix = numpy.nanmean(probabilityMatrices, axis=2)

            elif summaryStatistic == 'median':
                settlementSummaryMatrix = numpy.nanmedian(settlementMatrices, axis=2)
                probabilitySummaryMatrix = numpy.nanmedian(probabilityMatrices, axis=2)

            elif summaryStatistic == 'minimum':
                settlementSummaryMatrix = numpy.nanmin(settlementMatrices, axis=2)
                probabilitySummaryMatrix = numpy.nanmin(probabilityMatrices, axis=2)

            elif summaryStatistic == 'range':
                settlementSummaryMatrix = numpy.nanmax(settlementMatrices, axis=2) - numpy.nanmin(settlementMatrices, axis=2)
                probabilitySummaryMatrix = numpy.nanmax(probabilityMatrices, axis=2) - numpy.nanmin(settlementMatrices, axis=2)

            elif summaryStatistic == 'standard deviation':
                settlementSummaryMatrix = numpy.nanstd(settlementMatrices, axis=2, ddof=1)
                probabilitySummaryMatrix = numpy.nanstd(probabilityMatrices, axis=2, ddof=1)

            else:
                raise RuntimeError(_('Programming error in this tool: Unknown summaryStatistic "%(ss)s". Please contact the MGET development team for assistance.') % {'ss': summaryStatistic})

        finally:
            del settlementMatrices
            del probabilityMatrices

        # Create the output feature class using the summary matrices.

        cls._CreateConnectivityFeatureClass(simulationDirectory, metadata, minimumDispersal, minimumDispersalType, settlementSummaryMatrix, probabilitySummaryMatrix, os.path.dirname(outputConnections), os.path.basename(outputConnections))

    @staticmethod
    def _ComputeFractionAlive(mortalityMethod, mortalityRate, metadata, n):
        if mortalityMethod == 'A':
            return [math.exp(math.log(1-mortalityRate) * i * metadata['simulationTimeStep'] * metadata['summarizationPeriod']) for i in range(n)]
        if mortalityMethod == 'B':
            return [math.exp(-(mortalityRate * i * metadata['simulationTimeStep'] * metadata['summarizationPeriod'])) for i in range(n)]
        raise ValueError(_('Programming error in this tool: The mortalityMethod %(mortalityMethod)r is unknown. Please contact the developer of this tool for assistance.') % {'mortalityMethod': mortalityMethod})

    @staticmethod
    def _ComputeSettlementMatrixWithMortality(dispersalMatrix, fractionAlive):
        settlementMatrix = dispersalMatrix[:,:,0]       # At t=0, dispersal is zero between all pairs of patches
        for i in range(1, dispersalMatrix.shape[-1]):
            settlementMatrix += (dispersalMatrix[:,:,i] - dispersalMatrix[:,:,i-1]) * fractionAlive[i]
        return settlementMatrix

    @staticmethod
    def _ComputeProbabilityMatrix(simulationDirectory, settlementMatrix, metadata, larvaeReleasedForPatch=None):

        # Read the patch ID and patch cover rasters and compute the total
        # quantity of larvae released from each patch.

        import numpy

        if larvaeReleasedForPatch is None:
            patchIDsImage, patchIDsNoDataValue = ArcGISRaster2.ToNumpyArray(os.path.join(simulationDirectory, 'PatchData', 'patch_ids.img'))
            patchIDsNoDataValue = int(patchIDsNoDataValue)
            patchIDsImage[Grid.numpy_equal_nan(patchIDsImage, patchIDsNoDataValue)] = 0    # Force this to zero. If it is the max value, e.g. 65535, the numpy.bincount function below will not work as we want.

            patchCoverImage = ArcGISRaster2.ToNumpyArray(os.path.join(simulationDirectory, 'PatchData', 'patch_areas.img'))[0]

            larvaeReleasedForPatch = numpy.bincount(patchIDsImage.flatten(), weights=patchCoverImage.flatten())

        # Compute the probability matrix.

        probabilityMatrix = numpy.copy(settlementMatrix)

        for i, fromPatchID in enumerate(metadata['sourceIDs']):
            if larvaeReleasedForPatch[fromPatchID] < 0:
                raise RuntimeError(_('Programming error in this tool: the total larvae released from patch %(from)i was %(released)g, which is less than 0. This is not allowed. Please contact the MGET development team for assistance.') % {'from': fromPatchID, 'released': larvaeReleasedForPatch[fromPatchID]})
            elif larvaeReleasedForPatch[fromPatchID] > 0:
                probabilityMatrix[i,:] /= larvaeReleasedForPatch[fromPatchID]

        if any(probabilityMatrix.flatten() > 1.0001):
            raise RuntimeError(_('Programming error in this tool: the probability matrix contains a value greater than 1. This is not allowed. Please contact the MGET development team for assistance.'))

        return probabilityMatrix, larvaeReleasedForPatch        # Also returning larvaeReleasedForPatch, so the caller can pass it back in to us on future calls to save time

    @staticmethod
    def _CreateConnectivityFeatureClass(simulationDirectory, metadata, minimumDispersal, minimumDispersalType, settlementMatrix, probabilityMatrix, outputWorkspace, outputFCName):

        # Find the indices of the settlement or probability matrix (as
        # requested by the caller) that exceed the minimum dispersal value
        # (use 0 if one was not supplied). These are the connections that the
        # caller is interested in.

        import numpy

        if minimumDispersal is None:
            minimumDispersal = 0
            minimumDispersalType = 'quantity'

        if minimumDispersalType == 'quantity':
            connections = numpy.argwhere(settlementMatrix >= minimumDispersal)
        else:
            connections = numpy.argwhere(probabilityMatrix >= minimumDispersal)

        # Read the patch_geometry.dbf and build a dictionary that maps
        # patch IDs to their centroids.

        table = ArcGISTable(os.path.join(simulationDirectory, 'PatchData', 'patch_geometry.dbf'))
        patches = table.Query(fields=['VALUE', 'XCENTROID', 'YCENTROID', 'MINORAXIS'], reportProgress=False)
        patchCentroids = {}
        for i in range(len(patches['VALUE'])):
            patchCentroids[patches['VALUE'][i]] = p=[patches['XCENTROID'][i], patches['YCENTROID'][i], patches['MINORAXIS'][i]]      # Cannot use dict comprehension because it was introduced in Python 2.7 and we want to support prior versions

        # Create the output connectivity feature class.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        describePatchIDsRaster = gp.Describe(os.path.join(simulationDirectory, 'PatchData', 'patch_ids.img'))
        coordinateSystem = gp.CreateSpatialReference_management(describePatchIDsRaster.SpatialReference).getOutput(0).split(';')[0]

        outputWorkspace = ArcGISWorkspace(outputWorkspace,
                                          ArcGISTable,
                                          pathParsingExpressions=['%(TableName)s'], 
                                          queryableAttributes=(QueryableAttribute('TableName', _('Table name'), UnicodeStringTypeMetadata()),))

        outputTable = outputWorkspace.CreateTable(outputFCName, geometryType='LINESTRING', spatialReference=ArcGISTable.ConvertSpatialReference('ArcGIS', coordinateSystem, 'Obj'))

        outputTable.AddField('FromPatchID', 'int32', isNullable=False)
        outputTable.AddField('ToPatchID', 'int32', isNullable=False)
        outputTable.AddField('Quantity', 'float32', isNullable=False)
        outputTable.AddField('Probability', 'float32', isNullable=False)

        # Write each connection as a line to the feature class.

        def CircleCoords(xLeft, yCenter, r, n):
            return [(xLeft + r - math.cos(2*math.pi/n*x)*r, math.sin(2*math.pi/n*x)*r + yCenter) for x in range(n+1)]

        Logger.Info(_('Inserting %(count)i lines into %(dn)s.') % {'count': len(connections), 'dn': outputTable.DisplayName})

        ogr = outputTable._ogr()
        cursor = outputTable.OpenInsertCursor(rowCount=len(connections))
        try:
            for i in range(len(connections)):
                fromPatchID = metadata['sourceIDs'][connections[i][0]]
                toPatchID = metadata['destIDs'][connections[i][1]]

                cursor.SetValue('FromPatchID', fromPatchID)
                cursor.SetValue('ToPatchID', toPatchID)
                cursor.SetValue('Quantity', float(settlementMatrix[connections[i][0], connections[i][1]]))
                cursor.SetValue('Probability', float(probabilityMatrix[connections[i][0], connections[i][1]]))

                # If the connection is from a patch to itself, draw a
                # circle using the MINORAXIS of the zonal geometry as the
                # radius. This is how we visualize self recruitment.
                #
                # Otherwise draw a straight line connecting the patches.

                geometry = ogr.Geometry(ogr.wkbLineString)

                if fromPatchID == toPatchID:
                    for coords in CircleCoords(xLeft=patchCentroids[fromPatchID][0], yCenter=patchCentroids[fromPatchID][1], r= patchCentroids[fromPatchID][2], n=90):
                        geometry.AddPoint_2D(coords[0], coords[1])
                else:
                    geometry.AddPoint_2D(patchCentroids[fromPatchID][0], patchCentroids[fromPatchID][1])
                    geometry.AddPoint_2D(patchCentroids[toPatchID][0], patchCentroids[toPatchID][1])

                cursor.SetGeometry(geometry)

                cursor.InsertRow()
        finally:
            del cursor


###############################################################################
# Metadata: module
###############################################################################

from ..ArcGIS import ArcGISDependency
from ..ArcGIS import ArcGISDependency, ArcGISExtensionDependency
from ..Dependencies import PythonModuleDependency
from ..Metadata import *

AddModuleMetadata(shortDescription=_('Functions for simulating dispersal of marine larvae and modeling connectivity networks.'))

###############################################################################
# Metadata: LarvalDispersal class
###############################################################################

AddClassMetadata(LarvalDispersal,
    shortDescription=_('Functions for simulating larval dispersal and settlement, with configurable pre-competency, settlement, and mortality rates.'))

# Public method: LarvalDispersal.CreateSimulationFromArcGISRasters

AddMethodMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters,
    shortDescription=_('Creates a larval dispersal simulation and initializes it with habitat patches defined in rasters.'),
    isExposedToPythonCallers=True,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Larval Dispersal Simulation From Rasters'),
    arcGISToolCategory=_('Connectivity Analysis\\Simulate Larval Dispersal'),
    dependencies=[ArcGISDependency(3,6,0), ArcGISExtensionDependency('spatial'), PythonModuleDependency('numpy', cheeseShopName='numpy')])

AddArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=LarvalDispersal),
    description=_('%s class or an instance of it.') % LarvalDispersal.__name__)

AddArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'simulationDirectory',
    typeMetadata=DirectoryTypeMetadata(deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output directory to create to contain the simulation's data.

After creating the simulation directory, you must load ocean currents data
into it using other tools before you can run the simulation. Use the MGET
tools designed for this purpose. Unless you know what you are doing, do not
modify the contents of the simulation directory yourself."""),
    direction='Output',
    arcGISDisplayName=_('Simulation directory to create'))

AddArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'patchIDsRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True, allowedPixelTypes=['S8', 'U8', 'S16', 'U16', 'S32', 'U32', 'S64', 'U64']),
    description=_(
"""Integer raster specifying the locations and IDs of habitat patches from
which larvae will be released and upon which larvae can settle.

If you wish to control which patches larvae may be released from and which
they may settle upon, rather than simply having all of them serve in both
roles, do not worry about that now; you can control that later. For now, you
must provide a raster that defines all of the patches, regardless of their
ultimate roles.

Each patch is defined as one or more cells having the same positive integer ID
value. Patch IDs may range from 1 to 65535, inclusive. NoData indicates that
the cell is not part of a patch or that it is land. Typically, each patch's
cells form a single contiguous region, but this is not required; the cells of
a patch may be separated by NoData cells.

This raster also defines the coordinate system, extent, and cell size for the
analysis. It must use a projected coordinate system, with meters as the linear
unit. When ocean currents data are loaded into the simulation, they will be
automatically projected and clipped as needed to exactly match this raster's
coordinate system, extent, and cell size.

Due to compatibility problems between ArcGIS and some open source GIS
libraries used by MGET, we do not recommend you use any of the "Web Mercator"
coordinate systems. If you were inclined to use one of those, we recommend you
use one of the "World Mercator" coordinate systems instead.

A common challenge with this tool is that habitat patch data such as the
locations of coral reefs are typically available at very high
resolution--often 1 km cell size or finer--while ocean currents data are
typically available at much lower resolution--often 10 km or coarser. In
general, we recommend you conduct your simulation at the coarser resolution of
the ocean currents, rather than the finer resolution of the habitat patches,
for two reasons:

1. Although the tools provided to load currents into the simulation will
   automatically interpolate the currents data to the resolution of the
   habitat patches via bilinear or cubic spline interpolation, you have no
   assurance that these approaches to interpolation are realistic. Conducting
   the analysis at a substantially finer resolution than the ocean currents
   data will introduce an unknown degree of uncertainty into the results.

2. The memory required to run the simulation and the speed at which it runs
   are directly related to the number of rows and columns of the analysis.
   Large rasters can cause the tool to fail with an "OUT OF MEMORY" error.
   Even if this does not happen, large rasters can greatly increase the run
   time of the tool. In general, we recommend the dimensions of the analysis
   be less than 1000x1000 cells; ideally it should be less than 500x500 cells.

To rescale your patch IDs raster to a coarser resolution, consider using the
ArcGIS Spatial Analyst Block Statistics tool, setting Statistics Type to
MAJORITY. Then rescale the patch cover raster the same way with Statistics
Type set to MEAN, and the water mask raster with Statistics Type set to
MAXIMUM."""),
    arcGISDisplayName=_('Patch IDs raster'))

AddArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'patchCoverRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Floating-point raster specifying the proportion of each cell's area that is
occupied by habitat from which larvae can be released or upon which larvae can
settle.

The raster must have the same coordinate system, extent, and cell size as the
patch IDs raster.

The raster values must be greater than or equal to 0 and less than or equal to
1. The value 1 indicates that the entire cell is occupied by suitable habitat,
while 0.5 indicates that only half of it is. If the cell size was 25 km by 25
km, this would mean the cell contained either 625 or 312.5 square km of
suitable habitat, respectively.

If the value is 0 or NoData, it is assumed that the cell does not contain any
suitable habitat, even if the patch IDs raster indicates that suitable habitat
is there. If the value is greater than 0 but the corresponding cell in the
patch IDs raster contains NoData, it is assumed that the cell does not contain
any suitable habitat.

If you wish to control which patches larvae may be released from and which
they may settle upon, rather than simply having all of them serve in both
roles, do not worry about that now; you can control that later. For now, you
must provide a raster that gives the proportion of each cell that contains
suitable habitat, regardless of whether that habitat will be used for
spawning, settlement, or both. A limitation of this tool is that when a cell
is used for both spawning and settlement, the same proportion of it is used
for both roles."""),
    arcGISDisplayName=_('Patch cover raster'))

AddArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'waterMaskRaster',
    typeMetadata=ArcGISRasterLayerTypeMetadata(mustExist=True),
    description=_(
"""Raster specifying the locations of land and water. 0 or NoData indicates
land; any other value indicates water.

The raster must have the same coordinate system, dimensions, and cell size as
the patch IDs raster."""), 
    arcGISDisplayName=_('Water mask raster'))

AddArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'crosses180',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""Set this option to True if your study area crosses the 180th meridian (i.e.
180 W / 180 E). This could happen if you are studying coral reefs in the
tropical Pacific, for example."""),
    arcGISDisplayName=_('Study area crosses the 180th meridian'))

AddArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the simulation directory will be deleted and recreated, if it
exists. If False, a ValueError will be raised if the simulation directory
exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: LarvalDispersal.LoadCMEMSCurrentsIntoSimulation

AddMethodMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation,
    shortDescription=_('Downloads ocean currents from Copernicus Marine Service (CMEMS) into a larval dispersal simulation for a range of dates.'),
    isExposedToPythonCallers=True,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Load CMEMS Currents Into Larval Dispersal Simulation'),
    arcGISToolCategory=_('Connectivity Analysis\\Simulate Larval Dispersal'),
    
    # Although this tool does not require matplotlib, we included it as a
    # dependency so that it will be imported before this tool runs. We have
    # noticed that if matplotlib is loaded after this tool runs, e.g. when
    # RunSimulation2012 is executed, that one of matplotlib's own imports of
    # another package will fail. Because RunSimulation2012 is usually executed
    # next, we import matplotlib here to maximize chance of success.

    dependencies=[ArcGISDependency(3,6,0), ArcGISExtensionDependency('spatial'), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('matplotlib', cheeseShopName='matplotlib')])

CopyArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'cls', LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'cls')

AddArgumentMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'simulationDirectory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_(
"""Existing larval dispersal simulation directory that should receive the
currents.

The directory must have been created using the Create Larval Dispersal
Simulation tool.

If you have already loaded currents into the simulation, you can use this tool
to add data for an additional range of dates. If you try to load currents for
a range of dates that have been already loaded into the simulation, the
downloads for those dates will be skipped."""),
    arcGISDisplayName=_('Simulation directory to receive currents data'))

AddArgumentMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'startDate',
    typeMetadata=DateTimeTypeMetadata(),
    description=_(
"""Start date for the currents to load into the simulation. Currents that
occurred on or after the start date and on or before the end date will be
loaded into the simulation."""),
    arcGISDisplayName=_('Start date'))

AddArgumentMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'endDate',
    typeMetadata=DateTimeTypeMetadata(),
    description=_(
"""End date for the currents to load into the simulation. Currents that
occurred on or after the start date and on or before the end date will be
loaded into the simulation."""),
    arcGISDisplayName=_('End date'))

CopyArgumentMetadata(CMEMSARCOArray.__init__, 'username', LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'username')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'password', LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'password')

AddArgumentMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'datasetID',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_(
"""CMEMS Dataset ID to access. You can find the Dataset ID by going to the
`Copernicus Marine Data Store <https://data.marine.copernicus.eu/products>`__,
viewing your product of interest, clicking on Data Access, and scrolling to
the Dataset ID table. The dataset must have 4 dimensions: longitude, latitude,
depth, and time (in any order).

The default ``cmems_mod_glo_phy_my_0.083deg_P1D-m``, the Global Ocean Physics
Reanalysis at daily resolution, is a good choice when you don't know of
something better for your area of interest."""),
    arcGISDisplayName=_('CMEMS Dataset ID'))

AddArgumentMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'depth',
    typeMetadata=FloatTypeMetadata(minValue=0.),
    description=_(
"""Depth layer to download.

You must specify the exact depth of the layer, at full precision without
rounding. The default value is the shallowest layer of the default dataset
``cmems_mod_glo_phy_my_0.083deg_P1D-m``. For your convenience, when this tool
runs it will log a list of depth layers for the dataset you specify. If your
first attempt fails because the depth does not exist, copy one of the values
from the log message and try again.

This tool was designed primarily to study larvae that float at or near the
surface. If you are studying larvae that stay submerged, you can choose a
deeper depth, but be aware of two important points:

* This tool assumes the larvae remain at that depth for the entire simulation.
  It does not implement vertical migration or other behaviors that might be
  appropriate for your species.

* The spatial extent of available currents data will shrink as depth
  increases. For example, if you choose a deep depth such as 250 m, there
  will be no data available for regions close to shore because the ocean is
  typically shallower than 250 m in those regions. Data for very deep depths
  may only be available many kilometers from shore. If your species remains
  suspended just above the seafloor regardless of the seafloor's depth, you
  can use the depth value 20000 to represent this, and the tool will download
  whatever layer is the deepest at each latitude and longitude.

"""),
    arcGISDisplayName=_('CMEMS Dataset ID'))

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rotationOffset', LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'rotationOffset')

AddArgumentMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'resamplingTechnique',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True, allowedValues=['NEAREST', 'BILINEAR', 'CUBIC']),
    description=_(
"""Resampling algorithm to be used when projecting the ocean currents
data to the coordinate system and cell size of the simulation. One of:

* ``NEAREST`` - `Nearest neighbor assignment
  <http://en.wikipedia.org/wiki/Nearest-neighbor_interpolation>`__.

* ``BILINEAR`` - `Bilinear interpolation
  <http://en.wikipedia.org/wiki/Bilinear_interpolation>`__.

* ``CUBIC`` - Cubic convolution, also known as `bicubic interpolation
  <http://en.wikipedia.org/wiki/Bicubic_interpolation>`__. This method, the
  default, is slower but we believe it produces more accurate values.

The projection is accomplished with the ArcGIS
:arcpy_management:`Project-Raster` tool. Please see the documentation for that
tool for more information."""),
    arcGISDisplayName=_('Resampling technique'))

AddArgumentMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'interpolationMethod',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True, allowedValues=['Del2a', 'Del2b', 'Del2c', 'Del4', 'Spring'], canBeNone=True),
    description=_(
"""Method to use to guess ocean current values for cells marked as water by
the simulation's water mask but for which no estimate is available in the
currents data.

By default, this option is disabled and cells marked as water that do not have
any currents data are assumed to have a current velocity of zero. Larvae
within these cells cannot exit by advection, only by diffusion. Because
diffusion typically disperses larvae much more slowly than advection, these
zero-velocity cells will act as larvae sinks that appear to trap most larvae
that enter them.

That situation is usually unrealistic and undesirable, and when it happens the
simulator will issue a warning describing the problem. If you experience this
problem you can instruct the tool to guess current values using one of the
following algorithms:

* ``Del2a`` - Laplacian interpolation and linear extrapolation. We recommend
  you use this method unless you have a specific reason to select one of the
  others.

* ``Del2b`` - Same as ``Del2a`` but does not build as large a linear system of
  equations. May be faster than ``Del2a`` at the cost of some accuracy.

* ``Del2c`` - Same as ``Del2a`` but solves a direct linear system of equations
  for the NoData values. Faster than both ``Del2a`` and ``Del2b`` but is the
  least robust to noise on the boundaries of NoData cells and least able to
  interpolate accurately for smooth surfaces.

* ``Del4`` - Same as ``Del2a`` but instead of the Laplace operator (also
  called the ∇\\ :sup:`2` operator) it uses the biharmonic operator (also
  called the ∇\\ :sup:`4` operator). May result in more accurate
  interpolations, at some cost in speed.

* ``Spring`` - Uses a spring metaphor. Assumes springs (with a nominal length
  of zero) connect each cell with every neighbor (horizontally, vertically and
  diagonally). Since each cell tries to be like its neighbors, extrapolation
  is as a constant function where this is consistent with the neighboring
  nodes.

Be advised that this option should be considered a last resort. When ocean
current values are missing for a region, it is because the original data
provider does not know how to estimate or model the currents in that region.
If it was simply a matter of using one of the methods above, they would have
already done so. These methods produce estimates that are likely to be
inaccurate and should only be used when you are willing to accept those
inaccuracies because there is no other way to proceed.

Although this option can fill NoData clusters of any size, you should apply
common sense when using it. The larger the cluster, the less accurate the
guessed values will be.

If you receive and OUT OF MEMORY error when utilizing this parameter, try
switching to the Del2b or Del2c algorithm. If you still receive OUT OF MEMORY
when using Del2c, the analysis resolution is too fine for the spatial extent
you wish to simulate. You must recreate the simulation with either a coarser
resolution or a smaller spatial extent. You are welcome to contact the MGET
development team for advice. In general, we recommend the simulation rasters
span no more than 1000x1000 cells, ideally less than 500x500.

Thanks to John D'Errico for providing the code that implements the
mathematical algorithms described here (click `here
<http://www.mathworks.com/matlabcentral/fileexchange/4551>`__ for more
information)."""),
    arcGISDisplayName=_('Method for estimating missing currents values'))

AddResultMetadata(LarvalDispersal.LoadCMEMSCurrentsIntoSimulation, 'updatedSimulationDirectory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Updated simulation directory.'),
    arcGISDisplayName=_('Updated simulation directory'))

# Public method: LarvalDispersal.RunSimulation2012

AddMethodMetadata(LarvalDispersal.RunSimulation2012,
    shortDescription=_('Executes a larval dispersal simulation using the Treml et al. (2012) algorithm.'),
    longDescription=_(
"""This tool simulates larval dispersal for the date, duration, and settlement
parameters you specify using the hydrodynamic dispersal approach described by
Treml et. al (2012). The tool works by by simulating dispersal from each
patch, one at at time. For the focal patch, the simulator releases 1.0 units
of larvae at each cell that is fully occupied by suitable habitat (i.e. cells
where the patch cover raster is 1.0) and proportionally less at partially
occupied cells (e.g. 0.5 units at cells where the patch cover raster is 0.5).
It then circulates larvae around the study area by applying the
Multidimensional Positive Definite Advection Transport Algorithm (MPDATA)
(Smolarkiewicz and Margolin 1998) to the ocean currents. Larvae settle
according to the settlement parameters as they drift over patches (including
the source patch, if it is eligible for settlement).

Default values are provided for most parameters but you should carefully
review the documentation for each and configure them according to your species
and region of interest. You should also carefully examine any warning messages
reported in the ArcGIS geoprocessing output window and adjust parameter values
as needed to resolve potential problems.

It is often the case that the default Time Step parameter must be adjusted
based on the spatial resolution of your analysis and the ocean currents
present in your region of interest. We recommend that you first simulate
dispersal from a single patch for a short period to test that the Time Step
and other parameters are configured appropriately. To do this, set the
Duration parameter to a small value such as 5 or 10 days and specify a single
patch ID for the Patches That Disperse Larvae parameter. After carefully
reviewing the output and adjusting parameters, increase the Duration to the
final desired value and verify that it runs successfully for the single patch.
Then adjust the Patches That Disperse Larvae parameter to conduct the
simulation for all patches. Depending the size of the study area, the
duration, the time step, the number of patches, and other factors, the full
simulation can take minutes to hours to complete.

The algorithm implemented by this tool provides several important improvements
over the Treml et al. (2008) algorithm, such as mass-balanced larval
settlement and a more accurate numerical approach for the advection step. The
2008 algorithm is obsolete and we recommend it no longer be used.

References:

Smolarkiewicz PK, Margolin LG (1998) MPDATA: A Finite-Difference Solver
for Geophysical Flows. Journal of Computational Physics 140: 459-480.

Treml EA, Roberts J, Chao Y, Halpin P, Possingham HP, Riginos C (2012)
Reproductive output and duration of the pelagic larval stage determine
seascape-wide connectivity of marine populations. Integrative and
Comparative Biology 52(4): 525-537.

Treml EA, Halpin PN, Urban DL, Pratson LF (2008) Modeling population
connectivity by ocean currents, a graph-theoretic approach for marine
conservation. Landscape Ecology 23: 19-36."""),
    isExposedToPythonCallers=True,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Run Larval Dispersal Simulation (2012 Algorithm)'),
    arcGISToolCategory=_('Connectivity Analysis\\Simulate Larval Dispersal'),
    dependencies=[MatlabDependency(), ArcGISDependency(3,6,0), ArcGISExtensionDependency('spatial'), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('matplotlib', cheeseShopName='matplotlib')])

CopyArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'cls', LarvalDispersal.RunSimulation2012, 'cls')

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'simulationDirectory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_(
"""Existing larval dispersal simulation directory that has been loaded with
ocean currents.

The directory must have been created using the Create Larval Dispersal
Simulation tool and then loaded with ocean currents using one of the tools
provided for this purpose."""),
    arcGISDisplayName=_('Simulation directory'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'resultsDirectory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_(
"""Existing directory to receive files containing the results of the
simulation. To create GIS-compatible visualizations from the files, run the
Visualize Larval Dispersal Simulation Results (2012 Algorithm) tool.

The files written to the results directory are:

``Parameters.ini`` - a text file in Microsoft Windows ``.INI`` format that
lists the parameters used to execute the simulation.

``CompetencyCurve.png`` - a plot showing the proportion of larvae that are
competent to settle at each time step. The x axis units are days. The y axis
ranges from 0 (no larvae are competent) to 1 (all larvae are competent). The
competency curve is configured by the Competency Gamma a and Competency Gamma
b parameters.

``Results.pickle`` - a file in Python pickle format that contains the
following matrices.

* ``competencyCurve`` - a 1D `numpy <https://numpy.org/>`__ array, data type
  ``float32``, of the values used to produce ``CompetencyCurve.png``.

* ``dispersalMatrix`` - a 3D `numpy <https://numpy.org/>`__ array, data type
  ``float32``, that shows the cumulative quantity of larvae dispersed from
  every source patch to every destination patch, at each time the simulation
  is summarized. The matrix is indexed [``from``, ``to``, ``t``] where
  ``from`` represents the patch that is the source of larvae, ``to``
  represents the patch that larvae have settled upon, and ``t`` represents the
  summarization period. ``from`` and ``to`` are 0-based indices into
  ``metadata['sourceIDs']`` and ``metadata['destIDs']``. For example, if
  ``metadata['sourceIDs']`` and ``metadata['destIDs']`` are both ``[3, 6, 8]``,
  ``dispersalMatrix[1, 2, :]`` is the larvae released from patch 6 that
  settled on patch 8. ``t=0`` corresponds to the start of the simulation when
  no time steps have executed. At ``t=0``, the entire matrix will be zero
  because no larvae will have settled yet. ``t=1`` tallies the cumulative
  number of larvae that have settled after one summarization period has
  elapsed. ``t=2`` tallies the cumulative quantity of larvae that have settled
  after two summarization periods, and so on. The units of the matrix are
  arbitrary units of larvae, where the value 1.0 corresponds to the quantity
  of larvae released at the start of the simulation in one cell that is fully
  covered by suitable habitat (i.e. the Patch Cover Raster has the value 1.0
  in that cell).

* ``settledDensityMatrix`` - a 3D `numpy <https://numpy.org/>`__ array, data
  type ``float32``, that shows the cumulative quantity of larvae that have
  settled throughout the study area at each summarization step. The matrix
  indices are ``[x,y,t]``. ``t=0`` corresponds to the start of the simulation
  when no time steps have executed. At ``t=0``, no larvae will have settled
  yet, so all cells of the matrix will be zero. ``t=1`` tallies the cumulative
  quantity of larvae that have settled after one summarization period has
  elapsed. ``t=2`` tallies the cumulative quantity of larvae that have settled
  after two summarization periods, and so on. The units of this matrix are the
  same as the ``dispersalMatrix``.

* ``suspendedDensityMatrix`` - a 3D `numpy <https://numpy.org/>`__ array, data
  type ``float32``, that shows the instantaneous quantity of larvae suspended
  in the water column (i.e. those that have not settled or drifted off the
  edge of the map yet). The indexing and units of this matrix work the same as
  the ``settledDensityMatrix``. At ``t=0``, all larvae will be suspended in
  the water column over their source patches. At ``t>1``, some larvae will
  have drifted into other cells.

* ``metadata`` - a dictionary of the contents of the ``Parameters.ini`` file.

"""),
    arcGISDisplayName=_('Results directory'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'startDate',
    typeMetadata=DateTimeTypeMetadata(),
    description=_(
"""Start date of the simulation. The larvae are released from the patches on
this date. The simulation must contain currents that include this date."""),
    arcGISDisplayName=_('Start date'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'duration',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.0),
    description=_(
"""Duration of the simulation, in days. Typically this will be the pelagic
larval duration (PLD) of the species you are studying.

The simulation must contain currents that span the entire time range of the
simulation.

The simulation's run time and memory requirements scale linearly with the
duration and the number of patches from which larvae are released. We
recommend you first try a short simulation such as 5 days for a single patch
to quickly validate that the parameters produce reasonable results without
running out of memory. Then increase the duration and number of patches to the
desired values."""),
    arcGISDisplayName=_('Duration'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'simulationTimeStep',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.0),
    description=_(
"""Time step of the simulation, in hours.

The time step defines the period at which larvae density is recalculated using
the numerical advection-diffusion model. Smaller time steps increase the
stability of the model and accuracy of the results but also the run time and
computer memory requirements of the simulation.

To check the model stability, this tool calculates a stability condition from
the simulation time step, grid cell size, and maximum current velocity. If the
stability condition is less than 2^(-1/2), approximately 0.7071, the
simulation should be numerically stable. If the stability condition is greater
than this value, the simulator will issue a warning but proceed with the
simulation. To avoid anomalous results, you are strongly advised to reduce the
time step until the stability condition is less than 0.7071.

If the stability condition is substantially less than 0.7071, you can increase
the simulation time step to reduce the execution time of the tool without
sacrificing model stability (providing that you ensure the stability condition
is less than 0.7071)."""),
    arcGISDisplayName=_('Time step'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'summarizationPeriod',
    typeMetadata=IntegerTypeMetadata(minValue=1),
    description=_(
"""The period, expressed as a number of simulation time steps, at which the
simulation results should be summarized. The first summarization will occur at
the start of the simulation, and subsequent summarizations will occur every
time the period elapses. For example, if the time step is 1 hour and the
summarization period is 24, summarizations will occur every 24 hours.

The summarization period determines two time-related processes of the
simulation:

1. The temporal frequency at which mortality will be applied. Mortality is an
   optional biological process implemented by the Visualize Larval Dispersal
   Simulation Results tool. If you intend to apply mortality, we recommend
   that you choose a summarization period small enough that summarizations
   occur at least once per day. Because mortality is applied before
   settlement, if summarizations occur too infrequently, an unrealistically
   large number of larvae may be killed by mortality before they have a chance
   to settle. Please see the documentation for the Mortality Rate parameter of
   the Visualize Larval Dispersal Simulation Results tool for more
   information.

1. The temporal frequency of rasters produced by the Visualize Larval
   Dispersal Simulation Results tool that show the density of larvae
   throughout the study area as the simulation progresses. Here, the
   summarization period is mainly an aesthetic choice, e.g. do you want
   density rasters to be produced at, say, a daily time step or something
   else? Your choice may depend on whether you intend to examine just a few
   time slices, in which case a long period is OK, or want to build a smooth
   animation, in which case a short period is better, resulting in many
   rasters each showing small changes.

Whether you choose a short summarization period or a long one depends on your
preferences for these processes. Both are implemented by the Visualize Larval
Dispersal Simulation Results tool, which you execute after the simulation is
complete.

Visualization concerns aside, the main drawback to choosing a low
summarization period is that the tool will require more memory to execute and
utilize more disk space for the results. So long you as you have sufficient
memory and disk space, there is no harm in setting a low summarization
period."""),
    arcGISDisplayName=_('Simulation summarization period'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'a',
    typeMetadata=FloatTypeMetadata(minValue=0.0, canBeNone=True),
    description=_(
"""Shape parameter (often known as alpha or a) of the gamma cumulative
distribution function used to represent the onset of larval settlement
competency. If this parameter is omitted (the default) or set to zero, the
larvae will be immediately competent (i.e. as soon as they are released).

The Gamma Competency a and b parameters control the shape of the
cumulative distribution function. The function is computed from these
parameters using days as the units. At a*b days, approximately half
the larvae will be competent. The b parameter controls the rate at
which the larvae become competent, centered on this a*b value, with
smaller values of b producing a faster rate. For example, with a=20
and b=0.1, about half will be competent at 2 days; they will start to
become competent at about 1 day and nearly all be competent at 3.5
days. With a=200 and b=0.01, about 50% will be component at 2 days, as
before, but they will not start to become competent until about 1.7
days and nearly all will be competent by 2.3 days.

To help you visualize the competency function, the tool creates a plot
of it in the results directory.

For more about the gamma cumulative distribution function, see
`Wikipedia <https://en.wikipedia.org/wiki/Gamma_distribution>`__.
"""),
    arcGISDisplayName=_('Competency gamma a'),
    arcGISCategory=_('Settlement parameters'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'b',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.0, canBeNone=True),
    description=_(
"""Scale parameter (often known as theta or b) of the gamma cumulative
distribution function used to represent the onset of larval settlement
competency. Please see the documentation for the Competency Gamma a parameter
for more information."""),
    arcGISDisplayName=_('Competency gamma b'),
    arcGISCategory=_('Settlement parameters'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'settlementRate',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.0, maxValue=1.0),
    description=_(
"""Rate at which competent larvae will settle when suspended over a patch,
expressed as the proportion of larvae that will settle per day. For example,
the default value 0.8 indicates that 80% of the larvae suspended over the
patch for a day will settle.

This parameter must be greater than 0 and less than or equal to 1.

Only competent larvae may settle; incompetent larvae continue drifting. Larvae
may only settle on patches that are eligible for settlement. If you specify
values for the Patches Larvae Can Settle On parameter, only those patches will
be eligible. (If you do not specify any values for that parameter, all patches
are will be eligible.)"""),
    arcGISDisplayName=_('Settlement rate'),
    arcGISCategory=_('Settlement parameters'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'useSensoryZone',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""Specifies whether the larvae will settle using a sensory zone.

If True, all larvae suspended over a patch cell will be candidates for
settling, regardless of the proportion of that cell that is occupied by
suitable habitat. Under this scheme, it is assumed that the larvae employ a
sensory zone that allows them to detect and move to any suitable habitat that
occurs within the cell they occupy.

If False, the default, the number of candidate larvae will be proportional to
the proportion of cell that is occupied by suitable habitat. Under this
scheme, it is assumed that larvae are evenly distributed across the cell they
occupy and that they do not employ a sensory zone, allowing only the larvae
that are over the fraction of the cell occupied by suitable habitat to settle.

Only competent larvae may settle; incompetent larvae continue drifting. Larvae
may only settle on patches that are eligible for settlement. If you specify
values for the Patches Larvae Can Settle On parameter, only those patches will
be eligible. (If you do not specify any values for that parameter, all patches
are will be eligible.)"""),
    arcGISDisplayName=_('Use sensory zone'),
    arcGISCategory=_('Settlement parameters'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'sourcePatchIDs',
    typeMetadata=ListTypeMetadata(elementType=IntegerTypeMetadata(), canBeNone=True, minLength=1),
    description=_(
"""List of IDs of patches from which larvae should be dispersed. If the list
is empty, larvae will be dispersed from all patches except those listed for
the Excluded Patches parameter."""),
    arcGISDisplayName=_('Patches that disperse larvae'),
    arcGISCategory=_('Additional options'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'destPatchIDs',
    typeMetadata=ListTypeMetadata(elementType=IntegerTypeMetadata(), canBeNone=True, minLength=1),
    description=_(
"""List of IDs of patches upon which larvae can settle. If the list is empty,
larvae can settle on all patches except those listed for the Excluded Patches
parameter."""),
    arcGISDisplayName=_('Patches larvae can settle on'),
    arcGISCategory=_('Additional options'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'excludePatchIDs',
    typeMetadata=ListTypeMetadata(elementType=IntegerTypeMetadata(), canBeNone=True, minLength=1),
    description=_(
"""List of IDs of patches to exclude from the simulation.

This parameter is ignored if the two previous parameters are both provided, in
which case those parameters specify which patches are included in the
simulation."""),
    arcGISDisplayName=_('Excluded patches'),
    arcGISCategory=_('Additional options'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'diffusivity',
    typeMetadata=FloatTypeMetadata(minValue=0.0),
    description=_(
"""The horizontal diffusivity coefficient, in meters squared per second, to
use in the simulation.

It is recommended that you consult an oceanographer to determine this value.
The original study from which this tool was developed (Treml et al. 2012) used
the value 50. If you specify zero or omit this value, diffusion will not be
performed, which will greatly reduce the simulation run time."""),
    arcGISDisplayName=_('Diffusivity'),
    arcGISCategory=_('Additional options'))

AddArgumentMetadata(LarvalDispersal.RunSimulation2012, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the contents of the results directory will be overwritten, if it
exists. If False, a ValueError will be raised if the contents already
exist."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

AddResultMetadata(LarvalDispersal.RunSimulation2012, 'updatedResultsDirectory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Updated results directory.'),
    arcGISDisplayName=_('Updated results directory'))

# Public method: LarvalDispersal.VisualizeResults2012

AddMethodMetadata(LarvalDispersal.VisualizeResults2012,
    shortDescription=_('Produces GIS outputs that visualize the results of a simulation executed with the Treml et al. (2012) algorithm.'),
    longDescription=_(
"""Run this tool after the Run Larval Dispersal Simulation (2012 Algorithm)
tool to produce a time series of rasters showing larval density throughout the
study area and a line feature class showing connections between patches. You
many also optionally apply a mortality rate.

References:

Treml EA, Roberts J, Chao Y, Halpin P, Possingham HP, Riginos C (2012)
Reproductive output and duration of the pelagic larval stage determine
seascape-wide connectivity of marine populations. Integrative and Comparative
Biology 52(4): 525-537."""),
    isExposedToPythonCallers=True,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Visualize Larval Dispersal Simulation Results (2012 Algorithm)'),
    arcGISToolCategory=_('Connectivity Analysis\\Simulate Larval Dispersal'),
    dependencies=[ArcGISDependency(3,6,0), ArcGISExtensionDependency('spatial'), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('matplotlib', cheeseShopName='matplotlib')])

CopyArgumentMetadata(LarvalDispersal.CreateSimulationFromArcGISRasters, 'cls', LarvalDispersal.VisualizeResults2012, 'cls')
CopyArgumentMetadata(LarvalDispersal.RunSimulation2012, 'simulationDirectory', LarvalDispersal.VisualizeResults2012, 'simulationDirectory')

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'resultsDirectory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_(
"""Directory in which the results of the simulation have been created by the
Run Larval Dispersal Simulation (2012 Algorithm) tool."""),
    arcGISDisplayName=_('Results directory'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'outputGDBName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_(
"""Name of the output file geodatabase (``.gdb``) to create.

The geodatabase will be created in the results directory. If it already
exists, the tool will either overwrite it or fail with an error, depending on
whether you have requested that outputs be overwritten."""),
    arcGISDisplayName=_('Output geodatabase name'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'mortalityRate',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.0, mustBeLessThan=1.0, canBeNone=True),
    description=_(
"""Instantaneous daily mortality rate, as the proportion of larvae killed per
day. It must be greater than 0 and less than 1. Expressed as a percentage
killed per day, the value 0.1 corresponds to 10%.

If omitted (the default), larvae will not be subject to mortality. If
provided, survivorship will be calculated according to the Mortality Method
parameter using this mortality rate. For example, if the mortality rate is 0.1
and the mortality method is 'A', the proportion alive 1, 2, and 3 days after
the larvae were released will be 0.9, 0.81, and 0.729, respectively.

When mortality is used, the tool will create a plot named
``X_SurvivorshipCurve.png`` that shows the proportion of larvae alive over
time, assuming all drift without settling. ``X`` is the name of the output
geodatabase. If competency was used, the tool also creates a plot called
``X_SurvivorshipCurveWithCompetency.png`` that multiplies the survivorship
curve by the competency curve, giving the number of larvae alive that are
competent to settle at each point in time.

The tool applies mortality at each summarization period, after larvae have
moved but before they settle. For plausible results, it is therefore important
to ensure the summarization period is small relative to between-patch transit
times, or an unrealistically large fraction of larvae will be killed by
mortality before they have the chance to settle.

For example, consider a situation in which larvae can drift from a source
patch to destination patch in one day. Assume they are immediately competent
and can therefore settle at the destination patch as soon as they arrive, with
a settlement rate of 1.0. We would therefore expect that many larvae will have
settled between the first and second day. But if the first summarization
period does not elapse until day 10, survivorship will be calculated for all
the larvae that settle within the first 10 days using ``t=10`` in the equation
above. This would effectively assume that it took all of these larvae 10 days
to drift to the destination patch, during which time they were subject to 10
days of mortality. Because it only took took them 1 or 2 days to drift and
settle, the loss due to mortality will be unrealistically high, because they
only should have been subject to 1 or 2 days of mortality.

To ensure plausible results, when running the simulation we we recommend you
configure the Summarization Period parameter so that summaries occur every 1
day or less, particularly if you have a high mortality rate. The most
realistic results will be obtained by setting the Summarization Period
parameter to 1, so that summaries occur for every time step of the simulation.
However, if there are many time steps, as would occur if the Duration
parameter is large and the Time Step parameter is small, there may not be
sufficient memory for the simulation to execute. If so, the simulation may
fail immediately with an "OUT OF MEMORY" error. In that case, you have little
choice but to increase the Summarization Period.

For some readers, this discussion may prompt the question: why was mortality
implemented in this post-hoc way, rather than as part of the execution of the
simulation itself? If mortality were applied at each time step while the
simulation was executing, rather than at each summarization step after the
simulation is over, couldn't this problem could be avoided entirely?

The answer is that the approach of applying it after the simulation is over
allows you to quickly test the effects of different mortality rates without
rerunning the simulation, which can require hours if your simulation has a
long duration or hundreds of patches. Mortality has a strong influence on
connectivity (Treml et al. 2012). We have found it useful to perform this kind
of sensitivity analysis when mortality rates are uncertain and optimized the
design of the tool to facilitate this.

References:

Treml EA, Roberts J, Chao Y, Halpin P, Possingham HP, Riginos C (2012)
Reproductive output and duration of the pelagic larval stage determine
seascape-wide connectivity of marine populations. Integrative and
Comparative Biology 52(4): 525-537."""),
    arcGISDisplayName=_('Mortality rate'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'mortalityMethod',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['A', 'B'], makeUppercase=True),
    description=_(
"""Method used to calculate survivorship from the Mortality Rate parameter:

* ``A`` - Survivorship will be calculated according to the expression
  ``exp(log(1-L)*t)``. This is the default. Under this method, the number of
  larvae killed between ``t`` and ``t+1`` is the number alive at ``t``
  multiplied by the mortality rate ``L``. Treml et al. (2012, 2015) and Schill
  et al. (2015) all used this method.  For the mortality rate L=0.1 and t=1,
  2, and 3 days, the proportions of surviving larvae are 0.9, 0.81, and 0.729,
  respectively.

* ``B`` - Survivorship will be calculated according to the expression
  ``exp(-L*t)``. This method assumes an exponential decline in the surviving
  population at a constant rate. The formula is known as the survival function
  of the exponential distribution, among other names. Connolly and Baird
  (2010) presented this as their equation 8. For the mortality rate L=0.1 and
  t=1, 2, and 3 days, the proportions of surviving larvae are 0.904837,
  0.818731, 0.740818, respectively.

In these expressions, ``L`` is the mortality rate, ``t`` is the number of days
elapsed since larvae were released, ``log(x)`` is the natural logarithm of
``x``, and ``exp(x)`` is the mathematical constant ``e`` raised to the power
of ``x``.

References:

Connolly SR, Baird AH (2010) Estimating dispersal potential for marine larvae:
dynamic models applied to scleractinian corals. Ecology 91(12): 3572-3583.

Schill SR, Raber GT, Roberts JJ, Treml EA, Brenner J, Halpin PN (2015) No reef
is an island: Integrating coral reef connectivity data into the design of
regional-scale marine protected area networks. PLoS ONE 10(12): e0144199.

Treml EA, Roberts J, Chao Y, Halpin P, Possingham HP, Riginos C (2012)
Reproductive output and duration of the pelagic larval stage determine
seascape-wide connectivity of marine populations. Integrative and
Comparative Biology 52(4): 525-537.

Treml EA, Roberts J, Halpin PN, Possingham HP, Riginos C (2015) The emergent
geography of biophysical dispersal barriers across the Indo-West Pacific.
Diversity and Distributions 21(4): 465-476.

"""),
    arcGISDisplayName=_('Mortality method'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'createDensityRasters',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If this option is enabled (the default) the tool will create in the output
geodatabase a time series of rasters showing the density of larvae throughout
the study area as the simulation progresses.

The first raster will be created at the start of the simulation, before any
larvae have moved. Subsequent rasters will be created each time the
summarization period elapses. The rasters will be named
``Density_YYYYMMDD_HHMM`` where ``YYYY``, ``MM``, ``DD``, ``HH``, and ``MM``
are the year, month, day, hour, and minute.

The units of the rasters are the quantity of larvae per grid cell, relative to
the maximum possible quantity that can occupy a cell at the start of the
simulation when larvae are first released. The value 1.0 corresponds to the
quantity of larvae released at the start of the simulation in one cell that is
fully covered by suitable habitat (i.e. the Patch Cover Raster has the value
1.0 in that cell)."""),
    arcGISDisplayName=_('Create density rasters'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'minimumDensity',
    typeMetadata=FloatTypeMetadata(minValue=0.0, canBeNone=True),
    description=_(
"""Minimum value that a density raster cell must be to not be masked.

You may set this parameter as low as zero. If you set it to zero, the density
rasters will be produced with no masking. The results may seem surprising. For
most simulations, larvae will have spread throughout the entire study area,
albeit in very small quantities for most cells, via the diffusion component of
the hydrodynamic calculations. Diffusion occurs equally in all directions at
the rate specified by the Diffusivity parameter. Given enough time, an
infinitesimal fraction of larvae from any given patch can theoretically spread
throughout the entire ocean simply by diffusion. To avoid a confusing
visualization, use this parameter to mask the extremely density values that
result from diffusion."""),
    arcGISDisplayName=_('Minimum density value'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'useCompetencyForDensityRasters',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If this option is disabled (the default) the tool will include all larvae
in the density rasters. If enabled, the tool will exclude larvae that are not
yet competent from the density rasters.

This option is only useful if you configured the larval competency parameters
of your simulation such that larvae did not become immediately competent to
settle. This configuration raises the possibility that larvae released from a
patch may drift by a nearby patch before they become competent, leading to a
potentially surprising result that nearby patches may not be highly connected.
Use this option to help visualize whether this might be happening."""),
    arcGISDisplayName=_('Exclude incompetent larvae from density rasters'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'createConnectionsFeatureClass',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If this option is enabled (the default) the tool will create a Connections
line feature class in the output geodatabase showing the connections between
patches.

The lines are directional, originating at a source patch centroid and
terminating at a destination patch (or "sink patch") centroid. The Minimum
Dispersal Threshold parameter controls how strong the connection must be for a
line to be drawn. If sufficient larvae flowed in both directions between two
patches, one line will be drawn in each direction; the two lines will exactly
overlap. If a patch experienced sufficient self recruitment (larvae released
by the patch settled at that same patch), a circular line will be drawn from
the patch's centroid to itself. For convenience of visualization, the size of
the circle is scaled to the length of the "minor axis" of the zonal geometry
of the patch; the size does not relate to the degree of connectivity.

Each line has four attributes:

* ``FromPatchID`` - source patch that released larvae.

* ``ToPatchID`` - destination patch that larvae settled on.

* ``Quantity`` - quantity of larvae that settled. The units are relative to
  the maximum possible quantity that can occupy a cell at the start of the
  simulation when larvae are first released. The value 1.0 corresponds to the
  quantity of larvae released at the start of the simulation in one cell that
  is fully covered by suitable habitat (i.e. the Patch Cover Raster has the
  value 1.0 in that cell).

* ``Probability`` - probability that a larva released by the source patch
  settled on the destination patch. This is computed by dividing the Quantity
  (above) by the total amount of larvae released by the source patch at the
  start of the simulation.

"""),
    arcGISDisplayName=_('Create connections feature class'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'minimumDispersal',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.0, canBeNone=True),
    description=_(
"""Minimum dispersal threshold that must be met or exceeded for the tool to
draw a line connecting the source patch to a destination patch.

The threshold can be specified as either a minimum quantity of larvae released
by the source that must settle at the destination, or as the minimum
probability that a larva released by the source will settle at the
destination. The Minimum Dispersal Threshold Type parameter specifies which
kind of threshold is used.

This parameter must be greater than zero. If you set it to a very small value,
almost all patches will have lines drawn between them. This result may seem
surprising. For most simulations, larvae will have spread throughout the
entire study area, albeit in very small quantities for most cells, via the
diffusion component of the hydrodynamic calculations. Diffusion occurs
equally in all directions at the rate specified by the Diffusivity parameter.
Given enough time, an infinitesimal fraction of larvae from any given patch
can theoretically spread throughout the entire ocean simply by diffusion.

An important question is: why not set this parameter to a very small value and
then filter weak connections later? This is a valid approach. The main reason
not to do this is it may take the tool a long time to draw so many lines.
Whether or not this is a problem depends on the number of patches you have.
Assuming each patch can be both a source and sink for larvae, the number of
possible connections is ``2 * P^2``, where ``P`` is the number of patches. So
if you only have 20 patches, at most 800 lines will be drawn, a relatively
small number. But if you have 500 patches, as many as 500,000 lines will be
drawn."""),
    arcGISDisplayName=_('Minimum dispersal threshold'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'minimumDispersalType',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True, allowedValues=['Quantity', 'Probability']),
    description=_(
"""Type of minimum dispersal threshold that will be used to determine whether
a line should be drawn from a source patch to a destination patch. One of:

* ``Quantity`` - the minimum absolute quantity of larvae released by the
  source patch that must settle at the destination patch. A cell that is 100%
  covered by suitable habitat will release 1 unit of larvae, while one that is
  only 50% covered will release 0.5 units of larvae.

* ``Probability`` - the minimum probability that a larva released by the
  source patch will settle at the destination patch. For each
  source-destination pair, the probability is computed by dividing the
  absolute quantity of larvae from the source that settled on the destination
  by the total absolute quantity of larvae released by the source. For
  example, consider a source comprised of 5 cells that are 100% covered and 3
  cells that are 50% covered. The total quantity of larvae released will be
  6.5 units. If a destination patch receives in 0.52 units of larvae, totaled
  across all of its cells, then the probability is 0.52 / 6.5 = 0.08.

"""),
    arcGISDisplayName=_('Minimum dispersal threshold type'))

AddArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output geodatabase will be deleted and recreated, if it
exists. If False, a ValueError will be raised if the output geodatabase
exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

AddResultMetadata(LarvalDispersal.VisualizeResults2012, 'updatedResultsDirectory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Updated results directory.'),
    arcGISDisplayName=_('Updated results directory'))

# Public method: LarvalDispersal.VisualizeMultipleResults2012

AddMethodMetadata(LarvalDispersal.VisualizeMultipleResults2012,
    shortDescription=_('Produces GIS outputs that summarize multiple connectivity simulation runs executed with the Treml et al. (2012) algorithm.'),
    longDescription=_(
"""It is often useful to execute the Run Larval Dispersal Simulation tool for
different time periods to investigate how variations in ocean currents affect
connectivity. The Visualize Multiple Larval Dispersal Simulation Results tool
reads the results of multiple simulations, combines them, and produces a line
feature class that summarizes the connections between patches using the
statistic you specify. For example, if you ran 10 simulations and selected the
Mean summary statistic, the output line features would show the average
connectivity between each pair of patches over the 10 simulations.

You many also optionally apply a mortality rate. The same mortality rate will
be applied to all simulations prior to combining them and computing the
summary statistic.

References:

Treml EA, Roberts J, Chao Y, Halpin P, Possingham HP, Riginos C (2012)
Reproductive output and duration of the pelagic larval stage determine
seascape-wide connectivity of marine populations. Integrative and
Comparative Biology 52(4): 525-537."""),
    isExposedToPythonCallers=True,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Visualize Multiple Larval Dispersal Simulation Results (2012 Algorithm)'),
    arcGISToolCategory=_('Connectivity Analysis\\Simulate Larval Dispersal'),
    dependencies=[ArcGISDependency(3,6,0), ArcGISExtensionDependency('spatial'), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('matplotlib', cheeseShopName='matplotlib')])

CopyArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'cls', LarvalDispersal.VisualizeMultipleResults2012, 'cls')
CopyArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'simulationDirectory', LarvalDispersal.VisualizeMultipleResults2012, 'simulationDirectory')

AddArgumentMetadata(LarvalDispersal.VisualizeMultipleResults2012, 'resultsDirectories',
    typeMetadata=ListTypeMetadata(elementType=DirectoryTypeMetadata(mustExist=True), minLength=1),
    description=_(
"""List of one or more results directories created by the Run Larval Dispersal
Simulation (2012 Algorithm) tool."""),
    arcGISDisplayName=_('Results directories'))

AddArgumentMetadata(LarvalDispersal.VisualizeMultipleResults2012, 'outputConnections',
    typeMetadata=ArcGISFeatureClassTypeMetadata(deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Output line feature class to create showing the connections between patches.

The lines are directional, originating at a source patch centroid and
terminating at a destination patch (or "sink patch") centroid. The tool
creates them as follows:

1. If a morality rate is provided, the tool applies it to all simulation
   results. If no mortality is provided, this step is skipped.

2. The tool aggregates all of the simulation results and applies the summary
   statistic to all possible pairs of patches. For any given pair of patches,
   A and B, there are four possible connections: A to B, B to A, A to A, and B
   to B. The tool applies the statistic to all four possible connections, for
   all pairs of patches that were simulated.

3. The tool iterates through all possible connections and compares the
   summarized result to the Minimum Dispersal Threshold parameter to determine
   if a connection was strong enough for a line to be drawn. If sufficient
   larvae flowed in both directions between two patches, a line will be drawn
   in each direction; the two lines will exactly overlap. If a patch
   experienced sufficient self recruitment (larvae released by the patch
   settled at that same patch), a circular line will be drawn from the patch's
   centroid to itself. For convenience of visualization, the size of the
   circle is scaled to the length of the "minor axis" of the zonal geometry
   of the patch; the size does not relate to the degree of connectivity.

Each line has four attributes:

* ``FromPatchID`` - source patch that released larvae.

* ``ToPatchID`` - destination patch that larvae settled on.

* ``Quantity`` - quantity of larvae that settled. The units are relative to
  the maximum possible quantity that can occupy a cell at the start of the
  simulation when larvae are first released. The value 1.0 corresponds to the
  quantity of larvae released at the start of the simulation in one cell that
  is fully covered by suitable habitat (i.e. the Patch Cover Raster has the
  value 1.0 in that cell).

* ``Probability`` - probability that a larva released by the source patch
  settled on the destination patch. This is computed by dividing the Quantity
  (above) by the total amount of larvae released by the source patch at the
  start of the simulation. (Note: probabilities are first computed for each
  simulation, then the summary statistic is applied.)

"""),
    direction='Output',
    arcGISDisplayName=_('Output line feature class'))

AddArgumentMetadata(LarvalDispersal.VisualizeMultipleResults2012, 'summaryStatistic',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Maximum', 'Mean', 'Median', 'Minimum', 'Range', 'Standard Deviation'], makeLowercase=True),
    description=_(
"""Statistic to calculate. The same statistic is calculated for each of the
two output fields, Quantity and Probability.

Standard Deviation is the sample standard deviation, i.e. the standard
deviation estimated using Bessel's correction. In order to calculate this, at
least two simulations must have been conducted."""),
    arcGISDisplayName=_('Statistic'))

CopyArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'mortalityRate', LarvalDispersal.VisualizeMultipleResults2012, 'mortalityRate')
CopyArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'mortalityMethod', LarvalDispersal.VisualizeMultipleResults2012, 'mortalityMethod')
CopyArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'minimumDispersal', LarvalDispersal.VisualizeMultipleResults2012, 'minimumDispersal')
CopyArgumentMetadata(LarvalDispersal.VisualizeResults2012, 'minimumDispersalType', LarvalDispersal.VisualizeMultipleResults2012, 'minimumDispersalType')

AddArgumentMetadata(LarvalDispersal.VisualizeMultipleResults2012, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output feature class will be deleted and recreated, if it
exists. If False, a ValueError will be raised if the output feature class
exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['LarvalDispersal']
