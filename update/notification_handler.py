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

    def get(self, *args, **kwargs):
        '''
        Notifications can be fetch in bulk by the websocket
        so that we need to make multiple API calls for every
        user. In that case, we expect a multiple params with the
        key user and the value as user_id, last_notification_id
        Ex: /notification/?user=1,613434&user=2,8980978907&user=3,707093
        We will then fetch the notifications for each user, and respond
        '''
        response = {}
        users = self.get_arguments('user', None)
        '''
        If we have multiple users, loop through the list, and fetch
        the notifications for each user
        '''
        if users:
            qParams = {
                'is_read': False
            }
            for user in users:
                if ',' in user:
                    user_id, last_notification_id = user.split(',')
                    qParams['for_user'] = user_id
                    qParams['id__gt'] = last_notification_id
                else:
                    qParams['for_user'] = user

                user_notification = Notification.objects(**qParams)\
                    .order_by('-id')
                response[qParams['for_user']] = json_dumper(user_notification)

        elif self.current_user:
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

    @authenticated
    def post(self, *args, **kwargs):
        '''
        Update all unread notifications as read for the current user
        '''
        is_success = NotificationManager.markAsRead(self.current_user)
        self.write({
            'is_success': is_success
            })
