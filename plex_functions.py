from plexapi.server import PlexServer


def plex_update_library(plex, library):

    harrymack = plex.library.section(library)
    harrymack.update()


def connect_to_server():
    baseurl = "http://192.168.0.202:32400"  # the local address of your server
    token = "ao7MsVLaXxRWLtCoyXWm"
    return PlexServer(baseurl, token)


def get_playlists(plex):
    for playlist in plex.playlists():
        print(playlist.title)


def search_tracks(plex, library, track_title):
    lib = plex.library.section(library)
    t = lib.searchTracks(title=track_title)
    return t


def add_mood(plex, library, track_title, mood):
    t = search_tracks(plex, library, track_title)
    if len(t) < 1:
        print(f"Track {track_title} not found.  {t}")
        return False
    elif len(t) > 1:
        print(f"Too many matches found for {track_title}.  {t}")
        return False
    else:
        t[0].addMood(mood)
        return True


def currently_playing():
    plex = connect_to_server()
    sess = plex.sessions()
    libraries = ["Harry Mack Sources", "Harry Mack Tracks"]
    if len(sess) > 0:
        for s in sess:
            if s.librarySectionTitle in libraries:
                data = {
                    "title": s.title,
                    "library": s.librarySectionTitle,
                    "current_time": s.viewOffset,
                }
                return data
    else:
        return {}


if __name__ == "__main__":
    # plex = connect_to_server()
    # get_playlists(plex)
    # lib = plex.library.section("Harry Mack")
    print(currently_playing())
    # for track in lib.all():
    # print(album.tracks()[0].media[0].parts[0].file)
    #    print(track)

    # availableFields = [f.key.split('.')[-1] for f in lib.listFields()]
    # print("Available fields:", availableFields)
    # print(len(lib.searchTracks()))
    # print(lib.searchTracks(title="BTB11.1 Intro"))
#    search_tracks(plex, "Harry Mack", "BTB11.1 Intro")
