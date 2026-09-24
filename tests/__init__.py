import sys
import rpyc
import warnings
from pathlib import Path
import logging
import socket


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SocketTracker")


# Save references to original methods
_original_init = socket.socket.__init__
_original_close = socket.socket.close


# Monkey-patch __init__ to log socket creation
def logged_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    # Note: fileno() is -1 until fully initialized or connected on some systems
    logger.info(f"[CREATE] Socket initialized. Family: {self.family.name}, Type: {self.type.name}")


# Monkey-patch close to log socket closure
def logged_close(self):
    fd = self.fileno()
    # If fd is -1, it's already closed or uninitialized
    if fd != -1:
        logger.info(f"[CLOSE] Closing socket with File Descriptor: {fd}")
    _original_close(self)


# Apply patches globally
socket.socket.__init__ = logged_init
socket.socket.close = logged_close


def load_tests(loader, standard_tests, pattern):
    # Hook rpyc logger, unittest verbosity, and system paths
    rpyc.core.DEFAULT_CONFIG['logger'] = rpyc.lib.setup_logger()
    warnings.simplefilter("error", ResourceWarning)

    rpyc_tests_path = Path(__file__).absolute().parent
    rpyc_path = rpyc_tests_path.parent
    for p in [str(rpyc_path), str(rpyc_tests_path)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    # Discover on tests and add paths
    tests = loader.discover(start_dir=rpyc_tests_path, pattern=pattern, top_level_dir=rpyc_path)
    standard_tests.addTests(tests)
    return standard_tests
