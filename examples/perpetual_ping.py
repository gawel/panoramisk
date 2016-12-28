from pprint import pprint
import asyncio
from panoramisk import Manager
import sys


@asyncio.coroutine
def ping(lp, username, secret):
    manager = Manager(loop=lp,
                      host='127.0.0.1', port=5038,
                      username=username, secret=secret,
                      forgetable_actions=('login',))
    yield from manager.connect()
    while True:
        p = yield from manager.send_action({'Action': 'ping'})
        # p = yield from manager.send_action({'Action': 'SIPpeers'})
        pprint(p)
        yield from asyncio.sleep(1)
    manager.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ping(loop, sys.argv[1], sys.argv[2]))
    loop.close()


if __name__ == '__main__':
    main()
