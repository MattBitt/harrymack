from pathlib import Path
import os
import glob
from tracemalloc import start
from loguru import logger
import subprocess
from datetime import datetime
import eyed3
from eyed3.core import Date
from typing import List

from pydub import AudioSegment
from pydub_functions import split_on_silence, detect_silence
from models import Source as SourceTbl

# from source import Source

import itertools
import re
from yt_dlp_functions import get_json_info


class Track:
    def __init__(self, data_row, config, source, id3):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.load_data(data_row, config, source, id3)
        self.logger.debug("Track created:  {}", self.filename)
        self.create_folder()
        self.full_path = (
            self.root_directory / self.album_name / Path(self.filename + self.extension)
        )

    def load_data(self, data_row, config, source, id3):
        self.config = config
        self.source = source
        self.start_time = data_row["StartTime"]
        self.end_time = data_row["EndTime"]
        self.root_directory = Path(config[config["enviornment"]]["music_root"])
        self.filename = data_row["Filename"]
        self.extension = ".mp3"
        self.title = data_row["Title"]
        self.album_name = data_row["AlbumName"]
        self.track_number = data_row["TrackNumber"]
        self.beat_name = data_row["BeatName"]
        self.producer = data_row["Producer"]
        self.artist_name = data_row["ArtistName"]
        self.created_date = self.convert_date_time_object(datetime.now())
        self.plex_id = ""
        self.plex_rating = ""
        self.words = ""

    def create_folder(self):
        Path(self.root_directory / self.album_name).mkdir(exist_ok=True)

    def exists(self):
        return self.full_path.exists()

    def extract_from_source(self):
        self.logger.debug("Starting extraction from {}.", self.source.url)
        if not self.exists():
            args = [
                "ffmpeg",
                "-y",
                "-i",
                self.source.filenames["audio"],
                "-ss",
                self.start_time,
                "-to",
                self.end_time,
                "-hide_banner",
                "-loglevel",
                "warning",
                str(self.full_path),
            ]
            self.logger.debug("ffmpeg arguments:  " + " ".join(args))
            ffmpeg = subprocess.run(args)

            if ffmpeg.returncode:
                print("FFMPEG returned: {ffmpeg.returncode}.  Quitting")
                exit(1)
        else:
            self.logger.debug("File {} already exists.  Skipping", self.full_path)

    def write_id3_tags(self) -> None:
        self.logger.debug("Adding ID3 tags.")
        audiofile = eyed3.load(self.full_path)
        if audiofile is not None and audiofile.tag is not None:
            audiofile.tag.artist = self.artist_name
            audiofile.tag.album = self.album_name
            audiofile.tag.album_artist = self.artist_name
            audiofile.tag.title = self.title
            audiofile.tag.track_num = self.track_number
            # with open(img, "rb") as f:
            #    imagedata = f.read()
            #    audiofile.tag.images.set(3, imagedata, "image/jpeg", "")
            # audiofile.tag.recording_date = Date(y`ear)
            audiofile.tag.save()

    def save_to_db(self) -> None:

        self.root_directory = Path(self.config[config["enviornment"]]["music_root"])
        album_name = self.album_name
        artist_name = self.artist_name
        exists = self.exists()
        beat_name = self.beat_name
        created_date = self.created_date
        end_time = self.end_time
        file_path = str(
            self.root_directory / self.album_name / (self.filename + self.extension)
        )
        plex_id = self.plex_id
        plex_rating = self.plex_rating
        producer = self.producer
        start_time = (
            self.start_time
        )  # should these be stored as ms and converted as needed?
        track_number = self.track_number
        track_title = self.title
        words = self.words

        # if self.source.split_by_times():
        #     self.source.extract_single(self.start_time, self.end_time, self.full_path)
        #     pass
        # elif self.source.split_by_silence():
        #     self.source.extract_multiple(self.full_path)
