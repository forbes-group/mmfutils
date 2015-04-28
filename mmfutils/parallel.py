"""Tools for Parallel Computing

This module contains some useful tools for parallel computing with IPython.
"""
import atexit
import logging
import multiprocessing
import os
import subprocess
import time

from IPython import parallel


# Global list of clusters we start - this keeps them alive
CLUSTERS = []


class Cluster(object):
    """Represents a running IPython cluster.

    If a cluster with the specified profile is already running, then connect to
    that, otherwise launch a new cluster using the ``subprocess`` module. If we
    launch a cluster, then we also register a hook with ``atexit`` to shut down
    the cluster when we are done.

    This can also be used in a context to ensure the cluster is cleaned up when
    the context finishes.
    """
    def __init__(self, profile='default', n=None,
                 ipython_dir=None, sleep_time=0.1):
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

    @property
    def running(self):
        """True if the cluster is running.

        Our definition of running is that clients can connect successfully
        which usually requires that the PID files have been written. This might
        fail if the cluster is just starting up.
        """
        try:
            client = parallel.Client(
                profile=self.profile, ipython_dir=self.ipython_dir)
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
            if 'PBS_NODEFILE' in os.environ:
                with open(os.environ['PBS_NODEFILE']) as _f:
                    pbs_nodes = [_n.strip() for _n in _f]
                    self.n = max(1, len(pbs_nodes))
            else:
                # Leave one process free for running the cluster management
                # tools etc.
                self.n = max(1, multiprocessing.cpu_count() - 1)

        cmd = 'ipcluster start --daemonize --quiet --profile={} --n={}'.format(
            self.profile, self.n)

        if self.ipython_dir is not None:
            cmd = " ".join([
                cmd, '--ipython-dir="{}"'.format(self.ipython_dir)])

        logging.info("Starting cluster: {}".format(cmd))
        subprocess.check_call(cmd.split())

        # Who will stop the cluster?
        if keep_alive:               # pragma: nocover
            # No one here!  User is responsible for stopping the cluster.
            return

        # Register it
        global CLUSTERS
        CLUSTERS.append(self)

    def stop(self):
        """Stop the current cluster.

        Only affects clusters that are started here with the `start()` method
        and are not
        """
        global CLUSTERS
        if self in CLUSTERS:
            if self.client is not None:
                self.client.close()
            self.client = None

            cmd = "ipcluster stop --profile={}".format(self.profile)
            if self.ipython_dir is not None:
                cmd = " ".join([
                    cmd, '--ipython-dir="{}"'.format(self.ipython_dir)])

            logging.info("Stopping cluster: {}".format(cmd))
            subprocess.check_call(cmd.split())
            while self.running:               # pragma: nocover
                # Wait until cluster stops
                time.sleep(self.sleep_time)
            CLUSTERS.remove(self)

    def wait(self, timeout=5*60):
        """Wait for cluster to start and return the client."""
        tic = time.time()
        while True:
            if timeout < time.time() - tic:
                raise parallel.TimeoutError(
                    "{} engines did not start in timeout={}s".format(
                        self.n, timeout))
            try:
                self.client = parallel.Client(
                    profile=self.profile, ipython_dir=self.ipython_dir)
                break
            except IOError:
                logging.warning("No ipcontroller-client.json, waiting...")
            except parallel.TimeoutError:     # pragma: nocover
                logging.warning("No controller, waiting...")
            time.sleep(self.sleep_time)

        if not self.n:
            return self.client

        logging.info("waiting for {} engines".format(self.n))
        running = len(self.client)
        logging.info("{} of {} running".format(running, self.n))
        while len(self.client) < self.n:
            if timeout < time.time() - tic:   # pragma: nocover
                raise parallel.TimeoutError(
                    "{} engines did not start in timeout={}s".format(
                        self.n, timeout))
            time.sleep(self.sleep_time)
            if running < len(self.client):
                running = len(self.client)
                logging.info("{} of {} running".format(running, self.n))
        return self.client

    def __enter__(self):
        self.start(context=True)
        return self.wait()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return exc_type is None

    def __del__(self):
        self.stop()

    @staticmethod
    def stop_all():
        """Stop all registered clusters"""
        global CLUSTERS
        for c in reversed(CLUSTERS):
            c.stop()

atexit.register(Cluster.stop_all)


def get_client(profile='default', ipython_dir=None,
               launch=True, n=None):
    """Return an IPython.parallel.Client instance for the specified cluster.

    This will return a client connected to at least `N` engines, launching the
    appropriate cluster if needed.

    Arguments
    ---------
    launch : bool
       If `True`, then launch the cluster if it is not already running.
    n : int
       Number of engines to launch or minimum number of engines to wait for.
    """
    cluster = Cluster(profile=profile, n=n, ipython_dir=ipython_dir)
    if launch and not cluster.running:
        cluster.start()
    client = cluster.wait()
    return client
