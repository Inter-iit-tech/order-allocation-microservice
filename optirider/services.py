from django.conf import settings
from requests import Session
from urllib.parse import urljoin, quote
import numpy as np


class LiveServerSession(Session):
    def __init__(self, prefix_url):
        self.prefix_url = prefix_url
        super(LiveServerSession, self).__init__()

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)
        return super(LiveServerSession, self).request(method, url, *args, **kwargs)


def table_request_path(points):
    coord_string = ";".join([f"{pnt.coords[0]},{pnt.coords[1]}" for pnt in points])
    req_path = urljoin("/table/v1/driving/", quote(coord_string, safe=""))
    return req_path


def fetch_distance_matrix(points):
    req_path = table_request_path(points)
    with LiveServerSession(prefix_url=settings.OSRM_SETTINGS["BASE_URL"]) as s:
        r = s.get(req_path)
        adj_matrix = np.rint(np.array(r.json()["durations"])).astype(int).tolist()
    return adj_matrix
