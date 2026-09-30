# Descripción funcional: Servidor de chat TCP

## 1. Propósito
Sistema de chat de solo texto en el que varios usuarios de una misma red
se comunican en tiempo real a través de un servidor central que usa TCP.

## 2. Alcance
- Incluye: un servidor y un cliente de consola.
- No incluye: envío de archivos, imágenes, audio, cifrado, autenticación
  con contraseña ni almacenamiento del historial de mensajes.

## 3. Actores
- **Usuario:** persona que usa el cliente para chatear.
- **Servidor:** programa que acepta conexiones y distribuye los mensajes.

## 4. Descripción general del funcionamiento
1. El servidor se inicia y queda escuchando en un puerto TCP (por defecto 5000).
2. Un usuario ejecuta el cliente e indica la IP y el puerto del servidor.
3. El servidor le pide un apodo (nickname). El apodo debe ser único.
4. Al ser aceptado, el usuario entra a la sala común y todos los demás
   reciben un aviso de que entró.
5. Cada mensaje que un usuario envía se retransmite a todos los demás
   conectados, con el apodo de quien lo escribió.
6. Cuando un usuario sale (comando `/salir` o cierre de la conexión), los
   demás reciben un aviso.

## 5. Funcionalidades
| ID  | Funcionalidad                | Descripción                                                        |
|-----|------------------------------|--------------------------------------------------------------------|
| F1  | Conexión                     | El cliente se conecta al servidor por TCP usando IP y puerto.      |
| F2  | Registro de apodo            | El servidor valida que el apodo no esté vacío ni repetido.         |
| F3  | Límite de usuarios           | El servidor acepta máximo 10 usuarios simultáneos.                 |
| F4  | Rechazo por servidor lleno   | Al llegar el usuario 11, recibe un aviso y se cierra su conexión.  |
| F5  | Envío de mensajes            | El usuario escribe texto y lo envía a la sala.                     |
| F6  | Difusión (broadcast)         | El servidor reenvía cada mensaje a todos los demás usuarios.       |
| F7  | Avisos de entrada y salida   | Todos son notificados cuando alguien entra o sale.                 |
| F8  | Desconexión voluntaria       | El usuario sale con el comando `/salir`.                           |
| F9  | Desconexión inesperada       | Si un cliente se cae, el servidor libera su cupo sin fallar.       |

## 6. Reglas y restricciones
- Máximo 10 usuarios conectados al mismo tiempo.
- Solo texto codificado en UTF-8, un mensaje por línea.
- Longitud máxima de un mensaje: 500 caracteres.
- Longitud máxima del apodo: 20 caracteres.
- Los mensajes vacíos se ignoran.
- El servidor no guarda mensajes: quien entra tarde no ve lo anterior.

## 7. Entorno de ejecución
- Lenguaje: Python 3.
- Sistema: Ubuntu sobre WSL2.
- Red: los usuarios deben estar en la misma red que el servidor
  (o poder alcanzar su IP y puerto).