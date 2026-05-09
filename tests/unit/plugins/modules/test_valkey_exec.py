from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest

from ansible_collections.rkozlo.valkey.plugins.modules.valkey_exec import ValkeyExec


@pytest.fixture
def valkey_exec(mocker):
    mock_module = mocker.MagicMock()
    mock_module.check_mode = False
    mock_client = mocker.MagicMock()

    return ValkeyExec(module=mock_module, client=mock_client, command='test_command', args=[], params={})


def test_execute(valkey_exec):
    valkey_exec.client._execute.return_value = 'test_result'

    result = valkey_exec.execute()

    assert result == 'test_result'
    assert valkey_exec.client._execute.called
    assert valkey_exec.client._execute.call_args[0][0] == 'test_command'


def test_execute_check_mode(valkey_exec):
    valkey_exec.module.check_mode = True

    result = valkey_exec.execute()

    assert result == []
    assert not valkey_exec.client._execute.called
