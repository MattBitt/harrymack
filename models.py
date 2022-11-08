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
    ModelSelect,
)
from datetime import datetime

database = SqliteDatabase("harry_mack.db")


class BaseModel(Model):
    @classmethod
    def all(cls):
        result = cls.select()
        return result

    class Meta:
        database = database


# class Album(BaseModel):
#     id = AutoField()
#     album_name = CharField()
#     album_artist = CharField()
#     split_by_silence = BooleanField()


class Source(BaseModel):
    # album = ForeignKeyField(Album, backref="sources")
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

    @classmethod
    def not_ignored(cls):
        result = cls.select().where(cls.ignore.is_null(False))
        return result

    @classmethod
    def get_split_by_silence(cls):
        result = cls.select().where(cls.split_by_silence == 1)
        return result

    @classmethod
    def do_not_exist(cls) -> ModelSelect:
        result = cls.select().where(cls.audio_exists == 0, cls.ignore == False)
        return result


class Track(BaseModel):
    artist_name = CharField()
    album_name = CharField(null=True)
    exists = BooleanField()
    beat_name = CharField()
    created_date = DateField()
    end_time = TimeField()
    file_path = CharField(null=True)
    id = AutoField(primary_key=True)
    plex_id = CharField()
    plex_rating = IntegerField()
    producer = CharField()
    source = ForeignKeyField(Source, backref="tracks")

    start_time = TimeField()  # should these be stored as ms and converted as needed?
    track_number = IntegerField(null=True)
    track_title = CharField()
    words = CharField()

    @classmethod
    def do_not_exist(cls) -> ModelSelect:
        result = cls.select().where(cls.exists == 0)
        return result

    @classmethod
    def with_album(cls, album: str) -> ModelSelect:
        result = cls.select().where(cls.album_name == album)
        return result


def database_setup():
    database.connect()
    database.create_tables([Source, Track])


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
