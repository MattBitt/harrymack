import os
print(os.getcwd())

from flask import Flask, jsonify

from plex_functions import currently_playing
import flask_admin as admin
from flask_admin.contrib.peewee import ModelView
from models import Source, Track

app = Flask(__name__)

class SourceAdmin(ModelView):
    # Visible columns in the list view
    # column_exclude_list = ['artist_name']

    # List of columns that can be sorted. For 'user' column, use User.email as
    # a column.
    column_sortable_list = ('video_type', 'album_name', 'created_date', 'upload_date')

    # Full text search
    column_searchable_list = ('video_title', 'album_name')

    # Column filters
    column_filters = ('video_title',
                      'created_date',
                      'album_name')


class TrackAdmin(ModelView):
    # Visible columns in the list view
    column_exclude_list = ['artist_name']

    # List of columns that can be sorted. For 'user' column, use User.email as
    # a column.
    column_sortable_list = ('track_title', 'album_name', 'created_date')

    # Full text search
    column_searchable_list = ('track_title', 'album_name')

    # Column filters
    column_filters = ('track_title',
                      'created_date',
                      'album_name')

    # form_ajax_refs = {
    #     'user': {
    #         'fields': (User.username, 'email')
    #     }
    # }

@app.route("/")
def home():
    return '<a href="/admin/">Click me to get to Admin!</a>'


@app.route("/api/v1/sources", methods=["GET", "POST"])
@app.route('/api/v1/sources/<int:page>', methods=['GET'])
def sources_endpoint(page=1):
    # TODO: setup pagination
    query = Source.not_ignored()
    data = [i.serialize for i in query]
    return jsonify(data)

@app.route("/api/v1/source/<int:source_id>", methods=["GET"])
def source_endpoint(source_id):
    query = Source.select().where(Source.id == source_id)
    if query:
        return jsonify(query[0].serialize)
    else:
        return {}

@app.route("/api/v1/tracks", methods=["GET", "POST"])
# @app.route('api/v1/sources/<int:page>', methods=['GET'])
def tracks_endpoint():
    query = Track.all()
    data = [i.serialize for i in query]
    return jsonify(data)

@app.route("/api/v1/track/<int:track_id>", methods=["GET"])
def track_endpoint(track_id):
    query = Track.select().where(Track.id == track_id)
    if query:
        return jsonify(query[0].serialize)
    else:
        return {}


@app.route("/api/v1/whatsplaying", methods=["GET"])
def whatsplaying():
    return jsonify(currently_playing())

admin = admin.Admin(app, name='ESCUCHARR!!!')
admin.add_view(SourceAdmin(Source))
admin.add_view(TrackAdmin(Track))
app.run(debug=True, host='0.0.0.0')
