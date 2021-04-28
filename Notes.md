Developer Notes
===============

## Testing

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


