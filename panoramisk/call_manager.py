import asyncio
from . import manager
from . import actions
from datetime import datetime
from functools import partial


class Call:

    def __init__(self, uniqueid):
        self.uniqueid = uniqueid
        self.action_id = None
        self.queue = asyncio.Queue()
        self.created_at = datetime.now()

    def append(self, *events):
        for e in events:
            self.queue.put_nowait(e)


class CallManager(manager.Manager):

    def __init__(self, **config):
        super(CallManager, self).__init__(**config)
        self.CallClass = config.get('CallClass', Call)
        self.calls_queues = {}
        self.calls = {}
        self.register_event('*', self.handle_calls)

    def set_result(self, future, result):
        res = result.result()
        if isinstance(res, (list, tuple)):
            event = res[-1]
        else:
            event = res
        uniqueid = event.uniqueid.split('.', 1)[0]
        call = self.calls_queues[uniqueid]
        call.action_id = event.action_id
        future.set_result(call)

    def send_originate(self, action):
        action['Async'] = 'true'
        action = actions.Action(action)
        future = asyncio.Future()
        self.send_action(action).add_done_callback(
            partial(self.set_result, future))
        return future

    def clean_originate(self, call):
        self.calls_queues.pop(call.uniqueid, None)

    def handle_calls(self, manager, event):
        uniqueid = event.uniqueid or event.uniqueid1
        if uniqueid:
            uniqueid = uniqueid.split('.', 1)[0]
            call = self.calls_queues.setdefault(uniqueid, Call(uniqueid))
            call.append(event)
