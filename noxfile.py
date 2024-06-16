import nox

SUPPORTED_PYTHON_VERSIONS = ("3.7", "3.8", "3.9", "3.10", "3.11", "3.12")

@nox.session(python=SUPPORTED_PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Run the test suite."""
    session.run('python', '-m', 'ensurepip', '--upgrade')
    session.install('.[test]')
    session.run('pytest', '--cov=pyitc', *session.posargs)
