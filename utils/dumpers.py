'''
Overrides for bson's native default dumper
'''

import sys
sys.dont_write_bytecode = True
from datetime import datetime as DT
from bson.max_key import MaxKey
from bson.min_key import MinKey
from bson.objectid import ObjectId
from bson.timestamp import Timestamp
import calendar
import re
from pymongo import Connection
from bson.dbref import DBRef
from requires.settings import SETTINGS
from mongoengine.queryset import QuerySet

try:
    import json
except ImportError:
    import simplejson as json

connection = Connection(host="localhost", port=SETTINGS['mongo_port'])

db = connection[SETTINGS['mongo_db']]

EXCLUDES = {'password': 0}

try:
    import uuid
    _use_uuid = True
except ImportError:
    _use_uuid = False


_RE_TYPE = type(re.compile("foo"))


def default_json(obj):
    '''
    JSON loader overridden from BSON module's json_util.default
    Returns string representation of datetime data instead of native
    seconds since epoch and object data instead of DBREF.
    '''
    try:
        if isinstance(obj, ObjectId):
            data = {"$oid": str(obj)}
        if isinstance(obj, DBRef):
            collection = db[obj.collection]
            data = collection.find_one({'_id': obj._DBRef__id}, EXCLUDES)
        if isinstance(obj, DT):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
            millis = int(calendar.timegm(obj.timetuple()) * 1000 +
                         obj.microsecond / 1000)
            data = {"$date": millis}
        if isinstance(obj, _RE_TYPE):
            flags = ""
            if obj.flags & re.IGNORECASE:
                flags += "i"
            if obj.flags & re.MULTILINE:
                flags += "m"
            data = {"$regex": obj.pattern,
                    "$options": flags}
        if isinstance(obj, MinKey):
            data = {"$minKey": 1}
        if isinstance(obj, MaxKey):
            data = {"$maxKey": 1}
        if isinstance(obj, Timestamp):
            data = {"t": obj.time, "i": obj.inc}
        if _use_uuid and isinstance(obj, uuid.UUID):
            data = {"$uuid": obj.hex}
        return data
    except TypeError:
        raise TypeError("%r is not JSON serializable" % obj)


def json_dumper(data, fields=None, exclude=None):
    '''
    Convert mongo instance to JSON object
    '''
    excludes = ['password', '_cls', '_types']
    if exclude and fields:
        excludes.extend(fields)
    if isinstance(data, QuerySet):
        data = [x for x in data]
    if isinstance(data, list):
        ldata = [json.loads(json.dumps(x.to_mongo(),
                        default=default_json)) for x in data]
        for xdata in ldata:
            if not exclude and fields:
                for key in xdata.keys():
                    if key not in fields:
                        del xdata[key]
            else:
                for key in xdata.keys():
                    if key in excludes:
                        del xdata[key]

        '''for xdata in ldata:
            for key in excludes:
                [x.pop(key) for x in xdata if key in x.keys()]
            if not exclude:
                for key in xdata.keys():
                    if key not in fields:
                        del xdata[key]'''
        data = ldata
    else:
        if data:
            try:
                data = json.loads(json.dumps(data.to_mongo(),
                                    default=default_json))
            except AttributeError:
                pass
            for key in excludes:
                if key in data.keys():
                    del(data[key])
            if not exclude:
                if fields:
                    for key in data.keys():
                        if key not in fields:
                            del data[key]
    return data
