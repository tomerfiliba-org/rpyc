#This is a metaprogram to create unittest cases for the
#expose decorator. It is ugly, but it works

test_list=[]

output="""
##THIS IS AUTO-GENERATED BY ANOTHER FILE
##DO NOT MODIFY DIRECTLY, modify _gen_test_exposer.py
##TO recreate it.

import unittest
import functools
from rpyc.security import locks
from rpyc.security import olps
from rpyc.security.exposer import expose, routine_expose, field_expose
from rpyc.security.exceptions import SecurityError, SecurityAttrError
from nose.tools import nottest

class ToggleLock(locks.Lock):
    def __init__(self, name):
        self._unlocked=True
        self._name=name

    def permitted(self, **kwargs):
        return self._unlocked

    @property
    def unlocked(self):
        return self._unlocked

    @unlocked.setter
    def unlocked(self, value):
        self._unlocked = (value == True)

    def __str__(self):
        return self._name

#Create controllable locks.
toggle_lock_a = ToggleLock("a")
toggle_lock_b = ToggleLock("b")
toggle_lock_c = ToggleLock("c")
toggle_lock_d = ToggleLock("d")
toggle_lock_e = ToggleLock("e")
toggle_lock_f = ToggleLock("f")

#These locks are here to make sure
#properties are getting the right locks
#assigned
property_lock_get = ToggleLock("prop_get")
property_lock_set = ToggleLock("prop_set")
property_lock_del = ToggleLock("prop_del")


inherit_blob_c = \
    olps.OLP(getattr_locks={"&":toggle_lock_c},
                              setattr_locks={"&":toggle_lock_c},
                              delattr_locks={"&":toggle_lock_c},
                              cls_getattr_locks={"&":toggle_lock_c},
                              cls_setattr_locks={"&":toggle_lock_c},
                              cls_delattr_locks={"&":toggle_lock_c} )
inherit_blob_f = \
    olps.OLP(getattr_locks={"&":toggle_lock_f},
                              setattr_locks={"&":toggle_lock_f},
                              delattr_locks={"&":toggle_lock_f},
                              cls_getattr_locks={"&":toggle_lock_f},
                              cls_setattr_locks={"&":toggle_lock_f},
                              cls_delattr_locks={"&":toggle_lock_f} )
"""

all_exposure_types = ["blank", "empty", "lock", "locklist", "locklistand", "locklistor"]
property_exposure_types = ["empty", "lock", "locklist", "locklistand", "locklistor"] #drop blank
                                                                                     #because we add lock to
                                                                                     #property
all_function_forms = ["generator", "standard"]
property_function_forms = ["standard"]
value_types = ["function", "staticmethod", "classmethod", "method", "property"]
inherit_flags = ["noinherit", "inherit"]

namespaces={}
namespaces["global"]=""
extra_stuff="" #to append at end.

for class_exposure_type in all_exposure_types:
    for class_inherit_flag in inherit_flags:
        namespaces["foo_%s_%s" % (class_exposure_type, class_inherit_flag)]=""

def create_expose_lock_list(exposure_type, inherit_flag, class_exposure=False, extra_lock_name=None):
    if class_exposure:
        char_lock0 = "d"
    else:
        char_lock0 = "a"
    char_lock1 = chr(ord(char_lock0)+1)
    char_lock2 = chr(ord(char_lock0)+2)
    lock0_string = "toggle_lock_%s" % char_lock0
    lock1_string = "toggle_lock_%s" % char_lock1
    lock2_string = "toggle_lock_%s" % char_lock2

    if exposure_type == "blank":
        inside=[]
    if exposure_type == "empty":
        inside=[]
    elif exposure_type == "lock":
        inside=[lock0_string]
    elif exposure_type == "locklist":
        inside=["[%s, %s]" % (lock0_string, lock1_string)]
    elif exposure_type == "locklistand":
        inside=["locks.LL_And([%s, %s])" % (lock0_string, lock1_string)]
    elif exposure_type == "locklistor":
        inside=["locks.LL_Or([%s, %s])" % (lock0_string, lock1_string)]

    if extra_lock_name is not None:
        if len(inside)==0:
            inside.append("[]")
        inside=["locks.LL_And([%s, %s])" % (inside[0], extra_lock_name)]

    if inherit_flag == "inherit":
        inside.append("inherit=inherit_blob_%s" % char_lock2)

    return inside

def create_expose(indent, exposure_type, inherit_flag, class_exposure=False, extra_lock_name=None):
    if exposure_type == "blank":
        return "%s@expose\n" % indent
    else:
        inside = create_expose_lock_list(exposure_type,
                                         inherit_flag,
                                         class_exposure = class_exposure,
                                         extra_lock_name = extra_lock_name)

        return "%s@expose(%s)\n" % (indent, ", ".join(inside))

