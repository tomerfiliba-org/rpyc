.. _documentation:

Documentation
=============

Introduction
------------

.. toctree::
   :maxdepth: 1
   :hidden:

   docs/about
   docs/theory
   docs/howto
   docs/usecases
   docs/guidelines
   docs/capabilities


* :ref:`A little about RPyC <about>` - related projects, contributors, and
  logo issues

* :ref:`Theory of Operation <theory>` - background on the inner workings of
  RPyC and the terminology

* :ref:`Use cases <use-cases>` - some common use-cases, demonstrating the power
  and ease of RPyC

* :ref:`How to's <howto>` - solutions to specific problems

* :ref:`Guidelines <guidelines>` - guidelines for improving your work with RPyC

Reference
---------

.. toctree::
   :maxdepth: 1
   :hidden:

   docs/servers
   docs/classic
   docs/services
   docs/async
   docs/security
   docs/secure-connection
   docs/zerodeploy
   docs/splitbrain


* :ref:`Servers <servers>` - using the built-in servers and writing custom ones

* :ref:`Classic RPyC <classic>` - using RPyC in *slave mode* (AKA *classic
  mode*), where the client has unrestricted control over the server.

* :ref:`RPyC Services <services>` - writing well-defined services which restrict
  the operations a client (or server) can carry out.

* :ref:`Asynchronous Operation <async>` - invoking operations in the background,
  without having to wait for them to finish.

* :ref:`Security Concerns <security>` - keeping security in mind when using
  RPyC

* :ref:`Secure Connections <ssl>` - create an encrypted and authenticated
  connection over SSL or SSH

* :ref:`Zero-Deploy <zerodeploy>` - spawn temporary, short-lived RPyC server on remote
  machine with nothing more than SSH and a Python interpreter

* :ref:`Splitbrain Python <splitbrain>` - run code locally, but have all OS-level operations
  take place on the server machine. A killer feature for debugging and automated testing!





