# coding=utf-8
"""Object wrapper utilities"""
from __future__ import absolute_import
__author__ = 'Sriram Velamur'

import sys
sys.dont_write_bytecode = True
from mongoengine import (LookUpError, InvalidQueryError,
                         ValidationError, NotUniqueError)
import logging
import operator
from mongoengine.queryset import Q
from re import findall

obj_logger = logging.getLogger(__name__)

__all__ = ('QueryObject', 'CreateObject',)


class QueryObject(object):
    """Queryobject wrapper class"""

    def __init__(self, controller=None, model=None, query=None,
                 meta=None, testing=False):
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

        self.result = self.model.objects if self.model \
            else self.result

        try:
            and_or_keys = {key: val for key, val in query.iteritems()
                       if key.count('||') > 0 or key.count('&')}
            reg_keys = {key: val for key, val in query.iteritems()
                       if key not in and_or_keys.iterkeys()}
            for key, val in and_or_keys.iteritems():
                if key.count('||') > 0:
                    keys = [Q(**{skey.strip(): val}) for skey in key\
                        .split('||')]
                    self.result = self.result.filter(
                        reduce(operator.or_, keys))
                if key.count('&') > 0:
                    keys = [Q(**{skey.strip(): val}) for skey in key\
                        .split('&')]
                    self.result = self.result.filter(
                        reduce(operator.and_ , keys))
            self.result = self.result.filter(**reg_keys)

            if self.meta and self.result:
                    for (key, val) in self.meta.iteritems():
                        if hasattr(self.result, key) and \
                                hasattr(getattr(self.result,
                                                key), '__call__'):
                            self.result = getattr(
                                self.result, key).__call__(val)

            if self.count == 0:
                self.exception = {
                    'status_code': 404,
                    'custom_msg': "No object found"
                }

        except Exception, b_e:
            logging.log(9001, "Base Exception: %s" % b_e.message)
            self.result = None
            if 'duplicate' in b_e.message:
                self.exception = {
                    'status_code': 500,
                    'custom_msg': 'Duplicate entity'
                }
            elif 'Cannot resolve' in b_e.message:
                self.exception = {
                    'status_code': 500,
                    'custom_msg': 'Invalid query'
                }
            else:
                self.exception = {
                    'status_code': 500,
                    'custom_msg': str(b_e.message)
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
        _models_package, _models_pack_import = None, None
        #_model = None

        if self.controller:
            _models_package = self.controller.settings.get(
                'models_package')

        try:
            _models_pack_import = __import__(_models_package) if \
                _models_package else None
            self.model = getattr(_models_pack_import, self.model_name)
        except ImportError, ie:
            logging.log(9001, "Import error: %s" % ie.message)
            self.result = None
            self.exception = {
                'status_code': 500,
                'custom_msg': "Unable to import specified model"
            }
        except LookupError, le:
            logging.log(9001,
                        "Lookup error in model: %s" % le.message)
            self.result = None
            self.exception = {
                'status_code': 400,
                'custom_msg': le.message
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
            for field in (field for field in fields
                          if field not in exclude):
                item_data = getattr(item, field) if field not in (
                    'pk', 'id', '_id') else str(item.pk)
                item_data = item_data if not hasattr(
                    item_data, 'to_mongo') else \
                    item_data.to_json(fields=ref_fields.get(field,
                                      {}).get('fields', ()),
                                      exclude=ref_fields.get(field,
                                      {}).get('exclude', ()))

                item_dict.update({field: item_data})

            data.append(item_dict)

        return data

    def delete(self, **kwargs):
        """Object instance delete wrapper
        :param kwargs: Keyword args for delete call to Mongoengine.
        :type kwargs: dict
        """
        if self.result and hasattr(self.result, 'delete') \
                and hasattr(self.result.delete, '__call__'):
            try:
                if self.controller:
                    #user = getattr(self.controller, 'user')
                    # if not user:
                    #     return {
                    #         'status_code': 401
                    #     }
                    self.result.delete(**kwargs)
                    return_val = {
                        'status_code': 204
                    }
                else:
                    self.result.delete()
                    return_val = {
                        'status_code': 204
                    }
            except BaseException:
                return_val = {
                    'status_code': 202,
                    'message': '{0} object deletion failed'.format(
                        self.model_name)
                }
        else:
            return_val = {
                'status_code': 404
            }
        if reduce(lambda x, y: x and y, [hasattr(
                self.controller, x) for x in ['ui', 'request']]):

            setattr(self.controller, 'response', return_val)
            return_val = None

        return return_val

    def update(self, update_data):
        """Update object instance wrapper for QueryObject
        :param update_data: Resultset updation data
        :type update_data: dict
        """
        if not isinstance(update_data, dict):
            raise BaseException("Invalid data. Dict data required")

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
                        "Cannot resolve field", "Invalid field")
                    .replace('"', '')
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


class CreateObject(object):
    def __init__(self, controller=None, model=None, data=None):
        """
        Object creation wrapper init
        :param model:str Model to create an object instance of
        :param data: Data for object instance creation
        """
        self.object, self.exception = None, None
        if not model:
            raise Exception("No model provided for object creation")
        if not data:
            raise Exception("No data provided for object creation")

        self.controller = controller
        self.model_name = model
        self._fetch_model()

        if self.model:
            try:
                self.data = data
                self.object = self.model(**self.data)
                self.object.save()
            except ImportError, ie:
                raise Exception("Unable to import specified models pack")
            except ValidationError, v_e:
                self.object = None
                self.exception = {
                    'status_code': 500,
                    'custom_msg': ''
                }
                message = v_e.message
                self.exception['custom_msg'] = message.split(') (')[1].rstrip(')')
            except NotUniqueError, nu_err:
                dup_msg = 'Duplicate value for {0} field'
                field = findall(r'.*?\$(\w+)\_.*?', nu_err.message)
                field = field[0] if field else None
                self.object = None
                self.exception = {
                    'status_code': 500,
                    'custom_msg': ''
                }
                if field:
                    self.exception['custom_msg'] = dup_msg.format(field)

        if controller:
            setattr(controller, 'response',
                    self.exception if self.exception else self.json())

    def json(self):
        return self.object.json() if hasattr(self.object, 'json') else\
                 self.exception if self.exception else {'status_code': 500}

    def _fetch_model(self):
        """
        Model fetcher helper method.
        Imports the specified model passed to QueryObject init.
        If a controller instance is present checks for models in the
        individual applications or from a models package
        specified as a application settings key.
        """
        _models_package, _models_pack_import = None, None
        #_model = None

        if self.controller:
            _models_package = self.controller.settings.get(
                'models_package')

        try:
            _models_pack_import = __import__(_models_package) if \
                _models_package else None
            setattr(self, 'model', getattr(_models_pack_import,
                                      self.model_name))
        except ImportError, ie:
            logging.log(9001, "Import error: %s" % ie.message)
            self.result = None
            self.exception = {
                'status_code': 500,
                'custom_msg': "Unable to import specified model"
            }
        except LookupError, le:
            logging.log(9001,
                        "Lookup error in model: %s" % le.message)
            self.result = None
            self.exception = {
                'status_code': 400,
                'custom_msg': le.message
            }
