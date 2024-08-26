# Dependencies.py - Classes that allow other classes in the GeoEco Python
# package to declare dependencies on other software.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os
import platform
import types
import io
import sys

from .DynamicDocString import DynamicDocString
from .Exceptions import GeoEcoError
from .Internationalization import _


# Exceptions raised when a dependency is checked and fails.


class UnsupportedPlatformError(GeoEcoError):
    __doc__ = DynamicDocString()


class SoftwareNotInstalledError(GeoEcoError):
    __doc__ = DynamicDocString()


# Classes that represent various types of dependencies.


class Dependency(object):
    __doc__ = DynamicDocString()

    def Initialize(self):
        raise NotImplementedError('Derived classes must override this method.')

    def GetConstraintDescriptionStrings(self):
        return []


class WindowsDependency(Dependency):
    __doc__ = DynamicDocString()

    def __init__(self, minimumMajorVersion, minimumMinorVersion=None, minimumServicePack=None, minimumBuild=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        self.SetVersion(minimumMajorVersion, minimumMinorVersion, minimumServicePack, minimumBuild)

    def SetVersion(self, minimumMajorVersion, minimumMinorVersion=None, minimumServicePack=None, minimumBuild=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        if minimumMinorVersion is None:
            minimumMinorVersion = 0

        self._MinimumMajorVersion = minimumMajorVersion
        self._MinimumMinorVersion = minimumMinorVersion
        self._MinimumServicePack = minimumServicePack
        self._MinimumBuild = minimumBuild

    def _GetMinimumMajorVersion(self):
        return self._MinimumMajorVersion
    
    MinimumMajorVersion = property(_GetMinimumMajorVersion, doc=DynamicDocString())

    def _GetMinimumMinorVersion(self):
        return self._MinimumMinorVersion
    
    MinimumMinorVersion = property(_GetMinimumMinorVersion, doc=DynamicDocString())

    def _GetMinimumServicePack(self):
        return self._MinimumServicePack
    
    MinimumServicePack = property(_GetMinimumServicePack, doc=DynamicDocString())

    def _GetMinimumBuild(self):
        return self._MinimumBuild
    
    MinimumBuild = property(_GetMinimumBuild, doc=DynamicDocString())

    def Initialize(self):
        from .Logging import Logger
        Logger.Debug(_('Checking platform dependency: %s or later.') % self.GetProductNameFromVersionNumbers(self.MinimumMajorVersion, self.MinimumMinorVersion, self.MinimumServicePack, self.MinimumBuild))
        if sys.platform.lower() == 'win32':
            (major, minor, servicePack, build) = self.GetInstalledVersion()
            if self.MinimumBuild is not None and build is not None and self.MinimumBuild > build or \
               self.MinimumMajorVersion > major or \
               self.MinimumMajorVersion == major and self.MinimumMinorVersion > minor or \
               self.MinimumMajorVersion == major and self.MinimumMinorVersion == minor and self.MinimumServicePack is not None and self.MinimumServicePack > servicePack:
                Logger.RaiseException(UnsupportedPlatformError(_('This tool can only execute on a computer running %(required)s or a later version. Python reports that %(installed)s is installed. Please upgrade the operating system.') % {'required' : self.GetProductNameFromVersionNumbers(self.MinimumMajorVersion, self.MinimumMinorVersion, self.MinimumServicePack, self.MinimumBuild), 'installed' : self.GetProductNameFromVersionNumbers(major, minor, servicePack, build)}))
        else:
            Logger.RaiseException(UnsupportedPlatformError(_('This tool can only execute on a computer running the Microsoft Windows operating system. Python reports that this computer is running the \"%s\" operating system.') % platform.system()))

    _MajorVersion = None
    _MinorVersion = None
    _ServicePack = None
    _Build = None

    def GetConstraintDescriptionStrings(self):
        return [self.GetProductNameFromVersionNumbers(self.MinimumMajorVersion, self.MinimumMinorVersion, self.MinimumServicePack, self.MinimumBuild) + ' or later']

    @classmethod
    def GetInstalledVersion(cls):
        if WindowsDependency._MajorVersion is not None:
            return (WindowsDependency._MajorVersion, WindowsDependency._MinorVersion, WindowsDependency._ServicePack, WindowsDependency._Build)

        (WindowsDependency._MajorVersion, WindowsDependency._MinorVersion, WindowsDependency._Build, plat, text) = sys.getwindowsversion()
        if text is None:
            WindowsDependency._ServicePack = 0
        else:
            try:
                WindowsDependency._ServicePack = int(text.strip('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz \t\r\n.'))
            except:
                WindowsDependency._ServicePack = 0

        from .Logging import Logger
        Logger.Debug(_('%s is installed.') % cls.GetProductNameFromVersionNumbers(WindowsDependency._MajorVersion, WindowsDependency._MinorVersion, WindowsDependency._ServicePack, WindowsDependency._Build))

        return (WindowsDependency._MajorVersion, WindowsDependency._MinorVersion, WindowsDependency._ServicePack, WindowsDependency._Build)

    @classmethod
    def GetProductNameFromVersionNumbers(cls, majorVersion, minorVersion=None, servicePack=None, build=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # To determine the operating system name, if there is a build number,
        # just use that. See
        # https://en.wikipedia.org/wiki/List_of_Microsoft_Windows_versions

        osName = None

        if build is not None:
            if build >= 2600 and build < 3790:
                osName = _('Microsoft Windows XP')
            elif build == 3790:
                osName = _('Microsoft Windows XP Professional x64 or Windows Server 2003')
            elif build == 6002:
                osName = _('Microsoft Windows Vista')
            elif build == 6003:
                osName = _('Microsoft Windows Server 2008')
            elif build == 7601:
                osName = _('Microsoft Windows 7 or Windows Server 2008 R2')
            elif build == 9200:
                osName = _('Microsoft Windows 8 or Windows Server 2012')
            elif build == 9600:
                osName = _('Microsoft Windows 8.1 or Windows Server 2012 R2')
            elif build == 10240:
                osName = _('Microsoft Windows 10 version 1507')
            elif build == 10586:
                osName = _('Microsoft Windows 10 version 1511')
            elif build == 14393:
                osName = _('Microsoft Windows 10 version 1607 or Windows Server 2016')
            elif build == 15063:
                osName = _('Microsoft Windows 10 version 1703')
            elif build == 16299:
                osName = _('Microsoft Windows 10 version 1709 or Windows Server version 1709')
            elif build == 17134:
                osName = _('Microsoft Windows 10 version 1803 or Windows Server version 1803')
            elif build == 17763:
                osName = _('Microsoft Windows 10 version 1809 or Windows Server 2019')
            elif build == 18362:
                osName = _('Microsoft Windows 10 version 1903 or Windows Server version 1903')
            elif build == 18363:
                osName = _('Microsoft Windows 10 version 1909 or Windows Server version 1909')
            elif build == 19041:
                osName = _('Microsoft Windows 10 version 2004 or Windows Server version 2004')
            elif build == 19042:
                osName = _('Microsoft Windows 10 version 20H2 or Windows Server version 20H2')
            elif build == 19043:
                osName = _('Microsoft Windows 10 version 21H1')
            elif build == 19044:
                osName = _('Microsoft Windows 10 version 21H2')
            elif build == 20348:
                osName = _('Microsoft Windows Server 2022')
            elif build == 22000:
                osName = _('Microsoft Windows 11 version 21H2')
            elif build == 22000:
                osName = _('Microsoft Windows 11 version 21H2')
            elif build == 22621:
                osName = _('Microsoft Windows 11 version 22H2')
            elif build == 22631:
                osName = _('Microsoft Windows 11 version 23H2')

        # If that didn't work, try the version numbers

        if osName is None:
            if majorVersion == 5:
                if minorVersion is None or minorVersion == 0:
                    osName = _('Microsoft Windows 2000')
                elif minorVersion == 1:
                    osName = _('Microsoft Windows XP')
                else:
                    osName = _('Microsoft Windows Server 2003')
            elif majorVersion == 6:
                if minorVersion is None or minorVersion == 0:
                    osName = _('Microsoft Windows Vista or Server 2008')
                elif minorVersion == 1:
                    osName = _('Microsoft Windows 7 or Server 2008 R2')

        # If that didn't work, just construct a number.

        if osName is None:
            if minorVersion is None:
                minorVersion = 0
            if build is not None:
                osName = _('Microsoft Windows version %i.%i build %i') % (majorVersion, minorVersion, build)
            else:
                osName = _('Microsoft Windows version %i.%i') % (majorVersion, minorVersion)

        # Append the service pack number, if provided.

        if servicePack is not None and servicePack > 0:
            osName = _('%s Service Pack %i') % (osName, servicePack)

        return osName

            
class PythonDependency(Dependency):
    __doc__ = DynamicDocString()

    def __init__(self, minimumMajorVersion, minimumMinorVersion=None, minimumPatchVersion=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        self.SetVersion(minimumMajorVersion, minimumMinorVersion, minimumPatchVersion)

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

    def Initialize(self):
        from .Logging import Logger
        Logger.Debug(_('Checking software dependency: Python version %i.%i.%i or later.') % (self.MinimumMajorVersion, self.MinimumMinorVersion, self.MinimumPatchVersion))
        (major, minor, patch) = self.GetInstalledVersion()
        if self.MinimumMajorVersion > major or self.MinimumMajorVersion == major and self.MinimumMinorVersion > minor or self.MinimumMajorVersion == major and self.MinimumMinorVersion == minor and self.MinimumPatchVersion > patch:
            Logger.RaiseException(SoftwareNotInstalledError(_('This tool requires Python %i.%i.%i or a later version, but version %i.%i.%i is currently running. Please ensure the required version (or newer) is installed. You may download Python from http://www.python.org/. Also ensure that the MGET package for that version of Python is installed (if you reinstall Python, you have to reinstall MGET). Finally, ensure the operating system is configured to invoke the required version of Python when it interprets Python scripts, rather than an older version of Python. On Windows, you must configure a "file association" that associates the newer version of Python with .py files.') % (self.MinimumMajorVersion, self.MinimumMinorVersion, self.MinimumPatchVersion, major, minor, patch)))

    _MajorVersion = None
    _MinorVersion = None
    _PatchVersion = None

    def GetConstraintDescriptionStrings(self):
        return ['Python %i.%i.%i or later' % (self._MinimumMajorVersion, self._MinimumMinorVersion, self._MinimumPatchVersion)]

    @classmethod
    def GetInstalledVersion(cls):
        if PythonDependency._MajorVersion is not None:
            return (PythonDependency._MajorVersion, PythonDependency._MinorVersion, PythonDependency._PatchVersion)

        v = platform.python_version_tuple()
        PythonDependency._MajorVersion = cls._ParseVersionNumber(v[0])
        PythonDependency._MinorVersion = cls._ParseVersionNumber(v[1])
        PythonDependency._PatchVersion = cls._ParseVersionNumber(v[2])

        from .Logging import Logger
        Logger.Debug(_('Python %i.%i.%i is running.') % (PythonDependency._MajorVersion, PythonDependency._MinorVersion, PythonDependency._PatchVersion))

        return (PythonDependency._MajorVersion, PythonDependency._MinorVersion, PythonDependency._PatchVersion)

    @classmethod
    def _ParseVersionNumber(cls, s):
        assert isinstance(s, (int, str))
        if isinstance(s, int):
            return s
        s = s[:len(s) - len(s.lstrip('0123456789'))]
        if len(s) <= 0:
            return 0
        return int(s)


class PythonModuleDependency(Dependency):
    __doc__ = DynamicDocString()

    def __init__(self, importName, displayName=None, cheeseShopName=None, alternateURL=None, additionalMessage=None, logStdout=False):
        self.__doc__.Obj.ValidateMethodInvocation()

        self.ImportName = importName
        self.DisplayName = displayName
        self.CheeseShopName = cheeseShopName
        self.AlternateURL = alternateURL
        self.AdditionalMessage = additionalMessage
        self.LogStdout = logStdout

    _InstalledModules = {}        

    def Initialize(self):
        # If we already know that it is installed, return immediately.

        if self.ImportName in PythonModuleDependency._InstalledModules:
            return

        from .Logging import Logger
        Logger.Debug(_('Checking software dependency: Python module: %s') % self.ImportName)

        # If requested, start capturing stdout so we can log any messages that
        # are printed when we try to import the module. At the time this code
        # was written, I only knew of one module (rpy) that printed messages to
        # stdout during module importation.

        if self.LogStdout:
            oldStdout = sys.stdout
            sys.stdout = io.StringIO()

        # Import the module and, if requested, log any messages that are printed
        # to stdout.
        
        try:
            try:
                __import__(self.ImportName)
            finally:
                if self.LogStdout:
                    messages = []
                    try:
                        messages = sys.stdout.getvalue().split('\n')
                    except:
                        pass
                    sys.stdout = oldStdout
                    try:
                        for message in messages:
                            if len(message.strip()) > 0:
                                Logger.Debug(_('Python %(module)s module: %(message)s') % {'module' : self.ImportName, 'message' : message.strip()})
                    except:
                        pass
        except Exception as e:
            if self.DisplayName is None:
                message = _('This tool requires the Python %s module. Please verify that it is properly installed for the running version of Python (%s.%s). If it is Python-version-specific, ensure you installed the version of it for this Python version.') % (self.ImportName, str(platform.python_version_tuple()[0]), str(platform.python_version_tuple()[1]))
            else:
                message = _('This tool requires the %s. Please verify that it is properly installed for the running version of Python (%s.%s). If it is Python-version-specific, ensure you installed the version of it for this Python version.') % (self.DisplayName, str(platform.python_version_tuple()[0]), str(platform.python_version_tuple()[1]))
            if self.CheeseShopName is not None and self.AlternateURL is None:
                message = _('%s It may be available at http://www.python.org/pypi/%s.') % (message, self.CheeseShopName)
            elif self.CheeseShopName is None and self.AlternateURL is not None:
                message = _('%s It may be available at %s.') % (message, self.AlternateURL)
            elif self.CheeseShopName is not None and self.AlternateURL is not None:
                message = _('%s It may be available at http://www.python.org/pypi/%s or %s.') % (message, self.CheeseShopName, self.AlternateURL)
            if self.AdditionalMessage is not None:
                message = _('%s %s.') % (message, self.AdditionalMessage)
            message = _('%s Debugging information: the Python statement "__import__(\'%s\')" raised %s: %s"') % (message, self.ImportName, e.__class__.__name__, str(e))
            Logger.RaiseException(SoftwareNotInstalledError(message))

        Logger.Debug(_('Imported Python module %s successfully.') % self.ImportName)
        PythonModuleDependency._InstalledModules[self.ImportName] = True            

    def GetConstraintDescriptionStrings(self):
        if self.DisplayName is not None:
            return [self.DisplayName]
        return ['Python %s module' % self.ImportName]


###############################################################################
# Metadata: module
###############################################################################

from .Metadata import *
from .Types import *

AddModuleMetadata(shortDescription=_('Classes for declaring and checking dependencies on other software in :class:`~GeoEco.Metadata.MethodMetadata` and :class:`~GeoEco.Metadata.ArgumentMetadata`.'))

###############################################################################
# Metadata: UnsupportedPlatformError class
###############################################################################

AddClassMetadata(UnsupportedPlatformError,
    shortDescription=_('An exception indicating the current operating system or platform is not supported.'))

###############################################################################
# Metadata: SoftwareNotInstalledError class
###############################################################################

AddClassMetadata(SoftwareNotInstalledError,
    shortDescription=_('An exception indicating the that required software is not installed.'))

###############################################################################
# Metadata: Dependency class
###############################################################################

AddClassMetadata(Dependency,
    shortDescription=_('Base class for a metadata object representing a software dependency.'))

# Public method: Initialize

AddMethodMetadata(Dependency.Initialize,
    shortDescription=_('Check that the depended-upon software is available and initialize it for use.'),
    longDescription=_(
"""Derived classes must implement this method. The base class raises
:exc:`NotImplementedError`."""))

# Public method: GetConstraintDescriptionStrings

AddMethodMetadata(Dependency.GetConstraintDescriptionStrings,
    shortDescription=_('Returns the names of the software identified by this dependency, suitable to display to the user.'),
    longDescription=_(
"""The names should be as short as possible but complete. When documentation
is generated for a GeoEco method that has dependencies, the dependencies'
constraint description strings will be shown as a comma-separated list. If no
such strings should be displayed for a dependency, an empty list should be
returned.

The derived class should override this method. The base class returns an empty
list."""))

AddResultMetadata(Dependency.GetConstraintDescriptionStrings, 'descriptionStrings',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1)),
    description=_('List of software names, or an empty list if none should be displayed for this dependency.'))

###############################################################################
# Metadata: WindowsDependency class
###############################################################################

AddClassMetadata(WindowsDependency,
    shortDescription=_('A :class:`Dependency` that checks that the operating system is Microsoft Windows, and its version.'))

# Properties

AddPropertyMetadata(WindowsDependency.MinimumMajorVersion,
    typeMetadata=IntegerTypeMetadata(minValue=5),
    shortDescription=_('Minimum major version number (the first number reported by the ``ver`` command executed from the Windows Command Prompt) of Microsoft Windows that must be installed.'))

AddPropertyMetadata(WindowsDependency.MinimumMinorVersion,
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    shortDescription=_('Minimum minor version number (the second number reported by the ``ver`` command executed from the Windows Command Prompt) of Microsoft Windows that must be installed, or :py:data:`None` to indicate the minor version number should not be checked.'))

AddPropertyMetadata(WindowsDependency.MinimumServicePack,
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    shortDescription=_('Minimum Windows service pack number that must be installed, or :py:data:`None` to indicate the service pack number should not be checked.'))

AddPropertyMetadata(WindowsDependency.MinimumBuild,
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    shortDescription=_('Minimum Windows build number that must be installed, or :py:data:`None` to indicate the build number should not be checked. Starting with Windows 10, the build number should always be given.'))

# Constructor

AddMethodMetadata(WindowsDependency.__init__,
    shortDescription=_('Constructs a new %s instance.') % WindowsDependency.__name__)

AddArgumentMetadata(WindowsDependency.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=WindowsDependency),
    description=_(':class:`%s` instance.') % WindowsDependency.__name__)

AddArgumentMetadata(WindowsDependency.__init__, 'minimumMajorVersion',
    typeMetadata=WindowsDependency.MinimumMajorVersion.__doc__.Obj.Type,
    description=WindowsDependency.MinimumMajorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindowsDependency.__init__, 'minimumMinorVersion',
    typeMetadata=WindowsDependency.MinimumMinorVersion.__doc__.Obj.Type,
    description=WindowsDependency.MinimumMinorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindowsDependency.__init__, 'minimumServicePack',
    typeMetadata=WindowsDependency.MinimumServicePack.__doc__.Obj.Type,
    description=WindowsDependency.MinimumServicePack.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindowsDependency.__init__, 'minimumBuild',
    typeMetadata=WindowsDependency.MinimumBuild.__doc__.Obj.Type,
    description=WindowsDependency.MinimumBuild.__doc__.Obj.ShortDescription)

AddResultMetadata(WindowsDependency.__init__, 'dependency',
    typeMetadata=ClassInstanceTypeMetadata(cls=WindowsDependency),
    description=_('New :class:`%s` instance.') % WindowsDependency.__name__)

# Public method: SetVersion

AddMethodMetadata(WindowsDependency.SetVersion,
    shortDescription=_('Sets the minimum version number of Microsoft Windows that is required.'))

AddArgumentMetadata(WindowsDependency.SetVersion, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=WindowsDependency),
    description=_(':class:`%s` instance.') % WindowsDependency.__name__)

