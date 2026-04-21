const API = {
  base: '/api',

  getToken() {
    return localStorage.getItem('token');
  },

  setToken(token) {
    localStorage.setItem('token', token);
  },

  clearToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  headers() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getToken()}`
    };
  },

  async request(method, path, body = null) {
    const opts = { method, headers: this.headers() };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    if (res.status === 401) {
      this.clearToken();
      window.location.href = '/login';
      return;
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  },

  get(path)         { return this.request('GET', path); },
  post(path, body)  { return this.request('POST', path, body); },
  put(path, body)   { return this.request('PUT', path, body); },
  delete(path)      { return this.request('DELETE', path); },

  async login(email, password) {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    return data;
  }
};

function requireAuth() {
  if (!API.getToken()) {
    window.location.href = '/login';
  }
}

function today() {
  return new Date().toISOString().split('T')[0];
}

function formatNum(n, dec = 1) {
  return n != null ? (+n).toFixed(dec) : '—';
}