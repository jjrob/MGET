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

from ._FastMarchingDistanceGrid import FastMarchingDistanceGrid
from . import _FastMarchingDistanceGridMetadata

from ._GridSlice import GridSlice
from . import _GridSliceMetadata

from ._InpaintedGrid import InpaintedGrid
from . import _InpaintedGridMetadata

from ._RotatedGlobalGrid import RotatedGlobalGrid
from . import _RotatedGlobalGridMetadata

from ._TimeSeriesGridStack import TimeSeriesGridStack
from . import _TimeSeriesGridStackMetadata

from ._WindFetchGrid import WindFetchGrid
from . import _WindFetchGridMetadata

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['FastMarchingDistanceGrid',
           'GridSlice',
           'InpaintedGrid',
           'RotatedGlobalGrid',
           'TimeSeriesGridStack',
           'WindFetchGrid']
