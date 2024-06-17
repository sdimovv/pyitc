import nox
import re

def _natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    return sorted(l,
        key=lambda key: [convert(c) for c in re.split('([0-9]+)', key)])

with open('.python-version', 'r') as f:
    SUPPORTED_PYTHON_VERSIONS = _natural_sort(
        re.sub(r'[\n\s]+', ' ', f.read()).split())

@nox.session(python=SUPPORTED_PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Run the tests."""
    session.install(".[dev]")
    session.run("pytest", "--cov=pyitc", *session.posargs)


@nox.session(reuse_venv=True)
def format(session: nox.Session) -> None:
    """Format the code."""
    session.install(".[dev]")
    if not session.posargs:
        posargs = [os.path.dirname(os.path.realpath(__file__))]
    else:
        posargs = session.posargs
    session.run("black", *posargs)
    session.run("isort", *posargs)

@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Lint the code."""
    session.install(".[dev]")
    if not session.posargs:
        posargs = [os.path.dirname(os.path.realpath(__file__))]
    else:
        posargs = session.posargs
    session.run("flake8", *posargs)
    session.run("mypy", *posargs)
