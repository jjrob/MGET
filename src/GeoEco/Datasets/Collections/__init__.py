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

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('General purpose :class:`~GeoEco.Datasets.DatasetCollection`\\ s.'))

from ._FileDatasetCollection import FileDatasetCollection
from . import _FileDatasetCollectionMetadata

from ._DatasetCollectionTree import DatasetCollectionTree
from . import _DatasetCollectionTreeMetadata

from ._DirectoryTree import DirectoryTree
from . import _DirectoryTreeMetadata

from ._FTPDirectoryTree import FTPDirectoryTree
from . import _FTPDirectoryTreeMetadata

__all__ = ['DatasetCollectionTree',
           'DirectoryTree',
           'FileDatasetCollection',
           'FTPDirectoryTree']
