import sys
from nose import SkipTest
if sys.version_info < (3, 0):
    raise SkipTest("Those are only for Python3")

import inspect
import global_consts
from itertools import count
import netref_3 as netref

#####################################################################
#####################################################################
#
#
# TESTING:: inspect methods
#
#
#####################################################################
#####################################################################

simple_dict = {1:"A", 2:{"A":"C"}}

def test_inspect_methods_dict():
    meth_doc_list_actual = netref.inspect_methods(simple_dict)
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_dict, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = set([name for name, doc in netref.inspect_methods(simple_dict)])
    a_few_expected_dict_methods = set(['popitem', 'pop', 'get', 'keys', 'update', '__iter__', 'setdefault', 'items', 'clear'])
    print("Checking I get a few dict methods expected in 3.1")
    assert methods_actual > a_few_expected_dict_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_dict")
    assert all([hasattr(simple_dict, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_dict, meth), "__call__") for meth in methods_actual])
    
#===================================================================

simple_list = [1, 2, 3]

def test_inspect_methods_list():
    meth_doc_list_actual = netref.inspect_methods(simple_list)
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_list, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = set(name for name, doc in netref.inspect_methods(simple_list))
    a_few_expected_list_methods = set(['append', 'pop', 'extend', 'sort', '__iter__', 'count'])
    print("Checking I get a few list methods expected in 3.1")
    assert methods_actual > a_few_expected_list_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_list")
    assert all([hasattr(simple_list, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_list, meth), "__call__") for meth in methods_actual])

#===================================================================

simple_string = "example string"

def test_inspect_methods_str():
    meth_doc_list_actual = netref.inspect_methods(simple_string)
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_string, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = set(name for name, doc in netref.inspect_methods(simple_string))
    a_few_expected_string_methods = set(['startswith', 'encode', 'format', 'isdigit', 'rfind', 'strip'])
    print("Checking I get a few string methods expected in 3.1")
    assert methods_actual > a_few_expected_string_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_string")
    assert all([hasattr(simple_string, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_string, meth), "__call__") for meth in methods_actual])

#===================================================================

simple_mul_tuple = ("simple_mul_tuple", [])

def test_inspect_methods_mul_tuple():
    meth_doc_list_actual = netref.inspect_methods(simple_mul_tuple)
    meth_doc_list_expected = [(name, inspect.getdoc(attr)) for name, attr in inspect.getmembers(simple_mul_tuple, inspect.isroutine)]
    
    print("-"*40)
    print("Checking get more than inspect gets, as I going above what is in dir")
    result = (set(meth_doc_list_actual) - set(meth_doc_list_expected))
    print("RESULT=", result, "set=", set(meth_doc_list_actual) - set(meth_doc_list_expected))
    assert result
    
    print("-"*40)
    methods_actual = set(name for name, doc in netref.inspect_methods(simple_mul_tuple))
    a_few_expected_mul_tuple_methods = set(['__contains__', '__hash__', '__iter__', '__le__', '__len__', 'index'])
    print("Checking I get a few string methods expected in 3.1")
    assert methods_actual > a_few_expected_mul_tuple_methods
    
    print("-"*40)
    print("check every attr is actually an attr of simple_mul_tuple")
    assert all([hasattr(simple_mul_tuple, meth) for meth in methods_actual])
    
    print("-"*40)
    print("check every attr is actually callable")
    assert all([hasattr(getattr(simple_mul_tuple, meth), "__call__") for meth in methods_actual])

#===================================================================

class simple_cls(object):
    """Simple exmaple of a class, has a method simple_meth"""
    def __init__(self):
        """simple __init__"""
        self.eg_attr = "example"
    def simple_meth(self):
        """simple method doc"""
        return True

