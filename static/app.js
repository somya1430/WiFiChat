const chat = document.getElementById('chat');
const input = document.getElementById('message');
const nameInput = document.getElementById('name');
const form = document.getElementById('form');
let last = 0;

async function refresh() {
  try {
    const response = await fetch(`/messages?after=${last}`);
    const messages = await response.json();

    for (const message of messages) {
      const div = document.createElement('div');
      div.className = 'msg';
      const time = new Date(message.time).toLocaleTimeString();
      div.textContent = `${time} | ${message.name}: ${message.text}`;
      chat.appendChild(div);
      last = Math.max(last, message.id);
    }

    if (messages.length) {
      chat.scrollTop = chat.scrollHeight;
    }
  } catch {
    // Retry on the next polling cycle.
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  const name = nameInput.value.trim() || 'Guest';

  if (!text) return;

  input.value = '';

  try {
    const response = await fetch('/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, text }),
    });

    if (!response.ok) {
      alert('Message could not be sent.');
    }

    await refresh();
  } catch {
    alert('Cannot reach the computer. Check Wi-Fi.');
  }

  input.focus();
});

refresh();
setInterval(refresh, 700);
