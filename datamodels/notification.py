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
    # is, store it in from_user
    from_user = me.ReferenceField('User', required=False)
    # But who the notification is for is mandatory
    for_user = me.ReferenceField('User', required=True, dbref=True)
    text = me.StringField(max_length=500, required=False)
    is_read = me.BooleanField(default=False)


class NotificationManager:
    @staticmethod
    def createNotification(notification_type="O", for_user, from_user):
        if not mentioned_user:
            return False
        
        notification = Notification()
        notification.notification_type = notification_type[:1].upper()

        if not isinstance(for_user, User):
            try:
                for_user = User.objects.get(username=for_user)
                notification.for_user = for_user
            except pass

        notification.save()
