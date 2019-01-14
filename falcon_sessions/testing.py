from __future__ import unicode_literals

from falcon import API
from falcon.testing import TestClient, SimpleTestResource

from .backends.base import AbstractSessionStorage


def create_client(resource=None, middleware=None, handlers=None):
    res = resource or SimpleTestResource()

    app = API(middleware=middleware)
    app.add_route('/', res)

    if handlers:
        app.req_options.media_handlers.update(handlers)

    client = TestClient(app)
    client.resource = res

    return client


class CacheSessionStorage(AbstractSessionStorage):

    def __init__(self, **kwargs):
        super(CacheSessionStorage, self).__init__(**kwargs)
        self._cache = {}

    def exists(self, session_key):
        return session_key in self._cache

    def insert(self, session_key, session_data, expiry_age):
        self._cache[session_key] = session_data

    def read(self, session_key):
        return self._cache.get(session_key, {})

    def update(self, session_key, session_data, expiry_age):
        self._cache[session_key] = session_data

    def delete(self, session_key):
        if session_key in self._cache:
            del self._cache[session_key]

    def __len__(self):
        return len(self._cache)
