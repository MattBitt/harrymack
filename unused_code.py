# * these functions return booleans depending on what needs to be done (download, audio processing)
# download_file = download_source_file(dr, config["overwrite_download"])
# ffmpeg_process = process_with_ffmpeg(dr, config["overwrite_destination"])

#     if download_file:
#         downloaded = youtube_download(dr, config)
#         if not downloaded:
#             logger.error(
#                 "Error downloading clip {}. Skipping to next track", dr.url
#             )
#             continue

#     if ffmpeg_process:
#         pass

#     if dr.album != previous_album:
#         # * This clip is part of a different album than the previous.
#         # * if there was a previous album should i delete it?  probably not.
#         # * should wait until the end and delete everthing in the downloads folder
#         # ? should i check for files in downloads folder on start?  give warning?
#         # ? Create the folder /musicroot/album
#         # ? Take the album image and resize it to 1280x1280.  Make a copy called 'album.jpg'.  move to /musicroot/album folder
#         new_album = True
#         previous_album = track.album
#         create_album_folder(track.destination_directory)
#         new_albums.append(track.album)
#     else:
#         new_album = False

#     # * This function call should create 3 files:
#     #   * the mp3 file, the description file, and the image file
#     #   * once they are downloaded, the files will have the upload date in the name.  should probably remove it after capturing it

#     # * This function takes the source (downloads) directory and base filename
#     # * It will extract the year from the upload date, rename the files with the date removed and assign the files
#     # * to the music, audio, and description items in the files dictionary
#     downloaded_files, year = parse_files(source_directory, track.source_video_name)

#     if downloaded_files["image"]:
#         if downloaded_files["image"][-4:] == "webp":  # convert webp to jpg file
#             downloaded_files["image"] = convert_to_jpg(
#                 downloaded_files["image"], downloaded_files["image"][:-5] + ".jpg"
#             )
#         if new_album:
#             # album_image = resize_image(downloaded_files['image'], source_directory + 'album.jpg', 1280, 1280)
#             im = Image.open(downloaded_files["image"])
#             im = resize_image(im, 1280, 1280)
#             im.save(source_directory + "album.jpg")
#             copy_file(
#                 source_directory + "album.jpg",
#                 destination_directory + "album.jpg",
#                 True,
#             )
#             # downloaded_files['image'] = destination_directory  + "album.jpg"
#         # downloaded_files['image'] = resize_image(downloaded_files['image'], source_directory + 'album.jpg', 1280, 1280)
#         anchor_location = (0, 1100)
#         image_dimensions = (1280, 1280)
#         text_area_dimensions = (1280, 120)
#         text_area = TextArea(
#             text_area_dimensions, image_dimensions, anchor_location
#         )
#         if track.track_title[0:2] == "OB":
#             im = prepare_image(
#                 downloaded_files["image"], text_area, 1280, 1280, True
#             )
#         else:
#             im = prepare_image(
#                 downloaded_files["image"], text_area, 1280, 1280, False
#             )
#         draw = ImageDraw.Draw(im)
#         word_strings = track.words.split(",")
#         if config["font_sample"]:
#             fonts = get_fonts("./fonts/")
#             font_name = "./fonts/" + fonts[font_counter]
#             font_counter = font_counter + 1
#             f = ImageFont.truetype("./fonts/courbd.ttf", 96)
#             draw.rectangle([(50, 50), (1230, 300)], fill=(0, 0, 0))
#             draw.text((100, 100), font_name, font=f, fill=(0, 255, 0))
#         else:
#             font_name = config["font_name"]
#         wg = WordGrid(text_area, word_strings, font_name)

#         if wg:
#             wg.draw_text_area(draw)
#             for w in wg.words:
#                 wr = w.width_rectangle()
#                 mwr = w.max_width_rectangle()
#                 # draw.rectangle(wr, fill=(0,0,255), outline=(0,0,255), width=2)
#                 # draw.rectangle(mwr, fill=(0,255,255), outline=(0,255,255), width=2)
#             wg.draw_words(draw)
#             im.save("./media/working/" + track.title + ".jpg")
#             downloaded_files["image"] = "./media/working/" + track.title + ".jpg"
#         else:
#             print("Error creating WordGrid.  Check the words and try again")
#             exit()
#     else:
#         print("Image not returned. Quitting")
#         exit()
#     extract_audio(
#         downloaded_files["audio"], new_file, track.start_time, track.end_time
#     )
#     update_id3(
#         new_file,
#         track.artist,
#         album,
#         track.track_title,
#         track.track_number,
#         year,
#         downloaded_files["image"],
#     )

#     # * need to add the moods after the plex library has been updated.  instead of updating the library for every track,
#     # * just add it to a list.  once the library is updated (maybe sleep to allow it to finish?), loop through this list and addMood that way
#     if track.producer:
#         moods.append((track.track_title, track.producer))

# print("Updating Plex")
# plex_update_library(plex, "Harry Mack")
# if new_albums:
#     print(f"The following albums were created:  {new_albums}")

# print(f"Finished processing {len(tracks)} tracks.")
# for title, producer in moods:
#     add_mood(plex, "Harry Mack", title, producer)


# existing_tracks = len(
#    tracks.select().where(tracks.album_name == track.source.album_name)
# )
# track.track_number = existing_tracks + 1
# track.save()


# *setup connection to plex
# plex = connect_to_server()
# font_counter = 0

# ! Try setting it up like this
# ! sources = import_sources_to_db() (should actually create album as well)
# ! tracks = import_tracks_to_db()
# ! albums = get_albums()
# ! for each album:
# !     album.create_tacks()

# ! album.create_tracks()
# !     if split_by_silence:
# !          do that
# !     else:
# !         tracks = select tracks where album = self
# !         for each track in tracks
# !             if track doesn't exist
# !                 track.create()
# !
# ! return list of tracks
# !

# ****************************************************************************************
# Checking YouTube to get all of the videos added to the channel