def test_inspect_methods_simple_cls():
    meth_doc_dict = dict(netref.inspect_methods(simple_cls))
    print("-"*40)
    print("checking presence of simple method")
    assert simple_cls.simple_meth.__name__ in meth_doc_dict
    
    print("checking non presence of non callable eg_attr")
    assert "eg_attr" not in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method doc")
    assert meth_doc_dict["simple_meth"] == simple_cls.simple_meth.__doc__

#===================================================================

simple_instance = simple_cls()

def test_inspect_methods_simple_instance():
    meth_doc_dict = dict(netref.inspect_methods(simple_instance))
    print("-"*40)
    print("checking presence of simple method")
    assert simple_instance.simple_meth.__name__ in meth_doc_dict
    
    print("checking non presence of non callable eg_attr")
    assert "eg_attr" not in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method doc")
    assert meth_doc_dict["simple_meth"] == simple_instance.simple_meth.__doc__

#===================================================================

def simple_function(x):
    def nested_func():
        pass
    return 4

def test_inspect_methods_simple_function():
    meth_doc_dict = dict(netref.inspect_methods(simple_function))
    print("-"*40)
    print("checking presence of __call__ in simple function")
    print(meth_doc_dict.keys())
    assert '__call__' in meth_doc_dict
    
    print("-"*40)
    assert meth_doc_dict['__call__'] == simple_function.__call__.__doc__

#===================================================================

def test_inspect_methods_module():
    meth_doc_dict = dict(netref.inspect_methods(inspect))
    print("-"*40)
    print("checking presence of __str__ in simple function")
    assert "__str__" in meth_doc_dict

#===================================================================

class advanced_class(simple_cls):
    def __init__(self):
        """advanced __init__"""
        pass
    def another_meth(self):
        pass

def test_inspect_methods_advanced_cls():
    meth_doc_dict = dict(netref.inspect_methods(advanced_class))
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_class.simple_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_class.another_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of correct doc method for method in both simple and advanced class")
    assert meth_doc_dict["__init__"] == advanced_class.__init__.__doc__ != simple_cls.__init__.__doc__


#===================================================================

advanced_instance = advanced_class()

def test_inspect_methods_advanced_instance():
    meth_doc_dict = dict(netref.inspect_methods(advanced_instance))
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_instance.simple_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of simple method")
    assert advanced_instance.another_meth.__name__ in meth_doc_dict
    
    print("-"*40)
    print("checking presence of correct doc method for method in both simple and advanced class")
    assert meth_doc_dict["__init__"] == advanced_instance.__init__.__doc__ != simple_cls.__init__.__doc__

#===================================================================

#def test_inspect_methods_metaclass():
#    assert False   # I smeta class inheratnace the correct way around, is the method doc correct

#===================================================================


#####################################################################
#####################################################################
#
#
# TESTING:: make_proxy_class
#
#
#####################################################################
#####################################################################

class pretend_connection(object):
    obj_register = {}
    obj_id = count(1)
    def __init__(self):
        self.handlers = {global_consts.HANDLE_GETATTR: lambda oid, attr_name: getattr(self.obj_register[oid], attr_name),
                         global_consts.HANDLE_DELATTR: lambda oid, attr_name: delattr(self.obj_register[oid], attr_name),
                         global_consts.HANDLE_SETATTR: lambda oid, attr_name, val: setattr(self.obj_register[oid], attr_name, val),
                         global_consts.HANDLE_HASH: lambda oid: hash(self.obj_register[oid]),
                         global_consts.HANDLE_REPR:  lambda oid: repr(self.obj_register[oid]),
                         global_consts.HANDLE_STR: lambda oid: str(self.obj_register[oid]),
                         global_consts.HANDLE_CALL: lambda oid, args, kwargs: self.obj_register[oid](*args, **dict(kwargs)),
                         global_consts.HANDLE_CALLATTR:lambda oid, attr_name, args, kwargs: self.handlers[global_consts.HANDLE_GETATTR](oid, attr_name)(*args, **dict(kwargs))}
    
    def register_object(self, obj, oid):
        self.obj_register[oid] = obj
    
    def sync_request(self, handler, oid, *args):
        """conn().sync_request(handler, oid, *args)"""
        print("test_netref_3 sync_request, handler=", handler, "oid=", oid, "args=", args)
        
        try:
            ret_val = self.handlers[handler](oid, *args)
        except KeyError:
            print("Test doesn't handled that constant")
            raise
        else:
            return ret_val
    
    def async_request(self, handler, oid, *args):
        return "async_request", handler
    
    def make_proxy_for_testing(self, obj):
        func_cls = type(obj)
        clsname = func_cls.__name__
        modname = func_cls.__module__
        methods = netref.inspect_methods(obj)
        proxy_cls = netref.make_proxy_class(clsname, modname, methods)
        
        new_function_oid = self.obj_id.__next__()
        oid = new_function_oid
        
        self.register_object(obj, oid)
        proxy_obj = proxy_cls(self, oid)
        
        return proxy_obj, proxy_cls

