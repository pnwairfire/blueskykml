import datetime
import os
import re
import uuid
import subprocess

from .constants import *
from .dispersiongrid import BSDispersionGrid
from .polygon_generator import PolygonGenerator
from . import dispersion_file_utils as dfu

try:
    from .pykml import pykml
    from .pykml.kml_utilities import zip_files
except ImportError:
    from . import pykml
    from kml_utilities import zip_files

# Constants
KML_TIMESPAN_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
KML_TIMESPAN_DATE_FORMAT = "%Y-%m-%d"



class KmzCreator(object):

    URL_MATCHER = re.compile('^https?://')

    def __init__(self, config, grid_bbox, heights,
            fires_manager, start_datetime=None,
            legend_name="colorbar.png", pretty_kml=False):
        self._config = config
        self._grid_bbox = grid_bbox
        self._heights = heights

        self._start_datetime = start_datetime
        self._pretty_kml = pretty_kml

        self._modes = config.get('DEFAULT', 'MODES')
        self._concentration_param_label = config.get(
            'SmokeDispersionKMLOutput', "PARAMETER_LABEL")
        if re.sub("[ _-]*", "", self._concentration_param_label.lower()) == 'visualrange':
            self._concentration_param_label = "Visual Range"

        self._dispersion_image_dir = config.get(
            'DispersionGridOutput', "OUTPUT_DIR")

        section = 'SmokeDispersionKMLInput'
        self._met_type = config.get(section, "MET_TYPE")
        self._disclaimer_image = config.get(section, "DISCLAIMER_IMAGE")

        self._fire_location_icon = config.get(section, "FIRE_LOCATION_ICON")
        self._fire_location_icon_is_url = not not self.URL_MATCHER.match(
            self._fire_location_icon)
        self._fire_event_icon = config.get(section, "FIRE_EVENT_ICON")
        self._fire_event_icon_is_url = not not self.URL_MATCHER.match(
            self._fire_event_icon)

        self._do_create_polygons = (self._config.has_section('PolygonsKML') and
            self._config.getboolean('PolygonsKML', 'MAKE_POLYGONS_KMZ') and
            'dispersion' in self._modes)

        # Collect fire data and concentration images
        self._fire_information = self._create_fire_info_folder(
            fires_manager.fire_events)

        self._screen_lookat = None
        if start_datetime:
            self._screen_lookat = self._create_screen_lookat(start=start_datetime, end=start_datetime)
        location_style_group = self._create_style_group('location',
            os.path.basename(self._fire_location_icon) if not
            self._fire_location_icon_is_url else self._fire_location_icon)
        event_style_group = self._create_style_group('event',
            os.path.basename(self._fire_event_icon) if not
            self._fire_event_icon_is_url else self._fire_event_icon)
        self._combined_style_group = location_style_group + event_style_group
        self._disclaimer = self._create_screen_overlay('Disclaimer', os.path.basename(self._disclaimer_image),
                                            overlay_x=1.0, overlay_y=1.0, screen_x=1.0, screen_y=1.0)
        self._concentration_information = None
        if 'dispersion' in self._modes:
            self._dispersion_images = self._collect_images()
            self._concentration_information = self._create_concentration_information()
            self._image_assets = self._collect_image_assets()
            if self._do_create_polygons:
                pgGen = PolygonGenerator(self._config)
                self._polygon_kmls = [(os.path.join(pgGen.output_dir, f), dt) for f,dt in pgGen.kml_files]
                self._polygon_legend = os.path.join(pgGen.output_dir, pgGen.legend_filename)
                self._polygon_information = self._create_polygon_information(self._polygon_kmls)
                # TODO: set color on _polygon_screen_overlay?
                self._polygon_screen_overlay = self._create_screen_overlay('Legend', pgGen.legend_filename)

    def create(self, kmz_name, kml_name, prefix, include_fire_information,
            include_disclaimer, include_concentration_images, include_polygons):
        kml = pykml.KML()

        root_doc_name = ("%s %s" % (prefix, self._start_datetime.strftime('%Y%m%d'))
            if self._start_datetime else prefix)
        if self._met_type:
            root_doc_name += " %s" % (self._met_type)
        root_doc = pykml.Document().set_name(root_doc_name).set_open(True)

        # Set default KML screen time/position
        if self._screen_lookat:
            root_doc.with_time(self._screen_lookat)

        # Create and add style KML to root Document
        if include_fire_information:
            for style in self._combined_style_group:
                root_doc.with_style(style)
            root_doc.with_feature(self._fire_information)

        if include_disclaimer:
            root_doc.with_feature(self._disclaimer)

        if 'dispersion' in self._modes:
            if include_concentration_images:
                root_doc.with_feature(self._concentration_information)
            if include_polygons:
                root_doc.with_feature(self._polygon_screen_overlay)
                root_doc.with_feature(self._polygon_information)

        kml.add_element(root_doc)

        # TODO: move bluesky.osutils to pyairfire (or just copy
        #   bluesky.osutils.create_working_dir to this package/module) and use
        #   create_working_dir here (or maybe only use it if configured to
        #   throw away intermediate files, other than the kml, which is
        #   already removed once used)
        self._create_kml_file(kml, kml_name)

        kmz_assets = [kml_name]
        if include_disclaimer:
            kmz_assets.append(self._disclaimer_image)
        if include_fire_information:
            if not self._fire_location_icon_is_url:
                kmz_assets.append(self._fire_location_icon)
            if not self._fire_event_icon_is_url:
                kmz_assets.append(self._fire_event_icon)
        if 'dispersion' in self._modes:
            if include_concentration_images:
                kmz_assets.extend(self._image_assets)
            if include_polygons:
                kmz_assets.extend([e[0] for e in self._polygon_kmls])
                kmz_assets.append(self._polygon_legend)

        self._create_kmz(kmz_name, kmz_assets)
        os.remove(kml_name)

    def create_all(self):
        if (self._config.has_option('SmokeDispersionKMLOutput', "KMZ_FILE")
                and self._config.get('SmokeDispersionKMLOutput', "KMZ_FILE")):
            self.create(self._config.get('SmokeDispersionKMLOutput', "KMZ_FILE"),
                'doc.kml', 'BlueSky Smoke Dispersion', True, True, True, False)

        if (self._config.has_option('SmokeDispersionKMLOutput', "KMZ_FIRE_FILE")
                and self._config.get('SmokeDispersionKMLOutput', "KMZ_FIRE_FILE")):
            self.create(self._config.get('SmokeDispersionKMLOutput', "KMZ_FIRE_FILE"),
                'doc_fires.kml', 'BlueSky Fires', True, False, False, False)

        if self._do_create_polygons:
            self.create(self._config.get('PolygonsKML', "KMZ_FILE"), 'doc_polygons.kml',
                'BlueSky Smoke Dispersion- Polygons', True, False, False, True)


    ##
    ## Private Methods
    ##

    # Data Generating Methods

    def _collect_images(self):
        return dfu.collect_dispersion_images_for_kml(self._config, self._heights)


    # KML Creation Methods

    def _create_screen_lookat(self, start=None, end=None, latitude=40, longitude=-100,
                              altitude=4000000, altitude_mode='relativeToGround'):
        time_span = pykml.TimeSpan()
        if start is not None:
            time_span.set_begin(start.strftime(KML_TIMESPAN_DATE_FORMAT))
        if end is not None:
            time_span.set_end(end.strftime(KML_TIMESPAN_DATE_FORMAT))
        return (pykml.LookAt()
                .with_time(time_span)
                .set_latitude(latitude)
                .set_longitude(longitude)
                .set_altitude(altitude)
                .set_tilt(0.0)
                .set_altitude_mode(altitude_mode))


    def _create_style_group(self, id, icon_url):
        normal_style_id = id + '_normal'
        highlight_style_id = id + '_highlight'
        style_map = self._create_style_map(id, normal_style_id, highlight_style_id)
        normal_style = self._create_style(normal_style_id, icon_url, label_scale=0.0)
        highlight_style = self._create_style(highlight_style_id, icon_url)
        return style_map, normal_style, highlight_style


    def _create_style_map(self, style_map_id, normal_style_id, highlight_style_id):
        pair_normal = pykml.Pair().set_key('normal').set_style_url(normal_style_id)
        pair_highlight = pykml.Pair().set_key('highlight').set_style_url(highlight_style_id)
        return pykml.StyleMap(style_map_id).with_pair(pair_normal).with_pair(pair_highlight)


    def _create_style(self, id, icon_url, label_scale=1.0, icon_scale=1.0):
        # Balloon Style
        balloon_style_text = '$[description]'
        balloon_style = pykml.BalloonStyle().set_text(balloon_style_text)
        # Label Style
        label_style = pykml.LabelStyle().set_scale(label_scale)
        # Icon Style
        icon = (pykml.Icon()
                .set_href(icon_url)
                .set_refresh_interval(0.0)
                .set_view_refresh_time(0.0)
                .set_view_bound_scale(0.0))
        icon_style = pykml.IconStyle().set_scale(icon_scale).set_heading(0.0).with_icon(icon)
        return (pykml.Style(id)
                .with_balloon_style(balloon_style)
                .with_label_style(label_style)
                .with_icon_style(icon_style))


    def _create_screen_overlay(self, name, image_path,
                               overlay_x=0.0, overlay_xunits='fraction', overlay_y=0.0, overlay_yunits='fraction',
                               screen_x=0.0, screen_xunits='fraction', screen_y=0.0, screen_yunits='fraction',
                               size_x=-1.0, size_xunits='fraction', size_y=-1.0, size_yunits='fraction',
                               visible=True):
        icon = pykml.Icon().set_href(image_path)
        return (pykml.ScreenOverlay()
                .set_name(name)
                .with_icon(icon)
                .set_visibility(visible)
                .set_overlay_xy(overlay_x, overlay_y, overlay_xunits, overlay_yunits)
                .set_screen_xy(screen_x, screen_y, screen_xunits, screen_yunits)
                .set_size(size_x, size_y, size_xunits, size_yunits))


    def _create_fire_info_folder(self, fire_events):
        info_folder = pykml.Folder().set_name('Fire Information')
        for fire_event in fire_events:
            event_folder = self._create_fire_event_folder(fire_event)
            info_folder.with_feature(event_folder)
        return info_folder


    def _create_fire_event_folder(self, fire_event):
        include_disclaimer = self._config.getboolean(
            'SmokeDispersionKMLOutput',
            'INCLUDE_DISCLAIMER_IN_FIRE_PLACEMARKS')
        event_description = fire_event.placemark_description(
            include_disclaimer=include_disclaimer)
        event_placemark = self._create_placemark(fire_event.name, event_description, '#event', fire_event.lat,
                                            fire_event.lon)
        return (pykml.Folder()
                .set_name(fire_event.name)
                .with_feature(event_placemark))


    def _create_placemark(self, name, description, style_id, lat, lon, alt=0.0, start_date_time=None,
                          end_date_time=None, altitude_mode="relativeToGround", visible=True):
        point = pykml.Point().set_coordinates((lon, lat, alt)).set_altitude_mode(altitude_mode)
        placemark =  (pykml.Placemark()
                .set_name(name)
                .set_visibility(visible)
                .set_description(description)
                .set_style_url(style_id)
                .with_geometry(point))
        if start_date_time and end_date_time:
            time_span = (pykml.TimeSpan()
                .set_begin(start_date_time.strftime(KML_TIMESPAN_DATETIME_FORMAT))
                .set_end(end_date_time.strftime(KML_TIMESPAN_DATETIME_FORMAT)))
            placemark = placemark.with_time(time_span)

        return placemark


    def _create_concentration_information(self):
        kml_root = pykml.Folder().set_name('%s from Wildland Fire'
            % self._concentration_param_label).set_open(True)
        min_height_label = str(min([int(e.replace('m',''))
            for e in self._dispersion_images])) + 'm'
        for height_label in self._dispersion_images:
            height_root = pykml.Folder().set_name('Height %s ' % (height_label))
            for time_series_type in TimeSeriesTypes.ALL:
                t_dict = self._dispersion_images[height_label][time_series_type]
                visible = (TimeSeriesTypes.DAILY_MAXIMUM == time_series_type
                    and height_label == min_height_label)
                time_series_name = TIME_SERIES_PRETTY_NAMES[time_series_type]
                if time_series_type in (TimeSeriesTypes.DAILY_MAXIMUM,
                        TimeSeriesTypes.DAILY_AVERAGE):
                    time_series_root = pykml.Folder().set_name(time_series_name)
                    for utc_offset_value, images_dict in t_dict.items():
                        self._create_concentration_information_for_images(
                            time_series_root, images_dict, visible,
                            utc_offset_value)
                        visible = False # arbitrarily make first time zone
                    height_root = height_root.with_feature(time_series_root)
                else:
                    self._create_concentration_information_for_images(
                        height_root, t_dict, visible, time_series_name)
            kml_root = kml_root.with_feature(height_root)
        return kml_root

    def _create_concentration_information_for_images(self, parent_root,
            images_dict, visible, pretty_name):
        if images_dict:
            if images_dict['legend']:
                # TODO:  put legends in concentration folders?
                overlay = self._create_screen_overlay(
                    '%s Key' % (pretty_name), images_dict['legend'],
                    visible=visible)
                parent_root = parent_root.with_feature(overlay)

            if images_dict['smoke_images']:
                name = '%s %s' % (pretty_name,
                    self._concentration_param_label)
                data = self._create_concentration_folder(name,
                    images_dict['smoke_images'], visible=visible)
                parent_root = parent_root.with_feature(data)

    UTC_OFFSET_FILENAME_SUFFIX_EXTRACTOR = re.compile('_UTC[+-][0-9]{4}')

    def _create_concentration_folder(self, name, images, visible=False):
        concentration_folder = pykml.Folder().set_name(name)
        for image in images:
            # handle files names like '10m_hourly_201405300000.png' and
            # ' 10m_daily_maximum_20140529_UTC-0700.png'
            image_name_parts = self.UTC_OFFSET_FILENAME_SUFFIX_EXTRACTOR.sub(
                '', image).replace('.', '_').split('_')
            overlay_datetime_str = image_name_parts[-2]
            if len(overlay_datetime_str) == 8:
                image_datetime_format = '%Y%m%d'
                overlay_datetime_format = '%Y%m%d'
                end_offset = 24
            else:  # len == 12
                image_datetime_format = '%Y%m%d%H00'
                overlay_datetime_format = '%Y%m%d%H'
                end_offset = 1
            overlay_start = datetime.datetime.strptime(overlay_datetime_str, image_datetime_format)
            overlay_end = overlay_start + datetime.timedelta(hours=end_offset, seconds=-1)
            overlay_name = "%s %s" % (name, overlay_start.strftime(overlay_datetime_format))
            concentration_overlay = self._create_ground_overlay(
                overlay_name, image, start_date_time=overlay_start,
                end_date_time=overlay_end, visible=visible)
            concentration_folder.with_feature(concentration_overlay)
        return concentration_folder


    def _collect_image_assets(self):
        images = []

        def _collect(data):
            if 'smoke_images' in data:
                if data['legend']:
                    images.append(os.path.join(data['root_dir'], data['legend']))
                if data['smoke_images']:
                    images.extend([os.path.join(data['root_dir'], i) for i in data['smoke_images']])
            else:
                for k in data:
                    _collect(data[k])

        _collect(self._dispersion_images)

        return images


    def _create_polygon_information(self, polygon_kmls):
        kml_root = pykml.Folder().set_name('%s from Wildland Fire' %
            self._concentration_param_label).set_open(True)
        for (poly_kml, dt) in polygon_kmls:
            link = pykml.Link().set_href(os.path.basename(poly_kml))
            list_style = pykml.ListStyle().set_list_item_type('checkHideChildren')
            style = pykml.Style().with_list_style(list_style)
            time_span = pykml.TimeSpan().set_begin(dt.isoformat()).set_end((dt + datetime.timedelta(hours=1)).isoformat())
            f = (pykml.NetworkLink()
                .set_name(dt.strftime("Hour %HZ"))
                .set_visibility(True)
                .with_link(link)
                .with_style(style)
                .with_time(time_span))

            kml_root.with_feature(f)

        return kml_root

    def _sort_images_legends(self, images, legends):
        combined = list(zip(images, legends))
        combined_natural = self._natural_sort_tuple_list(combined)
        return tuple(list(item) for item in zip(*combined_natural)) # "unzip" the zipped images/legends back into different lists


    def _natural_sort_tuple_list(self, tuple_list):
        """ Alpha-numerically sort the given tuple list, as opposed to the alpha-ascii sort normally performed
        """
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(x) for x in re.split('([0-9]+)', key[0])] # uses 1st item in tuple list as key
        return sorted(tuple_list, key=alphanum_key)


    def _create_ground_overlay(self, name, image_path, start_date_time=None, end_date_time=None, visible=False):
        if start_date_time:
            start_date_str = start_date_time.strftime(KML_TIMESPAN_DATETIME_FORMAT)
        else:
            start_date_str = ""
        if end_date_time:
            end_date_str = end_date_time.strftime(KML_TIMESPAN_DATETIME_FORMAT)
        else:
            end_date_str = ""
        time_span = (pykml.TimeSpan()
                     .set_begin(start_date_str)
                     .set_end(end_date_str))
        icon = pykml.Icon().set_href(image_path)
        west, south, east, north = (float(val) for val in self._grid_bbox)
        lat_lon_box = pykml.LatLonBox().set_west(west).set_south(south).set_east(east).set_north(north)
        return (pykml.GroundOverlay()
                .set_name(name)
                .set_visibility(visible)
                .with_time(time_span)
                .with_icon(icon)
                .with_lat_lon_box(lat_lon_box))


    def _create_kml_file(self, kml, kml_name):
        with open(kml_name, 'w', encoding="utf-8") as out:
            if self._pretty_kml:
                out.write(kml.to_pretty_kml())
            else:
                out.write(str(kml))


    def _create_kmz(self, kmz_file, kmz_assets):
        zip_files(kmz_file, kmz_assets)



