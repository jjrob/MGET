# _BlockStatisticGridGridMetadata.py - Metadata for classes defined in
# _BlockStatisticGridGrid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Dependencies import PythonModuleDependency
from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from .. import Grid
from ._BlockStatisticGrid import BlockStatisticGrid


###############################################################################
# Metadata: BlockStatisticGrid class
###############################################################################

AddClassMetadata(BlockStatisticGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing a block statistic computed over another :class:`~GeoEco.Datasets.Grid`.'),
    longDescription=(
"""This class partitions the input :class:`~GeoEco.Datasets.Grid` into
non-overlapping blocks of cells and computes a summary statistic for each
block, yielding a reduced resolution representation of it. This operation is
sometimes known as downsampling."""))

# Constructor

AddMethodMetadata(BlockStatisticGrid.__init__,
    shortDescription=_('BlockStatisticGrid constructor.'))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=BlockStatisticGrid),
    description=_(':class:`%s` instance.') % BlockStatisticGrid.__name__)

AddArgumentMetadata(BlockStatisticGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(
""":class:`~GeoEco.Datasets.Grid` for which a block statistic should be
computed. This input grid must have a constant increment in each dimension for
which summarization is requested. For example, if the `zSize` parameter is
given, indicating that summarization should be performed in the depth
dimension, then the input grid must have ``z`` coordinates that increment by a
constant value. If it does not, then :class:`BlockStatisticGrid` cannot
summarize in the ``z`` dimension, and `zSize` should be left as
:py:data:`None`. In that situation, the :class:`BlockStatisticGrid` will have
the same number of cells in the ``z`` direction as the input grid."""))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'statistic',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['count', 'maximum', 'mean', 'median', 'minimum', 'range', 'standard_deviation', 'sum'], makeLowercase=True),
    description=_(
"""Summary statistic to calculate for each block, one of:

* ``count`` - number of cells in the block that have data.

* ``maximum`` - miniumum value of call cells in the block with data.

* ``mean`` - mean value of all cells in the block with data.

* ``median`` - median value of all cells in the block with data.

* ``minimum`` - miniumum value of all cells in the block with data.

* ``range`` - maximum value minus the minimum value, considering all cells in
  the block with data.

* ``standard_deviation`` - sample standard deviation (i.e. the standard
  deviation estimated using Bessel's correction) of all cells in the block
  with data. In order to calculate this, there must be at least two cells in
  the block with data.

* ``sum`` - sum of all cells in the block with data.

In all statistics, NoData values are ignored. For example, if a 5 x 5 block
has 2 cells with the NoData value, all statistics will be based on the 23
cells that have data. If no cells in a block have data, i.e., they all have
the NoData value, the result is the NoData value."""),
    arcGISDisplayName=_('Statistic'))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'xySize',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Size of the block in the ``x`` and ``y`` directions. If not given, 1 will
be used, and summarization will not be performed for the ``x`` or ``y``
dimensions. In this situation, the block statistic grid will have the same
number of cells in the ``x`` and ``y`` directions as the input grid."""))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'zSize',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Size of the block in the ``z`` (depth) direction. If not given, 1 will be
used, and summarization will not be performed for the ``z`` dimension. In this
situation, the block statistic grid will have the same number of cells in the
``z`` direction as the input grid. This parameter should be omitted if the
input grid does not have a ``z`` dimension."""))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'tSize',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Size of the block in the ``t`` (time) direction, in the units given by the
`tUnit` parameter. If not given, 1 will be used, and summarization will not be
performed for the ``t`` dimension. In this situation, the block statistic grid
will have the same number of cells in the ``t`` direction as the input grid.
This parameter should be omitted if the input grid does not have a ``t``
dimension.

The length of time specified by `tSize` and `tUnit` must be longer than the
time increment of the input grid. If tUnit is ``month`` or ``year`` and the
`tIncrementUnit` of the input grid is ``day``, ``hour``, ``minute``, or
``second``, then the resulting blocks will be based on however many days,
hours, minutes, or seconds actually fall within each block of months or years.

