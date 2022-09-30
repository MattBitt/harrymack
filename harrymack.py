import subprocess
import csv
import os
from datetime import datetime
import eyed3
from eyed3.core import Date
import shutil
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import glob
import sys
from loguru import logger
from pyaml_env import parse_config

from WordGrid import resize_image, TextArea, WordGrid, Word, prepare_image
from plex_functions import plex_update_library, connect_to_server, add_mood
#### Need to add logic to tell plex to update library after scan.  Music libraries excluded from auto updates in plex





class EmptyListError(ValueError):
    """
    Raised to signal the fact that a list is empty.
    """


class Source:
    def __init__(self, base_name, path):
        self.base_name = base_name
        self.path = path
        

    def get_full_path(self):
        pattern = f"{self.base_name}*.mp3"
        file_list = glob.glob(self.path + pattern)
        if len(file_list) == 0:
            return None
        if len(file_list) > 1:
            logger.debug("Too many results returned for query {}.  results = {}", pattern, file_list)
            return None
        return file_list[0]

    def exists(self):
        if not self.get_full_path():
            logger.debug("{} Does not exist", self.path + self.base_name)
            return False
        else:
            return True

class Track:
    def __init__(self, source_info, config):
        #self.source_video_name = source_info['WholeName'] # NPdKxsSE5JQ
        #self.source_path = config[config['enviornment']]['download_directory']
        #self.source_full_path = self.get_source_full_path()
        self.source = Source(source_info['WholeName'], config[config['enviornment']]['download_directory'])
        self.artist = source_info['ArtistName'] # Harry Mack
        self.album = source_info['AlbumName'] # Omegle Bars 1
        self.track_number = source_info['TrackNumber'] # 1
        self.track_title = source_info['Title'] # OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons
        self.filename = self.track_number + " - " + self.track_title + '.mp3' # 1 - OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons
        self.start_time = source_info['StartTime']
        self.end_time = source_info['EndTime']
        self.url = source_info['URL']
        self.beatname = source_info['BeatName']
        self.producer = source_info['Producer']
        self.words = source_info['Words']
        self.destination_path = os.path.join(config[config['enviornment']]['music_root'], self.album)
        self.destination_full_path = os.path.join(self.destination_path, self.filename) # ./media/musicroot/Omegle Bars 1/OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons.mp3


    
    def destination_exists(self):
        logger.debug(self.destination_full_path)
        return os.path.exists(self.destination_full_path)
    



def load_track_data(path):
    try:
        track_info_list = import_from_csv(path)

    except FileNotFoundError:
        logger.error("No CSV file found.  Please check the path and try again. path={}", path)
        raise
    except EmptyListError:
        logger.error("No records found in CSV file.  Please check the import and retry. path={}", path)
        raise
    except KeyError:
        logger.error("There is a problem with the CSV file.  path={}", path)
        raise
    
    tracks = []
    for track_info in track_info_list:
        tracks.append(Track(track_info, config))
    return tracks

def import_from_csv(csv_name):
    if not os.path.exists(csv_name):
        raise FileNotFoundError(f"File {csv_name} not found")

    with open(csv_name, "r") as f:
        csv_reader = csv.DictReader(f)
        track_info = list(csv_reader)
    
    # CSV file exists, but there aren't any records
    if track_info == []:
        raise EmptyListError(f"File {csv_name} does not contain any records")
    
    fields = ['WholeName', 'ArtistName', 'AlbumName', 'TrackNumber', 'Title', 'StartTime', 'EndTime', 'URL', 'BeatName', 'Producer' ]
    for f in fields:
        if not f in track_info[0].keys():
            logger.error("{} does not exist in csv.  Please export and try again.", f)
            raise KeyError(f"{f} does not exist in csv.  Please export and try again.")
    return track_info

