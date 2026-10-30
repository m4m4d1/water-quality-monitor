// Station map and alerts panel. Listens to the dashboard's events from app.js.
(function () {
  "use strict";
  var COLORS = { good: "--good", light: "--light", moderate: "--moderate", heavy: "--heavy" };
  var LABELS = {
    good: ["Meets standard", "Memenuhi baku mutu"], light: ["Lightly polluted", "Cemar ringan"],
    moderate: ["Moderately polluted", "Cemar sedang"], heavy: ["Heavily polluted", "Cemar berat"]
  };
  var PARAM_NAMES = { ph: "pH", do: "DO", bod: "BOD", cod: "COD", tss: "TSS" };
  var map = null;
  var markers = {};

  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  function t(en, id) { return '<span class="t-en">' + esc(en) + '</span><span class="t-id">' + esc(id) + "</span>"; }
  function color(status) { return getComputedStyle(document.documentElement).getPropertyValue(COLORS[status] || "--muted").trim(); }

  function drawMap(stations) {
    if (!window.L) return;
    if (!map) {
      map = window.L.map("map", { scrollWheelZoom: false }).setView([-3, 112], 5);
      window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 13, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      }).addTo(map);
      map.fitBounds(stations.map(function (s) { return [s.lat, s.lon]; }), { padding: [24, 24] });
      document.getElementById("legend").innerHTML = Object.keys(LABELS).map(function (k) {
        return '<span class="status s-' + k + '">' + t(LABELS[k][0], LABELS[k][1]) + "</span>";
      }).join("");
    }
    stations.forEach(function (s) {
      var r = s.latest;
      var c = color(r ? r.status : null);
      var popup = "<b>" + esc(s.name) + "</b><br>" + esc(s.river) + " · " + esc(s.province) +
        (r ? "<br>Index <b>" + r.index.toFixed(2) + "</b> · " + t(r.status_label.en, r.status_label.id) : "");
      if (markers[s.id]) {
        markers[s.id].setStyle({ color: c, fillColor: c }).setPopupContent(popup);
      } else {
        markers[s.id] = window.L.circleMarker([s.lat, s.lon], { radius: 9, color: c, fillColor: c, fillOpacity: 0.75, weight: 2 })
          .bindPopup(popup).addTo(map)
          .on("click", function () { document.dispatchEvent(new CustomEvent("wq:select", { detail: s.id })); });
      }
    });
  }

  function drawAlerts(alerts, stations) {
    var names = {};
    stations.forEach(function (s) { names[s.id] = s.name + " (" + s.river + ")"; });
    document.getElementById("alert-count").textContent = alerts.length;
    var list = document.getElementById("alerts");
    if (!alerts.length) {
      list.innerHTML = '<li class="empty">' + t("No moderate or heavy pollution in the last 24 hours.", "Tidak ada cemar sedang atau berat dalam 24 jam terakhir.") + "</li>";
      return;
    }
    list.innerHTML = alerts.slice(0, 60).map(function (a) {
      var broken = a.exceedances.map(function (e) { return PARAM_NAMES[e.parameter] + " " + e.value; }).join(", ");
      return '<li data-id="' + esc(a.station_id) + '"><span class="when">' + esc(new Date(a.timestamp).toLocaleString()) + "</span>" +
        "<span><b>" + esc(names[a.station_id] || a.station_id) + '</b> <span class="status s-' + a.status + '">' +
        t(a.status_label.en, a.status_label.id) + "</span> · " + a.index.toFixed(2) + "</span>" +
        '<span class="what">' + t("Over the limit: ", "Melebihi baku mutu: ") + esc(broken) + "</span></li>";
    }).join("");
  }

  document.getElementById("alerts").addEventListener("click", function (e) {
    var li = e.target.closest("li[data-id]");
    if (li) document.dispatchEvent(new CustomEvent("wq:select", { detail: li.dataset.id }));
  });

  document.addEventListener("wq:data", async function (e) {
    drawMap(e.detail.stations);
    drawAlerts(await e.detail.api("alerts?hours=24&min_status=moderate") || [], e.detail.stations);
  });

  document.addEventListener("wq:selected", function (e) {
    var m = markers[e.detail.id];
    if (m && map) { map.panTo(m.getLatLng()); m.openPopup(); }
  });
})();
