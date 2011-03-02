#!/usr/bin/env python
import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2, 4):
    sys.exit("requires python 2.4 and up")


setup(name="RPyC",
    version = "$$RPYC_VERSION$$",
    description = "Remote Python Call (RPyC), a transparent and symmetric RPC library",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    license = "MIT",
    url = "http://rpyc.wikidot.com",
    download_url = "http://sourceforge.net/projects/rpyc/files/main/__MAJOR__.__MINOR__.__REVISION__",
    packages = [
        'rpyc', 
        'rpyc.core', 
        'rpyc.utils', 
    ],
    scripts = [
        "servers/classic_server.py",
        "servers/registry_server.py",
        "servers/vdbconf.py",
    ],
    package_dir = {
        '' : 'src',
    },
    platforms = ["POSIX", "Windows"],
    long_description = ("A symmetric library for transparent RPC, clustering and "
        "distributed computing for python, built around the concept of remote "
        "services and object proxying"),
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Object Brokering",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Clustering",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
)


