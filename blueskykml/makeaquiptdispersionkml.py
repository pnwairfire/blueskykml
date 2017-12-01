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

    logging.info("Starting Make AQUIPT Dispersion KML.")

    config = configuration.ConfigBuilder(options, is_aquipt=True).config

    # Determine which mode to run OutputKML in
    if 'dispersion' in config.get('DEFAULT', 'MODES').split():
        # Create dispersion images directory within the specified bsf output directory
        dfu.create_dispersion_images_dir(config)

        # Generate smoke dispersion images
        logging.info("Processing smoke dispersion NetCDF data into plot images...")
        grid_bbox, heights = dispersiongrid.create_aquiptpost_images(config)

        # Post process smoke dispersion images
        logging.info("Formatting dispersion plot images...")
        dispersionimages.format_dispersion_images(config, verbose=options.verbose)
    else:
        grid_bbox = None

    # Generate KMZ
    smokedispersionkml.AquiptKmzCreator(config, grid_bbox,
        pretty_kml=options.prettykml, verbose=options.verbose).create_all()

    logging.info("Make AQUIPT Dispersion KML finished.")
