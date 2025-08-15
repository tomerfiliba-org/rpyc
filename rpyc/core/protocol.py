"""The RPyC protocol
"""
import sys
import itertools
import socket
import time  # noqa: F401
import gc  # noqa: F401

import collections
import os
import threading

from weakref import ref
from threading import Lock, Condition, RLock
from rpyc.lib import worker, spawn, Timeout, get_methods, get_id_pack, hasattr_static
from rpyc.lib.compat import pickle, next, maxint, select_error, acquire_lock  # noqa: F401
from rpyc.lib.colls import WeakValueDict, RefCountingColl
from rpyc.core import consts, brine, vinegar, netref
from rpyc.core.async_ import AsyncResult


class PingError(Exception):
    """The exception raised should :func:`Connection.ping` fail"""
    pass


UNBOUND_THREAD_ID = 0  # Used when the message is being sent but the thread is not bound yet.
DEFAULT_CONFIG = dict(
    # ATTRIBUTES
    allow_safe_attrs=True,
    allow_exposed_attrs=True,
    allow_public_attrs=False,
    allow_all_attrs=False,
    safe_attrs=set(['__abs__', '__add__', '__and__', '__bool__', '__cmp__', '__contains__',
                    '__delitem__', '__delslice__', '__div__', '__divmod__', '__doc__',
                    '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
                    '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
                    '__idiv__', '__ifloordiv__', '__ilshift__', '__imod__', '__imul__',
                    '__index__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
                    '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
                    '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
                    '__neg__', '__new__', '__nonzero__', '__oct__', '__or__', '__pos__',
                    '__pow__', '__radd__', '__rand__', '__rdiv__', '__rdivmod__', '__repr__',
                    '__rfloordiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__',
                    '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__',
                    '__rxor__', '__setitem__', '__setslice__', '__str__', '__sub__',
                    '__truediv__', '__xor__', 'next', '__length_hint__', '__enter__',
                    '__exit__', '__next__', '__format__']),
    exposed_prefix="exposed_",
    allow_getattr=True,
    allow_setattr=False,
    allow_delattr=False,
    # EXCEPTIONS
    include_local_traceback=True,
    include_local_version=True,
    instantiate_custom_exceptions=False,
    import_custom_exceptions=False,
    instantiate_oldstyle_exceptions=False,  # which don't derive from Exception
    propagate_SystemExit_locally=False,  # whether to propagate SystemExit locally or to the other party
    propagate_KeyboardInterrupt_locally=True,  # whether to propagate KeyboardInterrupt locally or to the other party
    log_exceptions=True,
    # MISC
    allow_pickle=False,
    connid=None,
    credentials=None,
    endpoints=None,
    logger=None,
    sync_request_timeout=30,
    before_closed=None,
    close_catchall=False,
    bind_threads=os.environ.get('RPYC_BIND_THREADS', 'false').lower() == 'true',
)
"""
The default configuration dictionary of the protocol. You can override these parameters
by passing a different configuration dict to the :class:`Connection` class.

.. note::
   You only need to override the parameters you want to change. There's no need
   to repeat parameters whose values remain unchanged.

=======================================  ================  =====================================================
Parameter                                Default value     Description
=======================================  ================  =====================================================
``allow_safe_attrs``                     ``True``          Whether to allow the use of *safe* attributes
                                                           (only those listed as ``safe_attrs``)
``allow_exposed_attrs``                  ``True``          Whether to allow exposed attributes
                                                           (attributes that start with the ``exposed_prefix``)
``allow_public_attrs``                   ``False``         Whether to allow public attributes
                                                           (attributes that don't start with ``_``)
``allow_all_attrs``                      ``False``         Whether to allow all attributes (including private)
``safe_attrs``                           ``set([...])``    The set of attributes considered safe
``exposed_prefix``                       ``"exposed_"``    The prefix of exposed attributes
``allow_getattr``                        ``True``          Whether to allow getting of attributes (``getattr``)
``allow_setattr``                        ``False``         Whether to allow setting of attributes (``setattr``)
``allow_delattr``                        ``False``         Whether to allow deletion of attributes (``delattr``)
``allow_pickle``                         ``False``         Whether to allow the use of ``pickle``

``include_local_traceback``              ``True``          Whether to include the local traceback
                                                           in the remote exception
``instantiate_custom_exceptions``        ``False``         Whether to allow instantiation of
                                                           custom exceptions (not the built in ones)
``import_custom_exceptions``             ``False``         Whether to allow importing of
                                                           exceptions from not-yet-imported modules
``instantiate_oldstyle_exceptions``      ``False``         Whether to allow instantiation of exceptions
                                                           which don't derive from ``Exception``. This
                                                           is not applicable for Python 3 and later.
``propagate_SystemExit_locally``         ``False``         Whether to propagate ``SystemExit``
                                                           locally (kill the server) or to the other
                                                           party (kill the client)
``propagate_KeyboardInterrupt_locally``  ``False``         Whether to propagate ``KeyboardInterrupt``
                                                           locally (kill the server) or to the other
                                                           party (kill the client)
``logger``                               ``None``          The logger instance to use to log exceptions
                                                           (before they are sent to the other party)
                                                           and other events. If ``None``, no logging takes place.

``connid``                               ``None``          **Runtime**: the RPyC connection ID (used
                                                           mainly for debugging purposes)
``credentials``                          ``None``          **Runtime**: the credentials object that was returned
                                                           by the server's :ref:`authenticator <api-authenticators>`
                                                           or ``None``
``endpoints``                            ``None``          **Runtime**: The connection's endpoints. This is a tuple
                                                           made of the local socket endpoint (``getsockname``) and the
                                                           remote one (``getpeername``). This is set by the server
                                                           upon accepting a connection; client side connections
                                                           do no have this configuration option set.

``sync_request_timeout``                 ``30``            Default timeout for waiting results
``bind_threads``                         ``False``         Whether to restrict request/reply by thread (experimental).
                                                           The default value is False. Setting the environment variable
                                                           `RPYC_BIND_THREADS` to `"true"` will enable this feature.
=======================================  ================  =====================================================
"""


