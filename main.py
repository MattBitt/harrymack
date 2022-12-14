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
import json
from flask import Flask

# from unused.WordGrid import resize_image, TextArea, WordGrid, Word, prepare_image
from plex_functions import plex_update_library, connect_to_server, add_mood

from source import SourceImporter, Source
from track import TrackImporter, Track

from models import database_setup


from models import Track as TrackTbl
from models import Source as SourceTbl
from models import Tag, Word

# regular comment
# * important comment is highlighted
# ! alert!!!
# ? for questions
# TODO: this is how to add TODOs

# this is a global dict to keep track of any stats throughout the program
# such as: files that don't exist, urls on channel not in db...
stats = {}


class EmptyListError(ValueError):
    """
    Raised to signal the fact that a list is empty.
    """


def load_track_data(path):
    """_summary_

    Args:
        path (_type_): _description_

    Returns:
        _type_: _description_
    """
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


def check_for_env_variables():
    required_env_variables = [
        "ENVIORNMENT",
        "LOGLEVEL",
        "PLEXTOKEN",
        "TAUTULLITOKEN",
        "HOME",
        "FLASK_APP",
        "FLASK_DEBUG",
    ]
    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise KeyError(env_var)

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
    if config["log_level"] == "DEBUG":
        log_format = (
            "<white>{time: YYYY-MM-DD HH:mm:ss.SSS} | </white>"
            "<lvl>[{level: <8}]"
            "</lvl><yellow>{name}:<c>{extra[classname]}</c>:{function}:{line}</yellow> - "
            "<lvl>{message}</lvl>"
        )
        logger.configure(extra={"classname": "None"})
        logger.add(
            sys.stderr, format=log_format, level=config["log_level"], colorize=True
        )
    else:
        log_format = "{time: YYYY-MM-DD HH:mm:ss} | [{level: <8}] | {message}"
        logger.add(sys.stderr, format=log_format, level=config["log_level"])

    # TODO: Setup a separate logging format if not in debug.  get rid of classes and line numbers...

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


def get_playlist_videos(playlist):
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
        playlist["url"],
    ]
    yt_dl = subprocess.run(args1 + args2 + args3)
    with open(tmp_file) as f:
        lines = f.read().splitlines()
    os.remove(tmp_file)
    if yt_dl.returncode:
        logger.error("There was an error processing {}", yt_dl.returncode)
        return []
    else:
        logger.success(
            "The URLs for playlist {} were downloaded.", playlist["video_type"]
        )
        return lines


def import_source_options(options):
    default_options = {"split_by_silence": False, "separate_album_per_episode": False}
    option_return = {}
    assert "video_type" in options.keys()
    option_return = options
    for k in default_options.keys():
        if k in options.keys():
            option_return[k] = options[k]
        else:
            option_return[k] = default_options[k]
    return option_return


def add_video_to_db(url, options, config):
    query = SourceTbl.select().where(SourceTbl.url == url)
    if not query.exists():
        # logger.debug("Video doesn't exist in DB.  Need to create")
        try:
            source = SourceImporter(url, options, config)
            source.save_to_db()
        except FileNotFoundError:
            logger.warning("Not able to create object {}", url)
    else:
        logger.debug("Video {} already exists", list(query)[0].video_title)


def import_channels(config):
    for channel in config["channels"]:
        if "playlists" in channel.keys():
            for playlist in channel["playlists"]:
                urls = get_playlist_videos(playlist)
                for url in urls:
                    options = import_source_options(playlist)
                    add_video_to_db(url, options, config)


def import_videos(config):
    for video in config["videos"]:
        options = import_source_options(video)
        add_video_to_db(video["url"], options, config)


def import_sources_to_db(config):
    import_channels(config)
    import_videos(config)


def import_tracks_to_db(config):
    data_rows = load_track_data(config["import_csv"])
    missing_sources = set()
    for data_row in data_rows:
        if data_row["URL"] == "":
            continue  # make sure a source url exists to create a track entry in the db
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

    if len(missing_sources) > 0:
        logger.info("Missing sources:")

        for ms in missing_sources:
            logger.info(ms)


def create_track_mp3(track, config):
    track_object = Track(track, config)
    try:
        track_object.extract_from_source()
        track_object.write_id3_tags()
        track.exists = True
        track.save()
        return track
    except IndexError:
        logger.error("Error creating track {}", track.track_title)


def import_sources_and_tracks(config):
    if not config["import_during_testing"] and config["enviornment"] == "env_dev":
        return False

    logger.info("Importing sources to DB")
    import_sources_to_db(config)
    # This may no longer be needed once the tracks from the CSV are created.
    logger.info("Importing manually specified tracks to DB")
    import_tracks_to_db(config)
    check_for_missing_videos()


