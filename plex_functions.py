from plexapi.server import PlexServer

def plex_update_library(plex, library):

    harrymack = plex.library.section(library)
    harrymack.update()

def connect_to_server():
    baseurl = 'http://192.168.0.202:32400' #the local address of your server
    token = 'ao7MsVLaXxRWLtCoyXWm'
    return PlexServer(baseurl, token)
if __name__ == "__main__":
    pass