'''
Created on 06-Aug-2013

@author: someshs
'''

from profile.handler import ProfileHandler

URLS = [('/api/profile/?$', ProfileHandler),
       ]

__all__ = ['URLS']

