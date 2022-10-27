# def download_playlists():
#     pass


# if __name__ == "__main__":
#     pass

import json
import yt_dlp
import sys

# Define default path
path = r"media/downloads/"
ydl_opts = None
# Define download rate limit in byte
ratelimit = 5000000

# Define download format
# format = "--extract-audio --write-description --audio-format mp3 --audio-quality 0 --write-thumbnail"
format = "best[ext=mp4]"

# Get url as argument


# Download all videos of a channel
def get_options(url):
    if url.startswith(
        (
            "https://www.youtube.com/c/",
            "https://www.youtube.com/channel/",
            "https://www.youtube.com/user/",
        )
    ):
        return {
            "ignoreerrors": True,
            "abort_on_unavailable_fragments": True,
            "format": format,
            "outtmpl": path
            # + "\\Channels\%(uploader)s\%(title)s ## %(uploader)s ## %(id)s.%(ext)s",
            # "ratelimit": ratelimit,
        }

    # Download all videos in a playlist
    elif url.startswith("https://www.youtube.com/playlist"):
        return {
            "ignoreerrors": True,
            "abort_on_unavailable_fragments": True,
            "format": format,
            "outtmpl": path + "%(id)s (%(upload_date)s).%(ext)s",
            "ratelimit": ratelimit,
        }

    # Download single video from url
    elif url.startswith(
        (
            "https://www.youtube.com/watch",
            "https://www.twitch.tv/",
            "https://clips.twitch.tv/",
        )
    ):
        return {
            "ignoreerrors": True,
            "abort_on_unavailable_fragments": True,
            "format": format
            # "outtmpl": path + "\\Videos\%(title)s ## %(uploader)s ## %(id)s.%(ext)s",
            # "ratelimit": ratelimit,
        }


# Downloads depending on the options set above
def get_json_info(url):
    ydl_opts = get_options(url)
    if ydl_opts is not None:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        # my_file = open("json_data.json", "w")
        # my_file.write(json.dumps(ydl.sanitize_info(info), indent=4, sort_keys=True))
        # json_dict = info
        # print(list(json_dict.keys()))
        # print(info["id"])
        # print(info["duration"])  # video length in seconds
        # print(info["upload_date"])
        # print(info["title"])
        return info
    else:
        raise KeyError


if __name__ == "__main__":
    try:
        url = sys.argv[1]
        print(get_json_info(url))
    except IndexError:
        sys.exit("Usage: python thisfile.py URL")
