# ArcGIS.py - Utility functions for interacting with the ESRI ArcGIS software
# package.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import functools
import inspect
import logging
import os
import sys
import types
import weakref

from .Dependencies import Dependency, SoftwareNotInstalledError
from .DynamicDocString import DynamicDocString
from .Logging import Logger
from .Internationalization import _
from .Metadata import ClassMetadata, MethodMetadata, TypeMetadata


# Private variables global to this module. Initially, when originally
# developing MGET for ArcGIS 9.1, I wanted to declare these as class
# attributes of the GeoprocessorManager class. But when I did that, their
# reference counts were never decreased to 0 by Python when the module was
# unloaded. This prevented the ArcGIS 9.1 geoprocessor COM Automation object
# from being released properly, which caused calls to its SetParameterAsText
# method to not work as intended. After very careful experimentation, I
# determined that the variables could be declared as module globals and be
# released properly.

_Geoprocessor = None
_WrappedGeoprocessor = None


# Public classes and functions exported by this module

class GeoprocessorManager(object):
    __doc__ = DynamicDocString()

    _ArcGISMajorVersion = None
    _ArcGISMinorVersion = None
    _ArcGISPatchVersion = None
    _ArcGISProductName = None
    _ArcGISLicenseLevel = None

    @classmethod
    def GetGeoprocessor(cls):

        # For safety, return a weak reference to the geoprocessor, so that the
        # caller cannot accidentally hold on to a strong reference and thereby
        # prevent the geoprocessor from being released properly when the
        # module unloads.
        
        if globals()['_Geoprocessor'] is not None:
            return weakref.proxy(globals()['_Geoprocessor'])
        return None

    @classmethod
    def SetGeoprocessor(cls, geoprocessor):
        # If the caller provided a geoprocessor, use it.
        
        if geoprocessor is not None:
            try:
                globals()['_Geoprocessor'] = geoprocessor
                globals()['_WrappedGeoprocessor'] = _ArcGISObjectWrapper(geoprocessor)
            except:
                globals()['_WrappedGeoprocessor'] = None
                globals()['_Geoprocessor'] = None
                raise
            Logger.Debug(_('GeoEco will now use %r for ArcGIS operations.'), globals()['_Geoprocessor'])

        # If they provided None, release our geoprocessor.

        elif globals()['_Geoprocessor'] is not None:
            Logger.Debug(_('GeoEco is releasing its reference to %s and will no longer use it for ArcGIS operations.'), globals()['_Geoprocessor'])
            globals()['_WrappedGeoprocessor'] = None
            globals()['_Geoprocessor'] = None

    @classmethod
    def GetWrappedGeoprocessor(cls):
        
        # For safety, return a weak reference to the geoprocessor wrapper, so
        # that the caller cannot accidentally hold on to a strong reference and
        # thereby prevent the wrapper (and enclosed geoprocessor) from being
        # released properly when the module unloads.
        
        if globals()['_WrappedGeoprocessor'] is not None:
            return weakref.proxy(globals()['_WrappedGeoprocessor'])
        return None

    @classmethod
    def GetArcGISVersion(cls):
        cls._GetArcGISInstallInfo()
        return (GeoprocessorManager._ArcGISMajorVersion, GeoprocessorManager._ArcGISMinorVersion, GeoprocessorManager._ArcGISPatchVersion)

    @classmethod
    def GetArcGISMajorVersion(cls):
        cls._GetArcGISInstallInfo()
        return GeoprocessorManager._ArcGISMajorVersion

    @classmethod
    def GetArcGISMinorVersion(cls):
        cls._GetArcGISInstallInfo()
        return GeoprocessorManager._ArcGISMinorVersion

    @classmethod
    def GetArcGISPatchVersion(cls):
        cls._GetArcGISInstallInfo()
        return GeoprocessorManager._ArcGISPatchVersion

    @classmethod
    def GetArcGISProductName(cls):
        cls._GetArcGISInstallInfo()
        return GeoprocessorManager._ArcGISProductName

    @classmethod
    def GetArcGISLicenseLevel(cls):
        cls._GetArcGISInstallInfo()
        return GeoprocessorManager._ArcGISLicenseLevel

    @classmethod
    def InitializeGeoprocessor(cls):
        if cls.GetGeoprocessor() is not None:
            return
        try:
            import arcpy
        except Exception as e:
            Logger.RaiseException(SoftwareNotInstalledError(_('Either a supported version of ArcGIS is not installed, or there is a problem with the installation or its ArcGIS software license. Error details: The Python statement "import arcpy" raised %(e)s: %(msg)s.') % {'e': e.__class__.__name__, 'msg': e}))
        cls.SetGeoprocessor(arcpy)

    @classmethod
    def _GetArcGISInstallInfo(cls):
        if GeoprocessorManager._ArcGISMajorVersion is not None:
            return

        # arcpy.GetInstallInfo() returns everything we need.

        cls.InitializeGeoprocessor()
        gp = cls.GetWrappedGeoprocessor()
        installInfo = gp.GetInstallInfo()

        # Parse the version numbers. For ArcGIS Pro, the 'Version' item
        # contains the version. But for ArcGIS Server, the 'Version' item
        # contains the version of Server, but the 'ProVersion' contains the
        # version of ArcGIS Pro that Server corresponds to. So look for
        # 'ProVersion' first, and if not found, try 'Version'

        versionKey = 'ProVersion' if 'ProVersion' in installInfo else 'Version'

        if versionKey not in installInfo:
            Logger.RaiseException(RuntimeError(_('Cannot retrieve ArcGIS installation information. The dictionary returned by arcpy.GetInstallInfo() does not have \'Version\' or \'ProVersion\' in it.')))

        try:
            components = str(installInfo[versionKey]).split('.')
            if len(components) not in (2,3):
                raise ValueError()
            GeoprocessorManager._ArcGISMajorVersion = int(components[0])
            GeoprocessorManager._ArcGISMinorVersion = int(components[1])
            GeoprocessorManager._ArcGISPatchVersion = int(components[2]) if len(components) == 3 else 0
        except:
            Logger.RaiseException(RuntimeError(_('Cannot retrieve ArcGIS installation information. Could not parse the %(key)s %(value)r returned by arcpy.GetInstallInfo().' % {'key': versionKey, 'value': str(installInfo['Version'])})))

        # Extract the ProductName.

        if 'ProductName' not in installInfo:
            Logger.RaiseException(RuntimeError(_('Cannot retrieve ArcGIS installation information. The dictionary returned by arcpy.GetInstallInfo() does not have \'ProductName\' in it.')))

        GeoprocessorManager._ArcGISProductName = installInfo['ProductName']

        # Extract the LicenseLevel, if available. This item was not available
        # in ArcGIS Desktop 10.x. It is available in ArcGIS Pro 3.2, but I'm
        # not sure about earlier versions.

        if 'LicenseLevel' in installInfo:
            GeoprocessorManager._ArcGISLicenseLevel = installInfo['LicenseLevel']

    @classmethod
    def ArcGISObjectExists(cls, path, correctTypes, typeDisplayName):
        cls.__doc__.Obj.ValidateMethodInvocation()
        gp = cls.GetWrappedGeoprocessor()
        if gp is None:
            Logger.RaiseException(RuntimeError(_('The ArcGIS geoprocessor must be initialized before this function can be called. Please call GeoprocessorManager.InitializeGeoprocessor() or GeoprocessorManager.SetGeoprocessor() first.')))
        exists = os.path.exists(path) or gp.Exists(path)
        if not exists and 'shapefile' in correctTypes and not path.lower().endswith('.shp') and os.path.isdir(os.path.dirname(path)):
            exists = gp.Exists(path + '.shp')
            if exists:
                path = path + '.shp'
        isCorrectType = False
        if exists:
            correctTypes = list(map(str.lower, correctTypes))
            if 'rasterdataset' in correctTypes and os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.img', '.jpg', '.png', '.tif']:     # Optimization for common raster formats
                isCorrectType = True
            else:
                d = gp.Describe(path)
                isCorrectType = d is not None and d.DataType.lower() in correctTypes
        if not exists:
            Logger.Debug(_('The %(type)s %(path)s does not exist.') % {'type': typeDisplayName, 'path': path})
        else:
            if isCorrectType:
                Logger.Debug(_('The %(type)s %(path)s exists.') % {'type': typeDisplayName, 'path': path})
            else:
                Logger.Debug(_('%(path)s exists but it is a %(actual)s, not a %(type)s.') % {'type': typeDisplayName, 'path': path, 'actual': d.DataType})
        return (exists, isCorrectType)

    @classmethod
    def DeleteArcGISObject(cls, path, correctTypes, typeDisplayName):
        cls.__doc__.Obj.ValidateMethodInvocation()
        exists, isCorrectType = cls.ArcGISObjectExists(path, correctTypes, typeDisplayName)
        if not exists:
            Logger.Info(_('The %(type)s %(path)s will not be deleted because it does not exist.') % {'type': typeDisplayName, 'path': path})
            return
        if not isCorrectType:
            Logger.RaiseException(ValueError(_('%(path)s exists but cannot be deleted because it is not a %(type)s.') % {'type': typeDisplayName, 'path': path}))
        try:
            gp = cls.GetWrappedGeoprocessor()
            gp.Delete_management(path)
        except:
            Logger.LogExceptionAsError(_('Could not delete %(type)s %(path)s.') % {'type': typeDisplayName, 'path': path})
            raise
        Logger.Info(_('Deleted %(type)s %(path)s.') % {'type': typeDisplayName, 'path': path})

    @classmethod
    def CopyArcGISObject(cls, source, destination, overwriteExisting, correctTypes, typeDisplayName):
        cls.__doc__.Obj.ValidateMethodInvocation()
        exists, isCorrectType = cls.ArcGISObjectExists(source, correctTypes, typeDisplayName)
        if not exists:
            Logger.RaiseException(ValueError(_('The %(type)s %(path)s cannot be copied because it does not exist.') % {'type': typeDisplayName, 'path': source}))
        if not isCorrectType:
                Logger.RaiseException(ValueError(_('%(path)s cannot be copied because it is not a %(type)s.') % {'type': typeDisplayName, 'path': source}))
        try:
            if overwriteExisting:
                oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
                Logger.SetLogInfoAsDebug(True)
                try:
                    cls.DeleteArcGISObject(destination, correctTypes, typeDisplayName)
                finally:
                    Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)
            else:
                exists, isCorrectType = cls.ArcGISObjectExists(destination, correctTypes, typeDisplayName)
                if exists:
                    Logger.RaiseException(ValueError(_('%(path)s already exists.') % {'path': destination}))
            gp = cls.GetWrappedGeoprocessor()
            Logger.Info(_('Copying %(type)s %(source)s to %(destination)s.') % {'type': typeDisplayName, 'source': source, 'destination': destination})
            if 'featureclass' in correctTypes or 'shapefile' in correctTypes or 'featurelayer' in correctTypes:
                gp.CopyFeatures_management(source, destination)
            else:
                gp.Copy_management(source, destination)
        except:
            Logger.LogExceptionAsError(_('Could not copy %(type)s %(source)s to %(destination)s.') % {'type': typeDisplayName, 'source': source, 'destination': destination})
            raise

    @classmethod
    def MoveArcGISObject(cls, source, destination, overwriteExisting, correctTypes, typeDisplayName):
        cls.__doc__.Obj.ValidateMethodInvocation()
        exists, isCorrectType = cls.ArcGISObjectExists(source, correctTypes, typeDisplayName)
        if not exists:
            Logger.RaiseException(ValueError(_('The %(type)s %(path)s cannot be moved because it does not exist.') % {'type': typeDisplayName, 'path': source}))
        if not isCorrectType:
            Logger.RaiseException(ValueError(_('%(path)s cannot be moved because it is not a %(type)s.') % {'type': typeDisplayName, 'path': source}))
        try:
            if overwriteExisting:
                oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
                Logger.SetLogInfoAsDebug(True)
                try:
                    cls.DeleteArcGISObject(destination, correctTypes, typeDisplayName)
                finally:
                    Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)
            else:
                exists, isCorrectType = cls.ArcGISObjectExists(destination, correctTypes, typeDisplayName)
                if exists:
                    Logger.RaiseException(ValueError(_('%(path)s already exists.') % {'path': destination}))
            gp = cls.GetWrappedGeoprocessor()
            Logger.Info(_('Moving %(type)s %(source)s to %(destination)s.') % {'type': typeDisplayName, 'source': source, 'destination': destination})
            if 'featureclass' in correctTypes or 'shapefile' in correctTypes or 'featurelayer' in correctTypes:
                gp.CopyFeatures_management(source, destination)
            else:
                gp.Copy_management(source, destination)
            gp.Delete_management(source)
        except:
            Logger.LogExceptionAsError(_('Could not move %(type)s %(source)s to %(destination)s.') % {'type': typeDisplayName, 'source': source, 'destination': destination})
            raise

    @classmethod
    def GetUniqueLayerName(cls):
        gp = cls.GetWrappedGeoprocessor()
        if gp is None:
            Logger.RaiseException(RuntimeError(_('The ArcGIS geoprocessor must be initialized before this function can be called. Please call GeoprocessorManager.InitializeGeoprocessor() or GeoprocessorManager.SetGeoprocessor() first.')))
        import random
        name = 'TempLayer%08X' % random.randint(0, 2147483647)
        while gp.Exists(name):
            name = 'TempLayer%08X' % random.randint(0, 2147483647)
        return name


