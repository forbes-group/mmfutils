"""Provide a %runmd magic that first converts the .md file to python using Jupytext.

Note: Converts `filename.md` -> `_filename.py` using jupytext from the command line.
"""

import shlex

from IPython.core.magic import register_line_magic

JUPYTEXT_COMMAND = "jupytext --opt comment_magics=false"


def load_ipython_extension(ip):
    """Define %runmd to convert `*.md` files to `_*.py` files using jupytext."""

    @register_line_magic("runmd")
    def run_wrapper(line):
        tokens = shlex.split(line)

        # Index of filename
        inds = [i for (i, token) in enumerate(tokens) if token.endswith(".md")]
        if len(inds) == 1:
            # First convert to file
            idx = inds[0]
            md_file = tokens[idx]
            py_file = md_file[:-3] + "_.py"
            ipy_file = md_file[:-3] + "_.ipy"

            cmd = " ".join(
                [
                    f"!{JUPYTEXT_COMMAND}",
                    f"--to py {shlex.quote(md_file)}",
                    f"--output {shlex.quote(py_file)}",
                ]
            )
            print(f"Running {cmd}")
            ip.run_cell(cmd)

            cmd = f"!mv {shlex.quote(py_file)} {shlex.quote(ipy_file)}"
            print(f"Running {cmd}")
            ip.run_cell(cmd)

            tokens[idx] = ipy_file
            new_line = " ".join(shlex.quote(t) for t in tokens)
        else:
            new_line = line

        return ip.run_line_magic("run", new_line)


def unload_ipython_extension(ip):
    """Restart to fully unload; IPython doesn't un-register overwritten magics."""
    pass
