# ArcGIS_test.py - pytest tests for GeoEco.Types._ArcGIS.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from GeoEco.Types import *


class TestArcGISTypes():

    def test_Envelope_ParseFromArcGISString(self):
        assert EnvelopeTypeMetadata.ParseFromArcGISString(None) == (None, None, None, None)
        assert EnvelopeTypeMetadata.ParseFromArcGISString((-180, -90, 180, 90)) == (-180., -90., 180., 90.)
        assert EnvelopeTypeMetadata.ParseFromArcGISString('-180 -90 180 90') == (-180., -90., 180., 90.)
        assert EnvelopeTypeMetadata.ParseFromArcGISString('-180.1 -90.2 180.3 90.4') == (-180.1, -90.2, 180.3, 90.4)
        assert EnvelopeTypeMetadata.ParseFromArcGISString('-180,1 -90,2 180,3 90,4') == (-180.1, -90.2, 180.3, 90.4)

        class _FakeExtent(object):
            def __init__(self, xmin, xmax, ymin, ymax):
                self.XMin = xmin
                self.XMax = xmax
                self.YMin = ymin
                self.YMax = ymax

        assert EnvelopeTypeMetadata.ParseFromArcGISString(_FakeExtent(-180., 180., -90., 90.)) == (-180., -90., 180., 90.)
