import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys

import setuptools
import setuptools.command.build
import setuptools.command.sdist


class BuildMatlabFunctions(setuptools.Command):
    """sdist SubCommand for building MATLAB .m files in GeoEco.Matlab._Matlab as a Python package.

    This SubCommand creates the files __init__.py, _Matlab.ctf, and
    MatlabFunctions.txt in src/GeoEco/Matlab/_Matlab from the .m files there
    using the MATLAB Compiler. A full version of MATLAB R2024b must be
    installed. Even though the three files are generated programmatically,
    they are considered source files, not build outputs, and thus are updated
    directly in the source tree by this SubCommand as part of the setuputils
    sdist command. The sdist command then copies the three files into the
    source tarball as if they were regular static files, and they may be
    subsequently be incorporated into built wheels, etc.

    The three files are platform-independent, so it does not matter what
    platform they are built upon. They are maintained in the source repo like
    static files. This SubCommand first compares the .m files to copies kept
    in the _Matlab.ctf file to see whether any of them have changed. If not,
    then the MATLAB Compiler is not invoked and the files are not rebuilt.
    This allows setup.py to be run to successful on a machine without MATLAB
    installed, so long as the .m files are not changed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matlab_path = None
        self.m_files = None
        self.matlab_package_dir = None

    def initialize_options(self):
        """Set or (reset) all options/attributes/caches used by the command to their default values."""
        self.matlab_path = None
        self.m_files = None
        self.matlab_package_dir = None

    def finalize_options(self):
        """Set final values for all options/attributes used by the command."""

        # In order to execute this script, you must have a full installation
        # of MATLABV. First, we need the path to the MATLAB executable. If it
        # has not set already, set it to the default path for the platform.

        if self.matlab_path is None:
            if sys.platform == 'linux':
                self.matlab_path = '/usr/local/MATLAB/R2024b/bin/matlab'
            else:
                self.matlab_path = NotImplementedError(f'This script does not currently support the {sys.platform} platform (but adding support would probably be easy).')

        # Determine the directory that contains the .m files and that will
        # receive the __init__.py and the .ctf file that results from
        # compiling them.

        if self.matlab_package_dir is None:
            self.matlab_package_dir = os.path.join(os.path.dirname(__file__), 'src', 'GeoEco', 'Matlab', '_Matlab')

        # Enumerate the .m files that we will compile.

        if self.m_files is None:
            self.m_files = glob.glob(os.path.join(self.matlab_package_dir, '*.m'))

    def ensure_finalized(self):
        """This function is undocumented by setuputils, but apparently we have to support it."""
        self.finalize_options()

    def get_output_mapping(self):
        """Return a mapping between destination files as they would be produced by the build (dict keys) into the respective existing (source) files (dict values)."""
        return {}

    def get_outputs(self):
        """Return a list of files intended for distribution as they would have been produced by the build."""
        return []

    def get_source_files(self):
        """Return a list of all files that are used by the command to create the expected outputs."""

        # Return a list of relative paths to the .m files, __init__.py, and
        # _Matlab.ctf, and MatlabFunctions.txt.

        if self.matlab_package_dir is None:
            self.finalize_options()

        rootDir = os.path.dirname(__file__)
        sourceFiles = [os.path.relpath(mFile, rootDir) for mFile in self.m_files]
        sourceFiles.append(os.path.join('src', 'GeoEco', 'Matlab', '_Matlab', '__init__.py'))
        sourceFiles.append(os.path.join('src', 'GeoEco', 'Matlab', '_Matlab', '_Matlab.ctf'))
        sourceFiles.append(os.path.join('src', 'GeoEco', 'Matlab', '_Matlab', 'MatlabFunctions.txt'))

        return sourceFiles

    def run(self):

        # We only want to rebuild the _Matlab.ctf file with the MATLAB
        # Compiler if any of the .m files have changed from when we last
        # rebuilt it. But we can't compare the contents of the current .m
        # files to those in the current _Matlab.ctf because the .ctf encrypts
        # them. To work around this, we store sha256 hashes of each .m file in
        # MatlabFunctions.txt. Read that file into a dictionary mapping file
        # names to hash digests.

        workingDir = os.path.dirname(__file__)
        ctfFile = os.path.join(workingDir, 'src', 'GeoEco', 'Matlab', '_Matlab', '_Matlab.ctf')
        txtFile = os.path.join(workingDir, 'src', 'GeoEco', 'Matlab', '_Matlab', 'MatlabFunctions.txt')

        if not os.path.isfile(ctfFile) or not os.path.isfile(txtFile):
            print(f'{ctfFile} or {os.path.basename(txtFile)} does not exist. They will be built.')
        else:
            with open(txtFile, 'rt') as f:
                oldMFiles = {line.strip().split()[0]: line.strip().split()[-1] for line in f.readlines() if not line.startswith('#')}

            # Create similar dictionary for the current .m files.
            # Replace '\r\n' with '\n', so that the same hash is produced
            # regardless of which line endings are used, to work around git
            # on Linux and Windows having different behavior around line
            # endings.

            newMFiles = {}
            for mFile in self.m_files:
                with open(mFile, "rb") as f:
                    newMFiles[os.path.splitext(os.path.basename(mFile))[0]] = hashlib.sha256(f.read().replace(b'\r', b'')).hexdigest()

            # If the dictionaries match, we do not need to rebuild the .ctf.

            if oldMFiles == newMFiles:
                print(f'All .m files in {os.path.dirname(self.m_files[0])} match those in {ctfFile}. There is no need to rebuild the .ctf file.')
                return

            print(f'The .m files in {os.path.dirname(self.m_files[0])} do not match those in {ctfFile}. The .ctf file will be rebuilt.')

        # We need to rebuild the .ctf file. Fail if MATLAB does not exist.

        if isinstance(self.matlab_path, Exception):
            raise self.matlab_path

        if not os.path.isfile(self.matlab_path):
            raise RuntimeError('Cannot rebuild the MATLAB functions. The MATLAB executable %s does not exist.' % self.matlab_path)

        mFilesStr = '[' + ','.join(['"' + f + '"' for f in self.m_files]) + ']'
        command = f'compiler.build.pythonPackage({mFilesStr}, "PackageName", "GeoEco.Matlab._Matlab", "Verbose", "on")'
        args = [self.matlab_path, '-nodesktop', '-nosplash', '-batch', command]

        # Execute the MATLAB Compiler from the command line.

        print(f'Executing: {" ".join(args)}')

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        result = process.poll()
        if result > 0:
            raise RuntimeError(f'{self.matlab_path} exited with code {result}, indicating failure.')

        print('MATLAB exited successfully.')

        # Copy the two files that we want out of the directory that the MATLAB
        # Compiler created into our source tree.

        for filename in ['__init__.py', '_Matlab.ctf']:
            src = os.path.join(workingDir, '_MatlabpythonPackage', 'GeoEco', 'Matlab', '_Matlab', filename)
            dest = os.path.join(self.matlab_package_dir, filename)
            print(f'Copying {os.path.relpath(src, workingDir)} to {os.path.relpath(dest, workingDir)}.')
            shutil.copy(src, dest)

        # Delete the directory that the MATLAB Compiler created.

        d = os.path.join(workingDir, '_MatlabpythonPackage')
        print(f'Deleting {d}.')
        shutil.rmtree(d)

        # Compute hashes of the .m files. Replace '\r\n' with '\n', so that
        # the same hash is produced regardless of which line endings are
        # used, to work around git on Linux and Windows having different
        # behavior around line endings.

        newMFiles = {}
        for mFile in self.m_files:
            with open(mFile, "rb") as f:
                newMFiles[mFile] = hashlib.sha256(f.read().replace(b'\r', b'')).hexdigest()

        # Write the MatlabFunctions.txt file.

        print(f'Writing {os.path.relpath(txtFile, workingDir)}.')
        with open(txtFile, 'wt') as f:
            f.write('# Do not edit this file. It is produced automatically and used by GeoEco.Matlab.__init__.py at run time.\n')
            for filename in self.m_files:
                f.write(f"{os.path.splitext(os.path.basename(filename))[0]} {newMFiles[filename]}\n")

        print('MATLAB functions built successfully.')


class BuildArcGISToolbox(setuptools.Command):
    """SubCommand for building MGET's ArcGIS Toolbox (.atbx file)."""

    def __init__(self, *args, **kwargs):
        self.build_lib = None
        super().__init__(*args, **kwargs)
        self.build_toolbox = False

    def initialize_options(self):
        """Set or (reset) all options/attributes/caches used by the command to their default values."""
        pass

    def finalize_options(self):
        """Set final values for all options/attributes used by the command."""

        # If it appears that an editable installation is being performed, do
        # not build the ArcGIS toolbox. Doing so will fail when setuptools
        # tries to build an editable wheel.

        self.build_toolbox = 'editable_wheel' not in self.distribution.command_options
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def ensure_finalized(self):
        """This function is undocumented by setuputils, but apparently we have to support it."""
        self.finalize_options()

    def get_output_mapping(self):
        """Return a mapping between destination files as they would be produced by the build (dict keys) into the respective existing (source) files (dict values)."""
        return {}

    def get_outputs(self):
        """Return a list of files intended for distribution as they would have been produced by the build."""
        return []

    def get_source_files(self):
        """Return a list of all files that are used by the command to create the expected outputs."""
        return []

    def run(self):
        if not self.build_toolbox:
            print('Not building the ArcGIS Toolbox; build_toolbox is False.')
            return

        # Add the build_lib directory to sys.path so we can import GeoEco
        # modules. Also set sys.dont_write_bytecode to inhibit writing of
        # __pycache__/*.pyc files. If they are created, setuptools will
        # include them in the built wheel.

        sys.path = [self.build_lib] + sys.path
        oldFlag = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:

            # Import GeoEco.ArcToolbox and generate the .tbx file in the build
            # directory with ArcToolboxGenerator.GenerateToolboxForPackage.

            import GeoEco
            from GeoEco.ArcToolbox import ArcToolboxGenerator

            ArcToolboxGenerator.GenerateToolboxForPackage(
                outputDir=os.path.join(self.build_lib, 'GeoEco', 'ArcToolbox', 'Marine Geospatial Ecology Tools'),
                packageName='GeoEco',
                displayName='Marine Geospatial Ecology Tools %s' % GeoEco.__version__.split('+')[0], 
                description='Access and manipulate marine ecological and oceanographic data', 
                alias='mget'
            )

        # When we are done, restore sys.dont_write_bytecode and remove the
        # build_lib directory from sys.path.

        finally:
            sys.dont_write_bytecode = oldFlag
            del sys.path[0]


