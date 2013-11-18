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
            'U': ('text', 'created_by', 'created_at', 'pk')
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
        project = QueryObject(self, 'Project', {
            'permalink__iexact': "%s/%s" % (
                self.path_kwargs.get('user'),
                self.path_kwargs.get('project')),
            'admin||members__contains': self.current_user
        })
        meta = {
            'order_by': 'created_at'
        }
        response_data = {}
        project = project.result[0] if project.count == 1 else None
        if not project:
            self.response = {
                'status_code': 404,
                'custom_msg': 'Invalid project scope'
            }
            self.view.as_json()
            return
        query = self.path_kwargs.get('query')
        is_sequence_search = True if sequence_search_matcher.match(
            query.upper()) else False
        response_data = {}
        count = 0

        if is_sequence_search:
            model = 'Task' if query[0].lower() == 't' else 'Story' \
                if query[0].lower() == 's' else 'Update'
            query = {'sequence': int(query[1:]), 'project': project}
            query.update({'is_active': True})
            sequence_search = QueryObject(self, model, query, meta)

            count += sequence_search.count
            response_key = 'tasks' if model == 'Task' else 'stories'
            model_key = 'T' if model == 'Task' else 'S'
            response = {response_key: sequence_search.json(
                fields=self.fields.get(model_key))} if \
                not sequence_search.exception else {}
            response_data.update(response)

        # Search in Task/Story titles
        else:
            models = ('Task', 'Story')
            query = {
                'title__icontains': self.path_kwargs.get('query'),
                'project': project
            }
            for model in models:
                title_search = QueryObject(self, model, query, meta)

                count += title_search.count
                response_key = 'tasks' if model == 'Task' else 'stories'
                model_key = 'T' if model == 'Task' else 'S'
                response = {response_key: title_search.json(
                    fields=self.fields.get(model_key))} if \
                    not title_search.exception else {}
                response_data.update(response)

        # Fetch updates irrespective of sequence search True/False
        model = 'Update'
        update_query = {'hashtags__icontains': self.path_kwargs.get(
            'query').lower(), 'project': project}
        update_search = QueryObject(self, model, update_query, meta)
        count += update_search.count

        response = {'updates': [obj.to_json(fields=('id', 'text',
            'created_by', 'created_at',)) for obj in
            update_search.result]} if not\
            update_search.exception else {}

        # response = {'updates': update_search.json(
        #                        fields=self.fields.get('U')) if \
        #                        update_search.result else []}

        response_data.update(response)
        response_data.update({'count': count})

        self.response = {
            'status_code': 200 if response_data else 404,
            'data': response_data or None
        }
        self.view.render()
