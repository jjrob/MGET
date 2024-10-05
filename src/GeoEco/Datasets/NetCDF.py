# NetCDF.py - Defines NetCDFFile, which exposes a netCDF file as a
# FileDatasetCollection, and NetCDFVariable, which exposes a netCDF variable
# as a Grid.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import os

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _

from . import QueryableAttribute, Grid
from .Collections import DirectoryTree, FileDatasetCollection


class NetCDFFile(FileDatasetCollection):
    __doc__ = DynamicDocString()

    def __init__(self, path, decompressedFileToReturn=None, displayName=None, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._RootDataset = None
        self._CallerProvidedDisplayName = displayName is not None

        if displayName is not None:
            self._DisplayName = displayName
        elif parentCollection is None:
            self._DisplayName = _('netCDF file %(path)s') % {'path': path}
        elif isinstance(parentCollection, DirectoryTree):
            self._DisplayName = _('netCDF file %(path)s') % {'path': os.path.join(parentCollection.Path, path)}
        else:
            self._DisplayName = _('netCDF file %(path)s from %(parent)s') % {'path': path, 'parent': parentCollection.DisplayName}

        # We allow querying for datasets by variable name and index. If the
        # parent collection(s) or the caller did not define the VariableName
        # and VariableIndex queryable attributes, we must define them.

        qa = []
        if queryableAttributes is not None:
            qa.extend(queryableAttributes)

        varNameAttr = None
        if parentCollection is not None:
            varNameAttr = parentCollection.GetQueryableAttribute('VariableName')
        if varNameAttr is None:
            for attr in qa:
                if attr.Name == 'VariableName':
                    varNameAttr = attr
                    break
        if varNameAttr is None:
            varNameAttr = QueryableAttribute('VariableName', _('Variable name'), UnicodeStringTypeMetadata())
            qa.append(varNameAttr)

        varTypeAttr = None
        if parentCollection is not None:
            varTypeAttr = parentCollection.GetQueryableAttribute('VariableIndex')
        if varTypeAttr is None:
            for attr in qa:
                if attr.Name == 'VariableIndex':
                    varTypeAttr = attr
                    break
        if varTypeAttr is None:
            varTypeAttr = QueryableAttribute('VariableIndex', _('Variable index'), IntegerTypeMetadata(minValue=0))
            qa.append(varTypeAttr)

        # Initialize the base class.
        
        super(NetCDFFile, self).__init__(path, decompressedFileToReturn, parentCollection, tuple(qa), queryableAttributeValues, lazyPropertyValues, cacheDirectory)

        # Validate that the caller has not assigned a value to the
        # VariableName or VariableIndex queryable attributes, either directly
        # to us or to our parent collection(s).

        if self.GetQueryableAttributeValue('VariableName') is not None:
            raise ValueError(_('This NetCDFFile or its parent collection(s) specify a value for the VariableName queryable attribute. This is not allowed, as the value of that queryable attribute is assigned by the NetCDFFile class.'))

        if self.GetQueryableAttributeValue('VariableIndex') is not None:
            raise ValueError(_('This NetCDFFile or its parent collection(s) specify a value for the VariableIndex queryable attribute. This is not allowed, as the value of that queryable attribute is assigned by the NetCDFFile class.'))

    def _Close(self):
        if hasattr(self, '_RootDataset') and self._RootDataset is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Closing %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
            self._RootDataset.close()
            self._RootDataset = None
        super(NetCDFFile, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known property, return None.

        if name not in ['VariableNames']:
            return None

        # Open the file, if not opened already.

        self._Open()

        # Retrieve VariableNames by doing a depth-first search of the netCDF's
        # groups for variables that have between 2 and 4 dimensions.

        variableNames = []
        
        def _GetVariableNames(variableNames, obj):
            for name, var in obj.variables.items():
                ndim = 0
                for i in range(len(var.dimensions)):
                    if var.shape[i] > 1:
                        ndim += 1
                if ndim in [2,3,4]:
                    variableNames.append(name)

            for name, group in obj.groups.items():
                _GetVariableNames(variableNames, group)

        _GetVariableNames(variableNames, self._RootDataset)
        
        self.SetLazyPropertyValue('VariableNames', variableNames)

        # Return the property value.

        return self.GetLazyPropertyValue(name)

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):

        # Go through the list of variables available in this file, testing
        # whether each one matches the query expression. For each match,
        # construct a NetCDFVariable instance.

        variableNames = self.GetLazyPropertyValue('VariableNames')
        datasetsFound = []

        for i in range(len(variableNames)):
            if parsedExpression is not None:
                attrValues = {'VariableName': variableNames[i], 'VariableIndex': i}
                attrValues.update(parentAttrValues)
                try:
                    result = parsedExpression.eval(attrValues)
                except Exception as e:
                    continue
            else:
                result = True

            if result is None or result:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for variable %(name)s (index %(index)i) of %(dn)s: %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 'name': variableNames[i], 'index': i, 'dn': self.DisplayName, 'result': repr(result)})

            if result:
                datasetsFound.append(NetCDFVariable(self, variableNames[i], i))
                if progressReporter is not None:
                    progressReporter.ReportProgress()

        return datasetsFound

    def _Open(self):
        if self._RootDataset is None:

            # Get the openable path for this NetCDF. If the NetCDF is part of
            # a remote collection and/or compressed, this will cause it to be
            # downloaded and/or decompressed.

            path, isOriginalFile = self._GetOpenableFile()

            # If this is not the same thing as our original path, update our
            # display name to reflect it.

            if not isOriginalFile and not self._CallerProvidedDisplayName:
                if self.ParentCollection is None:
                    self._DisplayName = _('netCDF file %(path)s (decompressed from %(oldpath)s)') % {'path': path, 'oldpath': self.Path}
                elif isinstance(self.ParentCollection, DirectoryTree):
                    self._DisplayName = _('netCDF file %(path)s (decompressed from %(oldpath)s)') % {'path': path, 'oldpath': os.path.join(self.ParentCollection.Path, self.Path)}
                else:
                    self._DisplayName = _('netCDF file %(path)s (a local copy of %(oldpath)s from %(parent)s)') % {'path': path, 'oldpath': self.Path, 'parent': self.ParentCollection.DisplayName}

            # Open the dataset with netCDF4.

            self._LogDebug(_('%(class)s 0x%(id)016X: Opening %(dn)s with the netCDF4 module.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})

            import netCDF4

            try:
                self._RootDataset = netCDF4.Dataset(path)
            except Exception as e:
                raise RuntimeError(_('Failed to open %(dn)s. The file may not be in netCDF format. Detailed error information: netCDF4.Dataset() reported %(e)s: %(msg)s.') % {'dn': self._DisplayName, 'e': e.__class__.__name__, 'msg': e})

            self._RegisterForCloseAtExit()


class NetCDFVariable(Grid):
    __doc__ = DynamicDocString()

    def _GetVariableName(self):
        return self._VariableName

    VariableName = property(_GetVariableName, doc=DynamicDocString())

    def _GetVariableIndex(self):
        return self._VariableIndex

    VariableIndex = property(_GetVariableIndex, doc=DynamicDocString())

    def __init__(self, netCDFFile, variableName, variableIndex, queryableAttributeValues=None, lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._VariableName = variableName
        self._VariableIndex = variableIndex
        self._DisplayName = _('variable %(name)s of %(dn)s') % {'name': variableName, 'dn': netCDFFile.DisplayName}

        # Assign values to known queryable attributes.

        qav = {}
        if queryableAttributeValues is not None:
            qav.update(queryableAttributeValues)

        qav['VariableName'] = variableName
        qav['VariableIndex'] = variableIndex

        # Initialize the base class.

        super(NetCDFVariable, self).__init__(netCDFFile, queryableAttributeValues=qav, lazyPropertyValues=lazyPropertyValues)

    def _Close(self):
        if hasattr(self, 'ParentCollection') and self.ParentCollection is not None:
            self.ParentCollection.Close()
        super(NetCDFVariable, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known property, return None.

        if name not in ['SpatialReference', 'Shape', 'Dimensions', 'PhysicalDimensions', 'PhysicalDimensionsFlipped', 'CoordDependencies', 'CoordIncrements', 'TIncrement', 'TIncrementUnit', 'TCornerCoordType', 'CornerCoords', 'UnscaledDataType', 'ScaledDataType', 'UnscaledNoDataValue', 'ScaledNoDataValue', 'ScalingFunction', 'UnscalingFunction']:
            return None

        # Fail if the variable does not have between two and four dimensions.

        import numpy

        v = self._GetVariable()
        rank = len(v.shape)
        
        if rank < 2 or rank > 4:
            raise RuntimeError(_('The %(dn)s has %(dim)i dimensions. This number of dimensions is not supported. Only scientific datasets with 2, 3, or 4 dimensions are supported.') % {'dn': self.DisplayName, 'dim': rank})

        # Try to interpret the netCDF dimension names to set
        # PhysicalDimensions, Dimensions, and SpatialReference.

        physicalDimensions = self.GetLazyPropertyValue('PhysicalDimensions', allowPhysicalValue=False)
        if physicalDimensions is None:
            physicalDimensions = [None] * rank
            
            for i in range(rank):
                if v.dimensions[i].lower() in ['x', 'lon', 'long', 'longitude', 'easting'] or \
                     hasattr(v, 'group') and v.dimensions[i] in v.group().variables and hasattr(v.group().variables[v.dimensions[i]], 'units') and v.group().variables[v.dimensions[i]].units in ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE'] or \
                     hasattr(v, 'group') and len([dv for dv in v.group().variables if len(v.group().variables[dv].dimensions) == 1 and v.group().variables[dv].dimensions[0].lower() == v.dimensions[i].lower() and hasattr(v.group().variables[dv], 'units') and v.group().variables[dv].units in ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE']]) > 0 or \
                     v.dimensions[i] in self.ParentCollection._RootDataset.variables and hasattr(self.ParentCollection._RootDataset.variables[v.dimensions[i]], 'units') and self.ParentCollection._RootDataset.variables[v.dimensions[i]].units in ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE']:
                    physicalDimensions[i] = 'x'
                elif v.dimensions[i].lower() in ['y', 'lat', 'latitude', 'northing'] or \
                     hasattr(v, 'group') and v.dimensions[i] in v.group().variables and hasattr(v.group().variables[v.dimensions[i]], 'units') and v.group().variables[v.dimensions[i]].units in ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN'] or \
                     hasattr(v, 'group') and len([dv for dv in v.group().variables if len(v.group().variables[dv].dimensions) == 1 and v.group().variables[dv].dimensions[0].lower() == v.dimensions[i].lower() and hasattr(v.group().variables[dv], 'units') and v.group().variables[dv].units in ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN']]) > 0 or \
                     v.dimensions[i] in self.ParentCollection._RootDataset.variables and hasattr(self.ParentCollection._RootDataset.variables[v.dimensions[i]], 'units') and self.ParentCollection._RootDataset.variables[v.dimensions[i]].units in ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN']:
                    physicalDimensions[i] = 'y'
                elif v.dimensions[i].lower() in ['z', 'depth', 'altitude'] or \
                     hasattr(v, 'group') and v.dimensions[i] in v.group().variables and hasattr(v.group().variables[v.dimensions[i]], 'positive') and v.group().variables[v.dimensions[i]].positive in ['up', 'down'] or \
                     hasattr(v, 'group') and len([dv for dv in v.group().variables if len(v.group().variables[dv].dimensions) == 1 and v.group().variables[dv].dimensions[0].lower() == v.dimensions[i].lower() and hasattr(v.group().variables[dv], 'positive') and v.group().variables[dv].positive in ['up', 'down']]) > 0 or \
                     v.dimensions[i] in self.ParentCollection._RootDataset.variables and hasattr(self.ParentCollection._RootDataset.variables[v.dimensions[i]], 'positive') and self.ParentCollection._RootDataset.variables[v.dimensions[i]].positive in ['up', 'down']:
                    physicalDimensions[i] = 'z'
                elif v.dimensions[i].lower() in ['t', 'time', 'time_steps'] or \
                     hasattr(v, 'group') and v.dimensions[i] in v.group().variables and hasattr(v.group().variables[v.dimensions[i]], 'units') and ' since ' in v.group().variables[v.dimensions[i]].units or \
                     hasattr(v, 'group') and len([dv for dv in v.group().variables if len(v.group().variables[dv].dimensions) == 1 and v.group().variables[dv].dimensions[0].lower() == v.dimensions[i].lower() and hasattr(v.group().variables[dv], 'positive') and ' since ' in v.group().variables[dv].units]) > 0 or \
                     v.dimensions[i] in self.ParentCollection._RootDataset.variables and hasattr(self.ParentCollection._RootDataset.variables[v.dimensions[i]], 'units') and ' since ' in self.ParentCollection._RootDataset.variables[v.dimensions[i]].units:
                    physicalDimensions[i] = 't'
                    
            if None not in physicalDimensions:
                physicalDimensions = ''.join(physicalDimensions)
                self.SetLazyPropertyValue('PhysicalDimensions', physicalDimensions)

        dimensions = self.GetLazyPropertyValue('Dimensions', allowPhysicalValue=False)
        if dimensions is None and physicalDimensions is not None:
            dimensions = ''

            for d in ['t', 'z', 'y', 'x']:
                if d in physicalDimensions:
                    dimensions += d

            self.SetLazyPropertyValue('Dimensions', dimensions)

        # For SpatialReference, all we support at this time is guessing that a
        # WGS 1984 equirectangular system should be used if the spatial
        # dimensions are longitude and latitude.

        hasLongitude = False
        hasLatitude = False

        for i in range(rank):
            if v.dimensions[i].lower() in ['lon', 'long', 'longitude', 'easting'] or \
                 hasattr(v, 'group') and v.dimensions[i] in v.group().variables and hasattr(v.group().variables[v.dimensions[i]], 'units') and v.group().variables[v.dimensions[i]].units in ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE'] or \
                 hasattr(v, 'group') and len([dv for dv in v.group().variables if len(v.group().variables[dv].dimensions) == 1 and v.group().variables[dv].dimensions[0].lower() == v.dimensions[i].lower() and hasattr(v.group().variables[dv], 'units') and v.group().variables[dv].units in ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE']]) > 0 or \
                 v.dimensions[i] in self.ParentCollection._RootDataset.variables and hasattr(self.ParentCollection._RootDataset.variables[v.dimensions[i]], 'units') and self.ParentCollection._RootDataset.variables[v.dimensions[i]].units in ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE']:
                hasLongitude = True
            elif v.dimensions[i].lower() in ['lat', 'latitude', 'northing'] or \
                 hasattr(v, 'group') and v.dimensions[i] in v.group().variables and hasattr(v.group().variables[v.dimensions[i]], 'units') and v.group().variables[v.dimensions[i]].units in ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN'] or \
                 hasattr(v, 'group') and len([dv for dv in v.group().variables if len(v.group().variables[dv].dimensions) == 1 and v.group().variables[dv].dimensions[0].lower() == v.dimensions[i].lower() and hasattr(v.group().variables[dv], 'units') and v.group().variables[dv].units in ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN']]) > 0 or \
                 v.dimensions[i] in self.ParentCollection._RootDataset.variables and hasattr(self.ParentCollection._RootDataset.variables[v.dimensions[i]], 'units') and self.ParentCollection._RootDataset.variables[v.dimensions[i]].units in ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN']:
                hasLatitude = True

        proj4String = None
        if self.GetLazyPropertyValue('SpatialReference', allowPhysicalValue=False) is None and hasLongitude and hasLatitude:
            proj4String = '+proj=latlong +ellps=WGS84 +datum=WGS84 +no_defs'
            self.SetLazyPropertyValue('SpatialReference', self.ConvertSpatialReference('proj4', proj4String, 'obj'))

        # Get the shape, now that we know the physicalDimensions.

        if self.GetLazyPropertyValue('Shape', allowPhysicalValue=False) is None:
            s = [None] * rank
            for i, d in enumerate(dimensions):
                s[i] = v.shape[physicalDimensions.index(d)]
            self.SetLazyPropertyValue('Shape', tuple(s))

        # If the netCDF includes variables for each dimension, try to read
        # them to determine PhysicalDimensionsFlipped.

        physicalDimensionsFlipped = self.GetLazyPropertyValue('PhysicalDimensionsFlipped', allowPhysicalValue=False)
        if physicalDimensionsFlipped is None:
            physicalDimensionsFlipped = [None] * rank

            for i, d in enumerate(physicalDimensions):
                dimensionVariable = self._GetDimensionVariableForVariable(d, v, i)
                if dimensionVariable is not None and len(dimensionVariable.shape) == 1:
                    if dimensionVariable.shape[0] <= 1:
                        physicalDimensionsFlipped[i] = False
                    else:
                        physicalDimensionsFlipped[i] = bool(dimensionVariable[1] < dimensionVariable[0])    # Use bool() to convert to base type from numpy array
                    
            if None not in physicalDimensionsFlipped:
                physicalDimensionsFlipped = tuple(physicalDimensionsFlipped)
                self.SetLazyPropertyValue('PhysicalDimensionsFlipped', physicalDimensionsFlipped)
            else:
                physicalDimensionsFlipped = None

        # For each dimension, if the netCDF variable for it has a 1D shape,
        # assume that CoordDependencies is None for that dimension.

        coordDependencies = self.GetLazyPropertyValue('CoordDependencies', allowPhysicalValue=False)
        if coordDependencies is None and physicalDimensions is not None and dimensions is not None:
            coordDependencies = []
            
            for i, d in enumerate(dimensions):
                j = physicalDimensions.index(d)
                dimensionVariable = self._GetDimensionVariableForVariable(d, v, j)
                if dimensionVariable is not None and len(dimensionVariable.shape) == 1:
                    coordDependencies.append(None)

            if len(coordDependencies) == rank:
                coordDependencies = tuple(coordDependencies)
                self.SetLazyPropertyValue('CoordDependencies', coordDependencies)
            else:
                coordDependencies = None

        # If we have CoordDependencies but not CoordIncrements, obtain a
        # CoordIncrements value for each dimension that has CoordDependencies
        # of None.

        coordIncrements = self.GetLazyPropertyValue('CoordIncrements', allowPhysicalValue=False)
        if coordIncrements is None and physicalDimensions is not None and dimensions is not None and coordDependencies is not None:
            coordIncrements = [None] * rank

            for i, d in enumerate(dimensions):
                if coordDependencies[i] is not None:        # This should generally not happen; usually the caller would have supplied coordIncrements if this were the case.
                    continue
                j = physicalDimensions.index(d)

                # If this dimension has a length of 1, we have no way to
                # compute the increment. Just assume it is 1.

                if v.shape[j] <= 1:
                    coordIncrements[i] = 1.

                # Otherwise, check that the increment is the same between all
                # cells. If it is, use that as the increment.

                else:
                    dimensionVariable = self._GetDimensionVariableForVariable(d, v, j)
                    if dimensionVariable is None:
                        continue
                    
                    assert len(dimensionVariable.shape) == 1, 'The dimension variable does not have an expected shape of 1. Please contact the MGET development team for assistance.'

                    increments = dimensionVariable[1:] - dimensionVariable[:-1]
                    if len(increments) <= 1 or all([increment == increments[0] for increment in increments[1:]]):
                        coordIncrements[i] = float(abs(increments[0]))
                        continue

                    # If we got to here, the increments are not the same
                    # between all cells. If this is the x or y dimension,
                    # check to see if the increments are very close to being
                    # the same. This happens with at least two-widely used
                    # datasets, NOAA NODC AVHRR Pathfinder SST 5.2 and NASA
                    # OceanColor L3 SMI. If they are within 0.1% of each
                    # other, compute a constant increment from the
                    # farthest-apart cells.

                    if d in ['x', 'y']:
                        fractionalDifference = [abs(1 - increment/increments[0]) for increment in increments]
                        if max(fractionalDifference) < 0.001:
                            coordIncrements[i] = float(abs((dimensionVariable[-1] - dimensionVariable[0]) / (dimensionVariable.shape[0] - 1)))

                            # As a further refinement, if this appears to be a
                            # global image and the coordinates are longitude
                            # or latitude, compute a precise increment.

                            if d == 'x' and hasLongitude and abs(360. - coordIncrements[i]*dimensionVariable.shape[0]) < 0.001:
                                coordIncrements[i] = 360. / dimensionVariable.shape[0]

                            elif d == 'y' and hasLatitude and abs(180. - coordIncrements[i]*dimensionVariable.shape[0]) < 0.001:
                                coordIncrements[i] = 180. / dimensionVariable.shape[0]

            # Unfortunately, when the netCDF creator does not store
            # fully-precise coordinates in the dimension variables, the logic
            # above can result in x and y coordinate increments that are
            # slightly different when they should be exactly the same. This
            # can cause problems for ArcGIS, which expects exactly square
            # cells for most raster formats. Check whether the coordinate
            # increments are within 0.1% of each other. If they are, make them
            # the same.

            if coordIncrements[-2] is not None and coordIncrements[-1] is not None and coordIncrements[-2] != coordIncrements[-1] and abs(1 - coordIncrements[-2]/coordIncrements[-1]) < 0.001:
                coordIncrements[-2] = (coordIncrements[-2] + coordIncrements[-1]) / 2
                coordIncrements[-1] = coordIncrements[-2]

            coordIncrements = tuple(coordIncrements)
            self.SetLazyPropertyValue('CoordIncrements', coordIncrements)

        # If we have a t dimension and CoordIncrements[0] is not None, try to
        # guess values for TIncrement, TIncrementUnit, and TCornerCoordType.

        if dimensions is not None and dimensions[0] == 't' and physicalDimensions is not None and self.GetLazyPropertyValue('TIncrement', allowPhysicalValue=False) is None and coordIncrements[0] is not None:

            # Just set TIncrement to CoordIncrements[0].
            
            self.SetLazyPropertyValue('TIncrement', coordIncrements[0])

            # Try to parse TIncrementUnit from the units attribute of the time
            # dimension variable.

            j = physicalDimensions.index('t')
            dimensionVariable = self._GetDimensionVariableForVariable('t', v, j)
            if dimensionVariable is not None:
                if hasattr(dimensionVariable, 'units') and ' since ' in dimensionVariable.units:
                    timeUnit = dimensionVariable.units.split(' ')[0]
                    if timeUnit.lower() in ['day', 'days', 'd']:
                        self.SetLazyPropertyValue('TIncrementUnit', 'day')
                    elif timeUnit.lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
                        self.SetLazyPropertyValue('TIncrementUnit', 'hour')
                    elif timeUnit.lower() in ['minute', 'minutes', 'min', 'mins']:
                        self.SetLazyPropertyValue('TIncrementUnit', 'minute')
                    elif timeUnit.lower() in ['second', 'seconds', 'sec', 'secs', 's']:
                        self.SetLazyPropertyValue('TIncrementUnit', 'second')

                # Guess that TCornerCoordType is 'center'. This seems to be
                # traditional for the datasets that have been using netCDF for
                # long time.

                self.SetLazyPropertyValue('TCornerCoordType', 'center')

        # If we have CoordDependencies but not CornerCoords, obtain a
        # CornerCoords value for each dimension that has CoordDependencies of
        # None.

        if self.GetLazyPropertyValue('CornerCoords', allowPhysicalValue=False) is None and physicalDimensions is not None and dimensions is not None and coordDependencies is not None:
            cornerCoords = [None] * rank

            for i, d in enumerate(dimensions):
                if coordDependencies[i] is not None:        # This should generally not happen; usually the caller would have supplied CornerCoords if this were the case.
                    continue

                j = physicalDimensions.index(d)
                dimensionVariable = self._GetDimensionVariableForVariable(d, v, j)
                if dimensionVariable is None:
                    continue

                if physicalDimensionsFlipped[j]:
                    cornerCoords[i] = dimensionVariable[-1]
                else:
                    cornerCoords[i] = dimensionVariable[0]

                if d != 't':
                    cornerCoords[i] = float(cornerCoords[i])

                # If this is the t dimension, parse a datetime from
                # the numerical coordinate.

                if d == 't':
                    if hasattr(dimensionVariable, 'units') and ' since ' in dimensionVariable.units:
                        import netCDF4
                        try:
                            cornerCoords[i] = netCDF4.num2date(cornerCoords[i], dimensionVariable.units)
                        except:
                            cornerCoords[i] = None
                    else:
                        cornerCoords[i] = None

                # If this is the x or y dimension and the coordinates are
                # longitudes/latitudes and it is a global image and the corner
                # coordinates are very close to but not exactly a round
                # degree, it is likely that the netCDF creator intended them
                # to be exactly that round degree but did not specify them in
                # full precision; round them to that degree.

                elif coordIncrements is not None and coordIncrements[i] is not None and \
                     (d == 'x' and hasLongitude and abs(360. - coordIncrements[i]*dimensionVariable.shape[0]) < 0.001 or \
                      d == 'y' and hasLatitude and abs(180. - coordIncrements[i]*dimensionVariable.shape[0]) < 0.001):
                    
                    if abs(cornerCoords[i] - round(cornerCoords[i])) / coordIncrements[i] < 0.001:
                        cornerCoords[i] = round(cornerCoords[i])
                        
                    elif abs(cornerCoords[i] - coordIncrements[i]/2 - round(cornerCoords[i] - coordIncrements[i]/2)) / coordIncrements[i] < 0.001:
                        cornerCoords[i] = round(cornerCoords[i] - coordIncrements[i]/2) + coordIncrements[i]/2

            cornerCoords = tuple(cornerCoords)
            self.SetLazyPropertyValue('CornerCoords', cornerCoords)

        # Get the UnscaledDataType.

        unscaledDataType = v.dtype.name
        if unscaledDataType not in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64']:
            raise TypeError(_('The %(dn)s has an unknown data type %(type)s. The data type of this variable is not supported.') %{'dn': self.DisplayName, 'type': unscaledDataType})
        self.SetLazyPropertyValue('UnscaledDataType', unscaledDataType)

        # If an UnscaledNoDataValue has not been defined, check the netCDF
        # attributes for standard values.

        unscaledNoDataValue = self.GetLazyPropertyValue('UnscaledNoDataValue', allowPhysicalValue=False)
        if unscaledNoDataValue is None:
            if 'missing_value' in v.ncattrs() and hasattr(v, 'missing_value') and v.missing_value is not None:
                unscaledNoDataValue = v.missing_value
            elif '_FillValue' in v.ncattrs() and hasattr(v, '_FillValue') and v._FillValue is not None:
                unscaledNoDataValue = v._FillValue
            else:
                unscaledNoDataValue = None

            if unscaledNoDataValue is not None:
                if unscaledDataType.startswith('int') or unscaledDataType.startswith('uint'):
                    unscaledNoDataValue = int(int(unscaledNoDataValue))     # Yes, call int() twice. I found that with Pathfinder 6.0 file, the sst_dtime variable which is int32 with _FillValue=-2147483648, the result of the FIRST int() was -2147483648L, a Python long, not -2147483648, a Python int. We want the int. By calling int() again, the -2147483648L is converted to -2147483648.
                self.SetLazyPropertyValue('UnscaledNoDataValue', unscaledNoDataValue)

        # If a ScalingFunction has not been defined, check the netCDF
        # attributes for standard values.

        if self.GetLazyPropertyValue('ScalingFunction', allowPhysicalValue=False) is None:
            if 'scale_factor' in v.ncattrs() and hasattr(v, 'scale_factor') and v.scale_factor is not None:
                scale_factor = v.scale_factor
            else:
                scale_factor = 1.

            if 'add_offset' in v.ncattrs() and hasattr(v, 'add_offset') and v.add_offset is not None:
                add_offset = v.add_offset
            else:
                add_offset = 0.

            if scale_factor != 1. or add_offset != 0.:

                # We found it. First set the ScaledDataType to float32, unless
                # it has already been defined.

                scaledDataType = self.GetLazyPropertyValue('ScaledDataType', allowPhysicalValue=False)
                if scaledDataType is None:
                    scaledDataType = 'float32'
                    self.SetLazyPropertyValue('ScaledDataType', scaledDataType)
                elif scaledDataType not in ['float32', 'float64']:
                    raise RuntimeError(_('Programming error: the %(dn)s has a scale_factor and/or add_offset attribute(s) defined, but the caller specified that the ScaledDataType lazy property is %(value)s. This is not allowed; it must be either float32 or float64. Please contact the MGET development team for assistance.') %{'dn': self.DisplayName, 'value': scaledDataType})

                # Set the ScalingFunction, ScaledNoDataValue, and
                # UnscalingFunction.

                scalingFunction = lambda data: numpy.asarray(scale_factor*data + add_offset, dtype=scaledDataType)
                self.SetLazyPropertyValue('ScalingFunction', scalingFunction)
                
                if unscaledNoDataValue is not None:
                    self.SetLazyPropertyValue('ScaledNoDataValue', scalingFunction(unscaledNoDataValue))
                else:
                    self.SetLazyPropertyValue('ScaledNoDataValue', None)

                self.SetLazyPropertyValue('UnscalingFunction', lambda data: numpy.asarray(numpy.round((data - add_offset)/scale_factor), dtype=v.dtype.name))

        # Log a debug message with the lazy property values.

        self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: Shape=%(Shape)r, PhysicalDimensions=%(PhysicalDimensions)r, PhysicalDimensionsFlipped=%(PhysicalDimensionsFlipped)r, Dimensions=%(Dimensions)r, CoordDependencies=%(CoordDependencies)r, CoordIncrements=%(CoordIncrements)r, TIncrement=%(TIncrement)r, TIncrementUnit=%(TIncrementUnit)r, CornerCoords=%(CornerCoords)r, TCornerCoordType=%(TCornerCoordType)r, UnscaledDataType=%(UnscaledDataType)r, UnscaledNoDataValue=%(UnscaledNoDataValue)r, ScaledDataType=%(ScaledDataType)r, ScaledNoDataValue=%(ScaledNoDataValue)r, SpatialReference=%(SpatialReference)r.'),
                       {'class': self.__class__.__name__, 'id': id(self), 'dn': self.DisplayName,
                        'Shape': self.GetLazyPropertyValue('Shape', allowPhysicalValue=False),
                        'Dimensions': self.GetLazyPropertyValue('Dimensions', allowPhysicalValue=False),
                        'PhysicalDimensions': self.GetLazyPropertyValue('PhysicalDimensions', allowPhysicalValue=False),
                        'PhysicalDimensionsFlipped': self.GetLazyPropertyValue('PhysicalDimensionsFlipped', allowPhysicalValue=False),
                        'CoordDependencies': self.GetLazyPropertyValue('CoordDependencies', allowPhysicalValue=False),
                        'CoordIncrements': self.GetLazyPropertyValue('CoordIncrements', allowPhysicalValue=False),
                        'TIncrement': self.GetLazyPropertyValue('TIncrement', allowPhysicalValue=False),
                        'TIncrementUnit': self.GetLazyPropertyValue('TIncrementUnit', allowPhysicalValue=False),
                        'CornerCoords': self.GetLazyPropertyValue('CornerCoords', allowPhysicalValue=False),
                        'TCornerCoordType': self.GetLazyPropertyValue('TCornerCoordType', allowPhysicalValue=False),
                        'UnscaledDataType': self.GetLazyPropertyValue('UnscaledDataType', allowPhysicalValue=False),
                        'UnscaledNoDataValue': self.GetLazyPropertyValue('UnscaledNoDataValue', allowPhysicalValue=False),
                        'ScaledDataType': self.GetLazyPropertyValue('ScaledDataType', allowPhysicalValue=False),
                        'ScaledNoDataValue': self.GetLazyPropertyValue('ScaledNoDataValue', allowPhysicalValue=False),
                        'SpatialReference': proj4String})

        # Return the property value.

        return self.GetLazyPropertyValue(name, allowPhysicalValue=False)

    def _GetDimensionVariableForVariable(self, d, v, j):
        dimensionVariable = None
        if hasattr(v, 'group'):
            if v.dimensions[j] in v.group().variables:
                dimensionVariable = v.group().variables[v.dimensions[j]]
            else:
                dvList = [dv for dv in v.group().variables if len(v.group().variables[dv].dimensions) == 1 and v.group().variables[dv].dimensions[0].lower() == v.dimensions[j].lower()]
                if len(dvList) == 1:
                    dimensionVariable = v.group().variables[dvList[0]]
                elif d == 't' and 'time' in v.group().variables and len(v.group().variables['time'].dimensions) == 1: 
                    dimensionVariable = v.group().variables['time']    # Hack: fall back to 'time' if it exists but we could not navigate to it through the netCDF metadata with any of the logic above. This occurs in CCMP v03.1, for example.
        if dimensionVariable is None and v.dimensions[j] in self.ParentCollection._RootDataset.variables:
            dimensionVariable = self.ParentCollection._RootDataset.variables[v.dimensions[j]]
        return dimensionVariable

    def _GetVariable(self):
        self.ParentCollection._Open()
        try:
            v = self.ParentCollection._RootDataset.variables[self._VariableName]
        except Exception as e:
            raise RuntimeError(_('Failed to open a variable named "%(name)s" in %(dn)s. Detailed error information: %(e)s: %(msg)s.') % {'name': self._VariableName, 'dn': self.ParentCollection.DisplayName, 'e': e.__class__.__name__, 'msg': e})

        # Turn off auto masking and scaling. We will handle those operations.

        v.set_auto_maskandscale(False)
        return v

    def _ReadNumpyArray(self, sliceList):
        v = self._GetVariable()
        sliceName = ','.join([str(s.start) + ':' + str(s.stop) for s in sliceList])
        self._LogDebug(_('%(class)s 0x%(id)016X: Reading slice [%(slice)s] of %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'slice': sliceName, 'dn': self.DisplayName})
        try:
            return v.__getitem__(tuple(sliceList)).copy(), self.GetLazyPropertyValue('UnscaledNoDataValue')
        except Exception as e:
            raise RuntimeError(_('Failed to read slice [%(slice)s] of %(dn)s. Detailed error information: %(e)s: %(msg)s.') % {'slice': sliceName, 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})


###############################################################################
# Metadata: module
###############################################################################

from ..Dependencies import PythonModuleDependency
from ..Metadata import *
from ..Types import *

AddModuleMetadata(shortDescription=_('A :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` and :class:`~GeoEco.Datasets.Grid` for accessing 2D, 3D, and 4D gridded variables in netCDF files through the Python `netCDF4 <https://pypi.org/project/netCDF4/>`_ module.'))

###############################################################################
# Metadata: NetCDFFile class
###############################################################################

AddClassMetadata(NetCDFFile,
    shortDescription=_('A :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` of the gridded variables in a netCDF-3 or netCDF-4 file.'))

# Public constructor: NetCDFFile.__init__

AddMethodMetadata(NetCDFFile.__init__,
    shortDescription=_('NetCDFFile constructor.'),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

AddArgumentMetadata(NetCDFFile.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=NetCDFFile),
    description=_(':class:`%s` instance.') % NetCDFFile.__name__)

CopyArgumentMetadata(FileDatasetCollection.__init__, 'path', NetCDFFile.__init__, 'path')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'decompressedFileToReturn', NetCDFFile.__init__, 'decompressedFileToReturn')

AddArgumentMetadata(NetCDFFile.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Informal name of this object. If you do not provide a name, a suitable name
will be created automatically."""))

CopyArgumentMetadata(FileDatasetCollection.__init__, 'parentCollection', NetCDFFile.__init__, 'parentCollection')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributes', NetCDFFile.__init__, 'queryableAttributes')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributeValues', NetCDFFile.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'lazyPropertyValues', NetCDFFile.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'cacheDirectory', NetCDFFile.__init__, 'cacheDirectory')

AddResultMetadata(NetCDFFile.__init__, 'collection',
    typeMetadata=ClassInstanceTypeMetadata(cls=NetCDFFile),
    description=_(':class:`%s` instance.') % NetCDFFile.__name__)

###############################################################################
# Metadata: NetCDFVariable class
###############################################################################

AddClassMetadata(NetCDFVariable,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing a 2D, 3D, or 4D gridded variable in a netCDF file.'))

# Public constructor: NetCDFVariable.__init__

AddMethodMetadata(NetCDFVariable.__init__,
    shortDescription=_('NetCDFVariable constructor.'),
    longDescription=_(
"""This class is not intended to be instantiated directly. Instances of this
class are returned by
:func:`GeoEco.Datasets.NetCDF.NetCDFFile.QueryDatasets`.

If `CF Metadata <https://cfconventions.org/>`_ are present, this tool will
attempt to parse them to determine how to set the lazy properties required by
:class:`~GeoEco.Datasets.Grid` that are related to spatial and temporal
coordinates and the scaling and NoData value of the variable. If suitable
metadata are not present, or are too sophisticated for this tool to
understand, you must manually set these lazy properties (with 
:func:`~GeoEco.Datasets.NetCDF.NetCDFVariable.SetLazyPropertyValue`) before
the :class:`~GeoEco.Datasets.NetCDF.NetCDFVariable` instance is usable."""),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

AddArgumentMetadata(NetCDFVariable.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=NetCDFVariable),
    description=_(':class:`%s` instance.') % NetCDFVariable.__name__)

AddArgumentMetadata(NetCDFVariable.__init__, 'netCDFFile',
    typeMetadata=ClassInstanceTypeMetadata(cls=NetCDFFile),
    description=_(
""":class:`~GeoEco.Datasets.NetCDF.NetCDFFile` instance that represents the
file that contains this variable."""))

AddArgumentMetadata(NetCDFVariable.__init__, 'variableName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of this variable in the netCDF file."""))

AddArgumentMetadata(NetCDFVariable.__init__, 'variableIndex',
    typeMetadata=IntegerTypeMetadata(minValue=0),
    description=_(
"""Index of this variable in the netCDF file. Only 2D, 3D, and 4D variables
are considered. The first one in the file has index 0, the second index 1, and
so on. In netCDF-4 files that contain groups, the groups are visited in depth
first order."""))

CopyArgumentMetadata(NetCDFFile.__init__, 'queryableAttributeValues', NetCDFVariable.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(NetCDFFile.__init__, 'lazyPropertyValues', NetCDFVariable.__init__, 'lazyPropertyValues')

AddResultMetadata(NetCDFVariable.__init__, 'variable',
    typeMetadata=ClassInstanceTypeMetadata(cls=NetCDFVariable),
    description=_(':class:`%s` instance.') % NetCDFVariable.__name__)


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['NetCDFFile', 'NetCDFVariable']
