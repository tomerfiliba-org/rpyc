#!/usr/bin/env python
import sys
from testbase import TestBase, TestSuite
from classic import Classic
from async import AsyncTest
from custom_service import CustomService
from tls import Tlslite
from threads import Multithreaded
from remoting import Remoting
from twisted_client import TwistedTest
from registry import TcpRegistryTest, UdpRegistryTest
from win32pipes import PipeTest, NamedPipeTest
from attributes import AttributeTest

if sys.version_info >= (2, 5):
    from python25 import Python25Test
else:
    class Python25Test(TestBase):
        def setup(self):
            self.cannot_run("this test requires python2.5 or greater")


class RpycSuite(TestSuite):
    TESTS = [
        Classic,
        AttributeTest,
        AsyncTest,
        CustomService,
        Multithreaded,
        Remoting,
        TwistedTest,
        TcpRegistryTest,
        UdpRegistryTest,
        Tlslite,
        # python2.5
        Python25Test,
        # win32
        PipeTest,
        NamedPipeTest,
    ]


if __name__ == '__main__':
    RpycSuite.run()


