# _MaskedGrid.py - A Grid that sets cells of another Grid to NoData
# according to one or more Grids representing masks.
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


class MaskedGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, masks, operators, values, unscaledNoDataValue=None, scaledNoDataValue=None, tolerance=1e-9):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        if len(values) < len(operators):
            values = values + [None] * (len(operators) - len(values))

        self._Grid = grid
        self._Masks = masks
        self._Operators = operators
        self._Values = values
        self._UnscaledNoDataValue = unscaledNoDataValue
        self._ScaledNoDataValue = scaledNoDataValue
        self._Tolerance = tolerance
        self._MaskOffsets = None

        self._DisplayName = _('%(dn)s, masked where %(maskExpressions)s') % {'dn': grid.DisplayName, 'maskExpressions': _(' or ').join([self._GetMaskDisplayExpression(*s) for s in zip(masks, operators, values)])}

        # Initialize the base class.
        
        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(MaskedGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
            for mask in self._Masks:
                mask.Close()
        super(MaskedGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetMaskDisplayExpression(self, mask, op, value):
        if op in ['=', '==', '!=', '<>', '<', '<=', '>', '>']:
            return mask.DisplayName + ' ' + op + ' ' + repr(value)

        if op in ['any', 'all']:
            if mask.DataType.endswith('8'):
                bits = 8
            elif mask.DataType.endswith('16'):
                bits = 16
            elif mask.DataType.endswith('32'):
                bits = 32
            else:
                bits = 64

            binaryReprOfValue = ''.join([str(int(value & 1 << i != 0)) for i in range(bits-1, -1, -1)])

            if op == 'any':
                return mask.DisplayName + ' & 0b' + binaryReprOfValue + ' != 0'
            return mask.DisplayName + ' & 0b' + binaryReprOfValue + ' == 0b' + binaryReprOfValue
        
        return mask.DisplayName + ' ' + op

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the requested property is PhysicalDimensions or
        # PhysicalDimensionsFlipped, return values indicating the dimensions
        # in the ideal order. The contained grid takes care of reordering, if
        # needed.

        if name == 'PhysicalDimensions':
            return self.Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self.Dimensions))

        # If the requested property is the UnscaledNoDataValue or
        # ScaledNoDataValue, determine the value we should return.

        if name == 'UnscaledNoDataValue':
            value = self._Grid.GetLazyPropertyValue(name)
            if value is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Using the UnscaledNoDataValue of the contained grid (%(value)s).'), {'class': self.__class__.__name__, 'id': id(self), 'value': repr(value)})
                return value
            
            if self._UnscaledNoDataValue is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Using the UnscaledNoDataValue supplied to the MaskedGrid constructor (%(value)s).'), {'class': self.__class__.__name__, 'id': id(self), 'value': repr(self._UnscaledNoDataValue)})
                return self._UnscaledNoDataValue

            value = self._GetNoDataValueForDataType(self.UnscaledDataType)
            self._LogDebug(_('%(class)s 0x%(id)016X: Using the default UnscaledNoDataValue (%(value)s) for UnscaledDataType %(dt)s. The contained grid does not have an UnscaledNoDataValue, nor was one supplied to the MaskedGrid constructor.'), {'class': self.__class__.__name__, 'id': id(self), 'value': repr(value), 'dt': self.UnscaledDataType})
            return value

        if name == 'ScaledNoDataValue':
            value = self._Grid.GetLazyPropertyValue(name)
            if value is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Using the ScaledNoDataValue of the contained grid (%(value)s).'), {'class': self.__class__.__name__, 'id': id(self), 'value': repr(value)})
                return value
            
            if self._ScaledNoDataValue is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Using the ScaledNoDataValue supplied to the MaskedGrid constructor (%(value)s).'), {'class': self.__class__.__name__, 'id': id(self), 'value': repr(self._ScaledNoDataValue)})
                return self._ScaledNoDataValue

            value = self._GetNoDataValueForDataType(self.DataType)
            if value is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Using the default ScaledNoDataValue (%(value)s) for DataType %(dt)s. The contained grid does not have an ScaledNoDataValue, nor was one supplied to the MaskedGrid constructor.'), {'class': self.__class__.__name__, 'id': id(self), 'value': repr(value), 'dt': self.DataType})
            return value

        # Otherwise just get the unaltered value from the contained
        # grid.

        return self._Grid.GetLazyPropertyValue(name)

    @classmethod
    def _GetNoDataValueForDataType(cls, dataType):
        if dataType == 'int8':
            return -128
        if dataType == 'uint8':
            return 255
        if dataType == 'int16':
            return -32768
        if dataType == 'uint16':
            return 65535
        if dataType == 'int32':
            return -2147483647      # To improve compatibility with ArcGIS, we use -2147483647 rather than -2147483648
        if dataType == 'uint32':
            return 4294967295
        if dataType == 'int64':
            return 0 - 2**63 + 1    # Our best guess is that ArcGIS uses +1 here like it does with int32
        if dataType == 'uint64':
            return 2**64 - 1
        if dataType == 'float32':
            return -3.4028234663852886e+038         # This is the float64 representation of the float32 -3.40282347e+38
        if dataType == 'float64':
            return -1.7976931348623157e+308
        return None

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

        # If we have not yet validated the masks and computed the
        # offsets into them, do it now.

        if self._MaskOffsets is None:
            self._ValidateMasksAndSetOffsets()

        # Get the unscaled data from the contained grid.

        data = self._Grid.UnscaledData.__getitem__(tuple(sliceList))

        # Apply each of the masks.

        for i in range(len(self._Masks)):
            if self._Operators[i] in ['=', '==', '!=', '<>', '<', '<=', '>', '>', 'any', 'all']:
                self._LogDebug(_('%(class)s 0x%(id)016X: Masking %(dn2)s where %(dn1)s %(op)s %(value)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn2': self._Grid.DisplayName, 'dn1': self._Masks[i].DisplayName, 'op': self._Operators[i], 'value': self._Values[i]})
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: Masking %(dn2)s where %(dn1)s %(op)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn2': self._Grid.DisplayName, 'dn1': self._Masks[i].DisplayName, 'op': self._Operators[i]})

            # Create a list of slices for retrieving the mask.

            maskSliceList = []
            for d in range(len(self.Dimensions)):
                if self.Dimensions[d] in self._Masks[i].Dimensions:
                    offset = self._MaskOffsets[i][self._Masks[i].Dimensions.index(self.Dimensions[d])]
                    maskSliceList.append(slice(sliceList[d].start + offset, sliceList[d].stop + offset))

            # Get the mask.

            maskData = self._Masks[i].Data.__getitem__(tuple(maskSliceList))

            # Perform the requested test on the mask.

            import numpy

            if self._Operators[i] in ['=', '==']:
                maskResult = Grid.numpy_equal_nan(maskData, self._Values[i])
            elif self._Operators[i] in ['!=', '<>']:
                maskResult = numpy.logical_not(Grid.numpy_equal_nan(maskData, self._Values[i]))
            elif self._Operators[i] == '<':
                maskResult = maskData < self._Values[i]
            elif self._Operators[i] == '<=':
                maskResult = maskData <= self._Values[i]
            elif self._Operators[i] == '>':
                maskResult = maskData > self._Values[i]
            elif self._Operators[i] == '>=':
                maskResult = maskData >= self._Values[i]
            elif self._Operators[i] == 'any':
                maskResult = maskData & self._Values[i] != 0
            elif self._Operators[i] == 'all':
                maskResult = maskData & self._Values[i] == self._Values[i]
            else:
                raise ValueError(_('Unknown mask operator "%(op)s".') % {'op': self._Operators[i]})
            
            # Set all cells where the test is True to
            # self.UnscaledNoDataValue. Handle the cases where the mask has
            # fewer dimensions than the data (for example, when a land mask
            # with dimensions yx is used to mask a time series of satellite
            # images with dimensions tyx).

            if self.Dimensions == self._Masks[i].Dimensions:
                data[maskResult] = self.UnscaledNoDataValue
            elif self.Dimensions in ['zyx', 'tyx'] and self._Masks[i].Dimensions == 'yx' or self.Dimensions == 'tzyx' and self._Masks[i].Dimensions == 'zyx':
                data[:, maskResult] = self.UnscaledNoDataValue
            elif self.Dimensions == 'tzyx' and self._Masks[i].Dimensions == 'tyx':
                data.transpose((1,0,2,3))[:, maskResult] = self.UnscaledNoDataValue
            else:       # self.Dimensions must be 'tzyx' and self._Masks[i].Dimensions must be 'yx'
                data[:, :, maskResult] = self.UnscaledNoDataValue

        # Return the data and self.UnscaledNoDataValue.

        return data, self.UnscaledNoDataValue

    def _ValidateMasksAndSetOffsets(self):
        maskOffsets = []
        
        for mask in self._Masks:

            # Validate that the mask dimensions are a subset of the contained
            # grid's dimensions.
            
            if len(self.Dimensions) < len(mask.Dimensions) or not (mask.Dimensions in ['yx', 'tzyx'] or mask.Dimensions == 'zyx' and self.Dimensions in ['zyx', 'tzyx'] or mask.Dimensions == 'tyx' and self.Dimensions in ['tyx', 'tzyx']):
                raise ValueError(_('%(dn1)s has dimensions (%(dim1)s) that are incompatible with the dimensions of %(dn2)s (%(dim2)s), so it cannot be used as a mask.') % {'dn1': mask.DisplayName, 'dn2': self._Grid.DisplayName, 'dim1': mask.Dimensions, 'dim2': self._Grid.Dimensions})

            # Validate that the mask uses the same coordinate system as the
            # contained grid.

            if not (self.GetSpatialReference('obj') is None and mask.GetSpatialReference('obj') is None) and \
               not (self.GetSpatialReference('obj') is not None and mask.GetSpatialReference('obj') is not None and self.GetSpatialReference('obj').IsSame(mask.GetSpatialReference('obj'))):
                raise ValueError(_('%(dn1)s has a different coordinate system than %(dn2)s, so it cannot be used as a mask.') % {'dn1': mask.DisplayName, 'dn2': self._Grid.DisplayName})

            # If the contained grid has any dimensions for which the
            # coordinates depend on the coordinates of other dimensions (e.g.
            # the value of z depends on t, y, and x, as is the case with
            # certain ROMS datasets), then we require that the shape of the
            # mask exactly match that of the contained grid (for the mask's
            # dimensions). We do not verify the coordinates of the mask as
            # this could be a very time consuming operation.

            if self.CoordDependencies != tuple([None] * len(self.Dimensions)):
                for i in range(len(mask.Dimensions)):
                    if mask.Shape[i] != self.Shape[self.Dimensions.index(mask.Dimensions[i])]:
                        raise ValueError(_('Because %(dn2)s has dimensions for which the coordinates depend on other dimensions, the MaskedGrid class can only apply masks that have dimensions with the same length as it. %(dn1)s cannot be used as a mask because the %(dim)s dimension has a different length (the mask has length %(len1)i but the grid has length %(len2)i).') % {'dn1': mask.DisplayName, 'dn2': self._Grid.DisplayName, 'dim': mask.Dimensions[i], 'len1': mask.Shape[i], 'len2': self.Shape[self.Dimensions.index[mask.Dimensions[i]]]})
                    
                maskOffsets.append([0] * len(mask.Dimensions))

            # Otherwise (there are no coordinate dependencies), verify that
            # the mask encloses the grid and has the same coordinates.

            else:
                import numpy

                offsets = []
                
                for i in range(len(mask.Dimensions)):
                    if mask.Dimensions[i] != 't':
                        gridCoords = numpy.asarray(self.CenterCoords[mask.Dimensions[i]], dtype='float64')
                        maskCoords = numpy.asarray(mask.CenterCoords[mask.Dimensions[i]], dtype='float64')

                        if mask.CoordIncrements[i] is not None:
                            absTol = mask.CoordIncrements[i]*self._Tolerance
                        else:
                            absTol = (maskCoords[-1] - maskCoords[0]) / mask.Shape[i] * self._Tolerance

                        if gridCoords[0] < maskCoords[0] - absTol or gridCoords[-1] > maskCoords[-1] + absTol:
                            self._LogInfo(_('In the %(dim)s dimension, the cell center coordinates %(dn1)s range from %(min)r to %(max)r.') % {'dim': mask.Dimensions[i], 'dn1': mask.DisplayName, 'min': maskCoords[0], 'max': maskCoords[-1]})
                            self._LogInfo(_('In the %(dim)s dimension, the cell center coordinates %(dn2)s range from %(min)r to %(max)r.') % {'dim': mask.Dimensions[i], 'dn2': self._Grid.DisplayName, 'min': gridCoords[0], 'max': gridCoords[-1]})
                            raise ValueError(_('%(dn1)s does not completely enclose %(dn2)s within the requested tolerance of %(tol)g of a grid cell, so it cannot be used as a mask.') % {'dn1': mask.DisplayName, 'dn2': self._Grid.DisplayName, 'tol': self._Tolerance})

                        offset = maskCoords.searchsorted(gridCoords[0] - absTol)
                        self._LogDebug(_('%(class)s 0x%(id)016X: Dimension %(dim)s: maskCoords[0] = %(m0)r, gridCoords[0] = %(g0)r, absTol = %(absTol)r, len(maskCoords) = %(lmc)s, offset = %(offset)s, len(gridCoords) = %(lgc)s'), {'class': self.__class__.__name__, 'id': id(self), 'dim': mask.Dimensions[i], 'm0': maskCoords[0], 'g0': gridCoords[0], 'absTol': absTol, 'lmc': len(maskCoords), 'offset': offset, 'lgc': len(gridCoords)})
                        try:
                            if len(maskCoords) - offset < len(gridCoords):
                                raise ValueError

                            if (numpy.abs(maskCoords[offset:offset+len(gridCoords)] - gridCoords) > absTol).any():
                                raise ValueError
                        except:
                            raise ValueError(_('The %(dim)s coordinates of %(dn1)s do not line up with the %(dim)s coordinates of %(dn2)s within the requested tolerance of %(tol)g of a grid cell, so it cannot be used as a mask.') % {'dn1': mask.DisplayName, 'dn2': self._Grid.DisplayName, 'dim': mask.Dimensions[i], 'tol': self._Tolerance})

                    else:
                        gridCoords = self.CenterCoords[mask.Dimensions[i]]
                        maskCoords = mask.CenterCoords[mask.Dimensions[i]]

                        if gridCoords[0] < maskCoords[0] or gridCoords[-1] > maskCoords[-1]:
                            self._LogInfo(_('In the %(dim)s dimension, the cell center coordinates %(dn1)s range from %(min)r to %(max)r.') % {'dim': mask.Dimensions[i], 'dn1': mask.DisplayName, 'min': maskCoords[0], 'max': maskCoords[-1]})
                            self._LogInfo(_('In the %(dim)s dimension, the cell center coordinates %(dn2)s range from %(min)r to %(max)r.') % {'dim': mask.Dimensions[i], 'dn2': self._Grid.DisplayName, 'min': gridCoords[0], 'max': gridCoords[-1]})
                            raise ValueError(_('%(dn1)s does not completely enclose %(dn2)s so it cannot be used as a mask.') % {'dn1': mask.DisplayName, 'dn2': self._Grid.DisplayName})
                    
                        offset = maskCoords.searchsorted(gridCoords[0])
                        self._LogDebug(_('%(class)s 0x%(id)016X: Dimension %(dim)s: len(maskCoords) = %(lmc)s, offset = %(offset)s, len(gridCoords) = %(lgc)s'), {'class': self.__class__.__name__, 'id': id(self), 'dim': mask.Dimensions[i], 'lmc': len(maskCoords), 'offset': offset, 'lgc': len(gridCoords)})
                        try:
                            if len(maskCoords) - offset < len(gridCoords):
                                self._LogDebug(_('%(class)s 0x%(id)016X: len(maskCoords) - offset Dimension %(dim)s offset: %(offset)r'), {'class': self.__class__.__name__, 'id': id(self), 'dim': mask.Dimensions[i], 'offset': offset})
                                raise ValueError

                            if (maskCoords[offset:offset+len(gridCoords)] != gridCoords).any():
                                raise ValueError
                        except:
                            raise ValueError(_('The %(dim)s coordinates of %(dn1)s do not line up with the %(dim)s coordinates of %(dn2)s, so it cannot be used as a mask.') % {'dn1': mask.DisplayName, 'dn2': self._Grid.DisplayName, 'dim': mask.Dimensions[i]})

                    offsets.append(offset)

                maskOffsets.append(offsets)

        self._MaskOffsets = maskOffsets


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