def load_config(config_path):
    #need to validate the settings here?
    # need to check paths as well
    if not os.path.exists(config_path):
        # what to do if the config file doesn't exist?
        pass
    config = parse_config(config_path)
    music_root = config[config['enviornment']]['music_root']
    source_directory = config[config['enviornment']]['download_directory']
    err_mess = ""
    if not music_root or not os.path.exists(music_root):
        err_mess = f"No music root directory found.  Please check the paths and try again. mr={music_root}"
    elif not source_directory or not os.path.exists(source_directory):
        err_mess = f"No source directory found.  Please check the paths and try again. sd={source_directory}"
   
    if err_mess:
        logger.error(err_mess)
        raise KeyError(err_mess)
    
    return config

def setup_logging():
    logger.remove(0)
    # adds logging to stderr
    log_format = (
        "{time: YYYY-MM-DD HH:mm:ss.SSS} | "
        "<lvl>[{level: <8}]"
        "</lvl><yellow>{name}:{function}:{line}</yellow> - "
        "<lvl>{message}</lvl>"
    )
    logger.add(sys.stderr, format=log_format, level=config['log_level'], colorize=True)
    # don't log to file on production.  run in docker so it should handle the log cleanup
    if config['log_level'] == "DEBUG" and not config['enviornment'] == 'env_prod':
        log_path = './logs/'
        log_file = 'harrymack.log'
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        logger.add(os.path.join(log_path, log_file), backtrace=True, diagnose=True)
    return logger

def process_with_ffmpeg(track, overwrite=False):
    if track.destination_exists() and not overwrite:
        # destination path exists and we don't want to overwrite
        logger.debug("File exists.  OVERWRITE=False.  Skipping processing.")
        return False
    elif track.destination_exists() and overwrite:
        # destination path exists but we do want to overwrite
        logger.debug("File exists.  OVERWRITE=True.  Need to process.")
        return True
    else:
        logger.debug("File does not exist.  Need to process.")
        return True

def download_source_file(track, overwrite=False):
    if track.source.exists() and not overwrite:
        # destination path exists and we don't want to overwrite
        logger.debug("File exists.  OVERWRITE=False.  Skipping download.")
        return False
    elif track.source.exists() and overwrite:
        # destination path exists but we do want to overwrite
        logger.debug("File exists.  OVERWRITE=True.  Need to download.")
        return True
    else:
        logger.debug("File does not exist.  Need to download.")
        return True


def youtube_download(track, config):
    # output name should not have ".ext"
    f = os.path.join(track.source.path, track.source.base_name + ".mp3")
    args1 = ["yt-dlp"]
    args2 = []
    if not config['log_level'] == 'DEBUG':
        args2 = ['--no-warnings', '--quiet']
    args3 = ['--extract-audio', 
            '--write-description',
            '--audio-format',
            'mp3',
            '--audio-quality',
            '0',
            "-o", 
            f[:-4] + " (%(upload_date)s).mp3",
            "--write-thumbnail", 
            track.url]
    logger.info("Starting download of {}", track.url)
    yt_dl = subprocess.run(args1 + args2 + args3)
    if yt_dl.returncode:
        logger.error("There was an error processing {}", yt_dl.returncode )
        return False
    else:
        
        logger.success("The file was successfully downloaded:  {}", track.url)
        return True



def extract_audio(source, destination, start_time, end_time):
    if not os.path.exists(destination):
        ffmpeg = subprocess.run(['ffmpeg', 
            '-y',
            '-i', 
            source, 
            '-ss', 
            start_time, 
            '-to', 
            end_time,
            '-hide_banner',
            '-loglevel', 
            'warning',
            destination])

        if ffmpeg.returncode:
            print("FFMPEG returned: {ffmpeg.returncode}.  Quitting")
            exit()
    else:
        print(f"File {destination} already exists")

def update_id3(mp3file, artist, album, title, track_num, year, img):
    
    audiofile = eyed3.load(mp3file)
    audiofile.tag.artist = artist
    audiofile.tag.album = album
    audiofile.tag.album_artist = artist
    audiofile.tag.title = title
    audiofile.tag.track_num = track_num
    with open(img,"rb") as f:
        imagedata = f.read()
        audiofile.tag.images.set(3,imagedata,"image/jpeg","")
    audiofile.tag.recording_date = Date(year)
    audiofile.tag.save()

