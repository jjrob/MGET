# _ArcGIS.py - Classes derived from .Metadata.TypeMetadata that represent
# ArcGIS data types, such as feature classes and rasters.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

##### THIS MODULE IS NOT MEANT TO BE IMPORTED DIRECTLY. IMPORT Types.py INSTEAD. #####

import os
import re

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from ._Base import _RaiseException, UnicodeStringTypeMetadata
from ._StoredObject import StoredObjectTypeMetadata, FileTypeMetadata


class ArcGISGeoDatasetTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 typeDisplayName=_('geographic dataset'),
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
                 arcGISType='ESRI.ArcGIS.Geoprocessing.DEGeoDatasetTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        super(ArcGISGeoDatasetTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
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
        return {'type': 'DEGeoDatasetType'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _CanonicalizePath(self, value, argMetadata, methodLocals):
        
        # It could be a layer or it could be a path to something.
        # Layers will already exist and do not require
        # canonicalization. If the value already exists, assume it is
        # a layer and return successfully. (Note that it might not be
        # the correct type, but this will be handled by
        # StoredObjectTypeMetadata.ValidateValue).
        
        exists, isCorrectType = self.Exists(value, argMetadata, methodLocals)
        if exists:
            return False, value, exists, isCorrectType

        # It did not exist. Canonicalize it.

        valueChanged, value, exists, isCorrectType = super(ArcGISGeoDatasetTypeMetadata, self)._CanonicalizePath(value, argMetadata, methodLocals)

        # If the canonicalized form is different than the original, we
        # have to check its existence again later, if necessary.
        # Return None for the existence parameters.
        
        if valueChanged:
            return True, value, None, None

        # The canonicalized form is no different than the orginal.
        # Therefore it will not be necessary to check its existence
        # again later. Return the results of our check.
        
        return False, value, False, False

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):

        # See if it exists.
        
        from ..Logging import Logger
        from ..ArcGIS import GeoprocessorManager
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        if gp is None:
            Logger.RaiseException(RuntimeError(_('The ArcGIS geoprocessor must be initialized before this function may be called. Please call GeoprocessorManager.InitializeGeoprocessor or GeoprocessorManager.SetGeoprocessor before calling this function.')))
        exists = gp.Exists(name)
        isCorrectType = False

        # If it exists, see if the describe object has an Extent
        # property. If it does, then it is a "geodataset".
        
        if exists:
            d = gp.Describe(name)
            isCorrectType = d is not None and hasattr(d, 'Extent') and d.Extent is not None

        # Log a debug message indicating what happened.
        
        if not exists:
            Logger.Debug(_('The geographic dataset %(path)s does not exist.') % {'path': name})
        else:
            if isCorrectType:
                Logger.Debug(_('The geographic dataset %(path)s exists.') % {'path': name})
            else:
                Logger.Debug(_('%(path)s exists but it is a %(actual)s, not a geographic dataset.') % {'path': name, 'actual': d.DataType})

        # Return the results.
        
        return (exists, isCorrectType)


class ArcGISRasterTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 allowedPixelTypes=None,
                 typeDisplayName=_('raster'),
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
                 arcGISType='ESRI.ArcGIS.DataSourcesRaster.DERasterDatasetTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.DataSourcesRaster',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):

        assert isinstance(allowedPixelTypes, (type(None), list, tuple)), 'allowedPixelTypes must be a list or tuple of Unicode strings, or None.'
        if isinstance(allowedPixelTypes, tuple):
            allowedPixelTypes = list(allowedPixelTypes)
        if allowedPixelTypes is not None:
            for s in allowedPixelTypes:
                assert isinstance(s, str), 'allowedPixelTypes must be a list or tuple of Unicode strings, or None.'
            self._AllowedPixelTypes = list(map(str.strip, list(map(str.lower, allowedPixelTypes))))
        else:
            self._AllowedPixelTypes = None
        
        super(ArcGISRasterTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
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
        return {'type': 'DERasterDataset'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetAllowedPixelTypes(self):
        return self._AllowedPixelTypes
    
    AllowedPixelTypes = property(_GetAllowedPixelTypes, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        # Before invoking the super-class ValidateValue function,
        # temporarily set the CreateParentDirectories property to
        # False. This is a hack; it prevents the super-class from
        # creating a subdirectory in a file geodatabase directory.
        # Rather than creating a subdirectory, a raster catalog must
        # be created; that is handled below.

        createParentDirectories = self.CreateParentDirectories
        self.CreateParentDirectories = False
        try:
            (valueChanged, value) = super(ArcGISRasterTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        finally:
            self.CreateParentDirectories = createParentDirectories

        if value is not None:
            from ..ArcGIS import GeoprocessorManager
            gp = GeoprocessorManager.GetWrappedGeoprocessor()

            # If it is an output argument, validate the path and name
            # (see MGET tickets #82 and #362).
            
            if argMetadata is not None and argMetadata.Direction == 'Output':

                # Break down the the path into components (i.e.
                # subdirectories). The path was already canonicalized,
                # so if it does not include a root directory, it is a
                # layer and we do not need to perform additional
                # validation here.

                components = []
                path, component = os.path.split(value)
                if path is not None and len(path) > 0:
                    while True:
                        if component is not None and len(component) > 0:
                            components.insert(0, component)
                        path, component = os.path.split(path)
                        if component is None or len(component) <= 0:
                            components.insert(0, path)
                            break

                    if len(components) >= 2 and components[0] == '\\\\':
                        components = [components[0] + components[1]] + components[2:]
                        if len(components) >= 2:
                            components = [os.path.join(components[0], components[1])] + components[2:]

                    # Only proceed if the path includes a root
                    # directory plus at least one additional
                    # component.

                    if len(components) >= 2 and os.path.isdir(components[0]):
                        path = components[0]
                        inDirectory = True
                        inGDB = False
                        i = 1

                        # Walk down the path components.
                        
                        while i < len(components):
                            newPath = os.path.join(path, components[i])

                            # If everything up to this point is a
                            # geodatabase (personal GDB or file GDB),
                            # there may be one or two remaining
                            # components. If there is just one, it is
                            # a raster name. If there are two, the
                            # first is a raster catalog name and the
                            # second is a raster name. In that case,
                            # create the raster catalog if it does not
                            # already exist.

                            if inGDB:
                                if i < len(components) - 2:
                                    _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, is not a valid raster path. Because %(gdb)s is a geodatabase, it must be followed by only one or two additional path components (if there are two, the first is the name of a raster catalog and the second is the name of a raster).') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'gdb': path}))
                                if i == len(components) - 2:
                                    catalogName = components[i]
                                    rasterName = components[i+1]
                                else:
                                    catalogName = None
                                    rasterName = components[i]

                                if catalogName is not None:
                                    if not(catalogName[0] >= 'a' and catalogName[0] <= 'z' or catalogName[0] >= 'A' and catalogName[0] <= 'Z'):
                                        _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, does not contain a valid raster catalog name: the name "%(name)s" does not begin with a letter (a-z or A-Z). Please provide a raster catalog name that begins with a letter.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': catalogName}))
                                    if re.match('^[a-zA-Z0-9_]+$', catalogName) is None:
                                        _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, does not contain a valid raster catalog name: the name "%(name)s" contains characters that are not letters (a-z and A-Z), numbers (0-9), or the underscore (_). Please provide a raster catalog name composed only of letters, numbers, and the underscore.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': catalogName}))

                                if not(rasterName[0] >= 'a' and rasterName[0] <= 'z' or rasterName[0] >= 'A' and rasterName[0] <= 'Z'):
                                    _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, does not contain a valid raster name: the name "%(name)s" does not begin with a letter (a-z or A-Z). Please provide a raster name that begins with a letter.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': rasterName}))
                                if re.match('^[a-zA-Z0-9_]+$', rasterName) is None:
                                    _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, does not contain a valid raster name: the name "%(name)s" contains characters that are not letters (a-z and A-Z), numbers (0-9), or the underscore (_). Please provide a raster name composed only of letters, numbers, and the underscore.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': rasterName}))

                                if catalogName is not None:
                                    if gp.Exists(os.path.join(path, catalogName)):
                                        if gp.Describe(os.path.join(path, catalogName)).DataType.lower() != 'rastercatalog':
                                            _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, does not contain a valid raster catalog name: %(name)s is an existing %(dt)s in that geodatabase. Please provide a the name of an existing raster catalog, or a name that does not exist (tool will create the raster catalog).') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': catalogName, 'dt': gp.Describe(os.path.join(path, catalogName)).DataType}))
                                    else:
                                        gp.CreateRasterCatalog_management(path, catalogName)
                                        Logger.Debug(_('Created raster catalog %s.'), os.path.join(path, catalogName))
                                    
                                break

                            # If everything up to this point is a
                            # directory, then the current component
                            # could be an existing file geodatabase,
                            # subdirectory, or personal geodatabase,
                            # or a non-existing raster (if it already
                            # existed, we deleted it above).
                            
                            elif inDirectory:

                                # If it is a file geodatabase, go on to the
                                # next deeper component in the path.
                                
                                if os.path.isdir(newPath):
                                    if newPath.lower().endswith('.gdb'):
                                        inGDB = True

                                # Otherwise, if it is the last
                                # component in the path, it is the
                                # name of the raster. Validate the
                                # name. Currently we only perform
                                # validation for ArcInfo Binary Grid
                                # format.

                                elif i == len(components) - 1:
                                    if components[i].find('.') < 0:     # If it has no extension, it is ArcInfo Binary Grid format.
                                        if len(components[i]) > 13:
                                            _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, is not a valid name for a raster in ArcInfo Binary Grid format: the name "%(name)s" exceeds 13 characters. Please provide a name that is 13 characters or less.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': components[i]}))
                                        if not(components[i][0] >= 'a' and components[i][0] <= 'z' or components[i][0] >= 'A' and components[i][0] <= 'Z'):
                                            _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, is not a valid name for a raster in ArcInfo Binary Grid format: the name "%(name)s" does not begin with a letter (a-z or A-Z). Please provide a name that begins with a letter.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': components[i]}))
                                        if re.match('^[a-zA-Z0-9_]+$', components[i]) is None:
                                            _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, is not a valid name for a raster in ArcInfo Binary Grid format: the name "%(name)s" contains characters that are not letters (a-z and A-Z), numbers (0-9), or the underscore (_). Please provide a name composed only of letters, numbers, and the underscore.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'name': components[i]}))

                                # Otherwise it is a non-existing
                                # subdirectory. Create it, if
                                # requested by the metadata.

                                else:
                                    os.mkdir(newPath)
                                    from ..Logging import Logger
                                    Logger.Debug(_('Created directory %s.'), newPath)
                            
                            # Proceed to the next deeper component of
                            # the path.
                            
                            i += 1
                            path = newPath

            # Otherwise (it is an input argument), perform other validation.
            
            elif self.AllowedPixelTypes is not None:
                if gp.Exists(value) and gp.Describe(value).PixelType.lower() not in self.AllowedPixelTypes:
                    if len(self.AllowedPixelTypes) == 1:
                        _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, is a %(pt)s %(type)s but this function requires a %(allowed)s %(type)s. Please provide a %(allowed)s %(type)s.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'pt': self.GetPixelTypeName(gp.Describe(value).PixelType), 'allowed': self.GetPixelTypeName(self.AllowedPixelTypes[0])}))
                    else:
                        _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, is a %(pt)s %(type)s but this function requires a %(type)s with one of the following pixel types: %(allowed)s. Please provide a %(type)s with an allowed pixel type.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'pt': self.GetPixelTypeName(gp.Describe(value).PixelType), 'allowed': str('\', \''.join(map(self.GetPixelTypeName, self.AllowedPixelTypes)))}))

        return (valueChanged, value)

    def GetPixelTypeName(self, pixelType):
        name = _('unknown data type')
        if isinstance(pixelType, str) and len(pixelType) >= 2:
            if pixelType[0] == '' or pixelType[0] == '':
                name = _('%s-bit unsigned integer') % pixelType[1:]
            elif pixelType[0] == 's' or pixelType[0] == 'S':
                name = _('%s-bit signed integer') % pixelType[1:]
            elif pixelType[0] == 'f' or pixelType[0] == 'F':
                name = _('%s-bit floating point') % pixelType[1:]
        return name

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..DataManagement.ArcGISRasters import ArcGISRaster
        return ArcGISRaster.Exists(name)

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..DataManagement.ArcGISRasters import ArcGISRaster
        ArcGISRaster.Delete(name)

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..DataManagement.ArcGISRasters import ArcGISRaster
        ArcGISRaster.Copy(source, dest, overwriteExisting=overwriteExisting)


