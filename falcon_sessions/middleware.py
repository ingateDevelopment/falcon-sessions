from __future__ import unicode_literals

from datetime import datetime, timedelta

from .session import Session


def total_seconds(td):
    return td.days * 24 * 60 * 60 + td.seconds


class SessionMiddleware(object):

    """Session middleware.

    :param session_storage: storage of session data
    :type session_storage: AbstractSessionStorage
    :param session_lifetime: session expiry. Default: 2 weeks
    :type session_lifetime: int | timedelta
    :param session_cookie_name: cookie name. This can be whatever you want
    :type session_cookie_name: basestring
    :param session_cookie_domain: a string like ".example.com", or None for standard
        domain cookie
    :type session_cookie_domain: basestring
    :param session_cookie_secure: whether the session cookie should be secure. Default: False
    :type session_cookie_secure: bool
    :param session_cookie_path: the path of the session cookie
    :type session_cookie_path: basestring
    :param session_cookie_http_only: whether to use the non-RFC standard httpOnly
        flag (IE, FF3+, others). Default: True
    :type session_cookie_http_only: bool
    :param session_expiry_at_browser_close: whether a user's session cookie expires
        when the Web browser is closed. Default: False
    :type session_expiry_at_browser_close: bool
    :param session_refresh_each_request: whether to save the session data on every
        request. Default: False
    :type session_refresh_each_request: bool
    """

    def __init__(self,
                 session_storage,
                 session_lifetime=timedelta(weeks=2),
                 session_cookie_name='session',
                 session_cookie_domain=None,
                 session_cookie_secure=False,
                 session_cookie_path=b'/',
                 session_cookie_http_only=True,
                 session_expiry_at_browser_close=False,
                 session_refresh_each_request=False):
        self.session_storage = session_storage
        self.session_lifetime = session_lifetime
        self.session_cookie_name = session_cookie_name
        self.session_cookie_domain = session_cookie_domain
        self.session_cookie_secure = session_cookie_secure
        self.session_cookie_path = session_cookie_path
        self.session_cookie_http_only = session_cookie_http_only
        self.session_expiry_at_browser_close = session_expiry_at_browser_close
        self.session_refresh_each_request = session_refresh_each_request

    def get_expiry_age(self, session):
        """Returns the number of seconds until the session expires."""
        expiry = session.expiry

        if expiry is None:
            expiry = self.session_lifetime

        if isinstance(expiry, timedelta):
            return total_seconds(expiry)

        elif isinstance(expiry, datetime):
            delta = expiry - datetime.utcnow()
            return total_seconds(delta)

        else:
            return expiry

    def get_expire_at_browser_close(self, session):
        """Returns ``True`` if the session is set to expire when the browser
        closes, and ``False`` if there's an expiry date.
        """
        expiry = session.expiry

        if expiry is None:
            return self.session_expiry_at_browser_close

        return expiry == 0

    def set_session_cookie(self, resp, session_key, max_age=None):
        """Sets session cookie."""
        resp.set_cookie(
            name=self.session_cookie_name,
            value=session_key,
            domain=self.session_cookie_domain,
            path=self.session_cookie_path,
            secure=self.session_cookie_secure,
            http_only=self.session_cookie_http_only,
            max_age=max_age
        )

    def unset_session_cookie(self, resp):
        """Disables session cookies."""
        resp.set_cookie(
            name=self.session_cookie_name,
            value='',
            domain=self.session_cookie_domain,
            path=self.session_cookie_path,
            secure=self.session_cookie_secure,
            http_only=self.session_cookie_http_only,
            expires=datetime.utcnow() - timedelta(1),
            max_age=-1
        )

    def process_request(self, req, resp):
        session_key = req.cookies.get(self.session_cookie_name)
        if session_key is not None and self.session_storage.exists(session_key):
            req.session = Session(
                key=session_key,
                data=self.session_storage.read(session_key)
            )
        else:
            req.session = Session()

    def process_response(self, req, resp, resource, req_succeeded):
        session = req.session

        if not session.data:
            if session.modified and session.key is not None:
                self.session_storage.delete(session.key)

            if self.session_cookie_name in req.cookies:
                self.unset_session_cookie(resp)

            return

        # Without "Vary:Cookie", authenticated users would also be
        # served the anonymous page from the browser cache
        if session.accessed:
            resp.append_header('Vary', 'Cookie')

        if req_succeeded and (session.modified or self.session_refresh_each_request):
            max_age = None
            expiry_age = self.get_expiry_age(session)
            if not self.get_expire_at_browser_close(session):
                max_age = expiry_age

            session_key = session.key
            if session_key is None:
                session_key = self.session_storage.create(
                    session.data, expiry_age)
            else:
                self.session_storage.update(
                    session_key, session.data, expiry_age)

            self.set_session_cookie(resp, session_key, max_age=max_age)
