import datetime
import csv
import json
import logging

from afdatetime.parsing import parse_utc_offset

from . import firedescriptions

class FireData(object):
    area_units = "acres"
    date_time_format = "%Y%m%d"
    emission_fields = ['pm2.5', 'pm10', 'co', 'co2', 'ch4', 'nox', 'nh3', 'so2', 'voc']
    fire_types = {'RX': "Prescribed Fire", 'WF': "Wild Fire"}

    def __init__(self):
        self.id = ''
        self.fire_type = ''
        self.area = 0
        self.emissions = dict()
        self.lat = 0
        self.lon = 0
        self.utc_offset = None
        self.start_date_time = None
        self.end_date_time = None

    def placemark_description(self):
        raise NotImplementedError("Abstract method not yet implemented")


class FireLocationInfo(FireData):
    def __init__(self):
        super(FireLocationInfo, self).__init__()
        self.event_name = None
        self.event_id = None
        self.fccs_number = None
        # TODO: Add Fuel Loading?

    def _build_event_name(self, raw_data):
        # TODO: Mimic SFEI event naming?
        self.event_name = "Satellite Hotspot Detection(s)*"
        political_info = [raw_data[f] for f in
            ('state', 'county', 'country') if raw_data.get(f)]
        if political_info:
            self.event_name += " in " + ", ".join(political_info)
        elif raw_data.get('latitude') and raw_data.get('longitude'):
            self.event_name += " at {}, {}".format(
                raw_data['latitude'], raw_data['longitude'])
        # else, leave as "Satellite Hotspot Detection(s)*"
        return self

    def _set_date_time(self, date_time_str):
        date_time_str = date_time_str[:8]  # grab only yyyymmdd
        self.start_date_time = datetime.datetime.strptime(date_time_str, self.date_time_format)
        self.end_date_time = self.start_date_time + datetime.timedelta(days=1, seconds=-1)
        return self

    def build_from_raw_data(self, raw_data):
        self.id = raw_data['id']
        self.fire_type = raw_data['type']
        self._set_date_time(raw_data['date_time'])
        self.lat = float(raw_data['latitude'])
        self.lon = float(raw_data['longitude'])

        # 'utc_offset' was recently introduced to the fire locations
        # csv, so handle case where it doesn't exist
        if raw_data.get('utc_offset'):
            try:
                self.utc_offset = int(parse_utc_offset(raw_data['utc_offset']))
            except ValueError as e:
                # cast to float before int, since int('-5.0') raises value error
                self.utc_offset = int(float(raw_data['utc_offset']))

        self.area = round(float(raw_data['area']), 2)
        # Set the event name based on optional raw data
        event_name = raw_data.get('event_name')
        # HACK: some upstream process is setting event name to '[None]'
        if event_name and event_name != '[None]':
            self.event_name = event_name
        else:
            self._build_event_name(raw_data)
        # Set event_id based on optional raw data, handling the cases where the
        # 'event_guid' and/or 'event_id' columns exist but have empty strings
        self.event_id = raw_data.get('event_guid') or raw_data.get('event_id') or self.id
        # Set the emissions fields based on optional raw data
        for field in self.emission_fields:
            value = raw_data.get(field)
            if value: # else ignore the field
                self.emissions[field] = round(float(value), 2)
        # Set the fccs number based on optional raw data
        self.fccs_number = raw_data.get('fccs_number')
        self.veg = raw_data.get('VEG') or raw_data.get('veg')

    def placemark_description(self):
        return firedescriptions.build_fire_location_description(self)


