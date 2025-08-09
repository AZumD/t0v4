(function () {
  const messages = document.getElementById('messages');
  const form = document.getElementById('form');
  const input = document.getElementById('input');
  const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');

  ws.addEventListener('message', (ev) => {
    const div = document.createElement('div');
    div.textContent = ev.data;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!input.value) return;
    ws.send(input.value);
    input.value = '';
  });
})(); 