# BatchProcessing.py - Utility classes used by other GeoEco classes to
# implement batch processing versions of their methods.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import copy
import inspect
import os
import sys
import types

from .ArcGIS import ArcGISDependency
from .Datasets import Database
from .DynamicDocString import DynamicDocString
from .Internationalization import _
from .Logging import Logger, ProgressReporter
from .Metadata import *
from .Types import *


class BatchProcessing(object):
    __doc__ = DynamicDocString()

    @classmethod
    def GenerateForMethod(cls,
                          method,
                          inputParamNames,
                          inputParamFieldArcGISDisplayNames,
                          inputParamDescriptions,
                          outputParamNames=None,
                          outputParamFieldArcGISDisplayNames=None,
                          outputParamExpressionArcGISDisplayNames=None,
                          outputParamDescriptions=None,
                          outputParamExpressionDescriptions=None,
                          outputParamDefaultExpressions=None,
                          constantParamNames=None,
                          newConstantParamDefaults=None,
                          resultFieldArcGISDisplayNames=None,
                          resultFieldDescriptions=None,
                          derivedResultsForArcGIS=None,
                          processListMethodName=None,
                          processListMethodShortDescription=None,
                          processListMethodResultDescription=None,
                          useExistingProcessListMethod=False,
                          processTableMethodName=None,
                          processTableMethodShortDescription=None,
                          processArcGISTableMethodName=None,
                          processArcGISTableMethodArcGISDisplayName=None,
                          findAndProcessMethodName=None,
                          findAndProcessMethodArcGISDisplayName=None,
                          findAndProcessMethodShortDescription=None,
                          findMethod=None,
                          findOutputFieldParams=None,
                          findAdditionalParams=None,
                          newFindAdditionalParamDefaults=None,
                          outputLocationTypeMetadata=None,
                          outputLocationParamDescription=None,
                          outputLocationParamArcGISDisplayName=None,
                          calculateFieldMethod=None,
                          calculateFieldExpressionParam=None,
                          calculateFieldAdditionalParams=None,
                          calculateFieldAdditionalParamsDefaults=None,
                          calculateFieldHiddenParams=None,
                          calculateFieldHiddenParamValues=None,
                          calculatedOutputsArcGISCategory=None,
                          constantParamsToOmitFromFindAndProcessMethod=None,
                          skipExistingDescription=None,
                          overwriteExistingDescription=None):

        # Validate the input parameters. We cannot use the
        # ClassMetadata.ValidateMethodInvocation method here because it
        # imports the MetadataUtils package, which is implemented in C++ and
        # therefore not available at build time.

        assert isinstance(method, types.MethodType) and isinstance(method.__doc__, DynamicDocString) and isinstance(method.__doc__.Obj, MethodMetadata), 'method must be a method, with the __doc__ attribute set to an instance of DynamicDocString and __doc__.Obj set to an instance of MethodMetadata'
        methodMetadata = method.__doc__.Obj
        assert methodMetadata.IsInstanceMethod or methodMetadata.IsClassMethod, 'method must be an instance method or classmethod'

        assert isinstance(inputParamNames, list) and len(inputParamNames) >= 1, 'inputParamNames must be a Python list with at least one element'
        for name in inputParamNames:
            assert isinstance(name, str), 'All elements of inputParamNames must be strings.'
            argMetadata = methodMetadata.GetArgumentByName(name)
            assert argMetadata is not None, '%s.%s must have an argument named %s' % (methodMetadata.Class.Name, methodMetadata.Name, name)
        
        assert isinstance(inputParamDescriptions, list), 'inputParamNames must be a Python list'
        assert len(inputParamDescriptions) == len(inputParamNames), 'inputParamDescriptions must be the same length as inputParamNames'
        for s in inputParamDescriptions:
            assert isinstance(s, str), 'All elements of inputParamDescriptions must be strings.'

        assert isinstance(outputParamNames, (list, type(None))), 'outputParamNames must be a Python list, or None'
        if outputParamNames is not None and len(outputParamNames) <= 0:
            outputParamNames = None
        if outputParamNames is not None:
            for name in outputParamNames:
                assert name not in inputParamNames, 'The same argument %s must not appear in both inputParamNames and outputParamNames' % name
                argMetadata = methodMetadata.GetArgumentByName(name)
                assert argMetadata is not None, '%s.%s must have an argument named %s' % (methodMetadata.Class.Name, methodMetadata.Name, name)
                assert isinstance(argMetadata.Type, StoredObjectTypeMetadata), 'If argument %s of %s.%s appears in outputParamNames, its type metadata must be an instance of StoredObjectTypeMetadata' % (name, methodMetadata.Class.Name, methodMetadata.Name)

            assert isinstance(outputParamDescriptions, list), 'outputParamDescriptions must be a Python list'
            assert len(outputParamDescriptions) == len(outputParamNames), 'outputParamDescriptions must have the same length as outputParamNames'
            for s in outputParamDescriptions:
                assert isinstance(s, str), 'All elements of outputParamDescriptions must be strings.'

        assert isinstance(constantParamNames, (list, type(None))), 'constantParamNames must be a Python list, or None'
        if constantParamNames is not None and len(constantParamNames) <= 0:
            constantParamNames = None
        if constantParamNames is not None:
            for name in constantParamNames:
                assert name not in inputParamNames, 'The same argument %s must not appear in both inputParamNames and constantParamNames' % name
                if outputParamNames is not None:
                    assert name not in outputParamNames, 'The same argument %s must not appear in both outputParamNames and constantParamNames' % name
                argMetadata = methodMetadata.GetArgumentByName(name)
                assert argMetadata is not None, '%s.%s must have an argument named %s' % (methodMetadata.Class.Name, methodMetadata.Name, name)
        if newConstantParamDefaults is not None:
            assert isinstance(newConstantParamDefaults, dict), 'newConstantParamDefaults must be a dictionary, or None'
            assert constantParamNames is not None, 'newConstantParamDefaults must be none if constantParamNames is None'
            for key in newConstantParamDefaults:
                assert key in constantParamNames, 'Every parameter specified as a key in newConstantParamDefaults must appear in the constantParamNames list'

        for argMetadata in methodMetadata.Arguments[1:]:
            assert argMetadata.HasDefault or (inputParamNames is not None and argMetadata.Name in inputParamNames) or (outputParamNames is not None and argMetadata.Name in outputParamNames) or (constantParamNames is not None and argMetadata.Name in constantParamNames), 'Argument %s of %s.%s must have a default or it must appear in either inputParamNames, outputParamNames, or constantParamNames' % (name, methodMetadata.Class.Name, methodMetadata.Name)

        assert isinstance(processListMethodName, (str, type(None))), 'processListMethodName must be a string, or None'
        assert isinstance(processListMethodShortDescription, (str, type(None))), 'processListMethodShortDescription must be a string, or None'
        assert processListMethodName is None and processListMethodShortDescription is None or processListMethodName is not None and processListMethodShortDescription is not None, 'processListMethodName and processListMethodShortDescription must both be None or must both not be None'
        if len(methodMetadata.Results) > 0 and (derivedResultsForArcGIS is None or len(derivedResultsForArcGIS) < len(methodMetadata.Results)):
            assert isinstance(processListMethodResultDescription, str), 'processListMethodResultDescription must be a string when the method has results that do not appear in derivedResultsForArcGIS'

        assert isinstance(useExistingProcessListMethod, bool), 'useExistingProcessListMethod must be a boolean.'
        if useExistingProcessListMethod:
            assert hasattr(methodMetadata.Class.Object, processListMethodName) and inspect.ismethod(getattr(methodMetadata.Class.Object, processListMethodName)), 'BatchProcessing.GenerateForMethod was called for %s.%s with useExistingProcessListMethod=True, but the specified processListMethodName %s does not exist as a method of class %s.' % (methodMetadata.Class.Name, methodMetadata.Name, processListMethodName, methodMetadata.Class.Name)

        assert processTableMethodName is None or processListMethodName is not None, 'If processTableMethodName is not None, processListMethodName must not be None'
        assert isinstance(processTableMethodName, (str, type(None))), 'processTableMethodName must be a string, or None'

        assert processTableMethodName is None and processTableMethodShortDescription is None or processTableMethodName is not None and processTableMethodShortDescription is not None, 'processTableMethodName and processTableMethodShortDescription must both be None or must both not be None'
        assert isinstance(processTableMethodName, (str, type(None))), 'processTableMethodName must be a string, or None'

        assert (processTableMethodName is None or len(methodMetadata.Results) <= 0 or (derivedResultsForArcGIS is not None and len(derivedResultsForArcGIS) == len(methodMetadata.Results))) and resultFieldDescriptions is None or (processTableMethodName is not None and len(methodMetadata.Results) > 0 and (derivedResultsForArcGIS is None or len(derivedResultsForArcGIS) < len(methodMetadata.Results))) and resultFieldDescriptions is not None, 'resultFieldDescriptions must be provided, and may only be provided, when processTableMethodName is not None and the non-batch method returns one or more results (that are not in derivedResultsForArcGIS)'
        assert isinstance(resultFieldDescriptions, (list, type(None))), 'resultFieldDescriptions must be a Python list, or None'
        if resultFieldDescriptions is not None:
            assert len(resultFieldDescriptions) == len(methodMetadata.Results), 'The length of resultFieldDescriptions must be equal to the number of results returned by the non-batch method'
            for element in resultFieldDescriptions:
                assert isinstance(element, str), 'All of the elements of resultFieldDescriptions must be strings'

        if outputParamNames is not None:
            assert isinstance(skipExistingDescription, (str, type(None))), 'skipExistingDescription must be a string or None when outputParamNames is provided'
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                assert isinstance(overwriteExistingDescription, str), 'overwriteExistingDescription must be a string when the method has an OverwriteExisting argument'

        assert processArcGISTableMethodName is None or processTableMethodName is not None, 'If processArcGISTableMethodName is not None, processTableMethodName must not be None'
        assert isinstance(processArcGISTableMethodName, (str, type(None))), 'processArcGISTableMethodName must be a string, or None'

        assert processArcGISTableMethodName is None and processArcGISTableMethodArcGISDisplayName is None or processArcGISTableMethodName is not None and processArcGISTableMethodArcGISDisplayName is not None, 'processArcGISTableMethodName and processArcGISTableMethodArcGISDisplayName must both be None or must both not be None'
        assert isinstance(processArcGISTableMethodArcGISDisplayName, (str, type(None))), 'processArcGISTableMethodArcGISDisplayName must be a string, or None'

        assert processArcGISTableMethodName is None and methodMetadata.ArcGISToolCategory is None or processArcGISTableMethodName is not None and methodMetadata.ArcGISToolCategory is not None, 'processArcGISTableMethodName and methodMetadata.ArcGISToolCategory must both be None or must both not be None'

        assert processArcGISTableMethodName is None and inputParamFieldArcGISDisplayNames is None or processArcGISTableMethodName is not None and inputParamFieldArcGISDisplayNames is not None, 'processArcGISTableMethodName and inputParamFieldArcGISDisplayNames must both be None or must both not be None'
        assert isinstance(inputParamFieldArcGISDisplayNames, (list, type(None))), 'inputParamFieldArcGISDisplayNames must be a Python list, or None'
        if inputParamFieldArcGISDisplayNames is not None:
            for name in inputParamFieldArcGISDisplayNames:
                assert isinstance(name, str), 'All elements of inputParamFieldArcGISDisplayNames must be strings'

        assert isinstance(outputParamFieldArcGISDisplayNames, (list, type(None))), 'outputParamFieldArcGISDisplayNames must be a Python list, or None'
        if outputParamFieldArcGISDisplayNames is not None:
            for name in outputParamFieldArcGISDisplayNames:
                assert isinstance(name, str), 'All elements of outputParamFieldArcGISDisplayNames must be strings'

        if processArcGISTableMethodName is not None and constantParamNames is not None:
            for i in range(len(constantParamNames)):
                argMetadata = methodMetadata.GetArgumentByName(constantParamNames[i])
                assert argMetadata.ArcGISDisplayName is not None, 'For %s.%s to be exposed as a "process table" batch processing method, %s must have an ArcGISDisplayName' % (argMetadata.Method.Class.Name, argMetadata.Method.Name, argMetadata.Name)

        assert isinstance(resultFieldArcGISDisplayNames, (list, type(None))), 'resultFieldArcGISDisplayNames must be a Python list, or None'
        if resultFieldArcGISDisplayNames is not None:
            assert resultFieldDescriptions is not None and len(resultFieldArcGISDisplayNames) == len(resultFieldDescriptions), 'resultFieldArcGISDisplayNames must be the same length as resultFieldDescriptions'
            for name in resultFieldArcGISDisplayNames:
                assert isinstance(name, str), 'All elements of resultFieldArcGISDisplayNames must be strings'

        assert isinstance(derivedResultsForArcGIS, (list, type(None))), 'derivedResultsForArcGIS must be a Python list, or None'
        if derivedResultsForArcGIS is not None:
            for name in derivedResultsForArcGIS:
                assert isinstance(name, str), 'All elements of derivedResultsForArcGIS must be strings'
                assert methodMetadata.GetResultByName(name) is not None, 'The name %s appeared in the derivedResultsForArcGIS list but %s.%s does not have a ResultMetadata for that name.' % (name, argMetadata.Method.Class.Name, argMetadata.Method.Name)

        # Still need "find and process" method validation:
        # - findMethod is a method with metadata
        # - findMethod has 1 mandatory arg and the rest are optional with defaults
        # - outputLocationTypeMetadata is a StoredObjectTypeMetadata
        # - outputParamExpressionArcGISDisplayNames

        # Determine if the basePath argument is needed for the method that we
        # will generate.
        
        needsBasePathArg = False
        for name in inputParamNames:
            argMetadata = methodMetadata.GetArgumentByName(name)
            if isinstance(argMetadata.Type, StoredObjectTypeMetadata) and argMetadata.Type.CanBeRelativePath:
                needsBasePathArg = True
                break
        if not needsBasePathArg:
            for name in outputParamNames:
                argMetadata = methodMetadata.GetArgumentByName(name)
                if isinstance(argMetadata.Type, StoredObjectTypeMetadata) and argMetadata.Type.CanBeRelativePath:
                    needsBasePathArg = True
                    break

        assert not needsBasePathArg or constantParamNames is None or 'basePath' not in constantParamNames, 'A batch processing method cannot be generated for %s.%s because that method has an argument named basePath that appears in the constantParamNames list. Please rename this argument to something different so the batch processing infrastructure can use that argument name.' % (methodMetadata.Class.Name, methodMetadata.Name)
    
        # Create the "process list" method, which takes inputs and outputs
        # from lists and returns a list.

        if processListMethodName is not None:
            cls._GenerateProcessListMethod(methodMetadata,
                                           inputParamNames,
                                           inputParamDescriptions,
                                           outputParamNames,
                                           outputParamDescriptions,
                                           constantParamNames,
                                           newConstantParamDefaults,
                                           derivedResultsForArcGIS,
                                           processListMethodName,
                                           processListMethodShortDescription,
                                           processListMethodResultDescription,
                                           useExistingProcessListMethod,
                                           skipExistingDescription,
                                           overwriteExistingDescription,
                                           needsBasePathArg)
    
        # Create the "process table" method, which takes inputs and outputs
        # from table fields and stores results in other fields.

        if processTableMethodName is not None:
            cls._GenerateProcessTableMethod(methodMetadata,
                                            inputParamNames,
                                            inputParamDescriptions,
                                            outputParamNames,
                                            outputParamDescriptions,
                                            constantParamNames,
                                            newConstantParamDefaults,
                                            resultFieldDescriptions,
                                            derivedResultsForArcGIS,
                                            processListMethodName,
                                            processTableMethodName,
                                            processTableMethodShortDescription,
                                            skipExistingDescription,
                                            overwriteExistingDescription,
                                            needsBasePathArg)
    
        # Create the "process ArcGIS table" method, which takes inputs and
        # outputs from table fields and stores results in other fields. This
        # method differs from the one above in that it requires ArcGIS and
        # accepts an ArcGIS-style path to a table.

        if processArcGISTableMethodName is not None:
            cls._GenerateProcessArcGISTableMethod(methodMetadata,
                                                  inputParamNames,
                                                  inputParamFieldArcGISDisplayNames,
                                                  inputParamDescriptions,
                                                  outputParamNames,
                                                  outputParamFieldArcGISDisplayNames,
                                                  outputParamDescriptions,
                                                  constantParamNames,
                                                  newConstantParamDefaults,
                                                  resultFieldArcGISDisplayNames,
                                                  resultFieldDescriptions,
                                                  derivedResultsForArcGIS,
                                                  processTableMethodName,
                                                  processTableMethodShortDescription,
                                                  processArcGISTableMethodName,
                                                  processArcGISTableMethodArcGISDisplayName,
                                                  skipExistingDescription,
                                                  overwriteExistingDescription,
                                                  needsBasePathArg)
    
        # Create the "find and process" method, which takes inputs from a find
        # method and calculates outputs from expressions.

        if findAndProcessMethodName is not None:
            cls._GenerateFindAndProcessMethod(methodMetadata,
                                              inputParamNames,
                                              outputParamNames,
                                              outputParamExpressionArcGISDisplayNames,
                                              outputParamExpressionDescriptions,
                                              outputParamDefaultExpressions,
                                              constantParamNames,
                                              newConstantParamDefaults,
                                              derivedResultsForArcGIS,
                                              processTableMethodName,
                                              findAndProcessMethodName,
                                              findAndProcessMethodArcGISDisplayName,
                                              findAndProcessMethodShortDescription,
                                              findMethod,
                                              findOutputFieldParams,
                                              findAdditionalParams,
                                              newFindAdditionalParamDefaults,
                                              outputLocationTypeMetadata,
                                              outputLocationParamDescription,
                                              outputLocationParamArcGISDisplayName,
                                              calculateFieldMethod,
                                              calculateFieldExpressionParam,
                                              calculateFieldAdditionalParams,
                                              calculateFieldAdditionalParamsDefaults,
                                              calculateFieldHiddenParams,
                                              calculateFieldHiddenParamValues,
                                              calculatedOutputsArcGISCategory,
                                              constantParamsToOmitFromFindAndProcessMethod,
                                              skipExistingDescription,
                                              overwriteExistingDescription)

    @classmethod
    def _GenerateProcessListMethod(cls,
                                   methodMetadata,
                                   inputParamNames,
                                   inputParamDescriptions,
                                   outputParamNames,
                                   outputParamDescriptions,
                                   constantParamNames,
                                   newConstantParamDefaults,
                                   derivedResultsForArcGIS,
                                   processListMethodName,
                                   processListMethodShortDescription,
                                   processListMethodResultDescription,
                                   useExistingProcessListMethod,
                                   skipExistingDescription,
                                   overwriteExistingDescription,
                                   needsBasePathArg):

        if methodMetadata.IsInstanceMethod:
            selfName = 'self'
        else:
            selfName = 'cls'

        # If the caller did not provide an existing process list
        # method, add one to the class.

        if not useExistingProcessListMethod:

            # Generate the method source code, starting with the def
            # declaration.

            source = 'def %s(%s' % (processListMethodName, selfName)

            # Append the method input, output, and constant parameters in
            # their original order. Input and output parameters are lists now;
            # constant parameters keep the same data type.

            for argMetadata in methodMetadata.Arguments[1:]:

                if argMetadata.Name in inputParamNames:
                    source += ', ' + argMetadata.Name + 'List'
                    if argMetadata.HasDefault:
                        source += '=None'

                elif outputParamNames is not None and argMetadata.Name in outputParamNames:
                    source += ', ' + argMetadata.Name + 'List'
                    if argMetadata.HasDefault:
                        source += '=None'

                elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                    source += ', ' + argMetadata.Name
                    if newConstantParamDefaults is not None and argMetadata.Name in newConstantParamDefaults:
                        source += '=' + repr(newConstantParamDefaults[argMetadata.Name])
                    elif argMetadata.HasDefault:
                        source += '=' + repr(argMetadata.Default)

            # Append batch processing parameters.

            if outputParamNames is not None:
                if skipExistingDescription is not None:
                    source += ', skipExisting=False'
                    
                argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
                if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                    source += ', overwriteExisting=False'

            if needsBasePathArg:
                source += ', basePath=None'

            source += '):\n'
            source += '    %s.__doc__.Obj.ValidateMethodInvocation()\n' % selfName
            source += '    from GeoEco.BatchProcessing import BatchProcessing\n'
            source += '    from %s import %s\n' % (methodMetadata.Class.Module.Name, methodMetadata.Class.Name)
            source += '    return BatchProcessing.ExecuteProcessListMethod(%s.%s, %s.%s.__doc__.Obj, locals(), %r, %r, %r, %r)\n' % (selfName, methodMetadata.Name, methodMetadata.Class.Name, methodMetadata.Name, inputParamNames, outputParamNames, constantParamNames, derivedResultsForArcGIS)

            # Compile the method and add it to the class.

            code = compile(source, '<string>', 'exec')
            tempNamespace = {}
            exec(code, methodMetadata.Class.Object.__dict__.copy(), tempNamespace)
            if methodMetadata.IsInstanceMethod:
                setattr(methodMetadata.Class.Object, processListMethodName, tempNamespace[processListMethodName])
            else:
                setattr(methodMetadata.Class.Object, processListMethodName, classmethod(tempNamespace[processListMethodName]))

        # Add the method's metadata to the class.

        AddMethodMetadata(processListMethodName, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                          shortDescription=processListMethodShortDescription,
                          longDescription=methodMetadata.LongDescription,
                          dependencies=methodMetadata.Dependencies)

        # Add the cls or self parameter.

        CopyArgumentMetadata(methodMetadata.Object, selfName, processListMethodName, selfName, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # Add the method input, output, and constant parameters in their
        # original order. Input and output parameters are lists; constant
        # parameters keep the same data type.

        for argMetadata in methodMetadata.Arguments[1:]:

            if argMetadata.Name in inputParamNames:
                i = inputParamNames.index(argMetadata.Name)

                # If the batch processing method will have a basePath argument
                # and the argument we are presently constructing is a stored
                # object that can have a relative path, set the
                # BasePathArgument property.

                elementTypeMetadata = copy.deepcopy(argMetadata.Type)

                if needsBasePathArg and isinstance(elementTypeMetadata, StoredObjectTypeMetadata) and elementTypeMetadata.CanBeRelativePath:
                    elementTypeMetadata.BasePathArgument = 'basePath'

                # Add the argument metadata. For efficiency, we set the
                # ListTypeMetadata maxItemsToValidate argument to 0. This
                # means the list elements will not be validated when the batch
                # processing method itself is called. Each element will be
                # validated individually when the method we are batching is
                # called on it.

                AddArgumentMetadata(processListMethodName, argMetadata.Name + 'List', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=ListTypeMetadata(elementType=elementTypeMetadata, canBeNone=argMetadata.HasDefault, maxItemsToValidate=0),
                                    description=inputParamDescriptions[i] % _('List of'),
                                    dependencies=argMetadata.Dependencies)

            elif outputParamNames is not None and argMetadata.Name in outputParamNames:
                i = outputParamNames.index(argMetadata.Name)

                # If the batch processing method will have a basePath argument
                # and the argument we are presently constructing is a stored
                # object that can have a relative path, set the
                # BasePathArgument property.

                elementTypeMetadata = copy.deepcopy(argMetadata.Type)

                if needsBasePathArg and isinstance(elementTypeMetadata, StoredObjectTypeMetadata) and elementTypeMetadata.CanBeRelativePath:
                    elementTypeMetadata.BasePathArgument = 'basePath'

                # Add the argument metadata. For efficiency, we set the
                # ListTypeMetadata maxItemsToValidate argument to 0. This
                # means the list elements will not be validated when the batch
                # processing method itself is called. Each element will be
                # validated individually when the method we are batching is
                # called on it.
                
                AddArgumentMetadata(processListMethodName, argMetadata.Name + 'List', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=ListTypeMetadata(elementType=elementTypeMetadata, canBeNone=argMetadata.HasDefault, maxItemsToValidate=0),
                                    description=outputParamDescriptions[i] % _('List of'),
                                    dependencies=argMetadata.Dependencies)

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                CopyArgumentMetadata(methodMetadata.Object, argMetadata.Name, processListMethodName, argMetadata.Name, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # If the non-batch method has one or more output parameters, add the
        # skipExisting parameter to the batch processing method. Also add the
        # overwriteExisting parameter if the non-batch method has it.

        if outputParamNames is not None:
            if skipExistingDescription is not None:
                AddArgumentMetadata(processListMethodName, 'skipExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=skipExistingDescription)

            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                AddArgumentMetadata(processListMethodName, 'overwriteExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=overwriteExistingDescription,
                                    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

        # If the non-batch method has one or more input or output parameters
        # that can be base paths, add the basePath parameter to the batch
        # processing method.

        if needsBasePathArg:        
            AddArgumentMetadata(processListMethodName, 'basePath', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                typeMetadata=StoredObjectTypeMetadata(typeDisplayName=_('path'), canBeRelativePath=False, useArcGISWorkspace=False, canBeNone=True),
                                description=_(
"""Base path to prepend to relative paths.

If any of the input paths (or output paths, if this method has outputs)
contained in the lists are relative paths, they will be converted to absolute
paths prior to processing, as follows:

* If a base path is provided, it will be prepended to the relative path.

* Otherwise, if the ArcGIS geoprocessor has been initialized and the
  geoprocessing workspace has been set (i.e. ``arcpy.env.Workspace`` is not
  and empty string or None), it will be prepended to the relative path.

* Otherwise, the current working directory for the executing process will be
  prepended to the path.

"""))

        # If the non-batch method does not return any results, neither does
        # the batch processing method. If it returns a single result, the
        # batch processing method returns a list of that type. If it returns
        # multiple results, the batch processing method returns a list of
        # tuples of arbitrary objects. In this last case, it would be nice if
        # our metadata allows us to describe each of the objects in the tuple,
        # but I consider that to be overkill at this time.
        #
        # If the non-batch method has any output parameters, the batch
        # processing method will have a skipExisting parameter. In this case,
        # the results canBeNone option must be set to True, because no results
        # will be provided for outputs that are skipped.

        results = []
        for resultMetadata in methodMetadata.Results:
            if derivedResultsForArcGIS is None or resultMetadata.Name not in derivedResultsForArcGIS:
                results.append(resultMetadata)

        if len(results) == 1:
            elementTypeMetadata = copy.deepcopy(results[0].Type)
            elementTypeMetadata.CanBeNone = elementTypeMetadata.CanBeNone or outputParamNames is not None
            AddResultMetadata(processListMethodName, results[0].Name + 'List', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                              typeMetadata=ListTypeMetadata(elementType=elementTypeMetadata),
                              description=processListMethodResultDescription)
            
        elif len(results) > 1:
            for resultMetadata in results:
                resultTypeMetadata = copy.deepcopy(resultMetadata.Type)
                AddResultMetadata(processListMethodName, 'resultsList', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                  typeMetadata=ListTypeMetadata(elementType=TupleTypeMetadata(elementTypeMetadata=AnyObjectTypeMetadata(canBeNone=True), canBeNone=outputParamNames is not None)),
                                  description=processListMethodResultDescription)

    @classmethod
    def ExecuteProcessListMethod(cls, boundMethod, methodMetadata, methodLocals, inputParamNames, outputParamNames, constantParamNames, derivedResultsForArcGIS):

        # Validate the lists are all the same length.

        numRows = len(methodLocals[inputParamNames[0] + 'List'])

        for name in inputParamNames[1:]:
            name = name + 'List'
            if methodLocals[name] is not None:
                if len(methodLocals[name]) != numRows:
                    Logger.RaiseException(ValueError(_('%(list1)s must have the same number of elements as %(list2)s.') % {'list1': name, 'list2': inputParamNames[0] + 'List'}))
            else:
                methodLocals[name] = [methodMetadata.GetArgumentByName(name).Default] * numRows

        if outputParamNames is not None:
            for name in outputParamNames:
                name = name + 'List'
                if methodLocals[name] is not None:
                    if len(methodLocals[name]) != numRows:
                        Logger.RaiseException(ValueError(_('%(list1)s must have the same number of elements as %(list2)s.') % {'list1': name, 'list2': outputParamNames[0] + 'List'}))
                else:
                    methodLocals[name] = [methodMetadata.GetArgumentByName(name).Default] * numRows

        # Return immediately if the input lists are empty.

        hasResults = len(methodMetadata.Results) > 0 and (derivedResultsForArcGIS is None or len(methodMetadata.Results) > len(derivedResultsForArcGIS))

        if numRows <= 0:
            if len(inputParamNames) > 1:
                Logger.Info(_('The input lists are empty; no work needs to be done.'))
            else:
                Logger.Info(_('The list of inputs is empty; no work needs to be done.'))

            if hasResults:
                return []
            else:
                return None

        # Build a dictionary that maps unique inputs to outputs. Most callers
        # will provide lists of inputs that contain no duplicate combinations,
        # but we can handle the situation where the same combination of inputs
        # is used to produce more than one combination of outputs. (For
        # example the same input file is copied to multiple output files.)

        if len(inputParamNames) > 1:
            Logger.Debug(_('Enumerating the unique input combinations in the lists of inputs...'))
        else:
            Logger.Debug(_('Enumerating the unique values in the list of inputs...'))

        inputsToOutputs = {}
        outputsToInputs = {}
        warnedAboutDuplicateRows = False

        for row in range(numRows):

            # Create a list and a key for this combination of inputs.
            
            inputCombo = []
            for i in range(len(inputParamNames)):
                inputCombo.append(methodLocals[inputParamNames[i] + 'List'][row])
            key = ';'.join(map(str, inputCombo))

            # Create a list for this combination of outputs, if any. Also
            # validate that each output is not being produced by multiple
            # input combinations.

            if outputParamNames is not None:
                outputCombo = []
                for i in range(len(outputParamNames)):
                    output = methodLocals[outputParamNames[i] + 'List'][row]
                    outputCombo.append(output)
                    if output is not None:
                        if output not in outputsToInputs:
                            outputsToInputs[output] = [key, outputParamNames[i] + 'List', row]
                        elif outputsToInputs[output][0] != key:
                            if len(inputParamNames) == 1:
                                Logger.RaiseException(ValueError(_('The same output %(output)s is specified for two different inputs: %(val1)s and %(val2)s (elements #%(i1)i and #%(i1)i of %(list)s, where 0 is the first element). This is not allowed because when the second input was processed, it would overwrite the output of the first one. This problem usually occurs when the outputs are paths or names calculated by a Python expression that produces the same result for two different inputs. If you received this error message after invoking a tool or function that calculates outputs using Python expressions, you must adjust the expressions. The default expressions are usually sufficient for a variety of situations but they may not be suited to your inputs.') % {'output': output, 'list': inputParamNames[0] + 'List', 'val1': outputsToInputs[output][0], 'i1': outputsToInputs[output][2], 'val2': key, 'i2': row}))
                            else:
                                Logger.RaiseException(ValueError(_('The same output %(output)s is specified for two different input combinations: combinations #%(i1)i and #%(i2)i (where 0 is the first combination in the input lists). This is not allowed because when the second input combination was processed, it would overwrite the output of the first one. This problem usually occurs when the outputs are paths or names calculated by a Python expression that produces the same result for two different input combinations. If you received this error message after invoking a tool or function that calculates outputs using Python expressions, you must adjust the expressions. The default expressions are usually sufficient for a variety of situations but they may not be suited to your inputs.') % {'output': output, 'i1': outputsToInputs[output][2], 'i2': row}))
                        elif outputsToInputs[output][1] != outputParamNames[i] + 'List':
                            if len(inputParamNames) == 1:
                                Logger.RaiseException(ValueError(_('For element %(i)i of %(list)s, where 0 is the first element in the list, the same output %(output)s appears in both %(list1)s and %(list2)s. This is not allowed.') % {'i': row, 'list1': inputParamNames[0] + 'List', 'output': output, 'list1': outputsToInputs[output][1], 'list2': outputParamNames[i] + 'List'}))
                            else:
                                Logger.RaiseException(ValueError(_('For input combination #%(i)i, where 0 is the first combination in the input lists, the same output %(output)s appears in both %(list1)s and %(list2)s. This is not allowed.') % {'i': row, 'output': output, 'list1': outputsToInputs[output][1], 'list2': outputParamNames[i] + 'List'}))

            # If we do not have this combination of inputs in our dictionary,
            # add it. The value is a list with these elements:
            #
            #     0 - List of output combinations (if any) that should be
            #         written when this input combination is processed
            #
            #     1 - Set to True when this input has been processed.
            #
            #     2 - Result returned when this input combination was processed.
            #         If no result was returned, this will be None.

            if key not in inputsToOutputs:
                if outputParamNames is not None:
                    inputsToOutputs[key] = [[outputCombo], False, None]
                else:
                    inputsToOutputs[key] = [None, False, None]

            # If we do have this combination of inputs in our dictionary,
            # check to see if we already have this combination of outputs. If
            # we do, warn the caller that they provided the same input/output
            # combination twice. If we do not, it means this input combination
            # should be written to multiple output combinations, and we should
            # add this to our list.

            else:
                isDuplicate = True
                if outputParamNames is not None:
                    outputsList = inputsToOutputs[key][0]
                    for i in range(len(outputsList)):
                        isDuplicate = True
                        for j in range(len(outputParamNames)):
                            if outputsList[i][j] != outputCombo[j]:
                                isDuplicate = False
                                break
                        if isDuplicate:
                            break
                    if not isDuplicate:
                        inputsToOutputs[key][0].append(outputCombo)
                if isDuplicate and not warnedAboutDuplicateRows:
                    if outputParamNames is not None:
                        Logger.Warning(_('The lists of inputs and outputs include duplicate input/output combinations. Duplicate combinations will be ignored.'))
                    else:
                        if len(inputParamNames) > 1:
                            Logger.Warning(_('The lists of inputs include duplicate input combinations. Duplicate combinations will be ignored.'))
                        else:
                            Logger.Warning(_('The list of inputs includes duplicate values. Duplicate values will be ignored.'))
                    warnedAboutDuplicateRows = True

        # Skip outputs that already exist, if requested.

        inputsSkipped = 0
        if outputParamNames is not None and 'skipExisting' in methodLocals and methodLocals['skipExisting']:
            if len(inputParamNames) > 1:
                Logger.Info(_('Checking for existing outputs for each input combination...'))
            else:
                Logger.Info(_('Checking for existing outputs for each input...'))

            # First, for efficiency, build a list of existence-checking
            # functions from the output parameter type metadata.

            existenceFunctions = []
            for name in outputParamNames:
                existenceFunctions.append(methodMetadata.GetArgumentByName(name).Type.Exists)

            # Now walk through the dictionary that maps input combinations to
            # output combinations.

            if len(inputParamNames) > 1:
                progressReporter = ProgressReporter(progressMessage1=_('Still checking for existing outputs: %(elapsed)s elapsed, %(opsCompleted)i input combinations checked, %(perOp)s per combination, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                    completionMessage=_('Finished checking for existing outputs: %(elapsed)s elapsed, %(opsCompleted)i input combinations checked, %(perOp)s per combination.'))
            else:
                progressReporter = ProgressReporter(progressMessage1=_('Still checking for existing outputs: %(elapsed)s elapsed, %(opsCompleted)i inputs checked, %(perOp)s per input, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                    completionMessage=_('Finished checking for existing outputs: %(elapsed)s elapsed, %(opsCompleted)i inputs checked, %(perOp)s per input.'))
                
            progressReporter.Start(len(inputsToOutputs))
            
            for (key, value) in list(inputsToOutputs.items()):

                # For this input combination, walk through all the output
                # combinations. Normally there will be just one. Delete any
                # output combinations where ALL outputs exist. If any outputs
                # in a given combination do not exist, we have to produce all
                # of the outputs for that combination again.
                
                outputsList = value[0]
                skippedOutputsList = []
                
                i = 0
                while i < len(outputsList):
                    allOutputsExist = True
                    for j in range(len(outputParamNames)):
                        if outputsList[i][j] is not None:
                            (exists, correctType) = existenceFunctions[i](outputsList[i][j])
                            if not exists:
                                allOutputsExist = False
                                break
                            if not correctType:
                                if len(inputParamNames) > 1:
                                    Logger.RaiseException(ValueError(_('The output %(output)s specified for input combination [%(input)s] already exists but it is not a %(type)s, so it cannot be accepted as a valid output. Please delete this object yourself or remove it from your list of outputs.') % {'input': key, 'output': outputsList[i][j], 'type': methodMetadata.GetArgumentByName(outputParamNames[j]).Type.TypeDisplayName}))
                                else:
                                    Logger.RaiseException(ValueError(_('The output %(output)s specified for input %(input)s already exists but it is not a %(type)s, so it cannot be accepted as a valid output. Please delete this object yourself or remove it from your list of outputs.') % {'input': key, 'output': outputsList[i][j], 'type': methodMetadata.GetArgumentByName(outputParamNames[j]).Type.TypeDisplayName}))

                    if allOutputsExist:
                        skippedOutputsList.append(outputsList.pop(i))
                    else:
                        i += 1

                # If we deleted all of the output combinations for this input
                # combination, then it does not need to be processed. Remove
                # it from the list of input combinations to process.
                
                if len(outputsList) <= 0:
                    if len(inputParamNames) > 1:
                        if len(skippedOutputsList) == 1 and len(skippedOutputsList[0]) == 1:
                            Logger.Debug(_('Skipping input combination [%(input)s]; the output %(output)s already exists.') % {'input': key, 'output': skippedOutputsList[0][0]})
                        else:
                            Logger.Debug(_('Skipping input combination [%(input)s]; all of the outputs %(output)r already exist.') % {'input': key, 'output': skippedOutputsList})
                    else:
                        if len(skippedOutputsList) == 1 and len(skippedOutputsList[0]) == 1:
                            Logger.Debug(_('Skipping input %(input)s; the output %(output)s already exists.') % {'input': key, 'output': skippedOutputsList[0][0]})
                        else:
                            Logger.Debug(_('Skipping input %(input)s; all of the outputs %(output)r already exist.') % {'input': key, 'output': skippedOutputsList})
                        
                    del inputsToOutputs[key]
                    inputsSkipped += 1

                progressReporter.ReportProgress()                

        # Return immediately if all outputs already exist.

        if inputsSkipped > 0:
            if len(inputsToOutputs) <= 0:
                if len(inputParamNames) > 1:
                    Logger.Info(_('Skipping processing of all %i input combinations because all of their outputs already exist. No work needs to be done.'), inputsSkipped)
                else:
                    Logger.Info(_('Skipping processing of all %i inputs because all of their outputs already exist. No work needs to be done.'), inputsSkipped)

                if hasResults:
                    return [None] * numRows
                else:
                    return None

            # Otherwise log a message saying how many inputs we skipped.
            
            if len(inputParamNames) > 1:
                Logger.Info(_('Skipping %i input combinations because their outputs already exist.'), inputsSkipped)
            else:
                Logger.Info(_('Skipping %i inputs because their outputs already exist.'), inputsSkipped)

        # To process the inputs, we are going to invoke the not-batched method
        # by passing in a tuple of arguments. Build a list which will be used
        # to generate the tuple every time we invoke the method.

        argList = []
        argsToGet = []

        for arg in methodMetadata.Arguments[1:]:
            if arg.Name in inputParamNames or outputParamNames is not None and arg.Name in outputParamNames:
                argList.append(None)
                argsToGet.append(arg.Name + 'List')
            elif constantParamNames is not None and arg.Name in constantParamNames or arg.Name.lower() == 'overwriteexisting' and isinstance(arg.Type, BooleanTypeMetadata) and arg.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                argList.append(methodLocals[arg.Name])
                argsToGet.append(None)
            else:
                argList.append(arg.Default)
                argsToGet.append(None)

        # If the method's metadata says it returns a result, allocate a list
        # that will hold the result for each row in the input lists.

        if hasResults:
            results = []
        else:
            results = None

        # Process the remaining inputs, in the order they were passed in.
        
        if len(inputParamNames) > 1:
            Logger.Info(_('Processing %i input combinations...'), len(inputsToOutputs))
        else:
            Logger.Info(_('Processing %i inputs...'), len(inputsToOutputs))

        if len(inputParamNames) > 1:
            progressReporter = ProgressReporter(progressMessage1=_('Progress report: %(elapsed)s elapsed, %(opsCompleted)i input combinations processed, %(perOp)s per combination, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                completionMessage=_('Processing complete: %(elapsed)s elapsed, %(opsCompleted)i input combinations processed, %(perOp)s per combination.'))
        else:
            progressReporter = ProgressReporter(progressMessage1=_('Progress report: %(elapsed)s elapsed, %(opsCompleted)i inputs processed, %(perOp)s per input, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                completionMessage=_('Processing complete: %(elapsed)s elapsed, %(opsCompleted)i inputs processed, %(perOp)s per input.'))

        progressReporter.Start(len(inputsToOutputs))

        for row in range(numRows):

            # Create a list and a key for this combination of inputs.
            
            inputCombo = []
            for i in range(len(inputParamNames)):
                inputCombo.append(methodLocals[inputParamNames[i] + 'List'][row])
            key = ';'.join(map(str, inputCombo))

            # If this input combination is not in the list of inputs to
            # process, it was removed because its outputs already exist. Just
            # append None for its result (if the method's metadata says it
            # returns a result). If the caller needs to obtain the result, he
            # must pass False for skipExisting, which will cause all inputs to
            # be processed.

            if key not in inputsToOutputs:
                if results is not None:
                    results.append(None)

            # Otherwise, if this input combination has already been processed,
            # just append its result (if the method's metadata says it returns
            # a result).

            elif inputsToOutputs[key][1]:
                if results is not None:
                    results.append(inputsToOutputs[key][2])

            # Otherwise process this input.

            else:

                # Get the arg values.

                for i in range(len(argsToGet)):
                    if argsToGet[i] is not None:
                        argList[i] = methodLocals[argsToGet[i]][row]

                # Call the method, capture its result, and append it to the
                # list of results to return (if the method's metadata says it
                # returns a result). Also cache it in case the combination of
                # inputs appears again.

                Logger.Debug(_('Invoking %s%s...'), boundMethod, repr(tuple(argList)))

                result = boundMethod(*tuple(argList))

                inputsToOutputs[key][1] = True
                
                if results is not None:

                    # Strip any results that are just "derived outputs"
                    # intended for ArcGIS.
                    
                    if derivedResultsForArcGIS is not None:
                        newResult = []
                        for i in range(len(methodMetadata.Results)):
                            if methodMetadata.Results[i].Name not in derivedResultsForArcGIS:
                                newResult.append(result[i])
                        result = tuple(newResult)

                    # Append the result to the list to return.
                        
                    results.append(result)
                    inputsToOutputs[key][2] = result

                # The method wrote the first output(s) listed for this input
                # combination. If additional outputs are listed, indicating
                # that the caller wanted the same output written to multiple
                # places, copy the first output(s) to the remaining outputs.

                if outputParamNames is not None:
                    outputsList = inputsToOutputs[key][0]
                    for i in range(1, len(outputsList)):
                        for j in range(len(outputParamNames)):
                            destValue = outputsList[i][j]
                            typeMetadata = methodMetadata.GetArgumentByName(outputParamNames[j]).Type
                            valueChanged, destValue = typeMetadata.ValidateValue(destValue, 'output')
                            typeMetadata.Copy(outputsList[0][j], destValue, overwriteExisting='overwriteExisting' in methodLocals and methodLocals['overwriteExisting'])

                progressReporter.ReportProgress()                            

        # Return successfully.

        return results        
        
    @classmethod
    def _GenerateProcessTableMethod(cls,
                                    methodMetadata,
                                    inputParamNames,
                                    inputParamDescriptions,
                                    outputParamNames,
                                    outputParamDescriptions,
                                    constantParamNames,
                                    newConstantParamDefaults,
                                    resultFieldDescriptions,
                                    derivedResultsForArcGIS,
                                    processListMethodName,
                                    processTableMethodName,
                                    processTableMethodShortDescription,
                                    skipExistingDescription,
                                    overwriteExistingDescription,
                                    needsBasePathArg):

        # Generate the method source code, starting with the def declaration
        # and the table parameter.

        if methodMetadata.IsInstanceMethod:
            selfName = 'self'
        else:
            selfName = 'cls'

        source = 'def %s(%s, table' % (processTableMethodName, selfName)

        # Append the method input, output, and constant parameters in their
        # original order. Input and output parameters are table fields now;
        # constant parameters keep the same data type.

        for argMetadata in methodMetadata.Arguments[1:]:

            if argMetadata.Name in inputParamNames:
                source += ', ' + argMetadata.Name + 'Field'
                if argMetadata.HasDefault:
                    source += '=None'

            elif outputParamNames is not None and argMetadata.Name in outputParamNames:
                source += ', ' + argMetadata.Name + 'Field'
                if argMetadata.HasDefault:
                    source += '=None'

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                source += ', ' + argMetadata.Name
                if newConstantParamDefaults is not None and argMetadata.Name in newConstantParamDefaults:
                    source += '=' + repr(newConstantParamDefaults[argMetadata.Name])
                elif argMetadata.HasDefault:
                    source += '=' + repr(argMetadata.Default)

        # Append the result parameters as table fields.

        for resultMetadata in methodMetadata.Results:
            if derivedResultsForArcGIS is None or resultMetadata.Name not in derivedResultsForArcGIS:
                source += ', ' + resultMetadata.Name + 'Field=None'

        # Append batch processing parameters

        source += ', where=None, orderBy=None'

        if outputParamNames is not None:
            if skipExistingDescription is not None:
                source += ', skipExisting=False'
                
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                source += ', overwriteExisting=False'

        if needsBasePathArg:
            source += ', basePath=None'

        # Append the method body.

        source += '):\n'
        source += '    %s.__doc__.Obj.ValidateMethodInvocation()\n' % selfName
        source += '    from GeoEco.BatchProcessing import BatchProcessing\n'
        source += '    from %s import %s\n' % (methodMetadata.Class.Module.Name, methodMetadata.Class.Name)
        source += '    BatchProcessing.ExecuteProcessTableMethod(%s.%s, %s.%s.__doc__.Obj, locals(), %r, %r, %r, %r)\n' % (selfName, processListMethodName, methodMetadata.Class.Name, methodMetadata.Name, inputParamNames, outputParamNames, constantParamNames, derivedResultsForArcGIS)

        # Compile the method and add it to the class.

        code = compile(source, '<string>', 'exec')
        tempNamespace = {}
        exec(code, methodMetadata.Class.Object.__dict__.copy(), tempNamespace)
        if methodMetadata.IsInstanceMethod:
            setattr(methodMetadata.Class.Object, processTableMethodName, tempNamespace[processTableMethodName])
        else:
            setattr(methodMetadata.Class.Object, processTableMethodName, classmethod(tempNamespace[processTableMethodName]))

        # Add the method's metadata to the class.

        AddMethodMetadata(processTableMethodName, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                          shortDescription=processTableMethodShortDescription,
                          longDescription=methodMetadata.LongDescription,
                          dependencies=methodMetadata.Dependencies)

        # Add the cls or self parameter.

        CopyArgumentMetadata(methodMetadata.Object, selfName, processTableMethodName, selfName, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # Add the table parameter.

        from .Datasets import Table

        AddArgumentMetadata(processTableMethodName, 'table', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                            typeMetadata=ClassInstanceTypeMetadata(cls=Table),
                            description=_('Table to query.'))

        # Add the method input, output, and constant parameters in
        # their original order. Input and output parameters are table
        # fields; constant parameters keep the same data type.

        for argMetadata in methodMetadata.Arguments[1:]:
            if argMetadata.Name in inputParamNames:
                i = inputParamNames.index(argMetadata.Name)
                AddArgumentMetadata(processTableMethodName, argMetadata.Name + 'Field', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=UnicodeStringTypeMetadata(canBeNone=argMetadata.HasDefault),
                                    description=inputParamDescriptions[i] % _('Field containing the'),
                                    dependencies=argMetadata.Dependencies)

            elif outputParamNames is not None and argMetadata.Name in outputParamNames:
                i = outputParamNames.index(argMetadata.Name)
                AddArgumentMetadata(processTableMethodName, argMetadata.Name + 'Field', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=UnicodeStringTypeMetadata(canBeNone=argMetadata.HasDefault),
                                    description=outputParamDescriptions[i] % _('Field containing the'),
                                    dependencies=argMetadata.Dependencies)

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                CopyArgumentMetadata(methodMetadata.Object, argMetadata.Name, processTableMethodName, argMetadata.Name, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # Add the results as table fields.

        for i in range(len(methodMetadata.Results)):
            if derivedResultsForArcGIS is None or methodMetadata.Results[i].Name not in derivedResultsForArcGIS:
                AddArgumentMetadata(processTableMethodName, methodMetadata.Results[i].Name + 'Field', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
                                    description=resultFieldDescriptions[i])

        # Add the where and orderBy parameters.

        from .Datasets import Table

        CopyArgumentMetadata(Table.OpenSelectCursor, 'where', processTableMethodName, 'where', fromClass=Table, fromModule=Table.__doc__.Obj.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)
        CopyArgumentMetadata(Table.OpenSelectCursor, 'orderBy', processTableMethodName, 'orderBy', fromClass=Table, fromModule=Table.__doc__.Obj.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # If the non-batch method has one or more output parameters, add the
        # skipExisting parameter to the batch processing method. Also add the
        # overwriteExisting parameter if the non-batch method has it.

        if outputParamNames is not None:
            if skipExistingDescription is not None:
                AddArgumentMetadata(processTableMethodName, 'skipExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=skipExistingDescription)

            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                AddArgumentMetadata(processTableMethodName, 'overwriteExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=overwriteExistingDescription,
                                    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

        # If the non-batch method has one or more input or output parameters
        # that can be base paths, add the basePath parameter to the batch
        # processing method.

        if needsBasePathArg:        
            AddArgumentMetadata(processTableMethodName, 'basePath', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                typeMetadata=StoredObjectTypeMetadata(typeDisplayName=_('path'), canBeRelativePath=False, useArcGISWorkspace=False, canBeNone=True),
                                description=_(
"""Base path to prepend to relative paths.

If any of the input paths (or output paths, if this method has
outputs) obtained from the table are relative paths, they will be
converted to absolute paths prior to processing, as follows:

* If a base path is provided, it will be prepended to the relative
  path.

* Otherwise, if the ArcGIS geoprocessor has been initialized and the
  geoprocessing workspace has been set (i.e. the Workspace property of
  the geoprocessor is not empty), it will be prepended to the relative
  path.

* Otherwise, the current working directory for the executing process
  will be prepended to the path. If you have not explicitly changed
  the working directory, it is usually the directory that contains the
  Python interpreter (e.g., on Windows computers, it would be
  C:\\\\Python24, if yo're running Python 2.4).

"""))

    @classmethod
    def ExecuteProcessTableMethod(cls, boundProcessListMethod, methodMetadata, methodLocals, inputParamNames, outputParamNames, constantParamNames, derivedResultsForArcGIS, additionalRequiredParamNames=None, additionalOptionalParamNames=None):

        # Validate that the table and fields specified by the caller all exist.

        table = methodLocals['table']
        inputFields = []
        outputFields = []
        resultFields = []

        for name in inputParamNames:
            param = name + 'Field'
            field = methodLocals[param]
            if field is not None and table.GetFieldByName(field) is None:
                Logger.RaiseException(ValueError(_('The field "%(field)s" provided for the %(param)s parameter does not exist in the table %(table)s. Please provide the name of an existing field.') % {'table': table, 'field': field, 'param': param}))
            inputFields.append(field)

        if outputParamNames is not None:
            for name in outputParamNames:
                param = name + 'Field'
                field = methodLocals[param]
                if field is not None and table.GetFieldByName(field) is None:
                    Logger.RaiseException(ValueError(_('The field "%(field)s" provided for the %(param)s parameter does not exist in the table %(table)s. Please provide the name of an existing field.') % {'table': table, 'field': field, 'param': param}))
                outputFields.append(field)
                
        firstResultParam = None
        for resultMetadata in methodMetadata.Results:
            if derivedResultsForArcGIS is None or resultMetadata.Name not in derivedResultsForArcGIS:
                param = resultMetadata.Name + 'Field'
                field = methodLocals[param]
                if field is not None:
                    if firstResultParam is None:
                        firstResultParam = param
                    if table.GetFieldByName(field) is None:
                        Logger.RaiseException(ValueError(_('The field "%(field)s" provided for the %(param)s parameter does not exist in the table %(table)s. Please provide the name of an existing field.') % {'table': table, 'field': field, 'param': param}))
                    resultFields.append(field)
                else:
                    resultFields.append(None)

        # If the caller specified any result fields, verify that this kind of
        # table supports update cursors.

        if firstResultParam is not None and table.TestCapability('UpdateCursor') is not None:
            Logger.RaiseException(ValueError(_('A value was provided for the %(param)s parameter but the provided table does not support UPDATE cursors. You must omit this parameter or provide a table that does support UPDATE cursors.') % {'param': firstResultParam}))

        # Open a SELECT cursor and read the fields into parallel lists.

        if len(outputFields) > 0:
            Logger.Info(_('Querying the table "%(table)s" to build lists of inputs and outputs...') % {'table': table})
        elif len(inputFields) > 1:
            Logger.Info(_('Querying the table "%(table)s" to build lists of inputs...') % {'table': table})
        else:
            Logger.Info(_('Querying the table "%(table)s" to build a list of inputs...') % {'table': table})

        inputLists = []
        for i in range(len(inputFields)):           # Note: DO NOT use this syntax: inputLists = [[]] * len(inputFields)
            inputLists.append([])

        outputLists = []
        for i in range(len(outputFields)):          # Note: DO NOT use this syntax: outputLists = [[]] * len(outputLists)
            outputLists.append([])

        cursor = table.OpenSelectCursor(where=methodLocals['where'], orderBy=methodLocals['orderBy'])
        try:
            while cursor.NextRow():
                for i in range(len(inputFields)):
                    if inputFields[i] is not None:
                        inputLists[i].append(cursor.GetValue(inputFields[i]))
                    else:
                        inputLists[i].append(None)
                for i in range(len(outputFields)):
                    if outputFields[i] is not None:
                        outputLists[i].append(cursor.GetValue(outputFields[i]))
                    else:
                        outputLists[i].append(None)
        finally:
            del cursor

        # Determine if the basePath argument should be passed to the "process
        # list" method.
        
        needsBasePathArg = False
        for name in inputParamNames:
            argMetadata = methodMetadata.GetArgumentByName(name)
            if isinstance(argMetadata.Type, StoredObjectTypeMetadata) and argMetadata.Type.CanBeRelativePath:
                needsBasePathArg = True
                break
        if not needsBasePathArg and outputParamNames is not None:
            for name in outputParamNames:
                argMetadata = methodMetadata.GetArgumentByName(name)
                if isinstance(argMetadata.Type, StoredObjectTypeMetadata) and argMetadata.Type.CanBeRelativePath:
                    needsBasePathArg = True
                    break

        # Call the "process list" method to do the processing.

        argList = []
        optionalArgCount = 0

        for argMetadata in methodMetadata.Arguments[1:]:
            if argMetadata.HasDefault:
                optionalArgCount += 1
            if optionalArgCount == 1 and additionalRequiredParamNames is not None:
                for name in additionalRequiredParamNames:
                    argList.append(methodLocals[name])

            if argMetadata.Name in inputParamNames:
                i = inputParamNames.index(argMetadata.Name)
                argList.append(inputLists[i])

            elif outputParamNames is not None and argMetadata.Name in outputParamNames:                
                i = outputParamNames.index(argMetadata.Name)
                argList.append(outputLists[i])

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                argList.append(methodLocals[argMetadata.Name])

        if optionalArgCount <= 0 and additionalRequiredParamNames is not None:
            for name in additionalRequiredParamNames:
                argList.append(methodLocals[name])

        if additionalOptionalParamNames is not None:
            for name in additionalOptionalParamNames:
                argList.append(methodLocals[name])

        if len(outputFields) > 0:
            if 'skipExisting' in methodLocals:
                argList.append(methodLocals['skipExisting'])
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                argList.append(methodLocals['overwriteExisting'])

        if needsBasePathArg:
            argList.append(methodLocals['basePath'])

        import reprlib
        r = reprlib.Repr()
        r.maxlist = 3
        r.maxstring = 1024
        r.maxother = 1024

        Logger.Debug(_('Invoking %s(%s)...'), boundProcessListMethod, ', '.join(map(r.repr, argList)))       # Can't convert argList to a tuple and invoke r.repr on it due to Python bug 1734723

        results = boundProcessListMethod(*tuple(argList))

        # If the caller specified any result fields, open an UPDATE cursor and
        # update them.

        if firstResultParam is not None:
            Logger.Info(_('Updating the table "%(table)s" with the processing results...') % {'table': table})

            numElements = len(inputLists[0])
            listIndex = 0
            rowCount = len(results)
            cursor = table.OpenUpdateCursor(where=methodLocals['where'], orderBy=methodLocals['orderBy'], rowCount=rowCount)
            try:
                while cursor.NextRow():

                    # Get the values of the inputs and outputs from this row.

                    rowInputs = []
                    for field in inputFields:
                        if field is not None:
                            rowInputs.append(cursor.GetValue(field))
                        else:
                            rowInputs.append(None)
                    
                    rowOutputs = []
                    for field in outputFields:
                        if field is not None:
                            rowOutputs.append(cursor.GetValue(field))
                        else:
                            rowOutputs.append(None)

                    # It is unlikely, but the database may have changed in the
                    # time that has passed since we opened the SELECT cursor.
                    # We cannot assume that the exact same rows will be
                    # returned. We will only update the rows that exist right
                    # now. Search our lists until we find the input/output
                    # combination that matches the values we just got from the
                    # database.

                    found = False
                    elementsChecked = 0
                    while elementsChecked < numElements:
                        found = True
                        for i in range(len(inputFields)):
                            if inputLists[i][listIndex] != rowInputs[i]:
                                found = False
                                break
                        if found and len(outputFields) > 0:
                            for i in range(len(outputFields)):
                                if outputLists[i][listIndex] != rowOutputs[i]:
                                    found = False
                                    break
                        if found:
                            break
                        elementsChecked += 1
                        listIndex += 1
                        if listIndex == numElements:
                            listIndex = 0

                    # If we did not find this database row in our input/output
                    # lists, continue on to the next row.

                    if not found:
                        rowCount += 1
                        cursor.SetRowCount(rowCount)
                        continue

                    # We found the row. Update the row unless we suspect that
                    # the output was skipped, in which case we don't want to
                    # overwrite the existing result value(s).

                    if len(resultFields) == 1:
                        if results[listIndex] is not None or outputParamNames is None or 'skipExisting' not in methodLocals or not methodLocals['skipExisting']:
                            cursor.SetValue(resultFields[0], results[listIndex])
                            cursor.UpdateRow()
                    else:
                        if results[listIndex] is not None:
                            for i in len(list(range(resultFields))):
                                if resultFields[i] is not None:
                                    cursor.SetValue(resultFields[i], results[listIndex][i])
                            cursor.UpdateRow()
            finally:
                del cursor
        
    @classmethod
    def _GenerateProcessArcGISTableMethod(cls,
                                          methodMetadata,
                                          inputParamNames,
                                          inputParamFieldArcGISDisplayNames,
                                          inputParamDescriptions,
                                          outputParamNames,
                                          outputParamFieldArcGISDisplayNames,
                                          outputParamDescriptions,
                                          constantParamNames,
                                          newConstantParamDefaults,
                                          resultFieldArcGISDisplayNames,
                                          resultFieldDescriptions,
                                          derivedResultsForArcGIS,
                                          processTableMethodName,
                                          processTableMethodShortDescription,
                                          processArcGISTableMethodName,
                                          processArcGISTableMethodArcGISDisplayName,
                                          skipExistingDescription,
                                          overwriteExistingDescription,
                                          needsBasePathArg):

        # Generate the method source code, starting with the def
        # declaration and the table parameter.

        if methodMetadata.IsInstanceMethod:
            selfName = 'self'
        else:
            selfName = 'cls'

        source = 'def %s(%s, table' % (processArcGISTableMethodName, selfName)

        # Append the method input, output, and constant parameters in
        # their original order. Input and output parameters are table
        # fields now; constant parameters keep the same data type.

        for argMetadata in methodMetadata.Arguments[1:]:

            if argMetadata.Name in inputParamNames:
                source += ', ' + argMetadata.Name + 'Field'
                if argMetadata.HasDefault:
                    source += '=None'

            elif outputParamNames is not None and argMetadata.Name in outputParamNames:
                source += ', ' + argMetadata.Name + 'Field'
                if argMetadata.HasDefault:
                    source += '=None'

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                source += ', ' + argMetadata.Name
                if newConstantParamDefaults is not None and argMetadata.Name in newConstantParamDefaults:
                    source += '=' + repr(newConstantParamDefaults[argMetadata.Name])
                elif argMetadata.HasDefault:
                    source += '=' + repr(argMetadata.Default)

        # Append the result parameters as table fields.

        for resultMetadata in methodMetadata.Results:
            if derivedResultsForArcGIS is None or resultMetadata.Name not in derivedResultsForArcGIS:
                source += ', ' + resultMetadata.Name + 'Field=None'

        # Append batch processing parameters.

        source += ', where=None, orderBy=None'

        if outputParamNames is not None:
            if skipExistingDescription is not None:
                source += ', skipExisting=False'
                
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                source += ', overwriteExisting=False'

        if needsBasePathArg:
            source += ', basePath=None'

        # Append the method body.

        source += '):\n'
        source += '    %s.__doc__.Obj.ValidateMethodInvocation()\n' % selfName
        source += '    from GeoEco.Datasets.ArcGIS import ArcGISTable\n'
        source += '    tableObj = ArcGISTable(table)\n'
        source += '    from GeoEco.BatchProcessing import BatchProcessing\n'
        source += '    from %s import %s\n' % (methodMetadata.Class.Module.Name, methodMetadata.Class.Name)
        source += '    return BatchProcessing.ExecuteProcessArcGISTableMethod(%s.%s, %s.%s.__doc__.Obj, locals(), %r, %r, %r, %r, %r)\n' % (selfName, processTableMethodName, methodMetadata.Class.Name, methodMetadata.Name, inputParamNames, outputParamNames, constantParamNames, derivedResultsForArcGIS, skipExistingDescription)

        # Compile the method and add it to the class.

        code = compile(source, '<string>', 'exec')
        tempNamespace = {}
        exec(code, methodMetadata.Class.Object.__dict__.copy(), tempNamespace)
        if methodMetadata.IsInstanceMethod:
            setattr(methodMetadata.Class.Object, processArcGISTableMethodName, tempNamespace[processArcGISTableMethodName])
        else:
            setattr(methodMetadata.Class.Object, processArcGISTableMethodName, classmethod(tempNamespace[processArcGISTableMethodName]))

        # If the method does not already have an ArcGISDependency in its list of
        # dependencies, add one now.

        dependencies = copy.deepcopy(methodMetadata.Dependencies)
        found = False
        for dependency in dependencies:
            if isinstance(dependency, ArcGISDependency):
                found = True
                break
        if not found:
            dependencies.append(ArcGISDependency())

        # Add the method's metadata to the class.

        AddMethodMetadata(processArcGISTableMethodName, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                          shortDescription=processTableMethodShortDescription,
                          longDescription=methodMetadata.LongDescription,
                          isExposedAsArcGISTool=True,
                          arcGISDisplayName=processArcGISTableMethodArcGISDisplayName,
                          arcGISToolCategory=methodMetadata.ArcGISToolCategory,
                          dependencies=dependencies)

        # Add the cls or self parameter.

        CopyArgumentMetadata(methodMetadata.Object, selfName, processArcGISTableMethodName, selfName, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # Add the table parameter.

        AddArgumentMetadata(processArcGISTableMethodName, 'table', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                            typeMetadata=ArcGISTableViewTypeMetadata(mustExist=True),
                            description=_('Table to query.'),
                            arcGISDisplayName=_('Table'))

        # Add the method input, output, and constant parameters in
        # their original order. Input and output parameters are table
        # fields; constant parameters keep the same data type.

        for argMetadata in methodMetadata.Arguments[1:]:

            allowedFieldTypes = None
            if isinstance(argMetadata.Type, IntegerTypeMetadata):
                allowedFieldTypes = ['SHORT', 'LONG']
            elif isinstance(argMetadata.Type, FloatTypeMetadata):
                allowedFieldTypes = ['FLOAT', 'DOUBLE']
            elif isinstance(argMetadata.Type, UnicodeStringTypeMetadata):
                allowedFieldTypes = ['TEXT']
            elif isinstance(argMetadata.Type, DateTimeTypeMetadata):
                allowedFieldTypes = ['DATE']

            if argMetadata.Name in inputParamNames:
                i = inputParamNames.index(argMetadata.Name)
                AddArgumentMetadata(processArcGISTableMethodName, argMetadata.Name + 'Field', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=ArcGISFieldTypeMetadata(canBeNone=argMetadata.HasDefault, allowedFieldTypes=allowedFieldTypes),
                                    description=inputParamDescriptions[i] % _('Field containing the'),
                                    arcGISDisplayName=inputParamFieldArcGISDisplayNames[i],
                                    arcGISCategory=argMetadata.ArcGISCategory,
                                    arcGISParameterDependencies=['table'],
                                    dependencies=argMetadata.Dependencies)

            elif outputParamNames is not None and argMetadata.Name in outputParamNames:
                i = outputParamNames.index(argMetadata.Name)
                AddArgumentMetadata(processArcGISTableMethodName, argMetadata.Name + 'Field', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=ArcGISFieldTypeMetadata(canBeNone=argMetadata.HasDefault, allowedFieldTypes=allowedFieldTypes),
                                    description=outputParamDescriptions[i] % _('Field containing the'),
                                    arcGISDisplayName=outputParamFieldArcGISDisplayNames[i],
                                    arcGISCategory=argMetadata.ArcGISCategory,
                                    arcGISParameterDependencies=['table'],
                                    dependencies=argMetadata.Dependencies)

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                AddArgumentMetadata(processArcGISTableMethodName, argMetadata.Name, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=argMetadata.Type,
                                    description=argMetadata.Description,
                                    arcGISDisplayName=argMetadata.ArcGISDisplayName,
                                    arcGISCategory=argMetadata.ArcGISCategory,
                                    dependencies=argMetadata.Dependencies)

        # Add the results as table fields.

        i = 0
        
        for resultMetadata in methodMetadata.Results:
            if derivedResultsForArcGIS is not None and resultMetadata.Name in derivedResultsForArcGIS:
                continue

            allowedFieldTypes = None
            if isinstance(resultMetadata.Type, IntegerTypeMetadata):
                allowedFieldTypes = ['SHORT', 'LONG']
            elif isinstance(resultMetadata.Type, FloatTypeMetadata):
                allowedFieldTypes = ['FLOAT', 'DOUBLE']
            elif isinstance(resultMetadata.Type, UnicodeStringTypeMetadata):
                allowedFieldTypes = ['TEXT']
            elif isinstance(resultMetadata.Type, DateTimeTypeMetadata):
                allowedFieldTypes = ['DATE']

            AddArgumentMetadata(processArcGISTableMethodName, resultMetadata.Name + 'Field', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                typeMetadata=ArcGISFieldTypeMetadata(canBeNone=True, allowedFieldTypes=allowedFieldTypes),
                                description=resultFieldDescriptions[i],
                                arcGISDisplayName=resultFieldArcGISDisplayNames[i],
                                arcGISParameterDependencies=['table'])

            i += 1

        # Add the where and orderBy parameters.

        from .Datasets import Table

        argMetadata = Table.OpenSelectCursor.__doc__.Obj.GetArgumentByName('where')
        AddArgumentMetadata(processArcGISTableMethodName, argMetadata.Name, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                            typeMetadata=SQLWhereClauseTypeMetadata(canBeNone=True),
                            description=argMetadata.Description,
                            arcGISDisplayName=_('Where clause'),
                            arcGISCategory=_('Batch processing options'),
                            arcGISParameterDependencies=['table'],
                            dependencies=argMetadata.Dependencies)

        argMetadata = Table.OpenSelectCursor.__doc__.Obj.GetArgumentByName('orderBy')
        AddArgumentMetadata(processArcGISTableMethodName, argMetadata.Name, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                            typeMetadata=argMetadata.Type,
                            description=argMetadata.Description,
                            arcGISDisplayName=_('Order by'),
                            arcGISCategory=_('Batch processing options'),
                            arcGISParameterDependencies=['table'],
                            dependencies=argMetadata.Dependencies)

        # If the non-batch method has one or more output parameters, add the
        # skipExisting parameter to the batch processing method. Also add the
        # overwriteExisting parameter if the non-batch method has it.

        if outputParamNames is not None:
            if skipExistingDescription is not None:
                AddArgumentMetadata(processArcGISTableMethodName, 'skipExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=skipExistingDescription,
                                    arcGISDisplayName=_('Skip existing outputs'),
                                    arcGISCategory=_('Batch processing options'))

            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                AddArgumentMetadata(processArcGISTableMethodName, 'overwriteExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=overwriteExistingDescription,
                                    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

        # If the non-batch method has one or more input or output parameters
        # that can be base paths, add the basePath parameter to the batch
        # processing method.

        if needsBasePathArg:        
            AddArgumentMetadata(processArcGISTableMethodName, 'basePath', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                typeMetadata=ArcGISWorkspaceTypeMetadata(canBeRelativePath=False, useArcGISWorkspace=False, canBeNone=True),
                                description=_(
"""Base path to prepend to relative paths.

If a base path is provided, it will be prepended to any relative paths
that are obtained from the fields that list the inputs (and outputs,
if this tool has outputs). If a base path is not provided, the
workspace containing the table will be prepended instead."""),
                                arcGISDisplayName=_('Base path'),
                                arcGISCategory=_('Batch processing options'))

        # If one or more of the method's results is designated as a
        # derived result for ArcGIS, copy these results from the
        # non-batch method. This will cause them to be created as
        # derived output parameters of the geoprocessing tool, which
        # the ArcGIS documentation says should be used when a tool
        # changes, but does not create, an input dataset.
        
        if derivedResultsForArcGIS is not None and len(derivedResultsForArcGIS) > 0:
            for derivedResult in derivedResultsForArcGIS:
                CopyResultMetadata(methodMetadata.Object, derivedResult, processArcGISTableMethodName, derivedResult, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # Otherwise add the table as result with a dependency on the
        # input parameter, so it will be created as a derived output
        # parameter.

        else:
            AddResultMetadata(processArcGISTableMethodName, 'outputTable', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                typeMetadata=ArcGISTableViewTypeMetadata(),
                description=_('Processed table.'),
                arcGISDisplayName=_('Processed table'),
                arcGISParameterDependencies=['table'])

    @classmethod
    def ExecuteProcessArcGISTableMethod(cls, boundProcessTableMethod, methodMetadata, methodLocals, inputParamNames, outputParamNames, constantParamNames, derivedResultsForArcGIS, skipExistingDescription):

        # Determine if the basePath argument should be passed to the "process
        # table" method.
        
        needsBasePathArg = False
        for name in inputParamNames:
            argMetadata = methodMetadata.GetArgumentByName(name)
            if isinstance(argMetadata.Type, StoredObjectTypeMetadata) and argMetadata.Type.CanBeRelativePath:
                needsBasePathArg = True
                break
        if not needsBasePathArg:
            for name in outputParamNames:
                argMetadata = methodMetadata.GetArgumentByName(name)
                if isinstance(argMetadata.Type, StoredObjectTypeMetadata) and argMetadata.Type.CanBeRelativePath:
                    needsBasePathArg = True
                    break

        # Call the "process table" method to do the processing.

        argList = [methodLocals['tableObj']]

        for argMetadata in methodMetadata.Arguments[1:]:

            if argMetadata.Name in inputParamNames or outputParamNames is not None and argMetadata.Name in outputParamNames:
                argList.append(methodLocals[argMetadata.Name + 'Field'])

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                argList.append(methodLocals[argMetadata.Name])

        for resultMetadata in methodMetadata.Results:
            if derivedResultsForArcGIS is None or resultMetadata.Name not in derivedResultsForArcGIS:
                argList.append(methodLocals[resultMetadata.Name + 'Field'])

        argList.append(methodLocals['where'])
        argList.append(methodLocals['orderBy'])

        if outputParamNames is not None:
            if skipExistingDescription is not None:
                argList.append(methodLocals['skipExisting'])
                
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                argList.append(methodLocals['overwriteExisting'])

        if needsBasePathArg:
            if methodLocals['basePath'] is not None:
                argList.append(methodLocals['basePath'])
            else:
                argList.append(os.path.dirname(methodLocals['table']))

        import reprlib
        r = reprlib.Repr()
        r.maxlist = 3
        r.maxstring = 1024
        r.maxother = 1024

        Logger.Debug(_('Invoking %s(%s)...'), boundProcessTableMethod, ', '.join(map(r.repr, argList)))       # Can't convert argList to a tuple and invoke r.repr on it due to Python bug 1734723

        boundProcessTableMethod(*tuple(argList))

        # If one or more of the method's results is designated as a
        # derived result for ArcGIS return these. Otherwise return the
        # input table.

        if derivedResultsForArcGIS is not None and len(derivedResultsForArcGIS) > 0:
            results = []
            for derivedResult in derivedResultsForArcGIS:
                results.append(methodLocals[methodMetadata.GetResultByName(derivedResult).ArcGISParameterDependencies[0]])
            return tuple(results)

        else:
            return methodLocals['table']
        
    @classmethod
    def _GenerateFindAndProcessMethod(cls,
                                      methodMetadata,
                                      inputParamNames,
                                      outputParamNames,
                                      outputParamExpressionArcGISDisplayNames,
                                      outputParamExpressionDescriptions,
                                      outputParamDefaultExpressions,
                                      constantParamNames,
                                      newConstantParamDefaults,
                                      derivedResultsForArcGIS,
                                      processTableMethodName,
                                      findAndProcessMethodName,
                                      findAndProcessMethodArcGISDisplayName,
                                      findAndProcessMethodShortDescription,
                                      findMethod,
                                      findOutputFieldParams,
                                      findAdditionalParams,
                                      newFindAdditionalParamDefaults,
                                      outputLocationTypeMetadata,
                                      outputLocationParamDescription,
                                      outputLocationParamArcGISDisplayName,
                                      calculateFieldMethod,
                                      calculateFieldExpressionParam,
                                      calculateFieldAdditionalParams,
                                      calculateFieldAdditionalParamsDefaults,
                                      calculateFieldHiddenParams,
                                      calculateFieldHiddenParamValues,                                      
                                      calculatedOutputsArcGISCategory,
                                      constantParamsToOmitFromFindAndProcessMethod,
                                      skipExistingDescription,
                                      overwriteExistingDescription):

        # Generate the method source code.

        if methodMetadata.IsInstanceMethod:
            selfName = 'self'
        else:
            selfName = 'cls'

        findMethodMetadata = findMethod.__doc__.Obj
        inputLocationParamName = 'input' + findMethodMetadata.Arguments[1].Name[0].upper() + findMethodMetadata.Arguments[1].Name[1:]
        source = 'def %s(%s, %s' % (findAndProcessMethodName, selfName, inputLocationParamName)

        outputLocationParamName = None
        if outputParamNames is not None:
            outputLocationParamName = 'output' + ''.join([s[0].upper() + s[1:] for s in outputLocationTypeMetadata.TypeDisplayName.split(' ')])
            source += ', ' + outputLocationParamName

        if constantParamNames is not None and constantParamsToOmitFromFindAndProcessMethod is not None:
            for name in constantParamsToOmitFromFindAndProcessMethod:
                if name in constantParamNames:
                    constantParamNames.remove(name)
            if len(constantParamNames) <= 0:
                constantParamNames = None

        if constantParamNames is not None:
            for name in constantParamNames:
                argMetadata = methodMetadata.GetArgumentByName(name)
                if argMetadata.ArcGISCategory is None:
                    source += ', ' + name
                    if newConstantParamDefaults is not None and argMetadata.Name in newConstantParamDefaults:
                        source += '=' + repr(newConstantParamDefaults[argMetadata.Name])
                    elif argMetadata.HasDefault:
                        source += '=' + repr(argMetadata.Default)

        if findAdditionalParams is not None:
            for name in findAdditionalParams:
                argMetadata = findMethodMetadata.GetArgumentByName(name)
                source += ', ' + argMetadata.Name
                if newFindAdditionalParamDefaults is not None and argMetadata.Name in newFindAdditionalParamDefaults:
                    source += '=' + repr(newFindAdditionalParamDefaults[argMetadata.Name])
                else:
                    source += '=' + repr(argMetadata.Default)

        if constantParamNames is not None:
            for name in constantParamNames:
                argMetadata = methodMetadata.GetArgumentByName(name)
                if argMetadata.ArcGISCategory is not None:
                    source += ', ' + name
                    if newConstantParamDefaults is not None and argMetadata.Name in newConstantParamDefaults:
                        source += '=' + repr(newConstantParamDefaults[argMetadata.Name])
                    elif argMetadata.HasDefault:
                        source += '=' + repr(argMetadata.Default)

        if outputParamNames is not None:
            calculateFieldMethodMetadata = calculateFieldMethod.__doc__.Obj

            for i in range(len(outputParamNames)):
                source += ', ' + outputParamNames[i] + calculateFieldExpressionParam[0].upper() + calculateFieldExpressionParam[1:]
                source += '=' + repr(outputParamDefaultExpressions[i])

            if calculateFieldAdditionalParams is not None:
                for i in range(len(calculateFieldAdditionalParams)):
                    source += ', ' + calculateFieldAdditionalParams[i]
                    source += '=' + repr(calculateFieldAdditionalParamsDefaults[i])

            if skipExistingDescription is not None:
                source += ', skipExisting=False'
                
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                source += ', overwriteExisting=False'

        source += '):\n'
        source += '    %s.__doc__.Obj.ValidateMethodInvocation()\n' % selfName
        source += '    from GeoEco.BatchProcessing import BatchProcessing\n'
        source += '    from %s import %s\n' % (methodMetadata.Class.Module.Name, methodMetadata.Class.Name)
        source += '    from %s import %s\n' % (findMethodMetadata.Class.Module.Name, findMethodMetadata.Class.Name)
        if outputParamNames is not None:
            source += '    from %s import %s\n' % (calculateFieldMethodMetadata.Class.Module.Name, calculateFieldMethodMetadata.Class.Name)
            source += '    return BatchProcessing.ExecuteFindAndProcessMethod(%s.%s, %s.%s.__doc__.Obj, locals(), %r, %r, %r, %r, %r, %r, %r, %s.%s.__doc__.Obj, %r, %r, %s.%s.__doc__.Obj, %r, %r, %r, %r, %r)\n' % (selfName,
                                                                                                                                                                                           processTableMethodName,
                                                                                                                                                                                           methodMetadata.Class.Name,
                                                                                                                                                                                           methodMetadata.Name,
                                                                                                                                                                                           inputParamNames,
                                                                                                                                                                                           inputLocationParamName,
                                                                                                                                                                                           outputParamNames,
                                                                                                                                                                                           outputLocationParamName,
                                                                                                                                                                                           constantParamNames,
                                                                                                                                                                                           constantParamsToOmitFromFindAndProcessMethod,
                                                                                                                                                                                           derivedResultsForArcGIS,
                                                                                                                                                                                           findMethodMetadata.Class.Name,
                                                                                                                                                                                           findMethodMetadata.Name,
                                                                                                                                                                                           findOutputFieldParams,
                                                                                                                                                                                           findAdditionalParams,
                                                                                                                                                                                           calculateFieldMethodMetadata.Class.Name,
                                                                                                                                                                                           calculateFieldMethodMetadata.Name,
                                                                                                                                                                                           calculateFieldExpressionParam,
                                                                                                                                                                                           calculateFieldAdditionalParams,
                                                                                                                                                                                           calculateFieldHiddenParams,
                                                                                                                                                                                           calculateFieldHiddenParamValues,
                                                                                                                                                                                           skipExistingDescription)
        else:
            source += '    return BatchProcessing.ExecuteFindAndProcessMethod(%s.%s, %s.%s.__doc__.Obj, locals(), %r, %r, %r, %r, %r, %r, %r, %s.%s.__doc__.Obj, %r, %r)\n' % (selfName,
                                                                                                                                                        processTableMethodName,
                                                                                                                                                        methodMetadata.Class.Name,
                                                                                                                                                        methodMetadata.Name,
                                                                                                                                                        inputParamNames,
                                                                                                                                                        inputLocationParamName,
                                                                                                                                                        outputParamNames,
                                                                                                                                                        outputLocationParamName,
                                                                                                                                                        constantParamNames,
                                                                                                                                                        constantParamsToOmitFromFindAndProcessMethod,
                                                                                                                                                        derivedResultsForArcGIS,
                                                                                                                                                        findMethodMetadata.Class.Name,
                                                                                                                                                        findMethodMetadata.Name,
                                                                                                                                                        findOutputFieldParams,
                                                                                                                                                        findAdditionalParams)

        # Compile the method and add it to the class.

        code = compile(source, '<string>', 'exec')
        tempNamespace = {}
        exec(code, methodMetadata.Class.Object.__dict__.copy(), tempNamespace)
        if methodMetadata.IsInstanceMethod:
            setattr(methodMetadata.Class.Object, findAndProcessMethodName, tempNamespace[findAndProcessMethodName])
        else:
            setattr(methodMetadata.Class.Object, findAndProcessMethodName, classmethod(tempNamespace[findAndProcessMethodName]))

        # Add the method's metadata to the class.

        AddMethodMetadata(findAndProcessMethodName, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                          shortDescription=findAndProcessMethodShortDescription,
                          longDescription=methodMetadata.LongDescription,
                          isExposedAsArcGISTool=True,
                          arcGISDisplayName=findAndProcessMethodArcGISDisplayName,
                          arcGISToolCategory=methodMetadata.ArcGISToolCategory)

        CopyArgumentMetadata(methodMetadata.Object, selfName, findAndProcessMethodName, selfName, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # Add the input location (e.g. workspace, directory) from the first
        # argument to the Find method.

        AddArgumentMetadata(findAndProcessMethodName, inputLocationParamName, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                            typeMetadata=findMethodMetadata.Arguments[1].Type,
                            description=findMethodMetadata.Arguments[1].Description,
                            arcGISDisplayName=findMethodMetadata.Arguments[1].ArcGISDisplayName)

        # If the non-batch method has one or more output parameters, add the
        # output location parameter.

        if outputParamNames is not None:
            AddArgumentMetadata(findAndProcessMethodName, outputLocationParamName, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                typeMetadata=outputLocationTypeMetadata,
                                description=outputLocationParamDescription,
                                arcGISDisplayName=outputLocationParamArcGISDisplayName)

        # Add the constant parameters that do not have an ArcGIS
        # category. Use their original data type.

        if constantParamNames is not None:
            for i in range(len(constantParamNames)):
                argMetadata = methodMetadata.GetArgumentByName(constantParamNames[i])
                if argMetadata.ArcGISCategory is None:
                    AddArgumentMetadata(findAndProcessMethodName, argMetadata.Name, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                        typeMetadata=argMetadata.Type,
                                        description=argMetadata.Description,
                                        arcGISDisplayName=argMetadata.ArcGISDisplayName,
                                        arcGISCategory=argMetadata.ArcGISCategory,
                                        dependencies=argMetadata.Dependencies)

        # Add the additional Find method parameters.

        if findAdditionalParams is not None:
            for name in findAdditionalParams:
                argMetadata = findMethodMetadata.GetArgumentByName(name)
                CopyArgumentMetadata(findMethodMetadata.Object, argMetadata.Name, findAndProcessMethodName, argMetadata.Name, fromClass=findMethodMetadata.Class.Object, fromModule=findMethodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # Add the constant parameters that do have an ArcGIS category.
        # Use their original data type.

        if constantParamNames is not None:
            for i in range(len(constantParamNames)):
                argMetadata = methodMetadata.GetArgumentByName(constantParamNames[i])
                if argMetadata.ArcGISCategory is not None:
                    AddArgumentMetadata(findAndProcessMethodName, argMetadata.Name, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                        typeMetadata=argMetadata.Type,
                                        description=argMetadata.Description,
                                        arcGISDisplayName=argMetadata.ArcGISDisplayName,
                                        arcGISCategory=argMetadata.ArcGISCategory,
                                        dependencies=argMetadata.Dependencies)

        # If the non-batch method has one or more output parameters, add output
        # expression parameters, the additional calculate field parameters, the
        # skipExisting parameter, and the overwriteExisting parameter if the
        # non-batch method has it.

        if outputParamNames is not None:
            argMetadata = calculateFieldMethodMetadata.GetArgumentByName(calculateFieldExpressionParam)
            typeMetadata = copy.deepcopy(argMetadata.Type)
            typeMetadata.CanBeNone = True
            for i in range(len(outputParamNames)):
                AddArgumentMetadata(findAndProcessMethodName, outputParamNames[i] + calculateFieldExpressionParam[0].upper() + calculateFieldExpressionParam[1:], cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=typeMetadata,
                                    description=outputParamExpressionDescriptions[i],
                                    arcGISDisplayName=outputParamExpressionArcGISDisplayNames[i],
                                    arcGISCategory=calculatedOutputsArcGISCategory,
                                    dependencies=argMetadata.Dependencies)

            for i in range(len(calculateFieldAdditionalParams)):
                argMetadata = calculateFieldMethodMetadata.GetArgumentByName(calculateFieldAdditionalParams[i])
                AddArgumentMetadata(findAndProcessMethodName, argMetadata.Name, cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=argMetadata.Type,
                                    description=argMetadata.Description,
                                    arcGISDisplayName=argMetadata.ArcGISDisplayName,
                                    arcGISCategory=calculatedOutputsArcGISCategory,
                                    dependencies=argMetadata.Dependencies)

            if skipExistingDescription is not None:
                AddArgumentMetadata(findAndProcessMethodName, 'skipExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=skipExistingDescription,
                                    arcGISDisplayName=_('Skip existing outputs'),
                                    arcGISCategory=_('Batch processing options'))
                
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                AddArgumentMetadata(findAndProcessMethodName, 'overwriteExisting', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                                    typeMetadata=BooleanTypeMetadata(),
                                    description=overwriteExistingDescription,
                                    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

        # If one or more of the method's results is designated as a
        # derived result for ArcGIS, copy these results from the
        # non-batch method. This will cause them to be created as
        # derived output parameters of the geoprocessing tool, which
        # the ArcGIS documentation says should be used when a tool
        # changes, but does not create, an input dataset.
        
        if derivedResultsForArcGIS is not None and len(derivedResultsForArcGIS) > 0:
            for derivedResult in derivedResultsForArcGIS:
                CopyResultMetadata(methodMetadata.Object, derivedResult, findAndProcessMethodName, derivedResult, fromClass=methodMetadata.Class.Object, fromModule=methodMetadata.Class.Module.Object, toClass=methodMetadata.Class.Object, toModule=methodMetadata.Class.Module.Object)

        # If the method has outputs, add the output location result
        # with a dependency on the corresponding input parameter, so
        # it will be created as a derived output parameter of the
        # geoprocessing tool.

        if outputParamNames is not None:
            AddResultMetadata(findAndProcessMethodName, 'updated' + outputLocationParamName[0].upper() + outputLocationParamName[1:], cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                              typeMetadata=outputLocationTypeMetadata,
                              description=outputLocationParamDescription,
                              arcGISDisplayName=_('Updated %s') % outputLocationParamArcGISDisplayName,
                              arcGISParameterDependencies=[outputLocationParamName])

        # Otherwise, if there are no results designated as derived
        # results for ArcGIS, add the input location as a result, so
        # the geoprocessing tool will at least have one output.

        elif derivedResultsForArcGIS is None or len(derivedResultsForArcGIS) <= 0:
            AddResultMetadata(findAndProcessMethodName, inputLocationParamName + 'Result', cls=methodMetadata.Class.Object, module=methodMetadata.Class.Module.Object,
                              typeMetadata=findMethodMetadata.Arguments[1].Type,
                              description=findMethodMetadata.Arguments[1].Description,
                              arcGISDisplayName=_('Searched %s') % findMethodMetadata.Arguments[1].Type.TypeDisplayName,
                              arcGISParameterDependencies=[inputLocationParamName])

    @classmethod
    def ExecuteFindAndProcessMethod(cls,
                                    boundProcessTableMethod,
                                    methodMetadata,
                                    methodLocals,
                                    inputParamNames,
                                    inputLocationParamName,
                                    outputParamNames,
                                    outputLocationParamName,
                                    constantParamNames,
                                    constantParamsToOmitFromFindAndProcessMethod,
                                    derivedResultsForArcGIS,
                                    findMethodMetadata,
                                    findOutputFieldParams,
                                    findAdditionalParams,
                                    calculateFieldMethodMetadata=None,
                                    calculateFieldExpressionParam=None,
                                    calculateFieldAdditionalParams=None,
                                    calculateFieldHiddenParams=None,
                                    calculateFieldHiddenParamValues=None,
                                    skipExistingDescription=None):

        # Instantiate an in-memory SQLiteDatabase to hold the table of inputs
        # and outputs.

        from GeoEco.Datasets.SQLite import SQLiteDatabase

        database = SQLiteDatabase(':memory:')

        # Call the find method to populate the inputs' fields.

        inputLocation = methodLocals['input' + findMethodMetadata.Arguments[1].Name[0].upper() + findMethodMetadata.Arguments[1].Name[1:]]
        args = "%s, database, 'work'" % repr(inputLocation)

        for i in range(len(findOutputFieldParams)):
            args += ", %s='%s'" % (findOutputFieldParams[i], inputParamNames[i])

        if findAdditionalParams is not None:
            for i in range(len(findAdditionalParams)):
                args += ', %s=%s' % (findAdditionalParams[i], repr(methodLocals[findAdditionalParams[i]]))

        Logger.Debug(_('Invoking %s(%s)...'), findMethodMetadata.Object, args)

        exec('from %s import %s' % (findMethodMetadata.Class.Module.Name, findMethodMetadata.Class.Name), globals(), sys._getframe().f_locals)
        eval('%s.%s(%s)' % (findMethodMetadata.Class.Name, findMethodMetadata.Name, args), globals(), sys._getframe().f_locals)

        # Add fields for the outputs and calculate them by calling the calculate
        # field method.

        table = database.QueryDatasets("TableName = 'work'", reportProgress=False)[0]

        if outputParamNames is not None:
            for name in outputParamNames:
                table.AddField(name, 'string')
                
                if methodLocals[name + calculateFieldExpressionParam[0].upper() + calculateFieldExpressionParam[1:]] is not None:
                    args = 'table, %r, %s=%r' % (name, calculateFieldExpressionParam, methodLocals[name + calculateFieldExpressionParam[0].upper() + calculateFieldExpressionParam[1:]])

                    if calculateFieldAdditionalParams is not None:
                        for additionalName in calculateFieldAdditionalParams:
                            args += ', %s=%r' % (additionalName, methodLocals[additionalName])

                    if calculateFieldHiddenParams is not None:
                        for i in range(len(calculateFieldHiddenParams)):
                            args += ', %s=%r' % (calculateFieldHiddenParams[i], calculateFieldHiddenParamValues[i])

                    Logger.Debug(_('Invoking %s(%s)...'), calculateFieldMethodMetadata.Object, args)

                    exec('from %s import %s' % (calculateFieldMethodMetadata.Class.Module.Name, calculateFieldMethodMetadata.Class.Name), globals(), sys._getframe().f_locals)
                    eval('%s.%s(%s)' % (calculateFieldMethodMetadata.Class.Name, calculateFieldMethodMetadata.Name, args), globals(), sys._getframe().f_locals)

        # Call the "process table" method to do the processing.

        argList = [table]

        for argMetadata in methodMetadata.Arguments[1:]:

            if argMetadata.Name in inputParamNames:
                i = inputParamNames.index(argMetadata.Name)
                if i < len(findOutputFieldParams):
                    argList.append(argMetadata.Name)
                else:
                    argList.append(None)        # Pass None if this field was not returned by the Find method

            elif outputParamNames is not None and argMetadata.Name in outputParamNames:
                argList.append(argMetadata.Name)

            elif constantParamNames is not None and argMetadata.Name in constantParamNames:
                argList.append(methodLocals[argMetadata.Name])

            elif constantParamsToOmitFromFindAndProcessMethod is not None and argMetadata.Name in constantParamsToOmitFromFindAndProcessMethod:
                argList.append(None)

        for resultMetadata in methodMetadata.Results:           # Pass None for result field name parameters
            argList.append(None)

        argList.append(None)            # Pass None for where parameter

        if len(findOutputFieldParams) > 0:
            argList.append(', '.join([inputParamNames[i] + ' ASC' for i in range(len(findOutputFieldParams))]))       # Construct the orderBy parameter
        else:
            argList.append(None)

        if outputParamNames is not None:
            if skipExistingDescription is not None:
                argList.append(methodLocals['skipExisting'])
                
            argMetadata = methodMetadata.GetArgumentByName('overwriteExisting')
            if argMetadata is not None and isinstance(argMetadata.Type, BooleanTypeMetadata) and argMetadata.InitializeToArcGISGeoprocessorVariable.lower().endswith('overwriteoutput'):
                argList.append(methodLocals['overwriteExisting'])

        from reprlib import Repr
        r = Repr()
        r.maxlist = 3
        r.maxstring = 1024
        r.maxother = 1024

        Logger.Debug(_('Invoking %s(%s)...'), boundProcessTableMethod, ', '.join(map(r.repr, argList)))       # Can't convert argList to a tuple and invoke r.repr on it due to Python bug 1734723

        boundProcessTableMethod(*tuple(argList))

        # If one or more of the method's results is designated as a
        # derived result for ArcGIS, add these to the return list.

        results = []

        if derivedResultsForArcGIS is not None and len(derivedResultsForArcGIS) > 0:
            for derivedResult in derivedResultsForArcGIS:
                results.append(methodLocals[methodMetadata.GetResultByName(derivedResult).ArcGISParameterDependencies[0]])

        # If the method has outputs, add the output location to the
        # return list.

        if outputParamNames is not None:
            results.append(methodLocals[outputLocationParamName])

        # If we haven't added any results to the list, add the input
        # location as a result.

        if len(results) <= 0:
            results.append(methodLocals[inputLocationParamName])

        # Return the results.

        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            return tuple(results)


###############################################################################
# Metadata: module
###############################################################################

AddModuleMetadata(shortDescription=_('Utility classes used by other GeoEco classes to implement batch processing versions of their methods.'))


###############################################################################
# Metadata: BatchProcessing class
###############################################################################

AddClassMetadata(BatchProcessing,
    shortDescription=_('Utility methods used by other GeoEco classes to implement batch processing versions of their methods.'))


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['BatchProcessing']
