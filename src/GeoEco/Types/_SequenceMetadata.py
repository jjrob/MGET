# _SequenceMetadata.py - Metadata for classes defined in _Sequence.py.
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

AddClassMetadata('ListTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`list`, a mutable sequence of items.'))

###############################################################################
# Metadata: TupleTypeMetadata class
###############################################################################

AddClassMetadata('TupleTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`tuple`, an immutable sequence of items.'))


###############################################################################
# Metadata: DictionaryTypeMetadata class
###############################################################################

AddClassMetadata('DictionaryTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`dict`, a dictionary that maps keys to values.'))

###############################################################################
# Metadata: ListTableTypeMetadata class
###############################################################################

AddClassMetadata('ListTableTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`list` of :py:class:`list`, where the outer list represents a table, and each inner list a row of values.'))

__all__ = []