class ArcGISDependency(Dependency):
    __doc__ = DynamicDocString()

    def __init__(self, minimumMajorVersion=3, minimumMinorVersion=2, minimumPatchVersion=None, productNames=['ArcGISPro', 'Server'], licenseLevels=None):
        self.SetVersion(minimumMajorVersion, minimumMinorVersion, minimumPatchVersion)
        self.ProductNames = productNames
        self.LicenseLevels = licenseLevels

    def SetVersion(self, minimumMajorVersion, minimumMinorVersion=None, minimumPatchVersion=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        if minimumMinorVersion is None:
            minimumMinorVersion = 0
        if minimumPatchVersion is None:
            minimumPatchVersion = 0

        self._MinimumMajorVersion = minimumMajorVersion
        self._MinimumMinorVersion = minimumMinorVersion
        self._MinimumPatchVersion = minimumPatchVersion

    def _GetMinimumMajorVersion(self):
        return self._MinimumMajorVersion
    
    MinimumMajorVersion = property(_GetMinimumMajorVersion, doc=DynamicDocString())

    def _GetMinimumMinorVersion(self):
        return self._MinimumMinorVersion
    
    MinimumMinorVersion = property(_GetMinimumMinorVersion, doc=DynamicDocString())

    def _GetMinimumPatchVersion(self):
        return self._MinimumPatchVersion
    
    MinimumPatchVersion = property(_GetMinimumPatchVersion, doc=DynamicDocString())

    def _GetProductNames(self):
        return self._ProductNames

    def _SetProductNames(self, productNames):
        self.__doc__.Obj.ValidatePropertyAssignment()
        self._ProductNames = productNames
    
    ProductNames = property(_GetProductNames, _SetProductNames, doc=DynamicDocString())

    def _GetLicenseLevels(self):
        return self._LicenseLevels

    def _SetLicenseLevels(self, licenseLevels):
        self.__doc__.Obj.ValidatePropertyAssignment()
        self._LicenseLevels = licenseLevels
    
    LicenseLevels = property(_GetLicenseLevels, _SetLicenseLevels, doc=DynamicDocString())

    _LoggedInstalledVersion = False

    def Initialize(self):

        # Check get the ArcGIS installation information.

        requirementDescription = self.GetConstraintDescriptionStrings()[0]
        Logger.Debug(_('Checking software dependency: %s') % requirementDescription)

        try:
            major = GeoprocessorManager.GetArcGISMajorVersion()
            minor = GeoprocessorManager.GetArcGISMinorVersion()
            patch = GeoprocessorManager.GetArcGISPatchVersion()
            productName = GeoprocessorManager.GetArcGISProductName()
            licenseLevel = GeoprocessorManager.GetArcGISLicenseLevel()
        except Exception as e:
            Logger.RaiseException(SoftwareNotInstalledError(_('This software requires %s, but the presence of ArcGIS could not be verified. %s') % (requirementDescription, e)))

        # Log a debug message with the installation information.

        if not ArcGISDependency._LoggedInstalledVersion:
            if productName == 'ArcGISPro':
                Logger.Debug(_('ArcGIS Pro %i.%i.%i is installed with a license level of %s.'), major, minor, patch, licenseLevel if licenseLevel is not None else 'Unknown')
            elif productName == 'Server':
                if major < 9:
                    Logger.Debug(_('An ArcGIS Pro-compatible version of ArcGIS Server is installed with an equivalent ArcGIS Pro version of %i.%i.%i and a license level of %s.'), major, minor, patch, licenseLevel if licenseLevel is not None else 'Unknown')
                else:
                    Logger.Debug(_('ArcGIS Server %i.%i.%i is installed with a license level of %s.'), major, minor, patch, licenseLevel if licenseLevel is not None else 'Unknown')
            else:
                Logger.Debug(_('The ArcGIS product %r version %i.%i.%i is installed with a license level of %s.'), productName, major, minor, patch, licenseLevel if licenseLevel is not None else 'Unknown')
            ArcGISDependency._LoggedInstalledVersion = True

        # Check compatibility.

        if self.ProductNames is not None and len(self.ProductNames) > 0 and productName not in self.ProductNames:
            Logger.RaiseException(SoftwareNotInstalledError(_('This software requires %s, but the ArcGIS %s product is installed. Please update your ArcGIS installation to a compatible product and try again.') % (requirementDescription, productName)))

        if self.MinimumMajorVersion > major or self.MinimumMajorVersion == major and self.MinimumMinorVersion > minor or self.MinimumMajorVersion == major and self.MinimumMinorVersion == minor and self.MinimumPatchVersion > patch:
            Logger.RaiseException(SoftwareNotInstalledError(_('This software requires %s, but version %i.%i.%i is installed. Please update your ArcGIS installation to a compatible version and try again.') % (requirementDescription, major, minor, patch)))

        if self.LicenseLevels is not None and len(self.LicenseLevels) > 0 and licenseLevel is not None and licenseLevel not in self.LicenseLevels:
            Logger.RaiseException(SoftwareNotInstalledError(_('This software requires %s, but license level %s is installed. Please update your ArcGIS installation to a compatible license level and try again.') % (requirementDescription, licenseLevel)))

    def GetConstraintDescriptionStrings(self):
        s = ''
        if self.ProductNames is None or 'ArcGISPro' in self.ProductNames:
            s = 'ArcGIS Pro %i.%i.%i or later' % (self.MinimumMajorVersion, self.MinimumMinorVersion, self.MinimumPatchVersion)
        if self.ProductNames is not None and 'Server' in self.ProductNames:
            if len(s) > 0:
                s += ' or '
            s += 'ArcGIS Server equivalent to ArcGIS Pro %i.%i.%i or later' % (self.MinimumMajorVersion, self.MinimumMinorVersion, self.MinimumPatchVersion)
        if self.LicenseLevels is not None and len(self.LicenseLevels) > 0:
            if len(self.LicenseLevels) == 1:
                s += ', with a license level of ' + self.LicenseLevels[0]
            else:
                s += ', with a license level of %s or %s' % (', '.join(self.LicenseLevels[0:-1]), self.LicenseLevels[-1])
        return [s]


class ArcGISExtensionDependency(Dependency):
    __doc__ = DynamicDocString()

    def __init__(self, extensionCode):
        self.ExtensionCode = extensionCode

    def _SetExtensionCode(self, value):
        self.__doc__.Obj.ValidatePropertyAssignment()
        self._ExtensionCode = value

    def _GetExtensionCode(self):
        return self._ExtensionCode
    
    ExtensionCode = property(_GetExtensionCode, _SetExtensionCode, doc=DynamicDocString())

    def Initialize(self):

        Logger.Debug(_('Checking software dependency: ArcGIS %r extension.') % self.ExtensionCode)

        # It appears that the geoprocessor does not maintain a reference count
        # on checked out extensions. Thus, you can call CheckOutExtension
        # multiple times for the same extension, but if you call
        # CheckInExtension just once, the extension is no longer checked out.
        # As a result, if we checked out an extension in a previous call we
        # have no guarantee that it is still checked out, because the caller
        # could have checked it in. To mitigate this, we always check out the
        # extension every time we're called. This seems to have no ill
        # effects. It does not cause multiple licenses to be taken from the
        # license server, and it does not yield an excessive performance hit
        # (the CheckOutExtension call returns relatively quickly).
        #
        # We also never check in the extension, because we don't know if this
        # would foul up the caller (he may assume the geoprocessor is
        # reference- ounting the extensions, when it really is not...)

        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        status = gp.CheckOutExtension(self.ExtensionCode)
        if status is None:
            Logger.RaiseException(SoftwareNotInstalledError(_('This software requires the ArcGIS \"%(extension)s\" extension. ArcGIS failed to report the status of the license for that extension. Please verify that you possess a license for that extension and that the extension is installed. If you use an ArcGIS license server, verify that this computer can properly communicate with it.') % {'extension': self.ExtensionCode}))
        elif status.lower() != 'checkedout':
            Logger.RaiseException(SoftwareNotInstalledError(_('This software requires the ArcGIS \"%(extension)s\" extension. ArcGIS reported the following status for that extension: \"%(status)s\". Please verify that you possess a license for that extension and that the extension is installed. If you use an ArcGIS license server, verify that this computer can properly communicate with it.') % {'extension': self.ExtensionCode, 'status' : status}))

    def GetConstraintDescriptionStrings(self):
        return ['ArcGIS %r extension' % self.ExtensionCode]


def ValidateMethodMetadataForExposureAsArcGISTool(moduleName, className, methodName):
    """Validates that a method has proper metadata defined to allow it to be exposed as an ArcGIS geoprocessing tool.

    This function is used during the GeoEco build process, when building the
    Marine Geospatial Ecology Tools ArcGIS toolbox."""

    # Validate the class and method metadata.

    assert moduleName in sys.modules, 'Module %s must be imported before ValidateMethodMetadataForExposureAsArcGISTool is invoked on that module.' % moduleName
    assert className in sys.modules[moduleName].__dict__ and issubclass(sys.modules[moduleName].__dict__[className], object), 'Module %s must contain a class named %s, and the class must derive from object.' % (moduleName, className)
    cls = sys.modules[moduleName].__dict__[className]
    assert isinstance(cls.__doc__, DynamicDocString) and isinstance(cls.__doc__.Obj, ClassMetadata), 'The __doc__ attribute of class %s must be an instance of DynamicDocString, and that Obj property of that instance must be an instance of ClassMetadata.' % className
    assert hasattr(cls, methodName) and inspect.ismethod(getattr(cls, methodName)), 'Class %s must contain an instance method or classmethod named %s.' % (className, methodName)
    assert isinstance(getattr(cls, methodName).__doc__, DynamicDocString) and isinstance(getattr(cls, methodName).__doc__.Obj, MethodMetadata), 'The __doc__ attribute of method %s of class %s must be an instance of DynamicDocString, and that Obj property of that instance must be an instance of MethodMetadata.' % (methodName, className)
    methodMetadata = getattr(cls, methodName).__doc__.Obj
    assert methodMetadata.IsInstanceMethod or methodMetadata.IsClassMethod, 'Method %s of class %s must be an instance method or a classmethod.' % (methodName, className)
    assert methodMetadata.IsExposedAsArcGISTool, '%s.%s.__doc__.Obj.IsExposedAsArcGISTool must be true.' % (className, methodName)
    assert isinstance(methodMetadata.ArcGISDisplayName, str), '%s.%s.__doc__.Obj.ArcGISDisplayName must be a unicode string.' % (className, methodName)
    assert '_' not in className and '_' not in methodName, 'In order for method %s of class %s to be exposed as an ArcGIS tool, neither the method name nor the class name may contain an underscore.' % (methodName, className)

    # Validate the metadata for the method's arguments.

    (args, varargs, varkw, defaults) = inspect.getargspec(getattr(cls, methodName))
    assert varargs is None, '%s.%s cannot include a varargs argument because this method is designated for exposure as an ArcGIS tool (ArcGIS tools do not support varargs arguments). Please remove the *%s argument.' % (className, methodName, varargs)
    assert varkw is None, '%s.%s cannot include a varkw argument because this method is designated for exposure as an ArcGIS tool (ArcGIS tools do not support varkw arguments). Please remove the **%s argument.' % (className, methodName, varkw)
    assert len(methodMetadata.Arguments) == len(args), '%s.%s.__doc__.Obj.Arguments must contain exactly one element for each argument to %s.%s. %s.%s.__doc__.Obj.Arguments contains %i elements, but %i elements were expected.' % (className, methodName, className, methodName, className, methodName, len(methodMetadata.Arguments), len(args))
    for i in range(1, len(args)):   # Skip the self or cls argument
        assert methodMetadata.Arguments[i].Name == args[i], '%s.%s.__doc__.Obj.Arguments[%i].Name must match the name of argument %i of %s.%s (where 0 is the first argument).' % (className, methodName, i, i, className, methodName)
        assert isinstance(methodMetadata.Arguments[i].Type, TypeMetadata), '%s.%s.__doc__.Obj.Arguments[%i].Type must be an instance of GeoEco.Metadata.TypeMetadata.' % (className, methodName, i)
        if methodMetadata.Arguments[i].ArcGISDisplayName is not None:
            assert isinstance(methodMetadata.Arguments[i].ArcGISDisplayName, str), '%s.%s.__doc__.Obj.Arguments[%i].ArcGISDisplayName must be a unicode string.' % (className, methodName, i)
            assert methodMetadata.Arguments[i].Type.CanBeArcGISInputParameter, '%s.%s.__doc__.Obj.Arguments[%i].Type.CanBeArcGISInputParameter must be True' % (className, methodName, i)
            assert methodMetadata.Arguments[i].InitializeToArcGISGeoprocessorVariable is None, 'Argument %i of %s.%s cannot have a value for ArcGISDisplayName when InitializeToArcGISGeoprocessorVariable is True. Either the argument can have an ArcGISDisplayName, in which case the argument is exposed as an ArcGIS parameter, or it can have InitializeToArcGISGeoprocessorVariable set to True, in which case the argument is not exposed in ArcGIS but is initialized to a geoprocessor variable.' % (i, className, methodName)
            if methodMetadata.Arguments[i].ArcGISParameterDependencies is not None:
                for param in methodMetadata.Arguments[i].ArcGISParameterDependencies:
                    assert param != methodMetadata.Arguments[i].Name, '%s.%s.__doc__.Obj.Arguments[%i].ArcGISParameterDependencies must not declare that this argument has a dependency on itself.' % (className, methodName, i)
                    assert param in args, '%s.%s.__doc__.Obj.Arguments[%i].ArcGISParameterDependencies must declare dependencies on existing arguments. The argument \'%s\' does not exist.' % (className, methodName, i, param)
        else:
            assert methodMetadata.Arguments[i].HasDefault or methodMetadata.Arguments[i].InitializeToArcGISGeoprocessorVariable is not None, 'Argument %i of %s.%s must have a default value, or its metadata must specify that it should be initialized to an ArcGIS geoprocessor variable, because the method is designated for exposure as an ArcGIS tool but the argument itself is not (its ArcGISDisplayName is None).' % (i, className, methodName)
            
    # Validate the metadata for the method's results.        

    for i in range(len(methodMetadata.Results)):
        assert isinstance(methodMetadata.Results[i].Type, TypeMetadata), '%s.%s.__doc__.Obj.Results[%i].Type must be an instance of GeoEco.Metadata.TypeMetadata.' % (className, methodName, i)
        if methodMetadata.Results[i].ArcGISDisplayName is not None:
            assert isinstance(methodMetadata.Results[i].ArcGISDisplayName, str), '%s.%s.__doc__.Obj.Results[%i].ArcGISDisplayName must be a unicode string.' % (className, methodName, i)
            assert methodMetadata.Results[i].Type.CanBeArcGISOutputParameter, '%s.%s.__doc__.Obj.Results[%i].Type.CanBeArcGISOutputParameter must be True' % (className, methodName, i)
            if methodMetadata.Results[i].ArcGISParameterDependencies is not None:
                for param in methodMetadata.Results[i].ArcGISParameterDependencies:
                    assert param in args, '%s.%s.__doc__.Obj.Results[%i].ArcGISParameterDependencies must declare dependencies on existing arguments. The argument \'%s\' does not exist.' % (className, methodName, i, param)


class _ArcGISObjectWrapper(object):

    def __init__(self, obj):
        _ArcGISObjectWrapper._LogDebug('Wrapping object %.255r', obj)
        self._Object = obj
        self._WrappedMethods = {}

    def __getattr__(self, name):
        assert isinstance(name, str), 'name must be a string.'

        # If the caller is asking for a private attribute (the name starts
        # with an underscore), they want an attribute of the wrapper class
        # instance, not of the wrapped object. In this case, we must use the
        # object class's implementation of __getattribute__.

        if name.startswith('_') and name not in ['__iter__', '__next__', '__getitem__', '__len__', '__contains__']:
            return object.__getattribute__(self, name)

        # The caller is asking for a data attribute or a method of the wrapped
        # object (of, if we are wrapping a module, a function of the module).
        # If we already built a wrapper method for the specified name, return
        # it now.

        if name in self._WrappedMethods:
            return object.__getattribute__(self, name)

        # Otherwise, retrieve the attribute from the wrapped object.

        try:
            try:
                value = getattr(self._Object, name)
            except AttributeError as e:

                # ArcGIS 10 seems to randomly fail with AttributeError:
                # DescribeData: Method SpatialReference does not exist. I
                # don't know if ArcGIS Pro exhibits this problem, but will
                # assume it does. Therefore, if we failed to retrieve
                # SpatialReference, try again once.
                
                if name == 'SpatialReference':
                    value = getattr(self._Object, name)
                else:
                    raise

        # If we catch an exception, log an error and reraise it the original
        # exception. If it is an AttributeError, do NOT log a message, because
        # this may be normal behavior: hasattr() calls getattr() and checks
        # for the exception.
        
        except Exception as e:
            if not isinstance(e, AttributeError):
                self._LogError(_('Failed to get the value of the %(name)s attribute of %(obj)s. This may result from a problem with your inputs or it may indicate a programming mistake in this tool or ArcGIS itself. Please check your inputs and try again. Also review any preceding error messages and the detailed error information that appears at the end of this message. If you suspect a programming mistake in this tool or ArcGIS, please contact the author of this tool for assistance. Detailed error information: The following exception was raised when the attribute was retrieved: %(error)s: %(msg)s') % {'name': name, 'obj': self._Object, 'error': e.__class__.__name__, 'msg': e})
            raise

        # If the caller asked for a method or function, create a wrapper, add
        # the wrapper to our dictionary of wrapped methods, and return the
        # wrapper. The wrapper will be an instance method of ourself
        # (i.e., the _ArcGISObjectWrapper instance represented by self),
        # regardless of what kind of method or function is being wrapped.

        if isinstance(value, (types.MethodType, types.FunctionType, types.BuiltinMethodType, types.BuiltinFunctionType)):

            # First determine whether this callable is an instance method by
            # checking for the presence of the '__self__' attribute. Note
            # that some such methods from arcpy will be of MethodType, but
            # others that are implemented in extension modules
            # (probably arcobjects) will be both BuiltinMethodType and
            # BuiltinFunctionType. In this latter case, it appears the way to
            # definitively determine that they are methods is to check
            # for '__self__'. (It might be safe to just assume that
            # everything we get that is a BuiltinMethodType is an instance
            # method, regardless of whether it is also BuiltinFunctionType,
            # but I am not sure.)

            if hasattr(value, '__self__'):

                # It is an instance method. In this situation, we (this
                # _ArcGISObjectWrapper instance) are wrapping the instance it
                # is a method of. Create a wrapper around it that performs
                # logging and conversion and bind it to ourself as an
                # instance method.

                self._BindInstanceMethod(value, name)

            else:
                # It is not an instance method, which means, in the case of
                # arcpy, that it is a module-level function. Similar to
                # above, create a wrapper around it that performs logging and
                # conversion and bind it to ourself as an instance method.
                # Thus, the caller, rather than working with the arcpy module
                # and its functions, will instead be working with us
                # (this _ArcGISObjectWrapper instance) and our methods.

                self._BindFunctionAsInstanceMethod(value, name)

            # Return the instance method we just bound.

            self._WrappedMethods[name] = True
            return object.__getattribute__(self, name)

        # Log the returned attribute value.

        self._LogDebug('%.255s.%s returned %.255r', self._Object, name, value)

        # The returned value is a property. Convert it from the geoprocessor's
        # preferred type to the type we prefer and return that instead.

        return self._FromGeoprocessorPreferredType(value)

    def __setattr__(self, name, value):
        assert isinstance(name, str), 'name must be a string.'

        # If the caller is asking for a private attribute (the name starts
        # with an underscore), he wants to set an attribute of the wrapper
        # class instance, not of the wrapped object. In this case, we must use
        # the object class's implementation of __setattr__.

        if name.startswith('_'):
            return object.__setattr__(self, name, value)

        # The caller wants to set an attribute of the wrapped object. Convert
        # the value from our preferred type to that preferred by the
        # geoprocessor.

        value = self._ToGeoprocessorPreferredType(value)

        # Set the attribute.

        try:
            setattr(self._Object, name, value)

        # If we catch some other exception, log a error and reraise the
        # original exception.
        
        except Exception as e:
            self._LogError(_('Failed to set the %(name)s attribute of %(obj)s to %(value)r. This may result from a problem with your inputs or it may indicate a programming mistake in this tool or ArcGIS itself. Please check your inputs and try again. Also review any preceding error messages and the detailed error information that appears at the end of this message. If you suspect a programming mistake in this tool or ArcGIS, please contact the author of this tool for assistance. Detailed error information: The following exception was raised when the attribute was set: %(error)s: %(msg)s') % {'name': name, 'obj': self._Object, 'value': value, 'error': e.__class__.__name__, 'msg': e})
            raise

        # Log the set value.

        self._LogDebug('Set %s.%s to %.255r', self._Object, name, value)

    def __call__(self, *args, **kwargs):

        # The caller has invoked the _ArcGISObjectWrapper instance as if it
        # were a function. Check if the wrapped object is callable. If so,
        # call it. The most common scenario of this type is when the wrapped
        # object is a class, in which case calling it will construct an
        # instance of it.

        if callable(self._Object):
            return self._CallWrappedFunction(self._Object, str(self._Object), args, kwargs)

        # Otherwise, just try to call it anyway, allowing Python to raise an
        # appropriate TypeError.

        return self._Object(*args, **kwargs)

    def _BindInstanceMethod(self, func, name):
        _ArcGISObjectWrapper._LogDebug('Wrapping %r', func)

        # Define a wrapper for func that performs logging and conversion.

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # wrapper() is a bound method of _ArcGISObjectWrapper, and the
            # self that is passed to it is the _ArcGISObjectWrapper instance.
            # We do not want to pass our 'self' to func. Delete 'self' from
            # kwargs or args before calling func.

            if 'self' in 'kwargs':
                del kwargs['self']
            elif len(args) > 0:
                args = args[1:]

            return self._CallWrappedFunction(func, '%s' % func, args, kwargs)

        # Bind the method to the _ArcGISObjectWrapper instance.
        
        boundMethod = types.MethodType(wrapper, self)
        object.__setattr__(self, name, boundMethod)     # Use object.__setattr__() so that our own override of __setattr__() is not called

    def _BindFunctionAsInstanceMethod(self, func, name):
        _ArcGISObjectWrapper._LogDebug('Wrapping %r from %r', func, self._Object)

        # Define a wrapper for func that performs logging and conversion.

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return self._CallWrappedFunction(func, '%s.%s' % (self._Object.__name__, func.__name__), args, kwargs)

        # Prepend 'self' to the wrapper's signature, so we can bind it as an
        # instance method of an _ArcGISObjectWrapper instance.

        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        newParams = [inspect.Parameter('self', inspect.Parameter.POSITIONAL_OR_KEYWORD)] + params
        wrapper.__signature__ = sig.replace(parameters=newParams)

        # Bind the method to the _ArcGISObjectWrapper instance.
        
        boundMethod = types.MethodType(wrapper, self)
        object.__setattr__(self, name, boundMethod)     # Use object.__setattr__() so that our own override of __setattr__() is not called

    def _CallWrappedFunction(self, func, funcName, args, kwargs):

        # Convert the arguments to the geoprocessor's preferred types.

        if args is not None:
            args = tuple([self._ToGeoprocessorPreferredType(arg) for arg in args])

        if kwargs is not None:
            kwargs = {param:self._ToGeoprocessorPreferredType(arg) for param, arg in kwargs.items()}

        # Log a message indicating we're calling the function.

        try:
            sig = inspect.signature(func)
            boundArgs = sig.bind(*args, **kwargs)
            argsStr = ', '.join(f'{key}={value!r:.255}' for key, value in boundArgs.arguments.items())
        except:
            argsStr = ', '.join([repr(arg) for arg in args] + ['%s=%.255r' % (key, value) for key, value in kwargs.items()])

        _ArcGISObjectWrapper._LogDebug('Calling %.255s(%s)', funcName, argsStr)

        # Call the function.

        try:
            result = func(*args, **kwargs)

        # If we an caught exception, log the geoprocessing messages and raise
        # the exception as ArcGISError. Note: call raise, rather than
        # Logger.RaiseException, so the caller can swallow the exception, if
        # needed.
        
        except Exception as e:
            self._LogReturnedGeoprocessingMessages(func)
            if isinstance(e, StopIteration):
                self._LogDebug(_('%(funcName).255s raised StopIteration.') % {'funcName': funcName})
            else:
                self._LogError(_('Execution of %(funcName).255s failed when given the inputs %(args)s and reported %(error)s: %(msg)s. This may result from a problem with your inputs or it may indicate a programming mistake in this tool or ArcGIS itself. Please review any preceding error messages, check your inputs, and try again. If you suspect a programming mistake in this tool or ArcGIS, please contact the author of this tool for assistance.') % {'funcName': funcName, 'args': argsStr, 'error': e.__class__.__name__, 'msg': e})
            raise

        # The method executed successfully. Log any geoprocessing messages it
        # generated.

        self._LogReturnedGeoprocessingMessages(func)

        # Log a message reporting the result.

        _ArcGISObjectWrapper._LogDebug('%.255s returned %.255r', funcName, result)

        # Convert the result from the geoprocessor's preferred type to our
        # preferred type and return it to the caller.

        return self._FromGeoprocessorPreferredType(result)

    def _ToGeoprocessorPreferredType(self, value):

        # In the ArcGIS Desktop 9.x and 10.x timeframe, the geoprocessor was
        # not very "Pythonic", which necessitated special handling of certain
        # types such as str, datetime.datetime, and None. With the increase
        # in Pythonicity that came with ArcGIS Pro, essentially all of this
        # is unnecessary, and the main thing is to extract wrapped objects
        # from _ArcGISObjectWrapper instances. So value is an instance
        # of _ArcGISObjectWrapper, return the wrapped object.

        if isinstance(value, _ArcGISObjectWrapper):
            return value._Object

        # If the value is a list, tuple, or dict, process every item with it.

        if isinstance(value, list):
            return [self._ToGeoprocessorPreferredType(item) for item in value]

        if isinstance(value, tuple):
            return tuple([self._ToGeoprocessorPreferredType(item) for item in value])

        if isinstance(value, dict):
            return {self._ToGeoprocessorPreferredType(k):self._ToGeoprocessorPreferredType(v) for k, v in value.items()}

        # The value is fine as it is. Just return it.        

        return value

    def _FromGeoprocessorPreferredType(self, value):

        # In the ArcGIS Desktop 9.x and 10.x timeframe, the geoprocessor was
        # not very "Pythonic", which necessitated special handling of certain
        # types. With the increase in Pythonicity that came with ArcGIS Pro,
        # essentially all of this is unnecessary, and the main thing is to
        # wrap instances of non-simple types in _ArcGISObjectWrapper
        # instances. So if we got a simple type back, just return it.

        if value is None or isinstance(value, (bool, int, float, complex, str, datetime.datetime, bytearray)):
            return value

        # If the value is a list, tuple, or dict, process every item with it.

        if isinstance(value, list):
            return [self._FromGeoprocessorPreferredType(item) for item in value]

        if isinstance(value, tuple):
            return tuple([self._FromGeoprocessorPreferredType(item) for item in value])

        if isinstance(value, dict):
            return {self._FromGeoprocessorPreferredType(k):self._FromGeoprocessorPreferredType(v) for k, v in value.items()}

        # If we got to here, it is a non-simple object. Wrap it
        # in _ArcGISObjectWrapper so we can log accesses to attributes and
        # calls to functions.

        return _ArcGISObjectWrapper(value)

    def _LogReturnedGeoprocessingMessages(self, func):

        # Only log the messages returned by the geoprocessor if the invoked
        # method appears to be a geoprocessing tool. The other methods of the
        # geoprocessor (the ones that are not geoprocessing tools) do not
        # report any messages, but they also do not clear out the queue of
        # messages from tool that was most recently called. Those messages
        # will stay in the queue until the next geoprocessing tool is called,
        # and there is no way we can get rid of them. Therefore, to avoid
        # reporting the same messages multiple times, only try to report
        # messages if we invoked a method that was a tool.
        #
        # There is no documented way to determine if a method is a tool, but
        # we discovered that func.__dict__ contains the key
        # '__esri_toolname__' if the method is a tool. In our testing with
        # ArcPro 3.2, this held true for the tools that came with Arc Pro
        # as well as tools added from external .tbx and .pyt toolboxes. It
        # seems that calling arcpy.AddToolbox() adds this item to the method's
        # __dict__.

        try:
            isTool = hasattr(func, '__dict__') and '__esri_toolname__' in func.__dict__
        except:
            isTool = False

        if isTool:
            i = 0
            try:
                geoprocessor = GeoprocessorManager.GetGeoprocessor()
                if geoprocessor is not None:
                    try:
                        while i < geoprocessor.GetMessageCount():
                            sev = geoprocessor.GetSeverity(i)
                            if sev == 0:
                                self._LogInfo(geoprocessor.GetMessage(i))
                            elif sev == 1:
                                self._LogWarning(geoprocessor.GetMessage(i))
                            else:
                                self._LogError(geoprocessor.GetMessage(i))
                            i += 1
                    finally:
                        del geoprocessor
            except:
                pass

    @staticmethod
    def _LogDebug(format, *args, **kwargs):
        try:
            logging.getLogger('GeoEco.ArcGIS').debug(format, *args, **kwargs)
        except:
            pass

    @staticmethod
    def _LogInfo(format, *args, **kwargs):
        try:
            logging.getLogger('GeoEco.ArcGIS').info(format, *args, **kwargs)
        except:
            pass

    @staticmethod
    def _LogWarning(format, *args, **kwargs):
        try:
            logging.getLogger('GeoEco.ArcGIS').warning(format, *args, **kwargs)
        except:
            pass

    @staticmethod
    def _LogError(format, *args, **kwargs):
        try:
            logging.getLogger('GeoEco.ArcGIS').error(format, *args, **kwargs)
        except:
            pass

    # In order to be recongized as supporting iteration, _ArcGISObjectWrapper
    # has to implement these methods:

    def __iter__(self):
        return self.__getattr__('__iter__')()

    def __next__(self):
        return self.__getattr__('__next__')()

    # For sequence protocol, we have to support these:

    def __getitem__(self, index):
        return self.__getattr__('__getitem__')(index)

    def __len__(self):
        return self.__getattr__('__len__')()

    def __contains__(self, item):
        return self.__getattr__('__getitem__')(item)




###############################################################################
# Metadata: module
###############################################################################

from .Metadata import *
from .Types import *

AddModuleMetadata(shortDescription=_('Utility functions for interacting with ESRI ArcGIS software.'))

###############################################################################
# Metadata: GeoprocessorManager class
###############################################################################

AddClassMetadata(GeoprocessorManager,
    shortDescription=_('Manages GeoEco\'s interface to ArcGIS\'s Python package, known historically as the "geoprocessor", and more recently as `arcpy <https://www.esri.com/en-us/arcgis/products/arcgis-python-libraries/libraries/arcpy>`_.'),
    longDescription=_(
"""Note:

    Do not instantiate this class. It is a collection of classmethods intended
    to be invoked on the class rather than an instance of it, like this:

    .. code-block:: python

        from GeoEco.ArcGIS import GeoprocessorManager

        GeoprocessorManager.InitializeGeoprocessor()

    See the documentation for :func:`InitializeGeoprocessor` for examples of
    how to use :class:`~GeoEco.ArcGIS.GeoprocessorManager`.
"""))

# Public method: GeoprocessorManager.GetGeoprocessor

AddMethodMetadata(GeoprocessorManager.GetGeoprocessor,
    shortDescription=_('Returns a :py:mod:`weakref` to the ArcGIS geoprocessor that the GeoEco package is using.'),
    longDescription=_(
"""This function will return None until :func:`InitializeGeoprocessor` or
:func:`SetGeoprocessor` has been called. In general, GeoEco functions that
need the geoprocessor should call :func:`GetWrappedGeoprocessor` rather than
:func:`GetGeoprocessor`, because the wrapped geoprocessor provides logging
that can be useful in debugging. See :func:`GetWrappedGeoprocessor` for more
information.

This function returns a :py:mod:`weakref` so that callers do not inadvertently
maintain references to GeoEco's instance of the geoprocessor and prevent it
from being released."""))

AddArgumentMetadata(GeoprocessorManager.GetGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetGeoprocessor, 'geoprocessor',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('A :py:mod:`weakref` to the ArcGIS geoprocessor that the GeoEco package is using, or None if neither :func:`InitializeGeoprocessor` nor :func:`SetGeoprocessor` has been called yet.'))

# Public method: GeoprocessorManager.SetGeoprocessor

AddMethodMetadata(GeoprocessorManager.SetGeoprocessor,
    shortDescription=_('Instructs the GeoEco package to use the provided object as the ArcGIS geoprocessor.'),
    longDescription=_(
"""In general, :func:`SetGeoprocessor` should never be used and is provided
for testing purposes or very unusual scenarios in which it is necessary to
substitute something for the real geoprocessor. Instead of using this
function, call :func:`InitializeGeoprocessor` instead, to allow the GeoEco
package to instantiate the geoprocessor itself.

If :func:`InitializeGeoprocessor` or :func:`SetGeoprocessor` has already been
called and you call :func:`SetGeoprocessor` again, the
:class:`~GeoEco.ArcGIS.GeoprocessorManager` will delete its existing 
geoprocessor and utilize the new one you provide."""))

AddArgumentMetadata(GeoprocessorManager.SetGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddArgumentMetadata(GeoprocessorManager.SetGeoprocessor, 'geoprocessor',
    typeMetadata=AnyObjectTypeMetadata(),
    description=_('The instance to be used as the geoprocessor by the GeoEco package from now on.'))

# Public method: GeoprocessorManager.GetWrappedGeoprocessor

AddMethodMetadata(GeoprocessorManager.GetWrappedGeoprocessor,
    shortDescription=_('Returns a :py:mod:`weakref` to an object that wraps the ArcGIS geoprocessor and logs all calls to it.'),
    longDescription=_(
"""This function will return None until :func:`InitializeGeoprocessor` or
:func:`SetGeoprocessor` has been called. This function returns a :py:mod:`weakref`
so that callers do not inadvertently maintain references to GeoEco's instance
of the geoprocessor and prevent it from being released.

In general, all GeoEco functions that need to access the geoprocessor should
obtain it by calling this function. If :func:`InitializeGeoprocessor`
(recommended) or :func:`SetGeoprocessor` has not been called yet during the
lifetime of the Python interpreter, it should be called first.

The wrapper object returned by this function automatically performs two kinds
of logging:

1. All geoprocessing messages reported by ArcGIS geoprocessing tools are
   logged as informational, warning, or error messages according to their
   severity.

2. All calls to geoprocessing tools and geoprocessor functions, all
   instantiations of ArcGIS-provided classes, all gets and sets of attributes
   of those instances, and all calls to their methods are logged as debug
   messages that include argument values and return values.

All messages are logged to the `GeoEco.ArcGIS` channel using
:class:`GeoEco.Logging.Logger`. You can configure that channel to see how
GeoEco is using ArcGIS functionality. By default, both debug and informational
messages are filtered out, and only warning and error messages will be shown.
You can configure logging to show informational messages to observe successful
activity from geoprocessing tools that GeoEco uses. Only configure it to show
debug messages when you're trying to diagnose a problem; the volume of debug
messages is so large that performance can be markedly slower.

Please see the :class:`GeoEco.Logging.Logger` documentation for more
information about configuring logging."""))

AddArgumentMetadata(GeoprocessorManager.GetWrappedGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetWrappedGeoprocessor, 'geoprocessor',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('A :py:mod:`weakref` to the wrapped ArcGIS geoprocessor that the GeoEco package is using, or None if neither :func:`InitializeGeoprocessor` nor :func:`SetGeoprocessor` has been called yet.'))

# Public method: GeoprocessorManager.GetArcGISVersion

AddMethodMetadata(GeoprocessorManager.GetArcGISVersion,
    shortDescription=_('Returns the major, minor, and patch version numbers of the installed copy of ArcGIS.'),
    longDescription=_(
"""The version numbers are extracted from the `Version` key of the dictionary
returned by :arcpy:`GetInstallInfo`, unless a `ProVersion` key exists, which
will happen if ArcGIS Server is installed, in which case `ProVersion` will be
used. This means that if ArcGIS Server is installed, the version numbers will
be based on the version of ArcGIS Pro that Server is compatible with, not on
the version numbers of ArcGIS Server itself.

Raises:
    :exc:`SoftwareNotInstalledError`: ArcGIS does not appear to be installed."""))

AddArgumentMetadata(GeoprocessorManager.GetArcGISVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISVersion, 'majorVersion',
    typeMetadata=TupleTypeMetadata(elementType=IntegerTypeMetadata()),
    description=_('A tuple containing the major, minor, and patch version numbers of the installed copy of ArcGIS.'))

# Public method: GeoprocessorManager.GetArcGISMajorVersion

AddMethodMetadata(GeoprocessorManager.GetArcGISMajorVersion,
    shortDescription=_('Returns the major version number of the installed copy of ArcGIS.'),
    longDescription=_(
"""The version number is extracted from the `Version` key of the dictionary
returned by :arcpy:`GetInstallInfo`, unless a `ProVersion` key exists, which
will happen if ArcGIS Server is installed, in which case `ProVersion` will be
used. This means that if ArcGIS Server is installed, the version number will
be based on the version of ArcGIS Pro that Server is compatible with, not on
the version number of ArcGIS Server itself.

Raises:
    :exc:`SoftwareNotInstalledError`: ArcGIS does not appear to be installed."""))

AddArgumentMetadata(GeoprocessorManager.GetArcGISMajorVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISMajorVersion, 'majorVersion',
    typeMetadata=IntegerTypeMetadata(),
    description=_('The major version number of the installed copy of ArcGIS.'))

# Public method: GeoprocessorManager.GetArcGISMinorVersion

AddMethodMetadata(GeoprocessorManager.GetArcGISMinorVersion,
    shortDescription=_('Returns the minor version number of the installed copy of ArcGIS.'),
    longDescription=_(
"""The version number is extracted from the `Version` key of the dictionary
returned by :arcpy:`GetInstallInfo`, unless a `ProVersion` key exists, which
will happen if ArcGIS Server is installed, in which case `ProVersion` will be
used. This means that if ArcGIS Server is installed, the version number will
be based on the version of ArcGIS Pro that Server is compatible with, not on
the version number of ArcGIS Server itself.

Raises:
    :exc:`SoftwareNotInstalledError`: ArcGIS does not appear to be installed."""))

AddArgumentMetadata(GeoprocessorManager.GetArcGISMinorVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISMinorVersion, 'minorVersion',
    typeMetadata=IntegerTypeMetadata(),
    description=_('The minor version number of the installed copy of ArcGIS.'))

# Public method: GeoprocessorManager.GetArcGISPatchVersion

AddMethodMetadata(GeoprocessorManager.GetArcGISPatchVersion,
    shortDescription=_('Returns the patch version number of the installed copy of ArcGIS.'),
    longDescription=_(
"""The version number is extracted from the `Version` key of the dictionary
returned by :arcpy:`GetInstallInfo`, unless a `ProVersion` key exists, which
will happen if ArcGIS Server is installed, in which case `ProVersion` will be
used. This means that if ArcGIS Server is installed, the version number will
be based on the version of ArcGIS Pro that Server is compatible with, not on
the version number of ArcGIS Server itself.

Raises:
    :exc:`SoftwareNotInstalledError`: ArcGIS does not appear to be installed."""))

AddArgumentMetadata(GeoprocessorManager.GetArcGISPatchVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISPatchVersion, 'servicePack',
    typeMetadata=IntegerTypeMetadata(),
    description=_('The patch version number of the installed copy of ArcGIS.'))

# Public method: GeoprocessorManager.GetArcGISProductName

AddMethodMetadata(GeoprocessorManager.GetArcGISProductName,
    shortDescription=_('Returns the product name of the installed copy of ArcGIS.'),
    longDescription=_(
"""Raises:
    :exc:`SoftwareNotInstalledError`: ArcGIS does not appear to be installed."""))

AddArgumentMetadata(GeoprocessorManager.GetArcGISProductName, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISProductName, 'productName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('The product name of the installed copy of ArcGIS, as returned by :arcpy:`GetInstallInfo`.'))

# Public method: GeoprocessorManager.GetArcGISLicenseLevel

AddMethodMetadata(GeoprocessorManager.GetArcGISLicenseLevel,
    shortDescription=_('Returns the license level of the installed copy of ArcGIS.'),
    longDescription=_(
"""Raises:
    :exc:`SoftwareNotInstalledError`: ArcGIS does not appear to be installed."""))

AddArgumentMetadata(GeoprocessorManager.GetArcGISLicenseLevel, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISLicenseLevel, 'licenseLevel',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('The license level of the installed copy of ArcGIS, as returned by :arcpy:`GetInstallInfo`, or None if no license level was returned by that function.'))

# Public method: GeoprocessorManager.InitializeGeoprocessor

AddMethodMetadata(GeoprocessorManager.InitializeGeoprocessor,
    shortDescription=_('Initializes the ArcGIS geoprocessor so that the GeoEco package can access ArcGIS functionality.'),
    longDescription=_(
"""It is usually not necessary for methods within GeoEco to call
:func:`InitializeGeoprocessor` directly. The usual pattern for implementing
a GeoEco method that needs to access ArcGIS is to define a 
:mod:`~GeoEco.Metadata.MethodMetadata` for the method with the `dependencies`
argument set to a :py:class:`list` containing an
:class:`~GeoEco.ArcGIS.ArcGISDependency`. Then, as usual for methods that
define a :mod:`~GeoEco.Metadata.MethodMetadata`, the method calls 
:func:`~GeoEco.Metadata.ClassMetadata.ValidateMethodInvocation` as its first
line of code, which initializes the :class:`~GeoEco.ArcGIS.ArcGISDependency`,
which in turn calls :func:`InitializeGeoprocessor`. The method can then use
:func:`GetWrappedGeoprocessor` to get the geoprocessor instance and access
ArcGIS:

.. code-block:: python

    from GeoEco.ArcGIS import GeoprocessorManager

    class MyClass(object):
        @classmethod
        def MyMethodThatAccessesArcGIS(cls):
            self.__doc__.Obj.ValidateMethodInvocation()

            # ValidateMethodInvocation() initialized the ArcGISDependency(),
            # which called InitializeGeoprocessor() for us. We can now just call
            # GetWrappedGeoprocessor().

            gp = GeoprocessorManager.GetWrappedGeoprocessor()
            gp.XXXXX(...)       # Call some geoprocessor tool or function

When using the :class:`~GeoEco.ArcGIS.GeoprocessorManager` from a stand-alone
script or other contexts that do not involve initializing a 
:class:`~GeoEco.ArcGIS.ArcGISDependency`, it is necessary to call 
:func:`InitializeGeoprocessor` explicitly:

.. code-block:: python

    from GeoEco.ArcGIS import GeoprocessorManager

    def MyStandAloneScript():
        GeoprocessorManager.InitializeGeoprocessor()
        gp = GeoprocessorManager.GetWrappedGeoprocessor()
        gp.XXXXX(...)       # Call some geoprocessor tool or function

    if __name__ == '__main__':
        MyStandAloneScript()

If you do not want to use :func:`InitializeGeoprocessor` to instantiate the
geoprocessor, you should create it yourself and call :func:`SetGeoprocessor`.
:class:`~GeoEco.ArcGIS.GeoprocessorManager` will cache a reference to your
geoprocessor and use it instead. :class:`~GeoEco.ArcGIS.GeoprocessorManager`
maintains a single, interpreter-wide geoprocessor shared by all of its
callers.

There is no harm in calling :func:`InitializeGeoprocessor` after it or 
:func:`SetGeoprocessor` has already been called. If 
:class:`~GeoEco.ArcGIS.GeoprocessorManager` already has a geoprocessor,
:func:`InitializeGeoprocessor` will do nothing. If you need to replace the
geoprocessor that :class:`~GeoEco.ArcGIS.GeoprocessorManager` is using, you
can call :func:`SetGeoprocessor`."""))

AddArgumentMetadata(GeoprocessorManager.InitializeGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

# Public method: GeoprocessorManager.ArcGISObjectExists

AddMethodMetadata(GeoprocessorManager.ArcGISObjectExists,
    shortDescription=_('Tests that a given path to an ArcGIS object exists and that the object is of a given type.'),
    longDescription=_(
"""This method uses the ArcGIS geoprocessor's Exists and Describe
functions to check the existence and type of the object."""))

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_(':class:`%s` or an instance of it.') % GeoprocessorManager.__name__)

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'path',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the object (e.g. a file, directory, raster, shapefile, table, etc.).'))

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'correctTypes',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata()),
    description=_(
"""List of data types that the object is expected to be, chosen from the
possible values of the `dataType` property of the object returned by
:arcpy:`Describe`. Please see the documentation for that function for the
possible values."""))

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'typeDisplayName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the expected data type of the object to display in logging
messages. This is usually a more generic name than the entries that appear in
`correctTypes`. For example, if the object is expected to be some kind of
table, `correctTypes` may contain five or ten possible values, while
`typeDisplayName` might simply be "table"."""))

AddResultMetadata(GeoprocessorManager.ArcGISObjectExists, 'result',
    typeMetadata=TupleTypeMetadata(elementType=BooleanTypeMetadata(), minLength=2, maxLength=2),
    description=_('A :py:class:`tuple` of two :py:class:`bool`, where the first is True if the geoprocessor\'s :arcpy:`Exists` function reports that the specified path exists, and the second True if the geoprocessor\'s :arcpy:`Describe` function reports that it is one of the types of objects specified by `correctTypes`.'))

# Public method: GeoprocessorManager.DeleteArcGISObject

AddMethodMetadata(GeoprocessorManager.DeleteArcGISObject,
    shortDescription=_('Deletes the specified ArcGIS object, if it exists.'),
    longDescription=_(
"""The object will be deleted with the :arcpy_management:`Delete`
geoprocessing tool. If the object does not exist, :arcpy_management:`Delete`
will not be called, and no error will be reported.

Raises:
    :exp:`ValueError`: The object exists but the geoprocessor's
        :arcpy:`Describe` function reports that it is not one of the types
        specified by `correctTypes`.
"""))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls', GeoprocessorManager.DeleteArcGISObject, 'cls')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'path', GeoprocessorManager.DeleteArcGISObject, 'path')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'correctTypes', GeoprocessorManager.DeleteArcGISObject, 'correctTypes')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'typeDisplayName', GeoprocessorManager.DeleteArcGISObject, 'typeDisplayName')

# Public method: GeoprocessorManager.CopyArcGISObject

AddMethodMetadata(GeoprocessorManager.CopyArcGISObject,
    shortDescription=_('Copies the specified ArcGIS object.'),
    longDescription=_(
"""First, if `overwriteExisting` is True and `destination` exists, it will be
deleted with the :arcpy_management:`Delete` geoprocessing tool. Then, if
`source` is a feature class, shapefile, or feature layer, it will be copied
with :arcpy_management:`Copy-Features`. If `source` is something else, it will
be copied with :arcpy_management:`Copy`.

Raises:
    :exp:`ValueError`: The source object does not exist or the geoprocessor's
        :arcpy:`Describe` function reports that it is not one of the types
        specified by `correctTypes`, or the destination object exists but
        either it is not one of the `correctTypes` or `overwriteExisting` is
        False.
"""))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls', GeoprocessorManager.CopyArcGISObject, 'cls')

AddArgumentMetadata(GeoprocessorManager.CopyArcGISObject, 'source',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the object to copy (e.g. a file, directory, raster, shapefile, table, etc.).'))

AddArgumentMetadata(GeoprocessorManager.CopyArcGISObject, 'destination',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the copy to create.'))

AddArgumentMetadata(GeoprocessorManager.CopyArcGISObject, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, `destination` will be overwritten.'))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'correctTypes', GeoprocessorManager.CopyArcGISObject, 'correctTypes')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'typeDisplayName', GeoprocessorManager.CopyArcGISObject, 'typeDisplayName')

# Public method: GeoprocessorManager.MoveArcGISObject

AddMethodMetadata(GeoprocessorManager.MoveArcGISObject,
    shortDescription=_('Moves the specified ArcGIS object.'),
    longDescription=_(
"""First, if `overwriteExisting` is True and `destination` exists, it will be
deleted with the :arcpy_management:`Delete` geoprocessing tool. Then, if
`source` is a feature class, shapefile, or feature layer, it will be copied
with :arcpy_management:`Copy-Features`. If `source` is something else, it will
be copied with :arcpy_management:`Copy`. Finally, `source` will be deleted
with :arcpy_management:`Delete`.

Raises:
    :exp:`ValueError`: The source object does not exist or the geoprocessor's
        :arcpy:`Describe` function reports that it is not one of the types
        specified by `correctTypes`, or the destination object exists but
        either it is not one of the `correctTypes` or `overwriteExisting` is
        False.
"""))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls', GeoprocessorManager.MoveArcGISObject, 'cls')

AddArgumentMetadata(GeoprocessorManager.MoveArcGISObject, 'source',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the object to move (e.g. a file, directory, raster, shapefile, table, etc.).'))

AddArgumentMetadata(GeoprocessorManager.MoveArcGISObject, 'destination',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('New path for the object.'))

CopyArgumentMetadata(GeoprocessorManager.CopyArcGISObject, 'overwriteExisting', GeoprocessorManager.MoveArcGISObject, 'overwriteExisting')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'correctTypes', GeoprocessorManager.MoveArcGISObject, 'correctTypes')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'typeDisplayName', GeoprocessorManager.MoveArcGISObject, 'typeDisplayName')

# Public method: GeoprocessorManager.GetUniqueLayerName

AddMethodMetadata(GeoprocessorManager.GetUniqueLayerName,
    shortDescription=_('Returns a randomly generated string that may be used as the name of a new geoprocessing layer.'),
    longDescription=_(
"""This function loops through random names until it finds one for which the
geoprocessor's :arcpy:`Exists` function returns False."""))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls', GeoprocessorManager.GetUniqueLayerName, 'cls')

