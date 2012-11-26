v3.2.3
^^^^^^
* Guy Rozendorn - backported lots of fixes from 3.3 branch
* Alon Horev - UNIX domain socket patch

v3.2.2
^^^^^^
* Rotem Yaari - Add logging of exceptions to the protocol layer, investigate ``EINTR`` issue
* Anselm Kruis - Make RPyC more introspection-friendly
* Rüdiger Kessel - SSH on windows patch

v3.2.1
^^^^^^
* Robert Hayward - adding missing import
* `pyscripter <https://github.com/pyscripter>`_ - investigating python 3 incompatibilities
* `xanep <https://github.com/xanep>`_ - handling ``__cmp__`` correctly

v3.2.0
^^^^^^
* Alex - IPv6 support
* Sponce - added the ``ThreadPoolServer``, several fixes to weak-references and 
  ``AsyncResult``
* Sagiv Malihi - Bug fix in classic server
* Miguel Alarcos - issue `#8 <https://github.com/tomerfiliba/rpyc/issues/8>`_
* Pola Abram - Discovered several races when server threads trerminate
* Chris - Several bug fixes (#46, #49, #50)

v3.1.0
^^^^^^
* Alex - better conventions, Jython support
* Fruch - testing, benchmarking
* Eyecue - porting to python3
* Jerome Delattre - IronPython support
* Akruis - bug fixes

v3.0.0-v3.0.7
^^^^^^^^^^^^^
* Noam Rapahel - provided the original Twisted-integration with RPyC.
* Gil Fidel - provided the original NamedPipeStream on Windows.
* Eyal Lotem - Consulting and spiritual support :)
* Serg Dobryak - backporting to python 2.3
* Jamie Kirkpatrick - patches for the registry server and client
