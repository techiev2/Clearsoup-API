'''
Created on 06-Dec-2013

@author: someshs
'''

from invitation.handlers import InvitationHandler

URLS = [
    ('/api/invitation/?$', InvitationHandler),
]

__all__ = ['URLS']
