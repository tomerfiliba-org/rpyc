"""
rpyc plug-in server (threaded or forking)
"""
import sys
import os
import socket
import time
import threading
import select
import errno
import logging
import Queue
from rpyc.core import SocketStream, Channel, Connection
from rpyc.utils.registry import UDPRegistryClient
from rpyc.utils.authenticators import AuthenticationError
from rpyc.lib import safe_import
from rpyc.core.async import AsyncResultTimeout
signal = safe_import("signal")


class Server(object):
    def __init__(self, service, hostname = "", ipv6 = None, port = 0, 
            backlog = 10, reuse_addr = True, authenticator = None, registrar = None,
            auto_register = True, protocol_config = {}, logger = None):
        self.active = False
        self._closed = False
        self.service = service
        self.authenticator = authenticator
        self.backlog = backlog
        self.auto_register = auto_register
        self.protocol_config = protocol_config
        self.clients = set()

        if ipv6 is None:
            ipv6 = socket.has_ipv6
        if ipv6:
            if hostname == "localhost":
                hostname = "localhost6"
            self.listener = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if reuse_addr and sys.platform != "win32":
            # warning: reuseaddr is not what you expect on windows!
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.listener.bind((hostname, port))
        self.port = self.listener.getsockname()[1]

        if logger is None:
            logger = logging.getLogger("%s/%d" % (self.service.get_service_name(), self.port))
        self.logger = logger
        if registrar is None:
            registrar = UDPRegistryClient(logger = self.logger)
        self.registrar = registrar

    def close(self):
        if self._closed:
            return
        self._closed = True
        self.active = False
        if self.auto_register:
            try:
                self.registrar.unregister(self.port)
            except Exception:
                 self.logger.exception("error unregistering services")
        self.listener.close()
        self.logger.info("listener closed")
        for c in set(self.clients):
            try:
                c.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            c.close()
        self.clients.clear()

    def fileno(self):
        return self.listener.fileno()

    def accept(self):
        while True:
            try:
                sock, addrinfo = self.listener.accept()
            except socket.timeout:
                pass
            except socket.error:
                ex = sys.exc_info()[1]
                if ex[0] == errno.EINTR:
                    pass
                else:
                    raise EOFError()
            else:
                break

        sock.setblocking(True)
        self.logger.info("accepted %s:%s", addrinfo[0], addrinfo[1])
        self.clients.add(sock)
        self._accept_method(sock)

    def _accept_method(self, sock):
        """this method should start a thread, fork a child process, or
        anything else in order to serve the client. once the mechanism has
        been created, it should invoke _authenticate_and_serve_client with
        `sock` as the argument"""
        raise NotImplementedError

    def _authenticate_and_serve_client(self, sock):
        try:
            if self.authenticator:
                addrinfo = sock.getpeername()
                h = addrinfo[0]
                p = addrinfo[1]
                try:
                    sock, credentials = self.authenticator(sock)
                except AuthenticationError:
                    self.logger.info("[%s]:%s failed to authenticate, rejecting connection", h, p)
                    return
                else:
                    self.logger.info("[%s]:%s authenticated successfully", h, p)
            else:
                credentials = None
            try:
                self._serve_client(sock, credentials)
            except Exception:
                self.logger.exception("client connection terminated abruptly")
                raise
        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            sock.close()
            self.clients.discard(sock)

    def _serve_client(self, sock, credentials):
        addrinfo = sock.getpeername()
        h = addrinfo[0]
        p = addrinfo[1]
        if credentials:
            self.logger.info("welcome [%s]:%s (%r)", h, p, credentials)
        else:
            self.logger.info("welcome [%s]:%s", h, p)
        try:
            config = dict(self.protocol_config, credentials = credentials)
            conn = Connection(self.service, Channel(SocketStream(sock)),
                config = config, _lazy = True)
            conn._init_service()
            conn.serve_all()
        finally:
            self.logger.info("goodbye [%s]:%s", h, p)

    def _bg_register(self):
        interval = self.registrar.REREGISTER_INTERVAL
        self.logger.info("started background auto-register thread "
            "(interval = %s)", interval)
        tnext = 0
        try:
            while self.active:
                t = time.time()
                if t >= tnext:
                    tnext = t + interval
                    try:
                        self.registrar.register(self.service.get_service_aliases(),
                            self.port)
                    except Exception:
                        self.logger.exception("error registering services")
                time.sleep(1)
        finally:
            if not self._closed:
                self.logger.info("background auto-register thread finished")

    def start(self):
        """starts the server. use close() to stop"""
        self.listener.listen(self.backlog)
        addrinfo = self.listener.getsockname()
        h = addrinfo[0] # to support both IPv4 and IPv6
        p = addrinfo[1]
        self.logger.info("server started on [%s]:%s", h, p)
        self.active = True
        if self.auto_register:
            t = threading.Thread(target = self._bg_register)
            t.setDaemon(True)
            t.start()
        #if sys.platform == "win32":
        # hack so we can receive Ctrl+C on windows
        self.listener.settimeout(0.5)
        try:
            try:
                while True:
                    self.accept()
            except EOFError:
                pass # server closed by another thread
            except KeyboardInterrupt:
                print("")
                self.logger.warn("keyboard interrupt!")
        finally:
            self.logger.info("server has terminated")
            self.close()


