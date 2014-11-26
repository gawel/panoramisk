# -*- coding: utf-8 -*-
from . import manager
from . import utils
from . import actions
from datetime import datetime
from functools import partial


class Call(object):

    def __init__(self, uniqueid):
        self.uniqueid = uniqueid
        self.action_id = None
        self.queue = utils.Queue()
        self.created_at = datetime.now()

    def append(self, *events):
        for e in events:
            self.queue.put_nowait(e)


class Manager(manager.Manager):

    def __init__(self, *args, **kwargs):
        super(Manager, self).__init__(*args, **kwargs)
        self.CallClass = kwargs.get('CallClass', Call)
        self.calls_queues = {}
        self.calls = {}
        self.register_event('*', self.handle_calls)

    def set_result(self, future, result):
        event = result.result()[-1]
        uniqueid = event.uniqueid.split('.', 1)[0]
        call = self.calls_queues[uniqueid]
        call.action_id = event.action_id
        future.set_result(call)

    def send_originate(self, action):
        action['Async'] = 'true'
        action = actions.Action(action)
        future = utils.asyncio.Future()
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
