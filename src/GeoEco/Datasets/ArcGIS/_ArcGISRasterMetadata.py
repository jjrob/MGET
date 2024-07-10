# _ArcGISRasterMetadata.py - Metadata for classes defined in _ArcGISRaster.py.
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

from .. import Grid
from ..Collections import FileDatasetCollection
from ._ArcGISRaster import ArcGISRaster
from ._ArcGISRasterBand import ArcGISRasterBand


###############################################################################
# Metadata: ArcGISRaster class
###############################################################################

AddClassMetadata(ArcGISRaster,
    module=__package__,
    shortDescription=_('A 2D raster dataset represented as a :class:`~GeoEco.Datasets.DatasetCollection` of :class:`ArcGISRasterBand`\\ s.'))

# Public properties

AddPropertyMetadata(ArcGISRaster.Path,
    typeMetadata=ArcGISRasterTypeMetadata(mustExist=True),
    shortDescription=_('ArcGIS catalog path to the raster.'))

CopyPropertyMetadata(FileDatasetCollection.DecompressedFileToReturn, ArcGISRaster.DecompressedFileToReturn)

AddPropertyMetadata(ArcGISRaster.ArcGISDataType,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Data type of the raster. Obtained from the ``DataType`` property returned by arcpy\'s :arcpy:`Describe`.'))

# Public constructor: ArcGISRaster.__init__

AddMethodMetadata(ArcGISRaster.__init__,
    shortDescription=_('ArcGISRaster constructor.'),
    dependencies=[ArcGISDependency()])

AddArgumentMetadata(ArcGISRaster.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRaster),
    description=_(':class:`%s` instance.') % ArcGISRaster.__name__)

AddArgumentMetadata(ArcGISRaster.__init__, 'path',
    typeMetadata=ArcGISRaster.Path.__doc__.Obj.Type,
    description=ArcGISRaster.Path.__doc__.Obj.ShortDescription)

AddArgumentMetadata(ArcGISRaster.__init__, 'decompressedFileToReturn',
    typeMetadata=ArcGISRaster.DecompressedFileToReturn.__doc__.Obj.Type,
    description=ArcGISRaster.DecompressedFileToReturn.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(FileDatasetCollection.__init__, 'parentCollection', ArcGISRaster.__init__, 'parentCollection')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'queryableAttributeValues', ArcGISRaster.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'lazyPropertyValues', ArcGISRaster.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(FileDatasetCollection.__init__, 'cacheDirectory', ArcGISRaster.__init__, 'cacheDirectory')

AddResultMetadata(ArcGISRaster.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRaster),
    description=_(':class:`%s` instance.') % ArcGISRaster.__name__)

# Public method: GetRasterBand

AddMethodMetadata(ArcGISRaster.GetRasterBand,
    shortDescription=_('Opens an ArcGIS raster and returns an :class:`ArcGISRasterBand` for the specified band.'),
    longDescription=_(
"""This is a convenience function that is equivalent to:

.. code-block:: python

    from GeoEco.Datasets.ArcGIS import ArcGISRaster

    with ArcGISRaster(path, decompressedFileToReturn=decompressedFileToReturn, cacheDirectory=cacheDirectory) as dataset:
        grids = dataset.QueryDatasets('Band = %i' % band, reportProgress=False)
        if len(grids) <= 0:
            raise ValueError(_('Cannot retrieve band %(band)i from %(dn)s. The band does not exist.') % {'band': band, 'dn': dataset.DisplayName})
        arcgisRasterBand = grids[0]

    # Now do something with the arcgisRasterBand object...
"""))

AddArgumentMetadata(ArcGISRaster.GetRasterBand, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=ArcGISRaster),
    description=_(':class:`%s` or an instance of it.') % ArcGISRaster.__name__)

CopyArgumentMetadata(ArcGISRaster.__init__, 'path', ArcGISRaster.GetRasterBand, 'path')

AddArgumentMetadata(ArcGISRaster.GetRasterBand, 'band', 
    typeMetadata=IntegerTypeMetadata(minValue=1),
    description=_('The band to get.'))

CopyArgumentMetadata(ArcGISRaster.__init__, 'decompressedFileToReturn', ArcGISRaster.GetRasterBand, 'decompressedFileToReturn')
CopyArgumentMetadata(ArcGISRaster.__init__, 'cacheDirectory', ArcGISRaster.GetRasterBand, 'cacheDirectory')

AddResultMetadata(ArcGISRaster.GetRasterBand, 'arcgisRasterBand',
    typeMetadata=ClassInstanceTypeMetadata(cls=ArcGISRasterBand),
    description=_(':class:`%s` instance.') % ArcGISRasterBand.__name__)

# Public method: CreateRaster

AddMethodMetadata(ArcGISRaster.CreateRaster,
    shortDescription=_('Writes a :class:`~GeoEco.Datasets.Grid` out as an ArcGIS raster.'),
    longDescription=_(
"""This is a convenience function that is equivalent to:

.. code-block:: python

    from GeoEco.Datasets.ArcGIS import ArcGISWorkspace, ArcGISRaster

    ws = ArcGISWorkspace(path=os.path.dirname(path),
                         datasetType=ArcGISRaster,
                         pathCreationExpressions=[os.path.basename(path)])

    ws.ImportDatasets(datasets=[grid], 
                      mode='Replace' if overwriteExisting else 'Add',
                      reportProgress=False,
                      options=options)
"""))

CopyArgumentMetadata(ArcGISRaster.GetRasterBand, 'cls', ArcGISRaster.CreateRaster, 'cls')

AddArgumentMetadata(ArcGISRaster.CreateRaster, 'path', 
    typeMetadata=ArcGISRasterTypeMetadata(),
    description=_('ArcGIS catalog path to the raster to create.'))

AddArgumentMetadata(ArcGISRaster.CreateRaster, 'grid', 
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to write to the raster. It must be two dimensional.'))

AddArgumentMetadata(ArcGISRaster.CreateRaster, 'overwriteExisting', 
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True and `path` exists, it will be overwritten. If False and `path` exists, an error will be raised.'))

AddArgumentMetadata(ArcGISRaster.CreateRaster, 'options',
    typeMetadata=DictionaryTypeMetadata(keyType=ClassInstanceTypeMetadata(cls=str), valueType=AnyObjectTypeMetadata(canBeNone=False)),
    description=_(
"""Additional options, which can include:

* ``blockSize`` (:py:class:`int`) - Number of bytes to read at a time from the
  grid and write to the raster. The default is 32*1024*1024 bytes (32 MB).

* ``buildPyramids`` (:py:class:`bool`) - If True, pyramids will be built for
  the raster using the :arcpy_management:`Build-Pyramids` geoprocessing tool.

* ``buildRAT`` (:py:class:`bool`) - If True, a raster attribute table will
  be built for the raster using the
  :arcpy_management:`Build-Raster-Attribute-Table` geoprocessing tool.

* ``calculateStatistics`` (:py:class:`bool`) - If True, statistics and a
  histogram will be calculated using GDAL and written along with the raster in
  the appropriate format. Depending on the raster's format, the statistics and
  histogram may be present in the raster file itself, or a "sidecar" file with
  the extension ``.aux.xml``.

* ``useUnscaledData`` (:py:class:`bool`) - If True and `grid` has a scaling
  equation, the underlying unscaled data will be written out, rather than the
  scaled data that are normally of interest.
"""))


##########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.ArcGIS instead.
##########################################################################################

__all__ = []
