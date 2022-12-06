from loguru import logger
from models import Source as SourceTbl
from pathlib import Path
from datetime import datetime
from pathlib import Path
import os
import glob
from tracemalloc import start
from loguru import logger
import subprocess
from datetime import datetime
from pydub import AudioSegment
from pydub_functions import split_on_silence, detect_silence
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from utils import create_folder

from utils import convert_date_string, convert_date_time_object, get_year
from mutagen.mp4 import MP4

# from models import Source as SourceTbl

import re
from yt_dlp_functions import get_json_info


class SourceImporter:
    # This object represents a YouTube video.

    def __init__(self, url: str, playlist: dict, config: dict):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.load_data(url, playlist, config)

        # self.find_all_files()

        # self.new_source = True if self.url != Source.old_source else False
        # if self.new_source:
        #     self.logger.debug("New source: {} Need to process", self.url)
        #     Source.old_source = self.url
        # else:
        #     self.logger.debug("Reusing source: {}", self.url)
        # if not self.exists("audio") or (
        #     self.exists("audio") and self.overwrite_download
        # ):
        #     # need to download new file

        # if not self.exists("audio"):
        #     # * need to raise an error here.  no audio files were found after the download took place
        #     self.logger.debug("No source audio found!")
        #     raise FileNotFoundError
        # else:
        #     self.logger.debug("Source audio file is {}", self.filenames["audio"])
        #     Source.old_source = self.url

    def load_data(self, url, playlist, config) -> None:
        if url:
            ignore = False
            info = get_json_info(url)
            if not info:
                ignore = True
                info = {}
                info["title"] = "Private Video"
                info["original_url"] = url
                info["id"] = "XXXXXXXXX"
                info["upload_date"] = str(datetime.today())[0:10]
                logger.debug("Probably a private video.  Adding to DB")
                # Should still add this video to the db.  Just add "Unknown" for all fields?
                # raise FileNotFoundError()
        else:
            self.logger.error("No URL found.  Quitting")
            raise FileNotFoundError()
        # load all values into instance
        self.config = config
        self.root_directory = Path(
            self.config[config["enviornment"]]["download_directory"]
        )
        self.created_date = convert_date_time_object(datetime.now())
        self.overwrite_download = config["overwrite_download"]
        self.video_title = info["title"]
        self.url = info["original_url"]
        self.youtube_id = info["id"]
        self.video_type = playlist["video_type"]
        self.ignore = ignore
        self.album_name = ""
        self.episode_number = ""
        self.upload_date = convert_date_string(info["upload_date"], "YYYY-MM-DD")
        self.audio_file = ""
        self.image_file = ""
        self.description_file = ""
        self.video_file = ""
        self.split_by_silence = playlist["split_by_silence"]
        self.file_base_path = self.root_directory / self.youtube_id
        if not playlist["separate_album_per_episode"]:
            self.album_name = self.video_type
            self.episode_number = ""
        else:
            found_exception = False
            if "video_exceptions" in playlist.keys():
                # check if this url is listed as an exception in the yaml.

                for exception in playlist["video_exceptions"]:
                    if exception["url"] in self.url:
                        found_exception = True
                        match exception:
                            case {"ignore": ignore}:
                                self.ignore = ignore
                            case {
                                "episode_number": episode_number,
                                "album_name": album_name,
                            }:
                                self.episode_number = episode_number
                                self.album_name = album_name
                            case {"episode_number": episode_number}:
                                self.episode_number = episode_number
                                self.album_name = (
                                    self.video_type + " " + str(self.episode_number)
                                )
                            case _:
                                self.logger.error(
                                    "Keys not understood:  {}", exception.keys()
                                )

                        # ep_number = str(exception["episode_number"])

            if "typical_video" in playlist.keys() and not found_exception:

                # no exception listed.  parse this file as typical
                try:
                    patterns = playlist["typical_video"][0]["episode_number_patterns"]
                    self.episode_number = self.find_episode_number(
                        self.video_title, patterns
                    )
                except KeyError:
                    # likely no episode number patterns found
                    self.episode_number = ""
                if self.episode_number != "":
                    self.album_name = self.video_type + " " + self.episode_number
                else:
                    self.album_name = self.video_type
            # this_album = albums.get({"album_name": self.album_name})
            # print(f"length of albums = {len(albums)}")
            # print(f"length of this_album = {len(this_album)}")
            # if self.album_name != "" and not this_album:
            #     albums.add(self.album_name, self.split_by_silence)
            #     self.album = albums.get({"album_name": self.album_name})
            #     self.album = self.album[0].id
            # elif albums.get({"album_name": self.album_name}):
            #     self.album = albums.get({"album_name": self.album_name})[0].id
            # need to create album here if it doesn't already exist.
        # else:
        #     self.logger.error(
        #         "No exceptions or templates found for video", self.video_title
        #     )
        #     raise KeyError()

        # self.words = info["PrimaryWords"]
        # self.episode_number = info["EpisodeNumber"]
        # self.album_name

    def find_episode_number(self, text: str, patterns: list) -> str:
        if text == "" or patterns == []:
            self.logger.error("No text or pattern found {} {}", text, patterns)
            raise KeyError
        for pattern in patterns:
            self.logger.debug("Pattern = {}", pattern)
            # print(re.search(pattern, video_title, re.DEBUG))
            pattern = re.compile(pattern)
            result = pattern.search(text)
            if result is not None:
                return str(result.groups(1)[0]).zfill(3)

        self.logger.warning("No Match found for {}", text)
        return ""

    def mp3_exists(self) -> bool:
        if self.audio_file == "":
            return False
        else:
            return os.path.exists(str(self.audio_file))

    def save_to_db(self):
        # should there be create/update checks here?
        # will i ever need to update the data without starting from
        source = SourceTbl.create(
            album_name=self.album_name,
            audio_exists=self.mp3_exists(),
            audio_file=self.audio_file,
            created_date=self.created_date,
            description_file=self.description_file,
            episode_number=self.episode_number,
            ignore=self.ignore,
            image_file=self.image_file,
            split_by_silence=self.split_by_silence,
            upload_date=self.upload_date,
            url=self.url,
            video_exists=False,
            video_file=self.video_file,
            video_title=self.video_title,
            video_type=self.video_type,
            youtube_id=self.youtube_id,
        )
        self.logger.success("Added record {}", self.video_title)


