import subprocess
import csv
import os
from datetime import datetime
import eyed3
import shutil
from PIL import Image



def youtube_download(url, location, output_name, extension):
    # output name should not have ".ext"
    audio_format = "bestaudio"

    filename = location + output_name + '.' + extension
    if not(os.path.exists(filename)):
        yt_dl = subprocess.run(["yt-dlp", 
        '--no-warnings',
        '--extract-audio', 
        '--audio-format',
        extension,
        '--audio-quality',
        '0',
        "-o", 
        filename,
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

def extract_audio(location, input_file, output_file, extension, start_time, end_time):
    input_filename = location + input_file + '.' + extension
    output_filename = location + output_file + '.' + extension
    """ffmpeg -i ./downloads/37duQAUSYXo.mp4 -ss 00:00:20 -to 00:00:40 -c copy ./downloads/file-2.mkv"""
    ffmpeg = subprocess.run(['ffmpeg', 
    '-i', 
    input_filename, 
    '-ss', 
    start_time, 
    '-to', 
    end_time,
    output_filename])

    if ffmpeg.returncode:
        print("FFMPEG returned: %d" % ffmpeg.returncode)
        exit()
def update_id3(location, inputfile, extension, artist, album, title, track_num):
    
    audiofile = eyed3.load(location + inputfile + '.' + extension)
    audiofile.tag.artist = artist
    audiofile.tag.album = album
    audiofile.tag.album_artist = artist
    audiofile.tag.title = title
    audiofile.tag.track_num = track_num
    #Need to convert image to jpg before embedding
    #'file.tag.images.set(3, imagedata , "image/jpeg" ,u"Description")

    #Need to add the year as well.  Should be able to get from yt-dlp.
    audiofile.tag.save()

def create_album_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def move_file(source_location, filename, extension, destination):
    source_file = source_location + filename + '.' + extension
    destination_file = destination + filename + '.' + extension
    shutil.move(source_file, destination_file)

def fix_image(location, filename, audio_extension, img_extension):
    image = location + filename + '.' + audio_extension + '.' + img_extension
    if not os.path.exists(image):
        image = location + filename + '.' + img_extension
        if not os.path.exists(image):
            image = location + filename + '.jpg'
            if not os.path.exists(image):
                print("Image File not found!")
                exit()

    img = Image.open(image)
    new_img = img.resize((1280,1280))
    new_img.save(location + "album.jpg", "JPEG", optimize=True)





IMPORT_CSV = "HarryMackClips.csv"
EXTENSION = "mp3"


now = datetime.now()
dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
print("\n\n\nStarting Program: ", dt_string)


# This will set the final destination for the audio files.  Separated due to developing on windows vs production on unraid
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



if os.path.exists(IMPORT_CSV):
    clips = import_csv(IMPORT_CSV)
else:
    print("No CSV file found.  Please check the path and try again.")
    exit()

album = None
new_album = False
for clip in clips:
    if not clip['AlbumName'] == album:
        new_album = True
        album = clip['AlbumName']
        dest_directory = music_root + album + '/'
        create_album_folder(dest_directory)
    else:
        album = clip['AlbumName']

    youtube_download(clip['URL'], './downloads/', clip['WholeName'], EXTENSION)
    if new_album:
        fix_image('./downloads/', clip['WholeName'], EXTENSION, 'webp')
        move_file('./downloads/', 'album', 'jpg', dest_directory)
    filename = clip['TrackNumber'] + " - " + clip['Title']
    extract_audio('./downloads/', clip['WholeName'], filename, EXTENSION, clip['StartTime'], clip['EndTime'])
    update_id3('./downloads/', filename, EXTENSION, clip['ArtistName'], clip['AlbumName'], clip['Title'], clip['TrackNumber'])
    
    move_file('./downloads/', filename, EXTENSION, dest_directory)
    



#CSV file will be a list of each "song" to be created (e.g. OB 45.3 - Hunger).  There can/will be multiple songs for each url.  Need to only download once though
# folder structure
# harrymack
#   Omegle Bars
#   
#           101 - florescent adolescence, rainbow, weatherspoons, , 
#           102 - cats, shoes, football, , 
#           103 - clowns, guitars, roast me, , 
#           104 - pussy, antidisestablishmentarianism, wall, , 
#           105 - wake up early, smoke a joint, hard work in the kitchen, smoke a joint, 
#           201 - covid, sports, comedy, , 
#           202 - huskies, iced coffee, bucket hats, , 
#           203 - sheep, Playstation, bottle, , 
#   Guerilla Bars
#   Wordplay Wednesdays (if this is just clips, probably shouldn't assign order.  should i put the video number/time stamp in the title though?)
#   Misc (same as above, no order)
#       Harry Mack w/ Beet Cleaver 
#       Barbarian

#
#Check for CSV file to process
# if it exists
    #open file
    #read into list of dicts
    #close file
    # for each in list
        # if new url <> previous url
            # download url
            
        # else
            # use existing file
        # extract time clip from downloaded file (new name in csv)
        # update id3 tags
        # insert thumbnail (may need to convert)
        # create folder if needed on server
        # move to final place in server
            # 
# else
    # exit
