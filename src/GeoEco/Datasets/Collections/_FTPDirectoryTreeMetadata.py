# _FTPDirectoryTreeMetadata.py - Metadata for classes defined in
# _FTPDirectoryTree.py.
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

from .._CollectibleObject import CollectibleObject
from ._DatasetCollectionTree import DatasetCollectionTree
from ._FTPDirectoryTree import FTPDirectoryTree


###############################################################################
# Metadata: FTPDirectoryTree class
###############################################################################

AddClassMetadata(FTPDirectoryTree,
    module=__package__,
    shortDescription=_('A :class:`DatasetCollectionTree` representing a directory on an FTP server.'))

# Public properties

AddPropertyMetadata(FTPDirectoryTree.DatasetType,
    typeMetadata=ClassTypeMetadata(cls=CollectibleObject),
    shortDescription=_('The type of :class:`~GeoEco.Datasets.CollectibleObject`\\ s contained by this :class:`~GeoEco.Datasets.Collections.FTPDirectoryTree`.'),
    longDescription=_(
"""If this type is a :class:`~GeoEco.Datasets.Dataset`, instances of it will
be constructed and returned when :func:`QueryDatasets` is called. If it is a
:class:`~GeoEco.Datasets.DatasetCollection`, instances will be constructed and
themselves queried, and the resulting :class:`~GeoEco.Datasets.Dataset`
instances will then be returned."""))

AddPropertyMetadata(FTPDirectoryTree.Host,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Hostname or IP address of the FTP server.'))

AddPropertyMetadata(FTPDirectoryTree.Port,
    typeMetadata=IntegerTypeMetadata(minValue=1),
    shortDescription=_('Port number of the FTP server.'))

AddPropertyMetadata(FTPDirectoryTree.User,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('User name for accessing the FTP server.'))

AddPropertyMetadata(FTPDirectoryTree.Password,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_('Password for accessing the FTP server.'))

AddPropertyMetadata(FTPDirectoryTree.Path,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1),
    shortDescription=_("Root directory of this tree on the FTP server. May be an absolute or relative path. Use ``/`` as the separator."))

AddPropertyMetadata(FTPDirectoryTree.CacheTree,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_('If True, the contents of the tree will be cached when it is first accessed, to improve performance on future accesses. If False, the contents will be obtained each time the tree is accessed.'))

# Public constructor: FTPDirectoryTree.__init__

AddMethodMetadata(FTPDirectoryTree.__init__,
    shortDescription=_('FTPDirectoryTree constructor.'))

AddArgumentMetadata(FTPDirectoryTree.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=FTPDirectoryTree),
    description=_(':class:`%s` instance.') % FTPDirectoryTree.__name__)

AddArgumentMetadata(FTPDirectoryTree.__init__, 'datasetType',
    typeMetadata=FTPDirectoryTree.DatasetType.__doc__.Obj.Type,
    description=FTPDirectoryTree.DatasetType.__doc__.Obj.ShortDescription)

AddArgumentMetadata(FTPDirectoryTree.__init__, 'host',
    typeMetadata=FTPDirectoryTree.Host.__doc__.Obj.Type,
    description=FTPDirectoryTree.Host.__doc__.Obj.ShortDescription)

AddArgumentMetadata(FTPDirectoryTree.__init__, 'port',
    typeMetadata=FTPDirectoryTree.Port.__doc__.Obj.Type,
    description=FTPDirectoryTree.Port.__doc__.Obj.ShortDescription)

AddArgumentMetadata(FTPDirectoryTree.__init__, 'user',
    typeMetadata=FTPDirectoryTree.User.__doc__.Obj.Type,
    description=FTPDirectoryTree.User.__doc__.Obj.ShortDescription)

AddArgumentMetadata(FTPDirectoryTree.__init__, 'password',
    typeMetadata=FTPDirectoryTree.Password.__doc__.Obj.Type,
    description=FTPDirectoryTree.Password.__doc__.Obj.ShortDescription)

AddArgumentMetadata(FTPDirectoryTree.__init__, 'path',
    typeMetadata=FTPDirectoryTree.Path.__doc__.Obj.Type,
    description=FTPDirectoryTree.Path.__doc__.Obj.ShortDescription)

AddArgumentMetadata(FTPDirectoryTree.__init__, 'timeout',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Number of seconds to wait for the server to respond before failing with a
timeout error.

If you also provide a maximum retry time and it is larger than the timeout
value, the failed request will be retried automatically (with the same timout
value) until it succeeds or the maximum retry time has elapsed.

If you receive a timeout error you should investigate the server to determine
if it is malfunctioning or just slow. Check the server's website to see if the
operator has posted a notice about the problem, or contact the operator
directly. If the server just slow, increase the timeout value to a larger
number, to give the server more time to respond.

"""))

AddArgumentMetadata(FTPDirectoryTree.__init__, 'maxRetryTime',
    typeMetadata=IntegerTypeMetadata(minValue=1, canBeNone=True),
    description=_(
"""Number of seconds to retry requests to the server before giving up.

Use this parameter to cope with a server that experiences transient failures.
For example, some servers are rebooted as part of nightly maintenance cycles.
If you start a long running operation and want it to run overnight without
failing, set the maximum retry time to a duration that is longer than the time
that the server is offline during the maintenance cycle.

To maximize performance while minimizing load during failure situations,
retries are scheduled with progressive delays:

* The first retry is issued immediately.

* Then, so long as fewer than 15 seconds have elapsed since the original
  request was issued, retries are issued every second.

* Then, so long as fewer than 60 seconds have elapsed since the original
  request was issued, retries are issued every 5 seconds.

* After that, retries are issued every 30 seconds until the maximum retry
  time is reached or the request succeeds.

"""))

CopyArgumentMetadata(DatasetCollectionTree.__init__, 'pathParsingExpressions', FTPDirectoryTree.__init__, 'pathParsingExpressions')

AddArgumentMetadata(FTPDirectoryTree.__init__, 'cacheTree',
    typeMetadata=FTPDirectoryTree.CacheTree.__doc__.Obj.Type,
    description=FTPDirectoryTree.CacheTree.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(DatasetCollectionTree.__init__, 'queryableAttributes', FTPDirectoryTree.__init__, 'queryableAttributes')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'queryableAttributeValues', FTPDirectoryTree.__init__, 'queryableAttributeValues')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'lazyPropertyValues', FTPDirectoryTree.__init__, 'lazyPropertyValues')
CopyArgumentMetadata(DatasetCollectionTree.__init__, 'cacheDirectory', FTPDirectoryTree.__init__, 'cacheDirectory')

AddResultMetadata(FTPDirectoryTree.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=FTPDirectoryTree),
    description=_(':class:`%s` instance.') % FTPDirectoryTree.__name__)


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
