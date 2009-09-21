#!/bin/sh
rm -rf dist
mkdir dist

##############################################################################
# create installers
##############################################################################
rm -rf build
mkdir build
mkdir build/rpyc

cp README build
cp setup.py build
cp __init__.py build/rpyc
cp license.py build/rpyc
cp -r core build/rpyc/
cp -r servers build/rpyc/
cp -r utils build/rpyc/

cd build
find . -name "*.pyc" | xargs rm
python setup.py sdist --formats=zip,gztar
python setup.py bdist_wininst

cd ..
mv build/dist/* dist

##############################################################################
# create development tar
##############################################################################
DEVTARNAME=rpyc-`date +%Y%m%d%H%M%S`-dev
rm -rf build
mkdir build
mkdir build/$DEVTARNAME

cp * build/$DEVTARNAME
cp -r core build/$DEVTARNAME/
cp -r demos build/$DEVTARNAME/
cp -r servers build/$DEVTARNAME/
cp -r tests build/$DEVTARNAME/
cp -r utils build/$DEVTARNAME/
cd build
find . -name "*.pyc" | xargs rm
find . -name ".svn" | xargs rm -rf
tar czf $DEVTARNAME.tar.gz $DEVTARNAME/

cd ..
mv build/$DEVTARNAME.tar.gz dist
rm -rf build
