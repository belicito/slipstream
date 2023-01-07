
from slipstream.algos import *


class TestAlgos:

    def test_all_none(self):
        a, b, c = None, None, None
        assert all_none(a, b, c)
        a, b, c = "None", None, None
        assert not all_none(a, b, c)

    def test_any_none(self):
        a, b, c = 1, None, "2"
        assert any_none(a, b, c)
        a, b, c = "None", "None", "None"
        assert not any_none(a, b, c)

    def test_all_not_none(self):
        a, b, c = 1, 2, 3
        assert all_not_none(a, b, c)
        a, b, c = "None", None, 123
        assert not all_not_none(a, b, c)

    def test_any_not_none(self):
        a, b, c = 1, 2, None
        assert any_not_none(a, b, c)
        a, b, c = None, None, None,
        assert not any_not_none(a, b, c)
