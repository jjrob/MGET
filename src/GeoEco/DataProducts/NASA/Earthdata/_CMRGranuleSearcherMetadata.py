# _CMRGranuleSearcherMetadata.py - Metadata for classes defined in
# _CMRGranuleSearcher.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ....Datasets import DatasetCollection
from ....Dependencies import PythonModuleDependency
from ....Internationalization import _
from ....Metadata import *
from ....Types import *

from ._CMRGranuleSearcher import CMRGranuleSearcher


###############################################################################
# Metadata: CMRGranuleSearcher class
###############################################################################

AddClassMetadata(CMRGranuleSearcher,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.DatasetCollection` that queries the `NASA Earthdata <https://www.earthdata.nasa.gov/>`__ Common Metadata Repository (CMR) for granules.'),
    longDescription=_(
"""This is a base class that should not be instantiated directly. Instead,
derive a new class from it. The derived class constructor should be sure to
call the base class constructor. The derived class should also override two
methods:

* ``_GetQueryableAttributeValuesForUrl(self, url, title)`` - given a URL to a
  granule and its title, return a dictionary that maps queryable attribute
  names to their values. The values should be derived from the URL. In
  general, the title should only be used in log messages or for similar
  display purposes.

* ``_ConstructFoundObjectForUrl(self, url, title, queryableAttributeValues)`` -

  given the URL to a granule and its title and dictionary of queryable
  attribute values, return a :class:`~GeoEco.Datasets.DatasetCollection`
  instance that represents the granule. For example, if the granule is a
  netCDF file, return a :class:`~GeoEco.Datasets.NetCDF.NetCDFFile` instance.
  The class you derived from
  :class:`~GeoEco.DataProducts.NASA.Earthdata.CMRGranuleSearcher` should be
  used as the parent collection for the instance. `queryableAttributeValues`
  should be also be used to initialize the given instance.

For an example of a derived class, see GHRSSTLevel4EarthdataGranules."""))   # TODO: Update documentation with a :class: reference, once GHRSSTLevel4EarthdataGranules has been defined

# Public constructor

AddMethodMetadata(CMRGranuleSearcher.__init__,
    shortDescription=_('CMRGranuleSearcher constructor.'),
    dependencies=[PythonModuleDependency('requests', cheeseShopName='requests'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=CMRGranuleSearcher),
    description=_(':class:`%s` instance.') % CMRGranuleSearcher.__name__)

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'username',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""NASA Earthdata account user name."""),
    arcGISDisplayName=_('NASA Earthdata user name'))

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'password',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""NASA Earthdata account password."""),
    arcGISDisplayName=_('NASA Earthdata password'))

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'queryParams',
    typeMetadata=DictionaryTypeMetadata(keyType=UnicodeStringTypeMetadata(), valueType=UnicodeStringTypeMetadata()),
    description=_(
"""Dictionary of HTTP query parameters, as defined by the NASA Earthdata
Common Metadata Repository (CMR) API."""))

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'linkTitleRegEx',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Regular expression to check against link titles, to determine if the link
is to the desired type of resource. For example, to access OPeNDAP datasets,
use ``^opendap request url$`` when accessing OPeNDAP datasets. To access
netCDF datasets, ``^download.+\\.nc$`` will usually work. The regular
expression is case-insensitive."""))

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'queryableAttributes',
    typeMetadata=DatasetCollection.__init__.__doc__.Obj.GetArgumentByName('queryableAttributes').Type,
    description=DatasetCollection.__init__.__doc__.Obj.GetArgumentByName('queryableAttributes').Description)

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'timeout',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Number of seconds to wait for the server to respond before failing with a
timeout error.

If you also provide a Maximum Retry Time and it is larger than the timeout
value, the failed request will be retried automatically (with the same timeout
value) until it succeeds or the Maximum Retry Time has elapsed.

If you receive a timeout error you should investigate the server to determine
if it is malfunctioning or just slow. Check the Earthdata website to see if
NASA has posted a notice about the problem, or contact the NASA directly. If
the server just slow, increase the timeout value to a larger number, to give
the server more time to respond."""),
    arcGISDisplayName=_('Timeout value'),
    arcGISCategory=_('Network options'))

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'maxRetryTime',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Number of seconds to retry requests to the server before giving up.

