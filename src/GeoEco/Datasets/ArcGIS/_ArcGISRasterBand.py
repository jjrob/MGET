# _ArcGISRasterBand.py - Defines ArcGISRasterBand, a Grid representing a band
# of an ArcGISRaster.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os

from ...ArcGIS import GeoprocessorManager
from ...DynamicDocString import DynamicDocString
from ...Internationalization import _

from .. import DatasetCollection, Grid


class ArcGISRasterBand(Grid):
    __doc__ = DynamicDocString()

    def _GetBand(self):
        return self._Band

    Band = property(_GetBand, doc=DynamicDocString())

    def __init__(self, arcGISRaster, band, queryableAttributeValues=None, lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Band = band

        # Assign values to known queryable attributes and lazy properties.

        qav = {}
        if queryableAttributeValues is not None:
            qav.update(queryableAttributeValues)

        qav['Band'] = band

        lpv = {}
        if lazyPropertyValues is not None:
            lpv.update(lazyPropertyValues)

        lpv['Dimensions'] = 'yx'
        lpv['PhysicalDimensions'] = 'yx'
        lpv['PhysicalDimensionsFlipped'] = (True, False)    # This is correct when we read the raster with GDAL, which we do with ArcGIS 9.x, but with ArcGIS 10.x we may ultimately read it with Arc's own numpy API. What does it do?
        lpv['CoordDependencies'] = (None, None)
        
        if arcGISRaster.GetLazyPropertyValue('TIncrementUnit', False) is None:
            lpv['TIncrementUnit'] = None
            
        if arcGISRaster.GetLazyPropertyValue('TSemiRegularity', False) is None:
            lpv['TSemiRegularity'] = None
            
        if arcGISRaster.GetLazyPropertyValue('TCountPerSemiRegularPeriod', False) is None:
            lpv['TCountPerSemiRegularPeriod'] = None
            
        if arcGISRaster.GetLazyPropertyValue('TCornerCoordType', False) is None:
            lpv['TCornerCoordType'] = None

        # Initialize the base class.

        super(ArcGISRasterBand, self).__init__(arcGISRaster, queryableAttributeValues=qav, lazyPropertyValues=lpv)

    def _Close(self):
        super(ArcGISRasterBand, self)._Close()
        if hasattr(self, 'ParentCollection') and self.ParentCollection is not None:
            self.ParentCollection.Close()

    def _GetDisplayName(self):
        return _('band %(band)i of %(dn)s') % {'band': self._Band, 'dn': self.ParentCollection.DisplayName}

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known lazy property, return None.

        if name not in ['SpatialReference', 'Shape', 'CoordIncrements', 'CornerCoords', 'UnscaledDataType', 'UnscaledNoDataValue']:
            return None

        # The spatial reference is maintained by ArcGIS on a per-raster basis,
        # not a per-band basis. If the caller wants that, retrieve its value
        # from our parent ArcGISRaster.

        if name == 'SpatialReference':
            return self.ParentCollection.GetLazyPropertyValue(name)

        # If the caller wants any of the other properties, get them from the
        # geoprocessor's Describe object, unless the caller wants the
        # UnscaledNoDataValue and we previously tried to get it from the
        # Describe object and failed.

        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        
        if self.ParentCollection.ParentCollection is None:
            path = self.ParentCollection.Path
        else:
            path = os.path.join(self.ParentCollection.ParentCollection.Path, self.ParentCollection.Path)

        if self.ParentCollection.GetLazyPropertyValue('Bands') > 1:
            path = os.path.join(path, 'Band_' + str(self._Band))

        if name in ['Shape', 'CoordIncrements', 'CornerCoords', 'UnscaledDataType', 'UnscaledNoDataValue']:
            d = gp.Describe(path)

            self.SetLazyPropertyValue('Shape', (d.Height, d.Width))
            self.SetLazyPropertyValue('CoordIncrements', (d.MeanCellHeight, d.MeanCellWidth))
            self.SetLazyPropertyValue('CornerCoords', (float(d.Extent.YMin) + d.MeanCellHeight / 2.0, float(d.Extent.XMin) + d.MeanCellWidth / 2.0))

            pixelType = d.PixelType.upper()
            if pixelType in ['U1', 'U2', 'U4', 'U8', 'UCHAR']:
                self.SetLazyPropertyValue('UnscaledDataType', 'uint8')
            elif pixelType in ['S8', 'CHAR']:
                self.SetLazyPropertyValue('UnscaledDataType', 'int8')
            elif pixelType in ['U16', 'USHORT']:
                self.SetLazyPropertyValue('UnscaledDataType', 'uint16')
            elif pixelType in ['S16', 'SHORT']:
                self.SetLazyPropertyValue('UnscaledDataType', 'int16')
            elif pixelType in ['U32', 'ULONG']:
                self.SetLazyPropertyValue('UnscaledDataType', 'uint32')
            elif pixelType in ['S32', 'LONG']:
                self.SetLazyPropertyValue('UnscaledDataType', 'int32')
            elif pixelType in ['F32', 'FLOAT']:
                self.SetLazyPropertyValue('UnscaledDataType', 'float32')
            elif pixelType in ['F64', 'DOUBLE']:
                self.SetLazyPropertyValue('UnscaledDataType', 'float64')
            else:
                raise ValueError(_('%(dn)s cannot be opened because it has an unknown ArcGIS PixelType "%(pt)s".') % {'pt': d.PixelType})

            self.SetLazyPropertyValue('UnscaledNoDataValue', d.NoDataValue)

            # Log a debug message with the properties of the band.

            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: Dimensions=%(Dimensions)s, PhysicalDimensions=%(PhysicalDimensions)s, PhysicalDimensionsFlipped=%(PhysicalDimensionsFlipped)s, Shape=%(Shape)s, CoordIncrements=%(CoordIncrements)s, CornerCoords=%(CornerCoords)s, UnscaledDataType=%(UnscaledDataType)s, UnscaledNoDataValue=%(UnscaledNoDataValue)s.'),
                           {'class': self.__class__.__name__,
                            'id': id(self),
                            'dn': self.DisplayName,
                            'Dimensions': self.GetLazyPropertyValue('Dimensions'),
                            'PhysicalDimensions': self.GetLazyPropertyValue('PhysicalDimensions'),
                            'PhysicalDimensionsFlipped': repr(self.GetLazyPropertyValue('PhysicalDimensionsFlipped')),
                            'Shape': repr(self.GetLazyPropertyValue('Shape')),
                            'CoordIncrements': repr(self.GetLazyPropertyValue('CoordIncrements')),
                            'CornerCoords': self.GetLazyPropertyValue('CornerCoords'),
                            'UnscaledDataType': repr(self.GetLazyPropertyValue('UnscaledDataType')),
                            'UnscaledNoDataValue': repr(self.GetLazyPropertyValue('UnscaledNoDataValue'))})

        # Return the value of the requested property.

        return self.GetLazyPropertyValue(name)

    def _ReadNumpyArray(self, sliceList):

        # Instantiate a GDALDataset for the raster.

        dataset = self.ParentCollection._InstantiateGDALDataset()

        # The following code is copied from GDALRasterBand._ReadNumpyArray().
        # Rather than instantiate a GDALRasterBand simply to be able to call
        # that function, I just copied the code. This is a bit dodgy from an
        # encapsulation and maintenance point of view but the code is so
        # simple that I consider it a reasonable tradeoff.
        #
        # Open the dataset and retrieve the band object.

        band = dataset._OpenBand(self.Band)
        try:
            
            # Get the data. Note that sliceList[0] contains the y indices and
            # sliceList[1] contains the x indices.

            xoff = sliceList[1].start
            yoff = sliceList[0].start
            win_xsize = sliceList[1].stop - sliceList[1].start
            win_ysize = sliceList[0].stop - sliceList[0].start

            self._LogDebug(_('%(class)s 0x%(id)016X: Band %(Band)i: Reading with GDAL a block of %(win_xsize)i columns by %(win_ysize)i rows at offsets x=%(xoff)i, y=%(yoff)i.') % {'class': self.__class__.__name__, 'id': id(self), 'Band': self.Band, 'xoff': xoff, 'yoff': yoff, 'win_xsize': win_xsize, 'win_ysize': win_ysize})

            try:
                data = band.ReadAsArray(xoff, yoff, win_xsize, win_ysize).copy()
            except Exception as e:
                self._gdal().ErrorReset()
                raise RuntimeError(_('Failed to retrieve a block of data of %(win_xsize)i columns by %(win_ysize)i rows at offsets x=%(xoff)i, y=%(yoff)i from band %(band)i of %(dn)s (a local copy of %(dn2)s) with the Geospatial Data Abstraction Library (GDAL). Verify that the dataset exists, is accessible, and has the expected dimensions. Detailed error information: band.ReadAsArray(%(xoff)i, %(yoff)i, %(win_xsize)i, %(win_ysize)i) reported %(e)s: %(msg)s.') % {'band': self.Band, 'dn': dataset.DisplayName, 'dn2': self.ParentCollection.DisplayName, 'xoff': xoff, 'yoff': yoff, 'win_xsize': win_xsize, 'win_ysize': win_ysize, 'e': e.__class__.__name__, 'msg': e})

            # Return the data along with the NoData value that GDAL is using.
            # Note that the data type and NoData value may not be what our
            # UnscaledDataType and UnscaledNoDataValue properties call for. If
            # they are different, our caller (Grid._ReadData) is responsible
            # for handling it.

            return data, band.GetNoDataValue()

        finally:
            del band

        # Return the array.

        return data

    @classmethod
    def ConstructFromArcGISPath(cls, path, decompressedFileToReturn=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Get the geoprocessor Describe object's DataType for the path. If it
        # is a RasterBand, instantiate an ArcGISRaster for its parent and then
        # query it for the ArcGISRasterBand that has the specified band
        # number.

        from . import ArcGISRaster

        d = GeoprocessorManager.GetWrappedGeoprocessor().Describe(path)
        dataType = d.DataType.lower()
        if dataType == 'rasterband':
            arcGISRaster = ArcGISRaster(d.Path, decompressedFileToReturn=decompressedFileToReturn, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues, cacheDirectory=cacheDirectory)
            return arcGISRaster.QueryDatasets('Band = ' + str(int(d.Name.split('_')[1])), reportProgress=False)[0]

        # If it is a RasterDataset, RasterLayer, or File (which could be a
        # compressed raster), instantiate an ArcGISRaster for it and query it
        # for the first ArcGISRasterBand. If it has multiple bands, report a
        # warning.

        if dataType in ['rasterdataset', 'rasterlayer', 'file']:
            arcGISRaster = ArcGISRaster(path, decompressedFileToReturn=decompressedFileToReturn, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues, cacheDirectory=cacheDirectory)
            if d.BandCount > 1:
                cls._LogWarning(_('%(dn)s has %(bands)i bands. The first band will be used.') % {'dn': arcGISRaster.DisplayName, 'bands': d.BandCount})
            return arcGISRaster.QueryDatasets('Band = 1', reportProgress=False)[0]

        # If we got to here, we do not know how to open it.

        raise ValueError(_('Cannot open "%(path)s" as an ArcGIS raster band, raster dataset, or raster layer. ArcGIS reports that it is a "%(dataType)".') % {'path': path, 'dataType': d.DataType})


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
