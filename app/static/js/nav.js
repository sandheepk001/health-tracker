function renderNav(activePage) {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const links = [
    { href: '/dashboard', label: 'Dashboard', key: 'dashboard' },
    { href: '/food-log', label: 'Food Log', key: 'food-log' },
    { href: '/stats', label: 'Stats', key: 'stats' },
    { href: '/weekly', label: 'Weekly', key: 'weekly' },
    { href: '/tracker', label: 'Tracker', key: 'tracker' },
    { href: '/profile', label: 'Profile', key: 'profile' },
  ];

  const html = `
    <nav class="nav">
      <a class="nav-brand" href="/dashboard">HT</a>
      <div class="nav-links">
        ${links.map(l => `
          <a href="${l.href}" class="${activePage === l.key ? 'active' : ''}">
            ${l.label}
          </a>`).join('')}
        <a href="#" onclick="logout()" style="color:var(--danger)">Out</a>
      </div>
    </nav>`;

  document.body.insertAdjacentHTML('afterbegin', html);
}

function logout() {
  API.clearToken();
  window.location.href = '/login';
}