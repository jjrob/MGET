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

        print(f'GenerateToolboxForPackage started:')
        print(f'    packageName = {packageName}')
        print(f'    outputDir = {outputDir}')

        # If overwriteExisting is False, verify that the outputDir does not
        # exist or is empty.

        outputDir = pathlib.Path(outputDir)

        if outputDir.is_file():
            raise ValueError(f'The output directory {outputDir} exists but is a file. Please delete it and try again.')

        if not overwriteExisting and outputDir.is_dir() and len(outputDir.glob('*')) > 0:
            raise ValueError(f'The output directory {outputDir} exists and is not empty but overwriteExisting is False. Please delete it or set overwriteExisting to True and try again.')

        # Enumerate the modules in the requested package that do not start
        # with '_'. This code requires the package to be installed.

        print(f'Enumerating modules in the {packageName} package.')

        def onError(moduleName):
            if moduleName == 'GeoEco.Matlab._Matlab':
                return
            raise ImportError(f'Failed to import the {moduleName} module')

        package = importlib.import_module(packageName)
        moduleNames = [mi.name for mi in pkgutil.walk_packages(package.__path__, packageName + '.', onerror=onError) if not mi.name.split('.')[-1].startswith('_')]

        # Enumerate methods of classes that have metadata where
        # IsExposedAsArcGISTool is True.

        print(f'Enumerating methods exposed as ArcGIS tools.')

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

        print(f'Found {len(methodsForToolbox)} methods.')

        # Create a temporary output directory.

        p = pathlib.Path(outputDir)
        existingTempOutputDirs = sorted(p.parent.glob(p.name + '_tmp[0-9][0-9][0-9][0-9]'))
        nextNumber = int(str(existingTempOutputDirs[-1]).split('_')[-1][3:]) + 1 if len(existingTempOutputDirs) > 0 else 0
        tempOutputDir = p.parent / (p.name + '_tmp%04i' % nextNumber)
        os.makedirs(tempOutputDir)

        print(f'Writing new toolbox to temporary directory {tempOutputDir}')

        # Create the toolbox.content file and and a subdirectory for each tool
        # with its own tool.content file.

        cls._CreateContentFiles(displayName, description, alias, methodsForToolbox, tempOutputDir)

        # Create the toolbox.module.py file. I don't know if the file must be
        # named this, but I am following ESRI's convention of putting the code
        # for all tools in a single file that has this name.

        #cls._CreateToolboxPythonFile(displayName, alias, methodsForToolbox, tempOutputDir)

        # Delete the current outputDir, if any, and rename the temp directory
        # to outputDir.

        print(f'Removing {outputDir}')

        if outputDir.is_dir():
            shutil.rmtree(outputDir)

        print(f'Renaming {tempOutputDir} to {outputDir}')

        os.rename(tempOutputDir, outputDir)

        # Create a zip file and rename it .atbx.

        outputATBX = str(outputDir) + '.atbx'

        print(f'Creating {outputATBX}')

        with zipfile.ZipFile(outputATBX, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(outputDir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, outputDir)
                    zipf.write(file_path, arcname)

        # After creating the zip, we can remove the outputDir. If we need to
        # debug something, we can comment out this code and the outputDir will
        # be included in the built wheel.

        print(f'Removing {outputDir}')

        if outputDir.is_dir():
            shutil.rmtree(outputDir)

        # Log a completion message.

        print(f'GenerateToolboxForPackage completed successfully.')
        print(f'Elapsed time: {datetime.datetime.now() - started}')

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

        print(f'Writing {filePath.name}')

        with filePath.open('wt') as f:
            json.dump(toolboxContent, f, indent=4)

        filePath = outputDir / 'toolbox.content.rc'

        print(f'Writing {filePath.name}')

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
                'datatype': am.Type.ArcGISDataTypeDict,
                'description': '$rc:' + am.Name + '.descr',
            }
            toolContentRC['map'][am.Name + '.name'] = am.ArcGISDisplayName
            toolContentRC['map'][am.Name + '.descr'] = cls._RestructuredTextToEsriXDoc(am.Description)

            domain = am.Type.ArcGISDomainDict
            if domain is not None:
                toolContent['params'][am.Name]['domain'] = domain

            if am.ArcGISCategory is not None and len(am.ArcGISCategory) > 0:
                if am.ArcGISCategory not in catNums:
                    lastCatNum += 1
                    catNums[am.ArcGISCategory] = lastCatNum
                    toolContentRC['map']['param.category' + str(catNums[am.ArcGISCategory])] = am.ArcGISCategory
                toolContent['params'][am.Name]['category'] = '$rc:param.category' + str(catNums[am.ArcGISCategory])

            if am.Direction == 'Output':
                toolContent['params'][am.Name]['direction'] = 'out'

            if am.HasDefault or am.Type.CanBeNone:
                toolContent['params'][am.Name]['type'] = 'optional'

            if am.HasDefault and am.Default is not None:
                # If the default is not a list or a tuple, just turn it into a
                # string.

                if not isinstance(am.Default, list) and not isinstance(am.Default, tuple):
                    toolContent['params'][am.Name]['value'] = str(am.Default)

                # Otherwise (it is a list or tuple), it means this is a
                # GPMultiValue parameter. We could find no documentation on
                # how the default of a GPMultiValue parameter should be
                # represented in JSON, but we discovered that if you render
                # the values into a semicolon-separated string, they will
                # each appear as a separate entry in the GUI, which is what
                # we need.

                else:
                    for v in am.Default:
                        if ';' in str(v):
                            raise ValueError(f'The default value for the {am.Name} argument of the {toolName} tool contains an item {v!r} that contains a semicolon. This argument must be represented in the tool.content JSON as a GPMultiValue parameter. We don\'t know how to encode default values of this type of parameter that include semicolons, because the semicolon is used as the delimiter in the list of default values.')
                    toolContent['params'][am.Name]['value'] = ';'.join([str(v) for v in am.Default])

            if am.ArcGISParameterDependencies is not None and len(am.ArcGISParameterDependencies) > 0:
                toolContent['params'][am.Name]['depends'] = am.ArcGISParameterDependencies

        for rm in mm.Results:
            if rm.ArcGISDisplayName is None:
                continue

            toolContent['params'][rm.Name] = {
                'displayname': '$rc:' + rm.Name + '.name',
                'datatype': rm.Type.ArcGISDataTypeDict,
                'description': '$rc:' + rm.Name + '.descr',
                'direction': 'out',
                'type': 'derived',
            }
            toolContentRC['map'][rm.Name + '.name'] = rm.ArcGISDisplayName
            toolContentRC['map'][rm.Name + '.descr'] = cls._RestructuredTextToEsriXDoc(rm.Description)

            if rm.ArcGISParameterDependencies is not None and len(rm.ArcGISParameterDependencies) > 0:
                toolContent['params'][rm.Name]['depends'] = rm.ArcGISParameterDependencies

        # Write the tool.content and tool.content.rc files.

        filePath = toolDir / 'tool.content'

        print(f'Writing {filePath.relative_to(outputDir)}')

        with filePath.open('wt') as f:
            json.dump(toolContent, f, indent=4)

        filePath = toolDir / 'tool.content.rc'

        print(f'Writing {filePath.relative_to(outputDir)}')

        with filePath.open('wt') as f:
            json.dump(toolContentRC, f, indent=4)

    @classmethod
    def _CreateToolPythonFiles(cls, toolName, mm, outputDir):

        # Create tool.script.execute.py

        toolDir = outputDir / (toolName + '.tool')
        scriptPath = toolDir / 'tool.script.execute.py'

        print(f'Writing {scriptPath.relative_to(outputDir)}')

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

        print(f'Writing {scriptPath.relative_to(outputDir)}')

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
    def _GetToolDescription(cls, methodMetadata):
        rst = methodMetadata.ShortDescription
        if methodMetadata.LongDescription is not None:
            rst += '\n\n' + methodMetadata.LongDescription
        return cls._RestructuredTextToEsriXDoc(rst)

    @classmethod
    def _RestructuredTextToEsriXDoc(cls, rst):

        # Get the docutils XML for the rst.

        import docutils.core
        import lxml.etree

        docutilsXML = lxml.etree.fromstring(docutils.core.publish_string(rst, writer_name='xml'))

        # If we have not done so already, load the XSL transform for
        # transforming docutils XML to ESRI XDoc XML.

        if not hasattr(ArcToolboxGenerator, '_RstToXdocTransformer'):
            xslFile = pathlib.Path(__file__).parent / 'DocutilsToEsriXdoc.xsl'
            print('Parsing %s' % xslFile)
            ArcToolboxGenerator._RstToXdocTransformer = lxml.etree.XSLT(lxml.etree.parse(xslFile))

            # Register some handlers for docutils roles that are not part of
            # the base restructuredText syntax.

            cls._RegisterCustomDocutilsRoles()

        # Transform the docutils XML into ESRI XDoc XML and return it.
        #
        # TODO: replace <i>argumentName</i> with <i>ArcGIS Display Name</i>

        try:
            return str(ArcToolboxGenerator._RstToXdocTransformer(docutilsXML)).strip('\n')

        except Exception as e:
            Logger.Error('The following restructuredText:')
            Logger.Error('')

            for line in rst.split('\n'):
                Logger.Error('    ' + line)

            Logger.Error('')
            Logger.Error('was transformed into Docutils XML:')
            Logger.Error('')

            for line in lxml.etree.tostring(docutilsXML, encoding='unicode', pretty_print=True).split('\n'):
                Logger.Error('    ' + line)

            Logger.Error('')
            Logger.Error('but could not be transformed into ESRI XDoc XML because of the following error.')

            raise

    @classmethod
    def _RegisterCustomDocutilsRoles(cls):
        from docutils.parsers.rst import roles
        from docutils import nodes

        # For :arcpy_XXXXX:, link to the ArcGIS documentation.

        def arcpy_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            ref = 'https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/%s.htm' % text.lower()
            node = nodes.reference(text=text.replace('-',''), refuri=ref, **options)
            return [node], []

        roles.register_canonical_role('arcpy', arcpy_role)

        def arcpy_conversion_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            ref = 'https://pro.arcgis.com/en/pro-app/latest/tool-reference/conversion/%s.htm' % text.lower()
            node = nodes.reference(text=text.replace('-',''), refuri=ref, **options)
            return [node], []

        roles.register_canonical_role('arcpy_conversion', arcpy_conversion_role)

        def arcpy_management_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            ref = 'https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/%s.htm' % text.lower()
            node = nodes.reference(text=text.replace('-',''), refuri=ref, **options)
            return [node], []

        roles.register_canonical_role('arcpy_management', arcpy_management_role)

        def arcpy_sa_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            ref = 'https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/%s.htm' % text.lower()
            node = nodes.reference(text=text.replace('-',''), refuri=ref, **options)
            return [node], []

        roles.register_canonical_role('arcpy_sa', arcpy_sa_role)

        # For :py: roles, we'll use Python's intersphinx mappings. First
        # download the Python intersphinx objects.inv and populate a
        # dictionary for looking up intersphinx references.

        import sphobjinv

        objectsInvURL = 'https://docs.python.org/3/objects.inv'
        print('Downloading ' + objectsInvURL)
        inv = sphobjinv.Inventory(url=objectsInvURL)
        iSphinxLookup = {}

        for dobj in inv.objects:
            if dobj.domain not in iSphinxLookup:
                iSphinxLookup[dobj.domain] = {}
            if dobj.role not in iSphinxLookup[dobj.domain]:
                iSphinxLookup[dobj.domain][dobj.role] = {}
            if dobj.name not in iSphinxLookup[dobj.domain][dobj.role]:
                iSphinxLookup[dobj.domain][dobj.role][dobj.name] = dobj
            elif dobj.priority < iSphinxLookup[dobj.domain][dobj.role][dobj.name].priority:  # Lower priority numbers are higher priorities, according to https://sphobjinv.readthedocs.io/en/stable/syntax.html
                iSphinxLookup[dobj.domain][dobj.role][dobj.name] = dobj

        # Define a function for parsing '~'' at the front of role text.

        def strip_tilde(text):
            if text.startswith('~'):
                return text[1:], text.split('.')[-1]
            return text, text

        # Register a role for :py:func:

        import docutils.nodes

        def python_func_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            iSphinxName, displayName = strip_tilde(text)
            if iSphinxName not in iSphinxLookup['py']['function']:
                raise ValueError('For the :py:func: role, the Python intersphinx objects.inv does not have an entry for %r.' % iSphinxName)
            dobj = iSphinxLookup['py']['function'][iSphinxName]
            ref = 'https://docs.python.org/3/' + dobj.uri.replace('$', iSphinxName)
            link_node = docutils.nodes.reference(refuri=ref, **options)
            link_node += docutils.nodes.literal(text=displayName + '()')
            return [link_node], []

        roles.register_canonical_role('py:func', python_func_role)

        # Register a role for :py:meth:

        def python_meth_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            iSphinxName, displayName = strip_tilde(text)
            if iSphinxName not in iSphinxLookup['py']['method']:
                raise ValueError('For the :py:meth: role, the Python intersphinx objects.inv does not have an entry for %r.' % iSphinxName)
            dobj = iSphinxLookup['py']['method'][iSphinxName]
            ref = 'https://docs.python.org/3/' + dobj.uri.replace('$', iSphinxName)
            link_node = docutils.nodes.reference(refuri=ref, **options)
            link_node += docutils.nodes.literal(text=displayName + '()')
            return [link_node], []

        roles.register_canonical_role('py:meth', python_meth_role)

        # Register a role for :py:class:

        def python_class_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            iSphinxName, displayName = strip_tilde(text)
            if iSphinxName not in iSphinxLookup['py']['class']:
                raise ValueError('For the :py:class: role, the Python intersphinx objects.inv does not have an entry for %r.' % iSphinxName)
            dobj = iSphinxLookup['py']['class'][iSphinxName]
            ref = 'https://docs.python.org/3/' + dobj.uri.replace('$', iSphinxName)
            link_node = docutils.nodes.reference(refuri=ref, **options)
            link_node += docutils.nodes.literal(text=displayName)
            return [link_node], []

        roles.register_canonical_role('py:class', python_class_role)

        # Register a role for :py:exc:

        def python_exc_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            iSphinxName, displayName = strip_tilde(text)
            if iSphinxName not in iSphinxLookup['py']['exception']:
                raise ValueError('For the :py:exc: role, the Python intersphinx objects.inv does not have an entry for %r.' % iSphinxName)
            dobj = iSphinxLookup['py']['exception'][iSphinxName]
            ref = 'https://docs.python.org/3/' + dobj.uri.replace('$', iSphinxName)
            link_node = docutils.nodes.reference(refuri=ref, **options)
            link_node += docutils.nodes.literal(text=displayName)
            return [link_node], []

        roles.register_canonical_role('py:exc', python_exc_role)

        # Register a role for :py:data:

        def python_data_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            if text not in iSphinxLookup['py']['data']:
                raise ValueError('For the :py:data: role, the Python intersphinx objects.inv does not have an entry for %r.' % text)
            dobj = iSphinxLookup['py']['data'][text]
            ref = 'https://docs.python.org/3/' + dobj.uri.replace('$', text)
            link_node = docutils.nodes.reference(refuri=ref, **options)
            link_node += docutils.nodes.literal(text=text)
            return [link_node], []

        roles.register_canonical_role('py:data', python_data_role)

        # Register a role for :py:mod:

        import docutils.nodes

        def python_mod_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            if text not in iSphinxLookup['py']['module']:
                raise ValueError('For the :py:mod: role, the Python intersphinx objects.inv does not have an entry for %r.' % text)
            dobj = iSphinxLookup['py']['module'][text]
            ref = 'https://docs.python.org/3/' + dobj.uri.replace('$', text)
            link_node = docutils.nodes.reference(refuri=ref, **options)
            link_node += docutils.nodes.literal(text=text)
            return [link_node], []

        roles.register_canonical_role('py:mod', python_mod_role)

        # Register a role for :py:ref:

        import docutils.nodes

        def python_ref_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
            if text not in iSphinxLookup['std']['label']:
                raise ValueError('For the :py:ref: role, the Python intersphinx objects.inv does not have an entry for %r.' % text)
            dobj = iSphinxLookup['std']['label'][text]
            ref = 'https://docs.python.org/3/' + dobj.uri.replace('$', text)
            link_node = docutils.nodes.reference(text=dobj.dispname, refuri=ref, **options)
            return [link_node], []

        roles.register_canonical_role('py:ref', python_ref_role)


