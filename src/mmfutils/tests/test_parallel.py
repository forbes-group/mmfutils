import multiprocessing
import os
import shutil
import subprocess
import tempfile
import time

import pytest

from mmfutils.parallel import Cluster, get_cluster, ipyparallel

from . import parallel_module


class TestCluster(object):
    @classmethod
    def setup_class(cls):
        """We start all the clusters here in parallel so we don't have to wait
        too long."""
        cls.ipython_dir = tempfile.mkdtemp()
        cmd = 'ipython profile create testing --parallel --ipython-dir="{}"'
        cmd = cmd.format(cls.ipython_dir)
        subprocess.check_call(cmd.split())

        cls.cluster1 = get_cluster(profile="testing1", ipython_dir=cls.ipython_dir)
        cls.cluster1.start()

        with tempfile.NamedTemporaryFile(delete=False) as nodefile:
            nodefile.write(b"\n".join([b"localhost"] * 3))
            nodefile.close()

        # Now start a cluster with nodes in PBS_NODEFILE
        cls.PBS_NODEFILE = nodefile.name
        os.environ["PBS_NODEFILE"] = nodefile.name
        # We start this way for coverage
        cls.cluster_pbs = get_cluster(
            profile="testing_pbs", ipython_dir=cls.ipython_dir
        )

        # Wait for cluster to start
        cls.cluster1.wait(n_min=0)

        # This will not be started here.
        cls.cluster3 = Cluster(profile="testing3", ipython_dir=cls.ipython_dir)

    @classmethod
    def teardown_class(cls):
        cls.cluster1.stop_all()
        shutil.rmtree(cls.ipython_dir)
        os.remove(cls.PBS_NODEFILE)

    def test_connect(self):
        """Simple test connecting to a cluster."""
        cluster = get_cluster(profile="testing1", ipython_dir=self.ipython_dir)
        assert cluster is self.cluster1
        assert max(1, multiprocessing.cpu_count() - 1) == len(cluster)

    def test_pbs(self):
        """Test that the PBS_NODEFILE is used if defined"""
        with get_cluster(
            profile="testing_pbs", ipython_dir=self.ipython_dir
        ) as cluster:
            assert cluster is self.cluster_pbs
            assert 3 == len(cluster)

    def test_doublestart(self):
        """Test that starting a running cluster does nothing."""
        tic = time.time()
        self.cluster1.start()
        assert time.time() - tic < 0.1

    def test_timeout1(self):
        """Test timeout (coverage)"""
        with pytest.raises(ipyparallel.TimeoutError):
            self.cluster1.wait(timeout=0)

    def test_views(self):
        view1 = self.cluster1.direct_view
        view1["x"] = 5.0
        view2 = self.cluster1.direct_view
        assert view1 is view2
        assert sum(view2["x"]) == 5 * len(self.cluster1)

        p = range(20)
        res = self.cluster1.load_balanced_view.map(parallel_module.exp2, p, block=True)
        assert res == [2 ** _p for _p in p]

    def test_del(self):
        """Test deleting of cluster objects"""
        cls = self.__class__
        key = cls.cluster3.key
        assert key in Cluster._clusters
        del cls.cluster3
        assert key not in Cluster._clusters


pytest.mark.slow(TestCluster)