_connection_id_generator = itertools.count(1)


class Connection(object):
    """The RPyC *connection* (AKA *protocol*).

    Objects referenced over the connection are either local or remote. This class retains a strong reference to
    local objects that is deleted when the reference count is zero. Remote/proxied objects have a life-cycle
    controlled by a different address space. Since garbage collection is handled on the remote end, a weak reference
    is used for netrefs.

    :param root: the :class:`~rpyc.core.service.Service` object to expose
    :param channel: the :class:`~rpyc.core.channel.Channel` over which messages are passed
    :param config: the connection's configuration dict (overriding parameters
                   from the :data:`default configuration <DEFAULT_CONFIG>`)
    """

    def __init__(self, root, channel, config={}):
        self._closed = True
        self._config = DEFAULT_CONFIG.copy()
        self._config.update(config)
        if self._config["connid"] is None:
            self._config["connid"] = f"conn{next(_connection_id_generator)}"

        self._HANDLERS = self._request_handlers()
        self._channel = channel
        self._seqcounter = itertools.count()
        self._recvlock = RLock()  # AsyncResult implementation means that synchronous requests have multiple acquires
        self._sendlock = Lock()
        self._recv_event = Condition()  # TODO: why not simply timeout? why not associate w/ recvlock? explain/redesign
        self._request_callbacks = {}
        self._local_objects = RefCountingColl()
        self._last_traceback = None
        self._proxy_cache = WeakValueDict()
        self._netref_classes_cache = {}
        self._remote_root = None
        self._send_queue = []
        self._local_root = root
        self._closed = False
        # Settings for bind_threads
        self._bind_threads = self._config['bind_threads']
        self._threads = None
        if self._bind_threads:
            self._lock = threading.RLock()
            self._threads = {}
            self._receiving = False
            self._thread_pool = []
            self._worker_pool = set()
            self._cleaning_thread = None

    def __del__(self):
        self.close()
        if self._bind_threads:
            with self._lock:
                cleaning_thread = self._cleaning_thread
                self._cleaning_thread = None
            if cleaning_thread is threading.current_thread():
                spawn(cleaning_thread.join)
            elif cleaning_thread is not None:
                cleaning_thread.join()

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()

    def __repr__(self):
        a, b = object.__repr__(self).split(" object ")
        return f"{a} {self._config['connid']!r} object {b}"

    def _cleanup(self, _anyway=True):  # IO
        if self._closed and not _anyway:
            return
        self._closed = True
        self._channel.close()
        self._local_root.on_disconnect(self)
        self._request_callbacks.clear()
        self._local_objects.clear()
        self._proxy_cache.clear()
        self._netref_classes_cache.clear()
        self._last_traceback = None
        self._remote_root = None
        self._local_root = None
        # self._seqcounter = None
        # self._config.clear()
        del self._HANDLERS
        if _anyway:
            try:
                self._recvlock.release()
            except Exception:
                pass
            try:
                self._sendlock.release()
            except Exception:
                pass
        self._cleanup_threads()

    def _cleanup_threads(self):
        if self._bind_threads:
            with self._lock:
                if threading.current_thread() in self._worker_pool:
                    if self._cleaning_thread is None:
                        self._cleaning_thread = worker(
                            self._cleanup_threads
                        )
                    return

                with _ReceivingGuard(self):
                    worker_pool = self._worker_pool
                    self._worker_pool = set()

                    for thd in worker_pool:
                        thread = self._get_thread(thd)
                        if thread:
                            thread.serve = False

            for thd in worker_pool:
                thd.join()

    def close(self):  # IO
        """closes the connection, releasing all held resources"""
        if self._closed:
            return
        try:
            self._closed = True
            if self._config.get("before_closed"):
                self._config["before_closed"](self.root)
            # TODO: define invariants/expectations around close sequence and timing
            self.sync_request(consts.HANDLE_CLOSE)
        except (EOFError, TimeoutError):
            pass
        except Exception:
            if not self._config["close_catchall"]:
                raise
        finally:
            self._cleanup(_anyway=True)

    @property
    def closed(self):  # IO
        """Indicates whether the connection has been closed or not"""
        return self._closed

    def fileno(self):  # IO
        """Returns the connectin's underlying file descriptor"""
        return self._channel.fileno()

    def ping(self, data=None, timeout=3):  # IO
        """Asserts that the other party is functioning properly, by making sure
        the *data* is echoed back before the *timeout* expires

        :param data: the data to send (leave ``None`` for the default buffer)
        :param timeout: the maximal time to wait for echo

        :raises: :class:`PingError` if the echoed data does not match
        :raises: :class:`EOFError` if the remote host closes the connection
        """
        if data is None:
            data = "abcdefghijklmnopqrstuvwxyz" * 20
        res = self.async_request(consts.HANDLE_PING, data, timeout=timeout)
        if res.value != data:
            raise PingError("echo mismatches sent data")

    def _get_seq_id(self):  # IO
        return next(self._seqcounter)

    def _send(self, msg, seq, args):  # IO
        data = brine.I1.pack(msg) + brine.dump((seq, args))  # see _dispatch
        if self._bind_threads:
            with self._lock:
                this_thread = self._get_thread()
                data = brine.I8I8.pack(this_thread.tid, this_thread._remote_thread_id) + data
                if msg == consts.MSG_REQUEST:
                    this_thread.incr()
                else:
                    this_thread.decr()
        # GC might run while sending data
        # if so, a BaseNetref.__del__ might be called
        # BaseNetref.__del__ must call asyncreq,
        # which will cause a deadlock
        # Solution:
        # Add the current request to a queue and let the thread that currently
        # holds the sendlock send it when it's done with its current job.
        # NOTE: Atomic list operations should be thread safe,
        # please call me out if they are not on all implementations!
        self._send_queue.append(data)
        # It is crucial to check the queue each time AFTER releasing the lock:
        while self._send_queue:
            if not self._sendlock.acquire(False):
                # Another thread holds the lock. It will send the data after
                # it's done with its current job. We can safely return.
                return
            try:
                # Can happen if another consumer was scheduled in between
                # `while` and `acquire`:
                if not self._send_queue:
                    # Must `continue` to ensure that `send_queue` is checked
                    # after releasing the lock! (in case another producer is
                    # scheduled before `release`)
                    continue
                data = self._send_queue.pop(0)
                self._channel.send(data)
            finally:
                self._sendlock.release()

    def _box(self, obj):  # boxing
        """store a local object in such a way that it could be recreated on
        the remote party either by-value or by-reference"""
        if brine.dumpable(obj):
            return consts.LABEL_VALUE, obj
        if type(obj) is tuple:
            return consts.LABEL_TUPLE, tuple(self._box(item) for item in obj)
        elif isinstance(obj, netref.BaseNetref) and obj.____conn__ is self:
            return consts.LABEL_LOCAL_REF, obj.____id_pack__
        else:
            id_pack = get_id_pack(obj)
            self._local_objects.add(id_pack, obj)
            return consts.LABEL_REMOTE_REF, id_pack

    def _unbox(self, package):  # boxing
        """recreate a local object representation of the remote object: if the
        object is passed by value, just return it; if the object is passed by
        reference, create a netref to it"""
        label, value = package
        if label == consts.LABEL_VALUE:
            return value
        if label == consts.LABEL_TUPLE:
            return tuple(self._unbox(item) for item in value)
        if label == consts.LABEL_LOCAL_REF:
            return self._local_objects[value]
        if label == consts.LABEL_REMOTE_REF:
            id_pack = (str(value[0]), value[1], value[2])  # so value is a id_pack
            proxy = self._proxy_cache.get(id_pack)  # Ensure referents exist until we increment refcount issue #558
            if proxy is not None:
                proxy.____refcount__ += 1  # if cached then remote incremented refcount, so sync refcount
            else:
                proxy = self._netref_factory(id_pack)
                self._proxy_cache[id_pack] = proxy
            return proxy
        raise ValueError(f"invalid label {label!r}")

    def _netref_factory(self, id_pack):  # boxing
        """id_pack is for remote, so when class id fails to directly match """
        cls = None
        if id_pack[2] == 0 and id_pack in self._netref_classes_cache:
            cls = self._netref_classes_cache[id_pack]
        elif id_pack[0] in netref.builtin_classes_cache:
            cls = netref.builtin_classes_cache[id_pack[0]]
        if cls is None:
            # in the future, it could see if a sys.module cache/lookup hits first
            cls_methods = self.sync_request(consts.HANDLE_INSPECT, id_pack)
            cls = netref.class_factory(id_pack, cls_methods)
            if id_pack[2] == 0:
                # only use cached netrefs for classes
                # ... instance caching after gc of a proxy will take some mental gymnastics
                self._netref_classes_cache[id_pack] = cls
        return cls(self, id_pack)

    def _dispatch_request(self, seq, raw_args):  # dispatch
        try:
            handler, args = raw_args
            args = self._unbox(args)
            res = self._HANDLERS[handler](self, *args)
        except:  # TODO: revisit how to catch handle locally, this should simplify when py2 is dropped
            # need to catch old style exceptions too
            t, v, tb = sys.exc_info()
            self._last_traceback = tb
            logger = self._config["logger"]
            if logger and t is not StopIteration:
                logger.debug("Exception caught", exc_info=True)
            if t is SystemExit and self._config["propagate_SystemExit_locally"]:
                raise
            if t is KeyboardInterrupt and self._config["propagate_KeyboardInterrupt_locally"]:
                raise
            self._send(consts.MSG_EXCEPTION, seq, self._box_exc(t, v, tb))
        else:
            self._send(consts.MSG_REPLY, seq, self._box(res))

    def _box_exc(self, typ, val, tb):  # dispatch?
        return vinegar.dump(typ, val, tb,
                            include_local_traceback=self._config["include_local_traceback"],
                            include_local_version=self._config["include_local_version"])

    def _unbox_exc(self, raw):  # dispatch?
        return vinegar.load(raw,
                            import_custom_exceptions=self._config["import_custom_exceptions"],
                            instantiate_custom_exceptions=self._config["instantiate_custom_exceptions"],
                            instantiate_oldstyle_exceptions=self._config["instantiate_oldstyle_exceptions"])

    def _seq_request_callback(self, msg, seq, is_exc, obj):
        _callback = self._request_callbacks.pop(seq, None)
        if _callback is not None:
            _callback(is_exc, obj)
        elif self._config["logger"] is not None:
            debug_msg = 'Received {} seq {} and a related request callback did not exist'
            self._config["logger"].debug(debug_msg.format(msg, seq))

    def _dispatch(self, data):  # serving---dispatch?
        msg, = brine.I1.unpack(data[:1])  # unpack just msg to minimize time to release
        if msg == consts.MSG_REQUEST:
            if self._bind_threads:
                with self._lock:
                    self._get_thread().incr()
            else:
                self._recvlock.release()
            seq, args = brine.load(data[1:])
            self._dispatch_request(seq, args)
        else:
            if self._bind_threads:
                with self._lock:
                    self._get_thread().decr()
            if msg == consts.MSG_REPLY:
                seq, args = brine.load(data[1:])
                obj = self._unbox(args)
                self._seq_request_callback(msg, seq, False, obj)
                if not self._bind_threads:
                    self._recvlock.release()  # releasing here fixes race condition with AsyncResult.wait
            elif msg == consts.MSG_EXCEPTION:
                if not self._bind_threads:
                    self._recvlock.release()
                seq, args = brine.load(data[1:])
                obj = self._unbox_exc(args)
                self._seq_request_callback(msg, seq, True, obj)
            else:
                raise ValueError(f"invalid message type: {msg!r}")

    def serve(self, timeout=1, wait_for_lock=True, waiting=lambda: True):  # serving
        """Serves a single request or reply that arrives within the given
        time frame (default is 1 sec). Note that the dispatching of a request
        might trigger multiple (nested) requests, thus this function may be
        reentrant.

        :returns: ``True`` if a request or reply were received, ``False`` otherwise.
        """
        timeout = Timeout(timeout)
        if self._bind_threads:
            return self._serve_bound(timeout, wait_for_lock)
        with self._recv_event:
            # Exit early if we cannot acquire the recvlock
            if not self._recvlock.acquire(False):
                if wait_for_lock:
                    if not waiting():  # unlikely, but the result could've arrived and another thread could've won the race to acquire
                        return False
                    # Wait condition for recvlock release; recvlock is not underlying lock for condition
                    return self._recv_event.wait(timeout.timeleft())
                else:
                    return False
        if not waiting():  # the result arrived and we won the race to acquire, unlucky
            self._recvlock.release()
            with self._recv_event:
                self._recv_event.notify_all()
            return False
        # Assume the receive rlock is acquired and incremented
        # We must release once BEFORE dispatch, dispatch any data, and THEN notify all (see issue #527 and #449)
        try:
            data = None  # Ensure data is initialized
            data = self._channel.poll(timeout) and self._channel.recv()
        except Exception as exc:
            self._recvlock.release()
            if isinstance(exc, EOFError):
                self.close()  # sends close async request
            raise
        else:
            if data:
                self._dispatch(data)  # Dispatch will unbox, invoke callbacks, etc.
                return True
            else:
                self._recvlock.release()
                return False
        finally:
            with self._recv_event:
                self._recv_event.notify_all()

    def _serve_bound(self, timeout, wait_for_lock):
        """Serves messages like `serve` with the added benefit of making request/reply thread bound.
        - Experimental functionality `RPYC_BIND_THREADS`

        The first 8 bytes indicate the sending thread ID and intended recipient ID. When the recipient
        thread ID is not the thread that received the data, the remote thread ID and message are appended
        to the intended threads `_deque` and `_event` is set.

        :returns: ``True`` if a request or reply were received, ``False`` otherwise.
        """
        message_available = False

        try:
            with self._lock:
                this_thread = self._get_thread()

                def isready():
                    nonlocal message_available
                    message_available = bool(this_thread._deque)
                    return message_available or not self._receiving

                ready = isready()
                if not ready and wait_for_lock:
                    self._thread_pool.append(this_thread)  # enter pool
                    ready = this_thread._condition.wait_for(isready, timeout=timeout.timeleft())
                    self._thread_pool.remove(this_thread)  # leave pool

                if not ready:
                    # timeout or not wait_for_lock
                    return False

                if message_available:
                    top = this_thread._deque.popleft()
                    if top is None:
                        return False
                    remote_thread_id, message = top
                else:
                    with _ReceivingGuard(self):
                        while True:
                            # from upstream
                            if not this_thread.serve:
                                return False

                            with _UnlockGuard(self._lock):
                                message = self._channel.poll(timeout) and self._channel.recv()

                            if not message:  # timeout; from upstream
                                return False

                            remote_thread_id, local_thread_id = brine.I8I8.unpack(message[:16])
                            message = message[16:]

                            new = False

                            if local_thread_id == UNBOUND_THREAD_ID and this_thread._occupation_count != 0:
                                # Message is not meant for this thread. Use a thread that is not occupied
                                # or have the pool create a new one. Occupation count for threads in
                                # thread_pool can be trusted
                                new = True
                                for thread in self._thread_pool:
                                    if thread.serve and thread._occupation_count == 0 and not thread._deque:
                                        new = False
                                        break

                            elif local_thread_id in {UNBOUND_THREAD_ID, this_thread.tid}:
                                # Of course, the message is for this thread if equal. When id is UNBOUND_THREAD_ID,
                                # we deduce that occupation count is 0 from the previous if condition.
                                break
                            else:
                                # Otherwise, message was meant for another thread.
                                thread = self._get_thread(tid=local_thread_id)
                                if not thread or not thread.serve:
                                    # bound thread terminated already.
                                    new = True

                            if new:
                                if not self._closed:
                                    thd = worker(self._serve_worker)
                                    self._worker_pool.add(thd)
                                    thread = self._get_thread(thd, create=True)
                                else:
                                    thread = None

                            if thread:
                                thread._deque.append((remote_thread_id, message))
                                thread._condition.notify()

                this_thread._remote_thread_id = remote_thread_id

        except EOFError:
            self.close()  # sends close async request
            raise

        self._dispatch(message)
        return True

    def _serve_worker(self):
        """Callable that is used to schedule serve as a new thread
        - Experimental functionality `RPYC_BIND_THREADS`

        :returns: None
        """
        thread = self._get_thread()

        # from upstream
        try:
            while thread.loop:
                self.serve(None)

        except (socket.error, select_error, IOError):
            if not self.closed:
                raise
        except EOFError:
            pass
        finally:
            thread.serve = False

    @staticmethod
    def _is_thread_alive(thd):
        # gevent does not properly implement in it's wrapper is_alive.
        # It causes an AttributeError
        # Consider thread to be alive in this case
        is_alive = thd.is_alive
        try:
            return is_alive()
        except AttributeError:
            return True

    def _get_thread(self, tid=None, *, create=None):
        """Get internal thread information for current thread for ID, when None use current thread.
        - Experimental functionality `RPYC_BIND_THREADS`

        :returns: _Thread
        """
        if isinstance(tid, threading.Thread):
            cthid = tid
            cid = tid.ident
            tid = cid
            if create is None:
                create = cthid is threading.current_thread()
        else:
            cthid = threading.current_thread()
            cid = cthid.ident
            if tid is None:
                tid = cid
            if create is None:
                create = tid == cid
            assert not create or cid == tid, (
                "create only supported for current thread or when thread object is given"
            )

        with self._lock:
            rthd, thread = self._threads.get(tid, (None, None))
            if rthd is not None:
                thd = rthd()
                if thd is None or not self._is_thread_alive(thd):
                    del rthd
                    self._threads.pop(tid)
                    thread = None
            if thread is None and create:
                rconnection = ref(self)

                def thread_deleted(_, tid=cid, rconnection=rconnection):
                    connection = rconnection()
                    if connection is not None:
                        with connection._lock:
                            connection._threads.pop(tid)

                thd = cthid
                rthd = ref(thd, thread_deleted)
                thread = _Thread(cid, self._lock)
                self._threads[cid] = rthd, thread

        return thread

    def poll(self, timeout=0):  # serving
        """Serves a single transaction, should one arrives in the given
        interval. Note that handling a request/reply may trigger nested
        requests, which are all part of a single transaction.

        :returns: ``True`` if a transaction was served, ``False`` otherwise"""
        return self.serve(timeout, False)

    def serve_all(self):  # serving
        """Serves all requests and replies for as long as the connection is
        alive."""
        try:
            while not self.closed:
                self.serve(None)
        except (socket.error, select_error, IOError):
            if not self.closed:
                raise
        except EOFError:
            pass
        finally:
            self.close()

    def serve_threaded(self, thread_count=10):  # serving
        """Serves all requests and replies for as long as the connection is alive.

        CAVEAT: using non-immutable types that require a netref to be constructed to serve a request,
        or invoking anything else that performs a sync_request, may timeout due to the sync_request reply being
        received by another thread serving the connection. A more conventional approach where each client thread
        opens a new connection would allow `ThreadedServer` to naturally avoid such multiplexing issues and
        is the preferred approach for threading procedures that invoke sync_request. See issue #345
        """
        def _thread_target():
            try:
                while True:
                    self.serve(None)
            except (socket.error, select_error, IOError):
                if not self.closed:
                    raise
            except EOFError:
                pass

        try:
            threads = [worker(_thread_target)
                       for _ in range(thread_count)]

            for thread in threads:
                thread.join()
        finally:
            self.close()

    def poll_all(self, timeout=0):  # serving
        """Serves all requests and replies that arrive within the given interval.

        :returns: ``True`` if at least a single transaction was served, ``False`` otherwise
        """
        at_least_once = False
        timeout = Timeout(timeout)
        try:
            while True:
                if self.poll(timeout):
                    at_least_once = True
                if timeout.expired():
                    break
        except EOFError:
            pass
        return at_least_once

    def sync_request(self, handler, *args):
        """requests, sends a synchronous request (waits for the reply to arrive)

        :raises: any exception that the requests may be generated
        :returns: the result of the request
        """
        timeout = self._config["sync_request_timeout"]
        _async_res = self.async_request(handler, *args, timeout=timeout)
        # _async_res is an instance of AsyncResult, the value property invokes Connection.serve via AsyncResult.wait
        # So, the _recvlock can be acquired multiple times by the owning thread and warrants the use of RLock
        return _async_res.value

    def _async_request(self, handler, args=(), callback=(lambda a, b: None)):  # serving
        seq = self._get_seq_id()
        self._request_callbacks[seq] = callback
        try:
            self._send(consts.MSG_REQUEST, seq, (handler, self._box(args)))
        except Exception:
            # TODO: review test_remote_exception, logging exceptions show attempt to write on closed stream
            # depending on the case, the MSG_REQUEST may or may not have been sent completely
            # so, pop the callback and raise to keep response integrity is consistent
            self._request_callbacks.pop(seq, None)
            raise

    def async_request(self, handler, *args, **kwargs):  # serving
        """Send an asynchronous request (does not wait for it to finish)

        :returns: an :class:`rpyc.core.async_.AsyncResult` object, which will
                  eventually hold the result (or exception)
        """
        timeout = kwargs.pop("timeout", None)
        if kwargs:
            raise TypeError("got unexpected keyword argument(s) {list(kwargs.keys()}")
        res = AsyncResult(self)
        if timeout is not None:
            res.set_expiry(timeout)
        self._async_request(handler, args, res)
        return res

    @property
    def root(self):  # serving
        """Fetches the root object (service) of the other party"""
        if self._remote_root is None:
            self._remote_root = self.sync_request(consts.HANDLE_GETROOT)
        return self._remote_root

    def _check_attr(self, obj, name, perm):  # attribute access
        config = self._config
        if not config[perm]:
            raise AttributeError(f"cannot access {name!r}")
        prefix = config["allow_exposed_attrs"] and config["exposed_prefix"]
        plain = config["allow_all_attrs"]
        plain |= config["allow_exposed_attrs"] and name.startswith(prefix)
        plain |= config["allow_safe_attrs"] and name in config["safe_attrs"]
        plain |= config["allow_public_attrs"] and not name.startswith("_")
        has_exposed = prefix and (hasattr(obj, prefix + name) or hasattr_static(obj, prefix + name))
        if plain and (not has_exposed or hasattr(obj, name)):
            return name
        if has_exposed:
            return prefix + name
        if plain:
            return name  # chance for better traceback
        raise AttributeError(f"cannot access {name!r}")

    def _access_attr(self, obj, name, args, overrider, param, default):  # attribute access
        if type(name) is bytes:
            name = str(name, "utf8")
        elif type(name) is not str:
            raise TypeError("name must be a string")
        accessor = getattr(type(obj), overrider, None)
        if accessor is None:
            accessor = default
            name = self._check_attr(obj, name, param)
        return accessor(obj, name, *args)

    @classmethod
    def _request_handlers(cls):  # request handlers
        return {
            consts.HANDLE_PING: cls._handle_ping,
            consts.HANDLE_CLOSE: cls._handle_close,
            consts.HANDLE_GETROOT: cls._handle_getroot,
            consts.HANDLE_GETATTR: cls._handle_getattr,
            consts.HANDLE_DELATTR: cls._handle_delattr,
            consts.HANDLE_SETATTR: cls._handle_setattr,
            consts.HANDLE_CALL: cls._handle_call,
            consts.HANDLE_CALLATTR: cls._handle_callattr,
            consts.HANDLE_REPR: cls._handle_repr,
            consts.HANDLE_STR: cls._handle_str,
            consts.HANDLE_CMP: cls._handle_cmp,
            consts.HANDLE_HASH: cls._handle_hash,
            consts.HANDLE_INSTANCECHECK: cls._handle_instancecheck,
            consts.HANDLE_DIR: cls._handle_dir,
            consts.HANDLE_PICKLE: cls._handle_pickle,
            consts.HANDLE_DEL: cls._handle_del,
            consts.HANDLE_INSPECT: cls._handle_inspect,
            consts.HANDLE_BUFFITER: cls._handle_buffiter,
            consts.HANDLE_OLDSLICING: cls._handle_oldslicing,
            consts.HANDLE_CTXEXIT: cls._handle_ctxexit,
        }

    def _handle_ping(self, data):  # request handler
        return data

    def _handle_close(self):  # request handler
        self._cleanup()

    def _handle_getroot(self):  # request handler
        return self._local_root

    def _handle_del(self, obj, count=1):  # request handler
        self._local_objects.decref(get_id_pack(obj), count)

    def _handle_repr(self, obj):  # request handler
        return repr(obj)

    def _handle_str(self, obj):  # request handler
        return str(obj)

    def _handle_cmp(self, obj, other, op='__cmp__'):  # request handler
        # cmp() might enter recursive resonance... so use the underlying type and return cmp(obj, other)
        try:
            return self._access_attr(type(obj), op, (), "_rpyc_getattr", "allow_getattr", getattr)(obj, other)
        except Exception:
            raise

    def _handle_hash(self, obj):  # request handler
        return hash(obj)

    def _handle_call(self, obj, args, kwargs=()):  # request handler
        return obj(*args, **dict(kwargs))

    def _handle_dir(self, obj):  # request handler
        return tuple(dir(obj))

    def _handle_inspect(self, id_pack):  # request handler
        if hasattr(self._local_objects[id_pack], '____conn__'):
            # When RPyC is chained (RPyC over RPyC), id_pack is cached in local objects as a netref
            # since __mro__ is not a safe attribute the request is forwarded using the proxy connection
            # see issue #346 or tests.test_rpyc_over_rpyc.Test_rpyc_over_rpyc
            conn = self._local_objects[id_pack].____conn__
            return conn.sync_request(consts.HANDLE_INSPECT, id_pack)
        else:
            return tuple(get_methods(netref.LOCAL_ATTRS, self._local_objects[id_pack]))

    def _handle_getattr(self, obj, name):  # request handler
        return self._access_attr(obj, name, (), "_rpyc_getattr", "allow_getattr", getattr)

    def _handle_delattr(self, obj, name):  # request handler
        return self._access_attr(obj, name, (), "_rpyc_delattr", "allow_delattr", delattr)

    def _handle_setattr(self, obj, name, value):  # request handler
        return self._access_attr(obj, name, (value,), "_rpyc_setattr", "allow_setattr", setattr)

    def _handle_callattr(self, obj, name, args, kwargs=()):  # request handler
        obj = self._handle_getattr(obj, name)
        return self._handle_call(obj, args, kwargs)

    def _handle_ctxexit(self, obj, exc):  # request handler
        if exc:
            try:
                raise exc
            except Exception:
                exc, typ, tb = sys.exc_info()
        else:
            typ = tb = None
        return self._handle_getattr(obj, "__exit__")(exc, typ, tb)

    def _handle_instancecheck(self, obj, other_id_pack):
        # TODOs:
        #  + refactor cache instancecheck/inspect/class_factory
        #  + improve cache docs

        if hasattr(obj, '____conn__'):  # keep unwrapping!
            # When RPyC is chained (RPyC over RPyC), id_pack is cached in local objects as a netref
            # since __mro__ is not a safe attribute the request is forwarded using the proxy connection
            # relates to issue #346 or tests.test_netref_hierachy.Test_Netref_Hierarchy.test_StandardError
            conn = obj.____conn__
            return conn.sync_request(consts.HANDLE_INSPECT, other_id_pack)
        # Create a name pack which would be familiar here and see if there is a hit
        other_id_pack2 = (other_id_pack[0], other_id_pack[1], 0)
        if other_id_pack[0] in netref.builtin_classes_cache:
            cls = netref.builtin_classes_cache[other_id_pack[0]]
            other = cls(self, other_id_pack)
        elif other_id_pack2 in self._netref_classes_cache:
            cls = self._netref_classes_cache[other_id_pack2]
            other = cls(self, other_id_pack2)
        else:  # might just have missed cache, FIX ME
            return False
        return isinstance(other, obj)

    def _handle_pickle(self, obj, proto):  # request handler
        if not self._config["allow_pickle"]:
            raise ValueError("pickling is disabled")
        return bytes(pickle.dumps(obj, proto))

    def _handle_buffiter(self, obj, count):  # request handler
        return tuple(itertools.islice(obj, count))

    def _handle_oldslicing(self, obj, attempt, fallback, start, stop, args):  # request handler
        try:
            # first try __xxxitem__
            getitem = self._handle_getattr(obj, attempt)
            return getitem(slice(start, stop), *args)
        except Exception:
            # fallback to __xxxslice__. see issue #41
            if stop is None:
                stop = maxint
            getslice = self._handle_getattr(obj, fallback)
            return getslice(start, stop, *args)


