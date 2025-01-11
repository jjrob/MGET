# _Datasets.py - Classes derived from ..Metadata.TypeMetadata that are related
# to the ..Datasets object model.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

##### THIS MODULE IS NOT MEANT TO BE IMPORTED DIRECTLY. IMPORT Types.py INSTEAD. #####

import os
import re

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from ._Base import _RaiseException
from ._StoredObject import StoredObjectTypeMetadata


class TableFieldTypeMetadata(StoredObjectTypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 tableParameterName,
                 allowedFieldTypes=None,
                 typeDisplayName=_('field'),
                 mustBeDifferentThanArguments=None,
                 mustExist=False,
                 mustNotExist=False,
                 deleteIfParameterIsTrue=None,
                 minLength=1,
                 maxLength=2147483647,
                 mustMatchRegEx=None,
                 canBeNone=False,
                 canBeArcGISInputParameter=True,
                 canBeArcGISOutputParameter=True):

        assert isinstance(tableParameterName, str), 'tableParameterName must be a Unicode string'
        self._TableParameterName = tableParameterName
        assert isinstance(allowedFieldTypes, (type(None), list, tuple)), 'allowedFieldTypes must be a list or tuple of Unicode strings, or None.'
        if isinstance(allowedFieldTypes, tuple):
            allowedFieldTypes = list(allowedFieldTypes)
        if allowedFieldTypes is not None:
            for s in allowedFieldTypes:
                assert isinstance(s, str), 'allowedFieldTypes must be a list or tuple of Unicode strings, or None.'
            self._AllowedFieldTypes = list(map(str.strip, list(map(str.lower, allowedFieldTypes))))
        else:
            self._AllowedFieldTypes = None
        
        super(TableFieldTypeMetadata, self).__init__(typeDisplayName=typeDisplayName,
                                                     isPath=False,
                                                     canBeRelativePath=False,
                                                     basePathArgument=None,
                                                     useArcGISWorkspace=False,
                                                     normalizePath=False,
                                                     mustBeDifferentThanArguments=mustBeDifferentThanArguments,
                                                     mustExist=mustExist,
                                                     mustNotExist=mustNotExist,
                                                     deleteIfParameterIsTrue=deleteIfParameterIsTrue,
                                                     createParentDirectories=False,
                                                     minLength=minLength,
                                                     maxLength=maxLength,
                                                     mustMatchRegEx=mustMatchRegEx,
                                                     canBeNone=canBeNone,
                                                     canBeArcGISInputParameter=canBeArcGISInputParameter,
                                                     canBeArcGISOutputParameter=canBeArcGISOutputParameter)

    def _GetTableParameterName(self):
        return self._TableParameterName
    
    TableParameterName = property(_GetTableParameterName, doc=DynamicDocString())

    def _GetAllowedFieldTypes(self):
        return self._AllowedFieldTypes
    
    AllowedFieldTypes = property(_GetAllowedFieldTypes, doc=DynamicDocString())

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):
        (valueChanged, value) = super(TableFieldTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)
        if value is not None and self.AllowedFieldTypes is not None and methodLocals is not None and self.TableParameterName is not None and methodLocals[self.TableParameterName] is not None:
            field = methodLocals[self.TableParameterName].GetFieldByName(value)
            if field is not None and field.DataType.lower() not in self.AllowedFieldTypes:
                if len(self.AllowedFieldTypes) == 1:
                    _RaiseException(ValueError(_('The field %(value)s in %(table)s, specified for the %(variable)s, has the data type \'%(dt)s\', but this function requires a field with the data type \'%(allowed)s\'. Please provide a field with data type \'%(allowed)s\'.') % {'value' : value, 'dn': methodLocals[self.TableParameterName].DisplayName, 'variable' : variableName, 'dt': field.DataType, 'allowed': self.AllowedFieldTypes[0]}))
                else:
                    _RaiseException(ValueError(_('The field %(value)s in %(table)s, specified for the %(variable)s, has the data type \'%(dt)s\', but this function requires a field with one of the following data types: \'%(allowed)s\'. Please provide a field with an allowed data type.') % {'value' : value, 'dn': methodLocals[self.TableParameterName].DisplayName, 'variable' : variableName, 'dt': field.DataType, 'allowed': str('\', \''.join(map(str, self.AllowedFieldTypes)))}))
        return (valueChanged, value)

    @classmethod
    def Exists(cls, name, argMetadata=None, methodLocals=None):
        assert methodLocals is not None and argMetadata is not None and self.TableParameterName is not None, 'TableFieldTypeMetadata.Exists requires that methodLocals, argMetadata, and self.TableParameterName be provided.'
        exists = methodLocals[self.TableParameterName].GetFieldByName(name)
        return exists, exists

    @classmethod
    def Delete(cls, name, argMetadata=None, methodLocals=None):
        assert methodLocals is not None and argMetadata is not None and self.TableParameterName is not None, 'TableFieldTypeMetadata.Delete requires that methodLocals, argMetadata, and self.TableParameterName be provided.'
        methodLocals[self.TableParameterName].DeleteField(name)

    @classmethod
    def Copy(cls, source, dest, overwriteExisting=False, argMetadata=None, methodLocals=None):
        _RaiseException(NotImplementedError('TableFieldTypeMetadata.Copy is not implemented.'))


###############################################################################
# Names exported by this module
#
# Note: This module is not meant to be imported directly. Import Types.py
# instead.
###############################################################################

__all__ = []
