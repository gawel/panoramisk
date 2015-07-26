import asyncio
from panoramisk import Manager
from pprint import pprint

loop = asyncio.get_event_loop()


@asyncio.coroutine
def queue_status():
    MANAGER = Manager(loop=asyncio.get_event_loop(), host='127.0.0.1', username='user', secret='password')
    yield from MANAGER.connect()
    queues_details = yield from MANAGER.send_action({'Action': 'QueueStatus', 'Queue': 'queue_name'})
    pprint(queues_details)

loop.run_until_complete(queue_status())
