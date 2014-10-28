# -*- coding: utf-8 -*-

import pytest


@pytest.fixture
def inject_file():
    return __file__

