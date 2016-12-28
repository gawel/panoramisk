from pprint import pprint
import asyncio
from panoramisk import fast_agi

loop = asyncio.get_event_loop()


@asyncio.coroutine
def call_waiting(request):
    pprint(['AGI variables:', request.headers])

    pprint((yield from request.send_command('ANSWER')))
    pprint((yield from request.send_command('SAY DIGITS 1 \"\"')))

    # To Raise a 510 error - 510 Invalid or unknown command
    pprint((yield from request.send_command('INVALID-COMMAND')))

    # To Raise a 520 error - 520-Invalid command syntax. Proper usage follows:
    pprint((yield from request.send_command('SAY PHONETIC Hello world .')))

    pprint((yield from request.send_command('SAY NUMBER 100 \"\"')))
    pprint((yield from request.send_command('GET DATA hello-world 5000 2')))

    pprint((yield from request.send_command('EXEC StartMusicOnHold')))
    pprint((yield from request.send_command('EXEC Wait 30')))


def main():
    fa_app = fast_agi.Application(loop=loop)
    fa_app.add_route('call_waiting', call_waiting)
    coro = asyncio.start_server(fa_app.handler, '0.0.0.0', 4574, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until CTRL+c is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    main()
