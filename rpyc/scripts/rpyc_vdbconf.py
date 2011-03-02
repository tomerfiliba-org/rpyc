#! /usr/bin/env python
"""%prog <filename> [options]

A simple configurator for tlslite's verifier databases (VDB), which allows you to: 
 1) list the usernames in a given vdb file
 2) add / modify a username in the given vdb file
 3) delete an existing username from the vdb file

Examples:
    vdbconf <filename> -l               : list all users in `filename`
    vdbconf <filename> -a <username>    : add/replace `username` in `filename`
    vdbconf <filename> -d <username>    : delete `username` from `filename`

SECURITY NOTE: 
Make sure the vdb file has the correct write permissions!
"""
import sys
import getpass
from optparse import OptionParser 
from rpyc.utils.authenticators import VdbAuthenticator


parser = OptionParser(usage = __doc__)
parser.add_option("-l", "--list", action="store_true", dest="listonly", 
    default=False, help="List usernames and exit")
parser.add_option("-a", "--add", action="store", dest="add", metavar="USERNAME", 
    default=None, help="Set the given username (required for -d or adding)")
parser.add_option("-d", "--delete", action="store", dest="delete", metavar="USERNAME", 
    default=None, help="Deletes the given username")

def get_options():
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("Missing filename!")
    if options.add and options.delete:
        parser.error("Options -a and -d are mutually exclusive!")
    
    options.filename = args[0]
    return options

def list_users(vdb, options):
    users = sorted(vdb.list_users())
    if not users:
        print "No users defined in %s:" % (options.filename,)
    else:
        print "Existing users in %s:" % (options.filename,)
        for user in users:
            print "  %s" % (user,)

def del_user(vdb, options):
    username = options.delete
    if username not in vdb.list_users():
        sys.exit("User %s doesn't exist in %s" % (username, options.filename))
    
    print "Removing user %s from %s" % (username, options.filename)
    vdb.del_user(username)
    vdb.sync()

def set_user(vdb, options):
    username = options.add
    if username in vdb.list_users():
        print "Adding user %s to %s" % (username, options.filename)
    else:
        print "Changing user %s in %s" % (username, options.filename)
    
    password1 = getpass.getpass("Password: ")
    password2 = getpass.getpass("Retype password: ")
    
    if password1 != password2:
        sys.exit("Passwords do not match!")
    if not password1:
        sys.exit("Password cannot be empty!")
    
    vdb.set_user(username, password1)
    vdb.sync()

def main():
    options = get_options()
    vdb = VdbAuthenticator.from_file(options.filename)
    
    if options.listonly:
        list_users(vdb, options)
    elif options.delete:
        del_user(vdb, options)
        print "OK"
    elif options.add:
        set_user(vdb, options)
        print "OK"
    else:
        parser.error("No action specified")


if __name__ == "__main__":
    main()






