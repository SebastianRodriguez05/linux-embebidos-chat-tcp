"""Pruebas de integración (IT-01 a IT-16).

Servidor real y clientes reales conectados por sockets en localhost.
"""

import os
import queue
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from src import protocol
from src.server import ChatServer

RAIZ = Path(__file__).resolve().parent.parent
PROMPT_APODO = "* Ingresa tu apodo:"
MSG_LLENO = "* Servidor lleno. Intenta más tarde."


# ---------------------------------------------------------------- utilidades

class ClienteTexto:
    """Cliente mínimo por socket, solo para las pruebas."""

    def __init__(self, puerto, host="127.0.0.1"):
        self.sock = socket.create_connection((host, puerto), timeout=3)
        self._buf = b""

    def enviar(self, texto):
        self.sock.sendall((texto + "\n").encode("utf-8"))

    def enviar_bytes(self, datos):
        self.sock.sendall(datos)

    def leer_linea(self, timeout=3.0):
        """Siguiente línea; None si el servidor cerró la conexión.
        Lanza TimeoutError si no llega nada a tiempo."""
        limite = time.monotonic() + timeout
        while b"\n" not in self._buf:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise TimeoutError("no llegó ninguna línea a tiempo")
            self.sock.settimeout(restante)
            try:
                datos = self.sock.recv(4096)
            except ConnectionResetError:
                datos = b""
            if not datos:
                return None
            self._buf += datos
        linea, self._buf = self._buf.split(b"\n", 1)
        return linea.decode("utf-8", errors="replace").rstrip("\r")

    def esperar(self, esperado, timeout=3.0, prefijo=False):
        """Lee líneas hasta encontrar la esperada.
        Devuelve la lista de líneas que se saltó por el camino."""
        limite = time.monotonic() + timeout
        saltadas = []
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise AssertionError(
                    f"No llegó {esperado!r}. Líneas vistas: {saltadas}")
            try:
                linea = self.leer_linea(restante)
            except TimeoutError:
                raise AssertionError(
                    f"No llegó {esperado!r}. Líneas vistas: {saltadas}") from None
            if linea is None:
                raise AssertionError(
                    f"La conexión se cerró antes de recibir {esperado!r}. "
                    f"Líneas vistas: {saltadas}")
            coincide = linea.startswith(esperado) if prefijo else linea == esperado
            if coincide:
                return saltadas
            saltadas.append(linea)

    def esperar_cierre(self, timeout=3.0):
        """Lee hasta que el servidor cierra la conexión. Devuelve lo leído."""
        limite = time.monotonic() + timeout
        leidas = []
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise AssertionError("El servidor no cerró la conexión a tiempo")
            try:
                linea = self.leer_linea(restante)
            except TimeoutError:
                raise AssertionError(
                    "El servidor no cerró la conexión a tiempo") from None
            if linea is None:
                return leidas
            leidas.append(linea)

    def entrar(self, apodo):
        self.esperar(PROMPT_APODO)
        self.enviar(apodo)
        self.esperar(f"* Bienvenido, {apodo}")

    def cerrar(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


class ProcesoCliente:
    """Ejecuta el client.py real como proceso aparte (IT-12)."""

    def __init__(self, puerto):
        entorno = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "src.client", "127.0.0.1", str(puerto)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            bufsize=1, cwd=RAIZ, env=entorno)
        self._lineas = queue.Queue()
        threading.Thread(target=self._leer, daemon=True).start()

    def _leer(self):
        for linea in self.proc.stdout:
            self._lineas.put(linea.rstrip("\n"))
        self._lineas.put(None)

    def esperar(self, esperado, timeout=5.0):
        limite = time.monotonic() + timeout
        vistas = []
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise AssertionError(
                    f"El cliente no mostró {esperado!r}. Salida vista: {vistas}")
            try:
                linea = self._lineas.get(timeout=restante)
            except queue.Empty:
                raise AssertionError(
                    f"El cliente no mostró {esperado!r}. Salida vista: {vistas}"
                ) from None
            if linea is None:
                raise AssertionError(
                    f"El cliente terminó sin mostrar {esperado!r}. Salida vista: {vistas}")
            if linea.strip() == esperado:
                return
            vistas.append(linea)

    def escribir(self, texto):
        self.proc.stdin.write(texto + "\n")
        self.proc.stdin.flush()

    def terminar(self):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()
        for flujo in (self.proc.stdin, self.proc.stdout):
            try:
                flujo.close()
            except OSError:
                pass


