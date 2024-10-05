# _GDALRasterBand.py - Defines GDALRasterBand, a Grid representing a raster
# band accessed through GDAL's osgeo.ogr.Band class.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Logging import Logger

from .. import Grid


class GDALRasterBand(Grid):
    __doc__ = DynamicDocString()

    def _GetBand(self):
        return self._Band

    Band = property(_GetBand, doc=DynamicDocString())

    def __init__(self, gdalDataset, band, queryableAttributeValues=None, lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Band = band

        # Assign values to known queryable attributes and lazy
        # properties.

        qav = {}
        if queryableAttributeValues is not None:
            qav.update(queryableAttributeValues)

        qav['Band'] = band

        lpv = {}
        if lazyPropertyValues is not None:
            lpv.update(lazyPropertyValues)

        lpv['Dimensions'] = 'yx'
        lpv['CoordDependencies'] = (None, None)
        
        if gdalDataset.GetLazyPropertyValue('TIncrementUnit', False) is None:
            lpv['TIncrementUnit'] = None
            
        if gdalDataset.GetLazyPropertyValue('TSemiRegularity', False) is None:
            lpv['TSemiRegularity'] = None
            
        if gdalDataset.GetLazyPropertyValue('TCountPerSemiRegularPeriod', False) is None:
            lpv['TCountPerSemiRegularPeriod'] = None
            
        if gdalDataset.GetLazyPropertyValue('TCornerCoordType', False) is None:
            lpv['TCornerCoordType'] = None

        # Initialize the base class.

        super(GDALRasterBand, self).__init__(gdalDataset, queryableAttributeValues=qav, lazyPropertyValues=lpv)

    def _Close(self):
        super(GDALRasterBand, self)._Close()
        if hasattr(self, 'ParentCollection') and self.ParentCollection is not None:
            self.ParentCollection.Close()

    def _GetDisplayName(self):
        return _('band %(band)i of %(dn)s') % {'band': self._Band, 'dn': self.ParentCollection.DisplayName}

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known property, return None.

        if name not in ['SpatialReference', 'Shape', 'CoordIncrements', 'CornerCoords', 'PhysicalDimensions', 'PhysicalDimensionsFlipped', 'UnscaledDataType', 'UnscaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # If the caller is requesting the ScalingFunction or
        # UnscalingFunction, return None. At some future point we may try to
        # construct these functions from information retrieved from GDAL (e.g.
        # by calling GetScale and GetOffset), but for now, it is the
        # responsibility of whoever instantiated us to set the ScalingFunction
        # and UnscalingFunction, if they are is needed.

        if name in ['ScalingFunction', 'UnscalingFunction']:
            return None

        # Some of these properties are maintained by GDAL on a per-dataset
        # basis, not a per-band basis. If it is one of those, retrieve its
        # value from our parent GDALDataset.

        if name in ['SpatialReference', 'Shape', 'CoordIncrements', 'CornerCoords', 'PhysicalDimensions', 'PhysicalDimensionsFlipped']:
            return self.ParentCollection.GetLazyPropertyValue(name)

        # To retrieve any of the other properties, we must first open the
        # dataset and retrieve the band object.

        band = self.ParentCollection._OpenBand(self.Band)
        try:

            # Retrieve the band's numpy data type.

            gdalDataType = band.DataType

            if not hasattr(GDALRasterBand, '_GDALDataTypeToNumpyDataType'):
                gdal = self._gdal()
                GDALRasterBand._GDALDataTypeToNumpyDataType = {gdal.GDT_Byte: 'uint8',
                                                               gdal.GDT_UInt16: 'uint16',
                                                               gdal.GDT_Int16: 'int16',
                                                               gdal.GDT_UInt32: 'uint32',
                                                               gdal.GDT_Int32: 'int32',
                                                               gdal.GDT_Float32: 'float32',
                                                               gdal.GDT_Float64: 'float64',
                                                               gdal.GDT_CFloat32: 'complex32',
                                                               gdal.GDT_CFloat64: 'complex64'}
                # GDAL 3.7 added support for int8.

                if hasattr(gdal, 'GDT_Int8'):
                	GDALRasterBand._GDALDataTypeToNumpyDataType[gdal.GDT_Int8] = 'int8'

            if gdalDataType not in GDALRasterBand._GDALDataTypeToNumpyDataType:
                raise TypeError(_('Band %(band)i of %(dn)s has an unknown GDAL data type %(dt)i. This band cannot be processed.') % {'dn': self.DisplayName, 'band': self.Band, 'dt': gdalDataType})
            numpyDataType = GDALRasterBand._GDALDataTypeToNumpyDataType[gdalDataType]

            # Prior to GDAL 3.7, GDAL does not natively support the int8 data
            # type. Instead, it returns it as uint8 data and provides a
            # mechanism to recognize that this was done. The caller is
            # supposed to detect it and cast the uint8 data to int8.
            #
            # If the numpy data type is uint8, check for the presence of
            # PIXELTYPE=SIGNEDBYTE metadata for the band. If we find it,
            # change the numpyDataType to int8.

            if numpyDataType == 'uint8':
                imageStructure = band.GetMetadata('IMAGE_STRUCTURE')
                if isinstance(imageStructure, dict) and 'PIXELTYPE' in imageStructure and imageStructure['PIXELTYPE'].upper() == 'SIGNEDBYTE':
                    numpyDataType = 'int8'

            # Retrieve the band's NoData value.

            noDataValue = band.GetNoDataValue()

            # GDAL always returns the NoData value as a Python 64-bit float.
            # If the numpy data type is an integer, cast the NoData value to
            # an integer.

            import numpy

            if noDataValue is not None and numpyDataType in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32']:
                noDataValue = int(noDataValue)

                # Sadly, for ArcInfo Binary Grid format, GDAL always returns a
                # NoData value, even when all pixels have data. This is not
                # documented but appears to be a consequence of the integer
                # compression protocol used by ArcInfo Binary Grid format:
                # there appears to be no way to tell whether there are NoData
                # pixels without scanning the data. To work around this, read
                # the value attribute table (VAT), which stores the count of
                # cells having each value that appears in the raster. Sum
                # these counts. If it equals the total number of cells, then
                # there are no cells with NoData.

                if self.ParentCollection._GDALDataset.GetDriver().ShortName == 'AIG':
                    vatFile = os.path.join(self.ParentCollection._OpenedFile, 'vat.adf')
                    if not os.path.isfile(vatFile):
                        Logger.RaiseException(ValueError(_('The ArcInfo Binary Grid %(raster)s does not have a value attribute table (VAT). To process the raster, this tool must be able to read the VAT. Try building one by running the ArcGIS Build Raster Attribute Table tool on the raster.') % {'raster': self.ParentCollection._OpenedFile}))
                    try:
                        vat = numpy.fromfile(vatFile, '>i4')
                    except Exception as e:
                        Logger.RaiseException(ValueError(_('Failed to read the value attribute table (VAT) for ArcInfo Binary Grid %(raster)s. To process the raster, this tool must be able to read the VAT. Try rebuilding the VAT by running the ArcGIS Build Raster Attribute Table tool on the raster. Dtailed error information: numpy.fromfile() reported %(e)s: %(msg)s.') % {'raster': self.ParentCollection._OpenedFile, 'e': e.__class__.__name__, 'msg': e}))
                    if sum(vat[1::2]) >= self.Shape[0] * self.Shape[1]:
                        noDataValue = None

            # If the numpy data type is float32, cast the NoData value from a
            # Python 64-bit float to a numpy 32-bit float. This is necessary
            # because if the Python 64-bit float is compared to numpy 32-bit
            # float data read from the band (e.g. a comparison similar to
            # band.Data[...] == band.NoDataValue), the comparison may say they
            # are unequal when the cell contains the NoData value. The problem
            # is solved by casting GDAL's NoData value (the 64-bit float) to
            # numpy float32 and THEN doing the comparison.

            elif noDataValue is not None and numpyDataType == 'float32':
                noDataValue = numpy.asarray(noDataValue, dtype='float32')

            # Set the lazy property values.

            self.SetLazyPropertyValue('UnscaledDataType', numpyDataType)
            if self.GetLazyPropertyValue('UnscaledNoDataValue', allowPhysicalValue=False) is None:
                self.SetLazyPropertyValue('UnscaledNoDataValue', noDataValue)

            # Log a debug message with the lazy property values.

            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: UnscaledDataType=%(UnscaledDataType)s, UnscaledNoDataValue=%(UnscaledNoDataValue)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self.DisplayName, 'UnscaledDataType': numpyDataType, 'UnscaledNoDataValue': repr(noDataValue)})

        finally:
            del band

        # Retrieve the value of the requested property.

        return self.GetLazyPropertyValue(name)

    def _ReadNumpyArray(self, sliceList):

        # Open the dataset and retrieve the band object.

        band = self.ParentCollection._OpenBand(self.Band)
        try:
            
            # Get the data. Note that sliceList[0] contains the y
            # indices and sliceList[1] contains the x indices.

            xoff = sliceList[1].start
            yoff = sliceList[0].start
            win_xsize = sliceList[1].stop - sliceList[1].start
            win_ysize = sliceList[0].stop - sliceList[0].start

            self._LogDebug(_('%(class)s 0x%(id)016X: Band %(Band)i: Reading a block of %(win_xsize)i columns by %(win_ysize)i rows at offsets x=%(xoff)i, y=%(yoff)i.') % {'class': self.__class__.__name__, 'id': id(self), 'Band': self.Band, 'xoff': xoff, 'yoff': yoff, 'win_xsize': win_xsize, 'win_ysize': win_ysize})

            try:
                data = band.ReadAsArray(xoff, yoff, win_xsize, win_ysize).copy()
            except Exception as e:
                self._gdal().ErrorReset()
                raise RuntimeError(_('Failed to retrieve a block of data of %(win_xsize)i columns by %(win_ysize)i rows at offsets x=%(xoff)i, y=%(yoff)i from band %(band)i of %(dn)s with the Geospatial Data Abstraction Library (GDAL). Verify that the dataset exists, is accessible, and has the expected dimensions. Detailed error information: band.ReadAsArray(%(xoff)i, %(yoff)i, %(win_xsize)i, %(win_ysize)i) reported %(e)s: %(msg)s.') % {'band': self.Band, 'dn': self.DisplayName, 'xoff': xoff, 'yoff': yoff, 'win_xsize': win_xsize, 'win_ysize': win_ysize, 'e': e.__class__.__name__, 'msg': e})

            # Return the data along with the NoData value that GDAL is
            # using. Note that the data type and NoData value may not
            # be what our UnscaledDataType and UnscaledNoDataValue
            # properties call for. If they are different, our caller
            # (Grid._ReadData) is responsible for handling it.

            return data, band.GetNoDataValue()

        finally:
            del band

        # Return the array.

        return data

    def _WriteNumpyArray(self, sliceList, data):

        # Open the dataset and retrieve the band object.

        band = self.ParentCollection._OpenBand(self.Band)
        try:
            
            # Write the data. Note that sliceList[0] contains the y
            # indices and sliceList[1] contains the x indices.

            xoff = sliceList[1].start
            yoff = sliceList[0].start
            win_xsize = sliceList[1].stop - sliceList[1].start
            win_ysize = sliceList[0].stop - sliceList[0].start

            self._LogDebug(_('%(class)s 0x%(id)016X: Band %(Band)i: Writing a block of %(win_xsize)i columns by %(win_ysize)i rows at offsets x=%(xoff)i, y=%(yoff)i.') % {'class': self.__class__.__name__, 'id': id(self), 'Band': self.Band, 'xoff': xoff, 'yoff': yoff, 'win_xsize': win_xsize, 'win_ysize': win_ysize})

            try:
                band.WriteArray(data, xoff, yoff)
            except Exception as e:
                self._gdal().ErrorReset()
                raise RuntimeError(_('Failed to write a block of data of %(win_xsize)i columns by %(win_ysize)i rows at offsets x=%(xoff)i, y=%(yoff)i to band %(band)i of %(dn)s with the Geospatial Data Abstraction Library (GDAL). Verify that the dataset exists, is accessible, and has the expected dimensions. Detailed error information: band.WriteArray(data, %(xoff)i, %(yoff)i) reported %(e)s: %(msg)s.') % {'band': self.Band, 'dn': self.DisplayName, 'xoff': xoff, 'yoff': yoff, 'win_xsize': win_xsize, 'win_ysize': win_ysize, 'e': e.__class__.__name__, 'msg': e})

        finally:
            del band


########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.GDAL instead.
########################################################################################

__all__ = []