A time slice of the input grid will be included in a block if its start time
is greater than or equal to the start time of the block, and less than or
equal to the end time of the block. By default, the start times of the blocks
are aligned with midnight of January 1 of the year the input grid starts. The
`tStart` parameter can override this behavior.

For example, if the input grid contains hourly time slices and starts on
2012-02-19 13:00:00, and the block statistic grid is defined with a `tSize` of
``1``, a `tUnit` of ``month``, and `tStart` is not given, then the first
block will summarize slices that start 2012-02-01 00:00:00 through 2012-02-29
23:00:00, inclusive. The second time slice will summarize slices that start
2012-03-01 00:00:00 through 2012-03-31 23:00:00, inclusive.

If `tUnit` is ``day``, ``hour``, ``minute``, or ``second`` and the `tSize`
would yield a series of blocks with a block that overlapped the transition
from December to January, the `tSemiRegularity` parameter controls what
happens."""))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'tUnit',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['year', 'month', 'day', 'hour', 'minute', 'second'], makeLowercase=True),
    description=_(
"""Unit of the `tSize` parameter. This parameter should be omitted if the
input grid does not have a ``t`` dimension."""))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'tStart',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Date and time to which the summary blocks' minimum ``t`` coordinates should
be aligned (or "snapped"). Ignored if no summarization is performed in the
``t`` direction (i.e., `tSize` is not given).

If a start date and time is given, it must be less than or equal to the
minimum ``t`` coordinate of the first time slice of the input grid. If it is
not given, it will be set to midnight on January 1 of the year the input grid
starts.

Blocks will be laid out in the ``t`` direction starting at this date and time
until a block is found that starts on or before the minimum ``t`` coordinate
of the input grid and ends after that coordinate. That block will become the
first in the block statistic grid (the ones before it will be dropped).

If `tUnit` is ``month``, then the start date and time must be midnight on the
first day of a month. The resulting summary blocks will thus encompass whole
months. Starting the blocks at any time other than the very beginning of the
month is not currently supported.

If `tSemiRegularity` is ``annual``, then the start date and time must be
midnight on January 1 of a year."""))

AddArgumentMetadata(BlockStatisticGrid.__init__, 'tSemiRegularity',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['annual']),
    description=_(
"""Type of semi-regularity to use for the ``t`` coordinate. Ignored if no
summarization is performed in the ``t`` direction (i.e., `tSize` is not
given), or if `tUnit` is ``month`` or ``year``.

If `tUnit` is ``day``, ``hour``, ``minute``, or ``second`` and
`tSemiRegularity` is not given, then the resulting series of summary blocks
will be allowed to contain blocks that overlap the December/January
transition. For example, this would happen if `tUnit` is ``day`` and `tSize`
is anything other than ``1``. This may be fine for many applications, but
sometimes it is desirable for the first block of every year to start at
midnight on January 1. To enable that, set `tSemiRegularity` to ``annual``.

When `tSemiRegularity` is ``annual``, the final block of each year will be
prevented from extending into January 1. Once the maximum number of whole
blocks are fitted into the year, the remaining fraction of time until midnight
January 1 of the next year is calculated. If it is less than half a block
long, then the final whole block is expanded to include the remaining
fraction. But if it is half or more of a block long, the remaining fraction is
added to the year as an additional, shorter-than-usual block.

For example, if `tSize` is ``8``, `tUnit` is ``day``, and `tSemiRegularity` is
``annual``, then the first block of every year will always start on midnight
January 1. There will always be 46 blocks per year. The 46th block of every
year will always start midnight December 27 on non leap years, and midnight
December 26 on leap years. In either case, the 46th block will stop at
midnight January 1 of the following year, spanning 5 days on non leap years
and 6 days on leap years."""))


AddResultMetadata(BlockStatisticGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=BlockStatisticGrid),
    description=_(':class:`%s` instance.') % BlockStatisticGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
