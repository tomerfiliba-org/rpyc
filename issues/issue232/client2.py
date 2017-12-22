
import rpyc

class ClientService(rpyc.SlaveService):

    def on_connect(self):
        self.exposed_namespace = {}
        self._conn._config.update(dict(
            allow_all_attrs = True,
            allow_pickle = True,
            allow_getattr = True,
            allow_setattr = True,
            allow_delattr = True,
            import_custom_exceptions = True,
            instantiate_custom_exceptions = True,
            instantiate_oldstyle_exceptions = True,
        ))

conn = rpyc.connect("localhost", port=4567, service=ClientService)
conn.serve_all()
