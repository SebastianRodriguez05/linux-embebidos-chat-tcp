"""Servidor de chat TCP: un hilo por cliente."""

import argparse
import logging
import socket
import threading

from src import protocol, registry

log = logging.getLogger("chat.server")


class Client:
    """Conexión de un cliente: envío seguro entre hilos y lectura por líneas."""

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.nickname = None
        self._send_lock = threading.Lock()
        self._reader = conn.makefile("rb")

    def send(self, text):
        """Envía una línea. Devuelve False si la conexión falló."""
        try:
            with self._send_lock:
                self.conn.sendall(protocol.encode_line(text))
            return True
        except OSError:
            return False

    def read_line(self):
        """Devuelve (texto, demasiado_largo) o None si el cliente se fue."""
        try:
            data = self._reader.readline(protocol.MAX_LINE_BYTES)
            if not data:
                return None
            too_long = False
            if not data.endswith(b"\n") and len(data) >= protocol.MAX_LINE_BYTES:
                too_long = True
                # Descarta el resto de la línea gigante
                while True:
                    rest = self._reader.readline(protocol.MAX_LINE_BYTES)
                    if not rest or rest.endswith(b"\n"):
                        break
            return protocol.decode_line(data), too_long
        except (OSError, ValueError):
            return None

    def shutdown(self):
        """Corta la conexión. Es seguro llamarlo desde cualquier hilo."""
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def close(self):
        """Cierre completo. Solo lo llama el hilo dueño del cliente."""
        self.shutdown()
        try:
            self._reader.close()
        except (OSError, ValueError):
            pass
        self.conn.close()


class ChatServer:
    def __init__(self, host=protocol.DEFAULT_HOST, port=protocol.DEFAULT_PORT,
                 max_clients=protocol.MAX_CLIENTS):
        self.host = host
        self.port = port
        self.registry = registry.ClientRegistry(max_clients)
        self._sock = None
        self._running = False

    def start(self):
        """Abre el puerto. Con port=0 el sistema elige uno libre."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen()
        self.port = self._sock.getsockname()[1]
        self._running = True

    def serve_forever(self):
        """Ciclo de aceptación: un hilo por cada cliente."""
        while self._running:
            try:
                conn, addr = self._sock.accept()
            except OSError:
                break
            threading.Thread(target=self._handle_client, args=(conn, addr),
                             daemon=True).start()

    def stop(self):
        self._running = False
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._sock.close()
        for _, client in self.registry.snapshot():
            client.shutdown()

    # ---------- atención de un cliente ----------

    def _handle_client(self, conn, addr):
        client = Client(conn, addr)
        registered = False
        try:
            log.info("Conexión desde %s:%s", *addr[:2])
            if self.registry.is_full():
                client.send(protocol.format_notice("Servidor lleno. Intenta más tarde."))
                return
            if not self._register(client):
                return
            registered = True
            client.send(protocol.format_notice(f"Bienvenido, {client.nickname}"))
            self._broadcast(protocol.notice_join(client.nickname), exclude=client)
            log.info("%s entró (%d conectados)", client.nickname, self.registry.count())
            self._chat_loop(client)
        except Exception:
            log.exception("Error inesperado con el cliente %s", addr)
        finally:
            if registered:
                self.registry.remove(client.nickname)
                self._broadcast(protocol.notice_leave(client.nickname), exclude=client)
                log.info("%s salió (%d conectados)", client.nickname, self.registry.count())
            client.close()

    def _register(self, client):
        """Pide el apodo hasta que sea válido. Devuelve False si no se pudo."""
        while True:
            client.send(protocol.format_notice("Ingresa tu apodo:"))
            result = client.read_line()
            if result is None:
                return False
            text, too_long = result
            nickname = text.strip()
            status = protocol.TOO_LONG if too_long else protocol.validate_nickname(nickname)
            if status == protocol.EMPTY:
                client.send(protocol.format_notice("El apodo no puede estar vacío."))
                continue
            if status == protocol.TOO_LONG:
                client.send(protocol.format_notice(
                    f"El apodo no puede superar {protocol.MAX_NICK_LEN} caracteres."))
                continue
            outcome = self.registry.add(nickname, client)
            if outcome == registry.FULL:
                client.send(protocol.format_notice("Servidor lleno. Intenta más tarde."))
                return False
            if outcome == registry.DUPLICATE:
                client.send(protocol.format_notice("Ese apodo ya está en uso."))
                continue
            client.nickname = nickname
            return True

    def _chat_loop(self, client):
        """Lee mensajes hasta que el cliente sale o se desconecta."""
        while True:
            result = client.read_line()
            if result is None:
                return  # desconexión inesperada
            text, too_long = result
            text = text.strip()
            if text.lower() == protocol.EXIT_COMMAND:
                return  # salida voluntaria
            status = protocol.TOO_LONG if too_long else protocol.validate_message(text)
            if status == protocol.EMPTY:
                continue
            if status == protocol.TOO_LONG:
                client.send(protocol.format_notice(
                    f"Mensaje demasiado largo (máximo {protocol.MAX_MSG_LEN} caracteres)."))
                continue
            self._broadcast(protocol.format_message(client.nickname, text), exclude=client)

    def _broadcast(self, text, exclude=None):
        """Envía a todos los demás. Si un envío falla, corta esa conexión y
        el hilo de ese cliente se encarga de limpiar y avisar."""
        for _, client in self.registry.snapshot():
            if client is exclude:
                continue
            if not client.send(text):
                client.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Servidor de chat TCP")
    parser.add_argument("--host", default=protocol.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=protocol.DEFAULT_PORT)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    server = ChatServer(args.host, args.port)
    server.start()
    print(f"Servidor escuchando en {args.host}:{server.port} (Ctrl+C para detener)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()