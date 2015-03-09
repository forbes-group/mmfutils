"""Various patches for issues I have encountered."""
import logging

try:
    import flake8.main

    if flake8.__version__ > '2.4.0':  # pragma: nocover
        pass
    else:

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

        if flake8.main.Flake8Command.run is not run:
            logging.info("Patching flake8 for issues 39 and 40")
            flake8.main.Flake8Command.run = run

except ImportError:             # pragma: nocover
    pass

try:
    import nose.commands

    if nose.__version__ > 'inf':  # pragma: nocover
        pass
    else:

        # Monkeypatch nose until the following issues is resolved
        # https://github.com/nose-devs/nose/issues/813
        def run(self, _run=nose.commands.nosetests.run):
            try:
                _run(self)
            except SystemExit, e:
                # nose raises an exception even on success.  See
                # https://github.com/nose-devs/nose/issues/813
                if e.code:
                    raise

        if nose.commands.nosetests.run is not run:
            logging.info("Patching nosetests for issues 813")
            nose.commands.nosetests.run = run

except ImportError:             # pragma: nocover
    pass
