import asyncio
from panoramisk import Manager

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


def main():
    manager.connect()
    try:
        manager.loop.run_forever()
    except KeyboardInterrupt:
        manager.loop.close()


if __name__ == '__main__':
    main()
