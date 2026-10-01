# Matriz de verificación

## 1. Criterios
- **Unitaria (UT):** prueba la lógica sin red (`protocol.py` y `registry.py`).
  Archivos: `tests/test_protocol.py` y `tests/test_registry.py`.
- **Integración (IT):** prueba el servidor y los clientes reales conectados por
  sockets en `localhost`. Archivo: `tests/test_integration.py`.
- **Inspección (INS):** verificación manual o por revisión del entorno.
- Las pruebas se ejecutan con `python -m pytest -v` dentro del entorno virtual.

## 2. Matriz requisito → prueba

| Requisito | Descripción corta                                   | Método    | Pruebas                 | Estado    |
|-----------|-----------------------------------------------------|-----------|-------------------------|-----------|
| RF-01     | Aceptar conexiones TCP en puerto configurable       | IT        | IT-01, IT-16            | Aprobado  |
| RF-02     | Solicitar apodo al conectarse                       | IT        | IT-01, IT-02            | Aprobado  |
| RF-03     | Rechazar apodos vacíos, repetidos o de más de 20    | UT, IT    | UT-01, UT-02, UT-03, UT-04, IT-02, IT-03 | Aprobado  |
| RF-04     | Máximo 10 clientes simultáneos                      | UT, IT    | UT-05, UT-06, UT-13, IT-04 | Aprobado  |
| RF-05     | Informar "servidor lleno" al cliente 11 y cerrarlo  | UT, IT    | UT-06, IT-05            | Aprobado  |
| RF-06     | Retransmitir mensajes a los demás con el apodo      | UT, IT    | UT-10, IT-06            | Aprobado  |
| RF-07     | Ignorar mensajes vacíos                             | UT, IT    | UT-08, IT-07            | Aprobado  |
| RF-08     | Rechazar mensajes de más de 500 caracteres          | UT, IT    | UT-09, IT-08            | Aprobado  |
| RF-09     | Avisar cuando un usuario entra o sale               | UT, IT    | UT-11, IT-09            | Aprobado  |
| RF-10     | `/salir` cierra la conexión y libera el cupo        | UT, IT    | UT-07, IT-10            | Aprobado  |
| RF-11     | Detectar desconexión inesperada y seguir funcionando| UT, IT    | UT-07, IT-11            | Aprobado  |
| RF-12     | Cliente escribe y recibe al mismo tiempo            | IT        | IT-12                   | Aprobado  |
| RF-13     | Cliente muestra error claro si no hay servidor      | IT        | IT-13                   | Aprobado  |
| RNF-01    | Mensajes en UTF-8, un mensaje por línea             | UT, IT    | UT-12, IT-06            | Aprobado  |
| RNF-02    | Ejecución en Ubuntu (WSL2) con Python 3             | INS       | INS-01                  | Aprobado  |
| RNF-03    | Mensaje entregado en menos de 1 segundo (red local) | IT        | IT-14                   | Aprobado  |
| RNF-04    | El servidor no se cae por datos malformados         | UT, IT    | UT-13, UT-14, IT-15     | Aprobado  |

## 3. Catálogo de pruebas

### 3.1 Pruebas unitarias

| ID    | Archivo            | Qué verifica                                                      | Resultado esperado                              |
|-------|--------------------|-------------------------------------------------------------------|-------------------------------------------------|
| UT-01 | test_protocol.py   | Validar un apodo correcto ("Ana")                                 | Se acepta                                       |
| UT-02 | test_protocol.py   | Validar apodo vacío o solo espacios                               | Se rechaza                                      |
| UT-03 | test_protocol.py   | Apodo de 20 caracteres y de 21 caracteres                         | 20 se acepta, 21 se rechaza                     |
| UT-04 | test_registry.py   | Registrar un apodo que ya existe                                  | Se rechaza                                      |
| UT-05 | test_registry.py   | Registrar 10 clientes distintos                                   | Los 10 se aceptan                               |
| UT-06 | test_registry.py   | Registrar un cliente número 11                                    | Se rechaza por lleno                            |
| UT-07 | test_registry.py   | Eliminar un cliente y registrar otro                              | El cupo se libera y el nuevo se acepta          |
| UT-08 | test_protocol.py   | Validar mensaje vacío o solo espacios                             | Se ignora                                       |
| UT-09 | test_protocol.py   | Mensaje de 500 caracteres y de 501 caracteres                     | 500 se acepta, 501 se rechaza                   |
| UT-10 | test_protocol.py   | Dar formato a un mensaje de "Ana" con texto "hola"                | `[Ana] hola`                                    |
| UT-11 | test_protocol.py   | Dar formato a avisos de entrada y salida                          | `* Ana entró al chat`, `* Ana salió del chat`   |
| UT-12 | test_protocol.py   | Codificar y decodificar texto con tildes y ñ ("Año, canción")     | El texto vuelve idéntico                        |
| UT-13 | test_registry.py   | 50 hilos intentan registrarse a la vez                            | Nunca hay más de 10 registrados                 |
| UT-14 | test_protocol.py   | Decodificar bytes que no son UTF-8 válido                         | No lanza excepción sin controlar                |