def esperar_hasta(condicion, timeout=3.0):
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        if condicion():
            return True
        time.sleep(0.02)
    return condicion()


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def servidor():
    srv = ChatServer(host="127.0.0.1", port=0)  # puerto 0: el sistema elige uno libre
    srv.start()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.stop()


@pytest.fixture
def conectar(servidor):
    """Fábrica de clientes; los cierra todos al terminar la prueba."""
    abiertos = []

    def _conectar(apodo=None):
        cliente = ClienteTexto(servidor.port)
        abiertos.append(cliente)
        if apodo is not None:
            cliente.entrar(apodo)
        return cliente

    yield _conectar
    for cliente in abiertos:
        cliente.cerrar()


# ------------------------------------------------------------------- pruebas

def test_it01_el_cliente_recibe_la_solicitud_de_apodo(conectar):
    c = conectar()
    c.esperar(PROMPT_APODO)


def test_it02_apodo_invalido_se_rechaza_y_se_vuelve_a_pedir(conectar):
    c = conectar()
    c.esperar(PROMPT_APODO)
    c.enviar("")
    c.esperar("* El apodo no puede estar vacío.")
    c.esperar(PROMPT_APODO)
    c.enviar("a" * (protocol.MAX_NICK_LEN + 1))
    c.esperar(f"* El apodo no puede superar {protocol.MAX_NICK_LEN} caracteres.")
    c.esperar(PROMPT_APODO)
    c.enviar("Ana")
    c.esperar("* Bienvenido, Ana")


def test_it03_el_segundo_cliente_con_el_mismo_apodo_es_rechazado(conectar):
    conectar("Ana")
    b = conectar()
    b.esperar(PROMPT_APODO)
    b.enviar("Ana")
    b.esperar("* Ese apodo ya está en uso.")
    b.esperar(PROMPT_APODO)
    b.enviar("ANA")  # distinta capitalización, mismo apodo
    b.esperar("* Ese apodo ya está en uso.")
    b.esperar(PROMPT_APODO)
    b.enviar("Beto")
    b.esperar("* Bienvenido, Beto")


def test_it04_diez_clientes_quedan_dentro_de_la_sala(servidor, conectar):
    for i in range(10):
        conectar(f"usuario{i}")
    assert esperar_hasta(lambda: servidor.registry.count() == 10)


def test_it05_el_cliente_11_recibe_servidor_lleno_y_los_demas_siguen(servidor, conectar):
    clientes = [conectar(f"usuario{i}") for i in range(10)]

    extra = conectar()
    extra.esperar(MSG_LLENO)
    extra.esperar_cierre()  # el servidor cerró su conexión

    assert servidor.registry.count() == 10
    clientes[0].enviar("sigo aquí")
    clientes[1].esperar("[usuario0] sigo aquí")


def test_it06_el_mensaje_llega_a_los_demas_y_no_vuelve_al_autor(conectar):
    ana = conectar("Ana")
    beto = conectar("Beto")
    carla = conectar("Carla")

    ana.enviar("hola")
    beto.esperar("[Ana] hola")
    carla.esperar("[Ana] hola")

    # UTF-8: tildes, eñes y signos de apertura
    ana.enviar("¡Qué año! ¿Cómo está la canción?")
    beto.esperar("[Ana] ¡Qué año! ¿Cómo está la canción?")

    # Ana no recibió eco de sus propios mensajes
    beto.enviar("ok")
    vistos_por_ana = ana.esperar("[Beto] ok")
    assert not any(linea.startswith("[Ana]") for linea in vistos_por_ana)


def test_it07_los_mensajes_vacios_no_llegan_a_nadie(conectar):
    ana = conectar("Ana")
    beto = conectar("Beto")

    ana.enviar("")
    ana.enviar("     ")
    ana.enviar("después")
    vistos = beto.esperar("[Ana] después")
    assert not any(linea.startswith("[Ana]") for linea in vistos)


def test_it08_mensaje_de_501_caracteres_se_rechaza_y_no_llega_a_otros(conectar):
    ana = conectar("Ana")
    beto = conectar("Beto")

    ana.enviar("a" * (protocol.MAX_MSG_LEN + 1))
    ana.esperar(
        f"* Mensaje demasiado largo (máximo {protocol.MAX_MSG_LEN} caracteres).")

    ana.enviar("ok")
    vistos = beto.esperar("[Ana] ok")
    assert not any("a" * 50 in linea for linea in vistos)