Use this parameter to cope with transient failures. For example, you may find
that the server is rebooted nightly during a maintenance cycle. If you start a
long running operation and want it to run overnight without failing, set the
maximum retry time to a duration that is longer than the time that the server
is offline during the maintenance cycle.

To maximize performance while minimizing load during failure situations,
retries are scheduled with progressive delays:

* The first retry is issued immediately.

* Then, so long as fewer than 10 seconds have elapsed since the original
  request was issued, retries are issued every second.

* After that, retries are issued every 30 seconds until the maximum retry time
  is reached or the request succeeds.

"""),
    arcGISDisplayName=_('Maximum retry time'),
    arcGISCategory=_('Network options'))

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'cacheDirectory',
    typeMetadata=DirectoryTypeMetadata(canBeNone=True),
    description=_(
"""Directory for caching local copies of downloaded data. A cache directory is
optional but highly recommended if you plan to repeatedly access data for the
same range of dates.

When data are requested, the cache directory will be checked for data that was
downloaded and cached during prior requests. If cached data exists that can
fulfill part of the current request, the request will be serviced by reading
from cache files rather than downloading from the server. If the entire
request can be serviced from the cache, the server will not be accessed at all
and the request will be completed extremely quickly. Any parts of the request
that cannot be serviced from the cache will be downloaded from the server and
added to the cache, speeding up future requests for the same data.

If you use a cache directory, be aware of these common pitfalls:

* The caching algorithm permits the cache to grow to infinite size and never
  deletes any cached data. If you access a large amount of data (e.g. an entire
  20 terabyte collection of satellite images) it will all be added to the
  cache. Be careful that you do not fill up your hard disk. To mitigate this,
  manually delete the entire cache or selected directories or files within it.

* The caching algorithm stores data in uncompressed files, so that subsets of
  those files may be quickly accessed. To save space on your hard disk, you
  can enable compression of the cache directory using the operating system. On
  Windows, right click on the directory in Windows Explorer, select
  Properties, click Advanced, and enable "Compress contents to save disk
  space".

* The caching algorithm cannot detect when portions of a dataset have been
  replaced on the server, thereby making the cached data obsolete. Thus, if a
  data provider republishes a dataset with improved data values, the caching
  algorithm will continue to use the old, obsolete values. To mitigate this,
  you should monitor when data providers reprocess their datasets, and delete
  the cached files when they become obsolete.

"""),
    arcGISDisplayName=_('Cache directory'),
    arcGISCategory=_('Network options'))

AddArgumentMetadata(CMRGranuleSearcher.__init__, 'metadataCacheLifetime',
    typeMetadata=FloatTypeMetadata(canBeNone=True, minValue=1.),
    description=_(
"""Maximum amount of time, in seconds, that granule metadata downloaded from
the NASA Earthdata Common Metadata Repository (CMR) will be cached.

Downloading metadata from the NASA Earthdata CMR can be slow. If this
parameter and a cache directory are both provided, when the CMR is queried for
all granule metadata for a given collection_concept_id, the downloaded
metadata will be cached in the directory for this amount of time. During this
period, the cached metadata will be accessed instead of the server, which can
greatly speed up processing involving NASA Earthdata granules. However, if new
datasets are stored in the CMR, they will not be discovered until the cached
metadata has expired.

If this parameter is not provided (the default), then granule metadata will
not be cached."""),
    arcGISDisplayName=_('Metadata cache lifetime'),
    arcGISCategory=_('Network options'))

AddResultMetadata(CMRGranuleSearcher.__init__, 'collection',
    typeMetadata=ClassInstanceTypeMetadata(cls=CMRGranuleSearcher),
    description=_('%s instance.') % CMRGranuleSearcher.__name__)


######################################################################################################
# This module is not meant to be imported directly. Import GeoEco.DataProducts.NASA.Earthdata instead.
######################################################################################################

__all__ = []
