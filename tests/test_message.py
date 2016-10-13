from panoramisk.message import Message
from panoramisk import utils
import pytest


@pytest.yield_fixture
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
