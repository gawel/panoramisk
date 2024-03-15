from panoramisk.message import Message
from panoramisk import utils
import pytest


@pytest.fixture
def message():
    def _message(data):
        return Message.from_line(data)
    EOL = utils.EOL
    utils.EOL = '\n'
    yield _message
    utils.EOL = EOL


def test_multivalue(message):
    m = message('''
Event: X
Value: X
Value: Y
''')
    assert m.value == ['X', 'Y']


def test_content(message):
    m = message('''\
Response: Follows
--- blah ---
''')
    assert m.content == '--- blah ---'


@pytest.mark.parametrize('msg', [
    Message(
        {
            'Response': 'Success',
            'ChanVariable': ['FROM_DID=', 'SIPURI=sip:42@10.10.10.1:4242'],
        }
    ),
    Message(
        {
            'Response': 'Success',
            'ChanVariable': 'var',
        }
    )
]
                         )
def test_getdict(msg):
    assert isinstance(msg.getdict('chanvariable'), utils.CaseInsensitiveDict)
    for k, v in msg.getdict('chanvariable').items():
        assert isinstance(k, str)
        assert isinstance(v, str)
