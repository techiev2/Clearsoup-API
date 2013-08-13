"""
Created on February 22 2013

@author: sriramm

URL map for core app.
"""

from core.handlers import Main

URLS = [('/$', Main)]

__all__ = ['URLS']


if __name__ == '__main__':
    pass
