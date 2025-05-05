# _GDALDatasetMetadata.py - Metadata for classes defined in
# _GDALDataset.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from .. import Grid
from ..Collections import FileDatasetCollection
from ._GDALDataset import GDALDataset
from ._GDALRasterBand import GDALRasterBand


###############################################################################
# Metadata: GDALDataset class
###############################################################################

AddClassMetadata(GDALDataset,
    module=__package__,
    shortDescription=_('A 2D raster dataset represented as a :class:`~GeoEco.Datasets.Collections.FileDatasetCollection` of :class:`GDALRasterBand`\\ s.'),
    longDescription=_(
"""The `Geospatial Data Abstraction Library (GDAL) <https://www.gdal.org>`_ is
a free open-source library for accessing geospatial data in a variety of
`raster formats <https://www.gdal.org/formats_list.html>`_ and `vector formats
<https://gdal.org/drivers/vector/index.html>`_ through a common interface.
The fundamental elements of GDAL's raster object model are the
:class:`osgeo.gdal.Dataset` and :class:`osgeo.gdal.Band` classes, wrapped here by
:class:`GDALDataset` and :class:`GDALRasterBand`. A :class:`osgeo.gdal.Dataset`
is an assembly of related :class:`osgeo.gdal.Band`\\ s, typically contained in
the same file, and some information common to them all, such as their
dimensions, coordinate system, spatial extent, and cell size. 

Note:
	The wrapper implemented here may not fully support all of GDAL's formats.
	Also, although GDAL provides some support for bands having more than two
	dimensions and for accessing hierarchical data formats such as HDF and
	NetCDF, those capabilities are not supported by the wrapper implemented
	here. Separate GeoEco classes are provided for accessing HDF, NetCDF, and
	OPeNDAP datasets.
"""))

# Public properties

AddPropertyMetadata(GDALDataset.IsUpdatable,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('Indicates whether the dataset should be opened in update mode, allowing the data within its bands to be changed.'))

# Public constructor: GDALDataset.__init__

AddMethodMetadata(GDALDataset.__init__,
    shortDescription=_('GDALDataset constructor.'))

AddArgumentMetadata(GDALDataset.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALDataset),
    description=_(':class:`%s` instance.') % GDALDataset.__name__)

AddArgumentMetadata(GDALDataset.__init__, 'path',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('path').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('path').Description)

AddArgumentMetadata(GDALDataset.__init__, 'updatable',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""Indicates whether the dataset should be opened in update mode, allowing the
data within its bands to be changed.

GDAL does not allow all formats to be opened in update mode. For more about
this, please see https://www.gdal.org/formats_list.html."""))

AddArgumentMetadata(GDALDataset.__init__, 'decompressedFileToReturn',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('decompressedFileToReturn').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('decompressedFileToReturn').Description)

AddArgumentMetadata(GDALDataset.__init__, 'displayName',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name for this dataset to be displayed to the user. If a display
name is not provided, a generic one will be generated
automatically."""))

AddArgumentMetadata(GDALDataset.__init__, 'parentCollection',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('parentCollection').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('parentCollection').Description)

AddArgumentMetadata(GDALDataset.__init__, 'queryableAttributeValues',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('queryableAttributeValues').Description)

AddArgumentMetadata(GDALDataset.__init__, 'lazyPropertyValues',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('lazyPropertyValues').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('lazyPropertyValues').Description)

AddArgumentMetadata(GDALDataset.__init__, 'cacheDirectory',
    typeMetadata=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('cacheDirectory').Type,
    description=FileDatasetCollection.__init__.__doc__.Obj.GetArgumentByName('cacheDirectory').Description)

AddArgumentMetadata(GDALDataset.__init__, 'warpOptions',
    typeMetadata=ClassInstanceTypeMetadata(cls=dict, canBeNone=True),
    description=_(
""":py:class:`dict` instance giving options to pass to ``gdal.Warp()``. If
provided, ``gdal.Warp()`` will be called on the dataset after it is opened and
used to create a GDAL virtual dataset (VRT), and this :class:`%(cls)s` instance will
wrap the warped virtual dataset instead.  If :py:data:`None` is provided,
``gdal.Warp()`` will not be called.

.. Note::
    Warped cell values will be generated on the fly by GDAL whenever they are
    retrieved from this :class:`%(cls)s` instance. This can be an expensive
    operation and no caching will be done. If you plan to access the same
    cells over and over, consider caching the retrieved values.

""" % {'cls': GDALDataset.__name__}))

AddResultMetadata(GDALDataset.__init__, 'gdalDataset',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALDataset),
    description=_(':class:`%s` instance.') % GDALDataset.__name__)

# Public method: GetRasterBand

AddMethodMetadata(GDALDataset.GetRasterBand,
    shortDescription=_('Opens a GDAL dataset and returns a :class:`GDALRasterBand` for the specified band.'),
    longDescription=_(
"""This is a convenience function that is equivalent to:

.. code-block:: python

    from GeoEco.Datasets.GDAL import GDALDataset

    with GDALDataset(path, updatable=updatable, decompressedFileToReturn=decompressedFileToReturn, displayName=displayName, cacheDirectory=cacheDirectory) as dataset:
        grids = dataset.QueryDatasets('Band = %i' % band, reportProgress=False)
        if len(grids) <= 0:
            raise ValueError(_('Cannot retrieve band %(band)i from %(dn)s. The band does not exist.') % {'band': band, 'dn': dataset.DisplayName})
        gdalRasterBand = grids[0]

    # Now do something with the gdalRasterBand object...
"""))

AddArgumentMetadata(GDALDataset.GetRasterBand, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GDALDataset),
    description=_(':class:`%s` or an instance of it.') % GDALDataset.__name__)

AddArgumentMetadata(GDALDataset.GetRasterBand, 'path', 
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Full path to the dataset to open. If the path points to compressed file, it
will be decompressed automatically. If a cache directory is provided, it will
be checked first for an existing decompressed file. If none is found the file
will be decompressed there. If the compressed file is an archive (e.g. .zip or
.tar), you must also specify a decompressed file to return."""))

