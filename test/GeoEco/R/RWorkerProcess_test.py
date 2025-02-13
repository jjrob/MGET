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
import math
import os
import sys
import zoneinfo

import pandas
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
    rscriptPath = None
    try:
        if sys.platform == 'win32':
            rscriptPath = r._LocateRscriptOnWin32()
        elif sys.platform == 'linux':
            rscriptPath = r._LocateRscriptOnLinux()
    except:
        pass
    return rscriptPath is not None


@pytest.fixture(scope="class")
def rWorkerProcess():
    r = RWorkerProcess()
    yield r
    r.Stop()


def equalWithNaN(obj1, obj2):
    """Recursively compares two objects, treating NaNs as equal."""
    if isinstance(obj1, float) and isinstance(obj2, float):
        return math.isnan(obj1) and math.isnan(obj2) or obj1 == obj2

    if isinstance(obj1, list) and isinstance(obj2, list):
        return len(obj1) == len(obj2) and all(equalWithNaN(a, b) for a, b in zip(obj1, obj2))

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        if obj1.keys() != obj2.keys():
            return False
        return all(equalWithNaN(obj1[k], obj2[k]) for k in obj1)

    return obj1 == obj2


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
        ('as.integer(c(0))', 0),
        ('as.integer(c(1))', 1),
        ('as.integer(c(-1))', -1),
        ('as.integer(c(1, NA, 2))', [1, None, 2]),

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
        ('NaN', float('nan')),
        ('Inf', float('inf')),
        ('-Inf', float('-inf')),
        ('c(1.1, 2.2, NaN, 3.3, Inf, 4.4, -Inf, 5.5, NA, 6.6)', [1.1, 2.2, float('nan'), 3.3, float('inf'), 4.4, float('-inf'), 5.5, None, 6.6]),
        ('list(1.1, NaN, Inf, -Inf, NA, 2.2)', [1.1, float('nan'), float('inf'), float('-inf'), None, 2.2]),
        ('list(a=1.1, b=NaN, c=Inf, d=-Inf, e=NA, f=2.2)', {'a': 1.1, 'b': float('nan'), 'c': float('inf'), 'd': float('-inf'), 'e': None, 'f': 2.2}),
        ('list(a=c(1.1), b=c(NaN), c=c(Inf), d=c(-Inf), e=c(NA), f=c(2.2))', {'a': 1.1, 'b': float('nan'), 'c': float('inf'), 'd': float('-inf'), 'e': None, 'f': 2.2}),
        ('list(a=c(1.1,5), b=c(NaN,6), c=c(Inf,7), d=c(-Inf,8), e=c(NA,9), f=c(2.2,10))', {'a': [1.1,5], 'b': [float('nan'),6], 'c': [float('inf'),7], 'd': [float('-inf'),8], 'e': [None,9], 'f': [2.2,10]}),
        ('list(x=list(q=1, r=2), y=list(a=1.1, b=NaN, c=Inf, d=-Inf, e=NA, f=2.2))', {'x': {'q':1, 'r': 2}, 'y': {'a': 1.1, 'b': float('nan'), 'c': float('inf'), 'd': float('-inf'), 'e': None, 'f': 2.2}}),

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
        x = rWorkerProcess.Eval(expr)
        assert equalWithNaN(x, result)

        rWorkerProcess['x'] = result
        x = rWorkerProcess['x']
        if isinstance(result, list) and len(result) == 1:
            result = result[0]    # Lists of length 1 are automatically unboxed
        assert equalWithNaN(x, result)

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

    def test_DataFrames(self, rWorkerProcess):
        df = pandas.DataFrame({'BoolCol': [True, False, None, False, True, True, False, False, False],
                               'IntCol': [0, -1, 1, 10, 0-2**31+1, 2**31-1, 1000, 2000, 3000],
                               'Int64Col': [0, -1, 1, 10, 0-2**63+1, 2**63-1, 1000, 2000, 3000],
                               'FloatCol': [0., 1.1, float('nan'), float('inf'), float('-inf'), sys.float_info.min, sys.float_info.max, 4.9406564584124654e-324, 4.9406564584124654e-324 * -1],
                               'StrCol': ['a', 'b', 'c', None, 'd', '', '[abc]', 'résumé', 'e'],
                               })

        rWorkerProcess['df'] = df
        assert rWorkerProcess.Eval('sapply(df, class)') == ['logical', 'integer', 'integer64', 'numeric', 'character']

        def isEqualNaN(x, y):
            return x == y or math.isnan(x) and math.isnan(y)

        df2 = rWorkerProcess['df']
        assert all(df.columns == df2.columns)
        assert all([all([isEqualNaN(df.at[i,c], df2.at[i,c]) for i in range(len(df))]) for c in df.columns])

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
        rWorkerProcess.Eval('rm(list=ls())')
        rWorkerProcess['x'] = 2
        assert rWorkerProcess['x'] == 2
        assert len(rWorkerProcess) == 1
        del rWorkerProcess['x']
        assert rWorkerProcess.Eval('1+1') == 2

    def test_ExecuteRAndEvaluateExpressions(self):
        x = RWorkerProcess.ExecuteRAndEvaluateExpressions(['1+1'], returnResult=True)
        assert x == 2

        x = RWorkerProcess.ExecuteRAndEvaluateExpressions(['1+1', '9'], returnResult=True)
        assert x == 9

        x = RWorkerProcess.ExecuteRAndEvaluateExpressions(['1+1'], returnResult=False)
        assert x is None

        with pytest.raises(Exception, match='.*timeout.*'):
            RWorkerProcess.ExecuteRAndEvaluateExpressions(['1+1'], timeout=0.01)

    @pytest.mark.parametrize('expr,result', [
        ('a', None),
        ('b', True),
        ('c', False),
        ('d', 123),
        ('e', 123.45),
        ('f', 'Hello'),
        ('g', ' '),
        ('h', datetime.datetime(2010,12,31, 1,23,45, tzinfo=zoneinfo.ZoneInfo(key='America/Los_Angeles'))),
        ('i', datetime.datetime(2010,12,31, 1,23,45, tzinfo=zoneinfo.ZoneInfo(key='America/Los_Angeles'))),
    ])
    def test_ExecuteRAndEvaluateExpressions_WithVariables(self, expr, result):
        x = RWorkerProcess.ExecuteRAndEvaluateExpressions([expr], 
                                                          returnResult=True, 
                                                          variableNames=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
                                                          variableValues=['', 'True', 'False', '123', '123.45', 'Hello', ' ', '2010-12-31 01:23:45-08:00', '2010-12-31 01:23:45'],
                                                          defaultTZ='America/Los_Angeles')
        assert x == result

    def test_ExecuteRAndEvaluateExpressions_InstallPackages(self, tmp_path):
        x = RWorkerProcess.ExecuteRAndEvaluateExpressions(['library(glue); 1+1'], rPackages=['glue'], rLibDir=tmp_path, returnResult=True)
        assert x == 2
