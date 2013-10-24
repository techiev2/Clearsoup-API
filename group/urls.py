'''
Created on 23-Oct-2013

@author: someshs
'''
from group.handler import GroupHandler

URLS = [('/api/group/?$', GroupHandler),
       ]

__all__ = ['URLS']