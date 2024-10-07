# DerivedGrid.py - A Grid that that derives its values from other Grids with a
# function you provide.
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


class DerivedGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grids, func, displayName, dataType=None, noDataValue=None, queryableAttributes=None, queryableAttributeValues=None, allowUnmasking=False):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Grids = grids
        self._Func = func
        self._DisplayName = displayName
        self._AllowUnmasking = allowUnmasking
        self._ValidatedGrids = False

        # Initialize the base class.
        
        super(DerivedGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

        # Set lazy properties that override those of the contained grids.

        self.SetLazyPropertyValue('UnscaledDataType', dataType if dataType is not None else self._Grids[0].DataType)
        self.SetLazyPropertyValue('UnscaledNoDataValue', noDataValue if noDataValue is not None else self._Grids[0].NoDataValue)
        self.SetLazyPropertyValue('ScaledDataType', None)
        self.SetLazyPropertyValue('ScaledNoDataValue', None)
        self.SetLazyPropertyValue('ScalingFunction', None)
        self.SetLazyPropertyValue('UnscalingFunction', None)

    def _Close(self):
        if hasattr(self, '_Grids') and self._Grids is not None:
            for grid in self._Grids:
                grid.Close()
        super(DerivedGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the requested property is PhysicalDimensions or
        # PhysicalDimensionsFlipped, return values indicating the dimensions
        # in the ideal order. The contained grids take care of reordering, if
        # needed.

        if name == 'PhysicalDimensions':
            return self.Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self.Dimensions))

        # Otherwise just get the unaltered value from the first contained
        # grid.

        return self._Grids[0].GetLazyPropertyValue(name)

    @classmethod
    def _TestCapability(cls, capability):
        if capability == 'SetSpatialReference':
            return NotImplementedError(_('DerivedGrid does not support setting the spatial reference.'))
        return cls._Grids[0]._TestCapability(capability)

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        return self._Grids[0]._GetCoords(coord, coordNum, slices, sliceDims, fixedIncrementOffset)

    def _ReadNumpyArray(self, sliceList):

        # If we have not yet validated the grids, do so now.

        if not self._ValidatedGrids:
            if len(self._Grids) > 1:
                for i, grid in enumerate(self._Grids):
                    if i > 0 and grid.Shape != self._Grids[0].Shape:
                        raise ValueError(_('self._Grids[%(i)s] has the shape %(shape1)r, which is not the same as self._Grids[0], which has shape %(shape0)r.') % {'i': i, 'shape1': self._Grids[i].Shape, 'shape0': self._Grids[0].Shape})

            self._ValidatedGrids = True

        # Evaluate the function.

        import numpy

        data = numpy.asarray(self._Func(self._Grids, tuple(sliceList)), dtype=self.DataType)

        # If a no data value was provided, mask any cells that have no data in
        # any of the grids. If the grid had fewer dimensions, automatically
        # expand the data.

        if self.NoDataValue is not None and not self._AllowUnmasking:
            for grid in self._Grids:
                if grid.NoDataValue is not None:
                    gridData = grid.Data.__getitem__(tuple(sliceList[len(sliceList)-len(grid.Shape):]))

                    for i in range(len(sliceList)-len(grid.Shape)-1, -1, -1):
                        gridData = numpy.concatenate([numpy.expand_dims(gridData,0)] * (sliceList[i].stop - sliceList[i].start), 0)

                    data[Grid.numpy_equal_nan(gridData, grid.NoDataValue)] = self.NoDataValue

        # Return the data and no data value.

        return data, self.NoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
