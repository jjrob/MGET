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

AddClassMetadata('AnyObjectTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value may be any Python object.'))


###############################################################################
# Metadata: NoneTypeMetadata class
###############################################################################

AddClassMetadata('NoneTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be :py:data:`None`.'))


###############################################################################
# Metadata: ClassTypeMetadata class
###############################################################################

AddClassMetadata('ClassTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value may be a Python class, but not an instance of it.'))


###############################################################################
# Metadata: ClassInstanceTypeMetadata class
###############################################################################

AddClassMetadata('ClassInstanceTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value may be an instance of a Python class, but not the class itself.'))


###############################################################################
# Metadata: ClassOrClassInstanceTypeMetadata class
###############################################################################

AddClassMetadata('ClassOrClassInstanceTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value may be a Python class or its instance may be provided.'))


###############################################################################
# Metadata: BooleanTypeMetadata class
###############################################################################

AddClassMetadata('BooleanTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`bool`, a Boolean (true or false) value.'))


###############################################################################
# Metadata: DateTimeTypeMetadata class
###############################################################################

AddClassMetadata('DateTimeTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`datetime.datetime`, a date with a time.'))


###############################################################################
# Metadata: FloatTypeMetadata class
###############################################################################

AddClassMetadata('FloatTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`float`, a 64-bit floating point number.'))


###############################################################################
# Metadata: IntegerTypeMetadata class
###############################################################################

AddClassMetadata('IntegerTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be an :py:class:`int`, an integer.'))


###############################################################################
# Metadata: UnicodeStringTypeMetadata class
###############################################################################

AddClassMetadata('UnicodeStringTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str`, a Unicode string.'))


###############################################################################
# Metadata: UnicodeStringHiddenTypeMetadata class
###############################################################################

AddClassMetadata('UnicodeStringHiddenTypeMetadata', module=__package__, shortDescription=_('Metadata specifying that a value must be a :py:class:`str`, a Unicode string, that should not be displayed (e.g. because it is a password).'))


###############################################################################
# Export nothing from this module
###############################################################################

__all__ = []