class ArcGISRasterLayerTypeMetadata(ArcGISRasterTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 allowedPixelTypes=None,
                 typeDisplayName=_('raster or raster layer'),
                 canBeRelativePath=True,
                 basePathArgument=None,
                 useArcGISWorkspace=True,
                 normalizePath=True,
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Geoprocessing.GPRasterLayerTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing'):
        
        super(ArcGISRasterLayerTypeMetadata, self).__init__(allowedPixelTypes=allowedPixelTypes,
                                                            typeDisplayName=typeDisplayName,
                                                            canBeRelativePath=canBeRelativePath,
                                                            basePathArgument=basePathArgument,
                                                            useArcGISWorkspace=useArcGISWorkspace,
                                                            normalizePath=normalizePath,
                                                            mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                                            mustExist=mustExist,
                                                            minLength=minLength,
                                                            maxLength=maxLength,
                                                            mustMatchRegEx=mustMatchRegEx,
                                                            canBeNone=canBeNone,
                                                            arcGISType=arcGISType,
                                                            arcGISAssembly=arcGISAssembly)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPRasterLayer'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _CanonicalizePath(self, value, argMetadata, methodLocals):
        
        # It could be a layer or it could be a path to something.
        # Layers will already exist and do not require
        # canonicalization. If the value already exists, assume it is
        # a layer and return successfully. (Note that it might not be
        # the correct type, but this will be handled by
        # StoredObjectTypeMetadata.ValidateValue).
        
        exists, isCorrectType = self.Exists(value, argMetadata, methodLocals)
        if exists:
            return False, value, exists, isCorrectType

        # It did not exist. Canonicalize it.

        valueChanged, value, exists, isCorrectType = super(ArcGISRasterLayerTypeMetadata, self)._CanonicalizePath(value, argMetadata, methodLocals)

        # If the canonicalized form is different than the original, we
        # have to check its existence again later, if necessary.
        # Return None for the existence parameters.
        
        if valueChanged:
            return True, value, None, None

        # The canonicalized form is no different than the orginal.
        # Therefore it will not be necessary to check its existence
        # again later. Return the results of our check.
        
        return False, value, False, False

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        return GeoprocessorManager.ArcGISObjectExists(name, ['rasterdataset', 'rasterlayer', 'rasterband'], _('ArcGIS raster, raster layer, or raster band'))


class ArcGISRasterCatalogTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 typeDisplayName=_('raster catalog'),
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
                 arcGISType='ESRI.ArcGIS.Geodatabase.DERasterCatalogTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geodatabase',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
                
        super(ArcGISRasterCatalogTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
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
        return {'type': 'DERasterCatalog'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        return GeoprocessorManager.ArcGISObjectExists(name, ['raster catalog'], _('ArcGIS raster catalog'))

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.DeleteArcGISObject(name, ['raster catalog'], _('ArcGIS raster catalog'))

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.CopyArcGISObject(source, dest, overwriteExisting, ['raster catalog'], _('ArcGIS raster catalog'))


class ArcGISFeatureClassTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 allowedShapeTypes=None,
                 typeDisplayName=_('feature class'),
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
                 arcGISType='ESRI.ArcGIS.Geodatabase.DEFeatureClassTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geodatabase',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):

        assert isinstance(allowedShapeTypes, (type(None), list, tuple)), 'allowedShapeTypes must be a list or tuple of Unicode strings, or None.'
        if isinstance(allowedShapeTypes, tuple):
            allowedShapeTypes = list(allowedShapeTypes)
        if allowedShapeTypes is not None:
            for s in allowedShapeTypes:
                assert isinstance(s, str), 'allowedShapeTypes must be a list or tuple of Unicode strings, or None.'
            self._AllowedShapeTypes = list(map(str.strip, list(map(str.lower, allowedShapeTypes))))
        else:
            self._AllowedShapeTypes = None
                
        super(ArcGISFeatureClassTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
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

    def _GetAllowedShapeTypes(self):
        return self._AllowedShapeTypes
    
    AllowedShapeTypes = property(_GetAllowedShapeTypes, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'DEFeatureClass'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):
        if self.AllowedShapeTypes is not None:
            geometryTypes = []
            for ast in self.AllowedShapeTypes:
                if ast.lower() == 'point':
                    geometryTypes.append('Point')
                elif ast.lower() == 'polyline':
                    geometryTypes.append('Polyline')
                elif ast.lower() == 'polygon':
                    geometryTypes.append('Polygon')
                elif ast.lower() == 'multipoint':
                    geometryTypes.append('Multipoint')
                elif ast.lower() == 'multipatch':
                    geometryTypes.append('MultiPatch')
                else:
                    raise NotImplementedError(_('%(cls)s._GetArcGISDomainDict() does not recognize the AllowedShapeType of %(ast)r.') % {'cls': self.__class__.__name__, 'ast': ast})
            return {'type': 'GPFeatureClassDomain', 'geometrytype': geometryTypes}

        return None

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(ArcGISFeatureClassTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None and self.AllowedShapeTypes is not None:
            from ..ArcGIS import GeoprocessorManager
            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            if gp.Exists(value) and gp.Describe(value).ShapeType.lower() not in self.AllowedShapeTypes:
                if len(self.AllowedShapeTypes) == 1:
                    _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, has the shape type \'%(shape)s\', but this function requires a %(type)s with the shape type \'%(allowed)s\'. Please provide a %(type)s with shape type \'%(allowed)s\'.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'shape': gp.Describe(value).ShapeType.lower(), 'allowed': self.AllowedShapeTypes[0]}))
                else:
                    _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, has the shape type \'%(shape)s\', but this function requires a %(type)s with one of the following shape types: \'%(allowed)s\'. Please provide a %(type)s with an allowed shape type.') % {'type' : self.TypeDisplayName, 'value' : value, 'variable' : variableName, 'shape': gp.Describe(value).ShapeType.lower(), 'allowed': str('\', \''.join(map(str, self.AllowedShapeTypes)))}))
        return (valueChanged, value)

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        return GeoprocessorManager.ArcGISObjectExists(name, ['featureclass', 'shapefile'], _('ArcGIS feature class'))

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.DeleteArcGISObject(name, ['featureclass', 'shapefile'], _('ArcGIS feature class'))

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.CopyArcGISObject(source, dest, overwriteExisting, ['featureclass', 'shapefile'], _('ArcGIS feature class'))


class ArcGISFeatureLayerTypeMetadata(ArcGISFeatureClassTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 allowedShapeTypes=None,
                 typeDisplayName=_('feature class or layer'),
                 canBeRelativePath=True,
                 basePathArgument=None,
                 useArcGISWorkspace=True,
                 normalizePath=True,
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Geoprocessing.GPFeatureLayerTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing'):
                
        super(ArcGISFeatureLayerTypeMetadata, self).__init__(allowedShapeTypes=allowedShapeTypes,
                                                             typeDisplayName=typeDisplayName,
                                                             canBeRelativePath=canBeRelativePath,
                                                             basePathArgument=basePathArgument,
                                                             useArcGISWorkspace=useArcGISWorkspace,
                                                             normalizePath=normalizePath,
                                                             mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                                             mustExist=mustExist,
                                                             minLength=minLength,
                                                             maxLength=maxLength,
                                                             mustMatchRegEx=mustMatchRegEx,
                                                             canBeNone=canBeNone,
                                                             arcGISType=arcGISType,
                                                             arcGISAssembly=arcGISAssembly)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPFeatureLayer'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _CanonicalizePath(self, value, argMetadata, methodLocals):
        
        # It could be a layer or it could be a path to something.
        # Layers will already exist and do not require
        # canonicalization. If the value already exists, assume it is
        # a layer and return successfully. (Note that it might not be
        # the correct type, but this will be handled by
        # StoredObjectTypeMetadata.ValidateValue).
        
        exists, isCorrectType = self.Exists(value, argMetadata, methodLocals)
        if exists:
            return False, value, exists, isCorrectType

        # It did not exist. Canonicalize it.

        valueChanged, value, exists, isCorrectType = super(ArcGISFeatureLayerTypeMetadata, self)._CanonicalizePath(value, argMetadata, methodLocals)

        # If the canonicalized form is different than the original, we
        # have to check its existence again later, if necessary.
        # Return None for the existence parameters.
        
        if valueChanged:
            return True, value, None, None

        # The canonicalized form is no different than the orginal.
        # Therefore it will not be necessary to check its existence
        # again later. Return the results of our check.
        
        return False, value, False, False

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        return GeoprocessorManager.ArcGISObjectExists(name, ['featureclass', 'shapefile', 'featurelayer'], _('ArcGIS feature class or layer'))


class ShapefileTypeMetadata(FileTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 typeDisplayName=_('shapefile'),
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
                 mustMatchRegEx=r'.+\.[Ss][Hh][Pp]$',
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Catalog.DEShapeFileTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Catalog',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        super(ShapefileTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
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
        return {'type': 'DEShapeFile'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..DataManagement.Shapefiles import Shapefile
        return Shapefile.Exists(name)

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..DataManagement.Shapefiles import Shapefile
        Shapefile.Delete(name)

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..DataManagement.Shapefiles import Shapefile
        Shapefile.Copy(source, dest, overwriteExisting=overwriteExisting)


class ArcGISWorkspaceTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 typeDisplayName=_('workspace'),
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
                 arcGISType='ESRI.ArcGIS.Geodatabase.DEWorkspaceTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geodatabase',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        super(ArcGISWorkspaceTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
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
        return {'type': 'DEWorkspace'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        return GeoprocessorManager.ArcGISObjectExists(name, ['workspace', 'folder'], _('ArcGIS workspace'))

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.DeleteArcGISObject(name, ['workspace', 'folder'], _('ArcGIS workspace'))

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.CopyArcGISObject(source, dest, overwriteExisting, ['workspace', 'folder'], _('ArcGIS workspace'))


class ArcGISTableTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 typeDisplayName=_('table'),
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
                 arcGISType='ESRI.ArcGIS.Geodatabase.DETableTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geodatabase',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        super(ArcGISTableTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
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
        return {'type': 'DETable'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        return GeoprocessorManager.ArcGISObjectExists(name, ['table', 'dbasetable', 'textfile', 'featureclass', 'shapefile', 'relationshipclass', 'rastercatalog', 'coveragefeatureclass', 'tableview', 'featurelayer', 'layer', 'arcinfotable'], _('ArcGIS table'))

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.DeleteArcGISObject(name, ['table', 'dbasetable', 'textfile', 'featureclass', 'shapefile', 'relationshipclass', 'rastercatalog', 'coveragefeatureclass', 'tableview', 'featurelayer', 'layer', 'arcinfotable'], _('ArcGIS table'))

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        GeoprocessorManager.CopyArcGISObject(source, dest, overwriteExisting, ['table', 'dbasetable', 'textfile', 'shapefile', 'featureclass', 'relationshipclass', 'rastercatalog', 'coveragefeatureclass', 'tableview', 'featurelayer', 'layer', 'arcinfotable'], _('ArcGIS table'))


class ArcGISTableViewTypeMetadata(ArcGISTableTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 typeDisplayName=_('table or table view'),
                 canBeRelativePath=True,
                 basePathArgument=None,
                 useArcGISWorkspace=True,
                 normalizePath=True,
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Geoprocessing.GPTableViewTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing'):
        
        super(ArcGISTableViewTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
                                                          canBeRelativePath=canBeRelativePath,
                                                          basePathArgument=basePathArgument,
                                                          useArcGISWorkspace=useArcGISWorkspace,
                                                          normalizePath=normalizePath,
                                                          mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                                          mustExist=mustExist,
                                                          minLength=minLength,
                                                          maxLength=maxLength,
                                                          mustMatchRegEx=mustMatchRegEx,
                                                          canBeNone=canBeNone,
                                                          arcGISType=arcGISType,
                                                          arcGISAssembly=arcGISAssembly)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPTableView'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _CanonicalizePath(self, value, argMetadata, methodLocals):
        
        # It could be a layer or it could be a path to something.
        # Layers will already exist and do not require
        # canonicalization. If the value already exists, assume it is
        # a layer and return successfully. (Note that it might not be
        # the correct type, but this will be handled by
        # StoredObjectTypeMetadata.ValidateValue).
        
        exists, isCorrectType = self.Exists(value, argMetadata, methodLocals)
        if exists:
            return False, value, exists, isCorrectType

        # It did not exist. Canonicalize it.

        valueChanged, value, exists, isCorrectType = super(ArcGISTableViewTypeMetadata, self)._CanonicalizePath(value, argMetadata, methodLocals)

        # If the canonicalized form is different than the original, we
        # have to check its existence again later, if necessary.
        # Return None for the existence parameters.
        
        if valueChanged:
            return True, value, None, None

        # The canonicalized form is no different than the orginal.
        # Therefore it will not be necessary to check its existence
        # again later. Return the results of our check.
        
        return False, value, False, False

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        from ..ArcGIS import GeoprocessorManager
        return GeoprocessorManager.ArcGISObjectExists(name, ['table', 'dbasetable', 'textfile', 'featureclass', 'shapefile', 'relationshipclass', 'rastercatalog', 'coveragefeatureclass', 'tableview', 'featurelayer', 'layer', 'arcinfotable'], _('ArcGIS table or table view'))


class ArcGISFieldTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 allowedFieldTypes=None,
                 typeDisplayName=_('field'),
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 mustNotExist=False,
                 deleteIfParameterIsTrue=None,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Geodatabase.FieldTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geodatabase',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):

        assert isinstance(allowedFieldTypes, (type(None), list, tuple)), 'allowedFieldTypes must be a list or tuple of Unicode strings, or None.'
        if isinstance(allowedFieldTypes, tuple):
            allowedFieldTypes = list(allowedFieldTypes)
        if allowedFieldTypes is not None:
            for s in allowedFieldTypes:
                assert isinstance(s, str), 'allowedFieldTypes must be a list or tuple of Unicode strings, or None.'
            self._AllowedFieldTypes = list(map(str.strip, list(map(str.lower, allowedFieldTypes))))
        else:
            self._AllowedFieldTypes = None
        
        super(ArcGISFieldTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
                                                      isPath=False,
                                                      canBeRelativePath=False,
                                                      basePathArgument=None,
                                                      useArcGISWorkspace=False,
                                                      normalizePath=False,
                                                      mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                                      mustExist=mustExist,
                                                      mustNotExist=mustNotExist,
                                                      deleteIfParameterIsTrue=deleteIfParameterIsTrue,
                                                      createParentDirectories=False,
                                                      minLength=minLength,
                                                      maxLength=maxLength,
                                                      mustMatchRegEx=mustMatchRegEx,
                                                      canBeNone=canBeNone,
                                                      arcGISType=arcGISType,
                                                      arcGISAssembly=arcGISAssembly,
                                                      canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                      canBeArcGISOutputParameter=canBeArcGISOutputParameter)

    def _GetAllowedFieldTypes(self):
        return self._AllowedFieldTypes
    
    AllowedFieldTypes = property(_GetAllowedFieldTypes, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'Field'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):
        if self.AllowedFieldTypes is not None:
            fieldTypes = []
            for aft in self.AllowedFieldTypes:
                if aft.lower() in ['short', 'int8', 'uint8', 'int16']:
                    fieldTypes.append('Short')
                elif aft.lower() in ['long', 'uint16', 'int32']:
                    fieldTypes.append('Long')
                elif aft.lower() in ['biginteger', 'uint32', 'int64', 'uint64']:    # We optimistically allow uint64
                    fieldTypes.append('BigInteger')
                elif aft.lower() in ['float', 'float32']:
                    fieldTypes.append('Float')
                elif aft.lower() in ['double', 'float64']:
                    fieldTypes.append('Double')
                elif aft.lower() in ['date', 'datetime']:
                    fieldTypes.append('Date')
                elif aft.lower() in ['text', 'string']:
                    fieldTypes.append('Text')
                elif aft.lower() in ['oid']:
                    fieldTypes.append('OID')
                else:
                    raise NotImplementedError(_('%(cls)s._GetArcGISDomainDict() does not recognize the AllowedFieldType of %(aft)r.') % {'cls': self.__class__.__name__, 'aft': aft})
            return {'type': 'GPFieldDomain', 'fieldtype': fieldTypes}

        return None

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(ArcGISFieldTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None and self.AllowedFieldTypes is not None and methodLocals is not None and argMetadata.ArcGISParameterDependencies is not None and len(argMetadata.ArcGISParameterDependencies) > 0 and methodLocals[argMetadata.ArcGISParameterDependencies[0]] is not None:
            from ..Datasets.ArcGIS import ArcGISTable
            table = ArcGISTable(methodLocals[argMetadata.ArcGISParameterDependencies[0]])
            field = table.GetFieldByName(value)
            if field is None:
                _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, does not exist.') % {'type' : self.TypeDisplayName, 'value' : os.path.join(methodLocals[argMetadata.ArcGISParameterDependencies[0]], value), 'variable' : variableName}))
            if field.DataType.lower() not in self.AllowedFieldTypes:
                if len(self.AllowedFieldTypes) == 1:
                    _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, has the data type \'%(dt)s\', but this function requires a %(type)s with the data type \'%(allowed)s\'. Please provide a %(type)s with data type \'%(allowed)s\'.') % {'type' : self.TypeDisplayName, 'value' : os.path.join(methodLocals[argMetadata.ArcGISParameterDependencies[0]], value), 'variable' : variableName, 'dt': field.DataType, 'allowed': self.AllowedFieldTypes[0]}))
                else:
                    _RaiseException(ValueError(_('The %(type)s %(value)s, specified for the %(variable)s, has the data type \'%(dt)s\', but this function requires a %(type)s with one of the following data types: \'%(allowed)s\'. Please provide a %(type)s with an allowed data type.') % {'type' : self.TypeDisplayName, 'value' : os.path.join(methodLocals[argMetadata.ArcGISParameterDependencies[0]], value), 'variable' : variableName, 'dt': field.DataType, 'allowed': str('\', \''.join(map(str, self.AllowedFieldTypes)))}))
        return (valueChanged, value)

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        assert methodLocals is not None and argMetadata is not None and argMetadata.ArcGISParameterDependencies is not None and len(argMetadata.ArcGISParameterDependencies) == 1, 'ArcGISFieldTypeMetadata.Exists requires that methodLocals and argMetadata be provided, and that argMetadata.ArcGISParameterDependencies[0] be set to the parameter that specifies the field\'s table.'
        from ..Datasets.ArcGIS import ArcGISTable
        table = ArcGISTable(methodLocals[argMetadata.ArcGISParameterDependencies[0]])
        field = table.GetFieldByName(name)
        return field is not None, field is not None

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        assert methodLocals is not None and argMetadata is not None and argMetadata.ArcGISParameterDependencies is not None and len(argMetadata.ArcGISParameterDependencies) == 1, 'ArcGISFieldTypeMetadata.Delete requires that methodLocals and argMetadata be provided, and that argMetadata.ArcGISParameterDependencies[0] be set to the parameter that specifies the field\'s table.'
        from ..Datasets.ArcGIS import ArcGISTable
        table = ArcGISTable(methodLocals[argMetadata.ArcGISParameterDependencies[0]])
        table.DeleteField(name, failIfDoesNotExist=False)

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        _RaiseException(NotImplementedError('ArcGISFieldTypeMetadata.Copy is not implemented.'))


class CoordinateSystemTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, 
                 treatUnknownCSAsNone=True, 
                 canBeNone=False):

        assert isinstance(treatUnknownCSAsNone, bool), 'treatUnknownCSAsNone must be a boolean'
        super(CoordinateSystemTypeMetadata, self).__init__(minLength=1,
                                                           maxLength=2147483647,
                                                           mustMatchRegEx=None,
                                                           canBeNone=canBeNone,
                                                           arcGISType='ESRI.ArcGIS.Geoprocessing.GPCoordinateSystemTypeClass',
                                                           arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                           canBeArcGISInputParameter=True,
                                                           canBeArcGISOutputParameter=True)
        self._TreatUnknownCSAsNone = treatUnknownCSAsNone

    def _GetTreatUnknownCSAsNone(self):
        return self._TreatUnknownCSAsNone
    
    TreatUnknownCSAsNone = property(_GetTreatUnknownCSAsNone, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPCoordinateSystem'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        valueChanged = False
        if self._TreatUnknownCSAsNone and isinstance(value, str) and value.strip().upper() == '{B286C06B-0879-11D2-AACA-00C04FA33C20}':
            value = None
            valueChanged = True
        (valueChanged2, value) = super(CoordinateSystemTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        return (valueChanged or valueChanged2, value)


class EnvelopeTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, canBeNone=False):
        super(EnvelopeTypeMetadata, self).__init__(minLength=1,
                                                   maxLength=2147483647,
                                                   mustMatchRegEx=r'([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)',
                                                   canBeNone=canBeNone,
                                                   arcGISType='ESRI.ArcGIS.Geoprocessing.GPEnvelopeTypeClass',
                                                   arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                   canBeArcGISInputParameter=True,
                                                   canBeArcGISOutputParameter=True)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPEnvelope'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def ParseFromArcGISString(cls, value):
        if value is None:
            return None, None, None, None

        # If value is a tuple or list with a length of 4, just return it (as a
        # tuple).

        if isinstance(value, list):
            value = tuple(value)

        if isinstance(value, tuple) and len(value) == 4 and all([isinstance(v, (float, int)) for v in value]):
            return tuple([float(v) for v in value])

        # If it is an object that has attributes XMin, YMin, XMax, and YMax,
        # as occurs with the arcpy Extent object, return those values.

        if hasattr(value, 'XMin') and hasattr(value, 'YMin') and hasattr(value, 'XMax') and hasattr(value, 'YMax'):
            return value.XMin, value.YMin, value.XMax, value.YMax       # left, bottom, right, top

        # Otherwise it must be a string.

        if not isinstance(value, str):
            raise ValueError('The extent value must be a list or tuple of four numbers, or an arcpy Extent object, or a string of four numbers separated by spaces, or None.')

        # If the string appears to use commas rather than periods as
        # the decimal point characters, replace the commas with
        # decimal points and try to parse it. This apparently can
        # happen with some localized versions of ArcGIS and/or
        # Windows. (The proper way to do this is probably to use the
        # atof function from the locale module, but I am afraid that
        # there are scenarios where ArcGIS will use commas even though
        # the operating system locale specifies periods, etc. So,
        # instead, I just try both.)
        
        if value.find(',') >= 0 and value.find('.') < 0:
            try:
                coords = value.replace(',', '.').split()
                return float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])       # left, bottom, right, top
            except:
                pass

        # The string did not appear to use commas for the decimal
        # point characters, or parsing it with commas failed. Try
        # periods instead.

        coords = value.split()
        return float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])       # left, bottom, right, top


class LinearUnitTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, canBeNone=False):
        super(LinearUnitTypeMetadata, self).__init__(minLength=1,
                                                     maxLength=2147483647,
                                                     mustMatchRegEx=None,
                                                     canBeNone=canBeNone,
                                                     arcGISType='ESRI.ArcGIS.Geoprocessing.GPLinearUnitTypeClass',
                                                     arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                     canBeArcGISInputParameter=True,
                                                     canBeArcGISOutputParameter=True)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPLinearUnit'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())


class MapAlgebraExpressionTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, canBeNone=False):
        super(MapAlgebraExpressionTypeMetadata, self).__init__(minLength=1,
                                                               maxLength=4000,
                                                               mustMatchRegEx=None,
                                                               canBeNone=canBeNone,
                                                               arcGISType='ESRI.ArcGIS.SpatialAnalystUI.GPSAMapAlgebraExpTypeClass',
                                                               arcGISAssembly='ESRI.ArcGIS.SpatialAnalystUI',
                                                               canBeArcGISInputParameter=True,
                                                               canBeArcGISOutputParameter=True)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPSAMapAlgebraExp'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())


class PointTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, canBeNone=False):
        super(PointTypeMetadata, self).__init__(minLength=1,
                                                mustMatchRegEx=r'([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)',
                                                canBeNone=canBeNone,
                                                arcGISType='ESRI.ArcGIS.Geoprocessing.GPPointTypeClass',
                                                arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                canBeArcGISInputParameter=True,
                                                canBeArcGISOutputParameter=True)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPPoint'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    @classmethod
    def ParseFromArcGISString(cls, value):
        if value is None:
            return None, None
        assert isinstance(value, str), 'value must be a string, or None'

        # If the string appears to use commas rather than periods as
        # the decimal point characters, replace the commas with
        # decimal points and try to parse it. This apparently can
        # happen with some localized versions of ArcGIS and/or
        # Windows. (The proper way to do this is probably to use the
        # atof function from the locale module, but I am afraid that
        # there are scenarios where ArcGIS will use commas even though
        # the operating system locale specifies periods, etc. So,
        # instead, I just try both.)
        
        if value.find(',') >= 0 and value.find('.') < 0:
            try:
                coords = value.replace(',', '.').split()
                return float(coords[0]), float(coords[1])
            except:
                pass

        # The string did not appear to use commas for the decimal
        # point characters, or parsing it with commas failed. Try
        # periods instead.

        coords = value.split()
        return float(coords[0]), float(coords[1])


class SpatialReferenceTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, canBeNone=False):
        super(SpatialReferenceTypeMetadata, self).__init__(minLength=1,
                                                           maxLength=2147483647,
                                                           mustMatchRegEx=None,
                                                           canBeNone=canBeNone,
                                                           arcGISType='ESRI.ArcGIS.Geoprocessing.GPSpatialReferenceTypeClass',
                                                           arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                           canBeArcGISInputParameter=True,
                                                           canBeArcGISOutputParameter=True)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPSpatialReference'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        from ..ArcGIS import _ArcGISObjectWrapper
        if isinstance(value, _ArcGISObjectWrapper):
            return False, value

        (valueChanged, value) = super(SpatialReferenceTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        return (valueChanged, value)


class SQLWhereClauseTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, canBeNone=False):
        super(SQLWhereClauseTypeMetadata, self).__init__(minLength=1,
                                                         maxLength=2147483647,
                                                         mustMatchRegEx=None,
                                                         canBeNone=canBeNone,
                                                         arcGISType='ESRI.ArcGIS.Geoprocessing.GPSQLExpressionTypeClass',
                                                         arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                         canBeArcGISInputParameter=True,
                                                         canBeArcGISOutputParameter=True)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPSQLExpression'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())


###############################################################################
# Names exported by this module
#
# Note: This module is not meant to be imported directly. Import Types.py
# instead.
###############################################################################

__all__ = []
