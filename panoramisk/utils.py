# -*- coding: utf-8 -*-
import uuid

try:  # pragma: no cover
    import asyncio
    from asyncio.queues import Queue
except ImportError:  # pragma: no cover
    import trollius as asyncio  # NOQA
    from trollius.queues import Queue  # NOQA

EOL = '\r\n'


class IdGenerator(object):

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
        for instance in cls.instances:
            if uid:
                instance.uid = uid
            instance.generator = instance.get_generator()

    def __call__(self):
        return next(self.generator)
