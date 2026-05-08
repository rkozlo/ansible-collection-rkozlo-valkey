from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest

from ansible_collections.rkozlo.valkey.plugins.modules.valkey_info import ValkeyInfoModule


@pytest.fixture
def valkey_info(mocker):
    mock_module = mocker.MagicMock()
    mock_module.check_mode = False
    mock_client = mocker.MagicMock()

    return ValkeyInfoModule(module=mock_module, client=mock_client, sections=['server'])


def test_execute(valkey_info):

    valkey_info.run()

    assert valkey_info.client._execute.called
    assert valkey_info.client._execute.call_args[0][0] == 'info'
    assert valkey_info.client._execute.call_args[0][1] == 'server'
