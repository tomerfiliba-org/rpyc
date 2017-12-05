import unittest
from rpyc.security.exposer import *
from rpyc.security import locks
from rpyc.security import olps
from rpyc.security import exceptions

class TestExposerCornerCases(unittest.TestCase):
    def test_double_expose(self):
        valid = False
        try:
            @expose
            @expose
            class foo:
                pass
        except ValueError as e:
            valid = True
        self.assertTrue(valid)

    def test_expose_above_property(self):
        valid = False
        try:
            class foo:
                @expose
                @property
                def x(self):
                    return 1
        except ValueError as e:
            valid = True
        self.assertTrue(valid)

    def test_get_exposed_key_error(self):
        valid = False
        try:
           default_exposer._get_exposed("test")
        except KeyError as e:
            self.assertEqual(e.args[0], "test")
            valid = True
        self.assertTrue(valid)

    def test_set_exposed_key_error(self):
        valid = False
        olp = olps.OLP()
        try:
            default_exposer._set_exposed(None, olp)#Someday weakrefs to None
                                                  #will be supported and
                                                  #this test will fail
        except TypeError as e:
            valid = True
        self.assertTrue(valid)

    def test_expose_multiple_locks(self):
        valid = False
        try:
            @expose(locks.BLOCKED, lock=locks.BLOCKED)
            class a:
                pass
        except TypeError as e:
            valid = True
        self.assertTrue(valid)

    def test_expose_too_many_args(self):
        valid = False
        try:
            @expose(locks.BLOCKED, 5)
            class a:
                pass
        except TypeError as e:
            valid = True
        self.assertTrue(valid)

    def test_expose_non_callable(self):
        def stupid_decorate(junk):
            return 1
        valid = False
        try:
            @expose
            @stupid_decorate
            def foo():
                pass
        except TypeError as e:
            valid = True
        self.assertTrue(valid)

    #code coverage case to cover one branch.
    def test_is_direct_static_method_not_there(self):
        class a:
            pass
        self.assertFalse(default_exposer.is_staticmethod(a, "rhutabaga"))

    #code coverage case to cover one branch.
    def test_is_direct_member_same_item_fallback(self):
        class a:
            x=3

        class b(a):
            x=a.x

        found = False
        for key, item in default_exposer._get_direct_members(b):
            if "x" == key:
                found = True

        self.assertTrue(found)

    #code coverage case to cover one branch.
    def test_python_bug_1785(self):
        class A(object):
            def __get__(*args):
                raise AttributeError()

        class B(object):
            x = A()

        found = False
        for key, item in default_exposer._get_direct_members(B):
            if "x" == key:
                found = True

        self.assertTrue(found)


    #code coverage case to cover one branch.
    def test_bad_dir_get_direct_members(self):
        class A(object):
            def __dir__(self):
                return list(A.__dict__.keys())+["rhutabaga"]
                #return list(super(A, self).__dir__())+["rhutabaga"]

        for key, item in default_exposer._get_direct_members(A()):
            self.assertFalse(key == "rhutabaga")

    def test_is_expose_class(self):
        class A(object):
            pass
        @expose
        class B(object):
            pass

        valid = False
        try:
            default_exposer._is_exposed_class(A)
        except ValueError:
            valid = True
        self.assertTrue(valid)
        #don't throw exception
        default_exposer._is_exposed_class(B)

    #code coverage case to cover 2 branches
    def test_get_failures(self):
        class A(object):
            pass

        valid = False
        try:
            default_exposer._get_direct(A, "rhutabaga")
        except AttributeError:
            valid = True
        self.assertTrue(valid)

        valid = False
        try:
            default_exposer._get_dict_version_only(A, "rhutabaga")
        except AttributeError:
            valid = True
        self.assertTrue(valid)

    #code coverage case to cover a branch
    def test_is_xxxmethod(self):
        class A(object):
            pass

        self.assertFalse(default_exposer.is_classmethod(A, "rhutabaga"))
        self.assertFalse(default_exposer.is_staticmethod(A, "rhutabaga"))


    #code coverage case to cover one branch.
    def test_expose_class_inheritance(self):
        @expose
        class A(object):
            @expose
            def foo(self):
                return 1

            def baz(self):
                return 3

        @expose(inherit=A)
        class B(A):
            @expose
            def bar(self):
                return 2

            def no(self):
                return 4

        instance=B()

        value = instance._rpyc_getattr("foo")._rpyc_getattr("__call__")()
        self.assertEqual(value, 1)

        value = instance._rpyc_getattr("bar")._rpyc_getattr("__call__")()
        self.assertEqual(value, 2)

        valid = False
        try:
            value = instance._rpyc_getattr("baz")
        except exceptions.SecurityAttrError:
            valid = True
        self.assertTrue(valid)

        valid = False
        try:
            value = instance._rpyc_getattr("no")
        except exceptions.SecurityAttrError:
            valid = True
        self.assertTrue(valid)


    #code coverage case to cover two branches
    def test_bad_inheritance(self):
        class A(object):
            @expose
            def foo(self):
                return 1

        valid = False
        try:
            @expose(inherit=A)
            class B(A):
                pass
        except ValueError as e:
            #A is not an exposed class
            valid = True
        self.assertTrue(valid)

        valid = False
        try:
            @expose(inherit="hello")
            class B(A):
                pass
        except ValueError as e:
            #"hello" is a string, not an OLP or class
            valid = True
        self.assertTrue(valid)

    #code coverage case to cover two branches
    def test_constructor_validation(self):
        valid = False
        try:
            Exposer(restrictor = None)
        except ValueError:
            valid = True
        self.assertTrue(valid)

        valid = False
        try:
            Exposer(default_profiles = None)
        except ValueError:
            valid = True
        self.assertTrue(valid)


    #code coverage case to cover two branches
    def test_class_expose_errors(self):
        x=3
        valid = False
        try:
            class_expose(x) #not a class
        except ValueError:
            valid = True
        self.assertTrue(valid)

        @expose
        class A:
            pass

        valid = False
        try:
            class_expose(A) #already exposed.
        except ValueError:
            valid = True
        self.assertTrue(valid)

    #code coverage cases
    def test_field_expose_errors(self):
        @expose
        class A:
            def foo(self):
                pass

        valid = False
        try:
            field_expose(A, "foo", exposure=None)
        except ValueError as e:
            valid = True
        self.assertTrue(valid)

        valid = False
        try:
            field_expose(A, "foo", exposure=-1)
        except ValueError as e:
            valid = True
        self.assertTrue(valid)

        valid = False
        try:
            field_expose(A, "1_alpha")  #illegal identifier
        except ValueError as e:
            valid = True
        self.assertTrue(valid)


        valid = False
        try:
            field_expose(A, "&")  #Default expose of wildcard.
        except ValueError as e:
            valid = True
        self.assertTrue(valid)

        valid = False
        try:
            #inherit of non-defined routine.
            field_expose(A, "rhutabaga", inherit=olps.OLP())
        except ValueError as e:
            valid = True
        self.assertTrue(valid)


        valid = False
        try:
            field_expose(A, "rhutabaga")  #Default expose of member that doesn't exist yet.
        except ValueError as e:
            valid = True
        self.assertTrue(valid)

    def test_field_expose_and_unexpose_simple(self):
        @expose
        class A:
            x = 3
        field_expose(A, "x")
        #make sure accessible from BOTH
        self.assertEqual(A._rpyc_getattr("x"), 3)
        self.assertEqual(A()._rpyc_getattr("x"), 3)
        field_unexpose(A, "x")
        valid = False
        try:
            A._rpyc_getattr("x")
        except exceptions.SecurityAttrError:
            valid = True
        self.assertTrue(valid)

    def test_field_expose_not_there(self):
        @expose
        class A:
            pass
        field_expose(A, "rhutabaga", exposure=EXPOSE_CLASS_SET | EXPOSE_CLASS_GET | EXPOSE_CLASS_DEL)

        A._rpyc_setattr("rhutabaga", 3)
        self.assertEqual(A.rhutabaga, 3)
        self.assertEqual(A._rpyc_getattr("rhutabaga"), 3)
        A._rpyc_delattr("rhutabaga")
        self.assertFalse(hasattr(A, "rhutabaga"))

        valid = False
        try:
            A._rpyc_setattr("not_rhutabaga", 3)
        except exceptions.SecurityAttrError as e:
            valid = True
        self.assertTrue(valid)

    #code coverage cases
    def test_routine_expose_errors(self):
        class A:
            pass
        valid = False
        try:
            routine_expose(A) #not a routine
        except ValueError:
            valid = True
        self.assertTrue(valid)

        @expose
        def foo():
            pass

        valid = False
        try:
            routine_expose(foo) #already exposed.
        except ValueError:
            valid = True
        self.assertTrue(valid)

    def test_routine_descriptor_expose_errors(self):
        valid = False
        try:
            routine_descriptor_expose(None)
        except ValueError:
            valid = True

    def test_routine_descriptor_separate_wrap(self):
        @expose
        class A:
            @expose
            @classmethod
            def foo(cls):
                pass

        @expose
        def foo2(self):
            pass
        self.assertIs(A.__dict__['foo'].__func__, A.foo.__func__)
        self.assertTrue(is_exposed(A.__dict__['foo']))
        A.foo=classmethod(foo2)
        self.assertIs(A.__dict__['foo'].__func__, foo2)
        self.assertFalse(is_exposed(A.__dict__['foo']))
        A.foo=routine_descriptor_expose(classmethod(foo2))
        self.assertIs(A.__dict__['foo'].__func__, foo2)
        self.assertTrue(is_exposed(A.__dict__['foo']))

    #code coverage case to cover one branch.
    def test_non_exposed_property(self):
        @expose
        class A(object):
            @property
            def x(self):
                return 1

        valid = False
        try:
            value = A._rpyc_getattr("x")
        except exceptions.SecurityAttrError:
            valid = True
        self.assertTrue(valid)

        instance=A()
        valid = False
        try:
            value = instance._rpyc_getattr("x")
        except exceptions.SecurityAttrError:
            valid = True
        self.assertTrue(valid)
        self.assertEqual(instance.x, 1)

    #Normal methods never get wrapped in the tests
    #---well they do, but from the __dict__ version,
    #This does it from the getattr (bound) version.
    def test_normal_method_descriptor_wrapping(self):
        class A:
            def foo(self):
                pass
        a=A()
        new_foo = default_exposer._routine_descriptor_remake(a.foo, a.foo.__func__)
        self.assertIsNot(new_foo, a.foo)
        self.assertEqual(new_foo, a.foo)

if __name__ == "__main__":
    unittest.main()



