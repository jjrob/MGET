# _DirectoryTree.py - Defines DirectoryTree, a DatasetCollectionTree
# representing a file system directory.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _

from . import DatasetCollectionTree


class DirectoryTree(DatasetCollectionTree):
    __doc__ = DynamicDocString()

    def _GetPath(self):
        return self._Path

    Path = property(_GetPath, doc=DynamicDocString())

    def _GetDatasetType(self):
        return self._DatasetType

    DatasetType = property(_GetDatasetType, doc=DynamicDocString())

    def _GetCacheTree(self):
        return self._CacheTree

    CacheTree = property(_GetCacheTree, doc=DynamicDocString())

    def __init__(self, path, datasetType, pathParsingExpressions=None, pathCreationExpressions=None, cacheTree=False, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        super(DirectoryTree, self).__init__(pathParsingExpressions, pathCreationExpressions, queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues, cacheDirectory=cacheDirectory)

        self._Path = path
        self._DatasetType = datasetType
        self._CacheTree = cacheTree
        if self._CacheTree:
            self._TreeCache = {}
        else:
            self._TreeCache = None
        self._DisplayName = _('directory %(name)s') % {'name': self._Path}

    def _GetDisplayName(self):
        return self._DisplayName

    def _ListContents(self, pathComponents):

        # If we are supposed to cache the tree, probe our cache for
        # the contents of this directory.

        directory = os.path.join(self.Path, *pathComponents)

        if self._CacheTree and directory in self._TreeCache:
            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved cached contents of directory %(dir)s'), {'class': self.__class__.__name__, 'id': id(self), 'dir': directory})
            return self._TreeCache[directory]

        # We did not retrieve the contents of this directory from the
        # cache. Get the contents from the operating system and update
        # the cache (if required).
        
        self._LogDebug(_('%(class)s 0x%(id)016X: Listing contents of directory %(dir)s'), {'class': self.__class__.__name__, 'id': id(self), 'dir': directory})
        
        contents = os.listdir(directory)
        contents.sort()
        
        if self._CacheTree:
            self._TreeCache[directory] = contents

        return contents

    def _ConstructFoundObject(self, pathComponents, attrValues, options):
        return self.DatasetType(os.path.join(*pathComponents), parentCollection=self, queryableAttributeValues=attrValues, cacheDirectory=self.CacheDirectory, **options)

    def _GetLocalFile(self, pathComponents):
        return os.path.join(self.Path, *pathComponents), False      # False indicates that it is NOT ok for the caller to delete the file after decompressing it, to save space

    def _RemoveExistingDatasetsFromList(self, pathComponents, datasets, progressReporter):
        self.DatasetType._RemoveExistingDatasetsFromList(os.path.join(self.Path, *pathComponents), datasets, progressReporter)

    def _ImportDatasetsToPath(self, pathComponents, sourceDatasets, mode, progressReporter, options):
        self.DatasetType._ImportDatasetsToPath(os.path.join(self.Path, *pathComponents), sourceDatasets, mode, progressReporter, options)


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
