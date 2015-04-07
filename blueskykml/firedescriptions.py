
from datetime import timedelta
import re

# Constants
OUTPUT_DATE_FORMAT = '%A, %B %d, %Y'

MAX_FCCS_ROWS = 5

def build_fire_location_description(fire_location):
    date_str = fire_location.start_date_time.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
    body = """<h2 class="fire_title">{date}</h2>
    <table class="box">
        <tr>
            <th>Type</th>
            <td>{fire_type}</td>
        </tr>
        {fccs_number}
    </table>
    """.format(date=date_str, fire_type=fire_location.fire_type,
               fccs_number=_build_fccs_number(fire_location.fccs_number), area=_format_value(fire_location.area),
               emissions=_build_emissions(fire_location.emissions))
    return _build_description(body)


def build_fire_event_description(fire_event):
    start_str = fire_event.start_date_time.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
    end_str = fire_event.end_date_time.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
    body = """<h2 class="fire_title">{fire_name}</h2>
    <table class="box">
        <tr>
            <th>Type</th>
            <td>{fire_type}</td>
        </tr>
        <tr>
            <th>Start Date</th>
            <td>{start}</td>
        </tr>
        <tr>
            <th>End Date</th>
            <td>{end}</td>
        </tr>
    </table>
    """.format(fire_name=fire_event.name, fire_type=fire_event.fire_type, start=start_str, end=end_str,
               area=_format_value(fire_event.area), num_locations=fire_event.num_locations,
               emissions=_build_emissions(fire_event.emissions))

    # create "daily" summary boxes
    for date in _daterange(fire_event.start_date_time, fire_event.end_date_time):
        # This assumes that fire_event.[daily_area|daily_num_locations|
        # daily_emissions|daily_stats_by_fccs_num] have the same set of keys
        # (i.e. that each is defined for the same set of dates)
        if (not fire_event.daily_area.has_key(date)):
            continue

        date_str = date.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
        body += """<h2>{date}</h2>
        <table class="box">
            <tr>
                <th>Area Burned</th>
                <td>{day_area} acres</td>
            </tr>
            <tr>
                <th># Modeled Locations</th>
                <td>{day_num_locations}</td>
            </tr>
            {fccs_stats}
            {day_emissions}
        </table>
        """.format(day_area=_format_value(fire_event.daily_area[date]), date=date_str,
                   day_num_locations=fire_event.daily_num_locations[date],
                   day_emissions=_build_emissions(fire_event.daily_emissions[date]),
                   fccs_stats=_build_daily_fccs_stats(fire_event.daily_stats_by_fccs_num[date]))

    return _build_description(body)

def _build_daily_fccs_stats(stats_by_fccs_num):
    s = """
        <tr class="spacer"></tr>
    """.format(count=len(stats_by_fccs_num))
    if len(stats_by_fccs_num) > 0:
        if len(stats_by_fccs_num) > MAX_FCCS_ROWS:
            s += """
                <tr>
                    <th> Top {max_fccs_rows}</th>
                    <td></td>
                </tr>
            """.format(max_fccs_rows=MAX_FCCS_ROWS)
        s += """
            <tr>
                <td colspan="2">
                    <table class="fccs">
                        <tr>
                            <th class="area">Acres</th>
                            <th class="num">FCCS #</th>
                            <th class="desc">Description</th>
                        </tr>
        """
        for fccs_num, fccs_dict in sorted(stats_by_fccs_num.items(), key=lambda e: -e[1]['total_area'])[:MAX_FCCS_ROWS]:
            s += """
                <tr>
                    <td class="area">{area}</td>
                    <td class="num">{fccs_num}</td>
                    <td class="desc">{veg}</td>
                </tr>
            """.format(area=fccs_dict['total_area'], fccs_num=fccs_num, veg=fccs_dict['description'])
        s += """
                    </table>
                </td>
            </tr>

        """

    return _convert_single_line(s)


def _build_description(body):
    description = """<html lang="en">
        <head>
            <meta charset="utf-8"/>
            <style>
                * {{
                    margin: 0;
                }}
                html, body {{
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}
                h2 {{
                    text-align: center;
                    background: #e5eCf9;
                }}
                #summaryData {{
                    font-family: 'Helvetica Neue', Arial, Helvetica, sans-serif;
                    font-size: 12px;
                    width: 350px;
                }}
                #summaryData th{{
                    padding-right: 20px;
                    width: 40%;
                }}
                .fire_title {{
                    background: #ffffff;
                    margin-bottom: 15px;
                }}
                table.fccs {{
                    text-align: left;
                }}
                table.fccs td.area {{
                    width: "20%";
                }}
                table.fccs td.num {{
                    width: "20%";
                }}
                table.fccs td.desc {{
                    width: "60%";
                }}
                .box {{
                    text-align: left;
                    padding: 1.5em;
                    padding-top: 1em;
                    margin-bottom: 1.5em;
                    background: #e5eCf9;
                    width: 100%;
                }}
                .spacer {{
                    height: 15px;
                }}
            </style>
        </head>
        <body>
            <div id="summaryData">
                {body}
            </div>
        </body>
    </html>
    """.format(body=body)
    return _convert_single_line(description)

def _build_fccs_number(fccs_number):
    fccs_number_str = ''
    if fccs_number:
        fccs_number_str += """
        <tr>
            <th>FCCS Number</th>
            <td>{fccs_number}</td>
        </tr>""".format(fccs_number=fccs_number)
    return fccs_number_str

def _build_emissions(emissions):
    emission_str = ''
    if emissions:
        emission_str += '<tr class="spacer"></tr>'
        for param in emissions:
            emission_str += """
            <tr>
                <th>{param}</th>
                <td>{value} tons</td>
            </tr>""".format(param=param.upper(), value=_format_value(emissions[param]))
    return emission_str


def _format_value(value):
    """Adds commas as thousands separator. So a value of 12345.789 would become '12,345.789'."""
    return "{:,}".format(value)


def _daterange(start_date, end_date):
    for n in reversed(range(int((end_date - start_date).days)+1)):
        yield start_date + timedelta(n)


def _convert_single_line(description):
    """Reduce description text to single line to help reduce kml file size."""
    description = description.replace('\n', '')  # Remove new line characters
    description = re.sub(' +', ' ', description)  # Reduce multiple spaces into a single space
    return description
