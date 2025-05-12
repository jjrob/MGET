# _GDALDataset.py - Defines GDALDataset, a FileDatasetCollection of
# GDALRasterBands accessed through GDAL's osgeo.ogr.Dataset class
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import contextlib
import os

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Logging import Logger
from ...Types import IntegerTypeMetadata

from .. import Dataset, Grid, QueryableAttribute
from ..Collections import DirectoryTree, FileDatasetCollection
from ._GDALRasterBand import GDALRasterBand


class GDALDataset(FileDatasetCollection):
    __doc__ = DynamicDocString()

    def _GetIsUpdatable(self):
        return self._IsUpdatable

    IsUpdatable = property(_GetIsUpdatable, doc=DynamicDocString())

    def __init__(self, path, updatable=False, decompressedFileToReturn=None, displayName=None, parentCollection=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None, warpOptions=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if updatable and warpOptions is not None:
            raise ValueError(_('updatable cannot be True when warpOptions is not None. You must either set updatable False, or set warpOptions to None.'))

        # Initialize our properties.
        
        self._IsUpdatable = updatable
        self._WarpOptions = warpOptions
        self._GDALDataset = None
        self._GDALDatasetToWarp = None
        self._OpenedFile = None
        self._GDALRasterBand = None
        self._OpenedBand = None

        if displayName is not None:
            self._DisplayName = displayName
        elif parentCollection is None:
            self._DisplayName = _('GDAL dataset "%(path)s"') % {'path': path}
        elif isinstance(parentCollection, DirectoryTree):
            self._DisplayName = _('GDAL dataset "%(path)s"') % {'path': os.path.join(parentCollection.Path, path)}
        else:
            self._DisplayName = _('GDAL dataset "%(path)s" from %(parent)s') % {'path': path, 'parent': parentCollection.DisplayName}

        # We allow querying for Grid datasets by band number. If the
        # parent collection(s) did not define the Band queryable
        # attribute, we must define it.

        queryableAttributes = None
        if parentCollection is not None:
            bandAttribute = parentCollection.GetQueryableAttribute('Band')
        if parentCollection is None or bandAttribute is None:
            bandAttribute = QueryableAttribute('Band', _('Band number'), IntegerTypeMetadata(minValue=1))
            queryableAttributes = (bandAttribute,)

        # Initialize the base class.

        super(GDALDataset, self).__init__(path, decompressedFileToReturn, parentCollection, queryableAttributes, queryableAttributeValues, lazyPropertyValues, cacheDirectory)

        # Validate that the caller has not assigned a value to the
        # Band queryable attribute, either directly to us or to our
        # parent collection(s).

        if self.GetQueryableAttributeValue('Band') is not None:
            raise ValueError(_('This GDALDataset or its parent collection(s) specify a value for the Band queryable attribute. This is not allowed, as the value of that queryable attribute is assigned by the GDALRasterBand class.'))

        # Assign values to known lazy properties.

        self.SetLazyPropertyValue('PhysicalDimensions', 'yx')

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known property, return None.

        if name not in ['Bands', 'SpatialReference', 'Shape', 'CoordIncrements', 'CornerCoords', 'PhysicalDimensionsFlipped']:
            return None

        # Open the GDAL dataset, if not opened already.

        self._Open()

        # Retrieve Bands, SpatialReference, and Shape. Note that we
        # only set the value of SpatialReference if it has not been
        # set already. This allows the caller that instantiated us to
        # override SpatialReference. That capability is used when the
        # caller knows that the dataset was created by ArcGIS with an
        # ESRI-specific WKT string, which GDAL will not recognize.

        self.SetLazyPropertyValue('Bands', self._GDALDataset.RasterCount)

        if 'SpatialReference' not in self._LazyPropertyValues:
            self.SetLazyPropertyValue('SpatialReference', Dataset.ConvertSpatialReference('wkt', self._GDALDataset.GetProjection(), 'obj'))
        
        self.SetLazyPropertyValue('Shape', (self._GDALDataset.RasterYSize, self._GDALDataset.RasterXSize))

        # Retrieve CoordIncrements, CornerCoords, and
        # PhysicalDimensionsFlipped from the GDAL affine.
        #
        # All GDAL datasets I have seen have:
        #
        #     * A positive affine[5]
        #     * A negative affine[1]
        #     * Zero for affine[2] and affine[4]
        #
        # For these datasets:
        #
        #     * affine[0] and affine[3] are the x and y coords of the
        #       upper left corner of the upper left cell.
        #
        #     * affine[1] is the x cell size. affine[5] is the y cell
        #       size, although it is negative.
        #
        #     * The x coordinate increases as the x index increases
        #       while the y coordinate decreases as the y index
        #       increases. Because our convention requires all
        #       coordinates to increase as indices increase, we
        #       consider those datasets to have flipped y coordinates.
        #
        # It seems fairly clear how to handle the cases where
        # affine[1] and affine[5] have different signs than positive
        # and negative respectively. so we do so even though I have
        # not seen an example where the signs are different.
        #
        # It is not clear how to handle cases where affine[2] and
        # affine[4] are non-zero. It probably means that the dimension
        # order is reversed, but for now, we just fail.
        
        affine = self._GDALDataset.GetGeoTransform()
        if affine[2] != 0 or affine[4] != 0:
            raise RuntimeError(_('%(dn)s cannot be processed because it has non-zero values for the third and/or fifth affine transformation coefficients (the six coefficients are %(affine)s). Datasets with non-zero values for these coefficients are not currently supported. Please contact the author of this tool for assistance.') % {'dn': self._DisplayName, 'affine': repr(affine)})

        self.SetLazyPropertyValue('CoordIncrements', (abs(affine[5]), abs(affine[1])))
        self.SetLazyPropertyValue('CornerCoords', (min(affine[3] + affine[5]/2, affine[3] + self._GDALDataset.RasterYSize*affine[5] - affine[5]/2), min(affine[0] + affine[1]/2, affine[0] + self._GDALDataset.RasterXSize*affine[1] - affine[1]/2)))
        self.SetLazyPropertyValue('PhysicalDimensionsFlipped', (affine[5] < 0, affine[1] < 0))

        # Log a debug message with the properties of the GDAL dataset.

        self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: Bands=%(Bands)s, Dimensions=yx, Shape=%(Shape)s, CoordIncrements=%(CoordIncrements)s, CornerCoords=%(CornerCoords)s, PhysicalDimensions=%(PhysicalDimensions)s, PhysicalDimensionsFlipped=%(PhysicalDimensionsFlipped)s, SpatialReference=%(SpatialReference)s.'),
                       {'class': self.__class__.__name__,
                        'id': id(self),
                        'dn': self.DisplayName,
                        'Bands': repr(self.GetLazyPropertyValue('Bands')),
                        'Shape': repr(self.GetLazyPropertyValue('Shape')),
                        'CoordIncrements': repr(self.GetLazyPropertyValue('CoordIncrements')),
                        'CornerCoords': repr(self.GetLazyPropertyValue('CornerCoords')),
                        'PhysicalDimensions': self.GetLazyPropertyValue('PhysicalDimensions'),
                        'PhysicalDimensionsFlipped': repr(self.GetLazyPropertyValue('PhysicalDimensionsFlipped')),
                        'SpatialReference': repr(Dataset.ConvertSpatialReference('obj', self.GetLazyPropertyValue('SpatialReference'), 'wkt'))})

        # Return the property value.

        return self.GetLazyPropertyValue(name)

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):

        # Go through the bands of this dataset, testing whether each
        # one matches the query expression. For each match, construct
        # a GDALRasterBand and add it to our list of datasets to
        # return.

        datasetsFound = []

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
                datasetsFound.append(GDALRasterBand(self, band))
                if progressReporter is not None:
                    progressReporter.ReportProgress()

        return datasetsFound

    def _Open(self):
        if self._GDALDataset is None:
            # Get the GDAL-openable path for this GDAL dataset. If the
            # dataset is part of a remote collection and/or
            # compressed, this will cause it to be downloaded and/or
            # decompressed.

            path, isOriginalFile = self._GetOpenableFile()

            # If this is not the same thing as our original path,
            # update our display name to reflect it.

            if not isOriginalFile:
                if self.ParentCollection is None:
                    self._DisplayName = _('GDAL dataset "%(path)s" (decompressed from "%(oldpath)s")') % {'path': path, 'oldpath': self.Path}
                elif isinstance(self.ParentCollection, DirectoryTree):
                    self._DisplayName = _('GDAL dataset "%(path)s" (decompressed from "%(oldpath)s")') % {'path': path, 'oldpath': os.path.join(self.ParentCollection.Path, self.Path)}
                else:
                    self._DisplayName = _('GDAL dataset "%(path)s" (a local copy of "%(oldpath)s" from %(parent)s)') % {'path': path, 'oldpath': self.Path, 'parent': parentCollection.DisplayName}

            # Open the dataset with GDAL.
            
            gdal = self._gdal()
            gdal.ErrorReset()
            gdalconst = self._gdalconst()

            if self.IsUpdatable:
                self._LogDebug(_('%(class)s 0x%(id)016X: Opening %(dn)s in update mode.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: Opening %(dn)s in read-only mode.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})

            gdal.PushErrorHandler(self._LogGDALWarnings)
            try:
                try:
                    ds = gdal.Open(path, {False: gdalconst.GA_ReadOnly, True: gdalconst.GA_Update}[self.IsUpdatable])
                except Exception as e:
                    gdal.ErrorReset()
                    if self.IsUpdatable:
                        raise RuntimeError(_('%(dn)s could not be opened with the Geospatial Data Abstraction Library (GDAL). Verify that the dataset exists, is writable, is in a format supported by GDAL, and that the GDAL driver for this format supports writing. For a list of supported formats, see http://www.gdal.org/formats_list.html. If the format is not supported, find a way to convert it to a supported format. If you have trouble deciding which supported format to use, we suggest ERDAS IMAGINE (.img), or GeoTIFF (.tif). Detailed error information: gdal.Open() reported %(e)s: %(msg)s.') % {'dn': self._DisplayName, 'e': e.__class__.__name__, 'msg': e})
                    else:
                        raise RuntimeError(_('%(dn)s could not be opened with the Geospatial Data Abstraction Library (GDAL). Verify that the dataset exists, is accessible, and in a format supported by GDAL. For a list of supported formats, see http://www.gdal.org/formats_list.html. If the format is not supported, find a way to convert it to a supported format. If you have trouble deciding which supported format to use, we suggest ERDAS IMAGINE (.img) or GeoTIFF (.tif). Detailed error information: gdal.Open() reported %(e)s: %(msg)s.') % {'dn': self._DisplayName, 'e': e.__class__.__name__, 'msg': e})
            finally:
                gdal.PopErrorHandler()

            self._LogDebug(_('%(class)s 0x%(id)016X: Opened %(dn)s with the GDAL %(driver)s driver.') % {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName, 'driver': ds.GetDriver().LongName})

            if ds.RasterCount <= 0:
                raise ValueError(_('%(dn)s cannot be used because it does not have any bands.') % {'dn': self._DisplayName})

            if self._WarpOptions is not None:
                self._LogDebug(_("%(class)s 0x%(id)016X: Invoking gdal.Warp('', ds, format='VRT', options={%(opts)s}).") % {'class': self.__class__.__name__, 'id': id(self), 'opts': [', '.join([repr(k) + ': ' + repr(v) for k, v in self._WarpOptions.items()])]})
                self._GDALDataset = gdal.Warp('', ds, format='VRT', **self._WarpOptions)
                self._GDALDatasetToWarp = ds
            else:
                self._GDALDataset = ds

            self._OpenedFile = path

            self._RegisterForCloseAtExit()

    def _LogGDALWarnings(self, err_class, err_no, err_msg):

        # When opening .img (ERDAS) rasters that have nan is the NoData value,
        # GDAL will issue "Warning 1: NaN converted to INT_MAX." As far as we
        # can tell, this has no practical ramifications. If we get it, just
        # log a DEBUG message.

        gdal = self._gdal()
        gdalconst = self._gdalconst()

        if err_class == gdalconst.CE_Warning and 'NaN converted to INT_MAX' in err_msg:
            self._LogDebug(_('%(class)s 0x%(id)016X: From GDAL: Warning %(err_no)s: %(err_msg)s') % {'class': self.__class__.__name__, 'id': id(self), 'err_no': err_no, 'err_msg': err_msg})

        # Otherwise, log other warnings as WARNING messages.

        elif err_class == gdalconst.CE_Warning:
            self._LogWarning(_('When opening %(dn)s, the Geospatial Data Abstraction Library (GDAL) reported Warning %(err_no)s: %(err_msg)s') % {'dn': self._DisplayName, 'err_no': err_no, 'err_msg': err_msg})

        # And allow the GDAL default error handler to handle the rest.

        else:
            gdal.CPLDefaultErrorHandler(err_class, err_no, err_msg)

    def _OpenBand(self, band):
        if self._GDALRasterBand is None or self._OpenedBand != band:
            if self._GDALRasterBand is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Closing band %(band)i.') % {'class': self.__class__.__name__, 'id': id(self), 'band': self._OpenedBand})
                self._GDALRasterBand = None
                self._OpenedBand = None
            else:
                self._Open()

            self._LogDebug(_('%(class)s 0x%(id)016X: Opening band %(band)i.') % {'class': self.__class__.__name__, 'id': id(self), 'band': band})
            try:
                self._GDALRasterBand = self._GDALDataset.GetRasterBand(band)
            except Exception as e:
                self._gdal().ErrorReset()
                raise RuntimeError(_('Could not open band %(band)i of %(dn)s with the Geospatial Data Abstraction Library (GDAL). Verify that the band number is valid and that the dataset exists and is readable. Detailed error information: dataset.GetRasterBand(%(band)i) reported %(e)s: %(msg)s.') % {'dn': self.DisplayName, 'band': band, 'e': e.__class__.__name__, 'msg': e})
            self._OpenedBand = band

        return self._GDALRasterBand

    def _Close(self):
        if hasattr(self, '_GDALDataset') and self._GDALDataset is not None:
            if self._GDALRasterBand is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Closing band %(band)i.') % {'class': self.__class__.__name__, 'id': id(self), 'band': self._OpenedBand})
                self._GDALRasterBand = None
                self._OpenedBand = None
                
            self._LogDebug(_('%(class)s 0x%(id)016X: Closing %(dn)s.') % {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
            self._GDALDatasetToWarp = None
            self._GDALDataset = None
            self._OpenedFile = None

        super(GDALDataset, self)._Close()

    @classmethod
    def _RemoveExistingDatasetsFromList(cls, path, datasets, progressReporter):

        # Because very few GDAL drivers support adding bands to
        # existing GDAL datasets, we cannot implement 'add' mode in
        # the way that most people would expect (that is, if
        # len(datasets) is greater than the number of existing bands,
        # add the remaining datasets as new bands). Instead we assume
        # that if the GDAL dataset exists, it already has all of the
        # necessary bands. Thus, if it exists, remove all of the
        # datasets from the caller's list.

        numDatasets = len(datasets)

        if cls._GDALDatasetExists(path):
            cls._LogDebug(_('%(class)s: GDAL dataset "%(path)s" exists.'), {'class': cls.__name__, 'path': path})
            while len(datasets) > 0:
                del datasets[0]
        else:
            cls._LogDebug(_('%(class)s: GDAL dataset "%(path)s" does not exist.'), {'class': cls.__name__, 'path': path})

        # Report that we checked all of these datasets.

        if progressReporter is not None:
            progressReporter.ReportProgress(numDatasets)

    @classmethod
    def _GDALDatasetExists(cls, gdalDatasetName):

        # Check whether gdalDatasetName is a file system path. If it
        # is, determine its existence using the file system. This is
        # presumably faster than trying to open it with GDAL.

        if gdalDatasetName[0] in ['/', '\\'] or hasattr(os.path, 'splitdrive') and os.path.splitdrive(gdalDatasetName)[0] != '':
            return os.path.exists(gdalDatasetName)

        # gdalDatasetName is not a file system path. Determine its
        # existence by trying to open it with GDAL.

        gdal = cls._gdal()
        try:
            gdalDataset = gdal.OpenShared(gdalDatasetName)
        except:
            gdal.ErrorReset()
            return False
        
        return gdalDataset is not None

    @classmethod
    def _ImportDatasetsToPath(cls, path, sourceDatasets, mode, progressReporter, options):

        # Unpack the options dictionary.

        gdal = cls._gdal()
        gdal.ErrorReset()

        if 'gdalDriverName' in options:
            driver = gdal.GetDriverByName(options['gdalDriverName'])
            if driver is None:
                raise ValueError(_('Cannot import %(dn)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" using the GDAL "%(driver)s". GDAL does not have a driver with that name.') % {'dn': dataset.DisplayName, 'path': path, 'driver': options['gdalDriverName']})
        else:
            driver = None

        useArcGISSpatialReference = 'useArcGISSpatialReference' in options and options['useArcGISSpatialReference']
        useUnscaledData = 'useUnscaledData' in options and options['useUnscaledData']
        calculateStatistics = 'calculateStatistics' not in options or options['calculateStatistics']        # Note that default for calculateStatistics is True
        calculateHistogram = 'calculateHistogram' not in options or options['calculateHistogram']           # Note that default for calculateHistogram is True

        if 'overviewResamplingMethod' in options and 'overviewList' in options:
            overviewResamplingMethod = options['overviewResamplingMethod']
            overviewList = options['overviewList']
            if not isinstance(overviewList, (list, tuple)) or len(overviewList) <= 0:
                raise TypeError(_('The value for overviewList in the import options must be a list or tuple of one or more integers.'))
            overviewList = list(overviewList)
            for i in overviewList:
                if not isinstance(i, int):
                    raise TypeError(_('The value for overviewList in the import options may only contain integers.'))
        else:
            overviewResamplingMethod = None
            overviewList = None

        gdalCreateOptions = []
        if 'gdalCreateOptions' in options:
            if not isinstance(options['gdalCreateOptions'], (list, tuple)):
                raise TypeError(_('The value for gdalCreateOptions in the import options must be a list or tuple of strings.'))
            gdalCreateOptions.extend(options['gdalCreateOptions'])

        if 'blockSize' in options and options['blockSize'] is not None:
            if not isinstance(options['blockSize'], int) or options['blockSize'] < 1024:
                raise TypeError(_('The value for blockSize in the import options must be an integer that is greater than or equal to 1024.'))
            blockSize = options['blockSize']
        else:
            blockSize = 32*1024*1024        # Default of 32 MB blocks when copying

        # Instruct GDAL to force statistics and histogram metadata to be
        # written to a .aux.xml file, which is what ArcGIS needs. At the time
        # of this writing, my understanding is that the only driver that uses
        # this option is GTiff. But there is no harm in setting it regardless
        # of what driver we will use.
        #
        # An added complication here is that older versions of GDAL do not
        # have the config_options context manager. So we define an
        # _OptionalContextManager that allows us to use it if it exists.

        class _OptionalContextManager:
            def __init__(self, context_manager=None):
                self.context_manager = context_manager

            def __enter__(self):
                if self.context_manager:
                    return self.context_manager.__enter__()

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.context_manager:
                    return self.context_manager.__exit__(exc_type, exc_val, exc_tb)

        if hasattr(gdal, 'config_options'):
            context = _OptionalContextManager(gdal.config_options({'ESRI_XML_PAM': 'TRUE'}))
        else:
            context = _OptionalContextManager()

        with context:

            # If the caller did not specify a GDALDriverName in the
            # options, try to guess a driver name from the path's
            # extension.

            if driver is None:
                if not hasattr(GDALDataset, '_GDALWritableDriverNameForExtension'):
                    GDALDataset._GDALWritableDriverNameForExtension = {'.asc': 'AAIGrid',
                                                                       '.bil': 'EHdr',
                                                                       '.blx': 'BLX',
                                                                       '.bmp': 'BMP',
                                                                       '.bt': 'BT',
                                                                       '.dem': 'USGSDEM',
                                                                       '.dt0': 'DTED',
                                                                       '.dt1': 'DTED',
                                                                       '.dt2': 'DTED',
                                                                       '.gen': 'ADRG',
                                                                       '.gif': 'GIF',
                                                                       '.img': 'HFA',
                                                                       '.jpc': 'JPEG',
                                                                       '.jpe': 'JPEG',
                                                                       '.jpg': 'JPEG',
                                                                       '.jpeg': 'JPEG',
                                                                       '.mpl': 'ILWIS',
                                                                       '.mpr': 'ILWIS',
                                                                       '.sdat': 'SDAT',
                                                                       '.ter': 'Terragen',
                                                                       '.terrain': 'Terragen',
                                                                       '.thf': 'ADRG',
                                                                       '.tff': 'GTiff',
                                                                       '.tif': 'GTiff',
                                                                       '.tiff': 'GTiff',
                                                                       '.txt': 'AAIGrid',
                                                                       '.xlb': 'BLX',
                                                                       '.xpm': 'XPM'}

                ext = os.path.splitext(path)[1].lower()
                if ext in GDALDataset._GDALWritableDriverNameForExtension:
                    driver = gdal.GetDriverByName(GDALDataset._GDALWritableDriverNameForExtension[ext])
                    if driver is None:
                        raise ValueError(_('Cannot open Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" using the GDAL "%(driver)s". GDAL was expected to have a driver with that name but does not. Please contact the author of this tool for assistance.') % {'path': path, 'driver': GDALDataset._GDALWritableDriverNameForExtension[ext]})
                else:
                    raise ValueError(_('Cannot open Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because a GDALDriverName was not specified in the import options and we could not guess the driver from the destination name. Please provide a value for the GDALDriverName option and try again.') % {'path': path})

            # Validate that the source datasets are all Grids and have
            # dimensions 'yx', evenly-spaced coordinates, valid data
            # types, and the same spatial reference, shape, coordinate
            # increments, corner coordinates, and data type.

            if not hasattr(GDALDataset, '_GDALDataTypeForNumpyDataType'):
                GDALDataset._GDALDataTypeForNumpyDataType = {'uint8': gdal.GDT_Byte,
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
                    raise TypeError(_('Cannot import %(dn)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because it is a %(type)s, which is not a Grid. It must be a Grid to be imported into a GDAL dataset.') % {'dn': dataset.DisplayName, 'path': path, 'type': dataset.__class__.__name__})
                if dataset.Dimensions != 'yx':
                    raise ValueError(_('Cannot import %(dn)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because it has dimensions "%(dim)s". It must have dimensions "yx" to be imported into a GDAL dataset.') % {'dn': dataset.DisplayName, 'path': path, 'dim': dataset.Dimensions})
                if dataset.CoordDependencies != (None, None):
                    raise ValueError(_('Cannot import %(dn)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because it does not have evenly-spaced coordinates (the coordinate dependencies are %(deps)s). It must have evenly-spaced coordinates (coordinate dependencies of (None, None)) to be imported into a GDAL dataset.') % {'dn': dataset.DisplayName, 'path': path, 'deps': repr(dataset.CoordDependencies)})
                if useUnscaledData:
                    if dataset.UnscaledDataType not in list(GDALDataset._GDALDataTypeForNumpyDataType.keys()):
                        raise ValueError(_('Cannot import %(dn)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because it has the unscaled data type %(dt)s. To be imported into a GDAL dataset, it must have one of the following unscaled data types: %(dts)s.') % {'dn': dataset.DisplayName, 'path': path, 'dt': dataset.UnscaledDataType, 'dts': ', '.join(list(GDALDataset._GDALDataTypeForNumpyDataType.keys()))})
                elif dataset.DataType not in list(GDALDataset._GDALDataTypeForNumpyDataType.keys()):
                    raise ValueError(_('Cannot import %(dn)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because it has the data type %(dt)s. To be imported into a GDAL dataset, it must have one of the following data types: %(dts)s.') % {'dn': dataset.DisplayName, 'path': path, 'dt': dataset.DataType, 'dts': ', '.join(list(GDALDataset._GDALDataTypeForNumpyDataType.keys()))})

            for i in range(1, len(sourceDatasets)):
                if not sourceDatasets[0].GetSpatialReference('obj').IsSame(sourceDatasets[i].GetSpatialReference('obj')):
                    raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because the two source datasets have different spatial references (%(sr1)s and %(sr2)s). All of the bands of a GDAL dataset must have the same spatial reference.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'sr1': repr(sourceDatasets[0].GetSpatialReference('wkt')), 'sr2': repr(sourceDatasets[i].GetSpatialReference('wkt'))})
                if sourceDatasets[0].Shape != sourceDatasets[i].Shape:
                    raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because the two source datasets have different shapes (%(shape1)s and %(shape2)s). All of the bands of a GDAL dataset must have the same shape.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'shape1': repr(sourceDatasets[0].Shape), 'shape2': repr(sourceDatasets[i].Shape)})
                if sourceDatasets[0].CoordIncrements != sourceDatasets[i].CoordIncrements:
                    raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because the two source datasets have different coordinate increments (%(incr1)s and %(incr2)s). All of the bands of a GDAL dataset must have the same coordinate increments.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'incr1': repr(sourceDatasets[0].CoordIncrements), 'incr2': repr(sourceDatasets[i].CoordIncrements)})
                if sourceDatasets[0].MinCoords['x',0] != sourceDatasets[i].MinCoords['x',0]:
                    raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because the two source datasets have different minimum x coordinates (%(c1)s and %(c2)s). All of the bands of a GDAL dataset must have the same corner coordinates.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'c1': repr(sourceDatasets[0].MinCoords['x',0]), 'c2': repr(sourceDatasets[i].MinCoords['x',0])})
                if sourceDatasets[0].MinCoords['y',0] != sourceDatasets[i].MinCoords['y',0]:
                    raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because the two source datasets have different minimum y coordinates (%(c1)s and %(c2)s). All of the bands of a GDAL dataset must have the same corner coordinates.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'c1': repr(sourceDatasets[0].MinCoords['y',0]), 'c2': repr(sourceDatasets[i].MinCoords['y',0])})
                if useUnscaledData:
                    if sourceDatasets[0].UnscaledDataType != sourceDatasets[i].UnscaledDataType:
                        raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because the two source datasets have different unscaled data types (%(dt1)s and %(dt2)s). All of the bands of a GDAL dataset must have the same data type.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'dt1': sourceDatasets[0].UnscaledDataType, 'dt2': sourceDatasets[i].UnscaledDataType})
                elif sourceDatasets[0].DataType != sourceDatasets[i].DataType:
                    raise ValueError(_('Cannot import both %(dn1)s and %(dn2)s into Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" because the two source datasets have different data types (%(dt1)s and %(dt2)s). All of the bands of a GDAL dataset must have the same data type.') % {'dn1': sourceDatasets[0].DisplayName, 'dn2': sourceDatasets[i].DisplayName, 'path': path, 'dt1': sourceDatasets[0].DataType, 'dt2': sourceDatasets[i].DataType})

            # If the mode is 'replace' and the GDAL dataset exists, delete
            # it using the GDAL driver.

            if mode == 'replace' and cls._GDALDatasetExists(path):
                cls._LogDebug(_('%(class)s: Deleting existing GDAL dataset "%(path)s".'), {'class': cls.__name__, 'path': path})
                try:
                    driver.Delete(path)
                except Exception as e:
                    gdal.ErrorReset()
                    raise RuntimeError(_('Failed to delete the existing Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" using the GDAL %(driver)s driver. The driver\'s Delete function failed with %(e)s: %(msg)s') % {'path': path, 'driver': driver.LongName, 'e': e.__class__.__name__, 'msg': e})

                # Also delete various files that may have been created by
                # ArcGIS but that are not deleted by GDAL.

                otherFiles = [path + '.xml', path + '.vat.dbf']

                for f in otherFiles:
                    if os.path.isfile(f):
                        try:
                            os.remove(f)
                        except Exception as e:
                            raise RuntimeError(_('Failed to delete file "%(file)s". Python\'s os.remove function failed with %(e)s: %(msg)s') % {'file': f, 'e': e.__class__.__name__, 'msg': e})

            # Otherwise, if the path is a file system path, create the
            # parent directories, if they do not exist already.

            elif (path[0] in ['/', '\\'] or hasattr(os.path, 'splitdrive') and os.path.splitdrive(path)[0] != '') and not os.path.isdir(os.path.dirname(path)):
                cls._LogDebug(_('%(class)s: Creating directory "%(path)s".'), {'class': cls.__name__, 'path': os.path.dirname(path)})
                try:
                    os.makedirs(os.path.dirname(path))
                except Exception as e:
                    raise RuntimeError(_('Failed to create directory "%(path)s". Python\'s os.makedirs function failed and reported %(e)s: %(msg)s') % {'path': os.path.dirname(path), 'e': e.__class__.__name__, 'msg': e})
            
            # At this point, the GDAL dataset should not exist and we need
            # to create it. First check whether the PIXELTYPE option is
            # assigned properly.

            if useUnscaledData:
                dataType = sourceDatasets[0].UnscaledDataType
            else:
                dataType = sourceDatasets[0].DataType

            if dataType == 'int8':
                if 'PIXELTYPE=DEFAULT' in gdalCreateOptions:
                    gdalCreateOptions.remove('PIXELTYPE=DEFAULT')
                if 'PIXELTYPE=SIGNEDBYTE' not in gdalCreateOptions:
                    gdalCreateOptions.append('PIXELTYPE=SIGNEDBYTE')
            elif 'PIXELTYPE=SIGNEDBYTE' in gdalCreateOptions:
                gdalCreateOptions.remove('PIXELTYPE=SIGNEDBYTE')

            # For most GDAL drivers, the default values of the creation
            # options seem designed to maximize compatibility of the
            # output files with as many other applications as possible. We
            # are mainly interested in maintaining compatibility for two
            # applications, ArcGIS and GDAL, which are what our users are
            # most likely to employ to work with the output files. To
            # maximize performance and functionality for those
            # applications, we tweak the default creation options for
            # certain drivers.

            if driver.ShortName == 'HFA':
                if useArcGISSpatialReference and 'FORCETOPESTRING=YES' not in gdalCreateOptions and 'FORCETOPESTRING=NO' not in gdalCreateOptions:
                    gdalCreateOptions.append('FORCETOPESTRING=YES')
                if 'COMPRESSED=YES' not in gdalCreateOptions and 'COMPRESSED=NO' not in gdalCreateOptions:
                    gdalCreateOptions.append('COMPRESSED=YES')

            # Now create the GDAL dataset and set the geographic transform
            # and spatial reference.

            transform = [sourceDatasets[0].MinCoords['x',0], sourceDatasets[0].CoordIncrements[1], 0.0, sourceDatasets[0].MaxCoords['y',-1], 0.0, 0.0 - sourceDatasets[0].CoordIncrements[0]]
            if sourceDatasets[0].GetSpatialReference('obj') is not None:
                if useArcGISSpatialReference:
                    sr = sourceDatasets[0].GetSpatialReference('arcgis')
                else:
                    sr = sourceDatasets[0].GetSpatialReference('wkt')
            else:
                sr = None

            cls._LogDebug(_('%(class)s: Creating GDAL dataset "%(path)s" with the GDAL %(driver)s driver: xsize=%(xsize)i, ysize=%(ysize)i, bands=%(bands)i, dataType=%(dt)s, options=%(options)s, transform=%(transform)s, spatialRef=%(sr)s.'),
                          {'class': cls.__name__,
                           'path': path,
                           'driver': driver.LongName,
                           'xsize': sourceDatasets[0].Shape[1],
                           'ysize': sourceDatasets[0].Shape[0],
                           'bands': len(sourceDatasets),
                           'dt': dataType,
                           'options': repr(gdalCreateOptions),
                           'transform': repr(transform),
                           'sr': repr(sr)})

            try:
                gdalDataset = driver.Create(path, sourceDatasets[0].Shape[1], sourceDatasets[0].Shape[0], len(sourceDatasets), GDALDataset._GDALDataTypeForNumpyDataType[dataType], gdalCreateOptions)
            except Exception as e:
                gdal.ErrorReset()
                raise RuntimeError(_('Failed to create the Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" using the GDAL %(driver)s driver with xsize=%(xsize)i, ysize=%(ysize)i, bands=%(bands)i, dataType=%(dt)s, options=%(options)s. The driver\'s Create function failed and reported %(e)s: %(msg)s') % {'path': path, 'driver': driver.LongName, 'xsize': sourceDatasets[0].Shape[1], 'ysize': sourceDatasets[0].Shape[0], 'bands': len(sourceDatasets), 'dt': dataType, 'options': repr(gdalCreateOptions), 'e': e.__class__.__name__, 'msg': e})

            try:
                try:
                    try:
                        gdalDataset.SetGeoTransform(transform)
                    except Exception as e:
                        gdal.ErrorReset()
                        raise RuntimeError(_('Failed to set the geographic transform of Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" (created with the GDAL %(driver)s driver) to %(transform)s. The GDAL SetGeoTransform function failed and reported %(e)s: %(msg)s.') % {'path': path, 'driver': driver.LongName, 'transform': repr(transform), 'e': e.__class__.__name__, 'msg': e})

                    if sr is not None:
                        try:
                            gdalDataset.SetProjection(sr)
                        except Exception as e:
                            gdal.ErrorReset()
                            raise RuntimeError(_('Failed to set the spatial reference of Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" (created with the GDAL %(driver)s driver) to %(sr)s. The GDAL SetProjection function failed and reported %(e)s: %(msg)s.') % {'path': path, 'driver': driver.LongName, 'sr': repr(sr), 'e': e.__class__.__name__, 'msg': e})

                    # Instantiate a GDALDataset instance for the newly-created
                    # GDAL dataset.

                    destDataset = cls(path, updatable=True)
                    destDataset._GDALDataset = gdalDataset
                    destDataset._OpenedFile = path
                    destDataset._RegisterForCloseAtExit()
                finally:
                    del gdalDataset

                try:
                    # Now we are ready to copy the source datasets to the
                    # bands of the newly-created GDAL dataset. To avoid
                    # exhausting system memory, we read up to 32 MB at a time
                    # before writing it out. To keep this simple and
                    # efficient, we only read complete rows of the grid.
                    # Compute the number of bytes in a row.

                    if dataType in ['int8', 'uint8']:
                        bytesPerCell = 1
                    elif dataType in ['int16', 'uint16']:
                        bytesPerCell = 2
                    elif dataType in ['int32', 'uint32', 'float32']:
                        bytesPerCell = 4
                    elif dataType in ['float64', 'complex32']:
                        bytesPerCell = 8
                    else:
                        bytesPerCell = 16

                    bytesPerRow = bytesPerCell * sourceDatasets[0].Shape[1]
                    
                    # Iterate through the source datasets, copying each one to
                    # a band of the GDAL dataset.

                    import numpy

                    for i in range(len(sourceDatasets)):
                        band = GDALRasterBand(destDataset, i+1)
                        try:
                            # Set the NoData value of the destination dataset
                            # to that of the source dataset.

                            if useUnscaledData:
                                noDataValue = sourceDatasets[i].UnscaledNoDataValue
                            else:
                                noDataValue = sourceDatasets[i].NoDataValue

                            if noDataValue is not None:
                                destDataset._OpenBand(i+1)
                                cls._LogDebug(_('%(class)s 0x%(id)016X: Setting NoData value of band %(band)i to %(nodata)s.') % {'class': cls.__name__, 'id': id(destDataset), 'band': i+1, 'nodata': repr(float(noDataValue))})
                                try:
                                    destDataset._GDALRasterBand.SetNoDataValue(float(noDataValue))
                                except Exception as e:
                                    gdal.ErrorReset()
                                    raise RuntimeError(_('Failed to set the NoData value of Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" (created with the GDAL %(driver)s driver) to %(nodata)s. The GDAL SetNoDataValue function failed and reported %(e)s: %(msg)s.') % {'path': path, 'driver': driver.LongName, 'nodata': repr(float(noDataValue)), 'e': e.__class__.__name__, 'msg': e})
                                
                            # Copy the data in blocks.
                            
                            rowsCopied = 0
                            rowsToCopy = blockSize // bytesPerRow
                            allNoData = noDataValue is not None

                            while rowsCopied < sourceDatasets[i].Shape[0]:
                                if rowsCopied + rowsToCopy > sourceDatasets[i].Shape[0]:
                                    rowsToCopy = sourceDatasets[i].Shape[0] - rowsCopied
                                    
                                if useUnscaledData:
                                    data = sourceDatasets[i].UnscaledData[rowsCopied:rowsCopied+rowsToCopy, :]
                                    band.UnscaledData[rowsCopied:rowsCopied+rowsToCopy, :] = data
                                else:
                                    data = sourceDatasets[i].Data[rowsCopied:rowsCopied+rowsToCopy, :]
                                    band.Data[rowsCopied:rowsCopied+rowsToCopy, :] = data

                                if allNoData:
                                    allNoData = numpy.all(data == noDataValue)
                                    
                                rowsCopied += rowsToCopy

                            # Calculate statistics and a histogram. By calling
                            # GDALRasterBand.GetStatistics() and
                            # GDALRasterBand.GetDefaultHistogram(), GDAL will
                            # write out a .aux.xml file containing the statistics
                            # and histogram.

                            if calculateStatistics:
                                if not allNoData:
                                    cls._LogDebug(_('%(class)s 0x%(id)016X: Calculating statistics for band %(band)i.') % {'class': cls.__name__, 'id': id(destDataset), 'band': i+1})
                                    try:
                                        statistics = destDataset._GDALRasterBand.GetStatistics(False, True)
                                    except Exception as e:
                                        gdal.ErrorReset()
                                        Logger.LogExceptionAsWarning(_('Failed to calculate the statistics for band %(band)i of Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" (created with the GDAL %(driver)s driver).') % {'band': i+1, 'path': path, 'driver': driver.LongName})
                                else:
                                    cls._LogDebug(_('%(class)s 0x%(id)016X: Not calculating statistics for band %(band)i because all of the cells are NoData.') % {'class': cls.__name__, 'id': id(destDataset), 'band': i+1})

                            if calculateHistogram:
                                if not allNoData:
                                    cls._LogDebug(_('%(class)s 0x%(id)016X: Calculating a histogram for band %(band)i.') % {'class': cls.__name__, 'id': id(destDataset), 'band': i+1})
                                    try:
                                        destDataset._GDALRasterBand.GetDefaultHistogram()
                                    except Exception as e:
                                        gdal.ErrorReset()
                                        Logger.LogExceptionAsWarning(_('Failed to calculate the histogram for band %(band)i of Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" (created with the GDAL %(driver)s driver).') % {'band': i+1, 'path': path, 'driver': driver.LongName})
                                else:
                                    cls._LogDebug(_('%(class)s 0x%(id)016X: Not calculating a histogram for band %(band)i because all of the cells are NoData.') % {'class': cls.__name__, 'id': id(destDataset), 'band': i+1})

                            # If this is not the last band we're creating,
                            # report progress. We'll report progress for the
                            # last band after we build overviews so that the
                            # time required to build them is factored into the
                            # progress calculations.

                            if progressReporter is not None and i < len(sourceDatasets) - 1:
                                progressReporter.ReportProgress()

                        # Close the band and the source dataset.
                        #
                        # This is less than optimal when we're importing
                        # more than one grid out of the same raster,
                        # because when we close the sourceDatasets[i] (the
                        # band) it will also close its parent (the
                        # raster), and the parent might need to be
                        # re-opened when we copy the next band. But we do
                        # not currently have a mechanism for optimally
                        # keeping the parent open while closing the child
                        # when it is not needed anymore. So we err on the
                        # side of making sure everything is closed.
                                
                        finally:
                            del band
                            if destDataset._OpenedBand is not None:
                                cls._LogDebug(_('%(class)s 0x%(id)016X: Closing band %(band)i.') % {'class': destDataset.__class__.__name__, 'id': id(destDataset), 'band': destDataset._OpenedBand})
                                destDataset._GDALRasterBand = None
                                destDataset._OpenedBand = None

                            sourceDatasets[i].Close()

                    # Build overviews.

                    if overviewResamplingMethod is not None:
                        cls._LogDebug(_('%(class)s 0x%(id)016X: Building overviews: resampling="%(resampling)s", levels=%(levels)s.') % {'class': cls.__name__, 'id': id(destDataset), 'resampling': overviewResamplingMethod, 'levels': repr(overviewList)})

                        try:
                            destDataset._GDALDataset.BuildOverviews(overviewResamplingMethod, overviewList)
                        except Exception as e:
                            gdal.ErrorReset()
                            raise RuntimeError(_('Failed to build overviews for Geospatial Data Abstraction Library (GDAL) dataset "%(path)s" (created with the GDAL %(driver)s driver) with resampling method "%(resampling)s" and levels %(levels)s. The GDAL BuildOverviews function failed and reported %(e)s: %(msg)s.') % {'path': path, 'driver': driver.LongName, 'resampling': overviewResamplingMethod, 'levels': repr(overviewList), 'e': e.__class__.__name__, 'msg': e})

                    # Report progress for the last band we created.

                    if progressReporter is not None:
                        progressReporter.ReportProgress()
                        
                finally:
                    destDataset.Close()
                    del destDataset

            # If an exception was raised after the dataset was created,
            # delete it.
            
            except:
                cls._LogDebug(_('%(class)s: Deleting the partially-created GDAL dataset "%(path)s" because an error was raised during creation.'), {'class': cls.__name__, 'path': path})
                try:
                    driver.Delete(path)
                except Exception as e:
                    gdal.ErrorReset()
                    cls._LogWarning(_('Failed to delete the partially-created dataset "%(path)s" using the GDAL %(driver)s driver. The driver\'s Delete function failed with %(e)s: %(msg)s') % {'path': path, 'driver': driver.LongName, 'e': e.__class__.__name__, 'msg': e})
                raise

    @classmethod
    def GetRasterBand(cls, path, band=1, updatable=False, decompressedFileToReturn=None, displayName=None, cacheDirectory=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        with GDALDataset(path, updatable=updatable, decompressedFileToReturn=decompressedFileToReturn, displayName=displayName, cacheDirectory=cacheDirectory) as dataset:
            grids = dataset.QueryDatasets('Band = %i' % band, reportProgress=False)
            if len(grids) <= 0:
                raise ValueError(_('Cannot retrieve band %(band)i from %(dn)s. The band does not exist.') % {'band': band, 'dn': dataset.DisplayName})
            return grids[0]

    @classmethod
    def CreateRaster(cls, path, grid, overwriteExisting=False, **options):
        cls.__doc__.Obj.ValidateMethodInvocation()

        dirTree = DirectoryTree(path=os.path.dirname(path),
                                datasetType=GDALDataset,
                                pathCreationExpressions=[os.path.basename(path)])

        dirTree.ImportDatasets(datasets=[grid], 
                               mode='Replace' if overwriteExisting else 'Add',
                               reportProgress=False,
                               options=options)


########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.GDAL instead.
########################################################################################

__all__ = []
