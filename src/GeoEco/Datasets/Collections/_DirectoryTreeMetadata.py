# _DirectoryTreeMetadata.py - Metadata for classes defined in
# _DirectoryTree.py.
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

from .._CollectibleObject import CollectibleObject
from ._DatasetCollectionTree import DatasetCollectionTree
from ._DirectoryTree import DirectoryTree


###############################################################################
# Metadata: DirectoryTree class
###############################################################################

AddClassMetadata(DirectoryTree,
    module=__package__,
    shortDescription=_('A :class:`DatasetCollectionTree` representing a file system directory.'))

# Public properties

AddPropertyMetadata(DirectoryTree.Path,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Path to the root directory of the tree.'))

AddPropertyMetadata(DirectoryTree.DatasetType,
    typeMetadata=ClassTypeMetadata(cls=CollectibleObject),
    shortDescription=_('The type of :class:`~GeoEco.Datasets.CollectibleObject`\\ s contained by this :class:`~GeoEco.Datasets.Collections.DirectoryTree`.'),
    longDescription=_(
"""If this type is a :class:`~GeoEco.Datasets.Dataset`, instances of it will
be constructed and returned when :func:`QueryDatasets` is called. If it is a
:class:`~GeoEco.Datasets.DatasetCollection`, instances will be constructed and
themselves queried, and the resulting :class:`~GeoEco.Datasets.Dataset`
instances will then be returned."""))

AddPropertyMetadata(DirectoryTree.CacheTree,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, the contents of the tree will be cached when it is first accessed, to improve performance on future accesses. If False, the contents will be obtained each time the tree is accessed.'))

# Public constructor: DirectoryTree.__init__

AddMethodMetadata(DirectoryTree.__init__,
    shortDescription=_('DirectoryTree constructor.'))

AddArgumentMetadata(DirectoryTree.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=DirectoryTree),
    description=_(':class:`%s` instance.') % DirectoryTree.__name__)

AddArgumentMetadata(DirectoryTree.__init__, 'path',
    typeMetadata=DirectoryTree.Path.__doc__.Obj.Type,
    description=DirectoryTree.Path.__doc__.Obj.ShortDescription)

AddArgumentMetadata(DirectoryTree.__init__, 'datasetType',
    typeMetadata=DirectoryTree.DatasetType.__doc__.Obj.Type,
    description=DirectoryTree.DatasetType.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(DatasetCollectionTree.__init__, 'pathParsingExpressions', DirectoryTree.__init__, 'pathParsingExpressions')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'pathCreationExpressions', DirectoryTree.__init__, 'pathCreationExpressions')

AddArgumentMetadata(DirectoryTree.__init__, 'cacheTree',
    typeMetadata=DirectoryTree.CacheTree.__doc__.Obj.Type,
    description=DirectoryTree.CacheTree.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(DatasetCollectionTree.__init__, 'queryableAttributes', DirectoryTree.__init__, 'queryableAttributes')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'queryableAttributeValues', DirectoryTree.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'lazyPropertyValues', DirectoryTree.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'cacheDirectory', DirectoryTree.__init__, 'cacheDirectory')

AddResultMetadata(DirectoryTree.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=DirectoryTree),
    description=_(':class:`%s` instance.') % DirectoryTree.__name__)


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
