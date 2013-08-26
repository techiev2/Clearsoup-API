'''
Created on 06-Aug-2013

@author: someshs
'''

from project.handler import ProjectHandler

URLS = [('/api/project/?$', ProjectHandler),
       ]

__all__ = ['URLS']

