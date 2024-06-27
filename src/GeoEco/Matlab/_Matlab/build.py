# build.py - Builds the GeoEco.Matlab._Matlab Python package from the .m files
# in this directory using the Matlab Compiler.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import glob
import os
import shutil
import subprocess
import sys

# This script only needs to be run when any of the .m files change. This
# script updates __init__.py and the _Matlab.ctf file. Those files are
# platform independent and are part of the git repo. So when the .m files
# change, this script only needs to be run once to update them. (It is not
# necessary to run this script once for Linux and again for Windows.)
#
# In order to execute this script, you must have a full installation of
# Matlab. First, we need the path to the Matlab executable. For now, we just
# hard-code the path to Matlab on our main Linux development machine.

if sys.platform == 'linux':
    matlabPath = '/usr/local/MATLAB/R2024a/bin/matlab'
else:
    raise NotImplementedError(f'This script does not currently support the {sys.platform} platform (but adding support would probably be easy).')

# Enumerate the .m files.

packageDir = os.path.join(os.path.dirname(__file__))
mFiles = glob.glob(os.path.join(packageDir, '*.m'))

# Execute the Matlab Compiler from the command line

mFilesStr = '[' + ','.join(['"' + f + '"' for f in mFiles]) + ']'
command = f'try compiler.build.pythonPackage({mFilesStr}, "PackageName", "GeoEco.Matlab._Matlab", "Verbose", "on"); catch; end; quit'
args = [matlabPath, '-nodesktop', '-nosplash', '-r', command]

print(f'Executing: {" ".join(args)}')
print('')

process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

while True:
    output = process.stdout.readline()
    if output == '' and process.poll() is not None:
        break
    if output:
        print(output.strip())

result = process.poll()
if result > 0:
    raise RuntimeError(f'{matlabPath} exited with code {result}, indicating failure.')

print('Matlab exited successfully.')

# Copy the two files that we want out of the directory that the Matlab
# Compiler created.

for filename in ['__init__.py', '_Matlab.ctf']:
    src = os.path.join(packageDir, '_MatlabpythonPackage', 'GeoEco', 'Matlab', '_Matlab', filename)
    dest = os.path.join(packageDir, filename)
    print(f'Copying {os.path.relpath(src, packageDir)} to {os.path.relpath(dest, packageDir)}.')
    shutil.copy(src, dest)

# Delete the directory that the Matlab Compiler created.

d = os.path.join(packageDir, '_MatlabpythonPackage')
print(f'Deleting {d}.')
shutil.rmtree(d)

# Write the MatlabFunctions.txt file.

txtFile = os.path.join(packageDir, 'MatlabFunctions.txt')
print(f'Writing {txtFile}.')
with open(txtFile, 'wt') as f:
    for filename in mFiles:
        f.write(f"{os.path.basename(filename).split('.')[0]}\n")

print ('Done.')
