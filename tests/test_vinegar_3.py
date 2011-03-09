import sys
from nose import SkipTest
if sys.version_info < (3, 0):
    raise SkipTest("Those are only for Python3")
            
from rpyc.core.vinegar_3 import dump, load, install_rpyc_excepthook, uninstall_rpyc_excepthook, rpyc_excepthook, GenericException

import traceback
from nose.tools import raises
from global_consts import EXCEPTION_STOP_ITERATION
from inspect import ismethod, isfunction

from vinegar_3 import dump, load, install_rpyc_excepthook, uninstall_rpyc_excepthook, rpyc_excepthook, Vinegar_Import_Exception, GenericException

from external_exception_for_vin3 import external_exception as external_exception_renamed

def check_equal(dictionary_of_key_values):
    """Just a useful function to make nose stdout readable."""
    
    print("-"*30)
    print("Testing")
    result = False
    print(result)
    print("-"*30)
    
    return result

#====================================================================
# Custom exceptions
#====================================================================

class my_exception_no_args(Exception):
    def __init__(self):
        self.args = ()
    def __repr__(self):
        return "repr: my_exception_no_args"

class my_exception_with_args(Exception):
    def __init__(self, err_string, err_type):
        self.args = (err_string, err_type)
        self.err_string = err_string
        self.type = err_type
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

class remote_exception(Exception):
    def __init__(self):
        self.args = ()
    def __str__(self):
        return "str: remote computer rebelling"
    def __repr__(self):
        return "repr: remote computer rebelling"

#====================================================================
# Generic useful functions
#====================================================================

def simulate_raise_exception(my_exception):
    exception_class = type(my_exception)
    try:
        raise my_exception
    except exception_class:
        traceback_txt = traceback.format_exception(exception_class, my_exception, my_exception.__traceback__)
    return exception_class, my_exception, my_exception.__traceback__

#====================================================================
# Test vinegar module setup
#====================================================================

def test_install_and_un_hook():
    orginal_hook = sys.excepthook
    install_rpyc_excepthook()
    new_hook = sys.excepthook
    
    print("orginal_hook:", orginal_hook)
    print("new_hook:", new_hook)
    
    assert new_hook != orginal_hook
    assert new_hook == rpyc_excepthook
    
    uninstall_rpyc_excepthook()
    
    restored_hook = sys.excepthook
    
    print("restored_hook:", restored_hook)
    
    assert restored_hook == orginal_hook

#========================================================================
# Test loading and dumping of exceptions
#========================================================================

