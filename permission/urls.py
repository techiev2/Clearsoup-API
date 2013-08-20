'''
Created on 16-Aug-2013

@author: someshs
'''
from permission.handler import PermissionHandler

URLS = [('/api/permission/?$', PermissionHandler),
       ]

__all__ = ['URLS']