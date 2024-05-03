# ArcGIS.py - Provides utility functions for interacting with the ESRI ArcGIS
# software package.
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

from GeoEco.Dependencies import Dependency, SoftwareNotInstalledError
from GeoEco.DynamicDocString import DynamicDocString
from GeoEco.Logging import Logger
from GeoEco.Internationalization import _
from GeoEco.Metadata import ClassMetadata, MethodMetadata, TypeMetadata


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
        gp = GetWrappedGeoprocessor()
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

        GeoprocessorManager._ProductName = installInfo['ProductName']

        # Extract the LicenseLevel, if available. This item was not available
        # in ArcGIS Desktop 10.x. It is availble in ArcGIS Pro 3.2, but I'm
        # not sure about earlier versions.

        if 'LicenseLevel' in installInfo:
            GeoprocessorManager._ArcGISLicenseLevel = installInfo['LicenseLevel']

    @classmethod
    def RefreshCatalog(cls, directory):
        cls.__doc__.Obj.ValidateMethodInvocation()
        gp = cls.GetWrappedGeoprocessor()
        if gp is not None:
            gp.RefreshCatalog(directory)
            Logger.Debug(_('Refreshed the ArcGIS catalog for directory %s'), directory)

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
            gp.Delete_Management(path)
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
                gp.Copy_Management(source, destination)
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
                gp.Copy_Management(source, destination)
            gp.Delete_Management(source)
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

    def __init__(self, minimumMajorVersion, minimumMinorVersion=None, minimumPatchVersion=None, productNames=['ArcGISPro', 'Server'], licenseLevels=None):
        self.SetVersion(minimumMajorVersion, minimumMinorVersion, minimumPatchVersion)
        self.ProductNames = productNames
        self.LicenseLevels = licenseLevels

    def SetVersion(self, minimumMajorVersion, minimumMinorVersion=None, minimumPatchVersion=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

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
                    Logger.Debug(_('An ArcGIS Pro-compatible verison of ArcGIS Server is installed with an equivalent ArcGIS Pro version of %i.%i.%i and a license level of %s.'), major, minor, patch, licenseLevel if licenseLevel is not None else 'Unknown')
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
        _ArcGISObjectWrapper._LogDebug('Wrapping object %s', repr(obj))     # Do not remove repr() from here. For some reason, the message does not get logged without it.
        self._Object = obj
        self._WrappedMethods = {}

    def __getattr__(self, name):
        assert isinstance(name, str), 'name must be a string.'

        # If the caller is asking for a private attribute (the name starts
        # with an underscore), they want an attribute of the wrapper class
        # instance, not of the wrapped object. In this case, we must use the
        # object class's implementation of __getattribute__.

        if name.startswith('_'):
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
        # exception.
        
        except Exception as e:
            self._LogError(_('Failed to get the value of the %(name)s attribute of %(obs)s. This may result from a problem with your inputs or it may indicate a programming mistake in this tool or ArcGIS itself. Please check your inputs and try again. Also review any preceding error messages and the detailed error information that appears at the end of this message. If you suspect a programming mistake in this tool or ArcGIS, please contact the author of this tool for assistance. Detailed error information: The following exception was raised when the attribute was retrieved: %(error)s: %(msg)s') % {'name': name, 'obj': self._Object, 'error': e.__class__.__name__, 'msg': e})
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

        self._LogDebug('%s.%s returned %r', self._Object, name, value)

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

        self._LogDebug('Set %s.%s to %r', self._Object, name, value)

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

        # TODO:
        #
        # Before invoking the method, check whether it is a Spatial
        # Analyst tool, which is indicated by it ending in "_sa". If
        # it is, create a temp directory and set the ScratchWorkspace
        # to it.
        #
        # We do this because some Spatial Analyst tools, particularly
        # the Map Algebra tools, create temporary ArcInfo binary grids
        # as part of their processing, but they do not delete them
        # upon completion. These will accumulate in the user's TEMP
        # directory unless a ScratchWorkspace has been set. Once
        # several thousand exist, the Spatial Analyst tools will stop
        # working (ArcCatalog or ArcMap will crash) until they are
        # deleted.
        #
        # Users typically encounter this only after running several
        # thousand Spatial Analyst tools without logging off. Windows
        # deletes the contents of the TEMP directory at logoff.
        # Nonetheless, certain batch jobs, such as converting
        # thousands of HDFs to rasters, are common scenarios for
        # GeoEco users so we must protect them from this problem.

        # try:
        #     tempDir = None
        #     scratchDir = None
        #     if self._Name == 'Geoprocessor' and methodName.endswith('_sa'):
        #         scratchDir = self.ScratchWorkspace
        #         from GeoEco.DataManagement.Directories import TemporaryDirectory
        #         tempDir = TemporaryDirectory()
        #         self.ScratchWorkspace = tempDir.Path

        #     # Invoke the method.

        # # If we created a temporary directory to manage the rasters
        # # leaked by the Spatial Analyst tools, delete it now.

        # finally:
        #     if tempDir is not None:
        #         try:
        #             del tempDir
        #         except:
        #             pass
        #         self.ScratchWorkspace = scratchDir

        # Convert the arguments to the geoprocessor's preferred types.

        if args is not None:
            args = tuple([self._ToGeoprocessorPreferredType(arg) for arg in args])

        if kwargs is not None:
            kwargs = {param:self._ToGeoprocessorPreferredType(arg) for param, arg in kwargs.items()}

        # Log a message indicating we're calling the function.

        try:
            sig = inspect.signature(func)
            boundArgs = sig.bind(*args, **kwargs)
            argsStr = ', '.join(f'{key}={value!r}' for key, value in boundArgs.arguments.items())
        except:
            argsStr = ', '.join([repr(arg) for arg in args] + ['%s=%r' % (key, value) for key, value in kwargs.items()])

        _ArcGISObjectWrapper._LogDebug('Calling %s(%s)', funcName, argsStr)

        # Call the function.

        try:
            result = func(*args, **kwargs)

        # If we an caught exception, log the geoprocessing messages and raise
        # the exception as ArcGISError. Note: call raise, rather than
        # Logger.RaiseException, so the caller can swallow the exception, if
        # needed.
        
        except Exception as e:
            self._LogReturnedGeoprocessingMessages(func)
            self._LogError(_('Execution of %(funcName)s failed when given the inputs %(args)s and reported %(error)s: %(msg)s. This may result from a problem with your inputs or it may indicate a programming mistake in this tool or ArcGIS itself. Please review any preceding error messages, check your inputs, and try again. If you suspect a programming mistake in this tool or ArcGIS, please contact the author of this tool for assistance.') % {'funcName': funcName, 'args': argsStr, 'error': e.__class__.__name__, 'msg': e})
            raise

        # The method executed successfully. Log any geoprocessing messages it
        # generated.

        self._LogReturnedGeoprocessingMessages(func)

        # Log a message reporting the result.

        _ArcGISObjectWrapper._LogDebug('%s returned %r', funcName, result)

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

        if value is None or isinstance(value, (bool, int, float, complex, str, datetime.datetime)):
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


###############################################################################
# Metadata: module
###############################################################################

from GeoEco.Metadata import *
from GeoEco.Types import *

AddModuleMetadata(shortDescription=_('Provides utility functions for interacting with the ESRI ArcGIS software package.'))

###############################################################################
# Metadata: GeoprocessorManager class
###############################################################################

AddClassMetadata(GeoprocessorManager,
    shortDescription=_('Manages the instance of the ArcGIS geoprocessor object used whenever any GeoEco function needs to invoke ArcGIS tools.'))

# Public properties

# AddPropertyMetadata(GeoprocessorManager.Geoprocessor,
#     typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
#     shortDescription=_('The ArcGIS geoprocessor object used whenever any GeoEco function needs to invoke ArcGIS tools.'),
#     longDescription=_(
# """This property is a singleton; all Python modules running in the same
# instance of the Python interpreter share the same value for this property. This
# property remains empty until it is explicitly set, or the InitializeGeoprocessor
# method is explicitly invoked, or a GeoEco function that has a dependency on
# ArcGIS is invoked (in which case it will invoke InitializeGeoprocessor).

# If you want to invoke GeoEco functions from your own ArcGIS geoprocessing script
# and you have already obtained a geoprocessor object, you should set this
# property to that object before invoking any other GeoEco functions. Failing to
# do so will cause GeoEco to allocate its own geoprocessor object, which can yield
# unpredictable results. (As far as I can tell, the ArcGIS tools still work
# correctly, but log messages may not end up in the ArcGIS GUIs.)

# If your geoprocessing script has not yet obtained the geoprocessor object, you
# may allow the GeoEco functions to obtain one when they first need it and then
# retrieve it by getting the value of this property.

# If you want to invoke GeoEco functions from something that is not a
# "geoprocessing script" (a program that does not invoke any ArcGIS
# geoprocessing tools directly), then you should ignore this property and
# allow the GeoEco functions to obtain and use their own geoprocessor object.

# See the documentation for InitializeGeoprocessor for more information about this
# property.

# *Note to GeoEco developers:* Generally, GeoEco functions should *not* use this
# property; they should use WrappedGeoprocessor instead. That property implements
# a wrapper around the geoprocessor that logs debug messages every time the
# geoprocessor is invoked."""))

# AddPropertyMetadata(GeoprocessorManager.WrappedGeoprocessor,
#     typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
#     shortDescription=_('The Geoprocessor property, wrapped by a class that logs messages whenever the geoprocessor is accessed.'),
#     longDescription=_(
# """This property is a singleton; all Python modules running in the same
# instance of the Python interpreter share the same value for this property. It is
# initialized whenever the Geoprocessor property is initialized; see the
# documentation for that property for more information.

# This property is actually a wrapper class around the ArcGIS geoprocessor object.
# The wrapper exports the same interface as the wrapped object but logs a debug
# message every time a method is invoked or a property is accessed. By default,
# these debug messages are discarded by the GeoEco logging infrastructure. You can
# enable them by initializing the Logger class with a custom configuration file
# or by editing the default configuration file. See the Logger class documentation
# for more information.

# All GeoEco functions use WrappedGeoprocessor to access the geoprocessor, rather
# than the Geoprocessor property, so that debug messages are reported whenever any
# function accesses the geoprocessor. External callers are welcome to use
# WrappedGeoprocessor as well, but they should consider using Geoprocessor
# instead, to completely eliminate the chance that a bug in the wrapper would
# affect their code."""))

# AddPropertyMetadata(GeoprocessorManager.ArcGISMajorVersion,
#     typeMetadata=IntegerTypeMetadata(canBeNone=True),
#     shortDescription=_('The major version number for ArcGIS, if it is installed on the machine.'),
#     longDescription=_('This property is empty if ArcGIS is not installed on the machine.'))

# AddPropertyMetadata(GeoprocessorManager.ArcGISMinorVersion,
#     typeMetadata=IntegerTypeMetadata(canBeNone=True),
#     shortDescription=_('The minor version number for ArcGIS, if it is installed on the machine.'),
#     longDescription=_('This property is empty if ArcGIS is not installed on the machine.'))

# AddPropertyMetadata(GeoprocessorManager.ArcGISPatchVersion,
#     typeMetadata=IntegerTypeMetadata(canBeNone=True),
#     shortDescription=_('The service pack number for ArcGIS, if it is installed on the machine.'),
#     longDescription=_('This property is empty if ArcGIS is not installed on the machine.'))

# Public method: GeoprocessorManager.GetGeoprocessor

AddMethodMetadata(GeoprocessorManager.GetGeoprocessor,
    shortDescription=_('Returns the value of the Geoprocessor property.'))

AddArgumentMetadata(GeoprocessorManager.GetGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetGeoprocessor, 'geoprocessor',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('The value of the Geoprocessor property.'))

# Public method: GeoprocessorManager.SetGeoprocessor

AddMethodMetadata(GeoprocessorManager.SetGeoprocessor,
    shortDescription=_('Sets the value of the Geoprocessor property.'))

AddArgumentMetadata(GeoprocessorManager.SetGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddArgumentMetadata(GeoprocessorManager.SetGeoprocessor, 'geoprocessor',
    typeMetadata=AnyObjectTypeMetadata(),
    description=_('The ArcGIS geoprocessor object obtained the Python arcpy module. See the documentation for the Geoprocessor property for more information.'))

# Public method: GeoprocessorManager.GetWrappedGeoprocessor

AddMethodMetadata(GeoprocessorManager.GetWrappedGeoprocessor,
    shortDescription=_('Returns the value of the WrappedGeoprocessor property.'))

AddArgumentMetadata(GeoprocessorManager.GetWrappedGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetWrappedGeoprocessor, 'geoprocessor',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_('The value of the WrappedGeoprocessor property.'))

# Public method: GeoprocessorManager.GetArcGISMajorVersion

AddMethodMetadata(GeoprocessorManager.GetArcGISMajorVersion,
    shortDescription=_('Returns the value of the ArcGISMajorVersion property.'))

AddArgumentMetadata(GeoprocessorManager.GetArcGISMajorVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISMajorVersion, 'majorVersion',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_('The value of the ArcGISMajorVersion property.'))

# Public method: GeoprocessorManager.GetArcGISMinorVersion

AddMethodMetadata(GeoprocessorManager.GetArcGISMinorVersion,
    shortDescription=_('Returns the value of the ArcGISMinorVersion property.'))

AddArgumentMetadata(GeoprocessorManager.GetArcGISMinorVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISMinorVersion, 'minorVersion',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_('The value of the ArcGISMinorVersion property.'))

# Public method: GeoprocessorManager.GetArcGISPatchVersion

AddMethodMetadata(GeoprocessorManager.GetArcGISPatchVersion,
    shortDescription=_('Returns the value of the ArcGISPatchVersion property.'))

AddArgumentMetadata(GeoprocessorManager.GetArcGISPatchVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddResultMetadata(GeoprocessorManager.GetArcGISPatchVersion, 'servicePack',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_('The value of the ArcGISMinorVersion property.'))

# Public method: GeoprocessorManager.InitializeGeoprocessor

AddMethodMetadata(GeoprocessorManager.InitializeGeoprocessor,
    shortDescription=_('Initializes the Geoprocessor property with a new ArcGIS geoprocessor object.'),
    longDescription=_(
"""If you want to use GeoEco's GeoprocessorManager to instantiate the
geoprocessor, you should either explicitly invoke this method or call
a GeoEco function that requires ArcGIS; the GeoEco function will
invoke this method on your behalf.

If you do not want to use GeoEco's GeoprocessorManager to instantiate
the geoprocessor, you should instantiate it yourself and call
GeoprocessorManager.SetGeoprocessor. GeoEco will cache a reference to
your geoprocessor and not allocate its own instance.

If the Geoprocessor property has already been initialized with a
geoprocessor object and forceCOMInstantiation and
forcePythonInstantiation are both False, this method does nothing. If
either forceCOMInstantiation or forcePythonInstantiation are True,
this method will raise a RuntimeError if the geoprocessor was
previously instantiated with the opposite method.

You should only pass True for forceCOMInstantiation or
forcePythonInstantiation if you plan to perform geoprocessing
operations that truly require one type of geoprocessor or the other.
If both are False, this method will automatically select the best
technique, as follows:

* If ArcGIS 9.1 is installed, COM Automation will always be used.

* If ArcGIS 9.2 is installed, arcgisscripting will be used if the
  script is executing under Python 2.4. Otherwise COM Automation will
  be used.

* If ArcGIS 9.3 is installed, arcgisscripting will be used if the
  script is executing under Python 2.5. Otherwise COM Automation will
  be used.

IMPORTANT NOTE: If arcgisscripting is used to instantiate the
geoprocessor, the arcgisscripting.create function will always be
called without any parameters, regardless of which version of ArcGIS
is installed. This means that, even if ArcGIS 9.3 or later is
installed, the instantiated geoprocessor will always use the inteface
from ArcGIS 9.2."""))

AddArgumentMetadata(GeoprocessorManager.InitializeGeoprocessor, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

# Public method: GeoprocessorManager.RefreshCatalog

AddMethodMetadata(GeoprocessorManager.RefreshCatalog,
    shortDescription=_('Refreshes the ArcGIS catalog\'s cached view of the specified directory.'),
    longDescription=_(
"""The ArcGIS geoprocessing system interacts with the file system through the
ArcGIS catalog, a cached view of the files and directories on the computer. It
is important that the catalog be "refreshed" after any changes are made to files
or directories. Otherwise the ArcGIS geoprocessor will not know about the
changes and operate off an obsolete view of the file system, ultimately causing
subsequent geoprocessing operations to fail.

Most GeoEco methods automatically refresh the ArcGIS catalog when it is
necessary to do so. Some methods allow you to explictly control whether the
refresh occurs. In general, you should always allow the catalog to be refreshed.
The main scenario in which it is appropriate to prevent it is when you are
making many consecutive changes inside a directory and do not want to incur the
performance hit of refreshing the catalog after each change. In that scenario,
you can use this method to refresh the catalog's view of that directory when you
are done.

If the GeoprocessorManager class is not holding an instance of the ArcGIS
geoprocessor, then this parameter is ignored. It will be holding one under the
following circumstances:

* Your code invokes a method of some class that has a dependency on ArcGIS and
  internally uses the geoprocessor to do whatever work it needs to do. In this,
  scenario, that method will cause GeoprocessorManager.InitializeGeoprocessor() to
  be called. This is the most common scenario.
  
* Your code explicitly initializes the geoprocessor by calling
  GeoprocessorManager.InitializeGeoprocessor().

* Your code provides the GeoprocessorManager with a geoprocessor instance by
  calling GeoprocessorManager.SetGeoprocessor()."""))

AddArgumentMetadata(GeoprocessorManager.RefreshCatalog, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddArgumentMetadata(GeoprocessorManager.RefreshCatalog, 'directory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_(
"""Parent directory of the files or directories that have changed. For example,
if you added three files to C:\\Data, you should pass C:\\Data as this
parameter. If you just created C:\\Data, then you need to pass C:\\ for this
parameter."""))

# Public method: GeoprocessorManager.ArcGISObjectExists

AddMethodMetadata(GeoprocessorManager.ArcGISObjectExists,
    shortDescription=_('Tests that a given path to an ArcGIS object exists and that the object is of a given type.'),
    longDescription=_(
"""This method uses the ArcGIS geoprocessor's Exists and Describe
functions to check the existence and type of the object."""))

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GeoprocessorManager),
    description=_('%s class or an instance of it.') % GeoprocessorManager.__name__)

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'path',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the object (e.g. a file, directory, raster, shapefile, table, etc.).'))

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'correctTypes',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata()),
    description=_(
"""List of data types that the object is expected to be, chosen from
the possible values of the DataType property of the object returned by
the geoprocessor's Describe function. Please see the ArcGIS
geoprocessing documentation for the possible data type strings."""))

AddArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'typeDisplayName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the expected data type of the object to display in logging
messages. This is usually a more generic name than the entries that
appear in correctTypes. For example, if the object is expected to be
some kind of table, correctTypes may contain five or ten possible
values, while typeDisplayName might simply be "table"."""))

AddResultMetadata(GeoprocessorManager.ArcGISObjectExists, 'exists',
    typeMetadata=BooleanTypeMetadata(),
    description=_('True if the geoprocessor\'s Exists function reports that the specified path exists.'))

AddResultMetadata(GeoprocessorManager.ArcGISObjectExists, 'isCorrectType',
    typeMetadata=BooleanTypeMetadata(),
    description=_('True if the geoprocessor\'s Describe function reports that the specified path is one of the types of objects specified by correctTypes.'))

# Public method: GeoprocessorManager.DeleteArcGISObject

AddMethodMetadata(GeoprocessorManager.DeleteArcGISObject,
    shortDescription=_('Deletes the specified ArcGIS object, if it exists.'),
    longDescription=_(
"""If the object does not exist, no error will be raised. If the
object exists but the geoprocessor's Describe function reports that it
is not one of the types specified by the correctTypes parameter, a
ValueError will be raised. If it exists and is one of the correct
types, it will be deleted with the geoprocessor's Delete_management
function."""))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls', GeoprocessorManager.DeleteArcGISObject, 'cls')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'path', GeoprocessorManager.DeleteArcGISObject, 'path')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'correctTypes', GeoprocessorManager.DeleteArcGISObject, 'correctTypes')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'typeDisplayName', GeoprocessorManager.DeleteArcGISObject, 'typeDisplayName')

# Public method: GeoprocessorManager.CopyArcGISObject

AddMethodMetadata(GeoprocessorManager.CopyArcGISObject,
    shortDescription=_('Copies the specified ArcGIS object.'),
    longDescription=_(
"""A ValueError will be raised if the source object does not exist or
the geoprocessor's Describe function reports that it is not one of the
types specified by the correctTypes parameter. A ValueError will also
be raised if the destination object exists but overwriteExisting is
False or if the object is not one of the correct types. If the
destination object exists and is a correct type, it will be deleted
with the geoprocessor's Delete_management function prior to making the
copy. The source object will be copied with the geoprocessor's
CopyFeatures_management (if the source object is a feature class,
shapefile, or feature layer) or the Copy_management function (if the
source object is some other type)."""))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls', GeoprocessorManager.CopyArcGISObject, 'cls')

AddArgumentMetadata(GeoprocessorManager.CopyArcGISObject, 'source',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the object to copy (e.g. a file, directory, raster, shapefile, table, etc.).'))

AddArgumentMetadata(GeoprocessorManager.CopyArcGISObject, 'destination',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the copy to create.'))

AddArgumentMetadata(GeoprocessorManager.CopyArcGISObject, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, the destination object will be overwritten.'))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'correctTypes', GeoprocessorManager.CopyArcGISObject, 'correctTypes')
CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'typeDisplayName', GeoprocessorManager.CopyArcGISObject, 'typeDisplayName')

# Public method: GeoprocessorManager.MoveArcGISObject

AddMethodMetadata(GeoprocessorManager.MoveArcGISObject,
    shortDescription=_('Movies the specified ArcGIS object.'),
    longDescription=_(
"""A ValueError will be raised if the source object does not exist or
the geoprocessor's Describe function reports that it is not one of the
types specified by the correctTypes parameter. A ValueError will also
be raised if the destination object exists but overwriteExisting is
False or if the object is not one of the correct types. If the
destination object exists and is a correct type, it will be deleted
with the geoprocessor's Delete_management function prior to making the
copy. The source object will be copied with the geoprocessor's
CopyFeatures_management (if the source object is a feature class,
shapefile, or feature layer) or the Copy_management function (if the
source object is some other type), and then deleted with the
Delete_management function."""))

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
"""This function loops through random names until it finds one for
which the geoprocessors Exists function returns False."""))

CopyArgumentMetadata(GeoprocessorManager.ArcGISObjectExists, 'cls', GeoprocessorManager.GetUniqueLayerName, 'cls')

AddResultMetadata(GeoprocessorManager.GetUniqueLayerName, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Randomly generated string that may be used as the name of a geoprocessing layer.'))

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['GeoprocessorManager',
           'ArcGISDependency',
           'ArcGISExtensionDependency',
           'ValidateMethodMetadataForExposureAsArcGISTool']
