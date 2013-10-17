import sys
sys.dont_write_bytecode = True

import mongoengine as me
from datetime import datetime
from utils.dumpers import json_dumper

from user import User

# Mention, Invite, Automated, Other
# This will be useful to render custom notification templates
# in the future
NOTIFICATION_TYPES = ['M','I','A','O']

class Notification(me.Document):
    # Meta
    created_at = me.DateTimeField(default=datetime.utcnow())

    # Fields
    notification_type = me.StringField(choices=NOTIFICATION_TYPES, required=True)
    # A notification need not be initiated by anyone, but if it
    # is, store it in from_user (as in mentions)
    from_user = me.ReferenceField('User', required=False, dbref=True)
    # But who the notification is for is mandatory
    for_user = me.ReferenceField('User', required=True)
    text = me.StringField(max_length=500, required=False)
    is_read = me.BooleanField(default=False)

    def __str__(self):
        return "Type: %s for user %s" %(self.notification_type, self.for_user.username)


class NotificationManager:
    @staticmethod
    def createNotification(for_user, from_user=None, notification_type="O", text=None):
        if not for_user:
            return False

        notification = Notification()
        notification.notification_type = notification_type[:1].upper()
        notification.text = text

        if not isinstance(for_user, User):
            try:
                for_user = User.objects.get(username=for_user)
            except User.DoesNotExist:
                raise me.ValidationError('Notification cannot be created if user is unknown')

        notification.for_user = for_user
        notification.from_user = from_user
        try:
            notification.save()
            return notification
        except:
            return None

    @staticmethod
    def fetchNotificationForUser(user):
        if not user:
            return None

        notifications = Notification.objects(
            for_user=user,
            is_read=False
            ).order_by('-id')

        return notifications

    @staticmethod
    def markAsRead(user):
        try:
            Notification.objects(for_user=user, is_read=False).update(set__is_read=True)
            return True
        except:
            return False
