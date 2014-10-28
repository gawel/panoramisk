# -*- coding: utf-8 -*-
from requests.structures import CaseInsensitiveDict
from . import utils


class Message(object):
    """Handle both Responses and Events with the same api:

    ..
        >>> resp = Message('response', 'Response body',
        ...                {'Response': 'Follows'})
        >>> event = Message('event', '',
        ...                {'Event': 'MeetmeEnd', 'Meetme': '4242'})

    Responses:

    .. code-block:: python

        >>> print(resp.message_type)
        response
        >>> bool(resp.success)
        True
        >>> resp.headers
        {'Response': 'Follows'}
        >>> print(resp.content)
        Response body
        >>> for line in resp.iter_lines():
        ...     print(resp.content)
        Response body

    Events:

    .. code-block:: python

        >>> print(event.message_type)
        event
        >>> print(event.name)
        MeetmeEnd
        >>> print(event['meetme'])
        4242
        >>> print(event.meetme)
        4242
        >>> print(event.unknown_header)
        None

    """

    def __init__(self, content, headers=None):
        self.content = content
        self.headers = CaseInsensitiveDict(headers)
        self.manager = self.name = None,
        self.orig = None

    @property
    def id(self):
        if 'commandid' in self.headers:
            return self.headers['commandid']
        elif 'actionid' in self.headers:
            return self.headers['actionid']
        return None

    @property
    def success(self):
        """return True if a response status is Success or Follows:

        .. code-block:: python

            >>> resp = Message('response', '', {'Response': 'Success'})
            >>> print(resp.success)
            Success
            >>> resp.headers['Response'] = 'Failed'
            >>> resp.success
            False
        """
        if self.message_type == 'event':
            return True
        status = self.headers['response']
        if status in ('Success', 'Follows'):
            return 'Success'
        return False

    def __getitem__(self, attr):
        return self.headers[attr]

    def __getattr__(self, attr):
        return self.headers.get(attr, None)

    def __contains__(self, value):
        return value in self.headers

    def __repr__(self):
        return '<{0} headers:{1} content:"{2}">'.format(
            self.message_type.title(), self.headers, self.content)

    def iter_lines(self):
        """Iter over response body"""
        for line in self.content.split('\n'):
            yield line

    @property
    def lheaders(self):
        """return headers with lower keys:

        .. code-block:: python

            >>> resp = Message('response', '', {'Ping': 'Pong'})
            >>> print(resp.lheaders)
            {'ping': 'Pong'}
        """
        h = {}
        for k, v in self.headers.items():
            h[k.lower()] = v
        return h

    @classmethod
    def from_line(cls, line, patterns=None):
            mlines = line.split(utils.EOL)
            headers = CaseInsensitiveDict()
            content = ''
            has_body = ('Response: Follows', 'Response: Fail')
            if mlines[0].startswith(has_body):
                content = mlines.pop()
                while not content and mlines:
                    content = mlines.pop()
            for mline in mlines:
                if ': ' in mline:
                    k, v = mline.split(': ', 1)
                    if k in headers:
                        o = headers.setdefault(k, [])
                        if not isinstance(o, list):
                            o = [o]
                        o.append(v)
                        headers[k] = o
                    else:
                        headers[k] = v
            return cls(content, headers)
