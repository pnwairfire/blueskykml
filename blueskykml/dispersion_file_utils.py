# TODO: refactor this as a class (possibly singleton?) that takes config in contstructor

import os

from .constants import *
from .memoize import memoizeme

__all__ = [
    'create_dispersion_images_dir', 'create_image_set_dir',
    'image_pathname', 'legend_pathname', 'parse_color_map_names',
    'collect_all_dispersion_images', 'collect_dispersion_images'
]

def create_height_label(height):
    """Doesn't do much, but it's centralized so that we change easily
    """
    return height + 'm'

def create_dir_if_does_not_exist(outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

def create_dispersion_images_dir(config):
    outdir = config.get('DispersionGridOutput', "OUTPUT_DIR")
    create_dir_if_does_not_exist(outdir)

def create_polygon_kmls_dir(config):
    outdir = config.get('PolygonsKML', "POLYGONS_OUTPUT_DIR")
    create_dir_if_does_not_exist(outdir)

def create_image_set_dir(config, *dirs):
    """Creates the directory to contain the specified image set, if necessary"""
    images_output_dir = config.get('DispersionGridOutput', "OUTPUT_DIR")
    dirs = [str(d) for d in dirs]
    outdir = os.path.join(images_output_dir, *dirs)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir

def image_pathname(image_set_dir, height_label, time_series_type, ts):
    filename = ts.strftime(height_label + '_'
        + IMAGE_PREFIXES[time_series_type]
        + FILE_NAME_TIME_STAMP_PATTERNS[time_series_type])
    return os.path.join(image_set_dir, filename)

def legend_pathname(image_set_dir, height_label, time_series_type):
    filename = "%s_colorbar_%s" % (height_label,
        TIME_SET_DIR_NAMES[time_series_type])
    return os.path.join(image_set_dir, filename)


# TODO: parse_color_map_names belongs somewhere else...or maybe this module,
# dispersion_file_utils, should be renamed more generically
# Note: this will memoize for a single instance of the config parse
# TODO: pass in color map names string instead of the config object ?
@memoizeme
def parse_color_map_names(config, set_name):
    if config.has_option("DispersionGridOutput", set_name):
        return [name.strip() for name in config.get("DispersionGridOutput", set_name).split(',')]
    return []

def is_smoke_image(file_name, height_label, time_series_type):
    return file_name.startswith(height_label + '_' + IMAGE_PREFIXES[time_series_type])


@memoizeme
def collect_all_dispersion_images(config, heights):
    """Collect images from all sets of colormap images in each time series category"""
    images = {}

    for height in heights:
        height_label = create_height_label(height)
        images[height_label] = dict((v, {}) for v in TimeSeriesTypes.ALL)
        for time_series_type in TimeSeriesTypes.ALL:
            for color_map_section in parse_color_map_names(config, CONFIG_COLOR_LABELS[time_series_type]):
                color_set = {
                    'root_dir': create_image_set_dir(config, height_label,
                        time_series_type, color_map_section),
                    'smoke_images': [],
                    'legend': None
                }
                for image in os.listdir(color_set['root_dir']):
                    if is_smoke_image(image, height_label, time_series_type):  # <-- this is to exclude color bar
                        color_set['smoke_images'].append(image)
                    else:  #  There should only be smoke images and a legend
                        color_set['legend'] = image

                images[height_label][time_series_type][color_map_section] = color_set

    return images


# Note: collect_dispersion_images was copied over from smokedispersionkml.py and
# refactored to remove redundancy
def collect_dispersion_images(config, heights):
    """Collect images from first set of colormap images in each time series category"""
    images = {}

    for height in heights:
        height_label = create_height_label(height)
        images[height_label] = dict((v, {'smoke_images':[], 'legend': None}) for v in TimeSeriesTypes.ALL)
        for time_series_type in TimeSeriesTypes.ALL:
            color_map_sections = parse_color_map_names(config, CONFIG_COLOR_LABELS[time_series_type])
            if color_map_sections and len(color_map_sections) > 0:
                outdir = create_image_set_dir(config, height_label,
                    time_series_type, color_map_sections[0])
                images[height_label][time_series_type]['root_dir'] = outdir
                for image in os.listdir(outdir):
                    if is_smoke_image(image, height_label, time_series_type):  # <-- this is to exclude color bar
                        images[height_label][time_series_type]['smoke_images'].append(image)
                    else:  #  There should only be smoke images and a legend
                        images[height_label][time_series_type]['legend'] = image

    return images
