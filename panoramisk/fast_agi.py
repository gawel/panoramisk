import asyncio
from collections import OrderedDict
import logging
import re

LOG = logging.getLogger(__name__)

AGI_RESULT_REGEX = re.compile(
    r'(?P<status_code>\d{3})'
    r'(?: result=(?P<result>\-?[0-9]+)?(?: \(?(?P<value>.*)\))?)|(?:-.*)')


def parse_agi_result(result):
    m = AGI_RESULT_REGEX.match(result)
    if m:
        d = m.groupdict()
        d['status_code'] = int(d['status_code'])
        if 'result' in d:
            d['result'] = int(d['result'])
        return d
    else:
        raise ValueError('Can\'t parse result in %r' % result)


class Request:
    def __init__(self, app, headers, reader, writer):
        self.app = app
        self.headers = headers
        self.reader = reader
        self.writer = writer

    @asyncio.coroutine
    def send_command(self, command):
        command += '\n'
        self.writer.write(command.encode(self.app.default_encoding))
        yield from self.writer.drain()
        response = yield from self.reader.readline()
        return parse_agi_result(response.decode(self.app.default_encoding))


class Application(dict):

    def __init__(self, default_encoding='utf-8', loop=None):
        self.default_encoding = default_encoding
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self._route = OrderedDict()
        super().__init__(self)

    def add_route(self, path, endpoint):

        assert callable(endpoint), endpoint
        if not asyncio.iscoroutinefunction(endpoint):
            endpoint = asyncio.coroutine(endpoint)
        self._route[path] = endpoint

    @asyncio.coroutine
    def handler(self, reader, writer):
        # print(config)
        buffer = b''
        while b'\n\n' not in buffer:
            buffer += yield from reader.read(100)
        lines = buffer[:-2].decode(self.default_encoding).split('\n')
        headers = OrderedDict()
        for line in lines:
            k, v = line.split(': ', 1)
            headers[k] = v
        LOG.debug("Received %r from %r", headers, writer.get_extra_info('peername'))

        if headers['agi_network_script'] in self._route:
            request = Request(app=self, headers=headers, reader=reader, writer=writer)
            yield from self._route[headers['agi_network_script']](request)
        else:
            LOG.error('No endpoints for this request')
        LOG.debug("Close the client socket")
        writer.close()