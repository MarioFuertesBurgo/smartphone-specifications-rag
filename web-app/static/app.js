const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");
const emptyState = document.getElementById("empty-state");

function removeEmptyState() {
  if (emptyState && emptyState.parentElement) {
    emptyState.remove();
  }
}

function appendMessage(text, role, options = {}) {
  if (!text) return null;
  removeEmptyState();

  const bubble = document.createElement("article");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  if (options.pending) {
    bubble.classList.add("pending");
  }

  const delay = Math.min(chat.children.length * 35, 240);
  bubble.style.setProperty("--delay", `${delay}ms`);

  chat.appendChild(bubble);
  chat.scrollTop = chat.scrollHeight;
  return bubble;
}

function setBusy(isBusy) {
  input.disabled = isBusy;
  sendButton.disabled = isBusy;
  sendButton.textContent = isBusy ? "Enviando..." : "Enviar";
}

async function sendMessage(message) {
  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!resp.ok) {
      return "No he podido consultar el servidor en este momento.";
    }

    const data = await resp.json();
    return (data.reply || "").trim() || "No he recibido contenido en la respuesta.";
  } catch (error) {
    return "No hay conexion con el servidor. Revisa que la aplicacion siga activa.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  input.value = "";
  setBusy(true);

  const pendingBubble = appendMessage("Pensando...", "bot", { pending: true });
  const reply = await sendMessage(message);

  if (pendingBubble) {
    pendingBubble.remove();
  }

  appendMessage(reply, "bot");
  setBusy(false);
  input.focus();
});
