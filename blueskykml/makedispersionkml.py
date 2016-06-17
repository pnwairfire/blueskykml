from datetime import datetime
import json
import logging

from . import configuration
from . import dispersiongrid
from . import dispersion_file_utils as dfu
from . import dispersionimages
from . import smokedispersionkml


def main(options):
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    # Note:  The log messages in this module are intended to be info level. The
    # verbose setting affects log messages in other modules in this package.

    logging.info("Starting Make Dispersion KML.")

    config = configuration.ConfigBuilder(options).config

    # Determine which mode to run OutputKML in
    if 'dispersion' in config.get('DEFAULT', 'MODES').split():
        # Create dispersion images directory within the specified bsf output directory
        dfu.create_dispersion_images_dir(config)

        # Generate smoke dispersion images
        logging.info("Processing smoke dispersion NetCDF data into plot images...")
        start_datetime, grid_bbox = dispersiongrid.create_dispersion_images(
            config)

        # Output dispersion grid bounds
        _output_grid_bbox(grid_bbox, config)

        # Post process smoke dispersion images
        logging.info("Formatting dispersion plot images...")
        dispersionimages.format_dispersion_images(config)
    else:
        start_datetime = config.get("DEFAULT", "DATE") if config.has_option("DEFAULT", "DATE") else datetime.now()
        grid_bbox = None

    # Generate KMZ
    smokedispersionkml.KmzCreator(config, grid_bbox, start_datetime=start_datetime).create_all()

    # If enabled, reproject concentration images to display in a different projection
    if config.getboolean('DispersionImages', 'REPROJECT_IMAGES'):
        dispersionimages.reproject_images(config, grid_bbox)

    logging.info("Make Dispersion finished.")

def _output_grid_bbox(grid_bbox, config):
    grid_info_file = config.get('DispersionGridOutput', "GRID_INFO_JSON")
    if grid_info_file is not None:
        logging.info("Outputting grid bounds to %s." % grid_info_file)
        grid_info_dict = {'bbox': grid_bbox}
        grid_info_json = json.dumps(grid_info_dict)
        with open(grid_info_file, 'w') as fout:
            fout.write(grid_info_json)