AddArgumentMetadata(WindowsDependency.SetVersion, 'minimumMajorVersion',
    typeMetadata=WindowsDependency.MinimumMajorVersion.__doc__.Obj.Type,
    description=WindowsDependency.MinimumMajorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindowsDependency.SetVersion, 'minimumMinorVersion',
    typeMetadata=WindowsDependency.MinimumMinorVersion.__doc__.Obj.Type,
    description=WindowsDependency.MinimumMinorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindowsDependency.SetVersion, 'minimumServicePack',
    typeMetadata=WindowsDependency.MinimumServicePack.__doc__.Obj.Type,
    description=WindowsDependency.MinimumServicePack.__doc__.Obj.ShortDescription)

AddArgumentMetadata(WindowsDependency.SetVersion, 'minimumBuild',
    typeMetadata=WindowsDependency.MinimumBuild.__doc__.Obj.Type,
    description=WindowsDependency.MinimumBuild.__doc__.Obj.ShortDescription)

# Public method: Initialize

AddMethodMetadata(WindowsDependency.Initialize,
    shortDescription=_('Check that the operating system is Microsoft Windows and that its version meets or exceeds what we require.'),
    longDescription=_(
"""Raises:
    :exc:`UnsupportedPlatformError`: The operating system is not Microsoft
        Windows, or its version does not meet the minimum specified for this
        :class:`WindowsDependency`.
"""))

