"""Constantes y funciones puras del protocolo del chat (sin red)."""

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
MAX_CLIENTS = 10
MAX_NICK_LEN = 20
MAX_MSG_LEN = 500
MAX_LINE_BYTES = 4096
ENCODING = "utf-8"
EXIT_COMMAND = "/salir"

# Resultados de validación
OK = "ok"
EMPTY = "empty"
TOO_LONG = "too_long"


def validate_nickname(nickname):
    """Devuelve OK, EMPTY o TOO_LONG."""
    nickname = nickname.strip()
    if not nickname:
        return EMPTY
    if len(nickname) > MAX_NICK_LEN:
        return TOO_LONG
    return OK


def validate_message(text):
    """Devuelve OK, EMPTY o TOO_LONG."""
    text = text.strip()
    if not text:
        return EMPTY
    if len(text) > MAX_MSG_LEN:
        return TOO_LONG
    return OK


def format_message(nickname, text):
    return f"[{nickname}] {text}"


def format_notice(text):
    return f"* {text}"


def notice_join(nickname):
    return format_notice(f"{nickname} entró al chat")


def notice_leave(nickname):
    return format_notice(f"{nickname} salió del chat")


def encode_line(text):
    """Texto -> bytes UTF-8 terminados en salto de línea."""
    return (text + "\n").encode(ENCODING)


def decode_line(data):
    """Bytes -> texto. Nunca lanza excepción por bytes inválidos."""
    return data.decode(ENCODING, errors="replace").rstrip("\r\n")