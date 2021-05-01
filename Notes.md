% Developer Notes

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
(Other projects should refer here for this discussion.)

## Packaging

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

## Repositories

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

## Testing

We use [pytest] for testing, running the tests with [Nox] for multiple versions of
python.  If you have multiple cores, you can run tests in parallel by passing the number
with `PYTEST_ADDPOPTS`:

```bash
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

### `tests/__init__.py`

Should the `tests` directories be importable modules as signified by having
`__init__.py` files?  In our case, yes, because several of them have associated modules
needed for testing (in particular `src/mmfutils/tests/parallel_module.py`) and not
having `__init__.py` files creates a problem for which I do not have an easy solution.
This may also help with potential name classes as discussed in the [pytest
documentation](https://docs.pytest.org/en/stable/goodpractices.html#tests-outside-application-code).


### Nox

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

### Continuous Integration (CI)

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


## Documentation

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


## Releases

We try to keep the repository clean with the following properties:

1. The default branch is stable: i.e. if someone runs `hg clone`, this will pull the latest stable release.
2. Each release has its own named branch so that e.g. `hg up 0.5.0` will get the right thing.  Note: this should update to the development branch, *not* the default branch so that any work committed will not pollute the development branch (which would violate the previous point).

To do this, we advocate the following proceedure.

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
7. **Pull Request**: Create a pull request on the development fork from your branch to `default` on the release project bitbucket. Review it, fix anything, then accept the PR and close the branch.
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


GitHub
======

We mirror our repos to GitHub to take advantage of continuous integration.

* https://cjolowicz.github.io/posts/hypermodern-python-06-ci-cd/
* https://docs.github.com/en/actions/guides/setting-up-continuous-integration-using-workflow-templates

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
[Nox]: <https://nox.thea.codes> "Nox: Flexible test automation"
[Hypermodern Python]: <https://cjolowicz.github.io/posts/hypermodern-python-01-setup/> "Hypermodern Python"
[`pyenv`]: <https://github.com/pyenv/pyenv> "Simple Python Version Management: pyenv"
[`minconda`]: <https://docs.conda.io/en/latest/miniconda.html> "Miniconda"
[Conda]: <https://docs.conda.io> "Conda"
[Heptapod]: <https://heptapod.net> "Heptapod website"
[pytest]: <https://docs.pytest.org> "pytest"
