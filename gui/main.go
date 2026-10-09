// Cliente gráfico del chat TCP (Fyne). Usa el mismo protocolo de texto que el
// cliente de consola: una línea por mensaje, UTF-8.
package main

import (
	"bufio"
	"net"
	"strings"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
)

const (
	promptNick  = "* Ingresa tu apodo:"
	welcomeHead = "* Bienvenido, "
	exitCmd     = "/salir"
	maxMsgLen   = 500
)

type chatApp struct {
	win fyne.Window

	// Pantalla de conexión
	connectView fyne.CanvasObject
	hostEntry   *widget.Entry
	portEntry   *widget.Entry
	nickEntry   *widget.Entry
	connectBtn  *widget.Button
	statusLabel *widget.Label

	// Pantalla de chat
	chatView   fyne.CanvasObject
	titleLabel *widget.Label
	messages   *fyne.Container
	scroll     *container.Scroll
	input      *widget.Entry

	mu   sync.Mutex
	conn net.Conn
	nick string
}

func newChatApp(win fyne.Window) *chatApp {
	a := &chatApp{win: win}

	// ---- Pantalla de conexión ----
	a.hostEntry = widget.NewEntry()
	a.hostEntry.SetText("127.0.0.1")
	a.portEntry = widget.NewEntry()
	a.portEntry.SetText("5000")
	a.nickEntry = widget.NewEntry()
	a.nickEntry.SetPlaceHolder("Tu apodo (máx. 20 caracteres)")
	a.nickEntry.OnSubmitted = func(string) { a.connect() }
	a.connectBtn = widget.NewButton("Conectar", a.connect)
	a.statusLabel = widget.NewLabel("")
	a.statusLabel.Wrapping = fyne.TextWrapWord

	form := widget.NewForm(
		widget.NewFormItem("IP del servidor", a.hostEntry),
		widget.NewFormItem("Puerto", a.portEntry),
		widget.NewFormItem("Apodo", a.nickEntry),
	)
	a.connectView = container.NewPadded(container.NewVBox(
		widget.NewLabelWithStyle("Chat TCP", fyne.TextAlignCenter, fyne.TextStyle{Bold: true}),
		form,
		a.connectBtn,
		a.statusLabel,
	))

	// ---- Pantalla de chat ----
	a.titleLabel = widget.NewLabelWithStyle("", fyne.TextAlignLeading, fyne.TextStyle{Bold: true})
	a.messages = container.NewVBox()
	a.scroll = container.NewVScroll(a.messages)
	a.input = widget.NewEntry()
	a.input.SetPlaceHolder("Escribe un mensaje y pulsa Enter")
	a.input.OnSubmitted = func(string) { a.send() }
	sendBtn := widget.NewButton("Enviar", a.send)
	leaveBtn := widget.NewButton("Salir", a.leave)

	top := container.NewBorder(nil, nil, nil, leaveBtn, a.titleLabel)
	bottom := container.NewBorder(nil, nil, nil, sendBtn, a.input)
	a.chatView = container.NewBorder(top, bottom, nil, nil, a.scroll)

	return a
}

// ---------------------------------------------------------------- conexión

func (a *chatApp) connect() {
	if a.connectBtn.Disabled() {
		return
	}
	host := strings.TrimSpace(a.hostEntry.Text)
	port := strings.TrimSpace(a.portEntry.Text)
	nick := strings.TrimSpace(a.nickEntry.Text)
	if host == "" || port == "" || nick == "" {
		a.statusLabel.SetText("Completa la IP, el puerto y el apodo.")
		return
	}
	a.connectBtn.Disable()
	a.statusLabel.SetText("Conectando...")
	go a.run(host, port, nick)
}

