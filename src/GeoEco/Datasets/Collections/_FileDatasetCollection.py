# _FileDatasetCollection.py - Defines FileDatasetCollection, a
# DatasetCollection representing a file that contains Datasets.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import glob
import os

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Logging import Logger

from .._DatasetCollection import DatasetCollection


class FileDatasetCollection(DatasetCollection):
    __doc__ = DynamicDocString()

    def _GetPath(self):
        return self._Path

    Path = property(_GetPath, doc=DynamicDocString())

    def _GetDecompressedFileToReturn(self):
        return self._DecompressedFileToReturn

    DecompressedFileToReturn = property(_GetDecompressedFileToReturn, doc=DynamicDocString())

    def __init__(self, path, decompressedFileToReturn=None, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        if parentCollection is not None and not hasattr(parentCollection, '_GetLocalFile'):
            raise TypeError(_('The parentCollection, if provided, must have a method called _GetLocalFile().'))
        
        self._Path = path
        self._DecompressedFileToReturn = decompressedFileToReturn
        
        super(FileDatasetCollection, self).__init__(parentCollection, queryableAttributes, queryableAttributeValues, lazyPropertyValues, cacheDirectory)

    def _GetOpenableFile(self):

        # If the file is not compressed and exists in the file system,
        # just return it.

        if self.ParentCollection is None:
            localPath = self.Path
        elif hasattr(self.ParentCollection, 'Path') and self.ParentCollection.Path is not None:
            localPath = os.path.join(self.ParentCollection.Path, self.Path)
        else:
            localPath = None

        if localPath is not None and os.path.splitext(localPath)[1] not in ['.bz2', '.gz', '.tar', '.z', '.zip'] and os.path.exists(localPath):
            return localPath, True

        # The file is not an uncompressed, existing file system
        # object. If we our our parent collections define a cache
        # directory and the file exists there in uncompressed form,
        # return it.

        cacheDirectory = None
        obj = self
        while obj is not None:
            if obj.CacheDirectory is not None:
                cacheDirectory = obj.CacheDirectory
                if not os.path.isdir(cacheDirectory):
                    self._LogDebug(_('Creating cache directory %(dir)s.') % {'dir': cacheDirectory})
                    os.makedirs(cacheDirectory)
                break
            obj = obj.ParentCollection

        if cacheDirectory is not None:
            if os.path.splitext(self.Path)[1] not in ['.bz2', '.gz', '.tar', '.z', '.zip']:
                if os.path.exists(os.path.join(cacheDirectory, self.Path)):
                    return os.path.join(cacheDirectory, self.Path), False
            elif not self.Path.endswith('.tar') and not self.Path.endswith('.tar.bz2') and not self.Path.endswith('.tar.gz') and not self.Path.endswith('.tar.z') and not self.Path.endswith('.zip'):
                if os.path.exists(os.path.join(cacheDirectory, os.path.splitext(self.Path)[0])):
                    return os.path.join(cacheDirectory, os.path.splitext(self.Path)[0]), False
            else:
                files = glob.glob(os.path.join(os.path.dirname(os.path.join(cacheDirectory, self.Path)), self._DecompressedFileToReturn))
                if len(files) > 0:
                    return files[0], False

        # If we have a parent collection, instruct it to create a
        # local copy of the file, if it does not exist already.

        isOriginalFile = True

        if self.ParentCollection is not None:
            pathComponents = list(os.path.split(self.Path))
            while pathComponents[1] != '':
                pathComponents = list(os.path.split(pathComponents[0])) + pathComponents[1:]
            pathComponents = [s for s in pathComponents if s != '']
            localPath, deleteFileAfterDecompressing = self.ParentCollection._GetLocalFile(pathComponents)
            isOriginalFile = False
        else:
            pathComponents = ['']
            localPath = os.path.join(self.Path)
            deleteFileAfterDecompressing = False

        # If the file is compressed, decompress it.

        if os.path.splitext(localPath)[1] in ['.bz2', '.gz', '.tar', '.z', '.zip']:        

            # If we or our parent collections did not define a cache
            # directory, create one.

            if cacheDirectory is None:
                cacheDirectory = self._CreateTempDirectory()

            # Decompress the file.

            oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
            Logger.SetLogInfoAsDebug(True)
            try:
                from ...DataManagement.Files import File
                decompressedFile = File.Decompress(localPath, os.path.join(cacheDirectory, os.path.dirname(self.Path)), True, self._DecompressedFileToReturn)
            finally:
                Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

            # If the parent collection indicated that it is ok to
            # delete the compressed file after decompressing it,
            # delete it now.

            if deleteFileAfterDecompressing:
                self._LogDebug(_('%(class)s 0x%(id)016X: Deleting %(file)s to save disk space'), {'class': self.__class__.__name__, 'id': id(self), 'file': localPath})
                try:
                    os.remove(localPath)
                except:
                    pass

            localPath = decompressedFile
            isOriginalFile = False

        # Return successfully.

        return localPath, isOriginalFile


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
