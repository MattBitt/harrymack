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
    fn,
)
from datetime import datetime

# from track import Track

database = SqliteDatabase("harry_mack.db", pragmas={"foreign_keys": 1})


class BaseModel(Model):
    @classmethod
    def all(cls):
        result = cls.select()
        return result

    class Meta:
        database = database


class ManyToMany(BaseModel):
    @classmethod
    def add_x_to_track(cls, track, field: str, field_str: str):

        match field:
            case "word":
                model = Word
            case "tag":
                model = Tag
            case _:
                model = None
        if model:
            new_record = model.add(field_str)
        match field:
            case "word":
                cls.create(track=track, word=new_record)
            case "tag":
                cls.create(track=track, tag=new_record)
            case _:
                model = None

            # if not cls.track_has_tag(track, field, field_str):

            # print(f"Adding {tag_str} to {track.track_title}")
            # else:
            #    print("This track already has this word")

    @classmethod
    def remove_tag_from_track(cls, track, field: str, tag_str: str):
        tag = Tag.get(tag=tag_str)
        if tag:
            cls.delete().where(cls.track == track.id, cls.tag == tag.id).execute()
        else:
            print(f"Tag {tag_str} is not associated with this track")

    @classmethod
    def track_has_x(cls, track, tag):
        track_tag = cls.select().where(cls.track == track.id, cls.tag == tag.id)
        if track_tag:
            return True
        else:
            return False


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
    video_exists = BooleanField(null=True)
    video_file = CharField(null=True)
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
        result = cls.select().where(cls.audio_exists == 0, cls.ignore == 0)  # ignore
        return result

    @classmethod
    def with_video_type(cls, video_type: str) -> ModelSelect:
        result = cls.select().where(cls.video_type == video_type)
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

    @classmethod
    def do_not_exist(cls) -> ModelSelect:
        result = cls.select().where(cls.exists == 0)
        return result

    @classmethod
    def with_album(cls, album: str) -> ModelSelect:
        result = cls.select().where(cls.album_name == album)
        return result


class Word(BaseModel):
    id = AutoField(primary_key=True)
    word = CharField()

    @classmethod
    def get(cls, word) -> ModelSelect:
        result = cls.select().where(cls.word.contains(word))
        return result

    @classmethod
    def add(cls, word):
        existing_word = cls.get(word)
        if existing_word:
            # print("word is already in db, skipping")
            return existing_word[0]
        else:
            result = cls.create(word=word)
            return result


class Tag(BaseModel):
    id = AutoField(primary_key=True)
    tag = CharField()

    @classmethod
    def add(cls, tag):
        existing_tag = cls.select().where(cls.tag == tag)
        if existing_tag:
            # print("word is already in db, skipping")
            return existing_tag[0]
        else:
            result = cls.create(tag=tag)
            return result


class TrackTag(ManyToMany):
    id = AutoField(primary_key=True)
    track = ForeignKeyField(Track)
    tag = ForeignKeyField(Tag)


class TrackWord(ManyToMany):
    id = AutoField(primary_key=True)
    track = ForeignKeyField(Track)
    word = ForeignKeyField(Word)

    # @classmethod
    # def add_word_to_track(cls, track: Track, word_str: str):
    #     word = Word.add(word_str)
    #     if not TrackWord.track_has_word(track, word):
    #         TrackWord.create(track=track, word=word)
    #         print(f"Adding {word_str} to {track.track_title}")
    #     else:
    #         print("This track already has this word")

    # @classmethod
    # def remove_word_from_track(cls, track: Track, word_str: str):
    #     word = Word.get(word=word_str)
    #     if word:
    #         cls.delete().where(cls.track == track.id, cls.word == word[0].id).execute()
    #     else:
    #         print("Word is not associated with this track")

    # @classmethod
    # def track_has_word(cls, track: Track, word: Word):
    #     track_word = cls.select().where(
    #         TrackWord.track == track.id, TrackWord.word == word.id
    #     )
    #     if track_word:
    #         return True
    #     else:
    #         return False


def database_setup():

    database.connect()
    database.create_tables([Source, Track, Word, Tag, TrackTag, TrackWord])


def find_words(string):
    s = string.split(",")
    words = []
    for word in s:
        if word[:3] == "OB ":
            word = word[3:]
        if word[:10] == "Unreleased":
            word = word[10:]
        i = 0
        for char in word:
            if char.isalpha():
                word = word[i:]
                break
            else:
                i = i + 1
        words.append(word)
    return words


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
    database_setup()
    # source = Source.create(
    #     title="Source Title",
    #     upload_date="",
    #     video_type=data_row["ClipTypes"],
    #     url=data_row["URL"],
    #     video_name=data_row["WholeName"],
    #     words=data_row["PrimaryWords"],
    #     episode_number=data_row["EpisodeNumber"],
    #     audio_file="",
    #     image_file="",
    #     description_file="",
    #     created_date=datetime.now(),
    #     audio_exists=False,
    #     album_name=data_row["AlbumName"],
    #     split_by_silence=False,
    # )
    # track = Track.create(
    #     start_time=data_row[
    #         "StartTime"
    #     ],  # should these be stored as ms and converted as needed?
    #     end_time=data_row["EndTime"],
    #     filename=data_row["Filename"],
    #     track_title=data_row["Title"],
    #     track_number=data_row["TrackNumber"],
    #     beat_name=data_row["BeatName"],
    #     producer=data_row["Producer"],
    #     artist_name=data_row["ArtistName"],
    #     created_date=datetime.now(),
    #     audio_exists=False,
    #     source=source,
    #     plex_id=15,
    #     plex_rating=5,
    # )

    # query = Track.select().join(Source).where(Source.id == "NPdKxsSE5JQ")
    # for track in source.tracks:
    #     print(track.track_title)

    # words = [
    #     "orange",
    #     "pinapple",
    #     "artist",
    #     "supercali",
    #     "anitdis",
    #     "hat",
    #     "bat",
    #     "cat",
    # ]
    # for word in words:
    #     Word.create(word=word)

    # word = Word.get("orange")[0].id

    # track = Track.select().where(
    #     Track.track_title == "OB 12.1 Orange, Fruit, Apples, Keyboard"
    # )
    # print(track[0].id)

    # TrackWord.create(word=word, track=track)

    # track = Track.select().where(Track.id == 210)
    # TrackWord.add_word_to_track(track=track[0], word_str="cat food")
    # TrackWord.remove_word_from_track(track=track[0], word_str="cat food")
    # TrackWord.add_word_to_track(track=track[0], word_str="Matthew Bittingerasdf")

    # TrackWord.create(word=word, track=track)

    # print(word.tracks)
    # print(Word.add("orange"))
    # print(Word.add("asdf"))

    # for track in tracks:

    #     if track.source.video_type == "Omegle Bars":
    #         for word in find_words(track.track_title):

    #             TrackWord.add_word_to_track(track, word.lower())
    # words = Word.all()
    # words_with_counts = []
    # for word in words:
    #     x = TrackWord.select(fn.COUNT(TrackWord.id)).where(TrackWord.word == word.id)
    #     words_with_counts.append({"word": word.word, "count": x.count()})
    # n = sorted(words_with_counts, key=lambda d: d["count"], reverse=True)
    # for word_count in n:
    #     print(f"{word_count['word']},{str(word_count['count'])}")
