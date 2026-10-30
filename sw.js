/* =====================================================================
   sha9ie service worker — application shell caching.

   What it caches: the HTML entry point, the manifest and the icons.
   The five studios, the tool code, the fonts, the hero image and the six
   bundled third-party libraries (pdf-lib, pdf.js + worker, JSZip, lamejs,
   qrcode-generator) are all inside index.html, so one cached document is
   the whole application.

   What it cannot make offline: anything that needs the browser to fetch a
   remote resource (Firebase sign-in), a codec the browser does not have,
   or a file the user has not picked yet.

   Bump CACHE_VERSION when you redeploy so old shells are dropped.
   ===================================================================== */
const CACHE_VERSION = "sha9ie-shell-v1";
const PRECACHE = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
      .catch((err) => {
        // a missing optional icon must not block installation
        console.warn("[sha9ie sw] precache incomplete:", err && err.message);
        return self.skipWaiting();
      })
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // never proxy third-party requests

  // Navigations: serve the cached shell first so the app opens offline, then
  // refresh the cache in the background when the network is available.
  if (req.mode === "navigate") {
    event.respondWith(
      caches.match("./index.html").then((cached) => {
        const network = fetch(req)
          .then((res) => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE_VERSION).then((cache) => cache.put("./index.html", copy));
            }
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // Static assets: cache-first, with a background revalidation.
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) {
        fetch(req).then((res) => {
          if (res && res.ok) caches.open(CACHE_VERSION).then((cache) => cache.put(req, res));
        }).catch(() => {});
        return cached;
      }
      return fetch(req).then((res) => {
        if (res && res.ok && res.type === "basic") {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(req, copy));
        }
        return res;
      }).catch(() =>
        new Response("This resource is not cached and the network is unavailable.", {
          status: 503,
          headers: { "Content-Type": "text/plain" }
        })
      );
    })
  );
});
