'''
Created on 07-Aug-2013

@author: someshs
'''

from story.handler import StoryHandler

URLS = [('/api/stories/?$', StoryHandler),
       ]

__all__ = ['URLS']

