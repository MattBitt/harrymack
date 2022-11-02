# from ast import AsyncFunctionDef

import subprocess
import csv
import os
import eyed3

import shutil
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import glob
import sys

from loguru import logger
from pyaml_env import parse_config
from pathlib import Path
import yaml
import random
from WordGrid import resize_image, TextArea, WordGrid, Word, prepare_image
from plex_functions import plex_update_library, connect_to_server, add_mood

from source import Source
from track import TrackImporter, Track

from models import database_setup


from models import Track as TrackTbl
from models import Source as SourceTbl


# TODO: Need to add logic to tell plex to update library after scan.  Music libraries excluded from auto updates in plex

# regular comment
# * important comment is highlighted
# ! alert!!!
# ? for questions
# TODO: this is how to add TODOs


class EmptyListError(ValueError):
    """
    Raised to signal the fact that a list is empty.
    """


def load_track_data(path):
    try:
        track_info_list = import_from_csv(path)

    except FileNotFoundError:
        logger.error(
            "No CSV file found.  Please check the path and try again. path={}", path
        )
        raise
    except EmptyListError:
        logger.error(
            "No records found in CSV file.  Please check the import and retry. path={}",
            path,
        )
        raise
    except KeyError:
        logger.error("There is a problem with the CSV file.  path={}", path)
        raise
    if not track_info_list:
        logger.error("No data rows were read from {}", config["import_csv"])
        exit(1)
    logger.debug(
        "Music root directory = {}", config[config["enviornment"]]["music_root"]
    )
    logger.debug(
        "Downloads directory = {}", config[config["enviornment"]]["download_directory"]
    )
    return track_info_list


def import_from_csv(csv_name):
    if not os.path.exists(csv_name):
        raise FileNotFoundError(f"File {csv_name} not found")

    with open(csv_name, "r") as f:
        csv_reader = csv.DictReader(f)
        track_info = list(csv_reader)
    # TODO: check for empty lines before returning
    # * CSV file exists, but there aren't any records
    if track_info == []:
        raise EmptyListError(f"File {csv_name} does not contain any records")

    # ? need to create this list from the csv itself?  that way, to add (or delete) a column,
    # ? I can just do it in excel and it will carry over here
    # ? but, that would eliminate the following check.  since the csv, by definition,
    # ? would contain all of the headings that it should
    fields = [
        "WholeName",
        "ArtistName",
        "AlbumName",
        "TrackNumber",
        "Title",
        "StartTime",
        "EndTime",
        "URL",
        "BeatName",
        "Producer",
    ]
    for f in fields:
        if f not in track_info[0].keys():
            logger.error("{} does not exist in csv.  Please export and try again.", f)
            raise KeyError(f"{f} does not exist in csv.  Please export and try again.")
    return track_info


def load_config(config_path):
    # ? need to validate the settings here?
    # ? need to check paths as welli
    if not os.path.exists(config_path):
        logger.info(
            "Config file {} does not exist.  Creating from default values.", config_path
        )
        create_yaml_from_dict(default_config(), config_path)
        remove_single_quotes(
            config_path
        )  # * need to do this since the !ENV lines in config get quotes added to them
    config = parse_config(config_path)
    music_root = config[config["enviornment"]]["music_root"]
    source_directory = config[config["enviornment"]]["download_directory"]
    err_mess = ""
    if not music_root or not os.path.exists(music_root):
        err_mess = f"No music root directory found.  Please check the paths and try again. mr={music_root}"
    elif not source_directory or not os.path.exists(source_directory):
        err_mess = f"No source directory found.  Please check the paths and try again. sd={source_directory}"

    if err_mess:
        logger.error(err_mess)
        raise KeyError(err_mess)

    return config


def default_config():
    return {
        "app_name": "harrymack",
        "enviornment": "!ENV ${ENVIORNMENT}",
        "import_csv": "./HarryMackClips.csv",
        "log_level": "!ENV ${LOGLEVEL}",
        "overwrite_destination": False,
        "overwrite_download": False,
        "env_dev": {
            "download_directory": "./media/downloads/",
            "music_root": "./media/musicroot/",
        },
        "env_prod": {"download_directory": "/downloads/", "music_root": "/music/"},
        "fonts": {
            "font_name": "./media/fonts/courbd.ttf",
            "font_sample": False,
            "init_font_size": 48,
            "max_font_size": 48,
        },
        "plex": {"baseurl": "!ENV ${PLEXURL}", "token": "!ENV ${PLEXTOKEN}"},
    }


