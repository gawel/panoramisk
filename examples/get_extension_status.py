from pprint import pprint
import asyncio
from panoramisk import Manager


async def extension_status():
    manager = Manager(loop=asyncio.get_event_loop(),
                      host='127.0.0.1', port=5038,
                      username='username', secret='mysecret')
    await manager.connect()
    action = {
        'Action': 'ExtensionState',
        'Exten': '2001',
        'Context': 'default',
    }
    extension = await manager.send_action(action)
    pprint(extension)
    manager.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(extension_status())
    loop.close()


if __name__ == '__main__':
    main()
