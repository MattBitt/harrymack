from typing import List
from track import Track


class Albums:
    def __init__(self):
        pass

    def stats(self):
        pass

    def new(self):
        pass

    def all(self):
        pass


class Album:
    def __init__(self, album_name: str, album_artist: str, split_by_silence: bool):
        self.album_name = album_name
        self.album_artist = album_artist
        self.split_by_silence = split_by_silence
        self.num_tracks = 0
        self.tracks = []

    def add_track(self, track):
        pass

    def load_album_track_info(self) -> List[Track]:
        pass
