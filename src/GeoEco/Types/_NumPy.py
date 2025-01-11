# _NumPy.py - Classes derived from ..Metadata.TypeMetadata that represent
# numpy data types, principally a numpy array.
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

from ._Base import _RaiseException, TypeMetadata


class NumPyArrayTypeMetadata(TypeMetadata):
    __doc__ = DynamicDocString()

    def __init__(self,
                 dimensions=None,
                 minShape=None,
                 maxShape=None,
                 allowedDTypes=None,
                 canBeNone=False):

        assert isinstance(dimensions, (int, type(None))), 'dimensions must be an integer, or None'
        assert dimensions is None or dimensions > 0, 'dimensions, if provided, must be greater than zero'
        assert isinstance(minShape, (type(None), list, tuple)), 'minShape must be a list or tuple of integers, or None'
        if isinstance(minShape, tuple):
            minShape = list(minShape)
        assert minShape is None or dimensions is not None and len(minShape) == dimensions, 'If minShape is provided, dimensions must also be provided, and len(minShape) must equal dimensions'
        if minShape is not None:
            for value in minShape:
                assert isinstance(value, int) and value >= 0, 'All elements of minShape must be non-negative integers.'
        assert isinstance(maxShape, (type(None), list, tuple)), 'maxShape must be a list or tuple of integers, or None'
        if isinstance(maxShape, tuple):
            maxShape = list(maxShape)
        assert maxShape is None or dimensions is not None and len(maxShape) == dimensions, 'If maxShape is provided, dimensions must also be provided, and len(maxShape) must equal dimensions'
        if maxShape is not None:
            for value in maxShape:
                assert isinstance(value, int) and value >= 0, 'All elements of maxShape must be non-negative integers.'
        assert isinstance(allowedDTypes, (type(None), list, tuple)), 'allowedDTypes must be a list or tuple of Unicode strings, or None.'
        if isinstance(allowedDTypes, tuple):
            allowedDTypes = list(allowedDTypes)
        if allowedDTypes is not None:
            for value in allowedDTypes:
                assert isinstance(value, str) and len(value) >= 0, 'All elements of allowedDTypes must be non-empty Unicode strings.'

        # We cannot assume that numpy can be imported. We must allow instances of
        # this class to be constructed without failing when numpy is not
        # installed. But if numpy is installed, we initialize our pythonType to
        # the appropriate class.

        try:
            import numpy
            pythonType = numpy.ndarray
        except:
            pythonType = object
                
        super(NumPyArrayTypeMetadata, self).__init__(pythonType=pythonType, 
                                                     canBeNone=canBeNone)

        self._Dimensions = dimensions
        self._MinShape = minShape
        self._MaxShape = maxShape
        self._AllowedDTypes = allowedDTypes

    def _GetDimensions(self):
        return self._Dimensions
    
    Dimensions = property(_GetDimensions, doc=DynamicDocString())

    def _GetMinShape(self):
        return self._MinShape
    
    MinShape = property(_GetMinShape, doc=DynamicDocString())

    def _GetMaxShape(self):
        return self._MaxShape
    
    MaxShape = property(_GetMaxShape, doc=DynamicDocString())

    def _GetAllowedDTypes(self):
        return self._AllowedDTypes
    
    AllowedDTypes = property(_GetAllowedDTypes, doc=DynamicDocString())

    def GetConstraintDescriptionStrings(self):
        constraints = []
        if self.Dimensions is not None:
            constraints.append(_('This array must have %i dimensions.') % self.Dimensions)
        if self.MinShape is not None:
            constraints.append(_('The shape of this array must not be less than %s.') % self.MinShape)
        if self.MaxShape is not None:
            constraints.append(_('The shape of this array must not be greater than %s.') % self.MaxShape)
        if self.AllowedDTypes is not None and len(self.AllowedDTypes) > 0:
            constraints.append(_('This array must have one of the following dtypes: ' + ', '.join(['``' + repr(av) + '``' for av in self.AllowedDTypes])))
        return constraints

    def ValidateValue(self, value, variableName, methodLocals=None, argMetadata=None):

        # It is possible that self.PythonType is set to object, rather than
        # numpy.ndarray. This will happen if the constructor was not able to
        # import the numpy module. That will happen if the user has not
        # installed their own copy of numpy. But in order to get to where we
        # are now, the numpy module must have been imported. The only way for
        # the constructor to not be able to import it but for it to be
        # imported now is if PythonModuleDependency('numpy').Initialize() was
        # successful. In that case, we can import numpy now set pythonType to
        # the proper value before calling the parent validate function.

        if self._PythonType == object:
            import numpy
            self._PythonType = numpy.ndarray

        (valueChanged, value) = super(NumPyArrayTypeMetadata, self).ValidateValue(value, variableName, methodLocals, argMetadata)

        # Perform additional validation.

        if value is not None:
            if self.Dimensions is not None:
                if self.Dimensions != value.ndim:
                    _RaiseException(ValueError(_('The NumPy array provided for the %(variable)s must have %(dim1)i dimensions. The array you provided has %(dim2)i.') % {'variable' : variableName, 'dim1' : self.Dimensions, 'dim2' : value.ndim}))

                if self.MinShape is not None:
                    for i in range(self.Dimensions):
                        if value.shape[i] < self.MinShape[i]:
                            _RaiseException(ValueError(_('The NumPy array provided for the %(variable)s must have the minimum dimensions %(dim1)i. The array you provided has the dimensions %(dim2)i.') % {'variable' : variableName, 'dim1' : repr(self.MinShape), 'dim2' : repr(list(value.shape))}))

                if self.MaxShape is not None:
                    for i in range(self.Dimensions):
                        if value.shape[i] > self.MaxShape[i]:
                            _RaiseException(ValueError(_('The NumPy array provided for the %(variable)s must have the maximum dimensions %(dim1)i. The array you provided has the dimensions %(dim2)i.') % {'variable' : variableName, 'dim1' : repr(self.MaxShape), 'dim2' : repr(list(value.shape))}))

            if self.AllowedDTypes is not None and str(value.dtype.name) not in self.AllowedDTypes:
                _RaiseException(ValueError(_('The NumPy array provided for the %(variable)s must have one of the following dtypes: %(types)s. The array you provided has the dtype %(type)s.') % {'variable' : variableName, 'types' : repr(self.AllowedDTypes), 'type' : str(value.dtype.name)}))

        return (valueChanged, value)


###############################################################################
# Names exported by this module
#
# Note: This module is not meant to be imported directly. Import Types.py
# instead.
###############################################################################

__all__ = []
