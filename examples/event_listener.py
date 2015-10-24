import asyncio
from panoramisk import Manager
from pprint import pprint
from aiohttp.web import Application

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


"""
# This will print NewChannel Events
@manager.register_event('NewChannel')
def callback(event, manager):
    print(manager)


# This will print Hangup Events
@manager.register_event('Hangup')
def callback(event, manager):
    print(manager)
"""


@asyncio.coroutine
def init(loop):
    app = Application(loop=loop)
    handler = app.make_handler()
    srv = yield from loop.create_server(handler, '127.0.0.1', 8080)
    return srv, handler


def main():
    manager.connect()
    loop = asyncio.get_event_loop()
    srv, handler = loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(handler.finish_connections())
    finally:
        loop.close()

if __name__ == '__main__':
    main()
