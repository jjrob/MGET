# _NumpyGrid.py - Defines NumpyGrid, which wraps a numpy array in the Grid
# interface.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from . import Grid


class NumpyGrid(Grid):
    __doc__ = DynamicDocString()

    def _GetArray(self):
        return self._NumpyArray
    
    Array = property(_GetArray, doc=DynamicDocString())
    
    def __init__(self, numpyArray, displayName, spatialReference, dimensions, coordIncrements, cornerCoords, unscaledNoDataValue=None,
                 tIncrementUnit=None, tSemiRegularity=None, tCountPerSemiRegularPeriod=None, tCornerCoordType=None, tOffsetFromParsedTime=None, coordDependencies=None,
                 physicalDimensions=None, physicalDimensionsFlipped=None,
                 scaledDataType=None, scaledNoDataValue=None, scalingFunction=None, unscalingFunction=None,
                 parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if len(numpyArray.shape) not in [2, 3, 4]:
            raise ValueError(_('numpyArray must have 2, 3, or 4 dimensions.'))

        if len(dimensions) != len(numpyArray.shape):
            raise ValueError(_('The length of the dimensions string must be equal to the number of dimensions of numpyArray.'))

        if unscaledNoDataValue is not None:
            if numpyArray.dtype.name in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32'] and not isinstance(unscaledNoDataValue, int):
                raise TypeError(_('When numpyArray has the %(name)s dtype, unscaledNoDataValue must be a Python int.') % {'name': numpyArray.dtype.name})
            if numpyArray.dtype.name in ['float32', 'float64'] and not isinstance(unscaledNoDataValue, float):
                raise TypeError(_('When numpyArray has the %(name)s dtype, unscaledNoDataValue must be a Python float.') % {'name': numpyArray.dtype.name})

        if 't' in dimensions:
            if tIncrementUnit is None:
                raise ValueError(_('tIncrementUnit must be provided when dimensions contains \'t\'.'))
            if tCornerCoordType is None:
                raise ValueError(_('tCornerCoordType must be provided when dimensions contains \'t\'.'))

        if physicalDimensions is not None:
            if len(physicalDimensions) != len(dimensions):
                raise ValueError(_('physicalDimensions must be the same length as dimensions.'))
            for d in physicalDimensions:
                if d not in dimensions:
                    raise ValueError(_('The physicalDimensions string must contain the same characters as the dimensions string (but they may be in a different order).'))

        if not all((scaledDataType is not None, scaledNoDataValue is not None, scalingFunction is not None, unscalingFunction is not None)) and not all((scaledDataType is None, scaledNoDataValue is None, scalingFunction is None, unscalingFunction is None)):
            raise ValueError(_('All of (scaledDataType, scaledNoDataValue, scalingFunction, unscalingFunction) must be None, or none of them must be None.'))

        # Initialize our properties.

        self._NumpyArray = numpyArray
        self._DisplayName = displayName

        # Build a dictionary of lazy property values from the caller's
        # parameters.

        if coordDependencies is None:
            coordDependencies = tuple([None] * len(dimensions))

        if 't' not in dimensions:
            tIncrementUnit = None
            tSemiRegularity = None
            tCountPerSemiRegularPeriod = None
            tCornerCoordType = None
            tOffsetFromParsedTime = None

        if physicalDimensions is None:
            physicalDimensions = dimensions

        if physicalDimensionsFlipped is None:
            physicalDimensionsFlipped = tuple([False] * len(dimensions))

        shape = []
        for dim in dimensions:
            shape.append(numpyArray.shape[physicalDimensions.index(dim)])
        shape = tuple(shape)

        lpv = {'SpatialReference': spatialReference,
               'Dimensions': dimensions,
               'Shape': shape,
               'CoordDependencies': coordDependencies,
               'CoordIncrements': coordIncrements,
               'TIncrementUnit': tIncrementUnit,
               'TSemiRegularity': tSemiRegularity,
               'TCountPerSemiRegularPeriod': tCountPerSemiRegularPeriod,
               'TCornerCoordType': tCornerCoordType,
               'TOffsetFromParsedTime': tOffsetFromParsedTime,
               'CornerCoords': cornerCoords,
               'PhysicalDimensions': physicalDimensions,
               'PhysicalDimensionsFlipped': physicalDimensionsFlipped,
               'UnscaledDataType': numpyArray.dtype.name,
               'UnscaledNoDataValue': unscaledNoDataValue,
               'ScaledDataType': scaledDataType,
               'ScaledNoDataValue': scaledNoDataValue,
               'ScalingFunction': scalingFunction,
               'UnscalingFunction': unscalingFunction}

        if lazyPropertyValues is not None:
            for name, value in lazyPropertyValues.items():
                lpv[name] = value

        # Initialize the base class.

        super(NumpyGrid, self).__init__(parentCollection=parentCollection, queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lpv)

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):
        return None

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['setspatialreference']:
            return None
        if isinstance(cls, NumpyGrid):
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__name__, 'cap': capability})

    @classmethod
    def _GetSRTypeForSetting(cls):
        return 'Obj'

    def _SetSpatialReference(self, sr):
        self.SetLazyPropertyValue('SpatialReference', sr)

    def _ReadNumpyArray(self, sliceList):
        return self._NumpyArray.__getitem__(tuple(sliceList)), self.GetLazyPropertyValue('UnscaledNoDataValue')

    def _WriteNumpyArray(self, sliceList, data):
        self._NumpyArray.__setitem__(tuple(sliceList), data)

    @classmethod
    def CreateFromGrid(cls, grid):
        cls.__doc__.Obj.ValidateMethodInvocation()

        cornerCoords = [grid.CenterCoords[d, 0] for d in grid.Dimensions]
        if 't' in grid.Dimensions:
            if grid.GetLazyPropertyValue('TCornerCoordType') == 'min':
                cornerCoords[0] = grid.MinCoords['t', 0]
            elif grid.GetLazyPropertyValue('TCornerCoordType') == 'max':
                cornerCoords[0] = grid.MaxCoords['t', 0]

        qav = {}
        for qa in grid.GetAllQueryableAttributes():
            qav[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)

        return NumpyGrid(grid.Data[:],
                         grid.DisplayName,
                         grid.GetSpatialReference('Obj'),
                         grid.Dimensions,
                         grid.CoordIncrements,
                         tuple(cornerCoords),
                         grid.UnscaledNoDataValue,
                         grid.TIncrementUnit,
                         grid.TSemiRegularity,
                         grid.TCountPerSemiRegularPeriod,
                         grid.GetLazyPropertyValue('TCornerCoordType'),
                         grid.GetLazyPropertyValue('TOffsetFromParsedTime'),
                         grid.CoordDependencies,
                         queryableAttributes=tuple(grid.GetAllQueryableAttributes()),
                         queryableAttributeValues=qav)


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
