import logging
import os

from panoramisk import Manager, Message


manager = Manager(
    host=os.getenv('AMI_HOST', '127.0.0.1'),
    port=os.getenv('AMI_PORT', 5038),
    username=os.getenv('AMI_USERNAME', 'username'),
    secret=os.getenv('AMI_SECRET', 'mysecret'),
    auth_type='md5',      # MD5 auth, no case sensitive
    ping_delay=10,        # Delay after start
    ping_interval=10,     # Periodically ping AMI (dead or alive)
    reconnect_timeout=2,  # Timeout reconnect if connection lost
)


@manager.register_event('*')  # Register all events
async def ami_callback(mngr: Manager, msg: Message):
    if msg.Event == 'FullyBooted':
        print(msg)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    manager.connect(run_forever=True)
