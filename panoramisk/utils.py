import re
import uuid
import collections

from configparser import ConfigParser

EOL = '\r\n'

re_code = re.compile(r'(?P<code>^\d*)\s*(?P<response>.*)')
re_kv = re.compile(r'(?P<key>\w+)=(?P<value>[^\s]+)\s*(?:\((?P<data>.*)\))*')


def parse_agi_result(line):
    """Parse AGI results using Regular expression.

    AGI Result examples::

        200 result=0

        200 result=-1

        200 result=132456

        200 result= (timeout)

        510 Invalid or unknown command

        520-Invalid command syntax. Proper usage follows:
        int() argument must be a string, a bytes-like object or a number, not
        'NoneType'

        HANGUP

    """
    # print("--------------\n", line)
    if line == 'HANGUP':
        return {'error': 'AGIResultHangup',
                'msg': 'User hungup during execution'}

    kwargs = dict(code=0, response="", line=line)
    m = re_code.search(line)
    try:
        kwargs.update(m.groupdict())
    except AttributeError:
        # None has no attribute groupdict
        pass
    return agi_code_check(**kwargs)


def agi_code_check(code=None, response=None, line=None):
    """
    Check the AGI code and return a dict to help on error handling.
    """
    code = int(code)
    response = response or ""
    result = {'status_code': code, 'result': ('', ''), 'msg': ''}
    if code == 200:
        for key, value, data in re_kv.findall(response):
            result[key] = (value, data)
            # If user hangs up... we get 'hangup' in the data
            if data == 'hangup':
                return {
                    'error': 'AGIResultHangup',
                    'msg': 'User hungup during execution'}
            elif key == 'result' and value == '-1':
                return {
                    'error': 'AGIAppError',
                    'msg': 'Error executing application, or hangup'}
    elif code == 510:
        result['error'] = 'AGIInvalidCommand'
    elif code == 520:
        # AGI Usage error
        result['error'] = 'AGIUsageError'
        result['msg'] = line
    else:
        # Unhandled code or undefined response
        result['error'] = 'AGIUnknownError'
    return result


class IdGenerator:
    """Generate some uuid for actions:

    .. code-block:: python

        >>> g = IdGenerator('mycounter')

    ..
        >>> IdGenerator.reset(uid='an_uuid4')

    It increments the counter at each calls:

    .. code-block:: python

        >>> print(g())
        mycounter/an_uuid4/1/1
        >>> print(g())
        mycounter/an_uuid4/1/2
    """

    instances = []

    def __init__(self, prefix):
        self.instances.append(self)
        self.prefix = prefix
        self.uid = str(uuid.uuid4())
        self.generator = self.get_generator()

    def get_generator(self):
        i = 0
        max_val = 10000
        while True:
            yield "%s/%s/%d/%d" % (self.prefix,
                                   self.uid, (i // max_val) + 1,
                                   (i % max_val) + 1)
            i += 1

    @classmethod
    def reset(cls, uid=None):
        """Mostly used for unit testing. Allow to use a static uuid and reset
        all counter"""
        for instance in cls.instances:
            if uid:
                instance.uid = uid
            instance.generator = instance.get_generator()

    def get_instances(self):
        """Mostly used for debugging"""
        return ["<%s prefix:%s (uid:%s)>" % (self.__class__.__name__,
                                             i.prefix, self.uid)
                for i in self.instances]

    def __call__(self):
        return next(self.generator)

    def __repr__(self):
        return "<%s prefix:%s (uid:%s)>" % (self.__class__.__name__, self.prefix, self.uid)


class CaseInsensitiveDict(collections.MutableMapping):
    """
    A case-insensitive ``dict``-like object.

    Implements all methods and operations of ``collections.MutableMapping``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive:

    .. code-block:: python

        cid = CaseInsensitiveDict()
        cid['Action'] = 'SIPnotify'
        cid['aCTION'] == 'SIPnotify'  # True
        list(cid) == ['Action']  # True

    For example, ``event['actionid']`` will return the
    value of a ``'ActionID'`` response event, regardless
    of how the event name was originally stored.
    """
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        self.update(data or {}, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __contains__(self, key):
        return key.lower() in self._store

    def __getattr__(self, attr):
        return self.get(attr, '')

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        raise NotImplementedError()

    def __iter__(self):
        return (key for key, value in self._store.values())

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return str(dict(self.items()))


def config(filename_or_fd, section='asterisk'):
    config = ConfigParser()
    if hasattr(filename_or_fd, 'read'):
        config.readfp(filename_or_fd)
    else:
        config.read(filename_or_fd)
    return dict(config.items(section))
