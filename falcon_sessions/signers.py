from __future__ import unicode_literals

import hmac
import hashlib


class AbstractSigner(object):

    def get_signature(self, value):
        raise NotImplementedError


class Sha1Signer(AbstractSigner):

    """Simple sha1 signer."""

    def get_signature(self, value):
        return hashlib.sha1(value).hexdigest()


class Django14Signer(AbstractSigner):

    """Django 1.4 compatible signer.

    :param django_secret_key: Django secret key from settings.SECRET_KEY
    :type django_secret_key: basestring
    :param django_session_class_name: name of used session class in Django
    :type django_session_class_name: basestring
    """

    def __init__(self, django_secret_key, django_session_class_name):
        self.django_secret_key = django_secret_key
        self.django_session_class_name = django_session_class_name

    def get_signature(self, value):
        key_salt = "django.contrib.sessions" + self.django_session_class_name

        # We need to generate a derived key from our base key.  We can do this by
        # passing the key_salt and our base key through a pseudo-random function and
        # SHA1 works nicely.
        key = hashlib.sha1(key_salt + self.django_secret_key).digest()

        # If len(key_salt + secret) > sha_constructor().block_size, the above
        # line is redundant and could be replaced by key = key_salt + secret, since
        # the hmac module does the same thing for keys longer than the block size.
        # However, we need to ensure that we *always* do this.
        return hmac.new(key, msg=value, digestmod=hashlib.sha1).hexdigest()
