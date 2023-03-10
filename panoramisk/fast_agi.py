import logging
import asyncio
from collections import OrderedDict
from .exceptions import AGIException, AGIUsageError
from .utils import parse_agi_result

log = logging.getLogger(__name__)


class Request:
    def __init__(self, app, headers, reader, writer, encoding='utf-8'):
        self.app = app
        self.headers = headers
        self.reader = reader
        self.writer = writer
        self.encoding = encoding

    async def send_command(self, command):
        """Send a command for FastAGI request:

        :param command: Command to launch on FastAGI request. Ex: 'EXEC StartMusicOnHolds'
        :type command: String

        :Example:

        ::

            async def call_waiting(request):
                print(['AGI variables:', request.headers])
                await request.send_command('ANSWER')
                await request.send_command('EXEC StartMusicOnHold')
                await request.send_command('EXEC Wait 10')

        """
        command += '\n'
        self.writer.write(command.encode(self.encoding))
        await self.writer.drain()

        try:
            agi_result = await self._read_result()
            # If Asterisk returns `100 Trying...`, wait for next the response.
            while agi_result.get('status_code') == 100:
                agi_result = await self._read_result()
        except AGIUsageError as err:
            message = err.args[0]
            # When we get AGIUsageError the following line contains some indication
            buff_usage_error = await self.reader.readline()
            message += buff_usage_error.decode(self.encoding)
            if self.app.raise_on_error:
                raise AGIUsageError(message, err.items)
            agi_result = err.items
            agi_result['error'] = err.__class__.__name__
            agi_result['msg'] = message
        except AGIException as err:
            if self.app.raise_on_error:
                raise
            agi_result = err.items
            agi_result['error'] = err.__class__.__name__
            agi_result['msg'] = err.args[0]

        return agi_result

    async def _read_result(self):
        """Read a response from the AGI and parse it.

        :return dict: The AGI response parsed into a dict.
        """
        response = await self.reader.readline()
        return parse_agi_result(response.decode(self.encoding)[:-1])


class Application(dict):
    """Main object:

    .. code-block:: python

        >>> fa_app = Application()
    """

    buf_size = 100

    def __init__(
            self, default_encoding='utf-8', loop=None, raise_on_error=False, decode_errors='strict'
    ):
        super(Application, self).__init__()
        self.default_encoding = default_encoding
        self.decode_errors = decode_errors
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
        self.loop = loop
        self.raise_on_error = raise_on_error
        self._route = OrderedDict()

    def add_route(self, path, endpoint):
        """Add a route for FastAGI requests:

        :param path: URI to answer. Ex: 'calls/start'
        :type path: String
        :param endpoint: command to launch. Ex: start
        :type endpoint: callable

        :Example:

        ::

            async def start(request):
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

            async def start(request):
                print('Receive a FastAGI request')
                print(['AGI variables:', request.headers])

            fa_app = Application()
            fa_app.add_route('calls/start', start)
            fa_app.del_route('calls/start')

        """
        if path not in self._route:
            raise ValueError('This route doesn\'t exist.')
        del self._route[path]

    async def handler(self, reader, writer):
        """AsyncIO coroutine handler to launch socket listening.

        :Example:

        ::

            async def start(request):
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
            buffer += await reader.read(self.buf_size)
        lines = buffer[:-2].decode(self.default_encoding, errors=self.decode_errors).split('\n')
        headers = OrderedDict([
            line.split(': ', 1) for line in lines if ': ' in line
        ])

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
                    await route(request)
                except BaseException:
                    log.exception(
                        'An exception has been raised for the request "%s"',
                        agi_network_script
                    )
            else:
                log.error('No route for the request "%s"', agi_network_script)
        else:
            log.error('No agi_network_script header for the request')
        log.debug("Closing client socket")
        writer.close()
