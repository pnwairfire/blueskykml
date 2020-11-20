from datetime import datetime
import json
import logging

from . import configuration
from . import dispersiongrid as dg
from . import dispersion_file_utils as dfu
from . import dispersionimages
from . import smokedispersionkml
from . import fires


def main(options):
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    # Note:  The log messages in this module are intended to be info level. The
    # verbose setting affects log messages in other modules in this package.

    logging.info("Starting Make Dispersion KML.")

    config = configuration.ConfigBuilder(options).config

    parameters = (config.get('DispersionGridInput', "PARAMETERS")
        or config.get('DispersionGridInput', "PARAMETER"))
    if not parameters:
        raise ValueError ("No NetCDF parameter(s) supplied.")
    if hasattr(parameters, "capitalize"):
        parameters = parameters.split()


    # this will load fires and events, dump to json, and
    # update the daily images utc offsets field if it was
    # auto
    fires_manager = fires.FiresManager(config)

    all_parameter_args = []
    for parameter in parameters:

        # Determine which mode to run OutputKML in
        if 'dispersion' in config.get('DEFAULT', 'MODES').split():

            # Create dispersion images directory within the specified
            # bsf output directory
            # For backwards compatibility, support old config key 'PARAMETER'
            dfu.create_dispersion_images_dir(config, parameter)

            # Generate smoke dispersion images
            logging.info("Processing smoke dispersion NetCDF data into plot images...")
            start_datetime, grid_bbox, heights = dg.create_dispersion_images(config, parameter)

            # Output dispersion grid bounds
            _output_grid_bbox(grid_bbox, config)

            # Post process smoke dispersion images
            logging.info("Formatting dispersion plot images...")
            dispersionimages.format_dispersion_images(config, parameter, heights)
        else:
            start_datetime = config.get("DEFAULT", "DATE") if config.has_option("DEFAULT", "DATE") else datetime.now()
            heights = None
            grid_bbox = None

        all_parameter_args.append({
            "parameter": parameter,
            "start_datetime": start_datetime,
            "heights": heights,
            "grid_bbox": grid_bbox
        })

    # Generate single KMZ
    smokedispersionkml.KmzCreator(config, all_parameter_args, fires_manager).create_all()

    # If enabled, reproject concentration images to display in a different projection
    if config.getboolean('DispersionImages', 'REPROJECT_IMAGES'):
        for a in all_parameter_args:
            dispersionimages.reproject_images(config, a['parameter'],
                a['grid_bbox'], a['heights'])

    logging.info("Make Dispersion finished.")

def _output_grid_bbox(grid_bbox, config):
    grid_info_file = config.get('DispersionGridOutput', "GRID_INFO_JSON")
    if grid_info_file is not None:
        logging.info("Outputting grid bounds to %s." % grid_info_file)
        grid_info_dict = {'bbox': grid_bbox}
        grid_info_json = json.dumps(grid_info_dict)
        with open(grid_info_file, 'w') as fout:
            fout.write(grid_info_json)
