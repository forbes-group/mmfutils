# 28 Feb 2026
Continue converting to pixi.  We will try writing tests and CI to use pixi environments.

# 25 Feb 2026
Converting to pixi and general cleanup.
* Moved docs from .py to .md.
* How should we deal with testing?  Should we use pixi or nox?

  Pixi: can I specify the version of python with an environment?  I.e. we would run
  tests as `pixi run -e py39 pytest`?  Yes: this is covered [in the
  docs](https://pixi.prefix.dev/dev/workspace/multi_environment).  Question: is there a
  DRY way to do this?
  
  It also seems that the dependency specifiers break when everything is included in
  `pyproject.toml`, but if I move the pixi stuff to `pixi.toml`, then things work.
  
  **Update**: This was a bug in pixi - updating to 0.65.0 fixes.  Still, I think I like
  the idea of keeping my Pixi configuration in `pixi.toml`.  However, it seems that if
  we do this, we need to repeat information in `pixi.toml` like `requires-python` and
  features.  Thus, we will stick with `pyproject.toml`.
  
  See also:
  * https://github.com/prefix-dev/pixi/discussions/5576
  * https://pixi.prefix.dev/latest/python/pyproject_toml/#dependency-section

  




Draft issue.

Multi environment with different python versions? Conditions not respected.

I am trying to setup a package using multi environments to support multiple versions of python.  Thus, I have a `pyproject.toml` file with something like this:

```toml
[project]
authors = []
dependencies = [
    "scipy >= 1.13.1; python_version < '3.10'",
    "scipy >= 1.14.1; python_version >= '3.10'",
]
name = "scipy_issue"
requires-python = ">=3.9,<3.15"
version = "0.1.0"
```

This uses [dependencies specifiers](https://packaging.python.org/en/latest/specifications/dependency-specifiers/) so that people can install my package with python 3.9 and up.

Now I want to use `pixi` to create different environments for testing etc.  Following the examples in [Multi Environments](https://pixi.prefix.dev/latest/workspace/multi_environment/#design-considerations) it seems I should add

```toml

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["osx-arm64", "linux-64", "osx-64"]

[tool.pixi.dependencies]
python = ">=3.9.23,<3.15"

[tool.pixi.pypi-dependencies]
scipy_issue = { path = ".", editable = true }

[tool.pixi.feature.py39.dependencies]
python = "~=3.9.0"

[tool.pixi.feature.py310.dependencies]
python = "~=3.10.0"

[tool.pixi.feature.py311.dependencies]
python = "~=3.11.0"

[tool.pixi.environments]
py39 = [ "py39" ]
py310 = [ "py310" ]
py311 = [ "py311" ]
```

However, when I try to produce the lock file, start a shell, etc. I get conflicts:

```bash
$ pixi lock
  ⠤ default:osx-64       [00:00:04] resolving scipy==1.17.1
  ⠤ default:osx-arm64    [00:00:04] resolving scipy==1.17.1
  ⠴ default:linux-64     [00:00:03] resolving scipy==1.17.1                                                                                Error:   x failed to solve the pypi requirements of environment 'py39' for platform 'osx-64'
  |-> failed to resolve pypi dependencies
  `-> Because the requested Python version (==3.9.*) does not satisfy Python>=3.10 and scipy>=1.14.1,<=1.15.3 depends on Python>=3.10, we
      can conclude that scipy>=1.14.1,<=1.15.3 cannot be used.
      And because only the following versions of scipy are available:
          scipy<=1.14.1
          scipy==1.15.0
          scipy==1.15.1
          scipy==1.15.2
          scipy==1.15.3
          scipy==1.16.0
          scipy==1.16.1
          scipy==1.16.2
          scipy==1.16.3
          scipy==1.17.0
          scipy==1.17.1
      we can conclude that scipy>=1.14.1,<1.16.0 cannot be used. (1)
      
      Because the requested Python version (==3.9.*) does not satisfy Python>=3.11 and scipy>=1.16.0 depends on Python>=3.11, we can
      conclude that scipy>=1.16.0 cannot be used.
      And because we know from (1) that scipy>=1.14.1,<1.16.0 cannot be used, we can conclude that scipy>=1.14.1 cannot be used.
      And because you require scipy>=1.14.1, we can conclude that your requirements are unsatisfiable.
      
      hint: Pre-releases are available for `scipy` in the requested range (e.g., 1.17.0rc2), but pre-releases weren't enabled (try:
      `--prerelease=allow`)
      
      hint: The `requires-python` value (==3.9.*) includes Python versions that are not supported by your dependencies (e.g.,
      scipy>=1.14.1,<=1.15.3 only supports >=3.10). Consider using a more restrictive `requires-python` value (like >=3.10).
```

Even pinning the version of scipy in the `py39` environment does not help:

```toml
[tool.pixi.feature.py39.pypi-dependencies]
scipy = ">=1.13.1"
```

How am I supposed to do this?