def setup_logging():
    logger.remove(0)
    # adds logging to stderr
    log_format = (
        "<white>{time: YYYY-MM-DD HH:mm:ss.SSS} | </white>"
        "<lvl>[{level: <8}]"
        "</lvl><yellow>{name}:<c>{extra[classname]}</c>:{function}:{line}</yellow> - "
        "<lvl>{message}</lvl>"
    )
    # TODO: Setup a separate logging format if not in debug.  get rid of classes and line numbers...
    logger.configure(extra={"classname": "None"})
    logger.add(sys.stderr, format=log_format, level=config["log_level"], colorize=True)

    # ! don't log to file on production.  run in docker so it should handle the log cleanup
    if config["log_level"] == "DEBUG" and not config["enviornment"] == "env_prod":
        log_path = "./logs/"
        log_file = "harrymack.log"
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        logger.add(
            os.path.join(log_path, log_file),
            format=log_format,
            level=config["log_level"],
            backtrace=True,
            diagnose=True,
        )

    return logger


def process_with_ffmpeg(track, overwrite=False):
    if track.destination_exists() and not overwrite:
        # * destination path exists and we don't want to overwrite
        logger.debug("File exists.  OVERWRITE=False.  Skipping processing.")
        return False
    elif track.destination_exists() and overwrite:
        # * destination path exists but we do want to overwrite
        logger.debug("File exists.  OVERWRITE=True.  Need to process.")
        return True
    else:
        logger.debug("File does not exist.  Need to process.")
        return True


def download_source_file(track, overwrite=False):
    if track.source.exists() and not overwrite:
        # * destination path exists and we don't want to overwrite
        logger.debug("File exists.  OVERWRITE=False.  Skipping download.")
        return False
    elif track.source.exists() and overwrite:
        # * destination path exists but we do want to overwrite
        logger.debug("File exists.  OVERWRITE=True.  Need to download.")
        return True
    else:
        logger.debug("File does not exist.  Need to download.")
        return True


def create_yaml_from_dict(default_config, config_path):
    with open(config_path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
    remove_single_quotes(config_path)


def remove_single_quotes(config_path):
    with open(config_path, "r") as f:
        data = f.read()
        data = data.replace("'", "")
    with open(config_path, "w") as f:
        f.write(data)


def keep_n_lines_of_file(n, file):
    n = n + 1  # * keep n # of records.  add 1 since there is a heading row first
    with open(file, "r+") as f:
        data = f.readlines()
        if len(data) > n:
            data = data[0:n]
            f.seek(0)
            f.writelines(data)
            f.truncate()

    return file


def remove_random_column_from_csv(csv_path, path):
    col_to_remove = [random.randint(0, 10)]
    row_count = 0  # * Current amount of rows processed

    with open(csv_path, "r") as source:
        reader = csv.reader(source)
        with open(Path.joinpath(path, "malformed.csv"), "w", newline="") as result:
            writer = csv.writer(result)
            for row in reader:
                row_count += 1
                for col_index in col_to_remove:
                    del row[col_index]
                writer.writerow(row)
    return Path.joinpath(path, "malformed.csv")


def get_playlist_videos(url):
    tmp_file = "playlist_videos.txt"
    args1 = ["yt-dlp"]
    args2 = []
    if not config["log_level"] == "DEBUG":
        args2 = ["--no-warnings", "--quiet"]
    args3 = [
        "--flat-playlist",
        "-i",
        "--print-to-file",
        "url",
        tmp_file,
        url,
    ]
    yt_dl = subprocess.run(args1 + args2 + args3)
    with open(tmp_file) as f:
        lines = f.read().splitlines()
    os.remove(tmp_file)
    if yt_dl.returncode:
        logger.error("There was an error processing {}", yt_dl.returncode)
        return []
    else:
        logger.success("The file was successfully downloaded:  {}", url)
        return lines


def youtube_download(track, config):
    # * output name should not have ".ext"
    f = os.path.join(track.source.path, track.source.base_name + ".mp3")
    args1 = ["yt-dlp"]
    args2 = []
    if not config["log_level"] == "DEBUG":
        args2 = ["--no-warnings", "--quiet"]
    args3 = [
        "--extract-audio",
        "--write-description",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "-o",
        f[:-4] + " (%(upload_date)s).mp3",
        "--write-thumbnail",
        track.url,
    ]
    logger.info("Starting download of {}", track.url)
    yt_dl = subprocess.run(args1 + args2 + args3)
    if yt_dl.returncode:
        logger.error("There was an error processing {}", yt_dl.returncode)
        return False
    else:
        logger.success("The file was successfully downloaded:  {}", track.url)
        return True


# TODO: Need to do a first pass on refactor/delete function
def extract_audio(source, destination, start_time, end_time):
    if not os.path.exists(destination):
        ffmpeg = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                source,
                "-ss",
                start_time,
                "-to",
                end_time,
                "-hide_banner",
                "-loglevel",
                "warning",
                destination,
            ]
        )

        if ffmpeg.returncode:
            print("FFMPEG returned: {ffmpeg.returncode}.  Quitting")
            exit()
    else:
        print(f"File {destination} already exists")


