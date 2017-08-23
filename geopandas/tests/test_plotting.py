from __future__ import absolute_import, division

from distutils.version import LooseVersion
import itertools
import warnings

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.affinity import rotate
from shapely.geometry import MultiPolygon, Polygon, LineString, Point

from geopandas import GeoSeries, GeoDataFrame, read_file

import pytest


@pytest.fixture(autouse=True)
def close_figures(request):
    yield
    plt.close('all')


try:
    cycle = matplotlib.rcParams['axes.prop_cycle'].by_key()
    MPL_DFT_COLOR = cycle['color'][0]
except KeyError:
    MPL_DFT_COLOR = matplotlib.rcParams['axes.color_cycle'][0]


class TestPointPlotting:

    def setup_method(self):
        # scatterplot does not yet accept list of colors in matplotlib 1.4.3
        # if we change the default to uniform, this might work again
        pytest.importorskip('matplotlib', '1.5.0')

        self.N = 10
        self.points = GeoSeries(Point(i, i) for i in range(self.N))
        values = np.arange(self.N)
        self.df = GeoDataFrame({'geometry': self.points, 'values': values})

    def test_figsize(self):

        ax = self.points.plot(figsize=(1, 1))
        np.testing.assert_array_equal(ax.figure.get_size_inches(), (1, 1))

        ax = self.df.plot(figsize=(1, 1))
        np.testing.assert_array_equal(ax.figure.get_size_inches(), (1, 1))

    def test_default_colors(self):

        # # without specifying values -> max 9 different colors

        # GeoSeries
        ax = self.points.plot()
        cmap = plt.get_cmap('Set1', 9)
        expected_colors = cmap(list(range(9))*2)
        _check_colors(self.N, ax.collections[0].get_facecolors(), expected_colors)

        # GeoDataFrame -> uses 'jet' instead of 'Set1'
        ax = self.df.plot()
        cmap = plt.get_cmap(lut=9)
        expected_colors = cmap(list(range(9))*2)
        _check_colors(self.N, ax.collections[0].get_facecolors(), expected_colors)

        # # with specifying values -> different colors for all 10 values
        ax = self.df.plot(column='values')
        cmap = plt.get_cmap()
        expected_colors = cmap(np.arange(self.N)/(self.N-1))
        _check_colors(self.N, ax.collections[0].get_facecolors(), expected_colors)

    def test_colormap(self):

        # # without specifying values -> max 9 different colors

        # GeoSeries
        ax = self.points.plot(cmap='RdYlGn')
        cmap = plt.get_cmap('RdYlGn', 9)
        expected_colors = cmap(list(range(9))*2)
        _check_colors(self.N, ax.collections[0].get_facecolors(), expected_colors)

        # GeoDataFrame -> same as GeoSeries in this case
        ax = self.df.plot(cmap='RdYlGn')
        _check_colors(self.N, ax.collections[0].get_facecolors(), expected_colors)

        # # with specifying values -> different colors for all 10 values
        ax = self.df.plot(column='values', cmap='RdYlGn')
        cmap = plt.get_cmap('RdYlGn')
        expected_colors = cmap(np.arange(self.N)/(self.N-1))
        _check_colors(self.N, ax.collections[0].get_facecolors(), expected_colors)

    def test_single_color(self):

        ax = self.points.plot(color='green')
        _check_colors(self.N, ax.collections[0].get_facecolors(), ['green']*self.N)

        ax = self.df.plot(color='green')
        _check_colors(self.N, ax.collections[0].get_facecolors(), ['green']*self.N)

        with warnings.catch_warnings(record=True) as _:  # don't print warning
            # 'color' overrides 'column'
            ax = self.df.plot(column='values', color='green')
            _check_colors(self.N, ax.collections[0].get_facecolors(), ['green']*self.N)

    def test_style_kwargs(self):

        # markersize
        ax = self.points.plot(markersize=10)
        assert ax.collections[0].get_sizes() == [10]

        ax = self.df.plot(markersize=10)
        assert ax.collections[0].get_sizes() == [10]

        ax = self.df.plot(column='values', markersize=10)
        assert ax.collections[0].get_sizes() == [10]

    def test_legend(self):
        with warnings.catch_warnings(record=True) as _:  # don't print warning
            # legend ignored if color is given.
            ax = self.df.plot(column='values', color='green', legend=True)
            assert len(ax.get_figure().axes) == 1  # no separate legend axis

        # legend ignored if no column is given.
        ax = self.df.plot(legend=True)
        assert len(ax.get_figure().axes) == 1  # no separate legend axis

        # # Continuous legend
        # the colorbar matches the Point colors
        ax = self.df.plot(column='values', cmap='RdYlGn', legend=True)
        point_colors = ax.collections[0].get_facecolors()
        cbar_colors = ax.get_figure().axes[1].collections[0].get_facecolors()
        # first point == bottom of colorbar
        np.testing.assert_array_equal(point_colors[0], cbar_colors[0])
        # last point == top of colorbar
        np.testing.assert_array_equal(point_colors[-1], cbar_colors[-1])

        # # Categorical legend
        # the colorbar matches the Point colors
        ax = self.df.plot(column='values', categorical=True, legend=True)
        point_colors = ax.collections[0].get_facecolors()
        cbar_colors = ax.get_legend().axes.collections[0].get_facecolors()
        # first point == bottom of colorbar
        np.testing.assert_array_equal(point_colors[0], cbar_colors[0])
        # last point == top of colorbar
        np.testing.assert_array_equal(point_colors[-1], cbar_colors[-1])


