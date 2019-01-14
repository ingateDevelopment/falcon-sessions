from __future__ import unicode_literals

import json

try:
    from six.moves import cPickle as pickle
except ImportError:
    import pickle


class AbstractSerializer(object):

    def dumps(self, obj):
        raise NotImplementedError

    def loads(self, data):
        raise NotImplementedError


class PickleSerializer(AbstractSerializer):
    """Simple wrapper around pickle."""

    def dumps(self, obj):
        return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)

    def loads(self, data):
        return pickle.loads(data)


class JSONSerializer(AbstractSerializer):
    """Simple wrapper around json."""

    def __init__(self, encoding='utf-8'):
        self.encoding = encoding

    def dumps(self, obj):
        return json.dumps(obj, separators=(',', ':')).encode(self.encoding)

    def loads(self, data):
        return json.loads(data.decode(self.encoding))
