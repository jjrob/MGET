# _ClimatologicalGridCollection.py - A DatasetCollection that summarizes a 3D
# or 4D Grid across time into a collection of 2D or 3D Grids representing
# aggregate values.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import bisect
import datetime

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Types import IntegerTypeMetadata, UnicodeStringTypeMetadata

from .. import DatasetCollection, QueryableAttribute


class ClimatologicalGridCollection(DatasetCollection):
    __doc__ = DynamicDocString()

    def _GetStatistic(self):
        return self._Statistic

    Statistic = property(_GetStatistic, doc=DynamicDocString())

    def _GetBinType(self):
        return self._BinType

    BinType = property(_GetBinType, doc=DynamicDocString())

    def _GetBinDuration(self):
        return self._BinDuration

    BinDuration = property(_GetBinDuration, doc=DynamicDocString())

    def _GetStartDayOfYear(self):
        return self._StartDayOfYear

    StartDayOfYear = property(_GetStartDayOfYear, doc=DynamicDocString())

    def _GetReportProgress(self):
        return self._ReportProgress

    def _SetReportProgress(self, value):
        self.__doc__.Obj.ValidatePropertyAssignment()
        self._ReportProgress = value

    ReportProgress = property(_GetReportProgress, _SetReportProgress, doc=DynamicDocString())

    def __init__(self, grid, statistic, binType, binDuration=1, startDayOfYear=1, reportProgress=False):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Validate that the grid has a t dimension and that it can be used to
        # produce the desired bin type.

        if 't' not in grid.Dimensions:
            raise ValueError(_('%(dn)s does not have a time dimension. In order to create a climatology, it must have a time dimension.') % {'dn': grid.DisplayName})

        # If the binDuration is monthly, validate that the startDayOfYear is
        # not the 28th, 29th, 30th, or 31st day of the start month. To keep
        # our calculations simple, we do not support those days as starting
        # days.

        startDateTime = datetime.datetime(2001, 1, 1) + datetime.timedelta(startDayOfYear - 1)      # Use a non-leap year for this calculation
        if startDateTime.day > 28:
            raise NotImplementedError(_('The Start Day Of Year parameter specifies that the first climatological grid should start on %(day)i %(month)s. This is not supported. The grid may not start later than day 28 of any month. We apologize for the inconvenience.') % {'day': startDateTime.day, 'month': startDateTime.strftime('%B')})

        # If the grid has a time increment that is larger than the bin length,
        # warn the user that this may produce undesirable output.

        if not binType.endswith('cumulative') and grid.CoordIncrements[0] is not None and grid.TIncrementUnit in ['second', 'minute', 'hour', 'day', 'month', 'year']:
            if grid.TIncrementUnit == 'second':
                gridTIncrement = grid.CoordIncrements[0]
            elif grid.TIncrementUnit == 'minute':
                gridTIncrement = grid.CoordIncrements[0] * 60
            elif grid.TIncrementUnit == 'hour':
                gridTIncrement = grid.CoordIncrements[0] * 60 * 60
            elif grid.TIncrementUnit == 'day':
                gridTIncrement = grid.CoordIncrements[0] * 60 * 60 * 24
            elif grid.TIncrementUnit == 'month':
                gridTIncrement = grid.CoordIncrements[0] * 60 * 60 * 24 * 30
            else:
                gridTIncrement = grid.CoordIncrements[0] * 60 * 60 * 24 * 365

            if binType.endswith('daily'):
                binLength = binDuration * 60 * 60 * 24
            else:
                binLength = binDuration * 60 * 60 * 24 * 30     # Monthly

            if gridTIncrement > binLength:
                if binType.endswith('monthly'):
                    if binDuration == 1:
                        binTypeName = 'month'
                    else:
                        binTypeName = 'months'
                else:
                    if binDuration == 1:
                        binTypeName = 'day'
                    else:
                        binTypeName = 'days'
                self._LogWarning(_('The time increment of %(dn)s is longer than the requested climatology bin length (%(gridTIncrement)g %(gridTIncrementUnit)s(s) vs. %(binDuration)i %(binTypeName)s). This may produce unsatisfactory results. The time slices are placed into bins according to their center time coordinate, and are not split between bins. This can lead to problems if the bin is short compared to the time slice. For example, if the bin is 1 day long while the time slice is 1 month long, the entire time slice will be placed in the bin for the day that occurs in the middle of that month. To avoid this kind of problem, increase the bin duration so that the bins are longer than the time slices (preferably a lot longer).') % {'dn': grid.DisplayName, 'gridTIncrement': grid.CoordIncrements[0], 'gridTIncrementUnit': grid.TIncrementUnit, 'binDuration': binDuration, 'binTypeName': binTypeName})

        # Initialize our properties.

        self._Grid = grid
        self._Statistic = statistic
        self._BinType = binType
        self._BinDuration = binDuration
        self._StartDayOfYear = startDayOfYear
        self._ReportProgress = reportProgress
        self._AggregateGrids = None
        self._ONIDict = None

        if binType.endswith('cumulative'):
            self._DisplayName = _('cumulative climatological %(statistic)s of the %(dn)s') % {'dn': grid.DisplayName, 'statistic': self._Statistic}
        elif binType.endswith('monthly'):
            if self._BinDuration == 1:
                self._DisplayName = _('monthly climatological %(statistic)s of the %(dn)s') % {'dn': grid.DisplayName, 'statistic': self._Statistic}
            else:
                self._DisplayName = _('%(binDuration)i-month climatological %(statistic)s of the %(dn)s') % {'dn': grid.DisplayName, 'binDuration': self._BinDuration, 'statistic': self._Statistic}
        else:
            if self._BinDuration == 1:
                self._DisplayName = _('daily climatological %(statistic)s of the %(dn)s') % {'dn': grid.DisplayName, 'statistic': self._Statistic}
            else:
                self._DisplayName = _('%(binDuration)i-day climatological %(statistic)s of the %(dn)s') % {'dn': grid.DisplayName, 'binDuration': self._BinDuration, 'statistic': self._Statistic}

        if binType.startswith('enso'):
            self._DisplayName = _('ENSO-phased ') + self._DisplayName

        # Create the queryable attributes appropriate for the bin
        # type.

        qa = [QueryableAttribute('ClimatologyBinType', 'Climatology bin type', UnicodeStringTypeMetadata()),
              QueryableAttribute('ClimatologyBinName', 'Climatology bin name', UnicodeStringTypeMetadata()),
              QueryableAttribute('Statistic', 'Statistic', UnicodeStringTypeMetadata())]

        qav = {'Statistic': self._Statistic.lower()}

        if binType.endswith('cumulative'):
            qav['ClimatologyBinType'] = 'Cumulative'

        elif binType.endswith('monthly'):
            qa.append(QueryableAttribute('FirstMonth', 'First month of this bin', IntegerTypeMetadata(minValue=1, maxValue=12)))
            qa.append(QueryableAttribute('DayOfFirstMonth', 'Day of the first month', IntegerTypeMetadata(minValue=1, maxValue=31)))
            qa.append(QueryableAttribute('LastMonth', 'Last month of this bin', IntegerTypeMetadata(minValue=1, maxValue=12)))
            qa.append(QueryableAttribute('DayOfLastMonth', 'Day of the last month', IntegerTypeMetadata(minValue=1, maxValue=31)))
            if self._BinDuration == 1:
                qav['ClimatologyBinType'] = 'Monthly'
            else:
                qav['ClimatologyBinType'] = '%imonth' % self._BinDuration

        else:
            qa.append(QueryableAttribute('FirstDay', 'First day of the year of this bin', IntegerTypeMetadata(minValue=1, maxValue=366)))
            qa.append(QueryableAttribute('LastDay', 'Last day of the year of this bin', IntegerTypeMetadata(minValue=1, maxValue=366)))
            if self._BinDuration == 1:
                qav['ClimatologyBinType'] = 'Daily'
            else:
                qav['ClimatologyBinType'] = '%iday' % self._BinDuration

        if binType.startswith('enso'):
            qav['ClimatologyBinType'] = _('ENSO_') + qav['ClimatologyBinType']

        # Copy the queryable attributes for the grid.

        gridQA = grid.GetAllQueryableAttributes()
        if gridQA is not None and len(gridQA) > 0:
            for a in gridQA:
                if grid.ParentCollection is None or grid.ParentCollection.GetQueryableAttribute(a.Name) is None:
                    qa.append(a)
                qav[a.Name] = grid.GetQueryableAttributeValue(a.Name)

        # Initialize the base class.

        super(ClimatologicalGridCollection, self).__init__(parentCollection=grid.ParentCollection, queryableAttributes=tuple(qa), queryableAttributeValues=qav)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        super(ClimatologicalGridCollection, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):

        # If we have not created the aggregate grids, do it now.

        from . import GridSlice, GridSliceCollection, AggregateGrid

        if self._AggregateGrids is None:
            self._AggregateGrids = []

            # If the bin type is 'cumulative', create a single AggregateGrid
            # for all of the time slices.

            if self._BinType == 'cumulative':
                self._AggregateGrids.append(AggregateGrid(GridSliceCollection(self._Grid, zQAName=None).QueryDatasets(reportProgress=False), self._Statistic, self._DisplayName, self._ReportProgress, parentCollection=self, queryableAttributeValues={'ClimatologyBinName': 'cumulative'}))

            # Otherwise, if the bin type is 'enso cumulative', create three
            # AggregateGrids, one for each ENSO phase.

            elif self._BinType == 'enso cumulative':
                ensoSlices = [[], [], []]       # Neutral, El Nino, La Nina
                
                for grid in GridSliceCollection(self._Grid, zQAName=None).QueryDatasets(reportProgress=False):
                    phase = self._GetONIPhaseForDate(grid.GetQueryableAttributeValue('DateTime'))       # Returns 0 for neutral, 1 for El Nino, -1 for La Nina, None if unknown
                    if phase is not None:
                        ensoSlices[phase].append(grid)

                binDefinitions = [[_('ENSO neutral phase cumulative climatological %(statistic)s of the %(dn)s') % {'dn': self._Grid.DisplayName, 'statistic': self._Statistic}, 0, 'neutral_cumulative'],
                                  [_('El Nino cumulative climatological %(statistic)s of the %(dn)s') % {'dn': self._Grid.DisplayName, 'statistic': self._Statistic}, 1, 'ElNino_cumulative'],
                                  [_('La Nina cumulative climatological %(statistic)s of the %(dn)s') % {'dn': self._Grid.DisplayName, 'statistic': self._Statistic}, -1, 'LaNina_cumulative']]
                
                for [displayName, phase, climatologyBinName] in binDefinitions:
                    if len(ensoSlices[phase]) > 0:
                        self._AggregateGrids.append(AggregateGrid(ensoSlices[phase], self._Statistic, displayName, self._ReportProgress, parentCollection=self, queryableAttributeValues={'ClimatologyBinName': climatologyBinName}))
                    else:
                        self._LogWarning(_('No data is available to create the %(dn)s.') % {'dn': displayName})

            # Otherwise, if the bin type is 'monthly' or 'enso monthly':

            elif self._BinType.endswith('monthly'):

                # Produce a list of [startMonthAndDay, endMonthAndDay]
                # records, one for each bin, sorted by endDay in ascending
                # order.

                numBins = int(round(12. / self._BinDuration))
                binMonthsAndDays = []
                startDateTime = datetime.datetime(2001, 1, 1) + datetime.timedelta(self._StartDayOfYear - 1)    # Use a non-leap year for this calculation.
                startMonth = startDateTime.month

                for i in range(numBins):
                    if i < numBins - 1:
                        if startMonth + self._BinDuration <= 12:
                            endMonthAndDay = int((datetime.datetime(2000, startMonth + self._BinDuration, startDateTime.day) - datetime.timedelta(1)).strftime('%m%d'))         # Use a leap year, to ensure that the last day of February is 29
                        else:
                            endMonthAndDay = int((datetime.datetime(2000, startMonth + self._BinDuration - 12, startDateTime.day) - datetime.timedelta(1)).strftime('%m%d'))    # Use a leap year, to ensure that the last day of February is 29
                    else:
                        endMonthAndDay = int((startDateTime - datetime.timedelta(1)).strftime('%m%d'))

                    binMonthsAndDays.append([startMonth*100 + startDateTime.day, endMonthAndDay])

                    startMonth += self._BinDuration
                    if startMonth > 12:
                        startMonth -= 12

                binMonthsAndDays.sort(key=lambda x: x[1])

                self._LogDebug(_('ClimatologicalGridCollection 0x%(id)016X: Using bin [startMonthAndDay, endMonthAndDay] definitions: %(binMonthsAndDays)s.'), {'id': id(self), 'binMonthsAndDays': str(binMonthsAndDays)})

                # Create GridSlice instances for each time slice of our grid
                # and sort them into monthly bins.

                binEndMonthsAndDays = [x[1] for x in binMonthsAndDays]
                bins = [[] for i in range(numBins)]

                for i, t in enumerate(self._Grid.CenterCoords['t']):
                    bin = bisect.bisect_left(binEndMonthsAndDays, t.month*100 + t.day)
                    if bin >= numBins:
                        bin = 0
                    bins[bin].append(GridSlice(self._Grid, tIndex=i, tQACoordType='center'))

                # If bin type is 'monthly' (not 'enso monthly'), just create
                # an AggregateGrid for each non-empty bin (maximum of 12).
                #
                # Otherwise (bin type is 'enso monthly'), further subdivide
                # each bin into three, one for each ENSO phase.

                for bin, grids in enumerate(bins):
                    queryableAttributeValues = {}
                    queryableAttributeValues['FirstMonth'] = binMonthsAndDays[bin][0] // 100
                    queryableAttributeValues['DayOfFirstMonth'] = binMonthsAndDays[bin][0] % 100
                    queryableAttributeValues['LastMonth'] = binMonthsAndDays[bin][1] // 100
                    queryableAttributeValues['DayOfLastMonth'] = binMonthsAndDays[bin][1] % 100

                    if self._BinDuration == 1:
                        binName = 'month%02i' % (binMonthsAndDays[bin][0] // 100)
                        displayName = _('%(month)s climatological %(statistic)s of the %(dn)s') % {'dn': self._Grid.DisplayName, 'month': datetime.datetime(2001, binMonthsAndDays[bin][0]//100, 1).strftime('%B'), 'statistic': self._Statistic}
                    else:
                        binName = 'months%02ito%02i' % (binMonthsAndDays[bin][0] // 100, binMonthsAndDays[bin][1] // 100)
                        displayName = _('months %(firstMonth)i-%(lastMonth)i climatological %(statistic)s of the %(dn)s') % {'dn': self._Grid.DisplayName, 'firstMonth': binMonthsAndDays[bin][0] // 100, 'lastMonth': binMonthsAndDays[bin][1] // 100, 'statistic': self._Statistic}

                    if self._BinType == 'monthly':
                        if len(grids) > 0:
                            queryableAttributeValues['ClimatologyBinName'] = binName
                            self._AggregateGrids.append(AggregateGrid(grids, self._Statistic, displayName, self._ReportProgress, parentCollection=self, queryableAttributeValues=queryableAttributeValues))
                        else:
                            self._LogWarning(_('No data is available to create the %(dn)s.') % {'dn': displayName})

                    else:
                        ensoSlices = [[], [], []]       # Neutral, El Nino, La Nina
                        
                        for grid in grids:
                            phase = self._GetONIPhaseForDate(grid.GetQueryableAttributeValue('DateTime'))       # Returns 0 for neutral, 1 for El Nino, -1 for La Nina, None if unknown
                            if phase is not None:
                                ensoSlices[phase].append(grid)

                        binDefinitions = [[_('ENSO neutral phase ') + displayName, 0, 'neutral_' + binName],
                                          [_('El Nino ') + displayName, 1, 'ElNino_' + binName],
                                          [_('La Nina ') + displayName, -1, 'LaNina_' + binName]]
                        
                        for [displayName, phase, climatologyBinName] in binDefinitions:
                            if len(ensoSlices[phase]) > 0:
                                qav = {}
                                qav.update(queryableAttributeValues)
                                qav['ClimatologyBinName'] = climatologyBinName
                                self._AggregateGrids.append(AggregateGrid(ensoSlices[phase], self._Statistic, displayName, self._ReportProgress, parentCollection=self, queryableAttributeValues=qav))
                            else:
                                self._LogWarning(_('No data is available to create the %(dn)s.') % {'dn': displayName})

            # Otherwise the bin type is 'daily' or 'enso daily':

            else:

                # Produce a list of [startDay, endDay] records, one for each
                # bin, sorted by endDay in ascending order.

                numBins = int(round(365. / self._BinDuration))
                binDays = []
                startDay = self._StartDayOfYear
                
                for i in range(numBins):
                    if i < numBins - 1:
                        endDay = startDay + self._BinDuration - 1
                    else:
                        endDay = self._StartDayOfYear - 1
                        
                    if endDay > 365:
                        endDay -= 365
                    elif endDay == 0 or endDay == 365:
                        endDay = 366

                    binDays.append([startDay, endDay])

                    startDay += self._BinDuration
                    if startDay >= 366:
                        startDay -= 365

                binDays.sort(key=lambda x: x[1])

                self._LogDebug(_('ClimatologicalGridCollection 0x%(id)016X: Using bin [startDay, endDay] definitions: %(binDays)s.'), {'id': id(self), 'binDays': str(binDays)})

                # Create GridSlice instances for each time slice of our grid
                # and sort them into the appropriate bins.

                binEndDays = [x[1] for x in binDays]
                bins = [[] for i in range(numBins)]

                for i, t in enumerate(self._Grid.CenterCoords['t']):
                    bin = bisect.bisect_left(binEndDays, t.timetuple()[7])
                    if bin >= numBins:
                        bin = 0
                    bins[bin].append(GridSlice(self._Grid, tIndex=i, tQACoordType='center'))

                # If bin type is 'daily' (not 'enso daily'), just create an
                # AggregateGrid for each non-empty bin.
                #
                # Otherwise (bin type is 'enso daily'), further subdivide each
                # bin into three, one for each ENSO phase.

                for bin, grids in enumerate(bins):
                    queryableAttributeValues = {}
                    queryableAttributeValues['FirstDay'] = binDays[bin][0]
                    queryableAttributeValues['LastDay'] = binDays[bin][1]

                    if self._BinDuration == 1:
                        binName = 'day%03i' % binDays[bin][0]
                        displayName = _('day %(day)03i climatological %(statistic)s of the %(dn)s') % {'dn': self._Grid.DisplayName, 'day': binDays[bin][0], 'statistic': self._Statistic}
                    else:
                        binName = 'days%03ito%03i' % (binDays[bin][0], binDays[bin][1])
                        displayName = _('days %(firstDay)03i-%(lastDay)03i climatological %(statistic)s of the %(dn)s') % {'dn': self._Grid.DisplayName, 'firstDay': binDays[bin][0], 'lastDay': binDays[bin][1], 'statistic': self._Statistic}

                    if self._BinType == 'daily':
                        if len(grids) > 0:
                            queryableAttributeValues['ClimatologyBinName'] = binName
                            self._AggregateGrids.append(AggregateGrid(grids, self._Statistic, displayName, self._ReportProgress, parentCollection=self, queryableAttributeValues=queryableAttributeValues))
                        else:
                            self._LogWarning(_('No data is available to create the %(dn)s.') % {'dn': displayName})

                    else:
                        ensoSlices = [[], [], []]       # Neutral, El Nino, La Nina
                        
                        for grid in grids:
                            phase = self._GetONIPhaseForDate(grid.GetQueryableAttributeValue('DateTime'))       # Returns 0 for neutral, 1 for El Nino, -1 for La Nina, None if unknown
                            if phase is not None:
                                ensoSlices[phase].append(grid)

                        binDefinitions = [[_('ENSO neutral phase ') + displayName, 0, 'neutral_' + binName],
                                          [_('El Nino ') + displayName, 1, 'ElNino_' + binName],
                                          [_('La Nina ') + displayName, -1, 'LaNina_' + binName]]
                        
                        for [displayName, phase, climatologyBinName] in binDefinitions:
                            if len(ensoSlices[phase]) > 0:
                                qav = {}
                                qav.update(queryableAttributeValues)
                                qav['ClimatologyBinName'] = climatologyBinName
                                self._AggregateGrids.append(AggregateGrid(ensoSlices[phase], self._Statistic, displayName, self._ReportProgress, parentCollection=self, queryableAttributeValues=qav))
                            else:
                                self._LogWarning(_('No data is available to create the %(dn)s.') % {'dn': displayName})

        # Execute the parsed expression against each of the aggregate grids,
        # returning all of those that match.

        results = []

        if parsedExpression is None:
            results.extend(self._AggregateGrids)
            if progressReporter is not None:
                progressReporter.ReportProgress(len(self._AggregateGrids))

        else:
            for aggregatedGrid in self._AggregateGrids:
                allAttrValues = {}
                for attr in aggregatedGrid.GetAllQueryableAttributes():
                    allAttrValues[attr.Name] = aggregatedGrid.GetQueryableAttributeValue(attr.Name)

                if parsedExpression.eval(allAttrValues):
                    results.append(aggregatedGrid)
                    if progressReporter is not None:
                        progressReporter.ReportProgress()

        return results

    def _GetONIPhaseForDate(self, dateTime):

        # If we have not built the ONI dictionary, do it now.

        if self._ONIDict is None:

            # Download a list of ONI values from NOAA ESRL.
            
            from GeoEco.DataProducts.NOAA.ClimateIndices import PSLClimateIndices

            self._LogInfo(_('Downloading Oceanic Nino Index (ONI) values from http://www.esrl.noaa.gov/psd/data/correlation/oni.data'))

            oniValues = PSLClimateIndices.UrlToList(r'http://www.esrl.noaa.gov/psd/data/correlation/oni.data')[0]

            # The oniValues may have several records on the end with None as
            # the ONI value. These are months for which the ONI cannot be
            # computed yet (e.g. because they are in the future). Remove these
            # from the list.

            while len(oniValues) > 0 and oniValues[-1][1] is None:
                del oniValues[-1]

            # Classify the ONI values into ENSO phases: 0 = neutral, 1 = El
            # Nino, -1 = La Nina.

            classifiedONIValues = PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList(oniValues)

            # Build our dictionary that allows the phase to be looked up for a
            # given year and month.

            self._ONIDict = {}

            for [d, oni, phase] in classifiedONIValues:
                if d.year not in self._ONIDict:
                    self._ONIDict[d.year] = {}
                self._ONIDict[d.year][d.month] = phase

        # Look up the ONI phase for this date.

        try:
            phase = self._ONIDict[dateTime.year][dateTime.month]
        except KeyError:
            phase = None

        self._LogDebug(_('ClimatologicalGridCollection 0x%(id)016X: ENSO phase of time slice %(dateTime)s = %(phase)s'), {'id': id(self), 'dateTime': str(dateTime), 'phase': str(phase)})

        return phase


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
