# 2 March 2026
* Trying to get CI working with a minimal LaTeX install:
  * https://github.com/matplotlib/matplotlib/issues/16911


# 28 Feb 2026
Continue converting to pixi.  We will try writing tests and CI to use pixi environments.
* Not sure what to do with nox.  It does not yet support pixi (see [nox#992][]).  We can
  dispatch with `PY_DEV_VER=3.9 make test` etc.
* Removing `Docs/README_files/`.  I don't know why we need this folder.



[nox#992]: <https://github.com/wntrblm/nox/issues/992>

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
