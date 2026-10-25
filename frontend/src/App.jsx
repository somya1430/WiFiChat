import { useEffect, useState } from 'react';
import { api } from './api';

export default function App() {
  const [rooms, setRooms] = useState([]);
  const [activeRoom, setActiveRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [name, setName] = useState(localStorage.getItem('wifi-chat-name') || '');
  const [text, setText] = useState('');
  const [newRoomName, setNewRoomName] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api.listRooms().then((items) => {
      setRooms(items);
      setActiveRoom(items[0] ?? null);
    }).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!activeRoom) {
      setMessages([]);
      return undefined;
    }

    const loadMessages = () => api.listMessages(activeRoom.id)
      .then(setMessages)
      .catch((err) => setError(err.message));

    loadMessages();
    const interval = window.setInterval(loadMessages, 2000);
    return () => window.clearInterval(interval);
  }, [activeRoom]);

  async function handleCreateRoom(event) {
    event.preventDefault();
    try {
      const room = await api.createRoom(newRoomName.trim());
      setRooms((items) => [...items, room].sort((a, b) => a.name.localeCompare(b.name)));
      setActiveRoom(room);
      setNewRoomName('');
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSend(event) {
    event.preventDefault();
    if (!activeRoom || !name.trim() || !text.trim()) return;

    try {
      const message = await api.sendMessage(activeRoom.id, name.trim(), text.trim());
      localStorage.setItem('wifi-chat-name', name.trim());
      setMessages((items) => [...items, message]);
      setText('');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <h1>Wi-Fi Chat</h1>
        <form className="room-form" onSubmit={handleCreateRoom}>
          <input value={newRoomName} onChange={(event) => setNewRoomName(event.target.value)} placeholder="New room name" maxLength="80" required />
          <button type="submit">Create</button>
        </form>
        <nav aria-label="Chat rooms">
          {rooms.map((room) => <button className={room.id === activeRoom?.id ? 'room active' : 'room'} key={room.id} onClick={() => setActiveRoom(room)}>{room.name}</button>)}
        </nav>
      </aside>

      <section className="chat-panel">
        <header><h2>{activeRoom ? `# ${activeRoom.name}` : 'Create or join a room'}</h2></header>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="messages" aria-live="polite">
          {messages.map((message) => <article className="message" key={message.id}><strong>{message.author_name}</strong><span>{message.body}</span></article>)}
        </div>
        <form className="message-form" onSubmit={handleSend}>
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" maxLength="30" required />
          <input value={text} onChange={(event) => setText(event.target.value)} placeholder="Write a message" maxLength="2000" required disabled={!activeRoom} />
          <button type="submit" disabled={!activeRoom}>Send</button>
        </form>
      </section>
    </main>
  );
}
