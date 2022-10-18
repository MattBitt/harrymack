from pathlib import Path
import os
import glob
from loguru import logger
import subprocess
from datetime import datetime
import eyed3
from eyed3.core import Date


class Source:
    old_source = ""

    # ! need to change video_type to clip type (or vice versa)
    def __init__(self, data_row, config):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.load_data(data_row, config)
        self.find_all_files()

        self.new_source = True if self.url != Source.old_source else False
        if self.new_source:
            self.logger.debug("New source: {} Need to process", self.url)
            Source.old_source = self.url
        else:
            self.logger.debug("Reusing source: {}", self.url)
        if not self.exists("audio") or (
            self.exists("audio") and self.overwrite_download
        ):
            # need to download new file
            self.download_files()
            self.find_all_files()
        if not self.exists("audio"):
            # * need to raise an error here.  no audio files were found after the download took place
            self.logger.debug("No source audio found!")
            raise FileNotFoundError
        else:
            self.logger.debug("Source audio file is {}", self.filenames["audio"])
            Source.old_source = self.url

    def load_data(self, data_row, config) -> None:
        self.config = config
        self.video_type = data_row["ClipTypes"]
        self.url = data_row["URL"]
        self.root_directory = Path(config[config["enviornment"]]["download_directory"])
        self.id = data_row["WholeName"]
        self.file_base_path = self.root_directory / self.id
        self.words = data_row["PrimaryWords"]
        self.episode_number = data_row["EpisodeNumber"]
        self.overwrite_download = config["overwrite_download"]

    def exists(self, filetype: str) -> bool:
        """
        the download is considered to exist if the mp3 file is there.  this is the file that i name in the download command
        need to check the directory for existence of the audio, image, and description files.  Since I wont know the name of the files after they are downloaded
        The format will be self.id + (YYYYMMDD).
        construct the whole path (path + name + extension)
        list
        check if the file exists
        if it does


        """
        if self.filenames[filetype] == "":
            return False
        else:
            return os.path.exists(self.filenames[filetype])

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
            str(self.file_base_path) + " (%(upload_date)s).mp3",
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
        self.filenames = {"audio": "", "image": "", "description": ""}
        k: str
        ext: str
        for k, ext in extensions.items():
            for e in ext:
                f = self.find_file(e)
                if not f == "":
                    self.filenames[k] = str(f)
                    continue

    def find_file(self, pattern) -> Path | str | None:
        search_string = str(self.root_directory / (self.id + pattern))
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


class ID3:
    def __init__(self, data_row):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.title = data_row["Title"]
        self.album_name = data_row["AlbumName"]
        self.track_number = data_row["TrackNumber"]
        self.beat_name = data_row["BeatName"]
        self.producer = data_row["Producer"]
        self.artist_name = data_row["ArtistName"]
        self.logger.debug("ID3 created:  {}", self.title)


class Track:
    def __init__(self, data_row, config, source, id3):
        self.logger = logger.bind(classname=self.__class__.__name__)
        self.load_data(data_row, config, source, id3)
        self.logger.debug("Track created:  {}", self.filename)
        self.create_folder()
        self.full_path = (
            self.root_directory
            / self.id3.album_name
            / Path(self.filename + self.extension)
        )

    def load_data(self, data_row, config, source, id3):
        self.source = source
        self.id3 = id3
        self.start_time = data_row["StartTime"]
        self.end_time = data_row["EndTime"]
        self.root_directory = Path(config[config["enviornment"]]["music_root"])
        self.filename = data_row["Filename"]
        self.extension = ".mp3"

    def create_folder(self):
        Path(self.root_directory / self.id3.album_name).mkdir(exist_ok=True)

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
            audiofile.tag.artist = self.id3.artist_name
            audiofile.tag.album = self.id3.album_name
            audiofile.tag.album_artist = self.id3.artist_name
            audiofile.tag.title = self.id3.title
            audiofile.tag.track_num = self.id3.track_number
            # with open(img, "rb") as f:
            #    imagedata = f.read()
            #    audiofile.tag.images.set(3, imagedata, "image/jpeg", "")
            # audiofile.tag.recording_date = Date(y`ear)
            audiofile.tag.save()

        # if self.source.split_by_times():
        #     self.source.extract_single(self.start_time, self.end_time, self.full_path)
        #     pass
        # elif self.source.split_by_silence():
        #     self.source.extract_multiple(self.full_path)

    def add_source(self, source: Source) -> None:
        pass
