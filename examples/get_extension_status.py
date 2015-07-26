from pprint import pprint
import asyncio
from panoramisk import Manager

loop = asyncio.get_event_loop()


@asyncio.coroutine
def extension_status():
    manager = Manager(loop=asyncio.get_event_loop(), host='127.0.0.1', username='user', secret='password')
    yield from manager.connect()
    extension = yield from manager.send_action({'Action': 'ExtensionState',
                                                'Exten': '2001',
                                                'Context': 'default'})
    pprint(extension)

loop.run_until_complete(extension_status())
