'''
Created on 13-Aug-2013

@author: someshs
'''

from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.project import Project
from mongoengine.errors import ValidationError
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper
import json


class OrganizationHandler(BaseHandler):
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('id',),
        'PUT': ('name'),
        'DELETE' : ('id',),
        }
    data = {}
    pass