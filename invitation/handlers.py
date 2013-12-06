'''
Created on 06-Dec-2013

@author: someshs
'''
from datetime import datetime

from tornado.web import HTTPError

from requires.base import BaseHandler
from datamodels.team import Invitation
from utils.dumpers import json_dumper
import tornado

class InvitationHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', )
    REQUIRED_FIELDS   = {'GET': ('code',)
        }

    def get(self, *args, **kwargs):
        code = self.get_argument('code')
        invitation = None
        try:
            invitation = Invitation.objects.get(code=code,
                                        valid_until__gte=datetime.utcnow())
            self.write(json_dumper(invitation))
        except Invitation.DoesNotExist:
            raise HTTPError(404, **{'reason': "Invalid token"})
