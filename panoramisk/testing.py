# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase
import codecs

import panoramisk


try:
    from unittest import mock
except ImportError:
    import mock


MagicMock = mock.MagicMock
patch = mock.patch
call = mock.call


class Connection(panoramisk.Connection):

    debug_count = [0]

    def connection_made(self, transport):
        super(Connection, self).connection_made(transport)
        self.transport = MagicMock()

    def send(self, data, as_list=False):
        panoramisk.IdGenerator.reset()
        resp = super(Connection, self).send(data, as_list=as_list)
        self.debug_count[0] += 1
        print(resp)
        print('called mock_data_received with %d' % self.debug_count[0])
        self.factory.loop.call_later(.1, self.mock_data_received, data,
                                     self.debug_count[0])
        return resp

    def mock_data_received(self, data, c):
        resp = ''
        try:
            with codecs.open('../tests/data/connection_response') as resp_fd:
                resp = resp_fd.read()
            self.data_received(resp)
        except OSError:
            self.log.error('Connection response test file can\'t be read')
        print('mock_data_received with %d' % c)


class Manager(panoramisk.Manager):

    def __init__(self, **config):
        self.defaults['connection_class'] = Connection
        super(Manager, self).__init__(**config)


class PanoramiskTestCase(TestCase):
    pass
