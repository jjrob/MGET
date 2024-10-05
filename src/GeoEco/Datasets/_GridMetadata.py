# _GridMetadata.py - Metadata for classes defined in _Grid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Dependencies import PythonModuleDependency
from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from . import Dataset
from ._Grid import Grid


###############################################################################
# Metadata: Grid class
###############################################################################

AddClassMetadata(Grid,
    module=__package__,
    shortDescription=_('Base class for classes representing gridded :class:`Dataset`\\ s with 2, 3, or 4 dimensions.'),
    longDescription=_(
""":class:`Grid` provides a generic wrapper around gridded and array data,
allowing GeoEco components to access them through a common interface that
returns and accepts :class:`numpy.ndarray`. class:`Grid` is a base class that
should not be instantiated directly; instead, users should instantiate one of
the many derived classes representing the type of grid they're interested in.

:class:`Grid` was developed in the 2000s for GeoEco's internal use and
predates more recent projects such as `Xarray <https://xarray.dev/>`_ that may
provide similar functionality with additional features or a more polished
interface. When GeoEco was ported to Python 3, we decided to expose
:class:`Grid` and other classes in :mod:`GeoEco.Datasets` in case they were
useful, but we encourage Python users needing to access multidimensional
arrays to consider Xarray and similar projects that have greater adoption and
a robust, well-funded developer community that supports their maintenance.

**Dimensions**

:class:`Grid` is specifically designed to represent the most common types of
gridded datasets used in marine spatial ecology. As such, :class:`Grid`
supports up to four dimensions: ``x`` (northing), ``y`` (easting), ``z``
(depth or altitude), and ``t`` (time). ``x`` and ``y`` may be angular
coordinates (e.g. degrees) or linear coordinates (e.g. meters) depending on
whether the :class:`Grid` uses a geographic or projected coordinate system.
You can retrieve the coordinate system with :func:`GetSpatialReference`.

:attr:`Dimensions` returns the dimensions as a string. Currently four
combinations of dimensions are supported:

* ``yx`` - static 2D datasets, such as bathymetry rasters.

* ``tyx`` - dynamic 3D datasets, such as a time series of sea surface
  temperature images.

* ``zyx`` - static 3D datasets, where each ``z`` slice represents the values
  at a certain depth or altitude, such as a stack of rasters representing a
  climatology of ocean temperature across a range of depths.

* ``tzyx`` - dynamic 4D datasets, such as a time series of ocean temperature
  data available across a range of depths, as output by a physical ocean model
  like `HYCOM <https://hycom.org>`_.

:attr:`Dimensions` and other attributes and methods of :class:`Grid` always
return dimensions in the orders shown above. If the underlying dataset stores
them in a different order, :class:`Grid` automatically reorders them into
those orders.

The spatial reference of the :class:`Grid` determines the units of ``x`` and
``y``. :attr:`TIncrementUnit` gives the unit of ``t``. Currently, :class:`Grid`
does not make the unit of ``z`` available.

**Coordinates**

:class:`Grid` supports both datasets with constant coordinate increments and
datasets with varying coordinate increments. :attr:`CoordIncrements` gives the
constant increment for each dimension, or :py:data:`None` if the increment is
variable. For example, a global bathymetry grid with a geographic coordinate
system and 0.1 degree resolution would have these properties:

.. code-block:: python

    >>> bathyGrid.GetSpatialReference('proj4')
    '+proj=longlat +datum=WGS84 +no_defs'
    >>> sr = bathyGrid.GetSpatialReference('obj')
    >>> bool(sr.IsGeographic())
    True
    >>> sr.GetAngularUnitsName()
    'Degree'
    >>> bathyGrid.Dimensions
    'yx'
    >>> bathyGrid.CoordIncrements
    (0.1, 0.1)

Variably-incrementing coordinates can optionally also be *dependent* on other
coordinates, which means that the coordinate values vary based on the values
of the depended-upon coordinates. :attr:`CoordDependencies` gives the
dependencies for each coordinate as a string, or :py:data:`None` if the
coordinate does not depend on other coordinates.

Datasets with coordinate dependencies are rare. The most complex example may
be ROMS ocean models that have a fixed number of depth layers (e.g. 40) but
the depth of each layer depends both on time and on geographic location. The
time dependency accounts for the temporally-varying height of the sea surface.
Close to shore, where the maximum depth is small, the spacing between each
depth layer is also small, boosting resolution in these dynamic nearshore
locations. Far from shore, where the maximum depth is large and it is not as
important to have high resolution, the depth layers are spaced farther apart.

As an example of a dataset with complex coordinate dependencies, the
circa-2010 ROMS-CoSiNE model produced by the University of Maine Ocean
Modeling Group had these properties:

.. code-block:: python

    >>> romsGrid.GetSpatialReference('proj4')
    '+proj=merc +lon_0=180 +k=1 +x_0=0 +y_0=0 +R=6371000 +units=m +no_defs'
    >>> sr = romsGrid.GetSpatialReference('obj')
    >>> bool(sr.IsGeographic())
    False
    >>> sr.GetLinearUnitsName()    # These names are determined by PROJ and GDAL
    'metre'
    >>> romsGrid.Dimensions
    'tzyx'
    >>> romsGrid.CoordIncrements
    (73.0, None, 13899.36583056984, 13899.36583056984)
    >>> romsGrid.CoordDependencies
    (None, 'tyx', None, None)
    >>> romsGrid.TIncrementUnit
    'hour'

This 4D grid used a Mercator coordinate system with a cell size of
approximately 13.9 km and a temporal resolution of 73 hours. The ``x``, ``y``,
and ``t`` coordinates used a constant increment but the ``z`` coordinate was
variably-incrementing and depended on the values of the other three
coordinates.

**Semi-regular t coordinates**

For many grids that have a constantly-incrementing ``t`` coordinate, each time
slice is always exactly as long as the ``t`` coordinate's increment. For
example, grids with increments of 6 hours, 1 day, 2 months, or 1 year exhibit
this property. We refer to these grids a having *regular* ``t`` coordinates.

It not necessary for each slice of a regular ``t`` coordinate to span the same
amount of absolute time: one 2-month slice may span more or fewer days than
another one, depending on which months are included in the slice. For a ``t``
coordinate to be considered regular, it is only necessary that the length of
every slice be the same multiple of the  :attr:`TIncrementUnit`. (E.g. every
2-month slice is still 2 months long, regardless of which months it includes.)

For some datasets with constantly-incrementing ``t`` coordinates, this
characteristic does not hold because they want the first time slice of every
year to start on January 1, but the year cannot always be divided into
equal-length slices. For example, `NASA GSFC Ocean Color L3
<https://oceancolor.gsfc.nasa.gov/l3/>`_ includes products that are 8-day
averages. Because the year spans 365 days in some years and 366 in others and
neither is evenly divisible by 8, it is not possible for every slice of a
given year to span exactly 8 days. Instead, the last slice of each year always
spans however may days are left. For example, for NASA's 8-day products, the
46th slice of each year spans days 361-365 on non-leap years, and days 361-366
on leap years.

We refer to these datasets as having *semi-regular* ``t`` coordinates. For
semi-regular grids, :attr:`TSemiRegularity` will be ``'annual'`` and
:attr:`TCountPerSemiRegularPeriod` will be the number of time slices per year,
e.g. 46 for NASA's 8-day products. For regular grids, both
:attr:`TSemiRegularity` and :attr:`TCountPerSemiRegularPeriod` will be
:py:data:`None`.

**Getting the length of each dimension**

:attr:`Shape` returns a :py:class:`tuple` giving the length of each dimension,
in the same order as :attr:`Dimensions`. Continuing the global bathymetry
example above:

.. code-block:: python

    >>> bathyGrid.Dimensions
    'yx'
    >>> bathyGrid.Shape
    (1800, 3600)

**Getting coordinate values**

To allow retrieval of coordinate values, :class:`Grid` exposes three
properties, :attr:`MinCoords`, :attr:`MaxCoords`, and :attr:`CenterCoords`.
Each is an immutable sequence-like object that supports ``[]``-style indexing.
Each accepts a 1-character dimension name and an :py:class:`int` or
:py:class:`range` and returns a single coordinate or :class:`numpy.ndarray` of
coordinates, respectively. Continuing the global bathymetry example above:

.. code-block:: python

    >>> bathyGrid.MinCoords['x', 0]      # int index returns a float
    -180.0
    >>> bathyGrid.MinCoords['x', -1]
    179.90000000000003
    >>> bathyGrid.MinCoords['x', :3]     # range index returns a numpy.ndarray
    array([-180. , -179.9, -179.8])
    >>> bathyGrid.MinCoords['x', -3:]
    array([179.7, 179.8, 179.9])

If only the dimension name is provided, all of the coordinates are returned:

.. code-block:: python

    >>> bathyGrid.MinCoords['x']
    array([-180. , -179.9, -179.8, ...,  179.7,  179.8,  179.9])

:attr:`MinCoords` and :attr:`MaxCoords` return the coordinates of the edges of
each cell; e.g. for the ``x`` coordinate, these are the left and right edges,
respectively. :attr:`CenterCoords` returns the coordinates of the centers:

.. code-block:: python

    >>> bathyGrid.MinCoords['x']
    array([-180. , -179.9, -179.8, ...,  179.7,  179.8,  179.9])
    >>> bathyGrid.MaxCoords['x']
    array([-179.9, -179.8, -179.7, ...,  179.8,  179.9,  180. ])
    >>> bathyGrid.CenterCoords['x']
    array([-179.95, -179.85, -179.75, ...,  179.75,  179.85,  179.95])

The coordinates of the right side of one cell are the same as the left side of
the adjacent cell:

.. code-block:: python

    >>> all(bathyGrid.MaxCoords['x', :-1] == bathyGrid.MinCoords['x', 1:])
    True
"""))