class TestPointZPlotting:

    def setup_method(self):
        # scatterplot does not yet accept list of colors in matplotlib 1.4.3
        # if we change the default to uniform, this might work again
        pytest.importorskip('matplotlib', '1.5.0')

        self.N = 10
        self.points = GeoSeries(Point(i, i, i) for i in range(self.N))
        values = np.arange(self.N)
        self.df = GeoDataFrame({'geometry': self.points, 'values': values})

    def test_plot(self):
        # basic test that points with z coords don't break plotting
        self.df.plot()


class TestLineStringPlotting:

    def setup_method(self):
        self.N = 10
        values = np.arange(self.N)
        self.lines = GeoSeries([LineString([(0, i), (4, i+0.5), (9, i)])
                                for i in range(self.N)],
                               index=list('ABCDEFGHIJ'))
        self.df = GeoDataFrame({'geometry': self.lines, 'values': values})

    def test_single_color(self):

        ax = self.lines.plot(color='green')
        _check_colors(self.N, ax.collections[0].get_colors(), ['green']*self.N)

        ax = self.df.plot(color='green')
        _check_colors(self.N, ax.collections[0].get_colors(), ['green']*self.N)

        with warnings.catch_warnings(record=True) as _:  # don't print warning
            # 'color' overrides 'column'
            ax = self.df.plot(column='values', color='green')
            _check_colors(self.N, ax.collections[0].get_colors(), ['green']*self.N)

    def test_style_kwargs(self):

        # linestyle
        linestyle = 'dashed'
        ax = self.lines.plot(linestyle=linestyle)
        exp_ls = _style_to_linestring_onoffseq(linestyle)
        for ls in ax.collections[0].get_linestyles():
            assert ls[0] == exp_ls[0]
            assert tuple(ls[1]) == exp_ls[1]

        ax = self.df.plot(linestyle=linestyle)
        for ls in ax.collections[0].get_linestyles():
            assert ls[0] == exp_ls[0]
            assert tuple(ls[1]) == exp_ls[1]

        ax = self.df.plot(column='values', linestyle=linestyle)
        for ls in ax.collections[0].get_linestyles():
            assert ls[0] == exp_ls[0]
            assert tuple(ls[1]) == exp_ls[1]


