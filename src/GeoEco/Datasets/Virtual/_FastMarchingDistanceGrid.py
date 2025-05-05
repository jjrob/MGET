# _FastMarchingDistanceGrid.py - A Grid representing distances to features in
# another Grid, computed with a fast marching algorithm.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _

from .. import Grid
from . import GridSlice


class FastMarchingDistanceGrid(Grid):
    __doc__ = DynamicDocString()

    def _GetMinDist(self):
        return self._MinDist

    MinDist = property(_GetMinDist, doc=DynamicDocString())

    def _GetMaxDist(self):
        return self._MaxDist

    MaxDist = property(_GetMaxDist, doc=DynamicDocString())

    def __init__(self, grid, minDist=None, maxDist=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if grid.DataType not in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64', 'float128']:
            raise TypeError(_('The input grid must use one of the following data types: int8, uint8, int16, uint16, int32, uint32, int64, uint64, float32, float64, float128.'))

        if grid.CoordDependencies[-1] is not None:
            raise ValueError(_('The input grid, %(dn)s, does not have a constant x increment. The current implementation of FastMarchingDistanceGrid only supports grids with constant x increments.') % {'dn': grid.DisplayName})

        if grid.CoordDependencies[-2] is not None:
            raise ValueError(_('The input grid, %(dn)s, does not have a constant y increment. The current implementation of FastMarchingDistanceGrid only supports grids with constant y increments.') % {'dn': grid.DisplayName})
        
        # Initialize our properties.
        
        self._Grid = grid
        self._MinDist = minDist
        self._MaxDist = maxDist
        self._CachedSlice = None
        self._CachedSliceIndices = None

        self._DisplayName = _('fast marching distances for %(dn)s') % {'dn': grid.DisplayName}

        # Initialize the base class.

        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(FastMarchingDistanceGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

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
        super(FastMarchingDistanceGrid, self)._Close()

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

        import skfmm

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
                    # we will compute distances for.

                    if self.Dimensions == 'yx':
                        grid = self._Grid
                    elif self.Dimensions == 'zyx':
                        grid = GridSlice(self._Grid, zIndex=s[0])
                    elif self.Dimensions == 'tyx':
                        grid = GridSlice(self._Grid, tIndex=s[0])
                    else:
                        grid = GridSlice(self._Grid, tIndex=s[0], zIndex=s[1])

                    # Get the 2D slice data's as 64-bit floats (this is
                    # required by the skfmm module).

                    sliceData = grid.Data[:, :]
                    assert len(sliceData.shape) == 2

                    phi = sliceData.astype('float64')       # astype always makes a copy

                    # Classify the cells as either outside (positive) or
                    # inside (zero or negative) the features of interest.

                    phi[phi > 0] = 1
                    phi[phi < 1] = -1

                    # Mask the slice, compute the fast marching distances, and
                    # store the resulting numpy array as our cached slice.

                    allNoData = False

                    if grid.NoDataValue is not None:
                        allNoData = Grid.numpy_equal_nan(sliceData, grid.NoDataValue).all()
                        mask = Grid.numpy_equal_nan(sliceData, grid.NoDataValue)

                        phi = numpy.ma.MaskedArray(phi, mask)

                    del sliceData

                    if not allNoData:
                        self._CachedSlice = skfmm.distance(phi, dx=grid.CoordIncrements[:])
                    else:
                        self._CachedSlice = numpy.zeros(phi.shape, dtype='float64')

                    # Apply min and max distances, if any.

                    if self._MinDist is not None:
                        self._CachedSlice[self._CachedSlice < self._MinDist] = self._MinDist

                    if self._MaxDist is not None:
                        self._CachedSlice[self._CachedSlice > self._MaxDist] = self._MaxDist

                    self._CachedSlice[mask] = self.NoDataValue
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


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
