from rpyc.core import brine
from rpyc.lib.compat import is_py_3k
import unittest


class BrineTest(unittest.TestCase):
    def test_brine_2(self):
        if is_py_3k:
            exec('''x = (b"he", 7, "llo", 8, (), 900, None, True, Ellipsis, 18.2, 18.2j + 13,
                 slice(1, 2, 3), frozenset([5, 6, 7]), NotImplemented, (1,2))''', globals())
        else:
            exec('''x = ("he", 7, u"llo", 8, (), 900, None, True, Ellipsis, 18.2, 18.2j + 13,
                 slice(1, 2, 3), frozenset([5, 6, 7]), NotImplemented, (1,2))''')
        self.assertTrue(brine.dumpable(x))  # noqa
        y = brine.dump(x)  # noqa
        z = brine.load(y)
        self.assertEqual(x, z)  # noqa


if __name__ == "__main__":
    unittest.main()
