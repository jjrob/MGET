# _RotatedGlobalGrid.py - A Grid that rotates a Grid longitudinally.
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


class RotatedGlobalGrid(Grid):
    __doc__ = DynamicDocString()

    def __init__(self, grid, rotationOffset, rotationUnits='Map units'):
        self.__class__.__doc__.Obj.ValidateMethodInvocation()

        # Validate that the grid has a constant x increment.

        if grid.CoordDependencies[-1] is not None:
            raise ValueError(_('The provided grid, %(dn)s, does not have a constant x increment. The current implementation of RotatedGlobalGrid only supports grids with constant x increments.') % {'dn': grid.DisplayName})

        # Initialize our properties.

        self._Grid = grid
        self._XRotationType = rotationUnits

        if self._XRotationType == 'cells':
            self._XRotationInCells = int(round(rotationOffset))
            self._XRotationInMapUnits = self._XRotationInCells * self._Grid.CoordIncrements[-1]
        else:
            self._XRotationInCells = int(round(rotationOffset / self._Grid.CoordIncrements[-1]))
            self._XRotationInMapUnits = self._XRotationInCells * self._Grid.CoordIncrements[-1]

        self._DisplayName = _('%(dn)s, rotated about the polar axis by %(cells)i cells (%(mapUnits)g map units)') % {'dn': self._Grid.DisplayName, 'cells': self._XRotationInCells, 'mapUnits': self._XRotationInMapUnits}

        # Determine lazy properties that we can cheaply calculate now.
        # Transposing and flipping the raw data is handled by the contained
        # grid, so we use idealized PhysicalDimensions and set
        # PhysicalDimensionsFlipped to False for all dimensions.

        lazyPropertyValues = {'PhysicalDimensions': self._Grid.Dimensions,
                              'PhysicalDimensionsFlipped': tuple([False] * len(self._Grid.Dimensions))}

        # Determine whether the contained grid uses a geographic coordinate
        # system or a projected coordinate system. If it is geographic, we
        # will use the same coordinate system  as that grid but a different x
        # corner coordinate. To do this, we have to override the CornerCoords
        # lazy property. This task is complicated because we have to expose
        # the same queryable attributes and have the same parent collection,
        # and those could be used to set the corner coordinates. Thus we can't
        # just wait to be called at _GetLazyPropertyPhysicalValue to return
        # CornerCoords because if a queryable attribute sets it, we won't ever
        # be called.
        #
        # To work around this, see if CornerCoords available from the
        # contained grid without accessing physical storage (i.e. it is
        # already cached by the contained grid or is set by a queryable
        # attribute of it or its parents). If it is, then set our modified
        # value now. Otherwise, do nothing; we know that we'll be called at
        # _GetLazyPropertyPhysicalValue when it is needed, and we can retrieve
        # and modify the values from the contained grid at that point.

        try:
            oldCornerCoords = self._Grid.GetLazyPropertyValue('CornerCoords', allowPhysicalValue=False)
            sr = self._Grid.GetSpatialReference('obj').Clone()

            if sr.IsGeographic() or sr.GetNormProjParm('central_meridian', 123456.) == 123456.:
                lazyPropertyValues['SpatialReference'] = sr
                if oldCornerCoords is not None:
                    lazyPropertyValues['CornerCoords'] = tuple(list(oldCornerCoords[:-1]) + [oldCornerCoords[-1] + self._XRotationInMapUnits])

            # If the contained grid uses a projected coordinate
            # system, we will use the same CornerCoords but change the
            # central_meridian to accomplish the rotation.

            else:
                srAtPrimeMeridian = sr.Clone()
                srAtPrimeMeridian.SetNormProjParm('central_meridian', 0.)
                srGeographic = self._osr().SpatialReference()
                srGeographic.CopyGeogCSFrom(sr)
                transformer = self._osr().CoordinateTransformation(srAtPrimeMeridian, srGeographic)
                offsetToCentralMeridian = transformer.TransformPoint(self._XRotationInMapUnits, 0.)[0]

                sr.SetNormProjParm('central_meridian', sr.GetNormProjParm('central_meridian') + offsetToCentralMeridian)
                lazyPropertyValues['SpatialReference'] = sr
                if oldCornerCoords is not None:
                    lazyPropertyValues['CornerCoords'] = oldCornerCoords
                
        except:
            self._gdal().ErrorReset()
            raise

        # Initialize the base class.
        
        queryableAttributes = tuple(grid.GetAllQueryableAttributes())
        
        queryableAttributeValues = {}
        for qa in queryableAttributes:
            queryableAttributeValues[qa.Name] = grid.GetQueryableAttributeValue(qa.Name)
        
        super(RotatedGlobalGrid, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues)

    def _Close(self):
        if hasattr(self, '_Grid') and self._Grid is not None:
            self._Grid.Close()
        super(RotatedGlobalGrid, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):
        if name == 'CornerCoords':
            oldCornerCoords = self._Grid.GetLazyPropertyValue('CornerCoords')
            sr = self._Grid.GetSpatialReference('obj')
            if sr.IsGeographic() or sr.GetNormProjParm('central_meridian', 123456.) == 123456.:
                return tuple(list(oldCornerCoords[:-1]) + [oldCornerCoords[-1] + self._XRotationInMapUnits])
            return oldCornerCoords

        return self._Grid.GetLazyPropertyValue(name)

    @classmethod
    def _TestCapability(cls, capability):
        if capability in ['setspatialreference']:
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return cls._Grid._TestCapability(capability)

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        return self._Grid._GetCoords(coord, coordNum, slices, sliceDims, fixedIncrementOffset)

    def _ReadNumpyArray(self, sliceList):

        # Convert the indices of the requested slice to account for
        # the rotation.

        xShape = self.Shape[-1]
        rotationInCells = self._XRotationInCells % xShape
        xStart = (sliceList[-1].start + rotationInCells) % xShape
        xStop = (sliceList[-1].stop - 1 + rotationInCells) % xShape + 1

        # If the stop index is greater than the start index, it means
        # the requested slice does not straddle the left and right
        # edges of the contained grid, and we can retrieve the data
        # with a single request.

        if xStop > xStart:
            data = self._Grid.UnscaledData.__getitem__(tuple(list(sliceList[:-1]) + [slice(xStart, xStop)]))

        # Otherwise (the requested slice straddles), retrieve the two
        # slabs of data and concatenate them together.

        else:
            import numpy
            data = numpy.concatenate((self._Grid.UnscaledData.__getitem__(tuple(list(sliceList[:-1]) + [slice(xStart, xShape)])),
                                      self._Grid.UnscaledData.__getitem__(tuple(list(sliceList[:-1]) + [slice(0, xStop)]))),
                                     axis=len(self.Dimensions) - 1)

        # Return the data and self.UnscaledNoDataValue.

        return data, self.UnscaledNoDataValue


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
