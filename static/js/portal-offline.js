// ============================================================
// portal-offline.js — IndexedDB queue + SW registration
// ============================================================

const PORTAL_OFFLINE = (() => {

  // ── Buka IndexedDB ────────────────────────────────────────
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

  // ── Simpan ke queue IndexedDB ─────────────────────────────
  async function queueCheckin(data) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx    = db.transaction('checkin_queue', 'readwrite');
      const store = tx.objectStore('checkin_queue');
      const req   = store.add({ ...data, queued_at: new Date().toISOString() });
      req.onsuccess = e => resolve(e.target.result);
      req.onerror   = e => reject(e.target.error);
    });
  }

  // ── Hitung jumlah pending ─────────────────────────────────
  async function getPendingCount() {
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx    = db.transaction('checkin_queue', 'readonly');
        const store = tx.objectStore('checkin_queue');
        const req   = store.count();
        req.onsuccess = e => resolve(e.target.result || 0);
        req.onerror   = () => resolve(0);
      });
    } catch { return 0; }
  }

  // ── Sync manual (online kembali) ──────────────────────────
  async function syncNow() {
    if (!navigator.onLine) return 0;
    const db = await openDB();
    const items = await new Promise((resolve) => {
      const tx  = db.transaction('checkin_queue', 'readonly');
      const req = tx.objectStore('checkin_queue').getAll();
      req.onsuccess = e => resolve(e.target.result || []);
      req.onerror   = () => resolve([]);
    });

    let synced = 0;
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

        if (res.ok || res.status === 302) {
          // Hapus dari queue
          await new Promise((resolve) => {
            const tx  = db.transaction('checkin_queue', 'readwrite');
            tx.objectStore('checkin_queue').delete(item.id);
            tx.oncomplete = resolve;
          });
          synced++;
        }
      } catch (e) { /* akan dicoba lagi */ }
    }
    return synced;
  }

  // ── Register Service Worker ───────────────────────────────
  async function registerSW() {
    if (!('serviceWorker' in navigator)) return;
    try {
      await navigator.serviceWorker.register('/static/js/sw.js', { scope: '/karyawan/' });
    } catch (e) {
      console.warn('SW register failed:', e);
    }
  }

  return { queueCheckin, getPendingCount, syncNow, registerSW };
})();

// ── Init saat halaman load ────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await PORTAL_OFFLINE.registerSW();

  // Update badge pending
  await updatePendingBadge();

  // Saat online kembali → auto sync
  window.addEventListener('online', async () => {
    updateNetworkBanner(true);
    const synced = await PORTAL_OFFLINE.syncNow();
    if (synced > 0) {
      showSyncToast(`${synced} data offline berhasil disinkron ✓`);
      await updatePendingBadge();
      // Reload setelah sync agar data terbaru tampil
      setTimeout(() => location.reload(), 1500);
    }
  });

  window.addEventListener('offline', () => updateNetworkBanner(false));

  // Cek status awal
  if (!navigator.onLine) updateNetworkBanner(false);
});

async function updatePendingBadge() {
  const count = await PORTAL_OFFLINE.getPendingCount();
  const badge = document.getElementById('offline-pending-badge');
  if (!badge) return;
  if (count > 0) {
    badge.textContent = `${count} data offline menunggu sinkron`;
    badge.style.display = 'block';
  } else {
    badge.style.display = 'none';
  }
}

function updateNetworkBanner(isOnline) {
  const banner = document.getElementById('network-banner');
  if (!banner) return;
  if (isOnline) {
    banner.style.display = 'none';
  } else {
    banner.style.display = 'block';
  }
}

function showSyncToast(msg) {
  const toast = document.createElement('div');
  toast.textContent = msg;
  toast.style.cssText = `
    position:fixed;bottom:80px;left:50%;transform:translateX(-50%);
    background:#27ae60;color:#fff;padding:.6rem 1.2rem;border-radius:20px;
    font-size:.85rem;font-weight:600;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.2);
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