AddResultMetadata(GeoprocessorManager.GetUniqueLayerName, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Randomly generated string that may be used as the name of a geoprocessing layer.'))

###############################################################################
# Metadata: ArcGISDependency class
###############################################################################

AddClassMetadata(ArcGISDependency,
    shortDescription=_('A :class:`~GeoEco.Dependencies.Dependency` that checks that ArcGIS and its Python package is installed, and its version.'),
    longDescription=_(
"""When :func:`Initialize` is called and the version numbers are checked, they
will be extracted from the `Version` key of the dictionary returned by
:arcpy:`GetInstallInfo`, unless a `ProVersion` key exists, which will happen
if ArcGIS Server is installed, in which case `ProVersion` will be used. This
means that if ArcGIS Server is installed, :func:`Initialize` will check the
version of ArcGIS Pro that Server is compatible with, not the version of ArcGIS
Server itself."""))

# Properties

AddPropertyMetadata(ArcGISDependency.MinimumMajorVersion,
    typeMetadata=IntegerTypeMetadata(minValue=1),
    shortDescription=_('Minimum major version number of ArcGIS that must be installed.'))

AddPropertyMetadata(ArcGISDependency.MinimumMinorVersion,
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    shortDescription=_('Minimum major version number of ArcGIS that must be installed.'))

AddPropertyMetadata(ArcGISDependency.MinimumPatchVersion,
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    shortDescription=_('Minimum patch version number of ArcGIS that must be installed.'))

AddPropertyMetadata(ArcGISDependency.ProductNames,
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1),
    shortDescription=_('List ArcGIS product names, at least one of which must be installed.'))

