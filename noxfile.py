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
    session.install('.[test]')
    session.run('pytest', '--cov=pyitc', *session.posargs)
