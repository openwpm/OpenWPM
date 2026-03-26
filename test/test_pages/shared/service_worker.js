var request = new Request(
  'http://localhost:8000/test_pages/shared/test_image_2.png'
);

self.addEventListener('install', function(event) {
  // Skip waiting so the worker activates immediately.
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  console.log("Service Worker activated. Fetches image.");
  // event.waitUntil keeps the worker alive until the fetch completes,
  // ensuring webRequest captures it before the browser shuts down.
  event.waitUntil(fetch(request));
});
