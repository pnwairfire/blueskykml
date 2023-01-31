import logging
import os
import re
import shutil
from PIL import Image
# from PIL import ImageColor # TODO: Can this replace SimpleColor?
from copy import deepcopy

from . import dispersion_file_utils as dfu
from .constants import TIME_SERIES_PRETTY_NAMES

class SimpleColor(object):
    """Represents a pixel color in the form of RGBA."""

    def __init__(self, r=255, g=255, b=255, a=255):
        """
        Keyword arguments:
            r -- Red color level (int between 0 and 255, default 255)
            g -- Green color level (int between 0 and 255, default 255)
            b -- Blue color level (int between 0 and 255, default 255)
            a -- Alpha level (int between 0 and 255, default 255)
        """
        self.set_color(r,g,b,a)

    def set_color(self, r=None, g=None, b=None, a=None):
        """Sets individual color levels.
        Arguments:
            r -- Red color level (int between 0 and 255, default None)
            g -- Green color level (int between 0 and 255, default None)
            b -- Blue color level (int between 0 and 255, default None)
            a -- Alpha level (int between 0 and 255, default None)
        Returns:
            The SimpleColor object instance
        """
        if r is not None:
            self.r = r
        if g is not None:
            self.g = g
        if b is not None:
            self.b = b
        if a is not None:
            self.a = a
        return self

    def get_color_tuple(self):
        """Provides tuple representation of the SimpleColor object.
        Returns:
            tuple(Red, Green, Blue, Alpha)
        """
        return self.r, self.g, self.b, self.a


def format_dispersion_images(config, parameter, heights):
    # [DispersionImages] configurations
    section = 'DispersionImages'
    image_opacity_factor = config.getfloat(section, "IMAGE_OPACITY_FACTOR")
    vr_part = ("_VISUAL_RANGE"
        if re.sub("[ _-]*", "", parameter.lower()) == 'visualrange' else "")
    if config.getboolean(section, "DEFINE_RGB"):
        red = config.getint(section, f"BACKGROUND_COLOR{vr_part}_RED")
        green = config.getint(section, f"BACKGROUND_COLOR{vr_part}_GREEN")
        blue = config.getint(section, f"BACKGROUND_COLOR{vr_part}_BLUE")
    elif config.getboolean(section, "DEFINE_HEX"): # Convert hex to RGB integers
        background_color_hex = config.get(section, f"BACKGROUND_COLOR{vr_part}_HEX")
        rgb_hex = background_color_hex[1:3], background_color_hex[3:5], background_color_hex[5:7]
        red, green, blue = ((int(hex_val, 16) for hex_val in rgb_hex))
    else:
        raise Exception("Configuration ERROR...DispersionImages.DEFINE_RGB or DispersionImages.DEFINE_HEX must be true.")
    background_color = SimpleColor(red, green, blue, 255)

    # [DispersionGridOutput] configurations
    images = dfu.collect_all_dispersion_images(config, parameter, heights)

    def _format(data, *keys):
        for k, v in data.items():
            _keys = list(keys) + [k]
            if 'smoke_images' in v:
                # k is the color map section
                # iof is the color map section's custom image opacity factor, if specified
                iof = (config.getfloat(k, "IMAGE_OPACITY_FACTOR") if
                    config.has_option(k, "IMAGE_OPACITY_FACTOR") else
                    image_opacity_factor)
                for i, image_name in enumerate(v['smoke_images']):
                    logging.debug("Applying transparency {} to plot"
                        " {} of {}".format(iof, i, ' > '.join(_keys)))
                    image_path = os.path.join(v['root_dir'], image_name)
                    image = Image.open(image_path)
                    image = _apply_transparency(image, deepcopy(background_color), iof)
                    image.save(image_path, "PNG")
            else:
                _format(v, *_keys)

    _format(images)


def _apply_transparency(image, background_color, opacity_factor):
    """Sets the background color of the image to be fully transparent, and modifies the overall image opacity based on a
    specified factor.
    Arguments:
        image            -- Image to apply transparency to (PIL.Image object)
        background_color -- Color that will be made transparent (SimpleColor object)
        opacity_factor   -- Determines visibility of image. A value of 0 would make the image fully transparent
                            (float 0.0 to 1.0)
    Returns:
        Modified img object
    """
    background_color_tuple = background_color.get_color_tuple() # Get color tuple to search for
    transparent_color_tuple = background_color.set_color(a=0).get_color_tuple() # Get transparent color tuple
    pixdata = image.load()

    for y in range(image.size[1]):
        for x in range(image.size[0]):
            if pixdata[x, y] == background_color_tuple:
                pixdata[x, y] = transparent_color_tuple
            else:
                pixel = pixdata[x, y]
                new_alpha = int(pixel[3]*opacity_factor)
                if new_alpha > 255:
                    new_alpha = 255
                elif new_alpha < 0:
                    new_alpha = 0
                pixel_color = SimpleColor(r=pixel[0], g=pixel[1], b=pixel[2], a=new_alpha)
                pixdata[x, y] = pixel_color.get_color_tuple()
    return image

