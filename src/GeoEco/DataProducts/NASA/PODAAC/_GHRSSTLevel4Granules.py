# _GHRSSTLevel4Granules.py - Defines GHRSSTLevel4Granules.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import re

from ....Datasets import Dataset, QueryableAttribute
from ....DynamicDocString import DynamicDocString
from ....Internationalization import _
from ....Types import *

from ..Earthdata._CMRGranuleSearcher import CMRGranuleSearcher


class GHRSSTLevel4Granules(CMRGranuleSearcher):
    __doc__ = DynamicDocString()

    # Define various metadata for each dataset we support. This includes the
    # Shape, so that GHRSSTLevel4 can build and clip a TimeSeriesGridStack
    # without interacting with the server. Also define the CornerCoords and
    # CoordIncrements rather than reading them from the server or netCDF file,
    # not just for efficiency but because they are often stored at low
    # precision, which can result in a compounding error that prevents the
    # resulting grids from exactly spanning the full geographic range.

    _Metadata = {
                 'AVHRR_OI-NCEI-L4-GLOB-v2.0':                {'CollectionConceptID': 'C2499940505-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 720, 1440), 'CornerCoords': (None, -89.875, -179.875), 'CoordIncrements': (1., 0.25, 0.25)},
                 'AVHRR_OI-NCEI-L4-GLOB-v2.1':                {'CollectionConceptID': 'C2036881712-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 720, 1440), 'CornerCoords': (None, -89.875, -179.875), 'CoordIncrements': (1., 0.25, 0.25)},
                 'CMC0.1deg-CMC-L4-GLOB-v3.0':                {'CollectionConceptID': 'C2036881720-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': True, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 1801, 3600), 'CornerCoords': (None, -90., -180.), 'CoordIncrements': (1., 0.1, 0.1)},
                 'CMC0.2deg-CMC-L4-GLOB-v2.0':                {'CollectionConceptID': 'C2499940521-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': True, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 901, 1800), 'CornerCoords': (None, -90., -180.), 'CoordIncrements': (1., 0.2, 0.2)},
                 'DMI_OI-DMI-L4-GLOB-v1.0':                   {'CollectionConceptID': 'C2036881727-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 3561, 7200), 'CornerCoords': (None, -89., -179.975), 'CoordIncrements': (1., 0.05, 0.05)},
                 'GAMSSA_28km-ABOM-L4-GLOB-v01':              {'CollectionConceptID': 'C2036881735-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': False, 'Shape': (1, 720, 1440), 'CornerCoords': (None, -89.875, -179.875), 'CoordIncrements': (1., 0.25, 0.25)},
                 'Geo_Polar_Blended-OSPO-L4-GLOB-v1.0':       {'CollectionConceptID': 'C2036877754-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 3600, 7200), 'CornerCoords': (None, -89.975, -179.975), 'CoordIncrements': (1., 0.05, 0.05)},
                 'Geo_Polar_Blended_Night-OSPO-L4-GLOB-v1.0': {'CollectionConceptID': 'C2036877745-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 3600, 7200), 'CornerCoords': (None, -89.975, -179.975), 'CoordIncrements': (1., 0.05, 0.05)},
                 'K10_SST-NAVO-L4-GLOB-v01':                  {'CollectionConceptID': 'C2036881956-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': True, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 1801, 3600), 'CornerCoords': (None, -90., -180.), 'CoordIncrements': (1., 0.1, 0.1)},
                 'MUR-JPL-L4-GLOB-v4.1':                      {'CollectionConceptID': 'C1996881146-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 17999, 36000), 'CornerCoords': (None, -89.99, -179.99), 'CoordIncrements': (1., 0.01, 0.01)},
                 'MUR25-JPL-L4-GLOB-v04.2':                   {'CollectionConceptID': 'C2036880657-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 720, 1440), 'CornerCoords': (None, -89.875, -179.875), 'CoordIncrements': (1., 0.25, 0.25)},
                 'MW_IR_OI-REMSS-L4-GLOB-v5.0':               {'CollectionConceptID': 'C2036878045-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 2048, 4096), 'CornerCoords': (None, -90. + 360./4096/2, -180. + 360./4096/2), 'CoordIncrements': (1., 360./4096, 360./4096)},
                 'MW_IR_OI-REMSS-L4-GLOB-v5.1':               {'CollectionConceptID': 'C2205102254-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 2048, 4096), 'CornerCoords': (None, -90. + 360./4096/2, -180. + 360./4096/2), 'CoordIncrements': (1., 360./4096, 360./4096)},
                 'MW_OI-REMSS-L4-GLOB-v5.0':                  {'CollectionConceptID': 'C2036878052-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 720, 1440), 'CornerCoords': (None, -89.875, -179.875), 'CoordIncrements': (1., 0.25, 0.25)},
                 'MW_OI-REMSS-L4-GLOB-v5.1':                  {'CollectionConceptID': 'C2205105895-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 720, 1440), 'CornerCoords': (None, -89.875, -179.875), 'CoordIncrements': (1., 0.25, 0.25)},
                 'OISST_HR_NRT-GOS-L4-BLK-v2.0':              {'CollectionConceptID': 'C2036878059-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 162, 257), 'CornerCoords': (None, 38.75, 26.375), 'CoordIncrements': (1., 0.0625, 0.0625)},
                 'OISST_HR_NRT-GOS-L4-MED-v2.0':              {'CollectionConceptID': 'C2036878073-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 253, 871), 'CornerCoords': (None, 30.25, -18.125), 'CoordIncrements': (1., 0.0625, 0.0625)},
                 'OISST_UHR_NRT-GOS-L4-BLK-v2.0':             {'CollectionConceptID': 'C2036878081-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 1208, 1920), 'CornerCoords': (None, 38.75416666666667, 26.379166666666666), 'CoordIncrements': (1., 1/120., 1/120.)},
                 'OISST_UHR_NRT-GOS-L4-MED-v2.0':             {'CollectionConceptID': 'C2036878088-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 1890, 6525), 'CornerCoords': (None, 30.254166666666666, -18.120833333333334), 'CoordIncrements': (1., 1/120., 1/120.)},
                 'OSTIA-UKMO-L4-GLOB-REP-v2.0':               {'CollectionConceptID': 'C2586786218-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 3600, 7200), 'CornerCoords': (None, -89.975, -179.975), 'CoordIncrements': (1., 0.05, 0.05)},
                 'OSTIA-UKMO-L4-GLOB-v2.0':                   {'CollectionConceptID': 'C2036877535-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': True, 'HasIce': True, 'Shape': (1, 3600, 7200), 'CornerCoords': (None, -89.975, -179.975), 'CoordIncrements': (1., 0.05, 0.05)},
                 'RAMSSA_09km-ABOM-L4-AUS-v01':               {'CollectionConceptID': 'C2036878103-POCLOUD', 'GDSVersion': 2, 'Protocol': 'dap4', 'ApplyMask': False, 'IsGlobal': False, 'HasIce': False, 'Shape': (1, 1081, 1561), 'CornerCoords': (None, -70.+1/12./2, 60.+1/12./2), 'CoordIncrements': (1., 1/12., 1/12.)}}  # Note that we added +1/12./2 to the corner coords. It appears the netCDF coord variables contain the cell edge coordinates, rather than the center coordinates. Our CornerCoords variable needs to contain the center coords of the lower-left corner cell.

    def __init__(self, username, password, shortName, datasetType='netcdf', timeout=60, maxRetryTime=300, cacheDirectory=None, metadataCacheLifetime=86400.):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._ShortName = shortName
        self._DatasetType = datasetType

        if self._DatasetType == 'opendap': 
            raise NotImplementedError('GHRSSTLevel4Granules does not currently support opendap datasets, but adding support is not difficult. Please contact the MGET development team for assistance.')
            linkTitleRegEx='^opendap request url$'
            self._Protocol = self._Metadata[self._ShortName]['Protocol']

        elif self._DatasetType == 'netcdf':
            linkTitleRegEx=r'^download.+\.nc$'
            self._Protocol = None

        else:
            raise ValueError(_('Programming error in this tool: unknown datasetType %(lt)s. Please contact the MGET development team for assistance.') % {'lt': self._DatasetType})

        # Initialize the base class.

        queryableAttributes=(QueryableAttribute('ShortName', _('Short Name'), UnicodeStringTypeMetadata()),
                             QueryableAttribute('CollectionConceptID', _('Collection Concept ID'), UnicodeStringTypeMetadata()),
                             QueryableAttribute('Title', _('Granule title'), UnicodeStringTypeMetadata()),
                             QueryableAttribute('GDSVersion', _('GHRSST GDS version'), IntegerTypeMetadata()),
                             QueryableAttribute('DateTime', _('Start date'), DateTimeTypeMetadata()))

        super(GHRSSTLevel4Granules, self).__init__(username=username, 
                                                   password=password, 
                                                   queryParams={'collection_concept_id': self._Metadata[self._ShortName]['CollectionConceptID']}, 
                                                   linkTitleRegEx=linkTitleRegEx, 
                                                   queryableAttributes=queryableAttributes, 
                                                   timeout=timeout, maxRetryTime=maxRetryTime, cacheDirectory=cacheDirectory, metadataCacheLifetime=metadataCacheLifetime)

    def _GetDisplayName(self):
        return _('NASA Earthdata GHRSST %(shortName)s granules') % {'shortName': self._ShortName}

    def _GetQueryableAttributeValuesForUrl(self, url, title):
        queryableAttributeValues = {}
        queryableAttributeValues['ShortName'] = self._ShortName
        queryableAttributeValues['CollectionConceptID'] = self._Metadata[self._ShortName]['CollectionConceptID']
        queryableAttributeValues['Title'] = title
        queryableAttributeValues['GDSVersion'] = self._Metadata[self._ShortName]['GDSVersion']

        if re.match(r'\d{14}-.*', title):
            dt = datetime.datetime.strptime(title[:14], '%Y%m%d%H%M%S')
            queryableAttributeValues['DateTime'] = dt
            queryableAttributeValues['Year'] = dt.year
            queryableAttributeValues['Month'] = dt.month
            queryableAttributeValues['Day'] = dt.day
            queryableAttributeValues['Hour'] = dt.hour
            queryableAttributeValues['Minute'] = dt.minute
            queryableAttributeValues['Second'] = dt.second
            queryableAttributeValues['DayOfYear'] = int(dt.strftime('%j'))
        else:
            raise ValueError(_('Could not parse the datetime of GHRSST dataset %(title)s at %(url)s. Please contact the MGET development team for assistance.') % {'title': title, 'url': url})

        return queryableAttributeValues

    def _ConstructFoundObjectForUrl(self, url, title, queryableAttributeValues):

        # In GDS 1.0, GHRSST did not include the hour, minute, and second in
        # the file name. We assumed that the averaging window started at
        # midnight on that day.

        if queryableAttributeValues['GDSVersion'] == 1:
            tCornerCoordType = 'min'        
   
        # In GDS 2.0, GHRSST started including the hour, minute, and second in
        # the file name and said for L4 products that the "indicative time"
        # for L4 products is the "nominal time of analysis" and "All times
        # should be given in UTC and should be chosen to best represent the
        # observation time for this dataset." Given this, and the time stamps
        # I observed in the products, the time stamp is the "center" of the
        # averaging window.

        elif queryableAttributeValues['GDSVersion'] == 2:
            tCornerCoordType = 'center'     
   
        else:
            raise ValueError(_('Programming error in this tool. For %(dn)s, the GDSVersion was %(GDSVersion)r, which is an unknown value. Please contact the MGET development team for assistance.') % {'dn': title, 'GDSVersion': queryableAttributeValues['GDSVersion']})

        lazyPropertyValues={'SpatialReference': Dataset.ConvertSpatialReference('proj4', '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs', 'obj'),
                            'Dimensions': 'tyx',
                            'Shape': self._Metadata[self._ShortName]['Shape'],
                            'CornerCoords': self._Metadata[self._ShortName]['CornerCoords'],
                            'CoordIncrements': self._Metadata[self._ShortName]['CoordIncrements'],
                            'CoordDependencies': (None, None, None),
                            'TIncrement': 1,
                            'TIncrementUnit': 'day',
                            'TSemiRegularity': None,
                            'TCountPerSemiRegularPeriod': None,
                            'TCornerCoordType': tCornerCoordType,
                            'PhysicalDimensions': 'tyx',
                            'VariableNames': ['analysed_sst', 'analysis_error', 'mask']}

        if self._Metadata[self._ShortName]['HasIce']:
            lazyPropertyValues['VariableNames'].append('sea_ice_fraction')

        if self._DatasetType == 'opendap':
            raise NotImplementedError('GHRSSTLevel4Granules does not currently support opendap datasets, but adding support is not difficult. Please contact the MGET development team for assistance.')
            lazyPropertyValues['VariableTypes'] = ['Grid'] * len(lazyPropertyValues['VariableNames'])
            return _GHRSSTLevel4OPeNDAPURL(url,
                                           username=self._Username,
                                           password=self._Password,
                                           protocol=self._Protocol,
                                           timeout=self._Timeout,
                                           maxRetryTime=self._MaxRetryTime,
                                           parentCollection=self,
                                           queryableAttributeValues=queryableAttributeValues,
                                           lazyPropertyValues=lazyPropertyValues,
                                           cacheDirectory=self._CacheDirectory)

        if self._DatasetType == 'netcdf':
            from GeoEco.Datasets.NetCDF import NetCDFFile

            return NetCDFFile(url.split('/')[-1],       # Just the file name here, not the URL. Our base class, CMRGranuleSearcher, is responsible for downloading the file given its name.
                              parentCollection=self, 
                              queryableAttributeValues=queryableAttributeValues, 
                              lazyPropertyValues=lazyPropertyValues, 
                              cacheDirectory=self.CacheDirectory)

        raise ValueError(_('Programming error in this tool: unknown datasetType %(lt)s. Please contact the MGET development team for assistance.') % {'lt': self._DatasetType})


###################################################################################################
# This module is not meant to be imported directly. Import GeoEco.DataProducts.NASA.PODAAC instead.
###################################################################################################

__all__ = []
