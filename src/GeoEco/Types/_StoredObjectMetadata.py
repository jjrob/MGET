# _StoredObjectMetadata.py - Metadata for classes defined in _StoredObject.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import AddClassMetadata


###############################################################################
# Metadata: StoredObjectTypeMetadata class
###############################################################################

AddClassMetadata('StoredObjectTypeMetadata', module=__package__, shortDescription=_('Base class for metadata classes that describe values representing stored objects such as files and directories.'))

###############################################################################
# Metadata: FileTypeMetadata class
###############################################################################

AddClassMetadata('FileTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is a path to a file.'))


###############################################################################
# Metadata: TextFileTypeMetadata class
###############################################################################

AddClassMetadata('TextFileTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is a path to a text file that ArcGIS recognizes as a tabular format (e.g. a .CSV).'))

###############################################################################
# Metadata: DirectoryTypeMetadata class
###############################################################################

AddClassMetadata('DirectoryTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str` that is a path to a directory.'))

__all__ = []
