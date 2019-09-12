var request = new Request(
  'http://localhost:8000/test_pages/shared/test_image_2.png'
);

self.addEventListener('message', function(event) {
  console.log("Service Worker received message. Fetches image.")
  fetch(request);
});
