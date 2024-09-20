# _DatasetCollectionTreeMetadata.py - Metadata for classes defined in
# _DatasetCollectionTree.py.
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

from .. import DatasetCollection
from ._DatasetCollectionTree import DatasetCollectionTree


###############################################################################
# Metadata: DatasetCollectionTree class
###############################################################################

AddClassMetadata(DatasetCollectionTree,
    module=__package__,
    shortDescription=_('Base class representing :class:`DatasetCollection`\\ s that are organized as hierarchical trees.'),
    longDescription=_(
""":class:`DatasetCollectionTree` is a base class that should not be
instantiated directly; instead, users should instantiate one of the many
derived classes representing the type of dataset collection they're interested
in."""))

# Public properties

AddPropertyMetadata(DatasetCollectionTree.PathParsingExpressions,
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    shortDescription=_(
"""List of regular expressions used for finding datasets in the tree and
parsing queryable attribute values from their paths. One expression per
path level. Use Python :py:ref:`re-syntax`.

Queryable attributes are represented by "named groups" in the regular
expressions. For example, if your collection is an ArcGIS geodatabase that
contains feature classes and tables that you want to query by name, you could
provide ``[r'(?P<TableName>.+)']`` for this parameter. This defines a single
path level (because the list has one element), which contains a single
queryable attribute (because there is one named group), which is named
``TableName``, which must be at least one character long (because ``.+`` means
"one or more characters"). Then, for `queryableAttributes`, provide
``(QueryableAttribute('TableName', 'Table name', UnicodeStringTypeMetadata()),)``.
Finally, when calling 
:func:`~GeoEco.Datasets.Collections.DatasetCollectionTree.QueryDatasets`, use
an `expression` like ``"TableName = 'Foo'"``.

"""))

AddPropertyMetadata(DatasetCollectionTree.PathCreationExpressions,
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    shortDescription=_('List of `printf-style formatters <https://docs.python.org/3/library/stdtypes.html#old-string-formatting>`_ used when importing datasets into this tree. Used to create destination path names from queryable attribute values. One formatter per path level.'))

# Public constructor: DatasetCollectionTree.__init__

AddMethodMetadata(DatasetCollectionTree.__init__,
    shortDescription=_('DatasetCollectionTree constructor.'))

AddArgumentMetadata(DatasetCollectionTree.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=DatasetCollectionTree),
    description=_(':class:`%s` instance.') % DatasetCollectionTree.__name__)

AddArgumentMetadata(DatasetCollectionTree.__init__, 'pathParsingExpressions',
    typeMetadata=DatasetCollectionTree.PathParsingExpressions.__doc__.Obj.Type,
    description=DatasetCollectionTree.PathParsingExpressions.__doc__.Obj.ShortDescription)

AddArgumentMetadata(DatasetCollectionTree.__init__, 'pathCreationExpressions',
    typeMetadata=DatasetCollectionTree.PathCreationExpressions.__doc__.Obj.Type,
    description=DatasetCollectionTree.PathCreationExpressions.__doc__.Obj.ShortDescription)

AddArgumentMetadata(DatasetCollectionTree.__init__, 'canSortByDate',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""This parameter is primarily of interest to developers of derived classes.
If True and `queryableAttributes` includes a
:class:`~GeoEco.Datasets.QueryableAttribute` with a `dataType` of
:class:`~GeoEco.Types.DateTimeTypeMetadata`, the  
:func:`GetOldestDataset` and :func:`GetNewestDataset` methods will assume they
can call the derived class's :func:`_QueryRecursive` method with a `queryType`
of ``'oldest'`` and ``'newest'``, respectively, and the derived class will
implement suitable optimizations to efficiently retrieve the oldest and newest
datasets in this collection.

If False, :func:`GetOldestDataset` and :func:`GetNewestDataset` will retrieve
and examine relevant metadata from every dataset in this collection to
determine which dataset is oldest and newest."""))

CopyArgumentMetadata(DatasetCollection.__init__, 'parentCollection', DatasetCollectionTree.__init__, 'parentCollection')
CopyArgumentMetadata(DatasetCollection.__init__, 'queryableAttributes', DatasetCollectionTree.__init__, 'queryableAttributes')
CopyArgumentMetadata(DatasetCollection.__init__, 'queryableAttributeValues', DatasetCollectionTree.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(DatasetCollection.__init__, 'lazyPropertyValues', DatasetCollectionTree.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(DatasetCollection.__init__, 'cacheDirectory', DatasetCollectionTree.__init__, 'cacheDirectory')

AddResultMetadata(DatasetCollectionTree.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=DatasetCollectionTree),
    description=_(':class:`%s` instance.') % DatasetCollectionTree.__name__)


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