class ThreadedServer(Server):
    def _accept_method(self, sock):
        t = threading.Thread(target = self._authenticate_and_serve_client, args = (sock,))
        t.setDaemon(True)
        t.start()

# the select package does not provide a poll interface on all platform,
# so we wrap it on platforms that do not provide it
if hasattr(select, 'poll'):
    def wrappedPoll():
        return select.poll()
else:
    class PollObject(object):
        def __init__(self):
            self.waitlist = []
        def unregister(self, fd):
            self.waitlist.remove(fd)
        def register(self, fd, flags):
            self.waitlist.append(fd)
        def poll(self, timeout):
            rlist, wlist, xlist = select.select(self.waitlist, [], [], timeout)
            return [(fd, select.POLLIN) for fd in rlist]
    def wrappedPoll():
        return PollObject()

class ThreadPoolServer(Server):
    '''This server is threaded like the ThreadedServer but reuses threads so that
    recreation is not necessary for each request. The pool of threads has a fixed
    size that can be set with the 'nbThreads' argument. The default size is 20.
    The server dispatches request to threads by batch, that is a given thread may process
    up to request_batch_size requests from the same connection in one go, before it goes to
    the next connection with pending requests. By default, self.request_batch_size
    is set to 10 and it can be overwritten in the constructor arguments.'''

    def __init__(self, *args, **kwargs):
        '''Initializes a ThreadPoolServer. In particular, instantiate the thread pool.'''
        # get the number of threads in the pool
        nbthreads = 20
        if 'nbThreads' in kwargs:
            nbthreads = kwargs['nbThreads']
            del kwargs['nbThreads']
        # get the request batch size
        self.request_batch_size = 10
        if 'requestBatchSize' in kwargs:
            self.request_batch_size = kwargs['requestBatchSize']
            del kwargs['requestBatchSize']
        # init the parent
        Server.__init__(self, *args, **kwargs)
        # a queue of connections having somethign to process
        self._active_connection_queue = Queue.Queue()
        # declare the pool as already active
        self.active = True
        # setup the thread pool for handling requests
        self.workers = []
        for i_unused in range(nbthreads):
            t = threading.Thread(target = self._serve_clients)
            t.setName('ThreadPoolWorker')
            t.daemon = True
            t.start()
            self.workers.append(t)
        # a polling object to be used be the polling thread
        self.poll_object = wrappedPoll()
        # a dictionnary fd -> connection
        self.fd_to_conn = {}
        # setup a thread for polling inactive connections
        self.pollingThread = threading.Thread(target = self._poll_inactive_clients)
        self.pollingThread.setName('PollingThread')
        self.pollingThread.daemon = True
        self.pollingThread.start()

    def close(self):
        '''closes a ThreadPoolServer. In particular, joins the thread pool.'''
        # close parent server
        Server.close(self)
        # stop producer thread
        self.pollingThread.join()
        # cleanup thread pool : first fill the pool with None fds so that all threads exit
        # the blocking get on the queue of active connections. Then join the threads
        for i_unused in range(len(self.workers)):
            self._active_connection_queue.put(None)
        for w in self.workers:
            w.join()

    def _remove_from_inactive_connection(self, fd):
        '''removes a connection from the set of inactive ones'''
        # unregister the connection in the polling object
        try:
            self.poll_object.unregister(fd)
        except KeyError:
            # the connection has already been unregistered
            pass

    def _drop_connection(self, fd):
        '''removes a connection by closing it and removing it from internal structs'''
        # cleanup fd_to_conn dictionnary
        try:
            conn = self.fd_to_conn[fd]
            del self.fd_to_conn[fd]
        except KeyError:
            # the active connection has already been removed
            pass
        # close connection
        conn.close()

    def _add_inactive_connection(self, fd):
        '''adds a connection to the set of inactive ones'''
        self.poll_object.register(fd, select.POLLIN|select.POLLPRI|select.POLLNVAL|select.POLLHUP|select.POLLERR)

    def _handle_poll_result(self, connlist):
        '''adds a connection to the set of inactive ones'''
        for fd, event in connlist:
            try:
                # remove connection from the inactive ones
                self._remove_from_inactive_connection(fd)
                # Is it an error ?
                if (event & (select.POLLNVAL|select.POLLHUP|select.POLLERR)) != 0:
                    # it was an error, connection was closed. Do the same on our side
                    self._drop_connection(fd)
                else:
                    # connection has data, let's add it to the active queue
                    self._active_connection_queue.put(fd)
            except KeyError:
                # the connection has already been dropped. Give up
                pass

    def _poll_inactive_clients(self):
        '''Main method run by the polling thread of the thread pool.
        Check whether inactive clients have become active'''
        while self.active:
            try:
                # the actual poll, with a timeout of 1s so that we can exit in case
                # we re not active anymore
                active_clients = self.poll_object.poll(1)
                # for each client that became active, put them in the active queue
                self._handle_poll_result(active_clients)
            except Exception, e:
                # "Caught exception in Worker thread" message
                self.logger.warning("failed to poll clients, caught exception : %s", str(e))
                # wait a bit so that we do not loop too fast in case of error
                time.sleep(.2)

    def _serve_requests(self, fd):
        '''Serves requests from the given connection and puts it back to the appropriate queue'''
        # serve a maximum of RequestBatchSize requests for this connection
        for i_unused in range(self.request_batch_size):
            try:
                if not self.fd_to_conn[fd].poll(): # note that poll serves the request
                    # we could not find a request, so we put this connection back to the inactive set
                    self._add_inactive_connection(fd)
                    return
            except EOFError:
                # the connection has been closed by the remote end. Close it on our side and return
                self._drop_connection(fd)
                return
            except Exception:
                # put back the connection to active queue in doubt and raise the exception to the upper level
                self._active_connection_queue.put(fd)
                raise
        # we've processed the maximum number of requests. Put back the connection in the active queue
        self._active_connection_queue.put(fd)

    def _serve_clients(self):
        '''Main method run by the processing threads of the thread pool.
        Loops forever, handling requests read from the connections present in the active_queue'''
        while self.active:
            try:
                # note that we do not use a timeout here. This is because the implementation of
                # the timeout version performs badly. So we block forever, and exit by filling
                # the queue with None fds
                fd = self._active_connection_queue.get(True)
                # fd may be None (case where we want to exit the blocking get to close the service)
                if fd:
                    # serve the requests of this connection
                    self._serve_requests(fd)
            except Queue.Empty:
                # we've timed out, let's just retry. We only use the timeout so that this
                # thread can stop even if there is nothing in the queue
                pass
            except Exception, e:
                # "Caught exception in Worker thread" message
                self.logger.warning("failed to serve client, caught exception : %s", str(e))
                # wait a bit so that we do not loop too fast in case of error
                time.sleep(.2)

    def _authenticate_and_build_connection(self, sock):
        '''Authenticate a client and if it succees, wraps the socket in a connection object.
        Note that this code is cut and paste from the rpyc internals and may have to be
        changed if rpyc evolves'''
        # authenticate
        if self.authenticator:
            h, p = sock.getpeername()
            try:
                sock, credentials = self.authenticator(sock)
            except AuthenticationError:
                self.logger.info("%s:%s failed to authenticate, rejecting connection", h, p)
                return None
        else:
            credentials = None
        # build a connection
        h, p = sock.getpeername()
        config = dict(self.protocol_config, credentials=credentials, connid="%s:%d"%(h, p))
        return Connection(self.service, Channel(SocketStream(sock)), config=config)

    def _accept_method(self, sock):
        '''Implementation of the accept method : only pushes the work to the internal queue.
        In case the queue is full, raises an AsynResultTimeout error'''
        try:
            # authenticate and build connection object
            conn = self._authenticate_and_build_connection(sock)
            # put the connection in the active queue
            if conn:
                fd = conn.fileno()
                self.fd_to_conn[fd] = conn
                self._add_inactive_connection(fd)
                self.clients.clear()
        except Exception, e:
            self.logger.warning("failed to serve client, caught exception : %s", str(e))


