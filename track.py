from pathlib import Path
import os
import glob
from loguru import logger
import subprocess
from datetime import datetime


class Source:
    # ! need to change video_type to clip type (or vice versa)
    def __init__(self, data_row, config):
        self.load_data(data_row, config)

        logger.debug("Source created:  {}", self.id)
        # if not self.exists() or (self.exists() and self.overwrite_download):
        # need to download new file
        self.download_files()
        self.find_all_files()

    def load_data(self, data_row, config):
        self.config = config
        self.video_type = data_row["ClipTypes"]
        self.url = data_row["URL"]
        self.root_directory = Path(config[config["enviornment"]]["download_directory"])
        self.id = data_row["WholeName"]
        self.words = data_row["PrimaryWords"]
        self.episode_number = data_row["EpisodeNumber"]
        self.overwrite_download = config["overwrite_download"]
        self.download_path = self.root_directory / self.id

    def exists(self, filetype):
        """
        the download is considered to exist if the mp3 file is there.  this is the file that i name in the download command
        need to check the directory for existence of the audio, image, and description files.  Since I wont know the name of the files after they are downloaded.add()
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

    def download_files(self):

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
            str(self.download_path) + " (%(upload_date)s).mp3",
            "--write-thumbnail",
            self.url,
        ]
        logger.info("Starting download of {}", self.url)
        yt_dl = subprocess.run(args1 + args2 + args3)
        if yt_dl.returncode:
            logger.error("There was an error processing {}", yt_dl.returncode)
            return False
        else:
            logger.success("The file was successfully downloaded:  {}", self.url)
            return True

    def find_all_files(self):
        # * these are the possible extensions to search for
        extensions = {}
        extensions["audio"] = ["*.mp3"]
        extensions["image"] = ["*.mp3.jpg", "*.mp3.webp"]
        extensions["description"] = ["*.mp3.description"]
        self.filenames = {"audio": "", "image": "", "description": ""}
        for k, ext in extensions.items():
            for e in ext:
                f = self.find_file(e)
                if not f == "":
                    self.filenames[k] = f
                    continue

    def find_file(self, pattern):
        search_string = str(self.root_directory / (self.id + pattern))
        file_list = glob.glob(search_string)
        if len(file_list) == 1:
            return file_list[0]
        elif len(file_list) > 1:
            logger.debug("Too many files found: %s", os.dir(self.path()))
        else:
            # * if the directory doesn't exist, then its not downloaded.  no need to check further
            return ""


class ID3:
    def __init__(self, data_row):
        self.title = data_row["Title"]
        self.album_name = data_row["AlbumName"]
        self.track_number = data_row["TrackNumber"]
        self.beat_name = data_row["BeatName"]
        self.producer = data_row["Producer"]
        self.artist_name = data_row["ArtistName"]
        # self.source = Source(source_info['WholeName'], config[config['enviornment']]['download_directory'])
        # self.filename = self.track_number + " - " + self.track_title + '.mp3'  # 1 - OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons
        logger.debug("ID3 created:  {}", self.title)


class Track:
    def __init__(self, data_row, config, source, id3):
        self.source = source
        self.id3 = id3
        self.start_time = data_row["StartTime"]
        self.end_time = data_row["EndTime"]
        self.root_directory = config[config["enviornment"]]["music_root"]
        self.filename = data_row["Filename"]
        self.extension = ".mp3"
        logger.debug("Track created:  {}", self.filename)

    def full_path(self):
        # * will return path /musicroot/album_folder/filename.mp3
        # * need to see if yt-dlp gives me names of downloaded files
        return Path.joinpath(self.root_directory, self.id3.album_name, self.filename, self.extension)

    def extract_from_source(self):
        if self.source.split_by_times():
            self.source.extract_single(self.start_time, self.end_time, self.full_path())
            pass
        elif self.source.split_by_silence():
            self.source.extract_multiple(self.full_path)
