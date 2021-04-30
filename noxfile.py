import nox

# By default, we only execute the conda tests because the others required various python
# interpreters to be installed.  The other tests can be run, e.g., with `nox -s test` if
# desired.
nox.options.sessions = ["test_conda"]


@nox.session(python=["3.6", "3.7", "3.8"])
def test(session):
    session.install(".[test]")
    session.run("pytest")


@nox.session(venv_backend="conda", python=["3.6", "3.7", "3.8"], reuse_venv=True)
def test_conda(session):
    # session.conda_env_update("environment.yml")
    # session.conda("env", "update", "--f", "environment.yml",
    #              conda="mamba", external=True)
    session.install(".[test]")
    session.run("pytest")
