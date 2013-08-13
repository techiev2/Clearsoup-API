import sys
sys.dont_write_bytecode = True
import re
import urllib
from datetime import datetime
from mongoengine import Q


def serialize(data, pattern=None, keysplit=None):
    '''
    Serializes a request string from get URI format to a dictionary.
    Requires the pattern for splitting key/value pairs as keysplit
    and pattern for splitting params as pattern.
    '''
    if not pattern:
        pattern = "&"
    if not keysplit:
        keysplit = "="
    if not isinstance(data, str):
        try:
            data = re.sub('\+', ' ',
                    urllib.unquote(data.request.body))
        except KeyError:
            pass
    data = data.split(pattern)
    return dict(zip([x.split(keysplit)[0] for x in data],
                    [x.split(keysplit)[1] for x in data]))


def millisecondToDatetime(millisecond):
    return datetime.utcfromtimestamp(int(millisecond) // 1000)
