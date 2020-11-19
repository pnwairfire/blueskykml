
from datetime import datetime, timedelta
import os
import gdal
import logging
import math
import numpy as np
import re
import subprocess

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from .memoize import memoizeme

from . import dispersion_file_utils as dfu
from .constants import (
    TimeSeriesTypes, CONFIG_COLOR_LABELS,
    TIME_SET_DIR_NAMES, PARAMETER_PLOT_LABELS
)

class BSDispersionGrid:

    GDAL_VERSION_MATCHER = re.compile('GDAL (\d+)\.(\d+)\.\d+, released \d+/\d+/\d+')
    def get_geotransform(self):
        flip_images = False

        try:
            gdal_info = subprocess.check_output(["gdalinfo","--version"])
            matches = self.GDAL_VERSION_MATCHER.match(gdal_info.decode('ascii'))
            major = int(matches.group(1))
            minor = int(matches.group(2))
            if (major > 1) or (major == 1 and minor >= 9):
                flip_images = True
        except OSError:
            # TODO: rather than just default to flip_images = False, read value from config
            pass

        x0 = float(self.metadata["NC_GLOBAL#XORIG"])
        y0 = float(self.metadata["NC_GLOBAL#YORIG"])
        dx = float(self.metadata["NC_GLOBAL#XCELL"])
        dy = float(self.metadata["NC_GLOBAL#YCELL"])
        #nx = int(self.metadata["NC_GLOBAL#NCOLS"])
        ny = int(self.metadata["NC_GLOBAL#NROWS"])

        if flip_images:
            return (x0, dx, 0.0, y0+float(ny-1)*dy, 0.0, -dy)
        else:
            return (x0, dx, 0.0, y0, 0.0, dy)

    def __init__(self, filename, param=None, time=None):
        if not os.path.exists(filename):
            raise ValueError("NetCDF file does not exists - {}.".format(
                filename))

        if not param:
            raise ValueError ("No NetCDF parameter supplied.")

        # if param is "visual range", we actually read PM25
        self.is_visual_range = re.sub("[ _-]*", "", param.lower()) == 'visualrange'
        file_param = 'PM25' if self.is_visual_range else param
        gdal_filename = "NETCDF:%s:%s" % (filename, file_param)
        logging.debug("loading gdal file %s", gdal_filename)

        self.ds = gdal.Open(gdal_filename)
        self.metadata = self.ds.GetMetadata()

        if not self.is_ioapi():
            raise Exception("[ERROR] Not dealing with a BlueSky Models3-style netCDF dispersion file.")

        # Get georeference info
        self.geotransform = self.get_geotransform()
        logging.debug("Using geo transform: %s", self.geotransform)

        if not self.metadata["NC_GLOBAL#GDTYP"] == '1':  # lat/lon grid
            raise ValueError("Unrecognized grid type for BlueSky Dispersion netCDF data")

        # Extract grid information
        self.minX, self.cellSizeX, self.skewX = self.geotransform[:3]
        self.minY, self.skewY, self.cellSizeY = self.geotransform[3:]
        self.sizeX = self.ds.RasterXSize
        self.sizeY = self.ds.RasterYSize
        self.sizeZ = int(self.metadata["NC_GLOBAL#NLAYS"])
        self.heights = self.metadata['NC_GLOBAL#VGLVLS'].replace('{','').replace(',0}','').split(',')

        # BlueSky dispersion outputs are dimensioned by [TSTEP, LAY, ROW, COL].
        # The number of GDAL raster bands (ds.RasterCount) will be TSTEP*LAY.
        self.num_times = self.ds.RasterCount // self.sizeZ

        # Extract date-time information
        self.datetimes = self.get_datetimes()

        # Extract the data
        timeid = 0
        layerid = 0
        self.data = np.zeros((self.num_times, self.sizeZ, self.sizeY, self.sizeX), dtype=np.float)
        for i in range(self.ds.RasterCount):
            rb = self.ds.GetRasterBand(i+1)
            data = rb.ReadAsArray(0, 0, self.sizeX, self.sizeY)
            # if param is "visual range", we need to convert PM25 values
            if self.is_visual_range:
                logging.debug("Converting PM2.5 to visual range")
                for d in data:
                    for i in range(len(d)):
                        # Visual Range (miles) = 539/PM2.5, but set to 539
                        # if PM2.5 < 1.0
                        d[i] = 539 / max(1, d[i])

            self.data[timeid,layerid,:,:] = data

            # GDAL bands will increment by layer the fastest, then by time
            layerid += 1
            if layerid == self.sizeZ:
                timeid += 1
                layerid = 0

    def is_ioapi(self):
        if "NC_GLOBAL#IOAPI_VERSION" in self.metadata:
            return True
        else:
            return False

    def get_datetimes(self):
        """Get Models3 IO/API date-time"""

        sdate = str(self.metadata['NC_GLOBAL#SDATE'])
        # Note: stime should be multiple of 10000 (i.e. multiple of hours), so that
        # casting to int and dividing by 10000 shouldn't lose any information
        stime = int(self.metadata['NC_GLOBAL#STIME']) // 10000
        tstep = str(self.metadata['NC_GLOBAL#TSTEP'])

        start_datetime = datetime.strptime("%s%s" % (sdate, stime), "%Y%j%H")
        tstep_hrs = float(tstep) / 10000

        return [start_datetime + timedelta(hours = i*tstep_hrs) for i in range(self.num_times)]

    def ioapi_datetime_to_object(self, yyyyddd, hhmmss):
        """Convert a Models3 IO/API convention datetime to a python datetime object."""

        hour = hhmmss
        secs = hour % 100
        hour = hour / 100
        mins = hour % 100
        hour = hour / 100

        dt = datetime.strptime(str(yyyyddd), "%Y%j")
        dt = dt.replace(hour=hour, minute=mins, second=secs)

        return dt

    ONE_DAY = timedelta(days=1)

    def compute_days_spanned(self, utc_offset):
        """Calculates the full and partial days spanned by DispersionGrid
        dataset.
        """
        self.local_start = self.datetimes[0] + timedelta(hours=utc_offset)
        self.local_end = self.local_start + timedelta(hours=self.num_times - 1)
        self.num_days = (self.local_end.date() - self.local_start.date()).days + 1
        self.dates = [
            self.local_start + i * self.ONE_DAY for i in range(self.num_days)
        ]

    def calc_aggregate_data(self, utc_offset=0):
        """Calculate various daily aggregates

        Assumes hourly time interval.
        """
        assert utc_offset > -24 and utc_offset < 24, ("[ERROR] utc_offset "
            "for aggregate calculations must be between -24 and 24.")

        self.compute_days_spanned(utc_offset)
        self.max_data = np.zeros((self.num_days, self.sizeZ, self.sizeY, self.sizeX), dtype=np.float)
        self.min_data = np.zeros((self.num_days, self.sizeZ, self.sizeY, self.sizeX), dtype=np.float)
        self.avg_data = np.zeros((self.num_days, self.sizeZ, self.sizeY, self.sizeX), dtype=np.float)

        shour = 0
        ehour = min(24 - self.local_start.hour, self.num_times)

        for day in range(self.num_days):
            for layer in range(self.sizeZ):
                self.max_data[day,layer,:,:] = np.max(self.data[shour:ehour,layer,:,:], axis=0)
                self.min_data[day,layer,:,:] = np.min(self.data[shour:ehour,layer,:,:], axis=0)
                self.avg_data[day,layer,:,:] = np.average(self.data[shour:ehour,layer,:,:], axis=0)
            shour = ehour
            ehour  = min(ehour + 24, self.num_times)


