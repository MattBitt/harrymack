from email.mime import image
from platform import java_ver
import subprocess
import csv
import os
from datetime import datetime
import eyed3
from eyed3.core import Date
import shutil
from PIL import Image
import glob




def youtube_download(url, filename):
    # output name should not have ".ext"
    filename = filename[:-4]
    if not(os.path.exists(filename)):
        yt_dl = subprocess.run(["yt-dlp", 
        '--no-warnings',
        '--extract-audio', 
        #'--write-info-json',  # this works but not sure if i need to use it.  contains upload date and description but probably pretty hard to extract
        '--write-description',
        '--audio-format',
        'mp3',
        '--audio-quality',
        '0',
        "-o", 
        filename + " (%(upload_date)s).mp3",
        "--write-thumbnail", 
        url])
        if yt_dl.returncode:
            print("There was an error processing %d" % yt_dl.returncode )
            return False
    return True

def import_csv(csv_name):

    with open(csv_name, "r") as f:
        csv_reader = csv.DictReader(f)
        name_records = list(csv_reader)
    return name_records

def extract_audio(source, destination, start_time, end_time):
    """ffmpeg -i ./downloads/37duQAUSYXo.mp4 -ss 00:00:20 -to 00:00:40 -c copy ./downloads/file-2.mkv"""
    ffmpeg = subprocess.run(['ffmpeg', 
    '-y',
    '-i', 
    source, 
    '-ss', 
    start_time, 
    '-to', 
    end_time,
    destination])

    if ffmpeg.returncode:
        print("FFMPEG returned: %d" % ffmpeg.returncode)
        exit()


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
        os.makedirs(path)

def move_file(source, destination):
    if os.path.exists(destination):
        os.remove(destination)
    shutil.move(source, destination)

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
            if len(file_list) == 1:
                files[t] =  file_list[0]
            if len(file_list) > 1:
                print(f"More than 1 file found matching the {pattern}\n{file_list}")
            
    
    year = get_year(files['audio'])
    return files, year

def convert_to_jpg(source, destination):
    img = Image.open(source)
    img.save(destination, optimize=True)
    return destination

def resize_image(source, destination, width, height):
    img = Image.open(source)
    new_img = img.resize((width,height))
    new_img.save(destination, optimize=True)
    return destination

def get_year(file):
    start = file.find('(')
    return int(file[start + 1:start + 5])



IMPORT_CSV = "HarryMackClips.csv"
EXTENSION = "mp3"
VERSION = "v1.0.0"
# Log Line for program staring
now = datetime.now()
dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
print(f"\n\n\nStarting Program ({VERSION}): {dt_string})")


# This will set the final destination for the audio files.  Separated due to developing on windows vs production on unraid
# ./musicroot will be used on 'Windows' for development.  
# /music/ will be the Docker volume used on the server
music_roots = ['/music/', './musicroot/']
music_root = None
for mr in music_roots:
    if os.path.exists(mr):
        music_root = mr
if not music_root:
    print("No music root directory found.  Please check the paths and try again.")
    exit()
else:
    print(f"Music root directory = {music_root}")


# Check to make sure a CSV file is available.  The Excel macro should create CSV files in the "Windows" folder as well as the Unraid folder
if os.path.exists(IMPORT_CSV):
    clips = import_csv(IMPORT_CSV)
else:
    print("No CSV file found.  Please check the path and try again.")
    exit()


album = None
previous_album = None
new_album = False

# Loop through each clip in the CSV
for clip in clips:

    base_name = clip['WholeName'] # NPdKxsSE5JQ
    artist = clip['ArtistName'] # Harry Mack
    album = clip['AlbumName'] # Omegle Bars 1
    track_number = clip['TrackNumber'] # 1
    track_title = clip['Title'] # OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons
    filename = track_number + " - " + track_title + '.mp3' # 1 - OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons
    start_time = clip['StartTime']
    end_time = clip['EndTime']
    url = clip['URL']
    
    album_image = ""
    source_directory = './downloads/'
    destination_directory = music_root + album + '/' # /music/
    source_file = source_directory + base_name + '.' + EXTENSION # ./downloads/NPdKxsSE5JQ (20200826).mp3


    if album != previous_album:
        # This clip is part of a different album than the previous.  
        # if there was a previous album should i delete it?  probably not.  should wait until the end and delete everthing in the downloads folder
        # should i check for files in downloads folder on start?  give warning?
        # Create the folder /musicroot/album
        # Take the album image and resize it to 1280x1280.  Make a copy called 'album.jpg'.  move to /musicroot/album folder
        new_album = True
        previous_album = album
        create_album_folder(destination_directory)
    else:
        new_album = False

    # This function call should create 3 files:
    #   the mp3 file, the description file, and the image file
    #   once they are downloaded, the files will have the upload date in the name.  should probably remove it after capturing it
    
    downloaded = youtube_download(url, source_file)
    if not downloaded:
        print("Error downloading clip")
        exit()
    
    # This function takes the source (downloads) directory and base filename
    # It will extract the year from the upload date, rename the files with the date removed and assign the files
    # to the music, audio, and description items in the files dictionary 
    downloaded_files, year = parse_files(source_directory, base_name)
    
    if downloaded_files['image']:
        if downloaded_files['image'][-4:] == 'webp': #convert webp to jpg file
            downloaded_files['image'] = convert_to_jpg(downloaded_files['image'], downloaded_files['image'][:-5] + '.jpg')
        downloaded_files['image'] = resize_image(downloaded_files['image'], source_directory + 'album.jpg', 1280, 1280)
        if new_album:
            #album_image = resize_image(downloaded_files['image'], source_directory + 'album.jpg', 1280, 1280)
            move_file(downloaded_files['image'], destination_directory  + "album.jpg")
            downloaded_files['image'] = destination_directory  + "album.jpg"
        
    else:
        print("Image not returned")
        exit()

    new_file = destination_directory + filename


    extract_audio(downloaded_files['audio'], new_file, start_time, end_time)
    update_id3(new_file, artist, album, track_title, track_number, year, downloaded_files['image'])
    