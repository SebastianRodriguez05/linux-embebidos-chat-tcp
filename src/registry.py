"""Registro de clientes conectados: límite de usuarios y apodos únicos."""

import threading

from src import protocol

ADDED = "added"
FULL = "full"
DUPLICATE = "duplicate"


class ClientRegistry:
    def __init__(self, max_clients=protocol.MAX_CLIENTS):
        self._max_clients = max_clients
        self._clients = {}  # apodo en minúsculas -> (apodo, cliente)
        self._lock = threading.Lock()

    def add(self, nickname, client):
        """Intenta registrar un cliente. Devuelve ADDED, FULL o DUPLICATE."""
        key = nickname.casefold()
        with self._lock:
            if len(self._clients) >= self._max_clients:
                return FULL
            if key in self._clients:
                return DUPLICATE
            self._clients[key] = (nickname, client)
            return ADDED

    def remove(self, nickname):
        """Elimina un cliente y libera su cupo. Devuelve True si existía."""
        with self._lock:
            return self._clients.pop(nickname.casefold(), None) is not None

    def is_full(self):
        with self._lock:
            return len(self._clients) >= self._max_clients

    def count(self):
        with self._lock:
            return len(self._clients)

    def snapshot(self):
        """Copia de la lista [(apodo, cliente), ...] para recorrerla sin lock."""
        with self._lock:
            return list(self._clients.values())