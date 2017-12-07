"""
This is an abstract list() implementation, except item writes
go through _map_item
"""

class MapTypeList(list):
    def __init__(self, *args):
        super(MapTypeList, self).__init__()
        argument=tuple()

        if len(args) > 1:
            raise TypeError("list() takes at most 1 argument " +
                            "(%d given)" % len(args))
        elif len(args) == 1:
            argument=args[0]

        for value in iter(argument):
            new_value = self._map_item(value)
            super(MapTypeList, self).append(new_value)

    def _map_item(self, item):
        raise NotImplementedError()

    def __add__(self, other):
        return self.__class__(super(MapTypeList, self).__add__(other))

    def __mul__(self, other):
        return self.__class__(super(MapTypeList, self).__mul__(other))

    def __rmul__(self, other):
        return self.__class__(super(MapTypeList, self).__rmul__(other))

    def __getitem__(self, index_or_slice):
        result = super(MapTypeList, self).__getitem__(index_or_slice)
        if isinstance(index_or_slice, slice):
            return self.__class__(result)
        return result

    #python2 version of list still has these functions, so even though
    #deprecated they are still used -- because they exist.
    def __getslice__(self, start, end):
        return self.__getitem__(slice(start,end))

    def __setitem__(self, index_or_slice, value):
        if isinstance(index_or_slice, slice):
            #Deal with slice actually.
            value=self.__class__(value)
        else:
            value=self._map_item(value)
        super(MapTypeList, self).__setitem__(index_or_slice, value)

    #python2 version of list still has these functions, so even though
    #deprecated they are still used -- because they exist.
    def __setslice__(self, start, end, values):
        self.__setitem__(slice(start,end), values)

    def append(self, value):
        self[len(self):]=[value]

    def extend(self, values):
        self[len(self):] = iterable

    def insert(self, index, value):
        self[index:index] = [value]

    def copy(self):
        return self.__class__.__init__(self)


