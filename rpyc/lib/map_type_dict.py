"""
This is an abstract dict() implementation, except key and item writes
go through _map_key and _map_item
"""

class MapTypeDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__([])
        other=[]
        if len(args) > 1:
            raise TypeError("dict expected at most 1 arguments, got %d" % len(args))
        elif len(args)==1:
            other=args[0]
        self.update(other, **kwargs)

    def _map_key(self, key):
        raise NotImplementedError()

    def _map_item(self, item):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        key=self._map_key(key)
        value=self._map_item(value)
        super().__setitem__(key, value)

    def setdefault(self, key, item=None):
        key=self._map_key(key)
        item=self._map_item(item)
        super().setdefault(key, item)

    def copy(self):
        return self.__class__.__init__(self)

    def update(self, *args, **kwargs):
        other=[]
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        elif len(args)==1:
            other=args[0]

        #This is the most annoying thing when subclassing dict
        #How does python C implementation of dict determine if
        #mapping or sequence?
        #
        #it duck types, based on whether keys is defined.
        keys=getattr(other, "keys", None)
        if keys is not None:
            sequence=[]
            keyIterator=keys() #if this is not callable, gives same errors
                               #inside dict implementation.
            for key in keyIterator:
                #dict also exposes exceptions from other[key]
                #access directly
                sequence.append( (key, other[key]) )

        else:
            #Just let it throw the TypeError if not iterable, it is 100% correct
            #to original dict implementation.
            sequence=list(other)

        for key in kwargs:
            sequence.append( (key, kwargs[key]) )

        index=0
        for values in sequence:
            try:
                values=tuple(values)
            except TypeError as e:
                raise TypeError("cannot convert dictionary update " +
                                "sequence element #%d to a sequence" % index)

            if len(values) != 2:
                 raise ValueError("dictionary update sequence element #" +
                                  "%d has length %d;" % (index, len(values)) +
                                  " ;2 is required" )
            key, item = values

            self.__setitem__(key, item)
            index+=1




