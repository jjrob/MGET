# _Sequence.py - Classes derived from ..Metadata.TypeMetadata that represent
# Python sequence types such as lists and dicts.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

##### THIS MODULE IS NOT MEANT TO BE IMPORTED DIRECTLY. IMPORT Types.py INSTEAD. #####

import xml.dom

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from ._Base import _RaiseException, TypeMetadata


class SequenceTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 elementType,
                 minLength=0,
                 maxLength=2147483647,
                 maxItemsToValidate=2147483647,
                 mustBeSameLengthAsArgument=None,
                 pythonType=object,
                 canBeNone=False,
                 arcGISType='ESRI.ArcGIS.Geoprocessing.GPMultiValueTypeClass',
                 arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=False,
                 sphinxMarkup=None):
        
        assert isinstance(elementType, TypeMetadata), 'elementType must be an instance of TypeMetadata'
        assert isinstance(minLength, int) and minLength >= 0 and minLength <= 2147483647, 'minLength must be an integer between 0 and 2147483647, inclusive'
        assert isinstance(maxLength, int) and maxLength >= 0 and maxLength <= 2147483647, 'maxLength must be an integer between 0 and 2147483647, inclusive'
        assert maxLength >= minLength, 'maxLength must be greater than or equal to minLength'
        assert isinstance(maxItemsToValidate, int) and maxItemsToValidate >= 0, 'maxItemsToValidate must be an integer greater than or equal to 0'
        assert isinstance(mustBeSameLengthAsArgument, (str, type(None))), 'mustBeSameLengthAsArgument must be a string, or None'
        assert not canBeArcGISInputParameter or not arcGISType != 'ESRI.ArcGIS.Geoprocessing.GPMultiValueTypeClass' or (issubclass(elementType.PythonType, str) or not hasattr(elementType.PythonType, '__getitem__')), 'For this sequence type to be passed as an ArcGIS input parameter using the ArcGIS data type ESRI.ArcGIS.Geoprocessing.GPMultiValueTypeClass, its elements may not themselves be sequences unless they are strings. (In other words, you can\'t pass nested sequences using ESRI.ArcGIS.Geoprocessing.GPMultiValueTypeClass.)'

        # Initialize the base class.
        
        super(SequenceTypeMetadata, self).__init__(pythonType=pythonType,
                                                   canBeNone=canBeNone,
                                                   arcGISType=arcGISType,
                                                   arcGISAssembly=arcGISAssembly,
                                                   canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                   canBeArcGISOutputParameter=canBeArcGISOutputParameter,
                                                   sphinxMarkup=sphinxMarkup)
        self._ElementType = elementType
        self._MinLength = minLength
        self._MaxLength = maxLength
        self._MaxItemsToValidate = maxItemsToValidate
        self._MustBeSameLengthAsArgument = mustBeSameLengthAsArgument

    def _GetElementType(self):
        return self._ElementType
    
    ElementType = property(_GetElementType, doc=DynamicDocString())

    def _GetMinLength(self):
        return self._MinLength
    
    MinLength = property(_GetMinLength, doc=DynamicDocString())

    def _GetMaxLength(self):
        return self._MaxLength
    
    MaxLength = property(_GetMaxLength, doc=DynamicDocString())

    def _GetMaxItemsToValidate(self):
        return self._MaxItemsToValidate
    
    MaxItemsToValidate = property(_GetMaxItemsToValidate, doc=DynamicDocString())

    def _GetMustBeSameLengthAsArgument(self):
        return self._MustBeSameLengthAsArgument
    
    MustBeSameLengthAsArgument = property(_GetMustBeSameLengthAsArgument, doc=DynamicDocString())

    def _GetArcGISDataTypeDict(self):
        return {'type': 'GPMultiValue',
                'datatype': self.ElementType.ArcGISDataTypeDict}

    ArcGISDataTypeDict = property(_GetArcGISDataTypeDict, doc=DynamicDocString())

    def _GetArcGISDomainDict(self):
        return self.ElementType.ArcGISDomainDict

    ArcGISDomainDict = property(_GetArcGISDomainDict, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(SequenceTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)

        length1 = 0
        length2 = 0

        if value is not None:

            if len(value) < self.MinLength:
                _RaiseException(ValueError(_('The length of the %(variable)s is too short. It must contain at least %(len)i items.') % {'variable' : variableName, 'len' : self.MinLength}))

            if len(value) > self.MaxLength:
                _RaiseException(ValueError(_('The length of the %(variable)s is too long. It must contain no more than %(len)i items.') % {'variable' : variableName, 'len' : self.MaxLength}))

            if self.MustBeSameLengthAsArgument is not None and methodLocals is not None:
                assert self.MustBeSameLengthAsArgument in methodLocals, _('To validate the %(param1)s of the method being validated, that method must also have an parameter named %(param2)s.') % {'param1' : variableName, 'param2' : self.MustBeSameLengthAsArgument}
                length1 = len(value)

            if self.MustBeSameLengthAsArgument is not None and methodLocals is not None and methodLocals[self.MustBeSameLengthAsArgument] is not None:
                try:
                    length2 = len(methodLocals[self.MustBeSameLengthAsArgument])
                except Exception as e:
                    _RaiseException(TypeError(_('To validate the %(param1)s of the method being validated, the length of method\'s %(param2)s parameter must be able to be obtained with the Python len function. That function raised the following exception when passed the value of that parameter: %(error)s: %(msg)s') % {'param1' : variableName, 'param2' : self.MustBeSameLengthAsArgument, 'error': e.__class__.__name__, 'msg': str(e)}))

            if length1 != length2:
                _RaiseException(TypeError(_('The %(param1)s must have the same number of items as the %(param2)s parameter.') % {'param1' : variableName, 'param2' : self.MustBeSameLengthAsArgument}))

        return (valueChanged, value)

    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        paramString = super(SequenceTypeMetadata, self).ParseValueFromArcGISInputParameterString(paramString, paramDisplayName, paramIndex)

        # The input string is a list of values formatted as follows:
        #     - Values are separated by semicolons
        #     - If a value contains a space or tab it is enclosed in apostrophes
        #     - There are no escape sequences for semicolons or apostrophes
        #     - An empty string is formatted as two successive semicolons
        #
        # We parse the string using a finite state machine. Because
        # there are no escape sequences for semicolons or apostrophes,
        # it there are certain strings that the user cannot pass to
        # us, and some strings will lead to undesirable results.
        
        FIRST_CHARACTER = 1                                     # We are positioned on the first character of the input strong or the first character following the semicolon that terminated the previous element.
        INSIDE_SEMICOLON = 2                                    # We are positioned on the second or subsequent character inside an element that did not begin with an apostrophe.
        INSIDE_QUOTE_NO_SPACE_FOUND = 3                         # We are positioned on the second or subsequent character inside an element that began with an apostrophe, and we have not yet found the space or tab character that necessitated the apostrophe, so it could just be part of the string.
        INSIDE_QUOTE_SPACE_FOUND = 4                            # We are positioned on the second or subsequent character inside an element that began with an apostrophe, and we have already found the space or tab character that necessitated the apostrophe.
        INSIDE_QUOTE_SPACE_FOUND_POSSIBLE_TRAILING_QUOTE = 5    # We are positioned on a character following the second or subsequent apostrophe inside an element that begain with an apostrophe and was found to have a space or tab character. The apostrophe we just parsed could be the closing apostrophe, if we now are positioned on a semicolon or the end of the string.

        state = FIRST_CHARACTER
        params = []
        i = 0
        paramStart = 0
        paramCharCount = 0
        failedBecauseArcGISForgotQuotes = False     # Sometimes ArcGIS seems to violate the rules described above in a way that makes the string unparsable. In this case we treat it as a single string and report a warning.

        #from ..Logging import Logger
        try:
            while i < len(paramString):
                #Logger.Debug('----------------------------')
                #Logger.Debug('i = %i, c = %s, state = %i, paramStart = %i, paramCharCount= %i' % (i, paramString[i], state, paramStart, paramCharCount))
                
                if state == FIRST_CHARACTER:
                    if paramString[i] == ';':
                        params.append('')
                    elif paramString[i] == '\'':
                        state = INSIDE_QUOTE_NO_SPACE_FOUND
                        paramStart = i
                        paramCharCount = 1
                    else:
                        state = INSIDE_SEMICOLON
                        paramStart = i
                        paramCharCount = 1

                elif state == INSIDE_SEMICOLON:
                    if paramString[i] == ' ' or paramString[i] == '\t':
                        failedBecauseArcGISForgotQuotes = True
                        raise ValueError(_('Failed to parse a list of values from the string provided for the %(paramName)s parameter (parameter number %(paramIndex)i). The parser encountered an error: a space or tab character was found outside of enclosing apostrophes. If an element in the list contains a space or tab, enclose the entire element in apostrophes. If you are invoking this function from ArcGIS, there is no need to do this explicitly, ArcGIS does it for you; you must have received this error for a different reason. Please contact the author of this function for assistance.') % {'paramName' : paramDisplayName, 'paramIndex' : paramIndex})
                    elif paramString[i] == ';':
                        state = FIRST_CHARACTER
                        params.append(paramString[paramStart:paramStart+paramCharCount])
                    else:
                        paramCharCount += 1

                elif state == INSIDE_QUOTE_NO_SPACE_FOUND:
                    if paramString[i] == ';':
                        state = FIRST_CHARACTER
                        if paramString[paramStart:paramStart+paramCharCount] == '\'\'':
                            params.append('')
                        else:
                            params.append(paramString[paramStart:paramStart+paramCharCount])
                    elif paramString[i] == ' ' or paramString[i] == '\t':
                        state = INSIDE_QUOTE_SPACE_FOUND
                        paramStart += 1
                    else:
                        paramCharCount += 1

                elif state == INSIDE_QUOTE_SPACE_FOUND:
                    if paramString[i] == '\'':
                        state = INSIDE_QUOTE_SPACE_FOUND_POSSIBLE_TRAILING_QUOTE
                    else:
                        paramCharCount += 1

                elif state == INSIDE_QUOTE_SPACE_FOUND_POSSIBLE_TRAILING_QUOTE:
                    if paramString[i] == '\'':
                        paramCharCount += 1
                    elif paramString[i] == ';':
                        state = FIRST_CHARACTER
                        params.append(paramString[paramStart:paramStart+paramCharCount])
                    else:
                        paramCharCount += 1

                else:
                    _RaiseException(RuntimeError(_('Failed to parse a list of values from the string provided for the %(paramName)s parameter (parameter number %(paramIndex)i) due to a programming error in the parser: the parser was found to be in unknown state %(state)i. Please contact the author of this function for assistance.') % {'paramName' : paramDisplayName, 'paramIndex' : paramIndex, 'state' : state}))

                #Logger.Debug('state = %i, paramStart = %i, paramCharCount= %i' % (state, paramStart, paramCharCount))

                i += 1
                
        except:
            if failedBecauseArcGISForgotQuotes:
                from ..Logging import Logger
                Logger.Warning(_('The string provided for %(paramName)s parameter (parameter number %(paramIndex)i) included a space but the string itself was not enclosed in apostrophes. This is a known problem with how ArcGIS passes parameters to Python scripts. As a result, the string cannot be parsed into a list of items and will be treated as a single item. This may result in unintended effects. Please check your outputs carefully.') % {'paramName' : paramDisplayName, 'paramIndex' : paramIndex})
                params.append(paramString)
            else:
                raise
            
        else:
            if state == FIRST_CHARACTER:
                if paramString.endswith(';'):
                    params.append('')
            elif state == INSIDE_SEMICOLON or state == INSIDE_QUOTE_NO_SPACE_FOUND or state == INSIDE_QUOTE_SPACE_FOUND_POSSIBLE_TRAILING_QUOTE:
                params.append(paramString[paramStart:paramStart+paramCharCount])
            elif state == INSIDE_QUOTE_SPACE_FOUND:
                _RaiseException(ValueError(_('Failed to parse a list of values from the string provided for the %(paramName)s parameter (parameter number %(paramIndex)i). The parser encountered an error: the last element in the list begain with an apostrophe, included at least one space or tab character but did not end with an apostrophe. Please end your string with an apostrophe. If you are invoking this function from ArcGIS, there is no need to do this explicitly, ArcGIS does it for you; you must have received this error for a different reason. Please contact the author of this function for assistance.') % {'paramName' : paramDisplayName, 'paramIndex' : paramIndex}))
            else:
                _RaiseException(RuntimeError(_('Failed to parse a list of values from the string provided for the %(paramName)s parameter (parameter number %(paramIndex)i) due to a programming error in the parser: the parser was found to be in unknown state %(state)i. Please contact the author of this function for assistance.') % {'paramName' : paramDisplayName, 'paramIndex' : paramIndex, 'state' : state}))

        # The parser built a list of strings. If we're supposed to return a
        # list of strings, just return now.

        if issubclass(self.ElementType.PythonType, str):
            return params

        # Parse the list of strings into the appropriate Python type. For
        # Python types that are not strings, we interpret whitespace as None.

        values = []        

        for i in range(len(params)):
            s = params[i].strip()
            if len(s) <= 0 and self.ElementType.CanBeNone:
                values.append(None)
                continue
            values.append(self.ElementType.ParseValueFromArcGISInputParameterString(s, _('element at position %i (where 0 is the first element) of the %s') % (i, paramDisplayName), paramIndex))
                
        return values

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            if self.CanBeNone:
                return _('instances of %(noneType)s or sequences of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
            return _('sequences of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True)}
        if self.CanBeNone:
            return _('instance of %(noneType)s or sequence of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
        return _('sequence of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True)}

    def GetConstraintDescriptionStrings(self):
        constraints = super(SequenceTypeMetadata, self).GetConstraintDescriptionStrings()
        if self.MinLength is not None and self.MinLength > 0:
            constraints.append('Minimum length: ' + repr(self.MinLength))
        if self.MaxLength is not None and self.MaxLength < 2147483647:
            constraints.append('Maximum length: ' + repr(self.MaxLength))
        if self.MustBeSameLengthAsArgument is not None:
            constraints.append('Must have the same length as `%s`' % self.MustBeSameLengthAsArgument)
        return constraints


class ListTypeMetadata(SequenceTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 elementType,
                 minLength=0,
                 maxLength=2147483647,
                 maxItemsToValidate=2147483647,
                 mustBeSameLengthAsArgument=None,
                 canBeNone=False,
                 sphinxMarkup=None):

        if sphinxMarkup is None:
            sphinxMarkup = ':py:class:`list` of %s' % elementType.SphinxMarkup
        
        super(ListTypeMetadata, self).__init__(elementType=elementType,
                                               minLength=minLength,
                                               maxLength=maxLength,
                                               maxItemsToValidate=maxItemsToValidate,
                                               mustBeSameLengthAsArgument=mustBeSameLengthAsArgument,
                                               pythonType=list,
                                               canBeNone=canBeNone,
                                               sphinxMarkup=sphinxMarkup)

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(ListTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None:
            itemsToValidate = min(len(value), self.MaxItemsToValidate)
            if itemsToValidate != len(value):
                from ..Logging import Logger
                Logger.Debug(_('The %(var)s contains %(count1)i items, but to minimize execution time, only the first %(count2)i items will be validated. If an invalid item is present, unexpected results may occur.') % {'var': variableName, 'count1': len(value), 'count2': self.MaxItemsToValidate})
            for i in range(itemsToValidate):
                (elementValueChanged, newElementValue) = self.ElementType.ValidateValue(value[i], _('element %i of the %s (where 0 is the first element)') % (i, variableName), methodLocals, argMetadata)
                if elementValueChanged:
                    value[i] = newElementValue
                    valueChanged = True
        return (valueChanged, value)

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            if self.CanBeNone:
                return _('instances of %(noneType)s or lists of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
            return _('lists of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True)}
        if self.CanBeNone:
            return _('instance of %(noneType)s or list of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
        return _('list of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True)}


class TupleTypeMetadata(SequenceTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 elementType,
                 minLength=0,
                 maxLength=2147483647,
                 maxItemsToValidate=2147483647,
                 mustBeSameLengthAsArgument=None,
                 canBeNone=False,
                 sphinxMarkup=None):
        
        if sphinxMarkup is None:
            sphinxMarkup = ':py:class:`tuple` of %s' % elementType.SphinxMarkup

        super(TupleTypeMetadata, self).__init__(elementType=elementType,
                                                minLength=minLength,
                                                maxLength=maxLength,
                                                maxItemsToValidate=maxItemsToValidate,
                                                mustBeSameLengthAsArgument=mustBeSameLengthAsArgument,
                                                pythonType=tuple,
                                                canBeNone=canBeNone,
                                                sphinxMarkup=sphinxMarkup)

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        valueChanged = False
        if isinstance(value, list):
            value = tuple(value)
            valueChanged = True
        (valueChanged2, value) = super(TupleTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None:
            itemsToValidate = min(len(value), self.MaxItemsToValidate)
            if itemsToValidate != len(value):
                from ..Logging import Logger
                Logger.Debug(_('The %(var)s contains %(count1)i items, but to minimize execution time, only the first %(count2)i items will be validated. If an invalid item is present, unexpected results may occur.') % {'var': variableName, 'count1': len(value), 'count2': self.MaxItemsToValidate})
            for i in range(itemsToValidate):
                (elementValueChanged, newElementValue) = self.ElementType.ValidateValue(value[i], _('element %i of the %s (where 0 is the first element)') % (i, variableName), methodLocals, argMetadata)
                if elementValueChanged:
                    if isinstance(value, tuple):
                        value = list(value)
                    value[i] = newElementValue
                    valueChanged = True
        return (valueChanged or valueChanged2, value)

    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        resultList = super(TupleTypeMetadata, self).ParseValueFromArcGISInputParameterString(paramString, paramDisplayName, paramIndex)
        return tuple(resultList)

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            if self.CanBeNone:
                return _('instances of %(noneType)s or tuples or lists of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
            return _('tuples or lists of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True)}
        if self.CanBeNone:
            return _('instance of %(noneType)s or tuple or list of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
        return _('tuple or list of %(type)s') % {'type': self.ElementType._GetPythonTypeDescription(plural=True)}


class DictionaryTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 keyType,
                 valueType,
                 minLength=0,
                 maxLength=2147483647,
                 pythonType=dict,
                 canBeNone=False,
                 sphinxMarkup=None):
        
        assert isinstance(keyType, TypeMetadata), 'keyType must be an instance of TypeMetadata'
        assert isinstance(valueType, TypeMetadata), 'valueType must be an instance of TypeMetadata'
        assert isinstance(minLength, int) and minLength >= 0 and minLength <= 2147483647, 'minLength must be an integer between 0 and 2147483647, inclusive'
        assert isinstance(maxLength, int) and maxLength >= 0 and maxLength <= 2147483647, 'maxLength must be an integer between 0 and 2147483647, inclusive'
        assert maxLength >= minLength, 'maxLength must be greater than or equal to minLength'

        if sphinxMarkup is None:
            sphinxMarkup = ':py:class:`dict` mapping %s to %s' % (keyType.SphinxMarkup, valueType.SphinxMarkup)

        # Initialize the base class.
        
        super(DictionaryTypeMetadata, self).__init__(pythonType=pythonType, canBeNone=canBeNone, sphinxMarkup=sphinxMarkup)
        self._KeyType = keyType
        self._ValueType = valueType
        self._MinLength = minLength
        self._MaxLength = maxLength

    def _GetKeyType(self):
        return self._KeyType
    
    KeyType = property(_GetKeyType, doc=DynamicDocString())

    def _GetValueType(self):
        return self._ValueType
    
    ValueType = property(_GetValueType, doc=DynamicDocString())

    def _GetMinLength(self):
        return self._MinLength
    
    MinLength = property(_GetMinLength, doc=DynamicDocString())

    def _GetMaxLength(self):
        return self._MaxLength
    
    MaxLength = property(_GetMaxLength, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(DictionaryTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)

        if value is not None:

            if len(value) < self.MinLength:
                _RaiseException(ValueError(_('The length of the %(variable)s is too short. It must contain at least %(len)i items.') % {'variable' : variableName, 'len' : self.MinLength}))

            if len(value) > self.MaxLength:
                _RaiseException(ValueError(_('The length of the %(variable)s is too long. It must contain no more than %(len)i items.') % {'variable' : variableName, 'len' : self.MaxLength}))

            for key, val in list(value.items()):
                (keyChanged, newKey) = self.ValueType.ValidateValue(key, _('key %s of the %s') % (str(repr(key)), variableName), methodLocals, argMetadata)
                (valChanged, newVal) = self.ValueType.ValidateValue(val, _('value of key %s of the %s') % (str(repr(key)), variableName), methodLocals, argMetadata)
                if keyChanged and valChanged:
                    del value[key]
                    value[newKey] = newVal
                elif keyChanged and not valChanged:
                    del value[key]
                    value[newKey] = val
                elif not keyChanged and valChanged:
                    value[key] = newVal
                valueChanged = keyChanged or valChanged

        return (valueChanged, value)

    def _GetPythonTypeDescription(self, plural=False):
        if plural:
            if self.CanBeNone:
                return _('instances of %(noneType)s or dictionaries mapping %(keyType)s to %(valueType)s') % {'keyType': self.KeyType._GetPythonTypeDescription(plural=True), 'valueType': self.ValueType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
            return _('dictionaries mapping %(keyType)s to %(valueType)s') % {'keyType': self.KeyType._GetPythonTypeDescription(plural=True), 'valueType': self.ValueType._GetPythonTypeDescription(plural=True)}
        if self.CanBeNone:
            return _('instance of %(noneType)s or dictionary mapping %(keyType)s to %(valueType)s') % {'keyType': self.KeyType._GetPythonTypeDescription(plural=True), 'valueType': self.ValueType._GetPythonTypeDescription(plural=True), 'noneType': str(type(None))}
        return _('dictionary mapping %(keyType)s to %(valueType)s') % {'keyType': self.KeyType._GetPythonTypeDescription(plural=True), 'valueType': self.ValueType._GetPythonTypeDescription(plural=True)}

    def GetConstraintDescriptionStrings(self):
        constraints = super(DictionaryTypeMetadata, self).GetConstraintDescriptionStrings()
        if self.MinLength is not None and self.MinLength > 0:
            constraints.append('Minimum length: ' + repr(self.MinLength))
        if self.MaxLength is not None and self.MaxLength < 2147483647:
            constraints.append('Maximum length: ' + repr(self.MaxLength))
        return constraints


class ListTableTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 columnTypes,
                 columnNames,
                 columnLengths,
                 minLength=0,
                 maxLength=2147483647,
                 maxItemsToValidate=2147483647,
                 mustBeSameLengthAsArgument=None,
                 canBeNone=False):
        
        assert isinstance(columnTypes, list), 'columnTypes must be an instance of list'
        assert len(columnTypes) > 0, 'len(columnTypes) must be greater than zero'
        for columnType in columnTypes:
            assert isinstance(columnType, TypeMetadata), 'All elements of columnTypes must be instances of TypeMetadata'
        assert isinstance(columnNames, list), 'columnNames must be an instance of list'
        assert len(columnNames) == len(columnTypes), 'len(columnNames) must be equal to len(columnTypes)'
        for columnName in columnNames:
            assert isinstance(columnName, str), 'All elements of columnNames must be instances of str'
            assert len(columnName) > 0, 'All elements of columnNames must have length > 0'
        assert isinstance(columnLengths, list), 'columnLengths must be an instance of list'
        assert len(columnLengths) == len(columnTypes), 'len(columnLengths) must be equal to len(columnTypes)'
        for columnLength in columnLengths:
            assert isinstance(columnLength, int), 'All elements of columnLengths must be instances of int'
            assert columnLength > 0, 'All elements of columnLengths must be > 0'
        assert isinstance(minLength, int) and minLength >= 0 and minLength <= 2147483647, 'minLength must be an integer between 0 and 2147483647, inclusive'
        assert isinstance(maxLength, int) and maxLength >= 0 and maxLength <= 2147483647, 'maxLength must be an integer between 0 and 2147483647, inclusive'
        assert maxLength >= minLength, 'maxLength must be greater than or equal to minLength'
        assert isinstance(maxItemsToValidate, int) and maxItemsToValidate >= 0, 'maxItemsToValidate must be an integer greater than or equal to 0'
        assert isinstance(mustBeSameLengthAsArgument, (str, type(None))), 'mustBeSameLengthAsArgument must be a string, or None'

        # Initialize the base class.
        
        super(ListTableTypeMetadata, self).__init__(pythonType=list,
                                                    canBeNone=canBeNone,
                                                    arcGISType='ESRI.ArcGIS.Geoprocessing.GPValueTableTypeClass',
                                                    arcGISAssembly='ESRI.ArcGIS.Geoprocessing',
                                                    canBeArcGISInputParameter=True,
                                                    canBeArcGISOutputParameter=False)
        self._ColumnTypes = columnTypes
        self._ColumnNames = columnNames
        self._ColumnLengths = columnLengths
        self._MinLength = minLength
        self._MaxLength = maxLength
        self._MaxItemsToValidate = maxItemsToValidate
        self._MustBeSameLengthAsArgument = mustBeSameLengthAsArgument

    def _GetColumnTypes(self):
        return self._ColumnTypes
    
    ColumnTypes = property(_GetColumnTypes, doc=DynamicDocString())

    def _GetColumnNames(self):
        return self._ColumnNames
    
    ColumnNames = property(_GetColumnNames, doc=DynamicDocString())

    def _GetColumnLengths(self):
        return self._ColumnLengths
    
    ColumnLengths = property(_GetColumnLengths, doc=DynamicDocString())

    def _GetMinLength(self):
        return self._MinLength
    
    MinLength = property(_GetMinLength, doc=DynamicDocString())

    def _GetMaxLength(self):
        return self._MaxLength
    
    MaxLength = property(_GetMaxLength, doc=DynamicDocString())

    def _GetMaxItemsToValidate(self):
        return self._MaxItemsToValidate
    
    MaxItemsToValidate = property(_GetMaxItemsToValidate, doc=DynamicDocString())

    def _GetMustBeSameLengthAsArgument(self):
        return self._MustBeSameLengthAsArgument
    
    MustBeSameLengthAsArgument = property(_GetMustBeSameLengthAsArgument, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(ListTableTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)

        length1 = 0
        length2 = 0

        if value is not None:

            if len(value) < self.MinLength:
                _RaiseException(ValueError(_('The length of the %(variable)s is too short. It must contain at least %(len)i items.') % {'variable' : variableName, 'len' : self.MinLength}))

            if len(value) > self.MaxLength:
                _RaiseException(ValueError(_('The length of the %(variable)s is too long. It must contain no more than %(len)i items.') % {'variable' : variableName, 'len' : self.MaxLength}))

            if self.MustBeSameLengthAsArgument is not None and methodLocals is not None:
                assert self.MustBeSameLengthAsArgument in methodLocals, _('To validate the %(param1)s of the method being validated, that method must also have an parameter named %(param2)s.') % {'param1' : variableName, 'param2' : self.MustBeSameLengthAsArgument}
                length1 = len(value)

            if self.MustBeSameLengthAsArgument is not None and methodLocals is not None and methodLocals[self.MustBeSameLengthAsArgument] is not None:
                try:
                    length2 = len(methodLocals[self.MustBeSameLengthAsArgument])
                except Exception as e:
                    _RaiseException(TypeError(_('To validate the %(param1)s of the method being validated, the length of method\'s %(param2)s parameter must be able to be obtained with the Python len function. That function raised the following exception when passed the value of that parameter: %(error)s: %(msg)s') % {'param1' : variableName, 'param2' : self.MustBeSameLengthAsArgument, 'error': e.__class__.__name__, 'msg': str(e)}))

            if length1 != length2:
                _RaiseException(TypeError(_('The %(param1)s must have the same number of items as the %(param2)s parameter.') % {'param1' : variableName, 'param2' : self.MustBeSameLengthAsArgument}))

            for i, row in enumerate(value):
                for j, cellValue in enumerate(row):
                    cellValueChanged, newCellValue = self.ColumnTypes[j].ValidateValue(cellValue, _('value %(j)i of row %(i)i of the %(variable)s') % {'i': i, 'j': j, 'variable': variableName}, methodLocals, argMetadata)
                    if cellValueChanged:
                        value[i][j] = newCellValue
                        valueChanged = True

        return (valueChanged, value)

    def ParseValueFromArcGISInputParameterString(self, paramString, paramDisplayName, paramIndex):
        paramString = super(ListTableTypeMetadata, self).ParseValueFromArcGISInputParameterString(paramString, paramDisplayName, paramIndex)

        # The input string is a list of values formatted as follows:
        #     - Rows are separated by semicolons
        #     - Within each row, values are separated by spaces
        #     - If a value contains a space or tab it is enclosed in apostrophes
        #     - There are no escape sequences for semicolons or apostrophes
        #     - If a value is not specifed in the GUI, the # character is used
        #
        # Because there are no escape sequences for apostrophes or
        # semicolons, the user is not able to pass values that include
        # these characters. If the user does that, the input string is
        # effectively unparsable.
        #
        # First split on the semicolons to get one string for each
        # row.

        rowStrings = paramString.split(';')
        rowStrings = [s.strip() for s in rowStrings]

        # Now parse each row string into substrings that constitute
        # the values.
        
        rows = []
        for s in rowStrings:
            values = []
            i = 0
            insideQuote = False
            value = ''
            for c in s:
                if not insideQuote:
                    if c == ' ':
                        values.append(value)
                        value = ''
                    elif c == "'":
                        insideQuote = True
                    else:
                        value += c
                elif c == "'":
                    insideQuote = False
                else:
                    value += c
                    
            if len(value) > 0:
                values.append(value)
                
            rows.append(values)

        # Iterate through the rows and parse each value substring into
        # an appropriate Python instance.

        for i, row in enumerate(rows):
            if len(row) > len(self.ColumnTypes):
                _RaiseException(ValueError(_('Row %(row)i of the table provided for the %(paramName)s parameter (parameter number %(paramIndex)i) does not have the correct number of values. It was supposed to have %(required)i but it had %(actual)i. Please provide the correct number of values.') % {'row': i+1, 'required': len(self.ColumnTypes), 'actual': len(row), 'paramName' : paramDisplayName, 'paramIndex' : paramIndex}))

            for j, s in enumerate(row):
                if s == '#':
                    rows[i][j] = None
                else:
                    rows[i][j] = self.ColumnTypes[j].ParseValueFromArcGISInputParameterString(s, _('value %(j)i of row %(i)i of the %(paramName)s') % {'i': i, 'j': j, 'paramName': paramDisplayName}, paramIndex)

            rows[i].extend([None] * (len(self.ColumnTypes) - len(row)))

        # Return successfully.

        return rows


###############################################################################
# Names exported by this module
#
# Note: This module is not meant to be imported directly. Import Types.py
# instead.
###############################################################################

__all__ = []
