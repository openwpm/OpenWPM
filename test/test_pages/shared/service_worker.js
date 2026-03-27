var IMAGE_URL = 'http://localhost:8000/test_pages/shared/test_image_2.png';

self.addEventListener('install', function(event) {
  // Skip the waiting phase so this worker activates immediately after install.
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', function(event) {
  console.log("Service Worker activated. Fetches image.");
  // waitUntil() extends the worker's lifetime until the fetch completes, so the
  // webRequest event fires before the browser is allowed to terminate the worker.
  event.waitUntil(fetch(IMAGE_URL));
});
