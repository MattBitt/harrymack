from datetime import datetime, date
from loguru import logger


def convert_date_string(dt: str, format: str) -> str:
    match format:
        case "YYYY-MM-DD":
            if len(dt) == 10:
                return dt
            elif len(dt) == 8:
                converted = dt[:4] + "-" + dt[4:6] + "-" + dt[6:]
                return converted
            else:
                logger.error("Source date not 8 characters (YYYYMMDD) {}", dt)
                raise KeyError()
        case _:
            logger.error("Date format not recognized: {}}", format)
            raise KeyError()


def convert_date_time_object(dt: datetime):
    return dt.strftime("%Y-%m-%d")


def ms_to_hhmmss(millis):
    millis = int(millis)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24
    hours = int(hours)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
