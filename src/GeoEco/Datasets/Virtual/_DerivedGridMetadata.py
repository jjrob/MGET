# _DerivedGridMetadata.py - Metadata for classes defined in _DerivedGrid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import types

from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from .. import CollectibleObject, Grid
from ._DerivedGrid import DerivedGrid


###############################################################################
# Metadata: DerivedGrid class
###############################################################################

AddClassMetadata(DerivedGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that that derives its values from other :class:`~GeoEco.Datasets.Grid`\\ s with a function you provide.'))

# Constructor

AddMethodMetadata(DerivedGrid.__init__,
    shortDescription=_('DerivedGrid constructor.'))

AddArgumentMetadata(DerivedGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=DerivedGrid),
    description=_(':class:`%s` instance.') % DerivedGrid.__name__)

AddArgumentMetadata(DerivedGrid.__init__, 'grids',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=Grid), minLength=1),
    description=_(
"""List of one or more :class:`~GeoEco.Datasets.Grid`\\ s from which values
will be derived."""))

AddArgumentMetadata(DerivedGrid.__init__, 'func',
    typeMetadata=ClassInstanceTypeMetadata(cls=types.FunctionType),
    description=_(
"""Python function or lambda with the signature ``func(grids, slices)`` and
the parameters:

* `grids` - :py:class:`list` of :class:`~GeoEco.Datasets.Grid`\\ s provided to
  the constructor.

* `slices` - :py:class:`tuple` of :py:class:`slice` or :py:class:`int` that
  define the slices of data to be returned as a numpy array. These may be used
  to retrieve the values of each grid `i` like this:
  ``grids[i].Data.__getitem__(slices)``.

`func` should return a numpy array of derived values for the range specified
by `slices`. Usually, this involves retrieving the data from the `grids` for
those `slices` and then performing a mathematical calculation. For example, if
you have a grid representing sea surface temperature values in kelvin and you
want to convert them to degrees Celsius, you could define this function:

.. code-block:: python

    def k2C(grids, slices):
        return grids[0].Data.__getitem__(slices) - 273.15

Then, you could construct your :class:`~GeoEco.Datasets.Virtual.DerivedGrid` like
this:

.. code-block:: python

    celsiusGrid = DerivedGrid(grids=[kelvinGrid], 
                              func=k2C, 
                              displayName=kelvinGrid.DisplayName + ' in C')

Sometimes you may need to derive values from multiple grids. For example, if
you have grids representing horizontal and vertical components of water
velocity, commonly symbolized `u` and `v`, respectively, and want to compute
the magnitude of velocity using the Pythagorean theorem:

.. code-block:: python

    def mag(grids, slices):
        u = grids[0].Data.__getitem__(slices)
        v = grids[1].Data.__getitem__(slices)
        return (u**2 + v**2)**0.5

You could construct a magnitude grid like this:

.. code-block:: python

    magGrid = DerivedGrid(grids=[uGrid, vGrid], 
                          func=mag, 
                          displayName='current magnitude',
                          noDataValue=-9999.)

Here, we decided to set the :attr:`~GeoEco.Datasets.Grid.NoDataValue` of
``magGrid`` to be ``-9999.`` We could have omitted that line, in which case
the NoDataValue would have been set to ``uGrid.NoDataValue``.

Note that :class:`~GeoEco.Datasets.Virtual.DerivedGrid` automatically coerces
the values returned by `func` to the :attr:`~GeoEco.Datasets.Grid.DataType` of
the first :class:`~GeoEco.Datasets.Grid` in the `grids`, and automatically
sets any cells to NoData that are NoData in any of the `grids`. Use `dataType`
and `allowUnmasking` to override these behaviors."""))

AddArgumentMetadata(DerivedGrid.__init__, 'displayName',
    typeMetadata=Grid.DisplayName.__doc__.Obj.Type,
    description=Grid.DisplayName.__doc__.Obj.ShortDescription)

AddArgumentMetadata(DerivedGrid.__init__, 'dataType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64'], canBeNone=True),
    description=_(
"""Numeric data type of the data returned by this grid. If not provided or
:py:data:`None` is provided, the :attr:`~GeoEco.Datasets.Grid.DataType` of the
first :class:`~GeoEco.Datasets.Grid` in `grids` will be used."""))

AddArgumentMetadata(DerivedGrid.__init__, 'noDataValue',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
""":py:class:`int`, :py:class:`float`, or single-element numpy array giving
the value that indicates that cells of of this grid should be interpreted as
having no data (these are also known as missing, NA, or NULL cells). If not
provided or :py:data:`None` is provided, the
:attr:`~GeoEco.Datasets.Grid.NoDataValue` of the first
:class:`~GeoEco.Datasets.Grid` in `grids` will be used."""))

CopyArgumentMetadata(CollectibleObject.__init__, 'queryableAttributes', DerivedGrid.__init__, 'queryableAttributes')
CopyArgumentMetadata(CollectibleObject.__init__, 'queryableAttributeValues', DerivedGrid.__init__, 'queryableAttributeValues')

AddArgumentMetadata(DerivedGrid.__init__, 'allowUnmasking',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If False, the default, :class:`~GeoEco.Datasets.Virtual.DerivedGrid` will
automatically set a cell to NoData if it is NoData in any of the provided
`grids`. This is done as a convenience, so your `func` does not have to handle
the `grids` having NoData values. If True,
:class:`~GeoEco.Datasets.Virtual.DerivedGrid` will not automatically set any
cell to NoData, and you must ensure that `func` does so appropriately."""))

AddResultMetadata(DerivedGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=DerivedGrid),
    description=_(':class:`%s` instance.') % DerivedGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
