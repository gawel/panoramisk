import asyncio
from panoramisk import Manager

manager = Manager(loop=asyncio.get_event_loop(),
                  host='ip',
                  username='user',
                  secret='secret')


@manager.register_event('*')
def callback(manager, message):
    if "FullyBooted" not in message.event:
        """This will print every event, but the FullyBooted events as these
        will continuously spam your screen"""
        print(message)


"""
# This will print NewChannel Events
@manager.register_event('NewChannel')
def callback(manager, message):
    print(message)


# This will print Hangup Events
@manager.register_event('Hangup')
def callback(manager, message):
    print(message)
"""


def main():
    manager.connect()
    try:
        manager.loop.run_forever()
    except KeyboardInterrupt:
        manager.loop.close()


if __name__ == '__main__':
    main()
