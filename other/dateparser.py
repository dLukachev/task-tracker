import dateparser
from datetime import datetime

DEFAULT_TZ = 'Europe/Moscow'

async def parse_datetime(input_str: str) -> datetime | None:
    dt = dateparser.parse(
        input_str,
        languages=['ru'],
        settings={
            'TIMEZONE': DEFAULT_TZ,
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'future',
        }
    )
    return dt