import re

__all__ = [
    'TimeSeriesTypes', 'TIME_SET_DIR_NAMES',
    'TIME_SERIES_PRETTY_NAMES', 'CONFIG_COLOR_LABELS',
    'FILE_NAME_TIME_STAMP_PATTERNS', 'PARAMETER_LABELS',
    'PARAMETER_PLOT_LABELS'
]

class TimeSeriesTypes:
    """Effectively an enum of image time series types"""
    # Enum to represent different time series
    NUM_TYPES = 5
    HOURLY, THREE_HOUR, DAILY_MAXIMUM, DAILY_MINIMUM, DAILY_AVERAGE = list(range(NUM_TYPES))
    ALL = list(range(NUM_TYPES))

    @classmethod
    def all_for_parameter(cls, parameter):
        is_visual_range = re.sub("[ _-]*", "", parameter.lower()) == 'visualrange'
        return [a for a in cls.ALL
            if not (is_visual_range and cls.DAILY_MAXIMUM == a) and
              not (not is_visual_range and cls.DAILY_MINIMUM == a)]



# Define the time set keys, used in the image paths and filenames, here rather
# than hardcode multiple times below
# TODO: make these configurable?
TIME_SET_DIR_NAMES = {
    TimeSeriesTypes.HOURLY: 'hourly',
    TimeSeriesTypes.THREE_HOUR: 'three_hour',
    TimeSeriesTypes.DAILY_MAXIMUM: 'daily_maximum',
    TimeSeriesTypes.DAILY_MINIMUM: 'daily_minimum',
    TimeSeriesTypes.DAILY_AVERAGE: 'daily_average'
}

TIME_SERIES_PRETTY_NAMES = dict(
    (t, ' '.join([d.capitalize()
    for d in TIME_SET_DIR_NAMES[t].split('_')])) for t in TimeSeriesTypes.ALL
)

CONFIG_COLOR_LABELS = {
    TimeSeriesTypes.HOURLY: 'HOURLY_COLORS',
    TimeSeriesTypes.THREE_HOUR: 'THREE_HOUR_COLORS',
    TimeSeriesTypes.DAILY_MAXIMUM: 'HOURLY_COLORS', # Is this right?
    TimeSeriesTypes.DAILY_MINIMUM: 'HOURLY_COLORS', # Is this right?
    TimeSeriesTypes.DAILY_AVERAGE: 'DAILY_COLORS'
}

FILE_NAME_TIME_STAMP_PATTERNS = {
    TimeSeriesTypes.HOURLY:     "%Y%m%d%H%M",
    TimeSeriesTypes.THREE_HOUR:     "%Y%m%d%H%M",
    TimeSeriesTypes.DAILY_MAXIMUM: "%Y%m%d",
    TimeSeriesTypes.DAILY_MINIMUM: "%Y%m%d",
    TimeSeriesTypes.DAILY_AVERAGE: "%Y%m%d"
}

PARAMETER_LABELS = {
    'PM25': 'PM2.5',
    'VisualRange': 'Visual Range'
}

PARAMETER_PLOT_LABELS = {
    'PM25': r'$PM_{2.5} \/[\mu g/m^{3}]$',
    'VisualRange': 'Visual Range (miles)'
}