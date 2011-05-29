.. toctree::
   :hidden:
   
   license
   changelog

Installing
==========
RPyC ::

  easy_install rpyc

or ::
  
  pip install rpyc


Download
--------
You can always download the latest releases of RPyC from the `sourceforge page
<http://sourceforge.net/projects/rpyc/files/>`_ or the project's `PyPI page
<http://pypi.python.org/pypi/RPyC>`_. 


Dependencies
------------
* TLSLite - required for tlslite support 

  * PyCrypto - if installed, will speed up ``tlslite``
  * PyOpenSSL - if installed, will speed up ``tlslite`` 
  
* SSH client - required for RPyC-over-SSH 
* PyWin32 - required for PipeStream on Windows
* SSL wrapper - required for SSL support on python prior to v2.5 
* zlib - required for IronPython prior to v2.7