class FireEventInfo(FireData):
    def __init__(self):
        super(FireEventInfo, self).__init__()
        self.name = ''
        self.daily_stats_by_fccs_num = dict()
        self.daily_area = dict()
        self.daily_emissions = dict()
        self.fire_locations = list()
        self.daily_num_locations = dict()
        self.num_locations = 0
        # TODO: Add Fuel Loading

    def _update_daily_stats_by_fccs_num(self, fire_location):
        dt = fire_location.start_date_time
        if dt not in self.daily_stats_by_fccs_num:
            self.daily_stats_by_fccs_num[dt] = {}
        fccs_number = fire_location.fccs_number or 'Unknown'
        if fccs_number not in self.daily_stats_by_fccs_num[dt]:
            self.daily_stats_by_fccs_num[dt][fccs_number] = {
                'total_area': 0, 'description': fire_location.veg
            }
        d = self.daily_stats_by_fccs_num[dt][fccs_number]
        d['total_area'] += fire_location.area
        d['description'] = d['description'] or fire_location.veg

    def _update_daily_area(self, date_time, location_area):
        if date_time not in self.daily_area:
            self.daily_area[date_time] = 0
        self.daily_area[date_time] += location_area
        self.area += location_area

    def _update_daily_emissions(self, date_time, location_emissions):
        if date_time not in self.daily_emissions:
            self.daily_emissions[date_time] = dict()
        for field in location_emissions:
            if field not in self.daily_emissions[date_time]:
                self.daily_emissions[date_time][field] = 0
            if field not in self.emissions:
                self.emissions[field] = 0
            self.daily_emissions[date_time][field] += location_emissions[field]
            self.emissions[field] += location_emissions[field]  # update total emissions as well

    def _update_date_time(self, start_date_time, end_date_time):
        if not self.start_date_time or self.start_date_time > start_date_time:
            self.start_date_time = start_date_time
        if not self.end_date_time or self.end_date_time < end_date_time:
            self.end_date_time = end_date_time

    def _update_daily_num_locations(self, date_time):
        if not date_time in self.daily_num_locations:
            self.daily_num_locations[date_time] = 0
        self.daily_num_locations[date_time] += 1
        self.num_locations += 1  # update total number of fire locations as well

    def build_data_from_locations(self):
        lat_sum = 0
        lon_sum = 0
        for fire_location in self.fire_locations:
            if not self.name:
                self.name = fire_location.event_name
            if not self.id:
                self.id = fire_location.event_id
            if not self.fire_type:
                self.fire_type = fire_location.fire_type
            lat_sum += fire_location.lat
            lon_sum += fire_location.lon
            self._update_daily_area(fire_location.start_date_time, fire_location.area)
            self._update_daily_emissions(fire_location.start_date_time, fire_location.emissions)
            self._update_date_time(fire_location.start_date_time, fire_location.end_date_time)
            self._update_daily_num_locations(fire_location.start_date_time)
            self._update_daily_stats_by_fccs_num(fire_location)
        self.lat = lat_sum / self.num_locations  # Set centroid lat
        self.lon = lon_sum / self.num_locations  # Set centroid lon
        return self

    def placemark_description(self, include_disclaimer=True):
        return firedescriptions.build_fire_event_description(
            self, include_disclaimer)


class FiresManager(object):

    def __init__(self, config):
        self.config = config
        self.fire_locations = self._build_fire_locations(
            config.get("SmokeDispersionKMLInput", "FIRE_LOCATION_CSV"))
        self.fire_events = self._build_fire_events(
            config.get("SmokeDispersionKMLInput", "FIRE_EVENT_CSV"))
        self._set_auto_daily_images_utc_offsets()

    # Data Gathering Methods

    def _build_fire_locations(self, fire_locations_csv):
        fire_location_dicts = list(csv.DictReader(open(fire_locations_csv, 'r', encoding="utf-8")))

        fire_locations = list()
        for fire_dict in fire_location_dicts:

            fire_location = FireLocationInfo()
            fire_location.build_from_raw_data(fire_dict)
            fire_locations.append(fire_location)

        self._dump_fire_locations_to_json(fire_locations_csv, fire_location_dicts)

        return fire_locations

    def _dump_fire_locations_to_json(self, fire_locations_csv, fire_location_dicts):
        """Dumps fire locations to file in json format.

        If fire_locations_csv is of the form
            /path/to/<filename>.csv'
        then dump json to
            /path/to/<filename>.json

        Otherwise, dump to
            '/path/to/fire_locations.json'
        (i.e. 'fire_locations.json' in the same dir as fire_locations_csv)
        """
        try:
            fire_locations_json = re.sub('\.csv$', '.json', fire_locations_csv)
            if fire_locations_json == fire_locations_csv:
                fire_locations_json = os.path.join(os.path.dirname(
                    fire_locations_csv), 'fire_locations.json')
            with open(fire_locations_json, 'w', encoding="utf-8") as f:
                f.write(json.dumps(fire_location_dicts))
        except:
            # we can live without the json dump
            pass

    def _build_fire_events(self, fire_events_csv):
        fire_events_dict = dict()
        for fire_location in self.fire_locations:
            # Set event id to fire's id if event id isn't defined, or make
            # up a new event id if neither fire id nor event id are defined
            if not fire_location.event_id:
                fire_location.event_id = fire_location.id or str(uuid.uuid4())

            if fire_location.event_id not in fire_events_dict:
                fire_events_dict[fire_location.event_id] = FireEventInfo()
            fire_events_dict[fire_location.event_id].fire_locations.append(fire_location)

        for event_id in fire_events_dict:
            fire_events_dict[event_id].build_data_from_locations()

        # fill in fire even names if events csv file was specified
        if fire_events_csv:
            for row in csv.DictReader(open(fire_events_csv, 'r', encoding="utf-8")):
                # if the event name is defined in the events csv, assume it's
                # correct and thus don't worry about overriding the possibly
                # correct name pulled from the locations csv
                if row['id'] in fire_events_dict and row.get('event_name'):
                    fire_events_dict[row['id']].name = row['event_name']

        fire_events = list(fire_events_dict.values())
        return fire_events

    def _set_auto_daily_images_utc_offsets(self):
        if not self.config.get("DispersionImages", "DAILY_IMAGES_UTC_OFFSETS"):
            utc_offsets = set([f.utc_offset
                for f in self.fire_locations if f.utc_offset is not None])
            utc_offsets.add(0)
            utc_offsets = list(utc_offsets)
            logging.debug("Auto setting DispersionImages > DAILY_IMAGES_UTC_OFFSETS"
                " to %s", utc_offsets)
            self.config.set("DispersionImages", "DAILY_IMAGES_UTC_OFFSETS",
                    utc_offsets)