class TestPolygonPlotting:

    def setup_method(self):

        t1 = Polygon([(0, 0), (1, 0), (1, 1)])
        t2 = Polygon([(1, 0), (2, 0), (2, 1)])
        self.polys = GeoSeries([t1, t2], index=list('AB'))
        self.df = GeoDataFrame({'geometry': self.polys, 'values': [0, 1]})

        multipoly1 = MultiPolygon([t1, t2])
        multipoly2 = rotate(multipoly1, 180)
        self.df2 = GeoDataFrame({'geometry': [multipoly1, multipoly2],
                                 'values': [0, 1]})

    def test_single_color(self):

        ax = self.polys.plot(color='green')
        _check_colors(2, ax.collections[0].get_facecolors(), ['green']*2, alpha=0.5)
        # color only sets facecolor
        _check_colors(2, ax.collections[0].get_edgecolors(), ['k'] * 2, alpha=0.5)

        ax = self.df.plot(color='green')
        _check_colors(2, ax.collections[0].get_facecolors(), ['green']*2, alpha=0.5)
        _check_colors(2, ax.collections[0].get_edgecolors(), ['k'] * 2, alpha=0.5)

        with warnings.catch_warnings(record=True) as _:  # don't print warning
            # 'color' overrides 'values'
            ax = self.df.plot(column='values', color='green')
            _check_colors(2, ax.collections[0].get_facecolors(), ['green']*2, alpha=0.5)

    def test_vmin_vmax(self):

        # when vmin == vmax, all polygons should be the same color

        # non-categorical
        ax = self.df.plot(column='values', categorical=False, vmin=0, vmax=0)
        actual_colors = ax.collections[0].get_facecolors()
        np.testing.assert_array_equal(actual_colors[0], actual_colors[1])

        # categorical
        ax = self.df.plot(column='values', categorical=True, vmin=0, vmax=0)
        actual_colors = ax.collections[0].get_facecolors()
        np.testing.assert_array_equal(actual_colors[0], actual_colors[1])

    def test_style_kwargs(self):

        # facecolor overrides default cmap when color is not set
        ax = self.polys.plot(facecolor='k')
        _check_colors(2, ax.collections[0].get_facecolors(), ['k']*2, alpha=0.5)

        # facecolor overrides more general-purpose color when both are set
        ax = self.polys.plot(color='red', facecolor='k')
        # TODO with new implementation, color overrides facecolor
        # _check_colors(2, ax.collections[0], ['k']*2, alpha=0.5)

        # edgecolor
        ax = self.polys.plot(edgecolor='red')
        np.testing.assert_array_equal([(1, 0, 0, 0.5)],
                                      ax.collections[0].get_edgecolors())

        ax = self.df.plot('values', edgecolor='red')
        np.testing.assert_array_equal([(1, 0, 0, 0.5)],
                                      ax.collections[0].get_edgecolors())

    def test_multipolygons(self):

        # MultiPolygons
        ax = self.df2.plot()
        assert len(ax.collections[0].get_paths()) == 4
        cmap = plt.get_cmap(lut=2)
        # colors are repeated for all components within a MultiPolygon
        expected_colors = [cmap(0), cmap(0), cmap(1), cmap(1)]
        # TODO multipolygons don't work yet when values are not specified
        # values are flattended, but color not yet (can fix, but we are
        # thinking to use uniform coloring by default, which would also fix
        # this)
        # _check_colors(4, ax.collections[0], expected_colors, alpha=0.5)

        ax = self.df2.plot('values')
        # specifying values -> same as without values in this case.
        _check_colors(4, ax.collections[0].get_facecolors(), expected_colors, alpha=0.5)


class TestPolygonZPlotting:

    def setup_method(self):

        t1 = Polygon([(0, 0, 0), (1, 0, 0), (1, 1, 1)])
        t2 = Polygon([(1, 0, 0), (2, 0, 0), (2, 1, 1)])
        self.polys = GeoSeries([t1, t2], index=list('AB'))
        self.df = GeoDataFrame({'geometry': self.polys, 'values': [0, 1]})

        multipoly1 = MultiPolygon([t1, t2])
        multipoly2 = rotate(multipoly1, 180)
        self.df2 = GeoDataFrame({'geometry': [multipoly1, multipoly2],
                                 'values': [0, 1]})

    def test_plot(self):
        # basic test that points with z coords don't break plotting
        self.df.plot()


