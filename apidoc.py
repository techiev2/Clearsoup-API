# coding=utf-8
"""API endpoints lister"""
__author__ = "Sriram Velamur"
import sys
sys.dont_write_bytecode = True

from pprint import pprint
import json
from requires import SETTINGS

end_points = {}

DEFAULT_METHODS = ('GET', 'PUT', 'POST', 'DELETE')
DEFAULT_FIELDS = {
    'GET': (),
    'POST': (),
    'PUT': (),
    'DELETE': ()
}


def get_end_points():
    """Generate end points JSON data"""
    apps = SETTINGS.get('APPS', ())
    for app in apps:
        app_data = []
        app_name, app = app, __import__(app)
        urls = getattr(getattr(app, 'urls'), 'URLS')
        for url in urls:
            data = {
                'methods': getattr(url[1],
                    'SUPPORTED_METHODS', DEFAULT_METHODS),
                'required_fields': getattr(url[1],
                    'REQUIRED_FIELDS', DEFAULT_FIELDS),
                'url': url[0].rstrip("$?")
            }
            app_data.append(data)
        end_points[app_name] = app_data

    return end_points


if __name__ == "__main__":
    with open("api_docs.json", "w") as apifile:
        apifile.write(json.dumps(get_end_points()))