class Source:
    def __init__(self, source, config):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.source_row = source
        self.config = config
        self.root_directory = Path(
            self.config[config["enviornment"]]["download_directory"]
        )
        file_base = self.sanitize_for_file_name()
        self.audio_folder = self.get_target_folder("audio")
        if not self.audio_folder.exists():
            create_folder(self.audio_folder)
        self.target_folder = self.get_target_folder("video")
        if not self.target_folder.exists():
            create_folder(self.target_folder)
        self.audio_file_base_path = self.audio_folder / file_base
        self.video_file_base_path = self.target_folder / file_base
        self.audio_file = str(self.audio_file_base_path) + ".mp3"
        self.video_file = str(self.video_file_base_path) + "-video.mp4"
        # self.track_num = self.get_track_num()

    def get_target_folder(self, filetype):
        # this will return the folder that the video will exist in
        # this folder should be root directory/"Harry Mack"/$albumname/
        # albumname should be the name stored in the db if separate track per album
        # should there be another option?

        return self.root_directory / filetype / "Harry Mack" / self.source_row.video_type

    def sanitize_for_file_name(self):
        fn = self.source_row.video_title
        return_line = ""
        bad_characters = r"$#\"'|?/&🔴:"
        for char in fn:
            if char not in bad_characters:
                return_line += char

        return return_line

    def download_files(self) -> bool:
        args1 = ["yt-dlp"]
        args2 = []
        if not self.config["log_level"] == "DEBUG":
            args2 = ["--no-warnings", "--quiet"]
        args3 = [
            "-f",
            '"res:720,fps" [ext=mp4]',
            "--write-description",
            "-o",
            self.video_file,
            "--write-thumbnail",
            self.source_row.url,
        ]
        self.logger.debug("Starting download of {}", self.source_row.video_title)
        yt_dl = subprocess.run(args1 + args2 + args3)
        if yt_dl.returncode:
            self.logger.error("There was an error processing {}", yt_dl.returncode)
            return False
        else:
            self.logger.success(
                "The file was successfully downloaded:  {}", self.source_row.video_title
            )
            # TODO Need to extract audio here
            self.convert_mp4_to_mp3()
            self.find_all_files()
            self.write_metadata()
            self.resize_image(self.source_row.image_file, 1280, 1280)
            return True

    def convert_mp4_to_mp3(self):
        source_mp4 = self.video_file
        target_mp3 = self.audio_file
        # self.logger.debug("Starting extraction from {}.", self.track_row.source.url)
        args = [
            "ffmpeg",
            "-y",
            "-i",
            source_mp4,
            "-hide_banner",
            "-loglevel",
            "warning",
            target_mp3,
        ]
        self.logger.debug("ffmpeg arguments:  " + " ".join(args))
        ffmpeg = subprocess.run(args)

        if ffmpeg.returncode:
            print(f"FFMPEG returned: {ffmpeg.returncode}.  Quitting")
            exit(1)

    def find_all_files(self):
        # * these are the possible extensions to search for
        extensions = {}
        extensions["image"] = ["*.mp3.jpg", "*.mp3.webp", "*.jpg", "*.webp"]
        extensions["description"] = ["*.description", "*.mp3.description"]
        filenames = {"image": "", "description": ""}
        k: str
        ext: str
        for k, ext in extensions.items():
            for e in ext:
                f = self.find_file(e)
                if not f == "":
                    filenames[k] = str(f)
                    continue
        self.source_row.audio_file = self.audio_file
        self.source_row.video_file = self.video_file
        self.source_row.image_file = filenames["image"]
        self.source_row.description_file = filenames["description"]
        self.source_row.audio_exists = True
        self.source_row.video_exists = True
        self.source_row.save()

    def find_file(self, pattern) -> Path | str | None:
        search_string = str(self.video_file_base_path) + pattern
        file_list = glob.glob(search_string)
        if len(file_list) == 1:
            return file_list[0]
        elif len(file_list) > 1:
            self.logger.debug(
                "Too many files found: %s", os.listdir(self.root_directory)
            )
        else:
            # * if the directory doesn't exist, then its not downloaded.  no need to check further
            return ""

    def convert_list_ms_to_list_start_end(self, chunks):
        output = []
        time_margin = 10  # ms to keep around tracks
        for start_time, end_time in chunks:
            if start_time < time_margin:
                start_time = 0
            else:
                start_time = start_time - time_margin
            if end_time != chunks[-1][1]:
                end_time = end_time + time_margin

            output.append(
                (
                    self.ms_to_hhmmss(start_time),
                    self.ms_to_hhmmss(end_time),
                )
            )
        return output

    def ms_to_hhmmss(self, millis):
        millis = int(millis)
        seconds = (millis / 1000) % 60
        seconds = int(seconds)
        minutes = (millis / (1000 * 60)) % 60
        minutes = int(minutes)
        hours = (millis / (1000 * 60 * 60)) % 24
        hours = int(hours)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def resize_image(self, img_path: str, width: int, height: int):
        img = Image.open(img_path)
        new_img = img.resize((width, height))
        new_img.save(img_path)
        return new_img

    def write_metadata(self):
        # these are examples of other tags that can be added
        # mp4_video_tags["\xa9gen"] = Genre
        # mp4_video_tags["aART"] = Album Artist
        # mp4_video_tags["\xa9wrt"] = Composer
        # mp4_video_tags["cprt"] = Copyright
        # mp4_video_tags["desc"] = Description
        # mp4_video_tags["disk"] = [(1, 1)]

        mp4_video_tags = MP4(self.video_file)

        mp4_video_tags["\xa9nam"] = self.source_row.video_title
        mp4_video_tags["\xa9alb"] = self.source_row.album_name

        mp4_video_tags["\xa9day"] = get_year(self.source_row.upload_date)
        mp4_video_tags["\xa9ART"] = "Harry Mack"

        # here, i need to put in a track number
        # mp4_video_tags["trkn"] = [(self.track_num, 1000)]
        mp4_video_tags.save()

    def get_track_num(self):
        if self.source_row.episode_number:
            return int(self.source_row.episode_number)
        else:
            print(len(self.source_row.with_video_type(self.source_row.video_type)))
