from panoramisk import utils


def test_parse_agi_valid_result():
    res = utils.parse_agi_result('200 result=0')
    assert res == {'msg': '', 'result': ('0', ''), 'status_code': 200}

    res = utils.parse_agi_result('200 result=1')
    assert res == {'msg': '', 'result': ('1', ''), 'status_code': 200}

    res = utils.parse_agi_result('200 result=1234')
    assert res == {'msg': '', 'result': ('1234', ''), 'status_code': 200}

    res = utils.parse_agi_result('200 result= (timeout)')
    assert res == {'msg': '', 'result': ('', ''), 'status_code': 200}


def test_parse_agi_invalid_result():
    res = utils.parse_agi_result('510 Invalid or unknown command')
    assert res == {'msg': '', 'result': ('', ''),
                   'error': 'AGIInvalidCommand',
                   'status_code': 510}

    res = utils.parse_agi_result('520 Use this')
    assert res == {'msg': '520 Use this', 'result': ('', ''),
                   'error': 'AGIUsageError',
                   'status_code': 520}
