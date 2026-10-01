# Chat TCP de solo texto

Servidor de chat de solo texto sobre TCP, para un máximo de **10 usuarios
simultáneos**, con cliente de consola. Proyecto del curso **Linux embebidos**
(Universidad Nacional de Colombia). Escrito en Python 3 y desarrollado en
Ubuntu sobre WSL2.

## Características
- Servidor TCP con un hilo por cliente.
- Máximo 10 usuarios conectados; el usuario 11 recibe "servidor lleno".
- Apodos únicos (hasta 20 caracteres), mensajes de hasta 500 caracteres.
- Difusión de mensajes a todos los demás, con avisos de entrada y salida.
- Desconexiones inesperadas manejadas sin afectar al resto.
- Protocolo de texto plano (UTF-8, una línea por mensaje): también funciona con `nc`.

## Requisitos
- Python 3 y `git`.
- Para las pruebas: `pytest`.

## Instalación

```bash
git clone https://github.com/SebastianRodriguez05/linux-embebidos-chat-tcp.git
cd linux-embebidos-chat-tcp
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
```

## Uso

Iniciar el servidor (puerto 5000 por defecto):

```bash
python -m src.server
python -m src.server --port 6000        # otro puerto
```

Conectar un cliente (en otra terminal):

```bash
python -m src.client                    # localhost:5000
python -m src.client 192.168.1.20 5000  # servidor en otro equipo
```

Dentro del chat se escribe el apodo y después los mensajes. El comando
`/salir` cierra la sesión. Alternativa sin el cliente: `nc localhost 5000`.

### Conexión desde otros equipos con WSL2
Ubuntu en WSL2 tiene su propia red interna, así que hay que reenviar el
puerto desde Windows. Con `IP_WSL` obtenida con `hostname -I` en Ubuntu,
en PowerShell como administrador:

```powershell
netsh interface portproxy add v4tov4 listenport=5000 listenaddress=0.0.0.0 connectport=5000 connectaddress=IP_WSL
New-NetFirewallRule -DisplayName "Chat TCP 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

Los clientes se conectan a la IP de Windows en esa red. La IP de WSL cambia
al reiniciarlo, y algunas redes públicas bloquean la comunicación entre
dispositivos.

## Pruebas

```bash
python -m pytest -v
```

30 pruebas: 14 unitarias (`tests/test_protocol.py`, `tests/test_registry.py`)
y 16 de integración con servidor y clientes reales (`tests/test_integration.py`).

## Estructura del repositorio

```
.
├── docs/
│   ├── 01-descripcion-funcional.md
│   ├── 02-casos-de-uso-y-requisitos.md
│   ├── 03-arquitectura.md
│   └── 04-matriz-de-verificacion.md
├── src/
│   ├── protocol.py    constantes y validación (sin red)
│   ├── registry.py    registro de clientes y límite de 10
│   ├── server.py      servidor TCP
│   └── client.py      cliente de consola
├── tests/
├── pytest.ini
└── README.md
```

## Documentación
1. [Descripción funcional](docs/01-descripcion-funcional.md)
2. [Casos de uso, historias de usuario y requisitos](docs/02-casos-de-uso-y-requisitos.md)
3. [Arquitectura](docs/03-arquitectura.md)
4. [Matriz de verificación y resultados](docs/04-matriz-de-verificacion.md)

## Autor
SebastianRodriguez05
