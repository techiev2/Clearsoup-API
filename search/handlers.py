# coding=utf-8
"""Search app for Clearsoup API"""
__author__ = "Sriram Velamur"

import sys
sys.dont_write_bytecode = True
#from tornado.web import RequestHandler
from utils.object import QueryObject
from requires.base import BaseHandler, authenticated
from utils.view import BaseView
import logging
import re

search_logger = logging.getLogger(__name__)
sequence_search_matcher = re.compile('[S|T]\d+')

__all__ = ('SearchController',)


class SearchController(BaseHandler):
    """Search view controller"""

    def __init__(self, *args, **kwargs):
        """
        Search view controller class init.
        """
        super(SearchController, self).__init__(*args, **kwargs)
        self.ref_fields = {
            'created_by': {
                'fields': ('username',)
            }
        }
        self.fields = {
            'T': ('sequence', 'created_by', 'title', 'task_type'),
            'S': ('sequence', 'created_by', 'title', 'priority'),
            'U': ('text', 'created_by', 'id', 'created_at')
        }
        self.models = {
            'T': 'Task',
            'S': 'Story',
            'U': 'Update'
        }
        self.response = None
        BaseView(self)

    @authenticated
    def get(self, **kwargs):
        """
        HTTP GET request handler method for Clearsoup API search
        end point
        :param kwargs: Keyword dictionary to fetch user, project,
        search terms
        :type kwargs: dict
        .. http:get:: /api/<username>/<project>/search/<query>
            Retrieve stories/tasks matching the query string. Works with
            Story/Task sequence/titles

            :param username: Session user name
            :type username: str

            :param project: Project name for scoping
            :type project: str

            :param query: Search query for title/sequence search
            :type query: str
            # Query needs to be prefixed with 'T' or 'S' for
            performing sequence search
        """
        meta = {
            'order_by': 'created_at'
        }

        query = self.path_kwargs.get('query')

        is_sequence_search = True if sequence_search_matcher.match(
            query) else False

        models = self.models.iteritems()
        response_data = {}

        count = 0

        project = QueryObject(self, 'Project', {
            'permalink__iexact': "%s/%s" % (
                self.path_kwargs.get('user'),
                self.path_kwargs.get('project')),
            'admin||members__contains': self.current_user
        })

        project = project.result[0] if project.count == 1 else None
        if not project:
            self.response = {
                'status_code': 404,
                'custom_msg': 'Invalid project scope'
            }
            self.view.as_json()
            return

        for model_key, model_name in models:
            query_data = self.path_kwargs.get('query')
            query = {'sequence': query_data.strip('S').strip('T')} \
                if is_sequence_search else {
                    'title__icontains': query_data} if \
                model_key in ('S', 'T') else \
                {
                    'hashtags__icontains':
                    query_data.lstrip('#').lower()
                }
            query.update({'project': project})
            q = QueryObject(self, model_name, query)
            count += q.count

            response_key = 'stories' if model_key == 'S' else \
                'tasks' if model_key == 'T' else 'updates'

            if response_key:
                if response_key in ('tasks',):
                    tasks_data = []
                    for item in q.result:
                        item_json = item.to_json(
                            fields=self.fields.get(model_key)) if \
                            not q.exception else {}
                        item_updates = QueryObject(
                            self, 'TaskUpdate', {
                                'task': item
                            })
                        if not item_updates.exception:
                            item_json.update(
                                {'updates': [x.to_json() for x in
                                             item_updates.result]})
                        else:
                            item_json.update({
                                'updates': []
                            })

                        tasks_data.append(item_json)

                    response = {response_key: tasks_data}

                else:
                    response = {response_key: q.json(
                        fields=self.fields.get(model_key))} \
                        if not q.exception else {}
            response_data.update(response)

        response_data.update({'count': count})

        self.response = {
            'status_code': 200 if response_data else 404,
            'data': response_data or None
        }
        self.view.render()
