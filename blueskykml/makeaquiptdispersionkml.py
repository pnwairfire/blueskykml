import configuration
import dispersiongrid
import dispersion_file_utils as dfu
import dispersionimages
import smokedispersionkml

def main(options):
    print "Starting Make AQUIPT Dispersion KML."

    config = configuration.ConfigBuilder(options, is_aquipt=True).config

    # Determine which mode to run OutputKML in
    if 'dispersion' in config.get('DEFAULT', 'MODES').split():
        # Create dispersion images directory within the specified bsf output directory
        dfu.create_dispersion_images_dir(config)

        # Generate smoke dispersion images
        print "Processing smoke dispersion NetCDF data into plot images..."
        grid_bbox = dispersiongrid.create_aquiptpost_images(config,
            verbose=options.verbose)

        # Post process smoke dispersion images
        print "Formatting dispersion plot images..."
        dispersionimages.format_dispersion_images(config, verbose=options.verbose)
    else:
        grid_bbox = None

    # Generate KMZ
    smokedispersionkml.AquiptKmzCreator(config, grid_bbox,
        pretty_kml=options.prettykml, verbose=options.verbose).create_all()

    print "Make AQUIPT Dispersion KML finished."
