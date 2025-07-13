# CMEMS.py - Defines classes for accessing datasets published by Copernicus
# Marine Service, a.k.a. Copernicus Marine Environmental Monitoring Service
# (CMEMS).
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import json
import math
import os
import pprint
import types

from ..ArcGIS import GeoprocessorManager
from ..Datasets import QueryableAttribute, Grid
from ..Datasets.ArcGIS import ArcGISRaster, ArcGISTable, ArcGISWorkspace
from ..Datasets.Virtual import GridSliceCollection, ClippedGrid, RotatedGlobalGrid, SeafloorGrid, CannyEdgeGrid, _CannyEdgesOverview, ClimatologicalGridCollection
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Matlab import MatlabDependency
from ..SpatialAnalysis.Interpolation import Interpolator
from ..Types import *


class CMEMSARCOArray(Grid):
    __doc__ = DynamicDocString()

    def _GetUsername(self):
        return self._Username

    Username = property(_GetUsername, doc=DynamicDocString())

    def _GetPassword(self):
        return self._Password

    Password = property(_GetPassword, doc=DynamicDocString())

    def _GetDatasetID(self):
        return self._DatasetID

    DatasetID = property(_GetDatasetID, doc=DynamicDocString())

    def _GetVariableShortName(self):
        return self._VariableShortName

    VariableShortName = property(_GetVariableShortName, doc=DynamicDocString())

    def _GetLog10Transform(self):
        return self._Log10Transform

    Log10Transform = property(_GetLog10Transform, doc=DynamicDocString())

    def __init__(self, username, password, datasetID, variableShortName, log10Transform=False, xCoordType='center', yCoordType='center', zCoordType='center', tCoordType='min', lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Username = username
        self._Password = password
        self._DatasetID = datasetID
        self._VariableShortName = variableShortName
        self._Log10Transform = log10Transform
        self._Log10TransformWarningIssued = False
        if log10Transform:
            self._DisplayName = _('log10-transformed variable %(name)s of Copernicus Marine Service dataset %(datasetID)s') % {'name': variableShortName, 'datasetID': datasetID}
        else:
            self._DisplayName = _('variable %(name)s of Copernicus Marine Service dataset %(datasetID)s') % {'name': variableShortName, 'datasetID': datasetID}
        self._URI = None
        self._ZCoords = None
        self._VariableStandardName = None
        self._Dataset = None

        # Do not use the caller's CoordType arguments to set the CornerCoords
        # lazy property yet. We don't know the dimensions of the grid until we
        # query the catalog, so we hold off on setting CornerCoords.

        self._CornerCoordTypes = (tCoordType, zCoordType, yCoordType, xCoordType)

        # Define QueryableAttributes for the DatasetID and VariableShortName.

        queryableAttributes = (QueryableAttribute('DatasetID', _('Dataset ID'), UnicodeStringTypeMetadata()),
                               QueryableAttribute('VariableShortName', _('Variable short name'), UnicodeStringTypeMetadata()))

        queryableAttributeValues = {'DatasetID': datasetID,
                                    'VariableShortName': variableShortName}

        # Initialize the base class.

        super(CMEMSARCOArray, self).__init__(queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues)

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known property, return None.

        if name not in ['SpatialReference', 'Shape', 'Dimensions', 'PhysicalDimensions', 'PhysicalDimensionsFlipped', 'CoordDependencies', 'CoordIncrements', 'TIncrement', 'TIncrementUnit', 'TCornerCoordType', 'CornerCoords', 'UnscaledDataType', 'ScaledDataType', 'UnscaledNoDataValue', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # Currently, we rely on Copernicus and xarray to handle all scaling.

        if name in ['ScaledDataType', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # If we haven't done so already, query the CMEMS catalog with the
        # dataset ID and extract the properties we can get from there.

        if self._URI is None:
            self._LogInfo('Querying Copernicus Marine Service catalogue for dataset ID "%(datasetID)s".' % {'datasetID': self._DatasetID})

            import copernicusmarine

            try:
                # In copernicusmarine 2.0.0 and later, the describe function
                # accepts a dataset_id and will retrieve just that dataset
                # rather than the whole catalog.

                if int(copernicusmarine.__version__.split('.')[0]) >= 2:
                    self._LogDebug('%(class)s 0x%(id)016X: Calling copernicusmarine.describe(dataset_id="%(datasetID)s", disable_progress_bar=True)' % {'class': self.__class__.__name__, 'id': id(self), 'datasetID': self._DatasetID})
                    cat = copernicusmarine.describe(dataset_id=self._DatasetID, disable_progress_bar=True)

                    # cat is now a copernicusmarine.CopernicusMarineCatalogue.
                    # In copernicusmarine 1.x, this object was serialized a
                    # large dictionary using Pydantic's model_dump() method.
                    # We wrote all our subsequent code to walk that
                    # dictionary. To avoid having to rewrite that code against
                    # the new copernicusmarine object model, just dump cat
                    # back to a dictionary.

                    cat = cat.model_dump()

                # In copernicusmarine 1.x, the describe function retrieves the
                # entire catalog and we have to search through it for the
                # dataset we want.

                else:
                    self._LogDebug('%(class)s 0x%(id)016X: Calling copernicusmarine.describe(contains=["%(datasetID)s"], include_datasets=True, disable_progress_bar=True)' % {'class': self.__class__.__name__, 'id': id(self), 'datasetID': self._DatasetID})
                    cat = copernicusmarine.describe(contains=[self._DatasetID], include_datasets=True, disable_progress_bar=True)

            except Exception as e:
                raise RuntimeError(_('Failed to query the Copernicus Marine Service catalogue for dataset ID "%(datasetID)s". The copernicusmarine.describe() function failed with %(e)s: %(msg)s.') % {'datasetID': self._DatasetID, 'e': e.__class__.__name__, 'msg': e})

            if not isinstance(cat, (dict, type(None))):
                raise RuntimeError(_('Failed to query the Copernicus Marine Service catalogue with the copernicusmarine.describe() function. The function returned a %(type)s instance rather than a dictionary. This is unexpected; please contact the MGET development team for assistance.') % {'type': type(cat)})

            if cat is None or len(cat) <= 0:
                raise RuntimeError(_('The Copernicus Marine Service catalogue does not contain a dataset with the ID "%(datasetID)s". Please check the ID and try again. Dataset IDs are case sensitive and must be given exactly as written on the Copernicus Marine Service website.') % {'datasetID': self._DatasetID})

            # Extract the 'static-arco' or 'arco-geo-series' service record
            # for the dataset.

            self._LogDebug('%(class)s 0x%(id)016X: Searching the returned catalogue for dataset.' % {'class': self.__class__.__name__, 'id': id(self)})

            service = None
            variable = None
            debugLines = []

            if 'products' not in cat or not isinstance(cat['products'], list):
                raise RuntimeError(_('The root level of the Copernicus Marine Service catalogue returned by copernicusmarine.describe() does not have a "products" key, or the "products" key does map to a list. This may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.'))

            try:
                for product in cat['products']:
                    if not isinstance(product, dict):
                        self._LogWarning(_('The "products" list at the root level of the Copernicus Marine Service catalogue contains something other than a dictionary. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.'))
                        continue

                    if 'datasets' not in product:
                        self._LogWarning(_('The "products" list at the root level of the Copernicus Marine Service catalogue contains a dictionary that does not have a "datasets" key. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.'))
                        continue

                    try:
                        debugLines.extend(pprint.pformat(product['datasets'], width=160, compact=True).split('\n'))
                    except:
                        pass

                    for dataset in product['datasets']:
                        if not isinstance(dataset, dict):
                            self._LogWarning(_('A "datasets" list in the Copernicus Marine Service catalogue contains something other than a dictionary. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.'))
                            continue

                        if 'dataset_id' not in dataset:
                            self._LogWarning(_('A "datasets" list in the Copernicus Marine Service catalogue contains a dictionary that does not have a "dataset_id" key. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.'))
                            continue

                        if dataset['dataset_id'] != self._DatasetID:
                            continue

                        if 'versions' not in dataset or not isinstance(dataset['versions'], list) or len(dataset['versions']) <= 0:
                            self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" dataset does not contain a "versions" key, or that key does not map to a list, or that list is empty. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                            continue

                        # The catalogue appears to support multiple versions of a
                        # given dataset, but we have not seen this in practice yet.
                        # For now, if there are multiple versions, attempt to access
                        # the latest one by finding the 'label' with the highest
                        # lexical value.

                        best = 0

                        if len(dataset['versions']) > 1:
                            if 'label' not in dataset['versions'][best] or not isinstance(dataset['versions'][best]['label']) or len(dataset['versions'][best]['label']) <= 0:
                                self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a version with no "label", or the label is not a string, or the string is empty. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                            else:
                                for i in range(1, len(dataset['versions'])):
                                    if 'label' not in dataset['versions'][i] or not isinstance(dataset['versions'][i]['label']) or len(dataset['versions'][i]['label']) <= 0:
                                        self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a version with no "label", or the label is not a string, or the string is empty. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                                        continue

                                    if best is None or dataset['versions'][i]['label'] > dataset['versions'][best]['label']:
                                        best = i

                        version = dataset['versions'][best]

                        # Similarly, a given version can have multiple "parts", but
                        # we've never seen more than one and don't know what they're
                        # for. In this case, just take the last part in the list and
                        # search through its services.

                        if 'parts' not in version or not isinstance(version['parts'], list) or len(version['parts']) <= 0:
                            self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a version dictionary with no "parts" key, or that key does not map to a list, or that list is empty. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                            continue

                        if not isinstance(version['parts'][-1], dict) or not 'services' in version['parts'][-1] or not isinstance(version['parts'][-1]['services'], list) or len(version['parts'][-1]['services']) <= 0:
                            self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a version dictionary in which the last item in the parts list is not a dictionary, or that dictionary does not contain a "services" key, or that key does not map to a list, or that list is empty. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                            continue

                        for s in version['parts'][-1]['services']:
                            if not isinstance(s, dict):
                                self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a services list that contains something other than a dictionary. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                                continue

                            # In copernicusmarine 2.0.0, they moved the
                            # members of the service_type dict up and deleted
                            # the service_type dict.

                            if int(copernicusmarine.__version__.split('.')[0]) >= 2:
                                if any([key not in s for key in ['service_format', 'service_name', 'uri', 'variables']]) or \
                                   not isinstance(s['service_format'], (str, type(None))) or \
                                   not isinstance(s['uri'], str) or len(s['uri']) <= 0 or \
                                   not isinstance(s['variables'], list) or len(s['variables']) <= 0 or \
                                   any([not isinstance(v, dict) or \
                                        not 'short_name' in v or not isinstance(v['short_name'], str) or len(v['short_name']) <= 0 or \
                                        not 'standard_name' in v or not isinstance(v['standard_name'], (str, type(None))) or \
                                        not 'coordinates' in v or not isinstance(v['coordinates'], list) \
                                        for v in s['variables']]):
                                    self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a services list that contains a dictionary that does not contain all the required keys or has some unexpected values. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                                    continue

                                for v in s['variables']:
                                    if v['short_name'] == self._VariableShortName and s['service_format'] == 'zarr' and s['service_name'] in ['static-arco', 'arco-geo-series']:
                                        if service is not None:
                                            self._LogWarning(_('The Copernicus Marine Service catalogue contains multiple datasets with the ID "%(datasetID)s", or the the metadata for that dataset contains multiple "static-arco" or "arco-geo-series" services, or the service contains multiple variables named "%(var)s". This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. The first variable of the first service for the first dataset will be used. Check your results carefully. If you suspect a problem, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                                            continue
                                        else:
                                            service = s
                                            variable = v

                            else:   # copernicusmarine 1.x

                                if any([key not in s for key in ['service_format', 'service_type', 'uri', 'variables']]) or \
                                   not isinstance(s['service_format'], (str, type(None))) or \
                                   not isinstance(s['service_type'], dict) or 'service_name' not in s['service_type'] or \
                                   not isinstance(s['uri'], str) or len(s['uri']) <= 0 or \
                                   not isinstance(s['variables'], list) or len(s['variables']) <= 0 or \
                                   any([not isinstance(v, dict) or \
                                        not 'short_name' in v or not isinstance(v['short_name'], str) or len(v['short_name']) <= 0 or \
                                        not 'standard_name' in v or not isinstance(v['standard_name'], (str, type(None))) or \
                                        not 'coordinates' in v or not isinstance(v['coordinates'], list) \
                                        for v in s['variables']]):
                                    self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a services list that contains a dictionary that does not contain all the required keys or has some unexpected values. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                                    continue

                                for v in s['variables']:
                                    if v['short_name'] == self._VariableShortName and s['service_format'] == 'zarr' and s['service_type']['service_name'] in ['static-arco', 'arco-geo-series']:
                                        if service is not None:
                                            self._LogWarning(_('The Copernicus Marine Service catalogue contains multiple datasets with the ID "%(datasetID)s", or the the metadata for that dataset contains multiple "static-arco" or "arco-geo-series" services, or the service contains multiple variables named "%(var)s". This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. The first variable of the first service for the first dataset will be used. Check your results carefully. If you suspect a problem, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                                            continue
                                        else:
                                            service = s
                                            variable = v

                # Fail if we didn't find anything.

                if service is None:
                    raise RuntimeError(_('Could not find a suitable service in the Copernicus Marine Service catalogue from which to access the "%(var)s" variable of the "%(datasetID)s" dataset. If any warnings were reported above, they may indicate why. If none were reported, it may be that the dataset or variable does not exist. Please the dataset ID and variable name carefully.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})

                self._LogDebug('%(class)s 0x%(id)016X: Found a suitable service with URI %(uri)s' % {'class': self.__class__.__name__, 'id': id(self), 'uri': service['uri']})
                self._LogDebug('%(class)s 0x%(id)016X: Using this variable:' % {'class': self.__class__.__name__, 'id': id(self)})
                for line in pprint.pformat(variable, width=160, compact=True).split('\n'):
                    self._LogDebug('%(class)s 0x%(id)016X:    %(line)s' % {'class': self.__class__.__name__, 'id': id(self), 'line': line})

                # Extract the lazy property values from the service and variable
                # records. First, determine the dimensions. Note that we can't
                # determine the *physical* dimension order from the catalogue
                # record. For that, we need to open the dataset itself.

                coordinates = {}

                for coord in variable['coordinates']:
                    if not isinstance(coord, dict) or ('coordinates_id' not in coord and 'coordinate_id' not in coord):
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, the coordinates dictionary for the "%(var)s" variable of the "%(datasetID)s" contains an item that is not a dictionary, or that dictionary does not contain a "coordinates_id" or "coordinate_id" key. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                    key = 'coordinates_id' if 'coordinates_id' in coord else 'coordinate_id'   # copernicusmarine 1.x uses 'coordinates_id', 2.0.0 uses 'coordinate_id'
                    if coord[key] not in ('time', 'depth', 'latitude', 'longitude'):
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, the coordinates dictionary for the "%(var)s" variable of the "%(datasetID)s" contains a coordinate named "%(coord)s". MGET does not recognize this coordinate and therefore cannot process this dataset. MGET can only recognize coordinates named "time", "depth", "latitude", and "longitude". Please check your dataset ID and variable name to ensure they are correct. If they are and you believe MGET should be able to handle this unrecognized coordinate, please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': coord[key]})
                    if coord[key] in coordinates:
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, the coordinates dictionary for the "%(var)s" variable of the "%(datasetID)s" contains more than one coordinate named "%(coord)s". This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': coord[key]})
                    coordinates[coord[key]] = coord

                dimensions = ''
                if 'time' in coordinates:
                    dimensions += 't'
                if 'depth' in coordinates:
                    dimensions += 'z'
                if 'latitude' in coordinates:
                    dimensions += 'y'
                if 'longitude' in coordinates:
                    dimensions += 'x'

                if dimensions not in ['yx', 'zyx', 'tyx', 'tzyx']:
                    raise RuntimeError(_('In the Copernicus Marine Service catalogue, the "%(var)s" variable of the "%(datasetID)s" has the coordinates: %(coords)s. This combination of coordinates is unsupported by MGET. Please check whether this was the dataset and variable you intended to access. For additional assistance, contact the MGET development team.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coords': ', '.join(coordinates)})

                # Determine Shape, CoordIncrements, and CornerCoords. Start with
                # the x coordinate.

                shape = [None] * len(dimensions)
                cornerCoords = [None] * len(dimensions)
                coordIncrements = [None] * len(dimensions)

                for key in ['step', 'minimum_value', 'maximum_value']:
                    for coord in ['longitude', 'latitude']:
                        if key not in coordinates[coord] or not isinstance(coordinates[coord][key], (float, int)):
                            raise RuntimeError(_('In the Copernicus Marine Service catalogue, the %(coord)s coordinate of the %(var)s" variable of the "%(datasetID)s" does not have a "%(attr)s" attribute, or that attribute is not a numeric value. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': coord, 'attr': key})

                xExtent = float(coordinates['longitude']['maximum_value']) - coordinates['longitude']['minimum_value'] + coordinates['longitude']['step']
                shape[-1] = int(round(xExtent / coordinates['longitude']['step']))

                # Check whether the dataset spans about 360 degrees. If so,
                # recompute the step value. We have noticed that products such as
                # GLOBAL_ANALYSISFORECAST_PHY_001_024 contain a 'step' value that
                # is not very precise. If we use their 'step' as our
                # coordIncrement, the grid will not span exactly 360.0 degrees,
                # which will cause problems for some users.

                if abs(360 - xExtent) != 0 and abs(360 - xExtent) / coordinates['longitude']['step'] < 0.001:
                    coordIncrements[-1] = 360. / round(360. / coordinates['longitude']['step'])
                    self._LogDebug('%(class)s 0x%(id)016X: For the longitude coordinate, step=%(step)r, minimum_value=%(min)r, and maximum_value=%(max)r, which yields an extent of %(extent)s. Recomputing step as %(step2)r.' % {'class': self.__class__.__name__, 'id': id(self), 'step': coordinates['longitude']['step'], 'min': coordinates['longitude']['minimum_value'], 'max': coordinates['longitude']['maximum_value'], 'extent': xExtent, 'step2': coordIncrements[-1]})
                else:
                    coordIncrements[-1] = float(coordinates['longitude']['step'])

                cornerCoords[-1] = float(coordinates['longitude']['minimum_value'])
                if self._CornerCoordTypes[-1] == 'min':
                    cornerCoords[-1] += coordIncrements[-1] / 2
                elif self._CornerCoordTypes[-1] == 'max':
                    cornerCoords[-1] -= coordIncrements[-1] / 2

                # If the dataset spans 360 degrees and the left edge is very
                # close to but not exactly -180.0 or 0.0, set it to -180.0 or
                # 0.0, repectively. There appears to be a precision or
                # rounding issue with certain datasets that causes this. It
                # will be problematic to our users.

                if shape[-1] * coordIncrements[-1] == 360.:
                    if abs(cornerCoords[-1] - coordIncrements[-1] / 2 + 180.) / coordIncrements[-1] < 0.001:
                        self._LogDebug('%(class)s 0x%(id)016X: The minimum_value of the longitude coordinate %(min)r yields a left edge of %(left)r, which is very close to but not exactly -180.0. This is probably a precision or rounding error at Copernicus. Setting the left edge to -180.0.' % {'class': self.__class__.__name__, 'id': id(self), 'min': coordinates['longitude']['minimum_value'], 'left': cornerCoords[-1] - coordIncrements[-1] / 2})
                        cornerCoords[-1] = -180. + coordIncrements[-1] / 2
                    elif abs(cornerCoords[-1] - coordIncrements[-1] / 2) / coordIncrements[-1] < 0.001:
                        self._LogDebug('%(class)s 0x%(id)016X: The minimum_value of the longitude coordinate %(min)r yields a left edge of %(left)r, which is very close to but not exactly 0.0. This is probably a precision or rounding error at Copernicus. Setting the left edge to -180.0.' % {'class': self.__class__.__name__, 'id': id(self), 'min': coordinates['longitude']['minimum_value'], 'left': cornerCoords[-1] - coordIncrements[-1] / 2})
                        cornerCoords[-1] = coordIncrements[-1] / 2

                # Handle the y coordinate. 

                yExtent = float(coordinates['latitude']['maximum_value']) - coordinates['latitude']['minimum_value'] + coordinates['latitude']['step']
                shape[-2] = int(round(yExtent / coordinates['latitude']['step']))

                # Similar to the problem with the longitude coordinate not
                # spanning exactly 360.0 degrees, we've seen the latitude
                # coordinate not span exactly 180.0 degrees. Apply same logic.

                if abs(180 - yExtent) != 0 and abs(180 - yExtent) / coordinates['latitude']['step'] < 0.001:
                    coordIncrements[-2] = 180. / round(180. / coordinates['latitude']['step'])
                    self._LogDebug('%(class)s 0x%(id)016X: For the latitude coordinate, step=%(step)r, minimum_value=%(min)r, and maximum_value=%(max)r, which yields an extent of %(extent)s. Recomputing step as %(step2)r.' % {'class': self.__class__.__name__, 'id': id(self), 'step': coordinates['latitude']['step'], 'min': coordinates['latitude']['minimum_value'], 'max': coordinates['latitude']['maximum_value'], 'extent': xExtent, 'step2': coordIncrements[-2]})
                else:
                    coordIncrements[-2] = float(coordinates['latitude']['step'])

                cornerCoords[-2] = float(coordinates['latitude']['minimum_value'])
                if self._CornerCoordTypes[-2] == 'min':
                    cornerCoords[-2] += coordIncrements[-2] / 2
                elif self._CornerCoordTypes[-2] == 'max':
                    cornerCoords[-2] -= coordIncrements[-2] / 2

                # If the bottom edge is very close to but not exactly
                # -90.0, set it to -90.0. There appears to be a precision
                # or rounding issue with certain datasets that causes
                # this. It will be problematic to our users.

                if abs(cornerCoords[-2] - coordIncrements[-2] / 2 + 90.) / coordIncrements[-2] < 0.001:
                    self._LogDebug('%(class)s 0x%(id)016X: The minimum_value of the latitude coordinate %(min)r yields a bottom edge of %(bottom)r, which is very close to but not exactly -90.0. This is probably a precision or rounding error at Copernicus. Setting the bottom edge to -90.0.' % {'class': self.__class__.__name__, 'id': id(self), 'min': coordinates['latitude']['minimum_value'], 'bottom': cornerCoords[-2] - coordIncrements[-2] / 2})
                    cornerCoords[-2] = -90. + coordIncrements[-2] / 2

                # Some datasets such as GLOBAL_ANALYSISFORECAST_PHY_001_024 are
                # node registered rather than cell registered, which means their
                # bottom-most row might be centered at -90.0 or the top most at
                # +90.0. We don't like this, because it means the grid extends
                # below -90.0 or above +90.0, which is impossible. Check for this
                # and move up and/or down one cell as needed to keep the grid
                # within +/- 90.0

                cellsUpFromBottom = 0
                originalBottomEdge = cornerCoords[-2] - coordIncrements[-2]/2
                while cornerCoords[-2] - coordIncrements[-2]/2 < -90.:
                    cellsUpFromBottom += 1
                    shape[-2] -= 1
                    cornerCoords[-2] += coordIncrements[-2]
                if cellsUpFromBottom > 0:
                    self._LogDebug('%(class)s 0x%(id)016X: The bottom edge of the bottom row of this dataset is %(orig)r, which is less than -90.0. Omitting the bottom-most %(skip)i row(s) of this dataset, so the bottom edge will be >= -90.0.' % {'class': self.__class__.__name__, 'id': id(self), 'orig': originalBottomEdge, 'skip': cellsUpFromBottom})

                cellsDownFromTop = 0
                originalTopEdge = cornerCoords[-2] + (shape[-2] - 1)*coordIncrements[-2] + coordIncrements[-2]/2
                while cornerCoords[-2] + (shape[-2] - 1)*coordIncrements[-2] + coordIncrements[-2]/2 > 90.:
                    cellsDownFromTop += 1
                    shape[-2] -= 1
                if cellsDownFromTop > 0:
                    self._LogDebug('%(class)s 0x%(id)016X: The top edge of the top row of this dataset is %(orig)r, which is greater than 90.0. Omitting the top-most %(skip)i row(s) of this dataset, so the top edge will be <= 90.0.' % {'class': self.__class__.__name__, 'id': id(self), 'orig': originalTopEdge, 'skip': cellsDownFromTop})

                # Handle the z coordinate.

                zCoords = None

                if 'z' in dimensions:
                    if 'values' in coordinates['depth'] and isinstance(coordinates['depth']['values'], list) and len(coordinates['depth']['values']) > 0:
                        numPositive = 0
                        for value in coordinates['depth']['values']:
                            if not isinstance(value, (float, int)):
                                raise RuntimeError(_('In the Copernicus Marine Service catalogue, the %(coord)s coordinate of the %(var)s" variable of the "%(datasetID)s" contains an item that is not a numerical value. This is unexpected and indicates there may be problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': 'depth'})
                            if value >= 0:
                                numPositive += 1
                        if numPositive > 0 and numPositive < len(coordinates['depth']['values']):
                            raise RuntimeError(_('In the Copernicus Marine Service catalogue, the %(coord)s coordinate of the %(var)s" variable of the "%(datasetID)s" contains both positive and negative values. This is unexpected and indicates there may be problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': 'depth'})

                        zCoords = [abs(depth) for depth in coordinates['depth']['values']]
                        if not all([zCoords[i+1] > zCoords[i] for i in range(len(zCoords)-1)]) and not all([zCoords[i+1] < zCoords[i] for i in range(len(zCoords)-1)]):
                            raise RuntimeError(_('In the Copernicus Marine Service catalogue, the %(coord)s coordinate of the %(var)s" variable of the "%(datasetID)s" is neither monotonically increasing nor monotonically decreasing. This is unexpected and indicates there may be problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance. The coordinate values are: %(values)s') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': 'depth', 'values': ', '.join(repr(val) for val in coordinates['depth']['values'])})

                        zCoords.sort()      # zCoords are now guaranteed to be positive and in ascending order

                        shape[-3] = len(zCoords)
                        cornerCoords[-3] = None
                        coordIncrements[-3] = None

                    else:
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, the %(coord)s coordinate of the %(var)s" variable of the "%(datasetID)s" does not have a "values" list. Currently, MGET only supports datasets that explicitly list their depth coordinate values. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': 'depth'})

                # Handle the t coordinate.

                tIncrementUnit = None

                if 't' in dimensions:

                    # Parse the units attribute.

                    key = 'units' if 'units' in coordinates['time'] else 'coordinate_unit'   # copernicusmarine 1.x used 'units', 2.0.0 used 'coordinate_unit'

                    if key not in coordinates['time'] or not isinstance(coordinates['time'][key], str):
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, the "time" coordinate of the %(var)s" variable of the "%(datasetID)s" does not have a "units" or "coordinate_unit" attribute, or that attribute is not a string value. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})

                    units = coordinates['time'][key].lower().split()
                    if len(units) < 4 or units[0] not in ['milliseconds', 'seconds', 'minutes', 'hours', 'days'] or units[1] != 'since':
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, for the "time" coordinate of the %(var)s" variable of the "%(datasetID)s", the value of the "units" attribute, "%(units)s", could not be parsed. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'units': coordinates['time'][key]})

                    try:
                        since = datetime.datetime.strptime((units[2] + ' ' + units[3])[:19], '%Y-%m-%d %H:%M:%S')
                    except:
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, for the "time" coordinate of the %(var)s" variable of the "%(datasetID)s", the value of the "units" attribute, "%(units)s", could not be parsed. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'units': coordinates['time'][key]})

                    # Handle times being provided with a constant step.

                    constantStep = True
                    for key in ['step', 'minimum_value', 'maximum_value']:
                        if key not in coordinates['time'] or not isinstance(coordinates['time'][key], (float, int)):
                            constantStep = False

                    if constantStep:
                        numSteps = (coordinates['time']['maximum_value'] - coordinates['time']['minimum_value'] + coordinates['time']['step']) / coordinates['time']['step']
                        if numSteps % 1 != 0:
                            self._LogWarning(_('In the Copernicus Marine Service catalogue, for the "time" coordinate of the %(var)s" variable of the "%(datasetID)s", the "maximum_value" minus the "minimum_value" is not evenly divisible by the "step". This is unexpected but MGET will proceed with accessing the dataset. Check your results carefully. If you suspect a problem, please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})

                        shape[0] = int(math.trunc(numSteps))
                        coordIncrements[0] = float(coordinates['time']['step'])

                        if units[0] == 'milliseconds':
                            tIncrementUnit = 'second'    # We don't support milliseconds; convert to seconds
                            cornerCoords[0] = since + datetime.timedelta(milliseconds=coordinates['time']['minimum_value'])
                            coordIncrements[0] = coordIncrements[0] / 1000

                        elif units[0] == 'seconds':
                            tIncrementUnit = 'second'
                            cornerCoords[0] = since + datetime.timedelta(seconds=coordinates['time']['minimum_value'])

                        elif units[0] == 'minutes':
                            tIncrementUnit = 'minute'
                            cornerCoords[0] = since + datetime.timedelta(minutes=coordinates['time']['minimum_value'])

                        elif units[0] == 'hours':
                            tIncrementUnit = 'hour'
                            cornerCoords[0] = since + datetime.timedelta(hours=coordinates['time']['minimum_value'])

                        elif units[0] == 'days':
                            tIncrementUnit = 'day'
                            cornerCoords[0] = since + datetime.timedelta(days=coordinates['time']['minimum_value'])

                        else:
                            raise RuntimeError(_('Programming error in this tool: unexpected time unit "%(units)s". Please contact the MGET development team for assistance.') % {'units': units[0]})

                    # Handle times provided with a list of values.

                    elif 'values' in coordinates['time'] and isinstance(coordinates['time']['values'], list) and len(coordinates['time']['values']) > 0:
                        for value in coordinates['time']['values']:
                            if not isinstance(value, (float, int)):
                                raise RuntimeError(_('In the Copernicus Marine Service catalogue, the %(coord)s coordinate of the %(var)s" variable of the "%(datasetID)s" contains an item that is not a numerical value. This is unexpected and indicates there may be problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': 'time'})

                        shape[0] = len(coordinates['time']['values'])

                        # Convert all the values to datetimes.

                        if units[0] == 'milliseconds':
                            tCoords = [since + datetime.timedelta(milliseconds=value) for value in coordinates['time']['values']]

                        elif units[0] == 'seconds':
                            tCoords = [since + datetime.timedelta(seconds=value) for value in coordinates['time']['values']]

                        elif units[0] == 'minutes':
                            tCoords = [since + datetime.timedelta(minutes=value) for value in coordinates['time']['values']]

                        elif units[0] == 'hours':
                            tCoords = [since + datetime.timedelta(hours=value) for value in coordinates['time']['values']]

                        elif units[0] == 'days':
                            tCoords = [since + datetime.timedelta(days=value) for value in coordinates['time']['values']]

                        else:
                            raise RuntimeError(_('Programming error in this tool: unexpected time unit "%(units)s". Please contact the MGET development team for assistance.') % {'units': units[0]})

                        # If there is only one time slice, we can't deduce the
                        # time step. Assume it is 1 day.

                        cornerCoords[0] = tCoords[0]

                        if shape[0] == 1:
                            coordIncrements[0] = 1.
                            tIncrementUnit = 'day'

                        # Otherwise, check whether the values increase by the same
                        # relative amount of time. If so, configure ourselves with
                        # a constant t increment.

                        else:
                            import dateutil.relativedelta

                            tCoords.sort()
                            deltas = [dateutil.relativedelta.relativedelta(tCoords[i+1], tCoords[i]).normalized() for i in range(len(tCoords) - 1)]

                            if len(set(deltas)) == 1:
                                if all([getattr(deltas[0], attr) == 0 for attr in ['microseconds', 'seconds', 'minutes', 'hours', 'days', 'weeks']]):
                                    if deltas[0].months == 0:
                                        if deltas[0].years > 0:
                                            coordIncrements[0] = deltas[0].years
                                            tIncrementUnit = 'year'
                                        else:
                                            raise RuntimeError(_('In the Copernicus Marine Service catalogue, the values of the "time" coordinate of the %(var)s" variable of the "%(datasetID)s" appear to contain duplicates. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                                    else:
                                        coordIncrements[0] = float(deltas[0].months + deltas[0].years * 12)
                                        tIncrementUnit = 'month'

                                elif all([getattr(deltas[0], attr) == 0 for attr in ['months', 'years']]):
                                    if deltas.microseconds > 0:
                                        coordIncrements[0] = float(deltas[0].microseconds * 0.000001 + deltas[0].seconds + deltas[0].minutes*60 + deltas[0].hours*60*60 + deltas[0].days*60*60*24 + deltas[0].weeks*60*60*24*7)
                                        tIncrementUnit = 'second'
                                    elif deltas.seconds > 0:
                                        coordIncrements[0] = float(deltas[0].seconds + deltas[0].minutes*60 + deltas[0].hours*60*60 + deltas[0].days*60*60*24 + deltas[0].weeks*60*60*24*7)
                                        tIncrementUnit = 'second'
                                    elif deltas.minutes > 0:
                                        coordIncrements[0] = float(deltas[0].minutes + deltas[0].hours*60 + deltas[0].days*60*24 + deltas[0].weeks*60*24*7)
                                        tIncrementUnit = 'minute'
                                    elif deltas.hours > 0:
                                        coordIncrements[0] = float(deltas[0].hours + deltas[0].days*24 + deltas[0].weeks*24*7)
                                        tIncrementUnit = 'hour'
                                    elif deltas.days > 0 or deltas.weeks > 0:
                                        coordIncrements[0] = float(deltas[0].days + deltas[0].weeks*7)
                                        tIncrementUnit = 'day'
                                    else:
                                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, the values of the "time" coordinate of the %(var)s" variable of the "%(datasetID)s" appear to contain duplicates. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                            else:
                                raise RuntimeError(_('In the Copernicus Marine Service catalogue, the values of the "time" coordinate of the %(var)s" variable of the "%(datasetID)s" do not monotonically increase. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                    else:
                        raise RuntimeError(_('In the Copernicus Marine Service catalogue, the attributes of the "time" coordinate of the %(var)s" variable of the "%(datasetID)s" could not be recognized. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})

            # If we raised an exception, debug log the datasets in the
            # catalogue, so we can look at them.

            except:
                if len(debugLines) > 0:
                    self._LogDebug('%(class)s 0x%(id)016X: Got the following datasets:' % {'class': self.__class__.__name__, 'id': id(self)})
                    for line in debugLines:
                        self._LogDebug('%(class)s 0x%(id)016X:    %(line)s' % {'class': self.__class__.__name__, 'id': id(self), 'line': line})
                raise

            # We successfully extracted all of the values. Save them.

            proj4String = '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs'

            self.SetLazyPropertyValue('SpatialReference', self.ConvertSpatialReference('proj4', proj4String, 'obj'))
            self.SetLazyPropertyValue('Dimensions', dimensions)
            self.SetLazyPropertyValue('Shape', shape)
            self.SetLazyPropertyValue('CoordDependencies', tuple([None] * len(dimensions)))
            self.SetLazyPropertyValue('CornerCoords', tuple(cornerCoords))
            self.SetLazyPropertyValue('CoordIncrements', tuple(coordIncrements))
            self.SetLazyPropertyValue('TIncrement', coordIncrements[0] if dimensions[0] == 't' else None)
            self.SetLazyPropertyValue('TIncrementUnit', tIncrementUnit)
            self.SetLazyPropertyValue('TCornerCoordType', self._CornerCoordTypes[0])

            self._ZCoords = zCoords
            self._VariableStandardName = variable['standard_name']
            self._URI = service['uri']

            # Log a debug message with the lazy property values.

            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: Shape=%(Shape)r, Dimensions=%(Dimensions)r, CoordDependencies=%(CoordDependencies)r, CoordIncrements=%(CoordIncrements)r, TIncrement=%(TIncrement)r, TIncrementUnit=%(TIncrementUnit)r, CornerCoords=%(CornerCoords)r, TCornerCoordType=%(TCornerCoordType)r, SpatialReference=%(SpatialReference)r.'),
                           {'class': self.__class__.__name__, 'id': id(self), 'dn': self.DisplayName,
                            'Shape': self.GetLazyPropertyValue('Shape', allowPhysicalValue=False),
                            'Dimensions': self.GetLazyPropertyValue('Dimensions', allowPhysicalValue=False),
                            'CoordDependencies': self.GetLazyPropertyValue('CoordDependencies', allowPhysicalValue=False),
                            'CoordIncrements': self.GetLazyPropertyValue('CoordIncrements', allowPhysicalValue=False),
                            'TIncrement': self.GetLazyPropertyValue('TIncrement', allowPhysicalValue=False),
                            'TIncrementUnit': self.GetLazyPropertyValue('TIncrementUnit', allowPhysicalValue=False),
                            'CornerCoords': self.GetLazyPropertyValue('CornerCoords', allowPhysicalValue=False),
                            'TCornerCoordType': self.GetLazyPropertyValue('TCornerCoordType', allowPhysicalValue=False),
                            'SpatialReference': proj4String})

        # If the caller is asking for one of the lazy properties we set above,
        # return it now.

        if name in ['Shape', 'Dimensions', 'CoordDependencies', 'CoordIncrements', 'TIncrement', 'TIncrementUnit', 'CornerCoords', 'TCornerCoordType', 'SpatialReference']:
            return self.GetLazyPropertyValue(name, allowPhysicalValue=False)

        # The caller is asking for a lazy property that requires us to open
        # the dataset itself. Open it and get the DataArray.

        self._Open()

        try:
            da = self._Dataset[self._VariableShortName]
        except Exception as e:
            raise RuntimeError(_('Failed to get the variable "%(var)s" of Copernicus Marine Service dataset "%(url)s". The dataset was successfully opened but accessing the variable failed. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance. The following error may indicate the problem: %(e)s: %(msg)s.') % {'url': self._URI, 'var': self._VariableShortName, 'e': e.__class__.__name__, 'msg': e})

        # Obtain the remaining lazy properties, starting with
        # PhysicalDimensions.

        physicalDimensions = ''

        for dim in da.dims:
            if dim == 'time':
                physicalDimensions += 't'
            elif dim == 'depth':
                physicalDimensions += 'z'
            elif dim == 'latitude':
                physicalDimensions += 'y'
            elif dim == 'longitude':
                physicalDimensions += 'x'
            else:
                raise RuntimeError(_('The variable "%(var)s" of Copernicus Marine Service dataset "%(url)s" has an unknown dimension "%(dim)s". MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'url': self._URI, 'var': self._VariableShortName, 'dim': dim})

        if len(physicalDimensions) != len(set(physicalDimensions)):
            raise RuntimeError(_('The variable "%(var)s" of Copernicus Marine Service dataset "%(url)s" contains duplicate dimensions %(dims)s. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'url': self._URI, 'var': self._VariableShortName, 'dims': da.dims})

        if set(physicalDimensions) != set(self.GetLazyPropertyValue('Dimensions', allowPhysicalValue=False)):
            raise RuntimeError(_('The dimensions %(physDims)s for variable "%(var)s" of Copernicus Marine Service dataset "%(url)s" do not match what is in the Copernicus Marine Service catalogue: %(dims)s. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'url': self._URI, 'var': self._VariableShortName, 'physDims': set(physicalDimensions), 'dims': set(self.GetLazyPropertyValue('Dimensions', allowPhysicalValue=False))})

        # Determine if any of the physical dimensions are flipped (i.e. in
        # descending order).

        import numpy

        physicalDimensionsFlipped = []
        
        for dim in da.dims:
            if len(da.coords[dim].values) < 2:
                physicalDimensionsFlipped.append(False)
            else:
                values = da.coords[dim].values[:2]
                if dim == 'depth':
                    values = numpy.abs(values)
                physicalDimensionsFlipped.append(values[1] < values[0])

        # Get the unscaledDataType.

        unscaledDataType = str(da.dtype)

        if unscaledDataType not in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:
            raise RuntimeError(_('The variable "%(var)s" of Copernicus Marine Service dataset "%(url)s" has an unsuppored data type "%(dataType)s". MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'url': self._URI, 'var': self._VariableShortName, 'dataType': unscaledDataType})

        # Get the unscaledNoDataValue. We don't actually know how Copernicus
        # indicates the NoData value but assume they use one of the
        # commonly-used NetCDF attributes missing_value or _FillValue. If
        # those are not present and the data are a floating point type, use
        # nan.

        unscaledNoDataValue = None

        for attr in ['missing_value', '_FillValue']:
            if attr in da.attrs and isinstance(da.attrs[attr], (float, int)):
                if unscaledDataType.startswith('float'):
                    unscaledNoDataValue = float(da.attrs[attr])
                else:
                    unscaledNoDataValue = int(da.attrs[attr])

        if unscaledNoDataValue is None and unscaledDataType.startswith('float'):
            unscaledNoDataValue = numpy.nan

        # We successfully extracted all of the values. Save them.

        self.SetLazyPropertyValue('PhysicalDimensions', physicalDimensions)
        self.SetLazyPropertyValue('PhysicalDimensionsFlipped', physicalDimensionsFlipped)
        self.SetLazyPropertyValue('UnscaledDataType', unscaledDataType)
        self.SetLazyPropertyValue('UnscaledNoDataValue', unscaledNoDataValue)

        # Log a debug message with the lazy property values.

        self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: PhysicalDimensions=%(PhysicalDimensions)r, PhysicalDimensionsFlipped=%(PhysicalDimensionsFlipped)r, UnscaledDataType=%(UnscaledDataType)r, UnscaledNoDataValue=%(UnscaledNoDataValue)r.'),
                       {'class': self.__class__.__name__, 'id': id(self), 'dn': self.DisplayName,
                        'PhysicalDimensions': self.GetLazyPropertyValue('PhysicalDimensions', allowPhysicalValue=False),
                        'PhysicalDimensionsFlipped': self.GetLazyPropertyValue('PhysicalDimensionsFlipped', allowPhysicalValue=False),
                        'UnscaledDataType': self.GetLazyPropertyValue('UnscaledDataType', allowPhysicalValue=False),
                        'UnscaledNoDataValue': self.GetLazyPropertyValue('UnscaledNoDataValue', allowPhysicalValue=False)})

        # Return the property value.

        return self.GetLazyPropertyValue(name, allowPhysicalValue=False)

    def _Open(self):
        if self._Dataset is None:
            import copernicusmarine
            try:
                from copernicusmarine.python_interface.open_dataset import open_dataset_from_arco_series
            except:
                from copernicusmarine.download_functions.download_arco_series import open_dataset_from_arco_series
            try:
                from copernicusmarine.python_interface.open_dataset import DepthParameters, GeographicalParameters, TemporalParameters
            except:
                from copernicusmarine.download_functions.subset_parameters import DepthParameters, GeographicalParameters, TemporalParameters
            if int(copernicusmarine.__version__.split('.')[0]) >= 2:
                try:
                    from copernicusmarine.python_interface.open_dataset import DEFAULT_COORDINATES_SELECTION_METHOD
                except:
                    from copernicusmarine.core_functions.models import DEFAULT_COORDINATES_SELECTION_METHOD

            if isinstance(self._VariableStandardName, str) and len(self._VariableStandardName) > 0:
                variableName = self._VariableStandardName
            else:
                variableName = self._VariableShortName
                self._LogDebug('%(class)s 0x%(id)016X: The "standard_name" attribute was %(standardName)r, so the "short_name" of %(shortName)r will be used instead.' % {'class': self.__class__.__name__, 'id': id(self), 'url': self._URI, 'standardName': self._VariableStandardName, 'shortName': self._VariableShortName})

            self._LogDebug('%(class)s 0x%(id)016X: Opening the xarray by calling copernicusmarine\'s open_dataset_from_arco_series(username="%(username)s", password=\'*****\', dataset_url="%(url)s", variables=["%(var)s"], geographical_parameters=GeographicalParameters(), temporal_parameters=TemporalParameters(), depth_parameters=DepthParameters())' % {'class': self.__class__.__name__, 'username': self._Username, 'id': id(self), 'url': self._URI, 'var': variableName})

            try:
                if int(copernicusmarine.__version__.split('.')[0]) > 2 or int(copernicusmarine.__version__.split('.')[0]) == 2 and int(copernicusmarine.__version__.split('.')[1]) >= 2:
                    self._Dataset = open_dataset_from_arco_series(username=self._Username, 
                                                                  password=self._Password,
                                                                  dataset_url=self._URI,
                                                                  variables=[variableName],
                                                                  geographical_parameters=GeographicalParameters(),
                                                                  temporal_parameters=TemporalParameters(),
                                                                  depth_parameters=DepthParameters(),
                                                                  coordinates_selection_method=DEFAULT_COORDINATES_SELECTION_METHOD,
                                                                  optimum_dask_chunking=None)                                          # copernicusmarine 2.2.0 renamed opening_dask_chunks
                elif int(copernicusmarine.__version__.split('.')[0]) == 2 and int(copernicusmarine.__version__.split('.')[1]) == 1:
                    self._Dataset = open_dataset_from_arco_series(username=self._Username, 
                                                                  password=self._Password,
                                                                  dataset_url=self._URI,
                                                                  variables=[variableName],
                                                                  geographical_parameters=GeographicalParameters(),
                                                                  temporal_parameters=TemporalParameters(),
                                                                  depth_parameters=DepthParameters(),
                                                                  coordinates_selection_method=DEFAULT_COORDINATES_SELECTION_METHOD,
                                                                  opening_dask_chunks='auto')                                          # copernicusmarine 2.1.0 renamed chunks parameter
                elif int(copernicusmarine.__version__.split('.')[0]) == 2:
                    self._Dataset = open_dataset_from_arco_series(username=self._Username, 
                                                                  password=self._Password,
                                                                  dataset_url=self._URI,
                                                                  variables=[variableName],
                                                                  geographical_parameters=GeographicalParameters(),
                                                                  temporal_parameters=TemporalParameters(),
                                                                  depth_parameters=DepthParameters(),
                                                                  coordinates_selection_method=DEFAULT_COORDINATES_SELECTION_METHOD,   # Added and required in copernicusmarine 2.0.0
                                                                  chunks='auto')
                else:
                    self._Dataset = open_dataset_from_arco_series(username=self._Username, 
                                                                  password=self._Password,
                                                                  dataset_url=self._URI,
                                                                  variables=[variableName],
                                                                  geographical_parameters=GeographicalParameters(),
                                                                  temporal_parameters=TemporalParameters(),
                                                                  depth_parameters=DepthParameters(),
                                                                  chunks='auto')
            except Exception as e:
                raise RuntimeError(_('Failed to open Copernicus Marine Service dataset "%(url)s". Please check your internet connectivity and that your username and password is correct. The following error, reported by the copernicusmarine\'s open_dataset_from_arco_series() function, may indicate the problem: %(e)s: %(msg)s.') % {'url': self._URI, 'e': e.__class__.__name__, 'msg': e})

            self._LogDebug('%(class)s 0x%(id)016X: xarray opened successfully.' % {'class': self.__class__.__name__, 'id': id(self)})

            self._RegisterForCloseAtExit()

    def _Close(self):
        if hasattr(self, '_Dataset') and self._Dataset is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Closing the xarray.'), {'class': self.__class__.__name__, 'id': id(self)})
            self._Dataset.close()
            self._Dataset = None
        super(CMEMSARCOArray, self)._Close()

    def _GetCoords(self, coord, coordNum, slices, sliceDims, fixedIncrementOffset):
        if coord != 'z':
            raise RuntimeError(_('CMEMSARCOArray._GetCoords() called with coord == \'%(coord)s\'. This should never happen. Please contact the MGET development team for assistance.') % {'coord': coord})

        import numpy

        zCoords = self._ZCoords
        if fixedIncrementOffset == -0.5:
            zCoords = [0.0] + list(map(lambda a, b: (a+b)/2., zCoords[:-1], zCoords[1:]))
        elif fixedIncrementOffset == 0.5:
            zCoords = list(map(lambda a, b: (a+b)/2., zCoords[:-1], zCoords[1:])) + [11000.0]
        if slices is None:
            return numpy.array(zCoords)

        return numpy.array(zCoords).__getitem__(*slices)

    def _ReadNumpyArray(self, sliceList):
        import numpy

        self._Open()
        sliceName = ','.join([str(s.start) + ':' + str(s.stop) for s in sliceList])
        self._LogDebug(_('%(class)s 0x%(id)016X: Reading slice [%(slice)s] of %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'slice': sliceName, 'dn': self.DisplayName})
        try:
            data = self._Dataset[self._VariableShortName].__getitem__(tuple(sliceList)).data
            data = data.compute().copy() if hasattr(data, 'compute') else data.copy()
        except Exception as e:
            raise RuntimeError(_('Failed to read slice [%(slice)s] of %(dn)s. Detailed error information: %(e)s: %(msg)s.') % {'slice': sliceName, 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        if self._Log10Transform:
            log10NonPositive = False

            # Handle log10 transform of a single value (a scalar).

            if not isinstance(data, numpy.ndarray) and data is not None and numpy.isfinite(data) and data != self.UnscaledNoDataValue:
                if data > 0:
                    data = numpy.asarray(numpy.log10(data), dtype=self.UnscaledDataType)
                else:
                    data = self.UnscaledNoDataValue if self.UnscaledNoDataValue is not None else numpy.nan
                    log10NonPositive = True

            # Handle log10 transform of an array of values.

            elif isinstance(data, numpy.ndarray):
                hasData = numpy.logical_and(numpy.isfinite(data), numpy.invert(Grid.numpy_equal_nan(data, self.UnscaledNoDataValue)))
                if hasData.any():
                    hasDataAndIsPositive = numpy.where(hasData, data > 0, False)
                    data[hasDataAndIsPositive] = numpy.log10(data[hasDataAndIsPositive])
                    log10NonPositive = hasDataAndIsPositive.sum() < hasData.sum()
                    if log10NonPositive:
                        hasDataAndIsNonPositive = numpy.where(hasData, data <= 0, False)
                        data[hasDataAndIsNonPositive] = self.UnscaledNoDataValue if self.UnscaledNoDataValue is not None else numpy.nan

            # If we tried to transform a non-positive number and have not
            # issued a warning about it before, do so now.

            if log10NonPositive and not self._Log10TransformWarningIssued:
                self._LogWarning(_('Some values of %(dn)s could not be log-transformed because the values were non-positive. These values will be treated as missing data. This warning will not be reported again for this dataset.')% {'dn': self.DisplayName})
                self._Log10TransformWarningIssued = True

        return data, self.UnscaledNoDataValue

    @classmethod
    def _RotateAndClip(cls, grid, rotationOffset=None, spatialExtent=None, minDepth=None, maxDepth=None, startDate=None, endDate=None):
        
        # Rotate the grid, if requested.
        
        if rotationOffset is not None:
            sr = grid.GetSpatialReference('obj')
            if not sr.IsGeographic():
                raise ValueError(_('Cannot rotate %(dn)s. This dataset uses a projected cooordinate system and the rotation option is only implemented for datasets that use a geographic (unprojected) coordinate system.') % {'dn': grid.DisplayName})
            if grid.MaxCoords['x', -1] - grid.MinCoords['x', 0] < 360:
                raise ValueError(_('Cannot rotate %(dn)s. This dataset only spans %(degrees)s degrees of longitude. It must span 360 degrees in order to be rotatable.') % {'dn': grid.DisplayName, 'degrees': grid.MaxCoords['x', -1] - grid.MinCoords['x', 0]})

            grid = RotatedGlobalGrid(grid, rotationOffset, 'Map units')

        # Clip the grid, if requested.

        if spatialExtent is not None or minDepth is not None or maxDepth is not None or startDate is not None or endDate is not None:
            xMin, yMin, xMax, yMax = None, None, None, None
            if spatialExtent is not None:
                from GeoEco.Types import EnvelopeTypeMetadata
                xMin, yMin, xMax, yMax = EnvelopeTypeMetadata.ParseFromArcGISString(spatialExtent)

            grid = ClippedGrid(grid, 'Map coordinates', xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax, zMin=minDepth, zMax=maxDepth, tMin=startDate, tMax=endDate)

        # Return the grid.

        return grid

    @classmethod
    def CreateArcGISRasters(cls, username, password, datasetID, variableShortName, 
                            outputWorkspace, mode='Add', log10Transform=False, 
                            xCoordType='center', yCoordType='center', zCoordType='center', tCoordType='min',
                            rotationOffset=None, spatialExtent=None, 
                            minDepth=None, maxDepth=None, startDate=None, endDate=None,
                            rasterExtension='.img', rasterNameExpressions=None, calculateStatistics=True, buildPyramids=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Construct a list of grids to import and import them to the output
        # workspace as rasters.

        grids, rasterNameExpressions, queryableAttributes = \
            cls._ConstructGrids(username, password, datasetID, variableShortName, 
                                outputWorkspace, log10Transform,
                                xCoordType, yCoordType, zCoordType, tCoordType,
                                rotationOffset, spatialExtent, 
                                minDepth, maxDepth, startDate, endDate,
                                rasterExtension, rasterNameExpressions)

        workspace = ArcGISWorkspace(outputWorkspace, ArcGISRaster, pathCreationExpressions=rasterNameExpressions, cacheTree=True, queryableAttributes=queryableAttributes)
        workspace.ImportDatasets(grids, mode, calculateStatistics=calculateStatistics, buildPyramids=buildPyramids)

        return outputWorkspace

    @classmethod
    def _ConstructGrids(cls, username, password, datasetID, variableShortName, 
                        outputWorkspace, log10Transform,
                        xCoordType, yCoordType, zCoordType, tCoordType,
                        rotationOffset, spatialExtent, 
                        minDepth, maxDepth, startDate, endDate,
                        rasterExtension, rasterNameExpressions,
                        wrapperGridClass=None, wrapperGridParams={}, vsnPostfix=''):

        # If rasterNameExpressions is not None, ignore rasterExtension.

        if rasterNameExpressions is not None:
            rasterExtension = None

        # Instantiate the CMEMSARCOArray. 

        grid = CMEMSARCOArray(username, password, datasetID, variableShortName, log10Transform=log10Transform, xCoordType=xCoordType, yCoordType=yCoordType, zCoordType=zCoordType, tCoordType=tCoordType)
        try:
            # If rasterNameExpressions is None, we will determine a default
            # value. First, do some preliminary work related to this.

            if rasterNameExpressions is None:

                # If the grid contains a t dimension, determine the
                # default suffix representing time.

                if 't' in grid.Dimensions:
                    if grid.TIncrementUnit == 'year' or grid.TIncrementUnit == 'month' and grid.CoordIncrements[0] % 12 == 0:
                        timeSuffix = '_%%Y'
                    elif grid.TIncrementUnit == 'month':
                        timeSuffix = '_%%Y%%m'
                    elif grid.TIncrementUnit == 'day' or grid.TIncrementUnit == 'hour' and grid.CoordIncrements[0] % 24 == 0 or grid.TIncrementUnit == 'minute' and grid.CoordIncrements[0] % 1440 == 0 or grid.TIncrementUnit == 'second' and grid.CoordIncrements[0] % 86400 == 0:
                        timeSuffix = '_%%Y%%m%%d'
                    else:
                        timeSuffix = '_%%Y%%m%%d_%%H%%M%%S'

                # If the grid contains a z dimension, determine whether any
                # digits should appear after the decimal point of the depth.
                # Also determine the maximum length of the depth string, so we
                # can zero pad it.

                if 'z' in grid.Dimensions:
                    depths = grid.MinCoords['z', :] if zCoordType == 'min' else grid.CenterCoords['z', :] if zCoordType == 'center' else grid.MaxCoords['z', :]
                    if all(depth % 1 == 0 for depth in depths):
                        depthDecimalDigits = 0
                    else:
                        for depthDecimalDigits in range(1, 15):
                            fmt = '%%0.%if' % depthDecimalDigits
                            if len(set([fmt % depth for depth in depths])) == len(depths):
                                break

                    fmt = '%%0.%if' % depthDecimalDigits
                    depthStrLen = max([len(fmt % depth) for depth in depths])

                # Determine whether the outputWorkspace is a file system
                # directory or not. If it is, then our default
                # rasterNameExpressions will store the rasters in a tree.
                # Otherwise it will construct a flat list of very long unique
                # names.

                GeoprocessorManager.InitializeGeoprocessor()
                gp = GeoprocessorManager.GetWrappedGeoprocessor()
                d = gp.Describe(outputWorkspace)
                outputWorkspaceIsDir = os.path.isdir(outputWorkspace) and (str(d.DataType).lower() != 'workspace' or str(d.DataType).lower() == 'filesystem')

            # Based on the dimensions of the grid, create a list of 2D slices
            # to import, a list of additional QueryableAttributes for the z
            # and t dimensions as appropriate, and determine the default value
            # of rasterNameExpressions if it was not provided.

            if grid.Dimensions == 'yx':
                grids = [cls._RotateAndClip(grid, rotationOffset, spatialExtent)]
                if wrapperGridClass is not None:
                    grids = [wrapperGridClass(grids[0], **wrapperGridParams)]
                qa = []
                if rasterNameExpressions is None:
                    if outputWorkspaceIsDir:
                        rasterNameExpressions = ['%(DatasetID)s', 
                                                 '%(VariableShortName)s' + vsnPostfix]
                    else:
                        rasterNameExpressions = ['Copernicus_%(DatasetID)s_%(VariableShortName)s' + vsnPostfix] 

            elif grid.Dimensions == 'tyx':
                clippedGrid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, startDate=startDate, endDate=endDate)
                wrappedGrid = wrapperGridClass(clippedGrid, **wrapperGridParams) if wrapperGridClass is not None else clippedGrid
                grids = GridSliceCollection(wrappedGrid, tQACoordType='min').QueryDatasets(reportProgress=False)
                qa = [QueryableAttribute('DateTime', _('Date'), DateTimeTypeMetadata())]
                if rasterNameExpressions is None:
                    if outputWorkspaceIsDir:
                        rasterNameExpressions = ['%(DatasetID)s', 
                                                 '%(VariableShortName)s' + vsnPostfix, 
                                                 '%(VariableShortName)s' + vsnPostfix + timeSuffix]
                        if '%%d' in timeSuffix:
                            rasterNameExpressions.insert(-1, '%%Y')
                    else:
                        rasterNameExpressions = ['Copernicus_%(DatasetID)s_%(VariableShortName)s' + vsnPostfix + timeSuffix] 

            elif grid.Dimensions in ['zyx', 'tzyx']:

                # If the caller requested a minimum depth that is within a
                # realistic range, instantiate those grids.

                grids = []
                if minDepth is None or minDepth <= 5500.:
                    clippedGrid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, minDepth, maxDepth, startDate if 't' in grid.Dimensions else None, endDate if 't' in grid.Dimensions else None)
                    wrappedGrid = wrapperGridClass(clippedGrid, **wrapperGridParams) if wrapperGridClass is not None else clippedGrid
                    grids.extend(GridSliceCollection(wrappedGrid, tQACoordType=grid._CornerCoordTypes[0] if 't' in grid.Dimensions else None, zQACoordType=grid._CornerCoordTypes[-3]).QueryDatasets(reportProgress=False))

                # If the caller requested a maximum depth that is greater than
                # or equal to 20000, instantiate a grid representing the
                # values at the seafloor.

                if minDepth == 20000. or maxDepth is not None and maxDepth >= 20000.:
                    clippedGrid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, None, None, startDate, endDate)
                    seafloorGrid = SeafloorGrid(clippedGrid, (QueryableAttribute('Depth', _('Depth'), FloatTypeMetadata()),), {'Depth': 20000.})
                    wrappedGrid = wrapperGridClass(seafloorGrid, **wrapperGridParams) if wrapperGridClass is not None else seafloorGrid
                    grids.extend(GridSliceCollection(wrappedGrid, tQACoordType=grid._CornerCoordTypes[0] if 't' in grid.Dimensions else None).QueryDatasets(reportProgress=False))

                # Determine the QueryableAttributes and rasterNameExpressions.

                qa = [QueryableAttribute('Depth', _('Depth'), FloatTypeMetadata())]
                if 't' in grid.Dimensions:
                    qa.append(QueryableAttribute('DateTime', _('Date'), DateTimeTypeMetadata()))

                if rasterNameExpressions is None:
                    if outputWorkspaceIsDir:
                        rasterNameExpressions = ['%(DatasetID)s', 
                                                 '%(VariableShortName)s' + vsnPostfix, 
                                                 'Depth_%%(Depth)0%i.%if' % (depthStrLen, depthDecimalDigits),
                                                 '%%(VariableShortName)s%s_%%(Depth)0%i.%if' % (vsnPostfix, depthStrLen, depthDecimalDigits)]
                        if 't' in grid.Dimensions:
                            rasterNameExpressions[-1] += timeSuffix
                            if '%%d' in timeSuffix:
                                rasterNameExpressions.insert(-1, '%%Y')
                    else:
                        rasterNameExpressions = ['Copernicus_%%(DatasetID)s_%%(VariableShortName)s%s_%%(Depth)0%i.%if' % (vsnPostfix, depthStrLen, depthDecimalDigits)] 
                        if 't' in grid.Dimensions:
                            rasterNameExpressions[-1] += timeSuffix

            else:
                raise ValueError(_('Unknown grid dimensions %(dim)s. This is likely a programming error in this tool. Please contact the MGET development team for assistance.') % {'dim': grid.Dimensions})

            # If the output workspace is a directory, apply the
            # rasterExtension, if it was given.

            if outputWorkspaceIsDir and rasterExtension is not None:
                if not rasterExtension.startswith('.') and not rasterNameExpressions[-1].endswith('.'):
                    rasterNameExpressions[-1] += '.' 
                rasterNameExpressions[-1] += rasterExtension

            # Return successfully.

            return grids, rasterNameExpressions, tuple(grid.GetAllQueryableAttributes() + qa)
        
        finally:
            grid.Close()

    @classmethod
    def CannyEdgesAsArcGISRasters(cls, username, password, datasetID, variableShortName, 
                                  outputWorkspace, mode='Add', log10Transform=False, 
                                  highThreshold=None, lowThreshold=None, sigma=1.4142, minSize=None,
                                  xCoordType='center', yCoordType='center', zCoordType='center', tCoordType='min',
                                  rotationOffset=None, spatialExtent=None, 
                                  minDepth=None, maxDepth=None, startDate=None, endDate=None,
                                  rasterExtension='.img', rasterNameExpressions=None, calculateStatistics=True, buildPyramids=False, buildRAT=True):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Construct a list of grids to import and import them to the output
        # workspace as rasters.

        grids, rasterNameExpressions, queryableAttributes = \
            cls._ConstructGrids(username, password, datasetID, variableShortName, 
                                outputWorkspace, log10Transform,
                                xCoordType, yCoordType, zCoordType, tCoordType,
                                rotationOffset, spatialExtent, 
                                minDepth, maxDepth, startDate, endDate,
                                rasterExtension, rasterNameExpressions,
                                wrapperGridClass=CannyEdgeGrid,
                                wrapperGridParams={'highThreshold': highThreshold, 'lowThreshold': lowThreshold, 'sigma': sigma, 'minSize': minSize},
                                vsnPostfix='_canny_fronts')

        workspace = ArcGISWorkspace(outputWorkspace, ArcGISRaster, pathCreationExpressions=rasterNameExpressions, cacheTree=True, queryableAttributes=queryableAttributes)
        workspace.ImportDatasets(grids, mode, calculateStatistics=calculateStatistics, buildPyramids=buildPyramids, buildRAT=buildRAT)

        return outputWorkspace

    @classmethod
    def CreateClimatologicalArcGISRasters(cls, username, password, datasetID, variableShortName,
                                          statistic, binType,
                                          outputWorkspace, mode='Add', log10Transform=False, 
                                          xCoordType='center', yCoordType='center', zCoordType='center', tCoordType='min',
                                          binDuration=1, startDayOfYear=1,
                                          rotationOffset=None, spatialExtent=None, 
                                          minDepth=None, maxDepth=None, startDate=None, endDate=None,
                                          rasterExtension='.img', rasterNameExpressions=None, calculateStatistics=True, buildPyramids=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # If rasterNameExpressions is not None, ignore rasterExtension.

        if rasterNameExpressions is not None:
            rasterExtension = None

        # Instantiate the CMEMSARCOArray. 

        grid = CMEMSARCOArray(username, password, datasetID, variableShortName, log10Transform=log10Transform, xCoordType=xCoordType, yCoordType=yCoordType, zCoordType=zCoordType, tCoordType=tCoordType)
        try:
            # Validate that the CMEMS grid has a t dimension.

            if 't' not in grid.Dimensions:
                raise ValueError(_('%(dn)s does not have a time dimension. In order to create a climatology, it must have a time dimension.') % {'dn': grid.DisplayName})

            # If rasterNameExpressions is None, we will determine a default
            # value. First, do some preliminary work related to this.

            if rasterNameExpressions is None:

                # If the grid contains a z dimension, determine whether any
                # digits should appear after the decimal point of the depth.
                # Also determine the maximum length of the depth string, so we
                # can zero pad it.

                if rasterNameExpressions is None and 'z' in grid.Dimensions:
                    depths = grid.MinCoords['z', :] if zCoordType == 'min' else grid.CenterCoords['z', :] if zCoordType == 'center' else grid.MaxCoords['z', :]
                    if all(depth % 1 == 0 for depth in depths):
                        depthDecimalDigits = 0
                    else:
                        for depthDecimalDigits in range(1, 15):
                            fmt = '%%0.%if' % depthDecimalDigits
                            if len(set([fmt % depth for depth in depths])) == len(depths):
                                break

                    fmt = '%%0.%if' % depthDecimalDigits
                    depthStrLen = max([len(fmt % depth) for depth in depths])

                # Determine whether the outputWorkspace is a file system
                # directory or not. If it is, then our default
                # rasterNameExpressions will store the rasters in a tree.
                # Otherwise it will construct a flat list of very long unique
                # names.

                GeoprocessorManager.InitializeGeoprocessor()
                gp = GeoprocessorManager.GetWrappedGeoprocessor()
                d = gp.Describe(outputWorkspace)
                outputWorkspaceIsDir = os.path.isdir(outputWorkspace) and (str(d.DataType).lower() != 'workspace' or str(d.DataType).lower() == 'filesystem')

            # Based on the dimensions of the grid, create a list of 2D slices
            # to import, an additional QueryableAttribute for the z dimension
            # as appropriate, and determine the default value of
            # rasterNameExpressions if it was not provided.

            if grid.Dimensions == 'tyx':
                clippedGrid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, startDate=startDate, endDate=endDate)
                collection = ClimatologicalGridCollection(clippedGrid, statistic, binType, binDuration, startDayOfYear, reportProgress=False)
                grids = collection.QueryDatasets(reportProgress=False)
                qa = []
                if rasterNameExpressions is None:
                    if outputWorkspaceIsDir:
                        rasterNameExpressions = ['%(DatasetID)s', 
                                                 '%(VariableShortName)s', 
                                                 '%(ClimatologyBinType)s_Climatology', 
                                                 '%(VariableShortName)s_%(ClimatologyBinName)s_%(Statistic)s']
                    else:
                        rasterNameExpressions = ['Copernicus_%(DatasetID)s_%(VariableShortName)s_%(ClimatologyBinType)s_Climatology_%(ClimatologyBinName)s_%(Statistic)s' + timeSuffix] 

            elif grid.Dimensions == 'tzyx':

                # If the caller requested a minimum depth that is within a
                # realistic range, instantiate a ClimatologicalGridCollection
                # from the clipped 4D (tzyx) grid, query the 3D grids (zyx)
                # from it, and get the 2D (yx) slices of it.

                grids = []
                if minDepth is None or minDepth <= 5500.:
                    clippedGrid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, minDepth, maxDepth, startDate, endDate)
                    collection = ClimatologicalGridCollection(clippedGrid, statistic, binType, binDuration, startDayOfYear, reportProgress=False)
                    for g in collection.QueryDatasets(reportProgress=False):
                        grids.extend(GridSliceCollection(g, zQACoordType=grid._CornerCoordTypes[-3]).QueryDatasets(reportProgress=False))

                # If the caller requested a maximum depth that is greater than
                # or equal to 20000, instantiate a 3D SeafloorGrid (tyx),
                # create a ClimatologicalGridCollection from it, and query the
                # 2D (yx) grids from it.

                if minDepth == 20000. or maxDepth is not None and maxDepth >= 20000.:
                    clippedGrid = cls._RotateAndClip(grid, rotationOffset, spatialExtent, None, None, startDate, endDate)
                    seafloorGrid = SeafloorGrid(clippedGrid, (QueryableAttribute('Depth', _('Depth'), FloatTypeMetadata()),), {'Depth': 20000.})
                    collection = ClimatologicalGridCollection(seafloorGrid, statistic, binType, binDuration, startDayOfYear, reportProgress=False)
                    grids.extend(collection.QueryDatasets(reportProgress=False))

                # Determine the QueryableAttributes and rasterNameExpressions.

                qa = [QueryableAttribute('Depth', _('Depth'), FloatTypeMetadata())]
                if rasterNameExpressions is None:
                    if outputWorkspaceIsDir:
                        rasterNameExpressions = ['%(DatasetID)s', 
                                                 '%(VariableShortName)s', 
                                                 'Depth_%%(Depth)0%i.%if' % (depthStrLen, depthDecimalDigits),
                                                 '%(ClimatologyBinType)s_Climatology', 
                                                 '%(VariableShortName)s_%(ClimatologyBinName)s_%(Statistic)s']
                    else:
                        rasterNameExpressions = ['Copernicus_%(DatasetID)s_%(VariableShortName)s_%%(Depth)0%i.%if_%(ClimatologyBinType)s_Climatology_%(ClimatologyBinName)s_%(Statistic)s' + timeSuffix] 

            else:
                raise ValueError(_('Unknown grid dimensions %(dim)s. This is likely a programming error in this tool. Please contact the MGET development team for assistance.') % {'dim': grid.Dimensions})

            # If the output workspace is a directory, apply the
            # rasterExtension, if it was given.

            if outputWorkspaceIsDir and rasterExtension is not None:
                if not rasterExtension.startswith('.') and not rasterNameExpressions[-1].endswith('.'):
                    rasterNameExpressions[-1] += '.' 
                rasterNameExpressions[-1] += rasterExtension

            # Create the rasters.

            workspace = ArcGISWorkspace(outputWorkspace, ArcGISRaster, pathCreationExpressions=rasterNameExpressions, cacheTree=True, queryableAttributes=tuple(collection.GetAllQueryableAttributes() + qa))
            workspace.ImportDatasets(grids, mode, calculateStatistics=calculateStatistics, buildPyramids=buildPyramids)
        
        finally:
            grid.Close()

        return outputWorkspace

    @classmethod
    def InterpolateAtArcGISPoints(cls, username, password, datasetID, variableShortName,
                                  points, valueField, zField=None, tField=None, method='Nearest', log10Transform=False, 
                                  where=None, noDataValue=None,
                                  xCoordType='center', yCoordType='center', zCoordType='center', tCoordType='min',
                                  orderByFields=None, numBlocksToCacheInMemory=256, xBlockSize=64, yBlockSize=64, zBlockSize=1, tBlockSize=1):
        cls.__doc__.Obj.ValidateMethodInvocation()
        grid = cls(username, password, datasetID, variableShortName, log10Transform=log10Transform, 
                   xCoordType=xCoordType, yCoordType=yCoordType, zCoordType=zCoordType, tCoordType=tCoordType)
        try:
            if 't' in grid.Dimensions and tField is None:
                raise ValueError('A value for the Date Field (tField) parameter must be given when the CMEMS dataset is a time series.')

            Interpolator.InterpolateGridsValuesForTableOfPoints(grids=[grid], 
                                                                table=ArcGISTable(points), 
                                                                fields=[valueField], 
                                                                zField=zField,
                                                                tField=tField, 
                                                                where=where, 
                                                                orderBy=', '.join([f + ' ASC' for f in orderByFields]) if orderByFields is not None else tField + ' ASC', 
                                                                method=method, 
                                                                noDataValue=noDataValue, 
                                                                gridsWrap=bool(grid.MaxCoords['x',-1] - grid.MinCoords['x',0] == 360), 
                                                                numBlocksToCacheInMemory=numBlocksToCacheInMemory, 
                                                                xBlockSize=xBlockSize, 
                                                                yBlockSize=yBlockSize, 
                                                                zBlockSize=zBlockSize, 
                                                                tBlockSize=tBlockSize)
        finally:
            grid.Close()
        return points


###############################################################################
# Metadata: module
###############################################################################

from ..ArcGIS import ArcGISDependency
from ..Datasets.ArcGIS import _CalculateStatisticsDescription, _BuildPyramidsDescription, _BuildRATDescription
from ..Dependencies import PythonModuleDependency
from ..Metadata import *

AddModuleMetadata(
    shortDescription=_('Classes for accessing oceanographic datasets published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`__.'),
    longDescription=_('Copernicus Marine Service is also known as Copernicus Marine Environmental Monitoring Service (CMEMS).'))

###############################################################################
# Metadata: CMEMSARCOArray class
###############################################################################

AddClassMetadata(CMEMSARCOArray,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` for accessing 2D, 3D, and 4D gridded datasets published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`__.'),
    longDescription=_(
"""Copernicus Marine Service is also known as Copernicus Marine Environmental
Monitoring Service (CMEMS). :ref:`This example
<python-downloading-cmems-rasters>` shows how to use this class to create time
series of chlorophyll concentration rasters from `Copernicus GlobColour
<https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L4_MY_009_104>`__
and ocean temperature rasters from the `Global Ocean Physics Reanalysis
<https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030>`__.
There is :ref:`another example <arcgis-downloading-cmems-rasters>` showing how
to do this in ArcGIS with the **Create Rasters for CMEMS Dataset**
geoprocessing tool."""))

# Public properties

AddPropertyMetadata(CMEMSARCOArray.Username,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Copernicus Marine Service user name.'))

AddPropertyMetadata(CMEMSARCOArray.Password,
    typeMetadata=UnicodeStringHiddenTypeMetadata(minLength=1),
    shortDescription=_('Copernicus Marine Service password.'))

AddPropertyMetadata(CMEMSARCOArray.DatasetID,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_(
"""Dataset ID to access. You can find the Dataset ID by going to the
`Copernicus Marine Data Store <https://data.marine.copernicus.eu/products>`__,
viewing your product of interest, clicking on Data Access, and scrolling to
the Dataset ID table. The dataset must have 2, 3, or 4 dimensions. Two of the
dimensions must be longitude and latitude. The third and fourth dimension can
be depth or time."""))

AddPropertyMetadata(CMEMSARCOArray.VariableShortName,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_(
""""Short name" of the variable to access. You can find the variable's short
name by going to to the `Copernicus Marine Data Store
<https://data.marine.copernicus.eu/products>`__, viewing your product of
interest, clicking on Data Access, scrolling to the Dataset ID table, and
clicking on Form under the Subset column. When the form appears, look under
the Variables heading. Each variable has a long description in black font,
followed by the variable short name and units (in brackets) in a lighter
color. Do not include the units as part of the short name."""))

AddPropertyMetadata(CMEMSARCOArray.Log10Transform,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_(
""""If True, a ``log10`` (base 10 logarithm) function will be applied to the
data after it is downloaded before further processing. This transformation may
be useful when working with data that are always positive but heavily skewed,
such as chlorophyll concentration or other biological oceanographic data. For
example, it is a common practice to ``log10`` transform chlorophyll data
before detecting chlorophyll fronts or utilizing chlorophyll in a species
distribution model.

Note that it is only possible to take the logarithm of a positive number. If
the data contain values less than or equal to zero, a warning will be issued
and they will be treated as missing values."""))

# Public constructor: CMEMSARCOArray.__init__

AddMethodMetadata(CMEMSARCOArray.__init__,
    shortDescription=_('CMEMSARCOArray constructor.'),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('copernicusmarine', cheeseShopName='copernicusmarine')])

AddArgumentMetadata(CMEMSARCOArray.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=CMEMSARCOArray),
    description=_(':class:`%s` instance.') % CMEMSARCOArray.__name__)

AddArgumentMetadata(CMEMSARCOArray.__init__, 'username',
    typeMetadata=CMEMSARCOArray.Username.__doc__.Obj.Type,
    description=CMEMSARCOArray.Username.__doc__.Obj.ShortDescription,
    arcGISDisplayName=_('Copernicus user name'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'password',
    typeMetadata=CMEMSARCOArray.Password.__doc__.Obj.Type,
    description=CMEMSARCOArray.Password.__doc__.Obj.ShortDescription,
    arcGISDisplayName=_('Copernicus password'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'datasetID',
    typeMetadata=CMEMSARCOArray.DatasetID.__doc__.Obj.Type,
    description=CMEMSARCOArray.DatasetID.__doc__.Obj.ShortDescription,
    arcGISDisplayName=_('Copernicus dataset ID'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'variableShortName',
    typeMetadata=CMEMSARCOArray.VariableShortName.__doc__.Obj.Type,
    description=CMEMSARCOArray.VariableShortName.__doc__.Obj.ShortDescription,
    arcGISDisplayName=_('Variable short name'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'log10Transform',
    typeMetadata=CMEMSARCOArray.Log10Transform.__doc__.Obj.Type,
    description=CMEMSARCOArray.Log10Transform.__doc__.Obj.ShortDescription,
    arcGISDisplayName=_('Apply log10 transform'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'xCoordType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_(
"""Specifies whether the latitude coordinates used by Copernicus for this
dataset are the left edges (``'min'``), the centers (``'center'``), or the
right edges (``'max'``) of the cells. This cannot be determined automatically
but for most Copernicus datasets the longitude coordinates are the centers of
the cells. To determine the appropriate value for your dataset of interest,
consult the dataset's documentation or contact Copernicus for help.
Alternatively, download the dataset to a raster using ``'center'``, load it
into a GIS, and overlay a high resolution shoreline. Examine the overlap to
determine whether ``'min'`` or ``'max'`` would provide a better match up
between the raster and the shoreline."""),
    arcGISDisplayName=_('Longitude coordinate type'),
    arcGISCategory=_('Dataset geolocation options'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'yCoordType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_(
"""Specifies whether the latitude coordinates used by Copernicus for this
dataset are the bottom edges (``'min'``), the centers (``'center'``), or the
top edges (``'max'``) of the cells. This cannot be determined automatically
but for most Copernicus datasets the latitude coordinates are the centers of
the cells. To determine the appropriate value for your dataset of interest,
consult the dataset's documentation or contact Copernicus for help.
Alternatively, download the dataset to a raster using ``'center'``, load it
into a GIS, and overlay a high resolution shoreline. Examine the overlap to
determine whether ``'min'`` or ``'max'`` would provide a better match up
between the raster and the shoreline."""),
    arcGISDisplayName=_('Latitude coordinate type'),
    arcGISCategory=_('Dataset geolocation options'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'zCoordType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_(
"""Specifies whether the depth coordinates used by Copernicus for this dataset
are the shallow edges (``'min'``), the centers (``'center'``), or the deep
edges (``'max'``) of the cells. This cannot be determined automatically but
for most Copernicus datasets the depth coordinates are the centers of the
cells. To determine the appropriate value for your dataset of interest,
consult the dataset's documentation or contact Copernicus for help."""),
    arcGISDisplayName=_('Depth coordinate type'),
    arcGISCategory=_('Dataset geolocation options'))

AddArgumentMetadata(CMEMSARCOArray.__init__, 'tCoordType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['min', 'center', 'max'], makeLowercase=True),
    description=_(
"""Specifies whether the time coordinates used by Copernicus for this dataset
are the starting times (``'min'``), the center times (``'center'``), or the
ending times (``'max'``) of the time slices. This cannot be determined
automatically but most Copernicus datasets that are "instantaneous" use center
times, while most datasets that represent mean values (e.g. daily or monthly
means) use starting times. To determine the appropriate value for your dataset
of interest, consult the dataset's documentation or contact Copernicus for
help."""),
    arcGISDisplayName=_('Time coordinate type'),
    arcGISCategory=_('Dataset geolocation options'))

CopyArgumentMetadata(Grid.__init__, 'lazyPropertyValues', CMEMSARCOArray.__init__, 'lazyPropertyValues')

AddResultMetadata(CMEMSARCOArray.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=CMEMSARCOArray),
    description=_(':class:`%s` instance.') % CMEMSARCOArray.__name__)

# Public method: CMEMSARCOArray.CreateArcGISRasters

AddMethodMetadata(CMEMSARCOArray.CreateArcGISRasters,
    shortDescription=_('Creates rasters for a 2D, 3D, or 4D gridded dataset published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`__.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Rasters for CMEMS Dataset'),
    arcGISToolCategory=_('Data Products\\Copernicus Marine Service (CMEMS)'),
    dependencies=[ArcGISDependency()] + CMEMSARCOArray.__init__.__doc__.Obj.Dependencies)

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=CMEMSARCOArray),
    description=_(':class:`%s` or an instance of it.') % CMEMSARCOArray.__name__)

CopyArgumentMetadata(CMEMSARCOArray.__init__, 'username', CMEMSARCOArray.CreateArcGISRasters, 'username')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'password', CMEMSARCOArray.CreateArcGISRasters, 'password')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'datasetID', CMEMSARCOArray.CreateArcGISRasters, 'datasetID')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'variableShortName', CMEMSARCOArray.CreateArcGISRasters, 'variableShortName')

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'outputWorkspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    description=_(
"""Directory or geodatabase to receive the rasters. Unless you have a specific
reason to store the rasters in a geodatabase, we recommend you store them in a
directory because it will be faster and allow the rasters to be organized in a
tree. The tree structure and raster names will be generated automatically
unless you provide a value for the Raster Name Expressions parameter."""),
    arcGISDisplayName=_('Output workspace'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'mode',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Add', 'Replace'], makeLowercase=True),
    description=_(
"""Overwrite mode, one of:

* ``Add`` - create rasters that do not exist and skip those that already
  exist. This is the default.

* ``Replace`` - create rasters that do not exist and overwrite those that
  already exist.

The ArcGIS Overwrite Output environment setting has no effect on this tool. If
'Replace' is selected the rasters will be overwritten, regardless of the
ArcGIS Overwrite Output setting."""),
    arcGISDisplayName=_('Overwrite mode'))

CopyArgumentMetadata(CMEMSARCOArray.__init__, 'log10Transform', CMEMSARCOArray.CreateArcGISRasters, 'log10Transform')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'xCoordType', CMEMSARCOArray.CreateArcGISRasters, 'xCoordType')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'yCoordType', CMEMSARCOArray.CreateArcGISRasters, 'yCoordType')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'zCoordType', CMEMSARCOArray.CreateArcGISRasters, 'zCoordType')
CopyArgumentMetadata(CMEMSARCOArray.__init__, 'tCoordType', CMEMSARCOArray.CreateArcGISRasters, 'tCoordType')

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rotationOffset',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Degrees to rotate the outputs about the polar axis. This parameter may only
be used for global products. The outputs can only be rotated in whole cells.
The value you provide will be rounded off to the closest cell. The value may
be positive or negative."""),
    arcGISDisplayName=_('Rotate by'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'spatialExtent',
    typeMetadata=EnvelopeTypeMetadata(canBeNone=True),
    description=_(
"""Spatial extent of the outputs, in degrees. This parameter is applied after
the rotation parameter and uses coordinates that result after rotation. The
outputs can only be clipped in whole grid cells. The values you provide will
be rounded off to the closest cell."""),
    arcGISDisplayName=_('Spatial extent'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'minDepth',
    typeMetadata=FloatTypeMetadata(minValue=0.0, maxValue=20000.0, canBeNone=True),
    description=_(
"""Minimum depth, in meters, for the outputs to create. This parameter is
ignored if the dataset does not have a depth coordinate. Its value must be
between 0 and 20000, inclusive. Outputs will be created for layers with depths
that are greater than or equal to the minimum depth and less than or equal to
the maximum depth. If you do not specify a minimum depth, the minimum depth of
the dataset will be used.

The value 20000 is a special code representing conditions at the seafloor. Use
this value if you need an estimate of "bottom temperature" or the value of
another variable at the seafloor. If this value is requested, an output will
be created with a fake depth of 20000 meters. The cells of this output will be
assigned by stacking all of the depth layers and selecting the deepest cells
that have data.

Note that some Copernicus datasets offer a variable representing values at the
seafloor that Copernicus computed ahead of time. This tool is not aware of
those variables and cannot access them automatically. But you can manually
access such a variable just like any other by providing its name for the
Variable Short Name parameter. Accessing those precomputed variables will be
faster than using a depth of 20000 to compute them yourself. Variables of that
kind will be treated by this tool as not having a depth coordinate."""),
    arcGISDisplayName=_('Minimum depth'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'maxDepth',
    typeMetadata=FloatTypeMetadata(minValue=0.0, maxValue=20000.0, canBeNone=True),
    description=_(
"""Maximum depth, in meters, for the outputs to create. This parameter is
ignored if the dataset does not have a depth coordinate. Its value must be
between 0 and 20000, inclusive. Outputs will be created for images with depths
that are greater than or equal to the minimum depth and less than or equal to
the maximum depth. If you do not specify a maximum depth, the maximum depth of
the dataset will be used.

The value 20000 is a special code representing conditions at the seafloor.
Please see the documenation for the Minimum Depth parameter for discussions of
this value."""),
    arcGISDisplayName=_('Maximum depth'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'startDate',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Start date for the outputs to create. This parameter is ignored if the
dataset does not have a time coordinate. Outputs will be created for images
that occur on or after the start date and on or before the end date. If you do
not provide a start date, the date of the first available time slice will be
used."""),
    arcGISDisplayName=_('Start date'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'endDate',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""End date for the outputs to create. This parameter is ignored if the
dataset does not have a time coordinate. Outputs will be created for images
that occur on or after the start date and on or before the end date. If you do
not specify an end date, the date of the most recent time slice will be
used."""),
    arcGISDisplayName=_('End date'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rasterExtension',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""File extension to use for output rasters. This parameter is ignored if the
rasters are stored in a geodatabase rather than the file system, or if the
Raster Name Expressions parameter is provided (in which case it determines the
file extension). The default is '.img', for ERDAS IMAGINE format. Another
popular choice is '.tif', the GeoTIFF format. Please see the ArcGIS
documentation for the extensions of the supported formats."""),
    arcGISDisplayName=_('Raster file extension'),
    arcGISCategory=_('Output raster options'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rasterNameExpressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    description=_(
"""List of expressions specifying how the output rasters should be named. If
you do not provide anything, a default naming scheme will be used.

If the output workspace is a file system directory, you may provide one or
more expressions. Each expression defines a level in a directory tree. The
final expression specifies the raster file name. If the output workspace is a
geodatabase, you should provide only one expression, which specifies the
raster name.

Each expression may contain any sequence of characters permitted by the output
workspace. Each expression may optionally contain one or more of the following
case-sensitive codes. The tool replaces the codes with appropriate values when
creating each raster:

* ``%(DatasetID)s`` - Copernicus dataset ID.

* ``%(ShortVariableName)s`` - Copernicus short variable name.

* ``%(Depth)s`` - depth of the raster. Only avilable for datasets that have depth
  coordinates.

* ``%%Y`` - four-digit year of the raster. This and the following codes are
  only available for datasets that have time coordinates.

* ``%%m`` - two-digit month of the raster.

* ``%%d`` - two-digit day of the month of the raster.

* ``%%j`` - three-digit day of the year of the raster.

* ``%%H`` - two-digit hour of the raster.

* ``%%M`` - two-digit minute of the raster.

* ``%%S`` - two-digit second of the raster.

"""),
    arcGISDisplayName=_('Raster name expressions'),
    arcGISCategory=_('Output raster options'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'calculateStatistics',
    typeMetadata=BooleanTypeMetadata(),
    description=_CalculateStatisticsDescription,
    arcGISDisplayName=_('Calculate statistics'),
    arcGISCategory=_('Output raster options'))

AddArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'buildPyramids',
    typeMetadata=BooleanTypeMetadata(),
    description=_BuildPyramidsDescription,
    arcGISDisplayName=_('Build pyramids'),
    arcGISCategory=_('Output raster options'))

AddResultMetadata(CMEMSARCOArray.CreateArcGISRasters, 'updatedOutputWorkspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(),
    description=_('Updated output workspace.'),
    arcGISDisplayName=_('Updated output workspace'),
    arcGISParameterDependencies=['outputWorkspace'])

# Public method: CMEMSARCOArray.CannyEdgesAsArcGISRasters

AddMethodMetadata(CMEMSARCOArray.CannyEdgesAsArcGISRasters,
    shortDescription=_('Creates rasters indicating the positions of fronts identified with the Canny edge detection algorithm in a 2D, 3D, or 4D gridded dataset published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`__.'),
    longDescription=_CannyEdgesOverview,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Find Canny Fronts in CMEMS Dataset'),
    arcGISToolCategory=_('Data Products\\Copernicus Marine Service (CMEMS)'),
    dependencies=[ArcGISDependency(), MatlabDependency()] + CMEMSARCOArray.__init__.__doc__.Obj.Dependencies)

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'cls', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'cls')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'username', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'username')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'password', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'password')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'datasetID', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'datasetID')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'variableShortName', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'variableShortName')

AddArgumentMetadata(CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'outputWorkspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    description=CMEMSARCOArray.CreateArcGISRasters.__doc__.Obj.GetArgumentByName('outputWorkspace').Description + _("""

The rasters will have an integer data type, with the value 1 where a front was
detected, 0 where a front was not detected, and NoData where there was land,
or data were missing for some other reason."""),
    arcGISDisplayName=_('Output workspace'))

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'mode', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'mode')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'log10Transform', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'log10Transform')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'highThreshold', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'highThreshold')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'lowThreshold', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'lowThreshold')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'sigma', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'sigma')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'minSize', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'minSize')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'xCoordType', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'xCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'yCoordType', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'yCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'zCoordType', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'zCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'tCoordType', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'tCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rotationOffset', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'rotationOffset')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'spatialExtent', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'spatialExtent')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'minDepth', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'minDepth')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'maxDepth', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'maxDepth')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'startDate', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'startDate')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'endDate', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'endDate')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rasterExtension', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'rasterExtension')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rasterNameExpressions', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'rasterNameExpressions')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'calculateStatistics', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'calculateStatistics')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'buildPyramids', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'buildPyramids')

AddArgumentMetadata(CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'buildRAT',
    typeMetadata=BooleanTypeMetadata(),
    description=_BuildRATDescription,
    arcGISDisplayName=_('Build raster attribute tables'),
    arcGISCategory=_('Output raster options'))

CopyResultMetadata(CMEMSARCOArray.CreateArcGISRasters, 'updatedOutputWorkspace', CMEMSARCOArray.CannyEdgesAsArcGISRasters, 'updatedOutputWorkspace')

# Public method: CMEMSARCOArray.CreateClimatologicalArcGISRasters

AddMethodMetadata(CMEMSARCOArray.CreateClimatologicalArcGISRasters,
    shortDescription=_('Creates climatological rasters for a 3D, or 4D gridded time series dataset published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`__.'),
    longDescription=_(
"""This tool produces rasters showing the climatological mean value (or
other statistic) of a time series of images. Given a desired dataset, a
statistic, and a climatological bin definition, this tool efficiently
downloads the images, classifies them into bins, and produces a single raster
for each bin. Each cell of the raster is produced by calculating the statistic
on the values of that cell extracted from all of the images in the bin."""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Climatological Rasters for CMEMS Dataset'),
    arcGISToolCategory=_('Data Products\\Copernicus Marine Service (CMEMS)'),
    dependencies=[ArcGISDependency()] + CMEMSARCOArray.__init__.__doc__.Obj.Dependencies)

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'cls', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'cls')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'username', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'username')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'password', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'password')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'datasetID', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'datasetID')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'variableShortName', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'variableShortName')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'statistic', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'statistic')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'binType', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'binType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'outputWorkspace', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'outputWorkspace')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'mode', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'mode')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'log10Transform', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'log10Transform')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'xCoordType', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'xCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'yCoordType', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'yCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'zCoordType', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'zCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'tCoordType', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'tCoordType')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'binDuration', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'binDuration')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'startDayOfYear', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'startDayOfYear')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rotationOffset', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'rotationOffset')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'spatialExtent', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'spatialExtent')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'minDepth', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'minDepth')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'maxDepth', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'maxDepth')

AddArgumentMetadata(CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'startDate',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Start date of the range of time slices to include in the climatology. If
you do not provide a start date, the climatology will start from the first
time slice in the dataset."""),
    arcGISDisplayName=_('Start date'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'endDate',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""End date of the range of time slices to include in the climatology. If you
do not provide an end date, the climatology will extend to the last time slice
in the dataset."""),
    arcGISDisplayName=_('End date'),
    arcGISCategory=_('Spatiotemporal extent'))

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'rasterExtension', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'rasterExtension')

AddArgumentMetadata(CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'rasterNameExpressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    description=_(
"""List of expressions specifying how the output rasters should be named. If
you do not provide anything, a default naming scheme will be used.

If the output workspace is a file system directory, you may provide one or
more expressions. Each expression defines a level in a directory tree. The
final expression specifies the raster file name. If the output workspace is a
geodatabase, you should provide only one expression, which specifies the
raster name.

Each expression may contain any sequence of characters permitted by the output
workspace. Each expression may optionally contain one or more of the following
case-sensitive codes. The tool replaces the codes with appropriate values when
creating each raster:

* ``%(DatasetID)s`` - Copernicus dataset ID.

* ``%(ShortVariableName)s`` - Copernicus short variable name.

* ``%(Depth)s`` - depth of the raster. Only avilable for datasets that have
  depth coordinates.

* ``%(ClimatologyBinType)s`` - type of the climatology bin, either ``Daily``
  if 1-day bins, ``Xday`` if multi-day bins (``X`` is replaced by the
  duration), ``Monthly`` if 1-month bins, ``Xmonth`` if multi-month bins, or
  ``Cumulative``. If an ENSO bin type is used, ``ENSO_`` will be prepended to
  those strings (e.g. ``ENSO_Daily``, ``ENSO_Monthly``).

* ``%(ClimatologyBinName)s`` - name of the climatology bin corresponding
  represented by the output raster, either ``dayXXX`` for 1-day bins (``XXX``
  is replaced by the day of the year), ``daysXXXtoYYY`` for multi-day bins
  (``XXX`` is replaced by the first day of the bin, ``YYY`` is replaced by the
  last day), ``monthXX`` for 1-month bins (``XX`` is replaced by the month),
  ``monthXXtoYY`` (``XX`` is replaced by the first month of the bin, ``YY`` by
  the last month), or ``cumulative``. If an ENSO bin type is used,
  ``neutral_``, ``ElNino_``, and ``LaNina_`` will be prepended to those
  strings for each of the three ENSO phased rasters (e.g.
  ``neutral_cumulative``, ``ElNino_cumulative``, and ``LaNina_cumulative``
  when ``ENSO Cumulative`` bins are requested).

* ``%(Statistic)s`` - statistic that was calculated, in lowercase and with
  spaces replaced by underscores; one of: ``count``, ``maximum``, ``mean``,
  ``minimum``, ``range``, ``standard_deviation``, ``sum``.

If the Bin Type is ``Daily``, the following additional codes are available:

* ``%(FirstDay)i`` - first day of the year of the climatology bin represented
  by the output raster.

* ``%(LastDay)i`` - last day of the year of the climatology bin represented by
  the output raster. For 1-day climatologies, this will be the same as
  ``%(FirstDay)i``.

If the Bin Type is ``Monthly``, the following additional codes are available:

* ``%(FirstMonth)i`` - first month of the climatology bin represented by the
  output raster.

* ``%(DayOfFirstMonth)i`` - first day of the first month of the climatology
  bin represented by the output raster.

* ``%(LastMonth)i`` - last month of the climatology bin represented by the
  output raster.

* ``%(DayOfLastMonth)i`` - last day of the last month of the climatology bin
  represented by the output raster.

Note that the additional codes are integers and may be formatted using
"printf"-style formatting codes. For example, to format the ``FirstDay`` as a
three-digit number with leading zeros::

    %(FirstDay)03i

"""),
    arcGISDisplayName=_('Raster name expressions'),
    arcGISCategory=_('Output raster options'))

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'calculateStatistics', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'calculateStatistics')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'buildPyramids', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'buildPyramids')

CopyResultMetadata(CMEMSARCOArray.CreateArcGISRasters, 'updatedOutputWorkspace', CMEMSARCOArray.CreateClimatologicalArcGISRasters, 'updatedOutputWorkspace')

# Public method: CMEMSARCOArray.InterpolateAtArcGISPoints

AddMethodMetadata(CMEMSARCOArray.InterpolateAtArcGISPoints,
    shortDescription=_('Interpolates values of a 2D, 3D, or 4D gridded dataset published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`__ at points.'),
    longDescription=_(
"""Given a desired CMEMS dataset, this tool interpolates the value of that
dataset at the given points. This tool performs the same basic operation as
the ArcGIS Spatial Analyst's :arcpy_sa:`Extract-Values-to-Points` tool, but it
reads the data from the CMEMS servers rather than reading rasters stored on your
machine."""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Interpolate CMEMS Dataset at Points'),
    arcGISToolCategory=_('Data Products\\Copernicus Marine Service (CMEMS)'),
    dependencies=[ArcGISDependency()] + CMEMSARCOArray.__init__.__doc__.Obj.Dependencies)

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'cls', CMEMSARCOArray.InterpolateAtArcGISPoints, 'cls')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'username', CMEMSARCOArray.InterpolateAtArcGISPoints, 'username')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'password', CMEMSARCOArray.InterpolateAtArcGISPoints, 'password')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'datasetID', CMEMSARCOArray.InterpolateAtArcGISPoints, 'datasetID')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'variableShortName', CMEMSARCOArray.InterpolateAtArcGISPoints, 'variableShortName')

AddArgumentMetadata(CMEMSARCOArray.InterpolateAtArcGISPoints, 'points',
    typeMetadata=ArcGISFeatureLayerTypeMetadata(mustExist=True, allowedShapeTypes=['Point']),
    description=_(
"""Feature class or layer containing the points at which values should be
interpolated. The points must have a field that contains the date of each
point and a field to receive the value interpolated from the raster.

CMEMS datasets use the WGS 1984 geographic coordinate system. It is
recommended but not required that the points use the same coordinate system.
If they do not, this tool will attempt to project the points to the WGS 1984
coordinate system prior to doing the interpolation. This may fail if a datum
transformation is required, in which case you will have to manually project
the points to the WGS 1984 coordinate system before using this tool."""),
    arcGISDisplayName=_('Point features'))

CopyArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'valueField', CMEMSARCOArray.InterpolateAtArcGISPoints, 'valueField')

AddArgumentMetadata(CMEMSARCOArray.InterpolateAtArcGISPoints, 'zField',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64'], canBeNone=True),
    description=_(
"""Field of the points that specifies the depth of the point. The field is
required if the CMEMS dataset includes depth layers; it should be omitted
otherwise."""),
    arcGISDisplayName=_('Depth field'),
    arcGISParameterDependencies=['points'])

AddArgumentMetadata(CMEMSARCOArray.InterpolateAtArcGISPoints, 'tField',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True, allowedFieldTypes=['date', 'datetime'], canBeNone=True),
    description=_(
"""Field of the points that specifies the date and time of the point. The
field is required if the CMEMS dataset is a time series; it should be omitted
otherwise. The field must have a datetime data type. If the field can only
represent dates with no time component, the time will assumed to be 00:00:00."""),
    arcGISDisplayName=_('Date field'),
    arcGISParameterDependencies=['points'])

AddArgumentMetadata(CMEMSARCOArray.InterpolateAtArcGISPoints, 'method',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Nearest', 'Linear'], makeLowercase=True),
    description=_(
"""Interpolation method to use, one of:

* ``Nearest`` - nearest neighbor interpolation. The interpolated value
  will simply be the value of the cell that contains the point. This
  is the default.

* ``Linear`` - linear interpolation. This method is suitable for continuous
  data such as sea surface temperature, but not for categorical data such as
  pixel quality flags (use nearest neighbor instead). This method averages
  the values of the eight nearest cells in the x, y, depth, and time
  dimensions (if applicable), weighting the contribution of each cell by the
  area of it that would be covered by a hypothetical cell centered on the
  point being interpolated. If the cell containing the point contains NoData,
  the result is NoData. Otherwise, and the result is based on the weighted
  average of the four (if the dataset is 2D), eight (if 3D), or 16 (if 4D)
  nearest cells that do contain data, including the one that contains the
  cell. If any of the other cells contain NoData, they are omitted from the
  average. This a multi-dimensional version of the bilinear interpolation
  implemented by the ArcGIS Spatial Analyst's
  :arcpy_sa:`Extract-Values-to-Points` tool.

"""),
    arcGISDisplayName=_('Interpolation method'))

AddArgumentMetadata(CMEMSARCOArray.InterpolateAtArcGISPoints, 'log10Transform',
    typeMetadata=CMEMSARCOArray.Log10Transform.__doc__.Obj.Type,
    description=CMEMSARCOArray.Log10Transform.__doc__.Obj.ShortDescription,
    arcGISDisplayName=_('Apply log10 transform'))

CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'where', CMEMSARCOArray.InterpolateAtArcGISPoints, 'where')
CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'noDataValue', CMEMSARCOArray.InterpolateAtArcGISPoints, 'noDataValue')

CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'xCoordType', CMEMSARCOArray.InterpolateAtArcGISPoints, 'xCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'yCoordType', CMEMSARCOArray.InterpolateAtArcGISPoints, 'yCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'zCoordType', CMEMSARCOArray.InterpolateAtArcGISPoints, 'zCoordType')
CopyArgumentMetadata(CMEMSARCOArray.CreateArcGISRasters, 'tCoordType', CMEMSARCOArray.InterpolateAtArcGISPoints, 'tCoordType')
CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'orderByFields', CMEMSARCOArray.InterpolateAtArcGISPoints, 'orderByFields')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'numBlocksToCacheInMemory', CMEMSARCOArray.InterpolateAtArcGISPoints, 'numBlocksToCacheInMemory')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'xBlockSize', CMEMSARCOArray.InterpolateAtArcGISPoints, 'xBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'yBlockSize', CMEMSARCOArray.InterpolateAtArcGISPoints, 'yBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'zBlockSize', CMEMSARCOArray.InterpolateAtArcGISPoints, 'zBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'tBlockSize', CMEMSARCOArray.InterpolateAtArcGISPoints, 'tBlockSize')

AddResultMetadata(CMEMSARCOArray.InterpolateAtArcGISPoints, 'updatedPoints',
    typeMetadata=ArcGISFeatureLayerTypeMetadata(),
    description=_('Updated points.'),
    arcGISDisplayName=_('Updated points'),
    arcGISParameterDependencies=['points'])


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['CMEMSARCOArray']
