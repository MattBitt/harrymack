from datetime import datetime
from loguru import logger


def convert_date_string(dt: str, format: str) -> str:
    match format:
        case "YYYY-MM-DD":
            if len(dt) == 8:
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
