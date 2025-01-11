# Metadata.py - Classes used to describe the classes, properties, methods, and
# other entities in the GeoEco Python package.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import copy
from functools import reduce
import inspect
import re
import types
import sys
import xml.dom

from .DynamicDocString import DynamicDocString
from .Internationalization import _


class Metadata(object):
    __doc__ = DynamicDocString()

    def __init__(self, name, shortDescription=None, longDescription=None):
        assert isinstance(name, str), 'The Name property must be a string.'
        self._Name = name.strip()
        self._ShortDescription = None
        self.ShortDescription = shortDescription
        self.LongDescription = longDescription

    def _GetName(self):
        return self._Name
    
    Name = property(_GetName, doc=DynamicDocString())

    def _GetShortDescription(self):
        return self._ShortDescription
    
    def _SetShortDescription(self, value):
        assert isinstance(value, (type(None), str)), 'The ShortDescription property must be a string, or None.'
        if value is not None:
            self._ShortDescription = value.strip()
        else:
            self._ShortDescription = value
        
    ShortDescription = property(_GetShortDescription, _SetShortDescription, doc=DynamicDocString())

    def _GetLongDescription(self):
        return self._LongDescription
    
    def _SetLongDescription(self, value):
        assert isinstance(value, (type(None), str)), 'The LongDescription property must be a string, or None.'
        self._LongDescription = value   # Do not strip LongDescription; it might contain a code block
        
    LongDescription = property(_GetLongDescription, _SetLongDescription, doc=DynamicDocString())

    def _GetObject(self):
        raise NotImplementedError('This metadata does not correspond to a concrete Python object. Because there is no object to be obtained, this method is not implemented.')
    
    def _GetObjectBase(self):
        return self._GetObject()            # This is necessary because Python doesn't allow derived classes to override property fget methods
    
    Object = property(_GetObjectBase, doc=DynamicDocString())

    def _GetDocString(self):
        raise NotImplementedError('This metadata does not correspond to a type of Python object that has a doc string, so this method is not implemented.')
    
    def _GetDocStringBase(self):
        return self._GetDocString()         # This is necessary because Python doesn't allow derived classes to override property fget methods
    
    DocString = property(_GetDocStringBase, doc=DynamicDocString())

    def __str__(self):
        return self.DocString


class ModuleMetadata(Metadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, name=None, shortDescription=None, longDescription=None):

        # If the caller did not provide a module name, use the caller's module
        # name.
        
        if name is None:
            name = str(inspect.getmodule(inspect.currentframe().f_back).__name__)

        super(ModuleMetadata, self).__init__(name, shortDescription, longDescription)
        assert name in sys.modules, 'Module %s must exist.' % name

    def _GetIsExposedToPythonCallers(self):
        for (name, obj) in list(self.Object.__dict__.items()):
            if name != '__doc__' and hasattr(obj, '__doc__') and isinstance(obj.__doc__, DynamicDocString) and hasattr(obj.__doc__.Obj, 'Module') and obj.__doc__.Obj.Module == self and hasattr(obj.__doc__.Obj, 'IsExposedToPythonCallers') and obj.__doc__.Obj.IsExposedToPythonCallers:
                return True
        return False
        
    IsExposedToPythonCallers = property(_GetIsExposedToPythonCallers, doc=DynamicDocString())

    def _GetObject(self):
        return sys.modules[self.Name]

    def _GetDocString(self):
        doc = ''
        if self.ShortDescription is not None:
            doc = doc + self.ShortDescription.strip() + '\n'
        if self.LongDescription is not None:
            if len(doc) > 0:
                doc = doc + '\n'
            doc = doc + self.LongDescription
        if len(doc) <= 0:
            return 'No description available.'
        return doc.rstrip()


class ClassMetadata(Metadata):
    __doc__ = DynamicDocString()
    
    def __init__(self, name, moduleMetadata=None, shortDescription=None, longDescription=None):

        # If the caller did not provide a ModuleMetadata instance for the module
        # that defines this class, assume the class is defined in the caller's
        # module.
        
        if moduleMetadata is None:
            obj = inspect.getmodule(inspect.currentframe().f_back.f_code)
            assert hasattr(obj, '__doc__') and isinstance(obj.__doc__, DynamicDocString) and isinstance(obj.__doc__.Obj, ModuleMetadata), 'In order to describe classes in module %s using %s instances, the __doc__ attribute of %s must be an instance of %s, and the Obj property of that must be an instance of %s.' % (obj.__name__, ClassMetadata.__name__, obj.__name__, DynamicDocString.__name__, ModuleMetadata.__name__)
            moduleMetadata = obj.__doc__.Obj
            
        super(ClassMetadata, self).__init__(name, shortDescription, longDescription)
        assert isinstance(moduleMetadata, ModuleMetadata), 'The Module property must be an instance of %s.' % ModuleMetadata.__name__
        assert name in moduleMetadata.Object.__dict__ and inspect.isclass(moduleMetadata.Object.__dict__[name]), 'Module %s must contain a class named %s.' % (moduleMetadata.Name, name)
        self._Module = moduleMetadata

    def _GetModule(self):
        return self._Module
    
    Module = property(_GetModule, doc=DynamicDocString())

    def _GetIsExposedToPythonCallers(self):
        mro = inspect.getmro(self.Object)
        for mroClass in mro:
            for name in list(mroClass.__dict__.keys()):
                obj = getattr(self.Object, name)
                if name != '__doc__' and hasattr(obj, '__doc__') and isinstance(obj.__doc__, DynamicDocString) and hasattr(obj.__doc__.Obj, 'IsExposedToPythonCallers') and obj.__doc__.Obj.IsExposedToPythonCallers:
                    return True
        return False
        
    IsExposedToPythonCallers = property(_GetIsExposedToPythonCallers, doc=DynamicDocString())

    def _GetObject(self):
        return self.Module.Object.__dict__[self.Name]

    def _GetDocString(self):
        doc = ''
        if self.ShortDescription is not None:
            doc = doc + self.ShortDescription.strip() + '\n'
        if self.LongDescription is not None:
            if len(doc) > 0:
                doc = doc + '\n'
            doc = doc + self.LongDescription
        if len(doc) <= 0:
            return 'No description available.'
        return doc.rstrip()

    def ValidatePropertyAssignment(self):

        # Get the parent stack frame. Make sure we release it in a finally
        # statement, so we do not accidentally create a memory cycle if an
        # exception is raised.

        parentFrame = inspect.currentframe().f_back
        try:

            # Validate that we're being called from the method of a class.
            
            (args, varargs, varkw, _locals) = inspect.getargvalues(parentFrame)
            assert len(args) == 2 and args[0] in _locals and hasattr(_locals[args[0]], parentFrame.f_code.co_name) and inspect.ismethod(getattr(_locals[args[0]], parentFrame.f_code.co_name)) and getattr(_locals[args[0]], parentFrame.f_code.co_name).__func__.__code__ == parentFrame.f_code, 'ValidatePropertyAssignment should only be called from the "fset" method of a property. The method must have exactly two arguments.'
            method = getattr(_locals[args[0]], parentFrame.f_code.co_name)
            if isinstance(method.__self__, type):
                cls = _locals[args[0]]
            else:
                cls = _locals[args[0]].__class__
            assert issubclass(cls, object), 'ValidatePropertyAssignment should only be called from the "fset" method of a property.'

            # Now we need to identify the class's property object that uses
            # the calling method as the "fset" method. Once we have that
            # property object we can use the property's metadata to validate
            # the assigned value.
            #
            # First, determine if the calling method is an instance method or
            # a classmethod.

            methodType = None        
            mro = inspect.getmro(cls)
            for mroClass in mro:
                if method.__name__ in mroClass.__dict__:
                    if isinstance(mroClass.__dict__[method.__name__], classmethod):
                        methodType = classmethod
                    else:
                        methodType = types.MethodType
                    break
            assert methodType is not None, 'Programming error in GeoEco.Metadata.ClassMetadata.ValidatePropertyAssignment: methodType is None. Please contact the authors of GeoEco for assistance.'

            propName = None
            prop = None

            # If the calling method is an instance method, look for the
            # property that has its fset property set to the method object
            # itself.

            if methodType == types.MethodType:
                props = inspect.getmembers(cls, inspect.isdatadescriptor)
                for (name, p) in props:
                    if hasattr(p, 'fset') and isinstance(p.fset, types.FunctionType) and p.fset == method.__func__:
                        propName = name
                        prop = p
                        break

            # If the calling method is a classmethod, we have to look up the
            # classmethod for which the calling method is the implementation.
            # We cannot get this from p.fset.__func__ or anything like that.
            # Any time I try to dereference fset when it is a classmethod,
            # Python just exits.

            else:

                # First find the classmethod for which the calling method is
                # the implementation.

                classmethodForMethod = None
                for mroClass in mro:
                    for key in list(mroClass.__dict__.keys()):
                        if isinstance(mroClass.__dict__[key], classmethod) and getattr(mroClass, key) == method:
                            classmethodForMethod = mroClass.__dict__[key]
                            break
                    if classmethodForMethod is not None:
                        break

                # Now look up the property that has its fset property set to
                # the classmethod object.

                if classmethodForMethod is not None:                
                    props = inspect.getmembers(cls, inspect.isdatadescriptor)
                    for (name, p) in props:
                        if hasattr(p, 'fset') and isinstance(p.fset, classmethod) and p.fset == classmethodForMethod:
                            propName = name
                            prop = p
                            break

            assert propName is not None and prop is not None, 'ValidatePropertyAssignment should only be called from the "fset" method of a property. None of the properties in class %s use method %s for their "fset" method. Please do not call ValidatePropertyAssignment from %s.' % (cls.__name__, method.__name__, method.__name__)

            # Validate that the property's __doc__ attribute contains a
            # DynamicDocString with a PropertyMetadata object inside.
            
            assert isinstance(prop.__doc__, DynamicDocString) and isinstance(prop.__doc__.Obj, PropertyMetadata), 'ValidatePropertyAssignment should only be called from "fset" methods for properties that have their __doc__ attribute set to an instance of DynamicDocString and the Obj property of DynamicDocString set to an instance of PropertyMetadata.'
            propMetadata = prop.__doc__.Obj

            # Validate the value. If the validation code changed the value, assign
            # the local variable in the parent stack frame. I am not entirely sure
            # if this is allowed by Python. At the time of this writing, it did work
            # and I could find no documentation or forum posts forbidding it.

            (valueChanged, newValue) = propMetadata.Type.ValidateValue(_locals[args[1]], '%s property' % (propMetadata.Name))
            if valueChanged:
                parentFrame.f_locals[args[1]] = newValue
                from ._MetadataUtils import SaveChangesToFrameLocals
                SaveChangesToFrameLocals(parentFrame)

            pass
        finally:
            del parentFrame

    _InitializedDependencies = {}

    def ValidateMethodInvocation(self):

        # Get the parent stack frame. Make sure we release it in a finally
        # statement, so we do not accidentally create a memory cycle if an
        # exception is raised.

        parentFrame = inspect.currentframe().f_back
        try:

            # Validate that we're being called from an instancemethod or
            # classmethod. (To validate staticmethod invocations, call
            # ValidateStaticMethodInvocation instead.)
            
            (args, varargs, varkw, _locals) = inspect.getargvalues(parentFrame)
            assert len(args) > 0 and args[0] in _locals and (inspect.isclass(_locals[args[0]]) or hasattr(_locals[args[0]], '__class__')) and hasattr(_locals[args[0]], parentFrame.f_code.co_name) and inspect.ismethod(getattr(_locals[args[0]], parentFrame.f_code.co_name)), 'ValidateMethodInvocation should only be called from instance methods or classmethods.'

            # Traverse up the class hierarchy until we locate the actual method
            # object that we were called from.

            method = None
            if inspect.isclass(_locals[args[0]]):
                mro = inspect.getmro(_locals[args[0]])
            else:
                mro = inspect.getmro(_locals[args[0]].__class__)
            for mroClass in mro:
                if parentFrame.f_code.co_name in mroClass.__dict__:
                    if isinstance(mroClass.__dict__[parentFrame.f_code.co_name], classmethod):
                        if mroClass.__dict__[parentFrame.f_code.co_name].__get__(_locals[args[0]]).__func__.__code__ == parentFrame.f_code:
                            method = mroClass.__dict__[parentFrame.f_code.co_name].__get__(_locals[args[0]])
                    elif inspect.isfunction(mroClass.__dict__[parentFrame.f_code.co_name]) and mroClass.__dict__[parentFrame.f_code.co_name].__code__ == parentFrame.f_code:
                        method = mroClass.__dict__[parentFrame.f_code.co_name]
            assert method is not None, 'ValidateMethodInvocation failed to validate that the calling method is implemented in the first argument\'s class or any of its base classes.'

            # Validate that the method's __doc__ attribute contains a
            # DynamicDocString with a MethodMetadata object inside.

            assert isinstance(method.__doc__, DynamicDocString) and isinstance(method.__doc__.Obj, MethodMetadata), 'ValidateMethodInvocation should only be called instance methods or classmethods that have their __doc__ attribute set to an instance of DynamicDocString and the Obj property of DynamicDocString set to an instance of MethodMetadata.'
            methodMetadata = method.__doc__.Obj

            # Initialize the method's dependencies.
            
            for d in methodMetadata.Dependencies:
                d.Initialize()

            # Validate the value of each argument. The validation code may
            # change the values. Also initialize dependencies for the argument,
            # if needed.

            from ._MetadataUtils import SaveChangesToFrameLocals

            for i in range(len(args)):        
                argMetadata = methodMetadata.Arguments[i]
                (valueChanged, value) = argMetadata.Type.ValidateValue(parentFrame.f_locals[argMetadata.Name], '%s parameter' % argMetadata.Name, parentFrame.f_locals, argMetadata)
                if valueChanged:
                    parentFrame.f_locals[argMetadata.Name] = value
                    SaveChangesToFrameLocals(parentFrame)
                if argMetadata.Type.DependenciesAreNeededForValue(value):
                    for d in argMetadata.Dependencies:
                        d.Initialize()

            i = len(args)
            if varargs is not None:
                argMetadata = methodMetadata.Arguments[i]
                assert argMetadata.Name == varargs
                (valueChanged, value) = argMetadata.Type.ValidateValue(parentFrame.f_locals[argMetadata.Name], '%s parameter' % argMetadata.Name, parentFrame.f_locals, argMetadata)
                if valueChanged:
                    parentFrame.f_locals[argMetadata.Name] = value
                    SaveChangesToFrameLocals(parentFrame)
                i = i + 1
                if argMetadata.Type.DependenciesAreNeededForValue(value):
                    for d in argMetadata.Dependencies:
                        d.Initialize()
                
            if varkw is not None:
                argMetadata = methodMetadata.Arguments[i]
                assert argMetadata.Name == varkw
                (valueChanged, value) = argMetadata.Type.ValidateValue(parentFrame.f_locals[argMetadata.Name], '%s parameter' % argMetadata.Name, parentFrame.f_locals, argMetadata)
                if valueChanged:
                    parentFrame.f_locals[argMetadata.Name] = value
                    SaveChangesToFrameLocals(parentFrame)
                if argMetadata.Type.DependenciesAreNeededForValue(value):
                    for d in argMetadata.Dependencies:
                        d.Initialize()

        finally:
            del parentFrame


