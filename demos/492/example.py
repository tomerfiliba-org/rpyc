"""
arguments: use_ssl wait
use_ssl == 'True' or != 'True'
wait    == 'True' or != 'True'
"""
KEY = "./tests/server.key"
CERT = "./tests/server.crt"
VERIFY_CLIENT = (
    False  # False for master because arguments are incorrectly passed to .wrap_socket
)

import rpyc
import rpyc.utils.authenticators as ru_authenticators
import logging
import signal
import ssl
import subprocess
import sys
import time


PORT = 18812

rpyc.core.DEFAULT_CONFIG['logger'] = rpyc.setup_logger()
rpyc.core.DEFAULT_CONFIG['sync_request_timeout'] = 5
rpyc.core.DEFAULT_CONFIG['allow_all_attrs'] = True
logging.basicConfig(
    format="{asctime} | {levelname:8} | {message} ({name}, {threadName}, {process})",
    style="{",
)


class Service(rpyc.Service):
    pass


if len(sys.argv) == 3:  # start server and client subprocess
    server_process = subprocess.Popen(
        [sys.executable, __file__, "False"] + sys.argv[1:]
    )
    logging.info("waiting for server to start")
    time.sleep(1)
    client_process = subprocess.Popen([sys.executable, __file__, "True"] + sys.argv[1:])

    client_process.wait()
    server_process.send_signal(signal.SIGINT)
    server_process.wait()

else:
    _, as_client, use_ssl, wait = sys.argv
    as_client = as_client == "True"
    use_ssl = use_ssl == "True"
    wait = wait == "True"

    if as_client:
        connection = (
            rpyc.ssl_connect(
                "localhost",
                PORT,
                keyfile=KEY,
                certfile=CERT,
                ca_certs=CERT if VERIFY_CLIENT else None,
                cert_reqs=ssl.CERT_REQUIRED if VERIFY_CLIENT else None,
            )
            if use_ssl
            else rpyc.connect("localhost", PORT)
        )
        bg = rpyc.BgServingThread(connection)
        if wait:
            logging.info("wait")
            time.sleep(1)
        logging.debug("get root")
        connection.root
        logging.debug("get root2")
    else:
        authenticator = ru_authenticators.SSLAuthenticator(
            keyfile=KEY,
            certfile=CERT,
            ca_certs=CERT if VERIFY_CLIENT else None,
            cert_reqs=ssl.CERT_REQUIRED if VERIFY_CLIENT else None,
        )
        server = rpyc.ThreadedServer(
            Service(), port=PORT, authenticator=authenticator if use_ssl else None
        )
        try:
            server.start()

        except KeyboardInterrupt:
            pass
