Developer Notes
===============

[![Documentation Status][rtd_badge]][rtd]
[![Tests][ci_badge]][ci]
[![Language grade: Python][lgtm_mmfutils_badge]][lgtm_mmfutils]
[![Language grade: Python][lgtm_mmfutils_fork_badge]][lgtm_mmfutils_fork]
[![Code style: black][black_img]][black]

These are some notes for developers and a general discussion about the design choices I
have made regarding things such as file hierarchy, packaging tools etc.  I intend for
this file to document my choices and discussions about these issues for all projects.
(Other projects should refer here for this discussion.)  For now, however, most of my
work is being done in the [Physics 581] project which I am teaching, so please visit
that for now.

# To Do

* Consider a two-branch model so that one can easily update to the latest development
  branch or the latest default branch.  Maybe default should be the development branch
  and we should have a release branch?  (Thinking about testing and badges... currently
  I have a branch for each version, but this means I need to specify the latest one each
  time.)

# Working Environment (Conda/pip and all that)

Our goal is to be able to use [conda] for packages that might require binary installs,
such as `mercurial`, `pyvista`, `numpy` etc., but in a way that:
1. Allows these conda environments to be installed in a read-only environment (i.e. as a
   separate `conda` user).
2. Allows us to install additional project dependencies if needed.

