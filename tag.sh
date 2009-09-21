if [ $# -lt 1 ] 
then
        echo "usage: $0 <version string>"
        exit 1
fi

svn copy https://sebulbasvn.googlecode.com/svn/trunk/rpyc https://sebulbasvn.googlecode.com/svn/tags/rpyc/$1 -m "tagging release"