class BSDispersionPlot:

    def __init__(self, config, parameter, dpi=75):
        self.parameter_label = PARAMETER_PLOT_LABELS.get(parameter) or parameter

        self.dpi = dpi
        self.export_format = 'png'

    def colormap_from_RGB(self, r, g, b):
        """ Create a colormap from lists of non-normalized RGB values (0-255)"""

        # Validate the RGB vectors
        assert len(r) == len(g) == len(b), "[ColorMap] RGB vectors must be the same size."
        assert max(r) <= 255 and min(r) >= 0, "ColorMap.RED vector element outside the range [0,255]"
        assert max(g) <= 255 and min(g) >= 0, "ColorMap.GREEN vector element outside the range [0,255]"
        assert max(b) <= 255 and min(b) >= 0, "ColorMap.BLUE vector element outside the range [0,255]"

        # matplotlib likes normalized [0,1] RGB values
        r = np.array(r)/255.
        g = np.array(g)/255.
        b = np.array(b)/255.

        # Create colormap
        self.colormap = mpl.colors.ListedColormap(list(zip(r, g, b)))

        # Set out-of-range values get the lowest and highest colors in the colortable
        self.colormap.set_under( color=(r[0],g[0],b[0]) )
        self.colormap.set_over( color=(r[-1],g[-1],b[-1]) )

        # Create special colormap without the first color for colorbars
        self.cb_colormap = mpl.colors.ListedColormap(list(zip(r[1:],g[1:],b[1:])))

    def colormap_from_hex(self, hex_colors):
        """Create colormap from list of hex colors."""

        # Convert colors from hex to matplotlib-style normalized [0,1] values
        colors = list()
        for c in hex_colors:
            colors.append(mpl.colors.hex2color(c))

        # Create colormap
        self.colormap = mpl.colors.ListedColormap(colors)

        # Set out-of-range values get the lowest and highest colors in the colortable
        self.colormap.set_under( color=mpl.colors.hex2color(hex_colors[0]) )
        self.colormap.set_over( color=mpl.colors.hex2color(hex_colors[-1]) )

        # Create special colormap without the first color for colorbars
        self.cb_colormap = mpl.colors.ListedColormap(colors[1:])

    def set_plot_bounds(self, grid):
        """Set X-axis and Y-axis coordinate values for the plot.
           Takes a BSDispersionGrid class as an input."""

        # TODO: Add bounds cropping capability.

        # X-axis and Y-axis values (longitudes and latitudes)
        self.xvals = np.linspace(grid.minX, grid.minX + ((grid.sizeX-1) * grid.cellSizeX), num=grid.sizeX)
        self.yvals = np.linspace(grid.minY, grid.minY + ((grid.sizeY-1) * grid.cellSizeY), num=grid.sizeY)

        # Set the plot extents for the KML
        # NOTE: original code just referenced the first and last elements
        #       of the arrays, but this doesn't work when using the new
        #       geotransform for gdal >= 1.9
        self.lonmin = min(self.xvals)
        self.lonmax = max(self.xvals)
        self.latmin = min(self.yvals)
        self.latmax = max(self.yvals)

    def generate_colormap_index(self, levels):
        """Generate a colormap index based on discrete intervals"""

        self.levels = levels
        assert hasattr(self, "colormap"), "BSDispersionPlot object must have a colormap before you can generate a colormap index."
        self.norm = mpl.colors.BoundaryNorm(self.levels,
                                            ncolors=self.colormap.N)

        # for colorbar
        self.cb_levels = self.levels[1:]
        self.cb_norm = mpl.colors.BoundaryNorm(self.cb_levels,
                                               ncolors=self.cb_colormap.N)

    def make_quadmesh_plot(self, raster_data, fileroot):
        """Create a quadilateral mesh plot."""

        fig = plt.figure()
        #fig.set_size_inches(7,5)
        ax = plt.Axes(fig, [0., 0., 1., 1.], )
        ax.set_axis_off()
        fig.add_axes(ax)
        plt.pcolormesh(self.xvals,
                       self.yvals,
                       raster_data,
                       cmap=self.colormap,
                       norm=self.norm)
        plt.savefig(fileroot+'.'+self.export_format, bbox_inches='tight', pad_inches=0., dpi=self.dpi, transparent=True)
        # explicitly close plot - o/w pyplot keeps it open until end of program
        plt.close()

    def make_contour_plot(self, raster_data, fileroot, filled=True, lines=False):
        """Create a contour plot."""

        """ TODO: contour() and contourf() assume the data are defined on grid edges.
        i.e. They line up the bottom-left corner of each square with the coordinates given.
        If the data are defined at grid centers, a half-grid displacement is necessary.
        xv = plot.xvals[:-1] + grid.cellSizeX / 2.
        yv = plot.yvals[:-1] + grid.cellSizeY / 2.
        """

        fig = plt.figure()
        ax = plt.Axes(fig, [0., 0., 1., 1.], )
        ax.set_axis_off()
        fig.add_axes(ax)
        cnf = plt.contourf(self.xvals,
                           self.yvals,
                           raster_data,
                           levels=self.levels,
                           cmap=self.colormap,
                           norm=self.norm,
                           extend='max')
        if lines:
            cn = plt.contour(self.xvals,
                             self.yvals,
                             raster_data,
                             levels=self.levels,
                             colors='black',
                             norm=self.norm)

        plt.savefig(fileroot+'.'+self.export_format, dpi=self.dpi, transparent=True)
        # explicitly close plot - o/w pyplot keeps it open until end of program
        plt.close()

    def make_colorbar(self, fileroot):
        mpl.rc('mathtext', default='regular')
        assert len(self.levels) == self.colormap.N + 1
        fig = plt.figure(figsize=(8,1))
        ax = fig.add_axes([0.05, 0.5, 0.9, 0.45])
        ax.tick_params(labelsize=12)
        cb = mpl.colorbar.ColorbarBase(ax, cmap=self.cb_colormap,
                                           norm=self.cb_norm,
                                           ticks=self.cb_levels[0:-1],
                                           orientation='horizontal')
        cb.set_label(self.parameter_label, size=12)
        plt.savefig(fileroot+'.'+self.export_format, dpi=self.dpi/3)
        # explicitly close plot - o/w pyplot keeps it open until end of program
        plt.close()

