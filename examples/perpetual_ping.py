from pprint import pprint
import asyncio
from panoramisk import Manager


async def ping():
    manager = Manager(host='127.0.0.1', port=5038,
                      username='username', secret='mysecret',
                      forgetable_actions=('login',))
    await manager.connect()
    while True:
        p = await manager.send_action({'Action': 'ping'})
        # p = await manager.send_action({'Action': 'SIPpeers'})
        pprint(p)
        await asyncio.sleep(1)
    manager.close()


def main():
    asyncio.run(ping())


if __name__ == '__main__':
    main()
