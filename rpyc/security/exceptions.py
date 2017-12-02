"""
Security Exceptions
"""

class SecurityError(Exception):
    """Placeholder"""
    pass

#fail_locks is a list of locks that we couldn't
#open that may have progressed us towards the object being
#accessible.
#
#It can be empty in a few cases (there are no locks, or you accessed
#a magic attribute, etc.)

#access_attrs is a dictionary
#it contains the following:
# access -- "getattr"/"setattr"/"delattr"
# instance -- the object from which the above access was attempted
# attribute -- the name of the attribute accessed. IE instance.attribute
# wildcard -- None, "*", or "!" depending if error happened during
#             wildcard access.
#
#fault signifies that the security checked failed not due to
#a normal security error, but because a locklist, lock, or object
#behaved badly. -- most commonly they didn't return the correct object
#or repr on them throws an exception.
#
#These must be attribute errors for getattr code to work properly.
#this does mean that code that catches attribute errors will
#catch these exceptions. That seems appropriate.
class SecurityAttrError(AttributeError, SecurityError):
    def __init__(self, message, fail_locks, attr_args, fault = False):
        super().__init__(message)
        self.fail_locks = fail_locks
        self.attr_args = attr_args
        self.fault = fault

#This error is only used when check_restricted detects
#that a restricted object has been wrapped up inside
#another wrapper/proxy.
class SecurityWrapError(SecurityError):
    pass