def create_dispersion_images(config, parameter):
    # [DispersionGridInput] configurations
    infile = config.get('DispersionGridInput', "FILENAME")
    layers = config.get('DispersionGridInput', "LAYERS")
    utc_offsets = config.get('DispersionImages', "DAILY_IMAGES_UTC_OFFSETS")

    grid = BSDispersionGrid(infile, param=parameter)  # dispersion grid instance
    if max(layers) >= grid.sizeZ:
        raise Exception("Requested layers ({}) outside of what's available in"
            " dispersion grid (which has {} layer{})".format(
                ', '.join([str(e) for e in layers]), grid.sizeZ,
                's' if grid.sizeZ > 1 else ''))

    plot = None

    for layer in layers:
        for color_map_section in dfu.parse_color_map_names(
                config, CONFIG_COLOR_LABELS[TimeSeriesTypes.HOURLY]):
            plot = create_hourly_dispersion_images(
                config, parameter, grid, color_map_section, layer)

        for color_map_section in dfu.parse_color_map_names(
                config, CONFIG_COLOR_LABELS[TimeSeriesTypes.THREE_HOUR]):
            plot = create_three_hour_dispersion_images(
                config, parameter, grid, color_map_section, layer)

        # Create MIN only for VR, and MAX only for all other;
        #  update any other parts of the code as necessary
        if grid.is_visual_range:
            for color_map_section in dfu.parse_color_map_names(
                    config, CONFIG_COLOR_LABELS[TimeSeriesTypes.DAILY_MINIMUM]):
                for utc_offset in utc_offsets:
                    plot = create_daily_dispersion_images(
                        config, parameter, grid, color_map_section, layer, utc_offset,
                        dfu.TimeSeriesTypes.DAILY_MINIMUM)
        else:
            for color_map_section in dfu.parse_color_map_names(
                    config, CONFIG_COLOR_LABELS[TimeSeriesTypes.DAILY_MAXIMUM]):
                for utc_offset in utc_offsets:
                    plot = create_daily_dispersion_images(
                        config, parameter, grid, color_map_section, layer, utc_offset,
                        dfu.TimeSeriesTypes.DAILY_MAXIMUM)

        for color_map_section in dfu.parse_color_map_names(
                config, CONFIG_COLOR_LABELS[TimeSeriesTypes.DAILY_AVERAGE]):
            for utc_offset in utc_offsets:
                plot = create_daily_dispersion_images(
                    config, parameter, grid, color_map_section, layer, utc_offset,
                    dfu.TimeSeriesTypes.DAILY_AVERAGE)

    if not plot:
        raise Exception("Configuration ERROR... No color maps defined.")

    # Return the grid starting date, and a tuple lon/lat bounding box of the plot
    return (
        grid.datetimes[0],
        (plot.lonmin, plot.latmin, plot.lonmax, plot.latmax),
        [grid.heights[l] for l in layers] # only the heights extracted
    )

