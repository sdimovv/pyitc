import nox

@nox.session
def test(session: nox.Session) -> None:
    """Run the test suite."""
    session.install('.[test]')
    session.run('pytest', *session.posargs)