class Test_make_proxy(object):
    def setup(self):
        self.conn = pretend_connection()
    def teardown(self):
        del self.conn

    def test_func(self):
        
        def new_function(x, y):
            return x+y
        
        proxy_obj, proxy_cls = self.conn.make_proxy_for_testing(new_function)
        
        #--------------------
        # Check got proxy
        
        print("Checking proxy_obj is a newref proxy")
        assert netref.is_netref(proxy_obj) == True
        print("Checking new_function is not a newref proxy")
        assert netref.is_netref(new_function) == False
        
        #--------------------
        # Check callable and return value
        expected_retval = 5
        new_func_retval = new_function(2, 3)
        proxy_func_retval = proxy_obj(2, 3)
        print("Checking (expected_retval={expected_retval}) == (new_func_retval={new_func_retval}) == (proxy_func_retval={proxy_func_retval})".format(**locals()))
        assert new_func_retval == proxy_func_retval == expected_retval
        
        #--------------------
        # Check async
        typ, hand = netref.asyncreq(proxy=proxy_obj, handler=4)
        print("Checking async call", ("async_request", 4))
        assert (typ, hand) == ("async_request", 4)

    def test_dict(self):
        
        local_dict = {"A":1, "B":2}
        
        proxy_obj, proxy_cls = self.conn.make_proxy_for_testing(local_dict)
        print("Checking proxy_obj is a newref proxy")
        assert netref.is_netref(proxy_obj) == True
        print("Checking new_function is not a newref proxy")
        assert netref.is_netref(local_dict) == False
        
        local_dict_retval = local_dict["A"]
        proxy_dict_retval = proxy_obj["A"]
        print("Checking (local_dict_retval={local_dict_retval}) == (proxy_dict_retval={proxy_dict_retval})".format(**locals()))
        assert local_dict_retval == proxy_dict_retval
        
        #------------------ 
        #method docs
        
        local_dict_keys_doc = local_dict.keys.__doc__
        proxy_dict_keys_doc = proxy_obj.keys.__doc__
        print("Checking keys method same (local_dict={local_dict_keys_doc}) == (proxy_obj={proxy_dict_keys_doc})".format(**locals()))
        assert local_dict_keys_doc == proxy_dict_keys_doc
        
        #------------------
        #method keys
        
        keys_proxy_obj, keys_proxy_cls = self.conn.make_proxy_for_testing(local_dict.keys)
        proxy_keys = keys_proxy_obj()
        local_dict_keys = local_dict.keys()
        print("Checking keys same (local_dict={local_dict_keys}) == (proxy_obj={proxy_keys})".format(**locals()))
        assert proxy_keys == local_dict_keys
        
        #-----------------
        #obj still iterable
        
        set_of_keys_from_proxy = set([key for key in proxy_obj])
        set_of_local_keys = set(local_dict_keys)
        print("Checking dict still iterable keys={set_of_keys_from_proxy})".format(**locals()))
        assert set_of_keys_from_proxy == set_of_local_keys
        
        #----------------
        #obj proxy still repr
        
        proxy_repr = repr(proxy_obj)
        local_repr = repr(local_dict)
        print("Checking dict still repr (proxy repr={proxy_repr})==(local repr={local_repr}))".format(**locals()))
        assert proxy_repr == local_repr


    def test_class(self):
        
        class local_class(object):
            cls_attr = 42
            def __init__(self, x):
                self.x = x
            @classmethod
            def local_cls_function(cls):
                """A local function"""
                return cls.cls_attr
        
        proxy_obj, proxy_cls = self.conn.make_proxy_for_testing(local_class)
        
        #--------------------------------
        # cls attr access
        print("checking class attr access and classmethod")
        assert proxy_obj.local_cls_function() == proxy_obj.cls_attr == local_class.local_cls_function() == local_class.cls_attr
        
        #--------------------------------
        # setting class attr via proxy
        proxy_obj.cls_attr += 1
        print("checking class attr set and reading changed value")
        assert proxy_obj.local_cls_function() == proxy_obj.cls_attr == local_class.local_cls_function() == local_class.cls_attr == 43
        
        #--------------------------------
        # instance creation
        instance_via_proxy = proxy_obj(1)
        instance_via_native = local_class(1)
        
        print("checking instance created via proxy and via native, (instance_via_proxy.x={instance_via_proxy.x}) == (instance_via_native.x={instance_via_native.x})".format(**locals()))
        assert instance_via_proxy.x == instance_via_native.x

    def test_instances(self):
        
        class local_class1(object):
            """DOC1"""
            def __init__(self):
                self.local_attr = 13
            def local_function(self):
                """A local function"""
                return 42
            def func1(self):
                return 1
            def __hash__(self):
                return 7
        
        class local_class2(local_class1):
            """DOC2"""
            def __init__(self):
                pass
            def func1(self):
                return "one"
        
        instance1 = local_class1()
        instance2 = local_class2()
        
        proxy_obj1, proxy_cls1 = self.conn.make_proxy_for_testing(instance1)
        proxy_obj2, proxy_cls2 = self.conn.make_proxy_for_testing(instance2)
        #make remote instances of above
        
        #-----------------------------
        # hash consistant
        proxy1_hash = hash(proxy_obj1)
        proxy2_hash = hash(proxy_obj2)
        local1_hash = hash(instance1)
        local2_hash = hash(instance2)
        print("hash consistant:: (proxy1_hash={proxy1_hash}) == (proxy2_hash={proxy2_hash}) == (local1_hash={local1_hash}) == (local2_hash={local2_hash})".format(**locals()))
        assert proxy1_hash == proxy2_hash == local1_hash == local2_hash
        
        #-----------------------------
        # class consistant
        proxy1_class = proxy_obj1.__class__
        local1_class = instance1.__class__
        print("hash1 consistant:: (proxy1_class={proxy1_class}) == (local1_class={local1_class})".format(**locals()))
        assert proxy1_class ==  local1_class
        
        proxy2_class = proxy_obj2.__class__
        local2_class = instance2.__class__
        print("hash2 consistant:: (proxy2_class={proxy2_class}) == (local2_class={local2_class})".format(**locals()))
        assert proxy2_class == local2_class
        
        #-----------------------------
        # doc consistant
        proxy1_doc = proxy_obj1.__doc__
        local1_doc = instance1.__doc__
        print("doc consistant:: (proxy1_doc={proxy1_doc}) == (local1_doc={local1_doc}) ".format(**locals()))
        assert proxy1_doc == local1_doc
        
        proxy2_doc = proxy_obj2.__doc__
        local2_doc = instance2.__doc__
        print("doc consistant:: (proxy2_doc={proxy2_doc}) == (local2_doc={local2_doc}) ".format(**locals()))
        assert proxy2_doc == local2_doc
        
        #-----------------------------
        # dict consistant
        proxy1_dict = proxy_obj1.__dict__
        local1_dict = instance1.__dict__
        print("__dict__ consistant:: (proxy1_dict={proxy1_dict}) == (local1_dict={local1_dict})".format(**locals()))
        assert proxy1_dict == local1_dict
        
        local2_dict = instance2.__dict__
        proxy2_dict = proxy_obj2.__dict__
        print("__dict__ consistant:: (proxy2_dict={proxy2_dict}) == (local2_dict={local2_dict})".format(**locals()))
        assert proxy2_dict == local2_dict
        
        #-----------------------------
        # func 1
        proxy1_func1 = proxy_obj1.func1()
        print("checking proxy1_func1", proxy1_func1)
        assert proxy1_func1 == 1
        
        proxy2_func1 = proxy_obj2.func1()
        print("checking proxy2_func1", proxy2_func1)
        assert proxy2_func1 == "one"
        
        #-----------------------------
        # func
        proxy2_func1 = lambda : 4
        proxy_obj2.func1 = proxy2_func1
        proxy2_func1 = proxy_obj2.func1()
        instance2_func1 = instance2.func1()
        proxy1_func1 = proxy_obj1.func1()
        print("checking newly made func through proxy", proxy2_func1)
        assert proxy2_func1 == proxy2_func1 == 4 != proxy1_func1
        
        #-----------------------------
        # new addr
        proxy_obj2.attr_new = 111
        proxy2_added_attr = proxy_obj2.attr_new
        instance2_added_attr = instance2.attr_new
        print("checking newly added attr", proxy2_added_attr)
        assert proxy2_added_attr == instance2_added_attr == 111
        
        local2_dict = instance2.__dict__
        proxy2_dict = proxy_obj2.__dict__
        print(local2_dict, proxy2_dict)
        print("__dict__ consistant after adding addr:: (proxy2_dict={proxy2_dict}) == (local2_dict={local2_dict})".format(**locals()))
        assert proxy2_dict == local2_dict and "attr_new" in local2_dict

    def test_generator(self):
        
        generator1 = (x for x in range(10))
        generator2 = (x for x in range(10))
        self.conn = pretend_connection()  #For some reason setup doesn't work here
        proxy_obj, proxy_cls = self.conn.make_proxy_for_testing(generator2)
        del self.conn
        for x, y in zip(generator1, proxy_obj):
            yield self.check_eq, x, y
    
    def check_eq(self, x, y):
        assert x == y
    
    def test_slots_objects(self):
        
        class slots_class(object):
            __slots__ = ('x', 'y')
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        native_slots = slots_class(1,2)
        proxy_slots, proxy_slots_cls = self.conn.make_proxy_for_testing(native_slots)
        
        print("Check slots object x attr the same native={native_slots.x}, proxy={proxy_slots.x}".format(**locals()))
        assert native_slots.x == proxy_slots.x
        
        try:
            native_slots.z = 3
        except AttributeError:
            pass
        else:
            raise Exception
        try:
            proxy_slots.a = 4
        except AttributeError:
            pass
        else:
            raise Exception

#===================================================================

def test_global_type_stores():
    native_types = netref.NATIVE_BUILTIN_TYPE_DICT
    proxy_types = netref.PROXY_BUILTIN_TYPE_DICT
    
    number_native_types = len(native_types)
    number_proxy_types = len(proxy_types)
    
    print("Checking for non zero type stores")
    assert number_native_types == number_proxy_types > 0
    
    all_ok = all([issubclass(typ, netref.BaseNetref) for typ in proxy_types.values()])
    print("Checking proxies are of corect class")
    print(type(tuple(proxy_types.values())[0]))
    assert all_ok
    
#===================================================================


#Files
#Sockets
#Etc

#Abstract, metaclass
#mutli inheratance
#Non mro object

#It sets class in class_factory, if this uses builtin_classes_cache does it work across computers???