class test_dump_load(object):
    def setup(self):
        install_rpyc_excepthook()

    def teardown(self):
        uninstall_rpyc_excepthook()

    def test_StopIteration(self):
        """Check and serialse and unserialise a StopIteration"""
        exception_instance = StopIteration()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        
        print("brimable_data: == EXCEPTION_STOP_ITERATION:")
        print("{0}=={1}".format(brimable_data, EXCEPTION_STOP_ITERATION))
        
        assert brimable_data == EXCEPTION_STOP_ITERATION
        
        decoded_exception = load(brimable_data)
        
        print("decoded_exception: == StopIteration:")
        print("{0}=={1}".format(type(decoded_exception), StopIteration))
        
        assert type(decoded_exception) == StopIteration
    
    def test_TypeError(self):
        """Check  serialise and unserialse a builtin TypeError"""
        exception_instance = TypeError()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        
        print("module_name (== \"builtins\") :: ", module_name)
        assert module_name == "builtins"
        
        print("exception_class_name (== \"TypeError\") :: ", exception_class_name)
        assert exception_class_name == "TypeError"
        
        print("arguments ( == () ) :: ", arguments)
        assert arguments == ()
        
        print("attributes :: ", attributes)
        
        print("traceback_txt (not in {None, ""}) :: ", traceback_txt)
        assert traceback_txt not in (None, "")
        
        print("brimable_data () :: ")
        print("{0}".format(brimable_data))
        
        decoded_exception = load(brimable_data)
        
        print("-"*30)
        print("decoded_exception: == TypeError:")
        print("{0} == {1}".format(type(decoded_exception), TypeError))
        assert type(decoded_exception) == TypeError
        
        
        print("-"*30)
        print("decoded_exception: should have remote_tb attribute")
        assert hasattr(decoded_exception, "_remote_tb")
        
        print("-"*30)
        print("check contains remote exception")
        assert decoded_exception._remote_tb[0].startswith("Traceback")
        
    def test_custom_xecpt_no_args(self):
        """Check  serialise and unserialse a Exception with no arguments"""
        exception_instance = my_exception_no_args()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        
        print("Dumping exception (serialization)")
        brimable_data = dump(cls, instance, traceback)
        print("-"*30)
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        
        print("\n --Exception in dumpable format---")
        print("module_name={0},\nexception_class_name={1},\narguments={2},\nattributes={3},\ntraceback_txt='{4}'".format(
                                module_name, exception_class_name, arguments, attributes, traceback_txt.replace('\n', '')))
        print("\n")
        
        print("-"*30)
        print("Checking exception class name is correct")
        assert exception_class_name == "my_exception_no_args"
        print("PASS")
        print("-"*30)
        print("Checking arguments are correct")
        assert arguments == ()
        print("PASS")
        print("-"*30)
        print("Loading in dumped exception (deserialization)")
        decoded_exception = load(brimable_data)
        
        # This decoded exception will be an generic representation of the custom exception above
        # This is because instantiate_custom_exceptions and use_nonstandard_exceptions are both off
        
        # Should not have arguments
        print("-"*30)
        print("decoded_exception: should have no arguments")
        print("decoded_exception args={0}".format(decoded_exception.args))
        assert decoded_exception.args == ()
        
        print("-"*30)
        print("decoded_exception: should have remote_tb attribute")
        assert hasattr(decoded_exception, "_remote_tb")
        
        print("-"*30)
        print("Checking representation of exception")
        print("type(decoded_exception)={0}".format(repr(type(decoded_exception))))
        print("type(orginal exception)={0}".format(type(exception_instance)))
        assert type(decoded_exception) == type(exception_instance)
        
    def test_custom_xecpt_as_generic_with_args(self):
        """Check can serialise and unserialse a Exception with arguments"""
        arguments_to_pass = "example_string", "ERROR_TYPE_TEST"
        exception_instance = my_exception_with_args(*arguments_to_pass)
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        
        #Dump
        brimable_data = dump(cls, instance, traceback)
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        print("-"*30)
        print(exception_class_name, " == my_exception_with_args")
        assert exception_class_name == "my_exception_with_args"
        print("-"*30)
        print(my_exception_with_args, " == ", arguments_to_pass)
        assert arguments == arguments_to_pass
        
        #Load
        decoded_exception = load(brimable_data, use_nonstandard_exceptions=False)
        
        print("-"*30)
        print("decoded_mod_name : {0} == {1} : orginal_mod_name".format(decoded_exception.__module__, my_exception_with_args.__module__))
        assert decoded_exception.__module__ == exception_instance.__module__
        print("-"*30)
        print("decoded_args : {0} == {1} : args_given".format(decoded_exception.args, arguments_to_pass))
        assert decoded_exception.args == arguments_to_pass
        print("-"*30)
        print("attr1 : {0} == {1} : should be".format(decoded_exception.type, arguments_to_pass[0]))
        assert decoded_exception.err_string == arguments_to_pass[0]
        print("-"*30)
        print("attr2 : {0} == {1} : should be".format(decoded_exception.err_string, arguments_to_pass[1]))
        assert decoded_exception.type == arguments_to_pass[1]
        print("-"*30)
        print("decoded_exception: should have remote_tb attribute")
        assert hasattr(decoded_exception, "_remote_tb")
        
        # This decoded exception will be an generic representation of the my_exception_with_args exception above
        # This is because instantiate_custom_exceptions and use_nonstandard_exceptions are both off
        print("-"*30)
        print("isinstance(decoded_exception, GenericException)")
        assert isinstance(decoded_exception, GenericException)

    def test_remote_tb(self):
        exception_instance = remote_exception()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        decoded_exception = load(brimable_data)
        
        print("-"*30)
        print("decoded_exception: should have remote_tb attribute")
        assert hasattr(decoded_exception, "_remote_tb")
        
        print("-"*30)
        print("remote traceback = {0}".format(''.join(decoded_exception._remote_tb)))
        assert "str: remote computer rebelling" in ''.join(decoded_exception._remote_tb)
    
    @raises(Vinegar_Import_Exception)
    def test_unimportable(self):
        """This testing trying to import a module which can't be imported""" 
        exception_instance = remote_exception()
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        new_module_name = "unfindable_module"
        print("Changing module name to '{0}'".format(new_module_name))
        brimable_data = (new_module_name, exception_class_name), arguments, attributes, traceback_txt
        decoded_exception = load(brimable_data, allow_importfail=False)
    
    def test_imported_exception(self):
        """Here we have a custom exception imported under a different name.  rpyc will try and import it.
        It will use two methods instantiate_custom exceptions
        """
        exception_instance = external_exception_renamed()
        print("orginal exception arguments=", exception_instance.args)
        
        cls, instance, traceback = simulate_raise_exception(exception_instance)
        brimable_data = dump(cls, instance, traceback)
        (module_name, exception_class_name), arguments, attributes, traceback_txt = brimable_data
        
        print("decoding exception arguments=", arguments)
        
        print("module_name={0},\nexception_class_name={1},\narguments={2},\nattributes={3},\ntraceback_txt='{4}'".format(
                        module_name, exception_class_name, arguments, attributes, traceback_txt.replace('\n', '')))
        
        print("-"*30)
        print("Changing module name to test that")
        assert module_name == "external_exception_for_vin3"
        assert exception_class_name == "external_exception"
        
        print("-"*30)
        print("Now trying to load external module")
        decoded_exception = load(brimable_data)
        
        print("-"*40)
        print("testing example exception attr")
        print("exception_instance.external_demo_attr=", exception_instance.external_demo_attr)
        print("decoded_exception.external_demo_attr=", decoded_exception.external_demo_attr)
        assert decoded_exception.external_demo_attr == 2
        print("PASS")
        
        print("-"*40)
        print("testing argument passing")
        print("exception_instance.args=", exception_instance.args)
        print("decoded_exception.args=", decoded_exception.args)
        assert decoded_exception.args == ('I am alive',)
        print("PASS")
        
        print("-"*40)
        print("testing exception instantated correctly")
        print("type(decoded_exception)={0}".format(type(decoded_exception)))
        print("type(exception_instance)={0}".format(type(exception_instance)))
        assert type(decoded_exception) == type(exception_instance)
        print("PASS")
        
    def test_imported_exception2(self):
        brimable_data = ("external_exception2_for_vin3", "orphan_external_exception"), ('I am alive',), (('external_demo_attr', 2),), "EXAMPLE_TRACEBACK"
        decoded_exception = load(brimable_data)
        from external_exception2_for_vin3 import orphan_external_exception
        
        print("decoded_exception.args=", decoded_exception.args)
        assert decoded_exception.args == ('I am alive',)
        
        print("type(decoded_exception)={0}".format(type(decoded_exception)))
        print("Real exception imported orginal={0}".format(type(orphan_external_exception())))
        assert type(decoded_exception) == type(orphan_external_exception())