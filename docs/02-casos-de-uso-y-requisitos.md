# Casos de uso, historias de usuario y requisitos

## 1. Casos de uso

| ID    | Nombre                     | Actor    | Descripción breve                                              |
|-------|----------------------------|----------|----------------------------------------------------------------|
| CU-01 | Conectarse al chat         | Usuario  | El usuario se conecta al servidor e indica su apodo.           |
| CU-02 | Enviar mensaje             | Usuario  | El usuario escribe un mensaje y este llega a los demás.        |
| CU-03 | Recibir mensajes           | Usuario  | El usuario ve en pantalla los mensajes de los demás.           |
| CU-04 | Salir del chat             | Usuario  | El usuario se desconecta con `/salir`.                         |
| CU-05 | Servidor lleno             | Usuario  | Un usuario intenta entrar cuando ya hay 10 conectados.         |
| CU-06 | Desconexión inesperada     | Servidor | Un cliente se cae y el servidor libera su cupo.                |

### CU-01 Conectarse al chat
- **Precondición:** el servidor está en ejecución y hay menos de 10 usuarios.
- **Flujo principal:**
  1. El usuario abre el cliente e indica IP y puerto.
  2. El servidor pide un apodo.
  3. El usuario escribe un apodo válido.
  4. El servidor lo acepta y avisa a los demás que entró.
- **Flujos alternos:**
  - A1. Apodo vacío, repetido o de más de 20 caracteres: el servidor lo rechaza y vuelve a pedirlo.
  - A2. El servidor no responde: el cliente muestra un error de conexión.
- **Postcondición:** el usuario está en la sala.

### CU-02 Enviar mensaje
- **Precondición:** el usuario está conectado.
- **Flujo principal:** el usuario escribe un texto y pulsa Enter; el servidor lo retransmite a todos los demás con el apodo del autor.
- **Flujos alternos:**
  - A1. Mensaje vacío: se ignora.
  - A2. Mensaje de más de 500 caracteres: el servidor lo rechaza y avisa al autor.

### CU-03 Recibir mensajes
- **Precondición:** el usuario está conectado.
- **Flujo principal:** cada vez que otro usuario envía un mensaje, este aparece en la pantalla con el formato `[apodo] texto`.

### CU-04 Salir del chat
- **Flujo principal:** el usuario escribe `/salir`; el servidor cierra su conexión, libera el cupo y avisa a los demás.

### CU-05 Servidor lleno
- **Precondición:** ya hay 10 usuarios conectados.
- **Flujo principal:** el usuario 11 se conecta, el servidor le envía un aviso de "servidor lleno" y cierra su conexión. Los 10 usuarios existentes no se ven afectados.

### CU-06 Desconexión inesperada
- **Flujo principal:** la conexión de un cliente se corta sin `/salir`; el servidor lo detecta, lo elimina de la lista, libera el cupo y avisa a los demás. El servidor sigue funcionando.

## 2. Historias de usuario

| ID    | Historia                                                                                                        | Caso de uso |
|-------|-----------------------------------------------------------------------------------------------------------------|-------------|
| HU-01 | Como usuario, quiero conectarme al servidor con un apodo para que los demás sepan quién soy.                    | CU-01       |
| HU-02 | Como usuario, quiero enviar mensajes de texto para comunicarme con el resto del grupo.                          | CU-02       |
| HU-03 | Como usuario, quiero ver los mensajes de los demás en tiempo real para seguir la conversación.                  | CU-03       |
| HU-04 | Como usuario, quiero salir del chat con un comando para cerrar mi sesión de forma ordenada.                     | CU-04       |
| HU-05 | Como usuario, quiero que me avisen si el servidor está lleno para saber por qué no pude entrar.                 | CU-05       |
| HU-06 | Como usuario, quiero que me avisen cuando alguien entra o sale para saber quién está en la sala.                | CU-01, CU-04|
| HU-07 | Como administrador del servidor, quiero que una caída de un cliente no afecte al resto para que el chat siga.   | CU-06       |

## 3. Requisitos

### 3.1 Funcionales

| ID     | Requisito                                                                                         | Origen        |
|--------|---------------------------------------------------------------------------------------------------|---------------|
| RF-01  | El servidor debe aceptar conexiones de clientes por TCP en un puerto configurable (por defecto 5000). | HU-01      |
| RF-02  | El servidor debe solicitar un apodo a cada cliente que se conecta.                                | HU-01         |
| RF-03  | El servidor debe rechazar apodos vacíos, repetidos o de más de 20 caracteres.                     | HU-01         |
| RF-04  | El servidor debe aceptar como máximo 10 clientes conectados simultáneamente.                      | HU-05         |
| RF-05  | Si hay 10 clientes conectados, el servidor debe informar "servidor lleno" al cliente 11 y cerrar su conexión. | HU-05 |
| RF-06  | El servidor debe retransmitir cada mensaje recibido a todos los demás clientes, con el apodo del autor. | HU-02, HU-03 |
| RF-07  | El servidor debe ignorar los mensajes vacíos.                                                     | HU-02         |
| RF-08  | El servidor debe rechazar los mensajes de más de 500 caracteres e informar al autor.              | HU-02         |
| RF-09  | El servidor debe notificar a todos los usuarios cuando uno entra o sale de la sala.               | HU-06         |
| RF-10  | El servidor debe cerrar la conexión y liberar el cupo cuando el cliente envía `/salir`.           | HU-04         |
| RF-11  | El servidor debe detectar la desconexión inesperada de un cliente, liberar su cupo y seguir funcionando. | HU-07  |
| RF-12  | El cliente debe permitir escribir y recibir mensajes al mismo tiempo.                             | HU-02, HU-03  |
| RF-13  | El cliente debe mostrar un mensaje de error claro si no puede conectarse al servidor.             | HU-01         |

### 3.2 No funcionales

| ID      | Requisito                                                                     |
|---------|-------------------------------------------------------------------------------|
| RNF-01  | Los mensajes se codifican en UTF-8, un mensaje por línea.                     |
| RNF-02  | El sistema debe ejecutarse en Ubuntu (WSL2) con Python 3.                     |
| RNF-03  | Un mensaje debe llegar a los demás en menos de 1 segundo en una red local.    |
| RNF-04  | El servidor no debe caerse por datos malformados enviados por un cliente.     |