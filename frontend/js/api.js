const API = axios.create({ baseURL: '/api', timeout: 15000 });
API.interceptors.request.use(c => { const t = localStorage.getItem('access_token'); if (t) c.headers.Authorization = `Bearer ${t}`; showLoader(true); return c }, e => Promise.reject(e));
API.interceptors.response.use(r => { showLoader(false); return r }, async e => {
    showLoader(false); const s = e.response?.status; const d = e.response?.data;
    if (s === 401) { localStorage.clear(); if (!location.pathname.endsWith('login.html') && location.pathname !== '/') location.href = '/login.html' }
    const msg = d?.message || (!e.response ? 'Network error. Check the server connection.' : 'Request failed.');
    if (window.Swal) Swal.fire({ icon: 'error', title: `Error${s ? ' ' + s : ''}`, text: msg });
    return Promise.reject(e)
});
function showLoader(v) { const e = document.getElementById('loader'); if (e) e.style.display = v ? 'flex' : 'none' }
function toast(message, icon = 'success') { Swal.fire({ toast: true, position: 'top-end', showConfirmButton: false, timer: 2500, icon, title: message }) }
function logout() { API.post('/auth/logout').finally(() => { localStorage.clear(); location.href = '/login.html' }) }
async function guard(role) { try { const r = await API.get('/auth/validate-token'); if (role && r.data.data.role !== role) location.href = '/unauthorized.html' } catch (_) { } }
