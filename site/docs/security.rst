.. _security:

Security
========
Operating over a network always involve a certain security risk, and requires some awareness. 
RPyC is believed to be a secure protocol -- no incidents have been reported since version 3 was
released. Version 3 was a rewrite of the library, specifically written with security in mind. 
It dropped the use of ``pickle``, added security-oriented configuration parameters, and generally 
attempts to never send more information than required. So I daresay RPyC itself is secure.

However, RPyC is also the perfect backdoor! It's not RPyC itself that matters -- it's what
you do with it. 

Classic Mode
------------
The classic mode (``SlaveService``) is **intentionally insecure** -- in this mode, the server
will expose everything (all modules and attributes) to the client -- you can think of the client
as the master and the server being the slave. Therefore, only ever expose a classic mode server
over secure, local networks.


Configuration Parameters
------------------------


Services
--------



What to Expose
--------------
