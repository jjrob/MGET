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

from ._ArcGISWorkspace import ArcGISWorkspace
from ._ArcGISRaster import ArcGISRaster
from ._ArcGISRasterBand import ArcGISRasterBand
from ._ArcGISTable import ArcGISCopyableTable, ArcGISTable

###############################################################################
# Metadata: module
###############################################################################

from ...Internationalization import _
from ...Metadata import AddModuleMetadata

AddModuleMetadata(shortDescription=_(':class:`~GeoEco.Datasets.Table` and :class:`~GeoEco.Datasets.Grid` wrappers around tabular, vector, and raster datasets accessible through the ArcGIS `arcpy <https://www.esri.com/en-us/arcgis/products/arcgis-python-libraries/libraries/arcpy>`_ library.'))

from . import _ArcGISWorkspaceMetadata
from . import _ArcGISRasterMetadata
from . import _ArcGISRasterBandMetadata
from . import _ArcGISTableMetadata


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['ArcGISCopyableTable',
           'ArcGISRaster',
           'ArcGISRasterBand',
           'ArcGISTable',
           'ArcGISWorkspace',]