class ForkingServer(Server):
    def __init__(self, *args, **kwargs):
        if not signal:
            raise OSError("ForkingServer not supported on this platform")
        Server.__init__(self, *args, **kwargs)
        # setup sigchld handler
        self._prevhandler = signal.signal(signal.SIGCHLD, self._handle_sigchld)

    def close(self):
        Server.close(self)
        signal.signal(signal.SIGCHLD, self._prevhandler)

    @classmethod
    def _handle_sigchld(cls, signum, unused):
        try:
            while True:
                pid, dummy = os.waitpid(-1, os.WNOHANG)
                if pid <= 0:
                    break
        except OSError:
            pass
        # re-register signal handler (see man signal(2), under Portability)
        signal.signal(signal.SIGCHLD, cls._handle_sigchld)

    def _accept_method(self, sock):
        pid = os.fork()
        if pid == 0:
            # child
            try:
                try:
                    self.logger.debug("child process created")
                    signal.signal(signal.SIGCHLD, self._prevhandler)
                    self.listener.close()
                    self.clients.clear()
                    self._authenticate_and_serve_client(sock)
                except:
                    self.logger.exception("child process terminated abnormally")
                else:
                    self.logger.debug("child process terminated")
            finally:
                self.logger.debug("child terminated")
                os._exit(0)
        else:
            # parent
            sock.close()

