from rpyc.security.restrictor import *
from rpyc.security.utility import *
from rpyc.security.exceptions import *
from rpyc.security.restrictor import exposed_mark as emark
from rpyc.security import olps
from rpyc.security import locks
from rpyc.lib.compat import is_py3k

import unittest
import sys
import datetime
import array
import collections
import types
import inspect

def function(x,y):
    return x+y

def closure(x,y):
    yield x+y

#old style Python object (for python 2)
class A:
    def method(self, x, y):
        return x+y

    @staticmethod
    def statmethod(x, y):
        return x+y

    @classmethod
    def clsmethod(cls, x, y):
        return x+y

    def methclosure(self, x, y):
        yield x+y

    @staticmethod
    def statclosure(x, y):
        yield x+y

    @classmethod
    def clsclosure(cls, x, y):
        yield x+y

#New style Python object (for python2)
class B(object):
    def method(self, x, y):
        return x+y

    @staticmethod
    def statmethod(x, y):
        return x+y

    @classmethod
    def clsmethod(cls, x, y):
        return x+y

    def methclosure(self, x, y):
        yield x+y

    @staticmethod
    def statclosure(x, y):
        yield x+y

    @classmethod
    def clsclosure(cls, x, y):
        yield x+y


class TestRestrictorIdentity(unittest.TestCase):
    @classmethod
    def add_version_dependent( cls, input_array ):
        if sys.hexversion < 0x03000000:
            input_array+=[ "xrange(0,4)" ]
            input_array+=[ 'buffer("a")' ]
        if sys.hexversion > 0x03030000:
            input_array+=[ "types.MappingProxyType({'a':3})" ]
        else:
            input_array+=[ "types.DictType()" ]

    #Test to make sure RPyC exposed objects
    #are passing the tests for identity--they are marked
    #right and are behaving like the objects that
    #they wrap, and don't break minor functionality.
    def test_identity(self):
        #'type' doesn't work for esoteric reasons
        test_values=["function", "hex", "A", "A()", #function, builtin, class, custom instance
                     "B", "B()",
                     "A.method", "A().method", #method, bound method (old)
                     "B.method", "B().method", #method, bound method (new)
                     "A.statmethod", "A().statmethod", #static method (old)
                     "B.statmethod", "B().statmethod", #static method (new)
                     "A.clsmethod",  "A().clsmethod",  #class method (old)
                     "B.clsmethod",  "B().clsmethod",  #class method (new)
                     "closure", "A.methclosure", "A().methclosure",
                     "B.methclosure", "B().methclosure",
                     "A.statclosure", "A().statclosure",
                     "B.statclosure", "B().statclosure",
                     "A.clsclosure", "A().clsclosure",
                     "B.clsclosure", "B().clsclosure",
                      "sys", "unittest", #builtin module, module
                      "tuple()", "list([1,2])", "dict()", "set()",
                      "reversed([])",#Need a generator
                      "reversed((1,2))",#Actually a different type
                      "sys.stdin", "range(2,3)", #filetype, rangetype
                      "slice(1,100,1)", "lambda x,y:x+y",
                      "function.__code__", '"hello"',
                      'u"hello"', "5.0", "5", "54239059892890525", "5.0+1j",
                      "True", "NotImplemented", "None",
                      "datetime.timedelta.days",
                      "array.array.typecode", "property()", "Ellipsis",
                      'collections.namedtuple("foo",["a","b"])' ]

        self.add_version_dependent(test_values)

        standard_callables=["function", "A.statmethod", "A().statmethod", "A().method", "A.clsmethod",
                            "A().clsmethod", "B.statmethod", "B().statmethod", "B().method",
                            "B.clsmethod", "B().clsmethod",
                            "lambda x,y:x+y", "closure",
                            "A().methclosure", "A.statclosure", "A().statclosure",
                            "A.clsclosure", "A().clsclosure",
                            "B().methclosure", "B.statclosure", "B().statclosure",
                            "B.clsclosure", "B().clsclosure"]

        loose_callables={"A.method":A(), "A.methclosure":A(),
                         "B.method":B(), "B.methclosure":B()}

        closures=[ "closure", "A.methclosure", "A().methclosure",
                   "A.statclosure", "A().statclosure",
                   "A.clsclosure", "A().clsclosure",
                   "B.methclosure", "B().methclosure",
                   "B.statclosure", "B().statclosure",
                   "B.clsclosure", "B().clsclosure" ]

        not_called=["hex", "A", "A()", "B", "B()",
                    "sys", "unittest",
                    "tuple()", "list([1,2])", "dict()", "set()", 'buffer("a")',
                    "reversed([])",#Need a generator
                    "reversed((1,2))", #Actually a different type
                    "sys.stdin", "range(2,3)", #filetype, rangetype
                    "slice(1,100,1)",
                    "function.__code__", '"hello"',
                    'u"hello"', "5.0", "5", "54239059892890525", "5.0+1j",
                    "True", "type", "NotImplemented", "None",
                    "datetime.timedelta.days",
                    "array.array.typecode", "property()", "Ellipsis",
                    'collections.namedtuple("foo",["a","b"])' ]

        self.add_version_dependent(not_called)
        olp = olps.OLP()
        olp.total_expose()

        for string_value in test_values:
            print("===STRING VALUE %s==" % string_value)
            checks=[standard_callables, loose_callables, not_called]
            total=0
            found=None
            for check in checks:
                if string_value in check:
                    total+=1
                    found=check
            assert(total==1)

            value=eval(string_value)
            doppelganger=security_restrict(value, olp)

            if hasattr(value, "__class__"):
                values = [(value, doppelganger), (value.__class__, doppelganger.__class__)]
            else:
                #old style python class.
                self.assertFalse(hasattr(doppelganger, "__class__"))
                values = [(value, doppelganger), (type(value), type(doppelganger))]

            for test in values:

                if test[0] is type:
                    self.assertFalse(is_exposed(test[1]))
                    self.assertEqual(repr(test[0]), repr(test[1]))
                elif (not is_py3k) and (test[0] is types.ClassType): #python2 classobj
                    self.assertFalse(is_exposed(test[1]))
                    self.assertEqual(repr(test[0]), repr(test[1]))
                else:
                    self.assertTrue(test[1] is not type)
                    self.assertTrue(is_exposed(test[1]))
                    self.assertEqual(emark(repr(test[0])), repr(test[1]))

                if type(test[0]) is type:
                    self.assertFalse(is_exposed( type(test[1])))
                    self.assertFalse(is_exposed( test[1].__class__))

                    if (not is_py3k) and (test[0] is types.ClassType):
                        #just continue---there will be a lot of issues
                        #with this type.
                        continue
                    self.assertEqual(repr(type(test[0])), repr(type(test[1])))
                    self.assertEqual(repr(test[0].__class__), repr(test[1].__class__))

                elif (not is_py3k) and (type(test[0]) is types.ClassType): #python2 classobj
                    self.assertFalse(is_exposed( type(test[1])))
                    self.assertEqual(repr(type(test[0])), repr(type(test[1])))
                else:
                    self.assertTrue(is_exposed( type(test[1])))
                    self.assertTrue(is_exposed( test[1].__class__))
                    self.assertEqual(emark(repr(type(test[0]))), repr(type(test[1])))
                    self.assertEqual(emark(type(test[0]).__repr__(test[0])), type(test[1]).__repr__(test[1]))
                    self.assertEqual(emark(repr(test[0].__class__)), repr(test[1].__class__))

                if (is_py3k) or not (test[0] is types.ClassType):
                    self.assertEqual(type(test[0]), rpyc_type(test[1]))
                self.assertEqual(inspect.isclass(test[0]), inspect.isclass(test[1]))

                #This doesn't work--need rpyc_type
                #self.assertEqual(type(test[0]), type(test[1]))

                if hasattr(test[0], "__class__"):
                    self.assertEqual(test[0].__class__, test[1].__class__)

                self.assertEqual(getattr(test[0], "__module__", None),
                                 getattr(test[1], "__module__", None))
                self.assertEqual(getattr(test[0], "__name__", None),
                                 getattr(test[1], "__name__", None))
                self.assertEqual(getattr(test[0], "__qualname__", None),
                                 getattr(test[1], "__qualname__", None))

                #isinstance and issubclass
                #Some classes don't allow subclassing, these don't work one way
                #with isinstance and issubclass.
                one_way = False
                try:
                    class Test(type(value)):
                        pass
                except TypeError:
                    one_way = True

                if hasattr(value, "__class__"):
                    if not one_way:
                       self.assertTrue(issubclass(doppelganger.__class__, value.__class__))
                    self.assertTrue(issubclass(value.__class__, doppelganger.__class__))

                    if not one_way:
                        self.assertTrue(isinstance(doppelganger, value.__class__))
                    self.assertTrue(isinstance(value, doppelganger.__class__))

                    self.assertTrue(inspect.isclass(doppelganger.__class__))

                self.assertTrue(inspect.isclass( type(doppelganger) ))

            if string_value not in not_called:
                if string_value in standard_callables:
                    result = value(2,3)
                    result2 = doppelganger(2,3)
                elif string_value in loose_callables:
                    result = value(loose_callables[string_value], 2,3)
                    result2 = doppelganger(loose_callables[string_value], 2, 3)

                if string_value in closures:
                    result=next(result)
                    result2=next(result2)
                    self.assertEqual( result, result2 )
                    self.assertIs( type(result), type(result2) )
                    self.assertIs( result.__class__, result2.__class__ )


                self.assertEqual( result, result2 )
                self.assertEqual( result2, 5 )

    def test_exposed_mark(self):
        self.assertEqual(emark("<>"), "< (RPyC exposed)>")
        self.assertEqual(emark(""), " (RPyC exposed)")
        valid = False
        try:
            emark(None)
        except TypeError:
            valid = True
        self.assertTrue(valid)

    def test_type_comparison(self):
        class A:
            pass
        A=security_restrict(A, None) #uses default
        a=A()
        self.assertTrue(type(a) == A)
        self.assertTrue(A == type(a))
        self.assertTrue(type(a)._rpyc_getattr == A._rpyc_getattr)

    def test_get_olp(self):
        class A:
            def foo(self):
                pass

        olp = olps.OLP()
        olp.total_expose()
        olp.replace_specified(getattr_locks={"|":locks.BLOCKED})

        instance = security_restrict(A(), olp)
        cls = instance.__class__

        other_olp = get_olp(cls)
        self.assertTrue(other_olp is olp)

        other_olp = get_olp(instance)
        self.assertTrue(other_olp is olp)

        #now test exposed case
        other_olp_cls = cls._rpyc_getattr("_rpyc__olp__")
        self.assertFalse(other_olp_cls is olp)

        other_olp_instance = instance._rpyc_getattr("_rpyc__olp__")
        self.assertFalse(other_olp_instance is olp)

        self.assertEqual(olp.dump(), other_olp_cls.dump())
        self.assertEqual(olp.dump(), other_olp_instance.dump())

        #make sure read only copy.
        valid = False
        try:
           other_olp_cls.getattr_locks["|"][0].permitted()
        except NotImplementedError:
            valid = True
        self.assertTrue(valid)

        #make sure read only copy.
        valid = False
        try:
           other_olp_instance.getattr_locks["|"][0].permitted()
        except NotImplementedError:
            valid = True
        self.assertTrue(valid)

    def test_multiple_olp(self):
        olp = olps.OLP()
        class A:
            pass

        A1 = security_restrict(A, olp)
        A2 = security_restrict(A, olp)
        #There is logic that if you use same
        #object lock profile you get same object.
        self.assertIs(A1, A2)

        instanceA=A()
        olp = olps.OLP()
        olp2 = olps.OLP()
        a=A()
        a1 = security_restrict(a, olp)
        a2 = security_restrict(a, olp)
        a3 = security_restrict(a, olp2)
        self.assertIs(a1, a2)
        self.assertIsNot(a2, a3)

    def test_is_exposed(self):
        class A:
            pass

        class B:
            pass

        A=security_restrict(A, None) #uses default
        a_instance=A()
        b_instance=B()

        self.assertTrue(is_exposed(A))
        self.assertTrue(check_exposed(A))
        self.assertTrue(is_exposed(a_instance))
        self.assertTrue(check_exposed(a_instance))

        self.assertFalse(is_exposed(B))
        self.assertFalse(check_exposed(B))
        self.assertFalse(is_exposed(b_instance))
        self.assertFalse(check_exposed(b_instance))

        class SimpleProxy(object):
            def __init__(self, proxy):
                self._proxy = proxy
            def __getattribute__(self, name):
                proxy = super(SimpleProxy, self).__getattribute__("_proxy")
                return getattr(proxy, name)
        a_proxy = SimpleProxy(a_instance)
        b_proxy = SimpleProxy(b_instance)

        self.assertFalse(is_exposed(a_proxy))
        valid = False
        try:
            value = check_exposed(a_proxy)
        except SecurityWrapError:
            valid = True
        self.assertTrue(valid)

        self.assertFalse(is_exposed(b_proxy))
        self.assertFalse(check_exposed(b_proxy))

    def test_get_olp_error(self):
        valid = False
        try:
            get_olp(None)
        except ValueError:
            valid = True
        self.assertTrue(valid)

    def test_weird_use_of_class_dir(self):
        if is_py3k: #Python3 only test.
            olp = olps.OLP()
            class A:
                pass

            class D:
                x=3

            A1 = security_restrict(A, olp)
            self.assertEqual(set(type(A1).__dir__(D)), set(type(A).__dir__(D)))
        else:
            self.assertTrue(True)

    def test__rpyc__unwrapped__(self):
        olp = olps.OLP()
        class A:
            pass

        A1 = security_restrict(A, olp)
        instanceA = A()
        instanceA1 = security_restrict(instanceA, olp)

        self.assertIs(unwrap(A1), A)
        self.assertIs(unwrap(instanceA1), instanceA)

    def test_simple_exercise_of_attr_functions(self):
        olp = olps.OLP()
        class A:
            pass
        A = security_restrict(A, olp)
        instanceA = A()

        A.x=3
        self.assertEqual(A.x, 3)
        self.assertEqual(instanceA.x, 3)
        del(A.x)
        valid = False
        try:
            A.x
        except AttributeError:
            valid = True
        self.assertTrue(valid)

        instanceA = A()
        instanceA.x = 3

        self.assertEqual(instanceA.x, 3)
        #make sure not set on class.
        valid = False
        try:
            A.x
        except AttributeError:
            valid = True
        del(instanceA.x)
        try:
            instanceA.x
        except AttributeError:
            valid = True
        self.assertTrue(valid)

    def test_unmarked(self):
        olp = olps.OLP(mark=False)
        class A:
            def __repr__(self):
                #define so no id/address printed.
                return "YEEEHA"
        A1 = security_restrict(A, olp)
        self.assertEqual(olp.mark, False)
        self.assertEqual(repr(A1()), repr(A()))
        olp.mark = True
        self.assertNotEqual(repr(A1()), repr(A()))

    def test_instance_dir(self):
        olp = olps.OLP(mark=False)
        class A:
            pass
        A1 = security_restrict(A, olp)
        instanceA=A()
        instanceA1=A1()
        #Makes sure __dir__ code is called, bypasses
        #descriptors.
        other=dir(instanceA)
        other+=["_rpyc_getattr", "_rpyc_setattr", "_rpyc_delattr"]
        self.assertEqual(set(dir(instanceA1)), set(other))

    def test_subclass_identity(self):
        from rpyc.security.exposer import expose
        #It is very easy to have a bug in SecureType
        #such that two classes inheriting from each other
        #suddenly behave identically in regard to one aspect.
        #This is because of the heavy magic. To that end, we
        #test that they don't.

        #Let's do diamond inheritances
        #IE: basically:
        #class A(object):
        #    pass
        #
        #class B(A):
        #    pass
        #
        #class C(A):
        #    pass
        #
        #class D(C,B):
        #    pass
        #
        #But vary whether we use new type objects (for python2)
        #and which of the classes are exposed, and the order of
        #inheritance by B

        class_list=["A", "B", "C", "D"]
        for base_object in ["(object)", ""]: #won't matter for python 3
            for expose_mask in range(0,16): #gonna use as a bit mask for exposure
                                            #of A,B,C,D

                exposed={}
                for i in range(4):
                    exposed_boolean = (expose_mask & 1) != 0
                    exposed[class_list[i]] = exposed_boolean
                    expose_mask = expose_mask >> 1


                subclass_table={ "A":{"A":True, "B":False, "C":False, "D":False},
                                 "B":{"A":True, "B":True, "C":False, "D":False},
                                 "C":{"A":True, "B":False, "C":True, "D":False},
                                 "D":{"A":True, "B":True, "C":True, "D":True} }

                for inheritance_order in ["C,B", "B,C"]:
                    #Build the inheritance
                    output = ""
                    if exposed['A']:
                        output += "@expose\n"
                    output += "class A%s:\n" % base_object
                    output += "\ta=1\n"
                    if exposed['B']:
                        output += "@expose\n"
                    output += "class B(A):\n"
                    output += "\tb=2\n"
                    if exposed['C']:
                        output += "@expose\n"
                    output += "class C(A):\n"
                    output += "\tc=3\n"
                    if exposed['D']:
                        output += "@expose\n"
                    if exposed['C'] and exposed['B']:
                        #we will have to unwrap them, or suffer metaclass issue.
                        if inheritance_order == "C,B":
                            inheritance_order = "unwrap(C),B"
                        elif inheritance_order == "B,C":
                            inheritance_order = "unwrap(B),C"
                        else:
                            self.assertTrue(False)

                    output += "class D(%s):\n" % inheritance_order
                    output += "\td=4\n"

                    #okay, ready to try it.
                    exec(output)

                    #Assert that the reproductions are all unique
                    #These specifically test functions inside
                    #SecureType of SecurityClassRestrictor, to make
                    #sure that "subtyped" is working.

                    reproductions = set()
                    hashes = set()
                    class_value_list = []
                    for class_index in range(len(class_list)):
                        class_name = class_list[class_index]
                        class_value = eval( "%s" % class_name )
                        #test __repr__
                        repr_value = repr(class_value)
                        if exposed[class_name]:
                            self.assertTrue("RPyC exposed" in repr_value)
                        else:
                            self.assertFalse("RPyC exposed" in repr_value)
                        self.assertFalse(repr_value in reproductions)
                        reproductions.add(repr_value)

                        #test __hash__
                        hash_value = hash(class_value)
                        self.assertFalse(hash_value in hashes)
                        hashes.add(hash_value)

                        #test __eq__
                        for value in class_value_list:
                            self.assertFalse(class_value == value)
                            self.assertFalse(value == class_value)
                        class_value_list.append(class_value)

                        #test __dir__
                        directory = dir(class_value)
                        if exposed[class_name]:
                            self.assertTrue("_rpyc_getattr" in directory)
                            self.assertTrue("_rpyc_setattr" in directory)
                            self.assertTrue("_rpyc_delattr" in directory)
                        else:
                            self.assertFalse("_rpyc_getattr" in directory)
                            self.assertFalse("_rpyc_setattr" in directory)
                            self.assertFalse("_rpyc_delattr" in directory)
                        for item in list("ABCD"):
                            if subclass_table[class_name][item]:
                               self.assertTrue(item.lower() in directory)
                            else:
                               self.assertFalse(item.lower() in directory)

                        for item in list("abcd")[class_index+1:]:
                            self.assertFalse(item in directory)

                        #test __delattr__ and __setattr__
                        for value in list("abcd"):
                            if class_name.lower()==value:
                                delattr(class_value, value)
                                self.assertTrue(value not in dir(class_value))
                                setattr(class_value, value, class_index)
                            else:
                                valid = False
                                try:
                                    delattr(class_value, value)
                                except AttributeError:
                                    valid = True
                                self.assertTrue(valid)

                        #test __subclasscheck__
                        sub_table = subclass_table[class_name]
                        for key in sub_table:
                            other_class = eval(key)
                            self.assertEqual(issubclass(class_value, other_class), sub_table[key])

                        #test __instancecheck__
                        for key in sub_table:
                            other_class = eval(key)
                            self.assertEqual(isinstance(class_value(), other_class), sub_table[key])


                    #test __call__
                    #_rpyc_getattr
                    #__getattribute__
                    #_rpyc_setattr
                    #_rpyc_delattr

if __name__ == "__main__":
    unittest.main()