class PropertyMetadata(Metadata):
    __doc__ = DynamicDocString()

    def __init__(self, name, classMetadata, typeMetadata, shortDescription=None, longDescription=None, isExposedToPythonCallers=False):
        super(PropertyMetadata, self).__init__(name, shortDescription, longDescription)
        assert isinstance(classMetadata, ClassMetadata), 'classMetadata must be an instance of %s.' % ClassMetadata.__name__
        assert hasattr(classMetadata.Object, name) and isinstance(getattr(classMetadata.Object, name), property), 'Class %s must contain a property named %s.' % (classMetadata.Name, name)
        self._Class = classMetadata
        self.Type = typeMetadata
        self.IsExposedToPythonCallers = isExposedToPythonCallers

    def _GetClass(self):
        return self._Class
    
    Class = property(_GetClass, doc=DynamicDocString())

    def _GetType(self):
        return self._Type
    
    def _SetType(self, value):
        assert isinstance(value, TypeMetadata), 'Type must be an instance of %s.' % TypeMetadata.__name__
        self._Type = value
    
    Type = property(_GetType, _SetType, doc=DynamicDocString())

    def _GetIsExposedToPythonCallers(self):
        return self._IsExposedToPythonCallers

    def _SetIsExposedToPythonCallers(self, value):
        assert isinstance(value, bool), 'IsExposedToPythonCallers must be a boolean.'
        self._IsExposedToPythonCallers = value

    IsExposedToPythonCallers = property(_GetIsExposedToPythonCallers, _SetIsExposedToPythonCallers, doc=DynamicDocString())

    def _GetIsReadOnly(self):
        return self.Object.fset is None

    IsReadOnly = property(_GetIsReadOnly, doc=DynamicDocString())

    def _GetObject(self):
        return getattr(self.Class.Object, self.Name)

    def _GetDocString(self):
        doc = '(%s or :py:data:`None`)' % self.Type.SphinxMarkup if self.Type.CanBeNone else '(%s)' % self.Type.SphinxMarkup

        doc += ' ' + self.ShortDescription.strip() if self.ShortDescription is not None else ''

        if self.IsReadOnly:
            doc += ' Read only.'

        constraints = self.Type.GetConstraintDescriptionStrings()
        if len(constraints) > 0:
            for c in [c for i, c in enumerate(constraints) if c not in constraints[:i]]:    # Remove duplicates but preserve order
                if not doc.endswith('\n'):
                    doc += ' '
                doc += c.replace(':','\uA789')   # Replace ASCII colons with Unicode 0xA789. Unfortunately Sphinx or its extensions interpret colons as markup and it messes up the documentation.
                if not doc.endswith('.'):
                    doc += '.'

        if self.LongDescription is not None:
            doc += '\n' + self.LongDescription

        return doc.rstrip()
        
    
class MethodMetadata(Metadata):
    __doc__ = DynamicDocString()

    def __init__(self, name, classMetadata, shortDescription=None, longDescription=None, isExposedToPythonCallers=False, isExposedAsArcGISTool=False, arcGISDisplayName=None, arcGISToolCategory=None, dependencies=[]):
        super(MethodMetadata, self).__init__(name, shortDescription, longDescription)
        assert isinstance(classMetadata, ClassMetadata), 'classMetadata must be an instance of %s.' % ClassMetadata.__name__
        assert hasattr(classMetadata.Object, name) and isinstance(getattr(classMetadata.Object, name), (types.MethodType, types.FunctionType)), 'Class %s must contain a method named %s.' % (classMetadata.Name, name)
        self._Class = classMetadata
        self.IsExposedToPythonCallers = isExposedToPythonCallers
        self.IsExposedAsArcGISTool = isExposedAsArcGISTool
        self.ArcGISDisplayName = arcGISDisplayName
        self.ArcGISToolCategory = arcGISToolCategory
        self._Arguments = []
        self._Results = []
        self.Dependencies = dependencies

    def _GetClass(self):
        return self._Class
    
    Class = property(_GetClass, doc=DynamicDocString())

    def _GetIsExposedToPythonCallers(self):
        return self._IsExposedToPythonCallers

    def _SetIsExposedToPythonCallers(self, value):
        assert isinstance(value, bool), 'IsExposedToPythonCallers must be a boolean.'
        self._IsExposedToPythonCallers = value

    IsExposedToPythonCallers = property(_GetIsExposedToPythonCallers, _SetIsExposedToPythonCallers, doc=DynamicDocString())

    def _GetIsExposedAsArcGISTool(self):
        return self._IsExposedAsArcGISTool
    
    def _SetIsExposedAsArcGISTool(self, value):
        assert isinstance(value, bool), 'IsExposedAsArcGISTool must be a boolean'
        self._IsExposedAsArcGISTool = value
        
    IsExposedAsArcGISTool = property(_GetIsExposedAsArcGISTool, _SetIsExposedAsArcGISTool, doc=DynamicDocString())

    def _IsExposedAsArcGISToolByUsNotParent(self, cls):
        parentClass = inspect.getmro(cls)[1]
        return self._IsExposedAsArcGISTool and self.Name in cls.__dict__ and (not hasattr(parentClass, self.Name) or getattr(parentClass, self.Name).__func__ != getattr(cls, self.Name).__func__)

    def _GetArcGISDisplayName(self):
        return self._ArcGISDisplayName
    
    def _SetArcGISDisplayName(self, value):
        assert isinstance(value, (type(None), str)), 'ArcGISDisplayName must be a string, or None.'
        if value is not None:
            self._ArcGISDisplayName = value.strip()
        else:
            self._ArcGISDisplayName = value
        
    ArcGISDisplayName = property(_GetArcGISDisplayName, _SetArcGISDisplayName, doc=DynamicDocString())

    def _GetArcGISToolCategory(self):
        return self._ArcGISToolCategory
    
    def _SetArcGISToolCategory(self, value):
        assert isinstance(value, (type(None), str)), 'ArcGISToolCategory must be a string, or None.'
        if value is not None:
            self._ArcGISToolCategory = value.strip()
        else:
            self._ArcGISToolCategory = value
        
    ArcGISToolCategory = property(_GetArcGISToolCategory, _SetArcGISToolCategory, doc=DynamicDocString())

    def _GetIsInstanceMethod(self):
        for (name, kind, homecls, obj) in inspect.classify_class_attrs(self.Class.Object):
            if name == self.Name:
                if kind.lower() == 'method':
                    return True
                else:
                    return False
        assert False, 'This line of code should never be executed.'
    
    IsInstanceMethod = property(_GetIsInstanceMethod, doc=DynamicDocString())

    def _GetIsClassMethod(self):
        for (name, kind, homecls, obj) in inspect.classify_class_attrs(self.Class.Object):
            if name == self.Name:
                if kind.lower() == 'class method':
                    return True
                else:
                    return False
        assert False, 'This line of code should never be executed.'
    
    IsClassMethod = property(_GetIsClassMethod, doc=DynamicDocString())

    def _GetIsStaticMethod(self):
        for (name, kind, homecls, obj) in inspect.classify_class_attrs(self.Class.Object):
            if name == self.Name:
                if kind.lower() == 'static method':
                    return True
                else:
                    return False
        assert False, 'This line of code should never be executed.'
    
    IsStaticMethod = property(_GetIsStaticMethod, doc=DynamicDocString())

    def _GetArguments(self):
        return self._Arguments
    
    def _SetArguments(self, value):
        assert isinstance(value, list)
        (args, varargs, varkw, defaults) = inspect.getfullargspec(self.Object)[:4]
        argCount = len(args)
        if varargs is not None:
            argCount = argCount + 1
        if varkw is not None:
            argCount = argCount + 1
        assert len(value) == argCount
        for i in len(args):
            assert isinstance(value[i], ArgumentMetadata) and value[i].Name == args[i]
        if varkw is not None:
            assert isinstance(value[-1], ArgumentMetadata) and value[-1].Name == varkw
            if varargs is not None:
                assert isinstance(value[-2], ArgumentMetadata) and value[-2].Name == varargs
        elif varargs is not None:
            assert isinstance(value[-1], ArgumentMetadata) and value[-1].Name == varargs
        self._Arguments = value
        
    Arguments = property(_GetArguments, _SetArguments, doc=DynamicDocString())

    def GetArgumentByName(self, name):
        assert isinstance(name, str), 'name must be a string.'
        for arg in self.Arguments:
            if arg.Name == name:
                return arg
        return None

    def _GetResults(self):
        return self._Results
    
    def _SetResults(self, value):
        assert isinstance(value, list)
        for result in value:
            assert isinstance(result, ResultMetadata)
        self._Results = value
        
    Results = property(_GetResults, _SetResults, doc=DynamicDocString())

    def GetResultByName(self, name):
        assert isinstance(name, str), 'name must be a string.'
        for result in self.Results:
            if result.Name == name:
                return result
        return None

    def _GetDependencies(self):
        return self._Dependencies
    
    def _SetDependencies(self, value):
        assert isinstance(value, list)
        if len(value) > 0:
            from .Dependencies import Dependency
            for result in value:
                assert isinstance(result, Dependency)
        self._Dependencies = value
        
    Dependencies = property(_GetDependencies, _SetDependencies, doc=DynamicDocString())

    def _GetObject(self):
        return getattr(self.Class.Object, self.Name)

    def _GetDocString(self):
        deps = [item for d in self.Dependencies for item in d.GetConstraintDescriptionStrings()]
        if len(deps) > 0:
            deps = 'Requires: ' + ', '.join([d for d in deps]) + '.'
        else:
            deps = None

        args = None
        if len(self.Arguments) > 1 or len(self.Arguments) == 1 and self.IsStaticMethod:
            args = 'Args:\n'
            for i in range(1 - int(self.IsStaticMethod), len(self.Arguments)):
                typeStr = '%s, optional' % self.Arguments[i].Type.SphinxMarkup if self.Arguments[i].HasDefault else self.Arguments[i].Type.SphinxMarkup
                descr = self.Arguments[i].Description.replace('\n','\n        ').replace('\n        \n','\n\n') if self.Arguments[i].Description is not None else 'No description available.'
                args += '    %s (%s): %s\n' % (self.Arguments[i].Name, typeStr, descr)

        results = None
        if len(self.Results) > 0:
            results = 'Returns:\n'
            if len(self.Results) == 1:
                descr = self.Results[0].Description.replace('\n','\n    ').replace('\n    \n','\n\n') if self.Results[0].Description is not None else 'No description available.'
                results += '    %s: %s\n' % (self.Results[0].Type.SphinxMarkup, descr)
            else:
                results += '    :py:class:`tuple` of %i items:\n' % len(self.Results)
                for i in range(len(self.Results)):
                    descr = self.Results[i].Description.replace('\n','\n    ').replace('\n    \n','\n\n') if self.Results[i].Description is not None else 'No description available.'
                    results += '\n    %i. %s: %s\n' % (i + 1, self.Results[i].Type.SphinxMarkup, descr)

        doc = '\n\n'.join(filter(None, [self.ShortDescription.strip() if self.ShortDescription is not None and self.Name != '__init__' else None,   # Omit ShortDescription for __init__, because it always says something uninformative, like "Construct a new XYZ instance"
                                        self.LongDescription,    # Do not strip() LongDescription; it might end in a code block, which will get messed up when we append deps
                                        deps,
                                        args,
                                        results]))

        if len(doc) <= 0:
            return 'No description available.'
        return doc.rstrip()


