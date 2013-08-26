'''
Created on 23-Aug-2013

@author: someshs
'''
from task.handler import TaskHandler

URLS = [('/api/project/?$', TaskHandler),
       ]

__all__ = ['URLS']


