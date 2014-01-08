# coding=utf-8
"""
Clearsoup SuperAdmin app
Provides basic analytics about users/projects
"""
import sys
sys.dont_write_bytecode = True

from itertools import groupby
from requires.base import BaseHandler, superuser
from utils.dumpers import json_dumper
from datamodels.user import User
from datamodels.project import Project
from datamodels.session import Session


class AdminHandler(BaseHandler, object):
    """
    Returns a list of Projects and Users
    """

    SUPPORTED_METHODS = ('GET',)

    def __init__(self, *args, **kwargs):
        """Admin view handler init"""
        super(AdminHandler, self).__init__(*args, **kwargs)

    @superuser
    def get(self, *args, **kwargs):
        """HTTP GET request handler method for Admin view"""
        users = User.objects.only("username", "email")
        unique_sessions = {}
        sessions = Session.objects(user__in=users).order_by("generated_at")
        # we now have to group the sessions by username,
        for username, sess in groupby(
                sessions, lambda x: x['user']['username']):
            unique_sessions[username] = list(sess)[-1].to_json()

        projects = Project.objects.only(
            "title", "permalink", "description", "members"
        )
        self.write({
            'users': json_dumper(users, fields=['username', 'email']),
            'sessions': unique_sessions,
            'projects': json_dumper(
                projects,
                fields=["title", "permalink", "description", "members"]
            )
        })
