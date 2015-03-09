"""Various patches for issues I have encountered."""
try:
    import flake8.main
    import logging

    if flake8.__version__ > '2.4.0':  # pragma: nocover
        pass
    else:

        # Monkeypatch flake8 until the following issues are resolve
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
                if e.code:      # pragma: nocover
                    raise

        if flake8.main.Flake8Command.run is not run:
            logging.info("Patching flake8 for issues 39 and 40")
            flake8.main.Flake8Command.run = run

except ImportError:             # pragma: nocover
    pass
