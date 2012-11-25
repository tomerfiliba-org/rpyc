#!/usr/bin/env python
import sys
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2, 4):
    sys.exit("requires python 2.4 and up")

here = os.path.dirname(__file__)
exec(open(os.path.join(here, 'rpyc', 'version.py')).read())

setup(name = "rpyc",
    version = version_string, #@UndefinedVariable
    description = "Remote Python Call (RPyC), a transparent and symmetric RPC library",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    license = "MIT",
    url = "http://rpyc.sourceforge.net",
    download_url = "http://sourceforge.net/projects/rpyc/files/main/%s" % (version_string,), #@UndefinedVariable
    packages = [
        'rpyc',
        'rpyc.core',
        'rpyc.lib',
        'rpyc.utils',
        'rpyc.scripts'
    ],
    scripts = [
        os.path.join("rpyc", "scripts", "rpyc_classic.py"),
        os.path.join("rpyc", "scripts", "rpyc_registry.py"),
    ],
    entry_points = dict(
        console_scripts = [
            "rpyc_classic = rpyc.scripts.rpyc_classic:main",
            "rpyc_registry = rpyc.scretips.rpyc_registry:main",
        ],
    ),
    platforms = ["POSIX", "Windows"],
    use_2to3 = False,
    zip_safe = False,
    long_description = open(os.path.join(here, "README.rst"), "r").read(),
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
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