@memoizeme
def create_color_plot(config, parameter, grid, section):
    # Create plots
    # Note that grid.data has dimensions of: [time,lay,row,col]

    # Create a dispersion plot instance
    plot = BSDispersionPlot(config, parameter, dpi=150)

    # Data levels for binning and contouring
    if parameter and ('PERCENT' in parameter or 'PCNTSIMS' in parameter):
        levels = [float(s) for s in config.get(section, "PERCENT_LEVELS").split()]
    else:
        levels = [float(s) for s in config.get(section, "DATA_LEVELS").split()]

    # Colormap
    if config.getboolean(section, "DEFINE_RGB"):
        r = [int(s) for s in config.get(section, "RED").split()]
        g = [int(s) for s in config.get(section, "GREEN").split()]
        b = [int(s) for s in config.get(section, "BLUE").split()]
        plot.colormap_from_RGB(r, g, b)

    elif config.getboolean(section, "DEFINE_HEX"):
        hex_colors = config.get(section, "HEX_COLORS").split()
        plot.colormap_from_hex(hex_colors)

    else:
        raise Exception("Configuration ERROR... ColorMap.DEFINE_RGB or ColorMap.HEX_COLORS must be true.")

    # Generate a colormap index based on discrete intervals
    plot.generate_colormap_index(levels)

    # X-axis and Y-axis values (longitudes and latitudes)
    plot.set_plot_bounds(grid)

    return plot

