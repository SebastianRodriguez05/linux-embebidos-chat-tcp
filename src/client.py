"""Cliente de chat de consola: un hilo recibe y el hilo principal envía."""

import argparse
import os
import signal
import socket
import sys
import threading

from src import protocol


def receive_loop(reader, leaving):
    """Muestra en pantalla todo lo que llega del servidor.

    Si el servidor cierra la conexión sin que el usuario haya pedido salir,
    avisa e interrumpe el input() del hilo principal.
    """
    try:
        for raw in reader:
            print(protocol.decode_line(raw), flush=True)
    except (OSError, ValueError):
        pass
    if not leaving.is_set():
        print("* Conexión cerrada por el servidor.", flush=True)
        os.kill(os.getpid(), signal.SIGINT)


def run_client(host, port):
    try:
        sock = socket.create_connection((host, port), timeout=5)
    except OSError as exc:
        detalle = exc.strerror or exc
        print(f"No se pudo conectar a {host}:{port} ({detalle}). "
              "Verifica que el servidor esté en ejecución.", file=sys.stderr)
        return 1
    sock.settimeout(None)

    leaving = threading.Event()
    reader = sock.makefile("rb")
    receiver = threading.Thread(target=receive_loop, args=(reader, leaving),
                                daemon=True)
    receiver.start()

    try:
        while True:
            line = input()
            saliendo = line.strip().lower() == protocol.EXIT_COMMAND
            if saliendo:
                leaving.set()  # antes de enviar, para no confundir el cierre con una caída
            sock.sendall(protocol.encode_line(line))
            if saliendo:
                receiver.join(timeout=2)
                break
    except (EOFError, KeyboardInterrupt):
        pass
    except OSError:
        print("* Se perdió la conexión con el servidor.")
    finally:
        leaving.set()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Cliente de chat TCP")
    parser.add_argument("host", nargs="?", default="127.0.0.1")
    parser.add_argument("port", nargs="?", type=int, default=protocol.DEFAULT_PORT)
    args = parser.parse_args()
    sys.exit(run_client(args.host, args.port))


if __name__ == "__main__":
    main()
