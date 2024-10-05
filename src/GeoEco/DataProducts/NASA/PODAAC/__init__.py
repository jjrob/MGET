# DataProducts/NASA/PODAAC/__init__.py - Grids and DatasetCollections that
# wrap data products from NASA JPL PO.DAAC.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ....Internationalization import _
from ....Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Classes for accessing data products from `NASA JPL PO.DAAC <https://podaac.jpl.nasa.gov/>`__.'))

from ._GHRSSTLevel4Granules import GHRSSTLevel4Granules
from ._GHRSSTLevel4GranulesMetadata import _GHRSSTLevel4_LongDescription

from ._GHRSSTLevel4 import GHRSSTLevel4
from . import _GHRSSTLevel4Metadata

__all__ = ['_GHRSSTLevel4_LongDescription',
           'GHRSSTLevel4',
           'GHRSSTLevel4Granules']
