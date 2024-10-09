# _AggregateGrid.py - A Grid built by statistically summarizing a list of
# Grids on a per-cell basis.
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


class AggregateGrid(Grid):
    __doc__ = DynamicDocString()

    def _GetReportProgress(self):
        return self._ReportProgress

    def _SetReportProgress(self, value):
        self.__doc__.Obj.ValidatePropertyAssignment()
        self._ReportProgress = value

    ReportProgress = property(_GetReportProgress, _SetReportProgress, doc=DynamicDocString())

    def __init__(self, grids, statistic, displayName, reportProgress=False, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()
        
        # Initialize our properties.
        
        self._Grids = []
        self._Grids.extend(grids)
        self._Statistic = statistic
        self._DisplayName = displayName
        self._ReportProgress = reportProgress
        self._ReportedStartMessage = False

        # Initialize the base class.
        
        super(AggregateGrid, self).__init__(parentCollection=parentCollection, queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

    def _Close(self):
        if hasattr(self, '_Grids') and self._Grids is not None:
            for grid in self._Grids:
                grid.Close()
        super(AggregateGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the caller requested PhysicalDimensions or
        # PhysicalDimensionsFlipped, return idealized values, as the
        # transposing and flipping is handled by the contained grid.

        if name == 'PhysicalDimensions':
            return self._Grids[0].Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self._Grids[0].Dimensions))

        # If the caller requested the UnscaledDataType or UnscaledNoDataValue,
        # calculate and return them.
        
        if name == 'UnscaledDataType':

            # For COUNT, return the smallest integer type that is guaranteed
            # hold the largest possible value.
            
            if self._Statistic == 'count':
                if len(self._Grids) < 256:
                    return 'uint8'
                if len(self._Grids) < 65536:
                    return 'uint16'
                return 'int32'

            # For MIN, MAX, and RANGE, return the data type of the first grid.
            # This is guaranteed to work if all of the grids have this type.
            # If they do not, it may still work but there is the possibility
            # of overflow or underflow. If it happens, we will detect it and
            # fail.

            if self._Statistic in ['minimum', 'maximum', 'range']:
                return self._Grids[0].DataType

            # For all others, return float32, unless the first grid is
            # float64, in which case return float64.

            if self._Grids[0].DataType == 'float64':
                return 'float64'
            return 'float32'

        if name == 'UnscaledNoDataValue':

            # For COUNT, return 0.

            if self._Statistic == 'count':
                if self.DataType in ['float32', 'float64']:
                    return 0.
                return 0

            # For MIN, MAX, and RANGE, return the NoData value of the first
            # grid.

            if self._Statistic in ['minimum', 'maximum', 'range']:
                return self._Grids[0].NoDataValue

            # For all others, return the smallest representable floating point
            # number:
            #
            # >>> float(numpy.finfo('float32').min)
            # -3.4028234663852886e+038
            # >>> float(numpy.finfo('float64').min)
            # -1.7976931348623157e+308

            import numpy

            if self.DataType == 'float32':
                return float(numpy.finfo('float32').min)
            return float(numpy.finfo('float64').min)

        # If the caller requested one of the properties related to scaling,
        # return None.

        if name in ['ScaledDataType', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # Otherwise use the value of the property from the first grid.
        
        return self._Grids[0].GetLazyPropertyValue(name)

    @classmethod
    def _TestCapability(cls, capability):
        return cls._Grids[0]._TestCapability(capability)

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        return self._Grids[0]._GetCoords(coord, coordNum, slices, sliceDims, fixedIncrementOffset)

    def _ReadNumpyArray(self, sliceList):
        import numpy

        # Initialize arrays needed to perform the aggregation.

        shape = [s.stop - s.start for s in sliceList]
        count = numpy.zeros(shape, dtype='int32')

        if self._Statistic in ['minimum', 'range']:
            smallest = numpy.zeros(shape, dtype=str(self.DataType))
            if self.DataType[0] == 'f':
                smallest += numpy.finfo(str(self.DataType)).max
            else:
                smallest += numpy.iinfo(str(self.DataType)).max
                
        if self._Statistic in ['maximum', 'range']:
            largest = numpy.zeros(shape, dtype=str(self.DataType))
            if self.DataType[0] == 'f':
                largest += numpy.finfo(str(self.DataType)).min
            else:
                largest += numpy.iinfo(str(self.DataType)).min

        if self._Statistic in ['sum', 'mean']:
            sum_ = numpy.zeros(shape, dtype=str(self.DataType))

        if self._Statistic == 'standard_deviation':
            mean = numpy.zeros(shape, dtype=str(self.DataType))
            M2 = numpy.zeros(shape, dtype=str(self.DataType))

        # If we were asked to report progress and the caller is requesting the
        # entire grid, create a progress reporter. If they're only requesting
        # part of the grid, do not create a progress reporter, even if they
        # asked for one, because it is highly likely that they'll just ask for
        # another part of it in a moment, which would cause us to report
        # progress again, and again...

        if self._ReportProgress:
            if not self._ReportedStartMessage:
                self._LogInfo(_('Aggregating %(grids)i grids to create the %(dn)s.') % {'grids': len(self._Grids), 'dn': self._DisplayName})

            if tuple(shape) == self.Shape:
                from GeoEco.Logging import ProgressReporter
                progressReporter = ProgressReporter(progressMessage1=_('Still aggregating: %(elapsed)s elapsed, %(opsCompleted)i grids aggregated, %(perOp)s per grid, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                    completionMessage=_('Aggregation complete: %(elapsed)s elapsed, %(opsCompleted)i grids aggregated, %(perOp)s per grid.'),
                                                    abortedMessage=_('Aggregation stopped before all grids were aggregated: %(elapsed)s elapsed, %(opsCompleted)i grids aggregated, %(perOp)s per grid, %(opsIncomplete)i not aggregated.'),
                                                    loggingChannel='GeoEco.Datasets',
                                                    arcGISProgressorLabel=_('Aggregating %(count)i grids') % {'count': len(self._Grids)} )
                progressReporter.Start(len(self._Grids))
            else:
                self._ReportedStartMessage = True
                progressReporter = None
        else:
            progressReporter = None

        # Iterate through the grids, aggregating their values into the
        # appropriate arrays we allocated.

        try:
            for i in range(len(self._Grids)):

                # First validate that this grid has the same dimensions and
                # shape as the first grid and a compatible data type.

                if self._Grids[i].Dimensions != self._Grids[0].Dimensions:
                    raise ValueError(_('Cannot aggregate %(dn1)s and %(dn2)s because they have different dimensions. The first grid has dimensions %(dim1)s and the second has dimensions %(dim2)s.' ) % {'dn1': self._Grids[0].DisplayName, 'dn2': self._Grids[1].DisplayName, 'dim1': self._Grids[0].Dimensions, 'dim2': self._Grids[1].Dimensions})

                if self._Grids[i].Shape != self._Grids[0].Shape:
                    raise ValueError(_('Cannot aggregate %(dn1)s and %(dn2)s because they have different shapes. The first grid has the shape %(shape1)s and the second has the shape %(shape2)s.' ) % {'dn1': self._Grids[0].DisplayName, 'dn2': self._Grids[1].DisplayName, 'shape1': self._Grids[0].Shape, 'shape2': self._Grids[1].Shape})

                if self._Statistic in ['minimum', 'maximum', 'range'] and not numpy.can_cast(str(self._Grids[i].DataType), str(self._Grids[0].DataType)):
                    raise ValueError(_('Cannot aggregate %(dn1)s and %(dn2)s because the second grid\'s data type, %(dt2)s, cannot be fully represented by the first grid\'s data type, %(dt1)s. Recreate the grids with the same data type and try again.' ) % {'dn1': self._Grids[0].DisplayName, 'dn2': self._Grids[1].DisplayName, 'dt1': self._Grids[i].DataType, 'dt2': self._Grids[i].DataType})

                # Now aggregate this grid.
                
                data = self._Grids[i].Data.__getitem__(tuple(sliceList))

                if self._Grids[i].NoDataValue is not None:
                    hasData = numpy.invert(Grid.numpy_equal_nan(data, self._Grids[i].NoDataValue))
                else:
                    hasData = numpy.ones(data.shape, dtype=bool)

                count += numpy.asarray(hasData, dtype='int32')

                if self._Statistic in ['minimum', 'range']:
                    isSmaller = numpy.logical_and(hasData, data < smallest)
                    smallest[isSmaller] = data[isSmaller]
                    
                if self._Statistic in ['maximum', 'range']:
                    isLarger = numpy.logical_and(hasData, data > largest)
                    largest[isLarger] = data[isLarger]

                if self._Statistic in ['sum', 'mean']:
                    sum_[hasData] += data[hasData]

                # To avoid having to make two passes through the grids to
                # calculate the standard deviation, we use an online
                # algorithm. See "On-line algorithm" in
                # http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance.

                if self._Statistic == 'standard_deviation':
                    delta = data[hasData] - mean[hasData]
                    mean[hasData] += delta/count[hasData]
                    M2[hasData] += delta*(data[hasData] - mean[hasData])

                # Report progress.

                if progressReporter is not None:
                    progressReporter.ReportProgress()

        except:
            if progressReporter is not None:
                progressReporter.Stop()
            raise

        # Calculate and return the result.

        if self._Statistic == 'count':
            count[count == 0] = self.NoDataValue
            return count, self.NoDataValue

        if self._Statistic == 'minimum':
            if self.NoDataValue is not None:
                smallest[count == 0] = self.NoDataValue
            return smallest, self.NoDataValue

        if self._Statistic == 'maximum':
            if self.NoDataValue is not None:
                largest[count == 0] = self.NoDataValue
            return largest, self.NoDataValue

        if self._Statistic == 'range':
            if self.NoDataValue is not None:
                largest[count == 0] = 0      # Try to prevent overflow/underflow warning when NoDataValue is large
                smallest[count == 0] = 0
            result = largest - smallest
            if self.NoDataValue is not None:
                result[count == 0] = self.NoDataValue
            return result, self.NoDataValue

        if self._Statistic == 'sum':
            sum_[count == 0] = self.NoDataValue
            return sum_, self.NoDataValue

        if self._Statistic == 'mean':
            mean = numpy.zeros(shape, dtype=str(self.DataType))
            mean += self.NoDataValue
            hasData = count >= 1
            mean[hasData] = sum_[hasData] / count[hasData]
            return mean, self.NoDataValue

        stdev = numpy.zeros(shape, dtype=str(self.DataType))
        stdev += self.NoDataValue
        hasData = count >= 2
        stdev[hasData] = (M2[hasData]/(count[hasData] - 1))**0.5
        return stdev, self.NoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
