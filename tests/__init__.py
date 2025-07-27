import sys
from pathlib import Path


def load_tests(loader, standard_tests, pattern):
    # Hook rpyc logger, unittest verbosity, and system paths
    #rpyc.core.DEFAULT_CONFIG['logger'] = rpyc.lib.setup_logger()
    rpyc_tests_path = Path(__file__).absolute().parent
    rpyc_path = rpyc_tests_path.parent
    for p in [str(rpyc_path), str(rpyc_tests_path)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    # Discover on tests and add paths
    tests = loader.discover(start_dir=rpyc_tests_path, pattern=pattern, top_level_dir=rpyc_path)
    standard_tests.addTests(tests)
    return standard_tests