class _Thread:
    """Internal thread information for the RPYC protocol used for thread binding."""

    def __init__(self, tid, lock):
        super().__init__()

        self.tid = tid

        self._remote_thread_id = UNBOUND_THREAD_ID
        self._occupation_count = 0
        self._serve = True
        self._condition = threading.Condition(lock)
        self._deque = collections.deque()

    @property
    def serve(self):
        with self._condition:
            return self._serve

    @property
    def loop(self):
        with self._condition:
            return self._serve or bool(self._deque)

    @serve.setter
    def serve(self, value):
        with self._condition:
            if value is False and self._serve is True:
                self._serve = False
                self._deque.append(None)
                self._condition.notify()

    def decr(self):
        with self._condition:
            if self._occupation_count <= 1:
                self._occupation_count = 0
                self._remote_thread_id = UNBOUND_THREAD_ID
            else:
                self._occupation_count -= 1

    def incr(self):
        self._occupation_count += 1


class _UnlockGuard:
    def __init__(self, lock):
        self._lock = lock

    def __enter__(self):
        self._depth = 0
        while True:
            try:
                self._lock.release()
            except RuntimeError:
                break
            else:
                self._depth += 1
        return self

    def __exit__(self, t, v, tb):
        for _ in range(self._depth):
            self._lock.acquire()


class _ReceivingGuard:
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        self._connection._lock.acquire()
        self._receiver = not self._connection._receiving
        if self._receiver:
            self._connection._receiving = True
        return self

    def __exit__(self, t, v, tb):
        if self._receiver:
            self._connection._receiving = False
            for thread in self._connection._thread_pool:
                if not thread._deque:
                    thread._condition.notify()
                    break
        self._connection._lock.release()
