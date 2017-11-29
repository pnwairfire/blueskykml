import configparser
import logging
import os
from collections import defaultdict

__all__ = [
    'ConfigurationError',
    'ConfigBuilder'
]

class ConfigurationError(Exception):
    pass

class BlueSkyKMLConfigParser(configparser.ConfigParser):
    """Custom config parser class whose sole contribution is to
    transform values to and from their ultimate data type.
    (configparser.ConfigParser only supports storing config
    values as strings)
    """

    # config settings that are expected to be of a certain type
    # even if they were originally specified as strings
    TO_CONVERT = {
        'DispersionGridInput': {
            'LAYERS': {"type": list, "nested_type": int},
        },
        'Foo':{'baz': {'type': int}}
    }

    def __init__(self, *args, **params):
        super(BlueSkyKMLConfigParser, self).__init__(*args, **params)
        self._converted = defaultdict(lambda: {})

    def set(self, *args, **params):
        # in case we need to update args[2], make args is an mutable
        args = list(args)
        section = args[0]
        param = args[1]
        val = args[2]

        # use duck typing to see if it's a list or compatible type
        if hasattr(val, 'append'):
            val = self.convert_list_to_string(val, section, param, type(val[0]))

        elif hasattr(val, 'real'):
            val = self.convert_scalar_to_string(val, section, param, type(val))

        args[2] = val

        return super(BlueSkyKMLConfigParser, self).set(*args, **params)

    def convert_list_to_string(self, val, section, param, nested_type):
        logging.debug(' * Converting %s.%s from list of %s to string',
            section, param, nested_type)
        self._converted[section][param] = {
            "type": list, "nested_type": nested_type
        }
        return ','.join([str(l) for l in val])

    def convert_scalar_to_string(self, val, section, param, _type):
        logging.debug(' * Converting %s.%s from %s to string',
            section, param, _type)
        self._converted[section][param] = {"type": _type}
        return str(val)



    def get(self, *args, **params):
        section = args[0]
        param = args[1]
        val = super(BlueSkyKMLConfigParser, self).get(*args, **params)
        info = self._converted[section].get(param)

        # Config settings that were converted on input
        if info:
            if info['type'] == list:
                val = self.convert_to_list(val, section, param,
                    info['nested_type'])
            else:
                val = self.convert_to_scalar(val, section, param, info['type'])

        elif section in self.TO_CONVERT and param in self.TO_CONVERT[section]:
            info = self.TO_CONVERT[section][param]
            if info['type'] == list:
                val = self.convert_to_list(val, section, param, info['nested_type'])
            else:
                val = self.convert_to_scalar(val, section, param, info['type'])

        return val

    def convert_to_list(self, val, section, param, nested_type):
        logging.debug('Converting %s.%s from string to list of %s',
            section, param, nested_type)
        return [nested_type(l) for l in val.split(',')]

    def convert_to_scalar(self, val, section, param, _type):
        logging.debug('Converting %s.%s from string to %s',
            section, param, _type)
        return _type(val)



