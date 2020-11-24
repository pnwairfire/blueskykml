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

def images_dir_name(config, parameter):
    return (config.get('DispersionGridOutput', "OUTPUT_DIR").rstrip('/')
        + '-' + parameter.lower())

def create_dispersion_images_dir(config, parameter):
    outdir = images_dir_name(config, parameter)
    create_dir_if_does_not_exist(outdir)

def create_polygon_kmls_dir(config, parameter):
    outdir = images_dir_name(config, parameter)
    create_dir_if_does_not_exist(outdir)

def create_image_set_dir(config, parameter, *dirs):
    """Creates the directory to contain the specified image set, if necessary"""
    images_output_dir = images_dir_name(config, parameter)
    dirs = [str(d) for d in dirs]
    outdir = os.path.join(images_output_dir, *dirs)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir

def image_pathname(image_set_dir, parameter, height_label, time_series_type,
        color_map_section, ts, utc_offset=None):
    filename = ts.strftime(
        parameter.lower()
        + '_' + height_label
        + '_' + IMAGE_PREFIXES[time_series_type]
        + ('_' + get_utc_label(utc_offset) if utc_offset is not None else '')
        + '_' + color_map_section
        + '_' + FILE_NAME_TIME_STAMP_PATTERNS[time_series_type]
    )

    return os.path.join(image_set_dir, filename)

def legend_pathname(image_set_dir, parameter, height_label, time_series_type,
        color_map_section, utc_offset=None):
    filename = (
        parameter.lower()
        + '_' + height_label
        + '_' + TIME_SET_DIR_NAMES[time_series_type]
        + ('_' + get_utc_label(utc_offset) if utc_offset is not None else '')
        +  '_' + color_map_section
        + '_' + "colorbar"
    )

    return os.path.join(image_set_dir, filename)

def get_utc_label(utc_offset):
    return 'UTC{}{}{}00'.format('+' if utc_offset >= 0 else '-',
        '0' if abs(utc_offset) < 10 else '', abs(utc_offset))


# TODO: parse_color_map_names belongs somewhere else...or maybe this module,
# dispersion_file_utils, should be renamed more generically
# Note: this will memoize for a single instance of the config parse
# TODO: pass in color map names string instead of the config object ?
@memoizeme
def parse_color_map_names(config, parameter, set_name):
    def _to_array(val):
        return [name.strip() for name in val.split(',')]

    key = "{}_{}".format(set_name, parameter.upper())
    if config.has_option("DispersionGridOutput", key):
        return _to_array(config.get("DispersionGridOutput", key))

    elif config.has_option("DispersionGridOutput", set_name):
        return _to_array(config.get("DispersionGridOutput", set_name))

    return []

def is_smoke_image(file_name, parameter, height_label, time_series_type):
    return (file_name.startswith(parameter.lower() + '_' + height_label + '_'
        + IMAGE_PREFIXES[time_series_type])) and file_name.find('colorbar') == -1


##
## Collecting all images for post-processing
##

@memoizeme
def collect_all_dispersion_images(config, parameter, heights):
    """Collect images from all sets of colormap images in each time series
    category
    """
    utc_offsets = config.get('DispersionImages', "DAILY_IMAGES_UTC_OFFSETS")

    images = {}

    for height in heights:
        height_label = create_height_label(height)
        time_series_types = TimeSeriesTypes.all_for_parameter(parameter)
        images[height_label] = dict((v, {}) for v in time_series_types)
        for time_series_type in time_series_types:
            if time_series_type in (TimeSeriesTypes.DAILY_MAXIMUM,
                    TimeSeriesTypes.DAILY_MINIMUM,
                    TimeSeriesTypes.DAILY_AVERAGE):
                for utc_offset in utc_offsets:
                    collect_all_colormap_dispersion_images(config, parameter, images,
                        height_label, time_series_type, utc_offset=utc_offset)
            else:
                collect_all_colormap_dispersion_images(config, parameter, images,
                    height_label, time_series_type)
    return images

def collect_all_colormap_dispersion_images(config, parameter, images, height_label,
        time_series_type, utc_offset=None):
    keys = [height_label, TIME_SET_DIR_NAMES[time_series_type]]
    if utc_offset is not None:
        keys.append(get_utc_label(utc_offset))

    for color_map_section in parse_color_map_names(config, parameter,
            CONFIG_COLOR_LABELS[time_series_type]):
        # Initialize and get reference to nested color section imatges dict
        _keys = keys + [color_map_section]
        color_set = initialize_sections_dict(images, *_keys)

        # create output dir
        color_set['root_dir'] = create_image_set_dir(config, parameter, *_keys)

        # collect images
        for image in os.listdir(color_set['root_dir']):
            if is_smoke_image(image, parameter, height_label, time_series_type):  # <-- this is to exclude color bar
                color_set['smoke_images'].append(image)
            else:  #  There should only be smoke images and a legend
                color_set['legend'] = image


##
## Collection images for KML
##

# Note: collect_dispersion_images_for_kml was copied over from
# smokedispersionkml.py and refactored to remove redundancy
def collect_dispersion_images_for_kml(config, parameter, heights):
    """Collect images from first set of colormap images in each time series
    category. Used in KML generation.
    """
    utc_offsets = config.get('DispersionImages', "DAILY_IMAGES_UTC_OFFSETS")

    images = {}

    for height in heights:
        height_label = create_height_label(height)
        for time_series_type in TimeSeriesTypes.all_for_parameter(parameter):
            if time_series_type in (TimeSeriesTypes.DAILY_MAXIMUM,
                    TimeSeriesTypes.DAILY_MINIMUM,
                    TimeSeriesTypes.DAILY_AVERAGE):
                for utc_offset in utc_offsets:
                    collect_color_map_dispersion_images_section_for_kml(
                        config, parameter, images, height_label,
                        time_series_type, utc_offset=utc_offset)
            else:
                collect_color_map_dispersion_images_section_for_kml(
                    config, parameter, images, height_label,
                    time_series_type)
    return images

def collect_color_map_dispersion_images_section_for_kml(config, parameter,
        images, height_label, time_series_type, utc_offset=None):
    color_map_sections = parse_color_map_names(config, parameter,
        CONFIG_COLOR_LABELS[time_series_type])
    for color_map_section in color_map_sections:

        # Initialize and get reference to nested color section imatges dict
        keys = [height_label, time_series_type]
        if utc_offset is not None:
            keys.append(get_utc_label(utc_offset))
        keys.append(color_map_section)
        images_section = initialize_sections_dict(images, *keys)

        # create output dir
        keys[1] = TIME_SET_DIR_NAMES[keys[1]]
        outdir = create_image_set_dir(config, parameter, *keys)

        # collect images
        images_section['root_dir'] = outdir
        for image in os.listdir(outdir):
            if is_smoke_image(image, parameter, height_label, time_series_type):  # <-- this is to exclude color bar
                images_section['smoke_images'].append(image)
            else:  #  There should only be smoke images and a legend
                images_section['legend'] = image

##
## General image collecting utilities
##

def initialize_sections_dict(images, *keys):
    if len(keys) > 1:
        images[keys[0]] = images.get(keys[0], {})
        return initialize_sections_dict(images[keys[0]], *keys[1:])
    else:
        images[keys[0]] = images.get(keys[0], {'smoke_images':[], 'legend': None})
        return images[keys[0]]
