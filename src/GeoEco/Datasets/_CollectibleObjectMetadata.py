# _CollectibleObjectMetadata.py - Metadata for classes defined in
# _CollectibleObject.py.
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

from ._CollectibleObject import CollectibleObject, QueryableAttribute
from ._DatasetCollection import DatasetCollection


###############################################################################
# Metadata: CollectibleObject class
###############################################################################

AddClassMetadata(CollectibleObject, 
	module=__package__,
    shortDescription=_('Base class for objects that can appear in a :class:`DatasetCollection`, namely :class:`Dataset` and :class:`DatasetCollection`.'),
    longDescription=_(
"""A :class:`CollectibleObject` typically represents a tabular or gridded
dataset such as a table, shapefile, raster, netCDF variable, or OPeNDAP grid.
:class:`CollectibleObject`\\ s are usually queried from a 
:class:`DatasetCollection`, which is referred to as the parent of the
:class:`CollectibleObject`\\ s within it. :class:`CollectibleObject`\\ s can
also be defined independently of a :class:`DatasetCollection`, and have no
parent. However, :class:`CollectibleObject` is a base class that should not be
instantiated directly; instead, users should instantiate one of the many
derived classes representing the type of dataset they're interested in.

A :class:`DatasetCollection` is also itself a :class:`CollectibleObject` and
can be contained within another :class:`DatasetCollection`. For example, a
:class:`DatasetCollection` representing a netCDF file, which contains
:class:`CollectibleObject`\\ s representing netCDF variables, may be contained
by a :class:`DatasetCollection` representing a file system directory tree or
an FTP server.

:class:`CollectibleObject`\\ s have *queryable attributes*, which are metadata
values used to retrieve a subset of :class:`CollectibleObject`\\ s from a
:class:`DatasetCollection` by calling :func:`~DatasetCollection.QueryDatasets`
and supplying a SQL-like expression. The values of queryable attributes are
often extracted from file names or other dataset characteristics related to
how they are organized or stored in their original source (which is
represented by the :class:`DatasetCollection`).

The queryable attribute definitions for a :class:`CollectibleObject` can be
obtained with :func:`~CollectibleObject.GetAllQueryableAttributes` or
retrieved individually by name with
:func:`~CollectibleObject.GetQueryableAttribute`. The queryable attribute
values can be retrieved with
:func:`~CollectibleObject.GetQueryableAttributeValue`.

Queryable attributes defined for a :class:`DatasetCollection` are also
implicitly defined for any child :class:`CollectibleObject`\\ s that they
contain (including child :class:`DatasetCollection`\\ s). The children will
also inherit the values of their parent's queryable attributes, unless the
children define their own values (these override the parent's). 

:class:`CollectibleObject`\\ s also have *lazy properties*, which are
additional metadata values that are often not related to how datasets are
organized or stored but are needed for certain tasks. Different types of
:class:`CollectibleObject`\\ s have different lazy properties, and it is
generally not possible to enumerate them; callers are expected to know the
names of the lazy properties they are interested in ahead of time.

Lazy properties may be expensive to retrieve; examples include the dimensions
or data type of a netCDF variable, which might not be known until the netCDF
file is downloaded and opened. The various types of
:class:`CollectibleObject`\\ s know how to retrieve them but typically defer
this until :func:`~CollectibleObject.GetLazyPropertyValue` is called. To allow
this potentially slow operation to be avoided entirely when the values are
known *a priori*, the caller can supply lazy property values to the
:class:`CollectibleObject` constructor or set them after construction with 
:func:`~CollectibleObject.SetLazyPropertyValue`. For example, if the caller
knows the dimensions, data type, and geospatial characteristics of a netCDF
variable, these can be supplied when the
:class:`CollectibleObject`\\ s are instantiated, so that they can be utilized
by various functions that need to know these values without actually having to
download the netCDF files.

The values of lazy properties can also be derived from queryable attributes.
Please see the :class:`QueryableAttribute` documentation for more
information."""))

# Public properties

