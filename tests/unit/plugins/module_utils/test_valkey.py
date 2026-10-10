from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import to_bytes_data, get_main_conn_kwargs


@pytest.mark.parametrize("value,expected", [
    ("1K", 1000),
    ("128k", 128000),
    ("1m", 1000000),
    ("16M", 16000000),
    ("1G", 1000000000),
    ("31g", 31000000000),
    ("1Kb", 1024),
    ("128KB", 131072),
    ("1Mb", 1048576),
    ("16MB", 16777216),
    ("1Gb", 1073741824),
    ("31GB", 33285996544),
])
def test_normalize_data_values(value, expected):
    result = to_bytes_data(value)
    assert result == expected


def test_get_main_conn_kwargs_default_db(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {
        'login_host': 'localhost',
        'login_port': 6379,
        'login_db': 0,
        'login_user': 'default',
        'login_password': 'pass',
    }
    result = get_main_conn_kwargs(mock_module)
    assert result == {
        'host': 'localhost',
        'port': 6379,
        'username': 'default',
        'password': 'pass',
    }


def test_get_main_conn_kwargs_custom_db(mocker):
    mock_module = mocker.MagicMock()
    mock_module.params = {
        'login_host': 'localhost',
        'login_port': 6379,
        'login_db': 1,
        'login_user': 'default',
        'login_password': 'pass',
    }
    result = get_main_conn_kwargs(mock_module)
    assert result == {
        'host': 'localhost',
        'port': 6379,
        'db': 1,
        'username': 'default',
        'password': 'pass',
    }
