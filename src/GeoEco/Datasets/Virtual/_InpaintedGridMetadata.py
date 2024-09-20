# _InpaintedGridMetadata.py - Metadata for classes defined in
# _InpaintedGrid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Internationalization import _
from ...Matlab import MatlabDependency
from ...Metadata import *
from ...Types import *

from .. import Grid
from ._InpaintedGrid import InpaintedGrid


###############################################################################
# Metadata: InpaintedGrid class
###############################################################################

AddClassMetadata(InpaintedGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that fills missing (NoData) values in another :class:`~GeoEco.Datasets.Grid` using a partial differential equation method.'),
    longDescription=_(
"""This tool is implemented in MATLAB using the `inpaint_nans
<https://www.mathworks.com/matlabcentral/fileexchange/4551-inpaint_nans>`_
function developed by John D'Errico. Many thanks to him for developing and
sharing this function. Please see GeoEco's LICENSE file for the relevant
copyright statement.

To run this tool, you either must have MATLAB R2024b or MATLAB Runtime R2024b
installed. The MATLAB Runtime is free and may be downloaded from
https://www.mathworks.com/help/compiler/install-the-matlab-runtime.html.
Please follow the installation instructions carefully. Version R2024b must be
used; other versions will not work. MATLAB Runtime allows multiple versions
can be installed at the same time.

Example usage:

.. code-block:: python

    # Load a chlorophyll concentration raster that is missing some values.

    from GeoEco.Datasets.GDAL import GDALDataset
    grid = GDALDataset.GetRasterBand('/home/jason/inpaint_test/GSMChl_2006160.img')

    # Fill in contiguous blocks of missing values that are less than 200 cells
    # in size. This size was chosen arbitrarily for this example. You might
    # prefer a smaller or larger size for your application.

    from GeoEco.Datasets.Virtual import InpaintedGrid
    inpaintedGrid = InpaintedGrid(grid, maxHoleSize=200)

    # Write the output raster.

    GDALDataset.CreateRaster('/home/jason/inpaint_test/GSMChl_2006160_filled.img', inpaintedGrid)
"""))

# Constructor

AddMethodMetadata(InpaintedGrid.__init__,
    shortDescription=_('InpaintedGrid constructor.'),
    dependencies=[MatlabDependency()])

AddArgumentMetadata(InpaintedGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=InpaintedGrid),
    description=_(':class:`%s` instance.') % InpaintedGrid.__name__)

AddArgumentMetadata(InpaintedGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` to fill. Its :attr:`~GeoEco.Datasets.Grid.ScaledDataType` must be ``float32`` or ``float64``.'))

AddArgumentMetadata(InpaintedGrid.__init__, 'method',
    typeMetadata=UnicodeStringTypeMetadata(makeLowercase=True, allowedValues=['Del2a', 'Del2b', 'Del2c', 'Del4', 'Spring']),
    description=_(
"""Method to use for interpolation and extrapolation of NoData values. One
of:

* ``Del2a`` - Performs Laplacian interpolation and linear extrapolation.

* ``Del2b`` - Same as ``Del2a`` but does not build as large a linear system of
  equations. May use less memory and be faster than ``Del2a``, at the cost of
  some accuracy. Use this method if ``Del2a`` fails due to insufficient memory
  or if it is too slow.

* ``Del2c`` - Same as ``Del2a`` but solves a direct linear system of equations
  for the NoData values. Faster than both ``Del2a`` and ``Del2b`` but is the
  least robust to noise on the boundaries of NoData cells and least able to
  interpolate accurately for smooth surfaces. Use this method if ``Del2a`` and
  ``Del2b`` both fail due to insufficient memory or are too slow.

* ``Del4`` - Same as ``Del2a`` but instead of the Laplace operator (also
  called the ∇\\ :sup:`2` operator) it uses the biharmoic operator (also
  called the ∇\\ :sup:`4` operator). May result in more accurate
  interpolations, at some cost in speed.

* ``Spring`` - Uses a spring metaphor. Assumes springs (with a nominal length
  of zero) connect each cell with every neighbor (horizontally, vertically and
  diagonally). Since each cell tries to be like its neighbors, extrapolation
  is as a constant function where this is consistent with the neighboring
  nodes.

"""))

AddArgumentMetadata(InpaintedGrid.__init__, 'maxHoleSize',
    typeMetadata=IntegerTypeMetadata(mustBeGreaterThan=0, canBeNone=True),
    description=_(
"""Maximum size, in cells, that a region of 4-connected NoData cells may be
for it to be filled in. Use this option to prevent the filling of large NoData
regions (e.g. large clouds in remote sensing images) when you are concerned
that values cannot be accurately guessed for those regions. If this option is
omitted, all regions will be filled, regardless of size."""))

AddArgumentMetadata(InpaintedGrid.__init__, 'xEdgesWrap',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the left and right edges of the grid are assumed to be connected
and computations along those edges will consider the values on the opposite
side of the grid."""))

AddArgumentMetadata(InpaintedGrid.__init__, 'minValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Minimum allowed value to use when NoData cells are interpolated (or
extrapolated). If this parameter is provided, all cells with less than the
minimum value will be rounded up to the minimum. This includes not just the
cells that had NoData in the original grid and were then interpolated or
extrapolated, but also the cells that had values in the original grid.

Use this parameter when the interpolation/extrapolation algorithm produces
impossibly low values. For example, consider a situation in which a
chlorophyll concentration grid coincidentally shows a negative gradient
approaching a cloud that straddles the edge of the grid. Missing pixels at the
edge of the grid will be filled by extrapolation. If the negative gradient is
strong enough, the algorithm might extrapolate negative concentrations for the
cloudy pixels. This should be impossible; chlorophyll concentration must be
zero or higher. To enforce that, you could specify a minimum value of zero (or
a very small non-zero number, if exactly zero would be problematic, as might
occur if the values were in a log scale)."""))

AddArgumentMetadata(InpaintedGrid.__init__, 'maxValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""Maximum allowed value to use when NoData cells are interpolated (or
extrapolated). If this parameter is provided, all cells with greater than the
maximum value will be rounded up to the maximum. This includes not just the
cells that had NoData in the original grid and were then interpolated or
extrapolated, but also the cells that had values in the original grid.

Use this parameter when the interpolation/extrapolation algorithm produces
impossibly high values. For example, consider a situation in which a percent
sea ice concentration grid shows a positive gradient approaching the coastline
but does not provide data right up to shore. Say you wanted to fill the
missing cells close to shore and were willing to assume that whatever gradient
occurred nearby was reasonable for filling them in. If the positive gradient
is strong enough, the algorithm might extrapolate ice concentration values
greater than 100 percent, which is impossible. To prevent values from
exceeding 100 percent, you could specify a maximum value of 100."""))

AddResultMetadata(InpaintedGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=InpaintedGrid),
    description=_(':class:`%s` instance.') % InpaintedGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
