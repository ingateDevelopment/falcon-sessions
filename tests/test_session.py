from __future__ import unicode_literals

import unittest

import six

from falcon_sessions.session import Session


class TestSession(unittest.TestCase):

    def setUp(self):
        self.session = Session()

    def test_new_session(self):
        self.assertFalse(self.session.modified)
        self.assertFalse(self.session.accessed)

    def test_get_empty(self):
        self.assertIsNone(self.session.get('cat'))

    def test_store(self):
        self.session['cat'] = "dog"
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.pop('cat'), 'dog')

    def test_pop(self):
        self.session['some key'] = 'exists'
        # Need to reset these to pretend we haven't accessed it:
        self.accessed = False
        self.modified = False

        self.assertEqual(self.session.pop('some key'), 'exists')
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)
        self.assertIsNone(self.session.get('some key'))

    def test_pop_default(self):
        self.assertEqual(self.session.pop('some key', 'does not exist'),
                         'does not exist')
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_pop_default_named_argument(self):
        self.assertEqual(self.session.pop('some key', default='does not exist'), 'does not exist')
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_pop_no_default_keyerror_raised(self):
        with self.assertRaises(KeyError):
            self.session.pop('some key')

    def test_setdefault(self):
        self.assertEqual(self.session.setdefault('foo', 'bar'), 'bar')
        self.assertEqual(self.session.setdefault('foo', 'baz'), 'bar')
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)

    def test_update(self):
        self.session.update({'update key': 1})
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.get('update key', None), 1)

    def test_has_key(self):
        self.session['some key'] = 1
        self.session._modified = False
        self.session._accessed = False
        self.assertIn('some key', self.session)
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_values(self):
        self.assertEqual(list(self.session.values()), [])
        self.assertTrue(self.session.accessed)
        self.session['some key'] = 1
        self.assertEqual(list(self.session.values()), [1])

    def test_iterkeys(self):
        self.session['x'] = 1
        self.session._modified = False
        self.session._accessed = False
        it = six.iterkeys(self.session)
        self.assertTrue(hasattr(it, '__iter__'))
        self.assertEqual(list(it), ['x'])
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_itervalues(self):
        self.session['x'] = 1
        self.session._modified = False
        self.session._accessed = False
        it = six.itervalues(self.session)
        self.assertTrue(hasattr(it, '__iter__'))
        self.assertEqual(list(it), [1])
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_iteritems(self):
        self.session['x'] = 1
        self.session._modified = False
        self.session._accessed = False
        it = six.iteritems(self.session)
        self.assertTrue(hasattr(it, '__iter__'))
        self.assertEqual(list(it), [('x', 1)])
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_clear(self):
        self.session['x'] = 1
        self.session._modified = False
        self.session._accessed = False
        self.assertEqual(list(self.session.items()), [('x', 1)])
        self.session.clear()
        self.assertEqual(list(self.session.items()), [])
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)


if __name__ == '__main__':
    unittest.main()
