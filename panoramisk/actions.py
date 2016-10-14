import asyncio
from . import utils


class Action(utils.CaseInsensitiveDict):
    """Dict like object to handle actions.
    Generate action IDs for you:

    ..
        >>> utils.IdGenerator.reset('myuuid')

    .. code-block:: python

        >>> action = Action({'Action': 'Status'})
        >>> print(action) # doctest: +NORMALIZE_WHITESPACE
        Action: Status
        ActionID: action/myuuid/1/1

        >>> action = Action({'Action': 'SIPnotify',
        ...                  'Variable': ['1', '2']})
        >>> print(action) # doctest: +NORMALIZE_WHITESPACE
        Action: SIPnotify
        ActionID: action/myuuid/1/2
        Variable: 1
        Variable: 2
    """

    action_id_generator = utils.IdGenerator('action')

    def __init__(self, *args, **kwargs):
        self.as_list = kwargs.pop('as_list', False)
        super(Action, self).__init__(*args, **kwargs)
        if 'actionid' not in self:
            self['ActionID'] = self.action_id_generator()
        self.responses = []
        self.future = asyncio.Future()

    @property
    def id(self):
        return self.actionid

    action_id = id

    def __str__(self):
        action = []
        for k, v in sorted(self.items()):
            if isinstance(v, (list, tuple)):
                action.extend(['%s: %s' % (k, i) for i in v])
            else:
                action.append('%s: %s' % (k, v))
        action.append(utils.EOL)
        return utils.EOL.join(action)

    @property
    def multi(self):
        resp = self.responses[0]
        msg = resp.message.lower()
        if resp.subevent == 'Start':
            return True
        elif 'EventList' in resp and resp['EventList'] == 'start':
            return True
        elif 'will follow' in msg:
            return True
        elif msg.startswith('added') and msg.endswith('to queue'):
            return True
        elif msg.endswith('successfully queued') and self.async != 'false':
            return True
        elif self.as_list:
            return True
        return False

    @property
    def completed(self):
        resp = self.responses[-1]
        if resp.event.endswith('Complete'):
            return True
        elif resp.subevent in ('End', 'Exec'):
            return True
        elif resp.response in ('Success', 'Error', 'Fail', 'Failure'):
            return True
        elif not self.multi:
            return True
        return False

    def add_message(self, message):
        self.responses.append(message)
        multi = self.multi
        if self.completed:
            if multi and len(self.responses) > 1:
                self.future.set_result(self.responses)
            elif not multi:
                self.future.set_result(self.responses[0])
            else:
                return False
            return True


class Command(Action):
    """Dict like object to handle Commands.
    Generate action/command IDs for you:

    ..
        >>> utils.IdGenerator.reset('myuuid')

    .. code-block:: python

        >>> command = Command({'Command' : 'Do something'})
        >>> print(command) # doctest: +NORMALIZE_WHITESPACE
        Action: Command
        ActionID: action/myuuid/1/1
        Command: Do something
        CommandID: command/myuuid/1/1
    """

    command_id_generator = utils.IdGenerator('command')

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        if 'action' not in self:
            self['Action'] = 'Command'
        if 'commandid' not in self:
            self['CommandID'] = self.command_id_generator()

    @property
    def id(self):
        return self.commandid

    @property
    def action_id(self):
        return self.actionid or None
