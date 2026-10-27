import { useEffect, useRef, useState } from 'react';
import { api } from './api';

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    try {
      const result = mode === 'login'
        ? await api.login(username, password)
        : await api.register(username, password);
      onAuthenticated(result);
    } catch (err) {
      setError(err.message);
    }
  }

  return <main className="auth-shell"><form className="auth-card" onSubmit={submit}>
    <h1>Wi-Fi Chat</h1><p>{mode === 'login' ? 'Sign in to continue.' : 'Create your chat account.'}</p>
    {error && <p className="error" role="alert">{error}</p>}
    <label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} minLength="3" maxLength="30" required autoComplete="username" /></label>
    <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength="8" maxLength="72" required autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>
    <button type="submit">{mode === 'login' ? 'Sign in' : 'Create account'}</button>
    <button type="button" className="text-button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>{mode === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}</button>
  </form></main>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [activeRoom, setActiveRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [text, setText] = useState('');
  const [newRoomName, setNewRoomName] = useState('');
  const [error, setError] = useState('');
  const socketRef = useRef(null);

  useEffect(() => {
    if (!localStorage.getItem('wifi-chat-token')) return;
    api.currentUser().then(setUser).catch(() => localStorage.removeItem('wifi-chat-token'));
  }, []);

  useEffect(() => {
    if (!user) return;
    api.listRooms().then(setRooms).catch((err) => setError(err.message));
  }, [user]);

  useEffect(() => {
    if (!activeRoom) { setMessages([]); setParticipants([]); return undefined; }
    let socket;
    api.listMessages(activeRoom.id).then(setMessages).catch((err) => setError(err.message));
    const token = localStorage.getItem('wifi-chat-token');
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    socket = new WebSocket(`${protocol}://${window.location.host}/api/ws/rooms/${activeRoom.id}?token=${encodeURIComponent(token)}`);
    socketRef.current = socket;
    socket.onmessage = ({ data }) => {
      const event = JSON.parse(data);
      if (event.type === 'message') setMessages((items) => [...items, event.message]);
      if (event.type === 'participants') setParticipants(event.participants);
    };
    socket.onerror = () => setError('Live connection lost. Rejoin the room to reconnect.');
    return () => {
      socket.close();
      if (socketRef.current === socket) socketRef.current = null;
    };
  }, [activeRoom]);

  function authenticated(result) {
    localStorage.setItem('wifi-chat-token', result.access_token);
    setUser(result.user);
  }

  async function selectRoom(room) {
    try { await api.joinRoom(room.id); setError(''); setActiveRoom(room); } catch (err) { setError(err.message); }
  }

  async function handleCreateRoom(event) {
    event.preventDefault();
    try {
      const room = await api.createRoom(newRoomName.trim());
      setRooms((items) => [...items, room].sort((a, b) => a.name.localeCompare(b.name)));
      setNewRoomName(''); setActiveRoom(room);
    } catch (err) { setError(err.message); }
  }

  function handleSend(event) {
    event.preventDefault();
    if (!activeRoom || !text.trim()) return;
    if (socketRef.current?.readyState !== WebSocket.OPEN) {
      setError('Still connecting to the room. Please try again.');
      return;
    }
    socketRef.current.send(JSON.stringify({ type: 'message', body: text.trim() }));
    setText('');
  }

  if (!user) return <AuthScreen onAuthenticated={authenticated} />;
  return <main className="app-shell">
    <aside className="sidebar"><h1>Wi-Fi Chat</h1><p className="signed-in">Signed in as <strong>{user.username}</strong></p>
      <form className="room-form" onSubmit={handleCreateRoom}><input value={newRoomName} onChange={(event) => setNewRoomName(event.target.value)} placeholder="New room name" maxLength="80" required /><button type="submit">Create</button></form>
      <nav aria-label="Chat rooms">{rooms.map((room) => <button className={room.id === activeRoom?.id ? 'room active' : 'room'} key={room.id} onClick={() => selectRoom(room)}>{room.name}</button>)}</nav>
      <button className="text-button logout" onClick={() => { localStorage.removeItem('wifi-chat-token'); setUser(null); setActiveRoom(null); }}>Sign out</button>
    </aside>
    <section className="chat-panel"><header><h2>{activeRoom ? `# ${activeRoom.name}` : 'Create or join a room'}</h2></header>{error && <p className="error" role="alert">{error}</p>}
      <div className="chat-content"><div className="messages" aria-live="polite">{messages.map((message) => <article className="message" key={message.id}><strong>{message.author_name}</strong><span>{message.body}</span></article>)}</div>
        <aside className="participants"><h3>Online — {participants.length}</h3>{participants.map((participant) => <span key={participant.id}>{participant.username}</span>)}</aside></div>
      <form className="message-form" onSubmit={handleSend}><input value={text} onChange={(event) => setText(event.target.value)} placeholder="Write a message" maxLength="2000" required disabled={!activeRoom} /><button type="submit" disabled={!activeRoom}>Send</button></form>
    </section>
  </main>;
}
