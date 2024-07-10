# _NumpyGridMetadata.py - Metadata for classes defined in _NumpyGrid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from . import CollectibleObject, Grid
from ._NumpyGrid import NumpyGrid


###############################################################################
# Metadata: NumpyGrid class
###############################################################################

AddClassMetadata(NumpyGrid,
    module=__package__,
    shortDescription=_('Wraps a :class:`numpy.ndarray` in the :class:`Grid` interface.'),
    longDescription=_(
""":class:`NumpyGrid` provides a convenient mechanism for modifying a
:class:`Grid`. The typical usage pattern is:

1. Obtain a :class:`Grid` instance from somewhere (e.g. a
   :class:`~GeoEco.Datasets.GDAL.GDALRasterBand` or an
   :class:`~GeoEco.Datasets.ArcGIS.ArcGISRasterBand` instance).

2. Call :func:`NumpyGrid.CreateFromGrid` to wrap the :class:`Grid` in a
   :class:`NumpyGrid`.

3. Get and set slices of the :attr:`~NumpyGrid.Data` property of the
   :class:`NumpyGrid`.

4. Import the :class:`NumpyGrid` into the desired :class:`DatasetCollection`.
"""))

# Constructor: NumpyGrid.__init__

AddMethodMetadata(NumpyGrid.__init__,
    shortDescription=_('NumpyGrid constructor.'))

AddArgumentMetadata(NumpyGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=NumpyGrid),
    description=_(':class:`%s` instance.') % NumpyGrid.__name__)

AddArgumentMetadata(NumpyGrid.__init__, 'numpyArray',
    typeMetadata=NumPyArrayTypeMetadata(allowedDTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']),
    description=_(':class:`numpy.ndarray` to wrap. This array must have 2, 3, or 4 dimensions. Note that the array is not copied. Data written to :attr:`Data` will written to the original array provided by the caller.'))

AddArgumentMetadata(NumpyGrid.__init__, 'displayName',
    typeMetadata=Grid.DisplayName.__doc__.Obj.Type,
    description=Grid.DisplayName.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'spatialReference',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('Spatial reference of the requested type as an :py:class:`osgeo.osr.SpatialReference` instance, or :py:data:`None` to indicate the spatial reference is unknown.'))

AddArgumentMetadata(NumpyGrid.__init__, 'dimensions',
    typeMetadata=Grid.Dimensions.__doc__.Obj.Type,
    description=Grid.Dimensions.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'coordIncrements',
    typeMetadata=TupleTypeMetadata(elementType=FloatTypeMetadata(canBeNone=True, mustBeGreaterThan=0.), mustBeSameLengthAsArgument='dimensions'),
    description=_('Coordinate increment for each dimension. :py:data:`None` for dimensions that do not have a constant coordinate increment.'))

AddArgumentMetadata(NumpyGrid.__init__, 'cornerCoords',
    typeMetadata=TupleTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=True), mustBeSameLengthAsArgument='dimensions'),
    description=_('The center coordinates of the lower-left cell of this grid.'))

AddArgumentMetadata(NumpyGrid.__init__, 'unscaledNoDataValue',
    typeMetadata=Grid.UnscaledNoDataValue.__doc__.Obj.Type,
    description=Grid.UnscaledNoDataValue.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'tIncrementUnit',
    typeMetadata=Grid.TIncrementUnit.__doc__.Obj.Type,
    description=Grid.TIncrementUnit.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'tSemiRegularity',
    typeMetadata=Grid.TSemiRegularity.__doc__.Obj.Type,
    description=Grid.TSemiRegularity.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'tCountPerSemiRegularPeriod',
    typeMetadata=Grid.TCountPerSemiRegularPeriod.__doc__.Obj.Type,
    description=Grid.TCountPerSemiRegularPeriod.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'tCornerCoordType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['min', 'center', 'max'], canBeNone=True),
    description=_('Indicates whether the ``t`` coordinate of `cornerCoords` is the minimum, center, or maximum coordinate for the cell. Ignored if `dimensions` does not have a ``t`` coordinate.'))

AddArgumentMetadata(NumpyGrid.__init__, 'tOffsetFromParsedTime',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_('Number of seconds to to add to ``t`` coordinates after computing them from `cornerCoords` and `coordIncrements`. Used for datasets that round off their times, e.g. the file name contains the year, month, and day, but the time slices do not start at midnight. If :py:data:`None`, nothing will be added.'))

