# HDF4.py - Defines HDF4SDSCollection, which exposes an HDF version 4 file as
# a FileDatasetCollection, and HDF4SDS, which exposes a Scientific Dataset
# (SDS) in an HDF4 file as a Grid.
#
# Copyright (C) 2025 Jason J. Roberts
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


class HDF4SDSCollection(FileDatasetCollection):
    __doc__ = DynamicDocString()

    def __init__(self, path, decompressedFileToReturn=None, displayName=None, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._HDF = None
        self._CallerProvidedDisplayName = displayName is not None

        if displayName is not None:
            self._DisplayName = displayName
        elif parentCollection is None:
            self._DisplayName = _('HDF version 4 file %(path)s') % {'path': path}
        elif isinstance(parentCollection, DirectoryTree):
            self._DisplayName = _('HDF version 4 file %(path)s') % {'path': os.path.join(parentCollection.Path, path)}
        else:
            self._DisplayName = _('HDF version 4 file %(path)s from %(parent)s') % {'path': path, 'parent': parentCollection.DisplayName}

        # We allow querying for datasets by SDS name and index. If the parent
        # collection(s) or the caller did not define the SDSName and SDSIndex
        # queryable attributes, we must define them.

        qa = []
        if queryableAttributes is not None:
            qa.extend(queryableAttributes)

        varNameAttr = None
        if parentCollection is not None:
            varNameAttr = parentCollection.GetQueryableAttribute('SDSName')
        if varNameAttr is None:
            for attr in qa:
                if attr.Name == 'SDSName':
                    varNameAttr = attr
                    break
        if varNameAttr is None:
            varNameAttr = QueryableAttribute('SDSName', _('HDF Scientific Dataset name'), UnicodeStringTypeMetadata())
            qa.append(varNameAttr)

        varTypeAttr = None
        if parentCollection is not None:
            varTypeAttr = parentCollection.GetQueryableAttribute('SDSIndex')
        if varTypeAttr is None:
            for attr in qa:
                if attr.Name == 'SDSIndex':
                    varTypeAttr = attr
                    break
        if varTypeAttr is None:
            varTypeAttr = QueryableAttribute('SDSIndex', _('HDF Scientific Dataset index'), IntegerTypeMetadata(minValue=0))
            qa.append(varTypeAttr)

        # Initialize the base class.
        
        super(HDF4SDSCollection, self).__init__(path, decompressedFileToReturn, parentCollection, tuple(qa), queryableAttributeValues, lazyPropertyValues, cacheDirectory)

        # Validate that the caller has not assigned a value to the
        # SDSName or SDSIndex queryable attributes, either directly to
        # us or to our parent collection(s).

        if self.GetQueryableAttributeValue('SDSName') is not None:
            raise ValueError(_('This HDF4SDSCollection or its parent collection(s) specify a value for the SDSName queryable attribute. This is not allowed, as the value of that queryable attribute is assigned by the HDF4SDSCollection class.'))

        if self.GetQueryableAttributeValue('SDSIndex') is not None:
            raise ValueError(_('This HDF4SDSCollection or its parent collection(s) specify a value for the SDSIndex queryable attribute. This is not allowed, as the value of that queryable attribute is assigned by the HDF4SDSCollection class.'))

    def _Close(self):
        if hasattr(self, '_HDF') and self._HDF is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Closing %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})
            self._HDF.end()
            self._HDF = None
        super(HDF4SDSCollection, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known property, return None.

        if name not in ['SDSNames', 'SDSIndices']:
            return None

        # Open the file, if not opened already.

        self._Open()

        # Retrieve SDSNames and SDSIndices.

        datasets = self._HDF.datasets()
        sdsNames = list(datasets.keys())
        sdsNames.sort()

        i = 0
        while i < len(sdsNames):
            if len(datasets[sdsNames[i]][0]) < 2 or len(datasets[sdsNames[i]][0]) > 4:
                del sdsNames[i]
            else:
                i += 1
        
        self.SetLazyPropertyValue('SDSNames', sdsNames)
        self.SetLazyPropertyValue('SDSIndices', [datasets[sdsName][3] for sdsName in sdsNames])

        # Return the property value.

        return self.GetLazyPropertyValue(name)

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):

        # Go through the list of SDSes available in this file, testing whether
        # each one matches the query expression. For each match, construct an
        # HDF4SDS instance.

        sdsNames = self.GetLazyPropertyValue('SDSNames')
        sdsIndices = self.GetLazyPropertyValue('SDSIndices')
        datasetsFound = []

        for i in range(len(sdsNames)):
            if parsedExpression is not None:
                attrValues = {'SDSName': sdsNames[i], 'SDSIndex': sdsIndices[i]}
                attrValues.update(parentAttrValues)
                try:
                    result = parsedExpression.eval(attrValues)
                except Exception as e:
                    continue
            else:
                result = True

            if result is None or result:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for SDS %(sdsName)s (index %(sdsIndex)i) of %(dn)s: %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 'sdsName': sdsNames[i], 'sdsIndex': sdsIndices[i], 'dn': self.DisplayName, 'result': repr(result)})

            if result:
                datasetsFound.append(HDF4SDS(self, sdsNames[i], sdsIndices[i]))
                if progressReporter is not None:
                    progressReporter.ReportProgress()

        return datasetsFound

    def _Open(self):
        if self._HDF is None:

            # Get the openable path for this HDF. If the HDF is part of a
            # remote collection and/or compressed, this will cause it to be
            # downloaded and/or decompressed.

            path, isOriginalFile = self._GetOpenableFile()

            # If this is not the same thing as our original path, update our
            # display name to reflect it.

            if not isOriginalFile and not self._CallerProvidedDisplayName:
                if self.ParentCollection is None:
                    self._DisplayName = _('HDF version 4 file %(path)s (decompressed from %(oldpath)s)') % {'path': path, 'oldpath': self.Path}
                elif isinstance(self.ParentCollection, DirectoryTree):
                    self._DisplayName = _('HDF version 4 file %(path)s (decompressed from %(oldpath)s)') % {'path': path, 'oldpath': os.path.join(self.ParentCollection.Path, self.Path)}
                else:
                    self._DisplayName = _('HDF version 4 file %(path)s (a local copy of %(oldpath)s from %(parent)s)') % {'path': path, 'oldpath': self.Path, 'parent': self.ParentCollection.DisplayName}

            # Open the dataset with pyhdf.

            self._LogDebug(_('%(class)s 0x%(id)016X: Opening %(dn)s with pyhdf.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})

            from pyhdf.SD import SD, SDC

            try:
                self._HDF = SD(path, SDC.READ)
            except Exception as e:
                raise RuntimeError(_('Failed to open %(dn)s. The file may not be in HDF 4 format. Detailed error information: pyhdf\'s SD constructor reported %(e)s: %(msg)s.') % {'dn': self._DisplayName, 'e': e.__class__.__name__, 'msg': e})

            self._RegisterForCloseAtExit()


class HDF4SDS(Grid):
    __doc__ = DynamicDocString()

    def _GetSDSName(self):
        return self._SDSName

    SDSName = property(_GetSDSName, doc=DynamicDocString())

    def _GetSDSIndex(self):
        return self._SDSIndex

    SDSIndex = property(_GetSDSIndex, doc=DynamicDocString())

    def __init__(self, hdf4SDSCollection, sdsName, sdsIndex, queryableAttributeValues=None, lazyPropertyValues=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._SDSName = sdsName
        self._SDSIndex = sdsIndex
        self._DisplayName = _('scientific dataset %(name)s of %(dn)s') % {'name': sdsName, 'dn': hdf4SDSCollection.DisplayName}

        # Assign values to known queryable attributes.

        qav = {}
        if queryableAttributeValues is not None:
            qav.update(queryableAttributeValues)

        qav['SDSName'] = sdsName
        qav['SDSIndex'] = sdsIndex

        # Initialize the base class.

        super(HDF4SDS, self).__init__(hdf4SDSCollection, queryableAttributeValues=qav, lazyPropertyValues=lazyPropertyValues)

    def _Close(self):
        if hasattr(self, 'ParentCollection') and self.ParentCollection is not None:
            self.ParentCollection.Close()
        super(HDF4SDS, self)._Close()

    def _GetDisplayName(self):
        return self._DisplayName

    def _GetLazyPropertyPhysicalValue(self, name):

        # If it is not a known property, return None.

        if name not in ['Shape', 'UnscaledDataType']:
            return None

        # Get the Shape. Fail if it does not have between two and four
        # dimensions.

        sds = self._GetSDS()

        rank, shape, dataType = sds.info()[1:4]
        
        if rank < 2 or rank > 4:
            raise RuntimeError(_('The %(dn)s has %(dim)i dimensions. This number of dimensions is not supported. Only scientific datasets with 2, 3, or 4 dimensions are supported.') % {'dn': self.DisplayName, 'dim': rank})

        if rank != len(self.Dimensions):
            raise RuntimeError(_('Programming error in this tool: the %(dn)s was expected to have %(dim1)i dimensions but it actually has %(dim2)i. Please contact the author of this tool for assistance.') % {'dn': self.DisplayName, 'dim1': len(self.Dimensions), 'dim2': rank})

        self.SetLazyPropertyValue('Shape', tuple(shape))

        # Get the UnscaledDataType.

        from pyhdf.SD import SDC

        if dataType == SDC.INT8:
            self.SetLazyPropertyValue('UnscaledDataType', 'int8')
        elif dataType == SDC.UINT8:
            self.SetLazyPropertyValue('UnscaledDataType', 'uint8')
        elif dataType == SDC.INT16:
            self.SetLazyPropertyValue('UnscaledDataType', 'int16')
        elif dataType == SDC.UINT16:
            self.SetLazyPropertyValue('UnscaledDataType', 'uint16')
        elif dataType == SDC.INT32:
            self.SetLazyPropertyValue('UnscaledDataType', 'int32')
        elif dataType == SDC.UINT32:
            self.SetLazyPropertyValue('UnscaledDataType', 'uint32')
        elif dataType == SDC.FLOAT32:
            self.SetLazyPropertyValue('UnscaledDataType', 'float32')
        elif dataType == SDC.FLOAT64:
            self.SetLazyPropertyValue('UnscaledDataType', 'float64')
        else:
            raise TypeError(_('The %(dn)s has an unknown data type %(type)s. The data type of this scientific dataset is not supported.') %{'dn': self.DisplayName, 'type': dataType})

        # Log a debug message with the lazy property values.

        self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved lazy properties of %(dn)s: Shape=%(Shape)s, UnscaledDataType=%(UnscaledDataType)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self.DisplayName, 'Shape': repr(self.GetLazyPropertyValue('Shape')), 'UnscaledDataType': self.GetLazyPropertyValue('UnscaledDataType')})

        # Return the property value.

        return self.GetLazyPropertyValue(name)

    def _GetSDS(self):
        self.ParentCollection._Open()
        try:
            return self.ParentCollection._HDF.select(self._SDSName)
        except Exception as e:
            raise RuntimeError(_('Failed to open a scientific dataset named "%(name)s" in %(dn)s. Detailed error information: %(e)s: %(msg)s.') % {'name': self._SDSName, 'dn': self.ParentCollection.DisplayName, 'e': e.__class__.__name__, 'msg': e})

    def _ReadNumpyArray(self, sliceList):
        sds = self._GetSDS()
        sliceName = ','.join(map(lambda s: str(s.start) + ':' + str(s.stop), sliceList))
        self._LogDebug(_('%(class)s 0x%(id)016X: Reading slice [%(slice)s] of %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'slice': sliceName, 'dn': self.DisplayName})
        try:
            return sds.__getitem__(tuple(sliceList)), self.GetLazyPropertyValue('UnscaledNoDataValue')
        except Exception as e:
            raise RuntimeError(_('Failed to read slice [%(slice)s] of %(dn)s. Detailed error information: %(e)s: %(msg)s.') % {'slice': sliceName, 'dn': self.DisplayName, 'e': e.__class__.__name__, 'msg': e})


###############################################################################
# Metadata: module
###############################################################################

from ..Dependencies import PythonModuleDependency
from ..Metadata import *
from ..Types import *

AddModuleMetadata(shortDescription=_('A :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` and :class:`~GeoEco.Datasets.Grid` for accessing 2D, 3D, and 4D scientific datasets (SDSes) in HDF version 4 files through the Python `pyhdf <https://pypi.org/project/pyhdf/>`_ module.'))

###############################################################################
# Metadata: HDF4SDSCollection class
###############################################################################

AddClassMetadata(HDF4SDSCollection,
    shortDescription=_('A :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` of the scientific datasets (SDSes) in an HDF version 4 file.'))

# Public constructor: HDF4SDSCollection.__init__

AddMethodMetadata(HDF4SDSCollection.__init__,
    shortDescription=_('HDF4SDSCollection constructor.'),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('pyhdf', cheeseShopName='pyhdf')])

AddArgumentMetadata(HDF4SDSCollection.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=HDF4SDSCollection),
    description=_(':class:`%s` instance.') % HDF4SDSCollection.__name__)

CopyArgumentMetadata(FileDatasetCollection.__init__, 'path', HDF4SDSCollection.__init__, 'path')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'decompressedFileToReturn', HDF4SDSCollection.__init__, 'decompressedFileToReturn')