# Public properties

AddPropertyMetadata(Grid.Dimensions,
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['yx', 'zyx', 'tyx', 'tzyx']),
    shortDescription=_('Dimensions of this grid.'))

AddPropertyMetadata(Grid.CoordIncrements,
    typeMetadata=TupleTypeMetadata(elementType=FloatTypeMetadata(canBeNone=True, mustBeGreaterThan=0.)),
    shortDescription=_('Same length as :attr:`Dimensions`. Coordinate increment for each dimension. :py:data:`None` for dimensions that do not have a constant coordinate increment.'))

AddPropertyMetadata(Grid.CoordDependencies,
    typeMetadata=TupleTypeMetadata(elementType=UnicodeStringTypeMetadata(canBeNone=True, minLength=1, maxLength=3)),
    shortDescription=_('Same length as :attr:`Dimensions`. Dimensions that each dimension depends on for determining its coordinates. :py:data:`None` for dimensions that have a constant coordinate increment.'))

AddPropertyMetadata(Grid.TIncrementUnit,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['year', 'month', 'day', 'hour', 'minute', 'second']),
    shortDescription=_('Unit of the ``t`` coordinate. :py:data:`None` if the grid\'s dimensions do not contain a ``t`` coordinate.'))

AddPropertyMetadata(Grid.TSemiRegularity,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['annual']),
    shortDescription=_("Type of semi-regularity used for the ``t`` coordinate. :py:data:`None` if the grid\'s dimensions do not contain a ``t`` coordinate or the ``t`` coordinate is not semi-regular."))

