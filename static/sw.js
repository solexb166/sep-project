const CACHE = 'sep-v1';

const PRECACHE = [
  '/',
  '/marketplace/',
  '/skills/',
  '/static/css/main.css',
  '/static/css/chatbot.css',
  '/static/js/main.js',
  '/static/js/chatbot.js',
  '/static/icons/icon-192.png',
];

// Install: cache core assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(PRECACHE))
  );
  self.skipWaiting();
});

// Activate: clear old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: network first, fall back to cache
self.addEventListener('fetch', e => {
  // Only handle GET requests
  if (e.request.method !== 'GET') return;
  // Skip cross-origin requests and browser extensions
  if (!e.request.url.startsWith(self.location.origin)) return;
  // Skip admin panel — always needs live data
  if (e.request.url.includes('/admin/')) return;

  e.respondWith(
    fetch(e.request)
      .then(response => {
        // Cache successful responses for static assets
        if (response.ok && e.request.url.includes('/static/')) {
          const clone = response.clone();
          caches.open(CACHE).then(cache => cache.put(e.request, clone));
        }
        return response;
      })
      .catch(() => {
        // Offline: serve from cache
        return caches.match(e.request).then(cached => {
          if (cached) return cached;
          // Offline fallback for HTML pages
          if (e.request.headers.get('accept').includes('text/html')) {
            return caches.match('/');
          }
        });
      })
  );
});