# Public method: GetInstalledVersion

AddMethodMetadata(WindowsDependency.GetInstalledVersion,
    shortDescription=_('Returns the major version, minor version, service pack number, and build number of Microsoft Windows, as obtained from Python\'s :py:func:`sys.getwindowsversion`.'))

AddArgumentMetadata(WindowsDependency.GetInstalledVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=WindowsDependency),
    description=_(':class:`%s` or an instance of it.') % WindowsDependency.__name__)

AddResultMetadata(WindowsDependency.GetInstalledVersion, 'versionTuple',
    typeMetadata=TupleTypeMetadata(elementType=IntegerTypeMetadata(canBeNone=True), minLength=4, maxLength=4),
    description=_('Tuple of the form ``(majorVersion, minorVersion, servicePack, build)``.'))

# Public method: GetProductNameFromVersionNumbers

AddMethodMetadata(WindowsDependency.GetProductNameFromVersionNumbers,
    shortDescription=_('Given version numbers, returns a descriptive name of the corresponding Microsoft Windows product.'))

AddArgumentMetadata(WindowsDependency.GetProductNameFromVersionNumbers, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=WindowsDependency),
    description=_(':class:`%s` or an instance of it.') % WindowsDependency.__name__)

AddArgumentMetadata(WindowsDependency.GetProductNameFromVersionNumbers, 'majorVersion',
    typeMetadata=IntegerTypeMetadata(minValue=5),
    description=_('Windows major version number (the first number reported by the ``ver`` command executed from the Windows Command Prompt).'))

