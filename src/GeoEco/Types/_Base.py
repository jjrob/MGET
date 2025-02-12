# _Base.py - Classes derived from ..Metadata.TypeMetadata that represent basic
# Python types such as integers, floats, and strings.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

##### THIS MODULE IS NOT MEANT TO BE IMPORTED DIRECTLY. IMPORT Types.py INSTEAD. #####

import datetime
import inspect
import pathlib
import re
import time
import xml.dom

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _


# Private helper function for raising exceptions

def _RaiseException(e):
    raise e


# Base class for metadata classes that describe the values that class properties and method arguments and return values can take.

class TypeMetadata(object):
    __doc__ = DynamicDocString()

    def __init__(self, 
                 pythonType, 
                 canBeNone=False, 
                 allowedValues=None, 
                 arcGISType=None, 
                 arcGISAssembly=None, 
                 canBeArcGISInputParameter=False, 
                 canBeArcGISOutputParameter=False, 
                 sphinxMarkup=None):

        assert isinstance(pythonType, type), 'pythonType must be a type.'
        assert isinstance(canBeNone, bool), 'canBeNone must be a boolean.'
        assert isinstance(allowedValues, (type(None), list, tuple)), 'allowedValues must be a list or tuple of values, or None.'
        if isinstance(allowedValues, tuple):
            allowedValues = list(allowedValues)
        assert arcGISType is None and arcGISAssembly is None or isinstance(arcGISType, str) and isinstance(arcGISAssembly, str), 'arcGISType and arcGISAssembly must both be strings or both be None.'
        assert isinstance(canBeArcGISInputParameter, bool), 'canBeArcGISInputParameter must be a boolean.'
        assert isinstance(canBeArcGISOutputParameter, bool), 'canBeArcGISOutputParameter must be a boolean.'
        assert isinstance(sphinxMarkup, (type(None), str)), 'sphinxMarkup must be a str or None.'
        self._PythonType = pythonType
        self._CanBeNone = canBeNone
        self._AllowedValues = allowedValues
        self._ArcGISType = arcGISType
        self._ArcGISAssembly = arcGISAssembly
        self._CanBeArcGISInputParameter = canBeArcGISInputParameter
        self._CanBeArcGISOutputParameter = canBeArcGISOutputParameter
        self._SphinxMarkup = sphinxMarkup

    def _GetPythonType(self):
        return self._PythonType
    
    PythonType = property(_GetPythonType, doc=DynamicDocString())

    def _GetCanBeNone(self):
        return self._CanBeNone

    def _SetCanBeNone(self, value):
        assert isinstance(value, bool), 'CanBeNone must be a boolean.'
        self._CanBeNone = value
    
    CanBeNone = property(_GetCanBeNone, _SetCanBeNone, doc=DynamicDocString())

    def _GetAllowedValues(self):
        return self._AllowedValues
    
    AllowedValues = property(_GetAllowedValues, doc=DynamicDocString())

    def _GetArcGISType(self):
        return self._ArcGISType
    
    ArcGISType = property(_GetArcGISType, doc=DynamicDocString())

    def _GetArcGISAssembly(self):
        return self._ArcGISAssembly
    
    ArcGISAssembly = property(_GetArcGISAssembly, doc=DynamicDocString())

    def _GetCanBeArcGISInputParameter(self):
        return self._CanBeArcGISInputParameter
    
    CanBeArcGISInputParameter = property(_GetCanBeArcGISInputParameter, doc=DynamicDocString())

    def _GetCanBeArcGISInputParameter(self):
        return self._CanBeArcGISInputParameter
    
    CanBeArcGISInputParameter = property(_GetCanBeArcGISInputParameter, doc=DynamicDocString())

    def _GetCanBeArcGISOutputParameter(self):
        return self._CanBeArcGISOutputParameter
    
    CanBeArcGISOutputParameter = property(_GetCanBeArcGISOutputParameter, doc=DynamicDocString())

    def _GetPythonTypeDescriptionBase(self):
        return self._GetPythonTypeDescription()
    
    PythonTypeDescription = property(_GetPythonTypeDescriptionBase, doc=DynamicDocString())

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            if self.CanBeNone:
                return _('instances of %(type)s or %(noneType)s') % {'type': str(self.PythonType), 'noneType': str(type(None))}
            else:
                return _('instances of %(type)s') % {'type': str(self.PythonType)}
        if self.CanBeNone:
            return _('instance of %(type)s or %(noneType)s') % {'type': str(self.PythonType), 'noneType': str(type(None))}
        else:
            return _('instance of %(type)s') % {'type': str(self.PythonType)}

    def _GetArcGISDataTypeDict(self):
        raise NotImplementedError(_('%(cls)s has not implemented _GetArcGISDataTypeDict().') % {'cls': self.__class__.__name__})

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):
        raise NotImplementedError(_('%(cls)s has not implemented _GetArcGISDomainDict().') % {'cls': self.__class__.__name__})

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def _GetSphinxMarkup(self):
        if self._SphinxMarkup is not None:
            return self._SphinxMarkup
        return self.PythonTypeDescription
    
    SphinxMarkup = property(_GetSphinxMarkup, doc=DynamicDocString())

    def GetConstraintDescriptionStrings(self):
        if self.AllowedValues is not None and len(self.AllowedValues) > 0:
            return ['Allowed values: ' + ', '.join(['``' + repr(av) + '``' for av in self.AllowedValues])]
        return []

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        if value is None:
            if not self.CanBeNone:
                from ..Logging import Logger
                Logger.RaiseException(TypeError(_('The %s is required. Please provide a value.') % variableName))
        else:
            if not isinstance(value, self.PythonType):
                from ..Logging import Logger
                Logger.RaiseException(TypeError(_('The value provided for the %(variable)s is an instance of %(badType)s, an invalid type. Please provide an instance of %(goodType)s.') % {'variable' : variableName, 'badType' : type(value), 'goodType' : self.PythonType}))
            if self.AllowedValues is not None:
                if issubclass(self.PythonType, str):
                    allowedValues = list(map(str.lower, self.AllowedValues))
                    if value.lower() not in allowedValues:
                        from ..Logging import Logger
                        Logger.RaiseException(ValueError(_('The value provided for the %(variable)s is not an allowed value. Please provide one of the following: %(values)s. (These values are not case-sensitive.)') % {'variable' : variableName, 'values' : ', '.join(map(str, allowedValues))}))
                else:
                    if value not in self.AllowedValues:
                        from ..Logging import Logger
                        Logger.RaiseException(ValueError(_('The value provided for the %(variable)s is not an allowed value. Please provide one of the following: %(values)s.') % {'variable' : variableName, 'values' : ', '.join(map(str, self.AllowedValues))}))
        return (False, value)

    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        assert isinstance(paramString, str), 'paramString must be a string'
        assert isinstance(paramDisplayName, str), 'paramDisplayName must be a string'
        assert isinstance(paramIndex, int) and paramIndex > 0, 'paramIndex must be an integer greater than zero'

        # If this type of parameter cannot be an ArcGIS input parameter, it is a
        # programming error to invoke this function.

        if not self.CanBeArcGISInputParameter:
            raise NotImplementedError('Methods with input parameters of data type %s cannot be invoked from ArcGIS because ArcGIS does not support this data type.' % self.__class__.__name__)

        # Return the string

        return paramString

    def GetArcGISOutputParameterStringForValue(self, value, paramDisplayName, paramIndex):
        assert isinstance(paramDisplayName, str), 'paramDisplayName must be a string'
        assert isinstance(paramIndex, int) and paramIndex > 0, 'paramIndex must be an integer greater than zero'

        # If this type of parameter cannot be an ArcGIS output parameter, it is
        # a programming error to invoke this function.

        if not self.CanBeArcGISOutputParameter:
            raise NotImplementedError('Methods with output parameters of data type %s cannot be invoked from ArcGIS because ArcGIS does not support this data type.' % self.__class__.__name__)

        # Return the string

        if value is None:
            return ''

        return str(value)
    
    def DependenciesAreNeededForValue(self, value):
        return value is not None


