# _GHRSSTLevel4GranulesMetadata.py - Metadata for classes defined in
# _GHRSSTLevel4Granules.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ....Dependencies import PythonModuleDependency
from ....Internationalization import _
from ....Metadata import *
from ....Types import *

from ..Earthdata._CMRGranuleSearcher import CMRGranuleSearcher
from ._GHRSSTLevel4Granules import GHRSSTLevel4Granules


###############################################################################
# Metadata: GHRSSTLevel4Granules class
###############################################################################

_GHRSSTLevel4_LongDescription = _(
"""The `Group for High-Resolution Sea Surface Temperature (GHRSST)
<https://www.ghrsst.org/>`__ provides a new generation of global
high-resolution (<10km) SST products to the operational oceanographic,
meteorological, climate and general scientific community. The overall aim of
the GHRSST is to provide the best quality sea surface temperature data for
applications in short, medium and decadal/climate time scales in the most cost
effective and efficient manner through international collaboration and
scientific innovation.

This %(name)s accesses Level 4 (L4) gap-free gridded SST products published in
near real-time by the GHRSST Global Data Assembly Center (GDAC) at the `NASA
JPL Physical Oceanography Distributed Active Archive Center (PO.DAAC)
<https://podaac.jpl.nasa.gov/GHRSST>`__ and subsequently hosted and
distributed by `NASA Earthdata <https://www.earthdata.nasa.gov/>`__. These
products provide regional and global daily cloud-free estimates of SST at
spatial resolutions ranging from 0.25 degrees to down 1 km. To fill in cloudy
areas, data from multiple satellite and in-situ sensors are combined and
regions without any data are filled in various interpolation and modeling
techniques.

All products accessed by this %(name)s are published at a daily timestep. Some
products are updated on a continual basis and available in near real time;
others are updated infrequently and are intended mainly for historical
analysis. The temporal extent, spatial resolution and extent, and sensors and
interpolation technique used vary by product. All products use the WGS 1984
geographic coordinate system. GHRSST temperatures are published in kelvin. By
default, this %(name)s converts them to degrees Celsius but provides an
option to obtain the original kelvin values.

This %(name)s supports many but not all of the GHRSST L4 published by PO.DAAC.
If you see a GHRSST L4 product on PO.DAAC that is not available with this
tool, please contact the MGET development team for assistance.

Please see `these instructions <https://podaac.jpl.nasa.gov/CitingPODAAC>`__
on how to acknowledge your use of PO.DAAC products.""")

AddClassMetadata(GHRSSTLevel4Granules,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.DataProducts.NASA.Earthdata.CMRGranuleSearcher` for `NASA JPL PO.DAAC GHRSST <https://podaac.jpl.nasa.gov/GHRSST>`__ L4 datasets hosted by `NASA Earthdata <https://www.earthdata.nasa.gov/>`__.'),
    longDescription=_GHRSSTLevel4_LongDescription % {'name': 'class'})

# Public constructor

AddMethodMetadata(GHRSSTLevel4Granules.__init__,
    shortDescription=_('GHRSSTLevel4Granules constructor.'),
    dependencies=[PythonModuleDependency('requests', cheeseShopName='requests'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

AddArgumentMetadata(GHRSSTLevel4Granules.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GHRSSTLevel4Granules),
    description=_(':class:`%s` instance.') % GHRSSTLevel4Granules.__name__)

CopyArgumentMetadata(CMRGranuleSearcher.__init__, 'username', GHRSSTLevel4Granules.__init__, 'username')
CopyArgumentMetadata(CMRGranuleSearcher.__init__, 'password', GHRSSTLevel4Granules.__init__, 'password')

AddArgumentMetadata(GHRSSTLevel4Granules.__init__, 'shortName',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=sorted(GHRSSTLevel4Granules._Metadata.keys())),
    description=_(
"""PO.DAAC Short Name of the GHRSST L4 product to access. Currently, the
following products are supported:

""" + '\n'.join(['* `%s <https://podaac.jpl.nasa.gov/dataset/%s>`__' % (product, product) for product in sorted(GHRSSTLevel4Granules._Metadata)]) + """

All products use the WGS 1984 geographic coordinate system and are published
at a daily time-step. Some products are updated on a continual basis and
available in near real time; others are updated infrequently and are intended
mainly for historical analysis. The temporal extent, spatial resolution and
extent, sensors and, interpolation technique used vary by product. Please see
the products' documentation for details.

This tool supports many but not all of the GHRSST L4 products published by
PO.DAAC. If you see a product on PO.DAAC that is not available with this tool,
please contact the MGET development team for assistance."""),
    arcGISDisplayName=_('GHRSST L4 product short name'))

AddArgumentMetadata(GHRSSTLevel4Granules.__init__, 'datasetType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['netCDF'], makeLowercase=True),
    description=_(
"""Dataset type to access. Currently only ``netCDF`` is supported. netCDF
files will be downloaded and cached locally. If you specify a Cache Directory,
they will be stored there and not deleted. Otherwise a temporary directory
will be created to hold the files while the download is in progress and
deleted when the relevent data are extracted and execution is complete.

The disadvantage with this approach is that when your study area is small and
you're accessing a global product, a lot of bandwidth and disk space is
wasted. This problem can become acute if you're accessing a global product
with very high resolution, such as one of the 1 km resolution datasets. If
this proves too problematic, contact the MGET development team for assistance.
We may be able to implement an alternative access method that allows downloads
to be limited to a geographic bounding box."""),
    arcGISDisplayName=_('Dataset type'),
    arcGISCategory=_('Network options'))

CopyArgumentMetadata(CMRGranuleSearcher.__init__, 'timeout', GHRSSTLevel4Granules.__init__, 'timeout')
CopyArgumentMetadata(CMRGranuleSearcher.__init__, 'maxRetryTime', GHRSSTLevel4Granules.__init__, 'maxRetryTime')
CopyArgumentMetadata(CMRGranuleSearcher.__init__, 'cacheDirectory', GHRSSTLevel4Granules.__init__, 'cacheDirectory')
CopyArgumentMetadata(CMRGranuleSearcher.__init__, 'metadataCacheLifetime', GHRSSTLevel4Granules.__init__, 'metadataCacheLifetime')

AddResultMetadata(GHRSSTLevel4Granules.__init__, 'collection',
    typeMetadata=ClassInstanceTypeMetadata(cls=GHRSSTLevel4Granules),
    description=_('GHRSSTLevel4Granules instance.'))


###################################################################################################
# This module is not meant to be imported directly. Import GeoEco.DataProducts.NASA.PODAAC instead.
###################################################################################################

__all__ = []
