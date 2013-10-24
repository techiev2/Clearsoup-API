# coding=utf-8
"""Object wrapper utilities"""
from __future__ import absolute_import
__author__ = 'Sriram Velamur'

import sys
sys.dont_write_bytecode = True
from mongoengine import (LookUpError, InvalidQueryError)
import logging

obj_logger = logging.getLogger(__name__)

__all__ = ('QueryObject',)


class QueryObject(object):
    """Queryobject wrapper class"""

    def __init__(self, controller=None, model=None, query=None,
                 meta=None):
        """Query object wrapper class init"""
        if not isinstance(model, str):
            raise BaseException("QueryObject requires a valid model "
                                "name string")
        self.model_name = model

        # Invalidate controller values that are not
        # tornado.web.RequestHandler instances
        # todo: Checks for other framework controller instances
        self.controller = controller if \
            hasattr(controller, '_headers_written') else None

        self.query = query if isinstance(query, dict) else {}
        self.meta = meta if isinstance(meta, dict) else {}
        self.model, self.exception, self.result = None, None, []

        # Import specified model and prepare for querying
        self._fetch_model()

        self.result = self.model.objects.filter(**self.query) if \
            self.model else self.result

        if self.meta and self.result:
            for (key, val) in self.meta.iteritems():
                if hasattr(self.result, key) and \
                        hasattr(getattr(self.result, key), '__call__'):
                    self.result = getattr(self.result, key).__call__(val)

        if self.count == 0:
            self.exception = {
                'status_code': 404,
                'custom_msg': "No object found"
            }

    @property
    def count(self):
        """Resultset count property"""
        return 0 if not self.result else self.result.count()

    def _fetch_model(self):
        """
        Model fetcher helper method.
        Imports the specified model passed to QueryObject init.
        If a controller instance is present checks for models in the
        individual applications or from a models package
        specified as a application settings key.
        """
        _models_package, _models_pack_import, _model = None, None, \
                                                      None
        if self.controller:
            _models_package = self.controller.settings.get(
                'models_package')

        try:
            _models_pack_import = __import__(_models_package) if \
                _models_package else None
            self.model = getattr(_models_pack_import, self.model_name)
        except ImportError:
            obj_logger.warn("Unable to import the specified model")
            self.exception = {
                'status_code': 500,
                'custom_msg': ''
            }

    def json(self, fields=None, exclude=None, ref_fields=None):
        """
        JSON dumper for QueryObject result set. Works with a json
        dumper method if the model defines one else defaults to a
        custom json dumper method from package.
        :param fields: Fields to include in JSON dict dump
        :type fields: tuple/list
        :param exclude: Fields to exclude in JSON dict dump
        :type exclude: tuple/list
        :param ref_fields: Fields to include in case of DBRef fields
        :type ref_fields: dict
        :returns: JSON representation of result set or exception dict
        :rtype: dict/list
        """
        # todo: JSON dumper normalization between ORM choices

        if self.exception:
            return self.exception

        fields = fields if isinstance(fields, (list, tuple)) else ()
        exclude = fields if isinstance(exclude, (list, tuple)) else ()

        ref_fields = ref_fields if isinstance(ref_fields, dict) \
            else {}

        # Convert result set to JSON list by calling a to_json
        # method in field object.
        # Generate reference field data using exclude/fields data
        # from ref_fields dict param.
        data = []
        for item in self.result or []:
            item_dict = {}
            for field in (field for field in fields if field not \
                in exclude):
                item_data = getattr(item, field)
                item_data = item_data if not hasattr(
                    item_data, 'to_mongo') else item_data.to_json(
                    fields=ref_fields.get(field,
                        {}).get('fields', ()),
                    exclude=ref_fields.get(field,
                        {}).get('exclude', ()))

                item_dict.update({field: item_data})

            data.append(item_dict)

        return data

    def delete(self, **kwargs):
        """Object instance delete wrapper"""
        if self.result and hasattr(self.result, 'delete') \
            and hasattr(self.result.delete, '__call__'):
            try:
                if self.controller:
                    user = getattr(self.controller, 'user')
                    # if not user:
                    #     return {
                    #         'status_code': 401
                    #     }
                    self.result.delete()
                    return_val = {
                        'status_code': 204
                    }
                else:
                    self.result.delete()
                    return_val = {
                        'status_code': 204
                    }
            except Exception, e:
                return_val = {
                    'status_code': 202,
                    'message': '{0} object deletion failed'.format(
                                                   self.model_name)
                }
        else:
            return_val = {
                'status_code': 404
            }
        if reduce(lambda x, y: x and y, [
                    hasattr(self.controller, x) for x in ['ui', 'request']]):
            setattr(self.controller, 'response', return_val)
            return_val = None
        return return_val

    def update(self, update_data):
        """Update object instance wrapper for QueryObject"""
        if update_data and self.result:
            # if not getattr(self.controller, 'user'):
            #     self.response = {'status_code': 401}
            #     return
            try:
                query_data = update_data
                update_kwargs = {'set__%s' % key: val for
                                 key, val in update_data.iteritems()}
                self.result.update(**update_kwargs)
                self.result = QueryObject(
                    self.controller, self.model_name,
                    query=query_data).result

            except LookUpError, l_e:
                self.result = None
                self.exception = {
                    'status_code': 500,
                    'custom_msg': l_e.message
                }
            except InvalidQueryError, iq_e:
                self.result = None
                self.exception = {
                    'status_code': 422,
                    'custom_msg': iq_e.message[0].replace(
                                    "Cannot resolve field",
                                    "Invalid field").replace('"', '')
                }
            except Exception, exc:
                self.result = None
                self.exception = {
                    'status_code': 500,
                    'custom_msg': exc.message
                }

        if reduce(lambda x, y: x and y, [
                hasattr(self.controller, x) for x in ['ui', 'request']]):
            setattr(self.controller, 'response', self.json())