# _DatasetMetadata.py - Metadata for classes defined in _Dataset.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ..Internationalization import _
from ..Metadata import *
from ..Types import *

from ._Dataset import Dataset


###############################################################################
# Metadata: Dataset class
###############################################################################

AddClassMetadata(Dataset,
	module=__package__,
    shortDescription=_('Base class for objects representing tabular and gridded datasets, principally :class:`Table` and :class:`Grid`.'),
    longDescription=_(
""":class:`Dataset` is a base class that should not be instantiated directly;
instead, users should instantiate one of the many derived classes representing
the type of dataset they're interested in."""))

# Public method: Dataset.ConvertSpatialReference

AddMethodMetadata(Dataset.ConvertSpatialReference,
    shortDescription=_('Converts a spatial reference from one format to another, such as an OGC WKT string to a Proj4 string.'),
    isExposedToPythonCallers=True)

AddArgumentMetadata(Dataset.ConvertSpatialReference, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Dataset),
    description=_(':class:`%s` or an instance of it.') % Dataset.__name__)

AddArgumentMetadata(Dataset.ConvertSpatialReference, 'srType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['WKT', 'ArcGIS', 'Proj4', 'Obj'], makeLowercase=True),
    description=_(
"""The type of spatial reference you are providing for `sr`:

* WKT - a WKT string in standard OGC format.

* ArcGIS - a WKT string in ESRI format, typically obtained from a dataset
  produced by ArcGIS. (The ESRI format differs from the OGC standard; various
  projections and parameters are named differently and certain nodes are not
  recognized. See the OSR documentation for more information.)

* Proj4 - a string in the format recognized by the Proj4 library.

* Obj - an instance of the :py:class:`osgeo.osr.SpatialReference` class.

"""))

AddArgumentMetadata(Dataset.ConvertSpatialReference, 'sr',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Spatial reference of the type specified by `srType`, or :py:data:`None`
for an "undefined" spatial reference."""))

AddArgumentMetadata(Dataset.ConvertSpatialReference, 'outputSRType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['WKT', 'ArcGIS', 'Proj4', 'Obj'], makeLowercase=True),
    description=_(
"""The type of spatial reference to return. The allowed values are the same as
for `srType`.

If `srType` and `outputSRType` are the same, a copy of the input spatial
reference will be returned. If they are ``'Obj'``, a deep copy of the input
:py:class:`osgeo.osr.SpatialReference` instance will be created by
initializing a new instance from the OGC WKT exported from the input instance.

If `sr` is :py:data:`None`, :py:data:`None` will be returned, except if
`outputSRType` is ``'ArcGIS'``, in which case the string
``'{B286C06B-0879-11D2-AACA-00C04FA33C20}'`` will be returned. ArcGIS uses
this string to represent the "Unknown" spatial reference.

"""))

AddResultMetadata(Dataset.ConvertSpatialReference, 'outputSR',
    typeMetadata=AnyObjectTypeMetadata(),
    description=_(
"""Spatial reference resulting from the conversion, either a string, an
:py:class:`osgeo.osr.SpatialReference` instance, or :py:data:`None`."""))

# Public method: Dataset.GetSpatialReference

AddMethodMetadata(Dataset.GetSpatialReference,
    shortDescription=_('Returns the spatial reference of this dataset.'),
    isExposedToPythonCallers=True)

AddArgumentMetadata(Dataset.GetSpatialReference, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=Dataset),
    description=_(':class:`%s` instance.') % Dataset.__name__)

AddArgumentMetadata(Dataset.GetSpatialReference, 'srType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['WKT', 'ArcGIS', 'Proj4', 'Obj'], makeLowercase=True),
    description=_(
"""Type of spatial reference that should be returned:

* WKT - a WKT string in standard OGC format.

* ArcGIS - a WKT string in ESRI format, typically obtained from
  a dataset produced by ArcGIS. (The ESRI format differs from the OGC
  standard; various projections and parameters are named differently
  and certain nodes are not recognized. See the OSR documentation for
  more information.)

* Proj4 - a string in the format recognized by the Proj4 library.

* Obj - an instance of the :py:class:`osgeo.osr.SpatialReference` class.

An :py:class:`osgeo.osr.SpatialReference` instance is stored internally. If
``'Obj'`` is requested, a reference to this instance is returned, not a copy
of it, allowing you to make changes to the internal instance. This behavior is
by design. Take care not to make changes unintentionally. Use
:func:`ConvertSpatialReference` to obtain a deep copy of the instance, if
needed.

If something other than ``'Obj'`` is requested, a string of the specified type
is exported from the internal :py:class:`osgeo.osr.SpatialReference` instance
and returned.

"""))

AddResultMetadata(Dataset.GetSpatialReference, 'sr',
    typeMetadata=AnyObjectTypeMetadata(),
    description=_(
"""Spatial reference of the requested type, either a string, an
:py:class:`osgeo.osr.SpatialReference` instance, or :py:data:`None`.

If the dataset does not support a spatial reference (e.g. it is a plain
table), or it does support a spatial reference but it has never been set,
:py:data:`None` will be returned, except if srType is ``'ArcGIS'``, in which
case the ``'{B286C06B-0879-11D2-AACA-00C04FA33C20}'`` will be returned.
ArcGIS uses this string to represent the "Unknown" spatial reference."""))

# Public method: Dataset.SetSpatialReference

AddMethodMetadata(Dataset.SetSpatialReference,
    shortDescription=_('Sets the spatial reference of this dataset.'),
    longDescription=_(
"""This method is similar in operation to the ArcGIS
:arcpy_management:`Define-Projection` geoprocessing tool; it changes the
spatial reference of the dataset without changing any of the data itself. The
change is not just made to the in-memory :class:`~GeoEco.Datasets.Dataset`
instance; it is also made to the underlying physical dataset itself. This
method is used mainly to fix datasets for which the spatial reference is
missing or mis-defined.

Not all datasets support setting the spatial reference. To determine if the
spatial reference can be set, 
use :func:`~GeoEco.Datasets.CollectibleObject.TestCapability` to test for the
``'SetSpatialReference'`` capability."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(Dataset.GetSpatialReference, 'self', Dataset.SetSpatialReference, 'self')

AddArgumentMetadata(Dataset.SetSpatialReference, 'srType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['WKT', 'ArcGIS', 'Proj4', 'Obj'], makeLowercase=True),
    description=_(
"""Type of spatial reference you are providing for the `sr` parameter.

The allowed values are:

* WKT - `sr` is a WKT string in standard OGC format.

* ArcGIS - `sr` is a WKT string in ESRI format, typically obtained from a
  dataset produced by ArcGIS. (The ESRI format differs from the OGC standard;
  various projections and parameters are named differently and certain nodes
  are not recognized. See the OSR documentation for more information.)

* Proj4 - `sr` is a string suitable for passing to the Proj4 utility.

* Obj - `sr` is an instance of the :py:class:`osgeo.osr.SpatialReference`
  class.

To set the spatial reference to unknown, set `srType` to ``'obj'`` and `sr` to
:py:data:`None`."""))

AddArgumentMetadata(Dataset.SetSpatialReference, 'sr',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_("Spatial reference for the dataset. To set the spatial reference to unknown, set `srType` to ``'obj'`` and `sr` to :py:data:`None`."))


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
