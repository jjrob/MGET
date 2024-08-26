# _SeafloorGrid.py - A Grid that extracts the deepest available values of a
#  Grid that has a z (depth) dimension, yielding a single layer representing
#  values at the seafloor.
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

class SeafloorGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, queryableAttributes=None, queryableAttributeValues=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Validate that the grid has z coordinates.

        if 'z' not in grid.Dimensions:
            raise ValueError(_('Cannot create a grid representing the values of the %(dn)s at the seafloor because that grid does not have a depth coordinate.') % {'dn': grid.DisplayName})

        # Validate that the grid has an UnscaledNoDataValue. If there is no
        # UnscaledNoDataValue, it means we can't tell where there is data and
        # where there isn't.
        
        if grid.UnscaledNoDataValue is None:
            raise ValueError(_('Cannot create a grid representing the values of the %(dn)s at the seafloor because that grid does not have an UnscaledNoDataValue.') % {'dn': grid.DisplayName})
        
        # Initialize our properties.
        
        self._Grid = grid
        self._DisplayName = _('seafloor values of the %(dn)s') % {'dn': grid.DisplayName}

        # For our queryable attributes, copy all of those of the grid plus
        # those provided by the caller.

        qa = []
        if grid._QueryableAttributes is not None:
            qa.extend(list(grid._QueryableAttributes))
        if queryableAttributes is not None:
            qa.extend(queryableAttributes)

        qav = {}
        if grid._QueryableAttributeValues is not None:
            qav.update(grid._QueryableAttributeValues)
        if queryableAttributeValues is not None:
            qav.update(queryableAttributeValues)

        # Initialize the base class.
        
        super(SeafloorGrid, self).__init__(parentCollection=grid.ParentCollection, queryableAttributes=tuple(qa), queryableAttributeValues=qav)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        super(SeafloorGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the caller is requesting one of the sequences related to the
        # dimensions, get the value from the contained grid but remove the z
        # dimension.
        
        if name == 'Dimensions':
            if self._Grid.Dimensions == 'tzyx':        # It is either tzyx or zyx.
                return 'tyx'
            return 'yx'

        if name == 'Shape':
            if self._Grid.Dimensions == 'tzyx':
                return (self._Grid.Shape[0], self._Grid.Shape[2], self._Grid.Shape[3])
            return (self._Grid.Shape[1], self._Grid.Shape[2])

        if name == 'CoordDependencies':
            if self._Grid.Dimensions == 'tzyx':
                return (self._Grid.CoordDependencies[0], self._Grid.CoordDependencies[2], self._Grid.CoordDependencies[3])
            return (self._Grid.CoordDependencies[1], self._Grid.CoordDependencies[2])

        if name == 'CoordIncrements':
            if self._Grid.Dimensions == 'tzyx':
                return (self._Grid.CoordIncrements[0], self._Grid.CoordIncrements[2], self._Grid.CoordIncrements[3])
            return (self._Grid.CoordIncrements[1], self._Grid.CoordIncrements[2])

        if name == 'CornerCoords':
            cornerCoords = self._Grid.GetLazyPropertyValue('CornerCoords')
            if self._Grid.Dimensions == 'tzyx':
                return (cornerCoords[0], cornerCoords[2], cornerCoords[3])
            return (cornerCoords[1], cornerCoords[2])

        if name == 'PhysicalDimensions':
            physicalDimensions = ''
            for d in self._Grid.GetLazyPropertyValue('PhysicalDimensions'):
                if d != 'z':
                    physicalDimensions += d
            return physicalDimensions

        if name == 'PhysicalDimensionsFlipped':
            physicalDimensionsFlipped = []
            for i, d in enumerate(self._Grid.GetLazyPropertyValue('PhysicalDimensions')):
                if d != 'z':
                    physicalDimensionsFlipped.append(self._Grid.GetLazyPropertyValue('PhysicalDimensionsFlipped')[i])
            return tuple(physicalDimensionsFlipped)

        # Otherwise get the value from the contained grid.

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

        # Initialize a numpy array to return with the UnscaledNoDataValue.

        import numpy
        
        shape = [s.stop - s.start for s in sliceList]
        result = numpy.zeros(shape, dtype=str(self.UnscaledDataType)) + self.UnscaledNoDataValue
        hasNoData = Grid.numpy_equal_nan(result, self.UnscaledNoDataValue)

        # Iterate through the depth layers, from deepest to shallowest,
        # filling cells of the result array that still have no data with
        # values from the depth layer.

        zIndex = self._Grid.GetLazyPropertyValue('PhysicalDimensions').index('z')
        if self._Grid.GetLazyPropertyValue('PhysicalDimensionsFlipped')[zIndex]:
            zLayers = list(range(self._Grid.Shape[-3]))
        else:
            zLayers = list(range(self._Grid.Shape[-3] - 1, -1, -1))

        for z in zLayers:
            sliceToRequest = list() + sliceList
            sliceToRequest.insert(zIndex, slice(z, z+1))
            data = self._Grid._ReadNumpyArray(sliceToRequest)[0]

            sliceToExtract = [slice(None) for i in range(len(sliceList))]
            sliceToExtract.insert(zIndex, 0)
            data = data.__getitem__(tuple(sliceToExtract))

            result[hasNoData] = data[hasNoData]

            hasNoData = Grid.numpy_equal_nan(result, self.UnscaledNoDataValue)
            if numpy.logical_not(hasNoData).all():
                break

        # Return the result.

        return result, self.UnscaledNoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
