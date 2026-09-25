from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
from ansible_collections.rkozlo.valkey.plugins.module_utils.valkey import to_bytes_data


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
