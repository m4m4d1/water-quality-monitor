// Water Quality Monitoring System dashboard. Talks to the API; when there is no
// API (the GitHub Pages demo) it reads the same responses from data/demo.json.
(function () {
  "use strict";
  var root = document.documentElement;
  var demo = null;
  var selected = null;
  var chart = null;

  // ---- language ---------------------------------------------------------
  try {
    var saved = localStorage.getItem("lang") || ((navigator.language || "").slice(0, 2) === "id" ? "id" : "en");
    root.dataset.lang = saved;
  } catch (e) {}
  document.querySelector(".lang").addEventListener("click", function () {
    root.dataset.lang = root.dataset.lang === "en" ? "id" : "en";
    try { localStorage.setItem("lang", root.dataset.lang); } catch (e) {}
  });

  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  function t(en, id) { return '<span class="t-en">' + esc(en) + '</span><span class="t-id">' + esc(id) + "</span>"; }
  function fmt(v, digits) { return v == null ? "–" : Number(v).toFixed(digits == null ? 1 : digits); }

  // ---- data -------------------------------------------------------------
  async function api(path) {
    if (!demo) {
      try {
        var res = await fetch("api/" + path);
        if (res.ok && (res.headers.get("content-type") || "").indexOf("json") !== -1) return res.json();
      } catch (e) {}
      var file = await fetch("data/demo.json");
      demo = await file.json();
      document.body.classList.add("is-demo");
    }
    return demo.api[path];
  }

  var PARAMS = [
    ["ph", "pH", "pH", "", 2], ["do", "Dissolved O₂", "O₂ terlarut", "mg/L", 2],
    ["bod", "BOD", "BOD", "mg/L", 1], ["cod", "COD", "COD", "mg/L", 0],
    ["tss", "TSS", "TSS", "mg/L", 0], ["temperature", "Temperature", "Suhu", "°C", 1]
  ];

  // ---- rendering --------------------------------------------------------
  function statusTag(r) {
    return r ? '<span class="status s-' + r.status + '">' + t(r.status_label.en, r.status_label.id) + "</span>" : "–";
  }

  function renderKpis(summary) {
    var c = summary.status_counts;
    var items = [
      ["var(--accent)", summary.reporting + "/" + summary.stations, "Stations reporting", "Stasiun melapor"],
      ["var(--good)", c.good, "Meet standard", "Memenuhi baku mutu"],
      ["var(--light)", c.light, "Lightly polluted", "Cemar ringan"],
      ["var(--moderate)", c.moderate, "Moderately polluted", "Cemar sedang"],
      ["var(--heavy)", c.heavy, "Heavily polluted", "Cemar berat"],
      ["var(--muted)", summary.alerts_24h, "Alerts (24 h)", "Peringatan (24 jam)"]
    ];
    document.getElementById("kpis").innerHTML = items.map(function (k) {
      return '<div class="kpi" style="--c:' + k[0] + '"><b>' + esc(k[1]) + "</b><span>" + t(k[2], k[3]) + "</span></div>";
    }).join("");
  }

  function renderTable(stations) {
    var rows = stations.slice().sort(function (a, b) {
      return (b.latest ? b.latest.index : -1) - (a.latest ? a.latest.index : -1);
    });
    document.getElementById("station-rows").innerHTML = rows.map(function (s) {
      var r = s.latest || {};
      var over = function (p) { return (r.exceedances || []).some(function (e) { return e.parameter === p; }) ? ' class="num bad"' : ' class="num"'; };
      return '<tr data-id="' + esc(s.id) + '"' + (s.id === selected ? ' class="selected"' : "") + ">" +
        "<td><b>" + esc(s.name) + "</b></td><td>" + esc(s.river) + "</td><td>" + statusTag(s.latest) + "</td>" +
        '<td class="num"><b>' + fmt(r.index, 2) + "</b></td><td" + over("do") + ">" + fmt(r.do) + "</td>" +
        "<td" + over("bod") + ">" + fmt(r.bod) + "</td><td" + over("ph") + ">" + fmt(r.ph) + "</td></tr>";
    }).join("");
  }

  async function renderDetail(station) {
    var r = station.latest;
    document.getElementById("d-name").textContent = station.name;
    document.getElementById("d-where").textContent = station.river + " · " + station.province;
    document.getElementById("d-status").innerHTML = statusTag(r);
    document.getElementById("d-index").textContent = r ? fmt(r.index, 2) : "–";
    var broken = (r && r.exceedances || []).map(function (e) { return e.parameter; });
    document.getElementById("d-params").innerHTML = PARAMS.map(function (p) {
      return '<div class="param' + (broken.indexOf(p[0]) !== -1 ? " over" : "") + '"><span>' + t(p[1], p[2]) +
        "</span><b>" + fmt(r && r[p[0]], p[4]) + "</b> <small>" + p[3] + "</small></div>";
    }).join("");

    var history = await api("stations/" + station.id + "/readings?hours=72") || [];
    var labels = history.map(function (h) {
      var d = new Date(h.timestamp);
      return d.toLocaleString(root.dataset.lang === "id" ? "id-ID" : "en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" });
    });
    var style = getComputedStyle(root);
    var datasets = [
      { label: "Index", data: history.map(function (h) { return h.index; }), borderColor: style.getPropertyValue("--heavy").trim(), yAxisID: "y" },
      { label: "DO (mg/L)", data: history.map(function (h) { return h.do; }), borderColor: style.getPropertyValue("--accent").trim(), yAxisID: "y1" },
      { label: "BOD (mg/L)", data: history.map(function (h) { return h.bod; }), borderColor: style.getPropertyValue("--light").trim(), yAxisID: "y1" }
    ];
    datasets.forEach(function (d) { d.borderWidth = 2; d.pointRadius = 0; d.tension = 0.3; });
    if (chart) chart.destroy();
    chart = new window.Chart(document.getElementById("d-chart"), {
      type: "line",
      data: { labels: labels, datasets: datasets },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { labels: { boxWidth: 12, color: style.getPropertyValue("--muted").trim() } } },
        scales: {
          x: { ticks: { maxTicksLimit: 6, color: style.getPropertyValue("--muted").trim() }, grid: { display: false } },
          y: { position: "left", title: { display: true, text: "Index" }, grid: { color: style.getPropertyValue("--line").trim() } },
          y1: { position: "right", title: { display: true, text: "mg/L" }, grid: { display: false } }
        }
      }
    });
  }

  // ---- wiring -----------------------------------------------------------
  var stationsCache = [];

  function select(id) {
    selected = id;
    var s = stationsCache.find(function (x) { return x.id === id; });
    if (!s) return;
    document.querySelectorAll("#station-rows tr").forEach(function (tr) { tr.classList.toggle("selected", tr.dataset.id === id); });
    renderDetail(s);
    document.dispatchEvent(new CustomEvent("wq:selected", { detail: s }));
  }

  document.getElementById("station-rows").addEventListener("click", function (e) {
    var tr = e.target.closest("tr");
    if (tr) select(tr.dataset.id);
  });
  document.addEventListener("wq:select", function (e) { select(e.detail); });

  async function refresh() {
    var results = await Promise.all([api("stations"), api("summary")]);
    stationsCache = results[0];
    renderKpis(results[1]);
    renderTable(stationsCache);
    var latest = stationsCache.map(function (s) { return s.latest && s.latest.timestamp; }).filter(Boolean).sort().pop();
    document.getElementById("updated").textContent = latest ? new Date(latest).toLocaleString() : "–";
    if (!selected && results[1].worst) selected = results[1].worst.station_id;
    select(selected);
    document.dispatchEvent(new CustomEvent("wq:data", { detail: { stations: stationsCache, api: api } }));
  }

  refresh();
  setInterval(function () { if (!demo) refresh(); }, 60000);
})();
