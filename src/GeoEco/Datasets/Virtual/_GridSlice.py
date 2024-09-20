# _GridSlice.py - A Grid that represents a slice of another Grid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Types import DateTimeTypeMetadata, FloatTypeMetadata

from .. import Grid, QueryableAttribute


class GridSlice(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, tIndex=None, zIndex=None, tQAName='DateTime', tQADisplayName=_('Date'), tQACoordType='min', zQAName='Depth', zQADisplayName=_('Depth'), zQACoordType='center', displayName=None, additionalQueryableAttributeValues=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if tIndex is None and zIndex is None:
            raise ValueError(_('Both tIndex and zIndex are None. A value must be provided for at least one of them.'))

        if tIndex is not None:
            if 't' not in grid.Dimensions:
                raise TypeError(_('A value was provided for tIndex but %(dn)s does not have a t dimension.') % {'dn': grid.DisplayName})
            if tQAName is None:
                raise TypeError(_('If a value is provided for tIndex, a value must also be provided for tQAName.'))
            if tQADisplayName is None:
                raise TypeError(_('If a value is provided for tIndex, a value must also be provided for tQADisplayName.'))
            if tQACoordType is None:
                raise TypeError(_('If a value is provided for tIndex, a value must also be provided for tQACoordType.'))

        if zIndex is not None:
            if 'z' not in grid.Dimensions:
                raise TypeError(_('A value was provided for zIndex but %(dn)s does not have a z dimension.') % {'dn': grid.DisplayName})
            if zQAName is None:
                raise TypeError(_('If a value is provided for zIndex, a value must also be provided for zQAName.'))
            if zQADisplayName is None:
                raise TypeError(_('If a value is provided for zIndex, a value must also be provided for zQADisplayName.'))
            if zQACoordType is None:
                raise TypeError(_('If a value is provided for zIndex, a value must also be provided for zQACoordType.'))

        # Validate the provided indices and make them positive.

        if tIndex is not None:
            if tIndex < 0:
                if tIndex + grid.Shape[0] < 0:
                    raise IndexError(_('tIndex is out of range.'))
                tIndex += grid.Shape[0]
            elif tIndex >= grid.Shape[0]:
                raise IndexError(_('tIndex is out of range.'))

        if zIndex is not None:
            if 'z' not in grid.Dimensions:
                if zIndex + grid.Shape[grid.Dimensions.index('z')] < 0:
                    raise IndexError(_('zIndex is out of range.'))
                zIndex += grid.Shape[grid.Dimensions.index('z')]
            elif zIndex >= grid.Shape[grid.Dimensions.index('z')]:
                raise IndexError(_('zIndex is out of range.'))

        # Initialize our properties.

        self._Grid = grid
        self._TIndex = tIndex
        self._ZIndex = zIndex

        if self._TIndex is not None:
            self._TQAName = tQAName
            self._TQADisplayName = tQADisplayName
            self._TQACoordType = tQACoordType
        else:
            self._TQAName = None
            self._TQADisplayName = None
            self._TQACoordType = None

        if self._ZIndex is not None:
            self._ZQAName = zQAName
            self._ZQADisplayName = zQADisplayName
            self._ZQACoordType = zQACoordType
        else:
            self._ZQAName = None
            self._ZQADisplayName = None
            self._ZQACoordType = None

        if displayName is not None:
            self._DisplayName = displayName
        elif self._TIndex is not None and self._ZIndex is not None:
            self._DisplayName = _('%(tdn)s, %(zdn)s slice [%(tIndex)i, %(zIndex)i] of %(dn)s') % {'tdn': self._TQADisplayName.lower(), 'zdn': self._ZQADisplayName.lower(), 'tIndex': self._TIndex, 'zIndex': self._ZIndex, 'dn': self._Grid.DisplayName}
        elif self._TIndex is not None:
            self._DisplayName = _('%(tdn)s slice %(tIndex)i of %(dn)s') % {'tdn': self._TQADisplayName.lower(), 'tIndex': self._TIndex, 'dn': self._Grid.DisplayName}
        else:
            self._DisplayName = _('%(zdn)s slice %(zIndex)i of %(dn)s') % {'zdn': self._ZQADisplayName.lower(), 'zIndex': self._ZIndex, 'dn': self._Grid.DisplayName}

        # For our queryable attributes, use all of those of the grid
        # plus the ones for the t and/or z dimensions.

        queryableAttributes = []
        queryableAttributes.extend(grid.GetAllQueryableAttributes())

        queryableAttributeValues = {}
        for qa in queryableAttributes:
            if qa.DerivedFromAttr is None or qa.DerivedFromAttr not in [self._TQAName, self._ZQAName]:
                queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)

        if self._TIndex is not None:
            queryableAttributes.append(QueryableAttribute(self._TQAName, self._TQADisplayName, DateTimeTypeMetadata()))
            if self._TQACoordType == 'min':
                queryableAttributeValues[self._TQAName] = self._Grid.MinCoords['t', self._TIndex]
            elif self._TQACoordType == 'center':
                queryableAttributeValues[self._TQAName] = self._Grid.CenterCoords['t', self._TIndex]
            else:
                queryableAttributeValues[self._TQAName] = self._Grid.MaxCoords['t', self._TIndex]

        if self._ZIndex is not None:
            queryableAttributes.append(QueryableAttribute(self._ZQAName, self._ZQADisplayName, FloatTypeMetadata()))
            if self._ZQACoordType == 'min':
                queryableAttributeValues[self._ZQAName] = self._Grid.MinCoords['z', self._ZIndex]
            elif self._ZQACoordType == 'center':
                queryableAttributeValues[self._ZQAName] = self._Grid.CenterCoords['z', self._ZIndex]
            else:
                queryableAttributeValues[self._ZQAName] = self._Grid.MaxCoords['z', self._ZIndex]

        if additionalQueryableAttributeValues is not None:
            queryableAttributeValues.update(additionalQueryableAttributeValues)

        # Our goal is to imitate the contained grid except with fewer
        # dimensions. In order to do this, we have to override the dimensions
        # and other lazy properties related to it. Obtain the indices of the
        # remaining dimensions.

        if 'z' in self._Grid.Dimensions and self._ZIndex is None:
            self._RemainingDimensionIndices = [1,2,3]     # It is a t slice of a tzyx grid, so remaining dimensions are zyx
        elif 't' in self._Grid.Dimensions and self._TIndex is None:
            self._RemainingDimensionIndices = [0,2,3]     # It is a z slice of a tzyx grid, so remaining dimensions are tyx
        else:
            self._RemainingDimensionIndices = list(range(len(self._Grid.Dimensions)))[-2:]     # It is either a tz slice of a tzyx grid, a t slice of a tyx grid, or a z slice of a zyx grid, so remaining dimensions are yx

        # Initialize the base class.
        
        super(GridSlice, self).__init__(queryableAttributes=tuple(queryableAttributes), queryableAttributeValues=queryableAttributeValues)

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the requested property is sequence related to the dimensions, get
        # the values from the grid we're slicing but remove the element
        # corresponding to the sliced dimension(s).

        if name == 'Dimensions':
            return ''.join([self._Grid.Dimensions[i] for i in self._RemainingDimensionIndices])

        if name == 'Shape':
            return tuple([self._Grid.Shape[i] for i in self._RemainingDimensionIndices])

        if name == 'CoordDependencies':
            return tuple([self._Grid.CoordDependencies[i] for i in self._RemainingDimensionIndices])

        if name == 'CoordIncrements':
            return tuple([self._Grid.CoordIncrements[i] for i in self._RemainingDimensionIndices])

        if name == 'CornerCoords':
            return tuple([self._Grid.GetLazyPropertyValue('CornerCoords')[i] for i in self._RemainingDimensionIndices])

        # If the requested property is PhysicalDimensions or
        # PhysicalDimensionsFlipped, return values indicating the dimensions
        # in the ideal order. The contained grid takes care of reordering, if
        # needed.

        if name == 'PhysicalDimensions':
            return self.Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self.Dimensions))

        # Otherwise just get the unaltered value from the contained grid.

        return self._Grid.GetLazyPropertyValue(name)

    @classmethod
    def _TestCapability(cls, capability):
        return cls._Grid._TestCapability(capability)

    @classmethod
    def _GetSRTypeForSetting(cls):
        return cls._Grid._GetSRTypeForSetting()

    def _SetSpatialReference(self, sr):
        return self._Grid._SetSpatialReference(sr)

    def _GetUnscaledDataAsArray(self, key):
        return self._Grid._GetUnscaledDataAsArray(self._AddSlicedDimsToKey(key))

    def _SetUnscaledDataWithArray(self, key, value):
        return self._Grid._SetUnscaledDataWithArray(self._AddSlicedDimsToKey(key), value)

    def _AddSlicedDimsToKey(self, key):

        # Validate the key. Although we are calling the _ValidateAndFlipKey
        # function, because our PhysicalDimensionsFlipped contains only False,
        # none of the key's indices will be flipped.
        
        key2 = self._ValidateAndFlipKey(key)

        # The key does not include the dimensions the sliced dimensions. Add
        # these to the key as single indices.

        if self._ZIndex is not None:
            key2.insert(0, self._ZIndex)

        if self._TIndex is not None:
            key2.insert(0, self._TIndex)

        # Return a tuple.

        return tuple(key2)

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        return self._Grid._GetCoords(coord, coordNum, slices, sliceDims, fixedIncrementOffset)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
