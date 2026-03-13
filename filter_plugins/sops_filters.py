# Filters for reliable dict key access in lists of dicts.
# Uses bracket notation for compatibility with plain dicts across Ansible/Jinja2 versions.

from __future__ import absolute_import, division, print_function

import re

_MISSING = object()


def _deep_get(obj, key, default=None):
    parts = key.split('.') if isinstance(key, str) and '.' in key else [key]
    val = obj
    for part in parts:
        if val is None:
            return default
        if isinstance(val, dict):
            val = val.get(part, _MISSING)
            if val is _MISSING:
                return default
        elif isinstance(val, (list, tuple)) and part.isdigit():
            idx = int(part)
            if idx < len(val):
                val = val[idx]
            else:
                return default
        elif hasattr(val, part):
            try:
                val = getattr(val, part)
            except (AttributeError, KeyError):
                return default
        else:
            return default
    return val


def _deep_has(obj, key):
    parts = key.split('.') if isinstance(key, str) and '.' in key else [key]
    val = obj
    for part in parts:
        if val is None:
            return False
        if isinstance(val, dict):
            if part not in val:
                return False
            val = val[part]
        elif isinstance(val, (list, tuple)) and part.isdigit():
            idx = int(part)
            if idx < len(val):
                val = val[idx]
            else:
                return False
        elif hasattr(val, part):
            try:
                val = getattr(val, part)
            except (AttributeError, KeyError):
                return False
        else:
            return False
    return True


def _test_item(d, key, test, value):
    if test == 'defined':
        return _deep_has(d, key)
    resolved = _deep_get(d, key, _MISSING)
    if test == 'truthy':
        return resolved is not _MISSING and bool(resolved)
    elif test == 'eq' or test == 'equalto':
        return resolved != _MISSING and resolved == value
    elif test == 'ne':
        return resolved != _MISSING and resolved != value
    elif test == 'in':
        return resolved is not _MISSING and resolved in (value or [])
    elif test == 'match':
        return bool(resolved and resolved is not _MISSING and re.match(value, str(resolved)))
    elif test == 'search' or test == 'regex':
        return bool(resolved and resolved is not _MISSING and re.search(value, str(resolved)))
    elif test == 'none':
        return resolved is None or resolved is _MISSING
    elif test == 'string':
        return resolved is not _MISSING and isinstance(resolved, str)
    elif test == 'number' or test == 'integer':
        return (resolved is not _MISSING
                and isinstance(resolved, (int, float))
                and not isinstance(resolved, bool))
    elif test == 'sequence':
        return resolved is not _MISSING and isinstance(resolved, (list, tuple))
    elif test == 'mapping':
        return resolved is not _MISSING and isinstance(resolved, dict)
    else:
        raise ValueError(
            "dict_selectattr/dict_rejectattr: unknown test '{}' "
            "(use match/search/regex/eq/equalto/ne/in/defined/truthy/"
            "none/string/number/integer/sequence/mapping)".format(test))


def dict_selectattr(list_of_dicts, key, test='truthy', value=None):
    """Filter list by key's value. Supports dotted keys."""
    return [d for d in list_of_dicts if _test_item(d, key, test, value)]


def dict_rejectattr(list_of_dicts, key, test='truthy', value=None):
    """Inverse of dict_selectattr."""
    return [d for d in list_of_dicts if not _test_item(d, key, test, value)]


class FilterModule(object):
    def filters(self):
        return {
            'dict_selectattr': dict_selectattr,
            'dict_rejectattr': dict_rejectattr,
        }
