from datetime import datetime, date
from loguru import logger
from pathlib import Path


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


def create_folder(path: Path):
    # need to implement.  take either str or a pathlib object
    # match path:
    #     case str(path):
    #         p = Path(path)
    #         p.mkdir(parents=True, exist_ok=True)
    #     case Path(path):
    path.mkdir(parents=True, exist_ok=True)


def get_year(dt):
    return str(dt.year)
