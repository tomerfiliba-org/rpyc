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

sed -e "s/__MAJOR__/$1/" -e "s/__MINOR__/$2/" -e "s/__REVISION__/$3/" -e "s/__DATE__/`date '+%d %b %Y'`/" ___init__.py > __init__.py
sed -e "s/__MAJOR__/$1/" -e "s/__MINOR__/$2/" -e "s/__REVISION__/$3/" -e "s/__PACKAGE_NAME__/rpyc/" _setup.py > setup.py
sed "s/__YEAR__/`date +%Y`/" _license.py > license.py

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

python setup.py bdist_wininst --plat-name=win32 > /dev/null
if [ $? -ne 0 ]; then
    echo "!! creating windows install failed !!"
    exit 1
fi

python2.5 setup.py bdist_egg > /dev/null
if [ $? -ne 0 ]; then
    echo "!! creating python2.5 egg failed !!"
    exit 1
fi

python2.6 setup.py bdist_egg > /dev/null
if [ $? -ne 0 ]; then
    echo "!! creating python2.6 egg failed !!"
    exit 1
fi

if [ "$is_final" = "yes" ]; then
    echo "registering on pypi"
    sed -e "s/__MAJOR__/$1/" -e "s/__MINOR__/$2/" -e "s/__REVISION__/$3/" -e "s/__PACKAGE_NAME__/RPyC/" ../_setup.py > setup.py
    
    python setup.py register
    if [ $? -ne 0 ]; then
        echo "!! registering on pypi failed !!"
        exit 1
    fi
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

echo "=============== created the following files ================"
find dist -type f 
echo 

##############################################################################
# continue only if this is a final build
##############################################################################
if [ "$is_final" != "yes" ]; then
    exit 0
fi

##############################################################################
# tag in git
##############################################################################
git tag -a -f -m "release $1.$2.$3 (`date +%Y%m%d%H%M%S`)" $1.$2.$3
if [ $? -ne 0 ]; then
    echo "!! git tag failed !!"
    exit 1
fi

git push --tag
if [ $? -ne 0 ]; then
    echo "!! pushing tag failed !!"
    exit 1
fi



