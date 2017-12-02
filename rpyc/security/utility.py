"""
The :mod:`rpyc.security.util` contains routines used to
query :ref:`RPyC Exposed<api-security-rpyc-exposed>` objects.
"""

from rpyc.security import exceptions

def check_restricted(value):
    """Checks to see if ``value`` is a `RPyC Exposed` value.

    :param value: Value to see if `RPyC Exposed` object.
    :return: ``True`` if it a `RPyC Exposed` object, ``False`` otherwise.
    :raises rpyc.security.exceptions.SecurityWrapError:
       if the  object is an `RPyC Exposed` value but it has been
       wrapped by another proxy/wrapper of some kind, such
       as :ref:`netref <api-netref>` or
       :func:`restricted <rpyc.utils.helpers.restricted>`.
    """
    try:
        #This checks also to see if the value
        #has been wrapped by another wrapper.
        if (value._rpyc__restricted__ != id(value)):
            raise exceptions.SecurityWrapError("RPYC restricted object "
                + "has been wrapped, or proxied by another.")
        return True
    except AttributeError:
        return False

#The difference between check_restricted and this
#is that check_restricted can throw a security
#wrap error.
def is_restricted(value):
    """
    Checks to see if value is a `RPyC Exposed` value.

    :param value: Value to see if `RPyC Exposed` object.
    :return bool: ``True`` if it a `RPyC Exposed` object, ``False``
        otherwise.

    The difference between this and
    :func:`check_restricted()  <rpyc.security.restrictor.check_restricted>`
    is that this version will return False rather than throwing a
    :class:`SecurityWrapError <rpyc.security.exceptions.SecurityWrapError>`
    """

    try:
        return check_restricted(value)
    except exceptions.SecurityWrapError:
        return False

def unwrap(value):
    """
    Returns the unwrapped, non `RPyC Exposed` original version of
    ``value``.

    :param value: Value that may or may not be `RPyC Exposed`
    :return: The unwrapped non-`RPyC Exposed` version of value.

    This will not work remotely unless
    :attr:`value._rpyc__unwrapped__ <rpyc_exposed._rpyc__unwrapped__>`
    is exposed. Generally it shouldn't be exposed for security reasons.
    """
    try:
        return value._rpyc__unwrapped__
    except AttributeError:
        return value

def get_olp(value):
    """
    Gets the
    :class:`object lock profile<rpyc.security.lock_profiles.LockProfile>`
    associated with a `RPyC Exposed` value.

    :param value: Value that has been `RPyC Exposed`
    :return: The **olp** associated with that value.

    Locally this will generally return a modifiable
    copy of the associated **olp**. Remotely, it will
    return
    :meth:`olp.read_only_copy() <rpyc.security.lock_profiles.LockProfile.read_only_copy>`
    """
    try:
        return value._rpyc__olp__
    except AttributeError:
        raise ValueError("No olp found for value")

def rpyc_type(value):
    """
    Gets the original type of a `RPyC Exposed` value, or
    type(value) if value is not `RPyC Exposed`.

    :param value: Value that may or may not be `RPyC Exposed`
    :return: The non `RPyC Exposed` type for value.

    This is an analog for the Python :func:`type` function for
    `RPyC Exposed` objects.

    This will not work remotely unless
    :attr:`value._rpyc__unwrapped__ <rpyc_exposed._rpyc__unwrapped__>`
    is exposed. Generally it shouldn't be exposed for security reasons.
    """
    return type(unwrap(value))

def rpyc_isinstance(instance, cls):
    """
    Determines if ``instance`` is an instance of ``cls``, even if
    ``instance`` is an `RPyC exposed` instance of a type that does
    not :ref:`work properly <api-security-rpyc-exposed-isinstance>`
    with Python's :func:`isinstance`

    :param instance: instance that may or may not be `RPyC Exposed`
    :param cls: class to check if instance is an instance of
    :return: True if ``instance`` is and instance of ``cls``

    This is an analog for the Python :func:`isinstance` function
    that works with certain problematic `RPyC Exposed` objects.

    This will not work remotely unless
    :attr:`value._rpyc__unwrapped__ <rpyc_exposed._rpyc__unwrapped__>`
    is exposed. Generally it shouldn't be exposed for security reasons.
    """
    return issubclass(rpyc_type(instance), cls)

def rpyc_issubclass(cls, other_cls):
    """
    Determines if ``cls`` is a subclass of ``other_cls``,
    even if ``cls`` is an `RPyC exposed` class that
    does not :ref:`work properly <api-security-rpyc-exposed-isinstance>`
    with Python's :func:`issubclass`

    :param cls: class to check to see if subclass. May or may not be
        `RPyC Exposed`
    :param other_cls: class to check against. May or may not be
        `RPyC Exposed`
    :return: True if ``cls`` is a subclass ``other_cls``

    This is an analog for the Python :func:`issubclass` function
    that works with certain problematic `RPyC Exposed` objects.

    This will not work remotely unless
    :attr:`value._rpyc__unwrapped__ <rpyc_exposed._rpyc__unwrapped__>`
    is exposed. Generally it shouldn't be exposed for security reasons.
    """
    return issubclass(unwrap(cls), other_cls)


