/* ================================================================
   ConnectU — Mentor Panel · Shared State & Utilities  v2.0
   mentor-shared.js — barcha mentor fayllar shu faylni import qiladi
   ================================================================ */

/* ─── GLOBAL STATE ─── */
window.CU = window.CU || {};
CU.currentUser   = null;
CU.mentorData    = null;
CU.sessions      = [];
CU.pointsHistory = [];
CU.certificates  = [];
CU.videos        = [];
CU.notifs        = [];
CU.news          = [];
CU._demoMode     = false;
CU._verifyData   = null;

/* ─── API BASE ─── */
CU.API = {
  base: '',
  async get(path) {
    const r = await fetch(this.base + path, {credentials:'include'});
    if(!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(this.base + path, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body), credentials:'include'
    });
    return r.json();
  },
  async put(path, body) {
    const r = await fetch(this.base + path, {
      method:'PUT', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body), credentials:'include'
    });
    return r.json();
  },
  async del(path) {
    const r = await fetch(this.base + path, {method:'DELETE', credentials:'include'});
    return r.json();
  }
};

/* ─── DEMO USER ─── */
CU._demoUser = function() {
  return {
    id: 'demo_mentor_1',
    full_name: 'Mentor Foydalanuvchi',
    username: 'mentor_demo',
    role: 'mentor',
    avatar_url: '',
    balance: 3950000,
    pending_balance: 480000,
    total_sessions: 12,
    rating: 4.8,
    reviews_count: 5,
    mentor_profile: {
      id: 'mp_demo',
      bio: 'TDYU 3-kurs talabasi. Matematika va fizika bo\'yicha mentor.',
      university: 'TDYU',
      faculty: 'Muhandislik fakulteti',
      year: 3,
      subjects: ['Matematika', 'Fizika'],
      languages: ['Uzbek', 'Russian'],
      individual_price: 8000,
      group_price: 2000,
      balance: 3950000,
      pending_balance: 480000,
      total_sessions: 12,
      rating: 4.8,
      total_reviews: 5,
      is_verified: true,
      card_last4: '1234',
      card_holder: 'DEMO USER',
    }
  };
};

CU._demoSessions = function() {
  const names = ['Bobur T.','Malika S.','Nilufar B.','Jasur M.','Dilnoza T.','Sherzod A.'];
  const statuses = ['pending','confirmed','completed','completed','cancelled','completed'];
  const types = ['individual','group','individual','group','individual','individual'];
  return names.map((n,i) => ({
    id: 'sess_'+i,
    student_name: n,
    student_university: 'TDYU',
    session_type: types[i],
    status: statuses[i],
    scheduled_at: new Date(Date.now() + (i-2)*86400000).toISOString(),
    duration_min: 60,
    notes: '',
    meet_link: i===1 ? 'https://meet.google.com/abc-defg-hij' : '',
    price: types[i] === 'individual' ? 8000 : 2000,
    created_at: new Date(Date.now() - i*86400000).toISOString(),
  }));
};

CU._demoPoints = function() {
  return [
    {id:'p1',points:8000,reason:'session_completed',reason_text:'Sessiya yakunlandi',description:'Individual sessiya — Bobur T.',created_at:new Date(Date.now()-86400000).toISOString(),balance_after:3950000},
    {id:'p2',points:2000,reason:'session_completed',reason_text:'Sessiya yakunlandi',description:'Guruh sessiya — Malika S.',created_at:new Date(Date.now()-86400000*3).toISOString(),balance_after:3942000},
    {id:'p3',points:-50000,reason:'withdrawal',reason_text:'Pul yechildi',description:'Pul yechish',created_at:new Date(Date.now()-86400000*7).toISOString(),balance_after:3890000},
    {id:'p4',points:8000,reason:'session_completed',reason_text:'Sessiya yakunlandi',description:'Individual sessiya — Jasur M.',created_at:new Date(Date.now()-86400000*10).toISOString(),balance_after:3940000},
  ];
};

