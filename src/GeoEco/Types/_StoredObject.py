# _StoredObject.py - Classes derived from ..Metadata.TypeMetadata that
# represent stored objects such as files and directories.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

##### THIS MODULE IS NOT MEANT TO BE IMPORTED DIRECTLY. IMPORT Types.py INSTEAD. #####

import os
import pathlib
import re
import sys

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from ._Base import _RaiseException, UnicodeStringTypeMetadata


class StoredObjectTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self,
                 typeDisplayName,
                 isPath=True,
                 canBeRelativePath=True,
                 basePathArgument=None,
                 useArcGISWorkspace=True,
                 normalizePath=True,
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 mustNotExist=False,
                 deleteIfParameterIsTrue=None,
                 createParentDirectories=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Geoprocessing.GPStringTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        assert isinstance(typeDisplayName, str), 'typeDisplayName must be a string'
        assert isinstance(isPath, bool), 'isPath must be a boolean'
        assert isinstance(canBeRelativePath, bool), 'canBeRelativePath must be a boolean'
        assert not (canBeRelativePath and not isPath), 'If canBeRelativePath is True, isPath must also be True'
        assert isinstance(basePathArgument, (str, type(None))), 'basePathArgument must be a string, or None'
        assert not (basePathArgument is not None and not canBeRelativePath), 'If basePathArgument is not None, canBeRelativePath must also be True'
        assert isinstance(useArcGISWorkspace, bool), 'useArcGISWorkspace must be a boolean'
        assert not (useArcGISWorkspace and not canBeRelativePath), 'If useArcGISWorkspace is True, canBeRelativePath must also be True'
        assert isinstance(normalizePath, bool), 'normalizePath must be a boolean'
        assert isinstance(mustExist, bool), 'mustExist must be a boolean'
        assert isinstance(mustNotExist, bool), 'mustNotExist must be a boolean'
        assert not mustExist or not mustNotExist, 'mustExist and mustNotExist cannot both be True'
        assert isinstance(deleteIfParameterIsTrue, (str, type(None))), 'deleteIfParameterIsTrue must be a string, or None'
        assert not mustNotExist or deleteIfParameterIsTrue is None, 'deleteIfParameterIsTrue must be None if mustNotExist is True'
        assert isinstance(createParentDirectories, bool), 'createParentDirectories must be a boolean'
        super(StoredObjectTypeMetadata, self).__init__(minLength=minLength,
                                                       maxLength=maxLength,
                                                       mustMatchRegEx=mustMatchRegEx,
                                                       canBeNone=canBeNone,
                                                       arcGISType=arcGISType,
                                                       arcGISAssembly=arcGISAssembly,
                                                       canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                       canBeArcGISOutputParameter=canBeArcGISOutputParameter)
        self._TypeDisplayName = typeDisplayName
        self._IsPath = isPath
        self._CanBeRelativePath = canBeRelativePath
        self._BasePathArgument = basePathArgument
        self._UseArcGISWorkspace = useArcGISWorkspace
        self._NormalizePath = normalizePath
        self._MustBeDifferentThanArguments = mustBeDifferentThanArguments
        self._MustExist = mustExist
        self._MustNotExist = mustNotExist
        self._DeleteIfParameterIsTrue = deleteIfParameterIsTrue
        self._CreateParentDirectories = createParentDirectories

    def _GetTypeDisplayName(self):
        return self._TypeDisplayName
    
    TypeDisplayName = property(_GetTypeDisplayName)

    def _GetIsPath(self):
        return self._IsPath
    
    IsPath = property(_GetIsPath)

    def _GetCanBeRelativePath(self):
        return self._CanBeRelativePath
    
    CanBeRelativePath = property(_GetCanBeRelativePath)

    def _GetBasePathArgument(self):
        return self._BasePathArgument

    def _SetBasePathArgument(self, value):
        assert isinstance(value, (str, type(None))), 'BasePathArgument must be a string, or None'
        self._BasePathArgument = value
    
    BasePathArgument = property(_GetBasePathArgument, _SetBasePathArgument)

    def _GetUseArcGISWorkspace(self):
        return self._UseArcGISWorkspace
    
    UseArcGISWorkspace = property(_GetUseArcGISWorkspace)

    def _GetNormalizePath(self):
        return self._NormalizePath
    
    NormalizePath = property(_GetNormalizePath)

    def _GetMustBeDifferentThanArguments(self):
        return self._MustBeDifferentThanArguments

    def _SetMustBeDifferentThanArguments(self, value):
        assert isinstance(value, (list, tuple, type(None))), 'MustBeDifferentThanArguments must be a list or tuple of strings, or None'
        if value is not None:
            if isinstance(value, tuple):
                value = list(value)
            for v in value:
                assert isinstance(value, str), 'MustBeDifferentThanArguments must be a list or tuple of strings, or None'
        self._MustBeDifferentThanArguments = value
    
    MustBeDifferentThanArguments = property(_GetMustBeDifferentThanArguments, _SetMustBeDifferentThanArguments)

    def _GetMustExist(self):
        return self._MustExist

    def _SetMustExist(self, value):
        assert isinstance(value, bool), 'MustExist must be a boolean'
        self._MustExist = value
    
    MustExist = property(_GetMustExist, _SetMustExist)

    def _GetMustNotExist(self):
        return self._MustNotExist

    def _SetMustNotExist(self, value):
        assert isinstance(value, bool), 'MustNotExist must be a boolean'
        self._MustNotExist = value
    
    MustNotExist = property(_GetMustNotExist, _SetMustNotExist)

    def _GetDeleteIfParameterIsTrue(self):
        return self._DeleteIfParameterIsTrue

    def _SetDeleteIfParameterIsTrue(self, value):
        assert isinstance(value, (str, type(None))), 'DeleteIfParameterIsTrue must be a string, or None'
        self._DeleteIfParameterIsTrue = value
    
    DeleteIfParameterIsTrue = property(_GetDeleteIfParameterIsTrue, _SetDeleteIfParameterIsTrue)

    def _GetCreateParentDirectories(self):
        return self._CreateParentDirectories

    def _SetCreateParentDirectories(self, value):
        assert isinstance(value, bool), 'CreateParentDirectories must be a boolean'
        self._CreateParentDirectories = value
    
    CreateParentDirectories = property(_GetCreateParentDirectories, _SetCreateParentDirectories)

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        valueChanged = False
        if self.IsPath and isinstance(value, pathlib.Path):
            value = str(value)
            valueChanged = True

        (valueChanged2, value) = super(StoredObjectTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        valueChanged = valueChanged or valueChanged2

        if value is not None:
            exists = None
            isCorrectType = None
            
            if self.IsPath:
                valueChanged2, value, exists, isCorrectType = self._CanonicalizePath(value, argMetadata, methodLocals)
                valueChanged = valueChanged or valueChanged2

            if self.MustBeDifferentThanArguments is not None and methodLocals is not None:
                for arg in self.MustBeDifferentThanArguments:
                    assert arg in methodLocals, _('To validate the %(param1)s of the method being validated, that method must also have an parameter named %(param2)s.') % {'param1' : variableName, 'param2' : arg}
                    if value == methodLocals[arg]:
                        same = True
                    elif hasattr(os.path,'samefile'):
                        try:
                            same = os.path.samefile(value, methodLocals[arg])
                        except OSError:
                            same = False
                    else:
                        same = os.path.normcase(os.path.abspath(value)) == os.path.normcase(os.path.abspath(methodLocals[arg]))
                    if same:
                        _RaiseException(ValueError(_('The %(param1)s and the %(param2)s parameter refer to the same %(type)s (%(value)s). You must not specify the same %(type)s.') % {'param1' : variableName, 'param2' : arg, 'type' : self.TypeDisplayName, 'value' : value}))

            from ..Logging import Logger
            oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
            Logger.SetLogInfoAsDebug(True)
            try:

                if self.MustExist or self.MustNotExist or self.DeleteIfParameterIsTrue is not None:
                    assert self.DeleteIfParameterIsTrue is None or self.DeleteIfParameterIsTrue in methodLocals, _('To validate the %(param1)s of the method being validated, that method must also have an parameter named %(param2)s.') % {'param1' : variableName, 'param2' : self.DeleteIfParameterIsTrue}
                    if exists is None:
                        exists, isCorrectType = self.Exists(value, argMetadata, methodLocals)
                    if exists:
                        if isCorrectType:
                            if self.MustNotExist or self.DeleteIfParameterIsTrue is not None and not methodLocals[self.DeleteIfParameterIsTrue]:
                                _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, already exists. Please delete it and try again, or specify a non-existing %(type)s.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName}))
                            if self.DeleteIfParameterIsTrue is not None and methodLocals[self.DeleteIfParameterIsTrue]:
                                self.Delete(value, argMetadata, methodLocals)
                        else:
                            if self.MustNotExist:
                                _RaiseException(ValueError(_('The value specified for the %(variable)s, %(value)s, already exists although it is not a %(type)s. Please delete it and try again, or specify a non-existing object.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName}))
                            if self.MustExist or self.DeleteIfParameterIsTrue is not None:
                                _RaiseException(ValueError(_('The value specified for the %(variable)s, %(value)s, exists but it is not a %(type)s. Please specify a %(type)s.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName}))
                    elif self.MustExist:
                        _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, does not exist. Please specify an existing %(type)s.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName}))

                if self.CreateParentDirectories and (re.match('^[A-Za-z]:[\\\\/]', value) or re.match('^[\\\\/]', value)) and \
                        not (os.path.dirname(value).lower().endswith('.gdb') and os.path.isdir(os.path.dirname(value)) or
                             os.path.dirname(os.path.dirname(value)).lower().endswith('.gdb') and os.path.isdir(os.path.dirname(os.path.dirname(value))) or
                             os.path.dirname(value).lower().endswith('.sde') and os.path.isfile(os.path.dirname(value)) or
                             os.path.dirname(os.path.dirname(value)).lower().endswith('.sde') and os.path.isdir(os.path.dirname(os.path.dirname(value)))):
                    
                    from ..DataManagement.Directories import Directory
                    Directory.Create(os.path.dirname(value))

            finally:
                Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)
            
        return (valueChanged, value)

    def _CanonicalizePath(self, value, argMetadata, methodLocals):
        valueChanged = False
        
        if self.IsRelativePath(value):
            if not self.CanBeRelativePath:
                _RaiseException(ValueError(_('The %(variable)s specifies the relative path "%(value)s" but relative paths are not allowed. Please provide an absolute path and try again.') % {'variable' : variableName, 'value' : value}))
                
            madeAbsolute = False

            if self.BasePathArgument is not None:
                if self.BasePathArgument not in methodLocals:
                    _RaiseException(RuntimeError(_('Programming error in this tool. The metadata for the %(variable)s specifies that when the caller provides a relative path, the base path can be obtained from the %(base)s parameter, but that parameter does not exist. Please contact the author of this tool for assistance.') % {'variable' : variableName, 'base': self.BasePathArgument}))
                if methodLocals[self.BasePathArgument] is not None:
                    value2 = os.path.join(methodLocals[self.BasePathArgument], value)
                    if value != value2:
                        value = value2
                        valueChanged = True
                    madeAbsolute = True

            if not madeAbsolute and self.UseArcGISWorkspace:
                from ..ArcGIS import GeoprocessorManager
                gp = GeoprocessorManager.GetWrappedGeoprocessor()
                if gp is not None and isinstance(gp.env.workspace, str) and len(gp.env.workspace) > 0:
                    value2 = os.path.join(gp.env.workspace, value)
                    if value != value2:
                        value = value2
                        valueChanged = True
                    madeAbsolute = True

            if not madeAbsolute:
                value2 = os.path.abspath(value)
                if value != value2:
                    value = value2
                    valueChanged = True

        if self.NormalizePath:
            value2 = os.path.normpath(value)
            if value != value2:
                value = value2
                valueChanged = True

        return valueChanged, value, None, None      # valueChanged, value, exists, isCorrectType

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        if isinstance(cls, StoredObjectTypeMetadata):
            className = cls.__class__.__name__
        else:
            className = cls.__name__
        _RaiseException(NotImplementedError('Programming error in the %s class: the class does not implement the Exists method.' % className))

    def GetConstraintDescriptionStrings(self):
        constraints = super(StoredObjectTypeMetadata, self).GetConstraintDescriptionStrings()
        if self.MustExist:
            constraints.append('Must exist.')
        if self.MustNotExist:
            constraints.append('Must not exist.')
        if self.MustBeDifferentThanArguments is not None and len(self.MustBeDifferentThanArguments) > 0:
            if len(self.MustBeDifferentThanArguments) == 1:
                constraints.append('Must be different than `%s`' % self.MustBeDifferentThanArguments[0])
            elif len(self.MustBeDifferentThanArguments) == 2:
                constraints.append('Must be different than `%s` and `%s`' % (self.MustBeDifferentThanArguments[0], self.MustBeDifferentThanArguments[1]))
            else:
                constraints.append('Must must be different than %s and `%s`' % (', '.join(['`' + arg + '`' for arg in self.MustBeDifferentThanArguments[:-1]]), self.MustBeDifferentThanArguments[-1]))
        return constraints

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        if isinstance(cls, StoredObjectTypeMetadata):
            className = cls.__class__.__name__
        else:
            className = cls.__name__
        _RaiseException(NotImplementedError('Programming error in the %s class: the class does not implement the Delete method.' % className))

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        if isinstance(cls, StoredObjectTypeMetadata):
            className = cls.__class__.__name__
        else:
            className = cls.__name__
        _RaiseException(NotImplementedError('Programming error in the %s class: the class does not implement the Copy method.' % className))

    @classmethod
    def IsRelativePath(cls, p):
        if p is None:
            return False
        if sys.platform == 'win32':
            if re.match(r'^[A-Za-z]:[\\\\/]', p) or re.match(r'^[\\\\/][\\\\/]\w', p):
                return False
        else:
            if p.startswith('/'):
                return False
        return True


class FileTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 mayBeCompressed=False,
                 decompressedFileToUse='*',
                 typeDisplayName=_('file'),
                 canBeRelativePath=True,
                 basePathArgument=None,
                 useArcGISWorkspace=True,
                 normalizePath=True,
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 mustNotExist=False,
                 deleteIfParameterIsTrue=None,
                 createParentDirectories=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Catalog.DEFileTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Catalog',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        assert isinstance(mayBeCompressed, bool), 'mayBeCompressed must be a boolean'
        super(FileTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
                                               isPath=True,
                                               canBeRelativePath=canBeRelativePath,
                                               basePathArgument=basePathArgument,
                                               useArcGISWorkspace=useArcGISWorkspace,
                                               normalizePath=normalizePath,
                                               mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                               mustExist=mustExist,
                                               mustNotExist=mustNotExist,
                                               deleteIfParameterIsTrue=deleteIfParameterIsTrue,
                                               createParentDirectories=createParentDirectories,
                                               minLength=minLength,
                                               maxLength=maxLength,
                                               mustMatchRegEx=mustMatchRegEx,
                                               canBeNone=canBeNone,
                                               arcGISType=arcGISType,
                                               arcGISAssembly=arcGISAssembly,
                                               canBeArcGISInputParameter=canBeArcGISInputParameter,
                                               canBeArcGISOutputParameter=canBeArcGISOutputParameter)

        self._MayBeCompressed = mayBeCompressed
        self._DecompressedFileToUse = decompressedFileToUse

    def _GetMayBeCompressed(self):
        return self._MayBeCompressed
    
    MayBeCompressed = property(_GetMayBeCompressed)

    def _GetDecompressedFileToUse(self):
        return self._DecompressedFileToUse
    
    DecompressedFileToUse = property(_GetDecompressedFileToUse)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'DEFile'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        return os.path.exists(name), os.path.isfile(name)

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..DataManagement.Files import File
        File.Delete(name)

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..DataManagement.Files import File
        File.Copy(source, dest, overwriteExisting=overwriteExisting)


class TextFileTypeMetadata(FileTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 mayBeCompressed=False,
                 decompressedFileToUse='*',
                 typeDisplayName=_('text file'),
                 canBeRelativePath=True,
                 basePathArgument=None,
                 useArcGISWorkspace=True,
                 normalizePath=True,
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 mustNotExist=False,
                 deleteIfParameterIsTrue=None,
                 createParentDirectories=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Catalog.DETextFileTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Catalog',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        super(TextFileTypeMetadata, self).__init__(mayBeCompressed=mayBeCompressed,
                                                   decompressedFileToUse=decompressedFileToUse,
                                                   typeDisplayName=typeDisplayName,
                                                   canBeRelativePath=canBeRelativePath,
                                                   basePathArgument=basePathArgument,
                                                   useArcGISWorkspace=useArcGISWorkspace,
                                                   normalizePath=normalizePath,
                                                   mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                                   mustExist=mustExist,
                                                   mustNotExist=mustNotExist,
                                                   deleteIfParameterIsTrue=deleteIfParameterIsTrue,
                                                   createParentDirectories=createParentDirectories,
                                                   minLength=minLength,
                                                   maxLength=maxLength,
                                                   mustMatchRegEx=mustMatchRegEx,
                                                   canBeNone=canBeNone,
                                                   arcGISType=arcGISType,
                                                   arcGISAssembly=arcGISAssembly,
                                                   canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                   canBeArcGISOutputParameter=canBeArcGISOutputParameter)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'DETextFile'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())


class DirectoryTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 typeDisplayName=_('directory'),
                 canBeRelativePath=True,
                 basePathArgument=None,
                 useArcGISWorkspace=True,
                 normalizePath=True,
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 mustNotExist=False,
                 deleteIfParameterIsTrue=None,
                 createParentDirectories=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Catalog.DEFolderTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Catalog',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        super(DirectoryTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
                                                    isPath=True,
                                                    canBeRelativePath=canBeRelativePath,
                                                    basePathArgument=basePathArgument,
                                                    useArcGISWorkspace=useArcGISWorkspace,
                                                    normalizePath=normalizePath,
                                                    mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                                    mustExist=mustExist,
                                                    mustNotExist=mustNotExist,
                                                    deleteIfParameterIsTrue=deleteIfParameterIsTrue,
                                                    createParentDirectories=createParentDirectories,
                                                    minLength=minLength,
                                                    maxLength=maxLength,
                                                    mustMatchRegEx=mustMatchRegEx,
                                                    canBeNone=canBeNone,
                                                    arcGISType=arcGISType,
                                                    arcGISAssembly=arcGISAssembly,
                                                    canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                    canBeArcGISOutputParameter=canBeArcGISOutputParameter)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'DEFolder'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..DataManagement.Directories import Directory
        return Directory.Exists(name)

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..DataManagement.Directories import Directory
        Directory.Delete(name, removeTree=True)

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..DataManagement.Directories import Directory
        Directory.Copy(source, dest, deleteExistingDestinationDirectory=overwriteExisting, overwriteExistingFiles=overwriteExisting)


###############################################################################
# Names exported by this module
#
# Note: This module is not meant to be imported directly. Import Types.py
# instead.
###############################################################################

__all__ = []