def create_album_folder(path):
    if not os.path.exists(path):
        os.umask(0)
        os.makedirs(path, mode=0o777)

def move_file(source, destination, overwrite):
    if os.path.exists(destination):
        if overwrite:
            os.remove(destination)
        else:
            print("Could not overwrite destination file {destination}")
            return False  
    shutil.move(source, destination)
    return True

def copy_file(source, destination, overwrite):
    if os.path.exists(destination):
        if overwrite:
            os.remove(destination)
        else:
            print("Could not overwrite destination file {destination}")
            return False  
    shutil.copy(source, destination)
    return True


def parse_files(dir, base_filename):
    if dir[-1] != "/":
        dir = dir + "/"

    types = ['audio', 'image', 'description']
    files = {}
    files['audio'] = ""
    files['image'] = ""
    files['description'] = ""  
    # these are the patterns downloaded from youtube.  
    patterns = {}
    patterns['audio'] = [base_filename + '*.mp3']
    patterns['image'] = [base_filename + '*.mp3.webp', base_filename + '*.webp', base_filename + '*.jpg']
    patterns['description'] = [base_filename + '*.mp3.description']
    for t in types:
        for pattern in patterns[t]:
            file_list = glob.glob(dir + pattern)
            if len(file_list) == 1: # This always chooses the first file returned.  Need to do any other testing here?
                files[t] =  file_list[0]
            elif len(file_list) > 1:
                #print(f"More than 1 file found matching the {pattern}\n{file_list}")
                pass
            else:
                #print(f"No matching files found:  {pattern}\n{file_list}")
                pass
            
    
    year = get_year(files['audio'])
    return files, year

def convert_to_jpg(source, destination):
    img = Image.open(source)
    img.save(destination, optimize=True)
    return destination

def get_fonts(dir):
    dir = add_slash(dir)
    return os.listdir(dir)
    #for entry in os.scandir(dir):
    #    if entry.name.endswith('.ttf'):
    #        yield dir + entry.name

def add_slash(path):
    if path[-1] != "/":
        path = path + "/"
    return path

def get_year(file):
    if file:
        start = file.find('(')
        return int(file[start + 1:start + 5])
    else:
        print(f"No file given.  Please try again")
        return False

def get_path(path_list):
    # this function returns whichever folder exists.  path_list should be in preference order
    for p in path_list:
        if os.path.exists(p):
            p = add_slash(p)
            return p
    print(f"No paths found {path_list}")
    return False








