import rpyc
from rpyc.utils.server import ThreadedServer
import unittest

CONNECT_CONFIG = {"allow_setattr": True}


class Fee(object):

    def __init__(self, msg="Fee"):
        self._msg = msg

    @property
    def exposed_msg(self):
        return self._msg

    @exposed_msg.setter
    def exposed_msg(self, value):
        self._msg = value

    def __str__(self):
        return str(self._msg)

    def __add__(self, rhs):
        return self.__str__() + str(rhs)


class Service(rpyc.Service):

    PORT = 18878

    def exposed_fee(self, arg):
        return arg

    def exposed_fee_str(self, arg):
        return str(arg)

    def exposed_foe_update(self, arg, msg):
        arg.msg = arg.msg + " foe" + msg
        return arg


class Intermediate(rpyc.Service):

    PORT = 18879

    def exposed_fee(self, arg):
        with rpyc.connect("localhost", port=Service.PORT, config=CONNECT_CONFIG) as conn:
            return conn.root.fee(arg)

    def exposed_fee_str(self, arg):
        with rpyc.connect("localhost", port=Service.PORT) as conn:
            return conn.root.fee_str(arg)

    def exposed_fie_update(self, arg):
        arg.msg = arg.msg + " fie"
        with rpyc.connect("localhost", port=Service.PORT, config=CONNECT_CONFIG) as conn:
            return conn.root.foe_update(arg, " foo bar")


class Test_rpyc_over_rpyc(unittest.TestCase):
    """Issue #346 shows that exceptions are being raised when an RPyC service method
    calls another RPyC service, forwarding a non-trivial (and thus given as a proxy) argument.
    """

    def setUp(self):
        self.server = ThreadedServer(Service, port=Service.PORT, auto_register=False)
        self.i_server = ThreadedServer(Intermediate, port=Intermediate.PORT,
                                       auto_register=False, protocol_config=CONNECT_CONFIG)
        self.server._start_in_thread()
        self.i_server._start_in_thread()
        self.conn = rpyc.connect("localhost", port=Intermediate.PORT, config=CONNECT_CONFIG)

    def tearDown(self):
        self.conn.close()
        while self.server.clients or self.i_server.clients:
            pass
        self.server.close()
        self.i_server.close()

    def test_immutable_object_return(self):
        """Tests using rpyc over rpyc---issue #346 reported traceback for this use case"""
        obj = Fee()
        result = self.conn.root.fee_str(obj)
        self.assertEqual(str(obj), "Fee", "String representation of obj should not have changed")
        self.assertEqual(str(result), "Fee", "String representation of result should be the same as obj")

    def test_return_of_unmodified_parameter(self):
        obj = Fee()
        original_obj_id = id(obj)
        result = self.conn.root.fee(obj)
        self.assertEqual(str(obj), "Fee", "String representation of obj should not have changed")
        self.assertEqual(id(result), original_obj_id, "Unboxing of result should be bound to the same object as obj")

    def test_return_of_modified_parameter(self):
        obj = Fee()
        original_obj_id = id(obj)
        result = self.conn.root.fie_update(obj)
        self.assertEqual(str(obj), "Fee fie foe foo bar", "String representation of obj should have changed")
        self.assertEqual(id(result), original_obj_id, "Unboxing of result should be bound to the same object as obj")


if __name__ == "__main__":
    unittest.main()