AddPropertyMetadata(ArcGISDependency.LicenseLevels,
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    shortDescription=_('List ArcGIS license levels, at least one of which must be installed. If None, then license levels will not be checked.'))
    
# Constructor

AddMethodMetadata(ArcGISDependency.__init__,
    shortDescription=_('Constructs a new %s instance.') % ArcGISDependency.__name__)

AddArgumentMetadata(ArcGISDependency.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISDependency),
    description=_(':class:`%s` instance.') % ArcGISDependency.__name__)

AddArgumentMetadata(ArcGISDependency.__init__, 'minimumMajorVersion',
    typeMetadata=ArcGISDependency.MinimumMajorVersion.__doc__.Obj.Type,
    description=ArcGISDependency.MinimumMajorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISDependency.__init__, 'minimumMinorVersion',
    typeMetadata=ArcGISDependency.MinimumMinorVersion.__doc__.Obj.Type,
    description=ArcGISDependency.MinimumMinorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISDependency.__init__, 'minimumPatchVersion',
    typeMetadata=ArcGISDependency.MinimumPatchVersion.__doc__.Obj.Type,
    description=ArcGISDependency.MinimumPatchVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISDependency.__init__, 'productNames',
    typeMetadata=ArcGISDependency.ProductNames.__doc__.Obj.Type,
    description=ArcGISDependency.ProductNames.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISDependency.__init__, 'licenseLevels',
    typeMetadata=ArcGISDependency.LicenseLevels.__doc__.Obj.Type,
    description=ArcGISDependency.LicenseLevels.__doc__.Obj.ShortDescription)

