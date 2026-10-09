from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest

from ansible_collections.rkozlo.valkey.plugins.modules.valkey_config import ValkeyConfig


@pytest.fixture
def valkey_config(mocker):
    mock_module = mocker.MagicMock()
    mock_module.check_mode = False
    mock_client = mocker.MagicMock()

    return ValkeyConfig(module=mock_module, client=mock_client, strict=False, config_rewrite=False)


def test_setup_object(valkey_config):
    assert valkey_config.module is not None
    assert valkey_config.client is not None
    assert valkey_config._config is None
    assert valkey_config._version_config is None


def test_load_configs(valkey_config):
    valkey_config.client.version = {'full': '9.1.2', 'major': 9, 'minor': 1, 'feature': 2}
    valkey_config._load_configs()
    assert valkey_config._version_config is not None
    assert valkey_config._version_config['maxmemory']['immutable'] is False


@pytest.mark.parametrize("settings,expected", [
    ({'mamemory_policy': 'allkeys-lfu'}, {'mamemory_policy': 'allkeys-lfu'}),
    ({'mamemory_policy': 'volatile-ttl'}, {}),
    ({'mamemory_policy': 'allkeys-lfu', 'bind': '0.0.0.1'}, {'mamemory_policy': 'allkeys-lfu', 'bind': '0.0.0.1'}),
    ({'mamemory_policy': 'allkeys-lfu', 'bind': '0.0.0.0'}, {'mamemory_policy': 'allkeys-lfu'}),
    ({'mamemory_policy': 'allkeys-lfu', 'activedefrag': 'yes'}, {'mamemory_policy': 'allkeys-lfu'}),
    ({'mamemory_policy': 'allkeys-lfu', 'activedefrag': 'no'}, {'mamemory_policy': 'allkeys-lfu', 'activedefrag': 'no'}),
])
def test_get_diff_runtime_configs(valkey_config, settings, expected):
    valkey_config._config = {
        'mamemory_policy': 'volatile-ttl',
        'bind': '0.0.0.0',
        'activedefrag': 'yes',
        'save': '',
    }
    result = valkey_config.get_diff_runtime_configs(settings)
    valkey_config.module.fail_json.assert_not_called()
    assert result == expected


@pytest.mark.parametrize("value,expected", [
    ("1000", "1000"),
])
def test_normalize_values(valkey_config, value, expected):
    result = valkey_config.normalize_value(value)
    assert result == expected


def test_load_configs_unsupported_version(valkey_config):
    valkey_config.module.fail_json.side_effect = SystemExit
    valkey_config.client.version = {'full': '99.0.0', 'major': 99, 'minor': 0, 'patch': 0}
    with pytest.raises(SystemExit):
        valkey_config._load_configs()
    assert 'Valkey 99.0 is not supported yet' in valkey_config.module.fail_json.call_args.kwargs['msg']


def test_is_immutable_attr_unknown_config(valkey_config):
    valkey_config.module.fail_json.side_effect = SystemExit
    valkey_config.client.version = {'full': '9.1.2', 'major': 9, 'minor': 1, 'patch': 2}
    with pytest.raises(SystemExit):
        valkey_config.is_immutable_attr('not-existing-config')
    assert 'Config not-existing-config is not known' in valkey_config.module.fail_json.call_args.kwargs['msg']
