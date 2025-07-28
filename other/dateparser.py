import pendulum
from datetime import datetime

async def parse_datetime(input_str: str) -> datetime | None:
    try:
        dt = pendulum.parse(input_str, strict=False)
        if isinstance(dt, pendulum.DateTime):
            return dt
        return None
    except ValueError:
        return None