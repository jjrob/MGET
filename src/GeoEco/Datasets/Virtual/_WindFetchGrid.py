# _WindFetchGrid.py - A Grid representing average distances to NoData cells in
# all directions in a land/water Grid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import math
import warnings

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Logging import ProgressReporter

from .. import Grid


class WindFetchGrid(Grid):
    __doc__ = DynamicDocString()

    def _GetDirections(self):
        return self._Directions

    Directions = property(_GetDirections, doc=DynamicDocString())

    def _GetMaxDist(self):
        return self._MaxDist

    MaxDist = property(_GetMaxDist, doc=DynamicDocString())

    def _GetMaxDistPerDir(self):
        return self._MaxDistPerDir

    MaxDistPerDir = property(_GetMaxDistPerDir, doc=DynamicDocString())

    def _GetPadByMaxDistPerDir(self):
        return self._PadByMaxDistPerDir

    PadByMaxDistPerDir = property(_GetPadByMaxDistPerDir, doc=DynamicDocString())

    def __init__(self, grid, directions, maxDist=None, maxDistPerDir=None, padByMaxDistPerDir=True, reportProgress=True):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if grid.CoordDependencies[-1] is not None:
            raise ValueError(_('The input grid, %(dn)s, does not have a constant x increment. The current implementation of WindFetchGrid only supports grids with constant x increments.') % {'dn': grid.DisplayName})

        if grid.CoordDependencies[-2] is not None:
            raise ValueError(_('The input grid, %(dn)s, does not have a constant y increment. The current implementation of WindFetchGrid only supports grids with constant y increments.') % {'dn': grid.DisplayName})
        
        # Initialize our properties.
        
        self._Grid = grid
        self._Directions = directions
        self._MaxDist = maxDist
        self._MaxDistPerDir = maxDistPerDir
        self._PadByMaxDistPerDir = padByMaxDistPerDir
        self._ReportProgress = reportProgress
        self._CachedSlice = None
        self._CachedSliceIndices = None

        self._DisplayName = _('wind fetch for %(dn)s') % {'dn': grid.DisplayName}

        # Initialize the base class.

        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(WindFetchGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the caller requested PhysicalDimensions or
        # PhysicalDimensionsFlipped, return idealized values, as any
        # transposing and flipping is handled by the contained grid.

        if name == 'PhysicalDimensions':
            return self._Grid.Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self._Grid.Dimensions))

        # We determine the data type and no data values. The precision and
        # range of float64 are unnecessary for nearly all applications. so we
        # use float32.

        if name == 'UnscaledDataType':
            return 'float32'
        
        if name == 'UnscaledNoDataValue':
            return -3.4028234663852886e+38      # This is what ArcGIS uses by default. Note that float(-3.4028234663852886e+38) == numpy.asarray(-3.4028234663852886e+38, dtype='float32')

        if name in ['ScaledDataType', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # Otherwise use the value of the property from the grid.
        
        return self._Grid.GetLazyPropertyValue(name)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        self._CachedSlice = None
        self._CachedSliceIndices = None
        super(WindFetchGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['setspatialreference']:
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return cls._Grid._TestCapability(capability)

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        return self._Grid._GetCoords(coord, coordNum, slices, sliceDims, fixedIncrementOffset)

    def _ReadNumpyArray(self, sliceList):

        # Allocate an array to return.

        import numpy

        data = numpy.zeros([s.stop-s.start for s in sliceList], dtype=str(self.DataType))

        # Iterate through each requested 2D slice and compute distances. Cache
        # the last slice. If we catch an exception, call _Close().

        try:
            if len(self.Dimensions) == 2:
                slices = [(sliceList[0], sliceList[1])]
            elif len(self.Dimensions) == 3:
                slices = [(d, sliceList[1], sliceList[2]) for d in range(sliceList[0].start, sliceList[0].stop)]
            else:
                slices = [(d1, d2, sliceList[2], sliceList[3]) for d1 in range(sliceList[0].start, sliceList[0].stop) for d2 in range(sliceList[1].start, sliceList[1].stop)]

            for s in slices:

                # Although the caller might not have requested the full extent
                # in the x or y direction, in order to obtain distances for
                # the caller's region of interest, we need to compute
                # distances across the entire 2D slice. If we computed
                # distances only from the portion of the source grid that
                # occurred within the caller's region of interest, we would
                # fail to consider features that might be just outside the
                # edges. So we compute and cache distances for the entire 2D
                # slice. Check to see if we have cached this slice,
                # considering only the t and z coordinates, if the source grid
                # has them. (If not, and the source is 2D, then the entire 2D
                # slice is effectively the entire source grid.)

                if s[:-2] != self._CachedSliceIndices:
                    self._CachedSlice = None
                    self._CachedSliceIndices = None

                    # Construct a Grid object representing the 2D slice that
                    # we will compute fetch for.

                    if self.Dimensions == 'yx':
                        grid = self._Grid
                    elif self.Dimensions == 'zyx':
                        grid = GridSlice(self._Grid, zIndex=s[0])
                    elif self.Dimensions == 'tyx':
                        grid = GridSlice(self._Grid, tIndex=s[0])
                    else:
                        grid = GridSlice(self._Grid, tIndex=s[0], zIndex=s[1])

                    # Extract the the 2D slice's data.

                    if len(s) == 2:
                        sliceData = grid.Data[:, :]
                    elif len(s) == 3:
                        sliceData = grid.Data[s[0], :, :]
                    else:
                        sliceData = grid.Data[s[0], s[1], :, :]

                    sliceData = grid.Data[:]

                    # Compute fetch and store the resulting numpy array as our
                    # cached slice.

                    if self._ReportProgress:
                        self._LogInfo(_('Computing wind fetch in %(dirs)s directions for %(dn)s.') % {'dirs': len(self.Directions), 'dn': grid.DisplayName})

                    self._CachedSlice = self.ComputeFetch(array=sliceData, 
                                                          landValue=grid.NoDataValue, 
                                                          cellSize=grid.CoordIncrements[-1], 
                                                          directions=self.Directions, 
                                                          maxDistPerDir=self._MaxDistPerDir, 
                                                          padByMaxDistPerDir=self._PadByMaxDistPerDir,
                                                          reportProgress=self._ReportProgress)
                    del sliceData

                    # Apply max distances, if any.

                    if self._MaxDist is not None:
                        self._CachedSlice[self._CachedSlice > self._MaxDist] = self._MaxDist

                    # Set nan values to the NoData value.

                    self._CachedSlice[numpy.isnan(self._CachedSlice)] = self.NoDataValue

                    self._CachedSliceIndices = s[:-2]

                # Extract an array representing the caller's region of
                # interest and store it in the array to return.

                if len(self.Dimensions) == 2:
                    data.__setitem__((slice(None, None, None), slice(None, None, None)), self._CachedSlice.__getitem__(s[-2:]))
                elif len(self.Dimensions) == 3:
                    data.__setitem__((slice(s[0] - slices[0][0], s[0] - slices[0][0] + 1, None), slice(None, None, None), slice(None, None, None)), self._CachedSlice.__getitem__(s[-2:]))
                else:
                    data.__setitem__((slice(s[0] - slices[0][0], s[0] - slices[0][0] + 1, None), slice(s[1] - slices[1][0], s[1] - slices[1][0] + 1, None), slice(None, None, None), slice(None, None, None)), self._CachedSlice.__getitem__(s[-2:]))

        except:
            self._Close()
            raise

        # Return successfully.

        return data, self.NoDataValue

    # The following function was based on https://github.com/KennethTM/WindFetch.
    # Thanks to Kenneth Martinsen (@KennthTM) for developing and sharing it.

    @classmethod
    def ComputeFetch(cls, array, landValue, cellSize, directions, maxDistPerDir=None, padByMaxDistPerDir=True, reportProgress=True):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Define a helper function for calculating fetch in one direction.
        # This is based on https://github.com/KennethTM/WindFetch. Thanks to
        # Kenneth Martinsen for developing and sharing it.

        import numpy
        import scipy.ndimage

        def fetch_single_dir(array, cellSize, direction):

            def fetch_length_vect(array, cellSize):
                """Calculate lengths."""

                w = array*-1
                v = w.flatten(order="F")
                n = numpy.isnan(v)
                a = ~n
                c = numpy.cumsum(a)
                b = numpy.concatenate(([0.0], c[n]))
                d = numpy.diff(b,)
                v[n] = -d
                x=numpy.cumsum(v)
                y=numpy.reshape(x, w.shape, order="F")*w*cellSize

                return(y)

            def estimated_pad(array, cellSize):
                """Estimate padding required before rotation."""

                nrow, ncol = array.shape
                xlen = cellSize*ncol
                ylen = cellSize*nrow
                padwidth = numpy.sqrt(xlen**2+ylen**2) - min([xlen, ylen])

                return(int(padwidth/2/cellSize)+1) 

            def padding(array, pad_width, fill_value, inverse=False):
                """Perform the padding."""

                if inverse == False:
                    arr = numpy.pad(array, pad_width=pad_width, mode="constant", constant_values=fill_value)
                else:
                    arr = array[pad_width:-pad_width, pad_width:-pad_width]

                return(arr)

            # Prepare array for fetch calculation i.e padding and rotating.

            pad_width = estimated_pad(array, cellSize)
            array_pad = padding(array, pad_width, numpy.nan)
            array_rot = scipy.ndimage.rotate(array_pad, angle=direction, reshape=False, mode="constant", cval=numpy.nan, order=0)
            array_fetch = fetch_length_vect(array_rot, cellSize)
            array_inv_rot = scipy.ndimage.rotate(array_fetch, angle=360-direction, reshape=False, mode="constant", cval=numpy.nan, order=0)
            array_inv_pad = padding(array_inv_rot, pad_width, -cellSize, inverse=True)

            return(array_inv_pad)

        # If we got a maxDistPerDir and padByMaxDistPerDir is True, then pad
        # the array on all sides by a value other than landValue, so that the
        # caller's study area will be effectively surrounded by water.

        if maxDistPerDir is not None and padByMaxDistPerDir:
            numPaddingCells = math.ceil(maxDistPerDir / cellSize) + 1
            padValue = 0 if landValue != 0 else 1
            array = numpy.pad(array, pad_width=numPaddingCells, mode='constant', constant_values=padValue)

        # Create an array where water is -1 and land is numpy.nan.

        if numpy.isnan(landValue):
            landwater = numpy.where(numpy.isnan(array), numpy.nan, -1)
        else:
            landwater = numpy.where(array == landValue, numpy.nan, -1)

        # Calculate mean fetch using Welford's online algorithm to control
        # memory usage.

        if reportProgress:
            progressReporter = ProgressReporter(progressMessage1=_('Computing wind fetch: %(elapsed)s elapsed, %(opsCompleted)i directions computed, %(perOp)s per direction, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                completionMessage=_('Wind fetch computation complete: %(elapsed)s elapsed, %(opsCompleted)i directions computed, %(perOp)s per direction.'),
                                                abortedMessage=_('Wind fetch computation stopped before all directions were computed: %(elapsed)s elapsed, %(opsCompleted)i directions computed, %(perOp)s per direction, %(opsIncomplete)i directions not computed.'))
            progressReporter.Start(len(directions))
        else:
            progressReporter = None

        meanFetch = None
        counts = None

        for d in directions:
            a = fetch_single_dir(landwater, cellSize, d)
            if maxDistPerDir is not None:
                a[a > maxDistPerDir] = maxDistPerDir

            if meanFetch is None:
                meanFetch = a
                counts = numpy.zeros_like(a, dtype=int)

            mask = ~numpy.isnan(a)
            counts[mask] += 1
            meanFetch[mask] += (a[mask] - meanFetch[mask]) / counts[mask]

            if reportProgress:
                progressReporter.ReportProgress()

        meanFetch[counts == 0] = numpy.nan

        # The computations above estimate fetch in some of the land cells as
        # well as water. Set the land cells back to nan.

        if numpy.isnan(landValue):
            meanFetch = numpy.where(numpy.isnan(array), numpy.nan, meanFetch)
        else:
            meanFetch = numpy.where(array == landValue, numpy.nan, meanFetch)

        # If we got a maxDistPerDir and padByMaxDistPerDir is True, remove the
        # padding from around meanFetch before returning it.

        if maxDistPerDir is not None and padByMaxDistPerDir:
            meanFetch = meanFetch[numPaddingCells:-numPaddingCells, numPaddingCells:-numPaddingCells]
            
        return(meanFetch)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
