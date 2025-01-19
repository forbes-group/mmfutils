Developer Notes
===============

[![Documentation Status][rtd_badge]][rtd]
[![Tests][ci_badge]][ci]
[![Language grade: Python][lgtm_mmfutils_badge]][lgtm_mmfutils]
[![Language grade: Python][lgtm_mmfutils_fork_badge]][lgtm_mmfutils_fork]
[![Code style: black][black_img]][black]

These are some notes for developers and a general discussion about some of the design
choices I have made regarding things such as file hierarchy, packaging tools etc.  I
intend for this file to document my choices and discussions about these issues for all
projects.  (Other projects should refer here for this discussion.)

<details><summary>Table of Contents</summary>
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
     

- [To Do](#to-do)
- [TL;DR](#tldr)
  - [GitLab](#gitlab)
- [Tools](#tools)
- [Python Dependencies](#python-dependencies)
  - [[PDM][]](#pdm)
- [[Conda][] Dependencies](#conda-dependencies)
  - [Makefile](#makefile)
- [Managing Multiple Versions of Python](#managing-multiple-versions-of-python)
  - [Testing](#testing)
    - [GitHub CI](#github-ci)
- [Tools](#tools-1)
  - [Useful Tools](#useful-tools)
- [Working Environment (Conda/Pip and all that)](#working-environment-condapip-and-all-that)
  - [Option 1 (Recommendation as of March 2023)](#option-1-recommendation-as-of-march-2023)
  - [Option 2 (experimental)](#option-2-experimental)
    - [Caveats](#caveats)
  - [Option 3 (old recommendation)](#option-3-old-recommendation)
  - [Option 3 (incomplete)](#option-3-incomplete)
    - [Testing for Option 2](#testing-for-option-2)
  - [Option 3](#option-3)
  - [References](#references)
  - [Reproducible Computing](#reproducible-computing)
    - [Conda-Pack](#conda-pack)
- [Packaging](#packaging)
  - [Distribution](#distribution)
  - [To Do](#to-do-1)
  - [Version Number](#version-number)
- [Documentation ([Read the Docs][])](#documentation-read-the-docs)
  - [Jupyter Book](#jupyter-book)
    - [Images](#images)
- [Repositories](#repositories)
  - [Badges](#badges)
  - [Continuous Integration (CI)](#continuous-integration-ci)
    - [Coverage](#coverage)
  - [References](#references-1)
- [Testing](#testing-1)
  - [`tests/__init__.py`](#tests__init__py)
  - [Nox](#nox)
    - [Matrix Testing](#matrix-testing)
    - [Gotchas](#gotchas)
  - [Documentation](#documentation)
- [Profiling (Incomplete)](#profiling-incomplete)
- [Releases](#releases)
- [`mmfutils`: This Package](#mmfutils-this-package)
  - [Dependencies](#dependencies)
  - [The Development Process: Makefiles](#the-development-process-makefiles)
    - [Details](#details)
      - [Conda and Anaconda Project](#conda-and-anaconda-project)
    - [Things that Did Not Work](#things-that-did-not-work)
  - [PDM](#pdm)
    - [Issues](#issues)
  - [Poetry](#poetry)
  - [Soft Dependencies](#soft-dependencies)
  - [Issues:](#issues)
  - [References](#references-2)
- [Testing](#testing-2)
  - [Issues:](#issues-1)
- [GitHub](#github)
- [Issues:](#issues-2)
  - [pyFFTW](#pyfftw)
  - [Sleep](#sleep)
- [[CoCalc][]](#cocalc)
  - [Implementation Details](#implementation-details)
- [Reference](#reference)
  - [Conda Issues](#conda-issues)
  - [Black Issues](#black-issues)
  - [PDM Issues](#pdm-issues)
  - [Poetry Issues](#poetry-issues)
  - [PipX Issues](#pipx-issues)
  - [CondaX Issues](#condax-issues)
  - [CoCalc Issues](#cocalc-issues)
- [Odds and Ends](#odds-and-ends)
- [References](#references-3)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
</details>

# To Do

* Consider a two-branch model so that one can easily update to the latest development
  branch or the latest default branch.  Maybe default should be the development branch
  and we should have a release branch?  (Thinking about testing and badges... currently
  I have a branch for each version, but this means I need to specify the latest one each
  time.)
* Fix bases to properly use GPU (sundered values etc.).

# TL;DR

Getting started should be as easy as:

1. Cloning the project (or initializing with [our cookiecutter templates][]).
2. (Optional) `make tools` and adding the appropriate folder to your path. *(This is not
   implemented yet: currently you should install your tools with your OS package
   managers, [pipx][] etc.)*
3. `make shell`: This launches a shell which should have everything installed so you can
   just start working.
4. `make doc-server`: Build and launch the documentation server.
5. `make realclean`: Cleanup everything as much as possible.

To support this, our project structure uses the following files:

* `Makefile`: We use [GNU make][] to collect "wisdom" about how to build, install,
  activate, etc. our development environments. In an effort to be platform and tool
  agnostic, these may get complicated, but they will contain lots of useful
  information.  Useful commands include:
  * `make shell`: Starts a shell with everything needed for work.
  * `make realclean`: Cleans up as much as possible.  As close as possible to a fresh checkout.
* [`pyproject.toml`][]: Most of our work is based on Python, and this is
  [the standard][pyproject.toml] way to specify dependencies and configure python.
  Various ([too many!][How to improve Python packaging]) tool exist for helping update
  this. Currently we recommend [PDM][] (was previously [Poetry][], but they do not
  [support this standard][poetry#3332].)  We follow [Scikit-HEP's
  recommendation](https://scikit-hep.org/developer/packaging#extras-lowmedium-priority)
  that the extras `test`, `docs`, and `dev` be defined here, though the latter may be
  managed by a tool like [PDM][].
* `environment.yaml`: Many of our projects require something for which installing
  with [conda][] is easiest.  ([PyFFTW][] and [CuPy][] are obvious examples, but even
  [NumPy with MKL][] optimizations is included.)  In principle, with [Anaconda
  Project][], an equivalent `anaconda-project.yaml` file can replace the `Makefile`
  and [`pyproject.toml`][], but this does not work for us (see below).

[poetry#3332]: <https://github.com/python-poetry/poetry/issues/3332>
[PEP-631]: <https://peps.python.org/pep-0631/>
[`pyproject.toml`]: 
  <https://packaging.python.org/en/latest/specifications/declaring-project-metadata>

# Tools

I generally make sure I have the following tools installed globally.  These will need to
be included on any docker images used for testing (CI) although some of them can be
installed by the `Makefile`.  See `.gitlab-ci.yml` for what is currently needed.

## Mac OS X

On my computer, I install most of these with [MacPorts][] or with [pipx][] if they are
python based.  I do this using a different account (`admin`) on my computer so I don't
accidentally muck these up.  I also keep my `base` [Conda][] environment in this account
for the same reason.  For complete details see [mac-os-x][].

```bash
# On Mac OS X using MacPorts:
ssh admin  # My alias to login as `admin`
port install git gmake pandoc myrepos graphviz
port install python37 python38 python39 python310 python311
exit

ssh conda  # My alias to login as `conda`
conda install -n base pipx
for app in cookiecutter pdm poetry yapf black nox    \
           nbdime jupytext nbstripout                \
           poetry2conda conda-lock conda-pack condax \
           sphobjinv rst-to-myst twine               \ 
           mercurial mmf_setup snakeviz              \
           grip; do pipx install ${app}; done
pipx inject nox nox-poetry poetry 
pipx inject pdm pdm-shell
pipx inject mercurial hg-git hg-evolve
exit
```


You may not need all of these for all packages.

In addition, you will likely need to install compilers and development tools, and
[TeX Live][] for making publication-quality plots.

In the future, the tools (except for [TeX Live][] and compilers) needed for the project
will be able to be installed locally with `make tools`.

In [our cookiecutter templates][], we are experimenting with ways of installing these
locally with the Makefile through a command like `make tools`, or as needed.  This is
still a bit of a work in progress.

# Python Dependencies

The pure python dependencies should be specified in [`pyproject.toml`][].  If you are
developing a package to publish on [PyPI][], then this should contain **all**
dependencies.


## [PDM][]

We currently manage this file with [PDM][], e.g.:

```bash
make shell
pdm add uncertainties
pdm add -G test pytest-cov
pdm add -G docs sphinx
pdm add --dev ipython
...
```

In addition to the development dependencies specified in `[tool.pdm.dev-dependencies]`,
one should generally include the `test` and `docs` extras.  For our work, we also often
use the following:

* `perf`: Tools for high-performance computing that might be difficult to install, so we
  make them optional.  [PyFFTW][], [Numba][], and [PyCUDA][] are good examples.  Note
  that, from a development perspective, these are often provided in the [Conda][]
  environment, but are needed here if you want your package to be [pip][]-installable
  from [PyPI][].  Some extra effort is needed to make sure that the versions specified
  in `environment.yaml` are consistent with the versions here.
  
  Now that I know about [recursive optional dependencies in Python][], I am considering
  splitting these into `gpu`, `pyfftw`, `numba`, etc.
* `full`: All functional dependencies.  I.e. everything except `docs` and `test`.  Note:
  if you include packages here or in `perf`, you should be sure to make sure that these
  do not break imports.  For example (see `src/mmfutils/performance/fft.py` for example):
  
  ```python
  try:
      import pyfftw
  except ImportError:
      warnings.warn("Could not import pyfftw... falling back to numpy")
      pyfftw = None
  ```
  
  An exception is if there is a particular sub-module that obviously depends on this
  feature, then it is probably okay for that to just fail on import.
* `all`: Everything including `docs` and `test`.  Perhaps this should always be spelled

    ```toml
    all = [
        "mmfutils[full,test,docs]"
    ]
    ```
    
    with `mmfutils` replaced by the package name?  (I don't think `".[full,test.docs]"`
    is supported.)

After you have finished editing [`pyproject.toml`][], you should check the dependencies
with your tool of choice, for example:

```bash
make shell
pdm update
```

# [Conda][] Dependencies

The development environment will generally be created with [micromamba][] as specified
in the `environment.yaml` file.  My current simplified approach is as follows:

1. Optionally use an `environment.yaml` file managed with [micromamba][] to setup the
   base environment.
2. Use `pip` (managed by another tool like [PDM][] or [Poetry][]) to provision pure
   python dependencies.
3. Control this with a `Makefile` that supports the following targets:

   * **`make tools`**:
     * Install necessary tools into `.local/bin/`.
   * **`make init`**: 
     * Initializes the environment.
     * Installs the Jupyter kernel for the environment.
   * **`make shell`**:
     * Spawns a shell with an initialized environment (similar to `poetry shell`).
   * **`make realclean`**:
     * Remove the kernel, all environments, cache files etc.

## Makefile

If we use some form of [Conda][], [micromamba][] or [anaconda-project][], then we need
the following commands, which we provide through appropriately defined variables.  For
all of these, the `conda` command will actually be called with `$(CONDA_EXE)` which can be
set to `mamba` if desired (but this does not work with `micromamba` for all commands).

* `CREATE_ENV`: Create the virtual/conda environment.
  * `conda env create -f environment.yaml -p <env_path>`
  * `micromamba create -f environment.yaml -p <env_path>`
  * `anaconda-project prepare [--spec <env_spec>]`
  * `pdm ???`
  * `poetry ???`
* `UPDATE_ENV`: Update the virtual/conda environment.  This should be fast if the
  environment is already up to date.
  * `conda env update -f environment.yaml -p <env_path>`
  * `micromamba update -f environment.yaml -p <env_path>`
  * `anaconda-project prepare` (Not really needed - this is done before all commands).
  * `pdm ???`
  * `poetry ???`
* `ACTIVATE_ENV`: Activate the virtual environment in the current shell.  We generally do
  not want to do this, but will use this in the `make shell` target.
  * `conda activate <env>`
  * `micromamba activate <env>`
  * `source anaconda-project activate <env>`???
  * `pdm ???`
  * `poetry ???`
* `RUN`: Run a command in the environment.
  * `conda run -p <env>`
  * `micromamba run -p <env>`
  * `CONDA_EXE=$(CONDA_EXE) anaconda-project run`
  * `pdm run`
  * `poetry run`

# Managing Multiple Versions of Python

Supporting multiple versions of python is painful -- especially ensuring that tests
pass.  Consider dropping support for [versions past their
end-of-life](https://devguide.python.org/versions/) if at all possible.  The general
strategy is to add conditional `python_version` entries as needed keep everything
working with previous python versions.  For example, to keep scipy working, one might
include the following:

```toml
scipy = [
    "scipy >= 1.7.3; python_version < '3.8'",
    "scipy >= 1.10.1; python_version >= '3.8' and python_version < '3.9'",
    "scipy >= 1.13.1; python_version >= '3.9' and python_version < '3.10'",
    "scipy >= 1.14.1; python_version >= '3.10'",
]
```

As far as I can tell, there are no tools like [PDM][] or [Poetry][] that do this
automatically.  This is an [acknowledged limition of
PDM](https://frostming.com/en/2024/pdm-lock-strategy/#conditional-dependencies) and also
makes locking difficult  The workaround is to [lock targets][], generating either a
bunch of lock files, or merging these into one.  Thus, you might do the following:
```bash
pdm lock --python="3.9.*" --append
pdm lock --python="3.10.*" --append
pdm lock --python="3.11.*" --append
pdm lock --python="3.12.*" --append
pdm lock --python="3.13.*" --append
```

We provide a target `make pdm.lock` that does this.

[lock targets]: <https://pdm-project.org/en/latest/usage/lock-targets/>


Instead, you must use these to deduce set of working versions.  I do
this by slowly building up set of working versions in a temporary project.

```bash
mkdir tmp && cd tmp
for ver in 3.9 3.10 3.11 3.12 3.13; do
  rm -rf pyproject.toml pdm.lock .pdm-python .venv
  pdm init --python "${ver}" -n  # Start with the lowest version you want to support.
  pdm add numba                  # Try adding the most difficult package. 
  grep numba pyproject.toml 
done

```

Note 

## Testing

To test against multiple versions, we use [Nox][], which is configured in `noxfile.py`.
For this to work, we must have the desired versions of python installed.  This can be
done globally (using the `test` session), using `conda` (using the `test_conda`
session), or using `make envs/py3.9` (I do this on my ARM Mac OS X for example).

Ultimately we would like these tests to run [GitHub][] and/or [GitLab][] with CI.  A
simple solution is to just provision and run [Nox][], but this has the disadvantage
that, if any version of python fails the tests, then the test just fails.


### GitHub CI
A natural strategy for running multiple tests is a [GitHub matrix][].  This works, but
has several limitations:

* Now you get a report of which individual tests fail, but I don't know how to
  incorporate this into status badges. There is a discussion about [status badges for
  matrix builds][], but as of 2025, this seems not to be implemented.  In this
  discussion, the suggestion is made to use [reusable workflows][] with individual
  badges for each workflow.  We discuss this approach below.
* This strategy requires provisioning multiple tests.  In the case of this project, we
  need to install some LaTeX so that matplotlib tests work.  From a development
  perspective, the easiest approach is to `apt-get install texlive-full`, but this
  requires multiple independent downloads of ~6GB of data which is slow and wasteful.  I
  don't have a good solution for this yet but expect there is something:
  * There is support for [GitHub caching][], but you need to specify exactly what is to
    be cached, and it is trivial how to [cache APT packages][], but this discussion has
    some suggestions.
  * There is probably a solution if one first builds a Docker container, then uses this
    as the base environment.
  * Another strategy is to minimize the provisioning.  For `texlive-full`, the following
    might help: [`texlive-full` without all the beef][].  We could also manually
    minimize the packages, but this might be a lot of work.
    
Our current approach uses [reusable workflows][].  This does not help with the caching
issue but gets us badges.  This seems to require one workflow file for each version of
python, so we generate these from our Makefile.


[![Python 3.9 test results][py3.9 badge]][py3.9 workflow]
[![Python 3.10 test results][py3.10 badge]][py3.10 workflow]
[![Python 3.11 test results][py3.11 badge]][py3.11 workflow]
[![Python 3.12 test results][py3.12 badge]][py3.12 workflow]
[![Python 3.13 test results][py3.13 badge]][py3.13 workflow]

[![Python 3.9 test results][gh3.9 badge]][py3.9 workflow]
[![Python 3.10 test results][gh3.10 badge]][py3.10 workflow]
[![Python 3.11 test results][gh3.11 badge]][py3.11 workflow]
[![Python 3.12 test results][gh3.12 badge]][py3.12 workflow]
[![Python 3.13 test results][gh3.13 badge]][py3.13 workflow]


[py3.9 badge]: <https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.9.yaml?label=3.9&logo=GitHub>
[py3.10 badge]: <https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.10.yaml?label=3.10&logo=GitHub>
[py3.11 badge]: <https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.11.yaml?label=3.11&logo=GitHub>
[py3.12 badge]: <https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.12.yaml?label=3.12&logo=GitHub>
[py3.13 badge]: <https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.13.yaml?label=3.13&logo=GitHub>

[gh3.9 badge]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.9.yaml/badge.svg>
[gh3.10 badge]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.10.yaml/badge.svg>
[gh3.11 badge]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.11.yaml/badge.svg>
[gh3.12 badge]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.12.yaml/badge.svg>
[gh3.13 badge]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.13.yaml/badge.svg>

[py3.9 workflow]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.9.yaml>
[py3.10 workflow]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.10.yaml>
[py3.11 workflow]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.11.yaml>
[py3.12 workflow]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.12.yaml>
[py3.13 workflow]: <https://github.com/forbes-group/mmfutils/actions/workflows/python_3.13.yaml>



[cache APT packages]: <https://stackoverflow.com/questions/59269850/caching-apt-packages-in-github-actions-workflow>
[Status badges for matrix builds]: <https://github.com/orgs/community/discussions/52616>
[reusable workflows]: <https://docs.github.com/en/actions/sharing-automations/reusing-workflows>
[GitHub caching]: <https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows>
[GitHub matrix]: <https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python#using-multiple-python-versions>
[`texlive-full` without all the beef]: <https://gist.github.com/wkrea/b91e3d14f35d741cf6b05e57dfad8faf>
  



# Tools

When developing applications, one often needs a set of tools (see following section).
The question is: how should these be managed?  Here are some options:

* As part of the package (i.e. specified in the `pyproject.toml`, `environment.yaml`, or
  `anaconda-project.yaml` files).  This is convenient and satisfies the DRY principle,
  but can cause some issues if the tool dependencies conflict with the project itself.
* [PDM][] development groups.  As of version 1.5.0, PDM supports [development-only
  dependencies][] that won't appear in the package index and should not affect the main
  package dependencies.  (I am not sure if [Poetry][] has a similar functionality.)
* In a separate [Conda][] environment.  Unlike the previous approaches, this allows one
  to install tools that require [Conda][].  This separates the dependencies, but
  provides a clean place for them -- `environment.tools.yaml`.
* Install each tool in an isolated environment with [PipX][] (or [CondaX][], but there
  are some issues, e.g. a lack of scriptable ways of locating the packages, or
  specifying python versions).  The current question is: where should one specify these
  dependences?  A nice solution from the user's perspective is to have separate targets
  in `Makefile` for each tool.  However, I think this means we need to specify the
  versions in the `Makefile`, or do some parsing.  It might also be a burden
  maintaining.  Perhaps an automatic rule could be used for `$(BIN)/tool:
  <what_file_here?>` which runs `pipx` to install the tool as specified in
  `<what_file_here?>`. (`requirements.txt`, or maybe a section in `pyproject.toml`?
  Probably needs custom parsing.)
  
For now I am going with `environment.tools.yaml` as it seems the simplest to maintain.

[development-only dependencies]: 
  <https://pdm.fming.dev/latest/usage/dependency/#add-development-only-dependencies>

## Useful Tools

* [PipX][]: A tool for installing packages in independent environments.
* [Coverage][]: Normally this is installed along with PyTest, but it can be needed as a
  standalone tool for `make clean` which calls `coverage erase` to remove the coverage
  files.  One could do this manually, but config files can override the default
  location.  Using the tool itself takes care of this.
* [Nox][]: a command-line tool that automates testing in multiple Python environments,
  similar to tox, but using a standard Python file for configuration.  Nox is configured
  via a `noxfile.py` file.
* [Jupytext][]: Converts notebooks.  More of a development tool, but often used in `make sync`.
* [Nbconvert][]: Similar and needed by [Jupytext][], but cannot be installed in the same
  environment with [PipX][].
* [PDM][]: a Python package management tool that allows you to manage your project
  dependencies and environments in a more flexible and efficient way than pip. It is
  built on top of pip and provides additional features such as dependency resolution,
  lock files, and build isolation. PDM is not limited to a specific build backend; users
  have the freedom to choose any build backend they prefer.
* [Poetry][]: Another Python package management tool that aims to provide a simple and
  reliable way to manage project dependencies. Poetry uses a lock file to ensure
  repeatable installs and provides features such as dependency resolution, virtual
  environments, and build isolation. 
* [micromamba][]: A fast and small alternative to [conda][].  It can be installed [as
  follows](https://mamba.readthedocs.io/en/latest/installation.html#install-script):

  ```bash
  "${SHELL}" <(curl -L micro.mamba.pm/install.sh)`
  ```
  
  This will install the executable into `~/.local/bin/micromamba`.  If you want to
  control this, you must explicitly choose a download. See the results of `curl -L
  micro.mamba.pm/install.sh` for an idea of how to modify this.  Currently I am using:
  
  ```bash
  $(MICROMAMBA):
  	"$(SHELL)" <(curl -L micro.mamba.pm/install.sh | \
  	                     sed "s:~/.local/bin:$(dir $@):g" | \
  	                     sed "s:\[ -t 0 \]:false:g" | \
  	                     sed 's:YES="yes":YES="no":g')
  ```
  
  [micromamba][] has some slight differences with [conda][], but is a very workable
  replacement.
  * There is not `micromamba env` like `conda env`.  One should just use `micromamba`.
    However, this probably means that [`anaconda-client`][] is not supported: I have
    not found a way of installing an environment from `anaconda.org` like `conda env
    create mforbes/work`, which pulls from an environment spec hosted on Anaconda cloud.
  * It seems that if you create an environment with `CONDA_SUBDIR=osx-64 micromamba`,
    then, after that environment, it will pull from the correct subdir.  This is
    different from (and better than) [conda][], which requires also running the rather
    magic `conda config --env --set subdir $(CONDA_SUBDIR)` command.
    
    ```bash
    CONDA_SUBDIR=osx-64 micromamba create -y -c defaults -p osx-64/ "python~=3.11"
    CONDA_SUBDIR=osx-arm64 micromamba create -y -c defaults -p osx-arm64/ "python~=3.11"
    micromamba install -c defaults -p osx-64/ numpy     # Pulls osx-64 version of numpy
    micromamba install -c defaults -p osx-arm64/ numpy  # Pulls osx-arm64 version of numpy
    ```
    
    In contrast, [conda][] needs additional machinations:
    
    ```
    # Both of these pull the WRONG osx-arm64 version of numpy
    conda install -c defaults -p osx-64/ numpy
    conda run -p osx-64 conda install -c defaults -p osx-64/ numpy
    
    # This works... and we will use this to be careful.
    CONDA_SUBDIR=osx-64 conda install -c defaults -p osx-64/ numpy
    
    # Otherwise, we need conda config... which annoyingly does not accept -p...
    conda run -p osx-64 conda config --env --set subdir osx-64

    # Now ONLY this one works:
    conda run -p osx-64 conda install -c defaults -p osx-64/ numpy
    ```
* [Anaconda Project][]:  A tool for managing data science projects that provides an easy
  way to create, share, and reproduce data science workflows. It allows you to specify
  required packages and multiple Conda environments in an `anaconda-project.yaml` file.
* [Black][]: A Python code formatter that reformats your code to make it more readable
  and consistent. If you want to format Jupyter Notebooks, install with `pip install
  "black[jupyter]"`.  Note: if you want to format cells in the notebook with the you
  must install `black` in the kernel, not the environment running `jupyter` (though `pip
  install "black[jupytyer]"` in that environment is a convenient way of installing the
  extension).  (See [issue #26](https://github.com/drillan/jupyter-black/issues/26).)
* [Jupytext][]: A Python package that provides two-way conversion between Jupyter
  notebooks and several other text-based formats like Markdown (we generally use [MyST][]
  Markdown files).

# Working Environment (Conda/Pip and all that)

Our goal is to be able to use [conda][] for packages that might require binary installs,
such as `pyfftw`, `pyvista`, `numpy` etc., but allow [pip][], [PDM][], or [Poetry][] to
be used for pure python packages.  Our strategy attempts to balance the following
desires/features/issues:

*  [Conda][] is the most convenient choice for managing binary installs in a platform
   independent way.  Alternatives include using package managers (platform dependent)
   like `apt`, `macports`, or building from source, but this can be tricky.
   
   A concrete example is [CuPy][] which requires very specific versions of the [CUDA][]
   toolkit, so generically upgrading to the latest might not be compatible.  [Conda][]
   allows one to resolve all of these issues **if** a package has been built.
*  [Conda][] can be very slow/memory intensive, especially if searching `conda-forge`.
   [Mamba][] can sometimes help, but is not always the solution.  [Micromamba][] seems
   to work very nicely.
   
   A concrete example is [CoCalc][] where even `conda search` can exhaust the memory since
   the default [Conda][] installation has a huge list of channels.  Reducing the number of
   channels solved this problem.  [Mamba][] works too, but [Micromamba][] is much better.
   
   <details><summary>Sample CoCalc Session</summary>
   
   Consider the following `environment.tools.yaml` file:
   
   ```yaml
   name: tools
   channels:
     - defaults
   dependencies:
     - python~=3.11
     - pip
     - pip:
       - pipx
       - black
       - jupytext
   ```
   
   
   ```bash
   $ conda clean --all --yes
   $ time anaconda2022 && /usr/bin/time -v conda env create -f environment.tools.yaml -p envs/tools
   Starting Anaconda Python environment
   Run 'exit-anaconda' to return to the standard terminal

   real	0m1.050s
   user	0m0.720s
   sys	0m0.246s
   Collecting package metadata (repodata.json): - Command terminated by signal 9
       Command being timed: "conda env create -f environment.tools.yaml -p envs/tools"
       User time (seconds): 44.69
       System time (seconds): 5.43
       Percent of CPU this job got: 93%
       Elapsed (wall clock) time (h:mm:ss or m:ss): 0:53.86
       ...
       Maximum resident set size (kbytes): 1905264 (1.8GB) 
   ```
   Crashes after running out of memory (~ 2GB).

   ```bash
   $ conda clean --all --yes
   $ time anaconda2022 && /usr/bin/time -v mamba env create -f environment.tools.yaml -p envs/tools
   Command being timed: "mamba env create -f environment.tools.yaml -p envs/tools"
       User time (seconds): 35.37
       Elapsed (wall clock) time (h:mm:ss or m:ss): 0:57.77
       ...
       Maximum resident set size (kbytes): 515596 (504MB)
   ```
   Uses 28% of 2GB.
      
   ```bash
   $ rm -rf envs
   $ micromamba clean --all --yes
   $ /usr/bin/time -v micromamba create -y -f environment.tools.yaml -p envs/tools
       Command being timed: "micromamba create -y -f environment.tools.yaml -p envs/tools"
       User time (seconds): 10.49
       System time (seconds): 2.43
       Percent of CPU this job got: 59%
       Elapsed (wall clock) time (h:mm:ss or m:ss): 0:21.58
       ...
       Maximum resident set size (kbytes): 66076 (65MB)
   ```

   This demonstrates that `micromamba` is a reasonable solution.  Even if we use
   `conda-forge` (though this is about twice as slow and uses thrice as much
   memory):

   ```bash
   $ rm -rf envs
   $ micromamba clean --all --yes
   $ /usr/bin/time -v micromamba create -y -f environment.tools.yaml -p envs/tools
   Command being timed: "micromamba create -y -f environment.tools.yaml -p envs/tools"
       User time (seconds): 21.59
       System time (seconds): 3.75
       Percent of CPU this job got: 54%
       Elapsed (wall clock) time (h:mm:ss or m:ss): 0:46.38
       ...
       Maximum resident set size (kbytes): 207756 (203MB)
   ```
   </details>
*  [Anaconda Cloud][] is a very convenient way of distributing environments: 

   ```bash
   conda install anaconda-client
   conda env create mforbes/work
   ```
   
   It would be ideal if this could give a fully provisioned environment `work` with both
   a useful set of python libraries for development and python-dependent utilities such
   as [black][], [cookiecutter][] and [mercurial][].  I no longer know how to do this (see
   below) -- please let me know if you have an idea.
*  Conflicts can be very problematic, especially for monolithic environments.  The
   [Anaconda][] meta-package manages, but I think it is a lot of work to maintain.
   
   I used to do this with my `work` environment, but when I switched to a new Mac with
   an [ARM][] processor, I started to run into major conflicts.  It turns our that most of
   these are caused by utilities like [coockiecutter][] and [black][] (which required
   conflicting versions of [click][]).
   
   As a result, I now recommend separately installing utilities.  In principle, this can
   be done using [pipx][] and [condax][], but these are not very flexible right now, so
   instead, I recommend manually doing this.
   
*  [Poetry][] does a more careful job of inspecting and managing dependencies -- breaking
   early, but producing a more reliable build specification.

1. Allows these conda environments to be installed in a read-only environment (i.e. as a
   separate `conda` user).
2. Allows us to install additional project dependencies if needed.
3. 

This kind of works: if you activate a conda environment that you do not have
write-access to, then you can at least use `python -m pip install --user` to install
additional packages, which will go in the directory
[`site.USER_BASE`](https://docs.python.org/3/library/site.html#site.USER_BASE) which can
be customized with the
[`PYTHONUSERBASE`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUSERBASE)
environment variable.  Unfortunately, this approach does not allow you to install
additional packages with [conda][].

## Option 1 (Recommendation as of March 2023)

1. Install [Miniconda][] on your system, preferably as a separate `conda` account and
   user.  E.g., on my Mac:
   
   ```bash
   # Install miniconda as conda user
   ssh conda
   bash Miniconda3-latest-MacOSX-arm64.sh -ubp /data/apps/conda
   
   # Update base environment
   conda install -n base anaconda-client
   conda update -n base --all
   conda env update mforbes/base
   conda activate base
   
   # Install standalone packages from environment files
   conda env create mforbes/hg
   ln -s /data/apps/conda/envs/hg/bin/hg /usr/local/bin/

   # Cookiecutter from source:
   PIPX_BIN_DIR=/usr/local/bin
   pipx install git+https://github.com/cookiecutter/cookiecutter.git@2.0.2#cookiecutter
   pipx install black
   
   # Poetry recommended install
   mkdir /data/apps/
   curl -sSL https://install.python-poetry.org | POETRY_HOME=/data/apps/poetry/ python3 -
   ln -s /data/apps/poetry/bin/poetry /usr/local/bin/
   ```
   
   Notes:

   * I include a `conda` alias in my `~/.ssh/config` to log me in.  It looks like
     this:
       
     ```
     # ~/.ssh/config
     ...
     Host conda
       Hostname localhost
       ForwardAgent yes
       User conda
     ```
   * On newer versions of Mac OS X, you need to [jump through some
     hoops](https://stackoverflow.com/questions/58396821) to make a new root folder like
     `/data` (called a "firm link").
   
   
The recommended approach is to use [Anaconda Project][] to specify an environment in an
`anaconda-project.yaml` file.  This allows you to specify the [conda][] dependencies, then
customize the remaining installs with [pip][].  Here is a minimal example:

```yaml
# anaconda-project.yaml
name: myenv
variables:
  CONDA_EXE: mamba   # If you want to use mamba

# This may be called `packages:` but then plain conda will fail.
dependencies:
  - python=3.9
  - numpy
  - pip
  - pip:
    - uncertainties

env_specs:
  myenv:
    channels: []
```

This will create a local environment in `envs/myenv` (as specified in the `env_specs`
section - you can have many) with [conda][] provisioning `python` and `numpy` while [pip][]
provisions `uncertainties`.  Note: you can generate a more complete
`anaconda-project.yml` file by running `anaconda-project init`.  If you use
`dependencies:` rather than `packages:` as in this example, then you can also use
[conda][] directly

```bash
conda env create -f anaconda-project.yaml
```

which will create an environment `myenv` (as specified by the `name` - [conda][] will
currently ignore the `env_specs`).  I use this on [Read the Docs][] for example.

## Option 2 (experimental)
If you want to use [Poetry][] instead of [pip][], then I recommend adding a command that
runs poetry after the environment is created.  In this case, you should really manage as
many dependencies with [Poetry][] as possible, using [anaconda project][] for only the
things where you really need [conda][].

```yaml
# anaconda-project.yaml
name: myenv

commands:
  init:
    unix: |
      poetry install
      #python3 -m ipykernel install --user --name "myenv" --display-name "Python 3 (myenv)"
      #jupyter nbextensions_configurator enable --user
    env_spec: myenv
  shell:
    unix: bash --init-file .init-file.bash
    env_spec: myenv

dependencies:
  - python=3.9
  - poetry   # Not the recommended way of installing poetry
  - numpy
  - pip

env_specs:
  myenv:
    channels: []
```

Here we provide an `anaconda-project run init` function that will first provision the
[conda][] environment in `envs/myenv`, then run [Poetry][].  You might also use the `init`
function to install a [Jupyter][] kernel, or perform other setup functions.

We also include an `anaconda-project run shell` command which behaves like `poetry
shell`, first activating the [conda][] environment, then spawning a shell with a local
init file where you can specify any additional build features.  For example, here we
explicitly use [conda][] to activate the environment, so we get the name in the prompt:

```bash
# .init-file.bash
export PS1="\h:\W \u\$ "
source $(conda info --base)/etc/profile.d/conda.sh

# Assume that this is set by running anaconda-project run shell
CONDA_ENV="${CONDA_PREFIX}"
conda deactivate
conda activate                 # Actvate the base environment
conda activate "${CONDA_ENV}"  # Now activate the previously set environment
alias ap="anaconda-project"
alias apr="anaconda-project run"

_exclude_array=(
    -name ".hg" -or
    -name ".git" -or
    -name '.eggs' -or
    -name '.ipynb_checkpoints' -or
    -name 'envs' -or 
    -name "*.sage-*" -or
    -name "_build" -or
    -name "build" -or
    -name "__pycache__"
)
# Finding stuff
function finda {
    find . \( "${_exclude_array[@]}" \) -prune -or -type f \
         -print0 | xargs -0 grep -H "${*:1}"
}

function findf {
    include_array=( -name "*.$1" )
    find . \( "${_exclude_array[@]}" \) -prune -or \( "${include_array[@]}" \) \
         -print0 | xargs -0 grep -H "${*:2}"
}

function findpy { findf py "${*}"; }
function findipy { findf ipynb "${*}"; }
function findjs { findf js "${*}"; }
function findcss { findf css "${*}"; }
```

We also define convenient aliases and functions.

### Caveats
* This will no longer work out-of-the-box on [Read the Docs][].  Instead, you will need to
  provision the other dependencies in your [Sphinx][] `conda.py` file.  For example:
  
  ```python
  # conf.py
  import os
  import subprocess
  on_rtd = os.environ.get("READTHEDOCS") == "True"
  
  ...
  
  # Allows us to perform initialization before building the docs.
  def my_init():
      """Run `anaconda-project run init`, or the equivalent if on RtD.

      We must customize this for RtD because we trick RTD into installing everything from
      `anaconda-project.yaml` as a conda environment.  If we then run `anaconda-project
      run init` as normal, this will create a **whole new conda environment** and install
      the kernel from there.
      """
      if on_rtd:
          print(f"On RTD in directory {os.getcwd()}!")
          subprocess.check_call(
              [
                  "pip",
                  "install",
                  "--upgrade",
                  "--use-feature=in-tree-build",
                  "../..[docs]",
              ]
          )
          subprocess.check_call(
              [
                  "python3",
                  "-m",
                  "ipykernel",
                  "install",
                  "--user",
                  "--name",
                  "phys-581-2021",
                  "--display-name",
                  "Python 3 (phys-581-2021)",
              ]
          )
      else:
          print("Not On RTD!  Assuming you have run anaconda-project run init.")
          # Don't reinstall everything each time or this can get really slow.
          # subprocess.check_call(["anaconda-project", "run", "init"])

  def setup(app):
      my_init()
  ```


## Option 3 (old recommendation)
For working on a specific project, we recommend doing this in the project root folder as follows.  In this
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

## Option 3 (incomplete)

If you do not need to install any additional packages with [conda][], and cannot afford
the disk space issues, then you can create a virtual environment [venv][].  I recommend
managing this with [Poetry][]:

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

If you need to reproduce a conda environment, then [`conda-pack`][] might be the right
tool.  This makes a copy of the environment and all of the files that can then be
archived and reinstalled elsewhere.  At the very least, `conda-pack` provides a check on
the code installed, failing if any files installed by [Conda][] have been overwritten or
are installed twice.

# Packaging

Some examples of packages we manage and their features:

* [sphinxcontrib-zopeext][zopeext]: A pure python package that must test against an incomplete
  matrix of versions of Python and Sphinx.  Hosted on [GitHub][] and is thus a
  reasonable place to look at their versions of CI.
  
  [![zopeext Test badge][]][zopeext GitHub Tests Workflow]
  [![zopeext PyPI badge][]][zopeext PyPI link]
  [![zopeext gh: tag badge][]][zopeext gh: tags]
  [![zopeext Coverage badge][]][zopeext Coverage link]
  [![zopeext Documentation status badge][]][zopeext Documentation link]
  [![zopeext Python versions badge][]][zopeext PyPI link]
  [![zopeext open-ssf badge][]][zopeext open-ssf link]
  [![zopeext gh: tag badge][]][zopeext gh: tags]
  [![zopeext gh: forks badge][]][zopeext gh: forks]
  [![zopeext gh: contributors badge][]][zopeext gh: contributors]
  [![zopeext gh: stars badge][]][zopeext gh: stars]
  [![zopeext gh: issues badge][]][zopeext gh: issues]
* [mmf-setup][]: A package for helping with development.  Has a script `mmf_setup` that
  will setup and environment on [CoCalc][], and has options for installing and
  configuring [Mercurial][], Jupyter notebooks, and customizing the import path.
* [mmfutils][]: This package.

  [![Python 3.9 test results][py3.9 badge]][py3.9 workflow]
  [![Python 3.10 test results][py3.10 badge]][py3.10 workflow]
  [![Python 3.11 test results][py3.11 badge]][py3.11 workflow]
  [![Python 3.12 test results][py3.12 badge]][py3.12 workflow]
  [![Python 3.13 test results][py3.13 badge]][py3.13 workflow]

  [![Python 3.9 test results][gh3.9 badge]][py3.9 workflow]
  [![Python 3.10 test results][gh3.10 badge]][py3.10 workflow]
  [![Python 3.11 test results][gh3.11 badge]][py3.11 workflow]
  [![Python 3.12 test results][gh3.12 badge]][py3.12 workflow]
  [![Python 3.13 test results][gh3.13 badge]][py3.13 workflow]

  [![mmfutils PyPI badge][]][mmfutils PyPI link]
  [![mmfutils gh: tag badge][]][mmfutils gh: tags]
  [![mmfutils Coverage badge][]][mmfutils Coverage link]
  [![mmfutils Documentation status badge][]][mmfutils Documentation link]
  [![mmfutils Python versions badge][]][mmfutils PyPI link]
  [![mmfutils open-ssf badge][]][mmfutils open-ssf link]
  [![mmfutils gh: tag badge][]][mmfutils gh: tags]
  [![mmfutils gh: forks badge][]][mmfutils gh: forks]
  [![mmfutils gh: contributors badge][]][mmfutils gh: contributors]
  [![mmfutils gh: stars badge][]][mmfutils gh: stars]
  [![mmfutils gh: issues badge][]][zopeext gh: issues]

[zopeext]: <https://github.com/sphinx-contrib/zopeext>
[zopeext Test badge]: 
  <https://github.com/sphinx-contrib/zopeext/actions/workflows/tests.yaml/badge.svg>
[zopeext GitHub Tests Workflow]: 
  <https://github.com/sphinx-contrib/zopeext/actions/workflows/tests.yaml>
[zopeext PyPI badge]: 
  <https://img.shields.io/pypi/v/sphinxcontrib-zopeext?logo=python&logoColor=FBE072">
[zopeext Coverage badge]: 
  <https://coveralls.io/repos/github/sphinx-contrib/zopeext/badge.svg?branch=main>
[zopeext Coverage link]: 
  <https://coveralls.io/github/sphinx-contrib/zopeext?branch=main>
[zopeext Documentation status badge]:
  <https://readthedocs.org/projects/zopeext/badge/?version=latest> 
[zopeext Documentation link]:  <https://zopeext.readthedocs.io/en/latest/?badge=latest>
[zopeext Python versions badge]:
  <https://img.shields.io/pypi/pyversions/sphinxcontrib-zopeext?logo=python&logoColor=FBE072>
[zopeext PyPI link]:
  <https://pypi.org/project/sphinxcontrib-zopeext/>
[zopeext open-ssf badge]: 
  <https://api.securityscorecards.dev/projects/github.com/sphinx-contrib/zopeext/badge>
[zopeext open-ssf link]:
  <https://deps.dev/pypi/sphinxcontrib-zopeext>
[zopeext gh: forks badge]:
  <https://img.shields.io/github/forks/sphinx-contrib/zopeext.svg?logo=github>
[zopeext gh: forks]:
  <https://github.com/sphinx-contrib/zopeext/network/members>
[zopeext gh: contributors badge]: 
  <https://img.shields.io/github/contributors/sphinx-contrib/zopeext.svg?logo=github>
[zopeext gh: contributors]:
  <https://github.com/sphinx-contrib/zopeext/graphs/contributors>
[zopeext gh: stars badge]:
  <https://img.shields.io/github/stars/sphinx-contrib/zopeext.svg?logo=github>
[zopeext gh: stars]:
  <https://github.com/sphinx-contrib/zopeext/stargazers>
[zopeext gh: tag badge]:
  <https://img.shields.io/github/v/tag/sphinx-contrib/zopeext?logo=github>
[zopeext gh: tags]:
  <https://github.com/sphinx-contrib/zopeext/tags>
[zopeext gh: issues badge]:
  <https://img.shields.io/github/issues/sphinx-contrib/zopeext?logo=github>
[zopeext gh: issues]:
  <https://github.com/sphinx-contrib/zopeext/issues>


[mmfutils]: <https://github.com/forbes-group/mmfutils>
[mmfutils PyPI badge]: 
  <https://img.shields.io/pypi/v/mmfutils?logo=python&logoColor=FBE072">
[mmfutils Coverage badge]: 
  <https://coveralls.io/repos/github/forbes-group/mmfutils/badge.svg?branch=main>
[mmfutils Coverage link]: 
  <https://coveralls.io/github/forbes-group/mmfutils?branch=main>
[mmfutils Documentation status badge]:
  <https://readthedocs.org/projects/mmfutils/badge/?version=latest> 
[mmfutils Documentation link]:  <https://mmfutils.readthedocs.io/en/latest/?badge=latest>
[mmfutils Python versions badge]:
  <https://img.shields.io/pypi/pyversions/mmfutils?logo=python&logoColor=FBE072>
[mmfutils PyPI link]:
  <https://pypi.org/project/mmfutils/>
[mmfutils open-ssf badge]: 
  <https://api.securityscorecards.dev/projects/github.com/forbes-group/mmfutils/badge>
[mmfutils open-ssf link]:
  <https://deps.dev/pypi/mmfutils>
[mmfutils gh: forks badge]:
  <https://img.shields.io/github/forks/forbes-group/mmfutils.svg?logo=github>
[mmfutils gh: forks]:
  <https://github.com/forbes-group/mmfutils/network/members>
[mmfutils gh: contributors badge]: 
  <https://img.shields.io/github/contributors/forbes-group/mmfutils.svg?logo=github>
[mmfutils gh: contributors]:
  <https://github.com/forbes-group/mmfutils/graphs/contributors>
[mmfutils gh: stars badge]:
  <https://img.shields.io/github/stars/forbes-group/mmfutils.svg?logo=github>
[mmfutils gh: stars]:
  <https://github.com/forbes-group/mmfutils/stargazers>
[mmfutils gh: tag badge]:
  <https://img.shields.io/github/v/tag/forbes-group/mmfutils?logo=github>
[mmfutils gh: tags]:
  <https://github.com/forbes-group/mmfutils/tags>
[mmfutils gh: issues badge]:
  <https://img.shields.io/github/issues/forbes-group/mmfutils?logo=github>
[mmfutils gh: issues]:
  <https://github.com/forbes-group/mmfutils/issues>
  
## Distribution

In general, we will try to distribute projects on [PyPI][] and this will be the primary
mode if distribution.  To use such projects in a [Conda][] environment, just use `pip`:

```yaml
# environment.yaml
...
[dependencies]
  ...
  - pip
  - pip:
    - mmfutils>=0.6
    ...
```

## To Do

* Consider a two-branch model so that one can easily update to the latest development
  branch or the latest default branch.  Maybe default should be the development branch
  and we should have a release branch?  (Thinking about testing and badges... currently
  I have a branch for each version, but this means I need to specify the latest one each
  time.)

To make packages available before their release on [PyPI][], one can make use of the
[`-f, --find-links
<url>`](https://pip.pypa.io/en/stable/cli/pip_wheel/?highlight=find-links#cmdoption-f)
option of `pip`.  If this points to a webpage with links, then these links can define
how to get a package from source etc.  I maintain my own set of links in my [MyPI][]
project.  Unfortunately, until [issue
#22572 *(gitlab is completely unusable without javascript.)*](https://gitlab.com/gitlab-org/gitlab/-/issues/22572) is resolved, GitLab-based
sites are useless for this purpose, so we rely on mirroring through GitHub.

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

# Documentation ([Read the Docs][])

We like to deploy our documentation on [Read the Docs][] (see e.g. [Math 583: Learning
from Signals](https://iscimath-583-learning-from-signals.readthedocs.io/en/latest/)).
Our documentation lives in the `Docs/` directory and is generally built with [Sphinx][]
using the [Jupyter Book][] framework (see [How to replicate Jupyter Book’s functionality
in Sphinx][]).

To build the documentation, manually, activate the environment, then run `make html` in
the documentation directory:

```bash
make shell
cd Docs && make html
```

Alternatively, while actively working on the documentation, you can run:

```bash
make doc-server
```

This will use [`sphinx-autobuild`][] to build and serve the documentation locally on
<http://127.0.0.1:8000>.  This documentation will be updated whenever you change files.

> Caveat: If you documentation literally includes files like `README.md` from the
> top-level, then editing these might not properly trigger a rebuild.  We try to
> mitigate this, but it is buggy.  See details in the `Makefile` and `Docs/index.md`.

To deploy the documentation on [Read the Docs][], push your source to [GitHub][] or [GitLab][],
then link these to the appropriate project on [Read the Docs][].  Once you establish the
appropriate web-hooks, [Read the Docs][] should automatically pull your changes when you
push, and build the documentation.

The documentation build process is controlled by the `.readthedocs.yaml` file.  We use
the following format:

```yaml
# .readthedocs.yaml
version: 2
sphinx:
   configuration: Docs/conf.py
build:
  os: ubuntu-22.04
  tools:
    python: "mambaforge-4.10"
  jobs:
    post_create_environment:
      - python3 -m ipykernel install --user --name math-583
conda:
  environment: environment.yaml
```

This augments the standard build process to register the `math-583` kernel used in the
notebooks.  Otherwise, everything is specified in `environment.yaml`, which can include
`.` as needed.

If you need more control, you can do something like this:

```yaml
# .readthedocs.yaml
version: 2
sphinx:
   configuration: Docs/conf.py
build:
  os: ubuntu-22.04
  tools:
    python: "3"
  commands:
    - make rtd
```

You must make sure that `make rtd` puts the generated documentation in `$READTHEDOCS_OUTPUT/html`.

## Jupyter Book

### Images

There are several ways to include images in your documents. ([JB Images and figures][]).

1. Use [MyST NB][] to generate the figures programmatically.  The output of the
   code-cell will be the figure:
   
   ````markdown
   ```{code-cell}
   :tags: [hide-input]
   
   fig, ax = plt.subplots()
   x = np.linspace(-1, 1)
   ax.plot(x, x**2)
   ```
   ````
   
   For this to work, I usually include something like the following at the top of my
   MyST files.
   
   ````markdown
   ```{code-cell}
   :tags: [hide-cell]

   import mmf_setup; mmf_setup.nbinit()
   from pathlib import Path
   FIG_DIR = Path(mmf_setup.ROOT) / 'Docs/_images/'
   os.makedirs(FIG_DIR, exist_ok=True)
   import logging; logging.getLogger("matplotlib").setLevel(logging.CRITICAL)
   %matplotlib inline
   import numpy as np, matplotlib.pyplot as plt
   try: from myst_nb import glue  # So this runs in plain notebooks without myst_nb
   except ImportError: glue = None
   ```
   ````
2. If you want more control over where the image appears, you can [glue][] it:

   ````markdown
   ```{code-cell}
   :tags: [hide-input]
   
   fig, ax = plt.subplots()
   x = np.linspace(-1, 1)
   ax.plot(x, x**2)
   if glue:  # So this runs in plain notebooks without myst_nb
       glue("fig:parabola, fig)
   ```
   
   Use it like this for a figure, or margin figure with a caption:
   
   ```{glue:figure} fig:parabola
   :figclass: margin

   This is a **caption**.  This figure is a parabola.
   ```
   ````
   
   *Note: this does not work across notebooks [MyST_NB issue #431][].*
3. If you want to reference a figure from another document, you currently must save it.
   I use `mmf_setup.ROOT` to locate this.  Here is code that allows you to do all of it.
   
   ````markdown
   ```{code-cell}
   :tags: [hide-input]
   
   fig, ax = plt.subplots()
   x = np.linspace(-1, 1)
   ax.plot(x, x**2)
   plt.savefig(FIG_DIR / "parabola.svg")
   ```
   
   Now you can use this with a standard `figure` environment.

   ```{figure} /_images/parabola.svg
   :figclass: margin

   This is a **caption**.  This figure is a parabola.
   ```
   ````

Here is complete code that does it all for reference.  (I prefer to break it up.)
````markdown
```{code-cell}
:tags: [hide-input]

import mmf_setup; mmf_setup.nbinit()
from pathlib import Path
FIG_DIR = Path(mmf_setup.ROOT) / 'Docs/_images/'
os.makedirs(FIG_DIR, exist_ok=True)
import logging; logging.getLogger("matplotlib").setLevel(logging.CRITICAL)
%matplotlib inline
import numpy as np, matplotlib.pyplot as plt
try: from myst_nb import glue  # So this runs in plain notebooks without myst_nb
except ImportError: glue = None

fig, ax = plt.subplots()
x = np.linspace(-1, 1)
ax.plot(x, x**2)

if glue:  # So this runs in plain notebooks without myst_nb
    glue("fig:parabola, fig)

plt.savefig(FIG_DIR / "parabola.svg")   # For HTML
plt.savefig(FIG_DIR / "parabola.pdf")   # For LaTeX
```
````

# Repositories

Currently the main repository is on our own [Heptapod][] server, but I have enabled 
`Settings/Repository/Mirroring repositories` to push to a public GitHub mirror
<https://github.com/forbes-group/mmfutils/>.  This required getting a personal token from GitHub
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

* <https://gitlab.com/forbes-group/mmfutils>: Main development repository.  This is
  where [Issues](https://gitlab.com/forbes-group/mmfutils/-/issues), [Merge
  Requests](https://gitlab.com/forbes-group/mmfutils/-/merge_requests) etc. should
  be reported here.
  
  **Note:** This was copied using repository export from our [Heptapod][] server
  <https://hg.iscimath.org/forbes-group/mmfutils>.
* <https://github.com/forbes-group/mmfutils>: Main public mirror (Git) for releases.  Protected
  branches are automatically pushed here.  No development work should be done here: this
  is just for public access, and to use GitHub's CI tools.  This is where badges are
  pulled from etc.
* <https://github.com/mforbes/mmfutils-fork>: My development fork (Git).  Everything is
  pushed here to use GitHub's CI tools during development.  Should not be used for
  anything else.
* <https://hg.iscimath.org/forbes-group/mmfutils>: Old development repository
  (Mercurial) running on our hosted [Heptapod][] server.  Should not be used any more.
  **Note:** To access this, you must connect to the swan server and forward the connections.


## Badges

With CI setup, we have the following badges:

* Documentation at [Read the Docs][].

    [![Documentation Status][rtd_badge]][rtd]

* Testing with GitHub actions.  The first set of badges are with <https://shields.io>:

  [![Python 3.9 test results][py3.9 badge]][py3.9 workflow]
  [![Python 3.10 test results][py3.10 badge]][py3.10 workflow]
  [![Python 3.11 test results][py3.11 badge]][py3.11 workflow]
  [![Python 3.12 test results][py3.12 badge]][py3.12 workflow]
  [![Python 3.13 test results][py3.13 badge]][py3.13 workflow]

  The second set are direct from GitHub, but are a bit unruly:
  
  [![Python 3.9 test results][gh3.9 badge]][py3.9 workflow]
  [![Python 3.10 test results][gh3.10 badge]][py3.10 workflow]
  [![Python 3.11 test results][gh3.11 badge]][py3.11 workflow]
  [![Python 3.12 test results][gh3.12 badge]][py3.12 workflow]
  [![Python 3.13 test results][gh3.13 badge]][py3.13 workflow]

* Style:

    [![Code style: black][black_img]][black]

* *(Obsolete)* Testing at [DroneIO](https://cloud.drone.io) and with GitHub actions:
    
    [![DroneIO Build Status][drone_badge]][drone]
    [![Tests][ci_badge]][ci]

* *(Obsolete)* Code quality testing at [lgtm](https://lgtm.com):

    [![Language grade: Python][lgtm_mmfutils_badge]][lgtm_mmfutils]
    [![Language grade: Python][lgtm_mmfutils_fork_badge]][lgtm_mmfutils_fork]

[rtd_badge]: <https://readthedocs.org/projects/mmfutils/badge/?version=latest>
[rtd]: <https://mmfutils.readthedocs.io/en/latest/?badge=latest>


[drone_badge]: <https://cloud.drone.io/api/badges/forbes-group/mmfutils/status.svg>
[drone]: https://cloud.drone.io/forbes-group/mmfutils
[ci_badge]: <https://github.com/forbes-group/mmfutils/actions/workflows/tests.yml/badge.svg?branch=topic%2F0.6.0%2Fgithub_ci>
[ci]: <https://github.com/mforbes/forbes-group/mmfutils/actions/workflows/tests.yml>

[black_img]: https://img.shields.io/badge/code%20style-black-000000.svg


[lgtm_mmfutils]: <https://lgtm.com/projects/g/forbes-group/mmfutils/context:python>
[lgtm_mmfutils_badge]: <https://img.shields.io/lgtm/grade/python/g/forbes-group/mmfutils.svg?logo=lgtm&logoWidth=18>

[lgtm_mmfutils_fork]: <https://lgtm.com/projects/g/forbes-group/mmfutils/context:python>
[lgtm_mmfutils_fork_badge]: <https://img.shields.io/lgtm/grade/python/g/forbes-group/mmfutils.svg?logo=lgtm&logoWidth=18> 

## Continuous Integration (CI)

As mentioned above, by providing
[`.github/workflows/tests.yml`](.github/workflows/tests.yml), we can engage a [GitHub
action for continuous
integration](https://docs.github.com/en/actions/guides/about-continuous-integration).
This can be configure to run the tests automatically on pushes, the results of which are
displayed in the appropriate badges.

The main difficulty I had was a need for a full LaTeX installation.  This is now
working with `apt-get texlive-full`, but could probably be simplified, just updating the
packages we really need for testing ([`mathpazo`][], [`siunitx`][], and [`type1cm`][] were
issues when just using the smaller [`texlive`][TeX Live] package.)

[`mathpazo`]: <https://ctan.org/pkg/mathpazo> "mathpazo – Fonts to typeset mathematics to match Palatino"
[`siunitx`]: <https://ctan.org/pkg/siunitx> "siunitx – A comprehensive (SI) units package"
[`type1cm`]: <https://ctan.org/pkg/type1cm> "type1cm – Arbitrary size font selection in LaTeX"


### Coverage

For general coverage, it is enough to install [`pytest-cov`][], but this does not work
so well for CI.

For [GitHub][], see [How to Ditch Codecov for Python
Projects](https://hynek.me/articles/ditch-codecov-python/) and the [Hypermodern GitHub
workflow][].  This is a little tricky, because the tests are run in separate machines.
The coverage reports need to be labeled individually, then uploaded as artifacts, and
finally combined after all tests are run.  Following the [Hypermodern GitHub
workflow][], we include a `coverage` session in `noxfile.py`.  Here are some potential
gotchas.

* You need to have at least the following in your `pyproject.toml` file:
  ```toml
  [tool.coverage.run]
  relative_files = true     # Remove the .nox/test-3-10 etc. prefix.
  parallel = true           # Needed to generate .coverage.* files for each process
  source = ["mmfutils"]     # This the installed package.
  ```
* Be careful with [`pytest-cov`][]: It will generate reports and eat the coverage files
  that you are trying to combine.  I think I recommend not using this, and relying on [Nox][].
* If you put the reports in a directory, you must specify this.

[Hypermodern GitHub workflow]:
  <https://github.com/cjolowicz/cookiecutter-hypermodern-python/blob/main/%7B%7Bcookiecutter.project_name%7D%7D/.github/workflows/tests.yml>



* <https://docs.gitlab.com/ee/user/project/badges.html>





Old:

For [GitHub][] one can use [Codecov][]. To do this, sign in, the link your [GitHub][]
account.  Once you give permissions, you can then add public repos.  You will need to
add the `CODECOV_TOKEN` token as a repository secret.  Once this is done, you can add
the following to your `.github/workflows/tests.yaml` workflow:

```yaml
- name: Upload coverage reports to Codecov
  uses: codecov/codecov-action@v3
```

[Codecov]: <https://app.codecov.io/>

## References
* https://stackoverflow.com/questions/67482906/show-coverage-in-github-pr: Discussion of
  how to get coverage reports to show in pull requests on [GitHub][].
* https://cjolowicz.github.io/posts/hypermodern-python-06-ci-cd/
* https://docs.github.com/en/actions/guides/setting-up-continuous-integration-using-workflow-templates

# Testing

We use [pytest][] for testing, running the tests with [Nox][] for multiple versions of
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

Testing is now done using [Nox][] as configured in `noxfile.py`.  This allows for testing
against multiple versions of python (similar to [Tox]) but I find that it is simpler to
use and works with [Conda][].  My general strategy is to use [Conda][] to minimally
provision environments with the desired version of python, then to install the package
with `pip install .[test]` in that environment.  This has the following advantages:

* Generally works.  The typical recommendation (for example in the [Hypermodern Python][]
  series) is to use [PyEnv][].  Unfortunately, this is a pain for me on my Mac OS X
  development machine as [PyEnv][] tries to compile python from source which can take
  forever, and often fails.  (For example, I cannot build `python=3.5.8` for some
  reason, and `miniconda3-3.5.*` is not available.)  Conversely, `conda env create -n
  py3.5 python=3.5` seems to always work for me.  Of course, this does require you to
  install [`miniconda`][] on your machine, which I do with something like this:
  
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

* This approach only used [Conda][] to install python: we then test `pip install` which we
  certainly want to test.

* We can use [Conda][] if we like to test installing dependencies from an
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

### Matrix Testing

Here is an example `noxfile.py` to test a "matrix" of versions, with some exceptions
that do not work:
    
```python
# noxfile.py
import nox

python_versions = ["3.7", "3.8", "3.9", "3.10", "3.11"]
sphinx_versions = {_p: ["4.5.0", "5.3.0", "6.1.3"] for _p in python_versions}
excluded_versions = {("3.7", "6.1.3")}
python_sphinx = [
    (python, sphinx)
    for python in python_versions
    for sphinx in sphinx_versions[python]
    if (python, sphinx) not in excluded_versions
]

@nox.session(reuse_venv=True)
@nox.parametrize("python,sphinx", python_sphinx)
def test(session, sphinx):
    session.install(".[test]", f"sphinx[test]~={sphinx}")
    session.run("pytest", "tests")
```

I would really like to programmatically determine the allowed versions from
[`pyproject.toml`][], and there is an option for doing this with poetry (see [this
discussion](https://github.com/cjolowicz/nox-poetry/discussions/289)) but I have not
found something that works with [PDM][].  (I asked [here]())

### Gotchas

I had a very difficult time with random errors when tested `mmf_setup` that boiled down
to `pip` not installing some packages in the testing environment because they were in
`~/.local`, but then having issues when the underlying tests were running and sometimes
did not have access to these.  (The specific case was when running `run_tests.py` for
Mercurial tests.)

The solution is to make sure that `PYTHONNOUSERSITE=1` before running anything.

* See: https://stackoverflow.com/a/51640558/1088938


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


# Profiling (Incomplete)

To measure peak memory usage, look at [Fil][].  Write your test-code as a script, then run
it with `fil-profile`:

```bash
fil-profile run test_script.py
```

# Releases

We try to keep the repository clean with the following properties:

1. The default branch is stable: i.e. if someone runs `hg clone`, this will pull the
   latest stable release.
2. Minor version numbers each have their own named branch.  *(We used to use a named
   branch for each release, but named branches and tags conflict, so we now only use
   named branches for the minor versions, and use tags for each release.)*
3. We use topics for each release.  Thus, branch `0.7` would contain topic `0.7.0` until
   this is released.  Upon release, we tag the topic so that `hg up 0.5.0` will get the right
   thing.  Note: this should update to the development branch, *not* the default branch
   so that any work committed will not pollute the default branch (which would
   violate point 1).

To do this, we advocate the following procedure.

1. **Update to Correct Branch**: Make sure this is the correct development branch, not
   the default branch by explicitly updating:

    ```bash
    hg up <version>
    ```
   
   This should update to the branch or topic. *(Compare with `hg up default` which
   should take you to the default branch instead.)*
2. **Work**: Do your work, committing as required with messages as shown in the
   repository with the following keys: 
    * `DOC`: Documentation changes.
    * `API`: Changes to the exising API.  This could break old code.
    * `EHN`: Enhancement or new functionality. Without an `API` tag, these should not
      break existing codes. 
    * `BLD`: Build system changes (`setup.py`, `requirements.txt` etc.)
    * `TST`: Update tests, code coverage, etc.
    * `BUG`: Address an issue as filed on the issue tracker.
    * `BRN`: Start a new branch (see below).
    * `REL`: Release (see below).
    * `WIP`: Work in progress.  Do not depend on these!  They will be stripped.  This is
      useful when testing things like the rendering of documentation etc. where you need
      to push an incomplete set of files.  Please collapse and strip these eventually
      when you get things working.
    * `CHK`: Checkpoints.  These should not be pushed.
3. **Tests**: Make sure the tests pass.  Comprehensive tests should be run with `make test`:
   
   ```bash
   make test
   ```
    
   *(This just runs `nox`, but gives an opportunity to do other things if needed, like
   installing `nox` for example.)*
   
   Quick tests while developing can be run with `make shell`:
   
   ```bash
   make shell
   pytest
   ```

   You can optionally specify a different version of python by setting `DEV_PY_VER`:

   ```bash
   DEV_PY_VER=3.10 make shell
   ```

4. **Update Docs**: Update the documentation if needed.  To generate new documentation run:

    ```bash
    make shell
    cd doc
    sphinx-apidoc -eTE ../src/mmfutils -o source
    ```
   
    * Include any changes at the bottom of this file (`doc/README.ipynb`).
    * You may need to copy new figures to `README_files/` if the figure numbers have
      changed, and then `hg add` these while `hg rm` the old ones.
   
    Edit any new files created (titles often need to be added) and check that this looks good with
  
    ```bash
    make html
    open build/html/index.html
    ```
     
    Look especially for errors of the type "WARNING: document isn't included in any
    toctree".  This indicates that you probably need to add the module to an upper level
    `.. toctree::`.  Also look for "WARNING: toctree contains reference to document
    u'...' that doesn't have a title: no link will be generated".  This indicates you
    need to add a title to a new file.  For example, when I added the
    `mmf.math.optimize` module, I needed to update the following:
  
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
  
5. **Clean up History**: Run `hg histedit`, `hg rebase`, or `hg strip` as needed to
   clean up the repo before you push.  Branches should generally be linear unless there
   is an exceptional reason to split development.
   
6. **Release**: First edit `pyproject.toml` to update the version number by removing the
   `dev` part of the version number.  Commit only this change and then push only the
   branch you are working on:

    ```bash
    hg com -m "REL: <version>"
    hg push -r .
   ```
   
7. **Pull Request**: Create a pull request on the development fork from your branch to
   `default` on the release project. Review it, fix anything, then accept the merge
   request.  **Do not close the branch!** Unlike bitbucket, if you close the branch on
   Heptapod, it will vanish, breaking our [MyPI][] index.
   
8. **Publish on PyPI**: Publish the released version on
   [PyPI](https://pypi.org/project/mmfutils/) using
   [twine](https://pypi.org/project/twine/) 

    ```bash
    # Build the package.
    python setup.py sdist bdist_wheel
    
    # Test that everything looks right:
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   
    # Upload to PyPI
    twine upload dist/*
    ```

9. **Build Conda Package**: This will run all the tests in a fresh environment as
   specified by `meta.yaml`.  Make sure that the dependencies in `meta.yaml`,
   `environment.yml`, and `setup.py` are consistent.  Note that the list of versions to
   be built is specified in `conda_build_config.yaml`. 

    ```bash
    conda build .
    conda build . --output   # Use this below
    anaconda login
    anaconda upload --all /data/apps/conda/conda-bld/noarch/mmfutils-0.5.0-py_0.tar.bz2
    ```
   
10. **Start new branch**: On the same development branch (not `default`), increase the
    version number in `mmfutils/__init__.py` and add `dev`: i.e.: 

    ```python
    __version__ = '0.5.1dev'
    ```
       
    Then create this branch and commit this:
  
    ```bash
    hg branch "0.5.1"
    hg com -m "BRN: Started branch 0.5.1"
    ```
       
11. Optional: Update any `setup.py` files that depend on your new features/fixes etc.

`mmfutils`: This Package
========================

Here we have details about this package specifically.  *Note: I think I am recommending
[PDM][] for package management but have not completely decided, so wherever you see [PDM][]
referenced below, please consider that this might change to [Poetry][], [Hatch][], or
something similar in the future.*

## Dependencies

We specify project dependencies in three places:

* `anaconda-project.yaml`: This contains any dependencies that should be installed with
  [Conda][], especially binary dependencies.  In principle, this provides a complete
  solution with both [Conda][] and [Pip][] sections as well as the ability to define
  custom commands.  I played with this for a while, and it can be quite convenient, but
  once dependencies become sufficiently complicated, it becomes advantageous to used
  [PDM][] or [Poetry][] to manage the python dependencies in [`pyproject.toml`][].  If you
  are starting from scratch (i.e. not using our [cookiecutters][]
  
  As we discuss below, we can include python-version specific dependencies in
  sub-environments if needed.  We might be able to also specify some platform-dependent
  dependencies in sub-environments but have not yet explored this.
  
  In principle, `anaconda-project add-packages` could be used for this, but currently
  this can cause problems, so we recommend just editing `anaconda-project.yaml` by hand
  for now.  This should be pretty minimal: things like `pyfftw` or `cupy` that have
  tight integration with binary packages.


## The Development Process: Makefiles

We currently drive our development process with [GNU make][] as specified in the project
`Makefile`.  This encodes all of our "wisdom" about platform dependence etc.  We
specifically provide the following targets:

* `make init`: Initialize the environment and make sure packages are up to date.
* `make shell`: Depends on `make init` and then open a shell that one can use to run
  commands in the project such as `jupyter notebook`, or `pytest`. This is most similar
  to `poetry shell`.
* `make qshell`: Do this quickly without checking.  This will create the environment if
  needed (`make dev`) but will not check or update an existing environment.
* `make clean`: Remove most intermediate files.  Often this will leave environments
  available so that it is easy to resume work, but will remove temporary files, log
  files, etc.
* `make realclean`: Remove as much as possible, including all environments, installed
  kernels etc.  This should be the equivalent of "get everything except the source off
  of my computer and reclaim as much disk space as possible".  After this command, you
  should be very close to 
* `make test`: This should run all of the tests in the development environment.
* `make doc-server`: If the project has documentation, then this launch the
  documentation server.
* `make dev`: This builds the development environment.  It is not intended to be used
  explicitly, but is done by many other commands like `make shell`.  Currently, this is
  done as follows:
  1. Some form of `conda` is used to create an environment in `envs/`.  This will
     contain a version of `python` as well as any libraries that may be needed (`fftw`,
     `cuda` etc.)
  2. `PDM` or `poetry` will be instructed to use this environment and will install the
     project and its dev dependencies.
* `make info`: Print debugging information.

### Details

We support several options defined by the following flags:
* `USE_ANACONDA_PROJECT`: Use [Anaconda Project][] to build environments.
* `USE_PDM`: Use [PDM][] to install pure python packages.
* `USE_POETRY`: Use [Poetry][] to install pure python packages.

Only one of `USE_PDM` or `USE_POETRY` should be true, but these can be used with or
without `USE_ANACONDA_PROJECT`.

Some environmental variables need to be exported to subcommands.  To do this, we must
enclose commands in parentheses:

```bash
$ CONDA_SUBDIR=osx-64 pdm run echo $CONDA_SUBDIR

$ (export CONDA_SUBDIR=osx-64 && pdm run echo $CONDA_SUBDIR)
osx-64
```


#### Conda and Anaconda Project
To build the [Conda][] environments we use [Anaconda Project][] for a couple of
reasons.  First, we can specify all of our dependencies and it still functions like an
`environment.yaml` file, as long as we rename `packages:` to `dependencies:`.  Second,
this allows us to customize environments for different versions of python.  Our
`Makefile` runs `anaconda-project add-env-spec`, which will fill these out if they were
not initially provided by the project.

We then install the development tools into this environment using [PDM][], [Poetry][],
or [Pip][]. *Initially I tried simply using the conda environment for the interpreter
with a custom virtual environment managed by these tools, but this fails in many cases.
For example, even if we install [PyFFTW][] in the conda environment, these tools cannot
compile it because the underlying `fftw` library does not exist. One must then be
careful that everything matches so that the `PDM`/`Poetry` install accepts it.*

In principle, the `anaconda-project.yaml` file can replace the `Makefile` (by defining
`commands`) and [`pyproject.toml`][] (using the `pip:` section of `dependencies:`), but this
does not work for us in all cases.  For example, on my new [ARM][] Mac, I sometimes need
to create an environment using `CONDA_SUBDIR=osx-x64` (Intel) as opposed to
`CONDA_SUBDIR=osx-arm64`.  Until issue [anaconda-project#392][] is resolved, the only
way for this to work is for this to be set **before** calling `anaconda-project`, but I
can't remember this, so I want this codified in my `Makefile`.  This may be a viable
option in the future.

[anaconda-project#392]: <https://github.com/Anaconda-Platform/anaconda-project/issues/392>


One can control the version
  of python by setting `DEV_PYTHON_VER`.  
  
[GNU make]: <https://www.gnu.org/software/make/manual/make.html>

Our development process is outlined in `Makefile`, and works as follows.  First we
explain in simple terms:

* We use `conda` to create a development environment in `envs/name-py3.9`.
with the 

### Things that Did Not Work

* Creating a [conda][] environment with binary dependencies, but then just using the
  conda-installed python in other virtual environments.  For example, creating a conda
  environment with [pyfftw][] would not allow one to build [pyfftw][] from source.  The
  [moral](https://fosstodon.org/@tacaswell/109548682896553945) is that [Conda][]
  environments need to be activated to work.  The only case where we break this
  assumption is when we use [Conda][] to install **only** python for [nox][] to use.  I
  think in this case it would be better to get [nox][] to do this on its own, but am not
  yet sure how to deal with platform dependence. 
  
  (The specific issue was that, on my new Mac M1 Max with an ARM processor, sometimes I
  needed to use Rosetta i.e. `CONDA_SUBDIR=osx-x64` as opposed to
  `CONDA_SUBDIR=osx-arm64`.  Another issue, now resolved, was that the ARM version of
  Python 3.11 was only available on `conda-forge`, but I try to avoid included
  `conda-forge` in my channels for performance reasons.)

* With my [zopeext][] project, I tried to support a variety of different versions of
  Python and Sphinx.  Unfortunately, there seems to be no good way of doing this:
  * There is no simple "matrix" of versions that work together.  For example, consider
    Python 3.7 and Sphinx 3.4.3:
  
    ```bash
    $ python3.7 -m venv .venv
    $ . .venv/bin/activate
    (.venv) $ pip install sphinx[test]==3.4.3
    (.venv) $ python3.7 -c "import sphinx.testing.fixtures"
    Traceback (most recent call last):
      ...
      File ".../.venv/lib/python3.7/site-packages/sphinx/util/rst.py", line 21, in <module>
        from jinja2 import Environment, environmentfilter
    ImportError: cannot import name 'environmentfilter' from 'jinja2' (.../.venv/lib/python3.7/site-packages/jinja2/__init__.py)
    ```
    
    To resolve this, one needs to pin `jinja2<3.0.0`...
    
    ```bash
    (.venv) $ pip install --upgrade "sphinx[test]==3.4.3" "jinja2<3.0.0"
    (.venv) $ python3.7 -c "import sphinx.testing.fixtures"
    Traceback (most recent call last):
       ...
      File ".../.venv/lib/python3.7/site-packages/jinja2/filters.py", line 13, in <module>
        from markupsafe import soft_unicode
    ImportError: cannot import name 'soft_unicode' from 'markupsafe' (.../.venv/lib/python3.7/site-packages/markupsafe/__init__.py)
    ```
    ... and, if `jinja2<3.0.0`, then we need `markupsafe<2.1.0`.
    
    ```bash
    (.venv) $ pip install --upgrade "sphinx[test]==3.4.3" "jinja2<3.0.0" "markupsafe<2.1.0"
    ```
    
    Of course, I only want to do this if the user insists on installing
    `sphinx<=3.4.3`. I have no idea how to do this, or even if it is possible.

  My current resolution is that I should simply not try to provide such backwards
  compatibility in python.  If someone needs this, they can install older versions of my
  packages, (hopefully they have a lock file with all of the appropriate dependencies),
  and moving forward, I just use lower bound constraints.  Of course, with such a
  change, I would release a new minor version, and indicate clearly in the change log
  which versions are no longer supported.

    
## PDM

We currently [PDM][] for managing the dependencies.  Pure python dependencies should be
specified in the [`pyproject.toml`][] file, whose format is discussed here:

* [Declaring project metadata (from PEP 621)][]
* [`pyproject.toml`][]

[Declaring project metadata (from PEP 621)]:
  <https://packaging.python.org/en/latest/specifications/declaring-project-metadata/>

### Issues

Although [PDM][] is possibly the best current option, there are still many unresolved
issues as of March 2023:

* [#46: Dependencies get overriden when there are multiple versions of different
  markers][pdm#46]: This explains why it is so hard to support multiple versions of
  python.
  

[pdm#46]: <https://github.com/pdm-project/pdm/issues/46>
## Poetry

DEPRECATED: We no longer use [Poetry][] for several reasons, preferring [PDM][] instead:

1. They strongly advocate using upper bound constraints, we causes real problems.  See
   Henry Schreiner's discussion [Should You Use Upper Bound Version
   Constraints](https://iscinumpy.dev/post/bound-version-constraints/) for a nice
   discussion.
2. They do not follow the standards, so the [`pyproject,toml`][] file they generate is not
   compliant.
   

* TL;DR: With the current project, you can do all of this with:

    ```bash
    make dev
    poetry shell
    ...
    ```

    System installs will take less disk space and time though.


[Poetry][] has great promise, but is currently a bit of a pain due to some unresolved
issues.  Here are some recommendations:


* Always work in an explicit environment.  This is an issue if you routinely have a
  [conda][] environment activated.  Currently, [poetry][] interprets an active [conda][]
  environment as a virtual environment and uses it.  This means that `poetry add ...`
  will add these dependencies **to that environment**.  Instead, I [recommend the
  following](https://github.com/python-poetry/poetry/issues/1724#issuecomment-834080057):
   
  1. Provide a set of python interpreters at the system level.  By *system* I mean that
     you should install these as a special user (`conda` or `admin`) so that users
     cannot accidentally install packages into these environments.  There are several ways
     of doing this.  Once these interpreters are available in `PATH`, then [Nox][] will
     find them and create a virtual environment with the appropriate interpreter for testing.
     
     I used to used [conda][], which is probably a good strategy on Linux systems etc.,
     but on my Mac M1 Max (ARM), I use [MacPorts][].  This step *(only needs to be done
     once per system)*.  [PyEnv][] might be another option, but I have had problems on
     my Mac OS X (see above).
     
     Here is an example with [conda][]:
      
     ```bash
     for py_ver in 3.7 3.8 3.9 3.10 3.11; do
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
      
      Or, using [MacPorts][]:
      
      ```bash
      port install python37 python38 python39 python310 python311
      ```
      
      Note: these are all native interpreters, meaning that on my Mac M1, they are ARM
      executables.  In some cases, you might need OSX-64 executables to be run under
      [Rosetta][].  Currently I need this to install [PyFFTW][] (see [issue
      #144](https://github.com/pyFFTW/pyFFTW/issues/144)).  This is more complicated,
      and so I provide a `Makefile` that does this if you run
      
      ```bash
      make envs
      ```
      
      This uses [conda][] like above, but also specifies the appropriate architecture
      (via `CONDA_SUBDIR` or the `subdir` config variable) and then links these to
      `build/bin` which can then be added to the path. This is also done in `noxfile.py`
      if executed on an Mac OS X ARM platform.
      
  2. Specifically activate one of these for each project while developing *(only needs
     to be done once per project)*:
   
     ```bash
     cd project
     poetry env use python3.9
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
  [`persist`][] package):
  
  1. Start with your desired python versions, then add projects, and restrict until
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

* To update packages, us the `poetry show` command:

   ```bash
   poetry show --outdated
   ```
   
   Note: it is useful to do this with two separate environments -- one at the lowest
   version supported, and another at the highest.
 
## Soft Dependencies

In general, [Poetry][] advocates [against unbound versions][].  While we generally
agree, we we really don't want installing `mmfutils` to break their environment because
they need a new version of [SciPy][] that we have not had a chance to test yet.

We follow the approach here that `mmfutils` depends explicitly on the minimum
requirements. Ideally, we would run a set of tests in an intelligent manner, slowly
expanding the range of allowed versions until we get the broadest range of dependencies
that work with each version of python.  However, it might be better to just exclude
known bad-versions, and be otherwise unbound. See also this discussion:

* [Support for "soft" or suggestet
  constraints](https://github.com/python-poetry/poetry/issues/7051)

All other dependencies -- especially complex ones that might break an install -- are
optional. Thus, one can still install it without [PyFFTW][] -- which might not be
available on your platform -- and still use other features.  To support this, we do the
following: 

* Delay imports.  Thus, `import mmfutils.contexts` does not import `mmfutils.plot`, so
    one can still use the useful `mmfutils.contexts.FPS` without installing
    `matplotlib`.  In some cases, the import might be delayed until a specific function
    is called, but this should be done sparingly.
* Make the associated dependencies optional.  If the user wants a fully-functional
    installation, they do
  
    ```bash
    pip install mmfutils[all]
    ```
    
    This will pull in a working version of [PyFFTW][], [SciPy][], etc.

## Issues:

* [![Issue](https://img.shields.io/github/issues/detail/state/python-poetry/poetry/1724)](
  https://github.com/python-poetry/poetry/issues/1724)
  "Document use of current conda env"

## References


Testing
=======

We generally use [Nox][] for testing since this provides a way of testing against
multiple versions of python.  For more complicated systems, we provide a set of tools in
`noxutils.py` inspired by the [rinohtype][]
[`noxutil.py`](https://github.com/brechtm/rinohtype/blob/master/noxutil.py) file which
provides a list of versions that might be installed.

[rinohtype]: <https://github.com/brechtm/rinohtype>

## Issues:

* It would be really nice if `noxutils.py` did not require [Poetry][] as an install and
  could get the appropriate information directly by invoking `poetry`, which might be
  installed outside of the development environment.
* Related to the above, it would be really nice if there were a semi-automated way of
  determining the widest dependency requirements with tests.  Something like: run tests
  with extreme versions of various libraries, bisecting to find boundaries.

[Poetry][] has great promise, but is currently a bit of a pain due to some unresolved
issues.  Here are some recommendations:

* Always work in an explicit environment.  This is an issue if you routinely have a
  [conda][] environment activated.  Currently, [poetry][] interprets an active [conda][]
  environment as a virtual environment and uses it.  This means that `poetry add ...`
  will add these dependencies **to that environment**.  Instead, I [recommend the
  following](https://github.com/python-poetry/poetry/issues/1724#issuecomment-834080057):
   
  1. Create some bare [conda][] environments with the various python interpreters you
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
  [`persist`][] package):
  
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
 
GitHub
======

You can [skip GitHub CI][] by including `[skip ci]` in a commit message.  This will also
[skip GitLab CI][].  To skip only GitHub, use `[no ci]`.

[skip GitHub CI] <https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/skipping-workflow-runs>

GitLab
======

## Mirroring Repositories

You can mirror a repository from, e.g. [GitLab][] (or [Heptapod][]) to [GitHub][] using
[GitLab push mirroring][]. This allows you to use [GitHub CI](#github-ci) for example:

1. [Get a personal token from GitHub][]. *([Settings/Developer settings/Personal access
   tokens/Fine-grained tokens](https://github.com/settings/personal-access-tokens))*.
   This must have read-write access for **contents**.  Store the generated token `github_pat_...`
2. Add the mirrored repository.
   * **Git repository URL:** `https://github.com/forbes-group/mmfutils`
   * **Authentication method:** `Username and Password`
   * **Username:** `mforbes`
   * **Password:** `github_pat_*`
   * Optional: `Mirror only protected branches`
   
[Get a personal token from GitHub]: <https://docs.gitlab.com/ee/user/project/repository/mirror/push.html#set-up-a-push-mirror-from-gitlab-to-github>
[GitLab push mirroring]: <https://docs.gitlab.com/ee/user/project/repository/mirror/push.html>


## Protected Branches


[GitLab][] as a mechanism to protect branches.  If you try to do any history editing
(`hg amend` etc.) on these branches, then when you push, you will get a warning:

```
warning: failed to update ...; pre-receive hook declined
```

Generally you should work on unprotected branches (i.e. topics in mercurial), then merge
these in once you are done, but if you need to do this, you can visit
[Settings/Repository/Protected branches][] on your [GitLab][] project, and then toggle
`Allowed to force push`.  This will allow you to `hg push -fr .` for example.

## CI

The [GitLab CI][] is configured in `.gitlab-ci.yml`.

You can [skip GitLab CI][] by including `[skip ci]` in your commit message.

### Documentation


```
image: ubuntu:24.10

build-docs:
  script:
    - apt-get update && apt-get install -y build-essential curl wget git libfftw3-dev pandoc
                                           #ffmpeg texlive-full
    # - EXTRAS=doc make tools
    - bash <(curl -L micro.mamba.pm/install.sh)
    # - source ~/.bashrc  # This does not work in CI for some reason.  Not a login shell?
    - export PATH=/root/.local/bin/:${PATH}
    - EXTRAS=doc make html
    - mv doc/build/html public
  pages: true  # specifies that this is a Pages job
  artifacts:
    paths:
      - public
```

### Docker Images

To run various tests etc. we need to base our CI on a docker image.  This then needs to
be provisioned, which can consume a lot of resources (especially with `texlive-full`).
To minimize the need to do this, we build our own docker image that is provisioned and
use this.  I am following the tutorial [GitLab CI - Create a Docker image and upload it to GitLab and
Docker Hub][] to do this.

1. Create a project where you want to define and store the image.
2. Clone the project and edit the `Dockerfile`.
3. 

[GitLab CI - Create a Docker image and upload it to GitLab and Docker Hub]: <https://www.youtube.com/watch?v=HCuBdbuJdTU&ab_channel=Tobi%27sDeveloperCorner)





[GitLab CI]: <https://docs.gitlab.com/ee/ci/>
[skip GitLab CI] <https://docs.gitlab.com/ee/ci/pipelines/#skip-a-pipeline>
[Settings/Repository/Protected branches]: <
  https://gitlab.com/forbes-group/mmfutils/-/settings/repository#js-protected-branches-settings>

### Running Locally

See <https://stackoverflow.com/a/36358790/1088938>


Issues
======



# Issues:

## pyFFTW

**TL;DR** Until several issues are fixed, use the following source to install pyFFTW:

```
PYFFTW_REPO="git+https://github.com/karlotness/pyFFTW.git@linker-flags"
python3 -m pip install -v --no-cache "${PYFFTW_REPO}"
```

I was having lots of issues with [pyFFTW][] on my ARM Mac.  These include the following:

* Poor performance - comparable or worse than NumPy.  This typically happens when the
  incorrect FFTW library is found: i.e. if you have an incompatible or poorly built
  version in an active Conda environment when you build.  Generally we recommend
  installing `fftw` from `conda-forge`, but if you have bad performance, you might need
  to recompile yourself.  See for example [fftw-feedstock issue #94](
  https://github.com/conda-forge/fftw-feedstock/issues/94) and [fftw issue #129](
  https://github.com/FFTW/fftw3/issues/129) which affected ARM platforms like the Mac OS
  X M1 chip.
  
  <details>
  
  To install the [FFTW][] on my Mac, I downloaded the source, then ran (as `admin`):
  
  ```bash
  MY_FLAGS="--enable-threads --enable-armv8-cntvct-el0 --prefix=/data/apps/fftw/3.3.10"
  make clean
  ./configure --enable-float $MY_FLAGS 
  make -j8
  make install
  make clean
  ./configure $MY_FLAGS
  make -j8
  make install
  make clean
  
  pushd /data/apps/fftw/ && ln -s 3.3.10 current && popd
  sudo mkdir -p /usr/local/lib
  sudo mkdir -p /usr/local/bin
  sudo mkdir -p /usr/local/include
  
  sudo ln -s /data/apps/fftw/current/lib/* /usr/local/lib/
  sudo ln -s /data/apps/fftw/current/include/* /usr/local/include/
  sudo ln -s /data/apps/fftw/current/bin/* /usr/local/bin/
  ```
  
  This installs the float and double precision versions in `/data/apps/fftw/3.3.10`
  which I then symlink to `/usr/local/lib`.  Note that ARM's do not have a separate long
  double, so the `fftwl` library is not built here.
  
  
  ```bash
  # Custom compile of pyfftw
  $ python testfftw.py 
  Nxyz=(2, 64)
  np    : 0.0014s (median 0.0014s)
  pyfftw: 0.0216s (median 0.0216s)

  Nxyz=(1200, 1200)
  np    : 0.2019s (median 0.2028s)
  pyfftw: 0.0821s (median 0.0824s)

  Nxyz=(256, 256, 256)
  np    : 0.0696s (median 0.0727s)
  pyfftw: 0.0326s (median 0.0332s)
  ```
  
  ```bash
  # With conda-forge verions of pyfftw
  $ python testfftw.py 
  Nxyz=(2, 64)
  np    : 0.0015s (median 0.0015s)
  pyfftw: 0.0187s (median 0.0187s)

  Nxyz=(1200, 1200)
  np    : 0.2050s (median 0.2060s)
  pyfftw: 0.0812s (median 0.0817s)

  Nxyz=(256, 256, 256)
  np    : 0.0698s (median 0.0698s)
  pyfftw: 0.0952s (median 0.0984s)
  ```

  ```bash
  # With conda-forge verions of pyfftw but forced recompile of pyfftw from source.
  $ python testfftw.py
  Nxyz=(2, 64)
  np    : 0.0014s (median 0.0014s)
  pyfftw: 0.0202s (median 0.0204s)

  Nxyz=(1200, 1200)
  np    : 0.1841s (median 0.1844s)
  pyfftw: 0.0704s (median 0.0740s)

  Nxyz=(256, 256, 256)
  np    : 0.0701s (median 0.0723s)
  pyfftw: 0.0335s (median 0.0344s)
  ```

  I use the following code to test:
  
  ```python
  # testfftw.py
  import os, time, timeit, numpy as np, pyfftw.builders

  rng = np.random.default_rng(seed=2)

  for Nxyz in [(2, 64), (1200,) * 2, (256,) * 3]:
      print(f"{Nxyz=}")
      psi = rng.normal(size=Nxyz) + rng.normal(size=Nxyz) * 1j

      tic = time.time()
      psi_t = np.fft.fftn(psi)
      t = time.time() - tic
      T, repeat = 3, 5  # Desired time for tests in s and number of repeats
      number = max(1, int(T / t / repeat))

      def test(fftn, label=""):
          ts = timeit.repeat(
              "fftn(psi)", globals=dict(psi=psi, fftn=fftn), repeat=repeat, number=number
          )
          print(f"{label:6}: {min(ts):.4f}s (median {np.median(ts):.4f}s)")

      test(np.fft.fft, "np")

      fftn = pyfftw.builders.fftn(
          psi.copy(), threads=os.cpu_count(), planner_effort="FFTW_MEASURE"
      )

      assert np.allclose(fftn(psi), psi_t)

      test(fftn, "pyfftw")
      print()
  ```
  
  The second number should be significantly smaller.  For example, with a custom built
  [FFTW][] library on my Mac OS M1 Max, building [pyFFTW][] from source (see below), I
  have (complex double transforms):
  
  ```bash
  $ python testfftw.py 
  np: 0.0214s
  pyfftw: 0.0027s
  ```
  
* Several new issues related to Cython 3.0 appeared in 2023: [issue
  #362](https://github.com/pyFFTW/pyFFTW/issues/362) and [issue
  #294](https://github.com/pyFFTW/pyFFTW/issues/294), and several related to paths
  [issue #349](https://github.com/pyFFT/pyFFTW/issues/349) and [issue
  #352](https://github.com/pyFFTW/pyFFTW/issues/352).  Most of these seem to be resolved
  by [PR #363](https://github.com/pyFFTW/pyFFTW/pull/363), so I currently recommend
  using that.
  
* Consider `pyFFTW`: if not using [Conda][], then this needs the FFTW libraries installed
  on the host platform, otherwise the install will fail.  How best to deal with this?
  My current solution is to provide these as extras, but it would be nice if there was a
  way to install if the libraries are present.

* `error: Could not find any of the FFTW libraries`: this was mostly related to [issue
   #303](https://github.com/pyFFTW/pyFFTW/issues/303) which is now fixed on `master`.
   Until this is release, one can install from source:

   ```bash
   pip install git+https://github.com/pyFFTW/pyFFTW.git
   ```

   As for [issue #303](https://github.com/pyFFTW/pyFFTW/issues/303), here is what
   changed: https://github.com/pyFFTW/pyFFTW/compare/v0.13.1..master.  You can probably
   fix this by specifying `-Werror=implicit-function-declaration` somehow in your compiler flags.

   Here is a typical example failure:

   ```bash
   micromamba create -y -c defaults -p envs/py3.11 python=3.11 fftw numpy Cython
   eval "$(micromamba shell hook --shell=bash)" && micromamba activate envs/py3.11
   python3 -m pip install --no-cache "pyfftw==0.13.1"
   ```

  <details>

  ```bash
  $ micromamba create -y -c defaults -p envs/py3.11 python=3.11 fftw numpy

                                             __
            __  ______ ___  ____ _____ ___  / /_  ____ _
           / / / / __ `__ \/ __ `/ __ `__ \/ __ \/ __ `/
          / /_/ / / / / / / /_/ / / / / / / /_/ / /_/ /
         / .___/_/ /_/ /_/\__,_/_/ /_/ /_/_.___/\__,_/
        /_/

  pkgs/main/noarch                                              No change
  pkgs/r/noarch                                                 No change
  pkgs/r/osx-arm64                                              No change
  pkgs/main/osx-arm64                                           No change

  Transaction

    Prefix: .../py3.11

    Updating specs:

     - python=3.11
     - fftw
     - numpy


    Package               Version  Build               Channel         Size
  ───────────────────────────────────────────────────────────────────────────
    Install:
  ───────────────────────────────────────────────────────────────────────────

    + blas                    1.0  openblas            pkgs/main     Cached
    + bzip2                 1.0.8  h620ffc9_4          pkgs/main     Cached
    + ca-certificates  2023.05.30  hca03da5_0          pkgs/main     Cached
    + fftw                  3.3.9  h1a28f6b_1          pkgs/main     Cached
    + libcxx               14.0.6  h848a8c0_0          pkgs/main     Cached
    + libffi                3.4.4  hca03da5_0          pkgs/main     Cached
    + libgfortran           5.0.0  11_3_0_hca03da5_28  pkgs/main     Cached
    + libgfortran5         11.3.0  h009349e_28         pkgs/main     Cached
    + libopenblas          0.3.21  h269037a_0          pkgs/main     Cached
    + llvm-openmp          14.0.6  hc6e5704_0          pkgs/main     Cached
    + ncurses                 6.4  h313beb8_0          pkgs/main     Cached
    + numpy                1.24.3  py311hb57d4eb_0     pkgs/main     Cached
    + numpy-base           1.24.3  py311h1d85a46_0     pkgs/main     Cached
    + openssl               3.0.8  h1a28f6b_0          pkgs/main     Cached
    + pip                  23.1.2  py311hca03da5_0     pkgs/main     Cached
    + python               3.11.3  hb885b13_1          pkgs/main     Cached
    + readline                8.2  h1a28f6b_0          pkgs/main     Cached
    + setuptools           67.8.0  py311hca03da5_0     pkgs/main     Cached
    + sqlite               3.41.2  h80987f9_0          pkgs/main     Cached
    + tk                   8.6.12  hb8d0fd4_0          pkgs/main     Cached
    + tzdata                2023c  h04d1e81_0          pkgs/main     Cached
    + wheel                0.38.4  py311hca03da5_0     pkgs/main     Cached
    + xz                    5.4.2  h80987f9_0          pkgs/main     Cached
    + zlib                 1.2.13  h5a0b063_0          pkgs/main     Cached

    Summary:

    Install: 24 packages

    Total download: 0 B

  ───────────────────────────────────────────────────────────────────────────



  Transaction starting
  Linking fftw-3.3.9-h1a28f6b_1
  Linking ncurses-6.4-h313beb8_0
  Linking xz-5.4.2-h80987f9_0
  Linking zlib-1.2.13-h5a0b063_0
  Linking blas-1.0-openblas
  Linking libcxx-14.0.6-h848a8c0_0
  Linking bzip2-1.0.8-h620ffc9_4
  Linking libffi-3.4.4-hca03da5_0
  Linking ca-certificates-2023.05.30-hca03da5_0
  Linking llvm-openmp-14.0.6-hc6e5704_0
  Linking readline-8.2-h1a28f6b_0
  Linking tk-8.6.12-hb8d0fd4_0
  Linking openssl-3.0.8-h1a28f6b_0
  Linking libgfortran5-11.3.0-h009349e_28
  Linking sqlite-3.41.2-h80987f9_0
  Linking libgfortran-5.0.0-11_3_0_hca03da5_28
  Linking libopenblas-0.3.21-h269037a_0
  Linking tzdata-2023c-h04d1e81_0
  Linking python-3.11.3-hb885b13_1
  Linking wheel-0.38.4-py311hca03da5_0
  Linking setuptools-67.8.0-py311hca03da5_0
  Linking pip-23.1.2-py311hca03da5_0
  Linking numpy-base-1.24.3-py311h1d85a46_0
  Linking numpy-1.24.3-py311hb57d4eb_0

  Transaction finished

  ...
  $ eval "$(micromamba shell hook --shell=bash)" && micromamba activate envs/py3.11
  (py3) $ python3 -m pip install --no-cache pyfftw
  Collecting pyfftw
    Downloading pyFFTW-0.13.1.tar.gz (114 kB)
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 114.4/114.4 kB 1.5 MB/s eta 0:00:00
    Installing build dependencies ... done
    Getting requirements to build wheel ... done
    Preparing metadata (pyproject.toml) ... done
  Requirement already satisfied: numpy<2.0,>=1.20 in ./envs/py3.11/lib/python3.11/site-packages (from pyfftw) (1.24.3)
  Building wheels for collected packages: pyfftw
    Building wheel for pyfftw (pyproject.toml) ... error
    error: subprocess-exited-with-error

    × Building wheel for pyfftw (pyproject.toml) did not run successfully.
    │ exit code: 1
    ╰─> [71 lines of output]
        running bdist_wheel
        running build
        running build_py
        creating build
        creating build/lib.macosx-11.1-arm64-3.11
        creating build/lib.macosx-11.1-arm64-3.11/pyfftw
        copying pyfftw/config.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw
        copying pyfftw/_version.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw
        copying pyfftw/__init__.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw
        creating build/lib.macosx-11.1-arm64-3.11/pyfftw/builders
        copying pyfftw/builders/builders.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/builders
        copying pyfftw/builders/__init__.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/builders
        copying pyfftw/builders/_utils.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/builders
        creating build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        copying pyfftw/interfaces/cache.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        copying pyfftw/interfaces/__init__.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        copying pyfftw/interfaces/scipy_fft.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        copying pyfftw/interfaces/dask_fft.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        copying pyfftw/interfaces/numpy_fft.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        copying pyfftw/interfaces/scipy_fftpack.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        copying pyfftw/interfaces/_utils.py -> build/lib.macosx-11.1-arm64-3.11/pyfftw/interfaces
        UPDATING build/lib.macosx-11.1-arm64-3.11/pyfftw/_version.py
        set build/lib.macosx-11.1-arm64-3.11/pyfftw/_version.py to '0.13.1'
        running build_ext
        DEBUG:__main__:Link FFTW dynamically
        DEBUG:__main__:Compiler include_dirs: ['./envs/py3.11/include/python3.11']
        DEBUG:__main__:3.11.3 (main, May 15 2023, 18:01:31) [Clang 14.0.6 ]
        DEBUG:__main__:Sniffer include_dirs: ['/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include', '/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw', '/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include', './envs/py3.11/include']
        DEBUG:__main__:objects: []
        DEBUG:__main__:libraries: []
        DEBUG:__main__:include dirs: ['/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include', '/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw', '/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include', './envs/py3.11/include']
        DEBUG:__main__:clang -DNDEBUG -fwrapv -O2 -Wall -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw -I/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include -I./envs/py3.11/include -I./envs/py3.11/include/python3.11 -c /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-5ht27cq0/None.c -o /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-5ht27cq0/None.o

        DEBUG:__main__:clang /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-5ht27cq0/None.o -L./envs/py3.11/lib -o /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-5ht27cq0/a.out

        DEBUG:__main__:Checking with includes ['fftw3.h']...ok
        DEBUG:__main__:objects: []
        DEBUG:__main__:libraries: ['fftw3']
        DEBUG:__main__:include dirs: ['/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include', '/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw', '/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include', './envs/py3.11/include']
        /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-hfaar1y4/fftw_plan_dft.c:2:17: error: implicit declaration of function 'fftw_plan_dft' is invalid in C99 [-Werror,-Wimplicit-function-declaration]
                        fftw_plan_dft();
                        ^
        1 error generated.
        WARNING:__main__:Compilation error: command '/usr/bin/clang' failed with exit code 1
        DEBUG:__main__:clang -DNDEBUG -fwrapv -O2 -Wall -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw -I/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include -I./envs/py3.11/include -I./envs/py3.11/include/python3.11 -c /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-hfaar1y4/fftw_plan_dft.c -o /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-hfaar1y4/fftw_plan_dft.o

        DEBUG:__main__:Checking for fftw_plan_dft...no
        DEBUG:__main__:objects: []
        DEBUG:__main__:libraries: ['fftw3f']
        DEBUG:__main__:include dirs: ['/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include', '/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw', '/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include', './envs/py3.11/include']
        /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-f8ktlj7y/fftwf_plan_dft.c:2:17: error: implicit declaration of function 'fftwf_plan_dft' is invalid in C99 [-Werror,-Wimplicit-function-declaration]
                        fftwf_plan_dft();
                        ^
        1 error generated.
        WARNING:__main__:Compilation error: command '/usr/bin/clang' failed with exit code 1
        DEBUG:__main__:clang -DNDEBUG -fwrapv -O2 -Wall -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw -I/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include -I./envs/py3.11/include -I./envs/py3.11/include/python3.11 -c /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-f8ktlj7y/fftwf_plan_dft.c -o /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-f8ktlj7y/fftwf_plan_dft.o

        DEBUG:__main__:Checking for fftwf_plan_dft...no
        DEBUG:__main__:objects: []
        DEBUG:__main__:libraries: ['fftw3l']
        DEBUG:__main__:include dirs: ['/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include', '/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw', '/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include', './envs/py3.11/include']
        /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-nkofnks4/fftwl_plan_dft.c:2:17: error: implicit declaration of function 'fftwl_plan_dft' is invalid in C99 [-Werror,-Wimplicit-function-declaration]
                        fftwl_plan_dft();
                        ^
        1 error generated.
        WARNING:__main__:Compilation error: command '/usr/bin/clang' failed with exit code 1
        DEBUG:__main__:clang -DNDEBUG -fwrapv -O2 -Wall -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -fPIC -O2 -isystem ./envs/py3.11/include -arch arm64 -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/include -I/tmp-dir/pip-install-uosc4e24/pyfftw_cae63f92cf0343b4bb3308a3d5308afe/pyfftw -I/tmp-dir/pip-build-env-jifbhuv5/overlay/lib/python3.11/site-packages/numpy/core/include -I./envs/py3.11/include -I./envs/py3.11/include/python3.11 -c /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-nkofnks4/fftwl_plan_dft.c -o /var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gr/T/pyfftw-nkofnks4/fftwl_plan_dft.o

        DEBUG:__main__:Checking for fftwl_plan_dft...no
        DEBUG:__main__:{'HAVE_DOUBLE': False, 'HAVE_DOUBLE_OMP': False, 'HAVE_DOUBLE_THREADS': False, 'HAVE_DOUBLE_MULTITHREADING': False, 'HAVE_DOUBLE_MPI': False, 'HAVE_SINGLE': False, 'HAVE_SINGLE_OMP': False, 'HAVE_SINGLE_THREADS': False, 'HAVE_SINGLE_MULTITHREADING': False, 'HAVE_SINGLE_MPI': False, 'HAVE_LONG': False, 'HAVE_LONG_OMP': False, 'HAVE_LONG_THREADS': False, 'HAVE_LONG_MULTITHREADING': False, 'HAVE_LONG_MPI': False, 'HAVE_MPI': False}
        error: Could not find any of the FFTW libraries
        [end of output]

    note: This error originates from a subprocess, and is likely not a problem with pip.
    ERROR: Failed building wheel for pyfftw
  Failed to build pyfftw
  ERROR: Could not build wheels for pyfftw, which is required to install pyproject.toml-based projects
  ```
  </details>

## Sleep

Sleeping with `time.sleep()` is [not very
accurate](https://stackoverflow.com/questions/1133857/how-accurate-is-pythons-time-sleep).
This causes various FPS tests to fail.  See that thread (and the code in
`misc/PlotSleepBehavior.py`) for some possible solutions.


* How to manage one definitive version?  The [current suggestion][] is to use
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
  
  The work-around is as follows.  (We could fallback to VCS maybe?  Or look in [`pyproject.toml`][]?).
  
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

# [CoCalc][]

We make fairly heavy use of [CoCalc][] for online computations and collaboration.  Thus,
we try to include a mechanism for easily building and running our software on that
platform.  Here are a couple of principles:

* [CoCalc][] comes with a few fairly complete software environments that can be enabled
  by running `anaconda2020` or `anaconda2021`.  Corresponding Jupyter kernels exist, so
  these are natural choices.  If possible, I recommend that simple projects just use
  these -- especially if they will be shared with many people who might not want to
  install software (i.e. students in a lower-level or non-programming course).
  
  This has the added advantage of allowing users to work on unpaid projects: these have
  no network access, so cannot install software.
  
  Caveat: Including many packages forces some packages like [SciPy][] to fairly low
  versions (see issue [cocalc#6391][]).  This means you might not be able to depend on
  the latest features.  Hopefully this will be resolved with `anaconda2022`.  To see
  which versions are included, look at <https://cocalc.com/software/python>.

* [CoCalc][] projects typically have limited memory (1-2GB), which can pose a problem
  for [conda][].  In particular, **do not** just try run [conda][] from one of the
  `anaconda*` environments without disabling channels:
  
  ```bash
  
  ```
  
  .  They include so many channels that even a
  simple `conda search` is likely to run out of memory.
  
  There are several mitigation strategies:
  
  * Directly call the executable:

    ```bash
    /ext/anaconda2021.11/bin/conda
    ```
  * Install and use [micromamba][]:
  
    ```bash
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | \
             tar -xvj bin/micromamba -O > ~/.local/bin/micromamba
    ```

## Implementation Details

**Detecting CoCalc**: Currently we use the presence of the environmental variable
`ANACONDA2020` to determine if we are on [CoCalc][].  *(In the
[future](https://github.com/sagemathinc/cocalc/issues/5483), `ANACONDA_CURRENT` will
point to the latest release.  It might be better to use this in case `ANACONDA2020` is
deprecated.)

**PATH**: `~/.local/bin` is included in the path, so this is where to put/symlink
executables.  Note, however, that this is only included for login shells.  If you put
things (like [mercurial][]) there that are needed over ssh, then you need to modify
`~/.bashrc` so these are added.  We do this with [mmf_setup][], moving the default
`~/.bashrc` to `~/.bashrc_cocalc`:

```bash
# ~/.bashrc
export PATH="~/.local/bin/:$PATH"
[ -f ~/.bashrc_cocalc ] && . ~/.bashrc_cocalc
```

[CoCalc][] follows the common linux practice of sourcing `~/.bash_aliases`, so we put
the rest of our customizations there.

**VCS**: One issue with [CoCalc][] is that all users share the same account.  Thus,
there is no easy way to tell who is logged in for purposes like committing code to VCS.
To deal with this, we abuse this by  See [cocalc#370][] for details.


[cocalc#370]: <https://github.com/sagemathinc/cocalc/issues/370>
[cocalc#6391]: <https://github.com/sagemathinc/cocalc/issues/6391>
[micromamba]: <https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html>



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
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/10690)](
  https://github.com/conda/conda/issues/10690)
  "Conda run fails with Permission denied if environment is read-only."
* [![Issue](https://img.shields.io/github/issues/detail/state/conda/conda/10105)](
  https://github.com/conda/conda/issues/10105)
  "Local environment.yml file hides remote environment file specification in conda env
  create."
  * Could be an issue with `anaconda-client`:
    [![Issue](https://img.shields.io/github/issues/detail/state/Anaconda-Platform/anaconda-client/549)](
    https://github.com/Anaconda-Platform/anaconda-client/issues/549)

## Black Issues

* [![Issue](https://img.shields.io/github/issues/detail/state/drillan/jupyter-black/26)](
  https://github.com/drillan/jupyter-black/issues/26)
  "Black is needed in the kernel, not the environment running jupyter, but the reverse
  is preferred."

## PDM Issues

* [![Issue](https://img.shields.io/github/issues/detail/state/pdm-project/pdm/1606)](
  https://github.com/pdm-project/pdm/issues/1606)
  "install development groups into separate environments".  This issue addresses a
  similar question related to installing development groups as separate environments.
  This was closed as not going to be supported in the core, but maybe in a plugin.

## Poetry Issues

* [![Issue](https://img.shields.io/github/issues/detail/state/python-poetry/poetry/1724)](
  https://github.com/python-poetry/poetry/issues/1724)
  "Document use of current conda env"
  
## PipX Issues

* [![Issue](https://img.shields.io/github/issues/detail/state/pypa/pipx/934)](
  https://github.com/pypa/pipx/issues/934)
  "Support for `pipx inject <package> -r <requirements-file>`"

## CondaX Issues

* [![Issue](https://img.shields.io/github/issues/detail/state/mariusvniekerk/condax/16)](
  https://github.com/mariusvniekerk/condax/issues/16)
  "Scriptable (commandline) customization of CONDAX_LINK_DESTINATION (link_destination)"
* [![Issue](https://img.shields.io/github/issues/detail/state/mariusvniekerk/condax/63)](
  https://github.com/mariusvniekerk/condax/issues/63)
  "Allow specifying Python version when installing a package (i.e. --python flag)"

## CoCalc Issues

* [![Issue](https://img.shields.io/github/issues/detail/state/sagemathinc/cocalc/370)](
  https://github.com/sagemathinc/cocalc/issues/370)
  "Version Control with SMC"
* [![Issue](https://img.shields.io/github/issues/detail/state/sagemathinc/cocalc/6391)](
  https://github.com/sagemathinc/cocalc/issues/6391)
  "Scipy regression with anaconda progression?"

https://discussions.apple.com/thread/254891544

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

# References

* [Recursive Optional Dependencies in Python][] (Hynek Schlawack):

<!-- Links -->
[Physics 581]: <https://gitlab.com/wsu-courses/physics-581-physics-inspired-computation>
  "Physics 581: Physics Inspired Computation course GitLab project."
[Conda]: <https://docs.conda.io> "Conda"
[Fil]: <https://pythonspeed.com/products/filmemoryprofiler/> "The Fil memory profiler for Python"
[Heptapod]: <https://heptapod.net> "Heptapod website"
[Hypermodern Python]: <https://cjolowicz.github.io/posts/hypermodern-python-01-setup/>
  "Hypermodern Python"
[MyPI]: <https://alum.mit.edu/www/mforbes/mypi/> "MyPI: My personal package index"
[PDM]: <https://pdm.fming.dev/latest/>
[Poetry]: <https://poetry.eustace.io> "Python packaging and dependency management made easy."
[Hatch]: <https://hatch.pypa.io/latest/>
[PyPI]: <https://pypi.org> "PyPI: The Python Package Index"
[`minconda`]: <https://docs.conda.io/en/latest/miniconda.html> "Miniconda"
[PyEnv]: <https://github.com/pyenv/pyenv> "Simple Python Version Management: pyenv"
[venv]: <https://docs.python.org/3/library/venv.html> "Creation of virtual environments"
[`conda-pack`]: <https://conda.github.io/conda-pack/> "Command line tool for creating archives of conda environments"
[Read the Docs]: <https://readthedocs.org>
[CuPy]: https://cupy.dev
[CUDA]: <https://developer.nvidia.com/cuda-toolkit> "CUDA Toolkit"
[Mamba]: https://github.com/mamba-org/mamba
[Micromamba]: <https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html>
[CoCalc]: https://cocalc.com
[Anaconda]: https://www.anaconda.com
[Anaconda Cloud]: https://www.anaconda.cloud
[Anaconda Project]: <https://anaconda-project.readthedocs.io/en/latest/>
[anaconda-client]: <https://github.com/Anaconda-Platform/anaconda-client>
[ARM]: https://www.arm.com
[cookiecutter]: https://github.com/cookiecutter/cookiecutter
[click]: https://click.palletsprojects.com
[pipx]: https://pypa.github.io/pipx/
[condax]: https://github.com/mariusvniekerk/condax
[MacPorts]: https://www.macports.org/
[Rosetta]: https://support.apple.com/en-us/HT211861
[PyFFTW]: https://github.com/pyFFTW/pyFFTW
[FFTW]: https://www.fftw.org/
[SciPy]: https://scipy.org/
[mercurial]: https://www.mercurial-scm.org/
[git]: https://git-scm.com/
[Jupytext]: <https://jupytext.readthedocs.io/en/latest/>
[Nox]: <https://nox.thea.codes/en/stable/> "Nox: Flexible test automation"
[PyTest]: <https://docs.pytest.org/en/latest/> "pytest"
[Coverage]: <https://coverage.readthedocs.io/en/latest>
[Black]: <https://black.readthedocs.io/en/stable/>
[Nbconvert]: <https://nbconvert.readthedocs.io/en/latest/>
[against unbound versions]: https://python-poetry.org/docs/faq/#why-are-unbound-version-constraints-a-bad-idea
[Jupyter Book]: <https://jupyterbook.org/> "Books with Jupyter"
[How to replicate Jupyter Book’s functionality in Sphinx]: 
  <https://jupyterbook.org/en/stable/explain/sphinx.html#how-to-replicate-jupyter-books-functionality-in-sphinx>
[Sphinx]: <https://www.sphinx-doc.org/>
[`sphinx-autobuild`]: <https://github.com/executablebooks/sphinx-autobuild>
[JB Images and figures]: <https://jupyterbook.org/en/stable/content/figures.html>
[MyST NB]: <https://myst-nb.readthedocs.io/en/latest/>
[MyST_NB issue #431]: <https://github.com/executablebooks/MyST-NB/issues/431>
[glue]: <https://myst-nb.readthedocs.io/en/latest/render/glue.html>

[against unbound versions]: 
  <https://python-poetry.org/docs/faq/#why-are-unbound-version-constraints-a-bad-idea>
[How to improve Python packaging]:
  <https://chriswarrick.com/blog/2023/01/15/how-to-improve-python-packaging/>
[mac-os-x]: <https://swan.physics.wsu.edu/forbes/draft/mac-os-x/>
[TeX Live]: <https://www.tug.org/texlive/>
[MacTeX]: <https://www.tug.org/mactex>
[Recursive Optional Dependencies in Python]: 
  <https://hynek.me/articles/python-recursive-optional-dependencies/>
[our cookiecutter templates]: <https://gitlab.com/forbes-group/cookiecutters>
[pyproject.toml]: <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>
[NumPy]: <https://numpy.org/>
[NumPy with MKL]: <https://numpy.org/install/#numpy-packages--accelerated-linear-algebra-libraries>
[Numba]:  <https://numba.pydata.org>
[PyCUDA]: <https://mathema.tician.de/software/pycuda/>
[cupy]: <https://cupy.dev>
[pip]: <https://pip.pypa.io/en/stable/>
[`pytest-cov`]: <https://github.com/pytest-dev/pytest-cov>
