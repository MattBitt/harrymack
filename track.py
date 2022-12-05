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
from models import Track as TrackTbl
from models import Tag, Word, TrackTag, TrackWord


# from source import Source

import itertools
import re
from yt_dlp_functions import get_json_info
from utils import convert_date_string, convert_date_time_object


class TrackImporter:
    def __init__(self, data_row, config):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.load_data(data_row, config)
        # self.logger.debug("Track created:  {}", self.filename)
        # self.create_folder()

    def load_data(self, data_row, config):
        self.config = config
        # query = SourceTbl.select().where(SourceTbl.url == data_row["URL"])

        self.start_time = data_row["StartTime"]
        self.end_time = data_row["EndTime"]
        self.root_directory = Path(config[config["enviornment"]]["music_root"])
        self.filename = data_row["Filename"]
        self.extension = ".mp3"
        self.filename = data_row["Title"]

        self.url = data_row["URL"]
        self.beat_name = data_row["BeatName"]
        self.producer = data_row["Producer"]
        self.artist_name = data_row["ArtistName"]
        self.track_title = data_row["Title"]
        self.created_date = convert_date_time_object(datetime.now())
        self.plex_id = ""
        self.plex_rating = 0
        self.words = ""

        query = SourceTbl.select().where(SourceTbl.url == self.url)
        if query.exists():
            # self.logger.debug("Source {} exists in DB", self.url)
            self.source = query.first().id
            self.album_name = query.first().album_name
            new_query = TrackTbl.select().where(TrackTbl.album_name == self.album_name)
            self.track_number = len(new_query) + 1
            if self.track_title == "":
                self.track_title = self.album_name + " Part " + str(self.track_number)
            if self.filename == "":
                self.filename = str(self.track_number) + " - " + self.track_title

        else:
            # self.logger.debug("Source {} does not exist", self.url)
            raise FileNotFoundError
        self.file_path = (
            self.root_directory / self.album_name / (self.filename + self.extension)
        )

    #     return self.file_path.exists()

    def save_to_db(self) -> None:

        self.root_directory = Path(
            self.config[self.config["enviornment"]]["music_root"]
        )
        track = TrackTbl.create(
            artist_name=self.artist_name,
            album_name=self.album_name,
            exists=False,
            beat_name=self.beat_name,
            created_date=self.created_date,
            end_time=self.end_time,
            file_path=self.file_path,
            plex_id=self.plex_id,
            plex_rating=self.plex_rating,
            producer=self.producer,
            source_id=self.source,
            start_time=(
                self.start_time
            ),  # should these be stored as ms and converted as needed?
            track_number=self.track_number,
            track_title=self.track_title,
            words=self.words,
        )
        # if self.source.split_by_times():
        #     self.source.extract_single(self.start_time, self.end_time, self.full_path)
        #     pass
        # elif self.source.split_by_silence():
        #     self.source.extract_multiple(self.full_path)


class Track:
    def __init__(self, track, config):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.track_row = track
        self.config = config
        self.root_directory = Path(self.config[config["enviornment"]]["music_root"])
        self.create_folder()

    def create_folder(self):
        album_folder = self.root_directory / self.track_row.source.album_name
        Path(album_folder).mkdir(exist_ok=True)

    def extract_from_source(self):
        self.logger.debug("Starting extraction from {}.", self.track_row.source.url)
        if str(self.track_row.start_time) == str(self.track_row.end_time):
            logger.error(
                "Start time and end time are the the same for track: {}",
                self.track_row.source.audio_file,
            )
            raise IndexError
        self.create_folder()
        if not self.exists():
            args = [
                "ffmpeg",
                "-y",
                "-i",
                self.track_row.source.audio_file,
                "-ss",
                str(self.track_row.start_time),
                "-to",
                str(self.track_row.end_time),
                "-hide_banner",
                "-loglevel",
                "warning",
                str(self.track_row.file_path),
            ]
            self.logger.debug("ffmpeg arguments:  " + " ".join(args))
            ffmpeg = subprocess.run(args)

            if ffmpeg.returncode:
                print("FFMPEG returned: {ffmpeg.returncode}.  Quitting")
                exit(1)
        else:
            self.logger.debug(
                "File {} already exists.  Skipping", self.track_row.file_path
            )

    def write_id3_tags(self) -> None:
        self.logger.debug("Adding ID3 tags.")
        audiofile = eyed3.load(self.track_row.file_path)
        if audiofile is not None and audiofile.tag is not None:
            audiofile.tag.artist = self.track_row.artist_name
            audiofile.tag.album_artist = self.track_row.artist_name
            audiofile.tag.album = self.track_row.source.album_name
            audiofile.tag.title = self.track_row.track_title
            audiofile.tag.track_num = self.track_row.track_number
            with open(self.track_row.source.image_file, "rb") as f:
                imagedata = f.read()
                audiofile.tag.images.set(3, imagedata, "image/jpeg", "")
            audiofile.tag.recording_date = str(self.track_row.source.upload_date)
            audiofile.tag.save()

    def exists(self):
        file_path = Path(self.track_row.file_path)
        return file_path.exists()

    def add_tag(self, tag_str):
        TrackTag.add_x_to_track(self.track_row, "tag", tag_str)

    def remove_tag(self, tag_str):
        TrackTag.remove_tag_from_track(self.track_row, "tag", tag_str)

    def add_word(self, word_str):
        TrackWord.add_x_to_track(self.track_row, "word", word_str)

    def remove_word(self, word_str):
        TrackWord.remove_tag_from_track(self.track_row, "word", word_str)

    def words(self):
        query = (
            TrackWord.select(TrackWord, TrackTbl, Word)
            .join(Word)
            .switch(TrackWord)
            .join(TrackTbl)
            .where(TrackTbl.id == self.track_row.id)
        )
        word_list = []
        for track_word in query.execute():
            word_id = track_word.word_id
            words = Word.select().where(Word.id == word_id)
            for word in words:
                word_list.append(word.word)

        return word_list

    def tags(self):
        query = (
            TrackTag.select(TrackTag, TrackTbl, Tag)
            .join(Tag)
            .switch(TrackTag)
            .join(TrackTbl)
            .where(TrackTbl.id == self.track_row.id)
        )
        tag_list = []
        for track_tag in query.execute():
            tag_id = track_tag.tag_id
            tags = Tag.select().where(Tag.id == tag_id)
            for tag in tags:
                tag_list.append(tag.tag)

        return tag_list
