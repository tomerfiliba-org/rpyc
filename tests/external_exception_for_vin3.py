class external_exception(Exception):
    def __init__(self, *args):
        if args:
            self.args = args
        else:
            self.args = ("I am alive",)
        self.external_demo_attr = 2

