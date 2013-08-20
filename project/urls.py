'''
Created on 06-Aug-2013

@author: someshs
'''

from project.handler import ProjectHandler, UpdateHandler

URLS = [('/api/project/(?P<project>.*?)/updates/?$', UpdateHandler),
		('/api/project/?$', ProjectHandler),
       ]

__all__ = ['URLS']

