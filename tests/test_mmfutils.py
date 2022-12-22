from mmfutils import unique_list


class TestUniqueList(object):
    """Test `unique_list`."""

    def test_1(self):
        r"""Test unique_list(hashable, preserve_order=True)"""
        l1 = [2, 1, 1, 3, 4, 2]
        l2 = unique_list(l1, preserve_order=True)
        assert l2 == [2, 1, 3, 4]

    def test_2(self):
        r"""Test unique_list(not_hashable, preserve_order=True)"""
        l1 = [[2], [1], [1], [3], [4], [2]]
        l2 = unique_list(l1, preserve_order=True)
        assert l2 == [[2], [1], [3], [4]]

    def test_3(self):
        r"""Test unique_list(hashable, preserve_order=False)"""
        l1 = [2, 1, 1, 3, 4, 2]
        l2 = unique_list(l1, preserve_order=False)
        for x in l1:
            assert x in l2
        while l2:
            x = l2.pop()
            assert x not in l2

    def test_4(self):
        r"""Test unique_list(not_hashable, preserve_order=False)"""
        l1 = [[2], [1], [1], [3], [4], [2]]
        l2 = unique_list(l1, preserve_order=False)
        for x in l1:
            assert x in l2
        while l2:
            x = l2.pop()
            assert x not in l2
