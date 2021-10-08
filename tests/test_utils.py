from panoramisk import utils
from panoramisk.exceptions import AGIException


def test_parse_agi_valid_result():
    res = try_parse_agi_result('200 result=0')
    assert res == {'msg': '', 'result': ('0', ''), 'status_code': 200}

    res = try_parse_agi_result('200 result=1')
    assert res == {'msg': '', 'result': ('1', ''), 'status_code': 200}

    res = try_parse_agi_result('200 result=1234')
    assert res == {'msg': '', 'result': ('1234', ''), 'status_code': 200}

    res = try_parse_agi_result('200 result= (timeout)')
    assert res == {'msg': '', 'result': ('', 'timeout'), 'status_code': 200}


def test_parse_agi_invalid_result():
    res = try_parse_agi_result('510 Invalid or unknown command')
    assert res == {'msg': '510 Invalid or unknown command',
                   'error': 'AGIInvalidCommand',
                   'status_code': 510}

    res = try_parse_agi_result('520 Use this')
    assert res == {'msg': '520 Use this',
                   'error': 'AGIUsageError',
                   'status_code': 520}


def try_parse_agi_result(result):
    try:
        res = utils.parse_agi_result(result)
    except AGIException as err:
        res = err.items
        res['error'] = err.__class__.__name__
        res['msg'] = err.args[0]

    return res
