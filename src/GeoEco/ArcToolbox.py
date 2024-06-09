# ArcToolbox.py - Functions for generating GeoEco's ArcGIS toolbox.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import pathlib
import importlib
import inspect
import json
import os
import pkgutil
import shutil
import sys
import zipfile

import GeoEco
from GeoEco.Logging import Logger
from GeoEco.Types import *


class ArcToolboxGenerator(object):

    @classmethod
    def GenerateToolboxForPackage(cls, outputDir, packageName, displayName, description, alias, overwriteExisting=False):

        # Log a startup message.

        started = datetime.datetime.now()

        Logger.Initialize()
        Logger.Info(f'GenerateToolboxForPackage started:')
        Logger.Info(f'    packageName = {packageName}')
        Logger.Info(f'    outputDir = {outputDir}')
        Logger.Info(f'')

        # If overwriteExisting is False, verify that the outputDir does not
        # exist or is empty.

        outputDir = pathlib.Path(outputDir)

        if outputDir.is_file():
            raise ValueError(f'The output directory {outputDir} exists but is a file. Please delete it and try again.')

        if not overwriteExisting and outputDir.is_dir() and len(outputDir.glob('*')) > 0:
            raise ValueError(f'The output directory {outputDir} exists and is not empty but overwriteExisting is False. Please delete it or set overwriteExisting to True and try again.')

        # Enumerate the modules in the requested package that do not start
        # with '_'. This code requires the package to be installed.

        Logger.Info(f'Enumerating modules in the {packageName} package.')

        package = importlib.import_module(packageName)
        moduleNames = [mi.name for mi in pkgutil.walk_packages(package.__path__, packageName + '.') if not mi.name.split('.')[-1].startswith('_')]

        # Enumerate methods of classes that have metadata where
        # IsExposedAsArcGISTool is True.

        Logger.Info(f'Enumerating methods exposed as ArcGIS tools.')

        methodsForToolbox = []

        for moduleName in moduleNames:
            module = importlib.import_module(moduleName)
            if module.__doc__ is not None and hasattr(module.__doc__, '_Obj'):
                if hasattr(module, '__all__'):
                    names = module.__all__
                else:
                    names = dir(module)
                for class_ in [getattr(module, name) for name in names if inspect.isclass(getattr(module, name))]:
                    if class_.__doc__ is not None and hasattr(class_.__doc__, '_Obj'):
                        for methodName, method in inspect.getmembers(class_, inspect.ismethod):
                            if method.__doc__ is not None and hasattr(method.__doc__, '_Obj') and method.__doc__._Obj.IsExposedAsArcGISTool:
                                methodsForToolbox.append(method)

        Logger.Info(f'Found {len(methodsForToolbox)} methods.')

        # Create a temporary output directory.

        p = pathlib.Path(outputDir)
        existingTempOutputDirs = sorted(p.parent.glob(p.name + '_tmp[0-9][0-9][0-9][0-9]'))
        nextNumber = int(str(existingTempOutputDirs[-1]).split('_')[-1][3:]) + 1 if len(existingTempOutputDirs) > 0 else 0
        tempOutputDir = p.parent / (p.name + '_tmp%04i' % nextNumber)
        os.makedirs(tempOutputDir)

        Logger.Info(f'Writing new toolbox to temporary directory {tempOutputDir}')

        # Create the toolbox.content file and and a subdirectory for each tool
        # with its own tool.content file.

        cls._CreateContentFiles(displayName, description, alias, methodsForToolbox, tempOutputDir)

        # Create the toolbox.module.py file. I don't know if the file must be
        # named this, but I am following ESRI's convention of putting the code
        # for all tools in a single file that has this name.

        #cls._CreateToolboxPythonFile(displayName, alias, methodsForToolbox, tempOutputDir)

        # Delete the current outputDir, if any, and rename the temp directory
        # to outputDir.

        Logger.Info(f'Removing {outputDir}')

        if outputDir.is_dir():
            shutil.rmtree(outputDir)

        Logger.Info(f'Renaming {tempOutputDir} to {outputDir}')

        os.rename(tempOutputDir, outputDir)

        # Create a zip file and rename it .atbx.

        outputATBX = str(outputDir) + '.atbx'

        Logger.Info(f'Creating {outputATBX}')

        with zipfile.ZipFile(outputATBX, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(outputDir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, outputDir)
                    zipf.write(file_path, arcname)

        # Log a completion message.

        Logger.Info(f'')
        Logger.Info(f'GenerateToolboxForPackage completed successfully.')
        Logger.Info(f'Elapsed time: {datetime.datetime.now() - started}')

    @classmethod
    def _CreateContentFiles(cls, displayName, description, alias, methodsForToolbox, outputDir):

        # Generate the toolbox.content and toolbox.content.rc dictionaries and
        # each tool in its own subdirectory.

        toolboxContent = {
            'version': '1.0',
            'alias': str(alias),
            'displayname': '$rc:title',
            'description': '$rc:description',
            'toolsets': {}
        }
        toolboxContentRC = {'map': {
            'title': str(displayName),
            'description': str(description),
        }}

        tsNums = {}
        lastTSNum = 0

        for method in methodsForToolbox:
            mm = method.__doc__._Obj

            if mm.ArcGISToolCategory not in tsNums:
                lastTSNum += 1
                tsNums[mm.ArcGISToolCategory] = lastTSNum
                toolboxContentRC['map']['param.category' + str(tsNums[mm.ArcGISToolCategory])] = mm.ArcGISToolCategory

            tsKey = '$rc:param.category' + str(tsNums[mm.ArcGISToolCategory])

            if tsKey not in toolboxContent['toolsets']:
                toolboxContent['toolsets'][tsKey] = {'tools': []}

            toolName = mm.Class.Name.split('.')[-1] + mm.Name
            toolboxContent['toolsets'][tsKey]['tools'].append(toolName)

            cls._CreateToolContentFile(toolName, mm, outputDir)

            cls._CreateToolPythonFiles(toolName, mm, outputDir)

        # Write the toolbox.content and toolbox.content.rc files.

        filePath = outputDir / 'toolbox.content'

        Logger.Info(f'Writing {filePath.name}')

        with filePath.open('wt') as f:
            json.dump(toolboxContent, f, indent=4)

        filePath = outputDir / 'toolbox.content.rc'

        Logger.Info(f'Writing {filePath.name}')

        with filePath.open('wt') as f:
            json.dump(toolboxContentRC, f, indent=4)

    @classmethod
    def _CreateToolContentFile(cls, toolName, mm, outputDir):

        # Create the subdirectory.

        toolDir = outputDir / (toolName + '.tool')
        os.makedirs(toolDir)

        # Generate the tool.content and tool.content.rc dictionaries.

        toolContent = {
            'type': 'ScriptTool',
            'displayname': '$rc:title',
            'description': '$rc:description',
            'params': {},
            'environments': [],
        }
        toolContentRC = {'map': {
            'title': mm.ArcGISDisplayName,
            'description': cls._GetToolDescription(mm),
        }}

        # Fill in the parameters.

        catNums = {}
        lastCatNum = 0

        for am in mm.Arguments:
            if am.ArcGISDisplayName is None:
                continue

            toolContent['params'][am.Name] = {
                'displayname': '$rc:' + am.Name + '.name',
                'datatype': {'type': cls._GetArcGISDataType(am.Type)},
                'description': '$rc:' + am.Name + '.descr',
            }
            toolContentRC['map'][am.Name + '.name'] = am.ArcGISDisplayName
            toolContentRC['map'][am.Name + '.descr'] = 'TODO: Add description'  # TODO

            if am.ArcGISCategory is not None and len(am.ArcGISCategory) > 0:
                if am.ArcGISCategory not in catNums:
                    lastCatNum += 1
                    catNums[am.ArcGISCategory] = lastCatNum
                    toolContentRC['map']['param.category' + str(catNums[am.ArcGISCategory])] = am.ArcGISCategory
                toolContent['params'][am.Name]['category'] = '$rc:param.category' + str(catNums[am.ArcGISCategory])

            if am.Direction == 'Output':
                toolContent['params'][am.Name]['direction'] = 'out'

            if am.HasDefault:
                toolContent['params'][am.Name]['type'] = 'optional'

            if am.HasDefault and am.Default is not None:
                toolContent['params'][am.Name]['value'] = str(am.Default)

            if am.ArcGISParameterDependencies is not None and len(am.ArcGISParameterDependencies) > 0:
                toolContent['params'][am.Name]['dependencies'] = am.ArcGISParameterDependencies

            # TODO: 'domain' based on allowedValues, minValue, etc.

        for rm in mm.Results:
            if rm.ArcGISDisplayName is None:
                continue

            toolContent['params'][rm.Name] = {
                'displayname': '$rc:' + rm.Name + '.name',
                'datatype': {'type': cls._GetArcGISDataType(rm.Type)},
                'description': '$rc:' + rm.Name + '.descr',      # TODO
                'direction': 'out',
                'type': 'derived',
            }
            toolContentRC['map'][rm.Name + '.name'] = rm.ArcGISDisplayName
            toolContentRC['map'][rm.Name + '.descr'] = 'TODO: Add description'  # TODO

            if rm.ArcGISParameterDependencies is not None and len(rm.ArcGISParameterDependencies) > 0:
                toolContent['params'][rm.Name]['dependencies'] = rm.ArcGISParameterDependencies

        # Write the tool.content and tool.content.rc files.

        filePath = toolDir / 'tool.content'

        Logger.Info(f'Writing {filePath.relative_to(outputDir)}')

        with filePath.open('wt') as f:
            json.dump(toolContent, f, indent=4)

        filePath = toolDir / 'tool.content.rc'

        Logger.Info(f'Writing {filePath.relative_to(outputDir)}')

        with filePath.open('wt') as f:
            json.dump(toolContentRC, f, indent=4)

    @classmethod
    def _CreateToolPythonFiles(cls, toolName, mm, outputDir):

        # Create tool.script.execute.py

        toolDir = outputDir / (toolName + '.tool')
        scriptPath = toolDir / 'tool.script.execute.py'

        Logger.Info(f'Writing {scriptPath.relative_to(outputDir)}')

        moduleFQN = mm.Class.Module.Name
        if moduleFQN.split('.')[-1].startswith('_'):
            moduleFQN = moduleFQN.rsplit('.', 1)[0]     # If we get an internal module, e.g. GeoEco.Foo.Bar._Baz, we want to import the containing package, e.g. GeoEco.Foo.Bar.

        with scriptPath.open('wt') as f:
            f.write(
f"""
def Main():
    from GeoEco.ArcGIS import GeoprocessorManager
    GeoprocessorManager.InitializeGeoprocessor()

    from GeoEco.Logging import Logger
    Logger.Initialize(activateArcGISLogging=True)

    import GeoEco.ArcToolbox
    import {moduleFQN}
    GeoEco.ArcToolbox._ExecuteMethodAsGeoprocessingTool({moduleFQN}.{mm.Class.Name}.{mm.Name})

if __name__ == "__main__":
    Main()
""")

        # Create tool.script.validate.py

        scriptPath = toolDir / 'tool.script.validate.py'

        Logger.Info(f'Writing {scriptPath.relative_to(outputDir)}')

        with scriptPath.open('wt') as f:
            f.write(
"""
class ToolValidator:
    def __init__(self):
        pass

    def initializeParameters(self):
        pass

    def updateParameters(self):
        pass

    def updateMessages(self):
        pass
""")

    @classmethod
    def _GetArcGISDataType(cls, typeMetadata):

        # If it is a SequenceTypeMetadata, return the data type of the
        # element it contains.

        if isinstance(typeMetadata, SequenceTypeMetadata):
            return cls._GetArcGISDataType(typeMetadata.ElementType)

        # For some types, we just need to strip 'Class' from the end of the
        # ArcObjects .NET class name.

        arcObjectsType = typeMetadata.ArcGISType.split('.')[-1]

        if arcObjectsType in ['DEGeoDatasetTypeClass', 'GPTypeClass']:
            return arcObjectsType[:-5]

        # For everything else, we need strip 'TypeClass' from the end.

        if arcObjectsType.endswith('TypeClass'):
            return arcObjectsType[:-9]

        return arcObjectsType

    @classmethod
    def _GetToolDescription(cls, methodMetadata):
        rst = methodMetadata.ShortDescription
        if methodMetadata.LongDescription is not None:
            rst += '\n\n' + methodMetadata.LongDescription
        return cls._RestructuredTextToEsriXDoc(rst)

    @classmethod
    def _RestructuredTextToEsriXDoc(cls, rst):
        return '<xdoc>' + rst.replace('\n', '<br/>') + '</xdoc>'      # TODO

    #############################################################################
    # TODO: Remove the following obsolete functions
    #############################################################################

    @classmethod
    def _CreateToolboxPythonFile(cls, displayName, alias, methodsForToolbox, outputDir):

        # Write the toolbox.module.py file.

        pyFilePath = outputDir / 'toolbox.module.py'

        Logger.Info(f'Writing {pyFilePath.name}')

        with pyFilePath.open('wt') as f:

            # Write the imports and Toolbox class:

            newline = '\n'
            f.write(
f"""# toolbox.module.py - GeoEco's ArcGIS Python geoprocessing tools.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = '''{displayName}'''
        self.alias = '{alias}'
        self.tools = [
            {(','+newline+'            ').join([meth.__doc__._Obj.Class.Name.split('.')[-1] + meth.__doc__._Obj.Name for meth in methodsForToolbox])}
        ]
""")
            # Write a class for each tool.

            for method in methodsForToolbox:
                methodMetadata = method.__doc__._Obj
                cls._WriteToolPythonClass(methodMetadata, f)

    @classmethod
    def _WriteToolPythonClass(cls, mm, f):

        # Write the class declaration and __init__(). Following ESRI's Python
        # tools that come with Arc Pro, we set self.description to an empty
        # string, self.canRunInBackground to False, and self.params to None.

        bs = '\\'
        quote = "'"
        className = mm.Class.Name.split('.')[-1] + mm.Name

        Logger.Debug(f'    class {className}:')

        f.write(
f"""

class {className}(object):
    def __init__(self):
        self.label = '''{mm.ArcGISDisplayName}'''
        self.description = ''
        self.canRunInBackground = False
        self.category = '{mm.ArcGISToolCategory.replace(bs, bs+bs) if mm.ArcGISToolCategory is not None else ""}'
        self.params = None
""")
        # Write the getParameterInfo() method.

        Logger.Debug(f'        getParameterInfo():')

        f.write('\n')
        f.write('    def getParameterInfo(self):\n')
        f.write('        params = []\n')

        for am in mm.Arguments:
            if am.ArcGISDisplayName is None:
                continue

            Logger.Debug(f'            parameter: {am.Name}')

            f.write(
f"""        
        params.append(arcpy.Parameter(
            displayName='''{am.ArcGISDisplayName}''',
            name='{am.Name}',
            datatype='{cls._GetArcGISDataType(am.Type)}',
            parameterType='{'Required' if not am.HasDefault else 'Optional'}',
            direction='{am.Direction}'
        ))
""")
            if am.ArcGISCategory is not None and len(am.ArcGISCategory) > 0:
                f.write(f'        params[-1].category = {repr(am.ArcGISCategory)}\n')

            if isinstance(am.Type, SequenceTypeMetadata):
                f.write(f'        params[-1].multiValue = True\n')

            if am.ArcGISParameterDependencies is not None and len(am.ArcGISParameterDependencies) > 0:
                f.write(f'        params[-1].parameterDependencies = [{", ".join([quote + d + quote for d in am.ArcGISParameterDependencies])}]\n')

            if am.HasDefault and am.Default is not None:
                f.write(f'        params[-1].value = {repr(am.Default)}\n')

            # TODO: filters

        for rm in mm.Results:
            if rm.ArcGISDisplayName is None:
                continue

            Logger.Debug(f'            result: {rm.Name}')

            f.write(
f"""        
        params.append(arcpy.Parameter(
            displayName='''{rm.ArcGISDisplayName}''',
            name='{rm.Name}',
            datatype='{cls._GetArcGISDataType(rm.Type)}',
            parameterType='Derived',
            direction='Output'
        ))
""")
            if rm.ArcGISParameterDependencies is not None and len(rm.ArcGISParameterDependencies) > 0:
                f.write(f'        params[-1].parameterDependencies = [{", ".join([quote + d + quote for d in rm.ArcGISParameterDependencies])}]\n')

        f.write('\n')
        f.write('        return params\n')

        # Write execute().

        Logger.Debug(f'        execute()')

        moduleFQN = mm.Class.Module.Name
        if moduleFQN.split('.')[-1].startswith('_'):
            moduleFQN = moduleFQN.rsplit('.', 1)[0]     # If we get an internal module, e.g. GeoEco.Foo.Bar._Baz, we want to import the containing package, e.g. GeoEco.Foo.Bar.
        f.write(
f"""
    def execute(self, parameters, messages):
        import GeoEco.ArcToolbox
        import {moduleFQN}
        GeoEco.ArcToolbox._ExecuteMethodAsGeoprocessingTool({moduleFQN}.{mm.Class.Name}.{mm.Name}, parameters, messages)
""")

        # Write isLicensed(), updateParameters(), and updateMessages(), and
        # postExecute(). We do not use these for anything.

        f.write(
"""
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        pass

    def updateMessages(self, parameters):
        pass

    def postExecute(self, parameters):
        pass
""")


def _ExecuteMethodAsGeoprocessingTool(method):

    # Determine the method's argument values.

    import arcpy

    mm = method.__doc__.Obj
    paramInfo = arcpy.GetParameterInfo()
    pni = {p.name: i for i, p in enumerate(paramInfo)}
    argValues = {}

    in_raster = arcpy.GetParameterAsText(pni["in_raster"])

    for am in mm.Arguments:
        if am.InitializeToArcGISGeoprocessorVariable is not None:
            argValues[am.Name] = getattr(arcpy, am.InitializeToArcGISGeoprocessorVariable)

        if am.ArcGISDisplayName is None:
                continue

        argValues[am.Name] = arcpy.GetParameter(pni[am.Name])

    # Log a debug message indicating the method is being called.

    Logger.Debug('Calling %s.%s.%s(%s)' % (mm.Class.Module.Name, mm.Class.Name, mm.Name, ', '.join([key + '=' + repr(value) for key, value in argValues.items()])))

    # Call the method.

    method(**argValues)


def Main() -> int:

    # Determine the output directory.

    outputDir = pathlib.Path(__file__).parent / 'ArcToolbox' / 'Marine Geospatial Ecology Tools'

    # Create the toolbox.

    ArcToolboxGenerator.GenerateToolboxForPackage(
        outputDir=outputDir,
        packageName='GeoEco',
        displayName='Marine Geospatial Ecology Tools %s' % GeoEco.__version__.split('+')[0], 
        description='Access and manipulate marine ecological and oceanographic data', 
        alias='mget',
        overwriteExisting=True
    )

    # Exit succesfully.

    return 0


if __name__ == "__main__":
    sys.exit(Main())
