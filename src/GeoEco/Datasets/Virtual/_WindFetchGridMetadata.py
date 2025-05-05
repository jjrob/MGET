# _WindFetchGridMetadata.py - Metadata for classes defined in
# _WindFetchGrid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Dependencies import PythonModuleDependency
from ...Internationalization import _
from ...Logging import ProgressReporter
from ...Metadata import *
from ...Types import *

from .. import Grid
from ._WindFetchGrid import WindFetchGrid


###############################################################################
# Metadata: WindFetchGrid class
###############################################################################

AddClassMetadata(WindFetchGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing mean distance to NoData cells in a land/water :class:`~GeoEco.Datasets.Grid` over a range of directions.'),
    longDescription=_(
"""The wind fetch computations performed by this tool were based on those of
https://github.com/KennethTM/WindFetch. Thanks to `Kenneth Martinsen
<https://github.com/KennethTM>`_ for developing and sharing it."""))

# Public properties

AddPropertyMetadata(WindFetchGrid.Directions,
    typeMetadata=ListTypeMetadata(elementType=FloatTypeMetadata(minValue=0., maxValue=360.), minLength=1),
    shortDescription=_(
"""Directions, in degrees, for which wind fetch distance should be computed
and averaged. Typically these range from 0 to 360 by a small (but not too
small) increment such as 15 degrees, e.g. ``list(range(0, 360, 15))``."""))

AddPropertyMetadata(WindFetchGrid.MaxDist,
    typeMetadata=FloatTypeMetadata(canBeNone=True, minValue=0.),
    shortDescription=_(
"""Maximum allowed mean wind fetch distance. If provided, after the mean
fetch distance in all directions is computed, it is compared against this maximum
value. Wherever the mean is larger, it is rounded down to the maximum."""))

AddPropertyMetadata(WindFetchGrid.MaxDistPerDir,
    typeMetadata=FloatTypeMetadata(canBeNone=True, minValue=0.),
    shortDescription=_(
"""Maximum allowed wind fetch distance in each direction. If provided, then
each time fetch distance is calculated for a specific direction, it is
compared against this maximum value. Wherever fetch in the calculated
direction is larger, it will be rounded down to the maximum value. This will
be done for each direction in turn, prior to averaging all of the directions
into a mean. Use this parameter to prevent a few extremely long distances from
dominating the mean."""))

AddPropertyMetadata(WindFetchGrid.PadByMaxDistPerDir,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_(
"""If True (the default) and the `MaxDistPerDir` parameter is given, then the
grid will be automatically padded on all sides by water before fetch is
computed. Use this option when you want the edges of the grid to be considered
open ocean rather than land, and you want to prevent fetch from decreasing
along the edges as if land was there. If False or `MaxDistPerDir` is not
given, then the edges will be considered land."""))

# Constructor

AddMethodMetadata(WindFetchGrid.__init__,
    shortDescription=_('WindFetchGrid constructor.'),
    dependencies=[PythonModuleDependency('scipy', cheeseShopName='scipy')])

AddArgumentMetadata(WindFetchGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=WindFetchGrid),
    description=_(':class:`%s` instance.') % WindFetchGrid.__name__)

AddArgumentMetadata(WindFetchGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` for which mean wind fetch should be computed. The :attr:`~GeoEco.Datasets.Grid.NoDataValue` is assumed to represent land, and all other cells water. Typically, this grid has 2 dimensions. If it has 3 or 4 dimensions, wind fetch will be computed for each 2D slice.'))

AddArgumentMetadata(WindFetchGrid.__init__, 'directions',
    typeMetadata=WindFetchGrid.Directions.__doc__.Obj.Type,
    description=WindFetchGrid.Directions.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindFetchGrid.__init__, 'maxDist',
    typeMetadata=WindFetchGrid.MaxDist.__doc__.Obj.Type,
    description=WindFetchGrid.MaxDist.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindFetchGrid.__init__, 'maxDistPerDir',
    typeMetadata=WindFetchGrid.MaxDistPerDir.__doc__.Obj.Type,
    description=WindFetchGrid.MaxDistPerDir.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindFetchGrid.__init__, 'padByMaxDistPerDir',
    typeMetadata=WindFetchGrid.PadByMaxDistPerDir.__doc__.Obj.Type,
    description=WindFetchGrid.PadByMaxDistPerDir.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindFetchGrid.__init__, 'reportProgress',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, progress messages will be logged periodically as the computation proceeds.'))

AddResultMetadata(WindFetchGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=WindFetchGrid),
    description=_(':class:`%s` instance.') % WindFetchGrid.__name__)

# Public method: ComputeFetch

AddMethodMetadata(WindFetchGrid.ComputeFetch,
    shortDescription=_('Compute mean wind fetch distance to for a 2D :class:`numpy.ndarray` representing land and water.'),
    dependencies=[PythonModuleDependency('scipy', cheeseShopName='scipy')])

AddArgumentMetadata(WindFetchGrid.ComputeFetch, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=WindFetchGrid),
    description=_(':class:`%s` or an instance of it.') % WindFetchGrid.__name__)

AddArgumentMetadata(WindFetchGrid.ComputeFetch, 'array',
    typeMetadata=NumPyArrayTypeMetadata(dimensions=2, minShape=[1,1], allowedDTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64', 'float128']),
    description=_(':class:`numpy.ndarray` representing land and water. Must have 2 dimensions.'))

AddArgumentMetadata(WindFetchGrid.ComputeFetch, 'landValue',
    typeMetadata=AnyObjectTypeMetadata(),
    description=_('Value of `array` that represents land. May be ``numpy.nan``. All other cells are assumed to be water.'))

AddArgumentMetadata(WindFetchGrid.ComputeFetch, 'cellSize',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0.),
    description=_('Cell size of `array`. Cells are assumed to be square. The cell size is the length or width of the cell.'))

CopyArgumentMetadata(WindFetchGrid.__init__, 'directions', WindFetchGrid.ComputeFetch, 'directions')
CopyArgumentMetadata(WindFetchGrid.__init__, 'maxDistPerDir', WindFetchGrid.ComputeFetch, 'maxDistPerDir')
CopyArgumentMetadata(WindFetchGrid.__init__, 'padByMaxDistPerDir', WindFetchGrid.ComputeFetch, 'padByMaxDistPerDir')
CopyArgumentMetadata(WindFetchGrid.__init__, 'reportProgress', WindFetchGrid.ComputeFetch, 'reportProgress')

AddResultMetadata(WindFetchGrid.ComputeFetch, 'obj',
    typeMetadata=NumPyArrayTypeMetadata(allowedDTypes=['float32']),
    description=_('A ``float32`` :class:`numpy.ndarray` representing the mean distance to land cells in `grid` in the given `directions`.'))


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
