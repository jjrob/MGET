# _BaseMetadata.py - Metadata for classes defined in _Base.py.
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
# Metadata: TypeMetadata class
###############################################################################

AddClassMetadata('TypeMetadata', module=__package__, shortDescription=_('Base class for metadata classes that describe the values that class properties and method arguments and return values can take.'))


###############################################################################
# Metadata: AnyObjectTypeMetadata class
###############################################################################

AddClassMetadata('AnyObjectTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that any Python object may be provided.'))


###############################################################################
# Metadata: NoneTypeMetadata class
###############################################################################

AddClassMetadata('NoneTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that no value may be provided, represented in Python by ``None``.'))


###############################################################################
# Metadata: ClassTypeMetadata class
###############################################################################

AddClassMetadata('ClassTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a Python class, but not an instance of it, may be provided.'))


###############################################################################
# Metadata: ClassInstanceTypeMetadata class
###############################################################################

AddClassMetadata('ClassInstanceTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that an instance of a Python class, but not the class itself, may be provided.'))


###############################################################################
# Metadata: ClassOrClassInstanceTypeMetadata class
###############################################################################

AddClassMetadata('ClassOrClassInstanceTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a Python class or its instance may be provided.'))


###############################################################################
# Metadata: BooleanTypeMetadata class
###############################################################################

AddClassMetadata('BooleanTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a Boolean may be provided, represented in Python by a ``bool`` instance.'))


###############################################################################
# Metadata: DateTimeTypeMetadata class
###############################################################################

AddClassMetadata('DateTimeTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a date and time may be provided, represented in Python by a ``datetime.datetime`` instance.'))


###############################################################################
# Metadata: FloatTypeMetadata class
###############################################################################

AddClassMetadata('FloatTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a 64-bit floating point number may be provided, represented in Python by a ``float`` instance.'))


###############################################################################
# Metadata: IntegerTypeMetadata class
###############################################################################

AddClassMetadata('IntegerTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a signed integer may be provided, represented in Python by an ``int`` instance.'))


###############################################################################
# Metadata: UnicodeStringTypeMetadata class
###############################################################################

AddClassMetadata('UnicodeStringTypeMetadata', module=__package__, shortDescription=_('Metadata indicating that a Unicode string may be provided, represented in Python by an ``str`` instance.'))


###############################################################################
# Export nothing from this module
###############################################################################

__all__ = []
