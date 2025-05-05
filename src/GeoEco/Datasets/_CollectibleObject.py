# _CollectibleObject.py - Defines CollectibleObject, the base class for most
# Datasets classes.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import atexit
import logging
import os
import shutil
import types
import weakref

from ..Dependencies import PythonModuleDependency
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Types import DateTimeTypeMetadata, FloatTypeMetadata, IntegerTypeMetadata, UnicodeStringTypeMetadata 


class CollectibleObject(object):
    __doc__ = DynamicDocString()

    # Public properties and methods

    def _GetDisplayNameProp(self):
        return self._GetDisplayName()

    DisplayName = property(_GetDisplayNameProp, doc=DynamicDocString())

    def _GetParentCollection(self):
        return self._ParentCollection

    ParentCollection = property(_GetParentCollection, doc=DynamicDocString())

    def GetQueryableAttribute(self, name):
        self.__doc__.Obj.ValidateMethodInvocation()

        obj = self
        while obj is not None:
            if obj._QueryableAttributes is not None:
                for attr in obj._QueryableAttributes:
                    if attr.Name == name:
                        return attr
            obj = obj.ParentCollection

        return None

    def GetQueryableAttributesWithDataType(self, typeMetadata):
        self.__doc__.Obj.ValidateMethodInvocation()

        attrs = []
        obj = self
        while obj is not None:
            if obj._QueryableAttributes is not None:
                for attr in obj._QueryableAttributes:
                    if issubclass(attr.DataType.__class__, typeMetadata):
                        attrs.append(attr)
            obj = obj.ParentCollection

        return attrs

    def GetAllQueryableAttributes(self):
        self.__doc__.Obj.ValidateMethodInvocation()

        attrs = []
        obj = self
        while obj is not None:
            if obj._QueryableAttributes is not None:
                for attr in obj._QueryableAttributes:
                    attrs.append(attr)
            obj = obj.ParentCollection

        return attrs

    def GetQueryableAttributeValue(self, name):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Check whether the value has been explicitly assigned to us
        # or our parents.

        obj = self
        while obj is not None:
            if obj._QueryableAttributeValues is not None:
                if name in obj._QueryableAttributeValues:
                    return obj._QueryableAttributeValues[name]
            obj = obj.ParentCollection

        # Check whether the value is derived from another queryable
        # attribute.

        thisAttr = self.GetQueryableAttribute(name)
        if thisAttr is not None and thisAttr.DerivedFromAttr is not None:
            derivedFromValue = self.GetQueryableAttributeValue(thisAttr.DerivedFromAttr)
            if derivedFromValue is not None:
                if thisAttr.DerivedValueMap is not None:
                    if derivedFromValue in thisAttr.DerivedValueMap:
                        return thisAttr.DerivedValueMap[derivedFromValue]
                else:
                    return thisAttr.DerivedValueFunc(self, derivedFromValue)

        # We did not find it. Return None.

        return None

    def GetLazyPropertyValue(self, name, allowPhysicalValue=True):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Check whether value is cached in our dictionary or our
        # parents' dictionaries.

        obj = self
        while obj is not None:
            if obj._LazyPropertyValues is not None and name in obj._LazyPropertyValues:
                return obj._LazyPropertyValues[name]
            obj = obj.ParentCollection

        # Check whether the value is assigned by a queryable
        # attribute.

        obj = self
        while obj is not None:
            if obj._QueryableAttributes is not None:
                for attr in obj._QueryableAttributes:
                    if attr.DerivedLazyDatasetProps is not None:
                        attrValue = self.GetQueryableAttributeValue(attr.Name)
                        if attrValue in attr.DerivedLazyDatasetProps and name in attr.DerivedLazyDatasetProps[attrValue]:
                            value = attr.DerivedLazyDatasetProps[attrValue][name]
                            self.SetLazyPropertyValue(name, value)
                            return value
            obj = obj.ParentCollection

        # If allowed, retrieve the value from physical storage. This
        # is typically slow and could involve downloading and/or
        # decompressing the dataset into a cache directory, if this is
        # the first time it is being physically accessed.

        if not allowPhysicalValue:
            return None

        value = self._GetLazyPropertyPhysicalValue(name)
        self.SetLazyPropertyValue(name, value)
        return value

    def SetLazyPropertyValue(self, name, value):
        self.__doc__.Obj.ValidateMethodInvocation()
        if self._LazyPropertyValues is None:
            self._LazyPropertyValues = {}
        self._LazyPropertyValues[name] = value

    def DeleteLazyPropertyValue(self, name):
        self.__doc__.Obj.ValidateMethodInvocation()
        if self._LazyPropertyValues is not None and name in self._LazyPropertyValues:
            del self._LazyPropertyValues[name]

    def HasLazyPropertyValue(self, name, allowPhysicalValue=True):
        self.__doc__.Obj.ValidateMethodInvocation()
        return self.GetLazyPropertyValue(name, allowPhysicalValue) is not None

    def Close(self):
        try:
            self._Close()
        except:
            pass

    @classmethod
    def TestCapability(cls, capability):
        cls.__doc__.Obj.ValidateMethodInvocation()
        return cls._TestCapability(capability)

    def __init__(self, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.
        
        self._ParentCollection = parentCollection
        self._QueryableAttributes = None

        self._QueryableAttributeValues = {}
        if queryableAttributeValues is not None:
            self._QueryableAttributeValues.update(queryableAttributeValues)

        self._LazyPropertyValues = {}
        if lazyPropertyValues is not None:
            self._LazyPropertyValues.update(lazyPropertyValues)

        self._TempDirectories = None

        # If the caller wants to define queryable attributes, perform
        # additional validation.

        if queryableAttributes is not None:

            # Validate that the caller is not trying to define a
            # queryable attribute that has already been defined by our
            # chain of parent collections.

            for qa in queryableAttributes:
                if self.GetQueryableAttribute(qa.Name) is not None:
                    raise ValueError(_('QueryableAttribute %(name)s has already been defined by a parent collection.') % {'name': qa.Name})

            # Validate that there is no more than one queryable
            # attribute with data type DateTimeTypeMetadata among the
            # attributes we define and our chain of parent
            # collections.

            foundDateTime = False

            collection = parentCollection
            while collection is not None:
                if collection._QueryableAttributes is not None:
                    for qa in collection._QueryableAttributes:
                        if isinstance(qa.DataType, DateTimeTypeMetadata):
                            foundDateTime = True
                            break
                collection = collection.ParentCollection
            
            for qa in queryableAttributes:
                if isinstance(qa.DataType, DateTimeTypeMetadata):
                    if foundDateTime:
                        raise ValueError(_('Only one QueryableAttribute with data type DateTimeTypeMetadata may be defined for this object and its chain of parent collections.'))
                    foundDateTime = True

            self._QueryableAttributes = queryableAttributes

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Close()
        return False  # Ensure any exceptions are propagated

    def __del__(self):
        self.Close()
        # super(CollectibleObject, self).__del__()    # Because object apparently does not have a __del__, this call results in AttributeError: 'super' object has no attribute '__del__'

    # Private methods that the derived class may override

    def _GetDisplayName(self):
        raise NotImplementedError(_('The _GetDisplayName method of class %s has not been implemented.') % self.__class__.__name__)

    def _GetLazyPropertyPhysicalValue(self, name):
        return None

    def _Close(self):                               # If you override, be sure to call the base class at the end of your implementation!
        if hasattr(self, '_TempDirectories') and self._TempDirectories is not None:
            while len(self._TempDirectories) > 0:
                self._LogDebug(_('%(class)s 0x%(id)016X: Deleting temporary directory %(dir)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dir': self._TempDirectories[0]})
                try:
                    shutil.rmtree(self._TempDirectories[0], onerror=CollectibleObject._LogFailedRemoval)
                except:
                    pass
                del self._TempDirectories[0]

        self._UnregisterForCloseAtExit()

    @classmethod
    def _TestCapability(cls, capability):
        if isinstance(cls, CollectibleObject):
            raise NotImplementedError(_('The _TestCapability method of class %s has not been implemented.') % cls.__class__.__name__)
        else:
            raise NotImplementedError(_('The _TestCapability method of class %s has not been implemented.') % cls.__name__)

    # Private properties and methods that the derived class may access
    # but generally does not override

    def _RegisterForCloseAtExit(self):
        if not hasattr(CollectibleObject, '_ObjectsToCloseAtExit'):
            CollectibleObject._ObjectsToCloseAtExit = []

        for r in CollectibleObject._ObjectsToCloseAtExit:
            if r() == self:
                return

        CollectibleObject._ObjectsToCloseAtExit.insert(0, weakref.ref(self))

    def _CreateTempDirectory(self):
        import tempfile
        tempDir = tempfile.mkdtemp(prefix='GeoEco_' + self.__class__.__name__ + '_Temp_')
        self._LogDebug(_('%(class)s 0x%(id)016X: Created temporary directory %(dir)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dir': tempDir})
        
        if self._TempDirectories is None:
            self._TempDirectories = []
        self._TempDirectories.insert(0, tempDir)

        self._RegisterForCloseAtExit()

        return tempDir

    @classmethod
    def _RequireCapability(cls, capability):
        error = cls._TestCapability(capability.lower())
        if error is not None:
            raise error

    @classmethod
    def _ogr(cls):
        if not hasattr(CollectibleObject, '_OGRModule'):
            cls._gdal()    # Calling this so that osgeo.gdal will be imported first and osgeo.gdal.UseExceptions() will be invoked
            from osgeo import ogr
            setattr(CollectibleObject, '_OGRModule', ogr)
            
            setattr(CollectibleObject, '_GeometryTypeForOGRGeometry', {ogr.wkbNone: None,
                                                                       ogr.wkbPoint: 'Point',
                                                                       ogr.wkbLineString: 'LineString',
                                                                       ogr.wkbPolygon: 'Polygon',
                                                                       ogr.wkbMultiPoint: 'MultiPoint',
                                                                       ogr.wkbMultiLineString: 'MultiLineString',
                                                                       ogr.wkbMultiPolygon: 'MultiPolygon',
                                                                       ogr.wkbGeometryCollection: 'GeometryCollection',
                                                                       ogr.wkbPoint25D: 'Point25D',
                                                                       ogr.wkbLineString25D: 'LineString25D',
                                                                       ogr.wkbPolygon25D: 'Polygon25D',
                                                                       ogr.wkbMultiPoint25D: 'MultiPoint25D',
                                                                       ogr.wkbMultiLineString25D: 'MultiLineString25D',
                                                                       ogr.wkbMultiPolygon25D: 'MultiPolygon25D',
                                                                       ogr.wkbGeometryCollection25D: 'GeometryCollection25D'})
            
            setattr(CollectibleObject, '_OGRGeometryForGeometryType', {None: ogr.wkbNone,
                                                                       'Point': ogr.wkbPoint,
                                                                       'LineString': ogr.wkbLineString,
                                                                       'Polygon': ogr.wkbPolygon,
                                                                       'MultiPoint': ogr.wkbMultiPoint,
                                                                       'MultiLineString': ogr.wkbMultiLineString,
                                                                       'MultiPolygon': ogr.wkbMultiPolygon,
                                                                       'GeometryCollection': ogr.wkbGeometryCollection,
                                                                       'Point25D': ogr.wkbPoint25D,
                                                                       'LineString25D': ogr.wkbLineString25D,
                                                                       'Polygon25D': ogr.wkbPolygon25D,
                                                                       'MultiPoint25D': ogr.wkbMultiPoint25D,
                                                                       'MultiLineString25D': ogr.wkbMultiLineString25D,
                                                                       'MultiPolygon25D': ogr.wkbMultiPolygon25D,
                                                                       'GeometryCollection25D': ogr.wkbGeometryCollection25D})
        return CollectibleObject._OGRModule

    @classmethod
    def _osr(cls):
        if not hasattr(CollectibleObject, '_OSRModule'):
            cls._gdal()    # Calling this so that osgeo.gdal will be imported first and osgeo.gdal.UseExceptions() will be invoked
            from osgeo import osr
            setattr(CollectibleObject, '_OSRModule', osr)
        return CollectibleObject._OSRModule

    @classmethod
    def _gdal(cls):
        if not hasattr(CollectibleObject, '_GDALModule'):
            d = PythonModuleDependency(importName='osgeo', displayName='Python bindings for the Geospatial Data Abstraction Library (GDAL)', cheeseShopName='GDAL')
            d.Initialize()
            from osgeo import gdal
            gdal.UseExceptions()
            setattr(CollectibleObject, '_GDALModule', gdal)
        return CollectibleObject._GDALModule

    @classmethod
    def _gdalconst(cls):
        if not hasattr(CollectibleObject, '_GDALConstModule'):
            cls._gdal()    # Calling this so that osgeo.gdal will be imported first and osgeo.gdal.UseExceptions() will be invoked
            from osgeo import gdalconst
            setattr(CollectibleObject, '_GDALConstModule', gdalconst)
        return CollectibleObject._GDALConstModule

    @classmethod
    def _Str(cls, s):
        if isinstance(s, str):
            return s
        return str(s)

    _LoggingChannel = 'GeoEco.Datasets'

    @classmethod
    def _GetLogger(cls):
        try:
            return logging.getLogger(CollectibleObject._LoggingChannel)
        except:
            return None

    @classmethod
    def _LogDebug(cls, format, *args, **kwargs):
        try:
            logging.getLogger(CollectibleObject._LoggingChannel).debug(format, *args, **kwargs)
        except:
            pass

    @classmethod
    def _LogInfo(cls, format, *args, **kwargs):
        try:
            logging.getLogger(CollectibleObject._LoggingChannel).info(format, *args, **kwargs)
        except:
            pass

    @classmethod
    def _LogWarning(cls, format, *args, **kwargs):
        try:
            logging.getLogger(CollectibleObject._LoggingChannel).warning(format, *args, **kwargs)
        except:
            pass

    @classmethod
    def _LogError(cls, format, *args, **kwargs):
        try:
            logging.getLogger(CollectibleObject._LoggingChannel).error(format, *args, **kwargs)
        except:
            pass

    @classmethod
    def _DebugLoggingEnabled(cls):
        return logging.getLogger('GeoEco.Datasets').isEnabledFor(logging.DEBUG)

    # Private methods that the derived class should not use

    def _UnregisterForCloseAtExit(self):
        if hasattr(CollectibleObject, '_ObjectsToCloseAtExit'):
            for i, r in enumerate(CollectibleObject._ObjectsToCloseAtExit):
                if r() == self:
                    del CollectibleObject._ObjectsToCloseAtExit[i]
                    return

    @staticmethod
    def _CloseObjectsAtExit():
        if hasattr(CollectibleObject, '_ObjectsToCloseAtExit'):
            while len(CollectibleObject._ObjectsToCloseAtExit) > 0:
                if CollectibleObject._ObjectsToCloseAtExit[0]() is None:        # Should never happen because CollectibleObject.__del__() removes the object from the list
                    del CollectibleObject._ObjectsToCloseAtExit[0]
                else:
                    CollectibleObject._ObjectsToCloseAtExit[0]()._Close()       # This will remove it from the list.

    @staticmethod
    def _LogFailedRemoval(function, path, excinfo):
        try:
            logger = logging.getLogger('GeoEco.Datasets')
            if function == os.remove:
                logger.warning(_('Could not delete temporary file %(path)s due to %(error)s: %(msg)s') % {'path' : path, 'error' : excinfo[0].__name__, 'msg' : str(excinfo[1])})
            elif function == os.rmdir:
                logger.warning(_('Could not delete temporary directory %(path)s due to %(error)s: %(msg)s') % {'path' : path, 'error' : excinfo[0].__name__, 'msg' : str(excinfo[1])})
            else:
                logger.warning(_('Could not delete temporary directory %(path)s. The directory contents could not be listed due to %(error)s: %(msg)s') % {'path' : path, 'error' : excinfo[0].__name__, 'msg' : str(excinfo[1])})
        except:
            pass

atexit.register(CollectibleObject._CloseObjectsAtExit)


class QueryableAttribute(object):
    __doc__ = DynamicDocString()

    def _GetName(self):
        return self._Name

    Name = property(_GetName, doc=DynamicDocString())

    def _GetDisplayName(self):
        return self._DisplayName

    DisplayName = property(_GetDisplayName, doc=DynamicDocString())

    def _GetDataType(self):
        return self._DataType

    DataType = property(_GetDataType, doc=DynamicDocString())

    def _GetDerivedLazyDatasetProps(self):
        return self._DerivedLazyDatasetProps

    DerivedLazyDatasetProps = property(_GetDerivedLazyDatasetProps, doc=DynamicDocString())

    def _GetDerivedFromAttr(self):
        return self._DerivedFromAttr

    DerivedFromAttr = property(_GetDerivedFromAttr, doc=DynamicDocString())

    def _GetDerivedValueMap(self):
        return self._DerivedValueMap

    DerivedValueMap = property(_GetDerivedValueMap, doc=DynamicDocString())

    def _GetDerivedValueFunc(self):
        return self._DerivedValueFunc

    DerivedValueFunc = property(_GetDerivedValueFunc, doc=DynamicDocString())

    def __init__(self, name, displayName, dataType, derivedLazyDatasetProps=None, derivedFromAttr=None, derivedValueMap=None, derivedValueFunc=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        if not isinstance(dataType, (UnicodeStringTypeMetadata, IntegerTypeMetadata, FloatTypeMetadata, DateTimeTypeMetadata)):
            raise TypeError(_('%(type)s is not an allowed data type for queryable attributes. Queryable attributes may only have the following data types: UnicodeStringTypeMetadata, IntegerTypeMetadata, FloatTypeMetadata, DateTimeTypeMetadata.') % {'type': dataType.__class__.__name__})

        if derivedFromAttr is not None and (derivedValueMap is None and derivedValueFunc is None or derivedValueMap is not None and derivedValueFunc is not None):
            raise TypeError(_('If the derivedFromAttr parameter is not None, a value must be provided for either derivedValueMap or derivedValueFunc, but not for both.'))

        if derivedValueFunc is not None and not isinstance(derivedValueFunc, (types.FunctionType, types.MethodType)):
            raise TypeError(_('The type of the derivedValueFunc parameter (%(type)s) is not an allowed type. It must be a function, a method, or None.') % {'type': str(type(derivedValueFunc))})

        self._Name = name
        self._DisplayName = displayName
        self._DataType = dataType
        self._DerivedLazyDatasetProps = derivedLazyDatasetProps
        self._DerivedFromAttr = derivedFromAttr
        self._DerivedValueMap = derivedValueMap
        self._DerivedValueFunc = derivedValueFunc


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
