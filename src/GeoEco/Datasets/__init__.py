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

from ..Internationalization import _
from ..Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Base classes that provide a common wrapper around tabular and gridded datasets accessible through various software frameworks.'))

from ._CollectibleObject import CollectibleObject, QueryableAttribute
from . import _CollectibleObjectMetadata

from ._Dataset import Dataset
from . import _DatasetMetadata

from ._DatasetCollection import DatasetCollection, CollectionIsEmptyError
from . import _DatasetCollectionMetadata

from ._Database import Database
from . import _DatabaseMetadata

from ._Table import Table, Field
from . import _TableMetadata

from ._Cursors import SelectCursor, UpdateCursor, InsertCursor
from . import _CursorsMetadata

from ._Grid import Grid
from . import _GridMetadata

from ._NumpyGrid import NumpyGrid
from . import _NumpyGridMetadata

__all__ = ['CollectibleObject',
           'CollectionIsEmptyError',
           'Database',
           'Dataset',
           'DatasetCollection',
           'Field',
           'Grid',
           'InsertCursor',
           'NumpyGrid',
           'QueryableAttribute',
           'SelectCursor',
           'Table',
           'UpdateCursor',
          ]
