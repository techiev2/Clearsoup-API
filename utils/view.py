# coding=utf-8
"""Base view for Clearsoup API"""
__author__ = "Sriram Velamur"

import sys
sys.dont_write_bytecode = True
import logging
import json

__all__ = ('BaseView',)

view_logger = logging.getLogger(__name__)

RESPONSE_HEADERS = {
    'json': 'application/json charset=utf-8',
    'xml': 'text/xml; charset=utf-8'
}


class BaseView(object):
    """Base view class for Clearsoup API"""
    def __init__(self, controller=None):
        """
        Base view class init.
        :param controller: Controller instance to update response
        data
        :type controller: tornado.web.RequestHandler
        :returns: None
        :rtype: None
        """
        self.controller = controller if hasattr(
            controller, '_headers_written') else None
        if not self.controller:
            #setattr(self.controller, 'response', {
            #    'status_code': 500,
            #    'custom_msg': 'Server error'
            #})
            raise BaseException("Invalid controller instance "
                                "provided")
        setattr(self.controller, 'view', self)

    def render(self, response_format='json', data=None):
        """
        View render method. Calls the appropriate render method
        depending on the format the Controller requests.
        :param response_format: Data format for response. Defaults
        to json string
        :type response_format: str
        """
        data = data or {}
        self.controller.response = data if data and data != {} else \
            self.controller.response
        response_format = response_format if isinstance(
            response_format, str) else 'json'

        # Set controller response headers. Default to
        # application/json
        self.controller.set_header('Content_type',
                                   RESPONSE_HEADERS.get(
                                       response_format,
                                       'application/json'))

        # Get a custom renderer method if defined for the format
        # else default to json renderer
        format_method = 'as_%s' % response_format
        format_method = getattr(self, format_method,
                                getattr(self, 'as_json'))
        format_method = format_method if hasattr(
            format_method, '__call__') else getattr(self, 'as_json')
        format_method.__call__()

    def as_json(self):
        """
        Render controller response as JSON string.
        """
        # Validate controller response for serialization
        try:
            self.controller.response = json.loads(json.dumps(self
            .controller.response))
        except (TypeError, ValueError):
            self.controller.response = {
                'status_code': 500,
                'custom_msg': 'Server error'
            }

        self.controller.write(self.controller.response)