class ArgumentMetadata(object):
    __doc__ = DynamicDocString()

    def __init__(self, name, methodMetadata, typeMetadata, description=None, direction='Input', initializeToArcGISGeoprocessorVariable=None, arcGISDisplayName=None, arcGISCategory=None, arcGISParameterDependencies=None, dependencies=[]):
        assert isinstance(name, str), 'name must be a string.'
        self._Name = name
        assert isinstance(methodMetadata, MethodMetadata), 'methodMetadata must be an instance of %s.' % MethodMetadata.__name__
        self._Method = methodMetadata
        (args, varargs, varkw, defaults) = inspect.getfullargspec(methodMetadata.Object)[:4]
        argFound = (varargs is not None and name == varargs or varkw is not None and name == varkw)
        if not argFound:
            for arg in args:
                if arg == name:
                    argFound = True
                    break
        assert argFound, 'The %s method of the %s class must have an argument named %s.' % (methodMetadata.Name, methodMetadata.Class.Name, name)
        self.Type = typeMetadata
        self.Description = description
        self.Direction = direction
        self.InitializeToArcGISGeoprocessorVariable = initializeToArcGISGeoprocessorVariable
        self.ArcGISDisplayName = arcGISDisplayName
        self.ArcGISCategory = arcGISCategory
        self.ArcGISParameterDependencies = arcGISParameterDependencies
        self.Dependencies = dependencies

    def _GetName(self):
        return self._Name
    
    Name = property(_GetName, doc=DynamicDocString())

    def _GetMethod(self):
        return self._Method
    
    Method = property(_GetMethod, doc=DynamicDocString())

    def _GetType(self):
        return self._Type
    
    def _SetType(self, value):
        assert isinstance(value, TypeMetadata), 'Type must be an instance of %s.' % TypeMetadata.__name__
        self._Type = value
    
    Type = property(_GetType, _SetType, doc=DynamicDocString())

    def _GetDescription(self):
        doc = self._Description
        addNewlines = '\n\n' in doc and not doc.endswith('\n\n')

        constraints = self.Type.GetConstraintDescriptionStrings()
        if len(constraints) > 0:
            for c in constraints:
                c = c.replace(':','\uA789')   # Replace ASCII colons with Unicode 0xA789. Unfortunately Sphinx or its extensions interpret colons as markup and it messes up the documentation.
                if c not in doc:
                    if addNewlines:
                        doc += '\n\n'
                        addNewlines = False
                    if not doc.endswith('\n'):
                        doc += ' '
                    doc += c
                    if not doc.endswith('.'):
                        doc += '.'

        deps = [item for d in self.Dependencies for item in d.GetConstraintDescriptionStrings()]
        if len(deps) > 0:
            if addNewlines:
                doc += '\n\n'
                addNewlines = False
            doc += ' Requires: ' + ', '.join([d for d in deps]) + '.'

        return doc.rstrip()
    
    def _SetDescription(self, value):
        assert isinstance(value, (type(None), str)), 'Description must be a string, or None.'
        self._Description = value   # Do not strip Description; it might contain a code block

    Description = property(_GetDescription, _SetDescription, doc=DynamicDocString())

    def _GetDirection(self):
        return self._Direction
    
    def _SetDirection(self, value):
        assert isinstance(value, str) and (value == 'Input' or value == 'Output'), 'Direction must be either the string \'Input\' or \'Output\'.'
        self._Direction = value
        
    Direction = property(_GetDirection, _SetDirection, doc=DynamicDocString())

    def _GetInitializeToArcGISGeoprocessorVariable(self):
        return self._InitializeToArcGISGeoprocessorVariable
    
    def _SetInitializeToArcGISGeoprocessorVariable(self, value):
        assert isinstance(value, (type(None), str)), 'InitializeToArcGISGeoprocessorVariable must be a string, or None.'
        assert self.IsFormalParameter or value is None, 'InitializeToArcGISGeoprocessorVariable may only be specified for formal parameters. It must remain None for the arbitrary argument list (varargs) and keywords dictionary (varkw) parameters.'
        if value is not None:
            self._InitializeToArcGISGeoprocessorVariable = value.strip()
        else:
            self._InitializeToArcGISGeoprocessorVariable = value
        
    InitializeToArcGISGeoprocessorVariable = property(_GetInitializeToArcGISGeoprocessorVariable, _SetInitializeToArcGISGeoprocessorVariable, doc=DynamicDocString())

    def _GetArcGISDisplayName(self):
        return self._ArcGISDisplayName
    
    def _SetArcGISDisplayName(self, value):
        assert isinstance(value, (type(None), str)), 'ArcGISDisplayName must be a string, or None.'
        if value is not None:
            self._ArcGISDisplayName = value.strip()
        else:
            self._ArcGISDisplayName = value
        
    ArcGISDisplayName = property(_GetArcGISDisplayName, _SetArcGISDisplayName, doc=DynamicDocString())

    def _GetArcGISCategory(self):
        return self._ArcGISCategory
    
    def _SetArcGISCategory(self, value):
        assert isinstance(value, (type(None), str)), 'ArcGISCategory must be a string, or None.'
        if value is not None:
            self._ArcGISCategory = value.strip()
        else:
            self._ArcGISCategory = value
        
    ArcGISCategory = property(_GetArcGISCategory, _SetArcGISCategory, doc=DynamicDocString())

    def _GetArcGISParameterDependencies(self):
        return self._ArcGISParameterDependencies
    
    def _SetArcGISParameterDependencies(self, value):
        assert isinstance(value, (list, type(None))), 'ArcGISParameterDependencies must be a list of strings, or None.'
        if isinstance(value, list):
            for param in value:
                assert isinstance(param, str), 'ArcGISParameterDependencies must be a list of strings, or None.'
        self._ArcGISParameterDependencies = value
        
    ArcGISParameterDependencies = property(_GetArcGISParameterDependencies, _SetArcGISParameterDependencies, doc=DynamicDocString())

    def _GetDependencies(self):
        return self._Dependencies
    
    def _SetDependencies(self, value):
        assert isinstance(value, list)
        if len(value) > 0:
            from .Dependencies import Dependency
            for result in value:
                assert isinstance(result, Dependency)
        self._Dependencies = value
        
    Dependencies = property(_GetDependencies, _SetDependencies, doc=DynamicDocString())

    def _GetIsFormalParameter(self):
        (args, varargs, varkw, defaults) = inspect.getfullargspec(self.Method.Object)[:4]
        for arg in args:
            if arg == self.Name:
                return True
        return False
    
    IsFormalParameter = property(_GetIsFormalParameter, doc=DynamicDocString())

    def _GetIsArbitraryArgumentList(self):
        (args, varargs, varkw, defaults) = inspect.getfullargspec(self.Method.Object)[:4]
        return self.Name == varargs
    
    IsArbitraryArgumentList = property(_GetIsArbitraryArgumentList, doc=DynamicDocString())

    def _GetIsKeywordArgumentDictionary(self):
        (args, varargs, varkw, defaults) = inspect.getfullargspec(self.Method.Object)[:4]
        return self.Name == varkw
    
    IsKeywordArgumentDictionary = property(_GetIsKeywordArgumentDictionary, doc=DynamicDocString())

    def _GetHasDefault(self):
        (args, varargs, varkw, defaults) = inspect.getfullargspec(self.Method.Object)[:4]
        if self.Name == varargs or self.Name == varkw:
            return False
        for i in range(len(args)):
            if args[i] == self.Name:
                if defaults is not None and len(args) - i <= len(defaults):
                    return True
                return False
        assert False, 'The method %s must have an argument named %s.' % (self.Method.Name, self.Name)
    
    HasDefault = property(_GetHasDefault, doc=DynamicDocString())

    def _GetDefault(self):
        (args, varargs, varkw, defaults) = inspect.getfullargspec(self.Method.Object)[:4]
        if self.Name == varargs or self.Name == varkw:
            return None
        for i in range(len(args)):
            if args[i] == self.Name:
                if defaults is not None and len(args) - i <= len(defaults):
                    return defaults[0 - len(args) + i]
                raise ValueError('The method %s does not have a default for the argument %s.' % (self.Method.Name, self.Name))
        assert False, 'The method %s must have an argument named %s.' % (self.Method.Name, self.Name)
    
    Default = property(_GetDefault, doc=DynamicDocString())


class ResultMetadata(object):
    __doc__ = DynamicDocString()

    def __init__(self, name, methodMetadata, typeMetadata, description=None, arcGISDisplayName=None, arcGISParameterDependencies=None):
        assert isinstance(name, str), 'name must be a string.'
        self._Name = name
        assert isinstance(methodMetadata, MethodMetadata), 'methodMetadata must be an instance of %s.' % MethodMetadata.__name__
        self._Method = methodMetadata
        self.Type = typeMetadata
        self.Description = description
        self.ArcGISDisplayName = arcGISDisplayName
        self.ArcGISParameterDependencies = arcGISParameterDependencies

    def _GetName(self):
        return self._Name
    
    Name = property(_GetName, doc=DynamicDocString())

    def _GetMethod(self):
        return self._Method
    
    Method = property(_GetMethod, doc=DynamicDocString())

    def _GetType(self):
        return self._Type
    
    def _SetType(self, value):
        assert isinstance(value, TypeMetadata), 'TypeMetadata must be an instance of %s.' % TypeMetadata.__name__
        self._Type = value
    
    Type = property(_GetType, _SetType, doc=DynamicDocString())

    def _GetDescription(self):
        return self._Description
    
    def _SetDescription(self, value):
        assert isinstance(value, (type(None), str)), 'Description must be a string, or None.'
        self._Description = value   # Do not strip Description; it might contain a code block
        
    Description = property(_GetDescription, _SetDescription, doc=DynamicDocString())

    def _GetArcGISDisplayName(self):
        return self._ArcGISDisplayName
    
    def _SetArcGISDisplayName(self, value):
        assert isinstance(value, (type(None), str)), 'ArcGISDisplayName must be a string, or None.'
        if value is not None:
            self._ArcGISDisplayName = value.strip()
        else:
            self._ArcGISDisplayName = value
        
    ArcGISDisplayName = property(_GetArcGISDisplayName, _SetArcGISDisplayName, doc=DynamicDocString())

    def _GetArcGISParameterDependencies(self):
        return self._ArcGISParameterDependencies
    
    def _SetArcGISParameterDependencies(self, value):
        assert isinstance(value, (list, type(None))), 'ArcGISParameterDependencies must be a list of strings, or None.'
        if isinstance(value, list):
            for param in value:
                assert isinstance(param, str), 'ArcGISParameterDependencies must be a list of strings, or None.'
        self._ArcGISParameterDependencies = value
        
    ArcGISParameterDependencies = property(_GetArcGISParameterDependencies, _SetArcGISParameterDependencies, doc=DynamicDocString())


