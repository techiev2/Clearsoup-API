import sys
sys.dont_write_bytecode = True

import json

from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from datetime import datetime

from requires.base import BaseHandler, authenticated
from datamodels.notification import Notification, NotificationManager
from utils.dumpers import json_dumper

class NotificationHandler(BaseHandler):

    SUPPORTED_METHODS = ('GET',)

    @authenticated
    def get(self, *args, **kwargs):
        qParams = {
            'for_user': self.current_user,
            'is_read': False
        }
        last_id = self.get_argument('last_id', None)
        if last_id:
            qParams['id__gt'] = last_id
        
        notifications = Notification.objects(**qParams)\
            .order_by('-id')[self._limit_from:self._limit_to]

        response = json_dumper(notifications)
        self.finish(json.dumps(response))

    # @authenticated
    # def post(self, *args, **kwargs):
    #     print NotificationManager.createNotification(for_user=self.current_user)
