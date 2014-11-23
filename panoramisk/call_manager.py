# -*- coding: utf-8 -*-
from . import manager
from . import utils
from . import actions
from datetime import datetime


class Call(object):

    def __init__(self, uniqueid):
        self.uniqueid = uniqueid
        self.action_id = None
        self.queue = utils.Queue()
        self.created_at = datetime.now()

    def append(self, event):
        self.queue.put_nowait(event)


class Manager(manager.Manager):

    def __init__(self, *args, **kwargs):
        super(Manager, self).__init__(*args, **kwargs)
        self.CallClass = kwargs.get('CallClass', Call)
        self.calls_queues = {}
        self.calls = {}
        self.register_event('*', self.handle_calls)

    def send_originate(self, action):
        action['Async'] = 'true'
        action = actions.Action(action)
        future = utils.asyncio.Future()
        self.calls[action.action_id] = future
        self.send_action(action)
        return future

    def clean_originate(self, call):
        self.calls.pop(call.action_id, None)
        self.calls_queues.pop(call.uniqueid, None)

    def handle_calls(self, manager, event):
        uniqueid = event.uniqueid or event.uniqueid1
        if uniqueid:
            uniqueid = uniqueid.split('.', 1)[0]
            call = self.calls_queues.setdefault(uniqueid, Call(uniqueid))
            call.append(event)
            if event.event == 'OriginateResponse':
                call.action_id = event.action_id
                self.calls[event.action_id].set_result(call)
