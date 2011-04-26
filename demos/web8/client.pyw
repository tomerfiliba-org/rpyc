import pygtk
pygtk.require('2.0')
import gtk
import gobject
import rpyc
from safegtk import SafeGTK


def BrowserServiceFactory(browser):
    class BrowserService(rpyc.Service):
        def on_connect(self):
            self._conn._config["allow_public_attrs"] = True
        def exposed_navigate(self, url):
            old_url = browser.txt_url.get_text()
            if url.startswith("/"):
                base = old_url.split("/")[0]
                url = base + url
            browser.txt_url.set_text(url)
            browser.on_navigate(None)
    return BrowserService

class Browser(object):
    def __init__(self):
        self.conn = None

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_resizable(True)
        window.connect("destroy", self.on_close)
        window.set_title("Web8 Browser")
        self.box_main = gtk.VBox()
        self.box_main.show()
        window.add(self.box_main)

        hbox1 = gtk.HBox()
        hbox1.show()
        self.box_main.pack_start(hbox1, fill = False, expand = False)

        self.txt_url = gtk.Entry()
        self.txt_url.set_text("localhost/main")
        self.txt_url.show()
        self.txt_url.connect("activate", self.on_navigate)
        hbox1.pack_start(self.txt_url)

        btn_send = gtk.Button("Go")
        btn_send.show()
        btn_send.connect("clicked", self.on_navigate)
        hbox1.pack_start(btn_send, fill=False, expand=False, padding = 10)

        self.box_content = None
        window.show()

    def on_close(self, widget):
        if self.conn:
            self.conn.close()
            self.conn = None
        gtk.main_quit()

    def on_navigate(self, widget, data = None):
        url = self.txt_url.get_text()
        if "/" not in url:
            url += "/"
        host, page = url.split("/", 1)
        if ":" in host:
            addr, port = host.split(":", 1)
            port = int(port)
        else:
            addr = host
            port = 18833
        if self.conn:
            self.conn.close()
            self.conn = None

        if self.box_content:
            self.box_main.remove(self.box_content)
            self.box_content.destroy()
            self.box_content = None
        self.box_content = gtk.VBox()
        self.box_content.show()
        self.box_main.pack_start(self.box_content)

        self.conn = rpyc.connect(host, port, service = BrowserServiceFactory(self))
        gobject.io_add_watch(self.conn, gobject.IO_IN, self.bg_server)
        self.conn.root.get_page(SafeGTK, self.box_content, page)

    def bg_server(self, source = None, cond = None):
        if self.conn:
            self.conn.poll_all()
            return True
        else:
            return False


if __name__ == "__main__":
    b = Browser()
    gtk.main()

