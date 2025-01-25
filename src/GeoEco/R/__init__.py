# R/__init__.py - Classes that facilitate invoking R from Python.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_('Classes that facilitate invoking R from Python.'))

from ._RWorkerProcess import RWorkerProcess
from . import _RWorkerProcessMetadata

__all__ = ['RWorkerProcess']
