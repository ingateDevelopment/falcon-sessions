from __future__ import unicode_literals, absolute_import

import operator
from collections import namedtuple

import redis

from cachetools import cachedmethod, LRUCache

from .base import AbstractSessionStorage, CorruptedSessionDataError


class AbstractRedisServer(object):

    def connect(self, session_key):
        raise NotImplementedError


class RedisServer(AbstractRedisServer):

    def __init__(self,
                 host='localhost',
                 port=6379,
                 url=None,
                 unix_domain_socket_path=None,
                 db=0,
                 password=None,
                 socket_timeout=0.1,
                 retry_on_timeout=False):
        self.host = host
        self.port = port
        self.url = url
        self.unix_domain_socket_path = unix_domain_socket_path
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.retry_on_timeout = retry_on_timeout

    def connect(self, session_key):
        if self.url is not None:
            return redis.StrictRedis.from_url(
                self.url,
                socket_timeout=self.socket_timeout
            )

        elif self.unix_domain_socket_path is not None:
            return redis.StrictRedis(
                unix_socket_path=self.unix_domain_socket_path,
                socket_timeout=self.socket_timeout,
                retry_on_timeout=self.retry_on_timeout,
                db=self.db,
                password=self.password,
            )

        else:
            return redis.StrictRedis(
                host=self.host,
                port=self.port,
                socket_timeout=self.socket_timeout,
                retry_on_timeout=self.retry_on_timeout,
                db=self.db,
                password=self.password
            )


class RedisSentinel(AbstractRedisServer):

    def __init__(self,
                 sentinels,
                 sentinel_master_alias,
                 db=0,
                 password=None,
                 socket_timeout=0.1,
                 retry_on_timeout=False):
        self.sentinels = sentinels
        self.sentinel_master_alias = sentinel_master_alias
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.retry_on_timeout = retry_on_timeout

    def connect(self, session_key):
        from redis.sentinel import Sentinel  # noqa
        return Sentinel(
            self.sentinels,
            socket_timeout=self.socket_timeout,
            retry_on_timeout=self.retry_on_timeout,
            db=self.db,
            password=self.password
        ).master_for(self.sentinel_master_alias)


WeighedServer = namedtuple(
    'WeighedServer',
    ['weight', 'server']
)


class RedisPoolUnableGetServerError(Exception):
    pass


class RedisPool(AbstractRedisServer):

    def __init__(self, *args):
        self.weighted_servers = args
        self.cache = LRUCache(1024)

    @cachedmethod(operator.attrgetter('cache'))
    def _get_server(self, session_key):
        total_weight = sum([connection.weight for connection in self.weighted_servers])
        pos = 0
        for i in range(3, -1, -1):
            pos = pos * 2 ** 8 + ord(session_key[i])
        pos = pos % total_weight

        pool = iter(self.weighted_servers)
        weighted_server = next(pool)
        i = 0
        while i < total_weight:
            if i <= pos < (i + weighted_server.weight):
                return weighted_server.server
            i += weighted_server.weight
            weighted_server = next(pool)

    def connect(self, session_key):
        server = self._get_server(session_key)

        if server is None:
            raise RedisPoolUnableGetServerError(
                "Unable to get a server for the session key '{}'".format(session_key))

        return server.connect(session_key)


class RedisSessionStorage(AbstractSessionStorage):

    def __init__(self, server, prefix='', **kwargs):
        super(RedisSessionStorage, self).__init__(**kwargs)
        self.server = server
        self.prefix = prefix

    def get_real_stored_key(self, session_key):
        """Returns the real key name in server storage."""
        if not self.prefix:
            return session_key

        return ':'.join((self.prefix, session_key))

    def exists(self, session_key):
        connection = self.server.connect(session_key)
        return connection.exists(self.get_real_stored_key(session_key))

    def insert(self, session_key, session_data, expiry_age):
        self.update(session_key, session_data, expiry_age)

    def read(self, session_key, **kwargs):
        connection = self.server.connect(session_key)
        try:
            return self.decode(
                connection.get(self.get_real_stored_key(session_key)))
        except CorruptedSessionDataError:
            raise
        except Exception:
            return {}

    def update(self, session_key, session_data, expiry_age):
        connection = self.server.connect(session_key)
        if redis.VERSION[0] >= 2:
            connection.setex(
                self.get_real_stored_key(session_key),
                expiry_age,
                self.encode(session_data)
            )
        else:
            self.server.set(
                self.get_real_stored_key(session_key),
                self.encode(session_data)
            )
            self.server.expire(
                self.get_real_stored_key(session_key),
                expiry_age
            )

    def delete(self, session_key):
        connection = self.server.connect(session_key)
        try:
            return connection.delete(self.get_real_stored_key(session_key))
        except Exception:
            pass
