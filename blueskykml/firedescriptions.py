
from datetime import timedelta
import re

# Constants
OUTPUT_DATE_FORMAT = '%A, %B %d, %Y'

MAX_FCCS_ROWS = 5

def build_fire_location_description(fire_location):
    date_str = fire_location.start_date_time.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
    body = """
        <h2 class="fire_title">
            {date}
        </h2>
        <div class="section">
            Type: {fire_type}
        </div>
    """.format(date=date_str, fire_type=fire_location.fire_type)

    if fire_location.fccs_number:
        body += '<div class="section">FCCS #{fccs_number}</div>'.format(
            fccs_number=fire_location.fccs_number)

    return _build_description(body)


def build_fire_event_description(fire_event):
    start_str = fire_event.start_date_time.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
    end_str = fire_event.end_date_time.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
    body = """
        <h2 class="fire_title">
            {fire_name}
        </h2>
        <div class="section">
            <span class="header">Type</span>: {fire_type}
        </div>
    """.format(fire_name=fire_event.name, fire_type=fire_event.fire_type)

    # create "daily" summary boxes
    growth = []
    for date in _daterange(fire_event.start_date_time, fire_event.end_date_time):
        # This assumes that fire_event.[daily_area|daily_num_locations|
        # daily_emissions|daily_stats_by_fccs_num] have the same set of keys
        # (i.e. that each is defined for the same set of dates)
        if (not fire_event.daily_area.has_key(date)):
            continue

        date_str = date.strftime(OUTPUT_DATE_FORMAT).replace(' 0', ' ')
        growth.append("""
            <div class="item">
                {date}: {day_area} (in {day_num_locations} location{plural_s})
            </div>
        """.format(
            date=date_str, day_area=_format_value(fire_event.daily_area[date]),
            day_num_locations=fire_event.daily_num_locations[date],
            plural_s='s' if fire_event.daily_num_locations[date] > 1 else ''))
    if growth:
        body += """
            <div class="section">
                <div class="header">Projected Growth</div>
                <div class="list">{growth}</div>
            </div>
        """.format(growth=_convert_single_line(''.join(growth)))

    stats_by_fccs_num = fire_event.daily_stats_by_fccs_num[date]
    if len(stats_by_fccs_num) > 0:
        fuelbeds = []
        sorted_stats = sorted(stats_by_fccs_num.items(),
            key=lambda e: -e[1]['total_area'])[:MAX_FCCS_ROWS]
        for fccs_num, fccs_dict in sorted_stats:
            fuelbeds.append(
                '<div class="item">'
                '<span class="fccs-num">#{fccs_num}</span> - '
                '<span class="fccs-area">{area} acres</span> - '
                '<span class="fccs-desc">{desc}</span>'
                '</div>'.format(
                area=fccs_dict['total_area'], fccs_num=fccs_num,
                desc=fccs_dict['description']))
        body += """
            <div class="section">
                <div class="header">FCCS Fuelbeds</div>
                <div class="list">{fuelbeds}</div>
            </div>
        """.format(fuelbeds=_convert_single_line(''.join(fuelbeds)))

    return _build_description(body)


def _build_description(body):
    description = """<html lang="en">
        <head>
            <meta charset="utf-8"/>
            <style>
                * {{
                    text-align: left;
                    background: #ffffff;
                    margin: 0;
                }}
                html, body {{
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}
                .summary {{
                    font-family: 'Helvetica Neue', Arial, Helvetica, sans-serif;
                    font-size: 12px;
                    width: 350px;
                    padding-bottom: 15px;
                }}
                .summary .fire_title {{
                    margin-bottom: 5px;
                }}
                .summary .section {{
                    margin: 0 0 10px 10px;
                }}
                .summary .section .header {{
                    font-weight: bold;
                }}
                .summary .section .list {{
                    margin-left: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="summary">
                {body}
            </div>
        </body>
    </html>
    """.format(body=body)
    return _convert_single_line(description)

def _format_value(value):
    """Adds commas as thousands separator. So a value of 12345.789 would become '12,345.789'."""
    return "{:,}".format(value)

def _daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(n)

def _convert_single_line(description):
    """Reduce description text to single line to help reduce kml file size."""
    description = description.replace('\n', '')  # Remove new line characters
    description = re.sub(' +', ' ', description)  # Reduce multiple spaces into a single space
    return description