# Private helper functions


def _GetModuleObject(module):
    assert isinstance(module, (types.ModuleType, str, type(None))), 'module must be a module object, a string that is the full name of the module, or None indicating that the calling module should be used.'
    assert not isinstance(module, str) or module in sys.modules, 'If module is a string, it must be the full name of a module that has already been imported.'
    if module is None:
        module = inspect.getmodule(inspect.currentframe().f_back.f_back)
    elif isinstance(module, str):
        module = sys.modules[module]
    return module


def _GetClassObject(cls, module):
    assert inspect.isclass(cls) or isinstance(cls, str), 'cls must be a class object or a string that is the name of a class defined in module %s.' % module.__name__
    assert not isinstance(cls, str) or cls in module.__dict__ and inspect.isclass(module.__dict__[cls]), 'If cls is a string, it must be the name of a class defined in module %s.' % module.__name__
    if isinstance(cls, str):
        cls = module.__dict__[cls]
    return cls


def _GetMethodObject(method, cls, module):
    assert inspect.ismethod(method) or inspect.isfunction(method) or isinstance(method, str), 'method must be an instance, class, or static method of a class, or a string that is the name of such a method.'
    if isinstance(method, str):
        assert cls is not None, 'When method is a method name, cls must not be None. It must specify the class that contains the method.'
        methodName = method
    else:
        methodName = str(method.__name__)
    if cls is None and inspect.ismethod(method):
        if inspect.isclass(method.__self__):
            return (method, method.__self__)
        else:
            return (method, type(method.__self__))
    if cls is not None:
        for (name, kind, homecls, obj) in inspect.classify_class_attrs(cls):
            if name == methodName:
                assert kind.lower() == 'class method' or kind.lower() == 'static method' or kind.lower() == 'method', 'Class %s contains an attribute named %s but it is not a method. Please specify a method.' % (cls.__name__, name)
                if not isinstance(method, str):
                    assert method == getattr(cls, name), 'Class %s does have a method named %s, but its method object %s is different than the method object %s that was provided.' % (cls.__name__, name, str(method), str(getattr(cls, name)))
                return (getattr(cls, name), cls)
        assert False, 'Class %s does not have a method named %s. Please specify an existing method.' % (cls.__name__, methodName)
    classesToSearch = []
    for val in list(module.__dict__.values()):
        if inspect.isclass(val):
            for (name, kind, homecls, obj) in inspect.classify_class_attrs(val):
                if (kind.lower() == 'class method' or kind.lower() == 'static method' or kind.lower() == 'method') and name == methodName and method == getattr(val, name):
                    return (getattr(val, name), val)
    assert False, 'Module %s does not have a class that contains a method named %s that matches the method provided. Please specify an existing method when calling AddMethodMetadata.' % (module.__name__, methodName)


def _ValidatePropertyInfo(prop, cls=None, module=None):
    if cls is not None:
        cls = _GetClassObject(cls, module)
    assert inspect.isdatadescriptor(prop) or isinstance(prop, str), 'prop must be a property object or a string that is the name of a property.'
    if isinstance(prop, str):
        assert cls is not None, 'If prop is a string, then cls must be a class object or a string that is the name of a class.'
        assert hasattr(cls, prop) and inspect.isdatadescriptor(getattr(cls, prop)), 'If prop is a string, it must be the name of a property contained by class %s.' % cls.__name__
        propName = prop
        prop = getattr(cls, prop)
    elif cls is not None:
        found = False
        for attr in list(cls.__dict__.keys()):
            if hasattr(cls, attr) and id(getattr(cls, attr)) == id(prop):
                found = True
                propName = attr
        assert found, 'If prop is a property object and cls is specified, prop must be a property of cls.'
    else:
        for val in list(module.__dict__.values()):
            if inspect.isclass(val):
                for attr in list(val.__dict__.keys()):
                    if hasattr(val, attr) and id(getattr(val, attr)) == id(prop):
                        cls = val
                        propName = attr
        assert cls is not None, 'If prop is a property object and cls is None, module %s must contain the class to which prop belongs.' % module.__name__
    assert isinstance(cls.__doc__, DynamicDocString), 'The __doc__ attribute of class %s defined in module %s must be an instance of GeoEco.Metadata.DynamicDocString. You should place the line\n\n    __doc__ = GeoEco.Metadata.DynamicDocString()\n\nin your class definition.' % (cls.__name__, module.__name__)
    assert isinstance(cls.__doc__.Obj, ClassMetadata), '%s.__doc__.Obj must be an instance of GeoEco.Metadata.ClassMetadata. Before calling AddPropertyMetadata or CopyPropertyMetadata, use GeoEco.Metadata.AddClassMetadata to add ClassMetadata to class %s.' % (cls.__name__, cls.__name__)
    assert isinstance(prop.__doc__, DynamicDocString), '%s.%s.__doc__ must be an instance of GeoEco.Metadata.DynamicDocString. When defining the property, set the doc parameter to a new instance of DynamicDocString, like this:\n\n    %s = property(..., doc=DynamicDocString())' % (cls.__name__, propName, propName)
    return prop, propName, cls


def _ValidateMethodMetadata(method, cls=None, module=None):
    if cls is not None:
        cls = _GetClassObject(cls, module)
    (method, cls) = _GetMethodObject(method, cls, module)
    assert isinstance(cls.__doc__, DynamicDocString), 'The __doc__ attribute of class %s defined in module %s must be an instance of GeoEco.Metadata.DynamicDocString. You should place the line\n\n    __doc__ = GeoEco.Metadata.DynamicDocString()\n\nin your class definition.' % (cls.__name__, module.__name__)
    assert isinstance(cls.__doc__.Obj, ClassMetadata), '%s.__doc__.Obj must be an instance of GeoEco.Metadata.ClassMetadata. Use GeoEco.Metadata.AddClassMetadata to add ClassMetadata to class %s.' % (cls.__name__, cls.__name__)
    return method, cls


# Public helper functions for applying metadata to classes, properties and methods


def AddModuleMetadata(shortDescription, longDescription=None, module=None):
    """Creates a :class:`ModuleMetadata` and attaches it to a module.

    Args:
        shortDescription (:py:class:`str`): One-line description of the module, ideally as plain text (but reStructuredText is OK).
        longDescription (:py:class:`str`, optional): Detailed description of the module, formatted as reStructuredText.
        module (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module object itself, or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.
    """
    module = _GetModuleObject(module)
    assert not isinstance(module.__doc__, DynamicDocString) or module.__doc__.Obj is None, 'If %s.__doc__ is an instance of DynamicDocString, %s.__doc__.Obj must be None. Do not call AddModuleMetadata on a module that already has metadata.' % (module.__name__, module.__name__)

    module.__doc__ = DynamicDocString(ModuleMetadata(str(module.__name__), shortDescription, longDescription))


def AddClassMetadata(cls, shortDescription, longDescription=None, module=None):
    """Creates a :class:`ClassMetadata` for a class and adds it to a :class:`ModuleMetadata`.

    Args:
        cls (:py:class:`type` or :py:class:`str`): The class itself, or the unqualified name of the class (without module or package names).
        shortDescription (:py:class:`str`): One-line description of the class, ideally as plain text (but reStructuredText is OK).
        longDescription (:py:class:`str`, optional): Detailed description of the class, formatted as reStructuredText.
        module (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains the class, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.

    Note:
        Before calling this function, use :func:`AddModuleMetadata` to create
        the :class:`ModuleMetadata` and attach it to the module.
    """
    module = _GetModuleObject(module)
    assert isinstance(module.__doc__, DynamicDocString) and isinstance(module.__doc__.Obj, ModuleMetadata), 'The __doc__ attribute of module %s must be an instance of GeoEco.Metadata.DynamicDocString, and __doc__.Obj must be an instance of GeoEco.Metadata.ModuleMetadata. Use the GeoEco.Metadata.AddModuleMetadata function to add the module\'s metadata before calling GeoEco.Metadata.AddClassMetadata.' % module.__name__
    cls = _GetClassObject(cls, module)
    assert isinstance(cls.__doc__, DynamicDocString), 'The __doc__ attribute of class %s defined in module %s must be an instance of GeoEco.Metadata.DynamicDocString. You should place the line\n\n    __doc__ = GeoEco.Metadata.DynamicDocString()\n\nin your class definition.' % (cls.__name__, module.__name__)
    assert cls.__doc__.Obj is None, '%s.__doc__.Obj must be None. Do not call AddClassMetadata on a class that already has metadata.' % cls.__name__
    
    cls.__doc__.Obj = ClassMetadata(str(cls.__name__), module.__doc__.Obj, shortDescription, longDescription)


def AddPropertyMetadata(prop, typeMetadata, shortDescription=None, longDescription=None, isExposedToPythonCallers=False, cls=None, module=None):
    """Creates a :class:`PropertyMetadata` and for a class property adds it to a :class:`ClassMetadata`.

    Args:
        prop (:py:class:`property` or :py:class:`str`): The :py:class:`property` object or name of the property. If the name is given, `cls` must also be given.
        typeMetadata (:class:`GeoEco.Types.TypeMetadata`): A :class:`~GeoEco.Types.TypeMetadata` that describes the data type and allowed values of the property.
        shortDescription (:py:class:`str`, optional): One-line description of the property, ideally as plain text (but reStructuredText is OK).
        longDescription (:py:class:`str`, optional): Detailed description of the property, formatted as reStructuredText.
        isExposedToPythonCallers (:py:class:`bool`, optional): If True, the property should be part of GeoEco's Public API. If False, the default, the property is considered part of GeoEco's Internal API and not recommended for use by external callers.
        cls (:py:class:`type` or :py:class:`str`, optional): The class containing the property, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `prop` is given as a name rather than a :py:class:`property` object.
        module (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains the class, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.

    Note:

        Before calling this function, use :func:`AddClassMetadata` to create
        the :class:`ClassMetadata` and add it to its module's
        :class:`ModuleMetadata`.
    """
    module = _GetModuleObject(module)
    (prop, propName, cls) = _ValidatePropertyInfo(prop, cls, module)
    assert prop.__doc__.Obj is None, '%s.%s.__doc__.Obj must be None. Do not call AddPropertyMetadata on a property that already has metadata.' % (cls.__name__, propName)

    prop.__doc__.Obj = PropertyMetadata(str(propName), cls.__doc__.Obj, typeMetadata, shortDescription, longDescription, isExposedToPythonCallers)


def CopyPropertyMetadata(fromProperty, toProperty, fromClass=None, fromModule=None, toClass=None, toModule=None):
    """Copies the :class:`PropertyMetadata` for a specified property from one class's :class:`ClassMetadata` to another's.

    Use this function to duplicate a :class:`PropertyMetadata` when two
    classes have an identical or very similar property. If they are not
    exactly the same, you can modify the second property's
    :class:`PropertyMetadata` after it has been copied.

    Args:
        fromProperty (:py:class:`property` or :py:class:`str`): The :py:class:`property` object or name of the property to copy :class:`PropertyMetadata` from. If the name is given, `fromClass` must also be given.
        toProperty (:py:class:`property` or :py:class:`str`): The :py:class:`property` object or name of the property to copy the :class:`PropertyMetadata` to. If the name is given, `toClass` must also be given.
        fromClass (:py:class:`type` or :py:class:`str`, optional): The class containing `fromProperty`, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `fromProperty` is given as a name rather than a :py:class:`property` object.
        fromModule (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains `fromClass`, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.
        toClass (:py:class:`type` or :py:class:`str`, optional): The class containing `toProperty`, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `toProperty` is given as a name rather than a :py:class:`property` object.
        toModule (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains `toClass`, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.

    Note:

        Before calling this function, use :func:`AddPropertyMetadata` to
        create a :class:`PropertyMetadata` and add it to the
        :class:`ClassMetadata` of the class that contains `fromProperty`.
    """
    fromModule = _GetModuleObject(fromModule)
    (fromProperty, fromPropertyName, fromClass) = _ValidatePropertyInfo(fromProperty, fromClass, fromModule)
    assert fromProperty.__doc__.Obj is not None, '%s.%s.__doc__.Obj must not be None. Before calling CopyPropertyMetadata, ensure that fromProperty already has metadata.' % (fromClass.__name__, fromPropertyName)

    toModule = _GetModuleObject(toModule)
    (toProperty, toPropertyName, toClass) = _ValidatePropertyInfo(toProperty, toClass, toModule)
    assert toProperty.__doc__.Obj is None, '%s.%s.__doc__.Obj must be None. Before calling CopyPropertyMetadata, ensure that toProperty does not have metadata already.' % (toClass.__name__, toPropertyName)

    toProperty.__doc__.Obj = PropertyMetadata(str(toPropertyName),
                                              toClass.__doc__.Obj,
                                              typeMetadata=copy.deepcopy(fromProperty.__doc__.Obj.Type),
                                              shortDescription=fromProperty.__doc__.Obj.ShortDescription,
                                              longDescription=fromProperty.__doc__.Obj.LongDescription,
                                              isExposedToPythonCallers=fromProperty.__doc__.Obj.IsExposedToPythonCallers)