AddPropertyMetadata(CollectibleObject.DisplayName,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Informal name of this object, suitable to be displayed to the user.'),
    isExposedToPythonCallers=True)

AddPropertyMetadata(CollectibleObject.ParentCollection,
    typeMetadata=ClassInstanceTypeMetadata(cls=DatasetCollection, canBeNone=True),
    shortDescription=_('Parent :class:`~GeoEco.Datasets.DatasetCollection` that this object is part of (if any).'),
    isExposedToPythonCallers=True)

# Public method: CollectibleObject.GetQueryableAttribute

AddMethodMetadata(CollectibleObject.GetQueryableAttribute,
    shortDescription=_('Returns the queryable attribute with the specified name.'),
    isExposedToPythonCallers=True)

AddArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=CollectibleObject),
    description=_(':class:`%s` instance.') % CollectibleObject.__name__)

AddArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    description=_(
"""Name of the queryable attribute to return."""))

AddResultMetadata(CollectibleObject.GetQueryableAttribute, 'attr',
    typeMetadata=ClassInstanceTypeMetadata(cls=QueryableAttribute, canBeNone=True),
    description=_(
""":class:`QueryableAttribute` instance with the specified name. If one is not
defined for this object, the chain of parent :class:`DatasetCollection`\\ s
(if any) will be searched, starting with the immediate parent. If one is still
not found, :py:data:`None` will be returned."""))

# Public method: CollectibleObject.GetQueryableAttributesWithDataType

AddMethodMetadata(CollectibleObject.GetQueryableAttributesWithDataType,
    shortDescription=_('Returns a list queryable attributes having the specified data type.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.GetQueryableAttributesWithDataType, 'self')

AddArgumentMetadata(CollectibleObject.GetQueryableAttributesWithDataType, 'typeMetadata',
    typeMetadata=ClassTypeMetadata(cls=TypeMetadata),
    description=_(
"""Subclass of :class:`~GeoEco.Metadata.TypeMetadata` that indicates the desired data type."""))

AddResultMetadata(CollectibleObject.GetQueryableAttributesWithDataType, 'attrList',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=QueryableAttribute)),
    description=_(
""":py:class:`list` of :class:`QueryableAttribute` instances having the
specified data type. This :class:`CollectibleObject` and all of its parent
:class:`DatasetCollection`\\ s will be searched for matching instances, and
all will be returned. If no matching instances are found, the list will be
empty."""))

# Public method: CollectibleObject.GetAllQueryableAttributes

AddMethodMetadata(CollectibleObject.GetAllQueryableAttributes,
    shortDescription=_('Returns a list of all queryable attributes.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.GetAllQueryableAttributes, 'self')

AddResultMetadata(CollectibleObject.GetAllQueryableAttributes, 'attrList',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=QueryableAttribute)),
    description=_(
""":py:class:`list` of :class:`QueryableAttribute` instances defined for this
object and all of its parent :class:`DatasetCollection`\\ s. If no instances
have been defined for it or any of its parents, the list will be empty."""))

# Public method: CollectibleObject.GetQueryableAttributeValue