class ConfigBuilder(object):
    """Class to build configuration object from config file and command line
    options.

    Public attributes:
      config -- BlueSkyKMLConfigParser object representing what's in the
            config file overlaid with what was specified on the command line
    """

    def __init__(self, options, is_aquipt=False):
        self._options = options
        self._is_aquipt = is_aquipt
        self._build_config()

    def _log(self, msg):
        logging.debug(msg)

    def _build_config(self):
        self._load_default_config_file()
        self._load_custom_config_file()
        self._check_output_directory()
        self._set_defaults()
        self._apply_overrides()
        self._dump_configuration()
        self._final_check()

    def _dump_configuration(self):
        self._log(" * Final Config Settings:")
        default_section = self.config.defaults()
        for option, val in default_section.items():
            self._log(" *   [DEFAULT] %s = %s" % (option.upper(), val))

        for section in self.config.sections():
            for option in self.config.options(section):
                val = None
                for m in ('get', 'getboolean', 'getfloat', 'getint'):
                    try:
                        val = getattr(self.config, m)(section, option)
                        break
                    except:
                        pass

                if option not in default_section or default_section[option] != val:
                    self._log(" *   [%s] %s = %s" % (section, option.upper(), val))

    DEFAULT_CONFIG = os.path.join(
        os.path.dirname(__file__), 'config/default.ini')
    DEFAULT_AQUIPT_CONFIG = os.path.join(
        os.path.dirname(__file__), 'config/default-aquipt.ini')

    def _load_default_config_file(self):
        default_config_file = (self.DEFAULT_AQUIPT_CONFIG
            if self._is_aquipt else self.DEFAULT_CONFIG)
        self._log(" * Loading default config file %s" % (default_config_file))
        self.config = BlueSkyKMLConfigParser()
        self.config.read(default_config_file)

    def _load_custom_config_file(self):
        if self._options.configfile:
            if not os.path.isfile(self._options.configfile):
                raise ConfigurationError(
                    "Configuration file '%s' does not exist." % (
                    self._options.configfile))

            self._log(" * Loading custom config file %s" % (
                self._options.configfile))
            self.config.read(self._options.configfile)

    def _check_output_directory(self):
        output_dir = self._options.output_directory #.rstrip('/')

        if not output_dir:
            raise ConfigurationError("Output directory must be specified")

        if not os.path.exists(output_dir):
            # TODO: create it rather than raise exception
            raise ConfigurationError("Output directory '%s' does not exist." % output_dir)

        self._log(" * Using output directory %s" % (output_dir))
        self._add_config_option("DEFAULT", "MAIN_OUTPUT_DIR", output_dir, "output_directory")
        self._add_config_option("DEFAULT", "BSF_OUTPUT_DIR", output_dir, "output_directory") # For backwards compatibility

    OVERRIDES = [
        {
            "command_line_option": "inputfile",
            "section": "DispersionGridInput",
            "option": "FILENAME"
        },
        {
            "command_line_option": "layer",
            "section": "DispersionGridInput",
            "option": "LAYER"
        },
        {
            "command_line_option": "fire_locations_csv",
            "section": "SmokeDispersionKMLInput",
            "option": "FIRE_LOCATION_CSV"
        },
        {
            "command_line_option": "fire_events_csv",
            "section": "SmokeDispersionKMLInput",
            "option": "FIRE_EVENT_CSV"
        },
        {
            "command_line_option": "smoke_dispersion_kmz_file",
            "section": "SmokeDispersionKMLOutput",
            "option": "KMZ_FILE"
        },
        {
            "command_line_option": "fire_kmz_file",
            "section": "SmokeDispersionKMLOutput",
            "option": "KMZ_FIRE_FILE"
        }
    ]

    def _apply_overrides(self):

        # Apply overrides specified with the alias command-line options
        for o in self.OVERRIDES:
            val = getattr(self._options, o["command_line_option"])
            if val:
                self._add_config_option(o["section"], o["option"], val, o["command_line_option"])

        # Apply the overrides specified with the '-O'/'--config-option' command line option
        if self._options.config_options:
            for section, section_options in self._options.config_options.items():
                for option, val in section_options.items():
                    self._add_config_option(section, option, val, 'config-option')

    def _add_config_option(self, section, option, val, command_line_option=None):
        if section is not "DEFAULT" and not self.config.has_section(section):
            # TODO: make sure it's a valid section ?
            self.config.add_section(section)

        # TODO: make sure it's a valid option?
        cmd_opt_str = " (command line option '%s')" % (command_line_option.replace('_','-')) if command_line_option else ""
        self._log(" * Setting [%s] %s = %s%s" % (section, option, val, cmd_opt_str))
        self.config.set(section, option, val)



    EXTRA_FILES = [
        {
            "dir": os.path.normpath(os.path.join(os.path.dirname(__file__), "./assets")),
            "option_set": [
                ("SmokeDispersionKMLInput", "DISCLAIMER_IMAGE", "disclaimer.png"),
                ("SmokeDispersionKMLInput", "FIRE_EVENT_ICON", "fire_event.png"),
                ("SmokeDispersionKMLInput", "FIRE_LOCATION_ICON", "fire_location.png")
            ]
        },
        {
            "dir": os.path.normpath(os.path.join(os.path.dirname(__file__), "../bin")),
            "option_set":[
                ("PolygonsKML", "MAKEPOLYGONS_BINARY", "makepolygons")
            ]
        }
    ]

    def _set_defaults(self):
        for file_set in self.EXTRA_FILES:
            for section, option, file_name in file_set["option_set"]:
                if not self.config.has_option(section, option) or not self.config.get(section, option):
                    f = os.path.join(file_set["dir"], file_name)
                    self._add_config_option(section, option, f)

    def _final_check(self):
        if (self.config.has_option('PolygonsKML', 'MAKE_POLYGONS_KMZ')
                and self.config.getboolean('PolygonsKML', 'MAKE_POLYGONS_KMZ')):
            if not os.path.isfile(self.config.get('PolygonsKML', 'MAKEPOLYGONS_BINARY')):
                raise ConfigurationError("Makepolygons binary '%s' does not exist." %
                    self.config.get('PolygonsKML', 'MAKEPOLYGONS_BINARY'))

        # Fire locations csv
        fire_locations_csv = self.config.get('SmokeDispersionKMLInput', "FIRE_LOCATION_CSV")
        if not fire_locations_csv:
            raise ConfigurationError("Fire locations csv not specified.")
        if not os.path.isfile(fire_locations_csv):
            raise ConfigurationError("Fire locations csv '%s' does not exist." %
                self.config.get('SmokeDispersionKMLInput', 'FIRE_LOCATION_CSV'))

        # fire events csv
        if self.config.has_option('SmokeDispersionKMLInput', "FIRE_EVENT_CSV"):
            if not os.path.isfile(self.config.get('SmokeDispersionKMLInput', "FIRE_EVENT_CSV")):
                # it's not essential, so log warning, set it to None in the
                # config, and move on
                self._log(" * WARNING: Fire events csv '%s' does not exist. Ignoring." %
                    self.config.get('SmokeDispersionKMLInput', 'FIRE_EVENT_CSV'))
                self.config.set('SmokeDispersionKMLInput', "FIRE_EVENT_CSV", None)
        else:
            # TDOO: set this someplace else
            self.config.set('SmokeDispersionKMLInput', "FIRE_EVENT_CSV", None)