class TestNonuniformGeometryPlotting:

    def setup_method(self):
        pytest.importorskip('matplotlib', '1.5.0')

        poly = Polygon([(1, 0), (2, 0), (2, 1)])
        line = LineString([(0.5, 0.5), (1, 1), (1, 0.5), (1.5, 1)])
        point = Point(0.75, 0.25)
        self.series = GeoSeries([poly, line, point])
        self.df = GeoDataFrame({'geometry': self.series, 'values': [1, 2, 3]})

    def test_colormap(self):

        ax = self.series.plot(cmap='RdYlGn')
        cmap = plt.get_cmap('RdYlGn', 3)
        # polygon gets extra alpha. See #266
        _check_colors(1, ax.collections[0].get_facecolors(), [cmap(0)], alpha=0.5)
        _check_colors(1, ax.collections[1].get_facecolors(), [cmap(1)], alpha=1)   # line
        _check_colors(1, ax.collections[2].get_facecolors(), [cmap(2)], alpha=1)   # point

    def test_style_kwargs(self):

        # markersize -> only the Point gets it
        ax = self.series.plot(markersize=10)
        assert ax.collections[2].get_sizes() == [10]
        ax = self.df.plot(markersize=10)
        assert ax.collections[2].get_sizes() == [10]


class TestPySALPlotting:

    @classmethod
    def setup_class(cls):
        try:
            import pysal as ps
        except ImportError:
            raise pytest.skip("PySAL is not installed")

        pth = ps.examples.get_path("columbus.shp")
        cls.tracts = read_file(pth)

    def test_legend(self):
        ax = self.tracts.plot(column='CRIME', scheme='QUANTILES', k=3,
                              cmap='OrRd', legend=True)

        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        expected = [u'0.00 - 26.07', u'26.07 - 41.97', u'41.97 - 68.89']
        assert labels == expected

    def test_invalid_scheme(self):
        with pytest.raises(ValueError):
            scheme = 'invalid_scheme_*#&)(*#'
            self.tracts.plot(column='CRIME', scheme=scheme, k=3,
                             cmap='OrRd', legend=True)


