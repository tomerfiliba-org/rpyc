from rpyc.core.brine import dumpable
from rpyc.core.brine import dump
from rpyc.core.brine import load

def test_brine():
    x = ("he", 7, u"llo", 8, (), 900, None, True, Ellipsis, 18.2, 18.2j + 13,
         slice(1, 2, 3), frozenset([5, 6, 7]), NotImplemented, (1,2))
    assert dumpable(x)
    y = dump(x)
    z = load(y)
    assert x == z

