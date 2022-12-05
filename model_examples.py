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


database = SqliteDatabase("testing.db", pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = database


class ManyToManyModel(BaseModel):
    @classmethod
    def add_x_to_track(cls, track, key, value):
        model, query = cls.is_existing(key, value)
        if model:
            if query:  # word already exists
                return query[0]
            else:
                result = model.add(value)
                cls.add(track, result)
                return result

    @classmethod
    def add(cls, track, result):
        pass

    @classmethod
    def is_existing(cls, key, value):
        match key:
            case "word":
                model = B
                field = model.word
                query = model.select().where(field == value)
            case "tag":
                model = C
                query = model.get(tag=value)
            case "beat":
                model = D
                query = model.get(beat=value)
            case _:
                print("model not recognized")
                model = None
                query = None
        return model, query


class F(BaseModel):  # Source object
    id = AutoField()
    url = CharField()


class B(BaseModel):  # Word object
    id = AutoField()
    word = CharField()

    @classmethod
    def add(cls, val):
        result = cls.create(word=val)
        return result


class C(BaseModel):  # Tag object
    id = AutoField()
    tag = CharField()

    @classmethod
    def add(cls, val):
        result = cls.create(tag=val)
        return result


class E(BaseModel):  # Producer object
    id = AutoField()
    producer = CharField()


class D(BaseModel):  # Beat object
    id = AutoField()
    beat_title = CharField()
    producer = ForeignKeyField(E, backref="beats")

    @classmethod
    def add(cls, val):
        result = cls.create(beat_title=val)
        return result


class A(BaseModel):  # Track object
    id = AutoField()
    track_title = CharField()
    # source = ForeignKeyField(F, backref="tracks")
    # beat = ForeignKeyField(D, backref="tracks")


class AB(ManyToManyModel):  # TrackWord Table
    id = AutoField(primary_key=True)
    track = ForeignKeyField(A)
    word = ForeignKeyField(B)


def database_setup():
    database.connect()
    database.create_tables([A, B, C, D, E, F, AB])


def get_model(key: str):
    match key:
        case "word":
            model = B
        case "tag":
            model = C
        case "beat":
            model = D
        case _:
            print("model not recognized")
            model = None
    return model


if __name__ == "__main__":
    database_setup()

    sources = ["http://www.google.com", "http://www.yahoo.com", "http://www.msn.com"]

    tracks = ["Track #1", "Track #2", "Track #3", "Track #4", "Track #5", "Track #6"]

    words = ["orange", "banana", "hat", "cat", "bat", "catastrophe"]

    tags = ["monotone", "nonsense bars", "rhyme scheme", "dope"]

    beats = ["beat #1", "beat #2", "beat #3", "beat #4"]

    producers = ["Homage", "thatkidGoran", "Darkside", "Anabolic Beats"]

    for url in sources:
        F.create(url=url)

    for track_title in tracks:
        A.create(track_title=track_title)

    track = A.get(A.id == 1)
    track_word = AB
    track_word.add_x_to_track(track, "word", "orange")
    track_word.add_x_to_track(track, "word", "asdf")
    track_word.add_x_to_track(track, "word", "banana")

    for tag in tags:
        C.create(tag=tag)

    for beat in beats:
        D.create(beat_title=beat)

    for producer in producers:
        E.create(producer=producer)