if __name__ == "__main__":
    VERSION = "1.4.0"
    CONFIG_PATH = "./config.yaml"
    config = load_config(CONFIG_PATH)
    logger = setup_logging()
    logger.success("Starting Program ({})", VERSION)

    tracks = load_track_data(config['import_csv'])
    if not tracks:
        logger.error("No Track objects were created {}", tracks)
    else:
        logger.debug("Music root directory = {}", tracks[0].destination_path)
        logger.debug("Downloads directory = {}", tracks[0].source.get_full_path())

    # setup connection to plex
    plex = connect_to_server()
    #font_counter = 0
    
    album = None
    previous_album = None
    new_album = False
    new_albums = []
    moods = []
    # Loop through each clip in the CSV
    for track in tracks:
        album_image = ""

        # these functions return booleans depending on what needs to be done (download, audio processing)
        download_file = download_source_file(track, config['overwrite_download'])
        ffmpeg_process = process_with_ffmpeg(track, config['overwrite_destination'])

        if download_file:
            downloaded = youtube_download(track, config)
            if not downloaded:
                logger.error("Error downloading clip {}. Skipping to next track", track.url)
                continue


        if ffmpeg_process:
            pass
        exit()
        if track.album != previous_album:
            # This clip is part of a different album than the previous.  
            # if there was a previous album should i delete it?  probably not.  should wait until the end and delete everthing in the downloads folder
            # should i check for files in downloads folder on start?  give warning?
            # Create the folder /musicroot/album
            # Take the album image and resize it to 1280x1280.  Make a copy called 'album.jpg'.  move to /musicroot/album folder
            new_album = True
            previous_album = track.album
            create_album_folder(track.destination_directory)
            new_albums.append(track.album)
        else:
            new_album = False

        # This function call should create 3 files:
        #   the mp3 file, the description file, and the image file
        #   once they are downloaded, the files will have the upload date in the name.  should probably remove it after capturing it
        

        
        # This function takes the source (downloads) directory and base filename
        # It will extract the year from the upload date, rename the files with the date removed and assign the files
        # to the music, audio, and description items in the files dictionary 
        downloaded_files, year = parse_files(source_directory, track.source_video_name)
        
        if downloaded_files['image']:
            if downloaded_files['image'][-4:] == 'webp': #convert webp to jpg file
                downloaded_files['image'] = convert_to_jpg(downloaded_files['image'], downloaded_files['image'][:-5] + '.jpg')
            if new_album:
                #album_image = resize_image(downloaded_files['image'], source_directory + 'album.jpg', 1280, 1280)
                im = Image.open(downloaded_files['image'])
                im = resize_image(im, 1280, 1280)
                im.save(source_directory + "album.jpg")
                copy_file(source_directory + 'album.jpg', destination_directory  + "album.jpg", True)
                #downloaded_files['image'] = destination_directory  + "album.jpg"
            #downloaded_files['image'] = resize_image(downloaded_files['image'], source_directory + 'album.jpg', 1280, 1280)
            anchor_location = (0,1100) 
            image_dimensions = (1280, 1280)
            text_area_dimensions = (1280, 120)
            text_area = TextArea(text_area_dimensions, image_dimensions, anchor_location)
            if track.track_title[0:2] == "OB":
                im = prepare_image(downloaded_files['image'], text_area, 1280, 1280, True)
            else:
                im = prepare_image(downloaded_files['image'], text_area, 1280, 1280, False)
            draw = ImageDraw.Draw(im)
            word_strings = track.words.split(",")
            if config['font_sample']:
                fonts = get_fonts('./fonts/')
                font_name = './fonts/' + fonts[font_counter]
                font_counter = font_counter + 1
                f = ImageFont.truetype('./fonts/courbd.ttf', 96)
                draw.rectangle([(50,50), (1230,300)], fill=(0,0,0))
                draw.text((100,100), font_name, font=f, fill=(0,255,0))
            else:
                font_name = config['font_name']
            wg = WordGrid(text_area, word_strings, font_name)

            if wg:
                wg.draw_text_area(draw)
                for w in wg.words:
                    wr = w.width_rectangle()
                    mwr = w.max_width_rectangle()
                    #draw.rectangle(wr, fill=(0,0,255), outline=(0,0,255), width=2)
                    #draw.rectangle(mwr, fill=(0,255,255), outline=(0,255,255), width=2)
                wg.draw_words(draw)
                im.save('./media/working/' + track.title + '.jpg')
                downloaded_files['image'] = './media/working/' + track.title + '.jpg'
            else:
                print("Error creating WordGrid.  Check the words and try again")
                exit()
            


        else:
            print("Image not returned. Quitting")
            exit()

        extract_audio(downloaded_files['audio'], new_file, track.start_time, track.end_time)
        update_id3(new_file, track.artist, album, track.track_title, track.track_number, year, downloaded_files['image'])
        
        # need to add the moods after the plex library has been updated.  instead of updating the library for every track,
        # just add it to a list.  once the library is updated (maybe sleep to allow it to finish?), loop through this list and addMood that way
        if track.producer:
            moods.append((track.track_title, track.producer))
        
    print("Updating Plex")


    plex_update_library(plex, "Harry Mack")
    if new_albums:
        print(f"The following albums were created:  {new_albums}")

    print(f"Finished processing {len(tracks)} tracks.")
    for title, producer in moods:
        add_mood(plex, "Harry Mack", title, producer)
    