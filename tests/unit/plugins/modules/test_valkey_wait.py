from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
import valkey.exceptions

from ansible_collections.rkozlo.valkey.plugins.modules.valkey_wait import ValkeyWait


@pytest.fixture
def valkey_wait(mocker):
    mock_module = mocker.MagicMock()
    mock_module.check_mode = False
    mock_module.params = {'interval': 1, 'retries': 1, 'state': 'ready', 'conditions': None}
    mock_client = mocker.MagicMock()

    return ValkeyWait(module=mock_module, client=mock_client)


@pytest.mark.parametrize("exception,expected", [
    (None, 'ready'),
    (valkey.exceptions.ConnectionError, 'down'),
    (valkey.exceptions.BusyLoadingError, 'down'),
    (valkey.exceptions.ResponseError, 'rejected'),
])
def test_wait_for_state(valkey_wait, exception, expected):
    valkey_wait.client.client.ping.side_effect = exception

    assert valkey_wait._wait_for_state() == expected
    valkey_wait.module.fail_json.assert_not_called()


def test_wait_for_state_auth_error_fails(valkey_wait):
    valkey_wait.client.client.ping.side_effect = valkey.exceptions.AuthenticationError('invalid password')

    valkey_wait._wait_for_state()

    valkey_wait.module.fail_json.assert_called_once()
    assert 'Authentication failed' in valkey_wait.module.fail_json.call_args.kwargs['msg']
