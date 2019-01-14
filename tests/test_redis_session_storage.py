from __future__ import unicode_literals

import os
import time
import unittest

from falcon_sessions.session import Session
from falcon_sessions.backends.redis import (
    RedisSessionStorage,
    RedisServer,
    RedisPool,
    WeighedServer
)

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 1)


class TestRedisSessionStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session_storage = RedisSessionStorage(
            RedisServer(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB))

    def setUp(self):
        self.session = Session()

    def test_non_existing(self):
        self.assertFalse(self.session_storage.exists('some_unknown_key'))

    def test_create_and_delete(self):
        self.session['key'] = 'value'

        session_key = self.session_storage.create(
            self.session.data, expiry_age=24 * 3600)
        self.assertTrue(self.session_storage.exists(session_key))
        self.session_storage.delete(session_key)
        self.assertFalse(self.session_storage.exists(session_key))

    def test_expiry(self):
        session_key = self.session_storage.create(self.session.data, 1)
        self.assertTrue(self.session_storage.exists(session_key))
        time.sleep(2)
        self.assertFalse(self.session_storage.exists(session_key))

    def test_create_and_read(self):
        self.session.expiry = 60
        self.session.setdefault('item_test', 8)
        session_key = self.session_storage.create(
            self.session.data, expiry_age=self.session.expiry)
        session_data = self.session_storage.read(session_key)
        self.assertEqual(8, session_data.get('item_test'))


class TestRedisPool(unittest.TestCase):

    def test_redis_pool_server_select(self):
        pool = RedisPool(
            WeighedServer(1, RedisServer(host='localhost2')),
            WeighedServer(1, RedisServer(host='localhost1'))
        )

        keys1 = (
            'm8f0os91g40fsq8eul6tejqpp6k22',
            'kcffsbb5o272et1d5e6ib7gh75pd9',
            'gqldpha87m8183vl9s8uqobcr2ws3',
            'ukb9bg2jifrr60fstla67knjv3e32',
            'k3dranjfna7fv7ijpofs6l6bj2pw1',
            'an4no833idr9jddr960r8ikai5nh3',
            '16b9gardpcscrj5q4a4kf3c4u7tq8',
            'etdefnorfbvfc165c5airu77p2pl9',
            'mr778ou0sqqme21gjdiu4drtc0bv4',
            'ctkgd8knu5hukdrdue6im28p90kt7'
        )

        keys2 = (
            'jgpsbmjj6030fdr3aefg37nq47nb8',
            'prsv0trk66jc100pipm6bb78c3pl2',
            '84ksqj2vqral7c6ped9hcnq940qq1',
            'bv2uc3q48rm8ubipjmolgnhul0ou3',
            '6c8oph72pfsg3db37qsefn3746fg4',
            'tbc0sjtl2bkp5i9n2j2jiqf4r0bg9',
            'v0on9rorn71913o3rpqhvkknc1wm5',
            'lmsv98ns819uo2klk3s1nusqm0mr0',
            '0foo2bkgvrlk3jt2tjbssrsc47tr3',
            '05ure0f6r5jjlsgaimsuk4n1k2sx6',
        )

        for key in keys1:
            server = pool._get_server(key)
            self.assertEqual('localhost1', server.host)

        for key in keys2:
            server = pool._get_server(key)
            self.assertEqual('localhost2', server.host)


class TestRedisServer(unittest.TestCase):

    def test_url(self):
        server = RedisServer(url='redis://{}:{}/{}'.format(REDIS_HOST, REDIS_PORT, REDIS_DB))
        connection = server.connect('')
        self.assertFalse(connection.exists('some_unknown_key'))

    def test_host_port(self):
        server = RedisServer(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        connection = server.connect('')
        self.assertFalse(connection.exists('some_unknown_key'))


if __name__ == '__main__':
    unittest.main()
