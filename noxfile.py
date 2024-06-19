# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
import os
import re
from typing import List

import nox


def _natural_sort(content: str) -> List[str]:
    convert = lambda text: int(text) if text.isdigit() else text.lower()  # noqa: E731
    return sorted(
        content, key=lambda key: [convert(c) for c in re.split("([0-9]+)", key)]
    )


with open(".python-version", "r") as f:
    SUPPORTED_PYTHON_VERSIONS = _natural_sort(re.sub(r"[\n\s]+", " ", f.read()).split())


@nox.session(python=SUPPORTED_PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Run the tests."""
    session.install(".[test]")
    session.run("pytest", "--cov=pyitc", *session.posargs)


@nox.session(reuse_venv=True)
def format(session: nox.Session) -> None:  # noqa: A001
    """Format the code."""
    session.install(".[qa]")
    session.run("ruff", "format", *session.posargs)


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Lint the code."""
    session.install(".[qa]")
    session.run("ruff", "check", *session.posargs)


@nox.session(reuse_venv=True, name="typeCheck")
def type_check(session: nox.Session) -> None:
    """Type check the code with mypy."""
    session.install(".[qa]")
    if not session.posargs:
        posargs = [os.path.dirname(os.path.realpath(__file__))]
    else:
        posargs = session.posargs
    session.run("mypy", *posargs)
