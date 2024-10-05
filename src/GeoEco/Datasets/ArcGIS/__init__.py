# Datasets/ArcGIS.py - Datasets and DatasetCollections that wrap the ArcGIS
# tabular and raster datasets accessible with the Python arcpy library.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

# To keep file sizes managable, we split the names defined by this package
# across several files.

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_(':class:`~GeoEco.Datasets.Table` and :class:`~GeoEco.Datasets.Grid` wrappers around tabular, vector, and raster datasets accessible through the ArcGIS `arcpy <https://www.esri.com/en-us/arcgis/products/arcgis-python-libraries/libraries/arcpy>`_ library.'))

from ._ArcGISRaster import ArcGISRaster, _UseUnscaledDataDescription, _CalculateStatisticsDescription, _BuildRATDescription, _BuildPyramidsDescription
from . import _ArcGISRasterMetadata

from ._ArcGISRasterBand import ArcGISRasterBand
from . import _ArcGISRasterBandMetadata

from ._ArcGISTable import ArcGISCopyableTable, ArcGISTable
from . import _ArcGISTableMetadata

from ._ArcGISWorkspace import ArcGISWorkspace
from . import _ArcGISWorkspaceMetadata

__all__ = ['_BuildPyramidsDescription',
           '_BuildRATDescription',
           '_CalculateStatisticsDescription',
           '_UseUnscaledDataDescription',
           'ArcGISCopyableTable',
           'ArcGISRaster',
           'ArcGISRasterBand',
           'ArcGISTable',
           'ArcGISWorkspace',]
