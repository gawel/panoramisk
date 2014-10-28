# -*- coding: utf-8 -*-
import uuid
import collections

try:  # pragma: no cover
    from urllib.parse import unquote
except ImportError:  # pragma: no cover
    from urllib import unquote  # NOQA


try:  # pragma: no cover
    import asyncio
    from asyncio.queues import Queue
except ImportError:  # pragma: no cover
    import trollius as asyncio  # NOQA
    from trollius.queues import Queue  # NOQA

EOL = '\r\n'


class IdGenerator(object):
    """Generate some uuid for actions:

    .. code-block:: python

        >>> g = IdGenerator('mycounter')

    ..
        >>> IdGenerator.reset(uid='an_uuid4')

    It increment counters at each calls:

    .. code-block:: python

        >>> print(g())
        mycounter/an_uuid4/1/1
        >>> print(g())
        mycounter/an_uuid4/1/2
    """

    instances = []

    def __init__(self, prefix):
        self.instances.append(self)
        self.prefix = prefix
        self.uid = str(uuid.uuid4())
        self.generator = self.get_generator()

    def get_generator(self):
        i = 0
        j = 1
        while True:
            i += 1
            yield self.prefix + '/' + self.uid + '/' + str(j) + '/' + str(i)
            if i > 10000:  # pragma: no cover
                j += 1
                i = 0

    @classmethod
    def reset(cls, uid=None):
        """Mostly used for unit testing. Allow to use a static uuid and reset
        all counter"""
        for instance in cls.instances:
            if uid:
                instance.uid = uid
            instance.generator = instance.get_generator()

    def __call__(self):
        return next(self.generator)


class CaseInsensitiveDict(collections.MutableMapping):

    def __init__(self, data=None, **kwargs):
        self._store = dict()
        self.update(data or {}, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __contains__(self, key):
        return key.lower() in self._store

    def __getattr__(self, attr):
        return self.get(attr, '')

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        raise NotImplementedError()

    def __iter__(self):
        return (key for key, value in self._store.values())

    def __len__(self):
        return len(self._store)
