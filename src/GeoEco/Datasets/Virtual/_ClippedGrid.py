# _ClippedGrid.py - A Grid that trims another Grid to a smaller
#  spatiotemoporal extent.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import bisect

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _

from .. import Grid


class ClippedGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, clipBy='Cell indices', xMin=None, xMax=None, yMin=None, yMax=None, zMin=None, zMax=None, tMin=None, tMax=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Validate the provided indices and convert them to a list of
        # slices with positive indices.

        sliceList = [self._GetSlicesForClippedExtent(grid, 'y', clipBy, yMin, yMax), self._GetSlicesForClippedExtent(grid, 'x', clipBy, xMin, xMax)]

        if 'z' in grid.Dimensions:
            sliceList = [self._GetSlicesForClippedExtent(grid, 'z', clipBy, zMin, zMax)] + sliceList
        elif zMin is not None or zMax is not None:
            raise ValueError(_('Values were provided for zMin or zMax but %(dn)s does not have a z dimension.') % {'dn': grid.DisplayName})

        if 't' in grid.Dimensions:
            sliceList = [self._GetSlicesForClippedExtent(grid, 't', clipBy, tMin, tMax)] + sliceList
        elif tMin is not None or tMax is not None:
            raise ValueError(_('Values were provided for tMin or tMax but %(dn)s does not have a t dimension.') % {'dn': grid.DisplayName})

        # Initialize our properties.

        self._Grid = grid
        self._SliceList = sliceList

        sliceListForDisplayName = []
        for i in range(len(grid.Dimensions)):
            dim = grid.Dimensions[i]
            coords = []
            indices = []

            if sliceList[i].start > 0:
                coord = grid.CenterCoords[dim, sliceList[i].start] if clipBy == 'cell indices' else \
                        xMin if dim == 'x' else yMin if dim == 'y' else zMin if dim == 'z' else tMin
                coords.append('%(dim)s >= %(coord)s' % {'dim': dim, 'coord': coord})
                indices.append(str(sliceList[i].start) + ':')
            
            if sliceList[i].stop < grid.Shape[i]:
                coord = grid.CenterCoords[dim, sliceList[i].stop - 1] if clipBy == 'cell indices' else \
                        xMax if dim == 'x' else yMax if dim == 'y' else zMax if dim == 'z' else tMax
                coords.append('%(dim)s <= %(coord)s' % {'dim': dim, 'coord': coord})
                indices.append(':' + str(sliceList[i].stop - 1))
            
            if len(coords) > 0:
                sliceListForDisplayName.append(' and '.join(coords) + ' (indices [' + ''.join(indices).replace('::',':') + '])')

        if len(sliceListForDisplayName) > 0:
            self._DisplayName = _('%(dn)s, clipped to cells with center coordinates of %(indices)s') % {'dn': self._Grid.DisplayName, 'indices': ', '.join(sliceListForDisplayName)}
        else:
            self._DisplayName = self._Grid.DisplayName

        # Initialize the base class.

        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(ClippedGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

        # Our goal is to imitate the contained grid except with a smaller
        # extent. In order to do this, we have to override the lazy properties
        # for the shape and corner coordinates. Set the shape now (we know it
        # already). For the corner coordinates,  we know that we'll be called
        # at _GetLazyPropertyPhysicalValue when they are needed, and we can
        # retrieve and modify the values from the contained grid at that
        # point.

        self.SetLazyPropertyValue('Shape', tuple([s.stop - s.start for s in sliceList]))

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        super(ClippedGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):
        if name == 'CornerCoords':
            return self._GetNewCornerCoords(self._Grid.GetLazyPropertyValue('CornerCoords'), self._Grid, self._SliceList)
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

    @classmethod
    def _GetSlicesForClippedExtent(cls, grid, dim, clipBy, start, stop):
        dimNum = grid.Dimensions.index(dim)
        
        if start is not None:
            if clipBy == 'cell indices':
                start = int(start)
                if start < 0:
                    absStart = grid.Shape[dimNum] + start
                else:
                    absStart = start
                if absStart < 0 or absStart > grid.Shape[dimNum] - 1:
                    raise IndexError(_('%(dim)sMin (%(value)i) is out of range.') % {'dim': dim, 'value': start})
            else:
                absStart = bisect.bisect_left(grid.CenterCoords[dim], start)
                if absStart > grid.Shape[dimNum] - 1:
                    raise IndexError(_('%(dim)sMin (%(value)s) is out of range. It must be less than or equal to %(max)s, the %(dim)s coordinate of the center of the right-most cell.') % {'dim': dim, 'value': repr(start), 'max': repr(grid.CenterCoords[dim, -1])})
        else:
            absStart = 0
        
        if stop is not None:
            if clipBy == 'cell indices':
                stop = int(stop)
                if stop < 0:
                    absStop = grid.Shape[dimNum] + stop
                else:
                    absStop = stop
                if absStop < 0 or absStop > grid.Shape[dimNum]:
                    raise IndexError(_('%(dim)sMax (%(value)i) is out of range.') % {'dim': dim, 'value': stop})
            else:
                if start is not None and stop < start:
                    raise IndexError(_('%(dim)sMin (%(value1)s) is greater than %(dim)sMax (%(value2)s). %(dim)sMax must be greater than %(dim)sMin.') % {'dim': dim, 'value1': repr(start), 'value2': repr(stop)})
                absStop = bisect.bisect_right(grid.CenterCoords[dim], stop)
                if absStop == 0:
                    raise IndexError(_('%(dim)sMax (%(value)s) is out of range. It must be greater than or equal to %(min)s, the %(dim)s coordinate of the center of the left-most cell.') % {'dim': dim, 'value': repr(stop), 'min': repr(grid.CenterCoords[dim, 0])})
        else:
            absStop = grid.Shape[dimNum]

        if absStart == absStop:
            if clipBy == 'cell indices':
                raise IndexError(_('%(dim)sMin and %(dim)sMax are the same (%(value)i). %(dim)sMax must be greater than %(dim)sMin.') % {'dim': dim, 'value': start})
            else:
                raise IndexError(_('%(dim)sMin and %(dim)sMax do not enclose the center of at least one cell. The clipped grid must have at least one cell along the %(dim)s axis. For this to happen, %(dim)sMin and %(dim)sMax must enclose the center of at least one cell.') % {'dim': dim})
        elif absStart > absStop:
            raise IndexError(_('%(dim)sMin (%(value1)i) is greater than %(dim)sMax (%(value2)i). %(dim)sMax must be greater than %(dim)sMin.') % {'dim': dim, 'value1': start, 'value2': stop})

        return slice(absStart, absStop)

    @classmethod
    def _GetNewCornerCoords(cls, oldCornerCoords, grid, sliceList):
        newCornerCoords = list(oldCornerCoords)
        
        for i in range(len(newCornerCoords)):
            if newCornerCoords[i] is not None:
                if grid.Dimensions[i] != 't':
                    if grid.CoordDependencies[i] is None:
                        newCornerCoords[i] = grid.CenterCoords[grid.Dimensions[i], sliceList[i].start]
                    else:
                        key = [grid.Dimensions[i]]
                        for d in grid.Dimensions:
                            if d == grid.Dimensions[i] or d in grid.CoordDependencies[i]:
                                key.append(sliceList[i].start)
                        newCornerCoords[i] = grid.CenterCoords.__getitem__(tuple(key))
                else:
                    tCornerCoordType = grid.GetLazyPropertyValue('TCornerCoordType')
                    if tCornerCoordType == 'min':
                        newCornerCoords[i] = grid.MinCoords['t', sliceList[i].start]
                    elif tCornerCoordType == 'center':
                        newCornerCoords[i] = grid.CenterCoords['t', sliceList[i].start]
                    else:
                        newCornerCoords[i] = grid.MaxCoords['t', sliceList[i].start]
                
        return tuple(newCornerCoords)

    def _GetCoordsForOffset(self, key, fixedIncrementOffset):

        # Validate the key.

        coord, coordNum, slices, sliceDims = self._GetSlicesForCoordsKey(key)

        # Adjust the slices list, which could be None, or a list of slices
        # and/or integers.

        if slices is not None:
            for i in range(0, len(sliceDims)):
                dimNum = self.Dimensions.index(sliceDims[i])
                
                if isinstance (slices[i], int):
                    slices[i] = self._AdjustCoord(slices[i], dimNum)
                    
                elif slices[i].start is None and slices[i].stop is None:
                    if slices[i].step is not None and slices[i].step < 0:
                        if self._SliceList[coordNum].start > 0:
                            slices[i] = slice(self._SliceList[coordNum].stop - 1, self._SliceList[coordNum].start - 1, slices[i].step)
                        else:
                            slices[i] = slice(self._SliceList[coordNum].stop - 1, None, slices[i].step)
                    else:
                        slices[i] = slice(self._SliceList[coordNum].start, self._SliceList[coordNum].stop, slices[i].step)
                        
                elif slices[i].start is not None and slices[i].stop is None:
                    if slices[i].step is not None and slices[i].step < 0:
                        if self._SliceList[coordNum].start > 0:
                            slices[i] = slice(self._AdjustCoord(slices[i].start, dimNum), self._SliceList[coordNum].start - 1, slices[i].step)
                        else:
                            slices[i] = slice(self._AdjustCoord(slices[i].start, dimNum), None, slices[i].step)
                    else:
                        slices[i] = slice(self._AdjustCoord(slices[i].start, dimNum), self._SliceList[coordNum].stop, slices[i].step)
                        
                elif slices[i].start is None and slices[i].stop is not None:
                    if slices[i].step is not None and slices[i].step < 0:
                        slices[i] = slice(self._SliceList[coordNum].stop - 1, self._AdjustCoord(slices[i].stop, dimNum), slices[i].step)
                    else:
                        slices[i] = slice(self._SliceList[coordNum].start, self._AdjustCoord(slices[i].stop, dimNum), slices[i].step)
                        
                else:
                    slices[i] = slice(self._AdjustCoord(slices[i].start, dimNum), self._AdjustCoord(slices[i].stop, dimNum), slices[i].step)
        else:
            slices = []
            for i in range(0, len(sliceDims)):
                dimNum = self.Dimensions.index(sliceDims[i])
                slices.append(self._SliceList[dimNum])

        # Get the coordinates from the contained grid.

        return self._Grid._GetCoordsForOffset(tuple([coord] + slices), fixedIncrementOffset)

    def _AdjustCoord(self, c, coordNum):
        if c >= 0:
            return c + self._SliceList[coordNum].start
        return c - (self._Grid.Shape[coordNum] - self._SliceList[coordNum].stop)

    # When reading and writing below: because the we did not override the
    # PhysicalDimensions lazy property, the sliceList is ordered according to
    # PhysicalDimensions, not Dimensions. But self._SliceList is ordered
    # according to Dimensions, so we have to be careful about pulling indices
    # from it when computing the slice to retreive from the contained grid.

    def _ReadNumpyArray(self, sliceList):
        slicesToRead = []
        for i, d in enumerate(self.GetLazyPropertyValue('PhysicalDimensions')):
            if not self.GetLazyPropertyValue('PhysicalDimensionsFlipped')[i]:
                offset = self._SliceList[self.Dimensions.index(d)].start
            else:
                offset = self._Grid.Shape[i] - self._SliceList[self.Dimensions.index(d)].stop
            slicesToRead.append(slice(sliceList[i].start + offset, sliceList[i].stop + offset, sliceList[i].step))
        return self._Grid._ReadNumpyArray(slicesToRead)

    def _WriteNumpyArray(self, sliceList, data):
        slicesToWrite = []
        for i, d in enumerate(self.GetLazyPropertyValue('PhysicalDimensions')):
            if not self.GetLazyPropertyValue('PhysicalDimensionsFlipped')[i]:
                offset = self._SliceList[self.Dimensions.index(d)].start
            else:
                offset = self._Grid.Shape[i] - self._SliceList[self.Dimensions.index(d)].stop
            slicesToWrite.append(slice(sliceList[i].start + offset, sliceList[i].stop + offset, sliceList[i].step))
        self._Grid._WriteNumpyArray(slicesToWrite, data)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
