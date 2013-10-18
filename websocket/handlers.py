import sys
sys.dont_write_bytecode = True

from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop, PeriodicCallback

import json
import datetime
import time

from datamodels.notification import Notification, NotificationManager
from datamodels.session import SessionManager

WEBSOCKET_REFRESH_TIMER = 30 * 1000
WEBSOCKET_PING_TIMER = 60 * 100
# Maintain a list of clients connected
CLIENTS = dict()

class AppWebSocketHandler(WebSocketHandler):
    """
    Notification websocket. This will be extended and made
    generic to handle all other messages in the future
    (for example, pushing live updates)

    One important point to keep in mind is that when the server
    receives a message, it is buffered. So on_message will be invoked
    only if the message is sufficiently large, else the messages will be
    buffered and invoked in one go. We MUST avoid this behavior when we
    want to send data from the client
    """
    def allow_draft76(self):
        return True

    def get_id(self):
        return id(self)

    def get_session_key(self):
        '''
        Returns a tuple with username, websocket_id
        '''
        token = self.get_secure_cookie("token", None)
        if token:
            session = SessionManager.loadSession(token)
            if session:
                user = session.user.username
                websocket_id = self.get_id()
                return (user, websocket_id)
            else:
                return None
        else:
            return None

    def open(self):
        '''
        Everytime a new websocket connection in initialized, store
        the handler and related data in the CLIENTS list. We need
        this because we need to send out specific updates to specific
        clients and not a broadcast
        '''
        session_key = self.get_session_key()
        if session:
            # Maintain a list of connected sockets
            # The key is a tuple (user, websocket_id)
            CLIENTS[session_key] = {
                'socket': self,
                'data': {}
            }
            print "Websocket opened: %d for user %s" % (websocket_id, user)


    def on_message(self, message):
        '''
        Everytime the client sends a message, it is received
        here. We have to make sure that the client is in the list
        to proceed further
        '''
        websocket_id = self.get_id()
        if websocket_id in CLIENTS:
            try:
                # We always expect a json encode message
                message = json.loads(message)
                message_type = message['message_type'].capitalize() \
                    if 'message_type' in message else 'Notification'
                message_type += 'Message'
                # Check if our message type has a processor
                if message_type in globals():
                    message_handler = globals()[message_type](websocket_id=websocket_id)
                    message_handler.process(self, message)
            except Exception, e:
                print e
                response = {
                    'error': True,
                    'message': str(e)
                }
                self.write_message(json.dumps(response))


    def on_close(self):
        pass
        # websocket_id = self.get_id()
        # print "Websocket closed: %d" % websocket_id
        # del CLIENTS[websocket_id]


class WebSocketMessage(object):
    def __init__(self, websocket_id):
        self._websocket_id = websocket_id

    def process(self, handler, message):
        raise NotImplementedError


class NotificationMessage(WebSocketMessage):
    def __init__(self, websocket_id):
        WebSocketMessage.__init__(self, websocket_id)
        self._type = 'notification'

    def process(self, handler, message):
        if message['action'] == 'update_last_id':
            self.update_last_id(message['last_id'])

    def update_last_id(self, last_id):
        # CLIENTS
        print 'updating id for socket %s with %d ' % (self._websocket_id, last_id)
        CLIENTS[self._websocket_id]['data']['last_id'] = last_id


def send_notifications():
    print 'sending notification'
    if notifications:
        notifications_html = self.render_string('modules/_notification.html',
            notifications=notifications)
        response = {
            'count': len(notifications),
            'notifications_html': notifications_html.strip(' \n')
        }

        self.write_message(json.dumps(response))

def ping():
    now = time.time()
    payload = json.dumps({
        'server_time': now
        })
    for key, value in CLIENTS.iteritems():
        print "pinging ", key[0]
        value['socket'].ping(payload)


# Websocket scheduler
websocket_scheduler = PeriodicCallback(send_notifications, WEBSOCKET_REFRESH_TIMER)
#websocket_scheduler.start()
ping_scheduler = PeriodicCallback(ping, WEBSOCKET_PING_TIMER)
ping_scheduler.start()
