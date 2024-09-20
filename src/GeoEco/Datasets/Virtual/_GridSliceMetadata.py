# _GridSliceMetadata.py - Metadata for classes defined in _GridSlice.py.
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
from ._GridSlice import GridSlice


###############################################################################
# Metadata: GridSlice class
###############################################################################

AddClassMetadata(GridSlice,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing a time or depth slice of a 3D or 4D :class:`~GeoEco.Datasets.Grid`.'))

# Constructor

AddMethodMetadata(GridSlice.__init__,
    shortDescription=_('GridSlice constructor.'))

AddArgumentMetadata(GridSlice.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GridSlice),
    description=_(':class:`%s` instance.') % GridSlice.__name__)

AddArgumentMetadata(GridSlice.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to slice. It must have a t (time) dimension or z (depth) dimension, or both.'))

AddArgumentMetadata(GridSlice.__init__, 'tIndex',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_('t index of the slice to extract. Omit if `grid` does not have a t dimension, or you don\'t want to slice the t dimension.'))

AddArgumentMetadata(GridSlice.__init__, 'zIndex',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_('z index of the slice to extract. Omit if `grid` does not have a z dimension, or you don\'t want to slice the z dimension.'))

AddArgumentMetadata(GridSlice.__init__, 'tQAName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_('Name of the :class:`~GeoEco.Datasets.QueryableAttribute` to define for the t coordinate. Must be given if `tIndex` is given. Ignored otherwise.'))

AddArgumentMetadata(GridSlice.__init__, 'tQADisplayName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_('Display name of the :class:`~GeoEco.Datasets.QueryableAttribute` to define for the t coordinate. Must be given if `tIndex` is given. Ignored otherwise.'))

AddArgumentMetadata(GridSlice.__init__, 'tQACoordType',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_( 
"""Type of t coordinate to use for the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` for the t coordinate. For
example, if `grid` has a :attr:`~GeoEco.Datasets.Grid.TIncrementUnit` of
``'day'``, and the t coordinates start at midnight and are spaced 1 day apart,
then if `tQACoordType` is ``'min'``, the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` will be midnight on the date of
the time slice. If it is ``'center'`` the value will be 12:00:00 on that date,
and if it is ``'max'`` it will be midnight of the next day."""))

AddArgumentMetadata(GridSlice.__init__, 'zQAName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_('Name of the :class:`~GeoEco.Datasets.QueryableAttribute` to define for the t (depth) coordinate. Must be given if `zIndex` is given. Ignored otherwise.'))

AddArgumentMetadata(GridSlice.__init__, 'zQADisplayName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_('Display name of the :class:`~GeoEco.Datasets.QueryableAttribute` to define for the z coordinate. Must be given if `zIndex` is given. Ignored otherwise.'))

AddArgumentMetadata(GridSlice.__init__, 'zQACoordType',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_( 
"""Type of z coordinate to use for the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` for the z coordinate. For
example, if increasing positive values of the z coordinate of `grid` indicate
deeper depths and `zQACoordType` is ``'min'``, the value of the
:class:`~GeoEco.Datasets.QueryableAttribute` will be the depth representing
the shallow edge of the depth slice. If it is ``'center'`` the value will be
the center depth, and if it is ``'max'`` it will the deep edge."""))

AddArgumentMetadata(GridSlice.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Informal name of this object. If you do not provide a name, a suitable name
will be created automatically."""))

AddArgumentMetadata(GridSlice.__init__, 'additionalQueryableAttributeValues',
    typeMetadata=DictionaryTypeMetadata(keyType=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'), valueType=AnyObjectTypeMetadata(canBeNone=True), canBeNone=True),
    description=_('Values of additional queryable attributes to define, expressed as a dictionary mapping the case-insensitive names of queryable attributes to their values.'))

AddResultMetadata(GridSlice.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=GridSlice),
    description=_(':class:`%s` instance.') % GridSlice.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