AddMethodMetadata(CollectibleObject.GetQueryableAttributeValue,
    shortDescription=_('Returns the value of the queryable attribute with the specified name.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.GetQueryableAttributeValue, 'self')

AddArgumentMetadata(CollectibleObject.GetQueryableAttributeValue, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    description=_(
"""Name of the queryable attribute to return the value of."""))

AddResultMetadata(CollectibleObject.GetQueryableAttributeValue, 'value',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Value of the queryable attribute with the specified name. If one is not
defined for this object, the chain of parent :class:`DatasetCollection`\\ s
(if any) will be searched, starting with the immediate parent. If one is still
not found, :py:data:`None` will be returned.

:py:data:`None` will also be returned if a queryable attribute is found but
the value of it is :py:data:`None`. To determine whether :py:data:`None` was
returned because the attribute's value was :py:data:`None` or because the
attribute does not exist, use
:func:`~CollectibleObject.GetQueryableAttribute` to determine if the queryable
attribute exists."""))

# Public method: CollectibleObject.GetLazyPropertyValue

AddMethodMetadata(CollectibleObject.GetLazyPropertyValue,
    shortDescription=_('Returns the value of the lazy property with the specified name.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.GetLazyPropertyValue, 'self')

AddArgumentMetadata(CollectibleObject.GetLazyPropertyValue, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    description=_(
"""Name of the lazy property to return the value of."""))

AddArgumentMetadata(CollectibleObject.GetLazyPropertyValue, 'allowPhysicalValue',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True and the value of the lazy property is not currently known, it will
be retrieved from the physical source of the data. For example, if getting the
value requires downloading a remote file and opening it, the file will be
downloaded and opened, a potentially expensive and slow operation. If False
and the value of the lazy property is not currently known, it will not be
retrieved and :py:data:`None` will be returned instead."""))

AddResultMetadata(CollectibleObject.GetLazyPropertyValue, 'value',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Value of the lazy property with the specified name, or :py:data:`None` if there is no
lazy property with that name, or if it cannot be retrieved from the physical
source of the data because `allowPhysicalValue` was False."""))

# Public method: CollectibleObject.SetLazyPropertyValue

AddMethodMetadata(CollectibleObject.SetLazyPropertyValue,
    shortDescription=_('Sets the lazy property with the specified name to the specified value.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.SetLazyPropertyValue, 'self')

AddArgumentMetadata(CollectibleObject.SetLazyPropertyValue, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    description=_(
"""Name of the lazy property to set."""))

AddArgumentMetadata(CollectibleObject.SetLazyPropertyValue, 'value',
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    description=_(
"""Value of the lazy property. In general, lazy properties cannot have the
value of :py:data:`None`. If :py:data:`None` is provided here, it will
effectively unset the lazy property, restoring it to the state of not having a
value."""))

# Public method: CollectibleObject.DeleteLazyPropertyValue

AddMethodMetadata(CollectibleObject.DeleteLazyPropertyValue,
    shortDescription=_('Deletes the lazy property with the specified name.'),
    longDescription=_('Use this function to force a lazy property to be reloaded from the underlying physical source of the data.'),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.DeleteLazyPropertyValue, 'self')

AddArgumentMetadata(CollectibleObject.DeleteLazyPropertyValue, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    description=_(
"""Name of the lazy property to delete."""))

# Public method: CollectibleObject.HasLazyPropertyValue

AddMethodMetadata(CollectibleObject.HasLazyPropertyValue,
    shortDescription=_('Returns True if the specified lazy property has a value.'),
    longDescription=_(
"""This method is equivalent to:

.. code-block:: python

    obj.GetLazyPropertyValue(name, allowPhysicalValue) is not None
"""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.HasLazyPropertyValue, 'self')

AddArgumentMetadata(CollectibleObject.HasLazyPropertyValue, 'name',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    description=_(
"""Name of the lazy property to check."""))

AddArgumentMetadata(CollectibleObject.HasLazyPropertyValue, 'allowPhysicalValue',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True and the value of the lazy property is not currently known but might
be available from the physical source of the data, the physical source will be
checked for it, a potentially expensive and slow operation. If False and the
value of the lazy property is not currently known, the physical source will
not be checked and False will be returned."""))

