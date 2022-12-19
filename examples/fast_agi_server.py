from pprint import pprint
import asyncio
from panoramisk import fast_agi


async def call_waiting(request):
    pprint(['AGI variables:', request.headers])
    pprint((await request.send_command('ANSWER')))
    pprint((await request.send_command('EXEC StartMusicOnHold')))
    pprint((await request.send_command('EXEC Wait 30')))


async def main():
    fa_app = fast_agi.Application()
    fa_app.add_route('call_waiting', call_waiting)
    server = await asyncio.start_server(fa_app.handler, '0.0.0.0', 4574)

    # Serve requests until CTRL+c is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        await server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Close the server
        server.close()


if __name__ == '__main__':
    asyncio.run(main())
