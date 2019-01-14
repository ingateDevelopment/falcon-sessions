from __future__ import unicode_literals

import six


class Session(object):

    """Session.

    Wrapper around dict that stores information about
    modifications and accesses.

    :param key: session key
    :type key: basestring
    :param data: session data
    :type data: dict
    """

    __not_given = object()

    def __init__(self, key=None, data=None):
        self._key = key
        self._data = data or {}
        self._modified = False
        self._accessed = False

    def __contains__(self, key):
        self._accessed = True
        return key in self._data

    def __getitem__(self, key):
        self._accessed = True
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self._modified = True
        self._accessed = True

    def __delitem__(self, key):
        del self._data[key]
        self._modified = True
        self._accessed = True

    def get(self, key, default=None):
        self._accessed = True
        return self._data.get(key, default)

    def pop(self, key, default=__not_given):
        self._modified = self.modified or key in self._data
        self._accessed = True
        args = () if default is self.__not_given else (default,)
        return self._data.pop(key, *args)

    def setdefault(self, key, value):
        self._accessed = True
        if key in self._data:
            return self._data[key]
        else:
            self._modified = True
            self._data[key] = value
            return value

    def update(self, dict_):
        self._data.update(dict_)
        self._modified = True
        self._accessed = True

    def _iteritems(self):
        self._accessed = True
        for key in self._data:
            yield key, self._data[key]

    def _iterkeys(self):
        self._accessed = True
        for key in self._data:
            yield key

    def _itervalues(self):
        self._accessed = True
        for key in self._data:
            yield self[key]

    if six.PY3:
        items = _iteritems
        keys = _iterkeys
        values = _itervalues
    else:
        iteritems = _iteritems
        iterkeys = _iterkeys
        itervalues = _itervalues

        def items(self):
            return list(self.iteritems())

        def keys(self):
            return list(self.iterkeys())

        def values(self):
            return list(self.itervalues())

    def clear(self):
        self._data = {}
        self._modified = True
        self._accessed = True

    @property
    def data(self):
        return self._data

    @property
    def key(self):
        return self._key

    @property
    def modified(self):
        return self._modified

    @property
    def accessed(self):
        return self._accessed

    @property
    def expiry(self):
        return self.get('_session_expiry')

    @expiry.setter
    def expiry(self, value):
        if value is None:
            try:
                del self['_session_expiry']
            except KeyError:
                pass
        else:
            self['_session_expiry'] = value
