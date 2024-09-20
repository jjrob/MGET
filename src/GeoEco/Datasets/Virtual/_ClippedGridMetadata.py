# _ClippedGridMetadata.py - Metadata for classes defined in _ClippedGrid.py.
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
from ._ClippedGrid import ClippedGrid


###############################################################################
# Metadata: ClippedGrid class
###############################################################################

AddClassMetadata(ClippedGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that trims a :class:`~GeoEco.Datasets.Grid` to a smaller spatiotemporal extent.'))

# Constructor

AddMethodMetadata(ClippedGrid.__init__,
    shortDescription=_('ClippedGrid constructor.'))

AddArgumentMetadata(ClippedGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClippedGrid),
    description=_(':class:`%s` instance.') % ClippedGrid.__name__)

AddArgumentMetadata(ClippedGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_('Grid to clip.'))

AddArgumentMetadata(ClippedGrid.__init__, 'clipBy',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Map coordinates', 'Cell indices'], makeLowercase=True),
    description=_(
"""Specifies the type of extent values that will be used to clip the grid, one
of:

* ``Map coordinates`` - the values are coordinates in space and time.
  Typically this means that x and y coordinates will be in degrees (if a
  geographic coordinate system is used) or a linear unit such as meters (if a
  projected coordinate system is used), the z (depth) coordinate will be in a
  linear unit such as meters, and the t (time) coordinate will be a date and
  time string in a standard format such as ``YYYY-MM-DD HH:MM:SS``, or a
  Python :py:class:`~datetime.datetime` instance.

* ``Indices`` - the values are integer indices of cells in the grid, starting
  at 0 and ending at the maximum index value. For example, if a 2D grid has
  360 columns and 180 rows, the x and y indices will range from 0 to 359 and
  0 to 179, respectively.

If ``Indices`` is specified but floating point numbers are provided for the
extent values, the decimal portions of the numbers will be truncated (e.g. the
value 1.7 will be truncated to 1).

If ``Map coordinates`` is specified and a coordinate value falls within a
cell, rather than exactly on a boundary between two cells, the cell will be
included in the clipped grid (it will not be clipped out). Because computers
cannot represent all floating-point numbers at full precision, the resulting
rounding errors can sometimes produce unexpected results. For example,
consider a grid with a cell size of 0.1. We expect that the cells centered at
0.5 and 1.5 would meet at coordinate value 0.1, but 0.1 cannot be fully
represented by the computer using standard 64-bit floating-point numbers. The
computer rounds it to 0.10000000000000001. Therefore, if you were to clip the
grid a maximum coordinate of 0.10000000000000001, you would expect that the
cell centered at 1.5 would be included in the resulting grid, because
0.10000000000000001 falls within that cell. But the computer actually
considers the boundary between the two cells to be at 0.10000000000000001, not
0.1, so that cell would be clipped out."""),
    arcGISDisplayName=_('Clip by'))

_ClipMaxParameterDescription = _(
"""%(extent)s %(dim)s coordinate or index. The Clip By parameter determines
whether the value is a coordinate or an index. If a coordinate is provided, it
may be an integer or a floating point number. If an index is provided, it
must be an non-negative integer. If a value is not provided, the clipped grid
will extend to the full extent in the %(dir)s %(dim)s direction.""")

AddArgumentMetadata(ClippedGrid.__init__, 'xMin',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_ClipMaxParameterDescription % {'extent': _('Minimum'), 'dim': 'x', 'dir': _('negative')},
    arcGISDisplayName=_('Minimum x extent'))

AddArgumentMetadata(ClippedGrid.__init__, 'xMax',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_ClipMaxParameterDescription % {'extent': _('Maximum'), 'dim': 'x', 'dir': _('positive')},
    arcGISDisplayName=_('Maximum x extent'))

AddArgumentMetadata(ClippedGrid.__init__, 'yMin',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_ClipMaxParameterDescription % {'extent': _('Minimum'), 'dim': 'y', 'dir': _('negative')},
    arcGISDisplayName=_('Minimum y extent'))

AddArgumentMetadata(ClippedGrid.__init__, 'yMax',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_ClipMaxParameterDescription % {'extent': _('Maximum'), 'dim': 'y', 'dir': _('positive')},
    arcGISDisplayName=_('Maximum y extent'))

AddArgumentMetadata(ClippedGrid.__init__, 'zMin',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_ClipMaxParameterDescription % {'extent': _('Minimum'), 'dim': 'z', 'dir': _('negative')},
    arcGISDisplayName=_('Minimum z extent'))

AddArgumentMetadata(ClippedGrid.__init__, 'zMax',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_ClipMaxParameterDescription % {'extent': _('Maximum'), 'dim': 'z', 'dir': _('positive')},
    arcGISDisplayName=_('Maximum z extent'))

AddArgumentMetadata(ClippedGrid.__init__, 'tMin',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Minimum t coordinate or index. The Clip By parameter determines whether 
the value is a coordinate or an index. If a coordinate is provided, it may be
a date and time string in a standard format such as ``YYYY-MM-DD HH:MM:SS`` or
a Python :py:class:`~datetime.datetime` instance. If an index is provided, it
must be an non-negative integer. If a value is not provided, the clipped
grid will extend to the full extent in the negative t direction."""),
    arcGISDisplayName=_('Minimum t extent'))

AddArgumentMetadata(ClippedGrid.__init__, 'tMax',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Maximum t coordinate or index. The Clip By parameter determines whether
the value is a coordinate or an index. If a coordinate is provided, it may be
a date and time string in a standard format such as ``YYYY-MM-DD HH:MM:SS``
or a Python :py:class:`~datetime.datetime` instance. If an index is provided,
it must be an non-negative integer. If a value is not provided, the clipped
grid will extend to the full extent in the positive t direction."""),
    arcGISDisplayName=_('Maximum t extent'))

AddResultMetadata(ClippedGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClippedGrid),
    description=_(':class:`%s` instance.') % ClippedGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
