'''
Created on 06-Aug-2013

@author: someshs
'''

from profile.handler import ProfileHandler, ResetPasswordHandler

URLS = [
    ('/api/profile/?$', ProfileHandler),
    (r'^/api/reset-password/?$', ResetPasswordHandler),
    (r'^/api/reset-password/(?P<token>.*?)/?$', ResetPasswordHandler)
]

__all__ = ['URLS']

