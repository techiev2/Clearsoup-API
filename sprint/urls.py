'''
Created on 21-Aug-2013

@author: someshs
'''

from sprint.handler import SprintHandler

URLS = [
        ('/api/sprint/?$', SprintHandler),
       ]

__all__ = ['URLS']