AddArgumentMetadata(WindowsDependency.GetProductNameFromVersionNumbers, 'minorVersion',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    description=_('Windows minor version number (the second number reported by the ``ver`` command executed from the Windows Command Prompt). :py:data:`None` is interpreted as 0.'))

AddArgumentMetadata(WindowsDependency.GetProductNameFromVersionNumbers, 'servicePack',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    description=_('Windows service pack number, or :py:data:`None` to indicate no service pack.'))

AddArgumentMetadata(WindowsDependency.GetProductNameFromVersionNumbers, 'build',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    description=_('Windows service build number, or :py:data:`None` if the build number is not known. Starting with Windows 10, the build number should always be provided.'))

AddResultMetadata(WindowsDependency.GetProductNameFromVersionNumbers, 'productName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Descriptive name of the Microsoft Windows product for the given version numbers.'))

###############################################################################
# Metadata: PythonDependency class
###############################################################################

AddClassMetadata(PythonDependency,
    shortDescription=_('A :class:`Dependency` that checks the version of Python that is running.'))

# Properties

AddPropertyMetadata(PythonDependency.MinimumMajorVersion,
    typeMetadata=IntegerTypeMetadata(minValue=3),
    shortDescription=_('Minimum major version number of Python that must be installed.'))

AddPropertyMetadata(PythonDependency.MinimumMinorVersion,
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    shortDescription=_('Minimum minor version number of Python that must be installed, or :py:data:`None` to indicate the minor version number should not be checked.'))

