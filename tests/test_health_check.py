import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.health import health_check


def test_git_status_returns_string():
    res = health_check.git_status(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    assert isinstance(res, str)


def test_disk_usage_has_keys():
    d = health_check.disk_usage('/')
    assert isinstance(d, dict)
    assert 'total' in d or 'error' in d


def test_python_version_present():
    v = health_check.python_version()
    assert isinstance(v, str)