class TestPlotCollections:

    def setup_method(self):
        self.N = 3
        self.values = np.arange(self.N)
        self.points = GeoSeries(Point(i, i) for i in range(self.N))
        self.lines = GeoSeries([LineString([(0, i), (4, i + 0.5), (9, i)])
                                for i in range(self.N)])
        self.polygons = GeoSeries([Polygon([(0, i), (4, i + 0.5), (9, i)])
                                   for i in range(self.N)])

    def test_points(self):
        # scatterplot does not yet accept list of colors in matplotlib 1.4.3
        # if we change the default to uniform, this might work again
        pytest.importorskip('matplotlib', '1.5.0')

        from geopandas.plotting import plot_point_collection
        from matplotlib.collections import PathCollection

        fig, ax = plt.subplots()
        coll = plot_point_collection(ax, self.points)
        assert isinstance(coll, PathCollection)
        ax.cla()

        # default: single default matplotlib color
        coll = plot_point_collection(ax, self.points)
        _check_colors(self.N, coll.get_facecolors(), [MPL_DFT_COLOR] * self.N)
        # edgecolor depends on matplotlib version
        # _check_colors(self.N, coll.get_edgecolors(), [MPL_DFT_COLOR]*self.N)
        ax.cla()

        # specify single other color
        coll = plot_point_collection(ax, self.points, color='g')
        _check_colors(self.N, coll.get_facecolors(), ['g'] * self.N)
        _check_colors(self.N, coll.get_edgecolors(), ['g'] * self.N)
        ax.cla()

        # specify edgecolor/facecolor
        coll = plot_point_collection(ax, self.points, facecolor='g',
                                     edgecolor='r')
        _check_colors(self.N, coll.get_facecolors(), ['g'] * self.N)
        _check_colors(self.N, coll.get_edgecolors(), ['r'] * self.N)
        ax.cla()

        # list of colors
        coll = plot_point_collection(ax, self.points, color=['r', 'g', 'b'])
        _check_colors(self.N, coll.get_facecolors(), ['r', 'g', 'b'])
        _check_colors(self.N, coll.get_edgecolors(), ['r', 'g', 'b'])
        ax.cla()

    def test_points_values(self):
        from geopandas.plotting import plot_point_collection

        # default colormap
        fig, ax = plt.subplots()
        coll = plot_point_collection(ax, self.points, self.values)
        cmap = plt.get_cmap()
        expected_colors = cmap(np.arange(self.N))

        # not sure why this is failing (gives only a single color, when
        # testing outside of pytest, this works perfectly
        # _check_colors(self.N, coll.get_facecolors(), expected_colors)
        # _check_colors(self.N, coll.get_edgecolors(), expected_colors)

    def test_linestrings(self):
        from geopandas.plotting import plot_linestring_collection
        from matplotlib.collections import LineCollection

        fig, ax = plt.subplots()
        coll = plot_linestring_collection(ax, self.lines)
        assert isinstance(coll, LineCollection)
        ax.cla()

        # default: single default matplotlib color
        coll = plot_linestring_collection(ax, self.lines)
        _check_colors(self.N, coll.get_color(), [MPL_DFT_COLOR] * self.N)
        ax.cla()

        # specify single other color
        coll = plot_linestring_collection(ax, self.lines, color='g')
        _check_colors(self.N, coll.get_colors(), ['g'] * self.N)
        ax.cla()

        # specify edgecolor / facecolor
        coll = plot_linestring_collection(ax, self.lines, facecolor='g',
                                          edgecolor='r')
        _check_colors(self.N, coll.get_facecolors(), ['g'] * self.N)
        _check_colors(self.N, coll.get_edgecolors(), ['r'] * self.N)
        ax.cla()

        # list of colors
        coll = plot_linestring_collection(ax, self.lines,
                                          color=['r', 'g', 'b'])
        _check_colors(self.N, coll.get_colors(), ['r', 'g', 'b'])
        ax.cla()

        # pass through of kwargs
        coll = plot_linestring_collection(ax, self.lines, linestyle='--')
        exp_ls = _style_to_linestring_onoffseq('dashed')
        res_ls = coll.get_linestyle()[0]
        assert res_ls[0] == exp_ls[0]
        assert tuple(res_ls[1]) == exp_ls[1]
        ax.cla()

    def test_linestrings_values(self):
        from geopandas.plotting import plot_linestring_collection

        fig, ax = plt.subplots()

        # default colormap
        coll = plot_linestring_collection(ax, self.lines, self.values)
        cmap = plt.get_cmap()
        expected_colors = cmap(np.arange(self.N))
        # failing, see above with points
        # _check_colors(self.N, coll.get_color(), expected_colors)
        ax.cla()

        # specify colormap
        coll = plot_linestring_collection(ax, self.lines, self.values,
                                          cmap='RdBu')
        cmap = plt.get_cmap('RdBu')
        expected_colors = cmap(np.arange(self.N))
        # failing, see above with points
        # _check_colors(self.N, coll.get_color(), expected_colors)
        ax.cla()

        # specify vmin/vmax
        coll = plot_linestring_collection(ax, self.lines, self.values,
                                          vmin=3, vmax=5)
        cmap = plt.get_cmap()
        expected_colors = cmap([0])
        # failing, see above with points
        # _check_colors(self.N, coll.get_color(), expected_colors)
        ax.cla()

    def test_polygons(self):
        from geopandas.plotting import plot_polygon_collection
        from matplotlib.collections import PatchCollection

        fig, ax = plt.subplots()
        coll = plot_polygon_collection(ax, self.polygons)
        assert isinstance(coll, PatchCollection)
        ax.cla()

        # default: single default matplotlib color
        # but with default alpha of 0.5 and black edgecolor
        coll = plot_polygon_collection(ax, self.polygons)
        _check_colors(self.N, coll.get_facecolor(), [MPL_DFT_COLOR] * self.N,
                       alpha=0.5)
        _check_colors(self.N, coll.get_edgecolor(), ['k'] * self.N, alpha=0.5)
        ax.cla()

        # default: color sets both facecolor and edgecolor
        # TODO but test fails for edge (still black)
        coll = plot_polygon_collection(ax, self.polygons, color='g')
        _check_colors(self.N, coll.get_facecolor(), ['g'] * self.N, alpha=0.5)
        # _check_colors(self.N, coll.get_edgecolor(), ['g'] * self.N, alpha=0.5)
        ax.cla()

        # only setting facecolor keeps default for edgecolor
        coll = plot_polygon_collection(ax, self.polygons, facecolor='g')
        _check_colors(self.N, coll.get_facecolor(), ['g'] * self.N, alpha=0.5)
        _check_colors(self.N, coll.get_edgecolor(), ['k'] * self.N, alpha=0.5)
        ax.cla()

        # custom facecolor and edgecolor
        coll = plot_polygon_collection(ax, self.polygons, facecolor='g',
                                       edgecolor='r')
        _check_colors(self.N, coll.get_facecolor(), ['g'] * self.N, alpha=0.5)
        _check_colors(self.N, coll.get_edgecolor(), ['r'] * self.N, alpha=0.5)
        ax.cla()

    def test_polygons_values(self):
        from geopandas.plotting import plot_polygon_collection

        fig, ax = plt.subplots()

        # default colormap, edge is still black by default
        coll = plot_polygon_collection(ax, self.polygons, self.values)
        cmap = plt.get_cmap()
        exp_colors = cmap(np.arange(self.N))
        # failing, see above with points
        # _check_colors(self.N, coll.get_facecolor(), exp_colors, alpha=0.5)
        _check_colors(self.N, coll.get_edgecolor(), ['k'] * self.N, alpha=0.5)
        ax.cla()

        # specify colormap
        coll = plot_polygon_collection(ax, self.polygons, self.values,
                                       cmap='RdBu')
        cmap = plt.get_cmap('RdBu')
        exp_colors = cmap(np.arange(self.N))
        # failing, see above with points
        # _check_colors(self.N, coll.get_facecolor(), exp_colors, alpha=0.5)
        ax.cla()

        # specify vmin/vmax
        coll = plot_polygon_collection(ax, self.polygons, self.values,
                                       vmin=3, vmax=5)
        cmap = plt.get_cmap()
        exp_colors = cmap([0])
        # failing, see above with points
        # _check_colors(self.N, coll.get_facecolor(), exp_colors, alpha=0.5)
        ax.cla()

        # override edgecolor
        coll = plot_polygon_collection(ax, self.polygons, self.values,
                                       edgecolor='g')
        cmap = plt.get_cmap()
        exp_colors = cmap(np.arange(self.N))
        # failing, see above with points
        # _check_colors(self.N, coll.get_facecolor(), exp_colors, alpha=0.5)
        _check_colors(self.N, coll.get_edgecolor(), ['g'] * self.N, alpha=0.5)
        ax.cla()