class DeleteFilesFromBDist(setuptools.Command):
    """SubCommand for deleting unneeded files from build_lib so they do not end up in the bdist.

    The reason for this command is that setuptools apparently does not have a
    mechanism for excluding specific files from a bdist. To work around this
    missing functionality, this command explicitly deletes unneeded files from
    build_lib. After this command is done, setuputils creates the bdist from
    what is left.
    """

    def __init__(self, *args, **kwargs):
        self.build_lib = None
        super().__init__(*args, **kwargs)

    def initialize_options(self):
        """Set or (reset) all options/attributes/caches used by the command to their default values."""
        pass

    def finalize_options(self):
        """Set final values for all options/attributes used by the command."""
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def ensure_finalized(self):
        """This function is undocumented by setuputils, but apparently we have to support it."""
        self.finalize_options()

    def get_output_mapping(self):
        """Return a mapping between destination files as they would be produced by the build (dict keys) into the respective existing (source) files (dict values)."""
        return {}

    def get_outputs(self):
        """Return a list of files intended for distribution as they would have been produced by the build."""
        return []

    def get_source_files(self):
        """Return a list of all files that are used by the command to create the expected outputs."""
        return []

    def run(self):
        if self.build_lib is not None:
            globsToDelete = [
                os.path.join('GeoEco', 'DocutilsToEsriXdoc.xsl'),
                os.path.join('GeoEco', '_MetadataUtils.cpp'),
                os.path.join('GeoEco', 'Matlab', '_Matlab', '*.m'),
            ]

            for g in globsToDelete:
                for f in glob.glob(os.path.join(self.build_lib, g)):
                    print(f'Deleting {f} so it is not included in the bdist')
                    os.remove(f)


setuptools.command.sdist.sdist.sub_commands.append(('build_matlab_functions', None))
setuptools.command.build.build.sub_commands.append(('build_arcgis_toolbox', None))
setuptools.command.build.build.sub_commands.append(('delete_files_from_bdist', None))


setuptools.setup(
    ext_modules=[
        setuptools.Extension(
            name='GeoEco._MetadataUtils',
            sources=[os.path.join('src', 'GeoEco', '_MetadataUtils.cpp')],
        ),
    ],
    cmdclass={
        'build_matlab_functions': BuildMatlabFunctions,
        'build_arcgis_toolbox': BuildArcGISToolbox,
        'delete_files_from_bdist': DeleteFilesFromBDist,
    }
)
