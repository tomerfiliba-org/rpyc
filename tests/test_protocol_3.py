import sys
from nose import SkipTest
if sys.version_info < (3, 0):
    raise SkipTest("Those are only for Python3")

import protocol_3 as protocol

'''
4 paths in each

immutable
mut_tup
local (connection getting an obj it knows back)
remote must get through filters above

_box
_unbox

'''
