# SequenceMetadata.py - Metadata for classes defined in Sequence.py.
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
# Metadata: SequenceTypeMetadata class
###############################################################################

AddClassMetadata('SequenceTypeMetadata', module=__package__, shortDescription=_('Base class for metadata classes that describe the values that are sequences, such as lists and tuples.'))


###############################################################################
# Metadata: ListTypeMetadata class
###############################################################################

AddClassMetadata('ListTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a mutable sequence of items may be provided, represented in Python by a ``list`` instance.'))

###############################################################################
# Metadata: TupleTypeMetadata class
###############################################################################

AddClassMetadata('TupleTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that an immutable sequence of items may be provided, represented in Python by a ``tuple`` instance.'))


###############################################################################
# Metadata: DictionaryTypeMetadata class
###############################################################################

AddClassMetadata('DictionaryTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a dictionary that maps keys to values may be provided, represented in Python by a ``dict`` instance.'))

###############################################################################
# Metadata: ListTableTypeMetadata class
###############################################################################

AddClassMetadata('ListTableTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a list of table rows may be provided, where each row is a list of cell values.'))

__all__ = []