def AddMethodMetadata(method, shortDescription=None, longDescription=None, isExposedToPythonCallers=False, isExposedAsArcGISTool=False, arcGISDisplayName=None, arcGISToolCategory=None, cls=None, module=None, dependencies=[]):
    """Creates a :class:`MethodMetadata` for a method and adds it to a :class:`ClassMetadata`.

    Args:
        method (:py:data:`~types.MethodType` or :py:class:`str`): The method itself or the name of the method. If the name is given, `cls` must also be given.
        shortDescription (:py:class:`str`, optional): One-line description of the method, ideally as plain text (but reStructuredText is OK).
        longDescription (:py:class:`str`, optional): Detailed description of the method, formatted as reStructuredText.
        isExposedToPythonCallers (:py:class:`bool`, optional): If True, the method should be part of GeoEco's Public API. If False, the default, the method is considered part of GeoEco's Internal API and not recommended for use by external callers.
        isExposedAsArcGISTool (:py:class:`bool`, optional): If True, the method should be part of GeoEco's Public API. If False, the default, the method is considered part of GeoEco's Internal API and not recommended for use by external callers.
        arcGISDisplayName (:py:class:`str`, optional): Name of the tool, as displayed in MGET's ArcGIS toolbox. Ignored if `isExposedAsArcGISTool` is False.
        arcGISToolCategory (:py:class:`str`, optional): Toolset that the tool appears under in MGET's ArcGIS toolbox. If :py:data:`None`, the default, the tool appears at the root level. Ignored if `isExposedAsArcGISTool` is False.
        cls (:py:class:`type` or :py:class:`str`, optional): The class containing the method, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `method` is given as a name rather than the method itself.
        module (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains the class, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.
        dependencies (:py:class:`list` of :class:`~GeoEco.Dependencies.Dependency`, optional): :py:class:`list` of :class:`~GeoEco.Dependencies.Dependency` objects defining software dependencies that should be checked prior to executing this method.

    Note:

        Before calling this function, use :func:`AddClassMetadata` to create
        the :class:`ClassMetadata` and add it to its module's
        :class:`ModuleMetadata`.
    """
    module = _GetModuleObject(module)
    (method, cls) = _ValidateMethodMetadata(method, cls, module)
    if not isinstance(method.__doc__, DynamicDocString):
        if hasattr(method, '__func__'):
            method.__func__.__doc__ = DynamicDocString()
        else:
            method.__doc__ = DynamicDocString()
    assert method.__doc__.Obj is None, '%s.%s.__doc__.Obj must be None. Do not call AddMethodMetadata on a method that already has metadata.' % (cls.__name__, method.__name__)
    
    method.__doc__.Obj = MethodMetadata(str(method.__name__), cls.__doc__.Obj, shortDescription, longDescription, isExposedToPythonCallers, isExposedAsArcGISTool, arcGISDisplayName, arcGISToolCategory, dependencies)


def AddArgumentMetadata(method, argumentName, typeMetadata, description=None, direction='Input', initializeToArcGISGeoprocessorVariable=None, arcGISDisplayName=None, arcGISCategory=None, arcGISParameterDependencies=None, cls=None, module=None, dependencies=[]):
    """Creates an :class:`ArgumentMetadata` for a method parameter and adds it to a :class:`MethodMetadata`.

    Args:
        method (:py:data:`~types.MethodType` or :py:class:`str`): The method itself or the name of the method. If the name is given, `cls` must also be given.
        argumentName (:py:class:`str`): Name of the parameter, as it appears in the method's signature.
        typeMetadata (:class:`~GeoEco.Types.TypeMetadata`): :class:`~GeoEco.Types.TypeMetadata` that describes the data type and allowed values of the parameter.
        description (:py:class:`str`, optional): The parameter's description, ideally one line of plain text (but reStructuredText is OK). Put long details in :attr:`MethodMetadata.LongDescription`.
        direction (:py:class:`str`, optional): Direction of the parameter, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise). Allowed values꞉ ``'Input'``, ``'Output'``. Case sensitive.
        initializeToArcGISGeoprocessorVariable (:py:class:`str`, optional): The parameter value should be obtained from this geoprocessor variable, rather than from the user as a tool parameter, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise). 
        arcGISDisplayName (:py:class:`str`, optional): Name of the parameter as it should appear in ArcGIS, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).
        arcGISToolCategory (:py:class:`str`, optional): Category of the parameter as it should appear in ArcGIS, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).
        arcGISParameterDependencies (:py:class:`list` of :py:class:`str`, optional): :py:class:`list` of names of parameters that this return value is dependent on (see ArcGIS documentation), when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).
        cls (:py:class:`type` or :py:class:`str`, optional): The class containing the method, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `method` is given as a name rather than the method itself.
        module (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains the class, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.
        dependencies (:py:class:`list` of :class:`~GeoEco.Dependencies.Dependency`, optional): :py:class:`list` of :class:`~GeoEco.Dependencies.Dependency` objects defining software dependencies that should be checked when the value provided for this parameter is not :py:data:`None` when the method is called (ignored otherwise).

    Note:

        Before calling this function, use :func:`AddMethodMetadata` to create
        the :class:`MethodMetadata` and add it to its class's
        :class:`ClassMetadata`.
    """
    module = _GetModuleObject(module)
    (method, cls) = _ValidateMethodMetadata(method, cls, module)
    assert isinstance(method.__doc__, DynamicDocString) and isinstance(method.__doc__.Obj, MethodMetadata), 'The %s.%s.__doc__ must be an instance of GeoEco.Metadata.DynamicDocString, and %s.%s.__doc__.Obj must be an instance of GeoEco.Metadata.MethodMetadata. Before calling GeoEco.Metadata.AddArgumentMetadata, use GeoEco.Metadata.AddMethodMetadata to add MethodMetadata to %s.%s.' % (cls.__name__, method.__name__, cls.__name__, method.__name__, cls.__name__, method.__name__)
    assert method.__doc__.Obj.GetArgumentByName(str(argumentName)) is None, '%s.%s.__doc__.Obj.Arguments already has ArgumentMetadata for the %s argument. Do not call AddArgumentMetadata for arguments that already have metadata.' % (cls.__name__, method.__name__, argumentName)
    
    method.__doc__.Obj.Arguments.append(ArgumentMetadata(str(argumentName), method.__doc__.Obj, typeMetadata, description, direction, initializeToArcGISGeoprocessorVariable, arcGISDisplayName, arcGISCategory, arcGISParameterDependencies, dependencies))


def AddResultMetadata(method, resultName, typeMetadata, description=None, arcGISDisplayName=None, arcGISParameterDependencies=None, cls=None, module=None):
    """Creates a :class:`ResultMetadata` for a method return value and adds it to a :class:`MethodMetadata`.

    Args:
        method (:py:data:`~types.MethodType` or :py:class:`str`): The method itself or the name of the method. If the name is given, `cls` must also be given.
        resultName (:py:class:`str`): Name of the return value. Although Python does not give names to return values, they are needed when a method is exposed as an ArcGIS goeprocessing tool, and can be useful in other contexts.
        typeMetadata (:class:`~GeoEco.Types.TypeMetadata`): :class:`~GeoEco.Types.TypeMetadata` that describes the data type and allowed values of the return value.
        description (:py:class:`str`, optional): The return value's description, ideally one line of plain text (but reStructuredText is OK). Put long details in :attr:`MethodMetadata.LongDescription`.
        arcGISDisplayName (:py:class:`str`, optional): Name of the return value as it should appear in ArcGIS, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).
        arcGISParameterDependencies (:py:class:`list` of :py:class:`str`, optional): :py:class:`list` of names of parameters that this return value is dependent on (see ArcGIS documentation), when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).
        cls (:py:class:`type` or :py:class:`str`, optional): The class containing the method, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `method` is given as a name rather than the method itself.
        module (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains the class, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.

    Note:

        Before calling this function, use :func:`AddMethodMetadata` to create
        the :class:`MethodMetadata` and add it to its class's
        :class:`ClassMetadata`.
    """
    module = _GetModuleObject(module)
    (method, cls) = _ValidateMethodMetadata(method, cls, module)
    assert isinstance(method.__doc__, DynamicDocString) and isinstance(method.__doc__.Obj, MethodMetadata), 'The %s.%s.__doc__ must be an instance of GeoEco.Metadata.DynamicDocString, and %s.%s.__doc__.Obj must be an instance of GeoEco.Metadata.MethodMetadata. Before calling GeoEco.Metadata.AddArgumentMetadata, use GeoEco.Metadata.AddMethodMetadata to add MethodMetadata to %s.%s.' % (cls.__name__, method.__name__, cls.__name__, method.__name__, cls.__name__, method.__name__)
    assert method.__doc__.Obj.GetResultByName(str(resultName)) is None, '%s.%s.__doc__.Obj.Results already has ResultMetadata for the %s result. Do not call AddResultMetadata for results that already have metadata.' % (cls.__name__, method.__name__, resultName)
    
    method.__doc__.Obj.Results.append(ResultMetadata(str(resultName), method.__doc__.Obj, typeMetadata, description, arcGISDisplayName, arcGISParameterDependencies))


def CopyArgumentMetadata(fromMethod, fromArgumentName, toMethod, toArgumentName, fromClass=None, fromModule=None, toClass=None, toModule=None):
    """Copies the :class:`ArgumentMetadata` for a specified parameter from one methods's :class:`MethodMetadata` to another's.

    Use this function to duplicate an :class:`ArgumentMetadata` when two
    classes have an identical or very similar parameter. If they are not
    exactly the same, you can modify the second methods's
    :class:`ArgumentMetadata` for the parameter after it has been copied.

    Args:
        fromMethod (:py:data:`~types.MethodType` or :py:class:`str`): The method or name of the method to copy the :class:`ArgumentMetadata` from. If the name is given, `fromClass` must also be given.
        fromArgumentName (:py:class:`str`): The name of the parameter in `fromMethod` for which the :class:`ArgumentMetadata` should be copied.
        toMethod (:py:data:`~types.MethodType` or :py:class:`str`): The method or name of the method to copy the :class:`ArgumentMetadata` to. If the name is given, `toClass` must also be given.
        toArgumentName (:py:class:`str`): The name of the parameter in `toMethod` that should receive the copied :class:`ArgumentMetadata`.
        fromClass (:py:class:`type` or :py:class:`str`, optional): The class containing `fromMethod`, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `fromMethod` is given as a name rather than the method itself.
        fromModule (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains `fromClass`, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.
        toClass (:py:class:`type` or :py:class:`str`, optional): The class containing `toMethod`, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `toMethod` is given as a name rather than the method itself.
        toModule (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains `toClass`, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.

    Note:

        Before calling this function, use :func:`AddArgumentMetadata` to
        create an :class:`ArgumentMetadata` for `fromArgumentName` and add it
        to the :class:`MethodMetadata` of `fromMethod`.
    """
    fromModule = _GetModuleObject(fromModule)
    (fromMethod, fromClass) = _ValidateMethodMetadata(fromMethod, fromClass, fromModule)
    assert isinstance(fromMethod.__doc__, DynamicDocString) and isinstance(fromMethod.__doc__.Obj, MethodMetadata), 'The %s.%s.__doc__ must be an instance of GeoEco.Metadata.DynamicDocString, and %s.%s.__doc__.Obj must be an instance of GeoEco.Metadata.MethodMetadata. Before calling GeoEco.Metadata.CopyArgumentMetadata, use GeoEco.Metadata.AddMethodMetadata to add MethodMetadata to %s.%s.' % (fromClass.__name__, fromMethod.__name__, fromClass.__name__, fromMethod.__name__, fromClass.__name__, fromMethod.__name__)
    assert fromMethod.__doc__.Obj.GetArgumentByName(str(fromArgumentName)) is not None, '%s.%s.__doc__.Obj.Arguments does not have ArgumentMetadata for the %s argument. You must assign metadata to this argument before trying to copy it to another argument.' % (fromClass.__name__, fromMethod.__name__, fromArgumentName)

    toModule = _GetModuleObject(toModule)
    (toMethod, toClass) = _ValidateMethodMetadata(toMethod, toClass, toModule)
    assert isinstance(toMethod.__doc__, DynamicDocString) and isinstance(toMethod.__doc__.Obj, MethodMetadata), 'The %s.%s.__doc__ must be an instance of GeoEco.Metadata.DynamicDocString, and %s.%s.__doc__.Obj must be an instance of GeoEco.Metadata.MethodMetadata. Before calling GeoEco.Metadata.CopyArgumentMetadata, use GeoEco.Metadata.AddMethodMetadata to add MethodMetadata to %s.%s.' % (toClass.__name__, toMethod.__name__, toClass.__name__, toMethod.__name__, toClass.__name__, toMethod.__name__)
    assert toMethod.__doc__.Obj.GetArgumentByName(str(toArgumentName)) is None, '%s.%s.__doc__.Obj.Arguments already has ArgumentMetadata for the %s argument. Do not call CopyArgumentMetadata to copy metadata to an argument that already has metadata.' % (toClass.__name__, toMethod.__name__, toArgumentName)

    fromArgument = fromMethod.__doc__.Obj.GetArgumentByName(str(fromArgumentName))
    toMethod.__doc__.Obj.Arguments.append(ArgumentMetadata(str(toArgumentName),
                                                           toMethod.__doc__.Obj,
                                                           typeMetadata=copy.deepcopy(fromArgument.Type),
                                                           description=fromArgument._Description,
                                                           direction=fromArgument.Direction,
                                                           initializeToArcGISGeoprocessorVariable=fromArgument.InitializeToArcGISGeoprocessorVariable,
                                                           arcGISDisplayName=fromArgument.ArcGISDisplayName,
                                                           arcGISCategory=fromArgument.ArcGISCategory,
                                                           arcGISParameterDependencies=copy.deepcopy(fromArgument.ArcGISParameterDependencies),
                                                           dependencies=copy.deepcopy(fromArgument.Dependencies)))


