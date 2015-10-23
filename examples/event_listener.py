import asyncio
from panoramisk import Manager
from pprint import pprint


manager = Manager(loop=asyncio.get_event_loop(),
                  host='ip',
                  username='user',
                  secret='secret')


@manager.register_event('*')
def callback(event, manager):
    if "FullyBooted" not in manager.event:
        """This will print every event, but the FullyBooted events as these
        will continuously spam your screen"""
        print(manager)


@asyncio.coroutine
def keep_alive():
    while True:
        yield from asyncio.sleep(.001)


def main():
    manager.connect()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(keep_alive())
    finally:
        loop.close()

if __name__ == '__main__':
    main()