CU._demoVideos = function() {
  return [
    {id:'v1',title:'DTM matematika — kasr va nisbat',url:'https://youtu.be/dQw4w9WgXcQ',thumbnail:'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg',access:'free',access_type:'free',views:248,likes:34,description:'2024-2025 DTM dasturi bo\'yicha asosiy mavzular',created_at:new Date(Date.now()-86400000*2).toISOString()},
    {id:'v2',title:'TDYU kirish imtihoniga tayyorlash strategiyasi',url:'https://youtu.be/9bZkp7q19f0',thumbnail:'https://img.youtube.com/vi/9bZkp7q19f0/hqdefault.jpg',access:'premium',access_type:'premium',views:156,likes:22,description:'TDYU 2025-2026 yil uchun to\'liq tayyorgarlik rejasi',created_at:new Date(Date.now()-86400000*5).toISOString()},
    {id:'v3',title:'Ingliz tili: Grammar essentials B1→B2',url:'https://youtu.be/XqZsoesa55w',thumbnail:'https://img.youtube.com/vi/XqZsoesa55w/hqdefault.jpg',access:'free',access_type:'free',views:312,likes:51,description:'B1 dan B2 darajasiga o\'tish uchun zarur grammar mavzular',created_at:new Date(Date.now()-86400000*8).toISOString()},
  ];
};

CU._demoNews = function() {
  return [
    {id:'n1',title:'📋 Yangi to\'lov tizimi ishga tushdi',content:'Endi sessiyangizdagi to\'lovlar 24 soat ichida balansga tushadi.',category:'update',priority:'high',created_at:new Date().toISOString()},
    {id:'n2',title:'📅 Mentor webinari: Dars o\'tish texnikasi',content:'Kelasi juma kuni mentor webinari bo\'lib o\'tadi.',category:'event',priority:'normal',link:'https://t.me/connectu_admin',created_at:new Date(Date.now()-86400000*2).toISOString()},
    {id:'n3',title:'⚠️ Profil to\'ldirilmagan mentorlar',content:'30% dan kam to\'ldirilgan profil 3 kun ichida archivga o\'tkaziladi.',category:'urgent',priority:'critical',created_at:new Date(Date.now()-86400000*3).toISOString()},
  ];
};

/* ─── AUTH ─── */
CU.init = async function(onSuccess) {
  try {
    const tg = window.Telegram?.WebApp;
    if(tg){tg.ready();tg.expand();}

    let d = null;
    try {
      d = await CU.API.get('/api/me');
    } catch(fetchErr) {
      d = null;
    }

    if(!d || !d.success) {
      /* Backend yo'q — demo rejimda ishlaymiz */
      CU._demoMode = true;
      CU.currentUser = CU._demoUser();
      CU.mentorData = CU.currentUser.mentor_profile;
      CU.sessions = CU._demoSessions();
      CU.pointsHistory = CU._demoPoints();
      CU.certificates = [];
      CU._verifyData = {success:true, status:'verified', is_verified:true, student_id_url:'/demo', days_left: 0};
    } else {
      CU._demoMode = false;
      CU.currentUser = d.user;
      if(CU.currentUser.role !== 'mentor') { location.href='/abuturyent.html'; return; }
      if(CU.currentUser.mentor_profile) CU.mentorData = CU.currentUser.mentor_profile;

      await Promise.allSettled([
        CU.loadSessions(),
        CU.loadPoints(),
        CU.loadCertificates(),
        CU.loadVerificationStatus(),
      ]);
    }

    CU.applyTheme();

    if(onSuccess) onSuccess();

    const ls = document.getElementById('loadingScreen');
    const shell = document.getElementById('appShell');
    if(ls) ls.style.display = 'none';
    if(shell) shell.style.display = 'flex';

  } catch(e) {
    console.error('Init error:', e);
    /* Xato bo'lsa demo rejimda */
    CU._demoMode = true;
    CU.currentUser = CU._demoUser();
    CU.mentorData = CU.currentUser.mentor_profile;
    CU.sessions = CU._demoSessions();
    CU.pointsHistory = CU._demoPoints();
    CU.certificates = [];
    CU._verifyData = {success:true, status:'verified', is_verified:true, student_id_url:'/demo', days_left: 0};

    CU.applyTheme();
    if(onSuccess) onSuccess();

    const ls = document.getElementById('loadingScreen');
    const shell = document.getElementById('appShell');
    if(ls) ls.style.display = 'none';
    if(shell) shell.style.display = 'flex';
  }
};

CU.logout = async function() {
  if(!CU._demoMode) {
    try { await fetch('/api/logout',{method:'POST',credentials:'include'}); } catch(e){}
  }
  location.href = '/login.html';
};

/* ─── DATA LOADERS ─── */
CU.loadSessions = async function() {
  try {
    const d = await CU.API.get('/api/sessions');
    if(d.success) CU.sessions = d.sessions || [];
  } catch(e) { console.error('Sessions load error:', e); }
};