AddPropertyMetadata(Grid.TCountPerSemiRegularPeriod,
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    shortDescription=_("Number of time slices per semi-regular period (i.e. per year). :py:data:`None` if the grid\'s dimensions do not contain a ``t`` coordinate or the ``t`` coordinate is not semi-regular."))

AddPropertyMetadata(Grid.Shape,
    typeMetadata=TupleTypeMetadata(elementType=IntegerTypeMetadata(canBeNone=True, mustBeGreaterThan=0)),
    shortDescription=_('Same length as :attr:`Dimensions`. Length (number of grid cells) of each dimension.'))

AddPropertyMetadata(Grid.CenterCoords,
    typeMetadata=AnyObjectTypeMetadata(),
    shortDescription=_("Coordinates of the grid cell centers, indexed using the 1-character dimension of interest and optionally a :py:class:`range` to retrieve a :class:`numpy.ndarray` of coordinates (e.g. ``CenterCoords['x', 0:4]``) or an integer to retrieve a :py:class:`float` for a single coordinate (e.g. ``CenterCoords['x', 10]``). Coordinates for the ``t`` dimension are returned as :py:class:`~datetime.datetime` instances."))

AddPropertyMetadata(Grid.MinCoords,
    typeMetadata=AnyObjectTypeMetadata(),
    shortDescription=_("Minimum coordinate value for each cell (i.e., the coordinates of the cells' left edges), indexed using the 1-character dimension of interest and optionally a :py:class:`range` to retrieve a :class:`numpy.ndarray` of coordinates (e.g. ``MinCoords['x', 0:4]``) or an integer to retrieve a :py:class:`float` for a single coordinate (e.g. ``MinCoords['x', 10]``). Coordinates for the ``t`` dimension are returned as :py:class:`~datetime.datetime` instances."))

AddPropertyMetadata(Grid.MaxCoords,
    typeMetadata=AnyObjectTypeMetadata(),
    shortDescription=_("Maximum coordinate value for each cell (i.e., the coordinates of the cells' right edges), indexed using the 1-character dimension of interest and optionally a :py:class:`range` to retrieve a :class:`numpy.ndarray` of coordinates (e.g. ``MaxCoords['x', 0:4]``) or an integer to retrieve a :py:class:`float` for a single coordinate (e.g. ``MaxCoords['x', 10]``). Coordinates for the ``t`` dimension are returned as :py:class:`~datetime.datetime` instances."))

AddPropertyMetadata(Grid.DataType,
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']),
    shortDescription=_('Numeric data type of the grid, after the scaling function (if any) has been applied to the raw data. :class:`numpy.ndarray`\\ s returned by :attr:`Data` have this type.'))

AddPropertyMetadata(Grid.NoDataValue,
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    shortDescription=_(':py:class:`int`, :py:class:`float`, or single-element numpy array giving the value that indicates that cells of :attr:`Data` should be interpreted as having no data (these are also known as missing, NA, or NULL cells), or :py:data:`None` if all cells must have data.'))

