const CACHE = "moto-track-v2";
const ASSETS = [
  "/",
  "/static/css/style.css",
  "/static/css/animations.css",
  "/static/css/motion.css",
  "/static/js/animations.js",
  "/static/js/offline-queue.js",
  "/static/icons/icon.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/api/")) return;

  e.respondWith(
    caches.match(e.request).then((cached) => {
      const network = fetch(e.request).then((res) => {
        if (res.ok && url.origin === self.location.origin) {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
        }
        return res;
      });
      return cached || network;
    })
  );
});

self.addEventListener("sync", (e) => {
  if (e.tag === "moto-sync") {
    e.waitUntil(
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => client.postMessage({ type: "SYNC_QUEUE" }));
      })
    );
  }
});

self.addEventListener("push", (e) => {
  let data = { title: "Moto Track", body: "Maintenance reminder" };
  try {
    if (e.data) data = e.data.json();
  } catch (_) {}
  e.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/static/icons/icon.svg",
      tag: data.tag || "moto-reminder",
    })
  );
});