CU.loadPoints = async function() {
  try {
    const d = await CU.API.get('/api/mentor/points');
    if(d.success) CU.pointsHistory = d.points || [];
  } catch(e) { console.error('Points load error:', e); }
};

CU.loadCertificates = async function() {
  try {
    const d = await CU.API.get('/api/mentor/certificates');
    if(d.success) CU.certificates = d.certificates || [];
  } catch(e) { console.error('Certs load error:', e); }
};

CU.loadVerificationStatus = async function() {
  try {
    const d = await CU.API.get('/api/mentor/student-id-status');
    if(d.success) CU._verifyData = d;
    return d;
  } catch(e) { return null; }
};

CU.loadVideos = async function() {
  try {
    const d = await CU.API.get('/api/mentor/videos');
    if(d.success) {
      CU.videos = d.videos || [];
    } else {
      CU.videos = CU._demoVideos();
    }
  } catch(e) {
    CU.videos = CU._demoVideos();
  }
};

/* ─── SESSION PRICE (mentor profilidan) ─── */
CU.sessionPts = function(type) {
  const md = CU.mentorData || {};
  if(type === 'individual') return md.individual_price || 8000;
  if(type === 'group') return md.group_price || 2000;
  return 0;
};

/* ─── UTILS ─── */
CU.fmt = function(n) {
  if(n===undefined||n===null) return '0';
  return Math.abs(Number(n)).toLocaleString('uz-UZ');
};

CU.fmtDate = function(str) {
  if(!str) return '—';
  const d = new Date(str), now = new Date(), diff = d - now;
  if(diff < 0) {
    const ago = Math.floor(-diff/86400000);
    if(ago === 0) return 'Bugun'; if(ago === 1) return 'Kecha'; return `${ago} kun oldin`;
  }
  const days = Math.floor(diff/86400000);
  const t = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  if(days===0) return `Bugun ${t}`; if(days===1) return `Ertaga ${t}`;
  return `${d.getDate()}.${d.getMonth()+1} ${t}`;
};

CU.fmtDateShort = function(str) {
  if(!str) return '—';
  const d = new Date(str);
  return `${d.getDate()}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()}`;
};

CU.timeAgo = function(str) {
  if(!str) return '';
  const sec = Math.floor((Date.now() - new Date(str)) / 1000);
  if(sec < 60) return 'Hozirgina';
  if(sec < 3600) return Math.floor(sec/60) + ' daqiqa oldin';
  if(sec < 86400) return Math.floor(sec/3600) + ' soat oldin';
  if(sec < 7*86400) return Math.floor(sec/86400) + ' kun oldin';
  return new Date(str).toLocaleDateString('uz-UZ');
};

CU.strColor = function(str) {
  let h = 0;
  for(let i=0;i<(str||'').length;i++) h = str.charCodeAt(i)+((h<<5)-h);
  return ['#1e3a6e','#2d1b69','#1a3a2a','#3a1a2a','#6e1e3a','#1e4040','#2a1a40'][Math.abs(h)%7];
};

CU.escHtml = function(s) {
  if(!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
};

CU.ytThumb = function(url) {
  const m = (url||'').match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/);
  return m ? `https://img.youtube.com/vi/${m[1]}/hqdefault.jpg` : '';
};

