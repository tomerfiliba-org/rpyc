import pygtk
pygtk.require('2.0')
import gtk
import gobject
import rpyc


class ChatClient(object):
    def __init__(self):
        self.conn = None
        self.user = None

        #-------- GUI CODE ---------
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_resizable(True)
        window.connect("destroy", self.on_close)
        window.set_title("RPyChat")

        top = gtk.VBox()
        top.show()
        window.add(top)
        hbox1 = gtk.HBox()
        hbox1.show()
        top.pack_start(hbox1, expand=False)
        hbox2 = gtk.HBox()
        hbox2.show()
        top.pack_start(hbox2, expand=False)
        self.box_main = gtk.VBox()
        top.pack_start(self.box_main, padding=10)

        lbl_host = gtk.Label("Host:")
        lbl_host.show()
        hbox1.pack_start(lbl_host)
        self.txt_host = gtk.Entry()
        self.txt_host.set_text("127.0.0.1")
        self.txt_host.show()
        self.txt_host.connect("activate", self.on_connect, "via-text")
        hbox1.pack_start(self.txt_host)

        lbl_port = gtk.Label("Port:")
        lbl_port.show()
        hbox1.pack_start(lbl_port, padding = 10)
        self.txt_port = gtk.Entry()
        self.txt_port.set_text("19912")
        self.txt_port.show()
        self.txt_port.connect("activate", self.on_connect, "via-text")
        hbox1.pack_start(self.txt_port)

        lbl_user = gtk.Label("Username:")
        lbl_user.show()
        hbox2.pack_start(lbl_user, padding = 10)
        self.txt_user = gtk.Entry()
        self.txt_user.show()
        self.txt_user.connect("activate", self.on_connect, "via-text")
        hbox2.pack_start(self.txt_user)

        lbl_password = gtk.Label("Password:")
        lbl_password.show()
        hbox2.pack_start(lbl_password, padding = 10)
        self.txt_password = gtk.Entry()
        self.txt_password.set_visibility(False)
        self.txt_password.show()
        self.txt_password.connect("activate", self.on_connect, "via-text")
        hbox2.pack_start(self.txt_password)

        self.btn_connect = gtk.Button("Connect")
        self.btn_connect.show()
        self.btn_connect.connect("clicked", self.on_connect)
        hbox2.pack_start(self.btn_connect, padding = 10)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        sw.show()
        self.box_main.pack_start(sw)

        self.txt_main = gtk.TextView()
        self.txt_main.set_editable(False)
        self.txt_main.show()
        sw.add(self.txt_main)

        hbox3 = gtk.HBox()
        hbox3.show()
        self.box_main.pack_start(hbox3, fill = False, expand=False)

        self.txt_input = gtk.Entry()
        self.txt_input.show()
        self.txt_input.connect("activate", self.on_send)
        hbox3.pack_start(self.txt_input)

        self.btn_send = gtk.Button("Send")
        self.btn_send.show()
        self.btn_send.connect("clicked", self.on_send)
        hbox3.pack_start(self.btn_send, fill=False, expand=False, padding = 10)

        window.show()
        #-------- END OF GUI CODE ---------

    def disconnect(self):
        if self.conn:
            try:
                self.user.logout()
            except:
                pass
            self.conn.close()
            self.user = None
            self.conn = None

    def on_close(self, widget):
        self.disconnect()
        gtk.main_quit()

    #
    # connect/disconnect logic
    #
    def on_connect(self, widget, data = None):
        if self.btn_connect.get_label() == "Connect":
            try:
                self.conn = rpyc.connect(self.txt_host.get_text(), int(self.txt_port.get_text()))
            except Exception:
                self.conn = None
                m=gtk.MessageDialog(buttons = gtk.BUTTONS_OK,
                    type = gtk.MESSAGE_ERROR,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    message_format="Connection refused")
                m.run()
                m.destroy()
                return

            try:
                self.user = self.conn.root.login(self.txt_user.get_text(),
                    self.txt_password.get_text(), self.on_message)
            except ValueError:
                self.conn.close()
                self.conn = None
                m=gtk.MessageDialog(buttons = gtk.BUTTONS_OK,
                    type = gtk.MESSAGE_ERROR,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    message_format="Invalid Login")
                m.run()
                m.destroy()
                return

            # register in the GTK reactor
            gobject.io_add_watch(self.conn, gobject.IO_IN, self.bg_server)
            self.btn_connect.set_label("Disconnect")
            self.box_main.show()
        else:
            if data == "via-text":
                return
            self.disconnect()
            self.box_main.hide()
            self.btn_connect.set_label("Connect")

    #
    # called by the reactor whenever the connection has something to say
    #
    def bg_server(self, source = None, cond = None):
        if self.conn:
            self.conn.poll_all()
            return True
        else:
            return False

    #
    # sends the current message
    #
    def on_send(self, widget, data = None):
        text = self.txt_input.get_text()
        self.txt_input.set_text("")
        if text.strip():
            self.user.say(text)

    #
    # called by the server, with the text to append to the GUI
    #
    def on_message(self, text):
        buf = self.txt_main.get_buffer()
        buf.place_cursor(buf.get_end_iter())
        buf.insert_at_cursor(text + "\n")
        self.txt_main.scroll_to_iter(buf.get_end_iter(), 0)


if __name__ == "__main__":
    cc = ChatClient()
    gtk.main()

