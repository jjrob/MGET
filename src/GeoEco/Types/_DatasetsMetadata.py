# _DatasetsMetadata.py - Metadata for classes defined in _Datasets.py.
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
# Metadata: TableFieldTypeMetadata class
###############################################################################

AddClassMetadata('TableFieldTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a field of a :class:`~GeoEco.Datasets.Dataset`.'))

__all__ = []
