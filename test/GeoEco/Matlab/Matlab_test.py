# Matlab_test.py - pytest tests for GeoEco.Matlab.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import math
import os
import sys

import numpy
import pytest

from GeoEco.Logging import Logger
from GeoEco.Matlab import MatlabDependency, MatlabWorkerProcess

Logger.Initialize()


def isMatlabInstalled():

    # Currently, we only support MGET's MATLAB functionality on Python 3.12 or
    # lower, because the MATLAB Compiler only supports that, and we can only
    # execute MATLAB code packaged by it on Python versions it supports.

    if sys.version_info.minor > 12:
        return False

    d = MatlabDependency()
    try:
        d.Initialize()
    except:
        return False
    return True


@pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
class TestMatlab():

    def test_None(self):
        with pytest.raises(TypeError, match='.*None cannot be passed to MATLAB.*|.*passing \'None\' to MATLAB not supported.*'):
            with MatlabWorkerProcess() as matlab:
                matlab.TestParameterType(None)

    def test_float(self):
        with MatlabWorkerProcess() as matlab:
            for input in [0.0, 1.0, -1.0, float('nan'), float('inf'), sys.float_info.min, sys.float_info.max]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_int(self):
        with MatlabWorkerProcess() as matlab:
            for input in [0, 1, -1, 2**31 - 1, 0 - 2**31, 2**63 - 1, 0 - 2**63]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_bool(self):
        with MatlabWorkerProcess() as matlab:
            for input in [False, True]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_str(self):
        with MatlabWorkerProcess() as matlab:
            for input in ['hello', '', ' ', 'a'*65535]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_dict(self):
        with MatlabWorkerProcess() as matlab:
            for input in [{}, {'a':'b'}, {'a': 'b', 'c':'d'}, {'a': 1., 'b': 2, 'c': True, 'd': ''}, {'a': {'b': 'c', 'd': {'a': 1., 'b': 2, 'c': True, 'd': ''}}}]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

            with pytest.raises(ValueError, match='.*invalid field for MATLAB struct.*|.*field name of Python dict object passed to MATLAB must be a nonempty string.*'):  # Only string keys are supported
                matlab.TestParameterType({1:2})

    def test_tuple(self):
        with MatlabWorkerProcess() as matlab:
            for input in [(), (0.0,), (1,), (True,), ('hello',), (0.0, 1, True, 'hello'), (0.0, 1, True, 'hello', (0.0, 1, True, 'hello', ('foo', 'bar')), ('baz',))]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_list(self):
        with MatlabWorkerProcess() as matlab:
            for input in [[], [0.0,], [1,], [True,], ['hello',], [0.0, 1, True, 'hello'], [0.0, 1, True, 'hello', [0.0, 1, True, 'hello', ['foo', 'bar']], ['baz',]]]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_set(self):
        with MatlabWorkerProcess() as matlab:
            for input in [set(), set((0.0,)), set((1,)), set((True,)), set(('hello',)), set((0.0, 1, True, 'hello'))]:
                output = matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_numpy_arrays(self):
        with MatlabWorkerProcess() as matlab:
            for dtype in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64']:
                for shape in [(2,3), (2,3,4), (2,3,4,5), (4096, 8192)]:
                    input = numpy.arange(math.prod(shape), dtype=dtype).reshape(shape)
                    output = matlab.TestParameterType(input)
                    self._OutputEqualsInput(input, output)

    def test_numpy_large_arrays(self):
        with MatlabWorkerProcess() as matlab:
            for dtype in ['float32', 'float64']:
                for shape in [(4096, 8192), (1024, 2048, 16)]:
                    input = numpy.arange(math.prod(shape), dtype=dtype).reshape(shape)
                    output = matlab.TestParameterType(input)
                    self._OutputEqualsInput(input, output)

    # Helper functions

    def _OutputEqualsInput(self, input, output):
        assert type(input) == type(output) or isinstance(input, (tuple, set)) and isinstance(output, list)  # tuples, sets, and lists are all turned into MATLAB cell arrays, which are always returned as lists

        if isinstance(input, float):
            assert output == input or math.isnan(output) and math.isnan(input) or math.isinf(output) and math.isinf(input)

        elif isinstance(input, (int, bool, str)):
            assert output == input

        elif isinstance(input, dict):
            for k in input:
                assert k in output
                assert type(input[k]) == type(output[k])
                self._OutputEqualsInput(input[k], output[k])

        elif isinstance(input, (tuple, list, set)):
            assert len(output) == len(input)
            for item1, item2 in zip(input, output):
                self._OutputEqualsInput(item1, item2)

        elif isinstance(input, numpy.ndarray):
            assert input.shape == output.shape

        else:
            raise NotImplementedError(f'The value {input!r} has a type {type(input)!r} that is not supported by this test code.')
