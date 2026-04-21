async function handleRegisterSendOTP(e) {
  e.preventDefault();
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
  };

  if (!payload.name || !payload.email || !payload.password || !payload.age || !payload.height_cm) {
    errEl.textContent = 'Please fill in all fields.';
    errEl.classList.remove('hidden');
    return;
  }

  try {
    await API.post('/auth/register/send-otp', payload);
    sucEl.textContent = 'OTP sent to your email.';
    sucEl.classList.remove('hidden');
    // show OTP section
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