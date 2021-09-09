import asyncio

import pytest

from panoramisk import Manager


@pytest.mark.asyncio
async def test_reconnection_without_lost(event_loop, asterisk):
    manager = Manager(loop=event_loop,
                      host='127.0.0.1',
                      username='username',
                      secret='mysecret')
    asterisk.start()

    await manager.connect()
    await manager.send_action({'Action': 'Ping'})

    asterisk.stop()

    manager.send_action({'Action': 'Ping'})
    f = manager.send_action({'Action': 'Status'})

    await asyncio.sleep(.1)
    assert manager.awaiting_actions
    asterisk.start()
    assert manager.awaiting_actions
    await asyncio.sleep(.5)
    assert not manager.awaiting_actions
    async for message in f:
        assert message.eventlist.lower() in ("start", "complete"), message
