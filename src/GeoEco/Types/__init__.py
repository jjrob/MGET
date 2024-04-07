# To keep file sizes managable, we split the names defined by this package
# across several files.

from .Base import AnyObjectTypeMetadata
from .Base import NoneTypeMetadata
from .Base import ClassTypeMetadata
from .Base import ClassInstanceTypeMetadata
from .Base import ClassOrClassInstanceTypeMetadata
from .Base import BooleanTypeMetadata
from .Base import DateTimeTypeMetadata
from .Base import FloatTypeMetadata
from .Base import IntegerTypeMetadata
from .Base import UnicodeStringTypeMetadata
from .Sequence import SequenceTypeMetadata
from .Sequence import ListTypeMetadata
from .Sequence import TupleTypeMetadata
from .Sequence import DictionaryTypeMetadata
from .Sequence import ListTableTypeMetadata

__all__ = ['AnyObjectTypeMetadata',
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
           # 'StoredObjectTypeMetadata',
           # 'FileTypeMetadata',
           # 'TextFileTypeMetadata',
           # 'DirectoryTypeMetadata',
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
