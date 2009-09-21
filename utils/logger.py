import sys
import os
import thread
import time
import traceback


class Logger(object):
    def __init__(self, name, console = sys.stderr, file = None, show_name = True,
    show_pid = False, show_tid = False, show_date = False, show_time = True, 
    show_label = True, quiet = False):
        self.name = name
        self.console = console
        self.file = file
        self.show_name = show_name
        self.show_pid = show_pid
        self.show_tid = show_tid
        self.show_date = show_date
        self.show_time = show_time
        self.show_label = show_label
        self.quiet = quiet
        self.filter = set()
    
    def log(self, label, msg):
        if label in self.filter:
            return
        header = []
        if self.show_name:
            header.append("%-10s" % (self.name,))
        if self.show_label:
            header.append("%-10s" % (label,))
        if self.show_date:
            header.append(time.strftime("%Y-%m-%d"))
        if self.show_time:
            header.append(time.strftime("%H:%M:%S"))
        if self.show_pid:
            header.append("pid=%d" % (os.getpid(),))
        if self.show_tid:
            header.append("tid=%d" % (thread.get_ident(),))
        if header:
            header = "[" + " ".join(header) + "] "
        sep = "\n...." + " " * (len(header) - 4)
        text = header + sep.join(msg.splitlines()) + "\n"
        if self.console:
            self.console.write(text)
        if self.file:
            self.file.write(text)
    
    def debug(self, msg, *args, **kwargs):
        if self.quiet: return
        if args: msg %= args
        self.log("DEBUG", msg)
    def info(self, msg, *args, **kwargs):
        if self.quiet: return
        if args: msg %= args
        self.log("INFO", msg)
    def warn(self, msg, *args, **kwargs):
        if self.quiet: return
        if args: msg %= args
        self.log("WARNING", msg)
    def error(self, msg, *args, **kwargs):
        if args: msg %= args
        self.log("ERROR", msg)
    def traceback(self, excinfo = None):
        if not excinfo:
            excinfo = sys.exc_info()
        self.log("TRACEBACK", "".join(traceback.format_exception(*excinfo)))


logger = Logger("root", show_name = False)


if __name__ == "__main__":
    try:
        logger.info("hello")
        1/0
    except:
        logger.traceback()






