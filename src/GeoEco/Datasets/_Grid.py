# _Grid.py - Defines Grid, the base class for classes representing gridded
# datasets.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import bisect
import datetime
import math
import types
import weakref

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from ._Dataset import Dataset


class Grid(Dataset):
    __doc__ = DynamicDocString()

    # Public properties and instance methods

    def _GetDimensions(self):
        return self.GetLazyPropertyValue('Dimensions')

    Dimensions = property(_GetDimensions, doc=DynamicDocString())

    def _GetShape(self):
        return self.GetLazyPropertyValue('Shape')

    Shape = property(_GetShape, doc=DynamicDocString())

    def _GetCoordDependencies(self):
        return self.GetLazyPropertyValue('CoordDependencies')

    CoordDependencies = property(_GetCoordDependencies, doc=DynamicDocString())

    def _GetCoordIncrements(self):
        return self.GetLazyPropertyValue('CoordIncrements')

    CoordIncrements = property(_GetCoordIncrements, doc=DynamicDocString())

    def _GetTIncrementUnit(self):
        return self.GetLazyPropertyValue('TIncrementUnit')
    
    TIncrementUnit = property(_GetTIncrementUnit, doc=DynamicDocString())

    def _GetTSemiRegularity(self):
        return self.GetLazyPropertyValue('TSemiRegularity')
    
    TSemiRegularity = property(_GetTSemiRegularity, doc=DynamicDocString())

    def _GetTCountPerSemiRegularPeriod(self):
        return self.GetLazyPropertyValue('TCountPerSemiRegularPeriod')
    
    TCountPerSemiRegularPeriod = property(_GetTCountPerSemiRegularPeriod, doc=DynamicDocString())

    def _GetMinCoords(self):
        return self._MinCoords

    MinCoords = property(_GetMinCoords, doc=DynamicDocString())

    def _GetCenterCoords(self):
        return self._CenterCoords

    CenterCoords = property(_GetCenterCoords, doc=DynamicDocString())

    def _GetMaxCoords(self):
        return self._MaxCoords

    MaxCoords = property(_GetMaxCoords, doc=DynamicDocString())

    def _GetDataType(self):
        if self.DataIsScaled:
            return self.GetLazyPropertyValue('ScaledDataType')
        return self.UnscaledDataType
    
    DataType = property(_GetDataType, doc=DynamicDocString())

    def _GetNoDataValue(self):
        if self.DataIsScaled:
            return self.GetLazyPropertyValue('ScaledNoDataValue')
        return self.UnscaledNoDataValue
    
    NoDataValue = property(_GetNoDataValue, doc=DynamicDocString())

    def _GetData(self):
        if self.DataIsScaled:
            return self._ScaledData
        return self._UnscaledData

    Data = property(_GetData, doc=DynamicDocString())

    def _GetDataIsScaled(self):
        return self.GetLazyPropertyValue('ScalingFunction') is not None

    DataIsScaled = property(_GetDataIsScaled, doc=DynamicDocString())

    def _GetUnscaledDataType(self):
        return self.GetLazyPropertyValue('UnscaledDataType')
    
    UnscaledDataType = property(_GetUnscaledDataType, doc=DynamicDocString())

    def _GetUnscaledNoDataValue(self):
        return self.GetLazyPropertyValue('UnscaledNoDataValue')
    
    UnscaledNoDataValue = property(_GetUnscaledNoDataValue, doc=DynamicDocString())

    def _GetUnscaledData(self):
        return self._UnscaledData

    UnscaledData = property(_GetUnscaledData, doc=DynamicDocString())

    @staticmethod
    def numpy_equal_nan(a, b):
        import numpy
        if a is None or b is None:    # Do not check for nan if either is None. numpy.isnan(None) fails with TypeError.
            return a == b
        return (a == b) | (numpy.isnan(a) & numpy.isnan(b))

    def GetIndicesForCoords(self, coords):

        # Validate the coordinates.

        if len(coords) != len(self.Dimensions):
            raise ValueError(_('%(dn)s has %(dim)i dimensions but %(coords)i coordinates were provided.') % {'dn': self.DisplayName, 'dim': len(self.Dimensions), 'coords': len(coords)})

        if self.Dimensions[0] == 't':
            if not isinstance(coords[0], (datetime.date, datetime.datetime)):
                raise TypeError(_('coords[0] is an instance of %(t1)s. It must be an instance of %(t2)s or %(t3)s') % {'t1': str(type(coords[0])), 't2': str(datetime.date), 't3': str(datetime.datetime)})
            numericIndicesStart = 1
        else:
            numericIndicesStart = 0

        for i in range(numericIndicesStart, len(coords)):
            if not isinstance(coords[i], (int, float)):
                raise TypeError(_('coords[%(i)i] is an instance of %(t1)s. It must be an instance of %(t2)s, or %(t3)s.') % {'i': i, 't1': str(type(coords[i])), 't2': str(int), 't3': str(float)})

        # First get the indices for dimensions that do not depend on
        # any others.

        indices = [None] * len(coords)
        done = [False] * len(coords)

        for i, d in enumerate(self.Dimensions):
            if self.CoordDependencies[i] is None:
                coord = coords[i]

                # If this dimension is x and the grid uses a
                # geographic projection handle the "0 to 360 vs.
                # -180 to 180" problem.

                if d == 'x':
                    isGeographic = self.GetLazyPropertyValue('IsGeographic')
                    if isGeographic is None:
                        sr = self.GetSpatialReference('obj')
                        isGeographic = sr is not None and sr.IsGeographic()
                        self.SetLazyPropertyValue('IsGeographic', isGeographic)

                    if isGeographic:
                        coord = coord - (coord // 360) * 360        # Convert the requested x coordinate to 0 to 360, regardless of what it currently is

                        # If coord is less than the min x extent, add 360
                        # until it is greater than or equal it, to handle
                        # coordinate systems such as NOAA OSCAR, which uses a
                        # 20 to 380 system.

                        if coord < self.MinCoords[d, 0]:
                            while coord < self.MinCoords[d, 0]:
                                coord += 360.

                        # Otherwise, if it is greater than or equal to the max
                        # x extent, subtract 360 until it is less than it, to
                        # handle coordinate systems such as MODIS L3 which
                        # uses a -180 to 180 system.

                        elif coord >= self.MaxCoords[d, -1]:
                            while coord >= self.MaxCoords[d, -1]:
                                coord -= 360.

                # If this dimension is x, y, or z and has a constant
                # increment, calculate the index directly.
                
                increment = self.CoordIncrements[i]
                if d in 'xyz' and increment is not None:
                    index = int(math.floor((coord - (self.GetLazyPropertyValue('CornerCoords')[i] - increment/2.)) / increment))
                    if index >= 0 and index <= self.Shape[i] - 1:
                        indices[i] = index

                # Otherwise (this dimension is t or does not have a
                # constant increment), find the index from the full
                # list of indices using a binary search.
                
                else:
                    index = bisect.bisect_right(self.MaxCoords[d], coord)
                    if index > 0 and index <= self.Shape[i] - 1 or index == 0 and coord >= self.MinCoords[d, 0]:
                        indices[i] = index
                        
                done[i] = True

        # Now get the indices for dimensions that do depend on others.

        if False in done:
            i = 0
            while i < len(self.Dimensions):
                if not done[i] and self.CoordDependencies[i] is not None and all([done[self.Dimensions.index(d)] for d in self.CoordDependencies[i]]):
                    maxCoordsKey = [self.Dimensions[i]]
                    minCoordKey = [self.Dimensions[i]]
                    for j in range(len(self.Dimensions)):
                        if self.Dimensions[j] == self.Dimensions[i]:
                            maxCoordsKey.append(slice(None))
                            minCoordKey.append(0)
                        elif self.Dimensions[j] in self.CoordDependencies[i]:
                            maxCoordsKey.append(indices[j])
                            minCoordKey.append(indices[j])

                    if None not in maxCoordsKey and None not in minCoordKey:
                        index = bisect.bisect_right(self.MaxCoords.__getitem__(tuple(maxCoordsKey)), coords[i])
                        if index > 0 and index < self.Shape[i] or index == 0 and coords[i] >= self.MinCoords.__getitem__(tuple(minCoordKey)):
                            indices[i] = index
                    
                    done[i] = True
                    i = 0

                else:
                    i += 1

        # Return successfully.

        return indices

    # Private base class constructor. Do not invoke directly; use a
    # derived class instead. If you override, be sure to call it from
    # your derived class's __init__.

    def __init__(self, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None):

        # Initialize the base class. Because the base class declared all of
        # them and will validate all of them, we skip validating them ourself,
        # so as not to duplicate effort.

        super(Grid, self).__init__(parentCollection, queryableAttributes, queryableAttributeValues, lazyPropertyValues)

        # But we do need to initialize our dependencies, though.
            
        for d in Grid.__init__.__doc__.Obj.Dependencies:
            d.Initialize()

        # Set various attributes that implement __getitem__.

        self._CachedGridCoords = {}

        self._MinCoords = _ContainerEmulator(self, '_GetMinCoords')
        self._CenterCoords = _ContainerEmulator(self, '_GetCenterCoords')
        self._MaxCoords = _ContainerEmulator(self, '_GetMaxCoords')
        self._ScaledData = _ContainerEmulator(self, '_GetScaledDataAsArray', '_SetScaledDataWithArray')
        self._UnscaledData = _ContainerEmulator(self, '_GetUnscaledDataAsArray', '_SetUnscaledDataWithArray')

    # Private methods that the derived class generally does not
    # override.

    def _GetMinCoords(self, key):
        return self._GetCoordsForOffset(key, -0.5)

    def _GetCenterCoords(self, key):
        return self._GetCoordsForOffset(key, 0.0)

    def _GetMaxCoords(self, key):
        return self._GetCoordsForOffset(key, 0.5)

    def _GetCoordsForOffset(self, key, fixedIncrementOffset):

        # Validate the key.

        coord, coordNum, slices, sliceDims = self._GetSlicesForCoordsKey(key)

        # If the caller is asking for a coordinate that does not have
        # a fixed increment, forward the call to the derived class.

        if self.CoordIncrements[coordNum] is None:
            return self._GetCoords(coord, coordNum, slices, sliceDims, fixedIncrementOffset)

        # The coordinate has a fixed increment. First check whether we
        # previously calculated and cached the full list of coordinates. If
        # not, do it now.

        import numpy

        if coord in 'xyz':

            # For x, y, and z, use numpy.linspace to calculate them, rather
            # than numpy.arange. Ensure the minimum coordinate of each cell is
            # exactly the same as the maximum coordinate of the next cell.

            if coord not in self._CachedGridCoords:
                self._CachedGridCoords[coord] = {}
                cornerCoord = self.GetLazyPropertyValue('CornerCoords')[coordNum]     # Always the center of the corner cell
                oneExtraCenterCoords = numpy.linspace(start=cornerCoord,
                                                      stop=cornerCoord + self.CoordIncrements[coordNum] * (self.Shape[coordNum]),
                                                      num=self.Shape[coordNum]+1)

                self._CachedGridCoords[coord][0.] = oneExtraCenterCoords[:-1]
                self._CachedGridCoords[coord][-0.5] = oneExtraCenterCoords[:-1] - 0.5 * self.CoordIncrements[coordNum]
                self._CachedGridCoords[coord][0.5] = oneExtraCenterCoords[1:] - 0.5 * self.CoordIncrements[coordNum]

        # For t, the calculation is more complicated.
        
        elif coord == 't':
            if coord not in self._CachedGridCoords:
                self._CachedGridCoords[coord] = {}
            if fixedIncrementOffset not in self._CachedGridCoords[coord]:
                self._CachedGridCoords[coord][fixedIncrementOffset] = self._GetTCoordsList(fixedIncrementOffset, self.Shape[coordNum])

        # Return a numpy array of the requested slice of coordinates (if any).

        if slices is not None:
            if isinstance(slices[0], int):
                return self._CachedGridCoords[coord][fixedIncrementOffset][slices[0]]
            return numpy.array(self._CachedGridCoords[coord][fixedIncrementOffset][slices[0]], dtype='object' if coord == 't' else 'float')
        return numpy.array(self._CachedGridCoords[coord][fixedIncrementOffset], dtype='object' if coord == 't' else 'float')

    def _GetSlicesForCoordsKey(self, key):

        # Validate the key. The first element must be a dimension
        # name. The additional elements are optional, and depend on
        # whether that dimension depends on any others. If not, there
        # may optionally be exactly one additional element, which is
        # an integer index or slice into that dimension. If the
        # dimension does depend on others, there may optionaly be
        # exactly n + 1 additional elements, each integer indices or
        # slices into dimensions, where n is the number of
        # depended-upon dimensions. In this latter case, the order of
        # the indices/slices is the same as the order of the
        # dimensions, regardless of which dimension is requested and
        # what dimensions it depends on.
        #
        # Consider, for example, the 4D ROMS ocean model, in which the
        # values of z depend on x, y, and t. That is, the values of
        # the depth levels depend on latitude, longitude, and time
        # (search the internet for "vertical s-coordinate" for more
        # information). For this dataset, if the caller just requests
        # 'z' and provides no additional elements, a 4D array will be
        # returned with the shape of the entire dataset. That array
        # will be quite large, and the caller usually won't need it,
        # so he will usually supply indices or slices. In that case,
        # the caller must specify exactly four indices or slices,
        # ordered t, z, y, x, which is the order of the dimensions of
        # a 4D Grid dataset.

        if isinstance(key, str):
            key = (key,)

        if not isinstance(key, tuple) or len(key) < 1 or not isinstance(key[0], str):
            raise TypeError(_('The key must be a tuple with at least one element. The first element must be the dimension name, one of: %(dimnames)s.') % {'dimnames': ', '.join(["'" + s + "'" for s in self.Dimensions])})
        if key[0] not in self.Dimensions:
            raise KeyError(_('The first element of the key must be an existing dimension name, one of: %(dimnames)s.') % {'dimnames': ', '.join(["'" + s + "'" for s in self.Dimensions])})

        coord = key[0]
        coordNum = self.Dimensions.index(coord)

        expectedSlices = 1
        if self.CoordDependencies[coordNum] is not None:
            expectedSlices += len(self.CoordDependencies[coordNum])
            sliceDims = ''
            for dim in self.Dimensions:
                if dim == key[0] or dim in self.CoordDependencies[coordNum]:
                    sliceDims += dim
        else:
            sliceDims = coord

        if len(key) > 1:
            if len(key) - 1 != expectedSlices:
                raise KeyError(_('Invalid number of slices. When requesting %(dim)s coordinates of %(dn)s, you must either specify no slices (in which case the entire array of coordinates will be returned) or specify exactly %(slices)i slices.') % {'dn': self.DisplayName, 'dim': coord, 'slices': expectedSlices})

            slices = list(key[1:])

            for i in range(0, len(slices)):
                if isinstance (slices[i], slice):
                    if not isinstance(slices[i].start, (type(None), int)) or not isinstance(slices[i].stop, (type(None), int)) or not isinstance(slices[i].step, (type(None), int)):
                        raise TypeError(_('The slice start, stop, and step must be integers, or None.'))
                elif isinstance (slices[i], int):
                    dimNum = self.Dimensions.index(sliceDims[i])
                    if slices[i] >= self.Shape[dimNum] or slices[i] < 0-self.Shape[dimNum]:
                        raise IndexError(_('Index for %(dim)s dimension out of bounds.') % {'dim': self.Dimensions[dimNum]})
                    if slices[i] < 0:
                        slices[i] += self.Shape[dimNum]
                else:
                    raise TypeError(_('Element %(i)i of the key must be an integer or a slice.') % {'i': i+1})
        else:
            slices = None

        # Return successfully.

        return coord, coordNum, slices, sliceDims

    def _GetTCoordsList(self, fixedIncrementOffset, listLength):
        tCoords = []

        # self.GetLazyPropertyValue('CornerCoords')[coordNum] is the
        # coordinate of the first time slice. Depending on the
        # dataset, this coordinate may be given as the min, center, or
        # max for that slice. A lot of the following complexity deals
        # with the scenario where we are asked to produce a coordinate
        # type (min, center, max) that is different than that
        # specified for the first time slice.

        coordNum = self.Dimensions.index('t')
        t0 = self.GetLazyPropertyValue('CornerCoords')[coordNum]

        # If the t increment is day, hour, minute, or second, then it
        # is the same number of seconds every time step. We can use
        # simple timedeltas to do the math.

        tCornerCoordType = self.GetLazyPropertyValue('TCornerCoordType')
        tIncrement = self.CoordIncrements[coordNum]

        if self.TIncrementUnit in ['day', 'hour', 'minute', 'second']:

            # Create a timedelta for the increment.
            
            if self.TIncrementUnit == 'day':
                increment = datetime.timedelta(days=tIncrement)
            elif self.TIncrementUnit == 'hour':
                increment = datetime.timedelta(hours=tIncrement)
            elif self.TIncrementUnit == 'minute':
                increment = datetime.timedelta(minutes=tIncrement)
            else:
                increment = datetime.timedelta(seconds=tIncrement)

            # Calculate an offset that will yield the coordinate that
            # we're supposed to produce.

            if tCornerCoordType == 'min' and fixedIncrementOffset == 0.5:
                offset = increment
            elif tCornerCoordType == 'min' and fixedIncrementOffset == 0.0 or tCornerCoordType == 'center' and fixedIncrementOffset == 0.5:
                offset = increment / 2
            elif tCornerCoordType == 'min' and fixedIncrementOffset == -0.5 or tCornerCoordType == 'center' and fixedIncrementOffset == 0.0 or tCornerCoordType == 'max' and fixedIncrementOffset == 0.5:
                offset = datetime.timedelta(0)
            elif tCornerCoordType == 'center' and fixedIncrementOffset == -0.5 or tCornerCoordType == 'max' and fixedIncrementOffset == 0.0:
                offset = datetime.timedelta(0) - increment / 2
            else:
                offset = datetime.timedelta(0) - increment

            # Create the full list of t coordinates. If the
            # coordinates are not semi-regular, then it is easy.

            if self.TSemiRegularity is None:
                tCoords.extend([t0 + i * increment + offset for i in range(listLength)])

            # If the coordinates are semi-regular, it is more
            # complicated. At the moment, only annual semi-regularity
            # is supported.

            else:
                if self.TSemiRegularity != 'annual':
                    raise NotImplementedError(_('Programming error in this tool: \'%(sr)s\' semi-regularity has not been implemented. Please contact the MGET development team for assistance.') % {'sr': self.TSemiRegularity})
                if tCornerCoordType != 'min':
                    raise NotImplementedError(_('Support for semi-regularity for grids that have a tCornerCoordType other than \'min\' has not been implemented. Please contact the MGET development team for assistance.'))

                # Count backwards from t0 to determine how many time
                # slices precede it in the starting year.
                #
                # If we have a lazy property called
                # TOffsetFromParsedTime, it means that t0 includes
                # that offset. So to count back to the beginning of
                # the year, we must remove TOffsetFromParsedTime from
                # t0.

                tOffsetFromParsedTime = self.GetLazyPropertyValue('TOffsetFromParsedTime')
                if tOffsetFromParsedTime is not None:
                    deltaFromParsedTime = datetime.timedelta(tOffsetFromParsedTime)
                    t0 = t0 - deltaFromParsedTime
                else:
                    deltaFromParsedTime = datetime.timedelta(0)
                
                yearlyCount = 0
                startDate = t0
                while tCornerCoordType == 'min' and (startDate - increment).year == t0.year or tCornerCoordType == 'center' and (startDate - increment * 3 / 2).year == t0.year or tCornerCoordType == 'max' and (startDate - increment * 2).year == t0.year:
                    startDate -= increment
                    yearlyCount += 1

                # Now construct the full list of t coordinates.

                ignoreLeapYear = bool(self.GetLazyPropertyValue('IgnoreLeapYear'))      # If IgnoreLeapYear is True, time slices that encompass February 29 should be one day longer than the others. This is used for datasets like CCMP that want to use the same calendar dates for each year of data, even on leap years.
                if ignoreLeapYear and tCornerCoordType != 'min':
                    raise NotImplementedError(_('Programming error in this tool: Support for TSemiRegularity == \'annual\' and IgnoreLeapYear==True has not been implemented. Please contact the MGET development team for assistance.'))

                t = t0
                currentYear = t0.year
                for i in range(listLength):
                    yearlyCount += 1

                    # If we are not on the last time slice of the
                    # year, we just need to advance by the increment
                    # value (except for a special case involving leap
                    # years).
                    
                    if yearlyCount < self.TCountPerSemiRegularPeriod:
                        if not ignoreLeapYear or int(datetime.datetime(t.year, 12, 31).strftime('%j')) == 365 or not (tCornerCoordType == 'min' and t < datetime.datetime(t.year, 2, 29) and t + increment >= datetime.datetime(t.year, 2, 29)):
                            tCoords.append(t + offset + deltaFromParsedTime)
                            t += increment

                        # If we got here, it is a leap year, we are
                        # supposed to ignore it, and this time slice
                        # spans the change from Feb 28 to Feb 29.
                        # Compute a tCoord and t that account for the
                        # extra day.

                        else:
                            if fixedIncrementOffset == -0.5:
                                tCoords.append(t + deltaFromParsedTime)
                            elif fixedIncrementOffset == 0.0:
                                tCoords.append(t + offset + deltaFromParsedTime + datetime.timedelta(hours=12))
                            else:
                                tCoords.append(t + offset + deltaFromParsedTime + datetime.timedelta(days=1))
                            t += increment + datetime.timedelta(days=1)

                    # If we got to here, we are on the last time slice
                    # of the year. Usually, this means we have to
                    # truncate or extend it. 
                        
                    else:

                        # Because we only support semi-regularity for grids
                        # with tCornerCoordType == 'min', we know that t
                        # represents the min coordinate here. If that's want
                        # the caller requested, just append it.

                        if fixedIncrementOffset == -0.5:
                            tCoords.append(t + deltaFromParsedTime)

                        # Otherwise, if they want the max coordinate, append
                        # midnight January 1 of the next year.

                        elif fixedIncrementOffset == 0.5:
                            tCoords.append(datetime.datetime(t.year + 1, 1, 1) + deltaFromParsedTime)

                        # Otherwise (they want the center coordinate), append
                        # the time that is halfway between.

                        else:
                            deltaHalf = datetime.timedelta(seconds=(datetime.datetime(t.year + 1, 1, 1) - t).total_seconds / 2)
                            tCoords.append(t + deltaHalf + deltaFromParsedTime)

                        # Reset to the beginning of the next year.
                        
                        yearlyCount = 0
                        currentYear += 1
                        t = datetime.datetime(currentYear, startDate.month, startDate.day, startDate.hour, startDate.minute, startDate.second, startDate.microsecond)

        # If the t increment is month, season, or year, then it may be
        # a different number of seconds each time step. In these
        # cases, we increment according to the fraction of the month
        # or day of the year. We do not currently support
        # semi-regularity in these cases.

        else:
            if self.TSemiRegularity is not None:
                raise NotImplementedError(_('Programming error in this tool: semi-regularity is not currently supported if the TIncrementUnit is \'%(unit)s\'. Please contact the author of this tool for assistance.') % {'unit': self.TIncrementUnit})

            if self.TIncrementUnit == 'month':

                # Fail if the t increment is not an integer.
                # Currently, we only support incrementing by whole
                # months. If the user needs to increment by some
                # fractions of a month, they should use a
                # TIncrementUnit of 'day'.

                if math.modf(tIncrement)[0] != 0:
                    raise NotImplementedError(_('Programming error in this tool: when the time increment unit is \'month\', the time coordinate increment must be a whole number of months. The requested non-integer values %(value)s is not supported. Please contact the author of this tool for assistance.') % {'value': tIncrement})
                tIncrement = int(tIncrement)

                # If we have a lazy property called
                # TOffsetFromParsedTime, it means that t0 includes
                # that offset. But datasets that require the
                # TOffsetFromParsedTime hack typically want the t
                # coordinates to start on the same offset from the
                # beginning of the month. For example, the MODIS
                # monthly SST always starts at 00:00:00 of the first
                # day of the month, minus 12 hours (i.e. 12:00:00 on
                # the last day of the previous month).
                #
                # To make this all work out, perform the computations
                # using the t0 without the offset, then add the offset
                # back in when we calculate the series of coordinates.

                tOffsetFromParsedTime = self.GetLazyPropertyValue('TOffsetFromParsedTime')
                if tOffsetFromParsedTime is not None:
                    t0 = t0 - datetime.timedelta(tOffsetFromParsedTime)
                else:
                    tOffsetFromParsedTime = 0.

                # Fail if t0 (after removing TOffsetFromParsedTime) is
                # not at midnight on the first day of the month.
                # Currently, we only support having t0 at the border
                # between months because the logic for handling any
                # other time is very complicated and we do not know of
                # any datasets that require it.

                if t0.day != 1 or t0.hour != 0 or t0.minute != 0 or t0.second != 0 or t0.microsecond != 0:
                    raise NotImplementedError(_('Programming error in this tool: when the time increment unit is \'month\', the time corner coordinate must be the first day of the month at 00:00:00. Time corner coordinates that fall sometime within the month are not supported. Please contact the author of this tool for assistance.'))

                # Construct the full list of t coordinates.

                t = t0
                
                tPrev = t0
                for j in range(tIncrement):
                    if tPrev.month == 1:
                        tPrev = datetime.datetime(tPrev.year - 1, 12, 1)
                    else:
                        tPrev = datetime.datetime(tPrev.year, tPrev.month - 1, 1)

                for i in range(listLength):
                    tNext = t
                    for j in range(tIncrement):
                        if tNext.month == 12:
                            tNext = datetime.datetime(tNext.year + 1, 1, 1)
                        else:
                            tNext = datetime.datetime(tNext.year, tNext.month + 1, 1)

                    if tCornerCoordType == 'min':
                        if fixedIncrementOffset == -0.5:
                            tCoords.append(t + datetime.timedelta(tOffsetFromParsedTime))
                        elif fixedIncrementOffset == 0.0:
                            tCoords.append(t + (tNext - t) / 2 + datetime.timedelta(tOffsetFromParsedTime))
                        else:
                            tCoords.append(tNext + datetime.timedelta(tOffsetFromParsedTime))

                    elif tCornerCoordType == 'center':
                        if fixedIncrementOffset == -0.5:
                            tCoords.append(tPrev + (t - tPrev) / 2 + datetime.timedelta(tOffsetFromParsedTime))
                        elif fixedIncrementOffset == 0.0:
                            tCoords.append(t + datetime.timedelta(tOffsetFromParsedTime))
                        else:
                            tCoords.append(t + (tNext - t) / 2 + datetime.timedelta(tOffsetFromParsedTime))

                    else:
                        if fixedIncrementOffset == -0.5:
                            tCoords.append(tPrev + datetime.timedelta(tOffsetFromParsedTime))
                        elif fixedIncrementOffset == 0.0:
                            tCoords.append(tPrev + (t - tPrev) / 2 + datetime.timedelta(tOffsetFromParsedTime))
                        else:
                            tCoords.append(t + datetime.timedelta(tOffsetFromParsedTime))

                    tPrev = t
                    t = tNext

            elif self.TIncrementUnit == 'year':
                tOffsetFromParsedTime = self.GetLazyPropertyValue('TOffsetFromParsedTime')
                if tOffsetFromParsedTime is not None:
                    deltaFromParsedTime = datetime.timedelta(tOffsetFromParsedTime)
                    t0 = t0 - deltaFromParsedTime
                else:
                    deltaFromParsedTime = datetime.timedelta(0)

                if tCornerCoordType == 'min' and fixedIncrementOffset == 0.5:
                    t = datetime.datetime(t0.year + 1, t0.month, t0.day, t0.hour, t0.minute, t0.second, t0.microsecond)
                elif tCornerCoordType == 'min' and fixedIncrementOffset == 0.0 or tCornerCoordType == 'center' and fixedIncrementOffset == 0.5:
                    if t0.month > 6:
                        t = datetime.datetime(t0.year + 1, t0.month - 6, t0.day, t0.hour, t0.minute, t0.second, t0.microsecond)
                    else:
                        t = datetime.datetime(t0.year, t0.month + 6, t0.day, t0.hour, t0.minute, t0.second, t0.microsecond)
                elif tCornerCoordType == 'min' and fixedIncrementOffset == -0.5 or tCornerCoordType == 'center' and fixedIncrementOffset == 0.0 or tCornerCoordType == 'max' and fixedIncrementOffset == 0.5:
                    t = t0
                elif tCornerCoordType == 'center' and fixedIncrementOffset == -0.5 or tCornerCoordType == 'max' and fixedIncrementOffset == 0.0:
                    if t0.month <= 6:
                        t = datetime.datetime(t0.year - 1, t0.month + 6, t0.day, t0.hour, t0.minute, t0.second, t0.microsecond)
                    else:
                        t = datetime.datetime(t0.year, t0.month - 6, t0.day, t0.hour, t0.minute, t0.second, t0.microsecond)
                else:
                    t = datetime.datetime(t0.year - 1, t0.month, t0.day, t0.hour, t0.minute, t0.second, t0.microsecond)

                for i in range(listLength):
                    tCoords.append(t + deltaFromParsedTime)
                    t = datetime.datetime(t.year + 1, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)

            else:
                raise NotImplementedError(_('Programming error in this tool: the t increment unit \'%(unit)s\' is not currently supported. Please contact the author of this tool for assistance.') % {'unit': self.TIncrementUnit})

        # Return the list of coordinates.

        return tCoords

    def _GetScaledDataAsArray(self, key):
        unscaledData = self._GetUnscaledDataAsArray(key)
        data = self.GetLazyPropertyValue('ScalingFunction')(unscaledData)

        import numpy

        if data.dtype.name != self.DataType:
            data = numpy.asarray(data, dtype=self.DataType)
            
        if self.UnscaledNoDataValue is not None and self.NoDataValue is not None:
            if data.ndim > 0:
                data[Grid.numpy_equal_nan(unscaledData, self.UnscaledNoDataValue)] = self.NoDataValue
            elif unscaledData == self.UnscaledNoDataValue or numpy.isnan(unscaledData) and numpy.isnan(self.UnscaledNoDataValue):
                return numpy.array(self.NoDataValue, data.dtype)
            
        return data

    def _SetScaledDataWithArray(self, key, value):
        unscaledData = self.GetLazyPropertyValue('UnscalingFunction')(value)

        import numpy

        if self.UnscaledNoDataValue is not None and self.NoDataValue is not None:
            if unscaledData.ndim > 0:
                unscaledData[Grid.numpy_equal_nan(value, self.NoDataValue)] = self.UnscaledNoDataValue
            elif value == self.NoDataValue:
                unscaledData = numpy.array(self.UnscaledNoDataValue, unscaledData.dtype)
        
        self._SetUnscaledDataWithArray(key, unscaledData)

    def _GetUnscaledDataAsArray(self, key):

        # Validate the key and if any of the phyical dimensions are
        # flipped (e.g. the y coordinate decreases as the y index
        # increases), flip the key indices for those dimensions.
        
        flippedKey = self._ValidateAndFlipKey(key)

        # Convert the flipped key to a list of slices to specify to
        # the derived class the hyperslab of physical data that we
        # want. For the convenience of the derived class, there is a
        # slice for every dimension, with non-negative integer start
        # and stop attributes, start <= stop, and step == None.
        
        sliceList = self._GetSlicesForFlippedKey(flippedKey)

        # If the physical dimension order is different than our
        # standard order (tzyx), reorder the slices into the physical
        # order.

        physicalDimensions = self.GetLazyPropertyValue('PhysicalDimensions')
        if self.Dimensions != physicalDimensions:
            reorderedSliceList = []
            for dim in physicalDimensions:
                reorderedSliceList.append(sliceList[self.Dimensions.index(dim)])
        else:
            reorderedSliceList = sliceList

        # Get a numpy array for the slice list. This may take some
        # time; the data could be on a remote server; it may need to
        # be downloaded and/or decompressed.

        data, actualNoDataValue = self._ReadNumpyArray(reorderedSliceList)

        # If the physical dimension order is different than our
        # standard order, transpose the returned numpy array to our
        # standard order.
        
        if self.Dimensions != physicalDimensions:
            transposeList = []
            for dim in self.Dimensions:
                transposeList.append(physicalDimensions.index(dim))

            if transposeList not in [[0,1], [0,1,2], [0,1,2,3]]:
                data = data.transpose(transposeList)

        # The array that we got back has the shape described by the
        # key but we cannot use the key to index into it because the
        # key refers to an array with the full shape, not this reduced
        # shape. Adjust the key indices to the reduced shape.

        flippedKey = self._AdjustFlippedKeyIndicesToReducedShape(flippedKey)

        # If the dataset should use a different NoData value and/or
        # data type than what was returned, change the array to use
        # the desired NoData value and/or recast it to use the desired
        # data type.

        import numpy

        if actualNoDataValue is not None and self.UnscaledNoDataValue is not None and ((isinstance(self.UnscaledNoDataValue, int) and int(actualNoDataValue) != self.UnscaledNoDataValue or isinstance(self.UnscaledNoDataValue, float) and actualNoDataValue != self.UnscaledNoDataValue and not(numpy.isnan(actualNoDataValue) and numpy.isnan(self.UnscaledNoDataValue)))):
            if data.dtype.kind == 'i':
                self._LogDebug(_('%(class)s 0x%(id)016X: Changing the NoData value of the returned data from %(v1)i to %(v2)i.') % {'class': self.__class__.__name__, 'id': id(self), 'v1': int(actualNoDataValue), 'v2': self.UnscaledNoDataValue})
                data[data == int(actualNoDataValue)] = self.UnscaledNoDataValue
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: Changing the NoData value of the returned data from %(v1)g to %(v2)g.') % {'class': self.__class__.__name__, 'id': id(self), 'v1': actualNoDataValue, 'v2': self.UnscaledNoDataValue})
                data[Grid.numpy_equal_nan(data, actualNoDataValue)] = self.UnscaledNoDataValue

        if data.dtype.name != self.UnscaledDataType:
            self._LogDebug(_('%(class)s 0x%(id)016X: Changing the data type of the returned data from %(t1)s to %(t2)s.') % {'class': self.__class__.__name__, 'id': id(self), 't1': data.dtype.name, 't2': self.UnscaledDataType})
            import numpy
            data = numpy.asarray(data, dtype=self.UnscaledDataType)

        # Return the data.

        if len(flippedKey) == 1:
            return data.__getitem__(flippedKey[0])
        
        return data.__getitem__(tuple(flippedKey))

    def _ValidateAndFlipKey(self, key):

        # Validate the key. In numpy terminology, we support single
        # element indexing and slice indexing. We do not support index
        # arrays (either of integers or booleans). Thus, the key must
        # follow these rules:
        #
        #     1. It must be an integer, a slice, or a tuple.
        #
        #     2. If a tuple, it may only contain integers and slices.
        #
        #     3. The tuple may contain no more elements than the
        #        dimensions of the grid.

        if not isinstance(key, (int, slice, tuple)) or isinstance(key, bool):           # Note: bool is a subclass of int, so the second check is needed
            raise TypeError(_('Grids may only be indexed with a tuple of integers and slices, or a single integer or slice.'))

        if not isinstance(key, tuple):
            key = (key,)

        if len(key) > len(self.Dimensions):
            raise IndexError(_('Too many indices.'))

        import numpy

        newKey = []      # We replace numpy scalar integers and length-1 integer arrays with Python int
        for k in key:
            if numpy.issubdtype(type(k), numpy.integer):
                newKey.append(int(k))
            elif isinstance(k, numpy.ndarray) and k.size == 1 and numpy.issubdtype(k.dtype, numpy.integer):
                newKey.append(int(k[0]))
            elif isinstance(k, slice):
                newKey.append(slice(int(k.start) if numpy.issubdtype(type(k.start), numpy.integer) else \
                                        int(k.start[0]) if isinstance(k.start, numpy.ndarray) and k.start.size == 1 and numpy.issubdtype(k.start.dtype, numpy.integer) else \
                                        k.start,
                                    int(k.stop) if numpy.issubdtype(type(k.stop), numpy.integer) else \
                                        int(k.stop[0]) if isinstance(k.stop, numpy.ndarray) and k.stop.size == 1 and numpy.issubdtype(k.stop.dtype, numpy.integer) else \
                                        k.stop,
                                    int(k.step) if numpy.issubdtype(type(k.step), numpy.integer) else \
                                        int(k.step[0]) if isinstance(k.step, numpy.ndarray) and k.step.size == 1 and numpy.issubdtype(k.step.dtype, numpy.integer) else \
                                        k.step))
            else:
                newKey.append(k)
        key = tuple(newKey)

        for i in range(len(key)):
            if not isinstance(key[i], (int, slice)) or isinstance(key, bool) or isinstance(key[i], slice) and (not isinstance(key[i].start, (int, type(None))) or not isinstance(key[i].stop, (int, type(None))) or not isinstance(key[i].step, (int, type(None)))):
                raise IndexError(_('%(key)r is an invalid Grid index. Grid indices must be integers or integer slices.') % {'key': key[i]})
            if isinstance(key[i], int):
                if key[i] >= self.Shape[i]:
                    raise IndexError(_('Index out of bounds for dimension \'%(dim)s\'; %(val)i > dimension length %(len)i.') % {'dim': self.Dimensions[i], 'val': key[i], 'len': self.Shape[i]})
                elif key[i] < 0 - self.Shape[i]:
                    raise IndexError(_('Index out of bounds for dimension \'%(dim)s\'; %(val)i < 0 - dimension length %(len)i.') % {'dim': self.Dimensions[i], 'val': key[i], 'len': self.Shape[i]})
        
        # If any of the phyical dimensions are flipped (e.g. the y
        # coordinate decreases as the y index increases), flip the key
        # indices for those dimensions. As shown in the following
        # example, we can flip an integer index by multiplying by -1
        # and subtracting 1. We can flip a slice by doing the same
        # operation with start and stop and multiplying step by -1.
        #
        #     >>> x1
        #     [0, 1, 2, 3, 4, 5]
        #     >>> x2
        #     [5, 4, 3, 2, 1, 0]
        #     >>> 
        #     >>> x1[1]
        #     1
        #     >>> x2[-2]
        #     1
        #     >>> 
        #     >>> x1.__getitem__(slice(3,5,1))
        #     [3, 4]
        #     >>> x2.__getitem__(slice(-4,-6,-1))
        #     [3, 4]
        #     >>> 
        #     >>> x1.__getitem__(slice(-5,-3,1))
        #     [1, 2]
        #     >>> x2.__getitem__(slice(4,2,-1))
        #     [1, 2]
        #     >>> 
        #     >>> x1.__getitem__(slice(5,3,-1))
        #     [5, 4]
        #     >>> x2.__getitem__(slice(-6,-4,1))
        #     [5, 4]
        #     >>> 
        #     >>> x1.__getitem__(slice(-3,-5,-1))
        #     [3, 2]
        #     >>> x2.__getitem__(slice(2,4,1))
        #     [3, 2]

        flippedKey = []
        physicalDimensionsFlipped = self.GetLazyPropertyValue('PhysicalDimensionsFlipped')
        for i in range(len(key)):
            if physicalDimensionsFlipped[i]:
                if isinstance(key[i], int):
                    flippedKey.append(-1*key[i] - 1)
                else:
                    start, stop, step = key[i].start, key[i].stop, key[i].step
                    if start is not None:
                        start = -1*start -1
                    if stop is not None:
                        stop = -1*stop -1
                    if step is not None:
                        step = -1*step
                    else:
                        step = -1   # If step is None, it defaults to 1, so flipping None results in -1
                    flippedKey.append(slice(start, stop, step))
            else:
                flippedKey.append(key[i])

        return flippedKey

    def _GetSlicesForFlippedKey(self, flippedKey):
        sliceList = []
        
        for i in range(len(self.Dimensions)):
            if i < len(flippedKey):
                if isinstance(flippedKey[i], slice):
                    indices = flippedKey[i].indices(self.Shape[i])
                    if indices[0] <= indices[1]:
                        sliceList.append(slice(indices[0], indices[1]))
                    else:
                        sliceList.append(slice(indices[1]+1, indices[0]+1))
                elif flippedKey[i] >= 0:
                    sliceList.append(slice(flippedKey[i], flippedKey[i] + 1))
                else:
                    sliceList.append(slice(self.Shape[i] + flippedKey[i], self.Shape[i] + flippedKey[i] + 1))
            else:
                sliceList.append(slice(0, self.Shape[i]))

        return sliceList

    def _AdjustFlippedKeyIndicesToReducedShape(self, flippedKey):
        newFlippedKey = []
        
        for i in range(len(flippedKey)):
            if isinstance(flippedKey[i], int):
                newFlippedKey.append(0)
            else:
                start, stop, step = flippedKey[i].indices(self.Shape[i])
                adjustment = min(start, stop)
                start -= adjustment
                stop -= adjustment
                if start == 0:
                    start = None
                if stop == 0:
                    stop = None
                newFlippedKey.append(slice(start, stop, step))

        return newFlippedKey
    
    def _SetUnscaledDataWithArray(self, key, value):

        # Validate the key and if any of the phyical dimensions are
        # flipped (e.g. the y coordinate decreases as the y index
        # increases), flip the key indices for those dimensions
        
        flippedKey = self._ValidateAndFlipKey(key)

        # Validate that the value is either a numpy array, an integer,
        # a float, or a complex.

        import numpy
        if not isinstance(value, (numpy.ndarray, int, float, complex)):
            raise TypeError(_('The value must be a numpy array, an int, a float, or a complex.'))

        # Validate that the value contains the expected number of
        # elements. Turn it into an array if needed.

        expectedSize = 1
        expectedShape = []

        for i in range(len(self.Dimensions)):
            if i >= len(flippedKey):
                length = self.Shape[i]
            elif isinstance(flippedKey[i], slice):
                length = len(range(*flippedKey[i].indices(self.Shape[i])))
            else:
                length = 1
            expectedSize *= length
            expectedShape.append(length)

        if expectedSize == 0:
            if not isinstance(value, numpy.ndarray) or value.size != 0:
                raise ValueError(_('The key and value do not match: the key describes an array of size %(expected)i, but the value is an array of size %(actual)i.') % {'expected': 0, 'actual': value.size})
        elif expectedSize == 1:
            if isinstance(value, numpy.ndarray):
                if value.size != 1:
                    raise ValueError(_('The key and value do not match: the key describes an array of size %(expected)i, but the value is an array of size %(actual)i.') % {'expected': 1, 'actual': value.size})
            else:
                value = numpy.array(value)
        elif isinstance(value, numpy.ndarray):
            if value.size != expectedSize:
                raise ValueError(_('The key and value do not match: the key describes an array of size %(expected)i, but the value is an array of size %(actual)i.') % {'expected': expectedSize, 'actual': value.size})
        else:
            value = numpy.repeat(value, expectedSize)

        # Reshape the array to the expected shape. This will expand
        # the dimensions (if needed).

        value = value.reshape(expectedShape)

        # Convert the flipped key to a list of slices to specify to
        # the derived class the hyperslab of physical data that we're
        # going to write. For the convenience of the derived class,
        # there is a slice for every dimension, with positive start
        # and stop attributes, start <= stop, and step == None.
        #
        # Also determine whether we need to flip any of the axes of
        # the caller's array prior to passing it to the derived class,
        # so the derived class does not need to worry about writing it
        # in reverse order.
        #
        # Finally, if the caller's key included slices that have
        # abs(step) != 1. If so, we save the caller the effort of
        # having to stride the writes across the physical store: we
        # read the hyperslab that encloses the entire range described
        # by the caller's slices, apply the array in memory (allowing
        # numpy to do the striding), and write the hyperslab back.

        sliceList = []
        needToFlipData = []
        largeStep = False
        largeStepKey = []
        physicalDimensionsFlipped = self.GetLazyPropertyValue('PhysicalDimensionsFlipped')

        for i in range(len(self.Dimensions)):
            if i < len(flippedKey):
                if isinstance(flippedKey[i], slice):
                    start, stop, step = flippedKey[i].indices(self.Shape[i])
                    largeStep = largeStep or step is not None and abs(step) > 1
                    if step is not None and step < 0:
                        needToFlipData.append(True)
                        rstart = start + step*((stop-start+1) // step)
                        rstop = start+1
                        rstep = -1*step
                        sliceList.append(slice(rstart, rstop))
                        largeStepKey.append(slice(0, rstop-rstart, rstep))
                    else:
                        needToFlipData.append(False)
                        sliceList.append(slice(start, stop))
                        largeStepKey.append(slice(0, stop-start, step))
                else:
                    needToFlipData.append(False)
                    if flippedKey[i] >= 0:
                        sliceList.append(slice(flippedKey[i], flippedKey[i] + 1))
                    else:
                        sliceList.append(slice(self.Shape[i] + flippedKey[i], self.Shape[i] + flippedKey[i] + 1))
                    largeStepKey.append(slice(None))
            else:
                needToFlipData.append(physicalDimensionsFlipped[i])
                sliceList.append(slice(0, self.Shape[i]))
                largeStepKey.append(slice(None))

        # If we need to flip any of the axes of the caller's array, do
        # it now.

        if True in needToFlipData:
            self._LogDebug(_('%(class)s 0x%(id)016X: Flipping the following axes prior to writing data: %(axes)s'), {'class': self.__class__.__name__, 'id': id(self), 'axes': ', '.join([d for d in self.Dimensions if needToFlipData[self.Dimensions.index(d)]])})
            value = value.__getitem__(tuple([slice(None, None, {True: -1, False: None}[f]) for f in needToFlipData]))

        # If the physical dimension order is different than our
        # standard order (tzyx), reorder the slices and data into the
        # physical order.

        physicalDimensions = self.GetLazyPropertyValue('PhysicalDimensions')
        if self.Dimensions != physicalDimensions:
            reorderedSliceList = []
            reorderedLargeStepKey = []
            transposeList = []

            for dim in physicalDimensions:
                reorderedSliceList.append(sliceList[self.Dimensions.index(dim)])
                reorderedLargeStepKey.append(largeStepKey[self.Dimensions.index(dim)])
                transposeList.append(physicalDimensions.index(dim))

            value = value.transpose(transposeList)
        else:
            reorderedSliceList = sliceList
            reorderedLargeStepKey = largeStepKey

        # If the data type of the value is not the same as this
        # dataset, cast the value to the correct data type.

        if value.dtype.name != self.UnscaledDataType:
            if not numpy.can_cast(value.dtype, str(self.UnscaledDataType)):
                self._LogDebug(_('%(class)s 0x%(id)016X: Warning: casting from %(dt1)s to %(dt2)s. The loss of precision may produce unexpected results.'), {'class': self.__class__.__name__, 'id': id(self), 'dt1': value.dtype.name, 'dt2': self.UnscaledDataType})
            value = numpy.asarray(value, dtype=self.UnscaledDataType)

        # If the caller's key included slices that have abs(step) > 1,
        # read the hyperslab that encloses the entire range described
        # by the caller's slices, apply the array in memory (allowing
        # numpy to do the striding), and write it back.

        if largeStep:
            existingData, actualNoDataValue = self._ReadNumpyArray(reorderedSliceList)
            
            if existingData.dtype.name != value.dtype.name:
                self._LogDebug(_('%(class)s 0x%(id)016X: Changing the data type of the returned data from %(t1)s to %(t2)s.') % {'class': self.__class__.__name__, 'id': id(self), 't1': existingData.dtype.name, 't2': value.dtype.name})
                existingData = numpy.asarray(existingData, dtype=value.dtype.name)

            existingData.__setitem__(largeStepKey, value)

            self._WriteNumpyArray(reorderedSliceList, existingData)

        # Otherwise just write the data (no need to read the existing
        # data first).

        else:
            self._WriteNumpyArray(reorderedSliceList, value)

    # Private methods that the derived class must override (except
    # _GetCoords when the derived class only uses fixed coordinate
    # increments).

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        raise NotImplementedError(_('The _GetCoords method of class %s has not been implemented.') % self.__class__.__name__)

    def _ReadNumpyArray(self, sliceList):
        raise NotImplementedError(_('The _ReadNumpyArray method of class %s has not been implemented.') % self.__class__.__name__)

    def _WriteNumpyArray(self, sliceList, data):
        raise RuntimeError(_('The Data property of class %(class)s is read only. It is not possible to set the values of cells in a %(class)s instance.') % {'class': self.__class__.__name__})


class _ContainerEmulator(object):      # Private helper class for Grid
    def __init__(self, grid, getMethod, setMethod=None):
        self._Grid = weakref.ref(grid)                  # This must be a weak reference so that we do not create a reference cycle and prevent the Grid instance from being garbage collected.
        self._GetMethod = getMethod
        self._SetMethod = setMethod

    def __getitem__(self, key):
        return getattr(self._Grid(), self._GetMethod)(key)

    def __setitem__(self, key, value):
        if self._SetMethod is None:
            raise TypeError('This property does not support item assignment')
        return getattr(self._Grid(), self._SetMethod)(key, value)


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
