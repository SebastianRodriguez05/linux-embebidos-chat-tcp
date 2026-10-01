"""Pruebas unitarias de src/protocol.py (UT-01 a UT-03, UT-08 a UT-12, UT-14)."""

from src import protocol


def test_ut01_apodo_valido_se_acepta():
    assert protocol.validate_nickname("Ana") == protocol.OK


def test_ut02_apodo_vacio_o_solo_espacios_se_rechaza():
    assert protocol.validate_nickname("") == protocol.EMPTY
    assert protocol.validate_nickname("     ") == protocol.EMPTY


def test_ut03_limite_de_20_caracteres_en_el_apodo():
    assert protocol.validate_nickname("a" * 20) == protocol.OK
    assert protocol.validate_nickname("a" * 21) == protocol.TOO_LONG


def test_ut08_mensaje_vacio_o_solo_espacios_se_ignora():
    assert protocol.validate_message("") == protocol.EMPTY
    assert protocol.validate_message("   \t  ") == protocol.EMPTY


def test_ut09_limite_de_500_caracteres_en_el_mensaje():
    assert protocol.validate_message("a" * 500) == protocol.OK
    assert protocol.validate_message("a" * 501) == protocol.TOO_LONG


def test_ut10_formato_de_mensaje_con_apodo():
    assert protocol.format_message("Ana", "hola") == "[Ana] hola"


def test_ut11_formato_de_avisos_de_entrada_y_salida():
    assert protocol.notice_join("Ana") == "* Ana entró al chat"
    assert protocol.notice_leave("Ana") == "* Ana salió del chat"


def test_ut12_codificacion_utf8_ida_y_vuelta_con_tildes_y_enie():
    texto = "Año, canción"
    datos = protocol.encode_line(texto)
    assert datos.endswith(b"\n")
    assert protocol.decode_line(datos) == texto


def test_ut14_bytes_invalidos_no_lanzan_excepcion():
    resultado = protocol.decode_line(b"\xff\xfe\x80abc\n")
    assert isinstance(resultado, str)
    assert resultado.endswith("abc")