AddArgumentMetadata(NumpyGrid.__init__, 'coordDependencies',
    typeMetadata=TupleTypeMetadata(elementType=UnicodeStringTypeMetadata(allowedValues=['x', 'y', 'z', 't', 'yx', 'zx', 'tx', 'ty', 'zy', 'tz', 'zyx', 'tyx', 'tzy'], canBeNone=True), mustBeSameLengthAsArgument='dimensions', canBeNone=True),
    description=_('Dimensions that each dimension depends on for determining its coordinates. :py:data:`None` for dimensions that have a constant coordinate increment.'))

AddArgumentMetadata(NumpyGrid.__init__, 'physicalDimensions',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['yx', 'xy', 'zyx', 'zxy', 'yzx', 'yxz', 'xzy', 'xyz', 'tyx', 'txy', 'ytx', 'yxt', 'xty', 'xyt', 'tzyx', 'tzxy', 'tyzx', 'tyxz', 'txzy', 'txyz', 'ztyx', 'ztxy', 'zytx', 'zyxt', 'zxty', 'zxyt', 'ytzx', 'ytxz', 'yztx', 'yzxt', 'yxtz', 'yxzt', 'xtzy', 'xtyz', 'xzty', 'xzyt', 'xytz', 'xyzt'], canBeNone=True),
    description=_('The dimensions physically used by `numpyArray`. If they do not conform the canonical order given by `dimensions`, provide their actual order here and :class:`Grid` will automatically reorder them as needed.'))

AddArgumentMetadata(NumpyGrid.__init__, 'physicalDimensionsFlipped',
    typeMetadata=TupleTypeMetadata(elementType=BooleanTypeMetadata(), mustBeSameLengthAsArgument='dimensions', canBeNone=True),
    description=_(':py:class:`tuple` of :py:class:`bool` indicating how the data of in `numpyArray` are ordered for each physical dimension. If False, the dimension is ordered in ascending coordinate order; if True, it is in descending coordinate order.'))

AddArgumentMetadata(NumpyGrid.__init__, 'scaledDataType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64'], canBeNone=True),
    description=Grid.DataType.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'scaledNoDataValue',
    typeMetadata=Grid.NoDataValue.__doc__.Obj.Type,
    description=Grid.NoDataValue.__doc__.Obj.ShortDescription)

AddArgumentMetadata(NumpyGrid.__init__, 'scalingFunction',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('Lambda or function for transforming the data of `numpyArray` before it is returned by :attr:`Data`, or :py:data:`None` of no such transformation is needed. The function must take one argument, a slice of `numpyArray`, and return a :py:class:`numpy.ndarray` of the `scaledDataType`.'))

AddArgumentMetadata(NumpyGrid.__init__, 'unscalingFunction',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('Lambda or function for back-transforming data written to :attr:`Data` (e.g. ``grid.Data[...] = ...``) before it is written to `numpyArray`, or :py:data:`None` of no such transformation is needed. The function must take one argument, a :py:class:`numpy.ndarray` of the `scaledDataType`, and return a :py:class:`numpy.ndarray` having the same data type as `numpyArray`.'))

CopyArgumentMetadata(Grid.__init__, 'parentCollection', NumpyGrid.__init__, 'parentCollection')
CopyArgumentMetadata(Grid.__init__, 'queryableAttributes', NumpyGrid.__init__, 'queryableAttributes')
CopyArgumentMetadata(Grid.__init__, 'queryableAttributeValues', NumpyGrid.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(Grid.__init__, 'lazyPropertyValues', NumpyGrid.__init__, 'lazyPropertyValues')

AddResultMetadata(NumpyGrid.__init__, 'numpyGrid',
    typeMetadata=ClassInstanceTypeMetadata(cls=NumpyGrid),
    description=_(':class:`%s` instance.') % NumpyGrid.__name__)

# Public method: NumpyGrid.CreateFromGrid

AddMethodMetadata(NumpyGrid.CreateFromGrid,
    shortDescription=_('Reads an entire :class:`Grid` into a newly-allocated numpy array and wraps it in a :class:`NumpyGrid` instance.'))

AddArgumentMetadata(NumpyGrid.CreateFromGrid, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=NumpyGrid),
    description=_('%s class or an instance of it.') % NumpyGrid.__name__)

AddArgumentMetadata(NumpyGrid.CreateFromGrid, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`Grid` instance to read. The entire grid will be read when this function is called.'))

CopyResultMetadata(NumpyGrid.__init__, 'numpyGrid', NumpyGrid.CreateFromGrid, 'numpyGrid')
