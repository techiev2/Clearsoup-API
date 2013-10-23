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
        BaseView(self)
        self.ref_fields = {
            'created_by': {
                'fields': ('username',)
            }
        }
        self.fields = ('sequence', 'created_by', 'title')
        self.models = {
            'T': 'Task',
            'S': 'Story'
        }

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

        project = QueryObject(self, 'Project', {
            'title__iexact': self.path_kwargs.get('project')})

        if not project.result or len(project.result) != 1:
            self.response = {
                'status_code': 404,
                'custom_msg': 'Invalid project'
            }
            self.view.as_json()

        project = project.result[0]

        model = self.models.get(query[0], 'Update') if \
            is_sequence_search else self.models.values()

        query = {'sequence': query[1:]} if \
            is_sequence_search and query[0] in \
            ('T', 'S',) else {'title__icontains': query}

        query.update({'project__iexact': project})

        if isinstance(model, str):
            q = QueryObject(self, model, query=query,
                            meta=meta)
            response_data = []

            fields = self.fields + ('task_type',) if \
                model == 'Task' else self.fields

            json_response = q.json(fields=fields,
                                   ref_fields=self.ref_fields)
            for idx, item in enumerate(q.result):
                item_json = json_response[idx]
                meta_query = {
                    'hashtags__icontains': '%s%s' % (
                        model[0].lower(), item.sequence)
                }
                item_updates = QueryObject(self, 'Update',
                                           meta_query)
                item_json.update({
                    'updates': item_updates.json(
                        fields=('text',),
                        ref_fields=self.ref_fields),
                    'type': model[0].upper()
                })
                response_data.append(item_json)

        else:
            response_data = []
            for model_item in model:
                q = QueryObject(self, model_item, query=query,
                            meta=meta)
                fields = self.fields + ('task_type',) if \
                    model_item == 'Task' else self.fields

                json_response = q.json(fields=fields,
                                       ref_fields=self.ref_fields)
                for idx, item in enumerate(q.result):
                    item_json = json_response[idx]
                    meta_query = {
                        'hashtags__icontains': '%s%s' % (
                            model_item[0].lower(), item.sequence)
                    }
                    item_updates = QueryObject(self, 'Update',
                                               meta_query)
                    item_json.update({
                        'updates': item_updates.json(
                            fields=('text',),
                            ref_fields=self.ref_fields),
                        'type': model_item[0].upper()
                    })
                    response_data.append(item_json)

        self.response = {
            'status_code': 200 if response_data else 404,
            'data': response_data or None
        }
        self.view.render()
