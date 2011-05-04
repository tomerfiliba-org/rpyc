"""
this class exposes only the gtk constants and some of the "safe" classes.
we don't want the server to open pop-ups on the client, so we won't expose
Window() et al.
"""
import pygtk
pygtk.require('2.0')
import gtk


safe_gtk_classes = set([
    "Box", "VBox", "HBox", "Frame", "Entry", "Button", "ScrolledWindow",
    "TextView", "Label",
])

class SafeGTK(object):
    for _name in dir(gtk):
        if _name in safe_gtk_classes or _name.isupper():
            exec "exposed_%s = gtk.%s" % (_name, _name)
    del _name

SafeGTK = SafeGTK()

