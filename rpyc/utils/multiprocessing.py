from multiprocessing import Value

class count(object):
    def __init__(self, c=0):
        self.c = Value('L', c)
    def __iter__(self):
        return self
    def __next__(self):
        with self.c.get_lock():
            rv = self.c.value
            self.c.value += 1
        return rv
