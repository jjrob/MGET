# _ClimatologicalGridCollectionMetadata.py - Metadata for classes defined in
# _ClimatologicalGridCollection.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from .. import Grid
from ._ClimatologicalGridCollection import ClimatologicalGridCollection


###############################################################################
# Metadata: ClimatologicalGridCollection class
###############################################################################

AddClassMetadata(ClimatologicalGridCollection,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.DatasetCollection` that summarizes a 3D or 4D :class:`~GeoEco.Datasets.Grid` across time into a collection of 2D or 3D :class:`~GeoEco.Datasets.Grid`\\ s representing aggregate values.'))

# Public properties

AddPropertyMetadata(ClimatologicalGridCollection.Statistic,
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Count', 'Maximum', 'Mean', 'Minimum', 'Range', 'Standard_Deviation', 'Sum'], makeLowercase=True),
    shortDescription=_(
"""Statistic to calculate for each cell, one of:

* ``Count`` - number of grids in which the cell had data.

* ``Maximum`` - maximum value for the cell.

* ``Mean`` - mean value for the cell, calculated as the sum divided by the
  count.

* ``Minimum`` - minimum value for the cell.

* ``Range`` - range for the cell, calculated as the maximum minus the
  minimum.

* ``Standard_Deviation`` - sample standard deviation for the cell (i.e. the
  standard deviation estimated using Bessel's correction). In order to
  calculate this, there must be at least two grids with data for the cell.

* ``Sum`` - the sum for the cell.

"""))

AddPropertyMetadata(ClimatologicalGridCollection.BinType,
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Daily', 'Monthly', 'Cumulative', 'ENSO Daily', 'ENSO Monthly', 'ENSO Cumulative'], makeLowercase=True),
    shortDescription=_(
"""Climatology bins to use, one of:

* ``Daily`` - daily bins. Time slices will be classified into bins according
  to their days of the year. The number of days in each bin is determined by
  the Bin Duration (which defaults to 1). The number of bins is calculated by
  dividing 365 by the bin duration. If there is no remainder, then that number
  of bins will be created; slices for the 366th day of leap years will be
  counted in the bin that includes day 365. For example, if the bin duration
  is 5, 73 bins will be created. The first will be for days 1-5, the second
  will be for days 5-10, and so on; the 73rd bin will be for days 361-365
  during normal years and 361-366 during leap years. If dividing 365 by the
  bin duration does yield a remainder, then one additional bin will be created
  to hold the remaining days. For example, if the bin duration is 8, 46 bins
  will be created. The first will be for days 1-8, the second for days 9-16,
  and so on; the 46th will be for days 361-365 during normal years and 361-366
  during leap years.

* ``Monthly`` - monthly bins. Time slices will be classified into bins
  according to their months of the year. The number of months in each bin is
  determined by the Bin Duration (which defaults to 1). The number of bins is
  calculated by dividing 12 by the bin duration. If there is no remainder,
  then that number of bins will be created. For example, if the bin duration
  is 3, there will be four bins: January-March, April-June, July-September,
  and October-December. If there is a remainder, then one additional bin will
  be created. For example, if the bin duration is 5, 3 bins will be created:
  January-May, June-October, November-December.

* ``Cumulative`` - one bin. A single climatology raster will be calculated
  from the entire dataset. The Bin Duration is ignored.

* ``ENSO Daily``, ``ENSO Monthly``, ``ENSO Cumulative`` - the same as above,
  except each of the bins above will be split into three, based on the phase
  of the `El Niño Southern Oscillation (ENSO)
  <https://en.wikipedia.org/wiki/ENSO>`_, as determined by the Oceanic Niño
  Index (ONI) calculated by the `NOAA NCEP Climate Prediction Center
  <https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ensoyears.shtml>`_.
  The ONI classifies each month into one of three phases: neutral, El Niño, or
  La Niña. This tool first classifies time slices according to their dates
  into ENSO phases (it downloads ONI data from the `NOAA Physical Sciences
  Laboratory <https://psl.noaa.gov/data/climateindices/list/>`_), then
  produces a climatology bin for each phase. For example, if you request
  ``ENSO Cumulative`` bins, three bins will be produced: one for all time
  slices occurring in neutral months, one for all in El Niño months, and one
  for all in La Niña months. If you request ``ENSO Monthly`` bins, 36 bins
  will be produced: one for each combination of the 12 months and the three
  ENSO phases.

For ``Daily`` and ``Monthly``, to adjust when the bins start (e.g. to center a
4-bin seasonal climatology on solstices and equinoxes), use the Start Day Of
The Year parameter.

"""))

AddPropertyMetadata(ClimatologicalGridCollection.BinDuration,
    typeMetadata=IntegerTypeMetadata(minValue=1),
    shortDescription=_(
"""Duration of each bin, in days or months, when the Bin Type is
``Daily``/``ENSO Daily`` or ``Monthly``/``ENSO Monthly``, respectively. The
default is 1. See Bin Type for more information."""))

AddPropertyMetadata(ClimatologicalGridCollection.StartDayOfYear,
    typeMetadata=IntegerTypeMetadata(minValue=1, maxValue=365),
    shortDescription=_(
"""Use this to create bin defintions that deviate from the traditional
calendar. The interpretation of this depends on the Bin Type:

* If Bin Type is ``Daily`` or ``ENSO Daily``, then Start Day of Year defines
  the day of the year of the first climatology bin. For example, if Start Day
  of Year is 100 and the Bin Duration is 10, the first bin will be numbered
  100-109. The bin spanning the end of the year will be numbered 360-004. The
  last bin will be numbered 095-099. To define a four-bin climatology with
  bins that are centered approximately on the equinoxes and solstices (i.e., a
  seasonal climatology), set the Bin Duration to 91 and the start day to 36
  (February 5). This will produce bins with dates 036-126, 127-217, 218-308,
  and 309-035.

* If Bin Type is ``Monthly`` or ``ENSO Monthly``, then Start Day of Year
  defines the day of the year of the first climatology bin, and the day of the
  month of that bin will be used as the first day of the month of all of the
  bins. For example, if Start Day of Year is 46, which is February 15, and the
  Bin Duration is 1, then the bins will be February 15 - March 14, March 15 -
  April 14, April 15 - May 14, and so on. Calculations involving Start Day of
  Year always assume a 365 day year (a non-leap year). To define a four-bin
  climatology using the months traditionally associated with spring, summer,
  fall, and winter in many northern hemisphere cultures, set the Bin Duration
  to 3 and the start day to 60 (March 1). This will produce bins with months
  03-05, 06-08, 09-11, and 12-02.

* If Bin Type is ``Cumulative`` or ``ENSO Cumulative``, then Start Day of Year
  is ignored.

"""))

AddPropertyMetadata(ClimatologicalGridCollection.ReportProgress,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_(
"""If True, progress messages will be reported tracking the computation of
each grid in the climatology from the time slices that make it up. The
computations do not occur until you attempt to access the data of the
climatological grids. Tracking the computation of each individual
climatological grid can be helpful if they span many time slices, as might
occur with a cumulative climatology of many years of daily time slices. In
these cases, the computations may take a number of minutes, and the progress
messages can help you estimate the time of completion. Conversely, if there
are many grids in the climatology and they span only a few time slices, having
progress reports generated for each grid can be too much information to be
helpful."""))

# Constructor

AddMethodMetadata(ClimatologicalGridCollection.__init__,
    shortDescription=_('ClimatologicalGridCollection constructor.'))

AddArgumentMetadata(ClimatologicalGridCollection.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClimatologicalGridCollection),
    description=_(':class:`%s` instance.') % ClimatologicalGridCollection.__name__)

AddArgumentMetadata(ClimatologicalGridCollection.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to summarize. It must have a t (time) dimension.'))

AddArgumentMetadata(ClimatologicalGridCollection.__init__, 'statistic',
    typeMetadata=ClimatologicalGridCollection.Statistic.__doc__.Obj.Type,
    description=ClimatologicalGridCollection.Statistic.__doc__.Obj._ShortDescription,
    arcGISDisplayName=_('Statistic'))

AddArgumentMetadata(ClimatologicalGridCollection.__init__, 'binType',
    typeMetadata=ClimatologicalGridCollection.BinType.__doc__.Obj.Type,
    description=ClimatologicalGridCollection.BinType.__doc__.Obj._ShortDescription,
    arcGISDisplayName=_('Climatology bin type'))

AddArgumentMetadata(ClimatologicalGridCollection.__init__, 'binDuration',
    typeMetadata=ClimatologicalGridCollection.BinDuration.__doc__.Obj.Type,
    description=ClimatologicalGridCollection.BinDuration.__doc__.Obj._ShortDescription,
    arcGISDisplayName=_('Climatology bin duration'),
    arcGISCategory=_('Climatology options'))

AddArgumentMetadata(ClimatologicalGridCollection.__init__, 'startDayOfYear',
    typeMetadata=ClimatologicalGridCollection.StartDayOfYear.__doc__.Obj.Type,
    description=ClimatologicalGridCollection.StartDayOfYear.__doc__.Obj._ShortDescription,
    arcGISDisplayName=_('Climatology start day of the year'),
    arcGISCategory=_('Climatology options'))

AddArgumentMetadata(ClimatologicalGridCollection.__init__, 'reportProgress',
    typeMetadata=ClimatologicalGridCollection.ReportProgress.__doc__.Obj.Type,
    description=ClimatologicalGridCollection.ReportProgress.__doc__.Obj.ShortDescription)

AddResultMetadata(ClimatologicalGridCollection.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=ClimatologicalGridCollection),
    description=_(':class:`%s` instance.') % ClimatologicalGridCollection.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
