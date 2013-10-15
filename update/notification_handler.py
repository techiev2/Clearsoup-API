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

    SUPPORTED_METHODS = ('GET','POST',)

    @authenticated
    def get(self, *args, **kwargs):
        notifications = Notification.objects(
            for_user=self.current_user,
            is_read=False
            ).order_by('-id')[self._limit_from:self._limit_to]

        response = json_dumper(notifications)
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        print NotificationManager.createNotification(for_user=self.current_user)


class NotificationWebSocket(WebSocketHandler):
    def open(self):
        print "WebSocket opened"
        # Once the websocket connection is open, we need
        # to continuously push stuff
        IOLoop.current().add_timeout(datetime.timedelta(seconds=5), self.test)

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print "WebSocket closed"

    def test(self):
    	print 'testing'