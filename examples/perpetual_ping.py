from pprint import pprint
import asyncio
from panoramisk import Manager
import sys


async def ping(lp, username, secret):
    manager = Manager(loop=lp,
                      host='127.0.0.1', port=5038,
                      username=username, secret=secret,
                      forgetable_actions=('login',))
    await manager.connect()
    while True:
        p = await manager.send_action({'Action': 'ping'})
        # p = await manager.send_action({'Action': 'SIPpeers'})
        pprint(p)
        await asyncio.sleep(1)
    manager.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ping(loop, sys.argv[1], sys.argv[2]))
    loop.close()


if __name__ == '__main__':
    main()