# TODO: Need to do a first pass on refactor/delete function
# def update_id3(mp3file, artist, album, title, track_num, year, img):

#     audiofile = eyed3.load(mp3file)
#     audiofile.tag.artist = artist
#     audiofile.tag.album = album
#     audiofile.tag.album_artist = artist
#     audiofile.tag.title = title
#     audiofile.tag.track_num = track_num
#     with open(img, "rb") as f:
#         imagedata = f.read()
#         audiofile.tag.images.set(3, imagedata, "image/jpeg", "")
#     audiofile.tag.recording_date = Date(year)
#     audiofile.tag.save()


# TODO: Need to do a first pass on refactor/delete function
def create_album_folder(path):
    if not os.path.exists(path):
        os.umask(0)
        os.makedirs(path, mode=0o777)


# TODO: Need to do a first pass on refactor/delete function
def move_file(source, destination, overwrite):
    if os.path.exists(destination):
        if overwrite:
            os.remove(destination)
        else:
            print("Could not overwrite destination file {destination}")
            return False
    shutil.move(source, destination)
    return True


# TODO: Need to do a first pass on refactor/delete function
def copy_file(source, destination, overwrite=False):
    if os.path.exists(destination):
        if overwrite:
            os.remove(destination)
        else:
            print("Could not overwrite destination file {destination}")
            return False
    shutil.copy(source, destination)
    return True


# TODO: Need to do a first pass on refactor/delete function
def parse_files(dir, base_filename):
    if dir[-1] != "/":
        dir = dir + "/"

    types = ["audio", "image", "description"]
    files = {}
    files["audio"] = ""
    files["image"] = ""
    files["description"] = ""
    # * these are the patterns downloaded from youtube.
    patterns = {}
    patterns["audio"] = [base_filename + "*.mp3"]
    patterns["image"] = [
        base_filename + "*.mp3.webp",
        base_filename + "*.webp",
        base_filename + "*.jpg",
    ]
    patterns["description"] = [base_filename + "*.mp3.description"]
    for t in types:
        for pattern in patterns[t]:
            file_list = glob.glob(dir + pattern)
            if (
                len(file_list) == 1
            ):  # ? This always chooses the first file returned.  Need to do any other testing here?
                files[t] = file_list[0]
            elif len(file_list) > 1:
                # print(f"More than 1 file found matching the {pattern}\n{file_list}")
                pass
            else:
                # print(f"No matching files found:  {pattern}\n{file_list}")
                pass
    year = get_year(files["audio"])
    return files, year


# TODO: Need to do a first pass on refactor/delete function
def convert_to_jpg(source, destination):
    img = Image.open(source)
    img.save(destination, optimize=True)
    return destination


# TODO: Need to do a first pass on refactor/delete function
def get_fonts(dir):
    dir = add_slash(dir)
    return os.listdir(dir)
    # for entry in os.scandir(dir):
    #    if entry.name.endswith('.ttf'):
    #        yield dir + entry.name


# TODO: Need to do a first pass on refactor/delete function
def add_slash(path):
    if path[-1] != "/":
        path = path + "/"
    return path


