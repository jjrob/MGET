# _GHRSSTLevel4Metadata.py - Metadata for classes defined in
# _GHRSSTLevel4.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ....ArcGIS import ArcGISDependency
from ....Datasets.ArcGIS import _UseUnscaledDataDescription, _CalculateStatisticsDescription, _BuildPyramidsDescription, _BuildRATDescription
from ....Datasets.Virtual import ClimatologicalGridCollection, CannyEdgeGrid, _CannyEdgesOverview
from ....Dependencies import PythonModuleDependency
from ....Internationalization import _
from ....Matlab import MatlabDependency
from ....Metadata import *
from ....SpatialAnalysis.Interpolation import Interpolator
from ....Types import *

from . import GHRSSTLevel4Granules, _GHRSSTLevel4_LongDescription
from . import GHRSSTLevel4


###############################################################################
# Metadata: GHRSSTLevel4 class
###############################################################################

AddClassMetadata(GHRSSTLevel4,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing a `GHRSST <https://podaac.jpl.nasa.gov/GHRSST>`__ Level 4 product from NASA JPL PO.DAAC, distributed by `NASA Earthdata <https://www.earthdata.nasa.gov/>`__.'),
    longDescription=_GHRSSTLevel4_LongDescription % {'name': 'class'})

# Public constructor

AddMethodMetadata(GHRSSTLevel4.__init__,
    shortDescription=_('GHRSSTLevel4 constructor.'),
    dependencies=[PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('requests', cheeseShopName='requests'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

AddArgumentMetadata(GHRSSTLevel4.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=GHRSSTLevel4),
    description=_(':class:`%s` instance.') % GHRSSTLevel4.__name__)

CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'username', GHRSSTLevel4.__init__, 'username')
CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'password', GHRSSTLevel4.__init__, 'password')
CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'shortName', GHRSSTLevel4.__init__, 'shortName')

AddArgumentMetadata(GHRSSTLevel4.__init__, 'variableName',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['analysed_sst', 'analysis_error']),
    description=_(
"""GHRSST variable to access, one of:

* ``analysed_sst`` - product-specific estimate of SST.

* ``analysis_error`` - product-specific estimate of of the error in the SST
  estimate.

Please see the product documentation for details about what these variables
mean and how they were calculated. These variable names are
case-sensitive."""),
    arcGISDisplayName=_('GHRSST variable'))

CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'datasetType', GHRSSTLevel4.__init__, 'datasetType')

AddArgumentMetadata(GHRSSTLevel4.__init__, 'applyMask',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If False, the default, no masking will be performed to the GHRSST
``analysed_sst`` variable beyond what the GHRSST team has already done. For
most GHRSST L4 products, this is sufficient because land and sea ice have
already been masked and will appear as the
:attr:`~GeoEco.Datasets.Grid.NoDataValue`.

If True, ``analysed_sst`` will be masked where the GHRSST ``mask`` variable is
some value other than 1. The value 1 indicates water that is free of sea ice.
To check for specific bits of the mask instead, use `maskBitsToCheck`."""))

AddArgumentMetadata(GHRSSTLevel4.__init__, 'maskBitsToCheck',
    typeMetadata=IntegerTypeMetadata(minValue=0, canBeNone=True),
    description=_(
"""Integer defining the bits of the GHRSST ``mask`` variable to check. This is
ignored unless `applyMask` is True. If it is, and this parameter is omitted
(the default) then cells will be masked when the ``mask`` variable is
something other than 1. If parameter is given, then if the GHRSST ``mask``
variable has a 1 for any bit that this parameter also has a 1, then the cell
is masked."""))

AddArgumentMetadata(GHRSSTLevel4.__init__, 'convertToCelsius',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True (the default), temperature values will be converted from
kelvin to degrees Celsius. If False, temperature values will be in the
original kelvin values."""),
    arcGISDisplayName=_('Convert temperatures to Celsius'),
    arcGISCategory=_('Output raster options'))

CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'timeout', GHRSSTLevel4.__init__, 'timeout')
CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'maxRetryTime', GHRSSTLevel4.__init__, 'maxRetryTime')
CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'cacheDirectory', GHRSSTLevel4.__init__, 'cacheDirectory')
CopyArgumentMetadata(GHRSSTLevel4Granules.__init__, 'metadataCacheLifetime', GHRSSTLevel4.__init__, 'metadataCacheLifetime')

AddResultMetadata(GHRSSTLevel4.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=GHRSSTLevel4),
    description=_(':class:`%s` instance.') % GHRSSTLevel4.__name__)

# Public method: GHRSSTLevel4.CreateArcGISRasters

AddMethodMetadata(GHRSSTLevel4.CreateArcGISRasters,
    shortDescription=_('Creates rasters for a `GHRSST <https://podaac.jpl.nasa.gov/GHRSST>`__ Level 4 product published by NASA JPL PO.DAAC.'),
    longDescription=_GHRSSTLevel4_LongDescription % {'name': 'tool'},
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Rasters for GHRSST L4 SST'),
    arcGISToolCategory=_('Data Products\\NASA JPL PO.DAAC\\GHRSST L4 SST'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('requests', cheeseShopName='requests'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=GHRSSTLevel4),
    description=_('GHRSSTLevel4 class or instance.'))

CopyArgumentMetadata(GHRSSTLevel4.__init__, 'username', GHRSSTLevel4.CreateArcGISRasters, 'username')
CopyArgumentMetadata(GHRSSTLevel4.__init__, 'password', GHRSSTLevel4.CreateArcGISRasters, 'password')
CopyArgumentMetadata(GHRSSTLevel4.__init__, 'shortName', GHRSSTLevel4.CreateArcGISRasters, 'shortName')
CopyArgumentMetadata(GHRSSTLevel4.__init__, 'variableName', GHRSSTLevel4.CreateArcGISRasters, 'variableName')

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'outputWorkspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(createParentDirectories=True),
    description=_(
"""Directory or geodatabase to receive the rasters. Unless you have a specific
reason to store the rasters in a geodatabase, we recommend you store them in a
directory because it will be faster and allow the rasters to be organized in a
tree. The tree structure and raster names will be generated automatically
unless you provide a value for the Raster Name Expressions parameter."""),
    arcGISDisplayName=_('Output workspace'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'mode',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Add', 'Replace'], makeLowercase=True),
    description=_(
"""Overwrite mode, one of:

* ``Add`` - create rasters that do not exist and skip those that already
  exist. This is the default.

* ``Replace`` - create rasters that do not exist and overwrite those that
  already exist.

The ArcGIS Overwrite Output environment setting has no effect on this tool. If
'Replace' is selected the rasters will be overwritten, regardless of the
ArcGIS Overwrite Output setting."""),
    arcGISDisplayName=_('Overwrite mode'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'rotationOffset',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Degrees to rotate the outputs about the polar axis. This parameter may only
be used for global products. The outputs can only be rotated in whole cells.
The value you provide will be rounded off to the closest cell. The value may
be positive or negative."""),
    arcGISDisplayName=_('Rotate by'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'spatialExtent',
    typeMetadata=EnvelopeTypeMetadata(canBeNone=True),
    description=_(
"""Spatial extent of the outputs, in degrees. This parameter is applied after
the rotation parameter and uses coordinates that result after rotation. The
outputs can only be clipped in whole grid cells. The values you provide will
be rounded off to the closest cell."""),
    arcGISDisplayName=_('Spatial extent'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'startDate',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Start date for the outputs to create. Outputs will be created for images
that occur on or after the start date and on or before the end date. If you do
not provide a start date, the date of the first available time slice will be
used."""),
    arcGISDisplayName=_('Start date'),
    arcGISCategory=_('Spatiotemporal extent'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'endDate',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""End date for the outputs to create. Outputs will be created for images that
occur on or after the start date and on or before the end date. If you do not
specify an end date, the date of the most recent time slice will be used."""),
    arcGISDisplayName=_('End date'),
    arcGISCategory=_('Spatiotemporal extent'))

CopyArgumentMetadata(GHRSSTLevel4.__init__, 'datasetType', GHRSSTLevel4.CreateArcGISRasters, 'datasetType')
CopyArgumentMetadata(GHRSSTLevel4.__init__, 'timeout', GHRSSTLevel4.CreateArcGISRasters, 'timeout')
CopyArgumentMetadata(GHRSSTLevel4.__init__, 'maxRetryTime', GHRSSTLevel4.CreateArcGISRasters, 'maxRetryTime')
CopyArgumentMetadata(GHRSSTLevel4.__init__, 'cacheDirectory', GHRSSTLevel4.CreateArcGISRasters, 'cacheDirectory')
CopyArgumentMetadata(GHRSSTLevel4.__init__, 'metadataCacheLifetime', GHRSSTLevel4.CreateArcGISRasters, 'metadataCacheLifetime')

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'rasterExtension',
    typeMetadata=UnicodeStringTypeMetadata(minLength=1, canBeNone=True),
    description=_(
"""File extension to use for output rasters. This parameter is ignored if the
rasters are stored in a geodatabase rather than the file system, or if the
Raster Name Expressions parameter is provided (in which case it determines the
file extension). The default is '.img', for ERDAS IMAGINE format. Another
popular choice is '.tif', the GeoTIFF format. Please see the ArcGIS
documentation for the extensions of the supported formats."""),
    arcGISDisplayName=_('Raster file extension'),
    arcGISCategory=_('Output raster options'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'rasterNameExpressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    description=_(
"""List of expressions specifying how the output rasters should be named. If
you do not provide anything, a default naming scheme will be used.

If the output workspace is a file system directory, you may provide one or
more expressions. Each expression defines a level in a directory tree. The
final expression specifies the raster file name. If the output workspace is a
geodatabase, you should provide only one expression, which specifies the
raster name.

Each expression may contain any sequence of characters permitted by the output
workspace. Each expression may optionally contain one or more of the following
case-sensitive codes. The tool replaces the codes with appropriate values when
creating each raster:

* %(ShortName)s - PO.DAAC Short Name of the GHRSST L4 product.

* %(VariableName)s - GHRSST variable represented in the output raster,
  usually either ``analysed_sst`` or ``analysis_error``.

* ``%%Y`` - four-digit year of the raster. This and the following codes are
  only available for datasets that have time coordinates.

* ``%%m`` - two-digit month of the raster.

* ``%%d`` - two-digit day of the month of the raster.

* ``%%j`` - three-digit day of the year of the raster.

* ``%%H`` - two-digit hour of the raster.

* ``%%M`` - two-digit minute of the raster.

* ``%%S`` - two-digit second of the raster.

"""),
    arcGISDisplayName=_('Raster name expressions'),
    arcGISCategory=_('Output raster options'))

CopyArgumentMetadata(GHRSSTLevel4.__init__, 'convertToCelsius', GHRSSTLevel4.CreateArcGISRasters, 'convertToCelsius')

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'useUnscaledData',
    typeMetadata=BooleanTypeMetadata(),
    description=_UseUnscaledDataDescription,
    arcGISDisplayName=_('Use unscaled data'),
    arcGISCategory=_('Output raster options'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'calculateStatistics',
    typeMetadata=BooleanTypeMetadata(),
    description=_BuildRATDescription,
    arcGISDisplayName=_('Calculate statistics'),
    arcGISCategory=_('Output raster options'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'buildRAT',
    typeMetadata=BooleanTypeMetadata(),
    description=_BuildRATDescription,
    arcGISDisplayName=_('Build raster attribute tables'),
    arcGISCategory=_('Output raster options'))

AddArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'buildPyramids',
    typeMetadata=BooleanTypeMetadata(),
    description=_BuildPyramidsDescription,
    arcGISDisplayName=_('Build pyramids'),
    arcGISCategory=_('Output raster options'))

AddResultMetadata(GHRSSTLevel4.CreateArcGISRasters, 'updatedOutputWorkspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(),
    description=_('Updated output workspace.'),
    arcGISDisplayName=_('Updated output workspace'),
    arcGISParameterDependencies=['outputWorkspace'])

# Public method: GHRSSTLevel4.CreateClimatologicalArcGISRasters

AddMethodMetadata(GHRSSTLevel4.CreateClimatologicalArcGISRasters,
    shortDescription=_('Creates climatological rasters for a `GHRSST <https://podaac.jpl.nasa.gov/GHRSST>`__ Level 4 product published by NASA JPL PO.DAAC.'),
    longDescription=_(
"""This tool produces rasters showing the climatological mean value (or other
statistic) of a time series of GHRSST L4 SST images. Given a desired GHRSST L4
product, a statistic, and a climatological bin definition, this tool
efficiently downloads the images, classifies them into bins, and produces a
single raster for each bin. Each cell of the raster is produced by calculating
the statistic on the values of that cell extracted from all of the images in
the bin.

""" + _GHRSSTLevel4_LongDescription) % {'name': 'tool'},
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Climatological Rasters for GHRSST L4 SST'),
    arcGISToolCategory=_('Data Products\\NASA JPL PO.DAAC\\GHRSST L4 SST'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('requests', cheeseShopName='requests'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'cls', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'cls')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'username', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'username')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'password', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'password')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'shortName', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'shortName')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'variableName', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'variableName')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'statistic', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'statistic')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'binType', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'binType')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'outputWorkspace', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'outputWorkspace')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'mode', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'mode')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'binDuration', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'binDuration')
CopyArgumentMetadata(ClimatologicalGridCollection.__init__, 'startDayOfYear', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'startDayOfYear')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'rotationOffset', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'rotationOffset')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'spatialExtent', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'spatialExtent')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'startDate', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'startDate')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'endDate', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'endDate')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'datasetType', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'datasetType')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'timeout', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'timeout')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'maxRetryTime', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'maxRetryTime')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'cacheDirectory', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'cacheDirectory')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'metadataCacheLifetime', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'metadataCacheLifetime')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'rasterExtension', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'rasterExtension')

AddArgumentMetadata(GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'rasterNameExpressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    description=_(
"""List of expressions specifying how the output rasters should be named. If
you do not provide anything, a default naming scheme will be used.

If the output workspace is a file system directory, you may provide one or
more expressions. Each expression defines a level in a directory tree. The
final expression specifies the raster file name. If the output workspace is a
geodatabase, you should provide only one expression, which specifies the
raster name.

Each expression may contain any sequence of characters permitted by the output
workspace. Each expression may optionally contain one or more of the following
case-sensitive codes. The tool replaces the codes with appropriate values when
creating each raster:

* %(ShortName)s - PO.DAAC Short Name of the GHRSST L4 product.

* %(VariableName)s - GHRSST variable represented in the output raster,
  either "analysed_sst" or "analysis_error".

* ``%(ClimatologyBinType)s`` - type of the climatology bin, either ``Daily``
  if 1-day bins, ``Xday`` if multi-day bins (``X`` is replaced by the
  duration), ``Monthly`` if 1-month bins, ``Xmonth`` if multi-month bins, or
  ``Cumulative``. If an ENSO bin type is used, ``ENSO_`` will be prepended to
  those strings (e.g. ``ENSO_Daily``, ``ENSO_Monthly``).

* ``%(ClimatologyBinName)s`` - name of the climatology bin corresponding
  represented by the output raster, either ``dayXXX`` for 1-day bins (``XXX``
  is replaced by the day of the year), ``daysXXXtoYYY`` for multi-day bins
  (``XXX`` is replaced by the first day of the bin, ``YYY`` is replaced by the
  last day), ``monthXX`` for 1-month bins (``XX`` is replaced by the month),
  ``monthXXtoYY`` (``XX`` is replaced by the first month of the bin, ``YY`` by
  the last month), or ``cumulative``. If an ENSO bin type is used,
  ``neutral_``, ``ElNino_``, and ``LaNina_`` will be prepended to those
  strings for each of the three ENSO phased rasters (e.g.
  ``neutral_cumulative``, ``ElNino_cumulative``, and ``LaNina_cumulative``
  when ``ENSO Cumulative`` bins are requested).

* ``%(Statistic)s`` - statistic that was calculated, in lowercase and with
  spaces replaced by underscores; one of: ``count``, ``maximum``, ``mean``,
  ``minimum``, ``range``, ``standard_deviation``, ``sum``.

If the Bin Type is ``Daily``, the following additional codes are available:

* ``%(FirstDay)i`` - first day of the year of the climatology bin represented
  by the output raster.

* ``%(LastDay)i`` - last day of the year of the climatology bin represented by
  the output raster. For 1-day climatologies, this will be the same as
  ``%(FirstDay)i``.

If the Bin Type is ``Monthly``, the following additional codes are available:

* ``%(FirstMonth)i`` - first month of the climatology bin represented by the
  output raster.

* ``%(DayOfFirstMonth)i`` - first day of the first month of the climatology
  bin represented by the output raster.

* ``%(LastMonth)i`` - last month of the climatology bin represented by the
  output raster.

* ``%(DayOfLastMonth)i`` - last day of the last month of the climatology bin
  represented by the output raster.

Note that the additional codes are integers and may be formatted using
"printf"-style formatting codes. For example, to format the ``FirstDay`` as a
three-digit number with leading zeros::

    %(FirstDay)03i

"""),
    arcGISDisplayName=_('Raster name expressions'),
    arcGISCategory=_('Output raster options'))

CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'convertToCelsius', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'convertToCelsius')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'calculateStatistics', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'calculateStatistics')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'buildPyramids', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'buildPyramids')

CopyResultMetadata(GHRSSTLevel4.CreateArcGISRasters, 'updatedOutputWorkspace', GHRSSTLevel4.CreateClimatologicalArcGISRasters, 'updatedOutputWorkspace')

# Public method: GHRSSTLevel4.InterpolateAtArcGISPoints

AddMethodMetadata(GHRSSTLevel4.InterpolateAtArcGISPoints,
    shortDescription=_('Interpolates values of a `GHRSST <https://podaac.jpl.nasa.gov/GHRSST>`__ Level 4 product published by NASA JPL PO.DAAC at points.'),
    longDescription=_(
"""Given a desired GHRSST L4 product, this tool interpolates the value of that
product at the given points. This tool performs the same basic operation as
the ArcGIS Spatial Analyst's :arcpy_sa:`Extract-Values-to-Points` tool, but it
reads the data from NASA's servers rather than reading rasters stored on your
machine.

""" + _GHRSSTLevel4_LongDescription) % {'name': 'tool'},
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Interpolate GHRSST L4 SST at Points'),
    arcGISToolCategory=_('Data Products\\NASA JPL PO.DAAC\\GHRSST L4 SST'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('requests', cheeseShopName='requests'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'cls', GHRSSTLevel4.InterpolateAtArcGISPoints, 'cls')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'username', GHRSSTLevel4.InterpolateAtArcGISPoints, 'username')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'password', GHRSSTLevel4.InterpolateAtArcGISPoints, 'password')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'shortName', GHRSSTLevel4.InterpolateAtArcGISPoints, 'shortName')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'variableName', GHRSSTLevel4.InterpolateAtArcGISPoints, 'variableName')

AddArgumentMetadata(GHRSSTLevel4.InterpolateAtArcGISPoints, 'points',
    typeMetadata=ArcGISFeatureLayerTypeMetadata(mustExist=True, allowedShapeTypes=['Point']),
    description=_(
"""Feature class or layer containing the points at which GHRSST values should
be interpolated. The points must have a field that contains the date of each
point and a field to receive the value interpolated from the raster.

The GHRSST data use the WGS 1984 geographic coordinate system. It is
recommended but not required that the points use the same coordinate system.
If they do not, this tool will attempt to project the points to the WGS 1984
coordinate system prior to doing the interpolation. This may fail if a datum
transformation is required, in which case you will have to manually project
the points to the WGS 1984 coordinate system before using this tool."""),
    arcGISDisplayName=_('Point features'))

CopyArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'tField', GHRSSTLevel4.InterpolateAtArcGISPoints, 'tField')
CopyArgumentMetadata(Interpolator.InterpolateTimeSeriesOfArcGISRastersValuesAtPoints, 'valueField', GHRSSTLevel4.InterpolateAtArcGISPoints, 'valueField')

AddArgumentMetadata(GHRSSTLevel4.InterpolateAtArcGISPoints, 'method',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Nearest', 'Linear'], makeLowercase=True),
    description=_(
"""Interpolation method to use, one of:

* ``Nearest`` - nearest neighbor interpolation. The interpolated value
  will simply be the value of the cell that contains the point. This
  is the default.

* ``Linear`` - linear interpolation (also known as trilinear interpolation).
  This method is suitable for continuous data such as sea surface temperature,
  but not for categorical data such as pixel quality flags (use nearest
  neighbor instead). This method averages the values of the eight nearest
  cells in the x, y, and time dimensions, weighting the contribution of each
  cell by the area of it that would be covered by a hypothetical cell centered
  on the point being interpolated. If the cell containing the point contains
  NoData, the result is NoData. Otherwise, and the result is based on the
  weighted average of the eight nearest cells that do contain data, including
  the one that contains the cell. If any of the other seven cells contain
  NoData, they are omitted from the average. This a 3D version of the bilinear
  interpolation implemented by the ArcGIS Spatial Analyst's
  :arcpy_sa:`Extract-Values-to-Points` tool.

"""),
    arcGISDisplayName=_('Interpolation method'))

CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'where', GHRSSTLevel4.InterpolateAtArcGISPoints, 'where')
CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'noDataValue', GHRSSTLevel4.InterpolateAtArcGISPoints, 'noDataValue')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'convertToCelsius', GHRSSTLevel4.InterpolateAtArcGISPoints, 'convertToCelsius')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'datasetType', GHRSSTLevel4.InterpolateAtArcGISPoints, 'datasetType')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'timeout', GHRSSTLevel4.InterpolateAtArcGISPoints, 'timeout')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'maxRetryTime', GHRSSTLevel4.InterpolateAtArcGISPoints, 'maxRetryTime')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'cacheDirectory', GHRSSTLevel4.InterpolateAtArcGISPoints, 'cacheDirectory')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'metadataCacheLifetime', GHRSSTLevel4.InterpolateAtArcGISPoints, 'metadataCacheLifetime')
CopyArgumentMetadata(Interpolator.InterpolateArcGISRasterValuesAtPoints, 'orderByFields', GHRSSTLevel4.InterpolateAtArcGISPoints, 'orderByFields')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'numBlocksToCacheInMemory', GHRSSTLevel4.InterpolateAtArcGISPoints, 'numBlocksToCacheInMemory')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'xBlockSize', GHRSSTLevel4.InterpolateAtArcGISPoints, 'xBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'yBlockSize', GHRSSTLevel4.InterpolateAtArcGISPoints, 'yBlockSize')
CopyArgumentMetadata(Interpolator.InterpolateGridsValuesForTableOfPoints, 'tBlockSize', GHRSSTLevel4.InterpolateAtArcGISPoints, 'tBlockSize')

AddResultMetadata(GHRSSTLevel4.InterpolateAtArcGISPoints, 'updatedPoints',
    typeMetadata=ArcGISFeatureLayerTypeMetadata(),
    description=_('Updated points.'),
    arcGISDisplayName=_('Updated points'),
    arcGISParameterDependencies=['points'])

# Public method: GHRSSTLevel4.CannyEdgesAsArcGISRasters

AddMethodMetadata(GHRSSTLevel4.CannyEdgesAsArcGISRasters,
    shortDescription=_('Creates rasters indicating the positions of fronts in `GHRSST <https://podaac.jpl.nasa.gov/GHRSST>`__ Level 4 images published by NASA JPL PO.DAAC, using the Canny edge detection algorithm.'),
    longDescription=_CannyEdgesOverview + '\n\n' + _GHRSSTLevel4_LongDescription % {'name': 'tool'},
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Find Canny Fronts in GHRSST L4 SST'),
    arcGISToolCategory=_('Data Products\\NASA JPL PO.DAAC\\GHRSST L4 SST'),
    dependencies=[ArcGISDependency(), MatlabDependency(), PythonModuleDependency('numpy', cheeseShopName='numpy'), PythonModuleDependency('requests', cheeseShopName='requests'), PythonModuleDependency('netCDF4', cheeseShopName='netCDF4')])

CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'cls', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'cls')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'username', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'username')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'password', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'password')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'shortName', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'shortName')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'outputWorkspace', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'outputWorkspace')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'mode', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'mode')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'highThreshold', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'highThreshold')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'lowThreshold', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'lowThreshold')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'sigma', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'sigma')
CopyArgumentMetadata(CannyEdgeGrid.__init__, 'minSize', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'minSize')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'rotationOffset', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'rotationOffset')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'spatialExtent', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'spatialExtent')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'startDate', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'startDate')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'endDate', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'endDate')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'datasetType', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'datasetType')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'timeout', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'timeout')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'maxRetryTime', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'maxRetryTime')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'cacheDirectory', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'cacheDirectory')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'metadataCacheLifetime', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'metadataCacheLifetime')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'rasterExtension', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'rasterExtension')

AddArgumentMetadata(GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'rasterNameExpressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1, canBeNone=True),
    description=_(
"""List of expressions specifying how the output rasters should be named. If
you do not provide anything, a default naming scheme will be used.

If the output workspace is a file system directory, you may provide one or
more expressions. Each expression defines a level in a directory tree. The
final expression specifies the raster file name. If the output workspace is a
geodatabase, you should provide only one expression, which specifies the
raster name.

Each expression may contain any sequence of characters permitted by the output
workspace. Each expression may optionally contain one or more of the following
case-sensitive codes. The tool replaces the codes with appropriate values when
creating each raster:

* %(ShortName)s - PO.DAAC Short Name of the GHRSST L4 product.

* %(VariableName)s - GHRSST variable represented in the output raster,
  always ``analysed_sst``.

* ``%%Y`` - four-digit year of the raster. This and the following codes are
  only available for datasets that have time coordinates.

* ``%%m`` - two-digit month of the raster.

* ``%%d`` - two-digit day of the month of the raster.

* ``%%j`` - three-digit day of the year of the raster.

* ``%%H`` - two-digit hour of the raster.

* ``%%M`` - two-digit minute of the raster.

* ``%%S`` - two-digit second of the raster.

"""),
    arcGISDisplayName=_('Raster name expressions'),
    arcGISCategory=_('Output raster options'))

CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'calculateStatistics', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'calculateStatistics')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'buildRAT', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'buildRAT')
CopyArgumentMetadata(GHRSSTLevel4.CreateArcGISRasters, 'buildPyramids', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'buildPyramids')

CopyResultMetadata(GHRSSTLevel4.CreateArcGISRasters, 'updatedOutputWorkspace', GHRSSTLevel4.CannyEdgesAsArcGISRasters, 'updatedOutputWorkspace')


###################################################################################################
# This module is not meant to be imported directly. Import GeoEco.DataProducts.NASA.PODAAC instead.
###################################################################################################

__all__ = []
