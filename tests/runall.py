#!/usr/bin/env python

from testbase import TestSuite
from classic import Classic
from async import AsyncTest
from custom_service import CustomService
from tls import Tlslite
from threads import Multithreaded
from remoting import Remoting
from twisted_client import TwistedTest
from win32pipes import PipeTest, NamedPipeStream


class RpycSuite(TestSuite):
    TESTS = [
        Classic,
        AsyncTest,
        CustomService,
        Tlslite,
        Multithreaded,
        Remoting,
        TwistedTest,
        # win32
        PipeTest,
        NamedPipeStream,
    ]


if __name__ == '__main__':
    RpycSuite.run()