def create_manual_expose(namespace, name, exposure_type, inherit_flag):
    inside = create_expose_lock_list(exposure_type, inherit_flag)

    if namespace == "global":
        inside = [name]+inside
        #Only routines can be exposed in global space.
        extra = "%s = routine_expose(%s)\n" % (name, ", ".join(inside))
    else:
        inside = [namespace, '"%s"' % name]+inside
        extra = "field_expose(%s)\n" % (", ".join(inside))
    return extra

getname_blob= \
"""
def get_name(value_type, value_form, exposure_type, inherit_flag, exposure_location):
    name = "%s_%s_%s_%s_%s" % (value_type, value_form, exposure_type, inherit_flag, exposure_location)
    return name
"""
#needs to exist both here and in test code.
output+=getname_blob
exec(getname_blob)

def create_value(namespace, value_type, value_form, exposure_type, inherit_flag, exposure_location):
    tab=" "*4
    indent=""
    if namespace != "global":
        indent=tab

    name = get_name(value_type, value_form, exposure_type, inherit_flag, exposure_location)
    value=""
    extra=""

    if value_type == "property":
        #Totally different than normal path, handle specially.
        value += "%s@property\n" % indent
        value += create_expose(indent, exposure_type, inherit_flag, extra_lock_name="property_lock_get")
        value += "%sdef %s(self):\n" % (indent, name)
        value += "%s%sreturn self._the_property\n\n" % (indent, tab)

        value += "%s@%s.setter\n" % (indent, name)
        value += create_expose(indent, exposure_type, inherit_flag, extra_lock_name="property_lock_set")
        value += "%sdef %s(self, value):\n" % (indent, name)
        value += "%s%sself._the_property=value\n\n" % (indent, tab)

        value += "%s@%s.deleter\n" % (indent, name)
        value += create_expose(indent, exposure_type, inherit_flag, extra_lock_name="property_lock_del")
        value += "%sdef %s(self):\n" % (indent, name)
        value += "%s%sself._the_property='deleted'\n\n" % (indent, tab)
        return value, extra

    #Otherewise handle normally.
    if exposure_location == "above":
        value += create_expose(indent, exposure_type, inherit_flag)

    if value_type in ["staticmethod", "classmethod"]:
        value += "%s@%s\n" % (indent, value_type)

    if exposure_location == "below":
        value += create_expose(indent, exposure_type, inherit_flag)

    if exposure_location == "manual":
        extra += create_manual_expose(namespace, name, exposure_type, inherit_flag)

    value+="%sdef %s(" % (indent, name)
    if value_type == "classmethod":
        value+= "cls, "
    elif value_type == "method":
        value+= "self, "
    value += "x, y):\n"

    if value_form == "standard":
       value += "%s%sreturn x+y\n" % (indent, tab)
    if value_form == "generator":
       value += "%s%syield x+y\n" % (indent, tab)

    value += "\n"
    return value, extra

for value_type in value_types:
    value_forms = all_function_forms
    exposure_types = all_exposure_types
    if value_type in ["classmethod", "staticmethod"]:
        exposure_locations=["above", "below", "manual"]
    elif value_type ==  "property":
        value_forms = property_function_forms
        exposure_types = property_exposure_types
        exposure_locations=["below"] #Hard to expose properties manually.
    else:
        exposure_locations=["above", "manual"]

    for value_form in value_forms:
        for exposure_location in exposure_locations:
            if exposure_location == "manual":
                try:
                    #No difference between blank and empty
                    #exposure_types for manual
                    exposure_types.remove("blank")
                except ValueError:
                    pass
            for exposure_type in exposure_types:
                if exposure_type == "blank":
                    inherit_flags = ["noinherit"]
                else:
                    inherit_flags = ["noinherit", "inherit"]

                for inherit_flag in inherit_flags:
                    if value_type == "function":
                        namespace="global"
                        value, extra = \
                            create_value(namespace,
                                         value_type,
                                         value_form,
                                         exposure_type,
                                         inherit_flag,
                                         exposure_location)
                        namespaces[namespace]+=value
                        extra_stuff += extra
                        test_list.append([namespace, value_type, value_form, exposure_type, inherit_flag, exposure_location])

                    else:
                        for class_exposure_type in all_exposure_types:
                            if class_exposure_type == "blank":
                                class_inherit_flags = ["noinherit"]
                            else:
                                class_inherit_flags = ["noinherit", "inherit"]

                            for class_inherit_flag in class_inherit_flags:
                                namespace="foo_%s_%s" % (class_exposure_type, class_inherit_flag)
                                value, extra = \
                                    create_value(namespace,
                                                 value_type,
                                                 value_form,
                                                 exposure_type,
                                                 inherit_flag,
                                                 exposure_location)
                                namespaces[namespace]+=value
                                extra_stuff += extra
                                test_list.append([namespace, value_type, value_form, exposure_type, inherit_flag, exposure_location])

