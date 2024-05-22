# _Dataset.py - Defines Dataset, the base class for classes representing
# tabular and gridded datasets.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import re

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from ._CollectibleObject import CollectibleObject


class Dataset(CollectibleObject):
    __doc__ = DynamicDocString()

    # Public properties and methods

    def GetSpatialReference(self, srType):
        self.__doc__.Obj.ValidateMethodInvocation()

        srRef = self.GetLazyPropertyValue('SpatialReference')

        if srRef is None:
            if srType == 'arcgis':
                return '{B286C06B-0879-11D2-AACA-00C04FA33C20}'        # This is ESRI's GUID for the "Unknown" coordinate system
            return None
        
        if srType == 'obj':
            return srRef
        
        if srType == 'wkt':
            return srRef.ExportToWkt()
        
        if srType == 'proj4':
            return srRef.ExportToProj4()
        
        if srType == 'arcgis':
            s = srRef.ExportToWkt()
            if len(s) > 0:
                sr = self._osr().SpatialReference(s)
                sr.MorphToESRI()
                s = sr.ExportToWkt()
            return s
        
        raise ValueError(_('"%(srType)s" is an invalid value for the srType parameter.') % {'srType': srType})

    def SetSpatialReference(self, srType, sr):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Verify that we have the required capabilities.

        self._RequireCapability('SetSpatialReference')

        # Convert the caller's spatial reference to the type required
        # by the derived class and call the derived class to set it.

        if srType != 'obj' and sr is not isinstance(sr, (type(None), str)):
            raise TypeError(_('If the srType parameter is \'%(srType)s\', the sr parameter must be a string or None.') % {'srType': srType})

        if sr is None or srType != 'obj' and len(sr.strip()) <= 0 or srType == 'arcgis' and sr.upper() == '{B286C06B-0879-11D2-AACA-00C04FA33C20}':     # This is ESRI's GUID for the "Unknown" coordinate system
            self._LogDebug(_('%(class)s 0x%(id)016X: Setting SpatialReference to None.'), {'class': self.__class__.__name__, 'id': id(self)})
        elif srType == 'obj':
            self._LogDebug(_('%(class)s 0x%(id)016X: Setting SpatialReference from OSR SpatialReference object 0x%(id2)016X that has WKT \'%(srString)s\'.'), {'class': self.__class__.__name__, 'id': id(self), 'id2': id(sr), 'srString': sr.ExportToWkt()})
        elif srType == 'wkt':
            self._LogDebug(_('%(class)s 0x%(id)016X: Setting SpatialReference from WKT \'%(srString)s\'.'), {'class': self.__class__.__name__, 'id': id(self), 'srString': sr})
        elif srType == 'proj4':
            self._LogDebug(_('%(class)s 0x%(id)016X: Setting SpatialReference from Proj4 string "%(srString)s".'), {'class': self.__class__.__name__, 'id': id(self), 'srString': sr})
        elif srType == 'arcgis':
            self._LogDebug(_('%(class)s 0x%(id)016X: Setting SpatialReference from ArcGIS WKT \'%(srString)s\'.'), {'class': self.__class__.__name__, 'id': id(self), 'srString': sr})
        else:
            raise ValueError(_('"%(srType)s" is an invalid value for the srType parameter.') % {'srType': srType})

        try:
            self._SetSpatialReference(self.ConvertSpatialReference(srType, sr, self._GetSRTypeForSetting()))
        except Exception as e:
            raise RuntimeError(_('Failed to set the spatial reference of %(dn)s due to %(e)s: %(msg)s') % {'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        # Set our SpatialReference property to a new OSR
        # SpatialReference.

        newSR = self.ConvertSpatialReference(srType, sr, 'obj')
        self.SetLazyPropertyValue('SpatialReference', newSR)
        self.SetLazyPropertyValue('IsGeographic', newSR is not None and newSR.IsGeographic())

    @classmethod
    def ConvertSpatialReference(cls, srType, sr, outputSRType):
        cls.__doc__.Obj.ValidateMethodInvocation()

        if srType != 'obj' and not isinstance(sr, (type(None), str)):
            raise TypeError(_('If the srType parameter is \'%(srType)s\', the sr parameter must be a string or None.') % {'srType': srType})

        if outputSRType != 'obj' and outputSRType == srType:
            return sr

        # Create a SpatialReference object

        if sr is None or srType != 'obj' and len(sr.strip()) <= 0 or srType == 'arcgis' and sr.upper() == '{B286C06B-0879-11D2-AACA-00C04FA33C20}':     # This is ESRI's GUID for the "Unknown" coordinate system
            return None

        elif srType == 'obj':
            srObj = cls._osr().SpatialReference(sr.ExportToWkt())

        elif srType == 'wkt':
            srObj = cls._osr().SpatialReference(sr)

        elif srType == 'proj4':
            srObj = cls._osr().SpatialReference()
            srObj.ImportFromProj4(sr)

        elif srType == 'arcgis':
            sr = re.sub("\\[\\'[^\\']*\\'", Dataset._FixESRIQuotes, sr)        # Convert ArcGIS's single quotes around WKT <name> tokens to double quotes, to conform to proper WKT syntax
            srObj = cls._osr().SpatialReference(sr)
            srObj.MorphFromESRI()

        else:
            raise ValueError(_('"%(srType)s" is an invalid value for the srType parameter.') % {'srType': srType})

        # Return the appropriate string or the SpatialReference
        # object.

        if outputSRType == 'obj':
            return srObj

        if outputSRType == 'wkt':
            return srObj.ExportToWkt()

        if outputSRType == 'proj4':
            return srObj.ExportToProj4()

        srObj.MorphToESRI()
        return srObj.ExportToWkt()

    # Private properties and methods that the derived class may access
    # but generally does not override

    @staticmethod
    def _FixESRIQuotes(matchobj):
        return '["' + matchobj.group(0)[2:-1] + '"'

    # Private methods that the derived class is expected to override

    @classmethod
    def _GetSRTypeForSetting(cls):
        if isinstance(cls, Dataset):
            raise NotImplementedError(_('The _GetSRTypeForSetting method of class %s has not been implemented.') % cls.__class__.__name__)
        else:
            raise NotImplementedError(_('The _GetSRTypeForSetting method of class %s has not been implemented.') % cls.__name__)

    def _SetSpatialReference(self, sr):
        raise NotImplementedError(_('The _SetSpatialReference method of class %s has not been implemented.') % self.__class__.__name__)


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
