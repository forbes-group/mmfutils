"""Various patches for issues I have encountered."""
import logging
import os

try:
    import flake8.main

    if flake8.__version__ <= '2.4.0' or 'CI' in os.environ:
        # Monkeypatch flake8 until the following issues are resolved
        # https://gitlab.com/pycqa/flake8/issues/39
        # https://gitlab.com/pycqa/flake8/issues/40

        def run(self, _run=flake8.main.Flake8Command.run):
            # Kill options dict to deal with
            # https://gitlab.com/pycqa/flake8/issues/40
            # The config file will be re-parsed.
            self.options_dict = {}
            try:
                _run(self)
            except SystemExit, e:
                # flake8 raises an exception even on success.  See
                # https://gitlab.com/pycqa/flake8/issues/39
                if e.code:
                    raise

        logging.info("Patching flake8 for issues 39 and 40")
        flake8.main.Flake8Command.run = run
    else:                        # pragma: nocover
        pass
except ImportError:             # pragma: nocover
    pass
