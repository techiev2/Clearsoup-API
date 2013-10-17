'''
Created on 23-Aug-2013

@author: someshs
'''

from update.handler import UpdateHandler
from update.notification_handler import NotificationHandler

URLS = [('/api/project/updates/?$', UpdateHandler),
		('/api/notification/?$', NotificationHandler),
       ]

__all__ = ['URLS']
