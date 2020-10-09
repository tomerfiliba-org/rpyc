import pathlib
import rpyc
import subprocess
import tempfile
import unittest
from rpyc.utils.server import ThreadedServer
from shutil import which


class ParentGDB(rpyc.Service):
    """ starts a new gdb service instance on connect and quits on disconnect """

    def on_connect(self, conn):
        tests_path = pathlib.Path(__file__).resolve().parent
        gdb_cmd = ['gdb', '-q', '-x', pathlib.Path(tests_path, 'gdb_service.py')]
        self._proc = subprocess.Popen(gdb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = self._proc.stdout.readline()
        self._gdb_svc_port = int(stdout.strip().decode())
        self.gdb_svc_conn = rpyc.connect(host='localhost', port=self._gdb_svc_port)

    def on_disconnect(self, conn):
        self._proc.communicate()
        self._proc.kill()
        self.gdb_svc_conn.root.quit()
        self.gdb_svc_conn.close()

    def exposed_get_gdb(self):
        return self.gdb_svc_conn.root.get()


@unittest.skipUnless(which('gdb') is not None, "Skipping gdb example test since gdb not found")
class Test_GDB(unittest.TestCase):

    def setUp(self):
        self.dtemp = tempfile.mkdtemp()
        self.a_out = pathlib.Path(self.dtemp, 'a.out')
        compile_cmd = ['g++', '-g', '-o', str(self.a_out), '-x', 'c++', '-']
        proc = subprocess.Popen(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        proc_input = b'int func(int a, int b){return a + b;}int main(){return func(1, 2);}'
        stdout, stderr = proc.communicate(input=proc_input)
        if stdout or stderr:
            raise ValueError("stdout and stderr should have be empty for a.out creation")
        self.server = ThreadedServer(ParentGDB, port=18878, auto_register=False,
                                     protocol_config={'allow_all_attrs': True})
        self.server._start_in_thread()

    def tearDown(self):
        self.server.close()
        while not self.server._closed:
            pass

    def test_gdb(self):
        parent_gdb_conn = rpyc.connect(host='localhost', port=18878)
        gdb = parent_gdb_conn.root.get_gdb()
        gdb.execute('file {}'.format(self.a_out))
        disasm = gdb.execute('disassemble main', to_string=True)
        self.assertIn('End of assembler dump', disasm)
        parent_gdb_conn.close()


if __name__ == "__main__":
    unittest.main()