AddPropertyMetadata(PythonDependency.MinimumPatchVersion,
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    shortDescription=_('Minimum patch version number of Python that must be installed, or :py:data:`None` to indicate the patch version number should not be checked.'))

# Constructor

AddMethodMetadata(PythonDependency.__init__,
    shortDescription=_('Constructs a new %s instance.') % PythonDependency.__name__)

AddArgumentMetadata(PythonDependency.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=PythonDependency),
    description=_(':class:`%s` instance.') % PythonDependency.__name__)

AddArgumentMetadata(PythonDependency.__init__, 'minimumMajorVersion',
    typeMetadata=PythonDependency.MinimumMajorVersion.__doc__.Obj.Type,
    description=PythonDependency.MinimumMajorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(PythonDependency.__init__, 'minimumMinorVersion',
    typeMetadata=PythonDependency.MinimumMinorVersion.__doc__.Obj.Type,
    description=PythonDependency.MinimumMinorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(PythonDependency.__init__, 'minimumPatchVersion',
    typeMetadata=PythonDependency.MinimumPatchVersion.__doc__.Obj.Type,
    description=PythonDependency.MinimumPatchVersion.__doc__.Obj.ShortDescription)

AddResultMetadata(PythonDependency.__init__, 'dependency',
    typeMetadata=ClassInstanceTypeMetadata(cls=PythonDependency),
    description=_('New :class:`%s` instance.') % PythonDependency.__name__)

# Public method: SetVersion

AddMethodMetadata(PythonDependency.SetVersion,
    shortDescription=_('Sets the minimum version number of Python that is required.'))

AddArgumentMetadata(PythonDependency.SetVersion, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=PythonDependency),
    description=_(':class:`%s` instance.') % PythonDependency.__name__)

AddArgumentMetadata(PythonDependency.SetVersion, 'minimumMajorVersion',
    typeMetadata=PythonDependency.MinimumMajorVersion.__doc__.Obj.Type,
    description=PythonDependency.MinimumMajorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(PythonDependency.SetVersion, 'minimumMinorVersion',
    typeMetadata=PythonDependency.MinimumMinorVersion.__doc__.Obj.Type,
    description=PythonDependency.MinimumMinorVersion.__doc__.Obj.ShortDescription)

AddArgumentMetadata(PythonDependency.SetVersion, 'minimumPatchVersion',
    typeMetadata=PythonDependency.MinimumPatchVersion.__doc__.Obj.Type,
    description=PythonDependency.MinimumPatchVersion.__doc__.Obj.ShortDescription)

# Public method: Initialize

AddMethodMetadata(PythonDependency.Initialize,
    shortDescription=_('Check that the version of Python meets or exceeds what we require.'),
    longDescription=_(
"""Raises:
    :exc:`SoftwareNotInstalledError`: The version of Python that is installed
        does not meet the minimum specified for this
        :class:`PythonDependency`. """))

# Public method: GetInstalledVersion

AddMethodMetadata(PythonDependency.GetInstalledVersion,
    shortDescription=_('Returns the major, minor, and patch version numbers of Python.'))

AddArgumentMetadata(PythonDependency.GetInstalledVersion, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=PythonDependency),
    description=_(':class:`%s` or an instance of it.') % PythonDependency.__name__)

AddResultMetadata(PythonDependency.GetInstalledVersion, 'versionTuple',
    typeMetadata=TupleTypeMetadata(elementType=IntegerTypeMetadata(canBeNone=True), minLength=3, maxLength=3),
    description=_('Tuple of the form ``(majorVersion, minorVersion, patchVersion)``.'))

###############################################################################
# Metadata: PythonModuleDependency class
###############################################################################

AddClassMetadata(PythonModuleDependency,
    shortDescription=_('A :class:`Dependency` that checks that a third-party Python module can be imported.'))

# Constructor

AddMethodMetadata(PythonModuleDependency.__init__,
    shortDescription=_('Constructs a new %s instance.') % PythonModuleDependency.__name__)

AddArgumentMetadata(PythonModuleDependency.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=PythonModuleDependency),
    description=_(':class:`%s` instance.') % PythonModuleDependency.__name__)

