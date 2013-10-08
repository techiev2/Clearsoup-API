'''
Created on 23-Aug-2013

@author: someshs
'''
from task.handler import TaskHandler, TaskCommentHandler

URLS = [('/api/task/?$', TaskHandler),
        ('/api/task-comment/?$', TaskCommentHandler)
       ]

__all__ = ['URLS']


