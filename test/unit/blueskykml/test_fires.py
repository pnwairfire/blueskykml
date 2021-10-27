import datetime

from py.test import raises

from blueskykml import configuration, fires


class TestFireLocationInfo_BuildFromRaWData(object):

    RAW_DATA_BSP = {
        'id': '202008130000_202008192359_152831138-154099469',
        'event_id': '',
        'latitude': '26.26859',
        'longitude': '-98.27474',
        'utc_offset': '-05:00',
        'source': 'HMS_VIIRS_SUOMI',
        'type': 'WF',
        'date_time': '20200813',
        'event_name': '',
        'fccs_number': '0',
        'fuelbed_fractions': '0 1.0',
        'heat': '6444399750.933901',
        'pm2.5': '3.455938336427968',
        'pm10': '4.078007236985004',
        'co': '24.7768521604355',
        'co2': '685.8598067688936',
        'ch4': '0.7917362513450691',
        'nh3': '0.605076448850053',
        'so2': '0.2749323522146909',
        'voc': '7.152530875214235',
        'nox': '0.875691719464744',
        'consumption_total': '402.7749844333687',
        'consumption_flaming': '358.44449599003184',
        'consumption_smoldering': '42.89607844333687',
        'consumption_residual': '1.4344099999999989',
        'area': '40.0',
        'elevation': '',
        'slope': '',
        'moisture_1hr': '',
        'moisture_10hr': '',
        'moisture_100hr': '',
        'moisture_1khr': '',
        'moisture_live': '',
        'moisture_duff': '',
        'canopy_consumption_pct': '',
        'min_wind': '',
        'max_wind': '',
        'min_wind_aloft': '',
        'max_wind_aloft': '',
        'min_humid': '',
        'max_humid': '',
        'min_temp': '',
        'max_temp': '',
        'min_temp_hour': '',
        'max_temp_hour': '',
        'sunrise_hour': '',
        'sunset_hour': '',
        'snow_month': '',
        'rain_days': '',
        'state': '',
        'county': '',
        'country': ''
    }
    RAW_DATA_BSF = dict(RAW_DATA_BSP, date_time='202008130000-05:00')
    RAW_DATA_INVALID = dict(RAW_DATA_BSP, date_time='2020asd0813T00:00-05:00')

    EXPECTED_FLI_FIELDS = {
        'id': '202008130000_202008192359_152831138-154099469',

        # 'event_id' is set to 'id' if neither it or 'event_guid' are in the raw data
        'event_id': '202008130000_202008192359_152831138-154099469',

        'lat': 26.26859,
        'lon': -98.27474,

        #'source': 'HMS_VIIRS_SUOMI', # not loaded
        'fire_type': 'WF',

        'start_date_time': datetime.datetime(2020,8,13),
        'utc_offset': -5,

        # event name is set dynamically set it not in raw data
        'event_name': 'Satellite Hotspot Detection(s)* at 26.26859, -98.27474',

        'fccs_number': '0',

        # 'fuelbed_fractions': '0 1.0', # not loaded
        # 'heat': '6444399750.933901', # not loaded

        # emissions are nested and rounded
        'emissions': {
            'pm2.5': 3.46,
            'pm10': 4.08,
            'co': 24.78,
            'co2': 685.86,
            'ch4': 0.79,
            'nh3': 0.61,
            'so2': 0.27,
            'voc': 7.15,
            'nox': 0.88
        },

        # consumption not loaded
        # 'consumption_total': '402.7749844333687',
        # 'consumption_flaming': '358.44449599003184',
        # 'consumption_smoldering': '42.89607844333687',
        # 'consumption_residual': '1.4344099999999989',

        'area': 40.0,

        #'elevation': '',  # not loaded
        #'slope': '',  # not loaded

        # moisture not loaded
        # 'moisture_1hr': '',
        # 'moisture_10hr': '',
        # 'moisture_100hr': '',
        # 'moisture_1khr': '',
        # 'moisture_live': '',
        # 'moisture_duff': '',
        # 'canopy_consumption_pct': '',  # not loaded

        # met fields not loaded
        # 'min_wind': '',
        # 'max_wind': '',
        # 'min_wind_aloft': '',
        # 'max_wind_aloft': '',
        # 'min_humid': '',
        # 'max_humid': '',
        # 'min_temp': '',
        # 'max_temp': '',
        # 'min_temp_hour': '',
        # 'max_temp_hour': '',
        # 'sunrise_hour': '',
        # 'sunset_hour': '',
        # 'snow_month': '',
        # 'rain_days': '',

        # geographical fields not loaded
        # 'state': '',
        # 'county': '',
        # 'country': ''
    }


    def test_bsp_date_time(self):
        fli = fires.FireLocationInfo()
        fli.build_from_raw_data(self.RAW_DATA_BSP)
        for f,v  in self.EXPECTED_FLI_FIELDS.items():
            assert getattr(fli, f) == v


    def test_bsf_date_time(self):
        fli = fires.FireLocationInfo()
        fli.build_from_raw_data(self.RAW_DATA_BSF)
        for f,v  in self.EXPECTED_FLI_FIELDS.items():
            assert getattr(fli, f) == v

    def test_invalid_datetime(self):
        fli = fires.FireLocationInfo()
        with raises(ValueError) as e:
            fli.build_from_raw_data(self.RAW_DATA_INVALID)
        assert e.value.args[0] == "Invalid datetime format '2020asd0'"
