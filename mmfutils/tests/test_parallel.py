import multiprocessing
import os
import shutil
import subprocess
import tempfile
import time

import nose.tools as nt

from mmfutils.parallel import Cluster, get_client, parallel


class TestCluster(object):
    slow = 1

    @classmethod
    def setup_class(cls):
        """We start all the clusters here in parallel so we don't have to wait
        too long."""
        cls.ipython_dir = tempfile.mkdtemp()
        cmd = 'ipython profile create testing --parallel --ipython-dir="{}"'
        cmd = cmd.format(cls.ipython_dir)
        subprocess.check_call(cmd.split())

        cls.cluster1 = Cluster(profile='testing1',
                               ipython_dir=cls.ipython_dir)
        cls.cluster1.start()

        with tempfile.NamedTemporaryFile(delete=False) as nodefile:
            nodefile.write("\n".join(['localhost']*3))
            nodefile.close()

        cls.PBS_NODEFILE = nodefile.name

        os.environ['PBS_NODEFILE'] = nodefile.name
        # We start this way for coverage
        get_client(profile='testing2', ipython_dir=cls.ipython_dir).close()

        # Wait for cluster to start
        cls.cluster1.wait().close()

    @classmethod
    def teardown_class(cls):
        cls.cluster1.stop_all()
        shutil.rmtree(cls.ipython_dir)
        os.remove(cls.PBS_NODEFILE)

    def test_connect(self):
        """Simple test connecting to a cluster."""
        client = get_client(profile='testing1', ipython_dir=self.ipython_dir)
        nt.eq_(max(1, multiprocessing.cpu_count() - 1), len(client))
        client.close()

    def test_pbs(self):
        """Test that the PBS_NODEFILE is used if defined"""
        with Cluster(profile='testing2',
                     ipython_dir=self.ipython_dir) as client:
                nt.eq_(3, len(client))
                client.close()

    def test_doublestart(self):
        """Test that starting a running cluster does nothing."""
        tic = time.time()
        self.cluster1.start()
        nt.ok_(time.time() - tic < 0.01)

    @nt.raises(parallel.TimeoutError)
    def test_timeout1(self):
        """Test timeout (coverage)"""
        self.cluster1.wait(timeout=0)