AddResultMetadata(ArcGISDependency.__init__, 'dependency',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISDependency),
    description=_('New :class:`%s` instance.') % ArcGISDependency.__name__)

# Public method: SetVersion

AddMethodMetadata(ArcGISDependency.SetVersion,
    shortDescription=_('Sets the minimum version number of ArcGIS that must be installed.'))

AddArgumentMetadata(ArcGISDependency.SetVersion, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISDependency),
    description=_(':class:`%s` instance.') % ArcGISDependency.__name__)

AddArgumentMetadata(ArcGISDependency.SetVersion, 'minimumMajorVersion',
    typeMetadata=ArcGISDependency.MinimumMajorVersion.__doc__.Obj.Type,
    description=ArcGISDependency.MinimumMajorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISDependency.SetVersion, 'minimumMinorVersion',
    typeMetadata=ArcGISDependency.MinimumMinorVersion.__doc__.Obj.Type,
    description=ArcGISDependency.MinimumMinorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISDependency.SetVersion, 'minimumPatchVersion',
    typeMetadata=ArcGISDependency.MinimumPatchVersion.__doc__.Obj.Type,
    description=ArcGISDependency.MinimumPatchVersion.__doc__.Obj.ShortDescription)

###############################################################################
# Metadata: ArcGISExtensionDependency class
###############################################################################

