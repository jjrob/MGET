# _MaskedGridMetadata.py - Metadata for classes defined in _MaskedGrid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from .. import Grid
from ._MaskedGrid import MaskedGrid


###############################################################################
# Metadata: MaskedGrid class
###############################################################################

AddClassMetadata(MaskedGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that sets cells of another :class:`~GeoEco.Datasets.Grid` to NoData according to one or more :class:`~GeoEco.Datasets.Grid`\\ s representing masks.'))

# Constructor

AddMethodMetadata(MaskedGrid.__init__,
    shortDescription=_('MaskedGrid constructor.'))

AddArgumentMetadata(MaskedGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=MaskedGrid),
    description=_(':class:`%s` instance.') % MaskedGrid.__name__)

AddArgumentMetadata(MaskedGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to mask.'))

AddArgumentMetadata(MaskedGrid.__init__, 'masks',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=Grid), minLength=1),
    description=_(
""":py:class:`list` of one or more :class:`~GeoEco.Datasets.Grid`\\ s that are
the masks. Each of the `masks` must have the same coordinates as `grid`. For a
given cell of `grid`, the :attr:`~GeoEco.Datasets.Grid.NoDataValue` will be
returned if any of the corresponding cells in the `masks` is masked. To
determine if a cell of a given mask is masked, the cell is compared to the
corresponding value in `values` using the corresponding operator in
`operators`."""))

AddArgumentMetadata(MaskedGrid.__init__, 'operators',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(allowedValues=['=', '==', '!=', '<>', '<', '<=', '>', '>=', 'any', 'all']), minLength=1, mustBeSameLengthAsArgument='masks'),
    description=_(
"""List of comparison operations that should be performed, one for
:class:`~GeoEco.Datasets.Grid` in `masks` and value in `values`. The possible
operators are:

* ``=`` or ``==`` - the mask cell is equal to the value. For this operator,
  ``float('nan')`` (the floating point "not a number" value) is considered
  equal to itself. This is contrary to normal practice in Python programming,
  but is convenient for masking.

* ``!=`` or ``<>`` - the mask cell is not equal to the value. As above,
  ``float('nan')`` is considered equal to itself, so a "not equal" comparison
  of ``float('nan')`` to itself is false.

* ``<`` - the mask cell is less than the value.

* ``<=`` - the mask cell is less or equal to than the value.

* ``>`` - the mask cell is greater than the value.

* ``>=`` - the mask cell is greater or equal to than the value.

* ``any`` - any of the bits of the value that are 1 are also 1 for the mask.
  Only applicable for integer-valued masks and values.

* ``all`` - all of the bits of the value that are 1 are also 1 for the mask.
  Only applicable for integer-valued masks and values.

"""))

AddArgumentMetadata(MaskedGrid.__init__, 'values',
    typeMetadata=ListTypeMetadata(elementType=AnyObjectTypeMetadata(canBeNone=False), minLength=1, mustBeSameLengthAsArgument='masks'),
    description=_(
"""List of values to which `masks` should be compared, one for each
:class:`~GeoEco.Datasets.Grid` in `masks` and operator in `operators`."""))

AddArgumentMetadata(MaskedGrid.__init__, 'unscaledNoDataValue',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
""":py:class:`int` or :py:class:`float` or single-valued numpy array giving
the unscaled NoData value to use when a cell of `grid` is considered masked.
You should provide a value when `grid` does not have an
:attr:`~GeoEco.Datasets.Grid.UnscaledNoDataValue`. Ignored
``grid.UnscaledNoDataValue`` does not return :py:data:`None`."""))

AddArgumentMetadata(MaskedGrid.__init__, 'scaledNoDataValue',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
""":py:class:`int` or :py:class:`float` or single-valued numpy array giving
the scaled NoData value to use when a cell of `grid` is considered masked. You
should provide a value when `grid` does not have a
:attr:`~GeoEco.Datasets.Grid.NoDataValue` and ``grid.DataIsScaled`` is True.
Ignored if ``grid.DataIsScaled`` is False or ``grid.NoDataValue`` does not
return :py:data:`None`."""))

AddArgumentMetadata(MaskedGrid.__init__, 'tolerance',
    typeMetadata=FloatTypeMetadata(canBeNone=True, minValue=0., mustBeLessThan=1.),
    description=_(
""":py:class:`float` giving the relative tolerance, expressed as the fraction
of a grid cell, for determining that the masks enclose the grid and align with
its cells. Having a non-zero tolerance helps avoid situations where the masks
and grid are supposed to have exactly the same extents or cell alignments, but
numerical rounding issues during their production has caused them to be very
slightly different. If the tolerance is zero, then the extents and cell
alignments must match exactly."""))

AddResultMetadata(MaskedGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=MaskedGrid),
    description=_(':class:`%s` instance.') % MaskedGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
