# _DatasetCollectionMetadata.py - Metadata for classes defined in
# _DatasetCollection.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Dependencies import PythonModuleDependency
from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from ._CollectibleObject import CollectibleObject
from ._Dataset import Dataset
from ._DatasetCollection import DatasetCollection, CollectionIsEmptyError


###############################################################################
# Metadata: DatasetCollection class
###############################################################################

AddClassMetadata(DatasetCollection,
    module=__package__,
    shortDescription=_('Base class for objects representing a collection of :class:`Dataset`\\ s or other :class:`DatasetCollection`\\ s.'))

# Public properties

AddPropertyMetadata(DatasetCollection.CacheDirectory,
    typeMetadata=DirectoryTypeMetadata(canBeNone=True),
    shortDescription=_('Directory for caching local copies of remote datasets.'),
    longDescription=_(
"""If a cache directory is not provided, then after a remote dataset is
downloaded it will be kept either only in memory or in a temporary directory
on disk, depending on the type of data it is. The temporary directory will be
automatically deleted when :func:`Close` is called.

If a cache directory is provided, remote datasets will be stored in it when
they are downloaded. Before a download is attempted, the cache directory will
be checked first for the relevant dataset, and if it is found, the download
will be skipped, speeding up execution.

The datasets are organized in the cache directory in an undocumented format
that is specific to the collection. Once a dataset is stored in the cache
directory, it is never changed or deleted. If the original remote datasets are
changed, these changes will not be detected and the cache will not be updated.
If the disk fills up, cached datasets will not be automatically deleted to
mitigate the problem.

If you determine that the cached datasets are obsolete or the disk is too
full, delete the entire cache directory. You may also be able to delete a
portion of it, if you can reverse engineer how datasets are stored within it,
but the organizational structure is not documented."""))

# Public method: DatasetCollection.QueryDatasets

AddMethodMetadata(DatasetCollection.QueryDatasets,
    shortDescription=_('Queries the collection and returns a :py:class:`list` of :class:`~GeoEco.Datasets.Dataset`\\ s that match a search expression.'),
    isExposedToPythonCallers=True,
    dependencies=[PythonModuleDependency('pyparsing', cheeseShopName='pyparsing')])

AddArgumentMetadata(DatasetCollection.QueryDatasets, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=DatasetCollection),
    description=_(':class:`%s` instance.') % DatasetCollection.__name__)

