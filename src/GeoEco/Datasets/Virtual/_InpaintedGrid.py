# _InpaintedGrid.py - A Grid that fills missing values in another Grid
# using a partial differential equation method.
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
from ...Matlab import SharedMatlabWorkerProcess

from .. import Grid
from . import GridSlice


class InpaintedGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, method='Del2a', maxHoleSize=None, xEdgesWrap=False, minValue=None, maxValue=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if grid.DataType not in ['float32', 'float64']:
            raise TypeError(_('This tool can only fill missing values in floating-point grids. It cannot fill missing values in integer grids.'))

        if minValue is not None and maxValue is not None and minValue >= maxValue:
            raise ValueError(_('The minimum value (%(min)r) is greater than or equal to the maximum value (%(max)s). This is not allowed. Please specify a minimum value that is less than the maximum value.') % {'min': minValue, 'max': maxValue})

        # Initialize our properties.
        
        self._Grid = grid
        self._TempDir = None
        self._MatlabWorkerProcess = None
        self._Method = method
        self._MaxHoleSize = maxHoleSize
        self._XEdgesWrap = xEdgesWrap
        self._MinValue = minValue
        self._MaxValue = maxValue

        if maxHoleSize is None:
            self._DisplayName = _('%(dn)s with missing cells filled using the %(method)s') % {'dn': grid.DisplayName, 'method': method}
        else:
            self._DisplayName = _('%(dn)s with clusters of missing cells no larger than %(maxHoleSize)i filled using the %(method)s') % {'dn': grid.DisplayName, 'maxHoleSize': maxHoleSize, 'method': method}

        # Initialize the base class.

        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(InpaintedGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        if hasattr(self, '_MatlabWorkerProcess') and self._MatlabWorkerProcess is not None:
            self._MatlabWorkerProcess = None   # Do not call _MatlabWorkerProcess.Stop() here. We want the shared process to keep running.
        self._TempDir = None
        super(InpaintedGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the caller requested PhysicalDimensions or
        # PhysicalDimensionsFlipped, return idealized values, as any
        # transposing and flipping is handled by the contained grid.

        if name == 'PhysicalDimensions':
            return self._Grid.Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self._Grid.Dimensions))

        # The contained grid also handles everything related to scaling.

        if name == 'UnscaledDataType':
            return self._Grid.DataType
        
        if name == 'UnscaledNoDataValue':
            return self._Grid.NoDataValue

        if name in ['ScaledDataType', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # Otherwise use the value of the property from the grid.
        
        return self._Grid.GetLazyPropertyValue(name)

    @classmethod
    def _TestCapability(cls, capability):
        return cls._Grid._TestCapability(capability)

    @classmethod
    def _GetSRTypeForSetting(cls):
        return cls._Grid._GetSRTypeForSetting()

    def _SetSpatialReference(self, sr):
        return self._Grid._SetSpatialReference(sr)

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        return self._Grid._GetCoords(coord, coordNum, slices, sliceDims, fixedIncrementOffset)

    def _ReadNumpyArray(self, sliceList):

        # Iterate through each requested 2D slice and create an inpainted
        # version of it in the temporary directory, if we have not done so
        # already. If we catch an exception, call _Close() to delete the
        # temporary directory.

        import numpy

        try:
            if len(self.Dimensions) == 2:
                slices = [(sliceList[0], sliceList[1])]
            elif len(self.Dimensions) == 3:
                slices = [(d, sliceList[1], sliceList[2]) for d in range(sliceList[0].start, sliceList[0].stop)]
            else:
                slices = [(d1, d2, sliceList[2], sliceList[3]) for d1 in range(sliceList[0].start, sliceList[0].stop) for d2 in range(sliceList[1].start, sliceList[1].stop)]

            for s in slices:
                if self._TempDir is not None:
                    inpaintedFile = os.path.join(self._TempDir, 'slice_%s_inpainted.dat' % '_'.join(map(str, s[:len(self.Dimensions) - 2])))
                    
                if self._TempDir is None or not os.path.exists(inpaintedFile):

                    # Extract the 2D slice.

                    if self.Dimensions == 'yx':
                        grid = self._Grid
                    elif self.Dimensions == 'zyx':
                        grid = GridSlice(self._Grid, zIndex=s[0])
                    elif self.Dimensions == 'tyx':
                        grid = GridSlice(self._Grid, tIndex=s[0])
                    else:
                        grid = GridSlice(self._Grid, tIndex=s[0], zIndex=s[1])

                    # Even though the caller might only be interested in part
                    # of the 2D slice, we have to inpaint the entire slice
                    # because cells outside their area of interest can
                    # influence values inpainted into their area of interest.
                    # Extract the entire slice to a numpy array and change the
                    # NoData value to NaN.

                    data = grid.Data[:]
                    data[Grid.numpy_equal_nan(data, grid.NoDataValue)] = numpy.nan

                    # If we have not created the temporary directory or
                    # instantiated MatlabWorkerProcess, do it now.

                    if self._TempDir is None:
                        self._TempDir = self._CreateTempDirectory()

                    if self._MatlabWorkerProcess is None:
                        self._MatlabWorkerProcess = SharedMatlabWorkerProcess.GetWorkerProcess()

                    # Inpaint the numpy array with the MATLAB function.

                    inpaintedFile = os.path.join(self._TempDir, 'slice_%s_inpainted.dat' % '_'.join(map(str, s[:len(self.Dimensions) - 2])))
                    self._LogDebug(_('%(class)s 0x%(id)016X: Creating %(inpaintedFile)s from slice %(slice)r of %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'inpaintedFile': inpaintedFile, 'slice': s, 'dn': self._Grid.DisplayName})

                    inpaintedArray = self._MatlabWorkerProcess.InpaintNaNs(data,                                                            # A
                                                                           {'del2a': 1, 'del2b': 0, 'del2c': 2, 'del4': 3, 'spring': 4}[self._Method.lower()],   # method
                                                                           self._MaxHoleSize if self._MaxHoleSize is not None else 0.,      # maxHoleSize
                                                                           float(self._XEdgesWrap),                                         # edgesWrap
                                                                           self._MinValue if self._MinValue is not None else numpy.nan,     # minValue
                                                                           self._MaxValue if self._MaxValue is not None else numpy.nan)     # maxValue

                    # In the returned array, convert NaN to the NoDataValue.

                    inpaintedArray[numpy.isnan(inpaintedArray)] = self.NoDataValue

                    # Write the returned array to the temporary directory.

                    inpaintedArray.tofile(inpaintedFile)

        except:
            self._Close()
            raise

        # Allocate an array to return.

        data = numpy.zeros([s.stop-s.start for s in sliceList], dtype=str(self.UnscaledDataType))

        # Read the inpainted slices from the temporary directory and
        # write them to the array. 

        for s in slices:
            inpaintedFile = os.path.join(self._TempDir, 'slice_%s_inpainted.dat' % '_'.join(map(str, s[:len(self.Dimensions) - 2])))
            inpaintedSlice = numpy.fromfile(inpaintedFile, str(self.DataType)).reshape(self.Shape[-2], self.Shape[-1])

            if len(self.Dimensions) == 2:
                data.__setitem__((slice(None, None, None), slice(None, None, None)), inpaintedSlice.__getitem__(s[-2:]))
            elif len(self.Dimensions) == 3:
                data.__setitem__((slice(s[0] - slices[0][0], s[0] - slices[0][0] + 1, None), slice(None, None, None), slice(None, None, None)), inpaintedSlice.__getitem__(s[-2:]))
            else:
                data.__setitem__((slice(s[0] - slices[0][0], s[0] - slices[0][0] + 1, None), slice(s[1] - slices[1][0], s[1] - slices[1][0] + 1, None), slice(None, None, None), slice(None, None, None)), inpaintedSlice.__getitem__(s[-2:]))

        # Return successfully.

        return data, self.NoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
