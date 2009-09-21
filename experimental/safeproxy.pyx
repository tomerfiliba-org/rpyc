cdef class SafeProxy:
	cdef object _obj
	cdef object __class__
	
	def __init__(self, obj):
		self._obj = obj
		self.__class__ = None
	def __getattr__(self, name):
		return getattr(self._obj, name)