AddClassMetadata(ArcGISExtensionDependency,
    shortDescription=_('A :class:`~GeoEco.Dependencies.Dependency` that checks that an ArcGIS extension is installed.'))

# Properties

AddPropertyMetadata(ArcGISExtensionDependency.ExtensionCode,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Product code of the extension that must be installed. Generally these are two characters, such as ``\'sa\'`` for Spatial Analyst and ``\'na\'`` for Network Analyst.'))
    
# Constructor

AddMethodMetadata(ArcGISExtensionDependency.__init__,
    shortDescription=_('Constructs a new %s instance.') % ArcGISExtensionDependency.__name__)

AddArgumentMetadata(ArcGISExtensionDependency.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISExtensionDependency),
    description=_(':class:`%s` instance.') % ArcGISExtensionDependency.__name__)

AddArgumentMetadata(ArcGISExtensionDependency.__init__, 'extensionCode',
    typeMetadata=ArcGISExtensionDependency.ExtensionCode.__doc__.Obj.Type,
    description=ArcGISExtensionDependency.ExtensionCode.__doc__.Obj.ShortDescription)

AddResultMetadata(ArcGISExtensionDependency.__init__, 'dependency',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISExtensionDependency),
    description=_('New :class:`%s` instance.') % ArcGISExtensionDependency.__name__)

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['GeoprocessorManager',
           'ArcGISDependency',
           'ArcGISExtensionDependency',
           'ValidateMethodMetadataForExposureAsArcGISTool']
