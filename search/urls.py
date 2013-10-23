# coding=utf-8
"""Search app urlmap for Clearsoup API"""
__author__ = "Sriram Velamur"

import sys
sys.dont_write_bytecode = True
from .handlers import SearchController

__all__ = ('URLS',)

url_str = '.*/api/(?P<user>[a-zA-Z0-9].*)/'
url_str += '(?P<project>[a-zA-Z0-9\_\-].*)'
url_str += '/search/(?P<query>.*?)/$'

#URLS = [('^/api/(?P<user>.*?)/(?P<project>.*?)/search/(?P<query>.*?)/$',
#         SearchController)]

URLS = [(url_str, SearchController)]