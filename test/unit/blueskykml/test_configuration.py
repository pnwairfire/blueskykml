from pytest import raises

from blueskykml.configuration import (
    BlueSkyKMLConfigParser, ConfigurationError
)


class TestBlueSkyKMLConfigParser(object):

    def setup_method(self):
        self.config_parser = BlueSkyKMLConfigParser()

    def test_set_and_get_string(self):
        self.config_parser.add_section("foo")

        self.config_parser.set("foo", "bar", "baz")
        assert "baz" == self.config_parser.get("foo", "bar")

        self.config_parser.set("foo", "bar", "1")
        assert "1" == self.config_parser.get("foo", "bar")

    def test_set_and_get_scalar(self):
        self.config_parser.add_section("foo")

        self.config_parser.set("foo", "bar", 1)
        assert 1 == self.config_parser.get("foo", "bar")

        self.config_parser.set("foo", "bar", 4.3)
        assert 4.3 == self.config_parser.get("foo", "bar")

    def test_set_and_get_list(self):
        self.config_parser.add_section("foo")

        self.config_parser.set("foo", "bar", ["sdf", "f"])
        assert ["sdf", "f"] == self.config_parser.get("foo", "bar")

        self.config_parser.set("foo", "bar", [1, 2, 3])
        assert [1, 2, 3] == self.config_parser.get("foo", "bar")

        self.config_parser.set("foo", "bar", [1.2, 3.4])
        assert [1.2, 3.4] == self.config_parser.get("foo", "bar")

        # For the following, the config parser will assume all values
        # are floats, based on the first
        self.config_parser.set("foo", "bar", [1.2, 3])
        assert [1.2,3.0] == self.config_parser.get("foo", "bar")

        self.config_parser.set("foo", "bar", [1, 3.4])
        # The following fails to cast '3.4' to an int when
        with raises(ValueError) as e:
            self.config_parser.get("foo", "bar")


    def test_set_and_get_utc_offsets(self):
        section = "DispersionImages"
        param = "DAILY_IMAGES_UTC_OFFSETS"
        self.config_parser.add_section(section)

        self.config_parser.set(section, param, "1,2,3")
        assert [1, 2, 3] == self.config_parser.get(section, param)

        self.config_parser.set(section, param, [1,2,3])
        assert [1, 2, 3] == self.config_parser.get(section, param)

        self.config_parser.set(section, param, 'auto')
        assert [] == self.config_parser.get(section, param)

        with raises(ConfigurationError) as e:
            self.config_parser.set(section, param, 4)
        with raises(ConfigurationError) as e:
            self.config_parser.set(section, param, 4.5)

    # TODO: add tests where config options are loaded from file
    #   might need to modify self.config_parser.TO_CONVERT to
    #   test setting and getting scalars?