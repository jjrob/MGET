# Datasets.py - Classes that provide a common wrapper around tabular and
# gridded datasets accessible through various geospatial software frameworks
# such as arcpy and GDAL.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

# To keep file sizes managable, we split the names defined by this package
# across several files.

from ._CollectibleObject import CollectibleObject
from ._CollectibleObject import QueryableAttribute
from ._Dataset import Dataset
from ._DatasetCollection import DatasetCollection
from ._Database import Database
from ._Table import Table
from ._Table import Field
from ._Cursors import SelectCursor
from ._Cursors import UpdateCursor
from ._Cursors import InsertCursor


###############################################################################
# Metadata: module
###############################################################################

from ..Internationalization import _
from ..Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Base classes that provide a common wrapper around tabular and gridded datasets accessible through various software frameworks.'))

from . import _CollectibleObjectMetadata
from . import _DatasetMetadata
from . import _DatasetCollectionMetadata
from . import _DatabaseMetadata
from . import _TableMetadata
from . import _CursorsMetadata


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['CollectibleObject',
           'Database',
           'Dataset',
           'DatasetCollection',
           'Field',
           'InsertCursor',
           'QueryableAttribute',
           'SelectCursor',
           'Table',
           'UpdateCursor',
          ]
