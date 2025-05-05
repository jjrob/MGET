# _BlockStatisticGrid.py - A Grid that computes a block statistic for another
# Grid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import bisect
import calendar
import datetime
import math
import warnings

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Types import UnicodeStringTypeMetadata

from .. import Grid, QueryableAttribute


class BlockStatisticGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, statistic, xySize=None, zSize=None, tSize=None, tUnit=None, tStart=None, tSemiRegularity=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if grid.CoordIncrements[-1] is None:
            raise ValueError(_('%(dn)s does not have a constant x increment. It must have a constant x increment for a block statistic to be computed.') % {'dn': grid.DisplayName})

        if grid.CoordIncrements[-2] is None:
            raise ValueError(_('%(dn)s does not have a constant y increment. It must have a constant y increment for a block statistic to be computed.') % {'dn': grid.DisplayName})

        if 'z' not in grid.Dimensions and zSize is not None:
            raise ValueError(_('zSize was given but %(dn)s has no z dimension. zSize must be omitted if the input grid does not have a z dimension.') % {'dn': grid.DisplayName})

        if zSize is not None and grid.CoordIncrements[-3] is None:
            raise ValueError(_('zSize was given but %(dn)s does not have a constant z increment. It must have a constant z increment for a block statistic to be computed in the z direction.') % {'dn': grid.DisplayName})

        if 't' not in grid.Dimensions:
            if tSize is not None:
                raise ValueError(_('tSize was given but %(dn)s has no t dimension. tSize must be omitted if the input grid does not have a t dimension.') % {'dn': grid.DisplayName})
            if tUnit is not None:
                raise ValueError(_('tUnit was given but %(dn)s has no t dimension. tUnit must be omitted if the input grid does not have a t dimension.') % {'dn': grid.DisplayName})

        if tSize is not None and tUnit is None or tSize is None and tUnit is not None:
            raise ValueError(_('Either both tSize and tUnit must be given or neither must be given.'))

        if tSize is not None:
            if grid.TIncrementUnit == 'minute' and tUnit in ['second']:
                raise ValueError(_('tUnit is %(tu)s but the input grid\'s TIncrementUnit is %(tiu)s. The tUnit must be the same as TIncrementUnit or a coarser unit, i.e. minute, hour, day, month, or year.') % {'tu': tUnit, 'tiu': grid.TIncrementUnit})
            if grid.TIncrementUnit == 'hour' and tUnit in ['second', 'minute']:
                raise ValueError(_('tUnit is %(tu)s but the input grid\'s TIncrementUnit is %(tiu)s. The tUnit must be the same as TIncrementUnit or a coarser unit, i.e. hour, day, month, or year.') % {'tu': tUnit, 'tiu': grid.TIncrementUnit})
            if grid.TIncrementUnit == 'day' and tUnit in ['second', 'minute', 'hour']:
                raise ValueError(_('tUnit is %(tu)s but the input grid\'s TIncrementUnit is %(tiu)s. The tUnit must be the same as TIncrementUnit or a coarser unit, i.e. day, month, or year.') % {'tu': tUnit, 'tiu': grid.TIncrementUnit})
            if grid.TIncrementUnit == 'month' and tUnit in ['second', 'minute', 'hour', 'day']:
                raise ValueError(_('tUnit is %(tu)s but the input grid\'s TIncrementUnit is %(tiu)s. The tUnit must be the same as TIncrementUnit or a coarser unit, i.e. month, or year.') % {'tu': tUnit, 'tiu': grid.TIncrementUnit})
            if grid.TIncrementUnit == 'year' and tUnit in ['second', 'minute', 'hour', 'day', 'month']:
                raise ValueError(_('tUnit is %(tu)s but the input grid\'s TIncrementUnit is %(tiu)s. The tUnit must be year when TIncrementUnit is year.') % {'tu': tUnit, 'tiu': grid.TIncrementUnit})

            # Note: the following safety checks of tSize and tUnit against
            # grid.CoordIncrements[0] and grid.TIncrementUnit do not cover
            # every possible situation.

            if tUnit == grid.TIncrementUnit and tSize < grid.CoordIncrements[0]:
                raise ValueError(_('In the t direction, the requested block size was %(tSize)s %(tUnit)s, but the input grid\'s t increment was %(ci)s %(tiu)s. The block size must be greater than or equal to the grid\'s t increment.') % {'tSize': tSize, 'tUnit': tUnit, 'ci': grid.CoordIncrements[0], 'tiu': grid.TIncrementUnit})

            elif tUnit in ['second', 'minute', 'hour', 'day']:
                tSizeInSeconds = self._GetSeconds(tSize, tUnit)
                tIncrementInSeconds = self._GetSeconds(grid.CoordIncrements[0], grid.TIncrementUnit)
                if tSizeInSeconds < tIncrementInSeconds:
                    raise ValueError(_('In the t direction, the requested block size was %(tSize)s %(tUnit)s, but the input grid\'s t increment was %(ci)s %(tiu)s. The block size must be greater than or equal to the grid\'s t increment.') % {'tSize': tSize, 'tUnit': tUnit, 'ci': grid.CoordIncrements[0], 'tiu': grid.TIncrementUnit})
                if tSizeInSeconds > 60 * 60 * 24 * 365:
                    raise ValueError(_('In the t direction, the requested block size was %(tSize)s %(tUnit)s. This exceeds 365 days, which is not allowed. For blocks that exceed 365 days, please switch tUnit to \'month\' or \'year\'.') % {'tSize': tSize, 'tUnit': tUnit})

            elif tUnit == 'month':
                if grid.TIncrementUnit == 'month':
                    if tSize < grid.CoordIncrements[0]:
                        raise ValueError(_('In the t direction, the requested block size was %(tSize)s %(tUnit)s, but the input grid\'s t increment was %(ci)s %(tiu)s. The block size must be greater than or equal to the grid\'s t increment.') % {'tSize': tSize, 'tUnit': tUnit, 'ci': grid.CoordIncrements[0], 'tiu': grid.TIncrementUnit})
                else:
                    tSizeInSeconds = tSize * 60 * 60 * 24 * 30
                    tIncrementInSeconds = self._GetSeconds(grid.CoordIncrements[0], grid.TIncrementUnit)
                    if tSizeInSeconds < tIncrementInSeconds:
                        raise ValueError(_('In the t direction, the requested block size was %(tSize)s %(tUnit)s, but the input grid\'s t increment was %(ci)s %(tiu)s. The block size must be greater than or equal to the grid\'s t increment.') % {'tSize': tSize, 'tUnit': tUnit, 'ci': grid.CoordIncrements[0], 'tiu': grid.TIncrementUnit})

            elif tUnit == 'year':
                if grid.TIncrementUnit == 'month':
                    tSizeInMonths = tSize * 12
                    if tSizeInMonths < grid.CoordIncrements[0]:
                        raise ValueError(_('In the t direction, the requested block size was %(tSize)s %(tUnit)s, but the input grid\'s t increment was %(ci)s %(tiu)s. The block size must be greater than or equal to the grid\'s t increment.') % {'tSize': tSize, 'tUnit': tUnit, 'ci': grid.CoordIncrements[0], 'tiu': grid.TIncrementUnit})
                else:
                    tSizeInSeconds = tSize * 60 * 60 * 24 * 365
                    tIncrementInSeconds = self._GetSeconds(grid.CoordIncrements[0], grid.TIncrementUnit)
                    if tSizeInSeconds < tIncrementInSeconds:
                        raise ValueError(_('In the t direction, the requested block size was %(tSize)s %(tUnit)s, but the input grid\'s t increment was %(ci)s %(tiu)s. The block size must be greater than or equal to the grid\'s t increment.') % {'tSize': tSize, 'tUnit': tUnit, 'ci': grid.CoordIncrements[0], 'tiu': grid.TIncrementUnit})

            if tUnit not in ['second', 'minute', 'hour', 'day']:
                tSemiRegularity = None                              # Grid._GetTCoordsList() only supports semiregularity for second, minute, hour, or day

            else:
                tSizeInSeconds = self._GetSeconds(tSize, tUnit)
                if tSizeInSeconds <= 86400 and 86400 % tSizeInSeconds == 0:    # If one day is evenly divisible by tSizeInSeconds, semiregularity is not necessary
                    tSemiRegularity = None

            if tStart is not None and tSemiRegularity is not None and (tStart.month != 1 or tStart.day != 1 or tStart.hour != 0 or tStart.minute != 0 or tStart.second != 0 or tStart.microsecond != 0):
                raise ValueError(_('tStart is %(tStart)s and tSemiRegularity is %(tSemiRegularity)r. Either tStart must be midnight January 1 of some year, or tSemiRegularity must be :py:data:`None`.') % {'tStart': tStart, 'tSemiRegularity': tSemiRegularity})

            if tUnit == 'month' and tStart is not None and (tStart.day != 1 or tStart.hour != 0 or tStart.minute != 0 or tStart.second != 0 or tStart.microsecond != 0):
                raise ValueError(_('tUnit is "month" but tStart is %(tStart)s. When tUnit is "month", tStart must start on midnight of the first day a month.') % {'tStart': tStart})

        if xySize is None and zSize is None and tSize is None:
            self._LogWarning(_('Neither xySize, nor zSize, nor tSize was provided. No summarization of %(dn)s will be performed, and its values will be returned unchanged.') % {'dn': grid.DisplayName})
        
        # Initialize our properties.
        
        self._Grid = grid
        self._Statistic = statistic
        self._XYSize = xySize
        self._ZSize = zSize
        self._TSize = tSize
        self._TUnit = tUnit
        self._TStart = tStart
        self._TSemiRegularity = tSemiRegularity
        self._CachedSlice = None
        self._CachedSliceIndices = None

        blockShape = []
        if xySize is not None:
            blockShape.extend([str(xySize), str(xySize)])
        if zSize is not None:
            blockShape.append(str(zSize))
        if tSize is not None:
            blockShape.append(str(tSize) + ' ' + tUnit)

        self._DisplayName = _('%(blockShape)s block %(stat)s of %(dn)s') % {'blockShape': ' x '.join(blockShape), 'stat': statistic, 'dn': grid.DisplayName}

        self._LogDebug(_('%(class)s 0x%(id)016X: Instantiated with displayName = %(dn)s.') % {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
        self._LogDebug(_('%(class)s 0x%(id)016X: xySize=%(xySize)s, zSize=%(zSize)s, tSize=%(tSize)s, tUnit=%(tUnit)s, tStart=%(tStart)s, tSemiRegularity=%(tSemiRegularity)s') % {'class': self.__class__.__name__, 'id': id(self), 'xySize': xySize, 'zSize': zSize, 'tSize': tSize, 'tUnit': tUnit, 'tStart': tStart, 'tSemiRegularity': tSemiRegularity})

        # Create the queryable attributes reflecting our parameters.

        qa = [QueryableAttribute('BlockSize', 'Block size', UnicodeStringTypeMetadata()),
              QueryableAttribute('Statistic', 'Statistic', UnicodeStringTypeMetadata())]

        qav = {'BlockSize': 'x'.join(blockShape).replace(' ',''),
               'Statistic': statistic}

        # Copy the queryable attributes of the grid.

        for qa2 in tuple(grid.GetAllQueryableAttributes()):
            if qa2.Name not in qav:
                qa.append(qa2)
                qav[qa2.Name] = grid.GetQueryableAttributeValue(qa2.Name)

        # Initialize the base class.

        super(BlockStatisticGrid, self).__init__(queryableAttributes=tuple(qa), queryableAttributeValues=qav)

    def _GetSeconds(self ,t, unit):
        if unit == 'second': 
            return t
        if unit == 'minute': 
            return t * 60
        if unit == 'hour': 
            return t * 60 * 60
        if unit == 'day': 
            return t * 60 * 60 * 24
        raise NotImplementedError('Unknown unit ' + unit)

    def _Close(self):
        # TODO
        super(BlockStatisticGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['setspatialreference']:
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return cls._Grid._TestCapability(capability)

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the caller requested PhysicalDimensions or
        # PhysicalDimensionsFlipped, return idealized values, as the
        # transposing and flipping is handled by the contained grid.

        if name == 'PhysicalDimensions':
            return self._Grid.Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self._Grid.Dimensions))

        # If the caller requested the UnscaledDataType or UnscaledNoDataValue,
        # calculate and return them.
        
        if name == 'UnscaledDataType':

            # For COUNT, return either int32, uint32, or int64, depending on
            # what we estimate the block shape to be.
            
            if self._Statistic == 'count':
                blockShape = []
                if self._XYSize is not None:
                    blockShape.extend([self._XYSize, self._XYSize])
                if self._ZSize is not None:
                    blockShape.append(self._ZSize)
                if self._TSize is not None:
                    blockShape.append(self._Grid.Shape[0] // max(self.Shape[0] - 3, 1))

                maxCount = math.prod(blockShape)

                if maxCount <= 2**31-1:
                    return 'int32'
                if maxCount <= 2**32-1:
                    return 'uint32'
                return 'int64'

            # For MIN and MAX, return the data type of the contained grid.

            if self._Statistic in ['minimum', 'maximum']:
                return self._Grid.DataType

            # For RANGE, return the data type of the contained grid, unless it
            # is a signed integer, in which case return the unsigned
            # equivalent.

            if self._Statistic == 'range':
                if self._Grid.DataType.startswith('i'):
                    return 'u' + self._Grid.DataType
                return self._Grid.DataType

            # For all others, return float64, unless the contained grid is
            # float32, in which case return float32.

            if self._Grid.DataType == 'float32':
                return 'float32'
            return 'float64'

        if name == 'UnscaledNoDataValue':

            # For COUNT, return 0.

            if self._Statistic == 'count':
                return 0

            # For MIN and MAX, return the NoData value of the contained grid.

            if self._Statistic in ['minimum', 'maximum']:
                return self._Grid.NoDataValue

            # For RANGE, return the NoData value of the contained grid, unless
            # it is a signed integer, in which case return maximum possible
            # value of the equivalent unsigned type.

            import numpy

            if self._Statistic == 'range':
                if self._Grid.DataType.startswith('i'):
                    return int(numpy.iinfo('u' + self._Grid.DataType).max)
                return self._Grid.NoDataValue

            # For all others, return the smallest representable floating point
            # number:
            #
            # >>> float(numpy.finfo('float32').min)
            # -3.4028234663852886e+038
            # >>> float(numpy.finfo('float64').min)
            # -1.7976931348623157e+308

            if self.DataType == 'float32':
                return float(numpy.finfo('float32').min)
            return float(numpy.finfo('float64').min)

        # If the caller requested one of the properties related to scaling,
        # return None.

        if name in ['ScaledDataType', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # Compute CoordIncrements from the contained grid's increments and the block size.

        if name == 'CoordIncrements':
            coordIncrements = []

            if self._TSize is not None:
                coordIncrements.append(self._TSize)
            elif 't' in self._Grid.Dimensions:
                coordIncrements.append(self._Grid.CoordIncrements[0])

            if self._ZSize is not None:
                coordIncrements.append(self._Grid.CoordIncrements[-3] * self._ZSize)
            elif 'z' in self._Grid.Dimensions:
                coordIncrements.append(self._Grid.CoordIncrements[-3])

            if self._XYSize is not None:
                coordIncrements.append(self._Grid.CoordIncrements[-2] * self._XYSize)
                coordIncrements.append(self._Grid.CoordIncrements[-1] * self._XYSize)
            else:
                coordIncrements.append(self._Grid.CoordIncrements[-2])
                coordIncrements.append(self._Grid.CoordIncrements[-1])

            self._LogDebug(_('%(class)s 0x%(id)016X: CoordIncrements = %(ci)r.') % {'class': self.__class__.__name__, 'id': id(self), 'ci': tuple(coordIncrements)})

            return(tuple(coordIncrements))

        # Compute Shape, CornerCoords, TSemiRegularity, and
        # TCountPerSemiRegularPeriod from the contained grid's properties and
        # the block size.

        if name in ['Shape', 'CornerCoords', 'TSemiRegularity', 'TCountPerSemiRegularPeriod']:

            # Start with the properties from the contained grid.

            shape = list(self._Grid.GetLazyPropertyValue('Shape', allowPhysicalValue=True))
            cornerCoords = list(self._Grid.GetLazyPropertyValue('CornerCoords', allowPhysicalValue=True))
            tSemiRegularity = self._Grid.GetLazyPropertyValue('TSemiRegularity', allowPhysicalValue=True)
            tCountPerSemiRegularPeriod = self._Grid.GetLazyPropertyValue('TCountPerSemiRegularPeriod', allowPhysicalValue=True)

            # If the caller specified xySize or zSize, adjust the shape and
            # cornerCoords for these dimensions.

            adjust = []

            if self._XYSize is not None:
                adjust.append(['x', -1, self._XYSize])
                adjust.append(['y', -2, self._XYSize])

            if self._ZSize is not None:
                adjust.append(['z', -3, self._ZSize])

            for dim, i, size in adjust:
                remainder = shape[i] % size
                shape[i] = shape[i] // size
                if remainder > 0:
                    shape[i] += 1

                cornerCoords[i] = self._Grid.MinCoords[dim, 0] + self._Grid.CoordIncrements[i] / 2 * size

            # If the caller specified tSize, compute the properties based on
            # tSize, tUnit, and the properties of the contained grid.

            if self._TSize is not None:

                # If the caller did not provide a tStart, set it to January 1
                # at 00:00:00 of the first year with data.

                tMin = self._Grid.MinCoords['t', 0]

                if self._TStart is None:
                    self._TStart = datetime.datetime(tMin.year, 1, 1)

                # Otherwise make sure that tStart occurs on or before the
                # minimum time coordinate of the contained grid.

                elif self._TStart > tMin:
                    raise ValueError(_('Cannot create a block summarization of %(dn)s that starts at %(tStart)s because that start time occurs after the grid starts at %(tMin)s. Please adjust tStart to occur on or before the grid start time.') % {'tStart': self._TStart, 'dn': self._Grid.DisplayName, 'tMin': tMin})

                # Count forward from tStart until we find the block that
                # includes tMin. The start time of that block is the t corner
                # coordinate. If we have t coordinate semiregularity, continue
                # to the end of the year so we can count the number of time
                # slices per semiregular period.

                if self._TUnit in ['second', 'minute', 'hour', 'day']:
                    tSizeInSeconds = self._GetSeconds(self._TSize, self._TUnit)

                t1 = None
                t2 = None
                tCornerCoord = None
                tCountPerSemiRegularPeriod = None

                while tCornerCoord is None or (self._TSemiRegularity == 'annual' and t1 is not None and t1.year <= tCornerCoord.year):
                    t1 = self._TStart if t1 is None else t2

                    if self._TUnit in ['second', 'minute', 'hour', 'day']:
                        t2 = t1 + datetime.timedelta(seconds=tSizeInSeconds)

                    elif self._TUnit == 'month':
                        t2 = datetime.datetime(t1.year, t1.month, 1)
                        for i in range(self._TSize):
                            if t2.month < 12:
                                t2 = datetime.datetime(t2.year, t2.month + 1, 1)
                            else:
                                t2 = datetime.datetime(t2.year + 1, 1, 1)

                    elif self._TUnit == 'year':
                        t2 = datetime.datetime(t1.year + self._TSize, t1.month, t1.day, t1.hour, t1.minute, t1.second, t1.microsecond)

                    else:
                        raise RuntimeError(_('Programming error in this tool: self._TUnit has the unexpected value %(tUnit)r. Please contact the MGET development team for assistance.') % {'tUnit': self._TUnit})

                    # If there is annual semiregularity, increment our count
                    # of time slices per semiregular period.

                    if self._TSemiRegularity == 'annual':
                        assert self._TUnit in ['second', 'minute', 'hour', 'day']
                        if t1.year == tMin.year:
                            tCountPerSemiRegularPeriod = 1 if tCountPerSemiRegularPeriod is None else tCountPerSemiRegularPeriod + 1

                        # If the t2 we computed above is in the next year,
                        # truncate it to midnight January 1.

                        if t2.year > t1.year:
                            t2 = datetime.datetime(t2.year, 1, 1)

                        # Otherwise, check whether there is less than 1.5
                        # blocks of time from t1 until the end of a 365 day
                        # year. If so, set t2 to midnight January 1 of the
                        # next year.

                        else:
                            t365 = t1 if not calendar.isleap(t1.year) else t1 + datetime.timedelta(days=1)
                            secondsLeft = (datetime.datetime(t365.year + 1, 1, 1) - t365).total_seconds()
                            if secondsLeft < tSizeInSeconds * 1.5:
                                t2 = datetime.datetime(t1.year + 1, 1, 1)

                    # If the first time slice of the caller's grid starts
                    # between t1 and t2, then t1 is when the first block
                    # should start.

                    if tMin >= t1 and tMin < t2:
                        assert tCornerCoord is None
                        tCornerCoord = t1

                # Set the t corner coordinate.

                cornerCoords[0] = tCornerCoord
                tSemiRegularity = self._TSemiRegularity

                # To determine the shape in the t direction, count forward
                # from the t corner coordinate until we capture the start time
                # of the final time slice of the caller's grid.

                tMinAtEnd = self._Grid.MinCoords['t', -1]
                tShape = 0
                t1 = tCornerCoord
                t2 = None

                while True:
                    tShape += 1

                    if self._TUnit in ['second', 'minute', 'hour', 'day']:
                        t2 = t1 + datetime.timedelta(seconds=tSizeInSeconds)

                    elif self._TUnit == 'month':
                        t2 = datetime.datetime(t1.year, t1.month, 1)
                        for i in range(self._TSize):
                            if t2.month < 12:
                                t2 = datetime.datetime(t2.year, t2.month + 1, 1)
                            else:
                                t2 = datetime.datetime(t2.year + 1, 1, 1)

                    elif self._TUnit == 'year':
                        t2 = datetime.datetime(t1.year + self._TSize, t1.month, t1.day, t1.hour, t1.minute, t1.second, t1.microsecond)

                    else:
                        raise RuntimeError(_('Programming error in this tool: self._TUnit has the unexpected value %(tUnit)r. Please contact the MGET development team for assistance.') % {'tUnit': self._TUnit})

                    if self._TSemiRegularity == 'annual':
                        if t2.year > t1.year:
                            t2 = datetime.datetime(t2.year, 1, 1)
                        else:
                            t365 = t1 if not calendar.isleap(t1.year) else t1 + datetime.timedelta(days=1)
                            secondsLeft = (datetime.datetime(t365.year + 1, 1, 1) - t365).total_seconds()
                            if secondsLeft < tSizeInSeconds * 1.5:
                                t2 = datetime.datetime(t1.year + 1, 1, 1)

                    if t2 > tMinAtEnd:
                        break

                    t1 = t2

                shape[0] = tShape

            # Set the properties we just computed.

            self.SetLazyPropertyValue('Shape', tuple(shape))
            self.SetLazyPropertyValue('CornerCoords', tuple(cornerCoords))
            self.SetLazyPropertyValue('TSemiRegularity', tSemiRegularity)
            self.SetLazyPropertyValue('TCountPerSemiRegularPeriod', tCountPerSemiRegularPeriod)

            self._LogDebug(_('%(class)s 0x%(id)016X: Shape=%(Shape)s, CornerCoords=%(CornerCoords)s, TSemiRegularity=%(TSemiRegularity)s, TCountPerSemiRegularPeriod=%(TCountPerSemiRegularPeriod)s') % {'class': self.__class__.__name__, 'id': id(self), 'Shape': shape, 'CornerCoords': cornerCoords, 'TSemiRegularity': tSemiRegularity, 'TCountPerSemiRegularPeriod': tCountPerSemiRegularPeriod})

            # Return the value the caller requested.

            return self.GetLazyPropertyValue(name)

        # For TIncrement and TIncrementUnit, return our properties if they're
        # not None, and for TCornerCoordType use min, otherwise fall through
        # and use the property from the contained grid.

        if name == 'TIncrement' and self._TSize is not None:
            return self._TSize

        if name == 'TIncrementUnit' and self._TUnit is not None:
            return self._TUnit

        if name == 'TCornerCoordType':
            if self._TSize is not None:
                return 'min'

        # We always return None for TOffsetFromParsedTime and False for
        # IgnoreLeapYear.

        if name == 'TOffsetFromParsedTime':
            return None

        if name == 'IgnoreLeapYear':
            return False

        # Otherwise use the value of the property from the contained grid.
        # This includes, minimally, SpatialReference and CoordDependencies.
        
        return self._Grid.GetLazyPropertyValue(name, allowPhysicalValue=True)

    def _ReadNumpyArray(self, sliceList):

        # There is no need or advantage to considering data outside the
        # caller's sliceList of interest. Therefore we do not need to compute
        # results beyond it or cache anything. If the caller is going to
        # retrieve the same data multiple times, they can wrap us with
        # MemoryCachedGrid, if desired.
        #
        # For our convenience, the base class (Grid) ensures that sliceList
        # contains a slice for every dimension, with non-negative integer
        # start and stop attributes that are in bounds, start <= stop, and
        # step == None.
        #
        # Each one of our cells always spans the same number of cells in the
        # x, y, and z directions of the grid we contain, but not necessarily
        # the same number of cells in the t direction. If we have a t
        # dimension, our strategy is to summarize one t slice at a time,
        # storing each summary slice in a list, which we then concatenate at
        # the end and return to the caller.
        #
        # So: first, if there is a t dimension, split the sliceList into a
        # list of slice lists to summarize, where the first element of each is
        # an integer index into our list of t coordinates. Otherwise, treat
        # the sliceList as the single slice we need to summarize.

        import numpy

        if 't' in self.Dimensions:
            slices = [[t] + sliceList[1:] for t in range(sliceList[0].start, sliceList[0].stop)]
            gridTMinCoords = self._Grid.MinCoords['t', :]    # Used below
        else:
            slices = [sliceList]

        # Summarize each slice.

        results = []

        for i, s in enumerate(slices):

            # Build a list of slices to read from the contained grid.

            sliceToRead = []    # Slices we will read from the contained grid.

            sliceReqMsg = []    # Strings for a log message saying which slices were requested
            coordsReqMsg = []   # Strings for a log message saying which coordinates were requested
            sliceReadMsg = []   # Strings for a log message saying which slices will be read from the contained grid
            coordsReadMsg = []  # Strings for a log message saying which coordinates will be read from the contained grid

            padWidth = []       # Cells of padding required for each dimension to make it evenly divisible by the block size for that dimension
            windowShape = []    # Size of the block window to be summarized, to be passed to numpy.lib.stride_tricks.sliding_window_view()

            for j, d in enumerate(self.Dimensions):

                # For the t dimension, each one of our t slices may not always
                # correspond to the same number of t slices of the contained
                # grid. Get the start and end times for our current t slice.
                # Then find the t indices of the contained grid of the slices
                # that start on or after our start time and before our end
                # time.

                if d == 't':
                    tStartDateTime = self.MinCoords['t', s[j]]
                    tStopDateTime = self.MaxCoords['t', s[j]]

                    tStart = bisect.bisect_left(gridTMinCoords, tStartDateTime)
                    if tStart >= len(gridTMinCoords):
                        raise RuntimeError('BlockStatisticGrid: Probable programming error in _ReadNumpyArray(): tStart >= len(gridTMinCoords). Please contact the MGET development team for assistance.')

                    tStop = bisect.bisect_left(gridTMinCoords, tStopDateTime)
                    if tStop <= 0:
                        raise RuntimeError('BlockStatisticGrid: Probable programming error in _ReadNumpyArray(): tStop <= 0. Please contact the MGET development team for assistance.')

                    sliceToRead.append(slice(tStart, tStop))

                    sliceReqMsg.append(f'{s[j]}')
                    coordsReqMsg.append(f'{tStartDateTime} : {tStopDateTime}')
                    sliceReadMsg.append(f'{tStart}:{tStop}')
                    coordsReadMsg.append(f'{self._Grid.MinCoords[d, tStart]} : {self._Grid.MaxCoords[d, tStop-1]}')

                    padWidth.append((0, 0))
                    windowShape.append(tStop - tStart)

                # For the dimensions other than t, multiply the requested
                # slice start and end by the block size for this dimension.
                # Limit the stop value to the Shape in this dimension, in case
                # the last block extends beyond the edge of the contained
                # grid. We'll pad it further below, prior to computing the
                # statistic.

                else:
                    blockSize = self._XYSize if d in ['x', 'y'] else self._ZSize
                    if blockSize is None:
                        blockSize = 1

                    start = s[j].start * blockSize
                    if start < 0 or start >= self._Grid.Shape[j]:
                        raise RuntimeError('BlockStatisticGrid: Probable programming error in _ReadNumpyArray(): start < 0 or start >= self._Grid.Shape[j]. Please contact the MGET development team for assistance.')

                    stop = min(s[j].stop * blockSize, self._Grid.Shape[j])

                    sliceToRead.append(slice(start, stop))

                    sliceReqMsg.append(f'{s[j].start}:{s[j].stop}')
                    coordsReqMsg.append(f'{self.MinCoords[d, s[j].start]} : {self.MaxCoords[d, s[j].stop-1]}')
                    sliceReadMsg.append(f'{start}:{stop}')
                    coordsReadMsg.append(f'{self._Grid.MinCoords[d, start]} : {self._Grid.MaxCoords[d, stop-1]}')

                    remainder = stop % blockSize
                    padWidth.append((0, blockSize - remainder if remainder > 0 else 0))
                    windowShape.append(blockSize)

            # Read the slice.

            self._LogDebug('%(class)s 0x%(id)016X: Request for slice [%(sliceReqMsg)s], coords [%(coordsReqMsg)s]' % {'class': self.__class__.__name__, 'id': id(self), 'sliceReqMsg': ', '.join(sliceReqMsg), 'coordsReqMsg': ', '.join(coordsReqMsg)})
            self._LogDebug('%(class)s 0x%(id)016X: Reading slice [%(sliceReadMsg)s], coords [%(coordsReadMsg)s]' % {'class': self.__class__.__name__, 'id': id(self), 'sliceReadMsg': ', '.join(sliceReadMsg), 'coordsReadMsg': ', '.join(coordsReadMsg)})
            self._LogDebug('%(class)s 0x%(id)016X: padWidth = %(padWidth)s' % {'class': self.__class__.__name__, 'id': id(self), 'padWidth': padWidth})

            data = self._Grid.Data.__getitem__(tuple(sliceToRead))

            # For the COUNT statistic, first determine which cells have data.
            # If the contained grid does not have a NoDataValue, all of them
            # will have data. Then pad any incomplete blocks with False.
            # Finally, make a numpy sliding_window_view() of our blocks and
            # summarize them with count_nonzero().

            from numpy.lib.stride_tricks import sliding_window_view

            steppedSlices = [slice(None, None, ws) for ws in windowShape] + [slice(None)]

            if self._Statistic == 'count':
                if self._Grid.NoDataValue is not None:
                    hasData = data != self._Grid.NoDataValue
                else:
                    hasData = numpy.ones(data.shape, dtype=bool)

                hasData = numpy.pad(hasData, padWidth, 'constant', constant_values=False)
                view = sliding_window_view(hasData, window_shape=windowShape).__getitem__(tuple(steppedSlices))
                axis = tuple(range(view.ndim)[-data.ndim:])
                results.append(numpy.count_nonzero(view, axis=axis).astype(self.DataType))

            # The logic for the MINIMUM and MAXIMUM statistics is essentially
            # the same, only varying by which extremum we want. Additionally,
            # we need to perform both computations in order to compute the
            # RANGE, so we execute this logic in a loop, which will only be
            # executed once for MINIMUM or MAXIMUM but twice for RANGE.

            for statistic in ['minimum', 'maximum']:
                if self._Statistic in [statistic, 'range']:

                    # First determine the appropriate extremum for the
                    # contained grid's data type. Then, if the grid has a
                    # NoDataValue, replace all cells that are NoData with that
                    # extremum. Then pad incomplete blocks with that extremum.
                    # Make a numpy sliding_window_view() of our blocks and
                    # summarize them with the appropriate numpy function.
                    # Finally, if the grid has a NoDataValue, replace any
                    # cells of the result that are the extremum with
                    # NoDataValue.

                    extremum = numpy.finfo(self._Grid.DataType) if self._Grid.DataType[0] == 'f' else numpy.iinfo(self._Grid.DataType)
                    extremum = extremum.max if statistic == 'minimum' else extremum.min

                    data2 = data.copy()     # Copy data because we'll do this loop twice when self._Statistic == 'range', and we'll need the original values again the second time

                    if self._Grid.NoDataValue is not None:
                        data2[self.numpy_equal_nan(data2, self._Grid.NoDataValue)] = extremum

                    data2 = numpy.pad(data2, padWidth, 'constant', constant_values=extremum)
                    view = sliding_window_view(data2, window_shape=windowShape).__getitem__(tuple(steppedSlices))
                    axis = tuple(range(view.ndim)[-data2.ndim:])
                    result = numpy.nanmin(view, axis=axis) if statistic == 'minimum' else numpy.nanmax(view, axis=axis)

                    if self._Grid.NoDataValue is not None:
                        result[self.numpy_equal_nan(result, extremum)] = self._Grid.NoDataValue

                    results.append(result)

            # For RANGE, we first computed the MINIMUM and MAXIMUM above and
            # appended these two result slices to the results list. First, pop
            # them from the results list and subtract the minimum from the
            # maximum, explicitly setting the dtype to our DataType and
            # allowing unsafe casting to handle integer overflows (e.g. when
            # self._Grid.DataType is int8, we set self.DataType to uint8, to
            # allow results like 125-(-125) = 250 to work). Then, if we have a
            # NoDataValue, set our result to NoDataValue wherever the original
            # results had NoDataValue. They'll both have it in the same place,
            # so it is sufficient to check just one of them.

            if self._Statistic == 'range':
                maxResult = results.pop(-1)
                minResult = results.pop(-1)
                result = numpy.subtract(maxResult, minResult, dtype=self.DataType, casting='unsafe')

                if self.NoDataValue is not None:
                    result[maxResult == self._Grid.NoDataValue] = self.NoDataValue

                results.append(result)

            # For the other statistics, we will always return a floating point
            # type. First, if the contained grid has a NoDataValue, determine
            # which cells have NoData. Then, if the original data uses an
            # integer type, cast it to the floating point type we will return.
            # Now that we have a floating point array, set the NoData cells to
            # NaN, then pad incomplete blocks with NaN. Make a numpy
            # sliding_window_view() of our blocks and summarize them with the
            # appropriate numpy NaN-compatible function. Finally, if the grid
            # has a NoDataValue, replace any NaNs in the result with that
            # NoDataValue.

            if self._Statistic in ['mean', 'median', 'standard_deviation', 'sum']:
                if self._Grid.NoDataValue is not None:
                    hasNoData = data == self._Grid.NoDataValue

                if numpy.issubdtype(data.dtype, numpy.integer):
                    data = data.astype(self.DataType)

                if self._Grid.NoDataValue is not None:
                    data[hasNoData] = numpy.nan

                data = numpy.pad(data, padWidth, 'constant', constant_values=numpy.nan)
                view = sliding_window_view(data, window_shape=windowShape).__getitem__(tuple(steppedSlices))
                axis = tuple(range(view.ndim)[-data.ndim:])

                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=RuntimeWarning)  # Ignore RuntimeWarning: Degrees of freedom <= 0 for slice.

                    if self._Statistic == 'mean':
                        result = numpy.nanmean(view, axis=axis)
                    elif self._Statistic == 'median':
                        result = numpy.nanmedian(view, axis=axis)
                    elif self._Statistic == 'standard_deviation':
                        result = numpy.nanstd(view, axis=axis, ddof=1)
                    else:
                        result = numpy.nansum(view, axis=axis)

                if self.NoDataValue is not None:
                    result[~numpy.isfinite(result)] = self.NoDataValue

                results.append(result)

        # Extract or stack the results, and return successfully.

        if 't' not in self.Dimensions:
            data = results[0]
        else:
            data = numpy.stack(results, axis=0)

            # Above, we summarized each block of time slices individually, so
            # each numpy array in results had a shape of (1, y, x) if there
            # was no z dimension or (1, z, y, x) if there was. Then, when we
            # stacked them immediately above, we ended up with shape (t, 1, z,
            # y, x) or (t, 1, y, x). Delete the extra dimension of length 1.

            if len(data.shape) != len(self.Dimensions) + 1 or data.shape[1] != 1:
                raise RuntimeError(_('Programming error in BlockStatisticGrid: len(data.shape) != len(self.Dimensions) + 1 or data.shape[1] != 1. Please contact the MGET development team for assistance.'))

            data = numpy.squeeze(data, axis=1)

        return data, self.NoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
