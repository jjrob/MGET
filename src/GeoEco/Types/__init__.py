# Types.py - Classes used to describe and validate property values, method
# arguments, and return values.
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
from ._Base import UnicodeStringHiddenTypeMetadata
from ._Sequence import SequenceTypeMetadata
from ._Sequence import ListTypeMetadata
from ._Sequence import TupleTypeMetadata
from ._Sequence import DictionaryTypeMetadata
from ._Sequence import ListTableTypeMetadata
from ._StoredObject import StoredObjectTypeMetadata
from ._StoredObject import FileTypeMetadata
from ._StoredObject import TextFileTypeMetadata
from ._StoredObject import DirectoryTypeMetadata
from ._ArcGIS import ArcGISGeoDatasetTypeMetadata
from ._ArcGIS import ArcGISRasterTypeMetadata
from ._ArcGIS import ArcGISRasterLayerTypeMetadata
from ._ArcGIS import ArcGISFeatureClassTypeMetadata
from ._ArcGIS import ArcGISRasterCatalogTypeMetadata
from ._ArcGIS import ArcGISFeatureLayerTypeMetadata
from ._ArcGIS import ShapefileTypeMetadata
from ._ArcGIS import ArcGISWorkspaceTypeMetadata
from ._ArcGIS import ArcGISTableTypeMetadata
from ._ArcGIS import ArcGISTableViewTypeMetadata
from ._ArcGIS import ArcGISFieldTypeMetadata
from ._ArcGIS import CoordinateSystemTypeMetadata
from ._ArcGIS import EnvelopeTypeMetadata
from ._ArcGIS import LinearUnitTypeMetadata
from ._ArcGIS import MapAlgebraExpressionTypeMetadata
from ._ArcGIS import PointTypeMetadata
from ._ArcGIS import SpatialReferenceTypeMetadata
from ._ArcGIS import SQLWhereClauseTypeMetadata
from ._NumPy import NumPyArrayTypeMetadata
from ._Datasets import TableFieldTypeMetadata

# We have to put this stuff down here to avoid circular imports.

from ..Internationalization import _
from ..Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Classes used to describe and validate property values, method arguments, and return values.'))

from . import _BaseMetadata
from . import _SequenceMetadata
from . import _StoredObjectMetadata
from . import _ArcGISMetadata
from . import _NumPyMetadata
from . import _DatasetsMetadata

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
           'UnicodeStringHiddenTypeMetadata',
           'SequenceTypeMetadata',
           'ListTypeMetadata',
           'TupleTypeMetadata',
           'DictionaryTypeMetadata',
           'ListTableTypeMetadata',
           'StoredObjectTypeMetadata',
           'FileTypeMetadata',
           'TextFileTypeMetadata',
           'DirectoryTypeMetadata',
           'ArcGISGeoDatasetTypeMetadata',
           'ArcGISRasterTypeMetadata',
           'ArcGISRasterLayerTypeMetadata',
           'ArcGISFeatureClassTypeMetadata',
           'ArcGISRasterCatalogTypeMetadata',
           'ArcGISFeatureLayerTypeMetadata',
           'ShapefileTypeMetadata',
           'ArcGISWorkspaceTypeMetadata',
           'ArcGISTableTypeMetadata',
           'ArcGISTableViewTypeMetadata',
           'ArcGISFieldTypeMetadata',
           'CoordinateSystemTypeMetadata',
           'EnvelopeTypeMetadata',
           'LinearUnitTypeMetadata',
           'MapAlgebraExpressionTypeMetadata',
           'PointTypeMetadata',
           'SpatialReferenceTypeMetadata',
           'SQLWhereClauseTypeMetadata',
           'NumPyArrayTypeMetadata',
           'TableFieldTypeMetadata',
          ]
