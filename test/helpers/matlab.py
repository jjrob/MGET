# matlab.py - helper functions for testing MGET's MATLAB-related functionality.
#
# Copyright (C) 2026 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import sys

from GeoEco.Matlab import MatlabDependency


def isMatlabInstalled():

    # Currently, we only support MGET's MATLAB functionality on Python 3.13 or
    # lower, because the MATLAB Compiler only supports that, and we can only
    # execute MATLAB code packaged by it on Python versions it supports.

    if sys.version_info.minor > 13:
        return False

    d = MatlabDependency()
    try:
        d.Initialize()
    except:
        return False
    return True

