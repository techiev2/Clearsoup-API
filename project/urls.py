'''
Created on 06-Aug-2013

@author: someshs
'''

from project.handler import ProjectHandler, ProjectSettingHandler

URLS = [('/api/project/?$', ProjectHandler),
        ('/api/setting/?$', ProjectSettingHandler),
        
        
       ]

__all__ = ['URLS']