AddArgumentMetadata(HDF4SDSCollection.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Informal name of this object. If you do not provide a name, a suitable name
will be created automatically."""))

CopyArgumentMetadata(FileDatasetCollection.__init__, 'parentCollection', HDF4SDSCollection.__init__, 'parentCollection')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributes', HDF4SDSCollection.__init__, 'queryableAttributes')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributeValues', HDF4SDSCollection.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'lazyPropertyValues', HDF4SDSCollection.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'cacheDirectory', HDF4SDSCollection.__init__, 'cacheDirectory')

AddResultMetadata(HDF4SDSCollection.__init__, 'collection',
    typeMetadata=ClassInstanceTypeMetadata(cls=HDF4SDSCollection),
    description=_(':class:`%s` instance.') % HDF4SDSCollection.__name__)

###############################################################################
# Metadata: HDF4SDS class
###############################################################################

AddClassMetadata(HDF4SDS,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing a 2D, 3D, or 4D scientific dataset (SDS) in a HDF version 4 file.'))

# Public constructor: HDF4SDS.__init__

AddMethodMetadata(HDF4SDS.__init__,
    shortDescription=_('HDF4SDS constructor.'),
    longDescription=_(
"""This class is not intended to be instantiated directly. Instances of this
class are returned by
:func:`GeoEco.Datasets.HDF4.HDF4SDSCollection.QueryDatasets`.

Note that this tool does not parse any of the HDF attributes and can only
recognize the Shape and DataType of the SDS. If the attributes contain useful
information such as the "fill value" or coordinate system, they will not be
recognized. You must manually set all necessary lazy properties (other than
Shape and DataType) with
:func:`~GeoEco.Datasets.HDF4.HDF4SDS.SetLazyPropertyValue`) before
the :class:`~GeoEco.Datasets.HDF4.HDF4SDS` instance is usable."""),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('pyhdf', cheeseShopName='pyhdf')])

AddArgumentMetadata(HDF4SDS.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=HDF4SDS),
    description=_(':class:`%s` instance.') % HDF4SDS.__name__)

AddArgumentMetadata(HDF4SDS.__init__, 'hdf4SDSCollection',
    typeMetadata=ClassInstanceTypeMetadata(cls=HDF4SDSCollection),
    description=_(
""":class:`~GeoEco.Datasets.HDF4.HDF4SDSCollection` instance that represents
the file that contains this variable."""))

AddArgumentMetadata(HDF4SDS.__init__, 'sdsName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of this scientific dataset (SDS) in the HDF file."""))

AddArgumentMetadata(HDF4SDS.__init__, 'sdsIndex',
    typeMetadata=IntegerTypeMetadata(minValue=0),
    description=_(
"""Index of this scientific dataset (SDS) in the HDF file. Only 2D, 3D, and 4D
SDSes are considered. The first one in the file has index 0, the second index
1, and so on."""))

CopyArgumentMetadata(HDF4SDSCollection.__init__, 'queryableAttributeValues', HDF4SDS.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(HDF4SDSCollection.__init__, 'lazyPropertyValues', HDF4SDS.__init__, 'lazyPropertyValues')

AddResultMetadata(HDF4SDS.__init__, 'variable',
    typeMetadata=ClassInstanceTypeMetadata(cls=HDF4SDS),
    description=_(':class:`%s` instance.') % HDF4SDS.__name__)


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['HDF4SDSCollection', 'HDF4SDS']
