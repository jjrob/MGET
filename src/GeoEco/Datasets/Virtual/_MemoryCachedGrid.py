# _MemoryCachedGrid.py - A Grid that wraps another Grid, caching blocks of it
# in memory to facilitate fast repeated retrievals.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import math

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _

from .. import Grid


class MemoryCachedGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, maxCacheSize=None, xMinBlockSize=None, yMinBlockSize=None, zMinBlockSize=None, tMinBlockSize=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Validate that the caller provided positive values for the max cache
        # size and all required dimensions. If not, report a debug message (no
        # need for a warning) and set everything to zero.

        if maxCacheSize is None or maxCacheSize <= 0 or \
           xMinBlockSize is None or xMinBlockSize <= 0 or \
           yMinBlockSize is None or yMinBlockSize <= 0 or \
           'z' in grid.Dimensions and (zMinBlockSize is None or zMinBlockSize <= 0) or \
           't' in grid.Dimensions and (tMinBlockSize is None or tMinBlockSize <= 0) :
            maxCacheSize = 0
            self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: Wrapping %(dn)s. No caching will be done because one of the required parameters was missing or zero.'), {'id': id(self), 'dn': grid.DisplayName})
        else:
            self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: Wrapping %(dn)s. maxCacheSize=%(maxCacheSize)s, xMinBlockSize=%(xMinBlockSize)s, yMinBlockSize=%(yMinBlockSize)s, zMinBlockSize=%(zMinBlockSize)s, tMinBlockSize=%(tMinBlockSize)s.'), {'id': id(self), 'dn': grid.DisplayName, 'maxCacheSize': repr(maxCacheSize), 'xMinBlockSize': repr(xMinBlockSize), 'yMinBlockSize': repr(yMinBlockSize), 'zMinBlockSize': repr(zMinBlockSize), 'tMinBlockSize': repr(tMinBlockSize)})

        # Initialize our remaining properties.

        self._Grid = grid
        self._MaxCacheSize = maxCacheSize

        if maxCacheSize > 0:
            if grid.Dimensions == 'yx':
                self._MinBlockSize = (yMinBlockSize, xMinBlockSize)
            elif grid.Dimensions == 'zyx':
                self._MinBlockSize = (zMinBlockSize, yMinBlockSize, xMinBlockSize)
            elif grid.Dimensions == 'tyx':
                self._MinBlockSize = (tMinBlockSize, yMinBlockSize, xMinBlockSize)
            else:
                self._MinBlockSize = (tMinBlockSize, zMinBlockSize, yMinBlockSize, xMinBlockSize)
        else:
            self._MinBlockSize =  None

        self._Cache = []
        self._CacheSize = 0

        # Initialize the base class.
        
        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(MemoryCachedGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        super(MemoryCachedGrid, self)._Close()

    def _GetDisplayName(self):
        return self._Grid.DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):
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

        # If the max cache size is zero, just forward the call to the
        # contained grid.

        if self._MaxCacheSize <= 0:
            return self._Grid._ReadNumpyArray(sliceList)

        self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: Servicing request for slice [%(slice)s].'), {'id': id(self), 'slice': ','.join([str(s.start) + ':' + str(s.stop) for s in sliceList])})

        # Allocate the numpy array that we will return.

        import numpy
        data = numpy.zeros([s.stop-s.start for s in sliceList], dtype=self.UnscaledDataType)

        # Try to fill the array completely from the cache.
        
        remainingRegion = []
        remainingRegion.extend(sliceList)

        if self._CacheSize > 0:
            remainingRegion = self._FillArrayFromCache(sliceList, remainingRegion, data)

        # If we could not fill the entire array, retrieve and cache
        # the region that was not filled in, and fill it in.

        if remainingRegion is not None:
            regionToRead = []
            
            for i in range(len(sliceList)):
                cellsRemaining = remainingRegion[i].stop - remainingRegion[i].start
                if cellsRemaining >= self._MinBlockSize[i]:
                    regionToRead.append(remainingRegion[i])
                else:
                    maxIndex = self.Shape[self.Dimensions.index(self.GetLazyPropertyValue('PhysicalDimensions')[i])]
                    regionToRead.append(slice(max(0, remainingRegion[i].start - int(math.floor((self._MinBlockSize[i] - cellsRemaining) / 2.))), min(maxIndex, int(math.ceil(remainingRegion[i].stop + (self._MinBlockSize[i] - cellsRemaining) / 2.)))))

            self._Cache.insert(0, [regionToRead, self._Grid._ReadNumpyArray(regionToRead)[0]])

            bytesAdded = regionToRead[0].stop - regionToRead[0].start
            for i in range(1, len(regionToRead)):
                bytesAdded *= regionToRead[i].stop - regionToRead[i].start
            self._CacheSize += bytesAdded * self._Cache[0][1].dtype.itemsize

            self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: Added slice [%(slice)s] to the in-memory cache. New cache size = %(size)i bytes.'), {'id': id(self), 'slice': ','.join([str(s.start) + ':' + str(s.stop) for s in regionToRead]), 'size': self._CacheSize})
                
            self._FillArrayFromCache(sliceList, remainingRegion, data)

        # If the cache is now larger than the maximum allowed
        # size, trim it the oldest blocks off the end.

        while self._CacheSize > self._MaxCacheSize:
            slices, block = self._Cache.pop()

            bytesDeleted = slices[0].stop - slices[0].start
            for i in range(1, len(slices)):
                bytesDeleted *= slices[i].stop - slices[i].start
            self._CacheSize -= bytesDeleted * block.dtype.itemsize

            self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: Deleted slice [%(slice)s] from the in-memory cache. New cache size = %(size)i bytes.'), {'id': id(self), 'slice': ','.join([str(s.start) + ':' + str(s.stop) for s in slices]), 'size': self._CacheSize})

        # Return successfully.

        return data, self.UnscaledNoDataValue

    def _FillArrayFromCache(self, sliceList, remainingRegion, data):

        # The cache contains zero or more slices, either rectangles (if 2D),
        # rectangular parallelepipeds (if 3D), or hyperrectangles (if 4D).
        # Ideally we would be able to determine, for any collection of slices,
        # whether they collectively completely overlap the slice requested by
        # the caller and if so, service the request from the slices. If there
        # was only partial overlap, we'd "fill in the holes" with multiple
        # read requests to the underlying grid.
        #
        # A completely general algorithm that optimally handles all cases
        # appears too complicated to be worth implementing. Instead we
        # implement a much simpler algorithm that should handle many common
        # cases. This algorithm repeatedly iterates through the cached slices,
        # looking for slices that overlap the caller's slice such that region
        # that remains unoverlapped after each iteration is still rectangular.
        # The defining characteristic of candidate slices is that their extent
        # exceeds that of the remaining region on all but one side, in which
        # case the algorithm continues, or on all sides, in which case the
        # caller's slice has been completely covered by the cached slices.

        i = 0
        firstUnusedSlice = 0
        while i < len(self._Cache):

            # Count how many dimensions of this cached slice fully
            # overlap (i.e. enclose) or partially overlap the
            # remaining region of this dimension.

            dimsWithFullOverlap = []
            dimsWithPartialOverlap = []
            for j in range(len(self.Dimensions)):
                if self._Cache[i][0][j].start <= remainingRegion[j].start and self._Cache[i][0][j].stop >= remainingRegion[j].stop:
                    dimsWithFullOverlap.append(j)
                elif self._Cache[i][0][j].start <= remainingRegion[j].start and self._Cache[i][0][j].stop > remainingRegion[j].start or self._Cache[i][0][j].stop >= remainingRegion[j].stop and self._Cache[i][0][j].start < remainingRegion[j].stop:
                    dimsWithPartialOverlap.append(j)

            #self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: i=%(i)i, self._Cache[i][0]=%(cachedSlices)s, dimsWithFullOverlap=%(dimsWithFullOverlap)s, dimsWithPartialOverlap=%(dimsWithPartialOverlap)s'), {'id': id(self), 'i': i, 'cachedSlices': repr(self._Cache[i][0]), 'dimsWithFullOverlap': repr(dimsWithFullOverlap), 'dimsWithPartialOverlap': repr(dimsWithPartialOverlap)})

            # If all of the dimensions of this cached slice fully overlap the
            # remaining region, it means the remaining region is a subset of
            # (i.e. fully contained by) this cached slice.

            if len(dimsWithFullOverlap) == len(self.Dimensions):
                self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: Reading [%(slice1)s] from cached slice [%(slice2)s].'), {'id': id(self), 'slice1': ','.join([str(s.start) + ':' + str(s.stop) for s in remainingRegion]), 'slice2': ','.join([str(s.start) + ':' + str(s.stop) for s in self._Cache[i][0]])})

                data.__setitem__(tuple([slice(s[0].start-s[1].start, s[0].stop-s[1].start) for s in zip(remainingRegion, sliceList)]), self._Cache[i][1].__getitem__(tuple([slice(s[0].start-s[1].start, s[0].stop-s[1].start) for s in zip(remainingRegion, self._Cache[i][0])])))

                self._Cache.insert(0, self._Cache.pop(i))
                remainingRegion = None
                break

            # If all but one of the dimensions of this cached slice fully
            # overlap the remaining region and the remaining one partially
            # overlaps, it means we can use the slice to fill in a block of
            # the rectangular region such that the part that remains is a
            # smaller rectangle (2D) / rectangular parallelepiped (3D) /
            # hyperrectangle (4D).

            if len(dimsWithFullOverlap) == len(self.Dimensions) - 1 and len(dimsWithPartialOverlap) == 1:
                cachedRegion = []
                for j in range(len(self.Dimensions)):
                    if j in dimsWithFullOverlap:
                        cachedRegion.append(remainingRegion[j])
                    elif self._Cache[i][0][j].start > remainingRegion[j].start:
                        cachedRegion.append(slice(self._Cache[i][0][j].start, remainingRegion[j].stop))
                        remainingRegion[j] = slice(remainingRegion[j].start, self._Cache[i][0][j].start)
                    else:
                        cachedRegion.append(slice(remainingRegion[j].start, self._Cache[i][0][j].stop))
                        remainingRegion[j] = slice(self._Cache[i][0][j].stop, remainingRegion[j].stop)

                self._LogDebug(_('MemoryCachedGrid 0x%(id)016X: Reading [%(slice1)s] from cached slice [%(slice2)s].'), {'id': id(self), 'slice1': ','.join([str(s.start) + ':' + str(s.stop) for s in cachedRegion]), 'slice2': ','.join([str(s.start) + ':' + str(s.stop) for s in self._Cache[i][0]])})

                data.__setitem__([slice(s[0].start-s[1].start, s[0].stop-s[1].start) for s in zip(cachedRegion, sliceList)], self._Cache[i][1].__getitem__([slice(s[0].start-s[1].start, s[0].stop-s[1].start) for s in zip(cachedRegion, self._Cache[i][0])]))

                self._Cache.insert(0, self._Cache.pop(i))
                firstUnusedSlice += 1
                i = firstUnusedSlice
                continue
            
            # Go on to the next slice.

            i += 1

        # Return the list of slices that define the region not
        # fulfilled from the cache, if any.

        return remainingRegion

    def _WriteNumpyArray(self, sliceList, data):

        # If the caller writes anything, invalidate the whole cache.
        # This is less than optimal, but we're not really intended to
        # be used by callers that need to both write and read.
        
        self._Cache = []
        return self._Grid._WriteNumpyArray(sliceList, data)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
