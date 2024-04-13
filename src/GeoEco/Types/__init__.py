# Types.py - Provides classes used to describe and validate property values,
# method arguments, and return values.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

# To keep file sizes managable, we split the names defined by this package
# across several files.

from ._Base import TypeMetadata
from ._Base import AnyObjectTypeMetadata
from ._Base import NoneTypeMetadata
from ._Base import ClassTypeMetadata
from ._Base import ClassInstanceTypeMetadata
from ._Base import ClassOrClassInstanceTypeMetadata
from ._Base import BooleanTypeMetadata
from ._Base import DateTimeTypeMetadata
from ._Base import FloatTypeMetadata
from ._Base import IntegerTypeMetadata
from ._Base import UnicodeStringTypeMetadata
from ._Sequence import SequenceTypeMetadata
from ._Sequence import ListTypeMetadata
from ._Sequence import TupleTypeMetadata
from ._Sequence import DictionaryTypeMetadata
from ._Sequence import ListTableTypeMetadata
from ._StoredObject import StoredObjectTypeMetadata
from ._StoredObject import FileTypeMetadata
from ._StoredObject import TextFileTypeMetadata
from ._StoredObject import DirectoryTypeMetadata


###############################################################################
# Metadata: module
###############################################################################

from ..Internationalization import _
from ..Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Classes used to describe and validate property values, method arguments, and return values.'))

# To avoid creating circular module imports that Python cannot handle, we have
# we could not put the metadata for the classes above in the same file that
# defined them. Instead, we created separate files just for the metadata.
# import those now, so that metadata is created.

from ._BaseMetadata import *
from ._SequenceMetadata import *
from ._StoredObjectMetadata import *


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['TypeMetadata',
           'AnyObjectTypeMetadata',
           'NoneTypeMetadata',
           'ClassTypeMetadata',
           'ClassInstanceTypeMetadata',
           'ClassOrClassInstanceTypeMetadata',
           'BooleanTypeMetadata',
           'DateTimeTypeMetadata',
           'FloatTypeMetadata',
           'IntegerTypeMetadata',
           'UnicodeStringTypeMetadata',
           'SequenceTypeMetadata',
           'ListTypeMetadata',
           'TupleTypeMetadata',
           'DictionaryTypeMetadata',
           'ListTableTypeMetadata',
           'StoredObjectTypeMetadata',
           'FileTypeMetadata',
           'TextFileTypeMetadata',
           'DirectoryTypeMetadata',
           # 'ArcGISGeoDatasetTypeMetadata',
           # 'ArcGISRasterTypeMetadata',
           # 'ArcGISRasterLayerTypeMetadata',
           # 'ArcGISFeatureClassTypeMetadata',
           # 'ArcGISRasterCatalogTypeMetadata',
           # 'ArcGISFeatureLayerTypeMetadata',
           # 'ShapefileTypeMetadata',
           # 'ArcGISWorkspaceTypeMetadata',
           # 'ArcGISTableTypeMetadata',
           # 'ArcGISTableViewTypeMetadata',
           # 'ArcGISFieldTypeMetadata',
           # 'CoordinateSystemTypeMetadata',
           # 'EnvelopeTypeMetadata',
           # 'LinearUnitTypeMetadata',
           # 'MapAlgebraExpressionTypeMetadata',
           # 'PointTypeMetadata',
           # 'SpatialReferenceTypeMetadata',
           # 'SQLWhereClauseTypeMetadata',
           # 'NumPyArrayTypeMetadata',
           # 'TableFieldTypeMetadata'
           ]
