const CACHE_NAME = 'traffic-predictor-v1.0.0';
const urlsToCache = [
  '/',
  '/style.css',
  '/script.js',
  '/manifest.json',
  '/icons/favicon-16x16.png',
  '/icons/favicon-32x32.png',
  '/icons/android-icon-192x192.png',
  '/icons/apple-icon-180x180.png'
];

// Install Service Worker
self.addEventListener('install', function(event) {
  console.log('🔧 Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('📦 Caching app shell');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch Event
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Return cached version or fetch from network
        if (response) {
          console.log('📋 Serving from cache:', event.request.url);
          return response;
        }
        
        console.log('🌐 Fetching from network:', event.request.url);
        return fetch(event.request);
      }
    )
  );
});

// Activate Service Worker
self.addEventListener('activate', function(event) {
  console.log('✅ Service Worker activated');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline predictions
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync') {
    console.log('🔄 Background sync triggered');
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  return new Promise(function(resolve) {
    console.log('📊 Performing background traffic data sync');
    // Add your background sync logic here
    setTimeout(resolve, 1000);
  });
}

// Push notification handler
self.addEventListener('push', function(event) {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || '🚦 Traffic update available',
      icon: '/icons/android-icon-192x192.png',
      badge: '/icons/favicon-96x96.png',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: '2'
      },
      actions: [
        {
          action: 'explore',
          title: 'View Traffic',
          icon: '/icons/favicon-32x32.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/icons/favicon-16x16.png'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification('Smart Traffic Predictor', options)
    );
  }
});