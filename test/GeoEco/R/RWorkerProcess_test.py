# RWorkerProcess_test.py - pytest tests for GeoEco.R.RWorkerProcess.
#
# Copyright (C) 2025 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import json
import logging
import os
import sys
import zoneinfo

import pytest
import tzlocal

from GeoEco.Logging import Logger
from GeoEco.R import RWorkerProcess

Logger.Initialize()


# This function is used to determine if tests should be skipped because R is
# not installed. This check is already implemented in RWorkerProcess. Rather
# than reimplement it here, we just rely on RWorkerProcess's internal
# functions. This means we can't use this skip function as a means to test
# those functions because it's the same code. So if we test them, we have to
# determine whether to skip or not via some other approach.

def isRInstalled():
    r = RWorkerProcess()
    if sys.platform == 'win32':
        rscriptPath = r._LocateRscriptOnWin32()
    elif sys.platform == 'linux':
        rscriptPath = None
        # rscriptPath = r._LocateRscriptOnLinux()  # Disable testing on Linux until RWorkerProcess fully supports Linux
    else:
        rscriptPath = None
    return rscriptPath is not None


@pytest.fixture(scope="class")
def rWorkerProcess():
    r = RWorkerProcess()
    yield r
    r.Stop()


@pytest.mark.skipif(not isRInstalled(), reason='R is not installed, or the Rscript program could not be located')
class TestRWorkerProcess():

    @pytest.mark.parametrize('expr,result', [
        ('logical(0)', []),
        ('numeric(0)', []),
        ('integer(0)', []),
        ('character(0)', []),
        ('c()', None),          # In R, c() is NULL, so it becomes JSON null and then Python None
        ('c(1)', 1),            # Length 1 vectors become Python scalars via unboxing
        ('c(1,2)', [1,2]),      # Length 2 or more vectors become Python lists
        ('list()', []),         # R lists that don't have any named elements are coerced to JSON lists by plumber, which then become Python lists rather than dicts
        ('list(1)', [1]),
        ('list(1,2)', [1,2]),
        ('list(a=1)', {'a': 1}),
        ('list(a=1, b=2, c=3)', {'a': 1, 'b': 2, 'c': 3}),
        ('list(a=1, 2, 3)', {'a': 1, '2': 2, '3': 3}),      # Nobody should do this in R, but here's how it works
        ('list(a=c(1))', {'a': 1}),
        ('list(a=c(1,2))', {'a': [1,2]}),
        ('list(a=TRUE, b=1, c=2.2, d="hello")', {'a': True, 'b': 1, 'c': 2.2, 'd': "hello"}),

        ('NULL', None),
        ('NA', None),
        ('c(NA, NA)', [None, None]),
        ('c(NA, NULL)', None),
        ('c(NA, NULL, NULL)', None),
        ('c(NA, NA, NULL)', [None, None]),
        ('c(NA, NA, NULL, 1)', [None, None, 1]),
        ('list(a=NA)', {'a': None}),
        ('list(a=NA, b=NA)', {'a': None, 'b': None}),

        ('TRUE', True),
        ('FALSE', False),

        ('0', 0),
        ('1', 1),
        ('-1', -1),
        (str(0-2**31), 0-2**31),        # Smallest 32-bit signed int
        (str(2**31-1), 2**31-1),        # Largest 32-bit signed int
        (str(0-2**31-1), 0-2**31-1),    # Smallest 32-bit signed int - 1
        (str(2**31), 2**31),            # Largest 32-bit signed int + 1
        # (str(0-2**63), 0-2**63),      # Smallest 64-bit signed int: doesn't work because R coerces this to a 64-bit float, which can't represent this number at full precision
        # (str(2**63-1), 2**63-1),      # Largest 64-bit signed int: doesn't work because R coerces this to a 64-bit float, which can't represent this number at full precision

        ('0.', 0.),
        ('0.0', 0.),
        ('1.23456789', 1.23456789),
        ('-1.23456789', -1.23456789),
        (repr(sys.float_info.max), sys.float_info.max),
        (repr(sys.float_info.min), sys.float_info.min),
        ('4.9406564584124654e-324', 4.9406564584124654e-324),   # numpy.nextafter(0, 1) used to return this
        ('5e-324', 5e-324),                                     # numpy.nextafter(0, 1) now returns this
        (repr(sys.float_info.max * -1), sys.float_info.max * -1),
        (repr(sys.float_info.min * -1), sys.float_info.min * -1),
        ('-4.9406564584124654e-324', 4.9406564584124654e-324 * -1),
        ('-5e-324', 5e-324 * -1),

        ('""', ''),
        ('"abc"', 'abc'),
        ('"Café, résumé, naïve, jalapeño"', "Café, résumé, naïve, jalapeño"),
        ('"["','['),
        ('"]"',']'),
        ('"{"','{'),
        ('"}"','}'),
        ('","',','),
    ])
    def test_RtoPythonJSONTypes(self, expr, result, rWorkerProcess):
        assert(result == rWorkerProcess.Eval(expr))
        rWorkerProcess['x'] = result
        if isinstance(result, list) and len(result) == 1:
            assert (rWorkerProcess['x'] == result[0])      # Lists of length 1 are automatically unboxed
        else:
            assert (rWorkerProcess['x'] == result)

    def test_JSONUTF8strings(self, rWorkerProcess):
        with open(os.path.join(os.path.dirname(__file__), 'utf8_test.json'), 'rt', encoding='utf-8') as f:
            strings = json.load(f)
        for s in strings:
            rWorkerProcess['x'] = s
            assert(rWorkerProcess['x'] == s)
        rWorkerProcess['x'] = strings
        assert(rWorkerProcess['x'] == strings)

    def test_DateTime(self):
        # Naive datetimes without defaultTZ.
        with RWorkerProcess() as r:
            for i in range(10):
                now = datetime.datetime.now()
                now = now.replace(microsecond=now.microsecond // 1000 * 1000)   # "mongo" time format only supports millsecond precision, at least as its implemented by jsonlite
                r['x'] = now
                assert r['x'].tzinfo == tzlocal.get_localzone()
                assert r['x'].replace(tzinfo=None) == now

        # Naive datetimes with defaultTZ.
        with RWorkerProcess(defaultTZ='UTC') as r:
            for i in range(10):
                now = datetime.datetime.now()
                now = now.replace(microsecond=now.microsecond // 1000 * 1000)   # "mongo" time format only supports millsecond precision, at least as its implemented by jsonlite
                r['x'] = now
                assert r['x'] == now.replace(tzinfo=zoneinfo.ZoneInfo('UTC'))

        # Non-naive datetimes without defaultTZ.
        with RWorkerProcess() as r:
            for i in range(10):
                now = datetime.datetime.now(tz=zoneinfo.ZoneInfo('UTC'))
                now = now.replace(microsecond=now.microsecond // 1000 * 1000)   # "mongo" time format only supports millsecond precision, at least as its implemented by jsonlite
                r['x'] = now
                assert r['x'].tzinfo is not None and (r['x'].tzinfo != now.tzinfo or tzlocal.get_localzone() == zoneinfo.ZoneInfo('UTC'))
                assert r['x'] == now.astimezone(r['x'].tzinfo)

        # Non-naive datetimes with defaultTZ.
        with RWorkerProcess(defaultTZ='America/Los_Angeles') as r:
            for i in range(10):
                now = datetime.datetime.now(tz=zoneinfo.ZoneInfo('UTC'))
                now = now.replace(microsecond=now.microsecond // 1000 * 1000)   # "mongo" time format only supports millsecond precision, at least as its implemented by jsonlite
                r['x'] = now
                assert r['x'].tzinfo is not None and r['x'].tzinfo != now.tzinfo
                assert r['x'] == now.astimezone(r['x'].tzinfo)

    def test_AuthenticationToken(self, rWorkerProcess):
        # Change Python's copy of the authentication token and verify that R
        # rejects our calls.

        originalAuthToken = rWorkerProcess._AuthenticationToken
        rWorkerProcess._AuthenticationToken = 'foo'
        with pytest.raises(RuntimeError, match='.*401: Unauthorized.*'):
            rWorkerProcess['x'] = 1
        with pytest.raises(RuntimeError, match='.*401: Unauthorized.*'):
            x = rWorkerProcess['x']
        with pytest.raises(RuntimeError, match='.*401: Unauthorized.*'):
            x = len(rWorkerProcess)
        with pytest.raises(RuntimeError, match='.*401: Unauthorized.*'):
            del rWorkerProcess['x']
        with pytest.raises(RuntimeError, match='.*401: Unauthorized.*'):
            rWorkerProcess.Eval('1+1')

        # Verify that it works again if we use the original token.

        rWorkerProcess._AuthenticationToken = originalAuthToken
        rWorkerProcess['x'] = 2
        assert rWorkerProcess['x'] == 2
        assert len(rWorkerProcess) == 1
        del rWorkerProcess['x']
        assert rWorkerProcess.Eval('1+1') == 2

    # def test_PythonToRJSONTypes(self, capsys):
    #     Logger.Initialize()   # Do not remove this from here, even though it is already called at module scope. If it is not here, capsys will not work.
