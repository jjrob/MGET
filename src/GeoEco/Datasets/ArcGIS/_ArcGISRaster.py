# _ArcGISRaster.py - Defines ArcGISRaster, DatasetCollectionTree of
# ArcGISRasterBands accessed through arcpy.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os
import re
import shutil
import tempfile

from ...ArcGIS import GeoprocessorManager
from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Types import IntegerTypeMetadata

from .. import Dataset, DatasetCollection, QueryableAttribute, Grid
from ..GDAL import GDALDataset, GDALRasterBand
from ._ArcGISRasterBand import ArcGISRasterBand


_UseUnscaledDataDescription = _(
"""If True and the original data is stored as integers that are processed
through a "scaling equation" to produce the actual floating point values, the
output rasters will be created with the integers rather the floating point
values. If False, or the original data is not processed through a scaling
equation, the output rasters will be created using the data's original data
type.""")

_CalculateStatisticsDescription = _(
"""If True, statistics will be calculated for the output rasters. This is
usually a good idea for most raster formats because ArcGIS will only display
them with helpful colors and gradients if statistics have been calculated. For
certain formats, the explicit calculation of statistics is not necessary
because it happens automatically when the rasters are created. If you're using
one of those formats, you can set this option to False to speed up the
creation of the output rasters.""")

_BuildRATDescription = _(
"""If True and the output rasters use an integer data type, raster attribute
tables (RATs) will be built for the output rasters using the ArcGIS Build
Raster Attribute Table tool. Raster attribute tables are essentially
histograms: they store the counts of cells having each value. If you do not
need this information, you can skip the building of raster attribute tables to
speed up the creation of the output rasters. Note that for certain raster
formats, such as ArcInfo Binary Grid, the explicit buliding of raster
attribute tables is not necessary because it happens automatically when the
rasters are created. This option is ignored if the output rasters use a
floating point data type.""")

_BuildPyramidsDescription = _(
"""If True, pyramids will be built for the output rasters using the ArcGIS
Build Pyramids tool. Pyramids, also known as overviews, are reduced resolution
versions of the rasters that can improve the speed at which they are displayed
in the ArcGIS user interface.""")


