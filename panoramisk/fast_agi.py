import logging
import asyncio
from collections import OrderedDict
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
        """Send a command for FastAGI request:

        :param command: Command to launch on FastAGI request. Ex: 'EXEC StartMusicOnHolds'
        :type command: String

        :Example:

        ::

            @asyncio.coroutine
            def call_waiting(request):
                print(['AGI variables:', request.headers])
                yield from request.send_command('ANSWER')
                yield from request.send_command('EXEC StartMusicOnHold')
                yield from request.send_command('EXEC Wait 10')

        """
        command += '\n'
        self.writer.write(command.encode(self.encoding))
        yield from self.writer.drain()
        response = yield from self.reader.readline()
        agi_result = parse_agi_result(response.decode(self.encoding)[:-1])
        # when we got AGIUsageError the following line contains some indication
        if 'error' in agi_result and agi_result['error'] == 'AGIUsageError':
            buff_usage_error = yield from self.reader.readline()
            agi_result['msg'] += buff_usage_error.decode(self.encoding)

        return agi_result


class Application(dict):
    """Main object:

    .. code-block:: python

        >>> fa_app = Application()
    """

    buf_size = 100

    def __init__(self, default_encoding='utf-8', loop=None):
        super(Application, self).__init__()
        self.default_encoding = default_encoding
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self._route = OrderedDict()

    def add_route(self, path, endpoint):
        """Add a route for FastAGI requests:

        :param path: URI to answer. Ex: 'calls/start'
        :type path: String
        :param endpoint: command to launch. Ex: start
        :type endpoint: callable

        :Example:

        ::

            @asyncio.coroutine
            def start(request):
                print('Receive a FastAGI request')
                print(['AGI variables:', request.headers])

            fa_app = Application()
            fa_app.add_route('calls/start', start)

        """
        assert callable(endpoint), endpoint
        if path in self._route:
            raise ValueError('A route already exists.')
        if not asyncio.iscoroutinefunction(endpoint):
            endpoint = asyncio.coroutine(endpoint)
        self._route[path] = endpoint

    def del_route(self, path):
        """Delete a route for FastAGI requests:

        :param path: URI to answer. Ex: 'calls/start'
        :type path: String

        :Example:

        ::

            @asyncio.coroutine
            def start(request):
                print('Receive a FastAGI request')
                print(['AGI variables:', request.headers])

            fa_app = Application()
            fa_app.add_route('calls/start', start)
            fa_app.del_route('calls/start')

        """
        if path not in self._route:
            raise ValueError('This route doesn\'t exist.')
        del(self._route[path])

    @asyncio.coroutine
    def handler(self, reader, writer):
        """AsyncIO coroutine handler to launch socket listening.

        :Example:

        ::

            @asyncio.coroutine
            def start(request):
                print('Receive a FastAGI request')
                print(['AGI variables:', request.headers])

            fa_app = Application()
            fa_app.add_route('calls/start', start)
            coro = asyncio.start_server(fa_app.handler, '0.0.0.0', 4574)
            server = loop.run_until_complete(coro)

        See https://docs.python.org/3/library/asyncio-stream.html
        """
        buffer = b''
        while b'\n\n' not in buffer:
            buffer += yield from reader.read(self.buf_size)
        lines = buffer[:-2].decode(self.default_encoding).split('\n')
        headers = OrderedDict([line.split(': ', 1) for line in lines])

        agi_network_script = headers.get('agi_network_script')
        log.info('Received FastAGI request from %r for "%s" route',
                 writer.get_extra_info('peername'), agi_network_script)
        log.debug("Asterisk Headers: %r", headers)

        if agi_network_script is not None:
            route = self._route.get(agi_network_script)
            if route is not None:
                request = Request(app=self,
                                  headers=headers,
                                  reader=reader, writer=writer,
                                  encoding=self.default_encoding)
                try:
                    yield from route(request)
                except Exception as e:
                    log.exception(e)
            else:
                log.error('No route for the request "%s"', agi_network_script)
        else:
            log.error('No agi_network_script header for the request')
        log.debug("Closing client socket")
        writer.close()