### 3.2 Pruebas de integración

| ID    | Qué verifica                                                              | Resultado esperado                                              |
|-------|---------------------------------------------------------------------------|-----------------------------------------------------------------|
| IT-01 | Un cliente se conecta al servidor                                         | Recibe la solicitud de apodo                                    |
| IT-02 | Un cliente envía un apodo inválido (vacío)                                | El servidor lo rechaza y vuelve a pedirlo                       |
| IT-03 | Dos clientes intentan usar el mismo apodo                                 | El segundo es rechazado                                         |
| IT-04 | 10 clientes se conectan con apodos distintos                              | Los 10 quedan dentro de la sala                                 |
| IT-05 | Un cliente 11 se conecta con 10 ya dentro                                 | Recibe "servidor lleno", su conexión se cierra y los 10 siguen conectados |
| IT-06 | Ana envía "hola" con Beto y Carla conectados                              | Beto y Carla reciben `[Ana] hola`; Ana no lo recibe de vuelta   |
| IT-07 | Un cliente envía un mensaje vacío                                         | Nadie recibe nada                                               |
| IT-08 | Un cliente envía un mensaje de 501 caracteres                             | El autor recibe un aviso de error y nadie más lo recibe         |
| IT-09 | Un cliente entra y luego sale con otro ya conectado                       | El otro recibe los avisos de entrada y de salida                |
| IT-10 | Con 10 conectados, uno envía `/salir` y entra un nuevo cliente            | El que salió queda desconectado y el nuevo cliente es aceptado  |
| IT-11 | Un cliente cierra el socket sin enviar `/salir`                           | El servidor sigue activo, libera el cupo y avisa a los demás    |
| IT-12 | Se ejecuta `client.py` y se envía y recibe texto en la misma sesión       | Ambas acciones funcionan sin bloquearse                         |
| IT-13 | Se ejecuta `client.py` sin servidor activo                                | Muestra un error claro y termina sin traza de Python            |
| IT-14 | Se mide el tiempo entre que Ana envía y Beto recibe                       | Menos de 1 segundo                                              |
| IT-15 | Un cliente envía bytes basura y luego otro cliente chatea con normalidad  | El servidor no se cae y el chat sigue funcionando               |
| IT-16 | Se inicia el servidor en un puerto distinto al 5000                       | Acepta conexiones en ese puerto                                 |

### 3.3 Inspección

| ID     | Qué verifica                                                      | Resultado esperado                                   |
|--------|-------------------------------------------------------------------|------------------------------------------------------|
| INS-01 | Ejecutar `python3 --version` y `uname -a` en el entorno de trabajo| Python 3 sobre Ubuntu en WSL2, y el proyecto corre sin cambios |

## 4. Cobertura
Todos los requisitos RF-01 a RF-13 y RNF-01 a RNF-04 tienen al menos una
prueba asociada. Si se agrega un requisito nuevo, debe agregarse su fila en
la matriz y al menos una prueba en el catálogo.S
## 5. Resultados de la ejecución

- Fecha: 2026-09-30
- Resultado: **30 pruebas aprobadas** (14 unitarias y 16 de integración), 0 fallos.
- Estabilidad: la suite completa se ejecutó 5 veces seguidas con el mismo resultado.
- Comando: `python -m pytest -v`

### Inspección INS-01 (entorno)

```
$ python3 --version
Python 3.14.4
$ uname -a
Linux HELEN 6.18.33.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun 18 21:54:43 UTC 2026 x86_64 GNU/Linux
```
