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


