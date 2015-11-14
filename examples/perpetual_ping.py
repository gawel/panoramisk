from pprint import pprint
import asyncio
from panoramisk import Manager
import sys


@asyncio.coroutine
def ping(lp, username, secret):
    manager = Manager(loop=lp,
                      host='127.0.0.1', port=5038,
                      username=username, secret=secret)
    yield from manager.connect()
    while True:
        p = yield from manager.send_action({'Action': 'ping'})
        pprint(p)
        yield from asyncio.sleep(0)
    manager.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(ping(loop, sys.argv[1], sys.argv[2]))
loop.close()
