"""Tools for Parallel Computing

This module contains some useful tools for parallel computing with IPython.
"""
import atexit
import logging
import multiprocessing
import os
import subprocess
import time
import weakref

try:
    import ipyparallel
except ImportError:
    from IPython import parallel as ipyparallel

__all__ = ["get_cluster"]


class Cluster(object):
    """Represents a running IPython cluster.

    If a cluster with the specified profile is already running, then connect to
    that, otherwise launch a new cluster using the ``subprocess`` module. If we
    launch a cluster, then we also register a hook with ``atexit`` to shut down
    the cluster when we are done.

    This can also be used in a context to ensure the cluster is cleaned up when
    the context finishes.
    """

    # Global list of clusters and clusters we start - this keeps them alive
    _clusters = weakref.WeakValueDictionary()
    _started_clusters = []

    def __init__(self, profile="default", n=None, ipython_dir=None, sleep_time=0.1):
        """
        Arguments
        ---------
        profile : str
           Profile to connect with.
        n : int
           Minimum number of engines to run.  Used when launching a new
           cluster. If not provided, then will be deduced from either the
           `PBS_NODEFILE` environment variable or the number of CPU cores.
        ipython_dir : str
           Specify where the ipython directory is.  Usually ``~/.ipython`` but
           can be changed.  (Used mostly for testing)
        sleep_time : float
           Time to sleep while waiting for cluster to respond.
        """
        self.profile = profile
        self.ipython_dir = ipython_dir
        self.n = n
        self.client = None
        self.sleep_time = sleep_time
        self._direct_view = None
        self._load_balanced_view = None

        self.key = self.get_key(profile=profile, n=n, ipython_dir=ipython_dir)
        Cluster._clusters[self.key] = self

    def __len__(self):
        """Return the number of engines in the current client."""
        return len(self.client)

    @classmethod
    def get_key(cls, profile, n, ipython_dir):
        return (profile, n, ipython_dir)

    @property
    def direct_view(self):
        if self._direct_view is None and self.client is not None:
            self._direct_view = self.client.direct_view()
        return self._direct_view

    @property
    def load_balanced_view(self):
        if self._load_balanced_view is None and self.client is not None:
            self._load_balanced_view = self.client.load_balanced_view()
        return self._load_balanced_view

    @property
    def running(self):
        """True if the cluster is running.

        Our definition of running is that clients can connect successfully
        which usually requires that the PID files have been written. This might
        fail if the cluster is just starting up.
        """
        try:
            client = ipyparallel.Client(
                profile=self.profile, ipython_dir=self.ipython_dir
            )
            client.close()
            return True
        except IOError:
            return False

    def start(self, keep_alive=False, context=False):
        """Start the cluster if it is not running.

        Arguments
        ---------
        keep_alive : bool
           If `True`, then the cluster will not be shut down when the object
           dies or the python process exits.  (Only clusters that are actually
           started here will be shut down automatically.)
        context : bool
           If `True`, then the assume the cluster is started in a context
           manager and will be killed at the end of the context via the
           `__exit__()` method.
        """
        if self.running:
            return
        elif self.n is None:
            if "PBS_NODEFILE" in os.environ:
                with open(os.environ["PBS_NODEFILE"]) as _f:
                    pbs_nodes = [_n.strip() for _n in _f]
                    self.n = max(1, len(pbs_nodes))
            else:
                # Leave one process free for running the cluster management
                # tools etc.
                self.n = max(1, multiprocessing.cpu_count() - 1)

        cmd = "ipcluster start --daemonize --quiet --profile={} --n={}".format(
            self.profile, self.n
        )

        if self.ipython_dir is not None:
            cmd = " ".join([cmd, '--ipython-dir="{}"'.format(self.ipython_dir)])

        logging.info("Starting cluster: {}".format(cmd))
        subprocess.check_call(cmd.split())

        # Who will stop the cluster?
        if keep_alive:  # pragma: nocover
            # No one here!  User is responsible for stopping the cluster.
            return

        # Register it
        Cluster._started_clusters.append(self)

    def stop(self):
        """Stop the current cluster.

        Only affects clusters that are started here with the `start()` method
        and are not
        """
        if self in Cluster._started_clusters:
            if self.client is not None:
                self.client.close()
            self.client = None

            cmd = "ipcluster stop --profile={}".format(self.profile)
            if self.ipython_dir is not None:
                cmd = " ".join([cmd, '--ipython-dir="{}"'.format(self.ipython_dir)])

            logging.info("Stopping cluster: {}".format(cmd))
            subprocess.check_call(cmd.split())
            while self.running:  # pragma: nocover
                # Wait until cluster stops
                time.sleep(self.sleep_time)
            Cluster._started_clusters.remove(self)
        self._load_balanced_view = None
        self._direct_view = None

    def wait(self, n_min=None, timeout=5 * 60):
        """Wait for n_min engines of the cluster to start."""
        tic = time.time()
        if n_min is None:
            n_min = self.n
        elif self.n is not None:
            assert n_min <= self.n

        while True:
            if timeout < time.time() - tic:
                raise ipyparallel.TimeoutError(
                    "{} engines did not start in timeout={}s".format(n_min, timeout)
                )
            try:
                self.client = ipyparallel.Client(
                    profile=self.profile, ipython_dir=self.ipython_dir
                )
                break
            except IOError:
                logging.warning("No ipcontroller-client.json, waiting...")
            except ipyparallel.TimeoutError:  # pragma: nocover
                logging.warning("No controller, waiting...")
            time.sleep(self.sleep_time)

        if not n_min:
            return self.client

        logging.info("waiting for {} engines".format(n_min))
        running = len(self.client)
        logging.info("{} of {} running".format(running, n_min))
        while len(self.client) < n_min:
            if timeout < time.time() - tic:  # pragma: nocover
                raise ipyparallel.TimeoutError(
                    "{} engines did not start in timeout={}s".format(n_min, timeout)
                )
            time.sleep(self.sleep_time)
            if running < len(self.client):
                running = len(self.client)
                logging.info("{} of {} running".format(running, n_min))
        return self.client

    def __enter__(self):
        self.start(context=True)
        self.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return exc_type is None

    def __del__(self):
        self.stop()

    @classmethod
    def stop_all(cls):
        """Stop all registered clusters"""
        for c in reversed(cls._started_clusters):
            c.stop()

    @classmethod
    def get_cluster(
        cls,
        profile="default",
        n=None,
        ipython_dir=None,
        launch=True,
        block=True,
        n_min=1,
    ):
        """Return a Custer instance for the specified cluster.

        This will return a cluster connected to at least `N` engines,
        launching the appropriate cluster if needed.

        Arguments
        ---------
        n : int
           Number of engines to launch.
        launch : bool
           If `True`, then launch the cluster if it is not already running.
        block : bool
           If `True`, then wait for cluster to start before returning.
        n_min : int
          The minimum number of engines to wait for.
        """
        kw = dict(profile=profile, n=n, ipython_dir=ipython_dir)
        key = cls.get_key(**kw)
        if key in cls._clusters:
            cluster = cls._clusters[key]
        else:
            cluster = Cluster(**kw)

        if launch and not cluster.running:
            cluster.start()
        if block:
            cluster.wait(n_min=n_min)
        return cluster


atexit.register(Cluster.stop_all)

get_cluster = Cluster.get_cluster
