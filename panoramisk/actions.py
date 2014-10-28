# -*- coding: utf-8 -*-
from .utils import asyncio
from . import utils


class Action(dict):
    """Dict like object to handle actions. Generate action ids for you:

    ..
        >>> utils.IdGenerator.reset('myuuid')

    .. code-block:: python

        >>> action = Action({'Action': 'Status'})
        >>> print(action) # doctest: +NORMALIZE_WHITESPACE
        Action: Status
        ActionID: action/myuuid/1/1
    """

    action_id_generator = utils.IdGenerator('action')

    def __init__(self, *args, **kwargs):
        self.as_list = kwargs.pop('as_list', False)
        super(Action, self).__init__(*args, **kwargs)
        if 'ActionID' not in self:
            self['ActionID'] = self.action_id_generator()
        self.responses = []
        self.future = asyncio.Future()

    @property
    def id(self):
        return self['ActionID']

    action_id = id

    def __str__(self):
        action = [': '.join(i) for i in sorted(self.items())]
        action.append(utils.EOL)
        return utils.EOL.join(action)

    @property
    def multi(self):
        headers = self.responses[0].headers
        if headers.get('SubEvent', '') == 'Start':
            return True
        elif 'will follow' in headers.get('Message', ''):
            return True
        elif 'Complete' in headers.get('Event', ''):
            return True
        elif self.as_list:
            return True
        return False

    @property
    def completed(self):
        resp = self.responses[-1]
        if resp.headers.get('Event', '').endswith('Complete'):
            return True
        elif resp.headers.get('SubEvent', '') == 'End':
            return True
        elif not self.multi:
            return True
        return False

    def add_message(self, message):
        self.responses.append(message)
        if self.completed:
            if self.multi:
                self.future.set_result(self.responses)
            else:
                self.future.set_result(self.responses[0])
            return True


class Command(Action):
    """Dict like object to handle actions. Generate action ids for you:

    ..
        >>> utils.IdGenerator.reset('myuuid')

    .. code-block:: python

        >>> command = Command({'Command' : 'Do something'})
        >>> print(command) # doctest: +NORMALIZE_WHITESPACE
        Action: AGI
        ActionID: action/myuuid/1/1
        Command: Do something
        CommandID: command/myuuid/1/1
    """

    command_id_generator = utils.IdGenerator('command')

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        if 'Action' not in self:
            self['Action'] = 'AGI'
        if 'CommandID' not in self:
            self['CommandID'] = self.command_id_generator()

    @property
    def id(self):
        return self['CommandID']
