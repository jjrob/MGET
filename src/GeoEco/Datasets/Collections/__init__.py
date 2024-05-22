# Datasets/Collections.py - Various DatasetCollections.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

# To keep file sizes managable, we split the names defined by this package
# across several files.

from ._DatasetCollectionTree import DatasetCollectionTree
from ._DirectoryTree import DirectoryTree
from ._FileDatasetCollection import FileDatasetCollection
from ._FTPDirectoryTree import FTPDirectoryTree


###############################################################################
# Metadata: module
###############################################################################

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Various :class:`DatasetCollection`\\ s.'))

from . import _DatasetCollectionTreeMetadata
from . import _DirectoryTreeMetadata
from . import _FileDatasetCollectionMetadata
from . import _FTPDirectoryTreeMetadata


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['DatasetCollectionTree',
           'DirectoryTree',
           'FileDatasetCollection',
           'FTPDirectoryTree']
