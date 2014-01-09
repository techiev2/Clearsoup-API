import sys
sys.dont_write_bytecode = True

from tornado.websocket import WebSocketHandler
from tornado.ioloop import PeriodicCallback
import json
import time

from datamodels.notification import NotificationManager
from datamodels.session import SessionManager

WEBSOCKET_REFRESH_TIMER = 30 * 1000
WEBSOCKET_PING_TIMER = 60 * 1000
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

    def get_current_user(self):
        token = self.get_secure_cookie("token", None)
        if token:
            session = SessionManager.loadSession(token)
            if session:
                user = session.user.username
                return user

        return None

    def open(self):
        '''
        Everytime a new websocket connection in initialized, store
        the handler and related data in the CLIENTS list. We need
        this because we need to send out specific updates to specific
        clients and not a broadcast
        '''
        user = self.current_user
        if user:
            websocket_id = self.get_id()
            # Maintain a list of connected sockets
            # The key is a tuple (user, websocket_id)
            CLIENTS[(user, websocket_id)] = {
                'socket': self,
                'data': {}
            }
            #print "User %s connected to websocket" % user
            # Start ping scheduler if not running
            if not ping_scheduler._running and CLIENTS:
                ping_scheduler.start()

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
                    message_handler = globals()[message_type](
                        websocket_id=websocket_id)
                    message_handler.process(self, message)
            except Exception, e:
                #print e
                response = {
                    'error': True,
                    'message': str(e)
                }
                self.write_message(json.dumps(response))

    def on_close(self):
        websocket_id = self.get_id()
        # CLIENTS = {k:v for k,v in CLIENTS.iteritems() if k[1] != 1}
        # Get the key with the websocket_id
        key = [k for k in CLIENTS.iterkeys() if k[1] == websocket_id]
        if key:
            #print key[0]
            del CLIENTS[key[0]]
            #print "User %s disconnected from websocket" % key[0][0]
        # If no clients, disable scheduler
        if ping_scheduler._running and not CLIENTS:
            ping_scheduler.stop()


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
        if message['action'] == 'markAsRead':
            is_success = NotificationManager.markAsRead(self.current_user)
            response = {
                'is_success': is_success
            }
            self.write_message(json.dumps(response))

    def update_last_id(self, last_id):
        # CLIENTS
        CLIENTS[self._websocket_id]['data']['last_id'] = last_id


def send_notifications(notifications):
    print 'sending notification'
    # We are bothered only about sending the notifications
    # for the users that are active in the websocket
    for key, value in CLIENTS.iteritems():
        if key[0] in notifications:
            socket = value['socket']
            try:
                notification_html = socket.render_string(
                    '_notification.html',
                    notification=notifications[key[0]])
                response = {
                    'message_type': 'notification',
                    'notifications_html': notification_html.strip(' \n')
                }
                socket.write_message(json.dumps(response))
            except Exception, e:
                print e


def ping():
    now = time.time()
    payload = json.dumps({
        'server_time': now
    })
    for key, value in CLIENTS.iteritems():
        #print "pinging ", key[0]
        value['socket'].ping(payload)


# Websocket scheduler
# websocket_scheduler = PeriodicCallback(
#    send_notifications, WEBSOCKET_REFRESH_TIMER)
# websocket_scheduler.start()
ping_scheduler = PeriodicCallback(ping, WEBSOCKET_PING_TIMER)
ping_scheduler.start()
