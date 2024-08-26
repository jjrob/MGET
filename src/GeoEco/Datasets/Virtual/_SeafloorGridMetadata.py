# _SeafloorGridMetadata.py - Metadata for classes defined in _SeafloorGrid.py.
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

from .. import CollectibleObject, Grid
from ._SeafloorGrid import SeafloorGrid


###############################################################################
# Metadata: SeafloorGrid class
###############################################################################

AddClassMetadata(SeafloorGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that extracts the deepest available values of a :class:`~GeoEco.Datasets.Grid` that has a z (depth) dimension, yielding a single layer representing values at the seafloor.'))

# Constructor

AddMethodMetadata(SeafloorGrid.__init__,
    shortDescription=_('SeafloorGrid constructor.'))

AddArgumentMetadata(SeafloorGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=SeafloorGrid),
    description=_(':class:`%s` instance.') % SeafloorGrid.__name__)

AddArgumentMetadata(SeafloorGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_('Grid that has a z (depth) dimension.'))

AddArgumentMetadata(SeafloorGrid.__init__, 'queryableAttributes',
    typeMetadata=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributes').Type,
    description=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributes').Description)

AddArgumentMetadata(SeafloorGrid.__init__, 'queryableAttributeValues',
    typeMetadata=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Type,
    description=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Description)

AddResultMetadata(SeafloorGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=SeafloorGrid),
    description=_(':class:`%s` instance.') % SeafloorGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
