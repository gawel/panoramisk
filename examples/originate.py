"""
Example script to originate a call through Asterisk Manager Interface.

Usage: python originate.py config.ini

"""
import sys
import asyncio
from panoramisk.call_manager import CallManager


async def originate():
    callmanager = CallManager.from_config(sys.argv[1])
    await callmanager.connect()
    call = await callmanager.send_originate({
        'Action': 'Originate',
        'Channel': 'Local/gpasgrimaud@bearstech',
        'WaitTime': 20,
        'CallerID': 'gawel',
        'Exten': '1000',
        'Context': 'ael-demo',
        'Priority': 1})
    print(call)
    while not call.queue.empty():
        event = call.queue.get_nowait()
        print(event)
    while True:
        event = await call.queue.get()
        print(event)
        if event.event.lower() == 'hangup' and event.cause in ('0', '17'):
            break
    callmanager.clean_originate(call)
    callmanager.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(originate())
    loop.close()


if __name__ == '__main__':
    main()
