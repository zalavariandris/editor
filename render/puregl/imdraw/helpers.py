import ctypes
def buffer_offset(itemsize):
    return ctypes.c_void_p(itemsize)