AddArgumentMetadata(GDALDataset.GetRasterBand, 'band', 
    typeMetadata=IntegerTypeMetadata(minValue=1),
    description=_('The band to get.'))

CopyArgumentMetadata(GDALDataset.__init__, 'updatable', GDALDataset.GetRasterBand, 'updatable')
CopyArgumentMetadata(GDALDataset.__init__, 'decompressedFileToReturn', GDALDataset.GetRasterBand, 'decompressedFileToReturn')
CopyArgumentMetadata(GDALDataset.__init__, 'displayName', GDALDataset.GetRasterBand, 'displayName')
CopyArgumentMetadata(GDALDataset.__init__, 'cacheDirectory', GDALDataset.GetRasterBand, 'cacheDirectory')

AddResultMetadata(GDALDataset.GetRasterBand, 'gdalRasterBand',
    typeMetadata=ClassInstanceTypeMetadata(cls=GDALRasterBand),
    description=_(':class:`%s` instance.') % GDALRasterBand.__name__)

# Public method: CreateRaster

AddMethodMetadata(GDALDataset.CreateRaster,
    shortDescription=_('Creates a GDAL raster dataset from a :class:`~GeoEco.Datasets.Grid`.'),
    longDescription=_(
"""This is a convenience function that is equivalent to:

.. code-block:: python

    from GeoEco.Datasets.Collections import DirectoryTree
    from GeoEco.Datasets.GDAL import GDALDataset

    dirTree = DirectoryTree(path=os.path.dirname(path),
                            datasetType=GDALDataset,
                            pathCreationExpressions=[os.path.basename(path)])

    dirTree.ImportDatasets(datasets=[grid], 
                           mode='Replace' if overwriteExisting else 'Add',
                           reportProgress=False,
                           options=options)
"""))

CopyArgumentMetadata(GDALDataset.GetRasterBand, 'cls', GDALDataset.CreateRaster, 'cls')

AddArgumentMetadata(GDALDataset.CreateRaster, 'path', 
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Path to the GDAL raster dataset to create.'))

AddArgumentMetadata(GDALDataset.CreateRaster, 'grid', 
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to write to the raster. It must be two dimensional.'))

AddArgumentMetadata(GDALDataset.CreateRaster, 'overwriteExisting', 
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True and `path` exists, it will be overwritten. If False and `path` exists, an error will be raised.'))

AddArgumentMetadata(GDALDataset.CreateRaster, 'options',
    typeMetadata=DictionaryTypeMetadata(keyType=ClassInstanceTypeMetadata(cls=str), valueType=AnyObjectTypeMetadata(canBeNone=False)),
    description=_(
"""Additional options, which can include:

* ``blockSize`` (:py:class:`int`) - Number of bytes to read at a time from the
  grid and write to the raster. The default is 32*1024*1024 bytes (32 MB).

* ``calculateStatistics`` (:py:class:`bool`) - If True, statistics will be
  calculated using GDAL and written along with the raster in the appropriate
  format. Depending on the raster's format, the statistics may be present in
  the raster file itself, or a "sidecar" file with the extension ``.aux.xml``.

* ``calculateHistogram`` (:py:class:`bool`) - If True, a histogram will be
  calculated using GDAL and written along with the raster in the appropriate
  format. Depending on the raster's format, the histogram may be present in
  the raster file itself, or a "sidecar" file with the extension ``.aux.xml``.

* ``gdalCreateOptions`` (:py:class:`list` of :py:class:`str`) - List of
  options to be passed to :py:meth:`osgeo.gdal.Driver.Create` to create the
  raster.

* ``gdalDriverName`` (:py:class:`str`) - GDAL driver name to use, to be passed
  to :py:func:`osgeo.gdal.GetDriverByName` to retrieve the driver.

* ``overviewResamplingMethod`` (:py:class:`str`) and ``'overviewList'``
  (:py:class:`list` of :py:class:`int`) - The resampling method and list of
  overview levels (decimation factors) to use to build overviews (known as
  "pyramids" in ArcGIS terminology) using
  :py:meth:`osgeo.gdal.Dataset.BuildOverviews`. Both must be specified.

* ``useArcGISSpatialReference`` (:py:class:`bool`) - If True, the
  ArcGIS-compatible WKT string will be used when defining the raster's spatial
  reference. Additionally, the ``FORCETOPESTRING=YES`` creation option will be
  set if the output is ERDAS IMAGINE (.img) format.

* ``useUnscaledData`` (:py:class:`bool`) - If True and `grid` has a scaling
  equation, the underlying unscaled data will be written out, rather than the
  scaled data that are normally of interest.

"""))


########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.GDAL instead.
########################################################################################

__all__ = []
