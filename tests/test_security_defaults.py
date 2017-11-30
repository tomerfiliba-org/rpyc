
import unittest
from rpyc.security import lock_profiles
from rpyc.security import locks
from rpyc.security.defaults import default_profiles

class TestDefaults(unittest.TestCase):
    def test_default_properties(self):
        blank_olp = lock_profiles.LockProfile()
        def stupid_hook(value, lock_list):
            self.assertEqual(lock_list, [locks.BLOCKED])
            return blank_olp

        for property_type in ["class", "instance", "routine", "routine_descriptor", "generator", "coroutine"]:
            #TEST routine_expose/closure_exposed/coroutine_exposed
            property = property_type + "_exposed"
            old_value = getattr(default_profiles, property)
            #one of the following will be in a proper list
            self.assertTrue( ("__module__" in old_value) or ("__dir__" in old_value) )

            valid = False
            try:
                setattr(default_profiles, property, None)
            except ValueError:
                valid = True
            self.assertTrue(valid)

            valid = False
            try:
                setattr(default_profiles, property,
                       ["test", "hello", "%@%##%"])
            except ValueError:
                valid = True
            self.assertTrue(valid)

            new_list=["hello", "__foo__"]
            setattr(default_profiles, property, new_list)
            self.assertEqual(getattr(default_profiles, property), new_list)

            #Restore original property (or at least copy of).
            setattr(default_profiles, property, old_value)

            """
            #TEST create_*_olp_hook properties
            hook = "create_%s_olp_hook" % property_type

            default_hook = getattr(default_profiles, hook)
            default_name= "default_"+hook
            self.assertEqual(default_hook,
                          getattr(default_profiles, default_name))
            create_name = "create_"+property_type+"_olp"
            create_function = getattr(default_profiles, create_name)

            olp = create_function(None, [])
            for item in old_value:
                self.assertTrue(item in olp.getattr_locks)

            #Check the sanitiziation.
            valid = False
            try:
                setattr(default_profiles, hook, None)
            except ValueError:
                valid = True
            self.assertTrue(valid)

            setattr(default_profiles, hook, stupid_hook)
            new_hook = getattr(default_profiles, hook)
            olp = new_hook(None, [locks.BLOCKED])
            self.assertIs(olp, blank_olp)
            olp = create_function(None, [locks.BLOCKED])
            self.assertIs(olp, blank_olp)

            #Restore original hook
            setattr(default_profiles, hook, default_hook)
            """

if __name__ == "__main__":
    unittest.main()


