async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const errEl = document.getElementById('error');

  try {
    const data = await API.login(email, password);
    API.setToken(data.access_token);
    const user = await API.get('/users/me');
    localStorage.setItem('user', JSON.stringify(user));
    window.location.href = '/dashboard';
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  }
}

async function handleRegisterSendOTP(e) {
  e.preventDefault();
  const errEl = document.getElementById('error');
  const sucEl = document.getElementById('success');
  errEl.classList.add('hidden');
  sucEl.classList.add('hidden');

  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const gender = document.getElementById('gender').value;
  const age = parseInt(document.getElementById('age').value);
  const height = parseFloat(document.getElementById('height').value);
  const initialWeight = parseFloat(document.getElementById('initial-weight').value) || null;

  // ── validate all fields before anything else ──
  function showError(msg) {
    errEl.textContent = msg;
    errEl.classList.remove('hidden');
    errEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  if (!name) return showError('Full name is required.');
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    return showError('Please enter a valid email address.');
  if (!password || password.length < 6)
    return showError('Password must be at least 6 characters.');
  if (!age || isNaN(age))
    return showError('Please enter your age.');
  if (age < 10 || age > 100)
    return showError('Age must be between 10 and 100 years.');
  if (!height || isNaN(height))
    return showError('Please enter your height.');
  if (height < 100 || height > 250)
    return showError('Height must be between 100 and 250 cm.');
  if (initialWeight !== null && (initialWeight < 20 || initialWeight > 300))
    return showError('Weight must be between 20 and 300 kg.');

  // ── all valid — now call API ──
  const payload = {
    email,
    password,
    name,
    gender,
    age,
    height_cm: height,
    initial_weight: initialWeight
  };

  try {
    await API.post('/auth/register/send-otp', payload);
    sucEl.textContent = 'OTP sent to your email.';
    sucEl.classList.remove('hidden');
    document.getElementById('otp-section').classList.remove('hidden');
    document.getElementById('send-otp-btn').classList.add('hidden');
    document.getElementById('form-fields').style.opacity = '0.5';
    document.getElementById('form-fields').style.pointerEvents = 'none';
    document.getElementById('otp-0').focus();
    startRegisterTimer();
  } catch(e) {
    errEl.textContent = e.message;
    errEl.classList.remove('hidden');
  }
}
async function handleRegisterVerifyOTP() {
  const errEl = document.getElementById('error');
  const sucEl = document.getElementById('success');
  errEl.classList.add('hidden');

  const otp = [0,1,2,3,4,5].map(i =>
    document.getElementById(`otp-${i}`).value
  ).join('');

  if (otp.length < 6) {
    errEl.textContent = 'Please enter the complete 6-digit OTP.';
    errEl.classList.remove('hidden');
    return;
  }

  const email = document.getElementById('email').value;

  try {
    await API.post('/auth/register/verify-otp', { email, otp });
    // auto login after registration
    const loginForm = new URLSearchParams();
    loginForm.append('username', email);
    loginForm.append('password', document.getElementById('password').value);
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: loginForm
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    API.setToken(data.access_token);
    const user = await API.get('/users/me');
    localStorage.setItem('user', JSON.stringify(user));
    window.location.href = '/dashboard';
  } catch(e) {
    errEl.textContent = e.message;
    errEl.classList.remove('hidden');
    [0,1,2,3,4,5].forEach(i => document.getElementById(`otp-${i}`).value = '');
    document.getElementById('otp-0').focus();
  }
}

let registerTimerInterval = null;

function startRegisterTimer() {
  let seconds = 600;
  const timerEl = document.getElementById('register-timer');
  const resendBtn = document.getElementById('register-resend-btn');

  registerTimerInterval = setInterval(() => {
    seconds--;
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    timerEl.textContent = `${m}:${s}`;
    if (seconds <= 0) {
      clearInterval(registerTimerInterval);
      timerEl.textContent = 'Expired';
      resendBtn.disabled = false;
    }
    if (seconds <= 540) resendBtn.disabled = false;
  }, 1000);
}

async function resendRegisterOTP() {
  const errEl = document.getElementById('error');
  const sucEl = document.getElementById('success');
  errEl.classList.add('hidden');
  sucEl.classList.add('hidden');

  const payload = {
  email: document.getElementById('email').value,
  password: document.getElementById('password').value,
  name: document.getElementById('name').value,
  gender: document.getElementById('gender').value,
  age: parseInt(document.getElementById('age').value),
  height_cm: parseFloat(document.getElementById('height').value),
  initial_weight: parseFloat(document.getElementById('initial-weight').value) || null,
};

  try {
    await API.post('/auth/register/send-otp', payload);
    sucEl.textContent = 'New OTP sent.';
    sucEl.classList.remove('hidden');
    clearInterval(registerTimerInterval);
    [0,1,2,3,4,5].forEach(i => document.getElementById(`otp-${i}`).value = '');
    document.getElementById('otp-0').focus();
    document.getElementById('register-resend-btn').disabled = true;
    startRegisterTimer();
  } catch(e) {
    errEl.textContent = e.message;
    errEl.classList.remove('hidden');
  }
}
