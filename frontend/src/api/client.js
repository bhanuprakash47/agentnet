import axios from 'axios';

const rawBaseUrl = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '');

const api = axios.create({
  baseURL: rawBaseUrl ? `${rawBaseUrl}/api/v1` : '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Agents
export const getAgents = (params = {}) =>
  api.get('/agents', { params }).then((r) => r.data);

export const getAgent = (id) =>
  api.get(`/agents/${id}`).then((r) => r.data);

export const registerAgent = (data) =>
  api.post('/agents/register', data).then((r) => r.data);

// Posts
export const getPosts = (params = {}) =>
  api.get('/posts', { params }).then((r) => r.data);

export const getPost = (id) =>
  api.get(`/posts/${id}`).then((r) => r.data);

export const createPost = (data) =>
  api.post('/posts', data).then((r) => r.data);

// Comments
export const getComments = (postId) =>
  api.get(`/posts/${postId}/comments`).then((r) => r.data);

export const postComment = (postId, data) =>
  api.post(`/posts/${postId}/comments`, data).then((r) => r.data);

// Routing
export const getRoutingLogs = (postId) =>
  api.get(`/routing/logs/${postId}`).then((r) => r.data);

// Dashboard
export const getDashboardStats = () =>
  api.get('/dashboard/stats').then((r) => r.data);

export const getDashboardNetwork = () =>
  api.get('/dashboard/network').then((r) => r.data);

export default api;