def test_it09_avisos_de_entrada_y_salida(conectar):
    ana = conectar("Ana")
    beto = conectar("Beto")
    ana.esperar("* Beto entró al chat")
    beto.enviar("/salir")
    ana.esperar("* Beto salió del chat")


def test_it10_salir_libera_el_cupo_y_entra_un_cliente_nuevo(servidor, conectar):
    clientes = [conectar(f"usuario{i}") for i in range(10)]

    clientes[0].enviar("/salir")
    clientes[0].esperar_cierre()  # su conexión quedó cerrada
    assert esperar_hasta(lambda: servidor.registry.count() == 9)

    conectar("nuevo")  # falla si el servidor aún dijera "lleno"
    assert servidor.registry.count() == 10
    clientes[1].esperar("* nuevo entró al chat")


def test_it11_desconexion_inesperada_libera_el_cupo_y_el_servidor_sigue(servidor, conectar):
    ana = conectar("Ana")
    beto = conectar("Beto")

    beto.cerrar()  # corta el socket sin enviar /salir
    ana.esperar("* Beto salió del chat")
    assert esperar_hasta(lambda: servidor.registry.count() == 1)

    conectar("Carla")  # el servidor sigue aceptando gente
    ana.esperar("* Carla entró al chat")


def test_it12_cliente_real_envia_y_recibe_en_la_misma_sesion(servidor, conectar):
    cli = ProcesoCliente(servidor.port)
    try:
        cli.esperar(PROMPT_APODO)
        cli.escribir("Ana")
        cli.esperar("* Bienvenido, Ana")

        beto = conectar("Beto")
        cli.esperar("* Beto entró al chat")        # recibe sin haber escrito nada

        cli.escribir("hola desde el cliente")      # envía
        beto.esperar("[Ana] hola desde el cliente")

        beto.enviar("respuesta de Beto")           # y vuelve a recibir
        cli.esperar("[Beto] respuesta de Beto")

        cli.escribir("/salir")
        assert cli.proc.wait(timeout=5) == 0
    finally:
        cli.terminar()


def test_it13_cliente_sin_servidor_muestra_error_claro():
    puerto = puerto_libre()  # nadie escucha en este puerto
    resultado = subprocess.run(
        [sys.executable, "-m", "src.client", "127.0.0.1", str(puerto)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True,
        encoding="utf-8", timeout=15, cwd=RAIZ)
    assert resultado.returncode == 1
    assert "No se pudo conectar" in resultado.stderr
    assert "Traceback" not in resultado.stderr + resultado.stdout


def test_it14_el_mensaje_llega_en_menos_de_un_segundo(conectar):
    ana = conectar("Ana")
    beto = conectar("Beto")

    tiempos = []
    for i in range(20):
        inicio = time.perf_counter()
        ana.enviar(f"ping {i}")
        beto.esperar(f"[Ana] ping {i}")
        tiempos.append(time.perf_counter() - inicio)
    assert max(tiempos) < 1.0, f"Tiempo máximo: {max(tiempos):.3f} s"


def test_it15_datos_basura_no_tumban_el_servidor(conectar):
    raro = conectar()
    raro.esperar(PROMPT_APODO)
    raro.enviar_bytes(b"\xff\xfe\x80\n")            # apodo que no es UTF-8 válido
    raro.esperar("* Bienvenido, ", prefijo=True)
    raro.enviar_bytes(b"\x00\x01\x02\xff\xfe\n")    # mensaje con bytes basura
    raro.enviar_bytes(b"x" * 10000 + b"\n")         # línea gigante, sin control
    raro.esperar(
        f"* Mensaje demasiado largo (máximo {protocol.MAX_MSG_LEN} caracteres).")

    # Otros clientes

    ana = conectar("Ana")
    beto = conectar("Beto")
    ana.enviar("hola")
    beto.esperar("[Ana] hola")


def test_it16_el_servidor_acepta_conexiones_en_otro_puerto():
    puerto = puerto_libre()
    assert puerto != protocol.DEFAULT_PORT
    srv = ChatServer(host="127.0.0.1", port=puerto)
    srv.start()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        assert srv.port == puerto
        cliente = ClienteTexto(puerto)
        try:
            cliente.entrar("Ana")
        finally:
            cliente.cerrar()
    finally:
        srv.stop()