# Types representing Python class instances or classes


class AnyObjectTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self, canBeNone=False):
        super(AnyObjectTypeMetadata, self).__init__(pythonType=object,
                                                    canBeNone=canBeNone,
                                                    arcGISType='ESRI.ArcGIS.Geoprocessing.GPTypeClass',
                                                    arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                    canBeArcGISInputParameter=True,
                                                    canBeArcGISOutputParameter=True,
                                                    sphinxMarkup=':py:class:`object`')

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPType'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):
        return None     

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())


class NoneTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self):
        super(NoneTypeMetadata, self).__init__(pythonType=type(None), 
                                               canBeNone=True,
                                               sphinxMarkup=':py:data:`None`')

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        if value is not None:
            _RaiseException(TypeError(_('The %s must be None (also called null or empty in languages other than Python).') % variableName))
        return (False, value)

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            return _('instances of %(type)s') % {'type': str(type(None))}
        return _('instance of %(type)s') % {'type': str(type(None))}


class ClassTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self, 
                 cls, 
                 canBeNone=False, 
                 sphinxMarkup=None):

        assert inspect.isclass(cls), 'cls must be a class'
        assert isinstance(sphinxMarkup, (str, type(None))), 'sphinxMarkup must be a str or None'
        if sphinxMarkup is None:
            sphinxMarkup = ':class:`~%s.%s`' % (cls.__module__, cls.__name__)
        super(ClassTypeMetadata, self).__init__(pythonType=cls, 
                                                canBeNone=canBeNone,
                                                sphinxMarkup=sphinxMarkup)

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        if value is None:
            if not self.CanBeNone:
                _RaiseException(TypeError(_('The %s is required. Please provide a value.') % variableName))
        elif not issubclass(value, self.PythonType):
            _RaiseException(TypeError(_('The value provided for the %(variable)s is invalid because it is a %(type)s, an invalid type. Please provide the class %(class)s or a subclass.') % {'variable' : variableName, 'type' : type(value).__name__, 'class' : self.PythonType.__name__}))
        return (False, value)

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            if self.CanBeNone:
                return _('subclasses of %(type)s or None') % {'type': str(self.PythonType)}
            return _('subclasses of %(type)s') % {'type': str(self.PythonType)}
        if self.CanBeNone:
            return _('subclass of %(type)s or None') % {'type': str(self.PythonType)}
        return _('subclass of %(type)s') % {'type': str(self.PythonType)}


class ClassInstanceTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self, 
                 cls, 
                 canBeNone=False, 
                 sphinxMarkup=None):

        assert inspect.isclass(cls), 'cls must be a class'
        assert isinstance(sphinxMarkup, (str, type(None))), 'sphinxMarkup must be a str or None'
        if sphinxMarkup is None:
            sphinxMarkup = ':class:`~%s.%s`' % (cls.__module__, cls.__name__)
        super(ClassInstanceTypeMetadata, self).__init__(pythonType=cls, 
                                                        canBeNone=canBeNone,
                                                        sphinxMarkup=sphinxMarkup)


class ClassOrClassInstanceTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self, 
                 cls, 
                 canBeNone=False, 
                 sphinxMarkup=None):

        assert inspect.isclass(cls), 'cls must be a class'
        assert isinstance(sphinxMarkup, (str, type(None))), 'sphinxMarkup must be a str or None'
        if sphinxMarkup is None:
            sphinxMarkup = ':class:`~%s.%s`' % (cls.__module__, cls.__name__)
        super(ClassOrClassInstanceTypeMetadata, self).__init__(pythonType=cls, 
                                                               canBeNone=canBeNone,
                                                               sphinxMarkup=sphinxMarkup)

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        if value is None:
            if not self.CanBeNone:
                _RaiseException(TypeError(_('The %s is required. Please provide a value.') % variableName))
        elif not (inspect.isclass(value) and issubclass(value, self.PythonType)) and not isinstance(value, self.PythonType):
            _RaiseException(TypeError(_('The value provided for the %(variable)s is invalid because it is a %(type)s, an invalid type. Please provide the class %(class)s, a subclass, or an instance of it or a subclass.') % {'variable' : variableName, 'type' : type(value).__name__, 'class' : self.PythonType.__name__}))
        return (False, value)

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            if self.CanBeNone:
                return _('instances or subclasses of %(type)s or None') % {'type': str(self.PythonType)}
            return _('instances or subclasses of %(type)s') % {'type': str(self.PythonType)}
        if self.CanBeNone: 
            return _('instance or subclass of %(type)s or None') % {'type': str(self.PythonType)}
        return _('instance or subclass of %(type)s') % {'type': str(self.PythonType)}


# Simple Python types from which many other types derive


class BooleanTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 canBeNone=False,
                 allowedValues=None):
        
        super(BooleanTypeMetadata, self).__init__(pythonType=bool,
                                                  canBeNone=canBeNone,
                                                  allowedValues=allowedValues,
                                                  arcGISType='ESRI.ArcGIS.Geoprocessing.GPBooleanTypeClass',
                                                  arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                  canBeArcGISInputParameter=True,
                                                  canBeArcGISOutputParameter=True,
                                                  sphinxMarkup=':py:class:`bool`')

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPBoolean'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):
        # Return a GPCodedValueDomain that allows the caller to pass the
        # strings "False" and "True". This mimics ESRI's tools, which always
        # allow a string to be passed. ESRI's strings are usually more
        # descriptive such as "NO_GAPS" and "GAPS". These strings appear as
        # the "code". Our metadata does not support the concept of
        # representing boolean True and False with descriptive strings, so we
        # just always use "True" and "False".
        #
        # Although our metadata supports canBeNone, the ESRI GUI renders
        # booleans as checkboxes that must either be checked or unchecked, and
        # does not appear to support the concept of a third state (e.g.
        # representing "neither" or "unknown"). So we do not incorporate
        # canBeNone into the "domain" dictionary returned here.
        #
        # Similarly, although our metadata supports allowedValues for
        # booleans, this is never used in practice: we never define a boolean
        # argument that must always be true or always be false. So we do not
        # incorporate allowedValues into the dictionary we return either.

        return {'type': 'GPCodedValueDomain', 
                'items': [{'type': 'GPBoolean', 'value': 'false', 'code': 'False'}, 
                          {'type': 'GPBoolean', 'value': 'true', 'code': 'True'}]}

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        s = super(BooleanTypeMetadata, self).ParseValueFromArcGISInputParameterString(paramString, paramDisplayName, paramIndex).strip().lower()
        if s == 'true':
            return True
        if s == 'false':
            return False
        _RaiseException(ValueError(_('Failed to parse a boolean from the string "%(string)s" provided for the %(paramName)s parameter (parameter number %(paramIndex)i). Please provide either "True" or "False".') % {'string' : s, 'paramName' : paramDisplayName, 'paramIndex' : paramIndex}))


class DateTimeTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 minValue=None,
                 mustBeGreaterThan=None,
                 maxValue=None,
                 mustBeLessThan=None,
                 canBeNone=False,
                 allowedValues=None):
        
        assert isinstance(minValue, (datetime.datetime, type(None))), 'minValue must be a datetime.datetime, or None'
        assert isinstance(mustBeGreaterThan, (datetime.datetime, type(None))), 'mustBeGreaterThan must be a datetime.datetime, or None'
        assert minValue is None or mustBeGreaterThan is None, 'minValue and mustBeGreaterThan cannot both be specified'
        assert isinstance(maxValue, (datetime.datetime, type(None))), 'maxValue must be a datetime.datetime, or None'
        assert isinstance(mustBeLessThan, (datetime.datetime, type(None))), 'mustBeLessThan must be a datetime.datetime, or None'
        assert maxValue is None or mustBeLessThan is None, 'maxValue and mustBeLessThan cannot both be specified'
        assert minValue is None or maxValue is None or minValue <= maxValue, 'minValue must be less than or equal to maxValue'
        assert mustBeGreaterThan is None or maxValue is None or mustBeGreaterThan < maxValue, 'mustBeGreaterThan must be less than maxValue'
        assert mustBeLessThan is None or minValue is None or mustBeLessThan > minValue, 'mustBeLessThan must be greater than minValue'
        assert mustBeGreaterThan is None or mustBeLessThan is None or mustBeGreaterThan < mustBeLessThan, 'mustBeGreaterThan must be less than mustBeLessThan'
        super(DateTimeTypeMetadata, self).__init__(pythonType=datetime.datetime,
                                                   canBeNone=canBeNone,
                                                   allowedValues=allowedValues,
                                                   arcGISType='ESRI.ArcGIS.Geoprocessing.GPDateTypeClass',
                                                   arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                   canBeArcGISInputParameter=True,
                                                   canBeArcGISOutputParameter=True,
                                                   sphinxMarkup=':py:class:`~datetime.datetime`')
        self._MinValue = minValue
        self._MustBeGreaterThan = mustBeGreaterThan
        self._MaxValue = maxValue
        self._MustBeLessThan = mustBeLessThan

    def _GetMinValue(self):
        return self._MinValue
    
    MinValue = property(_GetMinValue, doc=DynamicDocString())

    def _GetMustBeGreaterThan(self):
        return self._MustBeGreaterThan
    
    MustBeGreaterThan = property(_GetMustBeGreaterThan, doc=DynamicDocString())

    def _GetMaxValue(self):
        return self._MaxValue
    
    MaxValue = property(_GetMaxValue, doc=DynamicDocString())

    def _GetMustBeLessThan(self):
        return self._MustBeLessThan
    
    MustBeLessThan = property(_GetMustBeLessThan, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPDate'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):
        # We'd like to set the domain from properties above such as MinValue
        # and MaxValue but we don't have any examples from ESRI's toolboxes
        # showing how to set the domain dictionary for GPDate. So we just
        # return None. The argument value will still be validated when the
        # function actually runs, even though it won't be validated first by
        # the ArcGIS GUI.

        return None     

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        valueChanged = False
        if value is not None and not isinstance(value, datetime.datetime):
            try:
                import pywintypes
            except:
                pass
            else:
                if isinstance(value, pywintypes.TimeType):
                    value = datetime.datetime(value.year, value.month, value.day, value.hour, value.minute, value.second, value.msec)
                    valueChanged = True
        (valueChanged2, value) = super(DateTimeTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None:
            if self.MinValue is not None and value < self.MinValue:
                _RaiseException(ValueError(_('The value %(value)r provided for the %(variable)s is less than the minimum allowed value %(minValue)r.') % {'value' : value, 'variable' : variableName, 'minValue' : self.MinValue}))
            if self.MustBeGreaterThan is not None and value <= self.MustBeGreaterThan:
                _RaiseException(ValueError(_('The value %(value)r provided for the %(variable)s is less than or equal to %(minValue)r. It must be greater than %(minValue)r.') % {'value' : value, 'variable' : variableName, 'minValue' : self.MustBeGreaterThan}))
            if self.MaxValue is not None and value > self.MaxValue:
                _RaiseException(ValueError(_('The value %(value)r provided for the %(variable)s is greater than the maximum allowed value %(maxValue)r.') % {'value' : value, 'variable' : variableName, 'maxValue' : self.MaxValue}))
            if self.MustBeLessThan is not None and value >= self.MustBeLessThan:
                _RaiseException(ValueError(_('The value %(value)r provided for the %(variable)s is greater than or equal to %(maxValue)r. It must be less than %(maxValue)r.') % {'value' : value, 'variable' : variableName, 'maxValue' : self.MustBeLessThan}))
        return (valueChanged or valueChanged2, value)

    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        s = super(DateTimeTypeMetadata, self).ParseValueFromArcGISInputParameterString(paramString, paramDisplayName, paramIndex).strip().lower()

        # Sadly, it appears that ArcGIS passes datetimes in the locale-specific
        # format. I verified this on Windows by switching the Regional and
        # Language Options from English (United States) to German (Germany) and
        # observing the datetime string being passed in a different format.
        # This means we have to try to parse the string in the locale-specific
        # format. The ParseDatetimeFromString function tries to do this.

        try:
            return self.ParseDatetimeFromString(s)
        except Exception as e:
            _RaiseException(ValueError(_('Failed to parse a date/time value from the string "%(string)s" provided for the %(paramName)s parameter (parameter number %(paramIndex)i). Please provide a value in a supported date/time format. You may not provide a time without a date. Error details: %(e)s: %(msg)s') % {'string' : s, 'paramName' : paramDisplayName, 'paramIndex' : paramIndex, 'e': e.__class__.__name__, 'msg': e}))

    @classmethod
    def ParseDatetimeFromString(cls, s, ignoreTZ=False):

        # If we haven't done so yet for this instance (or the class itself)
        # whether the locale-specific date format lists the year first or
        # last, or whether the day comes before the month, do it now.

        if not hasattr(cls, '_YearFirst'):
            localeTimeStr = time.strftime('%x', (2007, 12, 31, 0, 0, 0, 0, 365, -1))
            cls._YearFirst = localeTimeStr.startswith('2007') or localeTimeStr.startswith('07') or localeTimeStr.startswith('7')
            cls._DayFirst = localeTimeStr.startswith('31') or cls._YearFirst and not localeTimeStr.endswith('31')

        # Use dateutil.parser.parse to parse a datetime from the string.

        import dateutil.parser
        return dateutil.parser.parse(s, ignoretz=ignoreTZ, dayfirst=cls._DayFirst, yearfirst=cls._YearFirst)

    def GetConstraintDescriptionStrings(self):
        constraints = super(DateTimeTypeMetadata, self).GetConstraintDescriptionStrings()
        if self.MinValue is not None:
            constraints.append('Minimum value: ' + repr(self.MinValue))
        if self.MustBeGreaterThan is not None:
            constraints.append('Must be greater than ' + repr(self.MustBeGreaterThan))
        if self.MaxValue is not None:
            constraints.append('Maximum value: ' + repr(self.MaxValue))
        if self.MustBeLessThan is not None:
            constraints.append('Must be less than ' + repr(self.MustBeLessThan))
        return constraints


class FloatTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 minValue=None,
                 mustBeGreaterThan=None,
                 maxValue=None,
                 mustBeLessThan=None,
                 canBeNone=False,
                 allowedValues=None):
        
        assert isinstance(minValue, (float, type(None))), 'minValue must be a float, or None'
        assert isinstance(mustBeGreaterThan, (float, type(None))), 'mustBeGreaterThan must be a float, or None'
        assert minValue is None or mustBeGreaterThan is None, 'minValue and mustBeGreaterThan cannot both be specified'
        assert isinstance(maxValue, (float, type(None))), 'maxValue must be a float, or None'
        assert isinstance(mustBeLessThan, (float, type(None))), 'mustBeLessThan must be a float, or None'
        assert maxValue is None or mustBeLessThan is None, 'maxValue and mustBeLessThan cannot both be specified'
        assert minValue is None or maxValue is None or minValue <= maxValue, 'minValue must be less than or equal to maxValue'
        assert mustBeGreaterThan is None or maxValue is None or mustBeGreaterThan < maxValue, 'mustBeGreaterThan must be less than maxValue'
        assert mustBeLessThan is None or minValue is None or mustBeLessThan > minValue, 'mustBeLessThan must be greater than minValue'
        assert mustBeGreaterThan is None or mustBeLessThan is None or mustBeGreaterThan < mustBeLessThan, 'mustBeGreaterThan must be less than mustBeLessThan'
        assert (minValue is None and mustBeGreaterThan is None and maxValue is None and mustBeLessThan is None) or allowedValues is None, 'minValue, mustBeGreaterThan, maxValue, mustBeLessThan must all be None, or allowedValues must be None; they cannot both be specified'
        super(FloatTypeMetadata, self).__init__(pythonType=float,
                                                canBeNone=canBeNone,
                                                allowedValues=allowedValues,
                                                arcGISType='ESRI.ArcGIS.Geoprocessing.GPDoubleTypeClass',
                                                arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                canBeArcGISInputParameter=True,
                                                canBeArcGISOutputParameter=True,
                                                sphinxMarkup=':py:class:`float`')
        self._MinValue = minValue
        self._MustBeGreaterThan = mustBeGreaterThan
        self._MaxValue = maxValue
        self._MustBeLessThan = mustBeLessThan

    def _GetMinValue(self):
        return self._MinValue
    
    MinValue = property(_GetMinValue, doc=DynamicDocString())

    def _GetMustBeGreaterThan(self):
        return self._MustBeGreaterThan
    
    MustBeGreaterThan = property(_GetMustBeGreaterThan, doc=DynamicDocString())

    def _GetMaxValue(self):
        return self._MaxValue
    
    MaxValue = property(_GetMaxValue, doc=DynamicDocString())

    def _GetMustBeLessThan(self):
        return self._MustBeLessThan
    
    MustBeLessThan = property(_GetMustBeLessThan, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPDouble'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):

        # If we have AllowedValues, return a GPCodedValueDomain for them.

        if self.AllowedValues is not None:
            return {'type': 'GPCodedValueDomain', 
                    'items': [{'type': 'GPDouble', 'value': repr(val), 'code': repr(val)} for val in self.AllowedValues]}

        # Otherwise, if we have CanBeNone, MinValue, MaxValue,
        # MustBeGreaterThan, or MustBeLessThan, create a GPNumericDomain.

        if self.CanBeNone or self.MinValue is not None or self.MustBeGreaterThan is not None or self.MaxValue is not None or self.MustBeLessThan is not None:
            domain = {'type': 'GPNumericDomain'}
            if self.CanBeNone:
                domain['allowempty'] = 'true'
            if self.MinValue is not None:
                domain['low'] = {'inclusive': 'true', 'val': repr(self.MinValue)}
            elif self.MustBeGreaterThan is not None:
                domain['low'] = {'inclusive': 'false', 'val': repr(self.MustBeGreaterThan)}
            if self.MaxValue is not None:
                domain['high'] = {'allow': 'true', 'val': repr(self.MaxValue)}
            elif self.MustBeLessThan is not None:
                domain['high'] = {'allow': 'false', 'val': repr(self.MustBeLessThan)}
            return domain

        # Otherwise do not return a domain dictionary.

        return None

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        valueChanged = False
        if isinstance(value, int) or hasattr(value, 'dtype') and (value.dtype.name.startswith('int') or value.dtype.name.startswith('uint')):
            newValue = float(value)
            if int(newValue) != value:
                _RaiseException(ValueError(_('The %(variable)s requires a float but a %(type)s was provided with the value %(value)r. This value cannot be represented by as a Python float without a loss of precision, so we cannot safely coerce it to a float automatically. Please either provide a float or a %(type)s that can be coerced safely.') % {'value' : value, 'type': type(value), 'variable' : variableName}))
            value = newValue
            valueChanged = True
        (valueChanged2, value) = super(FloatTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None:
            if self.MinValue is not None and value < self.MinValue:
                _RaiseException(ValueError(_('The value %(value)G provided for the %(variable)s is less than the minimum allowed value %(minValue)G.') % {'value' : value, 'variable' : variableName, 'minValue' : self.MinValue}))
            if self.MustBeGreaterThan is not None and value <= self.MustBeGreaterThan:
                _RaiseException(ValueError(_('The value %(value)G provided for the %(variable)s is less than or equal to %(minValue)G. It must be greater than %(minValue)G.') % {'value' : value, 'variable' : variableName, 'minValue' : self.MustBeGreaterThan}))
            if self.MaxValue is not None and value > self.MaxValue:
                _RaiseException(ValueError(_('The value %(value)G provided for the %(variable)s is greater than the maximum allowed value %(maxValue)G.') % {'value' : value, 'variable' : variableName, 'maxValue' : self.MaxValue}))
            if self.MustBeLessThan is not None and value >= self.MustBeLessThan:
                _RaiseException(ValueError(_('The value %(value)G provided for the %(variable)s is greater than or equal to %(maxValue)G. It must be less than %(maxValue)G.') % {'value' : value, 'variable' : variableName, 'maxValue' : self.MustBeLessThan}))
        return (valueChanged or valueChanged2, value)
    
    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        s = super(FloatTypeMetadata, self).ParseValueFromArcGISInputParameterString(paramString, paramDisplayName, paramIndex).strip()
        try:
            return self.ParseFromArcGISString(s)
        except Exception as e:
            _RaiseException(ValueError(_('Failed to parse a floating-point number from the string "%(string)s" provided for the %(paramName)s parameter (parameter number %(paramIndex)i). Please provide a string with valid formatting. The Python float function reported: %(msg)s') % {'string' : s, 'paramName' : paramDisplayName, 'paramIndex' : paramIndex, 'msg' : str(e)}))

    @classmethod
    def ParseFromArcGISString(cls, value):
        if isinstance(value, (float, type(None))):
            return value
        if isinstance(value, int):
            return float(value)
        assert isinstance(value, str), 'value must be a string, an integer, a float, or None'

        # If the string appears to use a comma rather than a period as
        # the decimal point character, replace the comma with a
        # decimal point and try to parse it. This apparently can
        # happen with some localized versions of ArcGIS and/or
        # Windows. (The proper way to do this is probably to use the
        # atof function from the locale module, but I am afraid that
        # there are scenarios where ArcGIS will use commas even though
        # the operating system locale specifies periods, etc. So,
        # instead, I just try both.)
        
        if len(value.split(',')) == 2:
            try:
                return float(value.replace(',', '.'))
            except:
                pass

        # The string did not appear to use a comma for the decimal
        # point character, or parsing it with a comma failed. Try a
        # period instead.
        
        return float(value)

    def GetConstraintDescriptionStrings(self):
        constraints = super(FloatTypeMetadata, self).GetConstraintDescriptionStrings()
        if self.MinValue is not None:
            constraints.append('Minimum value: ' + repr(self.MinValue))
        if self.MustBeGreaterThan is not None:
            constraints.append('Must be greater than ' + repr(self.MustBeGreaterThan))
        if self.MaxValue is not None:
            constraints.append('Maximum value: ' + repr(self.MaxValue))
        if self.MustBeLessThan is not None:
            constraints.append('Must be less than ' + repr(self.MustBeLessThan))
        return constraints


class IntegerTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 minValue=None,
                 mustBeGreaterThan=None,
                 maxValue=None,
                 mustBeLessThan=None,
                 canBeNone=False,
                 allowedValues=None):
        
        assert isinstance(minValue, (int, type(None))), 'minValue must be an int, or None'
        assert isinstance(mustBeGreaterThan, (int, type(None))), 'mustBeGreaterThan must be an int, or None'
        assert minValue is None or mustBeGreaterThan is None, 'minValue and mustBeGreaterThan cannot both be specified'
        assert isinstance(maxValue, (int, type(None))), 'maxValue must be an int, or None'
        assert isinstance(mustBeLessThan, (int, type(None))), 'mustBeLessThan must be an int, or None'
        assert maxValue is None or mustBeLessThan is None, 'maxValue and mustBeLessThan cannot both be specified'
        assert minValue is None or maxValue is None or minValue <= maxValue, 'minValue must be less than or equal to maxValue'
        assert mustBeGreaterThan is None or maxValue is None or mustBeGreaterThan < maxValue, 'mustBeGreaterThan must be less than maxValue'
        assert mustBeLessThan is None or minValue is None or mustBeLessThan > minValue, 'mustBeLessThan must be greater than minValue'
        assert mustBeGreaterThan is None or mustBeLessThan is None or mustBeGreaterThan < mustBeLessThan, 'mustBeGreaterThan must be less than mustBeLessThan'
        super(IntegerTypeMetadata, self).__init__(pythonType=int,
                                                  canBeNone=canBeNone,
                                                  allowedValues=allowedValues,
                                                  arcGISType='ESRI.ArcGIS.Geoprocessing.GPLongTypeClass',
                                                  arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                  canBeArcGISInputParameter=True,
                                                  canBeArcGISOutputParameter=True,
                                                  sphinxMarkup=':py:class:`int`')
        self._MinValue = minValue
        self._MustBeGreaterThan = mustBeGreaterThan
        self._MaxValue = maxValue
        self._MustBeLessThan = mustBeLessThan

    def _GetMinValue(self):
        return self._MinValue
    
    MinValue = property(_GetMinValue, doc=DynamicDocString())

    def _GetMustBeGreaterThan(self):
        return self._MustBeGreaterThan
    
    MustBeGreaterThan = property(_GetMustBeGreaterThan, doc=DynamicDocString())

    def _GetMaxValue(self):
        return self._MaxValue
    
    MaxValue = property(_GetMaxValue, doc=DynamicDocString())

    def _GetMustBeLessThan(self):
        return self._MustBeLessThan
    
    MustBeLessThan = property(_GetMustBeLessThan, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPLong'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):

        # If we have AllowedValues, return a GPCodedValueDomain for them.

        if self.AllowedValues is not None:
            return {'type': 'GPCodedValueDomain', 
                    'items': [{'type': 'GPLong', 'value': repr(val), 'code': repr(val)} for val in self.AllowedValues]}

        # Otherwise, if we have CanBeNone, MinValue, MaxValue,
        # MustBeGreaterThan, or MustBeLessThan, create a GPNumericDomain.

        if self.CanBeNone or self.MinValue is not None or self.MustBeGreaterThan is not None or self.MaxValue is not None or self.MustBeLessThan is not None:
            domain = {'type': 'GPNumericDomain'}
            if self.CanBeNone:
                domain['allowempty'] = 'true'
            if self.MinValue is not None:
                domain['low'] = {'inclusive': 'true', 'val': repr(self.MinValue)}
            elif self.MustBeGreaterThan is not None:
                domain['low'] = {'inclusive': 'false', 'val': repr(self.MustBeGreaterThan)}
            if self.MaxValue is not None:
                domain['high'] = {'allow': 'true', 'val': repr(self.MaxValue)}
            elif self.MustBeLessThan is not None:
                domain['high'] = {'allow': 'false', 'val': repr(self.MustBeLessThan)}
            return domain

        # Otherwise do not return a domain dictionary.

        return None

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(IntegerTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None:
            if self.MinValue is not None and value < self.MinValue:
                _RaiseException(ValueError(_('The value %(value)i provided for the %(variable)s is less than the minimum allowed value %(minValue)i.') % {'value' : value, 'variable' : variableName, 'minValue' : self.MinValue}))
            if self.MustBeGreaterThan is not None and value <= self.MustBeGreaterThan:
                _RaiseException(ValueError(_('The value %(value)i provided for the %(variable)s is less than or equal to %(minValue)i. It must be greater than %(minValue)i.') % {'value' : value, 'variable' : variableName, 'minValue' : self.MustBeGreaterThan}))
            if self.MaxValue is not None and value > self.MaxValue:
                _RaiseException(ValueError(_('The value %(value)i provided for the %(variable)s is greater than the maximum allowed value %(maxValue)i.') % {'value' : value, 'variable' : variableName, 'maxValue' : self.MaxValue}))
            if self.MustBeLessThan is not None and value >= self.MustBeLessThan:
                _RaiseException(ValueError(_('The value %(value)i provided for the %(variable)s is greater than or equal to %(maxValue)i. It must be less than %(maxValue)i.') % {'value' : value, 'variable' : variableName, 'maxValue' : self.MustBeLessThan}))
        return (valueChanged, value)

    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        s = super(IntegerTypeMetadata, self).ParseValueFromArcGISInputParameterString(paramString, paramDisplayName, paramIndex).strip()
        try:
            value = int(s)
        except Exception as e:
            _RaiseException(ValueError(_('Failed to parse an integer from the string "%(string)s" provided for the %(paramName)s parameter (parameter number %(paramIndex)i). Please provide a string with valid formatting. The Python integer function reported: %(msg)s') % {'string' : s, 'paramName' : paramDisplayName, 'paramIndex' : paramIndex, 'msg' : str(e)}))
        return value

    def GetConstraintDescriptionStrings(self):
        constraints = super(IntegerTypeMetadata, self).GetConstraintDescriptionStrings()
        if self.MinValue is not None:
            constraints.append('Minimum value: ' + repr(self.MinValue))
        if self.MustBeGreaterThan is not None:
            constraints.append('Must be greater than ' + repr(self.MustBeGreaterThan))
        if self.MaxValue is not None:
            constraints.append('Maximum value: ' + repr(self.MaxValue))
        if self.MustBeLessThan is not None:
            constraints.append('Must be less than ' + repr(self.MustBeLessThan))
        return constraints


class UnicodeStringTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 stripWhitespace=True,
                 makeLowercase=False,
                 makeUppercase=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 allowedValues=None,
                 arcGISType='ESRI.ArcGIS.Geoprocessing.GPStringTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        assert isinstance(stripWhitespace, bool), 'stripWhitespace must be a boolean'
        assert isinstance(makeLowercase, bool), 'makeLowercase must be a boolean'
        assert isinstance(makeUppercase, bool), 'makeUppercase must be a boolean'
        assert not(makeLowercase and makeUppercase), 'makeLowercase and makeUppercase may not both be true'
        assert isinstance(minLength, int) and minLength >= 0 and minLength <= 2147483647, 'minLength must be an integer between 0 and 2147483647, inclusive'
        assert isinstance(maxLength, int) and maxLength >= 0 and maxLength <= 2147483647, 'maxLength must be an integer between 0 and 2147483647, inclusive'
        assert maxLength >= minLength, 'maxLength must be greater than or equal to minLength'
        assert isinstance(mustMatchRegEx, (type(None), str)), 'mustMatchRegEx must be a string, or None'
        super(UnicodeStringTypeMetadata, self).__init__(pythonType=str,
                                                        canBeNone=canBeNone,
                                                        allowedValues=allowedValues,
                                                        arcGISType=arcGISType,
                                                        arcGISAssembly=arcGISAssembly,
                                                        canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                        canBeArcGISOutputParameter=canBeArcGISOutputParameter,
                                                        sphinxMarkup=':py:class:`str`')
        self._StripWhitespace = stripWhitespace
        self._MakeLowercase = makeLowercase
        self._MakeUppercase = makeUppercase
        self._MinLength = minLength
        self._MaxLength = maxLength
        self._MustMatchRegEx = mustMatchRegEx

    def _GetStripWhitespace(self):
        return self._StripWhitespace
    
    StripWhitespace = property(_GetStripWhitespace, doc=DynamicDocString())

    def _GetMakeLowercase(self):
        return self._MakeLowercase
    
    MakeLowercase = property(_GetMakeLowercase, doc=DynamicDocString())

    def _GetMakeUppercase(self):
        return self._MakeUppercase
    
    MakeUppercase = property(_GetMakeUppercase, doc=DynamicDocString())

    def _GetMinLength(self):
        return self._MinLength
    
    MinLength = property(_GetMinLength, doc=DynamicDocString())

    def _GetMaxLength(self):
        return self._MaxLength    
    MaxLength = property(_GetMaxLength, doc=DynamicDocString())

    def _GetMustMatchRegEx(self):
        return self._MustMatchRegEx
    
    MustMatchRegEx = property(_GetMustMatchRegEx, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPString'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):

        # If we have AllowedValues, return a GPCodedValueDomain for them.

        if self.AllowedValues is not None:
            return {'type': 'GPCodedValueDomain', 
                    'items': [{'type': self.ArcGISDataTypeDict['type'], 'value': val, 'code': val} for val in self.AllowedValues]}

        # Otherwise do not return a domain dictionary.

        return None

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        # For convenience, we accept a pathlib.Path object and automatically
        # convert it as a string.

        valueChanged = False

        if isinstance(value, pathlib.Path):
            value = str(value)
            valueChanged = True

        (valueChanged2, value) = super(UnicodeStringTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        valueChanged = valueChanged or valueChanged2
        
        if value is not None:
            if self.StripWhitespace:
                value = value.strip()
                valueChanged = True

            if self.MakeLowercase:
                value = value.lower()
                valueChanged = True

            if self.MakeUppercase:
                value = value.upper()
                valueChanged = True

            if len(value) < self.MinLength:
                _RaiseException(ValueError(_('The value provided for the %(variable)s is too short. It may be no shorter than %(len)i characters.') % {'variable' : variableName, 'len' : self.MinLength}))

            if len(value) > self.MaxLength:
                _RaiseException(ValueError(_('The value provided for the %(variable)s is too long. It may be no longer than %(len)i characters.') % {'variable' : variableName, 'len' : self.MaxLength}))

            if self.MustMatchRegEx is not None and not re.match(self.MustMatchRegEx, value):
                _RaiseException(ValueError(_('The value provided for the %(variable)s is not formatted properly. Please check the documentation for the %(variable)s for details on the format. (Technical details: the value did not match the regular expression "%(regex)s".)') % {'variable' : variableName, 'regex' : self.MustMatchRegEx}))

        return (valueChanged, value)

    def GetConstraintDescriptionStrings(self):
        constraints = super(UnicodeStringTypeMetadata, self).GetConstraintDescriptionStrings()
        if self.AllowedValues is None or len(self.AllowedValues) <= 0:
            if self.MinLength is not None and self.MinLength > 0:
                constraints.append('Minimum length: ' + repr(self.MinLength))
            if self.MaxLength is not None and self.MaxLength < 2147483647:
                constraints.append('Maximum length: ' + repr(self.MaxLength))
            if self.MustMatchRegEx is not None:
                constraints.append('Must match regular expression: ``' + str(self.MustMatchRegEx) + '``')
        elif not self.MakeLowercase and not self.MakeUppercase:
            constraints.append('Case sensitive')
        return constraints


class UnicodeStringHiddenTypeMetadata(UnicodeStringTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 stripWhitespace=True,
                 makeLowercase=False,
                 makeUppercase=False,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 allowedValues=None,
                 arcGISType='ESRI.ArcGIS.Geoprocessing.GPStringHiddenTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):
        
        super(UnicodeStringHiddenTypeMetadata, self).__init__(stripWhitespace=stripWhitespace,
                                                              makeLowercase=makeLowercase,
                                                              makeUppercase=makeUppercase,
                                                              minLength=minLength,
                                                              maxLength=maxLength,
                                                              mustMatchRegEx=mustMatchRegEx,
                                                              canBeNone=canBeNone,
                                                              allowedValues=allowedValues,
                                                              arcGISType=arcGISType,
                                                              arcGISAssembly=arcGISAssembly,
                                                              canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                              canBeArcGISOutputParameter=canBeArcGISOutputParameter)

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPStringHidden'}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())


###############################################################################
# Names exported by this module
#
# Note: This module is not meant to be imported directly. Import Types.py
# instead.
###############################################################################

__all__ = []
