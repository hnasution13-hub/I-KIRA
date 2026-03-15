// ============================================================
// sw.js — Service Worker HRIS Portal
// Cache portal shell + queue offline check-in/out
// ============================================================

const CACHE_NAME  = 'hris-portal-v1';
const OFFLINE_URL = '/karyawan/offline/';

// Aset yang di-cache saat install
const PRECACHE = [
  '/karyawan/',
  '/karyawan/offline/',
  '/static/manifest.json',
];

// ── Install: pre-cache shell ─────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE))
  );
  self.skipWaiting();
});

// ── Activate: hapus cache lama ───────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: network-first, fallback ke cache / offline page ──
self.addEventListener('fetch', event => {
  const req = event.request;

  // Jangan intercept request non-GET atau cross-origin
  if (req.method !== 'GET' || !req.url.startsWith(self.location.origin)) return;

  // Endpoint checkin/sync — jangan diinterrupt
  if (req.url.includes('/karyawan/checkin/') || req.url.includes('/karyawan/sync/')) return;

  event.respondWith(
    fetch(req).then(res => {
      // Cache respons sukses untuk halaman portal
      if (res.ok && req.url.includes('/karyawan/')) {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(c => c.put(req, clone));
      }
      return res;
    }).catch(() =>
      caches.match(req).then(cached => cached || caches.match(OFFLINE_URL))
    )
  );
});

// ── Background Sync: kirim antrian offline check-in ─────────
self.addEventListener('sync', event => {
  if (event.tag === 'sync-checkin') {
    event.waitUntil(syncOfflineQueue());
  }
});

async function syncOfflineQueue() {
  // Buka IndexedDB dan kirim semua record yang pending
  const db    = await openDB();
  const items = await getAllPending(db);

  for (const item of items) {
    try {
      const formData = new FormData();
      formData.append('csrfmiddlewaretoken', item.csrf);
      formData.append('mac_address',  item.mac_address  || '');
      formData.append('latitude',     item.latitude     || '');
      formData.append('longitude',    item.longitude    || '');
      formData.append('gps_accuracy', item.gps_accuracy || '');
      formData.append('gps_denied',   item.gps_denied   || '0');
      formData.append('offline_time', item.offline_time || '');
      formData.append('offline_type', item.offline_type || 'checkin');

      const res = await fetch('/karyawan/sync/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
      });

      if (res.ok) {
        await deleteItem(db, item.id);
        // Notifikasi ke user
        self.registration.showNotification('HRIS Portal', {
          body: `${item.offline_type === 'checkin' ? 'Check-in' : 'Check-out'} offline berhasil disinkron (${item.offline_time})`,
          icon: '/static/images/Logo.png',
        });
      }
    } catch (e) {
      // Akan dicoba lagi saat sync berikutnya
    }
  }
}

// ── IndexedDB helpers ────────────────────────────────────────
function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('hris-offline', 1);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('checkin_queue')) {
        const store = db.createObjectStore('checkin_queue', { keyPath: 'id', autoIncrement: true });
        store.createIndex('status', 'status');
      }
    };
    req.onsuccess = e => resolve(e.target.result);
    req.onerror   = e => reject(e.target.error);
  });
}

function getAllPending(db) {
  return new Promise((resolve, reject) => {
    const tx    = db.transaction('checkin_queue', 'readonly');
    const store = tx.objectStore('checkin_queue');
    const req   = store.getAll();
    req.onsuccess = e => resolve(e.target.result || []);
    req.onerror   = e => reject(e.target.error);
  });
}

function deleteItem(db, id) {
  return new Promise((resolve, reject) => {
    const tx    = db.transaction('checkin_queue', 'readwrite');
    const store = tx.objectStore('checkin_queue');
    const req   = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror   = e => reject(e.target.error);
  });
}
