# Datasets/Virtual/__init__.py - Grids and DatasetCollections that transform
# Grids and DatasetCollections.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

# To keep file sizes managable, we split the names defined by this package
# across several files.

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_(':class:`~GeoEco.Datasets.Grid`\\ s and :class:`~GeoEco.Datasets.DatasetCollection`\\ s that transform :class:`~GeoEco.Datasets.Grid`\\ s and :class:`~GeoEco.Datasets.DatasetCollection`\\ s, lazily if possible.'))

from ._GridSlice import GridSlice
from . import _GridSliceMetadata

from ._GridSliceCollection import GridSliceCollection
from . import _GridSliceCollectionMetadata

from ._TimeSeriesGridStack import TimeSeriesGridStack
from . import _TimeSeriesGridStackMetadata

from ._AggregateGrid import AggregateGrid
from . import _AggregateGridMetadata

from ._BlockStatisticGrid import BlockStatisticGrid
from . import _BlockStatisticGridMetadata

from ._CannyEdgeGrid import CannyEdgeGrid, _CannyEdgesOverview
from . import _CannyEdgeGridMetadata

from ._ClimatologicalGridCollection import ClimatologicalGridCollection
from . import _ClimatologicalGridCollectionMetadata

from ._ClippedGrid import ClippedGrid
from . import _ClippedGridMetadata

from ._DerivedGrid import DerivedGrid
from . import _DerivedGridMetadata

from ._FastMarchingDistanceGrid import FastMarchingDistanceGrid
from . import _FastMarchingDistanceGridMetadata

from ._InpaintedGrid import InpaintedGrid
from . import _InpaintedGridMetadata

from ._MaskedGrid import MaskedGrid
from . import _MaskedGridMetadata

from ._MemoryCachedGrid import MemoryCachedGrid
from . import _MemoryCachedGridMetadata

from ._RotatedGlobalGrid import RotatedGlobalGrid
from . import _RotatedGlobalGridMetadata

from ._SeafloorGrid import SeafloorGrid
from . import _SeafloorGridMetadata

from ._WindFetchGrid import WindFetchGrid
from . import _WindFetchGridMetadata

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['_CannyEdgesOverview',
           'AggregateGrid',
           'BlockStatisticGrid',
           'CannyEdgeGrid',
           'ClimatologicalGridCollection',
           'ClippedGrid',
           'FastMarchingDistanceGrid',
           'DerivedGrid',
           'GridSlice',
           'GridSliceCollection',
           'InpaintedGrid',
           'MaskedGrid',
           'MemoryCachedGrid',
           'RotatedGlobalGrid',
           'SeafloorGrid',
           'TimeSeriesGridStack',
           'WindFetchGrid']
