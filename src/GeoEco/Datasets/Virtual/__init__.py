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

from ._FastMarchingDistanceGrid import FastMarchingDistanceGrid
from ._RotatedGlobalGrid import RotatedGlobalGrid
from ._WindFetchGrid import WindFetchGrid


###############################################################################
# Metadata: module
###############################################################################

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_(':class:`~GeoEco.Datasets.Grid`\\ s and :class:`~GeoEco.Datasets.DatasetCollection`\\ s that transform :class:`~GeoEco.Datasets.Grid`\\ s and :class:`~GeoEco.Datasets.DatasetCollection`\\ s, lazily if possible.'))

from . import _FastMarchingDistanceGridMetadata
from . import _RotatedGlobalGridMetadata
from . import _WindFetchGridMetadata


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['FastMarchingDistanceGrid',
           'RotatedGlobalGrid',
           'WindFetchGrid']