class ArcGISRaster(DatasetCollection):
    __doc__ = DynamicDocString()

    def _GetPath(self):
        return self._Path

    Path = property(_GetPath, doc=DynamicDocString())

    def _GetDecompressedFileToReturn(self):
        return self._DecompressedFileToReturn

    DecompressedFileToReturn = property(_GetDecompressedFileToReturn, doc=DynamicDocString())

    def _GetArcGISDataType(self):
        return self.GetLazyPropertyValue('ArcGISDataType')

    ArcGISDataType = property(_GetArcGISDataType, doc=DynamicDocString())

    def __init__(self, path, decompressedFileToReturn=None, parentCollection=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Path = path
        self._DecompressedFileToReturn = decompressedFileToReturn
        self._GDALDataset = None
        self._TempCopy = None
        
        if parentCollection is None:
            self._DisplayName = _('ArcGIS raster "%(path)s"') % {'path': path}
        else:
            self._DisplayName = _('ArcGIS raster "%(path)s"') % {'path': os.path.join(parentCollection.Path, path)}

        # We allow querying for Grid datasets by band number. If the parent
        # collection(s) did not define the Band queryable attribute, we must
        # define it.

        queryableAttributes = None
        if parentCollection is not None:
            bandAttribute = parentCollection.GetQueryableAttribute('Band')
        if parentCollection is None or bandAttribute is None:
            bandAttribute = QueryableAttribute('Band', _('Band number'), IntegerTypeMetadata(minValue=1))
            queryableAttributes = (bandAttribute,)

        # Initialize the base class.
        
        super(ArcGISRaster, self).__init__(parentCollection, queryableAttributes, queryableAttributeValues, lazyPropertyValues, cacheDirectory)

        # Validate that the caller has not assigned a value to the Band
        # queryable attribute, either directly to us or to our parent
        # collection(s).

        if self.GetQueryableAttributeValue('Band') is not None:
            raise ValueError(_('This ArcGISRaster or its parent collection(s) specify a value for the Band queryable attribute. This is not allowed, as the value of that queryable attribute is assigned by the ArcGISRasterBand class.'))

    def _GetDisplayName(self):
        if self._GDALDataset is not None:
            return self._GDALDataset.DisplayName
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If this is a lazy property that we know how to retrieve, get it from
        # the geoprocessor's Describe object.

        if name not in ['ArcGISDataType', 'Bands', 'SpatialReference']:
            return None

        if self.ParentCollection is None:
            path = self._Path
        else:
            path = os.path.join(self.ParentCollection.Path, self._Path)

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        
        if not gp.Exists(path):
            raise ValueError(_('Failed to open ArcGIS raster "%(path)s". ArcGIS reports that it does not exist.') % {'path': path})

        d = gp.Describe(path)
        if d.DataType.lower() not in ['rasterdataset', 'rasterlayer']:
            raise ValueError(_('Failed to open "%(path)s" as an ArcGIS raster. ArcGIS reports that it is a %(dt)s, which cannot be opened as a raster.') % {'path': path, 'dt': d.DataType})
        
        self._DisplayName = _('ArcGIS %(dt)s "%(path)s"') % {'dt': d.DataType, 'path': path}

        self.SetLazyPropertyValue('ArcGISDataType', d.DataType)
        self.SetLazyPropertyValue('Bands', d.BandCount)
        self.SetLazyPropertyValue('SpatialReference', Dataset.ConvertSpatialReference('arcgis', gp.CreateSpatialReference_management(d.SpatialReference).getOutput(0).split(';')[0], 'obj'))

        # Log a debug message with the properties of the raster.
        
        self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: Bands=%(Bands)s, SpatialReference=%(SpatialReference)s.'),
                       {'class': self.__class__.__name__,
                        'id': id(self),
                        'dn': self.DisplayName,
                        'Bands': repr(self.GetLazyPropertyValue('Bands')),
                        'SpatialReference': repr(Dataset.ConvertSpatialReference('obj', self.GetLazyPropertyValue('SpatialReference'), 'arcgis'))})

        # Return the value of the requested property.

        return self.GetLazyPropertyValue(name)

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):

        # Go through the bands of this dataset, testing whether each one
        # matches the query expression. For each match, construct either a
        # GDALRasterBand or an ArcGISRasterBand and add it to our list of
        # datasets to return.

        datasetsFound = []
        triedGDAL = False
        gdalDataset = None

        for band in range(1, self.GetLazyPropertyValue('Bands') + 1):
            if parsedExpression is not None:
                attrValues = {'Band': band}
                attrValues.update(parentAttrValues)
                try:
                    result = parsedExpression.eval(attrValues)
                except Exception as e:
                    continue
            else:
                result = True

            if result is None or result:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for band %(band)i: %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 'band': band, 'result': repr(result)})

            if result:
                if not triedGDAL:
                    gdalDataset = self._TryToInstantiateGDALDataset()
                    triedGDAL = True

                if gdalDataset is not None:
                    datasetsFound.append(GDALRasterBand(gdalDataset, band))
                else:
                    datasetsFound.append(ArcGISRasterBand(self, band))
                
                if progressReporter is not None:
                    progressReporter.ReportProgress()

        return datasetsFound

    def _TryToInstantiateGDALDataset(self):
        
        # If we already instantiated a GDALDataset for this raster, return it.

        if self._GDALDataset is not None:
            return self._GDALDataset

        # Before we try to instantiate a GDALDataset for this raster, retrieve
        # the SpatialReference lazy property. Unfortunately, GDAL does not
        # know how to recognize some of the ESRI-specific WKT strings that
        # ArcGIS stores in rasters. To work around this, we retrieve it using
        # the geoprocessor. Next, when we instantiate the GDALDataset, we will
        # provide it as a lazy property so that GDALDataset does not try to
        # retrieve it.

        self.GetLazyPropertyValue('SpatialReference')       # Do not do anything with it. We just need it to be stored in the self._LazyPropertyValues dictionary.

        # If we created an IMG file for it in a temporary cache directory,
        # instantate and return a GDALDataset for it.

        if self._TempCopy is not None:
            self._GDALDataset = GDALDataset(self._TempCopy, parentCollection=self.ParentCollection, queryableAttributeValues=self._QueryableAttributeValues, lazyPropertyValues=self._LazyPropertyValues)
            self._RegisterForCloseAtExit()
            return self._GDALDataset

        # We have not instantiated a GDALDataset for this raster and did not
        # make a temporary IMG file. Determine if the path resolves to a file
        # system object that is not in a file geodatabase. If so, instantiate
        # and return a GDALDataset for it.

        if self.ParentCollection is None:
            path = self._Path
        else:
            path = os.path.join(self.ParentCollection.Path, self._Path)

        if os.path.exists(path) and len(os.path.dirname(path)) > 0 and GeoprocessorManager.GetWrappedGeoprocessor().Describe(os.path.dirname(path)).DataType.lower() == 'folder':
            self._GDALDataset = GDALDataset(path, decompressedFileToReturn=self.DecompressedFileToReturn, parentCollection=self.ParentCollection, queryableAttributeValues=self._QueryableAttributeValues, lazyPropertyValues=self._LazyPropertyValues, cacheDirectory=self.CacheDirectory)
            self._RegisterForCloseAtExit()
            return self._GDALDataset

        # The path does not resolve to a file system object that is not in a
        # file geodatabase. Therefore, it must be an in-memory raster layer or
        # a raster in a geodatabase, and we cannot access it directly with a
        # GDALDataset.

        return None

    def _InstantiateGDALDataset(self):

        # First try to open the raster directly with GDAL.

        if self._TryToInstantiateGDALDataset() is not None:
            return self._GDALDataset

        # We failed to open raster directly with GDAL, probably because it is
        # in a geodatabase or is an in-memory raster layer. Create a temporary
        # cache directory and copy the raster into it as an IMG file.

        if self.ParentCollection is None:
            path = self._Path
        else:
            path = os.path.join(self.ParentCollection.Path, self._Path)

        tempDir = self._CreateTempDirectory()
        tempPath = os.path.join(tempDir, 'raster.img')

        self._LogDebug(_('%(class)s 0x%(id)016X: Copying %(dn)s to "%(temp)s".'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self.DisplayName, 'temp': tempPath})
        GeoprocessorManager.GetWrappedGeoprocessor().CopyRaster_management(path, tempPath)

        self._TempCopy = tempPath

        # Now try to open it again. This should succeed.

        if self._TryToInstantiateGDALDataset() is not None:
            return self._GDALDataset

    def _Close(self):
        if hasattr(self, '_GDALDataset') and self._GDALDataset is not None:
            self._GDALDataset.Close()
            self._GDALDataset = None
        super(ArcGISRaster, self)._Close()

    @classmethod
    def _RemoveExistingDatasetsFromList(cls, path, datasets, progressReporter):

        # Because ArcGIS does not support adding bands to existing rasters, we
        # cannot implement 'add' mode in the way that most people would expect
        # (that is, if len(datasets) is greater than the number of existing
        # bands, add the remaining datasets as new bands). Instead we assume
        # that if the raster exists, it already has all of the necessary
        # bands. Thus, if it exists, remove all of the datasets from the
        # caller's list.

        numDatasets = len(datasets)

        if cls._ArcGISRasterExists(path):
            cls._LogDebug(_('%(class)s: ArcGIS raster "%(path)s" exists.'), {'class': cls.__name__, 'path': path})
            while len(datasets) > 0:
                del datasets[0]
        else:
            cls._LogDebug(_('%(class)s: ArcGIS raster "%(path)s" does not exist.'), {'class': cls.__name__, 'path': path})

        # Report that we checked all of these datasets.

        if progressReporter is not None:
            progressReporter.ReportProgress(numDatasets)

    @classmethod
    def _ArcGISRasterExists(cls, name):

        # Check whether name is a file system path. If it is, determine its
        # existence using the file system. This is faster than using the
        # geoprocessor.

        if (name[0] in ['/', '\\'] or hasattr(os.path, 'splitdrive') and os.path.splitdrive(name)[0] != '') and os.path.splitext(os.path.dirname(name))[1].lower() != '.gdb':
            return os.path.exists(name)

        # name is not a file system path. Determine its existence using the
        # geoprocessor.
        
        return GeoprocessorManager.GetWrappedGeoprocessor().Exists(name)

    @classmethod
    def _ImportDatasetsToPath(cls, path, sourceDatasets, mode, progressReporter, options):

        # Unpack the options dictionary.

        useUnscaledData = 'useUnscaledData' in options and options['useUnscaledData']
        calculateStatistics = 'calculateStatistics' not in options or options['calculateStatistics']        # Note that default for calculateStatistics is True.
        calculateHistogram = 'calculateHistogram' not in options or options['calculateHistogram']           # Note this option is ignored unless we write the dataset with GDAL; also its default is True.
        buildRAT = 'buildRAT' in options and options['buildRAT']
        buildPyramids = 'buildPyramids' in options and options['buildPyramids']

        if 'blockSize' in options:
            blockSize = options['blockSize']
        else:
            blockSize = None

        # Validate that the source datasets are all Grids and have dimensions
        # 'yx', evenly-spaced coordinates, valid data types, and the same
        # spatial reference, shape, coordinate increments, corner coordinates,
        # and data type.

        gdal = cls._gdal()
        gdal.ErrorReset()

        if not hasattr(ArcGISRaster, '_GDALDataTypeForNumpyDataType'):
            ArcGISRaster._GDALDataTypeForNumpyDataType = {'uint8': gdal.GDT_Byte,
                                                          'int8': gdal.GDT_Int8 if hasattr(gdal, 'GDT_Int8') else gdal.GDT_Byte,
                                                          'uint16': gdal.GDT_UInt16,
                                                          'int16': gdal.GDT_Int16,
                                                          'uint32': gdal.GDT_UInt32,
                                                          'int32': gdal.GDT_Int32,
                                                          'float32': gdal.GDT_Float32,
                                                          'float64': gdal.GDT_Float64,
                                                          'complex32': gdal.GDT_CFloat32,
                                                          'complex64': gdal.GDT_CFloat64}

        for dataset in sourceDatasets:
            if not isinstance(dataset, Grid):
                raise TypeError(_('Cannot import %(dn)s into ArcGIS raster "%(path)s" because it is a %(type)s, which is not a Grid. It must be a Grid to be imported into an ArcGIS raster.') % {'dn': dataset.DisplayName, 'path': path, 'type': dataset.__class__.__name__})
            if dataset.Dimensions != 'yx':
                raise ValueError(_('Cannot import %(dn)s into ArcGIS raster "%(path)s" because it has dimensions "%(dim)s". It must have dimensions "yx" to be imported into an ArcGIS raster.') % {'dn': dataset.DisplayName, 'path': path, 'dim': dataset.Dimensions})
            if dataset.CoordDependencies != (None, None):
                raise ValueError(_('Cannot import %(dn)s into ArcGIS raster "%(path)s" because it does not have evenly-spaced coordinates (the coordinate dependencies are %(deps)s). It must have evenly-spaced coordinates (coordinate dependencies of (None, None)) to be imported into an ArcGIS raster.') % {'dn': dataset.DisplayName, 'path': path, 'deps': repr(dataset.CoordDependencies)})
            if useUnscaledData:
                if dataset.UnscaledDataType not in ArcGISRaster._GDALDataTypeForNumpyDataType.keys():
                    raise ValueError(_('Cannot import %(dn)s into ArcGIS raster "%(path)s" because it has the unscaled data type %(dt)s. To be imported into an ArcGIS raster, it must have one of the following unscaled data types: %(dts)s.') % {'dn': dataset.DisplayName, 'path': path, 'dt': dataset.UnscaledDataType, 'dts': ', '.join(ArcGISRaster._GDALDataTypeForNumpyDataType.keys())})
            elif dataset.DataType not in ArcGISRaster._GDALDataTypeForNumpyDataType.keys():
                raise ValueError(_('Cannot import %(dn)s into ArcGIS raster "%(path)s" because it has the data type %(dt)s. To be imported into an ArcGIS raster, it must have one of the following data types: %(dts)s.') % {'dn': dataset.DisplayName, 'path': path, 'dt': dataset.DataType, 'dts': ', '.join(ArcGISRaster._GDALDataTypeForNumpyDataType.keys())})

        for i in range(1, len(sourceDatasets)):
            if not sourceDatasets[0].GetSpatialReference('obj').IsSame(sourceDatasets[i].GetSpatialReference('obj')):
                raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into ArcGIS raster "%(path)s" because the two source datasets have different spatial references (%(sr1)s and %(sr2)s). This function requires that all of the bands of an ArcGIS raster have the same spatial reference.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'sr1': repr(sourceDatasets[0].GetSpatialReference('wkt')), 'sr2': repr(sourceDatasets[i].GetSpatialReference('wkt'))})
            if sourceDatasets[0].Shape != sourceDatasets[i].Shape:
                raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into ArcGIS raster "%(path)s" because the two source datasets have different shapes (%(shape1)s and %(shape2)s). This function requires that all of the bands of an ArcGIS raster have the same shape.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'shape1': repr(sourceDatasets[0].Shape), 'shape2': repr(sourceDatasets[i].Shape)})
            if sourceDatasets[0].CoordIncrements != sourceDatasets[i].CoordIncrements:
                raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into ArcGIS raster "%(path)s" because the two source datasets have different coordinate increments (%(incr1)s and %(incr2)s). This function requires that all of the bands of an ArcGIS raster have the same coordinate increments.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'incr1': repr(sourceDatasets[0].CoordIncrements), 'incr2': repr(sourceDatasets[i].CoordIncrements)})
            if sourceDatasets[0].MinCoords['x',0] != sourceDatasets[i].MinCoords['x',0]:
                raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into ArcGIS raster "%(path)s" because the two source datasets have different minimum x coordinates (%(c1)s and %(c2)s). This function requires that all of the bands of an ArcGIS raster have the same corner coordinates.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'c1': repr(sourceDatasets[0].MinCoords['x',0]), 'c2': repr(sourceDatasets[i].MinCoords['x',0])})
            if sourceDatasets[0].MinCoords['y',0] != sourceDatasets[i].MinCoords['y',0]:
                raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into ArcGIS raster "%(path)s" because the two source datasets have different minimum y coordinates (%(c1)s and %(c2)s). This function requires that all of the bands of an ArcGIS raster have the same corner coordinates.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'c1': repr(sourceDatasets[0].MinCoords['y',0]), 'c2': repr(sourceDatasets[i].MinCoords['y',0])})
            if useUnscaledData:
                if sourceDatasets[0].UnscaledDataType != sourceDatasets[i].UnscaledDataType:
                    raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into ArcGIS raster "%(path)s" because the two source datasets have different unscaled data types (%(dt1)s and %(dt2)s). This function requires that all of the bands of an ArcGIS raster have the same data type.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'dt1': sourceDatasets[0].UnscaledDataType, 'dt2': sourceDatasets[i].UnscaledDataType})
            elif sourceDatasets[0].DataType != sourceDatasets[i].DataType:
                raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into ArcGIS raster "%(path)s" because the two source datasets have different data types (%(dt1)s and %(dt2)s). This function requires that all of the bands of an ArcGIS raster the same data type.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'dt1': sourceDatasets[0].DataType, 'dt2': sourceDatasets[i].DataType})

        # If the mode is 'replace' and the raster exists, delete it.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()

        if mode == 'replace' and cls._ArcGISRasterExists(path):
            cls._LogDebug(_('%(class)s: Deleting existing ArcGIS raster "%(path)s".'), {'class': cls.__name__, 'path': path})
            try:
                gp.Delete_management(path)
            except Exception as e:
                raise RuntimeError(_('Failed to delete the existing ArcGIS raster "%(path)s" due to %(e)s: %(msg)s') % {'path': path, 'e': e.__class__.__name__, 'msg': e})

        # Otherwise, if the path is a file system path, create the parent
        # directories, if they do not exist already. Use ArcGIS's
        # CreateFolder_management tool, so the ArcGIS catalog is aware of the
        # directories.

        elif (path[0] in ['/', '\\'] or hasattr(os.path, 'splitdrive') and os.path.splitdrive(path)[0] != '') and not os.path.exists(os.path.dirname(path)):
            cls._LogDebug(_('%(class)s: Creating directory "%(path)s".'), {'class': cls.__name__, 'path': os.path.dirname(path)})

            if hasattr(os.path, 'splitdrive') and os.path.splitdrive(path)[0] != '':
                root, subdirs = os.path.splitdrive(os.path.dirname(path))
                root = root + os.path.sep
            else:
                root, subdirs = path[0], os.path.dirname(path)[1:]

            subdirsList = []
            while len(subdirs) > 1:
                subdirsList.insert(0, os.path.basename(subdirs))
                subdirs = os.path.dirname(subdirs)

            dirToCheck = root
            for subdir in subdirsList:
                if not os.path.isdir(os.path.join(dirToCheck, subdir)):
                    try:
                        gp.CreateFolder_management(dirToCheck, subdir)
                    except Exception as e:
                        raise RuntimeError(_('Failed to create the directory "%(path)s" due to %(e)s: %(msg)s') % {'path': os.path.join(dirToCheck, subdir), 'e': e.__class__.__name__, 'msg': e})
                dirToCheck = os.path.join(dirToCheck, subdir)

        # If the output format is ArcInfo binary grid, verify that the raster
        # name conforms to ArcGIS's rules and if not, raise a helpful error
        # message. (Many users make mistakes with binary grid names but cannot
        # tell what went wrong from ArcGIS's unhelpful error messages.)

        outputIsFile = os.path.isdir(os.path.dirname(path)) and os.path.splitext(os.path.dirname(path))[1].lower() != '.gdb'
        outputIsAIG = outputIsFile and '.' not in os.path.basename(path)
        if outputIsAIG:
            rasterName = os.path.basename(path)
            if ' ' in rasterName:
                raise ValueError(_('Cannot create an ArcGIS raster named "%(path)s" because the raster\'s name contains a space. The names of rasters in ArcInfo Binary Grid format cannot contain spaces.') % {'path': path})
            if rasterName[0] >= '0' and rasterName[0] <= '9':
                raise ValueError(_('Cannot create an ArcGIS raster named "%(path)s" because the raster\'s name starts with a number. The names of rasters in ArcInfo Binary Grid format cannot start with numbers.') % {'path': path})
            if len(sourceDatasets) > 1:
                if len(rasterName) > 9:
                    raise ValueError(_('Cannot create an ArcGIS grid stack named "%(path)s" because the grid stack\'s name is longer than nine characters. The names of ArcGIS grid stacks must be no longer than nine characters.') % {'path': path})
            elif len(rasterName) > 13:
                raise ValueError(_('Cannot create an ArcGIS raster named "%(path)s" because the raster\'s name is longer than thirteen characters. The names of rasters in ArcInfo Binary Grid format must be no longer than thirteen characters.') % {'path': path})

        # At this point, the raster should not exist. If the destination is
        # the file system (rather than a geodatabase) and the output format
        # one that GDAL can create, use GDAL to create the raster directly at
        # the destination path. This will be much faster than calling any
        # geoprocessor functions.
        #
        # Use GDAL to calculate statistics. The geoprocessor's function for
        # calculating statistics is very slow compared to GDAL. While older
        # versions of GDAL could not save the statistics in a way that would
        # work with ArcGIS, it seems to be working now (I am currently
        # testing with GDAL 3.7).

        if outputIsFile and not outputIsAIG and os.path.splitext(path)[1].lower() not in ['.asc', '.gif', '.j2c', '.j2k', '.jp2', '.jpc', '.jpe', '.jpg', '.jpeg', '.jpx', '.png', '.txt']:
            cls._LogDebug(_('%(class)s: Creating ArcGIS raster "%(path)s" with GDAL.'), {'class': cls.__name__, 'path': path})
            GDALDataset._ImportDatasetsToPath(path, sourceDatasets, mode, None, {'useArcGISSpatialReference': True, 'useUnscaledData': useUnscaledData, 'calculateStatistics': calculateStatistics, 'calculateHistogram': calculateHistogram, 'blockSize': blockSize})
            
        # Otherwise, create a temporary directory, write an IMG file to it
        # with GDAL, and copy the IMG file to the destination path.

        else:
            # If the raster is being stored in a geodatabase, replace
            # characters other than letters, numbers, and underscores with an
            # underscore and log a warning.

            outputWorkspace, oldName = os.path.split(path)
            if len(outputWorkspace) > 0 and len(oldName) > 0:
                d = gp.Describe(outputWorkspace)
                if str(d.DataType).lower() == 'workspace' and str(d.DataType).lower() != 'filesystem':
                    newName = re.sub('[^A-Za-z0-9_]', '_', oldName)
                    if newName != oldName:
                        nameWarning = _('The raster name "%(oldName)s" contains characters that are not allowed in the destination workspace "%(outputWorkspace)s". The raster will be given the name "%(newName)s" instead.') % {'oldName': oldName, 'newName': newName, 'outputWorkspace': outputWorkspace}
                        if options is not None and 'suppressRenameWarning' in options and options['suppressRenameWarning']:
                            cls._LogDebug(nameWarning)
                        else:
                            cls._LogWarning(nameWarning)

                        path = os.path.join(outputWorkspace, newName)

            cls._LogDebug(_('%(class)s: Creating ArcGIS raster "%(path)s" by creating a temporary IMG file and then copying it with the geoprocessor.'), {'class': cls.__name__, 'path': path})

            # Create a temporary directory.

            tempDir = tempfile.mkdtemp(prefix='GeoEco_' + cls.__name__ + '_Temp_')
            cls._LogDebug(_('%(class)s: Created temporary directory %(dir)s.'), {'class': cls.__name__, 'dir': tempDir})

            try:
                # Write the IMG file to the temporary directory.

                tempRaster = os.path.join(tempDir, 'raster.img')
                GDALDataset._ImportDatasetsToPath(tempRaster, sourceDatasets, mode, None, {'useArcGISSpatialReference': True, 'useUnscaledData': useUnscaledData, 'calculateStatistics': calculateStatistics, 'calculateHistogram': calculateHistogram, 'blockSize': blockSize})

                # If the destination raster is an ArcInfo ASCII grid,
                # use the RasterToASCII_conversion tool to create it.

                if os.path.splitext(path)[1].lower() in ['.asc', '.txt']:
                    cls._LogDebug(_('%(class)s: Converting "%(src)s" to "%(dest)s".'), {'class': cls.__name__, 'src': tempRaster, 'dest': path})
                    gp.RasterToASCII_conversion(tempRaster, path)

                # Otherwise we'll use CopyRaster_management.

                else:
                    cls._LogDebug(_('%(class)s: Copying "%(src)s" to "%(dest)s".'), {'class': cls.__name__, 'src': tempRaster, 'dest': path})
                    gp.CopyRaster_management(tempRaster, path)

            # Delete the temporary directory.

            finally:
                cls._LogDebug(_('%(class)s: Deleting temporary directory %(dir)s.'), {'class': cls.__name__, 'dir': tempDir})
                shutil.rmtree(tempDir, onerror=DatasetCollection._LogFailedRemoval)

        # The raster now exists at the final destination. If any of the
        # additional processing steps fail, delete the raster.

        try:
            # Build the raster attribute table. This can only be done for
            # single-band integer rasters.

            if buildRAT and len(sourceDatasets) == 1 and (useUnscaledData and sourceDatasets[0].UnscaledDataType in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32'] or not useUnscaledData and sourceDatasets[0].DataType in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32']):
                cls._LogDebug(_('%(class)s: Building a raster attribute table for ArcGIS raster "%(path)s".'), {'class': cls.__name__, 'path': path})
                gp.BuildRasterAttributeTable_management(path)

            # Build pyramids.

            if buildPyramids:
                cls._LogDebug(_('%(class)s: Building pyramids for ArcGIS raster "%(path)s".'), {'class': cls.__name__, 'path': path})
                gp.BuildPyramids_management(path)
                
        except:
            cls._LogDebug(_('%(class)s: Deleting partially-created ArcGIS raster "%(path)s" because an error was raised during creation.'), {'class': cls.__name__, 'path': path})
            try:
                gp.Delete_management(path)
            except Exception as e:
                cls._LogWarning(_('Failed to delete the partially-created ArcGIS raster "%(path)s" due to %(e)s: %(msg)s') % {'path': path, 'e': e.__class__.__name__, 'msg': e})
            raise

        # Report progress.

        if progressReporter is not None:
            progressReporter.ReportProgress(reinitializeArcGISProgressor=True)

    @classmethod
    def GetRasterBand(cls, path, band=1, decompressedFileToReturn=None, cacheDirectory=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        with ArcGISRaster(path, decompressedFileToReturn=decompressedFileToReturn, cacheDirectory=cacheDirectory) as dataset:
            grids = dataset.QueryDatasets('Band = %i' % band, reportProgress=False)
            if len(grids) <= 0:
                raise ValueError(_('Cannot retrieve band %(band)i from %(dn)s. The band does not exist.') % {'band': band, 'dn': dataset.DisplayName})
            return grids[0]

    @classmethod
    def CreateRaster(cls, path, grid, overwriteExisting=False, **options):
        cls.__doc__.Obj.ValidateMethodInvocation()

        from . import ArcGISWorkspace

        ws = ArcGISWorkspace(path=os.path.dirname(path),
                             datasetType=ArcGISRaster,
                             pathCreationExpressions=[os.path.basename(path)])

        ws.ImportDatasets(datasets=[grid], 
                          mode='Replace' if overwriteExisting else 'Add',
                          reportProgress=False,
                          options=options)


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
