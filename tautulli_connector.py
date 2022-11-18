import requests
import os
from requests.exceptions import HTTPError
from utils import ms_to_hhmmss
# demo showing the requests library.  delete when up and running




def get_current_playing_time(progress_percent: str, duration: str):
    curr_time = int(progress_percent) / 100 * int(duration)
    return ms_to_hhmmss(curr_time)

class TautulliConnector:
    def __init__(self, url, api_key):
        self.url = url + "/api/v2?apikey=" + api_key + "&cmd="
    def get_activity(self):
        response = self.tautulli_request("get_activity")
        sessions = response.json()["response"]["data"]["sessions"]
        for session in sessions:
            if session["library_name"] == "Harry Mack":
                progress_percent = session["progress_percent"]
                duration = session["duration"]
                print(get_current_playing_time(progress_percent, duration))

    def tautulli_request(self, cmd: str):
    # example connection url
    # http://192.168.0.202:8181/api/v2?apikey=XXXXXXXXXXXXXXXXXX&cmd=server_status
        url = self.url + cmd
        return requests.get(url)

if __name__ == "__main__":
    url = os.environ.get("TAUTULLIURL")
    api_key = os.environ.get("TAUTULLIAPI")
    # connect_to_tautulli(tautulli_url,  tautulli_api_key)
    taut = TautulliConnector(url, api_key)
    taut.get_activity()
    