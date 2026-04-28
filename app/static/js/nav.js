function renderNav(activePage) {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const links = [
    { href: '/dashboard', label: 'Dashboard', key: 'dashboard' },
    { href: '/food-log', label: 'Food Log', key: 'food-log' },
    { href: '/stats', label: 'Stats', key: 'stats' },
    { href: '/workout', label: 'Workout', key: 'workout' },
    { href: '/measurements', label: 'Measurements', key: 'measurements' },
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

function renderNav(activePage) {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const links = [
    { href: '/dashboard', label: 'Dashboard', key: 'dashboard' },
    { href: '/food-log', label: 'Food Log', key: 'food-log' },
    { href: '/stats', label: 'Stats', key: 'stats' },
    { href: '/workout', label: 'Workout', key: 'workout' },
    { href: '/measurements', label: 'Measurements', key: 'measurements' },
    { href: '/weekly', label: 'Weekly', key: 'weekly' },
    { href: '/tracker', label: 'Tracker', key: 'tracker' },
    { href: '/profile', label: 'Profile', key: 'profile' },
  ];

  const desktopLinks = links.map(l => `
    <a href="${l.href}" class="${activePage === l.key ? 'active' : ''}">${l.label}</a>
  `).join('') + `<a href="#" onclick="logout()" style="color:var(--danger)">Out</a>`;

  const mobileLinks = links.map(l => `
    <a href="${l.href}" class="${activePage === l.key ? 'active' : ''}">${l.label}</a>
  `).join('') + `<a href="#" onclick="logout()" style="color:var(--danger)">Sign out</a>`;

  const html = `
    <nav class="nav">
      <a class="nav-brand" href="/dashboard">Health Tracker</a>
      <div class="nav-links">${desktopLinks}</div>
      <button class="nav-hamburger" id="hamburger" onclick="toggleMenu()"
        aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>
    </nav>
    <div class="nav-mobile-menu" id="mobile-menu">${mobileLinks}</div>
    <div class="nav-overlay" id="nav-overlay" onclick="closeMenu()"></div>
  `;

  document.body.insertAdjacentHTML('afterbegin', html);
}

function toggleMenu() {
  const hamburger = document.getElementById('hamburger');
  const menu = document.getElementById('mobile-menu');
  const overlay = document.getElementById('nav-overlay');
  const isOpen = menu.classList.contains('open');

  if (isOpen) {
    closeMenu();
  } else {
    hamburger.classList.add('open');
    menu.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeMenu() {
  document.getElementById('hamburger')?.classList.remove('open');
  document.getElementById('mobile-menu')?.classList.remove('open');
  document.getElementById('nav-overlay')?.classList.remove('open');
  document.body.style.overflow = '';
}

function logout() {
  API.clearToken();
  window.location.href = '/login';
}