AddPropertyMetadata(Grid.Data,
    typeMetadata=AnyObjectTypeMetadata(),
    shortDescription=_("This grid's data, indexable using slices (e.g. ``grid.Data[:, 5:10, -10:]``) or integers (e.g. ``grid.Data[0,1,-2]``) or both in combination. Strides and negative indexes are supported in the traditional manner. If the grid is writable, :attr:`Data` can be assigned to write values to the grid, e.g. ``grid.Data[0,1] = 5`` or ``grid.Data[:,:] = numpy.zeros(grid.Shape)``. Returns and accepts :class:`numpy.ndarray`, :py:class:`float`, and :py:class:`int`."))

AddPropertyMetadata(Grid.DataIsScaled,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_("If True, the underlying raw data are stored as the :attr:`UnscaledDataType` to save storage space and then transformed by a *scaling equation* on the fly when they are returned by :attr:`Data`. The raw data can be accessed with :attr:`UnscaledData`. If False, the raw data are returned as is, with no transformation needed, and :attr:`UnscaledDataType` and :attr:`DataType` are the same, and :attr:`UnscaledData` returns the same values as :attr:`Data`."))

AddPropertyMetadata(Grid.UnscaledDataType,
    typeMetadata=Grid.DataType.__doc__.Obj.Type,
    shortDescription=_('Numeric data type of the grid\'s raw data, before it has been transformed by a scaling equation. :class:`numpy.ndarray`\\ s returned by :attr:`UnscaledData` have this type. If no transformation is needed (:attr:`DataIsScaled` is False), then :attr:`UnscaledDataType` and :attr:`ScaledDataType` are the same, and :attr:`UnscaledData` returns the same values as :attr:`Data`.'))

AddPropertyMetadata(Grid.UnscaledNoDataValue,
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    shortDescription=_(':py:class:`int` or :py:class:`float` value that indicates that cells of :attr:`UnscaledData` should be interpreted as having no data (these are also known as missing, NA, or NULL cells), or :py:data:`None` if all cells must have data.'))

AddPropertyMetadata(Grid.UnscaledData,
    typeMetadata=AnyObjectTypeMetadata(),
    shortDescription=_("This grid's data underlying raw data, before it has been transformed by a scaling equation. :attr:`UnscaledData` is indexable using slices (e.g. ``grid.UnscaledData[:, 5:10, -10:]``) or integers (e.g. ``grid.UnscaledData[0,1,-2]``) or both in combination. Strides and negative indexes are supported in the traditional manner. If the grid is writable, :attr:`UnscaledData` can be assigned to write values to the grid, e.g. ``grid.UnscaledData[0,1] = 5`` or ``grid.UnscaledData[:,:] = numpy.zeros(grid.Shape)``. Returns and accepts :class:`numpy.ndarray`, :py:class:`float`, and :py:class:`int`."))

# Private constructor: Grid.__init__

AddMethodMetadata(Grid.__init__,
    shortDescription=_('Grid constructor.'),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy')])

AddArgumentMetadata(Grid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`%s` instance.') % Grid.__name__)

CopyArgumentMetadata(Dataset.__init__, 'parentCollection', Grid.__init__, 'parentCollection')
CopyArgumentMetadata(Dataset.__init__, 'queryableAttributes', Grid.__init__, 'queryableAttributes')
CopyArgumentMetadata(Dataset.__init__, 'queryableAttributeValues', Grid.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(Dataset.__init__, 'lazyPropertyValues', Grid.__init__, 'lazyPropertyValues')

AddResultMetadata(Grid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`%s` instance.') % Grid.__name__)

# Public method: Grid.GetIndicesForCoords

AddMethodMetadata(Grid.GetIndicesForCoords,
    shortDescription=_('Given a :py:class:`tuple` or :py:class:`list` of coordinates, returns a :py:class:`list` of :py:class:`int` indices into :attr:`Data` for the cell that contains the coordinates.'))

CopyArgumentMetadata(Grid.__init__, 'self', Grid.GetIndicesForCoords, 'self')

AddArgumentMetadata(Grid.GetIndicesForCoords, 'coords',
    typeMetadata=AnyObjectTypeMetadata(),
    description=_(':py:class:`tuple` or :py:class:`list` of coordinates that are :py:class:`float` (for ``x``, ``y``, and ``z``) or :py:class:`~datetime.datetime` (for ``t``). The coordinates must be in the same order as :attr:`Dimensions`.'))

AddResultMetadata(Grid.GetIndicesForCoords, 'indices',
    typeMetadata=ListTypeMetadata(elementType=IntegerTypeMetadata(), minLength=2, maxLength=4),
    description=_('List of integer indices into :attr:`Data` for the cell that contains `coords`.'))


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
