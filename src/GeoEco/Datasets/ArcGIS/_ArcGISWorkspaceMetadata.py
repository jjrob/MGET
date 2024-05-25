# _ArcGISWorkspaceMetadata.py - Metadata for classes defined in
# _ArcGISWorkspace.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...ArcGIS import ArcGISDependency
from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from ..Collections import DatasetCollectionTree
from ._ArcGISWorkspace import ArcGISWorkspace


###############################################################################
# Metadata: ArcGISWorkspace class
###############################################################################

AddClassMetadata(ArcGISWorkspace,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Collections.DatasetCollectionTree` and :class:`~GeoEco.Datasets.Database` representing an ArcGIS workspace, such as a geodatabase or file system directory.'))

# Public properties

AddPropertyMetadata(ArcGISWorkspace.Path,
    typeMetadata=ArcGISWorkspaceTypeMetadata(mustExist=True),
    shortDescription=_('ArcGIS catalog path to the workspace.'))

AddPropertyMetadata(ArcGISWorkspace.DatasetType,
    typeMetadata=AnyObjectTypeMetadata(),
    shortDescription=_('The class specifying the type of datasets to access in the workspace, either :class:`ArcGISTable` or :class:`ArcGISRaster`.'))

AddPropertyMetadata(ArcGISWorkspace.CacheTree,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, the contents of the workspace will be cached when it is first accessed, to improve performance on future accesses. If False, the contents will be obtained each time the workspace is accessed.'))

# Public constructor: ArcGISWorkspace.__init__

AddMethodMetadata(ArcGISWorkspace.__init__,
    shortDescription=_('ArcGISWorkspace constructor.'),
    dependencies=[ArcGISDependency()])

AddArgumentMetadata(ArcGISWorkspace.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISWorkspace),
    description=_(':class:`%s` instance.') % ArcGISWorkspace.__name__)

AddArgumentMetadata(ArcGISWorkspace.__init__, 'path',
    typeMetadata=ArcGISWorkspace.Path.__doc__.Obj.Type,
    description=ArcGISWorkspace.Path.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISWorkspace.__init__, 'datasetType',
    typeMetadata=ArcGISWorkspace.DatasetType.__doc__.Obj.Type,
    description=ArcGISWorkspace.DatasetType.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(DatasetCollectionTree.__init__, 'pathParsingExpressions', ArcGISWorkspace.__init__, 'pathParsingExpressions')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'pathCreationExpressions', ArcGISWorkspace.__init__, 'pathCreationExpressions')

AddArgumentMetadata(ArcGISWorkspace.__init__, 'cacheTree',
    typeMetadata=ArcGISWorkspace.CacheTree.__doc__.Obj.Type,
    description=ArcGISWorkspace.CacheTree.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(DatasetCollectionTree.__init__, 'queryableAttributes', ArcGISWorkspace.__init__, 'queryableAttributes')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'queryableAttributeValues', ArcGISWorkspace.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'lazyPropertyValues', ArcGISWorkspace.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'cacheDirectory', ArcGISWorkspace.__init__, 'cacheDirectory')

AddResultMetadata(ArcGISWorkspace.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISWorkspace),
    description=_(':class:`%s` instance.') % ArcGISWorkspace.__name__)


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