AddArgumentMetadata(DatasetCollection.QueryDatasets, 'expression',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""A SQL-like query expression that selects the datasets of interest based on
the values of their queryable attributes. If not provided, all of the datasets
in the collection will be selected.

The expression is similar to a SQL "where" clause and may contain the
following elements:

* The names of any queryable attributes, with no delimiters, that are defined
  for objects in the collection, including those they inherit from their
  parents.

* The binary comparison operators ``=``, ``<``, ``>``, ``<=``, ``>=``, and
  ``<>``.

* Literals for integers, floating point numbers (with ``.`` as the decimal
  point), Booleans (written ``true`` and ``false``), strings (delimited with
  single or double quotation marks), or dates (written ``#YYYY-mm-dd
  HH:MM:SS#`` or ``#YYYY-mm-dd#`` with ``YYYY`` as the four-digit year, ``mm``
  as the two-digit month, ``dd`` as the two-digit day, ``HH`` as the two-digit
  hour ``00`` to ``23``, ``MM`` as the two-digit second, and ``SS`` as the
  two-digit second, with the hour, minute, and second assumed to be
  ``00:00:00`` if not provided).

* The binary comparison operator ``in`` or ``not in`` followed by a
  comma-delimited list of literals, enclosed in ``(`` and ``)``.

* The binary comparison operator ``matches`` followed by a string literal that
  specifies a regular expression in Python syntax.

* The binary arithmetic operators ``+``, ``-``, ``*``, and ``/``, which may be
  applied to queryable attributes and numeric literals.

* The unary arithmetic operator ``-``, which may be used to negate a queryable
  attribute or numeric literal.

* The binary logical operators ``or`` and ``and`` and unary logical operator
  ``not``. ``not`` has highest precedence; ``or`` has lowest. Logical
  expressions may be chained together but not nested (in parentheses or by any
  other means).

Operators and queryable attribute names are case-insensitive."""))

AddArgumentMetadata(DatasetCollection.QueryDatasets, 'reportProgress',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, progress messages will be logged periodically as the query proceeds.'))

AddArgumentMetadata(DatasetCollection.QueryDatasets, 'options',
    typeMetadata=DictionaryTypeMetadata(keyType=ClassInstanceTypeMetadata(cls=str), valueType=AnyObjectTypeMetadata(canBeNone=True)),
    description=_('Additional options specific to the collection type.'))

AddResultMetadata(DatasetCollection.QueryDatasets, 'datasets',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=Dataset)),
    description=_(':py:class:`list` of :class:`~GeoEco.Datasets.Dataset`\\ s that match the search expression.'))

# Public method: DatasetCollection.GetOldestDataset

AddMethodMetadata(DatasetCollection.GetOldestDataset,
    shortDescription=_('Queries the collection and returns the oldest :class:`~GeoEco.Datasets.Dataset` that matches the search expression.'),
    isExposedToPythonCallers=True,
    dependencies=[PythonModuleDependency('pyparsing', cheeseShopName='pyparsing')])

CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'self', DatasetCollection.GetOldestDataset, 'self')
CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'expression', DatasetCollection.GetOldestDataset, 'expression')
CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'options', DatasetCollection.GetOldestDataset, 'options')

AddResultMetadata(DatasetCollection.GetOldestDataset, 'dataset',
    typeMetadata=ClassInstanceTypeMetadata(cls=Dataset, canBeNone=True),
    description=_('The oldest :class:`~GeoEco.Datasets.Dataset` that matches the search expression, or :py:data:`None` if nothing matches or the collection is empty.'))

# Public method: DatasetCollection.GetNewestDataset

AddMethodMetadata(DatasetCollection.GetNewestDataset,
    shortDescription=_('Queries the collection and returns the newest :class:`~GeoEco.Datasets.Dataset` that matches the search expression.'),
    isExposedToPythonCallers=True,
    dependencies=[PythonModuleDependency('pyparsing', cheeseShopName='pyparsing')])

CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'self', DatasetCollection.GetNewestDataset, 'self')
CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'expression', DatasetCollection.GetNewestDataset, 'expression')
CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'options', DatasetCollection.GetNewestDataset, 'options')

AddResultMetadata(DatasetCollection.GetNewestDataset, 'dataset',
    typeMetadata=ClassInstanceTypeMetadata(cls=Dataset, canBeNone=True),
    description=_('The newest :class:`~GeoEco.Datasets.Dataset` that matches the search expression, or :py:data:`None` if nothing matches or the collection is empty.'))

# Public method: DatasetCollection.ImportDatasets

AddMethodMetadata(DatasetCollection.ImportDatasets,
    shortDescription=_('Copies each :class:`~GeoEco.Datasets.Dataset` in a :py:class:`list` into this :class:`~GeoEco.Datasets.DatasetCollection`.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'self', DatasetCollection.ImportDatasets, 'self')

AddArgumentMetadata(DatasetCollection.ImportDatasets, 'datasets',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=Dataset)),
    description=_(':py:class:`list` of :class:`~GeoEco.Datasets.Dataset`\\ s to import.'))

AddArgumentMetadata(DatasetCollection.ImportDatasets, 'mode',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Add', 'Replace'], makeLowercase=True),
    description=_(
"""Overwrite mode, one of:

* Add - create datasets that do not exist and skip those that already exist.
  This is the default.

* Replace - create datasets that do not exist and overwrite those that already
  exist.

Note:

    The ArcGIS Overwrite Output geoprocessing environment setting has no
    influence here. If ``'Replace'`` is used, the datasets will be
    overwritten, regardless of the ArcGIS Overwrite Output setting.
"""))

AddArgumentMetadata(DatasetCollection.ImportDatasets, 'reportProgress',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, progress messages will be logged periodically as the import proceeds.'))

CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'options', DatasetCollection.ImportDatasets, 'options')

# Private constructor: DatasetCollection.__init__

AddMethodMetadata(DatasetCollection.__init__,
    shortDescription=_('DatasetCollection constructor. Not intended to be called directly. Only intended to be called from derived class constructors.'))

CopyArgumentMetadata(DatasetCollection.QueryDatasets, 'self', DatasetCollection.__init__, 'self')

AddArgumentMetadata(DatasetCollection.__init__, 'parentCollection',
    typeMetadata=DatasetCollection.ParentCollection.__doc__.Obj.Type,
    description=DatasetCollection.ParentCollection.__doc__.Obj.ShortDescription)

AddArgumentMetadata(DatasetCollection.__init__, 'queryableAttributes',
    typeMetadata=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributes').Type,
    description=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributes').Description)

AddArgumentMetadata(DatasetCollection.__init__, 'queryableAttributeValues',
    typeMetadata=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Type,
    description=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Description)

AddArgumentMetadata(DatasetCollection.__init__, 'lazyPropertyValues',
    typeMetadata=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('lazyPropertyValues').Type,
    description=CollectibleObject.__init__.__doc__.Obj.GetArgumentByName('lazyPropertyValues').Description)

AddArgumentMetadata(DatasetCollection.__init__, 'cacheDirectory',
    typeMetadata=DatasetCollection.CacheDirectory.__doc__.Obj.Type,
    description=DatasetCollection.CacheDirectory.__doc__.Obj.ShortDescription)

AddResultMetadata(DatasetCollection.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=DatasetCollection),
    description=_(':class:`%s` instance.') % DatasetCollection.__name__)


###############################################################################
# Metadata: CollectionIsEmptyError class
###############################################################################

AddClassMetadata(CollectionIsEmptyError,
    module=__package__,
    shortDescription=_('Exception indicating that a :class:`~GeoEco.Datasets.DatasetCollection` does not have any :class:`~GeoEco.Datasets.Dataset`\\ s in it.'))

# Constructor

AddMethodMetadata(CollectionIsEmptyError.__init__,
    shortDescription=_('Constructs a new %s instance.') % CollectionIsEmptyError.__name__)

AddArgumentMetadata(CollectionIsEmptyError.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=CollectionIsEmptyError),
    description=_(':class:`%s` instance.') % CollectionIsEmptyError.__name__)

AddArgumentMetadata(CollectionIsEmptyError.__init__, 'collectionDisplayName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(':class:`~GeoEco.Datasets.DatasetCollection.DisplayName` of the :class:`~GeoEco.Datasets.DatasetCollection`.'))

AddArgumentMetadata(CollectionIsEmptyError.__init__, 'expression',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_('Query expression that was used to query the :class:`~GeoEco.Datasets.DatasetCollection` and that failed to select any datasets.'))

AddResultMetadata(CollectionIsEmptyError.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=CollectionIsEmptyError),
    description=_('New :class:`%s` instance.') % CollectionIsEmptyError.__name__)


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