def download_source_files():
    sources = SourceTbl
    logger.info("Downloading source files")
    for source in sources.do_not_exist():
        source_object = Source(source, config)
        source_object.download_files()


def create_missing_tracks():
    tracks = TrackTbl
    logger.info(
        "Creating tracks that exist in the db but do not have an mp3 file created"
    )
    for track in tracks.do_not_exist():
        logger.debug("Need to create {} mp3", track.track_title)
        create_track_mp3(track, config)


def verify_files_exist():
    global stats
    stats["in_db_but_do_not_exist"] = []  # type: ignore

    sources = SourceTbl
    logger.info("Downloading source files")
    total_counter = 0
    exist_counter = 0
    does_not_exist_counter = 0
    for source in sources.all():
        files = [
            source.audio_file,
            source.description_file,
            source.image_file,
            source.video_file,
        ]
        for file in files:
            if not file or file == "None":
                continue
            f = Path(file)
            total_counter += 1
            if not f.exists():
                does_not_exist_counter += 1
                stats["in_db_but_do_not_exist"].append(file)
                # logger.error("File {} does not exist", str(f))
            else:
                exist_counter += 1
                # logger.success("File {} does exist", str(f))
    logger.info("Total files checked: {}", str(total_counter))
    logger.info("Total files Exist: {}", str(exist_counter))
    logger.info("Total files Do Not exist: {}", str(does_not_exist_counter))


def get_video_list_from_channel(url):
    global stats

    tmp_file = "channel_videos.txt"

    # yt-dlp  "%(title)s" "URL" > Videos.txt
    args1 = ["yt-dlp"]
    args2 = []
    if not config["log_level"] == "DEBUG":
        args2 = ["--no-warnings", "--quiet"]
    args3 = [
        "--flat-playlist",
        "--print-to-file",
        "%(url)s",
        tmp_file,
        url["url"],
    ]
    yt_dl = subprocess.run(args1 + args2 + args3)
    source = SourceTbl
    with open(tmp_file) as f:
        lines = f.read().splitlines()
    os.remove(tmp_file)
    if yt_dl.returncode:
        logger.error("There was an error processing {}", yt_dl.returncode)
        return []
    else:
        logger.success("The URLs for channel {} were downloaded.", url["channel_name"])
    url_list = []
    # ! Need to stop writing these to a file since I'm using the "stats" to track it
    with open("missing_urls.txt", "w") as channel:
        channel_urls = lines
        for ch_url in channel_urls:
            if not ch_url == "NA":
                result = source.select().where(SourceTbl.url == ch_url)

                if not result:
                    url_list.append({"url": ch_url})
                    channel.writelines(ch_url)
                    channel.write("\n")
    os.remove("missing_urls.txt")
    stats["on_channel_but_not_in_db " + url["url"]] = url_list  # type: ignore
    return lines


def write_stats_to_file(stats_file):
    with open(stats_file, "w") as write_file:
        json.dump(stats, write_file, indent=4, sort_keys=False)


def check_for_files_not_in_db():
    global stats
    sources = SourceTbl

    rootdir = Path(config[config["enviornment"]]["download_directory"])
    # For absolute paths instead of relative the current dir
    file_list = [str(f) for f in rootdir.resolve().glob("**/*") if f.is_file()]
    # print(file_list)
    stats["files_exist_but_not_in_db"] = []
    for file in file_list:
        if ".mp3" in file:
            query = sources.select().where(sources.audio_file == file)
        elif "description" in file:
            query = sources.select().where(sources.description_file == file)
        elif "webp" in file or "jpg" in file:
            query = sources.select().where(sources.image_file == file)
        elif ".mp4" in file:
            query = sources.select().where(sources.video_file == file)
        else:
            query = None
            logger.info("{} not found above", file)

        if not query:
            stats["files_exist_but_not_in_db"].append(file)


def check_for_missing_videos():
    # need to add this as well once yt-dlp is fixed:
    # not sure where it should be exactly?
    # ("https://www.youtube.com/@HarryMack/streams")
    channels = config["channels"]
    for channel in channels:
        get_video_list_from_channel(channel)


if __name__ == "__main__":
    VERSION = "2.1.0"
    CONFIG_PATH = "./config.yaml"
    STATS_PATH = "./logs/stats.txt"
    check_for_env_variables()
    config = load_config(CONFIG_PATH)
    logger = setup_logging()
    logger.success("Starting Program ({})", VERSION)
    database_setup()
    import_sources_and_tracks(config)
    check_for_files_not_in_db()
    verify_files_exist()
    download_source_files()
    create_missing_tracks()
    plex = connect_to_server()
    plex_update_library(plex, "Harry Mack Tracks")
    plex_update_library(plex, "Harry Mack Sources")

    write_stats_to_file(STATS_PATH)

    logger.success("Program finished successfully")
    logger.success("Starting webserver")