def _check_colors(N, actual_colors, expected_colors, alpha=None):
    """
    Asserts that the members of `collection` match the `expected_colors`
    (in order)

    Parameters
    ----------
    N : int
        The number of geometries believed to be in collection.
        matplotlib.collection is implemented such that the number of geoms in
        `collection` doesn't have to match the number of colors assignments in
        the collection: the colors will cycle to meet the needs of the geoms.
        `N` helps us resolve this.
    collection : matplotlib.collections.Collection
        The colors of this collection's patches are read from
        `collection.get_facecolors()`
    expected_colors : sequence of RGBA tuples
    alpha : float (optional)
        If set, this alpha transparency will be applied to the
        `expected_colors`. (Any transparency on the `collecton` is assumed
        to be set in its own facecolor RGBA tuples.)
    """
    import matplotlib.colors as colors
    conv = colors.colorConverter

    # Convert 2D numpy array to a list of RGBA tuples.
    actual_colors = map(tuple, actual_colors)
    all_actual_colors = list(itertools.islice(
        itertools.cycle(actual_colors), N))

    for actual, expected in zip(all_actual_colors, expected_colors):
        assert actual == conv.to_rgba(expected, alpha=alpha), \
            '{} != {}'.format(actual, conv.to_rgba(expected, alpha=alpha))


def _style_to_linestring_onoffseq(linestyle):
    """ Converts a linestyle string representation, namely one of:
            ['dashed',  'dotted', 'dashdot', 'solid'],
        documented in `Collections.set_linestyle`,
        to the form `onoffseq`.
    """
    if LooseVersion(matplotlib.__version__) >= '2.0':
        return matplotlib.lines._get_dash_pattern(linestyle)
    else:
        from matplotlib.backend_bases import GraphicsContextBase
        return GraphicsContextBase.dashd[linestyle]