def CopyResultMetadata(fromMethod, fromResultName, toMethod, toResultName, fromClass=None, fromModule=None, toClass=None, toModule=None):
    """Copies the :class:`ResultMetadata` for a specified return value from one methods's :class:`MethodMetadata` to another's.

    Use this function to duplicate a :class:`ResultMetadata` when two
    classes have an identical or very similar return value. If they are not
    exactly the same, you can modify the second methods's
    :class:`ResultMetadata` for the return value after it has been copied.

    Args:
        fromMethod (:py:data:`~types.MethodType` or :py:class:`str`): The method or name of the method to copy the :class:`ResultMetadata` from. If the name is given, `fromClass` must also be given.
        fromResultName (:py:class:`str`): The name of the return value in `fromMethod` for which the :class:`ResultMetadata` should be copied.
        toMethod (:py:data:`~types.MethodType` or :py:class:`str`): The method or name of the method to copy the :class:`ResultMetadata` to. If the name is given, `toClass` must also be given.
        toResultName (:py:class:`str`): The name of the return value in `toMethod` that should receive the copied :class:`ResultMetadata`.
        fromClass (:py:class:`type` or :py:class:`str`, optional): The class containing `fromMethod`, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `fromMethod` is given as a name rather than the method itself.
        fromModule (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains `fromClass`, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.
        toClass (:py:class:`type` or :py:class:`str`, optional): The class containing `toMethod`, either as the class itself or the unqualified name of the class (without module or package names). Only needed if `toMethod` is given as a name rather than the method itself.
        toModule (:py:class:`~types.ModuleType` or :py:class:`str`, optional): The module that contains `toClass`, either as the module object itself or the fully qualified name of the module (a.k.a. dotted module name). If not provided, the caller's module is used.

    Note:

        Before calling this function, use :func:`AddResultMetadata` to
        create a :class:`ResultMetadata` for `fromResultName` and add it
        to the :class:`MethodMetadata` of `fromMethod`.
    """
    fromModule = _GetModuleObject(fromModule)
    (fromMethod, fromClass) = _ValidateMethodMetadata(fromMethod, fromClass, fromModule)
    assert isinstance(fromMethod.__doc__, DynamicDocString) and isinstance(fromMethod.__doc__.Obj, MethodMetadata), 'The %s.%s.__doc__ must be an instance of GeoEco.Metadata.DynamicDocString, and %s.%s.__doc__.Obj must be an instance of GeoEco.Metadata.MethodMetadata. Before calling GeoEco.Metadata.CopyResultMetadata, use GeoEco.Metadata.AddMethodMetadata to add MethodMetadata to %s.%s.' % (fromClass.__name__, fromMethod.__name__, fromClass.__name__, fromMethod.__name__, fromClass.__name__, fromMethod.__name__)
    assert fromMethod.__doc__.Obj.GetResultByName(str(fromResultName)) is not None, '%s.%s.__doc__.Obj.Results does not have ResultMetadata for the %s result. You must assign metadata to this result before trying to copy it to another result.' % (fromClass.__name__, fromMethod.__name__, fromResultName)

    toModule = _GetModuleObject(toModule)
    (toMethod, toClass) = _ValidateMethodMetadata(toMethod, toClass, toModule)
    assert isinstance(toMethod.__doc__, DynamicDocString) and isinstance(toMethod.__doc__.Obj, MethodMetadata), 'The %s.%s.__doc__ must be an instance of GeoEco.Metadata.DynamicDocString, and %s.%s.__doc__.Obj must be an instance of GeoEco.Metadata.MethodMetadata. Before calling GeoEco.Metadata.CopyResultMetadata, use GeoEco.Metadata.AddMethodMetadata to add MethodMetadata to %s.%s.' % (toClass.__name__, toMethod.__name__, toClass.__name__, toMethod.__name__, toClass.__name__, toMethod.__name__)
    assert toMethod.__doc__.Obj.GetResultByName(str(toResultName)) is None, '%s.%s.__doc__.Obj.Results already has ResultMetadata for the %s result. Do not call CopyResultMetadata to copy metadata to a result that already has metadata.' % (toClass.__name__, toMethod.__name__, toResultName)

    fromResult = fromMethod.__doc__.Obj.GetResultByName(str(fromResultName))
    toMethod.__doc__.Obj.Results.append(ResultMetadata(str(toResultName),
                                                       toMethod.__doc__.Obj,
                                                       typeMetadata=copy.deepcopy(fromResult.Type),
                                                       description=fromResult._Description,
                                                       arcGISDisplayName=fromResult.ArcGISDisplayName,
                                                       arcGISParameterDependencies=copy.deepcopy(fromResult.ArcGISParameterDependencies)))


###############################################################################
# Metadata: module
###############################################################################

from .Types import *

AddModuleMetadata(shortDescription=_('Classes used to describe the modules, classes, properties, and methods in the GeoEco Python package.'))

###############################################################################
# Metadata: Metadata class
###############################################################################

AddClassMetadata(Metadata, shortDescription=_('Base class for most metadata classes.'))

# Constructor

AddMethodMetadata(Metadata.__init__,
    shortDescription=_('Constructs a new %s instance.') % Metadata.__name__)

AddArgumentMetadata(Metadata.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Metadata),
    description=_(':class:`%s` instance.') % Metadata.__name__)

AddArgumentMetadata(Metadata.__init__, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the entity.'))

AddArgumentMetadata(Metadata.__init__, 'shortDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('One-line description, ideally as plain text (but reStructuredText is OK).'))

AddArgumentMetadata(Metadata.__init__, 'longDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Detailed description, formatted as reStructuredText.'))

AddResultMetadata(Metadata.__init__, 'metadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=Metadata),
    description=_('New :class:`%s` instance.') % Metadata.__name__)

# Public properties

AddPropertyMetadata(Metadata.Name,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Name, as provided to the constructor.'))

AddPropertyMetadata(Metadata.ShortDescription,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    shortDescription=_('One-line description, ideally as plain text (but reStructuredText is OK).'),
    longDescription=_(
"""Keep the ShortDescription as concise as possible, ideally just one
sentence. *Do not* include newline characters in the ShortDescription. Put
detailed information in LongDescription (which can contain newlines)."""))

AddPropertyMetadata(Metadata.LongDescription,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    shortDescription=_('Detailed description, formatted as reStructuredText.'),
    longDescription=_(
"""LongDescription is optional; if detailed information is not needed, you
need only write a ShortDescription."""))

AddPropertyMetadata(Metadata.Object,
    typeMetadata=ClassInstanceTypeMetadata(cls=object),
    shortDescription=_('Python object to which this metadata applies.'),
    longDescription=_(
"""The type the Python object depends on which type of metadata is involved:

+---------------------------+----------------------------------+
| Type of metadata          | Type of the ``Object`` property  |
+===========================+==================================+
| :class:`ModuleMetadata`   | :py:class:`~types.ModuleType`    |
+---------------------------+----------------------------------+
| :class:`ClassMetadata`    | :py:class:`type`                 |
+---------------------------+----------------------------------+
| :class:`PropertyMetadata` | :py:class:`property`             |
+---------------------------+----------------------------------+
| :class:`MethodMetadata`   | :py:data:`~types.MethodType`     |
+---------------------------+----------------------------------+
"""))

AddPropertyMetadata(Metadata.DocString,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Python docstring (the value used for the ``__doc__`` attribute).'),
    longDescription=_('The docstring is constructed dynamically from metadata. It uses the format described in Google\'s Python Style Guide.'))

# Private method: _GetObject

AddMethodMetadata(Metadata._GetObject,
    shortDescription=_('Returns the Python object to which this metadata applies. For example, for the ClassMetadata class, this property returns Python class.'),
    longDescription=_(
"""This is called from the fget function for the Object property. Derived
classes must override this method unless they do not represent a concrete Python
object. For example, ClassMetadata._GetObject returns a Python class, but
ArgumentMetadata does not implement _GetObject, because arguments are not
concrete Python objects, they are merely part of function definitions."""))

AddArgumentMetadata(Metadata._GetObject, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Metadata),
    description=_(':class:`%s` instance.') % Metadata.__name__)

AddResultMetadata(Metadata._GetObject, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=object),
    description=_('Python object to which this metadata applies.'))

# Private method: _GetDocString

AddMethodMetadata(Metadata._GetDocString,
    shortDescription=_('Returns the Python "doc string" for the Python object to which this metadata applies (the value used for the object\'s __doc__ attribute).'),
    longDescription=_(
"""This is called from the fget function for the DocString property. Derived
classes must override this method unless they represent a type of Python object
that does not have a doc string. The base class implementation raises
NotImplementedError.

This method should return an appropriate doc string that includes
ShortDescription, LongDescription and so on. The first line should always be
ShortDescription, and should not wrap. Following lines should wrap to 80
columns."""))

AddArgumentMetadata(Metadata._GetDocString, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Metadata),
    description=_(':class:`%s` instance.') % Metadata.__name__)

AddResultMetadata(Metadata._GetDocString, 's',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Python "doc string" for the Python object to which this metadata applies.'))

###############################################################################
# Metadata: ModuleMetadata class
###############################################################################

AddClassMetadata(ModuleMetadata, shortDescription=_('Metadata that describes a Python module.'))

# Constructor

AddMethodMetadata(ModuleMetadata.__init__,
    shortDescription=_('Constructs a new %s instance.') % ModuleMetadata.__name__)

AddArgumentMetadata(ModuleMetadata.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ModuleMetadata),
    description=_(':class:`%s` instance.') % ModuleMetadata.__name__)

AddArgumentMetadata(ModuleMetadata.__init__, 'name',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Fully qualified name of the module (a.k.a. dotted module name). If :py:data:`None`, the name of the caller\'s module is used.'))

