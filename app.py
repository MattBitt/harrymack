from flask import Flask, jsonify

from plex_functions import currently_playing
import flask_admin as admin
from flask_admin.contrib.peewee import ModelView
from models import Source, Track, Producer, Beat, Word, Tag, TrackWord, database_setup
from flask_cors import CORS, cross_origin


database_setup()

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'



class SourceAdmin(ModelView):
    # Visible columns in the list view
    # column_exclude_list = ['artist_name']

    # List of columns that can be sorted. For 'user' column, use User.email as
    # a column.
    column_sortable_list = ("video_type", "album_name", "created_date", "upload_date")

    # Full text search
    column_searchable_list = ("video_title", "album_name")

    # Column filters
    column_filters = ("video_title", "created_date", "album_name")


class TrackAdmin(ModelView):
    column_hide_backrefs = False
    column_exclude_list = ["artist_name"]
    column_sortable_list = ("track_title", "album_name", "created_date")
    column_searchable_list = ("track_title", "album_name")
    column_filters = ("track_title", "created_date", "album_name")

    # form_ajax_refs = {
    #     'user': {
    #         'fields': (User.username, 'email')
    #     }
    # }


class BeatAdmin(ModelView):
    column_sortable_list = ["beat_name"]
    column_searchable_list = ["beat_name"]
    column_filters = ["beat_name"]


class ProducerAdmin(ModelView):
    column_sortable_list = ["producer_name"]
    column_searchable_list = ["producer_name"]
    column_filters = ["producer_name"]


class TagAdmin(ModelView):
    column_sortable_list = ["tag"]
    column_searchable_list = ["tag"]
    column_filters = ["tag"]


class WordAdmin(ModelView):
    column_sortable_list = ["word"]
    column_searchable_list = ["word"]
    column_filters = ["word"]


@app.route("/")
@cross_origin()
def home():

    return """<a href="/admin/">Click me to get to Admin!</a>"""


@app.route("/api/v1/sources", methods=["GET", "POST"])
@cross_origin()
def sources_endpoint(page=1):
    # TODO: setup pagination
    query = Source.not_ignored()
    data = [i.serialize for i in query]
    return jsonify(data)


@app.route("/api/v1/sources/<int:source_id>", methods=["GET"])
@cross_origin()
def source_endpoint(source_id):
    query = Source.select().where(Source.id == source_id)
    if query:
        return jsonify(query[0].serialize)
    else:
        return {}

   
    
@app.route("/api/v1/tracks", methods=["GET", "POST"])
@cross_origin()
# @app.route('api/v1/sources/<int:page>', methods=['GET'])
def tracks_endpoint():
    query = Track.all()
    data = [i.serialize for i in query]
    return jsonify(data)


@app.route("/api/v1/tracks/<int:track_id>", methods=["GET"])
@cross_origin()
def track_endpoint(track_id):
    query = Track.select().where(Track.id == track_id)
    if query:
        return jsonify(query[0].serialize)
    else:
        return {}


@app.route("/api/v1/whatsplaying", methods=["GET"])
@cross_origin()
def whatsplaying():
    wp = currently_playing()
    print(wp)
    if wp:
        lt = wp[0]["library_type"]
    data = []

    if lt == "source":
        query = Source.select().where(
            Source.video_file == "/" + wp[0]["video_file"].lstrip("'/harrymack_")
        )
        source = query[0].serialize
        source["current_time"] = wp[0]["current_time"]
        source["library_type"] = lt
        data.append(source)
    elif lt == "track":
        query = Track.select().where(
            Track.file_path == "/" + wp[0]["video_file"].lstrip("'/harrymack_")
        )
        track = query[0].serialize
        track["current_time"] = wp[0]["current_time"]
        track["library_type"] = lt
        data.append(track)
    return jsonify(data)


@app.route("/api/v1/whatsplaying_fake_track", methods=["GET"])
def whatsplaying_fake():
    return [
        {
            "album_name": "Happy Hour Clips",
            "artist_name": "Harry Mack",
            "beat_name": "",
            "created_date": "2022-12-08",
            "current_time": 366000,
            "end_time": "00:06:21",
            "exists": "True",
            "file_path": "/tracks/Happy Hour Clips/HH Clips.2 Harry Mack x Beat Cleaver 1.mp3",
            "id": "22",
            "plex_id": "",
            "plex_rating": "0",
            "producer": "",
            "source": "434",
            "start_time": "00:00:00",
            "track_number": "1",
            "track_title": "HH Clips.2 Harry Mack x Beat Cleaver 1",
        }
    ]


admin = admin.Admin(app, name="ESCUCHARR")
admin.add_view(SourceAdmin(Source))
admin.add_view(TrackAdmin(Track))
admin.add_view(WordAdmin(Word))
admin.add_view(TagAdmin(Tag))
admin.add_view(BeatAdmin(Beat))
admin.add_view(ProducerAdmin(Producer))
app.run(debug=False, host="0.0.0.0", port=5959)
