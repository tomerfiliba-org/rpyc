"""
These are exceptions associated with the :mod:`rpyc.security` modules.

These exceptions will serialize via :ref:`api-vinegar`, and are
used to signify security errors when accessing `RPyC Exposed` values.
"""

class SecurityError(Exception):
    """This is the base exception for all SecurityErrors

    It is also used directly for some security errors.
    It has the same interface as the Python
    :class:`Exception` type.
    """
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
    """This is used whenever an illegal attribute access
    is done. It also inherits from AttributeError so
    that it can safely be used with :meth:`__getattr__` and
    :meth:`__getattribute__` Python magic methods.

    Python first looks at :meth:`__getattr__` and if an
    :exc:`AttributeError` is thrown it then looks at
    :meth:`__getattribute__`. If any other exception type is thrown it
    aborts the process altogether.

    :param str message: Error message.
    :param list fail_locks: :class:`list` of :func:`str` representations
        of :class:`Lock <rpyc.security.locks.Lock>`
        items that blocked access.
    :param attr_args: Same as the ``**kwargs`` passed to
        :class:`Lock <rpyc.security.locks.Lock>` instances when
        calling
        :meth:`Lock.permitted <rpyc.security.locks.Lock.permitted>`
    :param fault: This will be ``False`` if things processed normally
        during checking locks. It will be ``True`` if something
        unusual happened that would qualify as some type of error.

    The ``attr_args`` will be set as follows:
        * ``attr_args["access"]`` will be one of "getattr","setattr", or "delattr"

        * ``attr_args["instance"]`` will be the original instance
          (not the `RPyC Exposed` version)

        * ``attr_args["attribute"]`` will be the name of the attribute
          being accessed

        * ``attr_args["value"]`` will be present if
          ``attr_args["access"]=="setattr"``. It will be the value
          being set.

        * ``attr_args["wildcard"]`` will be ``None`` when not using wildcards.
          Otherwise, it will be the wildcard in the
          :class:`OLP <rpyc.security.olps.OLP>`
          that :class:`Lock` is being evaluated on.


    The parameters ``fail_locks``, ``attr_args``, and ``fault`` are stored
    as attributes of the same name for the exceptions, and may be retrieved
    to determine the cause of failure. The message may be retrieved by using
    :func:`str` on the exception.
    """
    def __init__(self, message, fail_locks, attr_args, fault = False):
        super(SecurityAttrError, self).__init__(message)
        self.fail_locks = fail_locks
        self.attr_args = attr_args
        self.fault = fault

#This error is only used when check_exposed detects
#that an exposed object has been wrapped up inside
#another wrapper/proxy.
class SecurityWrapError(SecurityError):
    """This is a simple exception that inherits from
    SecurityError. It has the same interface as the Python
    :class:`Exception` type. It is used by
    :func:`check_exposed <rpyc.security.utility.check_exposed>`
    to signify that something has proxied a
    `RPyC Exposed` value.
    """
    pass
