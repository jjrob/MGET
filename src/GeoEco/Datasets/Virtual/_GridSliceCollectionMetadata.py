# _GridSliceCollectionMetadata.py - Metadata for classes defined in
# _GridSliceCollection.py.
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
from ._GridSliceCollection import GridSliceCollection


###############################################################################
# Metadata: GridSliceCollection class
###############################################################################

AddClassMetadata(GridSliceCollection,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.DatasetCollection` of :class:`~GeoEco.Datasets.Grid`\\ s representing the 2D slices of a 3D or 4D :class:`~GeoEco.Datasets.Grid` (or 3D slices of a 4D :class:`~GeoEco.Datasets.Grid`).'))

# Constructor

AddMethodMetadata(GridSliceCollection.__init__,
    shortDescription=_('GridSliceCollection constructor.'))

AddArgumentMetadata(GridSliceCollection.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GridSliceCollection),
    description=_(':class:`%s` instance.') % GridSliceCollection.__name__)

AddArgumentMetadata(GridSliceCollection.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to split into slices. It must have a t (time) dimension or z (depth) dimension, or both.'))

AddArgumentMetadata(GridSliceCollection.__init__, 'tQAName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
""":attr:`~GeoEco.Datasets.QueryableAttribute.Name` of the
:class:`~GeoEco.Datasets.QueryableAttribute` to define for each slice for the
time t (time) dimension. Provide :py:data:`None` if you don\'t want to slice
the t dimension. Ignored if `grid` does not have a t dimension."""))

AddArgumentMetadata(GridSliceCollection.__init__, 'tQADisplayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
""":attr:`~GeoEco.Datasets.QueryableAttribute.DisplayName` of the
:class:`~GeoEco.Datasets.QueryableAttribute` to define for each slice for the
time t (time) dimension. Ignored if `grid` does not have a t dimension or
`tQAName` is :py:data:`None`."""))

AddArgumentMetadata(GridSliceCollection.__init__, 'tQACoordType',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_( 
"""Type of t coordinate to use for the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` for the t coordinate. For
example, if `grid` has a :attr:`~GeoEco.Datasets.Grid.TIncrementUnit` of
``'day'``, and the t coordinates start at midnight and are spaced 1 day apart,
then if `tQACoordType` is ``'min'``, the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` will be midnight on the date of
the time slice. If it is ``'center'`` the value will be 12:00:00 on that date,
and if it is ``'max'`` it will be midnight of the next day. If :py:data:`None`
is provided, the ``TCornerCoordType`` lazy property of `grid` will be used for
`tQACoordType`. Ignored if `grid` does not have a t dimension or `tQAName` is
:py:data:`None`."""))

AddArgumentMetadata(GridSliceCollection.__init__, 'zQAName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
""":attr:`~GeoEco.Datasets.QueryableAttribute.Name` of the
:class:`~GeoEco.Datasets.QueryableAttribute` to define for each slice for the
time z (depth) dimension. Provide :py:data:`None` if you don\'t want to slice
the z dimension. Ignored if `grid` does not have a z dimension."""))

AddArgumentMetadata(GridSliceCollection.__init__, 'zQADisplayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_(
""":attr:`~GeoEco.Datasets.QueryableAttribute.DisplayName` of the
:class:`~GeoEco.Datasets.QueryableAttribute` to define for each slice for the
time z (depth) dimension. Ignored if `grid` does not have a z dimension or
`zQAName` is :py:data:`None`."""))

AddArgumentMetadata(GridSliceCollection.__init__, 'zQACoordType',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_( 
"""Type of z coordinate to use for the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` for the z coordinate. For
example, if increasing positive values of the z coordinate of `grid` indicate
deeper depths and `zQACoordType` is ``'min'``, the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` will be the depth representing
the shallow edge of the depth slice. If it is ``'center'`` the value will be
the center depth, and if it is ``'max'`` it will the deep edge. Ignored if
`grid` does not have a z dimension or `zQAName` is :py:data:`None`."""))

AddArgumentMetadata(GridSliceCollection.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Informal name of this object. If you do not provide a name, a suitable name
will be created automatically."""))

AddResultMetadata(GridSliceCollection.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=GridSliceCollection),
    description=_(':class:`%s` instance.') % GridSliceCollection.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
