"""Pruebas unitarias de src/registry.py (UT-04 a UT-07 y UT-13)."""

import threading

from src import registry


def test_ut04_apodo_repetido_se_rechaza():
    reg = registry.ClientRegistry()
    assert reg.add("Ana", object()) == registry.ADDED
    assert reg.add("Ana", object()) == registry.DUPLICATE
    # También se rechaza aunque cambien las mayúsculas
    assert reg.add("ANA", object()) == registry.DUPLICATE
    assert reg.count() == 1


def test_ut05_se_aceptan_los_10_clientes():
    reg = registry.ClientRegistry()
    for i in range(10):
        assert reg.add(f"usuario{i}", object()) == registry.ADDED
    assert reg.count() == 10
    assert reg.is_full()


def test_ut06_el_cliente_11_se_rechaza_por_lleno():
    reg = registry.ClientRegistry()
    for i in range(10):
        reg.add(f"usuario{i}", object())
    assert reg.add("usuario11", object()) == registry.FULL
    assert reg.count() == 10


def test_ut07_al_eliminar_un_cliente_se_libera_el_cupo():
    reg = registry.ClientRegistry()
    for i in range(10):
        reg.add(f"usuario{i}", object())
    assert reg.add("nuevo", object()) == registry.FULL

    assert reg.remove("usuario3") is True
    assert reg.count() == 9
    assert reg.add("nuevo", object()) == registry.ADDED
    assert reg.count() == 10
    # Eliminar a alguien que no existe no rompe nada
    assert reg.remove("fantasma") is False


def test_ut13_50_hilos_a_la_vez_nunca_superan_el_limite():
    reg = registry.ClientRegistry()
    hilos_totales = 50
    barrera = threading.Barrier(hilos_totales)
    resultados = []
    candado = threading.Lock()

    def intentar_registro(numero):
        barrera.wait()  # todos arrancan al mismo tiempo
        resultado = reg.add(f"usuario{numero}", object())
        with candado:
            resultados.append(resultado)

    hilos = [threading.Thread(target=intentar_registro, args=(n,))
             for n in range(hilos_totales)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert len(resultados) == hilos_totales
    assert resultados.count(registry.ADDED) == 10
    assert resultados.count(registry.FULL) == 40
    assert reg.count() == 10
