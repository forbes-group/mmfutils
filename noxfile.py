import os
import platform
import subprocess

import nox

# import sys
# sys.path.append(".")
# from noxutils import get_versions

# Do not use anything installed in the site local directory (~/.local for example) which
# might have been installed by pip install --user.  These can prevent the install here
# from pulling in the correct packages, thereby mucking up tests later on.
# See https://stackoverflow.com/a/51640558/1088938
os.environ["PYTHONNOUSERSITE"] = "1"

# https://github.com/pytest-dev/pytest/issues/9567
# https://github.com/pytest-dev/pytest/issues/2042
# os.environ["PY_IGNORE_IMPORTMISMATCH"] = "1"

# By default, we only execute the conda tests because the others required various python
# interpreters to be installed.  The other tests can be run, e.g., with `nox -s test` if
# desired.
nox.options.sessions = ["test_conda"]

args = dict(python=["3.7", "3.8", "3.9", "3.10", "3.11"], reuse_venv=True)

# Note: On new Mac's (ARM) one must use test for python <3.8, unless special effort is
# made to ensure conda chooses the correct channel:
# https://stackoverflow.com/a/70219965
if platform.system() == "Darwin" and platform.processor() == "arm":
    # Somewhat dangerous... is there a better way?
    nox_args = nox._options.options.parse_args()
    pys = nox_args.pythons
    if not pys:
        pys = args["python"]
    for py in pys:
        subprocess.run(args=["make", f"envs/py{py}"])
    os.environ["PATH"] = os.pathsep.join(["build/bin/", os.environ["PATH"]])
    nox.options.sessions = ["test"]


@nox.session(venv_backend="venv", **args)
# @nox.parametrize("sphinx", get_versions("sphinx", "minor"))
def test(session):
    session.install("--upgrade", "pip")
    session.install(".[test]")
    session.run("pytest")


@nox.session(venv_backend="conda", **args)
def test_conda(session):
    # session.conda_env_update("environment.yml")
    # session.conda("env", "update", "--f", "environment.yml",
    #              conda="mamba", external=True)
    session.conda_install("conda-forge::pyfftw==0.13.1")
    session.install(".[test]")
    session.run("pytest")
