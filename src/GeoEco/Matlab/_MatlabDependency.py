# Matlab/_MatlabDependency.py - Defines MatlabDependency, which checks for the
# presence of MATLAB or the MATLAB Runtime.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import logging
import os
import sys

from ..Dependencies import Dependency, PythonModuleDependency, SoftwareNotInstalledError, UnsupportedPlatformError
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _


class MatlabDependency(Dependency):
    __doc__ = DynamicDocString()

    _Initialized = False

    def GetConstraintDescriptionStrings(self):
        return [_('MATLAB Runtime R2024b (which can be freely downloaded from https://www.mathworks.com/products/compiler/matlab-runtime.html) or the full version of MATLAB R2024b')]

    def Initialize(self):

        # Return successfully if we have already been initalized.

        if MatlabDependency._Initialized:
            return

        # Check for MATLAB but do not set the path in preparation for running
        # it. That will be done by the MatlabFunctions class, when the caller
        # actually wants to call some functions.

        self.FindMatlab()

        # If we got to here without an exception, we found MATLAB.

        MatlabDependency._Initialized = True

    @classmethod
    def FindMatlab(cls, setPath=False, loggingQueue=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # We require numpy. Make sure it is available.

        d = PythonModuleDependency('numpy', cheeseShopName='numpy')
        d.Initialize()

        # Define a helper function for logging debug messages.

        def _LogDebug(fmt, *args):
            MatlabDependency._Log(logging.DEBUG, fmt % args, loggingQueue)

        # Check that the MATLAB Runtime has been installed and configured. If
        # we're running on Linux, check LD_LIBRARY_PATH for the needed .so
        # files.

        if sys.platform == 'linux':
            fileToFind = 'libmwmclmcrrt.so.24.2'
            defaultDirs = ['/usr/local/MATLAB/R2024b', '/usr/local/MATLAB/MATLAB_Runtime/R2024b']

            _LogDebug('MATLAB R2024b or MATLAB Runtime R2024b is required. Searching for %s in LD_LIBRARY_PATH.', fileToFind)

            oldLdLibraryPath = os.environ.get('LD_LIBRARY_PATH', '')
            if len(oldLdLibraryPath.strip()) > 0:
                _LogDebug('LD_LIBRARY_PATH = %s', oldLdLibraryPath)
                for dir in oldLdLibraryPath.split(':'):
                    if os.path.isfile(os.path.join(dir, fileToFind)):
                        _LogDebug('Found %s. MATLAB R2024b or MATLAB Runtime R2024b appears to be installed.' % os.path.join(dir, fileToFind))
                        return None

            _LogDebug('Did not find %s in LD_LIBRARY_PATH.' % fileToFind)
            for defaultDir in defaultDirs:
                defaultFile = os.path.join(defaultDir, 'runtime', 'glnxa64', fileToFind)
                if os.path.isfile(defaultFile):
                    _LogDebug('%s exists. MATLAB R2024b or MATLAB Runtime R2024b appears to be installed.' % defaultFile)

                    # We found it but LD_LIBRARY_PATH was not set. Set it
                    # if requested by the caller.

                    if setPath:
                        ldLibraryPath = [oldLdLibraryPath] if len(oldLdLibraryPath) > 0 else []
                        ldLibraryPath.append(defaultDir + '/runtime/glnxa64')
                        ldLibraryPath.append(defaultDir + '/bin/glnxa64')
                        ldLibraryPath.append(defaultDir + '/sys/os/glnxa64')
                        ldLibraryPath.append(defaultDir + '/extern/bin/glnxa64')
                        ldLibraryPath = ':'.join(ldLibraryPath)

                        _LogDebug('Setting LD_LIBRARY_PATH = %s' % ldLibraryPath)
                        os.environ['LD_LIBRARY_PATH'] = ldLibraryPath
                        return oldLdLibraryPath

                    return None 
                else:
                    _LogDebug('%s does not exist.' % defaultFile)

        # On Windows, we check for the presence of one of the required MATLAB
        # DLLs in the PATH.

        elif sys.platform == 'win32':
            fileToFind = 'mclmcrrt24_2.dll'
            defaultDirs = [os.path.join(os.environ.get('PROGRAMFILES', r'C:\Program Files'), r'MATLAB\MATLAB Runtime\R2024b\runtime\win64')]

            _LogDebug('MATLAB is required. Searching for %s in PATH.', fileToFind)

            oldPath = os.environ.get('PATH', '')
            if len(oldPath.strip()) > 0:
                _LogDebug('PATH = %s', oldPath)
                for dir in oldPath.split(';'):
                    if os.path.isfile(os.path.join(dir, fileToFind)):
                        _LogDebug('Found %s. MATLAB R2024b or MATLAB Runtime R2024b appears to be installed.' % os.path.join(dir, fileToFind))
                        return None

            _LogDebug('Did not find %s in PATH.' % fileToFind)
            for defaultDir in defaultDirs:
                defaultFile = os.path.join(defaultDir, fileToFind)
                if os.path.isfile(defaultFile):
                    _LogDebug('%s exists. MATLAB R2024b or MATLAB Runtime R2024b appears to be installed.' % defaultFile)

                    # We found it but its directory was not in the PATH. Set
                    # it if requested by the caller.

                    # We found it but its directory was not in the PATH.
                    # The MATLAB Runtime installer is supposed to do
                    # this, so there could be a problem with MATLAB.
                    # Nevertheless, add it to the PATH and try it.

                    if setPath:
                        newPath = oldPath + ';' + defaultDir
                        _LogDebug('Setting PATH = %s' % newPath)
                        os.environ['PATH'] = newPath
                        return oldPath

                    return None 
                else:
                    _LogDebug('%s does not exist.' % defaultFile)

        # Otherwise (this is not Linux or Windows), we're on an unsupported
        # plaform and need to fail.

        else:
            raise UnsupportedPlatformError(_('This tool rquires MATLAB R2024b or the MATLAB Runtime R2024b, support for accessing MATLAB when running on the %r platform has not been implemented yet. Please contact the developer of this tool for assistance.') % sys.platform)

        # If we fell through to here, we did not find MATLAB.

        raise SoftwareNotInstalledError(_('This tool requires that MATLAB R2024b or the MATLAB Runtime R2024b be installed. The MATLAB Runtime is free and may be downloaded from https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html. Please follow the installation instructions carefully. Version R2024b must be used; other versions will not work. MATLAB Runtime allows multiple versions can be installed at the same time.'))

    @staticmethod
    def _Log(level, msg, loggingQueue):

        # If loggingQueue was provided, write the message to it; our parent
        # process will pull it out and log it there. Otherwise just call the
        # logging module directly, so it is logged in our own process.

        if loggingQueue is not None:
            try:
                loggingQueue.put(('LOG', level, msg), timeout=10.)
            except:
                pass
        else:
            logging.getLogger('GeoEco').log(level, msg)


#################################################################################
# This module is not meant to be imported directly. Import GeoEco.Matlab instead.
#################################################################################

__all__ = []
