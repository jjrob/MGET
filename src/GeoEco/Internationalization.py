# Internationalization.py - Internationalization/localization infrastructure
# for the GeoEco Python package.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import locale
import gettext
import inspect
import os
import sys

def _InitializeTranslationsClass():

    # Build a list of languages, prioritized according to what the user might
    # want to view.

    languages = []

    # First use the current process-wide locale. If we're being called from a
    # language-aware application, it may have set the locale. If not, this
    # function will return None.
    
    lc = locale.getlocale()[0]
    if lc is not None:
        languages.append(lc)

    # Next try the default locale.
    
    lc = locale.getdefaultlocale()[0]
    if lc is not None:
        languages.append(lc)

    # Next search the environment variables that might specify languages. These
    # are typically only present on UNIX. locale.getdefaultlocale also searches
    # these but returns only the first one it finds. We want the others to be in
    # our list, so if the first one is not available, we'll fall back to the
    # others.

    for variable in ['LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG']:
        if variable in os.environ:
            value = os.environ[variable]
            languages.extend(value.split(':'))

    # Return the Translations instance.

    gettext.translation(domain='GeoEco',
                        localedir=os.path.join(os.path.dirname(inspect.getfile(sys.modules[__name__])), 'LanguageFiles'),
                        languages=languages,
                        fallback=True)

_Translations = None
try:
    _Translations = _InitializeTranslationsClass()
except:
    pass

def _gettext(s):
    return s

if _Translations is not None:
    _ = _Translations.ugettext
else:
    _ = _gettext

def _DecodeList(obj):
    for i in range(len(obj)):
        obj[i] = UserPreferredEncodingToUnicode(obj[i])
    return obj
        

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['_']
