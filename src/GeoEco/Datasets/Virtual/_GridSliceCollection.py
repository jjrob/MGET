# _GridSliceCollection.py - A DatasetCollection representing the 2D slices
# of a 3D or 4D Grid (or 3D slices of a 4D Grid).
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Types import DateTimeTypeMetadata, FloatTypeMetadata

from .. import DatasetCollection, QueryableAttribute
from . import GridSlice


class GridSliceCollection(DatasetCollection):
    __doc__ = DynamicDocString()

    def __init__(self, grid, tQAName='DateTime', tQADisplayName=_('Time'), tQACoordType=None, zQAName='Depth', zQADisplayName=_('Depth'), zQACoordType='center', displayName=None):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        if not ('t' in grid.Dimensions or 'z' in grid.Dimensions):
            raise ValueError(_('Cannot construct a GridSliceCollection from %(dn)s because it does not have a t dimension or a z dimension.') % {'dn': grid.DisplayName})

        if not ('t' in grid.Dimensions and tQAName is not None or 'z' in grid.Dimensions and zQAName is not None):
            raise ValueError(_('Cannot construct a GridSliceCollection from %(dn)s. Although it has a t dimension and/or z dimension, it was not sliced by that (or those) dimensions. It must be sliced by at least one of them.') % {'dn': grid.DisplayName})

        if 't' in grid.Dimensions and tQAName is not None and tQADisplayName is None:
            raise TypeError(_('If a value is provided for tQAName, a value must also be provided for tQADisplayName.'))

        if 't' in grid.Dimensions and tQAName is not None and tQACoordType is None:
            if grid.GetLazyPropertyValue('TCornerCoordType') is not None:
                tQACoordType = grid.GetLazyPropertyValue('TCornerCoordType')
            else:
                raise TypeError(_('If a value is provided for tQAName, a value must also be provided for tQACoordType.'))

        if 'z' in grid.Dimensions and zQAName is not None and zQADisplayName is None:
            raise TypeError(_('If a value is provided for zQAName, a value must also be provided for zQADisplayName.'))

        if 'z' in grid.Dimensions and zQAName is not None and zQACoordType is None:
            raise TypeError(_('If a value is provided for zQAName, a value must also be provided for zQACoordType.'))

        # Initialize our properties.

        self._Grid = grid

        if 't' in grid.Dimensions and tQAName is not None:
            self._TQAName = tQAName
            self._TQADisplayName = tQADisplayName
            self._TQACoordType = tQACoordType
        else:
            self._TQAName = None
            self._TQADisplayName = None
            self._TQACoordType = None

        if 'z' in grid.Dimensions and zQAName is not None:
            self._ZQAName = zQAName
            self._ZQADisplayName = zQADisplayName
            self._ZQACoordType = zQACoordType
        else:
            self._ZQAName = None
            self._ZQADisplayName = None
            self._ZQACoordType = None

        if displayName is not None:
            self._DisplayName = displayName
        elif self._TQAName is not None and self._ZQAName is not None:
            self._DisplayName = _('%(tdn)s and %(zdn)s slices of %(dn)s') % {'tdn': self._TQADisplayName.lower(), 'zdn': self._ZQADisplayName.lower(), 'dn': self._Grid.DisplayName}
        elif self._TQAName is not None:
            self._DisplayName = _('%(tdn)s slices of %(dn)s') % {'tdn': self._TQADisplayName.lower(), 'dn': self._Grid.DisplayName}
        else:
            self._DisplayName = _('%(zdn)s slices of %(dn)s') % {'zdn': self._ZQADisplayName.lower(), 'dn': self._Grid.DisplayName}

        # For our queryable attributes, use all of those of the grid
        # plus the ones for the t and/or z dimensions.

        queryableAttributes = []
        if grid._QueryableAttributes is not None:
            queryableAttributes.extend(grid._QueryableAttributes)

        if self._TQAName is not None:
            queryableAttributes.append(QueryableAttribute(self._TQAName, self._TQADisplayName, DateTimeTypeMetadata()))

        if self._ZQAName is not None:
            queryableAttributes.append(QueryableAttribute(self._ZQAName, self._ZQADisplayName, FloatTypeMetadata()))

        # Initialize the base class.

        super(GridSliceCollection, self).__init__(parentCollection=grid.ParentCollection, queryableAttributes=tuple(queryableAttributes))

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        super(GridSliceCollection, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):
        return self._QueryGridSlices(parsedExpression, progressReporter)

    def _GetOldestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):
        datasets = self._QueryGridSlices(parsedExpression, numResults=1)
        if len(datasets) > 0:
            return datasets[0]
        return None

    def _GetNewestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):
        datasets = self._QueryGridSlices(parsedExpression, numResults=1, reverseOrder=True)
        if len(datasets) > 0:
            return datasets[0]
        return None

    def _QueryGridSlices(self, parsedExpression, progressReporter=None, numResults=None, reverseOrder=False):

        attrValues = {}
        for attr in self._QueryableAttributes:
            attrValues[attr.Name] = self._Grid.GetQueryableAttributeValue(attr.Name)

        # Iterate through the slices in the appropriate order, z
        # changing before t.

        results = []

        if self._TQAName is not None:
            maxT = self._Grid.Shape[0]
            if reverseOrder:
                t = maxT - 1
            else:
                t = 0
        else:
            t = None

        if self._ZQAName is not None:
            maxZ = self._Grid.Shape[self._Grid.Dimensions.index('z')]
            if reverseOrder:
                z = maxZ - 1
            else:
                z = 0
        else:
            z = None

        while (numResults is None or len(results) < numResults) and \
              (self._TQAName is None or (t >= 0 and t < maxT)) and \
              (self._ZQAName is None or (z >= 0 and z < maxZ)):

            # Set the t and/or z queryable attribute values for this
            # slice.

            if self._TQAName is not None:
                if self._TQACoordType == 'min':
                    tCoord = self._Grid.MinCoords['t', t]
                elif self._TQACoordType == 'center':
                    tCoord = self._Grid.CenterCoords['t', t]
                else:
                    tCoord = self._Grid.MaxCoords['t', t]
                attrValues[self._TQAName] = tCoord
                attrValues['Year'] = tCoord.year
                attrValues['Month'] = tCoord.month
                attrValues['Day'] = tCoord.day
                attrValues['Hour'] = tCoord.hour
                attrValues['Minute'] = tCoord.minute
                attrValues['Second'] = tCoord.second
                attrValues['DayOfYear'] = (datetime.datetime(tCoord.year, tCoord.month, tCoord.day) - datetime.datetime(tCoord.year, 1, 1)).days + 1
            else:
                tCoord = None

            if self._ZQAName is not None:
                if self._ZQACoordType == 'min':
                    zCoord = self._Grid.MinCoords['z', z]
                elif self._ZQACoordType == 'center':
                    zCoord = self._Grid.CenterCoords['z', z]
                else:
                    zCoord = self._Grid.MaxCoords['z', z]
                attrValues[self._ZQAName] = zCoord
            else:
                zCoord = None

            # Evaluate the expression for this slice. The only thing
            # that will be different about this slice compared to
            # others is the t and/or z queryable attribute values.

            results.extend(self._EvaluateExpressionForSlice(parsedExpression, attrValues, t, z, tCoord, zCoord, progressReporter))

            # Go on to the next slice.

            if self._ZQAName is not None:
                if reverseOrder:
                    z -= 1
                else:
                    z += 1

            if self._TQAName is not None and (self._ZQAName is None or z < 0 or z >= maxZ):
                if reverseOrder:
                    if self._ZQAName is not None:
                        z = maxZ - 1
                    t -= 1
                else:
                    if self._ZQAName is not None:
                        z = 0
                    t += 1

        return results

    def _EvaluateExpressionForSlice(self, parsedExpression, attrValues, t, z, tCoord, zCoord, progressReporter):

        if parsedExpression is not None:
            try:
                result = parsedExpression.eval(attrValues)
            except Exception as e:
                return []
        else:
            result = True

        if result is None or result:
            if self._TQAName is not None and self._ZQAName is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for t=%(t)s (%(tCoord)s), z=%(z)i (%(zCoord)s): %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 't': t, 'z': z, 'tCoord': str(tCoord), 'zCoord': repr(zCoord), 'result': repr(result)})
            elif self._TQAName is not None:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for t=%(t)s (%(tCoord)s): %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 't': t, 'tCoord': str(tCoord), 'result': repr(result)})
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for z=%(z)i (%(zCoord)s): %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 'z': z, 'zCoord': repr(zCoord), 'result': repr(result)})

        if result:
            grids = [GridSlice(self._Grid, tIndex=t, zIndex=z, tQAName=self._TQAName, tQADisplayName=self._TQADisplayName, tQACoordType=self._TQACoordType, zQAName=self._ZQAName, zQADisplayName=self._ZQADisplayName, zQACoordType=self._ZQACoordType)]
            if progressReporter is not None:
                progressReporter.ReportProgress()
        else:
            grids = []

        return grids


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
