#Test exception filtering

import rpyc
import unittest

class CustomException1(Exception):
    pass

class CustomException2(Exception):
    pass

class MyService(rpyc.Service):
    def exposed_value_error(self):
        raise ValueError("Testing Value Error")

    def exposed_type_error(self):
        raise TypeError("Testing Type Error")

    def exposed_custom_exception1(self):
        raise CustomException1("Testing Custom Exception 1")

    def exposed_custom_exception2(self):
        raise CustomException2("Testing Custom Exception 2")

class TestCustomService(unittest.TestCase):
    def filter_exceptions(self, **kwargs):

        self.assertTrue( "modname" in kwargs )
        self.assertTrue( "clsname" in kwargs )
        self.assertTrue( "attrs" in kwargs )
        self.assertTrue( "tbtext" in kwargs )
        self.assertTrue( "builtin" in kwargs )

        if kwargs["builtin"]:
            if kwargs["clsname"]=="TypeError":
                return False
            else:
                return True
        modname = kwargs["modname"]

        if modname in ["__main__", "test_exception_filter"]:
            if kwargs["clsname"]=="CustomException1":
                return True
        return False

    def setUp(self):
        config={"import_custom_exceptions":True,
                "instantiate_custom_exceptions":True,
                "exception_filter_function":self.filter_exceptions}
        self.conn = rpyc.connect_thread(remote_service=MyService, config=config)
        self.conn.root # this will block until the service is initialized,

    def tearDown(self):
        self.conn.close()

    def test_exceptions(self):
        valid=False
        try:
            self.conn.root.value_error()
        except ValueError:
            valid=True
        self.assertTrue(valid)

        valid=False
        try:
            self.conn.root.type_error()
        except rpyc.core.vinegar.GenericException as e:
            valid=True
        self.assertTrue(valid)

        valid=False
        try:
            self.conn.root.custom_exception1()
        except CustomException1:
            valid=True
        self.assertTrue(valid)

        valid=False
        try:
            self.conn.root.custom_exception2()
        except rpyc.core.vinegar.GenericException as e:
            valid=True
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()


