# _FastMarchingDistanceGridMetadata.py - Metadata for classes defined in
# _FastMarchingDistanceGrid.py.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...Dependencies import PythonModuleDependency
from ...Internationalization import _
from ...Metadata import *
from ...Types import *

from .. import Grid
from ._FastMarchingDistanceGrid import FastMarchingDistanceGrid


###############################################################################
# Metadata: FastMarchingDistanceGrid class
###############################################################################

AddClassMetadata(FastMarchingDistanceGrid,
    module=__package__,
    shortDescription=_('A :class:`~GeoEco.Datasets.Grid` representing distances to features in another :class:`~GeoEco.Datasets.Grid`, computed with a fast marching algorithm.'),
    longDescription=_(
"""To compute fast marching distances, :class:`FastMarchingDistanceGrid` first
classifies the cells of the provided :class:`~GeoEco.Datasets.Grid` based on
their values:

* Cells with values of zero or less represent features to which distances
  should be calculated, called *inside* cells below.

* Cells with positive values represent areas that can be moved through, e.g.
  the ocean, called *outside* cells.

* Cells of NoData represent obstacles that cannot be moved through (e.g.
  land), called *barrier* cells.

The interfaces where inside and outside cells touch each other are called the
feature *edges*. Where inside and outside cells touch along a straight row or
column, the edge is a straight line located exactly where the cells meet. When
the feature has a "corner", the edge is rounded and curved within the inside
cell.

Fast marching distances are computed for both inside and outside cells.
Distances are negative for inside cells and positive for outside cells.
Distances are computed as the shortest path from the given cell to the closest
edge, and will be positive for outside cells and negative for inside cells. If
you instead want the distances for inside cells to zero throughout the
feature, set `minDist` to zero.

Example usage:

.. code-block:: python

    # Load the study area raster and get the first band as a GDALRasterGrid.

    from GeoEco.Datasets.GDAL import GDALDataset
    dataset = GDALDataset('/home/jason/fast_marching_test/Study_Area.img')
    grid = dataset.QueryDatasets(reportProgress=False)[0]

    # This band uses an int32 data type and has values of 0 for land and 1 for
    # water. Every cell has data. First, extract the band's data as a numpy array.
    # Then, in that array, set land (0) to NoData. Note that we do not want set
    # values of grid.Data itself (e.g. grid.Data[...] = ...) because this will
    # write values into the raster file, which we do not want to change. Also,
    # Grid does not support indexing with numpy arrays (e.g. data == 0).

    data = grid.Data[:]
    data[data == 0] = grid.NoDataValue

    # We are now representing land as NoData, which FastMarchingDistanceGrid
    # expects. Now set several cells that are currently marked as 1 to 0. These
    # new 0 cells represent the feature we will computing distances to. We know
    # the approximate coordinates of the centers of these cells and use a Grid
    # function to look up their integer indices, and then use those to set the
    # cell values. (These are in a projected coordinate system with meters as the
    # linear unit, which is why they are very large.)

    cellCoordsYX = [(1607000, 2882000),
                    (1602000, 2882000),
                    (1597000, 2882000),
                    (1592000, 2882000),
                    (1587000, 2882000),
                    (1582000, 2882000),
                    (1577000, 2877000),
                    (1572000, 2877000),
                    (1567000, 2877000),
                    (1562000, 2877000),]

    cellIndicesYX = [grid.GetIndicesForCoords(coords) for coords in cellCoordsYX]

    for indices in cellIndicesYX:
        data[indices[0], indices[1]] = -1

    # Create a NumpyGrid from the original band, then write our new data into it.

    from GeoEco.Datasets import NumpyGrid
    numpyGrid = NumpyGrid.CreateFromGrid(grid)
    numpyGrid.Data[:] = data

    # Construct the FastMarchingDistanceGrid. Set minDist to 0, so that cells
    # within the feature we defined above will have a distance of 0, rather than a
    # negative distance (from the cell center to the edge). Constructing this grid
    # does not perform the calculation; that is deferred until the grid's Data
    # property is accessed.

    from GeoEco.Datasets.Virtual import FastMarchingDistanceGrid
    fmdGrid = FastMarchingDistanceGrid(numpyGrid, minDist=0)

    # We want to write the FastMarchingDistanceGrid out as a raster with GDAL.
    # Construct a DirectoryTree that we can import it into. Note that because we
    # are just going to import this single raster, we can specify the destination
    # file name in pathCreationExpressions, and not have to define a
    # QueryableAttribute that gives the file name.

    from GeoEco.Datasets.Collections import DirectoryTree
    dirTree = DirectoryTree(path='/home/jason/fast_marching_test',
                            datasetType=GDALDataset,
                            pathCreationExpressions=['Distance.img'])

    # Import the grid into the DirectoryTree.

    dirTree.ImportDatasets([fmdGrid], mode='Replace', calculateStatistics=True)

"""))

# Public properties

AddPropertyMetadata(FastMarchingDistanceGrid.MinDist,
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    shortDescription=_('Minimum allowed distance. If it is provided, distances less than this will be rounded up to it.'))

AddPropertyMetadata(FastMarchingDistanceGrid.MaxDist,
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    shortDescription=_('Maximum allowed distance. If it is provided, distances greater than this will be rounded down to it.'))

# Constructor

AddMethodMetadata(FastMarchingDistanceGrid.__init__,
    shortDescription=_('FastMarchingDistanceGrid constructor.'),
    dependencies=[PythonModuleDependency('skfmm', cheeseShopName='scikit-fmm')])

AddArgumentMetadata(FastMarchingDistanceGrid.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=FastMarchingDistanceGrid),
    description=_(':class:`%s` instance.') % FastMarchingDistanceGrid.__name__)

AddArgumentMetadata(FastMarchingDistanceGrid.__init__, 'grid',
    typeMetadata=ClassInstanceTypeMetadata(cls=Grid),
    description=_(':class:`~GeoEco.Datasets.Grid` for which distances should be computed. Typically, it has 2 dimensions. If it has 3 or 4 dimensions, distances will be computed for each 2D slice.'))

AddArgumentMetadata(FastMarchingDistanceGrid.__init__, 'minDist',
    typeMetadata=FastMarchingDistanceGrid.MinDist.__doc__.Obj.Type,
    description=FastMarchingDistanceGrid.MinDist.__doc__.Obj.ShortDescription)

AddArgumentMetadata(FastMarchingDistanceGrid.__init__, 'maxDist',
    typeMetadata=FastMarchingDistanceGrid.MaxDist.__doc__.Obj.Type,
    description=FastMarchingDistanceGrid.MaxDist.__doc__.Obj.ShortDescription)

AddResultMetadata(FastMarchingDistanceGrid.__init__, 'obj',
    typeMetadata=ClassInstanceTypeMetadata(cls=FastMarchingDistanceGrid),
    description=_(':class:`%s` instance.') % FastMarchingDistanceGrid.__name__)


###########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Virtual instead.
###########################################################################################

__all__ = []