#Output globals:
output +=  namespaces["global"]

namespaces["global"]=[]
for class_exposure_type in all_exposure_types:
    if class_exposure_type == "blank":
        class_inherit_flags = ["noinherit"]
    else:
        class_inherit_flags = ["noinherit", "inherit"]

    for class_inherit_flag in class_inherit_flags:
        namespace="foo_%s_%s" % (class_exposure_type, class_inherit_flag)
        output += create_expose("", class_exposure_type, class_inherit_flag, class_exposure=True)
        output += "class %s(object):\n" % namespace
        output += namespaces[namespace]

output+="\n"
output+=extra_stuff
output+="""


class TestExposure(unittest.TestCase):

    def andf(self, boolean_list):
        return_value = True
        for value in boolean_list:
            return_value = return_value & value
        return return_value

    def orf(self, boolean_list):
        return_value = False
        for value in boolean_list:
            return_value = return_value | value
        return return_value

    @nottest
    def inherit_test(self, test_function, boolean_list):
        return test_function(boolean_list[:-1]) and boolean_list[-1]

    def create_truth_table(self, lock_list, class_lock_list, tester, class_tester ):
        table = []
        combined_lock_list=lock_list + class_lock_list
        table_size = 1 << len(combined_lock_list)
        for value in range(0, table_size):
            booleans = []
            shift_register = value
            for i in range(len(combined_lock_list)):
                booleans.insert(0, (shift_register & 1)==1)
                shift_register >>= 1
            entry=[]
            for i in range(len(combined_lock_list)):
                entry.append( (combined_lock_list[i], booleans[i]) )

            final_truth = tester(booleans[:len(lock_list)]) and class_tester(booleans[len(lock_list):])
            final_entry=( entry, final_truth )
            table.append( final_entry )
        return table

    @nottest
    def property_test(self, obj, name, expected):
        if expected == False:
            property_lock_get.unlocked = True
            property_lock_set.unlocked = True
            property_lock_del.unlocked = True
            valid = False
            try:
                obj._rpyc_setattr(name, "value")
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)

            valid = False
            try:
                obj._rpyc_getattr(name)
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)

            valid = False
            try:
                obj._rpyc_delattr(name)
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)
        else:
            property_lock_get.unlocked = False
            property_lock_set.unlocked = False
            property_lock_del.unlocked = False

            property_lock_set.unlocked = False
            valid = False
            try:
                obj._rpyc_setattr(name, "value")
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)
            property_lock_set.unlocked = True
            value = obj._rpyc_setattr(name, name)

            property_lock_get.unlocked = False
            property_lock_set.unlocked = False
            valid = False
            try:
                obj._rpyc_setattr(name, "value")
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)
            property_lock_set.unlocked = True
            obj._rpyc_setattr(name, name)

            property_lock_set.unlocked = False
            property_lock_get.unlocked = False
            valid = False
            try:
                obj._rpyc_getattr(name)
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)
            property_lock_get.unlocked = True
            value = obj._rpyc_getattr(name)
            self.assertEqual(value, name)

            property_lock_get.unlocked = False
            property_lock_del.unlocked = False
            try:
                obj._rpyc_delattr(name)
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)
            property_lock_del.unlocked = True
            obj._rpyc_delattr(name)
            property_lock_del.unlocked = False
            property_lock_get.unlocked = True
            value = obj._rpyc_getattr(name)
            self.assertEqual(value, "deleted") #del just sets this value
            property_lock_get.unlocked = False


    @nottest
    def field_test(self, obj, name, expected):
        if expected == False:
            valid = False
            try:
                obj._rpyc_getattr(name)
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)
        else:
            #Could be none, but won't be for any of the
            #classes we use.
            value = obj._rpyc_getattr(name)
            self.assertNotEqual(value, None)

    @nottest
    def callability_test(self, callable, value_form, expected):
        if expected == False:
            valid = False
            try:
                callable._rpyc_getattr("__call__")
            except SecurityAttrError:
                valid=True
            self.assertTrue(valid)
        else:
            #Could be none, but won't be for any of the
            #classes we use.
            value = callable._rpyc_getattr("__call__")(2,3)
            if value_form == "generator":
                #next proxy is an issue!!!! Currently this simply
                #won't work over remote..
                value = next(value)
            self.assertEqual(value, 5)

    def test_expose(self):
        test_list=[ \
"""
for test in test_list:
    output+=" "*12 + repr(test) + ",\n"

