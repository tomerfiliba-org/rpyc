import unittest
from rpyc.security import locks
from rpyc.security.exposer import expose, field_expose, EXPOSE_INSTANCE_GET
from rpyc.security import exceptions

class TestLocks(unittest.TestCase):
    def test_default_permitted(self):
        valid = False
        try:
            locks.Lock().permitted()
        except NotImplementedError:
            valid = True
        self.assertTrue(valid)

    def test_default_str(self):
        class rhutabaga(locks.Lock):
            pass

        self.assertEqual(str(rhutabaga()),
                         "rhutabaga")

    def test_sanitize_lock_list_item(self):
        class rhutabaga(object):
            pass

        valid = False
        try:
            locks.sanitize_lock_list_item(None, rhutabaga())
        except TypeError as e:
            valid = True
            self.assertTrue( "rhutabaga" in str(e) )
        self.assertTrue(valid)

        try:
            locks.sanitize_lock_list_item(None)
        except TypeError as e:
            valid = True
            self.assertTrue( "A LockList" in str(e) )
        self.assertTrue(valid)


    def test_abstract_lock_list_shared(self):
        valid = False
        try:
            locks.LockListShared().append(0)
        except NotImplementedError:
            valid = True
        self.assertTrue(valid)

    def test_blocked_permitted(self):
        self.assertFalse(locks.BLOCKED.permitted())

    def test_collection_lock(self):
        class Alpha(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled
        class Bravo(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled

        a=Alpha()
        b=Bravo()
        my_lock = locks.CollectionLock([a,b])

        @expose( lock=my_lock )
        def my_func():
            return True

        value = my_lock.permitted()

        for x in range(4):
            a.enabled = (x & 1)!= 0
            b.enabled = (x & 2)!= 0

            if a.enabled and b.enabled:
                test=my_func._rpyc_getattr("__call__")

                self.assertTrue(test())
            else:
                valid = False
                try:
                    test=my_func._rpyc_getattr("__call__")
                except exceptions.SecurityAttrError:
                    valid = True

                self.assertTrue(valid)

        assert("Alpha" in str(my_lock))
        assert("Bravo" in str(my_lock))
        assert("CollectionLock" in str(my_lock))

    def test_collection_lock(self):
        class Alpha(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled
        class Bravo(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled

        a=Alpha()
        b=Bravo()
        my_lock = locks.CollectionLock([a,b])

        @expose( lock=my_lock )
        def my_func():
            return True

        for x in range(4):
            a.enabled = (x & 1)!= 0
            b.enabled = (x & 2)!= 0

            if a.enabled and b.enabled:
                test=my_func._rpyc_getattr("__call__")

                self.assertTrue(test())
            else:
                valid = False
                try:
                    test=my_func._rpyc_getattr("__call__")
                except exceptions.SecurityAttrError:
                    valid = True

                self.assertTrue(valid)

        assert("Alpha" in str(my_lock))
        assert("Bravo" in str(my_lock))
        assert("CollectionLock" in str(my_lock))

    def test_prefix_lock(self):
        #Check passing in bad type for prefix
        valid=False
        try:
            locks.PrefixLock(prefix=None)
        except TypeError:
            valid=True
        self.assertTrue(valid)

        class Alpha(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled
        class Bravo(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled

        a=Alpha()
        b=Bravo()
        my_lock = locks.PrefixLock(lock=[a,b])

        @expose
        class Foo:
            def method_test(self):
                return True

            def exposed_method_test(self):
                return True

        field_expose(Foo, "|", lock=my_lock, exposure=EXPOSE_INSTANCE_GET)
        foo=Foo()

        for x in range(4):
            a.enabled = (x & 1)!= 0
            b.enabled = (x & 2)!= 0

            valid = False
            try:
                test=foo._rpyc_getattr("method_test")
            except exceptions.SecurityAttrError:
                valid = True
            self.assertTrue(valid)

            if a.enabled and b.enabled:
                test=foo._rpyc_getattr("exposed_method_test")
                self.assertTrue(test())
            else:
                valid = False
                try:
                    test=foo._rpyc_getattr("exposed_method_test")
                    self.assertTrue(test())
                except exceptions.SecurityAttrError:
                    valid = True
                self.assertTrue(valid)

        assert("exposed_" in str(my_lock))
        assert("Alpha" in str(my_lock))
        assert("Bravo" in str(my_lock))
        assert("PrefixLock" in str(my_lock))

    def test_safeattr_lock(self):
        class Alpha(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled
        class Bravo(locks.Lock):
            def __init__(self):
                self.enabled=False
            def permitted(self, **kwargs):
                return self.enabled

        a=Alpha()
        b=Bravo()
        my_lock = locks.SafeAttrLock(lock=[a,b])

        @expose
        class Foo:
            def __eq__(self, other):
                return True

            def blah(self):
                pass


            @expose( my_lock )
            def exposed_method_test(self):
                return True

        field_expose(Foo, "|", lock=my_lock, exposure=EXPOSE_INSTANCE_GET)
        foo=Foo()

        for x in range(4):
            a.enabled = (x & 1)!= 0
            b.enabled = (x & 2)!= 0

            valid = False
            try:
                test=foo._rpyc_getattr("blah")
            except exceptions.SecurityAttrError:
                valid = True
            self.assertTrue(valid)

            if a.enabled and b.enabled:
                test=foo._rpyc_getattr("__eq__")
                self.assertTrue(test(None))
            else:
                valid = False
                try:
                    test=foo._rpyc_getattr("__eq__")
                except exceptions.SecurityAttrError:
                    valid = True
                self.assertTrue(valid)

        assert("Alpha" in str(my_lock))
        assert("Bravo" in str(my_lock))
        assert("SafeAttrLock" in str(my_lock))

if __name__ == "__main__":
    unittest.main()



