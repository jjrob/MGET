# _MemoryCachedGridMetadata.py - Metadata for classes defined in
# _MemoryCachedGrid.py.
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
from ._MemoryCachedGrid import MemoryCachedGrid


###############################################################################
# Metadata: MemoryCachedGrid class
###############################################################################

AddClassMetadata(MemoryCachedGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that wraps another :class:`~GeoEco.Datasets.Grid`, caching blocks of it in memory to facilitate fast repeated retrievals.'))

# Constructor

AddMethodMetadata(MemoryCachedGrid.__init__,
    shortDescription=_('MemoryCachedGrid constructor.'))

AddArgumentMetadata(MemoryCachedGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=MemoryCachedGrid),
    description=_(':class:`%s` instance.') % MemoryCachedGrid.__name__)

AddArgumentMetadata(MemoryCachedGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to mask.'))

AddArgumentMetadata(MemoryCachedGrid.__init__, 'maxCacheSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Maximum size of the cache, in bytes."""))

AddArgumentMetadata(MemoryCachedGrid.__init__, 'xMinBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``x`` direction. The
size is given as the number of cells. If this parameter is 0, no blocks will
be cached in memory."""))

AddArgumentMetadata(MemoryCachedGrid.__init__, 'yMinBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``y`` direction. The
size is given as the number of cells. If this parameter is 0, no blocks will
be cached in memory."""))

AddArgumentMetadata(MemoryCachedGrid.__init__, 'zMinBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``z`` (depth)
direction. The size is given as the number of cells. If this parameter is 0,
no blocks will be cached in memory. This parameter is ignored if the grids do
not have a ``z`` dimension."""))

AddArgumentMetadata(MemoryCachedGrid.__init__, 'tMinBlockSize',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Size of the blocks of data to cache in memory in the ``t`` (time)
direction. The size is given as the number of cells. If this parameter is 0,
no blocks will be cached in memory. This parameter is ignored if the grids do
not have a ``t`` dimension."""))

AddResultMetadata(MemoryCachedGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=MemoryCachedGrid),
    description=_(':class:`%s` instance.') % MemoryCachedGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
