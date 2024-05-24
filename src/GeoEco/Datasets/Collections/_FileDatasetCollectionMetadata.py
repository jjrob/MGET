# _FileDatasetCollectionMetadata.py - Metadata for classes defined in
# _FileDatasetCollection.py.
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

from .._DatasetCollection import DatasetCollection
from ._FileDatasetCollection import FileDatasetCollection


###############################################################################
# Metadata: FileDatasetCollection class
###############################################################################

AddClassMetadata(FileDatasetCollection,
    module=__package__,
    shortDescription=_('Base class representing a :class:`DatasetCollection` that is a file containing one or more :class:`Dataset`\\ s.'),
    longDescription=_(
""":class:`FileDatasetCollection` is a base class that should not be
instantiated directly; instead, users should instantiate one of the derived
classes representing the type of file they're interested in."""))

# Public properties

AddPropertyMetadata(FileDatasetCollection.Path, 
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Path to the file to open.'),
    longDescription=_(
"""If there is no parent collection, this is the full path to the file. It
will be opened as stand-alone collection.

If there is a parent collection, this path is relative to it. For example, if
the parent collection is a :class:`~GeoEco.Datasets.Collections.DirectoryTree`,
this path is relative to a leaf directory of the
:class:`~GeoEco.Datasets.Collections.DirectoryTree`. Often, the leaf directory
will be the one containing the file, in which case the path provided here will
simply be the name of the file.

If the path points to compressed file, it will be decompressed automatically.
If a cache directory is provided, it will be checked first for an existing
decompressed file. If none is found the file will be decompressed there.

If the compressed file is an archive (e.g. .zip or .tar), you must also
specify a decompressed file to return.

"""))

AddPropertyMetadata(FileDatasetCollection.DecompressedFileToReturn,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    shortDescription=_(':py:func:`~glob.glob` expression that identifies the extracted file to open when the path points to an archive (e.g. a .zip or .tar file).'),
    longDescription=_(
"""This expression must select exactly one of the extracted files. Be sure to
leave it as :py:data:`None` when the path does not point to an archive."""))

# Private constructor: FileDatasetCollection.__init__

AddMethodMetadata(FileDatasetCollection.__init__,
    shortDescription=_('FileDatasetCollection constructor.'))

AddArgumentMetadata(FileDatasetCollection.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=FileDatasetCollection),
    description=_(':class:`%s` instance.') % FileDatasetCollection.__name__)

AddArgumentMetadata(FileDatasetCollection.__init__, 'path',
    typeMetadata=FileDatasetCollection.Path.__doc__.Obj.Type,
    description=FileDatasetCollection.Path.__doc__.Obj.ShortDescription + '\n\n' + FileDatasetCollection.Path.__doc__.Obj.LongDescription)

AddArgumentMetadata(FileDatasetCollection.__init__, 'decompressedFileToReturn',
    typeMetadata=FileDatasetCollection.DecompressedFileToReturn.__doc__.Obj.Type,
    description=FileDatasetCollection.DecompressedFileToReturn.__doc__.Obj.ShortDescription + '\n\n' + FileDatasetCollection.DecompressedFileToReturn.__doc__.Obj.LongDescription)

CopyArgumentMetadata(DatasetCollection.__init__, 'parentCollection', FileDatasetCollection.__init__, 'parentCollection')
CopyArgumentMetadata(DatasetCollection.__init__, 'queryableAttributes', FileDatasetCollection.__init__, 'queryableAttributes')
CopyArgumentMetadata(DatasetCollection.__init__, 'queryableAttributeValues', FileDatasetCollection.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(DatasetCollection.__init__, 'lazyPropertyValues', FileDatasetCollection.__init__, 'lazyPropertyValues')

AddArgumentMetadata(FileDatasetCollection.__init__, 'cacheDirectory',
    typeMetadata=DirectoryTypeMetadata(canBeNone=True),
    description=_(
"""Directory to cache a copy of the downloaded or decompressed file.

If provided, this directory will be checked for the file prior to download or
decompression. If the file is found, the download and decompression will be
skipped. Thus, when performing repetitive processing with remote or compressed
datasets, you can speed up processing considerably by providing a cache
directory.

"""))

AddResultMetadata(FileDatasetCollection.__init__, 'collection',
    typeMetadata=ClassInstanceTypeMetadata(cls=FileDatasetCollection),
    description=_(':class:`%s` instance.') % FileDatasetCollection.__name__)


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