output+="""
        ]

        for test in test_list:
            namespace, value_type, value_form, exposure_type, inherit_flag, exposure_location=test

            #create the lock truth table for the test:
            test_function = self.andf
            if exposure_type == "blank":
                lock_list = []
            elif exposure_type == "empty":
                lock_list = []
            elif exposure_type == "lock":
                lock_list = [toggle_lock_a]
            elif exposure_type == "locklist":
                lock_list = [toggle_lock_a, toggle_lock_b]
            elif exposure_type == "locklistand":
                lock_list = [toggle_lock_a, toggle_lock_b]
            elif exposure_type == "locklistor":
                test_function = self.orf
                lock_list = [toggle_lock_a, toggle_lock_b]

            #If lock is inside class, you do not need to meet
            #inheritability checks to fetch it, just to call it
            fetch_lock_list = list(lock_list)
            fetch_test_function = test_function

            if inherit_flag == "inherit":
                test_function = functools.partial( self.inherit_test, test_function )
                lock_list.append(toggle_lock_c)

            class_test_function = self.andf
            if namespace != "global": #check fetching it from class and instance:
                #Figure out class locks:
                class_name, class_exposure_type, class_inherit_flag = namespace.split("_")
                if class_exposure_type == "blank":
                    class_lock_list = []
                elif class_exposure_type == "empty":
                    class_lock_list = []
                elif class_exposure_type == "lock":
                    class_lock_list = [toggle_lock_d]
                elif class_exposure_type == "locklist":
                    class_lock_list = [toggle_lock_d, toggle_lock_e]
                elif class_exposure_type == "locklistand":
                    class_lock_list = [toggle_lock_d, toggle_lock_e]
                elif class_exposure_type == "locklistor":
                    class_test_function = self.orf
                    class_lock_list = [toggle_lock_d, toggle_lock_e]

                if class_inherit_flag == "inherit":
                    class_test_function = functools.partial( self.inherit_test, class_test_function )
                    class_lock_list.append(toggle_lock_f)
            else:
                class_lock_list=[]
            truth_table = self.create_truth_table(fetch_lock_list, class_lock_list,
                                                  fetch_test_function, class_test_function)

            name = get_name(value_type, value_form, exposure_type, inherit_flag, exposure_location)

            if namespace != "global": #check fetching it from class and instance:
                cls = globals()[namespace]
                instance = cls()

                #This is used for some inherit locks.
                for truth_lock_list, final_truth in truth_table:
                    for (tlock,setting) in truth_lock_list:
                        tlock.unlocked = setting

                    cls_final_truth=final_truth
                    if value_type in ["method", "property"]:
                        cls_final_truth = False #We do not allow calls to methods from class
                                                #when we expose them because they become
                                                #unbound to class
                    if value_type == "property":
                        self.property_test(cls, name, cls_final_truth)
                        self.property_test(instance, name, final_truth)
                    else:
                        self.field_test(cls, name, cls_final_truth)
                        self.field_test(instance, name, final_truth)

            if value_type == "property":
                continue #No need to do callability tests.
            #Prepare for callability tests.
            if namespace != "global":
                #Alright, grab a copy for the next test.
                toggle_lock_a.unlocked = True
                toggle_lock_b.unlocked = True
                toggle_lock_c.unlocked = True
                toggle_lock_d.unlocked = True
                toggle_lock_e.unlocked = True
                toggle_lock_f.unlocked = True
                if value_type == "method":
                    grabbed_from_cls = None
                else:
                    grabbed_from_cls = cls._rpyc_getattr(name)
                grabbed_from_instance = instance._rpyc_getattr(name)
            else:
                grabbed_from_cls = None
                grabbed_from_instance = globals()[name]

            #Alright, now test callability--this
            #bypasses class locks
            truth_table = self.create_truth_table(lock_list, [],
                                                  test_function, self.andf)

            for truth_lock_list, final_truth in truth_table:
                for (tlock,setting) in truth_lock_list:
                    tlock.unlocked = setting

                if grabbed_from_cls is not None:
                    self.callability_test(grabbed_from_cls, value_form, final_truth)
                self.callability_test(grabbed_from_instance, value_form, final_truth)

"""

#output has been created. Time to exec the code
#should be found by the unit tester.
exec(output)

if __name__ == "__main__":
    unittest.main()


