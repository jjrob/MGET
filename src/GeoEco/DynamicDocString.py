# DynamicDocString.py - Provides the DynamicDocString class, which is used by
# classes in the GeoEco Python package to store metadata within the classes'
# __doc__ attributes.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import types


class DynamicDocString(str):

    def __init__(self, obj=None):
        self.Obj = obj

    def _GetObj(self):
        return self._Obj
    
    def _SetObj(self, value):
        self._Obj = value

    Obj = property(_GetObj, _SetObj)

    def __getattribute__(self, name):
        assert isinstance(name, str)
        if name == 'Obj' or name == '_Obj' or name == '_GetObj' or name == '_SetObj' or name.startswith('__'):
            return object.__getattribute__(self, name)
        return getattr(str(self._Obj), name)

    # Python always calls __getattribute__ to obtain normal str functions such
    # as upper. This allows our __getattribute__ to expose these as if we were
    # a str ourself. But Python does NOT appear to call __getattribute__ to
    # obtain "magic" functions such as __eq__ or __getslice__. So we can't use
    # __getattribute__ to forward these calls to str(self._Obj).__eq__,
    # str(self._Obj).__getslice__, and so on. We have to create our own
    # versions that just call through to str(self._Obj). This is unfortunate
    # because if new versions of Python add new magic methods, we have to add
    # them here if we wish to remain a perfect replication of str.
    #
    # Note: This situation has has nothing to do with the fact that the if
    # statement preceding this comment includes the OR clause
    # "name.startswith('__')". That OR clause was added to prevent infinite
    # recusion that occurred when I discovered that __getattribute__ IS called
    # to obtain the __objclass__ attribute. Somehow Python treats this
    # attribute different than the others (such as __add__, __eq__, etc).

    def __add__(self, other):
        return str(self._Obj).__add__(other)

    def __contains__(self, other):
        return str(self._Obj).__contains__(other)

    def __doc__(self):
        return str(self._Obj).__doc__()

    def __eq__(self, other):
        return str(self._Obj).__eq__(other)

    def __format__(self, format_spec):
        return str(self._Obj).__format__(format_spec)

    def __ge__(self, other):
        return str(self._Obj).__ge__(other)

    def __getitem__(self, key):
        return str(self._Obj).__getitem__(key)

    def __getnewargs__(self):
        raise NotImplementedError('DynamicDocString does not currently support pickling.')

    def __getslice__(self, start, end):
        return str(self._Obj).__getslice__(start, end)

    def __gt__(self, other):
        return str(self._Obj).__gt__(other)

    def __hash__(self):
        raise NotImplementedError('DynamicDocString is not hashable because it is mutable. DynamicDocString cannot serve as a dictionary key.')

    def __iter__(self):
        return str(self._Obj).__iter__()

    def __le__(self, other):
        return str(self._Obj).__le__(other)

    def __len__(self):
        return str(self._Obj).__len__()

    def __lt__(self, other):
        return str(self._Obj).__lt__(other)

    def __mod__(self, other):
        return str(self._Obj).__mod__(other)

    def __mul__(self, other):
        return str(self._Obj).__mul__(other)

    def __ne__(self, other):
        return str(self._Obj).__ne__(other)

    def __reduce__(self):
        raise NotImplementedError('DynamicDocString does not currently support pickling.')

    def __reduce_ex__(self, protocol):
        raise NotImplementedError('DynamicDocString does not currently support pickling.')

    def __radd__(self, other):
        return other.__add__(str(self._Obj))        # str does not define __radd__ but we cannot be concatenated with other strings unless we do.

    def __repr__(self):
        return str(self._Obj).__repr__()

    def __rmod__(self, other):
        return str(self._Obj).__rmod__(other)

    def __rmul__(self, other):
        return str(self._Obj).__rmul__(other)

    def __str__(self):
        return str(self._Obj)


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['DynamicDocString']
