import unittest
from datetime import datetime, timedelta

from falcon_sessions.middleware import SessionMiddleware
from falcon_sessions.testing import create_client, CacheSessionStorage


class UpdateSessionResource(object):

    def on_get(self, req, resp, **params):
        req.session['test'] = 'data'


class ClearSessionResource(object):

    def on_get(self, req, resp, **params):
        req.session.clear()


class SetCustomSessionExpiryResource(object):

    def __init__(self, expiry):
        self.expiry = expiry

    def on_get(self, req, resp, **params):
        req.session.expiry = self.expiry


class TestSessionMiddleware(unittest.TestCase):

    def setUp(self):
        self.session_storage = CacheSessionStorage()
        self.session_middleware = SessionMiddleware(self.session_storage)

    def test_create_session(self):
        client = create_client(
            resource=UpdateSessionResource(),
            middleware=self.session_middleware
        )
        resp = client.simulate_get('/')
        self.assertEqual(1, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertEqual('Cookie', resp.headers['Vary'])

    def test_existent_session(self):
        client = create_client(
            middleware=self.session_middleware
        )
        session_key = self.session_storage.get_new_session_key()
        session_data = {'test': 'data'}
        self.session_storage.insert(session_key, session_data, 24 * 3600)
        resp = client.simulate_get('/', headers={'Cookie': 'session=%s' % session_key})
        self.assertEqual(1, len(self.session_storage))
        self.assertEqual(session_data, self.session_storage.read(session_key))
        self.assertTrue('session' not in resp.cookies)

    def test_non_existent_session(self):
        client = create_client(
            middleware=self.session_middleware
        )
        session_key = self.session_storage.get_new_session_key()
        resp = client.simulate_get('/', headers={'Cookie': 'session=%s' % session_key})
        self.assertEqual(0, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertTrue(datetime.utcnow() > resp.cookies['session'].expires)

    def test_create_new_session_if_received_does_not_exist(self):
        client = create_client(
            resource=UpdateSessionResource(),
            middleware=self.session_middleware
        )
        session_key = self.session_storage.get_new_session_key()
        resp = client.simulate_get('/', headers={'Cookie': 'session=%s' % session_key})
        self.assertEqual(1, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertEqual('Cookie', resp.headers['Vary'])
        self.assertFalse(self.session_storage.exists(session_key))

    def test_clear_session_and_unset_cookies(self):
        client = create_client(
            resource=ClearSessionResource(),
            middleware=self.session_middleware
        )
        session_key = self.session_storage.get_new_session_key()
        session_data = {'test': 'data'}
        self.session_storage.insert(session_key, session_data, 24 * 3600)
        resp = client.simulate_get('/', headers={'Cookie': 'session=%s' % session_key})
        self.assertEqual(0, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertTrue(datetime.utcnow() > resp.cookies['session'].expires)

    def test_custom_session_expiry_timedelta(self):
        client = create_client(
            resource=SetCustomSessionExpiryResource(timedelta(weeks=2, days=4)),
            middleware=self.session_middleware
        )
        resp = client.simulate_get('/')
        self.assertEqual(1, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertEqual(18 * 86400, resp.cookies['session'].max_age)
        self.assertEqual('Cookie', resp.headers['Vary'])

    def test_custom_session_expiry_datetime(self):
        now = datetime.utcnow()
        client = create_client(
            resource=SetCustomSessionExpiryResource(now.replace(day=now.day + 1)),
            middleware=self.session_middleware
        )
        resp = client.simulate_get('/')
        self.assertEqual(1, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertTrue(23 * 3600 < resp.cookies['session'].max_age <= 24 * 3600)
        self.assertEqual('Cookie', resp.headers['Vary'])

    def test_custom_session_expiry_seconds(self):
        client = create_client(
            resource=SetCustomSessionExpiryResource(1555200),
            middleware=self.session_middleware
        )
        resp = client.simulate_get('/')
        self.assertEqual(1, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertEqual(1555200, resp.cookies['session'].max_age)
        self.assertEqual('Cookie', resp.headers['Vary'])

    def test_custom_session_expiry_expiry_at_browser_close(self):
        client = create_client(
            resource=SetCustomSessionExpiryResource(0),
            middleware=self.session_middleware
        )
        resp = client.simulate_get('/')
        self.assertEqual(1, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertEqual(None, resp.cookies['session'].max_age)
        self.assertEqual('Cookie', resp.headers['Vary'])

    def test_get_expiry_at_browser_close(self):
        self.session_middleware.session_expiry_at_browser_close = True
        client = create_client(
            resource=UpdateSessionResource(),
            middleware=self.session_middleware
        )
        resp = client.simulate_get('/')
        self.assertEqual(1, len(self.session_storage))
        self.assertTrue('session' in resp.cookies)
        self.assertEqual(None, resp.cookies['session'].max_age)
        self.assertEqual('Cookie', resp.headers['Vary'])


if __name__ == '__main__':
    unittest.main()
