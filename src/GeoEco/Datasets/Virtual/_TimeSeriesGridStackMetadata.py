# _TimeSeriesGridStackMetadata.py - Metadata for classes defined in
# _TimeSeriesGridStack.py.
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

from .. import DatasetCollection
from ._TimeSeriesGridStack import TimeSeriesGridStack


###############################################################################
# Metadata: TimeSeriesGridStack class
###############################################################################

AddClassMetadata(TimeSeriesGridStack,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` built by stacking a set of 2D (yx) or 3D (zyx) Grids queried from a :class:`~GeoEco.Datasets.DatasetCollection`.'))

# Constructor

AddMethodMetadata(TimeSeriesGridStack.__init__,
    shortDescription=_('TimeSeriesGridStack constructor.'))

AddArgumentMetadata(TimeSeriesGridStack.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=TimeSeriesGridStack),
    description=_(':class:`%s` instance.') % TimeSeriesGridStack.__name__)

AddArgumentMetadata(TimeSeriesGridStack.__init__, 'collection',
    typeMetadata=ClassInstanceTypeMetadata(cls=DatasetCollection),
    description=_(
""":class:`~GeoEco.Datasets.DatasetCollection` containing the
:class:`~GeoEco.Datasets.Grid`\\ s to stack. The Grids must all have the same
dimensions. Typically, they are either 2-dimensional with dimensions ``yx`` or
3-dimensional with dimensions ``zyx``. However, they may also include a ``t``
dimension (i.e. ``tyx`` or ``tzyx``) so long as the length of each Grid in the
``t`` direction is 1. In any case, they must all have the same length as each
other for the other dimensions. They must also each have a
:class:`~GeoEco.Datasets.QueryableAttribute` defined with a
:attr:`~GeoEco.Datasets.QueryableAttribute.DataType` of
:class:`~GeoEco.Types.DateTimeTypeMetadata`. The value of this
QueryableAttribute must give the time coordinate of the Grid.

The oldest Grid in `collection` selected by `expression` must also have three
lazy properties defined: ``TIncrement``, ``TIncrementUnit``, and
``TCornerCoordType``. It should also have ``TSemiRegularity`` defined if
necessary. Please see the :class:`~GeoEco.Datasets.Grid` documentation for
descriptions of these properties.

Alternatively, if `collection` is the parent collection of the Grids, those
lazy properties can be defined by `collection` itself, rather than being
defined by the oldest Grid it contains. This is the common use pattern when
the Grids do not have a ``t`` dimension.

The Grids that are selected by `expression` must form a time series with time
coordinates that are consistent with the ``TIncrement`` and
``TIncrementUnit``. For example, if ``TIncrement`` is 1 and ``TIncrementUnit``
is ``'month'``, the Grids must occur as a monthly series. Missing time slices
are OK and will be automatically represented as slices of NoData. For example,
if the DatasetCollection contains 118 monthly Grids spanning 10 years but is
missing 2 Grids due to a satellite failure in one of those years, then those
two months will automatically be represented as NoData across the entire
spatial extent.

There must not be any duplicate time slices used to define the
:class:`TimeSeriesGridStack`. If `collection` contains duplicates,
`expression` should be used to select a unique set of slices. For example, if
`collection` includes Grids for several oceanographic variables but they can
be distinguished from each other by the ``VariableName`` QueryableAttribute,
then `expression` could be set to ``"VariableName = 'SST'"``, so that only the
SST Grids are stacked."""))

CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'expression', TimeSeriesGridStack.__init__, 'expression')
CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'reportProgress', TimeSeriesGridStack.__init__, 'reportProgress')
CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'options', TimeSeriesGridStack.__init__, 'options')

AddResultMetadata(TimeSeriesGridStack.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=TimeSeriesGridStack),
    description=_(':class:`%s` instance.') % TimeSeriesGridStack.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
