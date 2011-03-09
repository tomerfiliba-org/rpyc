class orphan_external_exception(Exception):
    def __init__(self, args=None):
        if args:
            self.args = (args,)
        else:
            self.args = ("Wow I have been imported",)
        self.external_demo_attr = "Now imported"
