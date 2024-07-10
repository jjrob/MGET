# _RotatedGlobalGridMetadata.py - Metadata for classes defined in
# _RotatedGlobalGrid.py.
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
from ._RotatedGlobalGrid import RotatedGlobalGrid


###############################################################################
# Metadata: RotatedGlobalGrid class
###############################################################################

AddClassMetadata(RotatedGlobalGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that rotates a :class:`~GeoEco.Datasets.Grid` longitudinally.'))

# Constructor

AddMethodMetadata(RotatedGlobalGrid.__init__,
    shortDescription=_('RotatedGlobalGrid constructor.'))

AddArgumentMetadata(RotatedGlobalGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=RotatedGlobalGrid),
    description=_(':class:`%s` instance.') % RotatedGlobalGrid.__name__)

AddArgumentMetadata(RotatedGlobalGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(
"""Grid to rotate. The grid must have global longitudinal extent."""))

AddArgumentMetadata(RotatedGlobalGrid.__init__, 'rotationOffset',
    typeMetadata=FloatTypeMetadata(),
    description=_(
"""Quantity to rotate the grid by, in the units specified by `rotationUnits`.

Use this parameter to center the grid on a different longitude. Positive
values move the center of the grid to the right (east); negative values move
the center to the left (west). For example, if `rotationUnits` is ``'Cells'``,
the value ``10`` will cause the center of the grid to shift 10 cells to the
right. Effectively, the 10 left-most cells will be stripped from the left edge
and moved to the right edge."""))

AddArgumentMetadata(RotatedGlobalGrid.__init__, 'rotationUnits',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Map units', 'Cells'], makeLowercase=True),
    description=_(
"""The type of values that will be used to rotate the grid, one of:

* ``Map units`` - the unit of rotation will be the same as the linear unit of
  the map, typically degrees for data in geographic coordinate systems and
  meters for data in projected coordinate systems. Because the rotation must
  be in whole cells, the rotation quantity will be converted to grid cells and
  rounded to the nearest cell.

* ``Cells`` - the unit of rotation will be in grid cells. Because the rotation
  must be in whole cells, the rotation quantity will be rounded to the
  neareast cell.

"""))

AddResultMetadata(RotatedGlobalGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=RotatedGlobalGrid),
    description=_(':class:`%s` instance.') % RotatedGlobalGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