# TODO: Need to do a first pass on refactor/delete function
def get_year(file):
    if file:
        start = file.find("(")
        return int(file[start + 1 : start + 5])
    else:
        print("No file given.  Please try again")
        return False


# TODO: Need to do a first pass on refactor/delete function
def get_path(path_list):
    # * this function returns whichever folder exists.  path_list should be in preference order
    for p in path_list:
        if os.path.exists(p):
            p = add_slash(p)
            return p
    print(f"No paths found {path_list}")
    return False


def import_sources_to_db(config):
    for channel in config["channels"]:
        if "playlists" in channel.keys():
            for playlist in channel["playlists"]:
                urls = get_playlist_videos(playlist["url"])
                for url in urls:
                    query = SourceTbl.select().where(SourceTbl.url == url)
                    if not query.exists():
                        logger.debug("Video doesn't exist in DB.  Need to create")
                        try:
                            source = Source(url, playlist, config)
                        except FileNotFoundError:
                            logger.warning("Not able to create object {}", url)
                            continue
                        source.save_to_db()
                    else:
                        logger.debug("Video {} already exits", url)


def import_tracks_to_db(config, sources):
    data_rows = load_track_data(config["import_csv"])
    album = None
    previous_album = None
    new_album = False
    new_albums = []
    moods = []
    # * Loop through each clip in the CSV
    missing_sources = set()
    for data_row in data_rows:

        album_image = ""
        # source = Source(data_row, config)
        # if not source.exists(
        #     "audio"
        # ):  # ? would i ever want to overwrite the downloads?
        #     source.download_files()
        if data_row["URL"] == "":
            continue
        try:
            track = TrackImporter(data_row, config)
        except FileNotFoundError:
            logger.debug("Not able to create object {}", data_row["URL"])
            missing_sources.add(data_row["AlbumName"] + " : " + data_row["URL"])
            continue
        query = TrackTbl.select().where(TrackTbl.track_title == track.track_title)
        if query.exists():
            # logger.debug("Track {} already exists in DB", track.file_path)
            pass
        else:
            logger.debug("Track {} is new.  Adding to DB", track.track_title)
            track.save_to_db()
        # track.add_source(source)
        # if not track.exists() or (track.exists() and config["overwrite_destination"]):
        #    track.extract_from_source()
        #    track.write_id3_tags()
    logger.info("Missing sources:")
    for ms in missing_sources:
        logger.info(ms)


# def split_by_silence():
#     if source.video_type in VIDEOS_TO_SPLIT_BY_SILENCE:
#         orig_title = id3.title
#         orig_filename = data_row["Filename"] + " "
#         track_times = source.find_tracks()

#         for tt in track_times:
#             data_row["StartTime"], data_row["EndTime"] = tt
#             time_string = f"{tt[0]}-{tt[1]}".replace(":", "")
#             id3.track_number = str((int(id3.track_number) + 1))
#             id3.title = orig_title + " " + id3.track_number

#             data_row["Filename"] = (
#                 orig_filename + id3.track_number + " (" + time_string + ")"
#             )
#             track = TrackImporter(data_row, config, source, id3)
#             if not track.exists() or (
#                 track.exists() and config["overwrite_destination"]
#             ):
#                 track.extract_from_source()
#                 track.write_id3_tags()


# ! THERE IS NO TRACK!.  There should be a source object that transforms into a destination object along side  an ID3 object as well.  Abstract out the Track to those two classes
# ! that way, both the source and destination objects can use the ID3 object.
# ? would this be the path or the actual file?  any use in capturing the actual file?
# ! destination.audio = source.audio.extract(start_time, end_time)
# ! something like:
# ! source, destination, ID3 = load_track_data

if __name__ == "__main__":
    VERSION = "2.0.0"
    CONFIG_PATH = "./config.yaml"

    config = load_config(CONFIG_PATH)
    logger = setup_logging()
    logger.success("Starting Program ({})", VERSION)
    database_setup()

    import_sources_to_db(config)
    sources = SourceTbl

    import_tracks_to_db(config, sources)
    tracks = TrackTbl

    for track in tracks.do_not_exist():
        logger.debug("Need to create {} mp3", track.track_title)

        track_object = Track(track, config)
        track_object.extract_from_source()
        track_object.write_id3_tags()
        track.exists = True
        track.save()