AddArgumentMetadata(PythonModuleDependency.__init__, 'importName',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    description=_('Name of the module, as it is imported, e.g. ``numpy``.'))

AddArgumentMetadata(PythonModuleDependency.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_('Name of the module to display in messages about it, e.g. ``Python NumPy library``. If not provided, ``Python importName module`` will be used, e.g. ``Python numpy module``.'))

AddArgumentMetadata(PythonModuleDependency.__init__, 'cheeseShopName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_('Name of the distribution package that appears on the `Python Package Index <https://www.python.org/pypi>`_.'))

AddArgumentMetadata(PythonModuleDependency.__init__, 'alternateURL',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_('Alternative URL where the module may be found found.'))

AddArgumentMetadata(PythonModuleDependency.__init__, 'additionalMessage',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1),
    description=_('Additional message to prepend to the debug message used to report a failure to import this module.'))

AddArgumentMetadata(PythonModuleDependency.__init__, 'logStdout',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, messages printed to stdout when the module is imported will be logged to the GeoEco logging channel as debug messages.'))

AddResultMetadata(PythonModuleDependency.__init__, 'dependency',
    typeMetadata=ClassInstanceTypeMetadata(cls=PythonModuleDependency),
    description=_('New :class:`%s` instance.') % PythonModuleDependency.__name__)

# Public method: Initialize

AddMethodMetadata(PythonModuleDependency.Initialize,
    shortDescription=_('Check that the given Python module can be imported.'),
    longDescription=_(
"""Raises:
    :exc:`SoftwareNotInstalledError`: The Python module specified by this
        :class:`PythonDependency` could not be imported, which usually implies
        that the module is not installed. """))


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['UnsupportedPlatformError',
           'SoftwareNotInstalledError',
           'Dependency',
           'WindowsDependency',
           'PythonDependency',
           'PythonModuleDependency']
