"""Windows: the app keeps listening when a client drops a connection before it is accepted.

On Windows asyncio accepts connections through the proactor, and when an accept fails with an OSError its loop logs
"Accept failed on a socket" and closes the listening socket (asyncio/proactor_events.py, _start_serving). A client
that gives up on a connection before it is accepted (the launcher's one-second check while the app is still starting,
say) fails the accept with WinError 64, "the specified network name is no longer available": the app then went on
running with nothing listening, and the launcher, hearing no answer, stopped it after three minutes. A dropped
connection is the client's business, not a reason to stop serving, so for those errors the loop waits for the next.

The function is asyncio's own (Python 3.13), with only that one change.
"""
from __future__ import annotations

import logging
import sys

log = logging.getLogger("yue2")

# ERROR_NETNAME_DELETED, ERROR_CONNECTION_ABORTED, ERROR_OPERATION_ABORTED while the socket is still open:
# the client went away, the listening socket is fine.
DROPPED = {64, 1236}


def install() -> None:
    if sys.platform != "win32":
        return
    from asyncio import exceptions, proactor_events, trsock

    base = proactor_events.BaseProactorEventLoop
    if getattr(base._start_serving, "_keeps_listening", False):
        return

    def _start_serving(self, protocol_factory, sock, sslcontext=None, server=None, backlog=100,
                       ssl_handshake_timeout=None, ssl_shutdown_timeout=None):

        def loop(f=None):
            try:
                if f is not None:
                    conn, addr = f.result()
                    protocol = protocol_factory()
                    if sslcontext is not None:
                        self._make_ssl_transport(
                            conn, protocol, sslcontext, server_side=True,
                            extra={'peername': addr}, server=server,
                            ssl_handshake_timeout=ssl_handshake_timeout,
                            ssl_shutdown_timeout=ssl_shutdown_timeout)
                    else:
                        self._make_socket_transport(conn, protocol, extra={'peername': addr}, server=server)
                if self.is_closed():
                    return
                f = self._proactor.accept(sock)
            except OSError as exc:
                if sock.fileno() != -1 and getattr(exc, "winerror", None) in DROPPED:
                    log.warning("A connection to the app was dropped before it was accepted (%s); still listening", exc)
                    self.call_soon(loop)
                    return
                if sock.fileno() != -1:
                    self.call_exception_handler({
                        'message': 'Accept failed on a socket',
                        'exception': exc,
                        'socket': trsock.TransportSocket(sock),
                    })
                    sock.close()
            except exceptions.CancelledError:
                sock.close()
            else:
                self._accept_futures[sock.fileno()] = f
                f.add_done_callback(loop)

        self.call_soon(loop)

    _start_serving._keeps_listening = True
    base._start_serving = _start_serving
