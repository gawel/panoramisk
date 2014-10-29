from pprint import pprint
import asyncio

from panoramisk import Manager


# logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()

@asyncio.coroutine
def originate():
    manager = Manager(loop=asyncio.get_event_loop(), host='127.0.0.1', username='user', secret='password')
    yield from manager.connect()
    result = yield from manager.send_action({'Action': 'Originate',
                                             'Channel': 'SIP/gawel',
                                             'WaitTime': 20,
                                             'CallerID': 'gawel',
                                             'Exten': '0299999999',
                                             'Context': 'default',
                                             'Priority': 1,})
    pprint(result)

loop.run_until_complete(originate())