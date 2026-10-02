"""Test-wide warning filters for third-party Python 3.15 deprecations."""

import warnings

import pytest


def _ignore_third_party_py315_deprecations() -> None:
    """Ignore google-genai's use of typing._UnionGenericAlias.

    Python 3.15 deprecates that private alias (removal in 3.17). google-genai
    still builds a Union with it at import time, including the latest release.
    Pytest applies ``-W`` inside its own catch_warnings, after conftest import,
    so the ignore has to be installed from a hook that runs inside that context.
    Other DeprecationWarnings stay errors.
    """
    # warnings filters match the start of the message. The text is
    # "'_UnionGenericAlias' is deprecated ...", so the pattern must allow
    # the leading quote.
    warnings.filterwarnings(
        "ignore",
        message=r".*_UnionGenericAlias.*",
        category=DeprecationWarning,
    )


@pytest.hookimpl(wrapper=True, trylast=True)
def pytest_collection(session):
    _ignore_third_party_py315_deprecations()
    return (yield)


@pytest.hookimpl(wrapper=True, trylast=True)
def pytest_runtest_protocol(item):
    _ignore_third_party_py315_deprecations()
    return (yield)