def reproject_images(config, parameter, grid_bbox, heights):
    """Reproject images for display on map software (i.e. OpenLayers).
    PNG images will first be translated to TIF files via the 'gdal_translate' command.  The new TIF file will then be
    reprojected using the 'gdalwarp' command.  Finally, the reprojected TIF file will be warped back into PNG image form.

    Currently hardcoded to reproject to  EPSG:3857 - http://spatialreference.org/ref/sr-org/epsg3857/
    """

    # Note: This code utilizes gdal CLI commands.  Idealy it should instead take advantage of the python gdal library.
    # However, there is no official documentation available for the python gdal API, making it rather tricky to
    # use correctly.  The below link points to a unit test suite for python gdal's transformation logic.  Perhaps there
    # are enough examples there to determain how to replace the translation/warp operations used from the command line.
    #
    # http://svn.osgeo.org/gdal/trunk/autotest/gcore/transformer.py
    #
    # Below are links to the command line documentation for gdal's "translate" and "warp" commands.
    #
    # gdal_translate - http://www.gdal.org/gdal_translate.html
    # gdalwarp -      http://www.gdal.org/gdalwarp.html

    images = dfu.collect_all_dispersion_images(config, parameter, heights)

    # Collect inputs for gdal translate and warp commands
    a_srs = 'WGS84'
    a_ullr = '%s %s %s %s' % (str(grid_bbox[0]), str(grid_bbox[3]), str(grid_bbox[2]), str(grid_bbox[1]))
    t_srs = config.get('DispersionImages', "REPROJECT_IMAGES_SRS")
    logging.info("Reprojecting images to SRS: %s", t_srs)

    _save_original(config, parameter, a_srs)

    def _reproject(data, *keys):
        if isinstance(data, dict):
            if 'smoke_images' in data:
                for i, image_name in enumerate(data['smoke_images']):
                    logging.debug("Reprojecting image"
                        " {} of {}".format(i, ' > '.join(keys)))
                    image_path = os.path.join(data['root_dir'], image_name)
                    tiff_path1 = os.path.join(data['root_dir'], 'temp1.tif')
                    tiff_path2 = os.path.join(data['root_dir'], 'temp2.tif')

                    # Build gdal translate and warp command line strings
                    gdal_translate_cmd1 = 'gdal_translate -a_srs %s -a_ullr %s %s %s' % (a_srs, a_ullr, image_path, tiff_path1)
                    gdal_warp_cmd = 'gdalwarp -t_srs \'%s\' %s %s' % (t_srs, tiff_path1, tiff_path2)
                    gdal_translate_cmd2 = 'gdal_translate -of PNG %s %s' % (tiff_path2, image_path)

                    # Gdal translate PNG image to TIF
                    logging.info("Executing: %s" % gdal_translate_cmd1)
                    os.system(gdal_translate_cmd1)

                    # Gdal warp TIF to new projection
                    logging.info("Executing: %s" % gdal_warp_cmd)
                    os.system(gdal_warp_cmd)

                    # Gdal translate new TIF back to PNG
                    logging.info("Executing: %s" % gdal_translate_cmd2)
                    os.system(gdal_translate_cmd2)

                    # Clean up intermediate files
                    os.remove(tiff_path1)
                    os.remove(tiff_path2)
                    os.remove(image_path + '.aux.xml')
            else:
                for k, v in data.items():
                    _reproject(v, *(list(keys) + [k]))

    _reproject(images)


def _save_original(config, parameter, a_srs):
    if config.getboolean('DispersionImages', 'REPROJECT_IMAGES_SAVE_ORIGINAL'):
        orig = dfu.images_dir_name(config, parameter)
        saved = os.path.join(os.path.dirname(orig), 'saved-original-images',
            a_srs, os.path.basename(orig))
        logging.info("Saving pre-reprojected images (%s) to %s", orig, saved)
        # delete existing, if any
        if os.path.exists(saved):
            shutil.rmtree(saved)
        # create path to save destination, if necessary
        os.makedirs(os.path.dirname(saved), exist_ok=True)
        shutil.copytree(orig, saved)