def create_hourly_dispersion_images(config, parameter, grid, section, layer):
    plot = create_color_plot(config, parameter, grid, section)
    height_label = dfu.create_height_label(grid.heights[layer])

    outdir = dfu.create_image_set_dir(config, parameter, height_label,
        TIME_SET_DIR_NAMES[dfu.TimeSeriesTypes.HOURLY], section)

    for i in range(grid.num_times):
        # Shift filename date stamps
        fileroot = dfu.image_pathname(outdir, height_label,
            dfu.TimeSeriesTypes.HOURLY, grid.datetimes[i]-timedelta(hours=1))

        logging.debug("Creating height %s hourly (%s) concentration "
            "plot %d of %d " % (height_label, section, i+1, grid.num_times))

        # Create a filled contour plot
        plot.make_contour_plot(grid.data[i,layer,:,:], fileroot)

    # Create a color bar to use in overlays
    fileroot = dfu.legend_pathname(outdir, height_label,
        dfu.TimeSeriesTypes.HOURLY)
    plot.make_colorbar(fileroot)

    # plot will be used for its already computed min/max lat/lon
    return plot

def create_three_hour_dispersion_images(config, parameter, grid, section, layer):

    # TODO: switch to iterating over time first and then over color scheme, to
    # avoid redundant average computations

    # TODO: write tests for this function

    plot = create_color_plot(config, parameter, grid, section)
    height_label = dfu.create_height_label(grid.heights[layer])

    outdir = dfu.create_image_set_dir(config, parameter, height_label,
        TIME_SET_DIR_NAMES[dfu.TimeSeriesTypes.THREE_HOUR], section)

    for i in range(1, grid.num_times - 1):
        # Shift filename date stamps; shift an extra hour because we are on third
        # hour of three hour series and we want timestamp to reflect middle hour
        fileroot = dfu.image_pathname(outdir, height_label,
            dfu.TimeSeriesTypes.THREE_HOUR,
            grid.datetimes[i]-timedelta(hours=1))

        logging.debug("Creating height %s three hour (%s) concentration "
            "plot %d of %d " % (height_label, section, i+1, grid.num_times))

        # Create a filled contour plot
        plot.make_contour_plot(np.average(grid.data[i-1:i+2,layer,:,:], 0), fileroot)


    # Create a color bar to use in overlays
    fileroot = dfu.legend_pathname(outdir, height_label,
        dfu.TimeSeriesTypes.THREE_HOUR)
    plot.make_colorbar(fileroot)

    # plot will be used for its already computed min/max lat/lon
    return plot

DATA_ATTR = {
    dfu.TimeSeriesTypes.DAILY_MAXIMUM: 'max_data',
    dfu.TimeSeriesTypes.DAILY_MINIMUM: 'min_data',
    dfu.TimeSeriesTypes.DAILY_AVERAGE: 'avg_data'
}
def create_daily_dispersion_images(config, parameter, grid, section, layer,
        utc_offset, time_series_type):
    plot = create_color_plot(config, parameter, grid, section)
    height_label = dfu.create_height_label(grid.heights[layer])
    outdir = dfu.create_image_set_dir(config, parameter, height_label,
        TIME_SET_DIR_NAMES[time_series_type],
        dfu.get_utc_label(utc_offset), section)

    grid.calc_aggregate_data(utc_offset)
    data = getattr(grid, DATA_ATTR[time_series_type])
    for i in range(grid.num_days):
        logging.debug("Creating height %s %s daily %s concentration "
            "plot %d of %d " % (height_label, dfu.get_utc_label(utc_offset),
                dfu.TIME_SET_DIR_NAMES[time_series_type], i + 1, grid.num_days))
        fileroot = dfu.image_pathname(outdir, height_label,
            time_series_type, grid.dates[i],
            utc_offset=utc_offset)
        plot.make_contour_plot(data[i,layer,:,:], fileroot)

    plot.make_colorbar(dfu.legend_pathname(outdir, height_label,
        time_series_type, utc_offset=utc_offset))
    return plot
