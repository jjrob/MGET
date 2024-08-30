# _CannyEdgeGridMetadata.py - Metadata for classes defined in
# _CannyEdgeGrid.py.
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
from ._CannyEdgeGrid import CannyEdgeGrid, _CannyEdgesOverview


###############################################################################
# Metadata: CannyEdgeGrid class
###############################################################################

AddClassMetadata(CannyEdgeGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` that represents the edges in another :class:`~GeoEco.Datasets.Grid` using the Canny edge detection algorithm..'),
    longDescription=_CannyEdgesOverview + _("""

Example usage:

.. code-block:: python

    # Load a sea surface temperature raster.

    from GeoEco.Datasets.GDAL import GDALDataset
    grid = GDALDataset.GetRasterBand(r'/home/jason/test/thetao_0000.5_20210101.img')

    # Instantiate a CannyEdgeGrid using the default parameters. The edges
    # won't be detected until data are requested from the CannyEdgeGrid
    # instance, which will happen when we write the output raster below.

    from GeoEco.Datasets.Virtual import CannyEdgeGrid
    edgeGrid = CannyEdgeGrid(grid)

    # Write the output raster.

    GDALDataset.CreateRaster('/home/jason/test/thetao_0000.5_20210101_fronts.img', edgeGrid)
"""))

# Constructor

AddMethodMetadata(CannyEdgeGrid.__init__,
    shortDescription=_('CannyEdgeGrid constructor.'),
    dependencies=[MatlabDependency()])

AddArgumentMetadata(CannyEdgeGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=CannyEdgeGrid),
    description=_(':class:`%s` instance.') % CannyEdgeGrid.__name__)

AddArgumentMetadata(CannyEdgeGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(
""":class:`~GeoEco.Datasets.Grid` in which to detect edges. If it is 3D or 4D,
edges will be detected in each 2D time and/or depth slice."""))

AddArgumentMetadata(CannyEdgeGrid.__init__, 'highThreshold',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., mustBeLessThan=1., canBeNone=True),
    description=_(
"""High threshold for the Canny edge detection algorithm. The Canny algorithm
uses the high threshold to find "strong edges", which are pixels that have
such a high gradient magnitude that they may confidently be classified as
edges. These are pixels where those that surround them show a strong increase
or decrease in value as you move across the image in some direction. The units
of the Canny thresholds are the change in the units of the image per pixel
traveled. For example, if the image represents sea surface temperature in
degrees C, the units are change in degrees C per pixel.

If you do not provide a value, one will be chosen automatically based on the
data within the image. If you are detecting edges in multiple images, a value
will be selected for each image separately.

If you do not know what value to use, try the automatic selection and check
the results carefully to see if they are acceptable for your problem. If not,
you may select a value by trial and error. To see the values selected
automatically, you enable verbose logging. (Please consult the MGET team for
help with this, if necessary.)

Increasing the high threshold will reduce the number of edges detected;
reducing it will increase the number of edges detected."""),
    arcGISDisplayName=_('High threshold'),
    arcGISCategory=_('Canny algorithm parameters'))

AddArgumentMetadata(CannyEdgeGrid.__init__, 'lowThreshold',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., mustBeLessThan=1., canBeNone=True),
    description=_(
"""Low threshold for the Canny edge detection algorithm. If you supply a low
threshold, you must also supply a high threshold. The low threshold must be
less than the high threshold.

After using the high threshold to find "strong edges", the Canny algorithm
uses the low threshold to find "weak edges", which are those that have a
gradient magnitude that is high enough that they might be edges, but not so
high that they may be confidently classified as edges on the basis of their
gradient magnitude alone. After identifying the weak edge pixels, the
algorithm checks whether 8-connected groups of weak pixels are connected to
strong ones (i.e. whether they touch them horizontally, vertically, or
diagonally). Groups of weak pixels that do not touch a strong pixel are
discarded. This approach essentially allows the strong edges to be "extended"
by the weak ones.

The units of the Canny thresholds are the change in the units of the image per
pixel traveled. For example, if the image represents sea surface temperature
in degrees C, the units are change in degrees C per pixel.

If you do not provide a value, one will be chosen automatically based on the
data within the image. If you are detecting edges in multiple images, a value
will be selected for each image separately. The value selected will be the
high threshold multiplied by 0.4.

If you do not know what value to use, try the automatic selection and check
the results carefully to see if they are acceptable for your problem. If not,
you may select a value by trial and error. To see the values selected
automatically, you enable verbose logging. (Please consult the MGET team for
help with this, if necessary.)

Increasing the low threshold will reduce the number of edges detected;
reducing it will increase the number of edges detected."""),
    arcGISDisplayName=_('Low threshold'),
    arcGISCategory=_('Canny algorithm parameters'))

AddArgumentMetadata(CannyEdgeGrid.__init__, 'sigma',
    typeMetadata=FloatTypeMetadata(mustBeGreaterThan=0., canBeNone=True),
    description=_(
"""Sigma parameter for the Gaussian filter applied by the Canny edge detection
algorithm. As its first step, before performing edge detection, the Canny
algorithm applies a Gaussian filter to the image to smooth out noise. The
sigma parameter controls the degree of smoothing. Higher values producing more
smoothing, resulting in fewer detected edges. Lower values yield less
smoothing and more detected edges.

If you do not provide a value, the square root of 2 will be used by default.
This is a good value for many problems. If your image is very noisy, you might
need a higher value. Try increasing it a little bit at a time (e.g. by 0.1 or
0.2). Be careful not to increase it too much; otherwise it may smooth out the
edges that you are trying to detect. If your image is not very noisy--e.g. it
is from an ocean model that produces theoretical results that do not contain
noise--consider reducing the value to 1 or less (it must be greater than zero,
however).

It is not necessary to specify the window size of the Gaussian filter; the
algorithm automatically selects the optimal window size based on the value of
the sigma parameter."""),
    arcGISDisplayName=_('Sigma'),
    arcGISCategory=_('Canny algorithm parameters'))

AddArgumentMetadata(CannyEdgeGrid.__init__, 'minSize',
    typeMetadata=IntegerTypeMetadata(mustBeGreaterThan=0, canBeNone=True),
    description=_(
"""Minimum number of pixels an individual edge must occupy for it to be
retained. Edges with fewer number of pixels will be discarded. For this
option, an "edge" is defined as the chain of pixels that are 8-connected (i.e.
they are connected horizontally, vertically, or diagonally). The edge may be
any shape, such as long and thin and branching or short and blob-like.

This option is applied after the Canny algorithm is complete. If a value is
not provided, all edges will be retained."""),
    arcGISDisplayName=_('Minimum edge size'),
    arcGISCategory=_('Canny algorithm parameters'))

AddResultMetadata(CannyEdgeGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=CannyEdgeGrid),
    description=_(':class:`%s` instance.') % CannyEdgeGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = ['_CannyEdgesOverview']
