'''
Created on 16-Aug-2013

@author: someshs
'''

from team.handler import TeamHandler

URLS = [('/api/team/?$', TeamHandler),
       ]

__all__ = ['URLS']

