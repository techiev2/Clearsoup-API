'''
Created on 23-Aug-2013

@author: someshs
'''

from update.handler import UpdateHandler

URLS = [('/api/project/(?P<project>.*?)/updates/?$', UpdateHandler),
       ]

__all__ = ['URLS']
