import sys
import asyncio
from panoramisk.call_manager import Manager

loop = asyncio.get_event_loop()


@asyncio.coroutine
def originate():
    manager = Manager.from_config(sys.argv[1])
    yield from manager.connect()
    call = yield from manager.send_originate({
        'Action': 'Originate',
        'Channel': 'Local/gpasgrimaud@bearstech',
        'WaitTime': 20,
        'CallerID': 'gawel',
        'Exten': '4260',
        'Context': 'bearstech',
        'Priority': 1})
    print(call)
    while not call.queue.empty():
        event = call.queue.get_nowait()
        print(event)
    while True:
        event = yield from call.queue.get()
        print(event)
        if event.event.lower() == 'hangup' and event.cause in ('0', '17'):
            break
    manager.clean_originate(call)

loop.run_until_complete(originate())
