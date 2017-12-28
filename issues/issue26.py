import rpyc

class AService(rpyc.Service):
    class exposed_A(object):
        @classmethod
        def exposed_foo(cls, a, b):
            return 17 * a + b

if __name__ == "__main__":
    with rpyc.connect_thread(remote_service = AService) as conn:
        print( conn.root.A.foo(1, 2))

