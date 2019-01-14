from __future__ import unicode_literals

import base64
from uuid import uuid4

import six

from ..serializers import PickleSerializer
from ..signers import Sha1Signer


class CorruptedSessionDataError(Exception):
    pass


class AbstractSessionStorage(object):

    def __init__(self, serializer=None, signer=None):
        self.serializer = serializer or PickleSerializer()
        self.signer = signer or Sha1Signer()

    def get_new_session_key(self):
        """Returns session key that isn't being used."""
        while True:
            session_key = uuid4().hex
            if not self.exists(session_key):
                return session_key

    def encode(self, session_data):
        """Returns the given session data serialized and encoded as a string."""
        serialized = self.serializer.dumps(session_data)
        signature = self.signer.get_signature(serialized)
        return base64.b64encode(signature.encode() + b':' + serialized).decode('ascii')

    def decode(self, session_data):
        """Returns decoded session data."""
        if six.PY3 and isinstance(session_data, six.text_type):
            session_data = session_data.encode('ascii')

        encoded_data = base64.b64decode(session_data)
        try:
            expected_signature, serialized = encoded_data.split(b':', 1)
        except ValueError:
            raise CorruptedSessionDataError("Session data has invalid format")

        signature = self.signer.get_signature(serialized)
        if signature != expected_signature.decode():
            raise CorruptedSessionDataError("Session data is corrupted")

        return self.serializer.loads(serialized)

    def exists(self, session_key):
        raise NotImplementedError

    def create(self, session_data, expiry_age):
        session_key = self.get_new_session_key()
        self.insert(session_key, session_data, expiry_age)
        return session_key

    def insert(self, session_key, session_data, expiry_age):
        raise NotImplementedError

    def read(self, session_key):
        raise NotImplementedError

    def update(self, session_key, session_data, expiry_age):
        raise NotImplementedError

    def delete(self, session_key):
        raise NotImplementedError