// run se ejecuta en una goroutine: conecta, entrega el apodo y lee mensajes.
func (a *chatApp) run(host, port, nick string) {
	conn, err := net.DialTimeout("tcp", net.JoinHostPort(host, port), 5*time.Second)
	if err != nil {
		a.showConnect("No se pudo conectar a " + host + ":" + port +
			". Verifica que el servidor esté en ejecución.")
		return
	}
	a.mu.Lock()
	a.conn = conn
	a.nick = nick
	a.mu.Unlock()

	reader := bufio.NewReader(conn)
	sentNick := false
	inChat := false
	lastNotice := ""

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			break
		}
		line = strings.TrimRight(line, "\r\n")

		switch {
		case inChat:
			a.addMessage(line)
		case line == promptNick:
			if sentNick {
				// El servidor volvió a pedir el apodo: lo rechazó.
				a.dropConn(conn)
				conn.Close()
				a.showConnect(noticeOr(lastNotice, "El servidor rechazó el apodo."))
				return
			}
			sentNick = true
			_, _ = conn.Write([]byte(nick + "\n"))
		case strings.HasPrefix(line, welcomeHead):
			inChat = true
			a.showChat(line)
		default:
			lastNotice = line // por ejemplo "Servidor lleno" o "Ese apodo ya está en uso"
		}
	}

	current := a.dropConn(conn)
	conn.Close()
	if !current {
		return // salimos nosotros a propósito
	}
	if inChat {
		a.showConnect("La conexión con el servidor se cerró.")
	} else {
		a.showConnect(noticeOr(lastNotice, "El servidor cerró la conexión."))
	}
}

func noticeOr(notice, fallback string) string {
	notice = strings.TrimSpace(strings.TrimPrefix(notice, "* "))
	if notice == "" {
		return fallback
	}
	return notice
}

// dropConn olvida la conexión si sigue siendo la actual; devuelve true si lo era.
func (a *chatApp) dropConn(conn net.Conn) bool {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.conn != conn {
		return false
	}
	a.conn = nil
	return true
}

// hangup avisa con /salir y cierra la conexión (sin tocar la interfaz).
func (a *chatApp) hangup() {
	a.mu.Lock()
	conn := a.conn
	a.conn = nil
	a.mu.Unlock()
	if conn != nil {
		_ = conn.SetWriteDeadline(time.Now().Add(2 * time.Second))
		_, _ = conn.Write([]byte(exitCmd + "\n"))
		_ = conn.Close()
	}
}

func (a *chatApp) leave() {
	a.hangup()
	a.showConnect("")
}

func (a *chatApp) send() {
	text := strings.TrimSpace(a.input.Text)
	a.input.SetText("")
	if text == "" {
		return
	}
	if strings.EqualFold(text, exitCmd) {
		a.leave()
		return
	}
	a.mu.Lock()
	conn, nick := a.conn, a.nick
	a.mu.Unlock()
	if conn == nil {
		return
	}
	_ = conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	if _, err := conn.Write([]byte(text + "\n")); err != nil {
		a.addMessage("* No se pudo enviar el mensaje.")
		return
	}
	// El servidor no devuelve el mensaje a su autor: lo mostramos aquí.
	// Si pasa del límite, el servidor lo rechaza y avisa, así que no lo mostramos.
	if len([]rune(text)) <= maxMsgLen {
		a.addMessage("[" + nick + "] " + text)
	}
}

// ---------------------------------------------------------------- interfaz
// Estas funciones se pueden llamar desde cualquier goroutine: usan fyne.Do.

func (a *chatApp) appendLabel(text string) {
	lbl := widget.NewLabel(text)
	lbl.Wrapping = fyne.TextWrapWord
	a.messages.Add(lbl)
	a.scroll.ScrollToBottom()
}

func (a *chatApp) addMessage(text string) {
	fyne.Do(func() { a.appendLabel(text) })
}

func (a *chatApp) showChat(welcome string) {
	a.mu.Lock()
	nick := a.nick
	a.mu.Unlock()
	fyne.Do(func() {
		a.messages.RemoveAll()
		a.titleLabel.SetText("Conectado como " + nick)
		a.appendLabel(welcome)
		a.win.SetContent(a.chatView)
		a.win.Canvas().Focus(a.input)
	})
}

func (a *chatApp) showConnect(msg string) {
	fyne.Do(func() {
		a.statusLabel.SetText(msg)
		a.connectBtn.Enable()
		a.win.SetContent(a.connectView)
	})
}

func main() {
	application := app.New()
	win := application.NewWindow("Chat TCP")
	chat := newChatApp(win)
	win.SetContent(chat.connectView)
	win.Resize(fyne.NewSize(480, 520))
	win.SetOnClosed(chat.hangup)
	win.ShowAndRun()
}
