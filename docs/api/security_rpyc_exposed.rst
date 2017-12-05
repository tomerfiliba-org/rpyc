.. _api-security-rpyc-exposed:

`RPyC Exposed` Objects
======================

Within the :ref:`rpyc.security <api-security>` module there exists the 
concept of creating `RPyC Exposed` objects.

These are proxied Python objects that are wrapped to allow 
remote access, but only to specific attributes of the object.

They work very similarly to how :func:`restricted <rpyc.utils.helpers.restricted>` 
objects do, but are more powerful. 

They are created at a low level via use of the
:class:`SecurityRestrictor <rpyc.security.restrictor.SecurityRestrictor>`
class but can also be made multiple ways using the :mod:`rpyc.security` API. They
most commonly should be created using the 
:func:`@expose <rpyc.security.exposer.expose>` decorator. IE::

    >>> from rpyc.security.exposer import expose
    >>> @expose
    ... class Foo:        
    ...     pass
    ... 
    >>> class Bar:
    ...     pass
    ...
    >>> print(Foo)
    <class '__main__.Foo' (RPyC exposed)>
    >>> print(Bar)
    <class '__main__.Bar'>
    >>> print(Foo())
    <__main__.Foo object at 0x7f0dcff2e668 (RPyC exposed)>
    >>> print(Bar())
    <class '__main__.Bar'>
    <main__.Bar object at 0x7f0dcff2e5f8>

As can be seen here, `RPyC Exposed` classes and instances are specially marked 
when :func:`repr` is called on them by default.

In general `RPyC Exposed` values behave exactly like their underlying object
with a few exceptions:

    * When your :func:`repr` them they will show that they are "RPyC exposed". (You
      can turn this off for instances, but not for classes).

    * :meth:`_rpyc_getattr`, :meth:`_rpyc_setattr`, and
      :meth:`_rpyc_delattr` methods are added  to the value. If you create
      a `RPyC Exposed` object from any object that has already 
      defined one or more of these methods, they will be called within
      the new :meth:`_rpyc_???attr` definitions.

    * Only certain attributes are accessible via the :meth:`rpyc_???attr` methods, 
      and only in specific ways. The specific attributes exposed are determined
      by an object lock profile (:class:`OLP <rpyc.security.olps.OLP>`).

    * Classes that use metaclasses *may* not get wrapped properly when 
      `RPyC Exposed`. Classes that use metaclasses should probably 
      handle exposure manually via the :meth:`_rpyc_???attr` methods.

    * :func:`isinstance` and :func:`issubclass` will generally work normally, but
      will break for certain degenerate cases.

    * Multiple inheritance of multiple `RPYC exposed` classes can cause
      a metaclass conflict. There are simple ways to deal with this.

    * There are special magic attributes defined that you can get via 
      :func:`getattr` or a :meth:`_rpyc_getattr` call. These are always 
      prefixed with "_rypc__" and end with "__", similar to hom Python magic
      methods are prefixed with "__" and end with "__".

The RPyC protocol will always use the :meth:`rpyc_???attr` methods to access
an object if they exist. Therefore only what is exposed by those methods will
be exposed remotely.

Simultaneous Class and Instance Definition
==========================================

Whenever a `RPyC Exposed` object is created, a definition for both
the class and instance are created. Instantiating a `RPyC Exposed` class
will create a `RPyC Exposed` instance.  Similarly, the :attr:`__class__` 
attribute of a `RPyC Exposed` instance will return a `RPyC Exposed`
class.

This is done for multiple reasons:
    * To make the wrapping of multiple objects more seamless.

    * So that you can pass classes to other pieces of 
      code and have them instantiate exposed objects without
      requiring modification.

    * The policy for access of attributes on the class 
      and instance are individually controllable, but the 
      :class:`OLP` definition for both ends up in one place. 

