import logging
from collections import OrderedDict
from .utils import asyncio
from .utils import parse_agi_result

log = logging.getLogger(__name__)


class Request:
    def __init__(self, app, headers, reader, writer, encoding='utf-8'):
        self.app = app
        self.headers = headers
        self.reader = reader
        self.writer = writer
        self.encoding = encoding

    @asyncio.coroutine
    def send_command(self, command):
        command += '\n'
        self.writer.write(command.encode(self.encoding))
        yield from self.writer.drain()
        response = yield from self.reader.readline()
        return parse_agi_result(response.decode(self.encoding))


class Application(dict):

    def __init__(self, default_encoding='utf-8', loop=None):
        super(Application, self).__init__()
        self.default_encoding = default_encoding
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self._route = OrderedDict()

    def add_route(self, path, endpoint):
        assert callable(endpoint), endpoint
        if not asyncio.iscoroutinefunction(endpoint):
            endpoint = asyncio.coroutine(endpoint)
        self._route[path] = endpoint

    @asyncio.coroutine
    def handler(self, reader, writer):
        buffer = b''
        while b'\n\n' not in buffer:
            buffer += yield from reader.read(100)
        lines = buffer[:-2].decode(self.default_encoding).split('\n')
        headers = OrderedDict()
        for line in lines:
            k, v = line.split(': ', 1)
            headers[k] = v
        log.debug("Received %r from %r",
                  headers, writer.get_extra_info('peername'))

        if headers['agi_network_script'] in self._route:
            request = Request(app=self,
                              headers=headers,
                              reader=reader, writer=writer,
                              encoding=self.default_encoding)
            try:
                yield from self[headers['agi_network_script']](request)
            except Exception as e:
                log.exception(e)
        else:
            log.error('No endpoints for this request')
        log.debug("Closing client socket")
        writer.close()
