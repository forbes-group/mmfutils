"""Integration tests for %runmd — uses a real IPython shell and jupytext."""

import contextlib
import os
import textwrap
import pytest

from IPython.testing.globalipapp import get_ipython


@pytest.fixture(scope="session")
def ip():
    """Return a real InteractiveShell instance, with the extension loaded."""
    shell = get_ipython()

    # Load our extension
    from mmfutils.runmd import load_ipython_extension

    load_ipython_extension(shell)
    return shell


TST1_MD = textwrap.dedent("""\
```{code-cell} ipython3
x = 2
%time y = x**2
z = 3*y
```
""")


class TestRunMD:
    def test_runmd(self, ip, tmp_path):
        tst1_md = tmp_path / "tst1.md"
        tst1_md.write_text(TST1_MD)

        tst1__py = tmp_path / "tst1_.py"
        tst1__ipy = tmp_path / "tst1_.ipy"

        with contextlib.chdir(tmp_path):
            ip.run_line_magic("runmd", str(tst1_md))

        assert not tst1__py.exists(), f"Expected {tst1__py} to be move to {tst1__ipy}"
        assert tst1__ipy.exists(), f"Expected {tst1__ipy} to be created by jupytext"
        assert ip.user_ns.get("x") == 2
        assert ip.user_ns.get("y") == 4
        assert ip.user_ns.get("z") == 12
