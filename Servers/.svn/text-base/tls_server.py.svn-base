from Rpyc.Utils.Serving import DEFAULT_PORT, threaded_server, start_discovery_agent_thread
from Users import users
from tlslite.api import VerifierDB


#
# creates the verifier db
#
vdb = VerifierDB()
for username, password in users.iteritems():
    vdb[username] = vdb.makeVerifier(username, password, 2048)

def main(port = DEFAULT_PORT):
    start_discovery_agent_thread(rpyc_port = port)
    threaded_server(port = port, secure = True, vdb = vdb)


if __name__ == "__main__":
    main()

