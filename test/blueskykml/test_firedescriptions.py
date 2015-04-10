import datetime
import mock

#from py.test import raises

from blueskykml import firedescriptions

##
## Tests for Fire
##

class TestBuildFuelbeds(object):

    def setup(self):
        self.fire_event = mock.Mock()

    def test_build_fuelbeds_empty(self):
        self.fire_event.daily_stats_by_fccs_num = {}
        expected = ""
        assert expected == firedescriptions._build_fuelbeds(self.fire_event)

    def test_build_fuelbeds_1_day_1_fuelbed(self):
        self.fire_event.daily_stats_by_fccs_num = {
            datetime.datetime(2014, 5, 31, 0, 0): {
                '49': {
                    'total_area': 200.0, 'description': 'Creosote bush shrubland'
                }
            }
        }
        expected = (
            '<div class="section">'
                ' <div class="header">FCCS Fuelbeds</div>'
                ' <div class="list">'
                    '<div class="item">'
                        '<span class="fccs-num">#49</span> -'
                        ' <span class="fccs-area">200 acres</span> -'
                        ' <span class="fccs-desc">Creosote bush shrubland</span>'
                    '</div>'
                '</div>'
            ' </div>'
        )
        assert expected == firedescriptions._build_fuelbeds(self.fire_event)

    def test_build_fuelbeds_2_days_1_fuelbed_same(self):
        self.fire_event.daily_stats_by_fccs_num = {
            datetime.datetime(2014, 5, 31, 0, 0): {
                '49': {
                    'total_area': 200.0, 'description': 'Creosote bush shrubland'
                }
            },
            datetime.datetime(2014, 6, 2, 0, 0): {
                '49': {
                    'total_area': 100.0, 'description': 'Creosote bush shrubland'
                }
            }
        }
        expected = (
            '<div class="section">'
                ' <div class="header">FCCS Fuelbeds</div>'
                ' <div class="list">'
                    '<div class="item">'
                        '<span class="fccs-num">#49</span> -'
                        ' <span class="fccs-area">150 acres</span> -'
                        ' <span class="fccs-desc">Creosote bush shrubland</span>'
                    '</div>'
                '</div>'
            ' </div>'
        )
        assert expected == firedescriptions._build_fuelbeds(self.fire_event)

    def test_build_fuelbeds_2_days_1_fuelbed_different(self):
        self.fire_event.daily_stats_by_fccs_num = {
            datetime.datetime(2014, 5, 31, 0, 0): {
                '49': {
                    'total_area': 200.0, 'description': 'Creosote bush shrubland'
                }
            },
            datetime.datetime(2014, 6, 2, 0, 0): {
                '43': {
                    'total_area': 100.0, 'description': 'trees'
                }
            }
        }
        expected = (
            '<div class="section">'
                ' <div class="header">FCCS Fuelbeds</div>'
                ' <div class="list">'
                    '<div class="item">'
                        '<span class="fccs-num">#49</span> -'
                        ' <span class="fccs-area">100 acres</span> -'
                        ' <span class="fccs-desc">Creosote bush shrubland</span>'
                    '</div>'
                    '<div class="item">'
                        '<span class="fccs-num">#43</span> -'
                        ' <span class="fccs-area">50 acres</span> -'
                        ' <span class="fccs-desc">trees</span>'
                    '</div>'
                '</div>'
            ' </div>'
        )
        assert expected == firedescriptions._build_fuelbeds(self.fire_event)

    def test_build_fuelbeds_1_day_2_fuelbeds(self):
        self.fire_event.daily_stats_by_fccs_num = {
            datetime.datetime(2014, 5, 31, 0, 0): {
                '49': {
                    'total_area': 200.0, 'description': 'Creosote bush shrubland'
                },
                '43': {
                    'total_area': 100.0, 'description': 'trees'
                }
            }
        }
        expected = (
            '<div class="section">'
                ' <div class="header">FCCS Fuelbeds</div>'
                ' <div class="list">'
                    '<div class="item">'
                        '<span class="fccs-num">#49</span> -'
                        ' <span class="fccs-area">200 acres</span> -'
                        ' <span class="fccs-desc">Creosote bush shrubland</span>'
                    '</div>'
                    '<div class="item">'
                        '<span class="fccs-num">#43</span> -'
                        ' <span class="fccs-area">100 acres</span> -'
                        ' <span class="fccs-desc">trees</span>'
                    '</div>'
                '</div>'
            ' </div>'
        )
        assert expected == firedescriptions._build_fuelbeds(self.fire_event)


    def test_build_fuelbeds_2_days_2_fuelbeds_same(self):
        self.fire_event.daily_stats_by_fccs_num = {
            datetime.datetime(2014, 5, 31, 0, 0): {
                '49': {
                    'total_area': 20.0, 'description': 'Creosote bush shrubland'
                },
                '43': {
                    'total_area': 100.0, 'description': 'trees'
                }
            },
            datetime.datetime(2014, 6, 2, 0, 0): {
                '49': {
                    'total_area': 200.0, 'description': 'Creosote bush shrubland'
                },
                '43': {
                    'total_area': 130.0, 'description': 'trees'
                }
            }
        }
        expected = (
            '<div class="section">'
                ' <div class="header">FCCS Fuelbeds</div>'
                ' <div class="list">'
                    '<div class="item">'
                        '<span class="fccs-num">#43</span> -'
                        ' <span class="fccs-area">115 acres</span> -'
                        ' <span class="fccs-desc">trees</span>'
                    '</div>'
                    '<div class="item">'
                        '<span class="fccs-num">#49</span> -'
                        ' <span class="fccs-area">110 acres</span> -'
                        ' <span class="fccs-desc">Creosote bush shrubland</span>'
                    '</div>'
                '</div>'
            ' </div>'
        )
        assert expected == firedescriptions._build_fuelbeds(self.fire_event)

    def test_build_fuelbeds_2_days_2_fuelbeds_different(self):
        self.fire_event.daily_stats_by_fccs_num = {
            datetime.datetime(2014, 5, 31, 0, 0): {
                '49': {
                    'total_area': 200.0, 'description': 'Creosote bush shrubland'
                },
                '43': {
                    'total_area': 100.0, 'description': 'trees'
                }
            },
            datetime.datetime(2014, 6, 2, 0, 0): {
                '43': {
                    'total_area': 50.0, 'description': 'trees foo'  # <-- 'trees' will be used from first day
                },
                '23': {
                    'total_area': 100.0, 'description': 'grasses'
                }
            }
        }
        expected = (
            '<div class="section">'
                ' <div class="header">FCCS Fuelbeds</div>'
                ' <div class="list">'
                    '<div class="item">'
                        '<span class="fccs-num">#49</span> -'
                        ' <span class="fccs-area">100 acres</span> -'
                        ' <span class="fccs-desc">Creosote bush shrubland</span>'
                    '</div>'
                    '<div class="item">'
                        '<span class="fccs-num">#43</span> -'
                        ' <span class="fccs-area">75 acres</span> -'
                        ' <span class="fccs-desc">trees</span>'
                    '</div>'
                    '<div class="item">'
                        '<span class="fccs-num">#23</span> -'
                        ' <span class="fccs-area">50 acres</span> -'
                        ' <span class="fccs-desc">grasses</span>'
                    '</div>'
                '</div>'
            ' </div>'
        )
        assert expected == firedescriptions._build_fuelbeds(self.fire_event)
