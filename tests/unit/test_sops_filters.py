"""Tests for filter_plugins/sops_filters.py

The sops_filters provide dict_selectattr and dict_rejectattr for reliable
dict key access in lists of dicts, used by the SOPS update tasks.
"""

import pytest
from filter_plugins.sops_filters import (
    dict_selectattr,
    dict_rejectattr,
    FilterModule,
)

# Sample data used by update_sops_secrets tasks (dict2items output)
DICT2ITEMS_SAMPLE = [
    {"key": "api_token", "value": "new-token-12345"},
    {"key": "database_password", "value": "new-password-67890"},
    {"key": "old_key", "value": ""},
]

# Simulates registered task results (sops set/unset loop)
SHELL_RESULTS = [
    {"item": "key1", "rc": 0, "stdout": "ok", "stderr": ""},
    {"item": "key2", "rc": 1, "stdout": "", "stderr": "key not found"},
    {"item": "key3", "rc": 0, "stdout": "ok", "stderr": ""},
    {"item": "key4", "rc": 2, "stdout": "", "stderr": "permission denied"},
]

STAT_RESULTS = [
    {"item": "/etc/a.conf", "stat": {"exists": True, "size": 100}},
    {"item": "/etc/b.conf", "stat": {"exists": False, "size": 0}},
    {"item": "/etc/c.conf", "stat": {"exists": True, "size": 50}},
]


# ===========================================================================
# dict_selectattr — eq (used for sops_keys_to_unset: value eq '')
# ===========================================================================
class TestDictSelectattrEq:
    def test_eq_empty_string_selects(self):
        result = dict_selectattr(DICT2ITEMS_SAMPLE, "value", "eq", "")
        assert len(result) == 1
        assert result[0]["key"] == "old_key"

    def test_eq_nested_stat_exists(self):
        result = dict_selectattr(STAT_RESULTS, "stat.exists", "eq", True)
        assert len(result) == 2

    def test_eq_rc_zero(self):
        result = dict_selectattr(SHELL_RESULTS, "rc", "eq", 0)
        assert len(result) == 2


# ===========================================================================
# dict_selectattr — ne (used for sops_keys_to_set: value ne '')
# ===========================================================================
class TestDictSelectattrNe:
    def test_ne_empty_string_filters_out(self):
        result = dict_selectattr(DICT2ITEMS_SAMPLE, "value", "ne", "")
        assert len(result) == 2
        assert [d["key"] for d in result] == ["api_token", "database_password"]

    def test_ne_rc_nonzero(self):
        result = dict_selectattr(SHELL_RESULTS, "rc", "ne", 0)
        assert len(result) == 2
        assert [d["item"] for d in result] == ["key2", "key4"]


# ===========================================================================
# dict_selectattr — none (used for dict_rejectattr value none)
# ===========================================================================
class TestDictSelectattrNone:
    def test_none_selects_missing_or_none(self):
        data = [{"k": "a", "v": None}, {"k": "b", "v": "ok"}, {"k": "c"}]
        result = dict_selectattr(data, "v", "none")
        assert len(result) == 2


# ===========================================================================
# dict_selectattr — search (used for stderr search 'key not found')
# ===========================================================================
class TestDictSelectattrSearch:
    def test_search_key_not_found(self):
        result = dict_selectattr(SHELL_RESULTS, "stderr", "search", "key not found")
        assert len(result) == 1
        assert result[0]["item"] == "key2"

    def test_search_regex_alias(self):
        result = dict_selectattr(SHELL_RESULTS, "stderr", "regex", "key not found")
        assert len(result) == 1


# ===========================================================================
# dict_selectattr — defined, truthy
# ===========================================================================
class TestDictSelectattrDefined:
    def test_defined_all_have_key(self):
        result = dict_selectattr(DICT2ITEMS_SAMPLE, "key", "defined")
        assert len(result) == 3

    def test_defined_nested(self):
        result = dict_selectattr(STAT_RESULTS, "stat.exists", "defined")
        assert len(result) == 3


class TestDictSelectattrTruthy:
    def test_truthy_default(self):
        data = [{"v": ""}, {"v": "x"}, {"v": None}]
        result = dict_selectattr(data, "v")
        assert len(result) == 1
        assert result[0]["v"] == "x"


# ===========================================================================
# dict_selectattr — match
# ===========================================================================
class TestDictSelectattrMatch:
    def test_match_prefix(self):
        result = dict_selectattr(DICT2ITEMS_SAMPLE, "key", "match", "^api_")
        assert len(result) == 1
        assert result[0]["key"] == "api_token"


# ===========================================================================
# dict_rejectattr (inverse of dict_selectattr)
# ===========================================================================
class TestDictRejectattr:
    def test_rejectattr_eq(self):
        result = dict_rejectattr(DICT2ITEMS_SAMPLE, "value", "eq", "")
        assert len(result) == 2
        assert [d["key"] for d in result] == ["api_token", "database_password"]

    def test_rejectattr_search_key_not_found(self):
        result = dict_rejectattr(SHELL_RESULTS, "stderr", "search", "key not found")
        assert len(result) == 3
        assert all(d["item"] != "key2" for d in result)

    def test_rejectattr_rc_ne_zero(self):
        result = dict_rejectattr(SHELL_RESULTS, "rc", "ne", 0)
        assert len(result) == 2
        assert all(d["rc"] == 0 for d in result)


# ===========================================================================
# FilterModule
# ===========================================================================
class TestFilterModule:
    def test_filters_returns_dict(self):
        fm = FilterModule()
        filters = fm.filters()
        assert isinstance(filters, dict)

    def test_filters_has_dict_selectattr_and_dict_rejectattr(self):
        fm = FilterModule()
        filters = fm.filters()
        assert "dict_selectattr" in filters
        assert "dict_rejectattr" in filters
        assert filters["dict_selectattr"] is dict_selectattr
        assert filters["dict_rejectattr"] is dict_rejectattr


# ===========================================================================
# Unknown test raises
# ===========================================================================
class TestUnknownTest:
    def test_unknown_test_raises(self):
        with pytest.raises(ValueError, match="unknown test"):
            dict_selectattr(DICT2ITEMS_SAMPLE, "key", "bogus", "val")
