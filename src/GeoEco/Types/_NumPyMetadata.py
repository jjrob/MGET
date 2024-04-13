# _NumPyMetadata.py - Metadata for classes defined in _NumPy.py.
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
# Metadata: NumPyArrayTypeMetadata class
###############################################################################

AddClassMetadata('NumPyArrayTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :class:`numpy.ndarray`.'))

__all__ = []
