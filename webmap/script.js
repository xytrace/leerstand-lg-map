const config = await (await fetch("config.json")).json();
const SUPABASE_URL = config.supabase_url;
const SUPABASE_API_KEY = config.supabase_key;
const TABLE_NAME = config.supabase_table || "meldungen";

const map = L.map("map").setView([53.246, 10.414], 13);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

// External red icon
const redIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// MarkerClusterGroup with maxClusterRadius of ~200 meters
const markerClusterGroup = L.markerClusterGroup({
  maxClusterRadius: 100  // pixels; roughly corresponds to ~200m at zoom level 13–15
});
map.addLayer(markerClusterGroup);

async function fetchMeldungen() {
  const url = `${SUPABASE_URL}/rest/v1/${TABLE_NAME}?select=adresse,wohnungslage,dauer,bestaetigungen,image_url,lat,lon,created_at`;
  const res = await fetch(url, {
    headers: {
      apikey: SUPABASE_API_KEY,
      Authorization: `Bearer ${SUPABASE_API_KEY}`
    }
  });
  const data = await res.json();

  markerClusterGroup.clearLayers();

  data.forEach(item => {
    if (!item.lat || !item.lon) return;

    let html = `<b>${item.adresse || "Unbekannte Adresse"}</b><br>`;
    if (item.wohnungslage) html += `🧱 Wohnungslage: ${item.wohnungslage}<br>`;
    if (item.dauer) html += `⏳ Leerstand seit: ${item.dauer}<br>`;
    if (item.bestaetigungen !== null) html += `👍 Bestätigungen: ${item.bestaetigungen}<br>`;
    if (item.created_at) html += `📅 Gemeldet am: ${new Date(item.created_at).toLocaleDateString()}<br>`;
    if (item.image_url) html += `<br><img src="${item.image_url}" width="200" style="margin-top:5px;">`;

    const marker = L.marker([item.lat, item.lon], { icon: redIcon }).bindPopup(html);
    markerClusterGroup.addLayer(marker);
  });
}

fetchMeldungen();
setInterval(fetchMeldungen, 30000); // alle 30 Sekunden aktualisieren
