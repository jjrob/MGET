# _AggregateGridMetadata.py - Metadata for classes defined in
# _AggregateGrid.py.
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
from ._AggregateGrid import AggregateGrid


###############################################################################
# Metadata: AggregateGrid class
###############################################################################

AddClassMetadata(AggregateGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` built by statistically summarizing a list of :class:`~GeoEco.Datasets.Grid`\\ s on a per-cell basis.'))

# Public properties

AddPropertyMetadata(AggregateGrid.ReportProgress,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_(
"""If True, progress messages will be reported as the computation of the
aggregate grid proceeds. This can be helpful if many many grids are
aggregated and the computation takes a long time."""))

# Constructor

AddMethodMetadata(AggregateGrid.__init__,
    shortDescription=_('AggregateGrid constructor.'))

AddArgumentMetadata(AggregateGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=AggregateGrid),
    description=_(':class:`%s` instance.') % AggregateGrid.__name__)

AddArgumentMetadata(AggregateGrid.__init__, 'grids',
    typeMetadata=ListTypeMetadata(elementType=ClassInstanceTypeMetadata(cls=Grid), minLength=1),
    description=_('A :py:class:`list` of :class:`~GeoEco.Datasets.Grid`\\ s to summarize. They must all have the same dimensions and shape.'))

AddArgumentMetadata(AggregateGrid.__init__, 'statistic',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['Count', 'Maximum', 'Mean', 'Minimum', 'Range', 'Standard_Deviation', 'Sum'], makeLowercase=True),
    description=_(
"""Statistic to calculate for each cell, one of:

* ``Count`` - number of images in which the cell had data.

* ``Maximum`` - maximum value for the cell.

* ``Mean`` - mean value for the cell, calculated as the sum divided by the
  count.

* ``Minimum`` - minimum value for the cell.

* ``Range`` - range for the cell, calculated as the maximum minus the minimum.

* ``Standard_Deviation`` - sample standard deviation for the cell (i.e. the
  standard deviation estimated using Bessel's correction). In order to
  calculate this, there must be at least two images with data for the cell.

* ``Sum`` - the sum for the cell.

"""),
    arcGISDisplayName=_('Statistic'))

AddArgumentMetadata(AggregateGrid.__init__, 'displayName',
    typeMetadata=Grid.DisplayName.__doc__.Obj.Type,
    description=Grid.DisplayName.__doc__.Obj.ShortDescription)

AddArgumentMetadata(AggregateGrid.__init__, 'reportProgress',
    typeMetadata=AggregateGrid.ReportProgress.__doc__.Obj.Type,
    description=AggregateGrid.ReportProgress.__doc__.Obj.ShortDescription)

CopyArgumentMetadata(Grid.__init__, 'parentCollection', AggregateGrid.__init__, 'parentCollection')
CopyArgumentMetadata(Grid.__init__, 'queryableAttributes', AggregateGrid.__init__, 'queryableAttributes')
CopyArgumentMetadata(Grid.__init__, 'queryableAttributeValues', AggregateGrid.__init__, 'queryableAttributeValues')

AddResultMetadata(AggregateGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=AggregateGrid),
    description=_(':class:`%s` instance.') % AggregateGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