AddArgumentMetadata(ModuleMetadata.__init__, 'shortDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[2].Description)

AddArgumentMetadata(ModuleMetadata.__init__, 'longDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[3].Description)

AddResultMetadata(ModuleMetadata.__init__, 'metadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=ModuleMetadata),
    description=_('New :class:`%s` instance.') % ModuleMetadata.__name__)

# Public properties

AddPropertyMetadata(ModuleMetadata.IsExposedToPythonCallers,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, the module is part of GeoEco\'s Public API.'),
    longDescription=_(
"""The value of this property is determined by whether there are any classes
in the module that are part of the Public API. If not, this property will be
False, and the module is considered part of GeoEco's Internal API and not
recommended for use by external callers. """))

###############################################################################
# Metadata: ClassMetadata class
###############################################################################

AddClassMetadata(ClassMetadata, shortDescription=_('Metadata that describes a Python class.'))

# Public properties

AddPropertyMetadata(ClassMetadata.Module,
    typeMetadata=ClassInstanceTypeMetadata(cls=ModuleMetadata),
    shortDescription=_('%s for the module that contains this class.') % ModuleMetadata.__name__)

# Constructor

AddMethodMetadata(ClassMetadata.__init__,
    shortDescription=_('Constructs a new %s instance.') % ClassMetadata.__name__)

AddArgumentMetadata(ClassMetadata.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    description=_(':class:`%s` instance.') % ClassMetadata.__name__)

AddArgumentMetadata(ClassMetadata.__init__, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Unqualified name of the class (without module or package names).'))

AddArgumentMetadata(ClassMetadata.__init__, 'moduleMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=ModuleMetadata, canBeNone=True),
    description=_(':class:`ModuleMetadata` for the module that contains this class. If None, the caller\'s module is used.'))

AddArgumentMetadata(ClassMetadata.__init__, 'shortDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[2].Description)

AddArgumentMetadata(ClassMetadata.__init__, 'longDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[3].Description)

AddResultMetadata(ClassMetadata.__init__, 'metadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    description=_('New :class:`%s` instance.') % ClassMetadata.__name__)

# Public properties

AddPropertyMetadata(ClassMetadata.IsExposedToPythonCallers,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, the class is part of GeoEco\'s Public API.'),
    longDescription=_(
"""The value of this property is determined by whether there are any methods
or properties of the class that are part of the Public API. If not, this
property will be False, and the class is considered part of GeoEco's Internal
API and not recommended for use by external callers. """))

# Public method: ValidatePropertyAssignment

AddMethodMetadata(ClassMetadata.ValidatePropertyAssignment,
    shortDescription=_('Validates a property\'s value using the property\'s :class:`PropertyMetadata`.'),
    longDescription=_(

"""This method is intended to be called from the setter method of a property
to which a :class:`PropertyMetadata` has been added. It calls the
:func:`~GeoEco.Types.TypeMetadata.ValidateValue` method of the
:class:`~GeoEco.Types.TypeMetadata` obtained from :attr:`PropertyMetadata.Type`
for the property. :func:`~GeoEco.Types.TypeMetadata.ValidateValue` raises an
exception if the specified value does not pass whatever checks are implemented
by the :class:`~GeoEco.Types.TypeMetadata`. For example::

    from GeoEco.Internationalization import _
    import GeoEco.Metadata
    import GeoEco.Types

    class MyClass(object):

        def _GetMyProperty(self):
            return self._MyProperty

        def _SetMyProperty(self, value):
            self.__doc__.Obj.ValidatePropertyAssignment()
            self._MyProperty = value
        
        MyProperty = property(_GetMyProperty, _SetMyProperty, doc=GeoEco.Metadata.DynamicDocString())

    GeoEco.Metadata.AddModuleMetadata(shortDescription=_('This is my example module.'))

    GeoEco.Metadata.AddClassMetadata(MyClass, shortDescription=_('This is my example class.'))

    GeoEco.Metadata.AddPropertyMetadata(MyClass.MyProperty,
        typeMetadata=GeoEco.Types.UnicodeStringTypeMetadata(),
        shortDescription=_('This is my example property.'))

    c = MyClass()
    c.MyProperty = 'Hello, world!'          # This will succeed
    c.MyProperty = 1                        # 1 is not a string; ValidatePropertyAssignment will raise TypeError
"""))

AddArgumentMetadata(ClassMetadata.ValidatePropertyAssignment, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    description=_(':class:`%s` instance.') % ClassMetadata.__name__)

# Public method: ValidateMethodInvocation

AddMethodMetadata(ClassMetadata.ValidateMethodInvocation,
    shortDescription=_('Validates a classmethod\'s or instance method\'s arguments using the method\'s :class:`MethodMetadata`.'),
    longDescription=_(
"""This method is intended to be called from the top of a classmethod or
instance method to which a :class:`MethodMetadata` has been added. Do not call
it from static methods; at this time a validation function for static methods
has not been implemented.

Before performing any validation, this method initializes the calling method's
dependencies, if any are specified in the method's metadata. If any
:class:`~GeoEco.Dependencies.Dependency` initializer raises an exception, it 
will bubble up and validation will fail. Assuming all dependencies succeed,
this method then validates each of the calling method's arguments by calling
the :func:`~GeoEco.Types.TypeMetadata.ValidateValue` method of the
:class:`~GeoEco.Types.TypeMetadata` obtained from :attr:`ArgumentMetadata.Type`
for the argument. :func:`~GeoEco.Types.TypeMetadata.ValidateValue` raises an
exception if the specified value does not pass whatever checks are implemented
by the :class:`~GeoEco.Types.TypeMetadata`. For example::

    from GeoEco.Internationalization import _
    import GeoEco.Metadata
    import GeoEco.Types

    class MyClass(object):
        @classmethod
        def IncrementInteger(cls, value):
            self.__doc__.Obj.ValidateMethodInvocation()
            return value + 1

    GeoEco.Metadata.AddModuleMetadata(shortDescription=_('This is my example module.'))

    GeoEco.Metadata.AddClassMetadata(MyClass, shortDescription=_('This is my example class.'))

    GeoEco.Metadata.AddMethodMetadata(MyClass.IncrementInteger, shortDescription=_('Increments the specified integer.'))

    GeoEco.Metadata.AddArgumentMetadata(MyClass.IncrementInteger, 'cls',
        typeMetadata=GeoEco.Types.PythonClassorClassInstance(cls=MyClass),
        description=_(':class:`%s` or an instance of it.') % MyClass.__name__)

    GeoEco.Metadata.AddArgumentMetadata(MyClass.IncrementInteger, 'value',
        typeMetadata=GeoEco.Types.IntegerTypeMetadata(),
        description=_('Integer to increment.'))

    GeoEco.Metadata.AddResultMetadata(MyClass.IncrementInteger, 'newValue',
        typeMetadata=GeoEco.Types.IntegerTypeMetadata(),
        description=_('Incremented integer.'))

    x = MyClass.IncrementInteger(1)     # This will succeed
    y = MyClass.IncrementInteger('a')   # 'a' is not an int; ValidateMethodInvocation will raise TypeError

After each argument is validated, this method examines the argument's metadata
to determine if the argument has any dependencies. If it does, this method
then checks the metadata to see if the argument value requires the
dependencies to be initialized, and if so, initializes them. (By default, if
the argument is something other than :py:data:`None`, the dependencies will be
initialized. This behavior may be overridden for by subclasses of
:class:`~GeoEco.Types.TypeMetadata`.)"""))

AddArgumentMetadata(ClassMetadata.ValidateMethodInvocation, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    description=_(':class:`%s` instance.') % ClassMetadata.__name__)

###############################################################################
# Metadata: PropertyMetadata class
###############################################################################

AddClassMetadata(PropertyMetadata, shortDescription=_('Metadata that describes a property of a Python class.'))

# Constructor

AddMethodMetadata(PropertyMetadata.__init__,
    shortDescription=_('Constructs a new %s instance.') % PropertyMetadata.__name__)

AddArgumentMetadata(PropertyMetadata.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=PropertyMetadata),
    description=_(':class:`%s` instance.') % PropertyMetadata.__name__)

AddArgumentMetadata(PropertyMetadata.__init__, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the property.'))

AddArgumentMetadata(PropertyMetadata.__init__, 'classMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    description=_('The :class:`ClassMetadata` for the class that contains the property.'))

AddArgumentMetadata(PropertyMetadata.__init__, 'typeMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=TypeMetadata),
    description=_('A :class:`~GeoEco.Types.TypeMetadata` that describes the data type and allowed values of the property.'))

AddArgumentMetadata(PropertyMetadata.__init__, 'shortDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[2].Description)

AddArgumentMetadata(PropertyMetadata.__init__, 'longDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[3].Description)

AddArgumentMetadata(PropertyMetadata.__init__, 'isExposedToPythonCallers',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, the property should be part of GeoEco\'s Public API.'))

AddResultMetadata(PropertyMetadata.__init__, 'metadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=PropertyMetadata),
    description=_('New :class:`%s` instance.') % PropertyMetadata.__name__)

# Public properties

AddPropertyMetadata(PropertyMetadata.Class,
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    shortDescription=_('%s for the class that contains this property.') % ClassMetadata.__name__)

AddPropertyMetadata(PropertyMetadata.IsExposedToPythonCallers,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, this property is part of GeoEco\'s Public API.'),
    longDescription=_(
"""If False, the default, this property is considered part of GeoEco's Internal
API and not recommended for use by external callers. """))

AddPropertyMetadata(PropertyMetadata.IsReadOnly,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, this property is read only (you can get it but not set it).'))

AddPropertyMetadata(PropertyMetadata.Type,
    typeMetadata=ClassInstanceTypeMetadata(cls=TypeMetadata),
    shortDescription=_('A :class:`~GeoEco.Types.TypeMetadata` that describes the data type and allowed values of this property.'))

###############################################################################
# Metadata: MethodMetadata class
###############################################################################

AddClassMetadata(MethodMetadata, shortDescription=_('Metadata that describes a method of a Python class.'))

# Constructor

AddMethodMetadata(MethodMetadata.__init__,
    shortDescription=_('Constructs a new %s instance.') % MethodMetadata.__name__)

AddArgumentMetadata(MethodMetadata.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    description=_(':class:`%s` instance.') % MethodMetadata.__name__)

AddArgumentMetadata(MethodMetadata.__init__, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the method.'))

AddArgumentMetadata(MethodMetadata.__init__, 'classMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    description=_('The :class:`ClassMetadata` for the class that contains the method.'))

AddArgumentMetadata(MethodMetadata.__init__, 'shortDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[2].Description)

AddArgumentMetadata(MethodMetadata.__init__, 'longDescription',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=Metadata.__init__.__doc__.Obj.Arguments[3].Description)

AddArgumentMetadata(MethodMetadata.__init__, 'isExposedToPythonCallers',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, the method should be part of GeoEco\'s Public API.'))

AddArgumentMetadata(MethodMetadata.__init__, 'isExposedAsArcGISTool',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, the method should be exposed as a geoprocessing tool in MGET\'s ArcGIS toolbox.'))

AddArgumentMetadata(MethodMetadata.__init__, 'arcGISDisplayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Name of the tool, as displayed in MGET\'s ArcGIS toolbox. Ignored if `isExposedAsArcGISTool` is False.'))

AddArgumentMetadata(MethodMetadata.__init__, 'arcGISToolCategory',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Toolset that the tool appears under in MGET\'s ArcGIS toolbox. If not provided, the tool will appear at the root level. Ignored if `isExposedAsArcGISTool` is False.'))

AddArgumentMetadata(MethodMetadata.__init__, 'dependencies',
    typeMetadata=ListTypeMetadata(elementType=AnyObjectTypeMetadata()),     # We'd like to use elementType=ClassInstanceTypeMetadata(cls=Dependency), but that would require importing Dependency here, which would create a circular import. So we use AnyObjectTypeMetadata instead.
    description=_(':py:class:`list` of :class:`~GeoEco.Dependencies.Dependency` objects defining software dependencies that should be checked prior to executing this method.'))

AddResultMetadata(MethodMetadata.__init__, 'metadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    description=_('New :class:`%s` instance.') % MethodMetadata.__name__)

# Public properties

AddPropertyMetadata(MethodMetadata.Class,
    typeMetadata=ClassInstanceTypeMetadata(cls=ClassMetadata),
    shortDescription=_('%s for the class that contains this method.') % ClassMetadata.__name__)

AddPropertyMetadata(MethodMetadata.IsExposedToPythonCallers,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, this method is part of GeoEco\'s Public API.'),
    longDescription=_(
"""If False, the default, this method is considered part of GeoEco's Internal
API and not recommended for use by external callers. """))

AddPropertyMetadata(MethodMetadata.IsExposedAsArcGISTool,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, this method is exposed as a geoprocessing tool in MGET\'s ArcGIS toolbox.'))

AddPropertyMetadata(MethodMetadata.ArcGISDisplayName,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    shortDescription=_('Name of the tool, as displayed in MGET\'s ArcGIS toolbox. Ignored if :attr:`IsExposedAsArcGISTool` is False.'))

AddPropertyMetadata(MethodMetadata.ArcGISToolCategory,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    shortDescription=_('Toolset that the tool appears under in MGET\'s ArcGIS toolbox. If :py:data:`None`, the tool appears at the root level. Ignored if :attr:`IsExposedAsArcGISTool` is False.'))

AddPropertyMetadata(MethodMetadata.IsClassMethod,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if this method is a :py:func:`classmethod`.'))

AddPropertyMetadata(MethodMetadata.IsInstanceMethod,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if this method is an instance method (not a :py:func:`classmethod` or :py:func:`staticmethod`).'))

AddPropertyMetadata(MethodMetadata.IsStaticMethod,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if this method is a :py:func:`staticmethod`.'))

AddPropertyMetadata(MethodMetadata.Arguments,
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=ArgumentMetadata)),
    shortDescription=_(':py:class:`list` of :class:`ArgumentMetadata` objects describing each of this method\'s arguments.'),
    longDescription=_(
"""We recommend using :func:`AddArgumentMetadata` to add them, rather than
modifying the :attr:`Arguments` property directly."""))

AddPropertyMetadata(MethodMetadata.Dependencies,
    typeMetadata=ListTypeMetadata(elementType=AnyObjectTypeMetadata()),     # We'd like to use elementType=ClassInstanceTypeMetadata(cls=Dependency), but that would require importing Dependency here, which would create a circular import. So we use AnyObjectTypeMetadata instead.
    shortDescription=_(':py:class:`list` of :class:`~GeoEco.Dependencies.Dependency` objects defining software dependencies that are checked prior to executing this method.'),
    longDescription=_(
"""The dependencies are checked by
:func:`ClassMetadata.ValidateMethodInvocation`, which is traditionally placed at
the top of the method's implementation. See
:func:`ClassMetadata.ValidateMethodInvocation` for an example."""))

AddPropertyMetadata(MethodMetadata.Results,
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=ResultMetadata)),
    shortDescription=_(':py:class:`list` of :class:`ResultMetadata` objects describing each of this method\'s return values.'),
    longDescription=_(
"""We recommend using :func:`AddResultMetadata` to add them, rather than
modifying the :attr:`Results` property directly. If the method does not return
a value, leave :attr:`Results` an empty list."""))

# Public method: GetArgumentByName

AddMethodMetadata(MethodMetadata.GetArgumentByName,
    shortDescription=_('Returns the :class:`ArgumentMetadata` for an argument given its name.'),
    longDescription=_(
"""Returns :py:data:`None` if the method doesn't have an argument with the
requested name, or if an :class:`ArgumentMetadata` has not been added to this
:class:`MethodMetadata` yet."""))

AddArgumentMetadata(MethodMetadata.GetArgumentByName, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    description=_(':class:`%s` instance.') % MethodMetadata.__name__)

AddArgumentMetadata(MethodMetadata.GetArgumentByName, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the argument.'))

AddResultMetadata(MethodMetadata.GetArgumentByName, 'arg',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArgumentMetadata, canBeNone=True),
    description=_('The %s instance for the argument.') % ArgumentMetadata.__name__)

# Public method: GetResultByName

AddMethodMetadata(MethodMetadata.GetResultByName,
    shortDescription=_('Returns the :class:`ResultMetadata` for a return value given its name.'),
    longDescription=_(
"""Returns :py:data:`None` a :class:`ResultMetadata` with the given name has
not been added to this :class:`MethodMetadata` yet."""))

AddArgumentMetadata(MethodMetadata.GetResultByName, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    description=_(':class:`%s` instance.') % MethodMetadata.__name__)

AddArgumentMetadata(MethodMetadata.GetResultByName, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the return value.'))

AddResultMetadata(MethodMetadata.GetResultByName, 'arg',
    typeMetadata=ClassInstanceTypeMetadata(cls=ResultMetadata, canBeNone=True),
    description=_('The %s instance for the return value.') % ResultMetadata.__name__)

###############################################################################
# Metadata: ArgumentMetadata class
###############################################################################

AddClassMetadata(ArgumentMetadata, shortDescription=_('Metadata that describes a parameter of a method of a Python class.'))

# Constructor

AddMethodMetadata(ArgumentMetadata.__init__,
    shortDescription=_('Constructs a new %s instance.') % ArgumentMetadata.__name__)

AddArgumentMetadata(ArgumentMetadata.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArgumentMetadata),
    description=_(':class:`%s` instance.') % ArgumentMetadata.__name__)

AddArgumentMetadata(ArgumentMetadata.__init__, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the parameter, as it appears in the method\'s signature.'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'methodMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    description=_('The :class:`MethodMetadata` for the method.'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'typeMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=TypeMetadata),
    description=_('A :class:`~GeoEco.Types.TypeMetadata` that describes the data type and allowed values of this parameter.'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'description',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('The parameter\'s description, ideally one line of plain text (but reStructuredText is OK). Put long details in :attr:`MethodMetadata.LongDescription`.'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'direction',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Input', 'Output']),
    description=_('Direction of the parameter, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'initializeToArcGISGeoprocessorVariable',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('The parameter value should be obtained from this geoprocessor variable, rather than from the user as a tool parameter, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'arcGISDisplayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Name of the parameter as it should appear in ArcGIS, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'arcGISCategory',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Category of the parameter as it should appear in ArcGIS, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'arcGISParameterDependencies',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), canBeNone=True),
    description=_(':py:class:`list` of names of parameters that this parameter is dependent on (see ArcGIS documentation), when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).'))

AddArgumentMetadata(ArgumentMetadata.__init__, 'dependencies',
    typeMetadata=ListTypeMetadata(elementType=AnyObjectTypeMetadata()),     # We'd like to use elementType=ClassInstanceTypeMetadata(cls=Dependency), but that would require importing Dependency here, which would create a circular import. So we use AnyObjectTypeMetadata instead.
    description=_(':py:class:`list` of :class:`~GeoEco.Dependencies.Dependency` objects defining software dependencies that should be checked when the value provided for this parameter is not :py:data:`None` when the method is called (ignored otherwise).'))

AddResultMetadata(ArgumentMetadata.__init__, 'metadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArgumentMetadata),
    description=_('New :class:`%s` instance.') % ArgumentMetadata.__name__)

# Public properties

AddPropertyMetadata(ArgumentMetadata.Name,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[1].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[1]._Description)

AddPropertyMetadata(ArgumentMetadata.Method,
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    shortDescription=_('%s for the class that contains this method.') % MethodMetadata.__name__)

AddPropertyMetadata(ArgumentMetadata.Type,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[3].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[3]._Description)

AddPropertyMetadata(ArgumentMetadata.Description,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[4].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[4]._Description)

AddPropertyMetadata(ArgumentMetadata.Direction,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[5].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[5]._Description)

AddPropertyMetadata(ArgumentMetadata.InitializeToArcGISGeoprocessorVariable,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[6].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[6]._Description)

AddPropertyMetadata(ArgumentMetadata.ArcGISDisplayName,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[7].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[7]._Description)

AddPropertyMetadata(ArgumentMetadata.ArcGISCategory,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[8].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[8]._Description)

AddPropertyMetadata(ArgumentMetadata.ArcGISParameterDependencies,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[9].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[9]._Description)

AddPropertyMetadata(ArgumentMetadata.Dependencies,
    typeMetadata=ArgumentMetadata.__init__.__doc__.Obj.Arguments[10].Type,
    shortDescription=ArgumentMetadata.__init__.__doc__.Obj.Arguments[10]._Description)

AddPropertyMetadata(ArgumentMetadata.IsFormalParameter,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if the parameter is the default kind of parameter in Python, known in Python as a :py:term:`positional-or-keyword <parameter>` parameter.'))

AddPropertyMetadata(ArgumentMetadata.IsArbitraryArgumentList,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if the parameter an arbitrary sequence of positional arguments, traditionally written ``*args`` in the method signature and known in Python as the :py:term:`var-positional <parameter>` parameter.'))

AddPropertyMetadata(ArgumentMetadata.IsKeywordArgumentDictionary,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if the parameter a dictionary of arbitrarily many keyword arguments, traditionally written ``**kwargs`` in the method signature and known in Python as the :py:term:`var-keyword <parameter>` parameter.'))

AddPropertyMetadata(ArgumentMetadata.HasDefault,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('True if the parameter has a default value defined in the method signature. If so, the parameter is optional.'))

AddPropertyMetadata(ArgumentMetadata.Default,
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    shortDescription=_('The default value of the parameter as defined in the method signature, if :attr:`HasDefault` is True. :py:data:`None` otherwise.'))

###############################################################################
# Metadata: ResultMetadata class
###############################################################################

AddClassMetadata(ResultMetadata, shortDescription=_('Metadata that describes the value returned by a method of a Python class.'))

# Constructor

AddMethodMetadata(ResultMetadata.__init__,
    shortDescription=_('Constructs a new %s instance.') % ResultMetadata.__name__)

AddArgumentMetadata(ResultMetadata.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ResultMetadata),
    description=_(':class:`%s` instance.') % ResultMetadata.__name__)

AddArgumentMetadata(ResultMetadata.__init__, 'name',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the return value. Although Python does not give names to return values, they are needed when a method is exposed as an ArcGIS goeprocessing tool, and can be useful in other contexts.'))

AddArgumentMetadata(ResultMetadata.__init__, 'methodMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    description=_('The :class:`MethodMetadata` for the method.'))

AddArgumentMetadata(ResultMetadata.__init__, 'typeMetadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=TypeMetadata),
    description=_('A :class:`~GeoEco.Types.TypeMetadata` that describes the data type and allowed values of this return value.'))

AddArgumentMetadata(ResultMetadata.__init__, 'description',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Return value description, ideally one line of plain text (but reStructuredText is OK). Put long details in :attr:`MethodMetadata.LongDescription`.'))

AddArgumentMetadata(ResultMetadata.__init__, 'arcGISDisplayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_('Name of the return value as it should appear in ArcGIS, when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).'))

AddArgumentMetadata(ResultMetadata.__init__, 'arcGISParameterDependencies',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), canBeNone=True),
    description=_(':py:class:`list` of names of parameters that this return value is dependent on (see ArcGIS documentation), when the method is exposed as an ArcGIS geoprocessing tool (ignored otherwise).'))

AddResultMetadata(ResultMetadata.__init__, 'metadata',
    typeMetadata=ClassInstanceTypeMetadata(cls=ResultMetadata),
    description=_('New :class:`%s` instance.') % ResultMetadata.__name__)

# Public properties

AddPropertyMetadata(ResultMetadata.Name,
    typeMetadata=ResultMetadata.__init__.__doc__.Obj.Arguments[1].Type,
    shortDescription=ResultMetadata.__init__.__doc__.Obj.Arguments[1]._Description)

AddPropertyMetadata(ResultMetadata.Method,
    typeMetadata=ClassInstanceTypeMetadata(cls=MethodMetadata),
    shortDescription=_('%s for the class that contains this method.') % MethodMetadata.__name__)

AddPropertyMetadata(ResultMetadata.Type,
    typeMetadata=ResultMetadata.__init__.__doc__.Obj.Arguments[3].Type,
    shortDescription=ResultMetadata.__init__.__doc__.Obj.Arguments[3]._Description)

AddPropertyMetadata(ResultMetadata.Description,
    typeMetadata=ResultMetadata.__init__.__doc__.Obj.Arguments[4].Type,
    shortDescription=ResultMetadata.__init__.__doc__.Obj.Arguments[4]._Description)

AddPropertyMetadata(ResultMetadata.ArcGISDisplayName,
    typeMetadata=ResultMetadata.__init__.__doc__.Obj.Arguments[5].Type,
    shortDescription=ResultMetadata.__init__.__doc__.Obj.Arguments[5]._Description)

AddPropertyMetadata(ResultMetadata.ArcGISParameterDependencies,
    typeMetadata=ResultMetadata.__init__.__doc__.Obj.Arguments[6].Type,
    shortDescription=ResultMetadata.__init__.__doc__.Obj.Arguments[6]._Description)

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['Metadata',
           'ModuleMetadata',
           'ClassMetadata',
           'PropertyMetadata',
           'MethodMetadata',
           'ArgumentMetadata',
           'ResultMetadata',
           'AddModuleMetadata',
           'AddClassMetadata',
           'AddPropertyMetadata',
           'CopyPropertyMetadata',
           'AddMethodMetadata',
           'AddArgumentMetadata',
           'AddResultMetadata',
           'CopyArgumentMetadata',
           'CopyResultMetadata']
