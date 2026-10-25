async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Something went wrong.');
  }
  return response.json();
}

export const api = {
  listRooms: () => request('/api/rooms'),
  createRoom: (name) => request('/api/rooms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  }),
  listMessages: (roomId) => request(`/api/rooms/${roomId}/messages`),
  sendMessage: (roomId, authorName, body) => request(`/api/rooms/${roomId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ author_name: authorName, body }),
  }),
};