AddResultMetadata(CollectibleObject.HasLazyPropertyValue, 'value',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""True if a value is known for the lazy property. False if there is no value
for it, or there might be a value available from the physical source of the
data but `allowPhysicalValue` was False so it could not be checked."""))

# Public method: CollectibleObject.Close

AddMethodMetadata(CollectibleObject.Close,
    shortDescription=_('Closes any open files or connections associated with this object and releases any other resources allocated to access it.'),
    longDescription=_(
"""It is OK to call :func:`Close` after it has already been called. If nothing
is open, :func:`Close` will quickly and silently do nothing.

The :class:`CollectibleObject` finalizer :py:meth:`~object.__del__` always
calls :func:`Close`, so that under normal circumstances, :func:`Close` will be
called automatically by Python when the :class:`CollectibleObject` is about to
be destroyed. :class:`CollectibleObject` also uses :py:mod:`atexit` to
register itself to call :func:`Close` on all still-allocated instances when
Python exits. However, this procedure is subject to the various caveats
documented by :py:mod:`atexit`, so under unusual circumstances it is possible
that :func:`Close` will not be called, and it will be up to lower-level
libraries and the operating system itself to clean up open resources."""),
    isExposedToPythonCallers=True)

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.Close, 'self')

# Public method: CollectibleObject.TestCapability

AddMethodMetadata(CollectibleObject.TestCapability,
    shortDescription=_('Tests whether a capability is supported by this class or an instance of it.'),
    longDescription=_(
"""If called on an instance, this method tests whether the underlying
object represented by the instance supports the capability.

If called on the class, this method tests whether at least one
instance can possibly support the capability. If no instances can ever
support the capability, this method will indicate that the capability
is not supported."""),
    isExposedToPythonCallers=True)

AddArgumentMetadata(CollectibleObject.TestCapability, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=CollectibleObject),
    description=_(':class:`%s` or an instance of it.') % CollectibleObject.__name__)

AddArgumentMetadata(CollectibleObject.TestCapability, 'capability',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True),
    description=_("""Capability to test."""))

AddResultMetadata(CollectibleObject.TestCapability, 'error',
    typeMetadata=ClassInstanceTypeMetadata(cls=Exception, canBeNone=True),
    description=_(
""":py:data:`None` if the capability is supported, or an instance of :class:`Exception`
if it is not supported. The string representation of the Exception explains
why the capability is not supported (if possible) in the context of when it
might be needed."""))

# Private constructor: CollectibleObject.__init__

AddMethodMetadata(CollectibleObject.__init__,
    shortDescription=_('CollectibleObject constructor. Not intended to be called directly. Only intended to be called from derived class constructors.'))

CopyArgumentMetadata(CollectibleObject.GetQueryableAttribute, 'self', CollectibleObject.__init__, 'self')

AddArgumentMetadata(CollectibleObject.__init__, 'parentCollection',
    typeMetadata=CollectibleObject.ParentCollection.__doc__.Obj.Type,
    description=CollectibleObject.ParentCollection.__doc__.Obj.ShortDescription)

AddArgumentMetadata(CollectibleObject.__init__, 'queryableAttributes',
    typeMetadata=TupleTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=QueryableAttribute), canBeNone=True),
    description=_('Queryable attributes defined for this object.'))

AddArgumentMetadata(CollectibleObject.__init__, 'queryableAttributeValues',
    typeMetadata=DictionaryTypeMetadata(keyType=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'), valueType=AnyObjectTypeMetadata(canBeNone=True), canBeNone=True),
    description=_('Values of the queryable attributes, expressed as a dictionary mapping the case-insensitive names of queryable attributes to their values.'))

AddArgumentMetadata(CollectibleObject.__init__, 'lazyPropertyValues',
    typeMetadata=DictionaryTypeMetadata(keyType=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'), valueType=AnyObjectTypeMetadata(canBeNone=True), canBeNone=True),
    description=_('Lazy properties to set when this object is constructed, expressed as a dictionary mapping the names of lazy properties to their values.'))

AddResultMetadata(CollectibleObject.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=CollectibleObject),
    description=_(':class:`%s` instance.') % CollectibleObject.__name__)

###############################################################################
# Metadata: QueryableAttribute class
###############################################################################

AddClassMetadata(QueryableAttribute,
	module=__package__,
    shortDescription=_('Describes an attribute of a :class:`CollectibleObject` that can be used to query it from a :class:`DatasetCollection`.'))

# Public properties

AddPropertyMetadata(QueryableAttribute.Name,
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    shortDescription=_("Case-insensitive formal name of this this queryable attribute."))

AddPropertyMetadata(QueryableAttribute.DisplayName,
    typeMetadata=UnicodeStringTypeMetadata(),
    shortDescription=_('Informal name of this queryable attribute to be displayed in user interfaces, log messages, and similar places.'))

AddPropertyMetadata(QueryableAttribute.DataType,
    typeMetadata=ClassInstanceTypeMetadata(cls=TypeMetadata),
    shortDescription=_(':class:`~GeoEco.Metadata.TypeMetadata` instance defining the data type of this queryable attribute.'))

AddPropertyMetadata(QueryableAttribute.DerivedLazyDatasetProps,
    typeMetadata=DictionaryTypeMetadata(keyType=AnyObjectTypeMetadata(canBeNone=True), valueType=DictionaryTypeMetadata(keyType=UnicodeStringTypeMetadata(minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'), valueType=AnyObjectTypeMetadata(canBeNone=True)), canBeNone=True),
    shortDescription=_('Dictionary mapping values of this queryable attribute to names and values of lazy properties to assign.'))

AddPropertyMetadata(QueryableAttribute.DerivedFromAttr,
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True, minLength=1, mustMatchRegEx='[a-zA-Z][a-zA-Z0-9_]+'),
    shortDescription=_('Name of another queryable attribute that this one is derived from.'))

AddPropertyMetadata(QueryableAttribute.DerivedValueMap,
    typeMetadata=DictionaryTypeMetadata(keyType=AnyObjectTypeMetadata(), valueType=AnyObjectTypeMetadata(), canBeNone=True),
    shortDescription=_('Dictionary mapping values of the attribute that this one is derived from to values to use for this attribute.'))

AddPropertyMetadata(QueryableAttribute.DerivedValueFunc,
    typeMetadata=AnyObjectTypeMetadata(canBeNone=True),
    shortDescription=_('Function (may be a lambda) or method that should be called to derive the value of this attribute from the one it is derived from.'))

# Public constructor: QueryableAttribute.__init__

AddMethodMetadata(QueryableAttribute.__init__,
    shortDescription=_('QueryableAttribute constructor.'))

AddArgumentMetadata(QueryableAttribute.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=QueryableAttribute),
    description=_(':class:`%s` instance.') % QueryableAttribute.__name__)

AddArgumentMetadata(QueryableAttribute.__init__, 'name',
    typeMetadata=QueryableAttribute.Name.__doc__.Obj.Type,
    description=QueryableAttribute.Name.__doc__.Obj.ShortDescription)

AddArgumentMetadata(QueryableAttribute.__init__, 'displayName',
    typeMetadata=QueryableAttribute.DisplayName.__doc__.Obj.Type,
    description=QueryableAttribute.DisplayName.__doc__.Obj.ShortDescription)

AddArgumentMetadata(QueryableAttribute.__init__, 'dataType',
    typeMetadata=QueryableAttribute.DataType.__doc__.Obj.Type,
    description=QueryableAttribute.DataType.__doc__.Obj.ShortDescription)

AddArgumentMetadata(QueryableAttribute.__init__, 'derivedLazyDatasetProps',
    typeMetadata=QueryableAttribute.DerivedLazyDatasetProps.__doc__.Obj.Type,
    description=QueryableAttribute.DerivedLazyDatasetProps.__doc__.Obj.ShortDescription)

AddArgumentMetadata(QueryableAttribute.__init__, 'derivedFromAttr',
    typeMetadata=QueryableAttribute.DerivedFromAttr.__doc__.Obj.Type,
    description=QueryableAttribute.DerivedFromAttr.__doc__.Obj.ShortDescription)

AddArgumentMetadata(QueryableAttribute.__init__, 'derivedValueMap',
    typeMetadata=QueryableAttribute.DerivedValueMap.__doc__.Obj.Type,
    description=QueryableAttribute.DerivedValueMap.__doc__.Obj.ShortDescription)

AddArgumentMetadata(QueryableAttribute.__init__, 'derivedValueFunc',
    typeMetadata=QueryableAttribute.DerivedValueFunc.__doc__.Obj.Type,
    description=QueryableAttribute.DerivedValueFunc.__doc__.Obj.ShortDescription)

AddResultMetadata(QueryableAttribute.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=QueryableAttribute),
    description=_(':class:`%s` instance.') % QueryableAttribute.__name__)


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