/* ─── TOAST ─── */
let _toastTimer;
CU.toast = function(msg, type='ok') {
  clearTimeout(_toastTimer);
  let el = document.getElementById('_cuToast');
  if(!el) {
    el = document.createElement('div');
    el.id = '_cuToast';
    el.style.cssText = 'position:fixed;bottom:86px;left:50%;transform:translateX(-50%);background:#1A2A4A;color:#fff;padding:11px 22px;border-radius:20px;font-size:13px;font-weight:600;z-index:9999;box-shadow:0 4px 24px rgba(0,0,0,.6);white-space:nowrap;transition:opacity .3s;pointer-events:none;max-width:90vw;text-align:center';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.borderLeft = type==='err' ? '3px solid #FF4D6A' : '3px solid #00BFA6';
  el.style.opacity = '1';
  _toastTimer = setTimeout(() => el.style.opacity='0', 2800);
};

/* ─── THEME ─── */
CU.applyTheme = function() {
  try {
    if(localStorage.getItem('cu_theme') === 'light') {
      document.body.classList.add('light-theme');
    }
    if (typeof window.updateThemeToggle === 'function') {
      window.updateThemeToggle();
    }
  } catch(e) {}
};

CU.toggleTheme = function() {
  try {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem('cu_theme', isLight ? 'light' : 'dark');
    if (typeof window.updateThemeToggle === 'function') {
      window.updateThemeToggle();
    }
  } catch(e) {}
};

/* ─── MODAL (bottom sheet) ─── */
CU.openModal = function(id) {
  const el = document.getElementById(id);
  if(el) { el.classList.add('open'); document.body.style.overflow = 'hidden'; }
};
CU.closeModal = function(id) {
  const el = document.getElementById(id);
  if(el) { el.classList.remove('open'); document.body.style.overflow = ''; }
};

/* ─── SESSION HELPERS ─── */
CU.sessionBadge = function(status) {
  const clockSvg = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:3px"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  const checkSvg = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:3px"><polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const starSvg  = '<svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle;margin-right:3px"><polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26 12,2"/></svg>';
  const xSvg     = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:3px"><line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>';
  const m = {
    pending:   '<span class="badge b-gold">'   + clockSvg + 'Kutilmoqda</span>',
    confirmed: '<span class="badge b-teal">'   + checkSvg + 'Tasdiqlangan</span>',
    completed: '<span class="badge b-green">'  + starSvg  + 'Tugallandi</span>',
    cancelled: '<span class="badge b-red">'    + xSvg     + 'Bekor</span>',
    in_progress: '<span class="badge b-purple">' + checkSvg + 'Jarayonda</span>',
  };
  return m[status] || '';
};

CU.sessionTypeLabel = function(type) {
  const userSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:3px"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/></svg>';
  const groupSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:3px"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  return type === 'individual' ? userSvg + 'Individual' : type === 'group' ? groupSvg + 'Guruh' : (type||'').toUpperCase();
};

CU.confirmSession = async function(id, onDone) {
  if(CU._demoMode) {
    const s = CU.sessions.find(x=>x.id===id);
    if(s) s.status = 'confirmed';
    CU.toast('Sessiya tasdiqlandi');
    if(onDone) onDone();
    return;
  }
  try {
    const d = await CU.API.post(`/api/sessions/${id}/confirm`, {});
    if(d.success) {
      const s = CU.sessions.find(x=>x.id===id);
      if(s) s.status = 'confirmed';
      CU.toast('Sessiya tasdiqlandi');
      if(onDone) onDone();
    } else CU.toast(d.error||'Xatolik','err');
  } catch(e) { CU.toast('Server xatosi','err'); }
};

CU.rejectSession = async function(id, onDone) {
  if(CU._demoMode) {
    const s = CU.sessions.find(x=>x.id===id);
    if(s) s.status = 'cancelled';
    CU.toast('Rad etildi');
    if(onDone) onDone();
    return;
  }
  try {
    const d = await CU.API.post(`/api/sessions/${id}/reject`, {});
    if(d.success) {
      const s = CU.sessions.find(x=>x.id===id);
      if(s) s.status = 'cancelled';
      CU.toast('Rad etildi');
      if(onDone) onDone();
    } else CU.toast(d.error||'Xatolik','err');
  } catch(e) { CU.toast('Server xatosi','err'); }
};

/* ─── AUTH HEADERS ─── */
CU.authHeaders = function() {
  /* Session cookie based — qo'shimcha header shart emas,
     lekin Telegram WebApp bo'lsa initData ham yuboramiz */
  const headers = {};
  try {
    const tg = window.Telegram?.WebApp;
    if (tg?.initData) {
      headers['X-Telegram-InitData'] = tg.initData;
    }
  } catch(e) {}
  return headers;
};

/* ─── NAVIGATION ─── */
CU.PAGES = {
  'home':     '/mentor-dashboard.html',
  'sessions': '/mentor-sessions.html',
  'videos':   '/mentor-videos.html',
  'earnings': '/mentor-earnings.html',
  'profile':  '/mentor-profile.html',
};

CU.navTo = function(page) {
  const url = CU.PAGES[page];
  if(url) location.href = url;
};

/* ─── ACTIVE NAV HIGHLIGHT ─── */
CU.highlightNav = function(current) {
  document.querySelectorAll('.ni').forEach(n => {
    const page = n.dataset.page;
    n.classList.toggle('active', page === current);
  });
};