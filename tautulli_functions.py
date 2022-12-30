from tautulli import RawAPI
import os

tt = os.environ.get("TAUTULLITOKEN")
# if tt:
# api = RawAPI(base_url="http://www.google.com", api_key=tt, verbose=True)
api = RawAPI(base_url="http://192.168.0.202:8181", api_key=tt)
