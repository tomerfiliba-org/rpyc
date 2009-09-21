#!/bin/sh

if [ $# -lt 3 ] 
then
    echo "usage: `basename $0` major minor revision [is_final]"
    echo "    where 'is_final' is 'yes' or 'no' (default 'no')"
    exit 1
fi

is_final=$4

rm -rf dist
mkdir dist

##############################################################################
# embed version string
##############################################################################
rm -f __init__.py
rm -f setup.py

sed "s/__MAJOR__/$1/" ___init__.py | sed "s/__MINOR__/$2/" | sed "s/__REVISION__/$3/" > __init__.py
sed "s/__MAJOR__/$1/" _setup.py | sed "s/__MINOR__/$2/" | sed "s/__REVISION__/$3/" > setup.py

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
python setup.py sdist --formats=zip,gztar > /dev/null
if [ $? -ne 0 ]; then
    echo "!! creating python packages failed !!"
    exit 1
fi

python setup.py bdist_wininst > /dev/null

if [ $? -ne 0 ]; then
    echo "!! creating windows install failed !!"
    exit 1
fi

python setup.py bdist_egg > /dev/null

if [ $? -ne 0 ]; then
    echo "!! creating egg failed !!"
    exit 1
fi

cd ..
mv build/dist/* dist

##############################################################################
# create development tar
##############################################################################
DEVTARNAME=rpyc-snapshot-`date +%Y%m%d%H%M%S`
rm -rf build
mkdir build
mkdir build/$DEVTARNAME

cp * build/$DEVTARNAME 2> /dev/null
cp -r core build/$DEVTARNAME/ 2> /dev/null
cp -r demos build/$DEVTARNAME/
cp -r servers build/$DEVTARNAME/
cp -r tests build/$DEVTARNAME/
cp -r utils build/$DEVTARNAME/
cd build
find . -name "*.pyc" | xargs rm
find . -name ".svn" | xargs rm -rf
tar czf $DEVTARNAME.tar.gz $DEVTARNAME/

if [ $? -ne 0 ]; then
    echo "!! creating tarball failed !!"
    exit 1
fi

cd ..
mv build/$DEVTARNAME.tar.gz dist
rm -rf build

##############################################################################
# continue only if this is a final build
##############################################################################
echo "created the following files:"
find dist -type f 

if [ "$is_final" != "yes" ]; then
    exit
fi

echo "tagging in svn"

##############################################################################
# tag in svn
##############################################################################
svn commit -m "building of $1.$2.$3"

echo "removing previous svn tag"
svn rm https://sebulbasvn.googlecode.com/svn/tags/rpyc/$1.$2.$3 -m "tagging release"
echo "creating svn tag"
svn copy https://sebulbasvn.googlecode.com/svn/trunk/rpyc https://sebulbasvn.googlecode.com/svn/tags/rpyc/$1.$2.$3 -m "tagging release"

if [ $? -ne 0 ]; then
    echo "!! creating svn tag failed !!"
    exit 1
fi

##############################################################################
# upload to sourceforge 
##############################################################################
echo "uploading to sourceforge"
scp dist/* gangesmaster@frs.sourceforge.net:uploads