def _ExecuteMethodAsGeoprocessingTool(method):

    # Determine the method's argument values.

    from GeoEco.ArcGIS import GeoprocessorManager, _ArcGISObjectWrapper

    gp = GeoprocessorManager.GetWrappedGeoprocessor()
    gpUnwrapped = GeoprocessorManager.GetGeoprocessor()
    paramInfo = gp.GetParameterInfo()
    pni = {p.name: i for i, p in enumerate(paramInfo)}
    mm = method.__doc__.Obj
    argValues = {}
    argValuesToLog = {}

    for i, am in enumerate(mm.Arguments):

        # If it is the first argument, which is cls or self, skip it. We do
        # not provide a value for this argument directly.

        if i == 0:
            continue

        # If we are supposed to initialize this argument to a geoprocessor
        # variable (typically a member of arcpy.env), get that value. If the
        # argument is supposed to be a hidden string, use the unwrapped
        # geoprocessor so we don't log its value.

        if am.InitializeToArcGISGeoprocessorVariable is not None:
            value = gp if not isinstance(am.Type, UnicodeStringHiddenTypeMetadata) else gpUnwrapped
            for attr in am.InitializeToArcGISGeoprocessorVariable.split('.'):
                value = getattr(value, attr)

        # Otherwise, if the argument is displayed in the ArcGIS user interface,
        # get the value that the user provided. As above, if the argument is
        # supposed to be a hidden string, use the unwrapped geoprocessor so
        # we don't log its value.

        elif am.ArcGISDisplayName is not None:
            if isinstance(am.Type, UnicodeStringHiddenTypeMetadata):
                value = gpUnwrapped.GetParameterAsText(pni[am.Name])
                if value == '':
                    value = None

            # Otherwise, if this argument's TypeMetadata is an instance of
            # UnicodeStringTypeMetadata, get it with gp.GetParameterAsText.
            # Unwrap the _ArcGISObjectWrapper.

            elif isinstance(am.Type, UnicodeStringTypeMetadata):
                value = gp.GetParameterAsText(pni[am.Name])
                if isinstance(value, _ArcGISObjectWrapper):
                    value = value._Object
                if value == '':
                    value = None

            # Otherwise, extract the value from the arcpy Parameter object.

            else:
                param = paramInfo[pni[am.Name]]
                value = param.values if hasattr(param, 'values') else param.value

                # If value is an instance of _ArcGISObjectWrapper, unwrap it.
                # If it is a "geoprocessing value object", extract its value.

                if isinstance(value, _ArcGISObjectWrapper):
                    value = value._Object
                if 'geoprocessing value object' in str(type(value)):
                    value = value.value

                # If value is a list, repeat the steps above on its items.

                if isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, _ArcGISObjectWrapper):
                            item = item._Object
                        if 'geoprocessing value object' in str(type(item)):
                            item = item.value
                        value[i] = item

        # Otherwise, we won't assign a value to this argument and its default
        # value will be used.

        else:
            continue

        argValues[am.Name] = value
        argValuesToLog[am.Name] = argValues[am.Name] if not isinstance(am.Type, UnicodeStringHiddenTypeMetadata) else '*****'

    # Log a debug message indicating the method is being called.

    Logger.Debug('Calling %s.%s.%s(%s)' % (mm.Class.Module.Name, mm.Class.Name, mm.Name, ', '.join([key + '=' + repr(value) for key, value in argValuesToLog.items()])))

    # Call the method.

    results = method(**argValues)

    # Set the "derived" output parameters using the returned results

    if len(mm.Results) > 0:
        r = 0
        if len(mm.Results) == 1:
            results = (results,)
        for i, rm in enumerate(mm.Results):
            if rm.ArcGISDisplayName is not None:
                if not isinstance(rm.Type, UnicodeStringHiddenTypeMetadata):
                    Logger.Debug('Setting geoprocessing output parameter %s=%r' % (rm.Name, results[i]))
                    gp.SetParameterAsText(pni[rm.Name], str(results[r]))
                else:
                    Logger.Debug('Setting geoprocessing output parameter %s=\'*****\'' % rm.Name)
                    gpUnwrapped.SetParameterAsText(pni[rm.Name], str(results[r]))
                r += 1
