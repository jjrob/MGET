# Exceptions.py - Defines the base class for custom exceptions defined by
# modules of the GeoEco Python package.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from .DynamicDocString import DynamicDocString
from .Internationalization import _


class GeoEcoError(Exception):
    __doc__ = DynamicDocString()

    def __init__(self, message):
        self.__doc__.Obj.ValidateMethodInvocation()
        self.Message = message

    def __str__(self):
        return self.Message


###############################################################################
# Metadata: module
###############################################################################

from .Metadata import *
from .Types import *

AddModuleMetadata(shortDescription=_('Defines the base class for all exceptions defined by the GeoEco package.'))

###############################################################################
# Metadata: GeoEcoError class
###############################################################################

AddClassMetadata(GeoEcoError,
    shortDescription=_('Base class for all exceptions defined by the GeoEco package.'))

# Constructor

AddMethodMetadata(GeoEcoError.__init__,
    shortDescription=_('Constructs a new %s instance.') % GeoEcoError.__name__)

AddArgumentMetadata(GeoEcoError.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GeoEcoError),
    description=_(':class:`%s` instance.') % GeoEcoError.__name__)

AddArgumentMetadata(GeoEcoError.__init__, 'message',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('The message to report.'))

AddResultMetadata(GeoEcoError.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=GeoEcoError),
    description=_('New :class:`%s` instance.') % GeoEcoError.__name__)


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['GeoEcoError']
