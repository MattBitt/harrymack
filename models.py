from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    DateField,
    TimeField,
    TimestampField,
    IntegerField,
    BooleanField,
    ForeignKeyField,
    AutoField,
)
from datetime import datetime

database = SqliteDatabase("harry_mack.db")


class BaseModel(Model):
    class Meta:
        database = database


class Source(BaseModel):
    album_name = CharField()
    audio_exists = BooleanField()
    audio_file = CharField()
    created_date = DateField()
    description_file = CharField()
    episode_number = CharField()
    id = AutoField()
    ignore = BooleanField(null=True)
    image_file = CharField()
    split_by_silence = BooleanField()
    video_title = CharField()
    upload_date = DateField()
    url = CharField()
    youtube_id = CharField()
    video_type = CharField()


class Album(BaseModel):
    id = AutoField()
    album_name = CharField()
    album_artist = CharField()


class Track(BaseModel):
    artist_name = CharField()
    exists = BooleanField()
    beat_name = CharField()
    created_date = TimestampField()
    end_time = TimeField()
    filename = CharField()
    id = AutoField()
    plex_id = CharField()
    plex_rating = IntegerField()
    producer = CharField()
    source = ForeignKeyField(Source, backref="tracks")
    album = ForeignKeyField(Album, backref="tracks")
    start_time = TimeField()  # should these be stored as ms and converted as needed?
    track_number = IntegerField()
    track_title = CharField()
    words = CharField()


def database_setup():
    database.connect()
    database.create_tables([Source, Track, Album])


if __name__ == "__main__":
    data_row = {
        "ClipTypes": "OmegleBarsClips",
        "EpisodeNumber": "1",
        "TrackNumber": "1",
        "StartTime": "00:00:55",
        "EndTime": "00:04:32",
        "PrimaryWords": "Florescent Adolescence, Rainbow, Wetherspoons",
        "ArtistName": "Harry Mack",
        "URL": "https://www.youtube.com/watch?v=TuXo1fC9UKY",
        "AlbumName": "Omegle Bars 1",
        "Title": "OB 1.51 Florescent Adolescence, Rainbow, Wetherspoonsasdf",
        "Filename": "1 - OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons",
        "WholeName": "NPdKxsSE5JQasdf",
        "BeatName": "Test Beatname",
        "Producer": "Homage",
    }
    database.connect()
    database.create_tables([Source, Track])
    source = Source.create(
        title="Source Title",
        upload_date="",
        video_type=data_row["ClipTypes"],
        url=data_row["URL"],
        video_name=data_row["WholeName"],
        words=data_row["PrimaryWords"],
        episode_number=data_row["EpisodeNumber"],
        audio_file="",
        image_file="",
        description_file="",
        created_date=datetime.now(),
        audio_exists=False,
        album_name=data_row["AlbumName"],
        split_by_silence=False,
    )
    track = Track.create(
        start_time=data_row[
            "StartTime"
        ],  # should these be stored as ms and converted as needed?
        end_time=data_row["EndTime"],
        filename=data_row["Filename"],
        track_title=data_row["Title"],
        track_number=data_row["TrackNumber"],
        beat_name=data_row["BeatName"],
        producer=data_row["Producer"],
        artist_name=data_row["ArtistName"],
        created_date=datetime.now(),
        audio_exists=False,
        source=source,
        plex_id=15,
        plex_rating=5,
    )

    # query = Track.select().join(Source).where(Source.id == "NPdKxsSE5JQ")
    for track in source.tracks:
        print(track.track_title)
