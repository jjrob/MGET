# _CannyEdgeGrid.py - A Grid that represents the edges in another Grid using
# the Canny edge detection algorithm.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Matlab import SharedMatlabWorkerProcess

from .. import Grid
from . import GridSlice


_CannyEdgesOverview = (
"""To run this tool, you either must have MATLAB R2024b or MATLAB Runtime R2024b
installed. The MATLAB Runtime is free and may be downloaded from
https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html.
Please follow the installation instructions carefully. Version R2024b must be
used; other versions will not work. MATLAB Runtime allows multiple versions
can be installed at the same time.

The Canny edge detection algorithm is a generic, widely-used algorithm for
delineating edges between objects in digital images. The algorithm may be
successfully applied to a wide variety of problems, including the problem of
detecting fronts between water masses. Canny (1986) describes the algorithm in
full detail, including its mathematical derivation. Some readers may find the
paper difficult due to its length and technical detail. Shorter, more
approachable descriptions may be found by searching the Internet for "Canny
algorithm".""")


class CannyEdgeGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, highThreshold=None, lowThreshold=None, sigma=1.4142, minSize=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if grid.DataType not in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:
            raise TypeError(_('To detect edges with the Canny edge detector, the input grid must use one of the following data types: int8, uint8, int16, uint16, int32, uint32, float32, float64.'))

        if lowThreshold is not None and highThreshold is None:
            self._LogWarning(_('A low threshold was specified to the Canny edge detector without a high threshold also being specified. This is not allowed. The low threshold will be ignored.'))
            lowThreshold = None

        if highThreshold is not None and lowThreshold is not None and lowThreshold >= highThreshold:
            raise ValueError(_('The low threshold was greater than or equal to the high threshold. The Canny edge detector requires that the low threshold be less than the high threshold.'))
        
        # Initialize our properties.
        
        self._Grid = grid
        self._TempDir = None
        self._MatlabWorkerProcess = None
        self._HighThreshold = highThreshold
        self._LowThreshold = lowThreshold
        self._Sigma = sigma
        self._MinSize = minSize
        self._ThresholdsDict = {}

        self._DisplayName = _('Canny edges (high threshold=%(highThreshold)r, low threshold=%(lowThreshold)r, sigma=%(sigma)r, min size=%(minSize)r) in %(dn)s') % {'dn': grid.DisplayName, 'highThreshold': highThreshold, 'lowThreshold': lowThreshold, 'sigma': sigma, 'minSize': minSize}

        # Initialize the base class.

        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(CannyEdgeGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues)

    def _GetLazyPropertyPhysicalValue(self, name):

        # If the caller requested PhysicalDimensions or
        # PhysicalDimensionsFlipped, return idealized values, as any
        # transposing and flipping is handled by the contained grid.

        if name == 'PhysicalDimensions':
            return self._Grid.Dimensions

        if name == 'PhysicalDimensionsFlipped':
            return tuple([False] * len(self._Grid.Dimensions))

        # We determine the data type and no data values.

        if name == 'UnscaledDataType':
            return 'uint8'
        
        if name == 'UnscaledNoDataValue':
            return 255

        if name in ['ScaledDataType', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # Otherwise use the value of the property from the grid.
        
        return self._Grid.GetLazyPropertyValue(name)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        if hasattr(self, '_MatlabWorkerProcess') and self._MatlabWorkerProcess is not None:
            self._MatlabWorkerProcess = None   # Do not call _MatlabWorkerProcess.Stop() here. We want the shared process to keep running.
        self._TempDir = None
        super(CannyEdgeGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

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

        # Iterate through each requested 2D slice, detect edges, and write
        # edges to a file in the temporary directory, if we have not done so
        # already. If we catch an exception, call _Close() to delete the
        # temporary directory.

        import numpy

        try:
            if len(self.Dimensions) == 2:
                slices = [(sliceList[0], sliceList[1])]
            elif len(self.Dimensions) == 3:
                slices = [(d, sliceList[1], sliceList[2]) for d in range(sliceList[0].start, sliceList[0].stop)]
            else:
                slices = [(d1, d2, sliceList[2], sliceList[3]) for d1 in range(sliceList[0].start, sliceList[0].stop) for d2 in range(sliceList[1].start, sliceList[1].stop)]

            for s in slices:
                if self._TempDir is not None:
                    edgesFile = os.path.join(self._TempDir, 'slice_%s_edges.dat' % '_'.join(map(str, s[:len(self.Dimensions) - 2])))
                    
                if self._TempDir is None or not os.path.exists(edgesFile):

                    # Extract the 2D slice.

                    if self.Dimensions == 'yx':
                        grid = self._Grid
                    elif self.Dimensions == 'zyx':
                        grid = GridSlice(self._Grid, zIndex=s[0])
                    elif self.Dimensions == 'tyx':
                        grid = GridSlice(self._Grid, tIndex=s[0])
                    else:
                        grid = GridSlice(self._Grid, tIndex=s[0], zIndex=s[1])

                    # Even though the caller might only be interested in part
                    # of the 2D slice, we have to detect fronts in the entire
                    # slice because cells outside their area of interest can
                    # influence edges inside their area of interest. Extract
                    # the entire slice to a numpy array and change the NoData
                    # value to NaN.

                    data = grid.Data[:]
                    data[Grid.numpy_equal_nan(data, grid.NoDataValue)] = numpy.nan

                    # If we have not created the temporary directory or
                    # instantiated MatlabWorkerProcess, do it now.

                    if self._TempDir is None:
                        self._TempDir = self._CreateTempDirectory()

                    if self._MatlabWorkerProcess is None:
                        self._MatlabWorkerProcess = SharedMatlabWorkerProcess.GetWorkerProcess()

                    # Detect edges in the numpy array with the MATLAB function.

                    edgesFile = os.path.join(self._TempDir, 'slice_%s_edges.dat' % '_'.join(map(str, s[:len(self.Dimensions) - 2])))
                    if self._HighThreshold is None and self._LowThreshold is None:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Creating %(edgesFile)s from slice %(slice)r of %(dn)s, sigma=%(sigma)g, minSize=%(minSize)s. Thresholds will be computed.'), {'class': self.__class__.__name__, 'id': id(self), 'edgesFile': edgesFile, 'slice': s, 'dn': self._Grid.DisplayName, 'sigma': self._Sigma, 'minSize': self._MinSize})
                    elif self._LowThreshold is None:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Creating %(edgesFile)s from slice %(slice)r of %(dn)s, high threshold=%(ht)g, sigma=%(sigma)g, minSize=%(minSize)s. The low threshold will be computed.'), {'class': self.__class__.__name__, 'id': id(self), 'edgesFile': edgesFile, 'slice': s, 'dn': self._Grid.DisplayName, 'sigma': self._Sigma, 'minSize': self._MinSize, 'ht': self._HighThreshold})
                    else:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Creating %(edgesFile)s from slice %(slice)r of %(dn)s, high threshold=%(ht)g, low threshold=%(lt)g, sigma=%(sigma)g, minSize=%(minSize)s.'), {'class': self.__class__.__name__, 'id': id(self), 'edgesFile': edgesFile, 'slice': s, 'dn': self._Grid.DisplayName, 'sigma': self._Sigma, 'minSize': self._MinSize, 'ht': self._HighThreshold, 'lt': self._LowThreshold})

                    edges, lowThresh, highThresh = self._MatlabWorkerProcess.CannyEdges(
                                                       data,
                                                       self._LowThreshold if self._LowThreshold is not None else -1,
                                                       self._HighThreshold if self._HighThreshold is not None else -1,
                                                       self._Sigma if self._Sigma is not None else -1,
                                                       float(self._MinSize) if self._MinSize is not None else -1
                                                   )

                    # Log the thresholds.

                    if self._HighThreshold is None and self._LowThreshold is None:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Computed high threshold=%(ht)g, low threshold=%(lt)g.'), {'class': self.__class__.__name__, 'id': id(self), 'edgesFile': edgesFile, 'slice': s, 'dn': self._Grid.DisplayName, 'ht': highThresh, 'lt': lowThresh})
                    elif self._LowThreshold is None:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Computed low threshold=%(lt)g.'), {'class': self.__class__.__name__, 'id': id(self), 'edgesFile': edgesFile, 'slice': s, 'dn': self._Grid.DisplayName, 'lt': lowThresh})

                    # In the returned array, convert NaN to the NoDataValue.
                    # Then cast it to our preferred data type.

                    edges[numpy.isnan(edges)] = self.NoDataValue
                    edges = numpy.asarray(edges, dtype=self.DataType) 

                    # Write the returned array to the temporary directory.

                    edges.tofile(edgesFile)

        except:
            self._Close()
            raise

        # Allocate an array to return.

        data = numpy.zeros([s.stop-s.start for s in sliceList], dtype=str(self.UnscaledDataType))

        # Read the detected edges from the temporary directory and write them
        # to the array.

        for s in slices:
            edgesFile = os.path.join(self._TempDir, 'slice_%s_edges.dat' % '_'.join(map(str, s[:len(self.Dimensions) - 2])))
            edgesSlice = numpy.fromfile(edgesFile, str(self.DataType)).reshape(self.Shape[-2], self.Shape[-1])

            if len(self.Dimensions) == 2:
                data.__setitem__((slice(None, None, None), slice(None, None, None)), edgesSlice.__getitem__(s[-2:]))
            elif len(self.Dimensions) == 3:
                data.__setitem__((slice(s[0] - slices[0][0], s[0] - slices[0][0] + 1, None), slice(None, None, None), slice(None, None, None)), edgesSlice.__getitem__(s[-2:]))
            else:
                data.__setitem__((slice(s[0] - slices[0][0], s[0] - slices[0][0] + 1, None), slice(s[1] - slices[1][0], s[1] - slices[1][0] + 1, None), slice(None, None, None), slice(None, None, None)), edgesSlice.__getitem__(s[-2:]))

        # Return successfully.

        return data, self.NoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
