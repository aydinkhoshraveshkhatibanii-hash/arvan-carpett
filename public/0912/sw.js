const CACHE='expert-0912-v3';
const FILES=['./','./index.html','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
 if(e.request.method!=='GET'||new URL(e.request.url).origin!==self.location.origin)return;
 e.respondWith(caches.open(CACHE).then(async cache=>{
  const cached=await cache.match(e.request);
  if(cached)return cached;
  try{const response=await fetch(e.request);if(response.ok)cache.put(e.request,response.clone());return response}
  catch(err){return (await cache.match('./index.html'))||Response.error()}
 }));
});