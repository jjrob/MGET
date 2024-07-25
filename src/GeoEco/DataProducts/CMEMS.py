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
import math
import types

from ..Datasets import QueryableAttribute, Grid
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _


class CMEMSARCOArray(Grid):
    __doc__ = DynamicDocString()

    def _GetDatasetID(self):
        return self._DatasetID

    DatasetID = property(_GetDatasetID, doc=DynamicDocString())

    def _GetVariableShortName(self):
        return self._VariableShortName

    VariableShortName = property(_GetVariableShortName, doc=DynamicDocString())

    def __init__(self, username, password, datasetID, variableShortName, xCoordType='center', yCoordType='center', zCoordType='center', tCoordType='min', lazyPropertyValues=None):
        #self.__doc__.Obj.ValidateMethodInvocation()   TODO

        # Initialize our properties.

        self._Username = username
        self._Password = password
        self._DatasetID = datasetID
        self._VariableShortName = variableShortName
        self._DisplayName = _('variable %(name)s of Copernicus Marine Service dataset %(datasetID)s') % {'name': variableShortName, 'datasetID': datasetID}
        self._URI = None
        self._ZCoords = None
        self._VariableStandardName = None
        self._Dataset = None

        # Do not use the caller's CoordType arguments to set the CornerCoords
        # lazy property yet. We don't know the dimensions of the grid until we
        # query the catalog, so we hold off on setting CornerCoords.

        self._CornerCoordTypes = (tCoordType, zCoordType, yCoordType, xCoordType)

        # Initialize the base class.

        super(CMEMSARCOArray, self).__init__()

    def _Close(self):
        pass   # TODO

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

            self._LogDebug('%(class)s 0x%(id)016X: Calling copernicusmarine.describe(contains=["%(datasetID)s"], include_datasets=True, disable_progress_bar=True)' % {'class': self.__class__.__name__, 'id': id(self), 'datasetID': self._DatasetID})
            try:
                cat = copernicusmarine.describe(contains=[self._DatasetID], include_datasets=True, disable_progress_bar=True)
            except Exception as e:
                raise RuntimeError(_('Failed to query the Copernicus Marine Service catalogue for dataset ID "%(datasetID)s". The copernicusmarine.describe() function failed with %(e)s: %(msg)s.') % {'datasetID': self._DatasetID, 'e': e.__class__.__name__, 'msg': e})

            if not isinstance(cat, (dict, types.NoneType)):
                raise RuntimeError(_('Failed to query the Copernicus Marine Service catalogue with the copernicusmarine.describe() function. The function returned a %(type)s instance rather than a dictionary. This is unexpected; please contact the MGET development team for assistance.') % {'type': type(cat)})

            if cat is None or len(cat) <= 0:
                raise RuntimeError(_('The Copernicus Marine Service catalogue does not contain a dataset with the ID "%(datasetID)s". Please check the ID and try again. Dataset IDs are case sensitive and must be given exactly as written on the Copernicus Marine Service website.') % {'datasetID': self._DatasetID})

            # Extract the 'arco-geo-series' service record for the dataset.

            self._LogDebug('%(class)s 0x%(id)016X: Searching the returned catalogue for dataset.' % {'class': self.__class__.__name__, 'id': id(self)})

            service = None
            variable = None

            if 'products' not in cat or not isinstance(cat['products'], list):
                raise RuntimeError(_('The root level of the Copernicus Marine Service catalogue returned by copernicusmarine.describe() does not have a "products" key, or the "products" key does map to a list. This may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.'))

            for product in cat['products']:
                if not isinstance(product, dict):
                    self._LogWarning(_('The "products" list at the root level of the Copernicus Marine Service catalogue contains something other than a dictionary. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.'))
                    continue

                if 'datasets' not in product:
                    self._LogWarning(_('The "products" list at the root level of the Copernicus Marine Service catalogue contains a dictionary that does not have a "datasets" key. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.'))
                    continue

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

                        if any([key not in s for key in ['service_format', 'service_type', 'uri', 'variables']]) or \
                           not isinstance(s['service_format'], (str, types.NoneType)) or \
                           not isinstance(s['service_type'], dict) or 'service_name' not in s['service_type'] or \
                           not isinstance(s['uri'], str) or len(s['uri']) <= 0 or \
                           not isinstance(s['variables'], list) or len(s['variables']) <= 0 or \
                           any([not isinstance(v, dict) or \
                                not 'short_name' in v or not isinstance(v['short_name'], str) or len(v['short_name']) <= 0 or \
                                not 'standard_name' in v or not isinstance(v['standard_name'], str) or len(v['standard_name']) <= 0 or \
                                not 'coordinates' in v or not isinstance(v['coordinates'], list) \
                                for v in s['variables']]):
                            self._LogWarning(_('In the Copernicus Marine Service catalogue, the dataset dictionary for the "%(datasetID)s" contains a services list that contains a dictionary that does not contain all the required keys or has some unexpected values. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. If your attempt to access this dataset is unsuccessful, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID})
                            continue

                        for v in s['variables']:
                            if v['short_name'] == self._VariableShortName and s['service_format'] == 'zarr' and s['service_type']['service_name'] == 'arco-geo-series':
                                if service is not None:
                                    self._LogWarning(_('The Copernicus Marine Service catalogue contains multiple datasets with the ID "%(datasetID)s", or the the metadata for that dataset contains multiple "arco-geo-series" services, or the service contains multiple variables named "%(var)s". This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. The first variable of the first service for the first dataset will be used. Check your results carefully. If you suspect a problem, contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                                    continue
                                else:
                                    service = s
                                    variable = v

            # Extract the lazy property values from the service and variable
            # records. First, determine the dimensions. Note that we can't
            # determine the *physical* dimension order from the catalogue
            # record. For that, we need to open the dataset itself.

            coordinates = {}

            for coord in variable['coordinates']:
                if not isinstance(coord, dict) or not 'coordinates_id' in coord:
                    raise RuntimeError(_('In the Copernicus Marine Service catalogue, the coordinates dictionary for the "%(var)s" variable of the "%(datasetID)s" contains an item that is not a dictionary, or that dictionary does not contain a "coordinates_id" key. This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})
                if coord['coordinates_id'] not in ('time', 'depth', 'latitude', 'longitude'):
                    raise RuntimeError(_('In the Copernicus Marine Service catalogue, the coordinates dictionary for the "%(var)s" variable of the "%(datasetID)s" contains a coordinate named "%(coord)s". MGET does not recognize this coordinate and therefore cannot process this dataset. MGET can only recognize coordinates named "time", "depth", "latitude", and "longitude". Please check your dataset ID and variable name to ensure they are correct. If they are and you believe MGET should be able to handle this unrecognized coordinate, please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': coord['coordinates_id']})
                if coord['coordinates_id'] in coordinates:
                    raise RuntimeError(_('In the Copernicus Marine Service catalogue, the coordinates dictionary for the "%(var)s" variable of the "%(datasetID)s" contains more than one coordinate named "%(coord)s". This is unexpected and may indicate a problem with Copernicus Marine Service, the copernicusmarine Python package, or MGET. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'coord': coord['coordinates_id']})
                coordinates[coord['coordinates_id']] = coord

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
            # coordIncrement, the grid will not span exactly 360 degrees,
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

            # Handle the y coordinate. 

            yExtent = float(coordinates['latitude']['maximum_value']) - coordinates['latitude']['minimum_value'] + coordinates['latitude']['step']
            shape[-2] = int(round(yExtent / coordinates['latitude']['step']))

            cornerCoords[-2] = float(coordinates['latitude']['minimum_value'])
            if self._CornerCoordTypes[-2] == 'min':
                cornerCoords[-2] += coordIncrements[-2] / 2
            elif self._CornerCoordTypes[-2] == 'max':
                cornerCoords[-2] -= coordIncrements[-2] / 2

            coordIncrements[-2] = float(coordinates['latitude']['step'])   # We have not noticed a problem with the latitude 'step' like we did for longitude

            # Some datasets such as GLOBAL_ANALYSISFORECAST_PHY_001_024 are
            # node registered rather than cell registered, which means their
            # bottom-most row might be centered at -90.0 or the top most at
            # +90.0. We don't like this, because it means the grid extends
            # below -90.0 or above +90.0, which is impossible. Check for this
            # and move up and/or down one cell as needed to keep the grid
            # within +/- 90.0

            cellsUpFromBottom = 0
            while cornerCoords[-2] - coordIncrements[-2]/2 < -90.:
                cellsUpFromBottom += 1
                shape[-2] -= 1
                cornerCoords[-2] += coordIncrements[-2]
            if cellsUpFromBottom > 0:
                self._LogDebug('%(class)s 0x%(id)016X: The bottom edge of the bottom row of this dataset is %(orig)r, which is less than -90.0. Omitting the bottom-most %(skip)i row(s) of this dataset, so the bottom edge will be >= -90.0.' % {'class': self.__class__.__name__, 'id': id(self), 'orig': float(coordinates['latitude']['minimum_value']), 'skip': cellsUpFromBottom})

            cellsDownFromTop = 0
            while cornerCoords[-2] + (shape[-2] - 1)*coordIncrements[-2] + coordIncrements[-2]/2 > 90.:
                cellsDownFromTop += 1
                shape[-2] -= 1
            if cellsDownFromTop > 0:
                self._LogDebug('%(class)s 0x%(id)016X: The top edge of the top row of this dataset is %(orig)r, which is greater than 90.0. Omitting the top-most %(skip)i row(s) of this dataset, so the top edge will be <= 90.0.' % {'class': self.__class__.__name__, 'id': id(self), 'orig': cornerCoords[-2] + (shape[-2] - 1 + cellsDownFromTop)*coordIncrements[-2] + coordIncrements[-2]/2, 'skip': cellsDownFromTop})

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

                if 'units' not in coordinates['time'] or not isinstance(coordinates['time']['units'], str):
                    raise RuntimeError(_('In the Copernicus Marine Service catalogue, the "time" coordinate of the %(var)s" variable of the "%(datasetID)s" does not have a "units" attribute, or that attribute is not a numeric value. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName})

                units = coordinates['time']['units'].lower().split()
                if len(units) < 4 or units[0] not in ['milliseconds', 'seconds', 'minutes', 'hours', 'days'] or units[1] != 'since':
                    raise RuntimeError(_('In the Copernicus Marine Service catalogue, for the "time" coordinate of the %(var)s" variable of the "%(datasetID)s", the value of the "units" attribute, "%(units)s", could not be parsed. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'units': coordinates['time']['units']})

                try:
                    since = datetime.datetime.strptime((units[2] + ' ' + units[3])[:19], '%Y-%m-%d %H:%M:%S')
                except:
                    raise RuntimeError(_('In the Copernicus Marine Service catalogue, for the "time" coordinate of the %(var)s" variable of the "%(datasetID)s", the value of the "units" attribute, "%(units)s", could not be parsed. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'datasetID': self._DatasetID, 'var': self._VariableShortName, 'units': coordinates['time']['units']})

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
            raise RuntimeError(_('The dimensions %(dims)s for variable "%(var)s" of Copernicus Marine Service dataset "%(url)s" do not match what is in the Copernicus Marine Service catalogue. MGET may not be compatible with this dataset, or there may be problem with Copernicus Marine Service or the copernicusmarine Python package. Please contact the MGET development team for assistance.') % {'url': self._URI, 'var': self._VariableShortName, 'dims': da.dims})

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
            from copernicusmarine.download_functions.download_arco_series import open_dataset_from_arco_series
            from copernicusmarine.download_functions.subset_parameters import DepthParameters, GeographicalParameters, TemporalParameters

            self._LogDebug('%(class)s 0x%(id)016X: Opening the xarray by calling copernicusmarine.download_functions.download_arco_series.open_dataset_from_arco_series(username=***, password=***,, dataset_url="%(url)s", variables=["%(var)s"], geographical_parameters=GeographicalParameters(), temporal_parameters=TemporalParameters(), depth_parameters=DepthParameters(), chunks="auto")' % {'class': self.__class__.__name__, 'id': id(self), 'url': self._URI, 'var': self._VariableStandardName})

            try:
                self._Dataset = open_dataset_from_arco_series(username=self._Username, 
                                                              password=self._Password,
                                                              dataset_url=self._URI,
                                                              variables=[self._VariableStandardName],
                                                              geographical_parameters=GeographicalParameters(),
                                                              temporal_parameters=TemporalParameters(),
                                                              depth_parameters=DepthParameters(),
                                                              chunks='auto')
            except Exception as e:
                raise RuntimeError(_('Failed to open Copernicus Marine Service dataset "%(url)s". Please check your internet connectivity and that your username and password is correct. The following error, reported by the copernicusmarine.download_functions.download_arco_series.open_dataset_from_arco_series() function, may indicate the problem: %(e)s: %(msg)s.') % {'url': self._URI, 'e': e.__class__.__name__, 'msg': e})

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
        self._Open()
        sliceName = ','.join([str(s.start) + ':' + str(s.stop) for s in sliceList])
        self._LogDebug(_('%(class)s 0x%(id)016X: Reading slice [%(slice)s] of %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'slice': sliceName, 'dn': self.DisplayName})
        try:
            return self._Dataset[self._VariableShortName].__getitem__(tuple(sliceList)).data.compute(), self.GetLazyPropertyValue('UnscaledNoDataValue')
        except Exception as e:
            raise RuntimeError(_('Failed to read slice [%(slice)s] of %(dn)s. Detailed error information: %(e)s: %(msg)s.') % {'slice': sliceName, 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})


###############################################################################
# Metadata: module
###############################################################################

from ..Dependencies import PythonModuleDependency
from ..Metadata import *
from ..Types import *

AddModuleMetadata(
    shortDescription=_('Classes for accessing oceanographic datasets published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`_.'),
    longDescription=_('Copernicus Marine Service is also known as Copernicus Marine Environmental Monitoring Service (CMEMS).'))

###############################################################################
# Metadata: CMEMSARCOArray class
###############################################################################

AddClassMetadata(CMEMSARCOArray,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` for accessing 3D and 4D gridded datasets published by `Copernicus Marine Service <https://data.marine.copernicus.eu/products>`_.'),
    longDescription=_('Copernicus Marine Service is also known as Copernicus Marine Environmental Monitoring Service (CMEMS).'))

# TODO


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['CMEMSARCOArray']
