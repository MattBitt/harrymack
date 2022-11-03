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


from utils import convert_date_string, convert_date_time_object

# from models import Source as SourceTbl

import re
from yt_dlp_functions import get_json_info


class Source:
    # This object represents a YouTube video.

    def __init__(self, url: str, playlist: dict, config: dict):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.load_data(url, playlist, config)
        self.download_files()
        self.find_all_files()
        self.resize_image(self.image_file, 1280, 1280)

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
            info = get_json_info(url)
            if not info:
                logger.debug("Probably a private video")
                # TODO: Should still add this video to the db.  Just add "Unknown" for all fields?
                raise FileNotFoundError()
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
        self.ignore = False
        self.album_name = ""
        self.episode_number = ""
        self.upload_date = convert_date_string(info["upload_date"], "YYYY-MM-DD")
        self.audio_file = ""
        self.image_file = ""
        self.description_file = ""
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
                    if exception["video_title"] in self.video_title:
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

    def exists(self) -> bool:
        """
        the download is considered to exist if the mp3 file is there.  this is the file that i name in the download command
        need to check the directory for existence of the audio, image, and description files.  Since I wont know the name of the files after they are downloaded
        The format will be self.id + (YYYYMMDD).
        construct the whole path (path + name + extension)
        list
        check if the file exists
        if it does

        """
        if self.audio_file == "":
            return False
        else:
            return os.path.exists(str(self.audio_file))

    #    def full_paths(self):
    #        filetypes = ["audio", "image", "description"]
    #        files = []
    #        for f in filetypes:
    #            files.append((f, self.find_file(f)))
    #        file_dict = {k: v for k, v in filetypes}
    #        return file_dict

    def download_files(self) -> bool:

        """
        build yt-dlp command
        run command
        """

        # * output name should not have ".ext"
        # f = os.path.join(track.source.path, track.source.base_name + ".mp3")

        args1 = ["yt-dlp"]
        args2 = []
        if not self.config["log_level"] == "DEBUG":
            args2 = ["--no-warnings", "--quiet"]
        args3 = [
            "--extract-audio",
            "--write-description",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "0",
            "-o",
            str(self.file_base_path) + ".mp3",
            "--write-thumbnail",
            self.url,
        ]
        self.logger.info("Starting download of {}", self.url)
        yt_dl = subprocess.run(args1 + args2 + args3)
        if yt_dl.returncode:
            self.logger.error("There was an error processing {}", yt_dl.returncode)
            return False
        else:
            self.logger.success("The file was successfully downloaded:  {}", self.url)
            return True

    def find_all_files(self):
        # * these are the possible extensions to search for
        extensions = {}
        extensions["audio"] = ["*.mp3"]
        extensions["image"] = ["*.mp3.jpg", "*.mp3.webp", "*.jpg"]
        extensions["description"] = ["*.mp3.description"]
        filenames = {"audio": "", "image": "", "description": ""}
        k: str
        ext: str
        for k, ext in extensions.items():
            for e in ext:
                f = self.find_file(e)
                if not f == "":
                    filenames[k] = str(f)
                    continue
        self.audio_file = filenames["audio"]
        self.image_file = filenames["image"]
        self.description_file = filenames["description"]

    def find_file(self, pattern) -> Path | str | None:
        search_string = str(self.root_directory / (self.youtube_id + pattern))
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

    def find_tracks(self) -> list[tuple[str, str]]:
        if self.audio_file == "":
            logger.error("No audio file found.  Cannot proceed")
            raise FileNotFoundError
        self.logger.debug("Analyzing audio clip {}", self.audio_file)
        whole_track = AudioSegment.from_mp3(self.audio_file)
        # silences = self.detect_silence(whole_track)
        chunks = detect_silence(
            whole_track,
            min_silence_len=800,
            silence_thresh=-16,
            seek_step=50,
        )
        # now recombine the chunks so that the parts are at least 90 sec long
        target_length = 180 * 1000
        output_chunks = []
        new_chunk = True
        start_time = 0
        for chunk in chunks:
            if new_chunk:
                start_time = chunk[0]
            end_time = chunk[1]
            if (end_time - start_time) > target_length:
                output_chunks.append((start_time, end_time))
                new_chunk = True
            else:
                new_chunk = False
            # if len(output_chunks[-1]) < target_length:
            #     output_chunks[-1] += chunk
            # else:
            #     # if the last output chunk is longer than the target length,
            #     # we can start a new one
            #     output_chunks.append(chunk)
        output_chunks = self.convert_list_ms_to_list_start_end(output_chunks)

        return output_chunks

    def convert_list_ms_to_list_start_end(self, chunks):
        output = []
        time_margin = 3000  # ms to keep around tracks
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
            video_title=self.video_title,
            video_type=self.video_type,
            youtube_id=self.youtube_id,
        )
        self.logger.success("Added record {}", self.video_title)

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

    def resize_image(self, img_path: str, width: int, height: int):
        img = Image.open(img_path)
        new_img = img.resize((width, height))
        new_img.save(img_path)
        return new_img

    # def create_source_video_object(self, url: str, playlist: dict, config: dict):

    #     # match playlist:
    #     #     case {"separate_album_per_episode": true}:
    #     #         pass
    #     #     case {"video_exceptions": exceptions}:
    #     #         pass

    #     # if playlist["separate_album_per_episode"]:
    #     #     if "video_exceptions" in playlist.keys():
    #     #         for override in playlist["episode_number_overrides"]:
    #     #             if override["title"] in info["title"]:
    #     #                 ep_number = str(override["episode_number"])
    #     #     if ep_number == "":
    #     #         ep_number = get_episode_number(info["title"], playlist["patterns"]).zfill(3)
    #     #         if ep_number == "000" or ep_number == "":
    #     #             continue

    #     return source