This kind of works: if you activate a conda environment that you do not have
write-access to, then you can at least use `python -m pip install --user` to install
additional packages, which will go in the directory
[`site.USER_BASE`](https://docs.python.org/3/library/site.html#site.USER_BASE) which can
be customized with the
[`PYTHONUSERBASE`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUSERBASE)
environment variable.  Unfortunately, this approach does not allow you to install
additional packages with [conda].

## Option 1 (recommended)
The recommended approach is to clone the environment.  For working on a specific
project, we recommend doing this in the project root folder as follows.  In this
example, we will clone the `work` environment:


```bash
cd myproject
conda create -p ./.conda/envs/myproject --clone work   # Took 1.5m on my Mac OS X laptop
conda install -p ./.conda/envs/myproject ipykernel     # So jupyter notebooks will find this
conda activate ./.conda/envs/myproject
```

This gives the following:

```bash
(.../.conda) $ poetry env info

Virtualenv
Python:         3.9.4
Implementation: CPython
Path:           /Users/mforbes/current/research/skeleton/.conda
Valid:          True
...
(.../.conda) $ poetry shell
Virtual environment already activated: /Users/mforbes/current/research/skeleton/.conda
$ du -sh ./.conda
3.0G	./.conda
$ du -sh /data/apps/conda/envs/work ./.conda
3.0G	/data/apps/conda/envs/work
565M	./.conda
```

Although `.conda/` looks like it takes 3GB, we see from the second command that it only
takes about 0.5GB indicating that there is significant use of hard-links to reduce disk
space.

**To Do:** It would be nice to have a better way of activating this, or recording it so
that just running `poetry shell` would work without having to explicitly activate the
environment.  We could code something into the [`Makefile`](Makefile).

## Option 2 (incomplete)

If you do not need to install any additional packages with [conda], and cannot afford
the disk space issues, then you can create a virtual environment [venv].  I recommend
managing this with [Poetry]:

```bash
cd <project>
conda activate work
python3 -m venv --system-site-packages .venv
poetry env info   # Should find .venv
poetry shell
```

Note: Poetry will use a virtual environment in `.venv` if the
[`virtualenvs.in-project`
option](https://python-poetry.org/docs/configuration#virtualenvsin-project) is `None`
(default) or `true`.





set `PYTHONUSERBASE`:

```bash
conda activate work
export PYTHONUSERBASE=./.local
export PATH="./.local/bin:$PATH"
python3 -m pip install --user ipykernel ...
python3 -m ipykernel install --user --name=skeleton # Goes to the wrong place...
```

This generally works, but the kernel is not going into `PYTHONUSERBASE`... not sure
why.  Need a better solution.  Maybe look into [copip](https://github.com/fperez/copip)?


See also: `python3 -m venv --system-site-packages .venv`


### Testing for Option 2

We will use the `mmfutil[test]` package to test this.

```bash
tmpdir="/tmp/testvenv"
for i in {1..10}; do conda deactivate; done  # Ensure all envrionments are deactivated.
if [ -e "$tmpdir" ]; then 
  find "$tmpdir" -type d -exec chmod u+w {} \;
  rm -rf "$tmpdir"
fi
mkdir "$tmpdir"
cd "$tmpdir"
conda create -y -p .conda_env python=3.8 poetry matplotlib scipy  # Use conda for these
find .conda_env -type d -exec chmod a-w {} \;
conda activate ./.conda_env
poetry init --name testvenv -n
python3 -m venv --system-site-packages .venv
poetry add mmfutils -E test

# Cleanup 
find "$tmpdir" -type d -exec chmod u+w {} \;
rm -rf "$tmpdir"
```

* https://github.com/python-poetry/poetry/issues/697

Here is a play-by-play
```bash
$ conda activate ./.conda_env

```


    ```bash
    $ poetry show -t
    mmfutils 0.5.4 Useful Utilities
    ├── backports.tempfile *
    │   └── backports.weakref * 
    ├── husl *
    ├── pathlib *
    └── zope.interface >=3.8.0
    ```




* Active conda environment to get python: poetry installs everything needed:

    ```bash
    for i in {1..10}; do conda deactivate; done  # Ensure all envrionments are deactivated.
    mkdir /tmp/testvenv0
    cd /tmp/testvenv0
    conda create -y -p .conda_env python=3.8 poetry
    conda activate ./.conda_env
    poetry init --name testvenv -n
    poetry config virtualenvs.in-project true --local
    poetry env use python3
    poetry add mmfutils
    ```

    ```bash
    $ poetry show -t
    mmfutils 0.5.4 Useful Utilities
    ├── backports.tempfile *
    │   └── backports.weakref * 
    ├── husl *
    ├── pathlib *
    └── zope.interface >=3.8.0
    ```

* Here we include the `zope.interface` dependency in the conda environment: poetry
    ignores this because it creates an isolated virtual environment.
  
    ```bash
    for i in {1..10}; do conda deactivate; done  # Ensure all envrionments are deactivated.
    mkdir /tmp/testvenv1
    cd /tmp/testvenv1
    conda create -y -p .conda_env python=3.8 poetry zope.interface
    conda activate ./.conda_env
    poetry init --name testvenv -n
    poetry config virtualenvs.in-project true --local
    poetry env use python3
    poetry add mmfutils
    ```

    ```bash
    $ poetry show -t
    mmfutils 0.5.4 Useful Utilities
    ├── backports.tempfile *
    │   └── backports.weakref * 
    ├── husl *
    ├── pathlib *
    └── zope.interface >=3.8.0
    ```

* Here we include the `zope.interface` dependency in the conda environment, and use our
    approach above for sharing the `site-packages`:
  
    ```bash
    for i in {1..10}; do conda deactivate; done  # Ensure all envrionments are deactivated.
    mkdir /tmp/testvenv2
    cd /tmp/testvenv2
    conda create -y -p .conda_env python=3.8 poetry
    conda activate ./.conda_env
    pip install zope.interface
    poetry init --name testvenv -n
    poetry config virtualenvs.in-project true --local
    python3 -m venv --system-site-packages .venv
    poetry add mmfutils
    ```

    ```bash
    $ poetry show -t
    mmfutils 0.5.4 Useful Utilities
    ├── backports.tempfile *
    │   └── backports.weakref * 
    ├── husl *
    ├── pathlib *
    └── zope.interface >=3.8.0
    ```



## Option 3
For testing, however, one should instead try to rely on a more isolated procedure.  If
your requirements can be satisfied purely by `pip` and you want to support pure `pip`
installations, then you should test **outside of the conda environment** by creating a
virtual environment:


If you need to depend on `conda`, then you should at least provide an `environment.yml`
file.

```bash
conda deactivate    # Just in case
```

## References

There are several potential issues related to permissions:

* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/7227)](https://github.com/conda/conda/issues/7227)
  Write permission error with a shared package cache folder.

## Reproducible Computing
### Conda-Pack

If you need to reproduce a conda environment, then [`conda-pack`] might be the right
tool.  This makes a copy of the environment and all of the files that can then be
archived and reinstalled elsewhere.  At the very least, `conda-pack` provides a check on
the code installed, failing if any files installed by [Conda] have been overwritten or
are installed twice.



# Distribution

In general, we will try to distribute projects on [PyPI] and this will be the primary
mode if distribution.  To use such projects in a [Conda] environment, just use `pip`:

```yml
# environment.yml
...
[dependencies]
  ...
  - pip
  - pip:
    - mmfutils>=0.6
    ...
```

To make packages available before their release on [PyPI], one can make use of the
[`-f, --find-links
<url>`](https://pip.pypa.io/en/stable/cli/pip_wheel/?highlight=find-links#cmdoption-f)
option of `pip`.  If this points to a webpage with links, then these links can define
how to get a package from source etc.  I maintain my own set of links in my [MyPI]
project.  Unfortunately, until [issue
#22572 *(gitlab is completely unusable without javascript.)*](https://gitlab.com/gitlab-org/gitlab/-/issues/22572) is resolved, GitLab-based
sites are useless for this purpose, so we rely on mirroring through GitHub.

# Packaging

Starting with version 0.6.0, we reorganized the repository as follows (modified from the
output of `tree -L 2`:

```bash
$ tree -L 2
.
|-- doc
|   |-- README.py        # Front page as a notebook.
|   |-- README.ipynb     # Front page as a notebook with output for display on repos.
|   ...                  # (We don't commit other .ipynb's)
|   `-- source           # Sphinx documentation
...
|-- Makefile             # Record instructions here, like how to test, or build docs.
|-- Notes.md             # Developer notes
|-- README.rst           # Generated from doc/README.ipynb for display on repos.
...
|-- environment.yml      # Useful development environment... not formal part of package.
|-- meta.yaml
`-- src
|   `-- mmfutils         # This is the main package.
|       |-- __init__.py  # Required for packages
|       ...
|       |-- math
|       |   |-- __init__.py
|       |   |-- bases
|       |   |   |-- __init__.py
|       |   |   ...
|       |   |   `-- tests                # Tests for mmfutils.math.bases
|       |   |       `-- test_bases.py
|       |   ...
|       |   `-- tests                    # Tests for mmfutils.math
|       |       |-- test_bessel.py
|       |       ...
|       |       `-- test_special.py
|       ...
|       `-- tests                        # Tests for mmfutils
|           |-- test_containers.py
|           |-- test_context.py
|           ...
|-- noxfile.py
|-- pytest.ini
|-- requirements.txt
|-- setup.cfg
|-- setup.py
`-- setup_tests
    `-- drone.io.sh

|-- noxfile.py
|-- pytest.ini
|-- requirements.txt
|-- setup.cfg
|-- setup.py
`-- setup_tests
    `-- drone.io.sh
```


## Version Number

There should be one definitive place for the version number.  Options are discussed
here: [Single-sourcing the package
version](https://packaging.python.org/guides/single-sourcing-package-version).  I am
going with option 5, which uses `importlib.metadata`.

# Repositories

Currently the main repository is on our own [Heptapod] server, but I have enabled 
`Settings/Repository/Mirroring repositories` to push to a public GitHub mirror
https://github.com/forbes-group/mmfutils/.  This required getting a personal token from GitHub
as [described
here](https://hg.iscimath.org/help/user/project/repository/repository_mirroring#setting-up-a-push-mirror-from-gitlab-to-github).
I chose to `Mirror only protected branches` to keep things clean, but this means that
we should either make all release branches protected, or be careful to tag the releases.

I don't want to use GitHub for managing issues or pull-requests, so instead, I also
maintain a development fork (under my personal GitHub account) which I can use for code
reviews.  For this one, I mirror everything.

> Notes:
> 
> * Do not actually fork the project - just push from Heptapod.  (LGTM will not analyze forks).
> * If you want to be able to update GitHub workflows, you must grant `workflow`
>   permission for the token.  Doing this will not invalidate the token.

Summary:

* https://hg.iscimath.org/forbes-group/mmfutils: Main development repository (Mercurial)
  running on our hosted [Heptapod] server.  This is where
  [Issues](https://hg.iscimath.org/forbes-group/mmfutils/-issues), [Merge
  Requests](https://hg.iscimath.org/forbes-group/mmfutils/-/merge_requests) etc. should
  be reported here.
* https://github.com/forbes-group/mmfutils: Main public mirror (Git) for releases.  Protected
  branches are automatically pushed here.  No development work should be done here: this
  is just for public access, and to use GitHub's CI tools.
* https://github.com/mforbes/mmfutils-fork: My development fork (Git).  Everything is
  pushed here to use GitHub's CI tools during development.  Should not be used for
  anything else.


## Badges

With CI setup, we have the following badges:

* Documentation at [Read the Docs](https://readthedocs.org):

    [![Documentation Status][rtd_badge]][rtd]

* Testing at [DroneIO](https://cloud.drone.io) and with GitHub actions:
    
    [![DroneIO Build Status][drone_badge]][drone]
    [![Tests][ci_badge]][ci]

* Code quality testing at [lgtm](https://lgtm.com):

    [![Language grade: Python][lgtm_mmfutils_badge]][lgtm_mmfutils]
    [![Language grade: Python][lgtm_mmfutils_fork_badge]][lgtm_mmfutils_fork]

* Style:

    [![Code style: black][black_img]][black]


[rtd_badge]: <https://readthedocs.org/projects/mmfutils/badge/?version=latest>
[rtd]: <https://mmfutils.readthedocs.io/en/latest/?badge=latest>


[drone_badge]: <https://cloud.drone.io/api/badges/forbes-group/mmfutils/status.svg>
[drone]: https://cloud.drone.io/forbes-group/mmfutils
[ci_badge]: <https://github.com/mforbes/mmfutils-fork/actions/workflows/tests.yml/badge.svg?branch=topic%2F0.6.0%2Fgithub_ci>
[ci]: <https://github.com/mforbes/mmfutils-fork/actions/workflows/tests.yml>

[black]: https://github.com/psf/black
[black_img]: https://img.shields.io/badge/code%20style-black-000000.svg


[lgtm_mmfutils]: <https://lgtm.com/projects/g/forbes-group/mmfutils/context:python>
[lgtm_mmfutils_badge]: <https://img.shields.io/lgtm/grade/python/g/forbes-group/mmfutils.svg?logo=lgtm&logoWidth=18>

[lgtm_mmfutils_fork]: <https://lgtm.com/projects/g/forbes-group/mmfutils/context:python>
[lgtm_mmfutils_fork_badge]: <https://img.shields.io/lgtm/grade/python/g/mforbes/mmfutils-fork.svg?logo=lgtm&logoWidth=18> 

## Continuous Integration (CI)

As mentioned above, by providing
[`.github/workflows/tests.yml`](.github/workflows/tests.yml), we can engage a [GitHub
action for continuous
integration](https://docs.github.com/en/actions/guides/about-continuous-integration).
This can be configure to run the tests automatically on pushes, the results of which are
displayed in the appropriate badges.

The main difficulty I had was a need for a full LaTeX installation.  This is now
working with `apt-get texlive-full`, but could probably be simplified, just updating the
packages we really need for testing ([`mathpazo`], [`siunitx`], and [`type1cm`] were
issues when just using the smaller `texlive` package.)

[`mathpazo`]: <https://ctan.org/pkg/mathpazo> "mathpazo – Fonts to typeset mathematics to match Palatino"
[`siunitx`]: <https://ctan.org/pkg/siunitx> "siunitx – A comprehensive (SI) units package"
[`type1cm`]: <https://ctan.org/pkg/type1cm> "type1cm – Arbitrary size font selection in LaTeX"

## References
* https://cjolowicz.github.io/posts/hypermodern-python-06-ci-cd/
* https://docs.github.com/en/actions/guides/setting-up-continuous-integration-using-workflow-templates

# Testing

We use [pytest] for testing, running the tests with [Nox] for multiple versions of
python.  If you have multiple cores, you can run tests in parallel by passing the number
with `PYTEST_ADDPOPTS`:

```bash
make clean                      # Remove any .pyc files etc... these can muckup tests.
export PYTEST_ADDOPTS="-n 8"    # Use 8 processes for testing in parallel
nox
```

There are [two
conventions](https://docs.pytest.org/en/latest/explanation/goodpractices.html#choosing-a-test-layout-import-rules)
for locating tests: outside of the application code, or with the application code.  Some
advantages of the former are [discussed by Ionel Cristian
Mărieș](https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure).  He gives
four main points which we discuss here:

> Module discovery tools will trip over your test modules.  Strange things usually
> happen in test module. The help builtin does module discovery. E.g.:
>
> ```python
> >>> help('modules')
> Please wait a moment while I gather a list of all available modules...
>
> __future__          antigravity         html                select
> ...
> ```

I need to play with this a bit later... might still be an issue.

> Tests usually require additional dependencies to run, so they aren't useful by their
> own - you can't run them directly.

I provide a `[test]` extra, so users can get all the dependencies with `python3 -m pip
install .[test]`.

> Tests are concerned with development, not usage.

and 

> It's extremely unlikely that the user of the library will run the tests instead of the
> library's developer. E.g.: you don't run the tests for Django while testing your
> apps - Django is already tested.

Both these assumptions are not valid for research code: here the tests often provide useful
examples for the users about how things can be done.  Also, the users are often the
developers.

## `tests/__init__.py`

Should the `tests` directories be importable modules as signified by having
`__init__.py` files?  In our case, yes, because several of them have associated modules
needed for testing (in particular `src/mmfutils/tests/parallel_module.py`) and not
having `__init__.py` files creates a problem for which I do not have an easy solution.
This may also help with potential name classes as discussed in the [pytest
documentation](https://docs.pytest.org/en/stable/goodpractices.html#tests-outside-application-code).

## Nox

Testing is now done using [Nox] as configured in `noxfile.py`.  This allows for testing
against multiple versions of python (similar to [Tox]) but I find that it is simpler to
use and works with [Conda].  My general strategy is to use [Conda] to minimally
provision environments with the desired version of python, then to install the package
with `pip install .[test]` in that environment.  This has the following advantages:

* Generally works.  The typical recommendation (for example in the [Hypermodern Python]
  series) is to use [`pyenv`].  Unfortunately, this is a pain for me on my Mac OS X
  development machine as [`pyenv`] tries to compile python from source which can take
  forever, and often fails.  (For example, I cannot build `python=3.5.8` for some
  reason, and `miniconda3-3.5.*` is not available.)  Conversely, `conda env create -n
  py3.5 python=3.5` seems to always work for me.  Of course, this does require you to
  install [`miniconda`] on your machine, which I do with something like this:
  
    ```bash
    # I install conda as a non-privileged user in /data/apps/conda 
    CONDA_PATH=/data/apps/conda1
    CONDA_USER=mforbes
    sudo -u "$CONDA_USER" mkdir -p "$CONDA_PATH"
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    shasum -a 256 Miniconda3-latest-MacOSX-x86_64.sh
    # The following runs in batch mode: be sure to read the license before you do this.
    bash Miniconda3-latest-MacOSX-x86_64.sh -f -b -p "$CONDA_PATH"
    ```

* This approach only used [Conda] to install python: we then test `pip install` which we
  certainly want to test.

* We can use [Conda] if we like to test installing dependencies from an
  `environment.yml` file for example.

Tests should be run as follows:

```bash
nox -s test_conda -p 3.6
```

This runs the test against the latest version of Python 3.6, essentially running
something like:

```bash
conda env create -p .nox/test_conda-3-6
conda activate ./.nox/test_conda-3-6
pip install .[test]
pytest
```

If this fails, you can debug by simply activating the environment:

```bash
conda env create -p .nox/test_conda-3-6
pytest
```

or using the environment defined in `environment.yml`:

```bash
cond activate _mmfutils
pytest
```

### Gotchas

I had a very difficult time with random errors when tested `mmf_setup` that boiled down
to `pip` not installing some packages in the testing environment because they were in
`~/.local`, but then having issues when the underlying tests were running and sometimes
did not have access to these.  (The specific case was when running `run_tests.py` for
Mercurial tests.)

The solution is to make sure that `PYTHONNOUSERSITE=1` before running anything.

* See: https://stackoverflow.com/a/51640558/1088938

# Documentation

If you are a developer of this package, there are a few things to be aware of.

1. If you modify the notebooks in ``docs/notebooks`` then you may need to regenerate
   some of the ``.rst`` files and commit them so they appear on bitbucket.   This is
   done automatically by the ``pre-commit`` hook in ``.hgrc`` if you include this in
   your ``.hg/hgrc`` file with a line like:

    ```
    # %include ../.hgrc
    ```
    
**Security Warning:** if you do this, be sure to inspect the ``.hgrc`` file carefully to
make sure that no one inserts malicious code.  This runs the following code:

    !cd $ROOTDIR; jupyter nbconvert --to=rst --output=README.rst doc/README.ipynb


# Profiling (Incomplete)

To measure peak memory usage, look at [Fil].  Write your test-code as a script, then run
it with `fil-profile`:

```bash
fil-profile run test_script.py
```

# Releases

We try to keep the repository clean with the following properties:

1. The default branch is stable: i.e. if someone runs `hg clone`, this will pull the latest stable release.
2. Each release has its own named branch so that e.g. `hg up 0.5.0` will get the right thing.  Note: this should update to the development branch, *not* the default branch so that any work committed will not pollute the development branch (which would violate the previous point).

To do this, we advocate the following procedure.

1. **Update to Correct Branch**: Make sure this is the correct development branch, not the default branch by explicitly updating:

    ```bash
    hg up <version>
    ```
   
    (Compare with `hg up default` which should take you to the default branch instead.)
2. **Work**: Do your work, committing as required with messages as shown in the repository with the following keys:

    * `DOC`: Documentation changes.
    * `API`: Changes to the exising API.  This could break old code.
    * `EHN`: Enhancement or new functionality. Without an `API` tag, these should not break existing codes.
    * `BLD`: Build system changes (`setup.py`, `requirements.txt` etc.)
    * `TST`: Update tests, code coverage, etc.
    * `BUG`: Address an issue as filed on the issue tracker.
    * `BRN`: Start a new branch (see below).
    * `REL`: Release (see below).
    * `WIP`: Work in progress.  Do not depend on these!  They will be stripped.  This is useful when testing things like the rendering of documentation on bitbucket etc. where you need to push an incomplete set of files.  Please collapse and strip these eventually when you get things working.
    * `CHK`: Checkpoints.  These should not be pushed to bitbucket!
3. **Tests**: Make sure the tests pass.  Comprehensive tests should be run with `nox`:
   
    ```bash
    nox
    ```
   
    Quick tests while developing can be run with the `_mmfutils` environment:
   
    ```bash
    conda env update --file environment.yml
    conda activate _mmfutils; pytest
    ```

    (`hg com` will automatically run tests after pip-installing everything in `setup.py` if you have linked the `.hgrc` file as discussed above, but the use of independent environments is preferred now.)
4. **Update Docs**: Update the documentation if needed.  To generate new documentation run:

    ```bash
    cd doc
    sphinx-apidoc -eTE ../mmfutils -o source
    rm source/mmfutils.*tests*
    ```
   
    * Include any changes at the bottom of this file (`doc/README.ipynb`).
    * You may need to copy new figures to `README_files/` if the figure numbers have changed, and then `hg add` these while `hg rm` the old ones.
   
    Edit any new files created (titles often need to be added) and check that this looks good with
  
    ```bash
    make html
    open build/html/index.html
    ```
     
    Look especially for errors of the type "WARNING: document isn't included in any toctree".  This indicates that you probably need to add the module to an upper level `.. toctree::`.  Also look for "WARNING: toctree contains reference to document u'...' that doesn't have a title: no link will be generated".  This indicates you need to add a title to a new file.  For example, when I added the `mmf.math.optimize` module, I needed to update the following:
  
[comment]: # (The rst generate is mucked up by this indented code block...)
```rst
   .. doc/source/mmfutils.rst
   mmfutils
   ========
   
   .. toctree::
       ...
       mmfutils.optimize
       ...
```   
```rst
   .. doc/source/mmfutils.optimize.rst
   mmfutils.optimize
   =================
       
   .. automodule:: mmfutils.optimize
       :members:
       :undoc-members:
       :show-inheritance:
```
  
5. **Clean up History**: Run `hg histedit`, `hg rebase`, or `hg strip` as needed to clean up the repo before you push.  Branches should generally be linear unless there is an exceptional reason to split development.
6. **Release**: First edit `mmfutils/__init__.py` to update the version number by removing the `dev` part of the version number.  Commit only this change and then push only the branch you are working on:

    ```bash
    hg com -m "REL: <version>"
    hg push -b .
   ```
7. **Pull Request**: Create a pull request on the development fork from your branch to
   `default` on the release project. Review it, fix anything, then accept the merge
   request.  **Do not close the branch!** Unlike bitbucket, if you close the branch on
   Heptapod, it will vanish, breaking our [MyPI] index.
8. **Publish on PyPI**: Publish the released version on [PyPI](https://pypi.org/project/mmfutils/) using [twine](https://pypi.org/project/twine/)

    ```bash
    # Build the package.
    python setup.py sdist bdist_wheel
    
    # Test that everything looks right:
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   
    # Upload to PyPI
    twine upload dist/*
    ```

9. **Build Conda Package**: This will run all the tests in a fresh environment as specified by `meta.yaml`.  Make sure that the dependencies in `meta.yaml`, `environment.yml`, and `setup.py` are consistent.  Note that the list of versions to be built is specified in `conda_build_config.yaml`.

    ```bash
    conda build .
    conda build . --output   # Use this below
    anaconda login
    anaconda upload --all /data/apps/conda/conda-bld/noarch/mmfutils-0.5.0-py_0.tar.bz2
    ```
   
10. **Start new branch**: On the same development branch (not `default`), increase the version number in `mmfutils/__init__.py` and add `dev`: i.e.:

    ```python
    __version__ = '0.5.1dev'
    ```
       
    Then create this branch and commit this:
  
    ```bash
    hg branch "0.5.1"
    hg com -m "BRN: Started branch 0.5.1"
    ```
       
11. Optional: Update any `setup.py` files that depend on your new features/fixes etc.


Poetry
======

[Poetry] has great promise, but is currently a bit of a pain due to some unresolved
issues.  Here are some recommendations:

* Always work in an explicit environment.  This is an issue if you routinely have a
  [conda] environment activated.  Currently, [poetry] interprets an active [conda]
  environment as a virtual environment and uses it.  This means that `poetry add ...`
  will add these dependencies **to that environment**.  Instead, I [recommend the
  following](https://github.com/python-poetry/poetry/issues/1724#issuecomment-834080057):
   
  1. Create some bare [conda] environments with the various python interpreters you
     want to use *(only needs to be done once per system)*:
      
     ```bash
     for py_ver in 2.7 3.6 3.7 3.8 3.9; do
          conda_env="py${py_ver}"
          conda create --strict-channel-priority \
                       -c defaults -y            \
                       -n "${conda_env}"         \ 
                       python="${py_ver}"
          conda activate "${conda_env}"
          ln -fs "$(type -p python${py_ver})" ~/.local/bin/
          conda deactivate
      done
      ```
  2. Specifically activate one of these for each project while developing *(only needs
     to be done once per project)*:
   
     ```bash
     cd project
     poetry env use python3.8
     ```
  3. Poetry should now remember this and use it.  See also `poetry env list` to see all
     environments, and `poetry env remove 3.8` to remove the environment.
   
     <details>

     Prior to creating the virtual environment with `poetry env using`, poetry assumes
     that the conda `work` environment is the virtual env:

     ```bash
     $ cd project
     $ poetry env info

     Virtualenv
     Python:         3.8.8
     Implementation: CPython
     Path:           /data/apps/conda/envs/work
     Valid:          True

     System
     Platform: darwin
     OS:       posix
     Python:   /data/apps/conda/envs/work

     $ poetry env using 3.8
     $ poetry env info

     Virtualenv
     Python:         3.8.8
     Implementation: CPython
     Path:           .../Caches/pypoetry/virtualenvs/project-...-py3.8
     Valid:          True

     System
     Platform: darwin
     OS:       posix
     Python:   /data/apps/conda/envs/work
     ```
     </details>
* To support multiple versions of python, use `python = "^2.7 || ^3.6"` for example,
  with logical or `||` not a comma `,`.  Note, however, that poetry has difficulty
  resolving dependencies when you have multiple version specified.  You may have to
  first add your dependencies with each explicit version.  Sometimes I just activate a
  shell and use `pip` to see what it brings.  Here is a strategy (I did this with the
  [`persist`] package):
  
  1.  Start with your desired python versions, then add projects, and restrict until
      everything works:
     
      ```bash
      $ poetry env use 3.8
      # python = "^3.6"
      $ poetry add zope.interface importlib-metadata
      Using version ^5.4.0 for zope.interface
      Using version ^4.0.1 for importlib-metadata
      $ poetry add --optional Sphinx pytest pytest-cov sphinx-rtd-theme \
        sphinxcontrib-zopeext nbsphinx h5py mmf-setup scipy
      Using version ^3.5.4 for Sphinx
      ...
        SolverProblemError
        ...
        For scipy, a possible solution would be to set the `python` property to ">=3.8,<3.10"
      # Try with python = ">=3.8,<3.10"... it works.  Now relax scipy as:
      # scipy = [
      #     {version = "*", python="<3.8", optional = true},
      #     {version = "^1.6.3", python="^3.8, <3.10", optional = true}]
      # and try again with python = "^3.6"
      $ poetry update
      ...
        SolverProblemError
        For h5py, a possible solution would be to set the `python` property to ">=3.7,<4.0"
      # Try with python = ">=3.8,<3.10"... it works.  Now relax scipy as:
      # h5py = [
      #     {version = "*", python="<3.7", optional = true},
      #     {version = "^3.2.1", python="^3.7", optional = true}]
      $ poetry update 
      ```
     
      Note: Be very careful to express complete constraints.  The following works
     
      Consider both sides of the suggested dependencies.  Once I relaxed the
      requirements for scipy for `python="<3.8"` I still got errors saying 
    
     
  2.  Add all dependencies and see what happens:
  
      ```bash
      
      ```
*   If you only need a tool for development, you can add it with the `-D` flag.  Note: if
    you get an error about the version of python required here, you can simply avoid this
    by specifying a more specific version required for installing the dev tools.  For
    example:
  
    ```bash
    $ poetry add -D ipython
    ...
      SolverProblemError
    ...
        - ipython requires Python >=3.7
    ...
    $ poetry add -D ipython --python '^3.7'
    Using version ^7.24.1 for ipython
    ...
    ```
 
## Issues:

* Consider `pyFFTW`: if not using [Conda], then this needs the FFTW libraries installed
  on the host platform, otherwise the install will fail.  How best to deal with this?
  My current solution is to provide these as extras, but it would be nice if there was a
  way to install if the libraries are present.

* How to manage one definitive version?  The [current suggestion] is to use
  `importlib.metadata`:
  
  ```python
  # __init__.py
  try:
      import importlib.metadata as _metadata
  except ModuleNotFoundError:
      import _metadata

  __version__ = _metadata.version(__name__)
  ```
  
  ```toml
  # pyproject.toml
  [tool.poetry.dependencies]
  ...
  importlib-metadata = {version = "^1.0", python = "<3.8"}
  ```
  
  If you only support Python >= 3.8, then you can simply do:
  
  ```python
  # __init__.py
  import importlib.metadata as _metadata
  __version__ = _metadata.version(__name__)
  ```

  This works for installed packages, but fails when one just adds the source directory
  to the path:
  
  ```bash
  $ cd src
  $ python -c "import mmfutils
  Traceback (most recent call last):
     ...
  importlib.metadata.PackageNotFoundError: mmfutils
  ```
  
  The work-around is as follows.  (We could fallback to VCS maybe?  Or look in `pyproject.toml`?).
  
  ```python
  try:
      __version__ = _metadata.version(__name__)
  except _metadata.PackageNotFoundError:
      __version__ = "<unknown source distribution>"    
  ```

[current suggestion]: <https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094>

* [Document use of current conda env #1724](https://github.com/python-poetry/poetry/issues/1724)
* [Ability to override/ignore sub-dependencies
  #697](https://github.com/python-poetry/poetry/issues/697): What to do when
  sub-dependencies do not properly specify requirements, leading to conflicts.  (Not
  sure of the actual resolution.)
* [Poetry install tries to update system packages is 'system-site-packages' option enabled #4033](https://github.com/python-poetry/poetry/issues/4033)

# Reference

## Conda Issues

* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/1329)](https://github.com/conda/conda/issues/1329)
  "Better support for conda envs accessed by multiple users"
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/6991)](https://github.com/conda/conda/issues/6991)
  "conda env create -f hangs if yaml is on read-only network share"
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/7227)](https://github.com/conda/conda/issues/7227)
  "Write permission error with a shared package cache folder."
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/7279)](https://github.com/conda/conda/issues/7279)
  "conda env update --prune does not remove installed packages not defined in
  environment.yml"
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/8592)](https://github.com/conda/conda/issues/8592)
  "It takes a couple of minutes to run conda commands"
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/8983)](https://github.com/conda/conda/issues/8983)
  "conda fails install for local user due to permission issues"
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/10690)](https://github.com/conda/conda/issues/10690)
  "Conda run fails with Permission denied if environment is read-only."
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/10105)](https://github.com/conda/conda/issues/10105)
  "Local environment.yml file hides remote environment file specification in conda env
  create."
  * Could be an issue with `anaconda-client`:
    [![Issue](https://img.shields.io/github/issues/detail/state/Anaconda-Platform/anaconda-client/549)](https://github.com/Anaconda-Platform/anaconda-client/issues/549)

# Odds and Ends

Consider using
[gitignore.io](https://www.toptal.com/developers/gitignore/api/latex,python) to generate
`.gitignore` and `.hgignore` files.

When trying to use `pyenv` I get the following error:

```bash
$ pyenv install 3.6.12
Downloading openssl-1.1.0j.tar.gz...
-> https://www.openssl.org/source/old/1.1.0/openssl-1.1.0j.tar.gz
Installing openssl-1.1.0j...
Installed openssl-1.1.0j to /Users/mforbes/.pyenv/versions/3.6.12

Downloading readline-8.0.tar.gz...
-> https://ftpmirror.gnu.org/readline/readline-8.0.tar.gz
Installing readline-8.0...
Installed readline-8.0 to /Users/mforbes/.pyenv/versions/3.6.12

Downloading Python-3.6.12.tar.xz...
-> https://www.python.org/ftp/python/3.6.12/Python-3.6.12.tar.xz
Installing Python-3.6.12...
python-build: use zlib from xcode sdk

BUILD FAILED (OS X 10.14.6 using python-build 20180424)

Inspect or clean up the working tree at /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gp/T/python-build.20210427233639.16374
Results logged to /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gp/T/python-build.20210427233639.16374.log

Last 10 log lines:
  "_libintl_textdomain", referenced from:
      _PyIntl_textdomain in libpython3.6m.a(_localemodule.o)
      _PyIntl_textdomain in libpython3.6m.a(_localemodule.o)
ld: symbol(s) not found for architecture x86_64
ld: symbol(s) not found for architecture x86_64
clang: error: linker command failed with exit code 1 (use -v to see invocation)
clang: error: linker command failed with exit code 1 (use -v to see invocation)
make: *** [Programs/_testembed] Error 1
make: *** Waiting for unfinished jobs....
make: *** [python.exe] Error 1
```

<!-- Links -->
[Physics 581]: <https://gitlab.com/wsu-courses/physics-581-physics-inspired-computation> "Physics 581: Physics Inspired Computation course GitLab project."
[Conda]: <https://docs.conda.io> "Conda"
[Fil]: <https://pythonspeed.com/products/filmemoryprofiler/> "The Fil memory profiler for Python"
[Heptapod]: <https://heptapod.net> "Heptapod website"
[Hypermodern Python]: <https://cjolowicz.github.io/posts/hypermodern-python-01-setup/> "Hypermodern Python"
[MyPI]: <https://alum.mit.edu/www/mforbes/mypi/> "MyPI: My personal package index"
[Nox]: <https://nox.thea.codes> "Nox: Flexible test automation"
[Poetry]: <https://poetry.eustace.io> "Python packaging and dependency management made easy."
[PyPI]: <https://pypi.org> "PyPI: The Python Package Index"
[`minconda`]: <https://docs.conda.io/en/latest/miniconda.html> "Miniconda"
[`pyenv`]: <https://github.com/pyenv/pyenv> "Simple Python Version Management: pyenv"
[pytest]: <https://docs.pytest.org> "pytest"
[venv]: <https://docs.python.org/3/library/venv.html> "Creation of virtual environments"
[`conda-pack`]: <https://conda.github.io/conda-pack/> "Command line tool for creating archives of conda environments"
