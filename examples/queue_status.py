import asyncio
from panoramisk import Manager
from pprint import pprint


async def queue_status():
    manager = Manager(loop=asyncio.get_event_loop(),
                      host='127.0.0.1', port=5039,
                      username='username', secret='mysecret')
    await manager.connect()
    queues_details = await manager.send_action(
        {'Action': 'QueueStatus', 'Queue': 'queue_name'})
    manager.close()
    pprint(queues_details)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(queue_status())
    loop.close()


if __name__ == '__main__':
    main()
