import rpyc
from rpyc import ThreadedServer, restricted
import unittest
from threading import Thread
import time

#This is exceedingly magical, it does some tricks to test corner
#cases, and therefore is very brittle.

def aTestFunction(x, y):
    return x+y

class MyService(rpyc.Service):
    def on_connect(self):
        self.classToggle(False)
        self.enable(True)

    @classmethod
    def enable(cls, value):
        cls._enabled=value

    @classmethod
    def enabled(cls):
        return cls._enabled

    @classmethod
    def _rpyc_class_getattr(cls, name):
        if name in {"enable", "classToggle"}:
            try:
                return getattr(cls, name)
            except AttributeError as e:
                raise RuntimeError("Got unexpected attribute error") # from e
        if cls.enabled():
            if name=="__call__": #Switches from class method to regular method
                return cls.__call__
            elif name=="testClassMethod":
                return cls.testClassMethod
        raise AttributeError("name %s not found" % name)

    def _rpyc_getattr(self, name):
        if name in {"getCall", "getFunction", "getStaticMethod", "getClassMethod", "getMethod"}:
            try:
                return getattr(self, name)
            except AttributeError as e:
                raise RuntimeError("Got unexpected attribute error") #from e

        if self.enabled():
            if name=="__call__":
                return self.__call__ #Switched from class method to regular method
            elif name=="testMethod":
                return self.testMethod
        raise AttributeError("name %s not found" % name)


    @classmethod
    def classToggle(cls, value):
        def special_call(self, x, y):
            return x+y
        special_call.__name__="__call__" #Ugly hack to make this other ugly hack work

        if value == True:
            cls.__call__=classmethod(special_call)
        else:
            cls.__call__=special_call

    @staticmethod
    def testStaticMethod(x,y):
        return x+y

    @classmethod
    def testClassMethod(cls, x,y):
        return x+y

    def testMethod(self, x,y):
        return x+y

    def getCall(self):
        return self.__call__

    def getStaticMethod(self):
        if self.enabled():
            return restricted(self.testStaticMethod, ["__call__"])
        else:
            return self.testStaticMethod

    def getClassMethod(self):
        self.classToggle(self.enabled())
        return self.testClassMethod

    def getMethod(self):
        return self.testMethod

    def getFunction(self):
        if self.enabled():
            return restricted(aTestFunction, ["__call__"])
        else:
            return aTestFunction

class TestProtectedCalls(unittest.TestCase):
    def setUp(self):
        config={ "allow_safe_attrs":False,
                 "allow_exposed_attrs":False,
                 "allow_unprotected_calls":False }

        self.server = ThreadedServer(MyService, port = 0, protocol_config=config)
        self.thd = Thread(target = self.server.start)
        self.thd.start()
        time.sleep(1)
        self.conn = rpyc.connect("localhost", self.server.port)

    def tearDown(self):
        self.conn.close()
        self.server.close()
        self.thd.join()

    def test_protected_calls(self):
        root=self.conn.root

        types=["getFunction", "getStaticMethod", "getClassMethod", "getMethod", "getCall"]

        for type in types:
            root.classToggle(False) #reset to known state.
            root.enable(True)

            #avoid getattr -- as it does an invocation under the hood that the
            #protocol vectors -- That's okay, but not for this test.
            callable=getattr(root, type)()

            if type != "call": #We call constructor!!!!
                self.assertEqual(callable(3,5), 8)
            self.assertEqual(callable.__call__(5,6), 11)
            root.enable(False)
            callable=getattr(root, type)()
            with self.assertRaises(AttributeError):
                if type != "call": #We call constructor!!!!
                    callable(3,5)
            with self.assertRaises(AttributeError):
                callable.__call__(5,6)