The last point is important--in general you'd want to do things
like expose a standard method call on instance, but not expose the same method
accessed from the class. If you access the class version of the method, you can
spoof in any value for `self`. However it still is convenient to associate 
the definition for instance and class exposure with the class definition.

It is still possible to have two different objects of the same class have two
different security policies.  However, in that case, each will have their own 
`RPyC Exposed` class returned by their :attr:`__class__` attribute.

.. _api-security-rpyc-exposed-isinstance:

:func:`isinstance` and :func:`issubclass` Limitation
====================================================

:func:`isinstance` and :func:`issubclass` generally will just work.
However, they are problematic for proxies of classes that Python
prohibits inheritance of. These are all special Python internally 
defined classes. IE::

    def foo(self):
        pass

    class A(foo.__class__):
        pass

This throws a `TypeError` in Python because the function class is not
inheritable. Unfortunately this means that
``isinstance( expose(foo), foo.__class__ )`` will fail. This
is a hard language limitation.

Inheritance
===========

There are several caveats having to do with class inheritance of `RPyC
Exposed` classes

Proxy Stripping
---------------

When you inherit a `RPyC Exposed` class locally the `RPyC Exposed`
proxy wrapping is removed via metaclass magic.

Therefore the new class will not be a `RPyC Exposed` class at all. This is by
design.  

Object Lock Profile Inheritance
-------------------------------

If you do wish to inherit the :class:`OLP` restrictions from one class
to another class, you may do so via the alternate mechanism of the
``inherit`` argument of the  :func:`@expose <rpyc.security.exposer.expose>` decorator.

Remote Inheritance
------------------

Python inheritance of `RPyC Exposed` classes on the remote side over a 
:ref:`netref <api-netref>` wll not work at all.

Multiple `RPyC Exposed` Inheritance
--------------------------------------

Unfortunately, inheriting from two `RPyC Exposed` classes will cause
a problem::

    @expose
    class A:
        pass
    
    @expose
    class B:
        pass
    
    class C(A, B):
        pass

Will yield the error::

    TypeError: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases

The solution is to allow only one `RPyC Exposed` class to be inherited.
You can use the :func:`unwrap() <rpyc.security.utility.unwrap>` function
if necessary.

Magic Attributes
================

`RPyC exposed` values have the following magic attributes:

.. attribute:: rpyc_exposed._rpyc__exposed__

This is set to `id(rpyc_exposed)` at the time of the wrapping.
The value is an id rather than a simple boolean, such that
one can detect whether the value has been wrapped or 
otherwise proxied further in some way (such as via netref).

This magic attribute is always accessible, regardless of
whatever else may or may not be exposed.

Normally you should use the
:func:`check_exposed() <rpyc.security.utility.check_exposed>`
or :func:`is_exposed() <rpyc.security.utility.is_exposed>` functions
rather than using this attribute directly.

.. attribute:: rpyc_exposed._rpyc__unwrapped_id__

This is the id of the original object that has been
proxied, before it was wrapped to become a `RPyC exposed`
object.

This magic attribute is always accessible, regardless of
whatever else may or may not be exposed. It is used 
internally.

.. attribute:: rpyc_exposed._rpyc__olp__

This is set to the 
:class:`OLP <rpyc.security.olps.OLP>`
associated with ``rpyc_exposed``. The value returned will
be   special read only copy if accessed via :meth:`_rpyc_getattr`
rather than via :func:`getattr` means.

This magic attribute is always accessible, regardless of
whatever else may or may not be exposed.

Normally you should use the 
:func:`get_olp() <rpyc.security.utility.get_olp>`
function rather than accessing this attribute directly.

.. attribute:: rpyc_exposed._rpyc__unwrapped__

This returns the original non-`RPyC exposed`
object that is being wrapped.

This magic attribute cannot be accessed via 
:meth:`_rpyc_getattr` unless specifically exposed by 
the :class:`OLP` for security reasons.

Normally you should use the 
:func:`unwrap() <rpyc.security.utility.unwrap>`
function rather than accessing this attribute directly.


