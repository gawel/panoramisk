import asyncio
from panoramisk import Manager
from pprint import pprint


async def queue_status():
    manager = Manager(host='127.0.0.1', port=5038,
                      username='username', secret='mysecret')
    await manager.connect()
    action = {'Action': 'QueueStatus', 'Queue': 'queue_name'}
    async for message in manager.send_action(action):
        pprint(message)
    manager.close()


def main():
    asyncio.run(queue_status())


if __name__ == '__main__':
    main()
