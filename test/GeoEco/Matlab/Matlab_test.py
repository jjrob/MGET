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
import GeoEco.Matlab

Logger.Initialize()


def isMatlabInstalled():
    d = GeoEco.Matlab.MatlabDependency()
    try:
        d.Initialize()
    except:
        return False
    return True


@pytest.mark.skipif(not isMatlabInstalled(), reason='MATLAB or MATLAB Runtime is not installed, or initialization of interoperability with it failed')
class TestMatlab():

    def test_None(self):
        with pytest.raises(TypeError, match='.*None cannot be passed to MATLAB.*'):
            GeoEco.Matlab.TestParameterType(None)

    def test_float(self):
        for input in [0.0, 1.0, -1.0, float('nan'), float('inf'), sys.float_info.min, sys.float_info.max]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

    def test_int(self):
        for input in [0, 1, -1, 2**31 - 1, 0 - 2**31, 2**63 - 1, 0 - 2**63]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

    def test_bool(self):
        for input in [False, True]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

    def test_str(self):
        for input in ['hello', '', ' ', 'a'*65535]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

    def test_dict(self):
        for input in [{}, {'a':'b'}, {'a': 'b', 'c':'d'}, {'a': 1., 'b': 2, 'c': True, 'd': ''}, {'a': {'b': 'c', 'd': {'a': 1., 'b': 2, 'c': True, 'd': ''}}}]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

        with pytest.raises(ValueError, match='.*invalid field for MATLAB struct.*'):  # Only string keys are supported
            GeoEco.Matlab.TestParameterType({1:2})

    def test_tuple(self):
        for input in [(), (0.0,), (1,), (True,), ('hello',), (0.0, 1, True, 'hello'), (0.0, 1, True, 'hello', (0.0, 1, True, 'hello', ('foo', 'bar')), ('baz',))]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

    def test_list(self):
        for input in [[], [0.0,], [1,], [True,], ['hello',], [0.0, 1, True, 'hello'], [0.0, 1, True, 'hello', [0.0, 1, True, 'hello', ['foo', 'bar']], ['baz',]]]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

    def test_set(self):
        for input in [set(), set((0.0,)), set((1,)), set((True,)), set(('hello',)), set((0.0, 1, True, 'hello'))]:
            output = GeoEco.Matlab.TestParameterType(input)
            self._OutputEqualsInput(input, output)

    def test_numpy_arrays(self):
        for dtype in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64']:
            for shape in [(2,3), (2,3,4), (2,3,4,5), (4096, 8192)]:
                input = numpy.arange(math.prod(shape), dtype=dtype).reshape(shape)
                output = GeoEco.Matlab.TestParameterType(input)
                self._OutputEqualsInput(input, output)

    def test_numpy_large_arrays(self):
        for dtype in ['float32', 'float64']:
            for shape in [(4096, 8192), (1024, 2048, 16)]:
                input = numpy.arange(math.prod(shape), dtype=dtype).reshape(shape)
                output = GeoEco.Matlab.TestParameterType(input)
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
