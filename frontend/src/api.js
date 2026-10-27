async function request(path, options = {}) {
  const token = localStorage.getItem('wifi-chat-token');
  const headers = { ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Something went wrong.');
  }
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  register: (username, password) => request('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  }),
  login: (username, password) => request('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  }),
  currentUser: () => request('/api/auth/me'),
  listRooms: () => request('/api/rooms'),
  createRoom: (name) => request('/api/rooms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  }),
  joinRoom: (roomId) => request(`/api/rooms/${roomId}/join`, { method: 'POST' }),
  listMessages: (roomId) => request(`/api/rooms/${roomId}/messages`),
};
