import sys
sys.dont_write_bytecode = True

from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from datetime import datetime

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