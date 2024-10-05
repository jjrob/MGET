# DataProducts/NASA/Earthdata/__init__.py - Grids and DatasetCollections that
# wrap data products from NASA Earthdata.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ....Internationalization import _
from ....Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Classes for accessing data products from `NASA Earthdata <https://www.earthdata.nasa.gov/>`__.'))

from ._CMRGranuleSearcher import CMRGranuleSearcher
from . import _CMRGranuleSearcherMetadata

__all__ = ['CMRGranuleSearcher']
