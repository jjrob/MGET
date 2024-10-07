# _TimeSeriesGridStack.py - A tyx or tzyx Grid built by stacking a set of yx
# or zyx Grids in a DatasetCollection.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Types import DateTimeTypeMetadata

from .. import Grid, QueryableAttribute


class TimeSeriesGridStack(Grid):
    __doc__ = DynamicDocString()

    def _GetReportProgress(self):
        return self._ReportProgress

    def _SetReportProgress(self, value):
        assert isinstance(value, bool), 'ReportProgress must be a bool.'
        self._ReportProgress = value

    ReportProgress = property(_GetReportProgress, _SetReportProgress, doc=DynamicDocString())

    def __init__(self, collection, expression=None, reportProgress=True, **options):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Validate that the collection has a queryable attribute with
        # data type DateTimeTypeMetadata.

        dateTimeAttrs = collection.GetQueryableAttributesWithDataType(DateTimeTypeMetadata)
        if len(dateTimeAttrs) <= 0:
            raise ValueError(_('This dataset collection does not have a queryable attribute defined with the data type DateTimeTypeMetadata. In order to build a TimeSeriesGridStack from it, it must have an attribute with that data type.'))
        if len(dateTimeAttrs) > 1:      # Should never happen; CollectibleObject.__init__ prevents it
            raise ValueError(_('This dataset collection has multiple queryable attributes defined with the data type DateTimeTypeMetadata. In order to build a TimeSeriesGridStack from it, only one queryable attribute of that type must be defined.'))

        # Query the collection for the oldest grid within it.

        self._CachedOldestGrid = collection.GetOldestDataset(expression, **options)

        if self._CachedOldestGrid is None:
            raise CollectionIsEmptyError(collection.DisplayName, expression)
        
        if not issubclass(self._CachedOldestGrid.__class__, Grid):
            raise TypeError(_('The dataset collection %(dn)s does not contain Grid datasets. %(cls)s can only be used with dataset collections that contain Grid datasets.') % {'dn': collection.DisplayName, 'cls': self.__class__.__name__})

        # Copy all of the queryable attributes, except the
        # DateTimeTypeMetadata one, and their values from the oldest grid. All
        # of the grids returned by the expression should have the same values
        # for any given queryable attribute (except the DateTimeTypeMetadata
        # attribute and attributes derived from it). We do not verify this,
        # however.

        queryableAttributes = []
        obj = self._CachedOldestGrid
        while obj is not None:
            if obj._QueryableAttributes is not None:
                for attr in obj._QueryableAttributes:
                    if attr.Name != dateTimeAttrs[0].Name:
                        queryableAttributes.append(QueryableAttribute(attr.Name, attr.DisplayName, attr.DataType, None, attr.DerivedFromAttr, attr.DerivedValueMap, attr.DerivedValueFunc))      # Do not copy attr.DerivedLazyDatasetProps 
            obj = obj.ParentCollection

        queryableAttributeValues = {}
        for attr in queryableAttributes:
            if attr.DerivedFromAttr != dateTimeAttrs[0].Name:
                queryableAttributeValues[attr.Name] = self._CachedOldestGrid.GetQueryableAttributeValue(attr.Name)

        # Initialize our properties.

        self._Collection = collection
        self._Expression = expression
        self._ReportProgress = reportProgress
        self._Options = options
        self._DateTimeAttrName = dateTimeAttrs[0].Name
        self._CachedQueryExpression = None
        self._CachedDatasets = None

        # Initialize the base class.

        super(TimeSeriesGridStack, self).__init__(queryableAttributes=tuple(queryableAttributes), queryableAttributeValues=queryableAttributeValues)

    def _Close(self):
        if hasattr(self, '_CachedOldestGrid') and self._CachedOldestGrid is not None:
            self._CachedOldestGrid.Close()

        if hasattr(self, '_CachedDatasets') and self._CachedDatasets is not None:
            while len(self._CachedDatasets) > 0:
                self._CachedDatasets[0].Close()
                del self._CachedDatasets[0]
            self._CachedQueryExpression = None
            self._CachedDatasets = None

        if hasattr(self, '_Collection'):
            self._Collection.Close()
            
        super(TimeSeriesGridStack, self)._Close()

    def _GetDisplayName(self):
        if self._Expression is not None:
            return _('%(dn)s where %(expr)s') % {'dn': self._Collection.DisplayName, 'expr': self._Expression}
        return self._Collection.DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the oldest grid does not have a t dimension already, we are
        # stacking a collection of 2D (yx) or 3D (zyx) grids into a 3D (tyx)
        # or 4D (tzyx) stack.
        #
        # As a special case, we treat a 3D (txy) or 4D (tzxy) grid with one
        # time slice as a 2D (xy) or 3D (zxy) grid.

        if 't' not in self._CachedOldestGrid.Dimensions or self._CachedOldestGrid.Shape[0] == 1:

            # Handle properties that are not identical to but are easily
            # calculated from the values of the oldest grid.

            if name == 'Dimensions':
                if self._CachedOldestGrid.Dimensions[0] != 't':
                    return 't' + self._CachedOldestGrid.Dimensions
                return self._CachedOldestGrid.Dimensions

            if name == 'PhysicalDimensions':
                if self._CachedOldestGrid.Dimensions[0] != 't':
                    return 't' + self._CachedOldestGrid.Dimensions      # Transposing of the underlying time slices is done when we fetch each slice, thus they are all properly ordered by the time we receive them.
                return self._CachedOldestGrid.Dimensions

            if name == 'PhysicalDimensionsFlipped':
                if self._CachedOldestGrid.Dimensions[0] != 't':
                    return tuple([False] * (len(self._CachedOldestGrid.Dimensions) + 1))      # Flipping of the underlying time slices is done when we fetch each slice, thus they are all properly oriented by the time we receive them.
                return tuple([False] * len(self._CachedOldestGrid.Dimensions))

            if name == 'CoordDependencies':
                if self._CachedOldestGrid.Dimensions[0] != 't':
                    return tuple([None] + list(self._CachedOldestGrid.CoordDependencies))
                return tuple([None] + list(self._CachedOldestGrid.CoordDependencies[1:]))

            if name == 'CoordIncrements':
                if self._CachedOldestGrid.Dimensions[0] != 't':
                    return tuple([self._CachedOldestGrid.GetLazyPropertyValue('TIncrement')] + list(self._CachedOldestGrid.CoordIncrements))
                return tuple([self._CachedOldestGrid.GetLazyPropertyValue('TIncrement')] + list(self._CachedOldestGrid.CoordIncrements[1:]))

            if name == 'CornerCoords':
                if self._CachedOldestGrid.Dimensions[0] != 't':
                    return tuple([self._CachedOldestGrid.GetQueryableAttributeValue(self._DateTimeAttrName)] + list(self._CachedOldestGrid.GetLazyPropertyValue('CornerCoords')))
                return tuple([self._CachedOldestGrid.GetQueryableAttributeValue(self._DateTimeAttrName)] + list(self._CachedOldestGrid.GetLazyPropertyValue('CornerCoords')[1:]))

            # Handle the shape. This is more complicated because we have to
            # determine how many time slices there are.

            if name == 'Shape':

                # If the t increment is not None, we do not need to retrieve
                # the full list of grids to know how many time slices there
                # are. Instead, we can calculate how many must appear between
                # the oldest grid and the newest grid.

                if self.CoordIncrements[0] is not None:
                    newestGrid = self._Collection.GetNewestDataset(self._Expression, **self._Options)
                    if not issubclass(newestGrid.__class__, Grid):
                        raise TypeError(_('The dataset collection %(dn)s does not contain Grid datasets. %(cls)s can only be used with dataset collections that contain Grid datasets.') % {'dn': self._Collection.DisplayName, 'cls': self.__class__.__name__})
                    newestGridDateTime = newestGrid.GetQueryableAttributeValue(self._DateTimeAttrName)

                    # Estimate the number of time slices between the oldest
                    # grid and newest grid.

                    delta = newestGridDateTime - self._CachedOldestGrid.GetQueryableAttributeValue(self._DateTimeAttrName)
                    delta = delta.days * 86400. + delta.seconds

                    if self.TIncrementUnit == 'year':
                        numTimeSlices = int(1.1 * delta / 86400. / 365.)
                    elif self.TIncrementUnit == 'season':
                        numTimeSlices = int(1.1 * delta / 86400. / 365. * 4.)
                    elif self.TIncrementUnit == 'month':
                        numTimeSlices = int(1.1 * delta / 86400. / 365. * 12.)
                    elif self.TIncrementUnit == 'day':
                        numTimeSlices = int(1.1 * delta / 86400.)
                    elif self.TIncrementUnit == 'hour':
                        numTimeSlices = int(1.1 * delta / 3600.)
                    elif self.TIncrementUnit == 'minute':
                        numTimeSlices = int(1.1 * delta / 60.)
                    elif self.TIncrementUnit == 'second':
                        numTimeSlices = int(1.1 * delta)
                    else:
                        raise NotImplementedError(_('Programming error in this tool: the t increment unit \'%(unit)s\' is unknown. Please contact the author of this tool for assistance.') % {'unit': self.TIncrementUnit})

                    if numTimeSlices < 1:
                        numTimeSlices = 1

                    # Get a list of t coordinates starting with the first time
                    # slice.

                    tCornerCoordType = self.GetLazyPropertyValue('TCornerCoordType').lower()
                    if tCornerCoordType == 'min':
                        fixedIncrementOffset = -0.5
                    elif tCornerCoordType == 'center':
                        fixedIncrementOffset = 0.0
                    elif tCornerCoordType == 'max':
                        fixedIncrementOffset = 0.5
                    else:
                        raise NotImplementedError(_('Programming error in this tool: the t corner coordinate type \'%(type)s\' is unknown. Please contact the author of this tool for assistance.') % {'type': self.GetLazyPropertyValue('TCornerCoordType')})

                    tCoords = self._GetTCoordsList(fixedIncrementOffset, numTimeSlices)

                    # While the time of the newest grid is newer than the
                    # newest t coordinate, double the size of the list. This
                    # should probably never happen.

                    while len(tCoords) > 0 and tCoords[-1] < newestGridDateTime:
                        numTimeSlices *= 2
                        tCoords = self._GetTCoordsList(fixedIncrementOffset, numTimeSlices)

                    # Search the t coordinates backwards for the time of the
                    # newest grid. This tells us the number of time slices. If
                    # we do not find it, something odd is going on; the parsed
                    # datetime is inconsistent with the definition of the
                    # dataset.

                    i = len(tCoords) - 1
                    while i >= 0:
                        if tCoords[i] == newestGridDateTime:
                            break
                        if tCoords[i] < newestGridDateTime:
                            raise ValueError(_('Failed to compute a time coordinate that matched the time of the newest grid in this %(cls)s. The datetime of that grid is %(last)s but the two closest time coordinates are %(dt1)s and %(dt2)s.') % {'cls': self.__class__.__name__, 'last': newestGridDateTime.strftime('%Y-%m-%d %H:%M:%S'), 'dt1': tCoords[i].strftime('%Y-%m-%d %H:%M:%S'), 'dt2': tCoords[i+1].strftime('%Y-%m-%d %H:%M:%S')})
                        i -= 1
                    if i < 0:
                        raise ValueError(_('Programming error in this tool: The datetime of the newest grid in this %(cls)s is %(last)s, which comes before the datetime of the first time coordinate, %(dt1)s. Please contact the author of this tool for assistance') % {'cls': self.__class__.__name__, 'last': newestGridDateTime.strftime('%Y-%m-%d %H:%M:%S'), 'dt1': tCoords[0].strftime('%Y-%m-%d %H:%M:%S')})

                    # Set and return the shape.

                    if self._CachedOldestGrid.Dimensions[0] != 't':
                        shape = tuple([i+1] + list(self._CachedOldestGrid.Shape))
                    else:
                        shape = tuple([i+1] + list(self._CachedOldestGrid.Shape[1:]))

                    self.SetLazyPropertyValue('Shape', shape)

                    return shape

                # The t increment is None. We need to retrieve the full list
                # of grids to know the number of time slices. We do not
                # currently support this.

                raise NotImplementedError(_('The dataset collection %(dn)s contains grids that do not have a fixed time increment. The current implementation of %(cls)s does not support grids of this kind.') % {'dn': self._Collection.DisplayName, 'cls': self.__class__.__name__})

        # If the contained grids have a t dimension already, we are
        # concatenating a collection of 3D (tyx) or 4D (tzyx) grids. The stack
        # will have the same dimensions as an individual grid in the
        # collection. We do not currently support this.

        else:
            raise NotImplementedError(_('The dataset collection %(dn)s contains grids that have a time dimension. The current implementation of %(cls)s does not support grids with a time dimension.') % {'dn': self._Collection.DisplayName, 'cls': self.__class__.__name__})

        # If we got to here, the caller has requested a lazy property that is
        # assumed to be the same for all grids in the collection as well as
        # the stack itself. Return the value from the oldest grid.

        return self._CachedOldestGrid.GetLazyPropertyValue(name)

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        raise NotImplementedError(_('The current implementation of %(cls)s does not support grids that do not have fixed coordinate increments.') % {'cls': self.__class__.__name__})

    def _ReadNumpyArray(self, sliceList):

        # Get a list of t coordinates for the requested time slices.

        tCornerCoordType = self.GetLazyPropertyValue('TCornerCoordType').lower()
        if tCornerCoordType == 'min':
            tCoords = self.MinCoords.__getitem__(('t', sliceList[0]))
        elif tCornerCoordType == 'center':
            tCoords = self.CenterCoords.__getitem__(('t', sliceList[0]))
        elif tCornerCoordType == 'max':
            tCoords = self.MaxCoords.__getitem__(('t', sliceList[0]))
        else:
            raise NotImplementedError(_('Programming error in this tool: the t corner coordinate type \'%(type)s\' is unknown. Please contact the author of this tool for assistance.') % {'type': self.GetLazyPropertyValue('TCornerCoordType')})

        # Query the collection for a list of datasets with t coordinates that
        # fall within the min and max coordinates of the requested time
        # slices. If the coordinates have the same hour, minute, and second
        # values, the caller is querying across a range of days, months, or
        # years. In that case, base the query on Year and DayOfYear, so that
        # the query can complete without retrieving the time components, which
        # can speed processing for collections like NASA PO.DAAC GHRSST L4,
        # which stores daily images in subdirectories by day of year. (Having
        # to probe into those directories to obtain the hour, minute, and
        # second of the file is expensive.) In some situations, this may
        # result in us obtaining more datasets than are needed, which is sub-
        # optimal, but the while loop further below handles this excess and
        # will return a correct result.

        if tCoords[0].hour == tCoords[-1].hour and tCoords[0].minute == tCoords[-1].minute and tCoords[0].second == tCoords[-1].second:
            expression = tCoords[0].strftime('(Year = %Y AND DayOfYear >= %j OR Year > %Y)') + tCoords[-1].strftime(' AND (Year = %Y AND DayOfYear <= %j OR Year < %Y)')
        else:
            expression = tCoords[0].strftime('(Year >= %Y AND ' + self._DateTimeAttrName + ' >= #%Y-%m-%d %H:%M:%S#)') + tCoords[-1].strftime(' AND (Year <= %Y AND ' + self._DateTimeAttrName + ' <= #%Y-%m-%d %H:%M:%S#)')

        if self._Expression is not None:
            expression = '(' + expression + ') AND (' + self._Expression + ')'

        if self._CachedQueryExpression is None or self._CachedQueryExpression != expression:
            if self._CachedDatasets is not None:
                while len(self._CachedDatasets) > 0:
                    self._CachedDatasets[0].Close()
                    del self._CachedDatasets[0]            
                self._CachedDatasets = None
                self._CachedQueryExpression = None
            
            self._CachedDatasets = self._Collection.QueryDatasets(expression, self._ReportProgress and len(tCoords) > 1, **self._Options)
            self._CachedQueryExpression = expression

            # Most likely, the datasets are already sorted in ascending time
            # order, but this is not required. Sort them, to be sure.

            self._CachedDatasets.sort(key=lambda ds: ds.GetQueryableAttributeValue(self._DateTimeAttrName))

        # Allocate a numpy array to return.

        import numpy
        data = numpy.zeros([s.stop - s.start for s in sliceList], str(self._CachedOldestGrid.UnscaledDataType))

        # Fill each time slice by retrieving the data from the corresponding
        # dataset. If we encounter a time slice for which there is no dataset
        # with a matching time coordinate, allocate a slice of NoData and
        # report a warning. If there is no NoData value, leave the values at
        # zero.

        t = 0
        i = 0
        while t < len(tCoords):
            while i < len(self._CachedDatasets) and self._CachedDatasets[i].GetQueryableAttributeValue(self._DateTimeAttrName) < tCoords[t]:
                i += 1
                
            if i < len(self._CachedDatasets) and self._CachedDatasets[i].GetQueryableAttributeValue(self._DateTimeAttrName) == tCoords[t]:
                if self._CachedDatasets[i].Dimensions[0] != 't':
                    data[t] = self._CachedDatasets[i].UnscaledData.__getitem__(tuple(sliceList[1:]))
                else:
                    data[t] = self._CachedDatasets[i].UnscaledData.__getitem__(tuple([0] + sliceList[1:]))
            elif self._CachedOldestGrid.UnscaledNoDataValue is not None:
                if tCornerCoordType == 'min':
                    self._LogWarning(_('There is no data in %(dn)s for the time slice that starts on %(ts)s.') % {'dn': self._Collection.DisplayName, 'ts': tCoords[t].strftime('%Y-%m-%d %H:%M:%S')})
                elif tCornerCoordType == 'center':
                    self._LogWarning(_('There is no data in %(dn)s for the time slice %(ts)s.') % {'dn': self._Collection.DisplayName, 'ts': tCoords[t].strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    self._LogWarning(_('There is no data in %(dn)s for the time slice that ends on %(ts)s.') % {'dn': self._Collection.DisplayName, 'ts': tCoords[t].strftime('%Y-%m-%d %H:%M:%S')})
                data[t] += self._CachedOldestGrid.UnscaledNoDataValue
            else:
                if tCornerCoordType == 'min':
                    self._LogWarning(_('There is no data in %(dn)s for the time slice that starts on %(ts)s but the datasets in this collection do not have a NoData value defined. The values of this time slice will be set to 0.') % {'dn': self._Collection.DisplayName, 'ts': tCoords[t].strftime('%Y-%m-%d %H:%M:%S')})
                elif tCornerCoordType == 'center':
                    self._LogWarning(_('There is no data in %(dn)s for the time slice %(ts)s but the datasets in this collection do not have a NoData value defined. The values of this time slice will be set to 0.') % {'dn': self._Collection.DisplayName, 'ts': tCoords[t].strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    self._LogWarning(_('There is no data in %(dn)s for the time slice that ends on %(ts)s but the datasets in this collection do not have a NoData value defined. The values of this time slice will be set to 0.') % {'dn': self._Collection.DisplayName, 'ts': tCoords[t].strftime('%Y-%m-%d %H:%M:%S')})

            t += 1

        # Return the populated numpy array.

        return data, self._CachedOldestGrid.UnscaledNoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
