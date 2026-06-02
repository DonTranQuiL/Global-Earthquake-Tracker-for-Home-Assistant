<div align="center">

<img width="1024" height="434" alt="Global Earthquake Tracker Header"  src="https://github.com/user-attachments/assets/e541c943-38d1-436f-9f42-5458d28b753e" />


# 🌍 Global Earthquake Tracker
**The high-performance, real-time global seismic and tsunami early warning system for Home Assistant.**

> ⚠️ **LATEST RELEASE ANNOUNCEMENT:** > We have successfully migrated to a **Dynamic Entity Lifecycle Engine**! The tracker now securely hooks into the USGS 7-Day API, utilizing dual-magnitude thresholds and zero-bloat spawning logic. Custom local map pins and Tsunami warnings are now fully supported!

[![Latest Release](https://img.shields.io/github/v/release/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant?style=for-the-badge&color=007ec6)](https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/releases)
[![License](https://img.shields.io/github/license/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant?style=for-the-badge&color=007ec6)](https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/blob/main/LICENSE)
[![Home Assistant CI](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/hass-ci.yml?label=Home%20Assistant%20CI&style=for-the-badge)](https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/actions/workflows/hass-ci.yml)
[![Code Checks](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/codechecker.yml?style=for-the-badge&label=CODE%20CHECKS&color=5dbb0f)](https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/actions)
[![Tests](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/pytest.yml?style=for-the-badge&label=TESTS&color=5dbb0f)](https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/actions)
[![HACS Validation](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/hacs.yaml?style=for-the-badge&label=HACS%20VALIDATION&color=5dbb0f)](https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/actions)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-5dbb0f?style=for-the-badge)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000?style=for-the-badge)](https://github.com/astral-sh/ruff)
[![HACS Custom](https://img.shields.io/badge/HACS-CUSTOM-ff6e27?style=for-the-badge)](https://hacs.xyz/)
[![Home Assistant Version](https://img.shields.io/badge/Home%20Assistant-2025.1%2B-007ec6?style=for-the-badge)](https://www.home-assistant.io/)
[![Maintainer](https://img.shields.io/badge/maintainer-%40DonTranQuiL-007ec6?style=for-the-badge)](https://github.com/DonTranQuiL)
[![Donate](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-ffdd00?style=for-the-badge)](https://ko-fi.com/DonTranQuiL)
[![Community Forum](https://img.shields.io/badge/community-forum-007ec6?style=for-the-badge)](https://community.home-assistant.io/t/ads-b-tracker-for-home-assistant/1011081)

</div>

### 🚨 Real-Time Seismic Intelligence
Bring ultra-fast, live earthquake and tsunami telemetry directly into Home Assistant using the official **USGS Worldwide Network API**. Engineered for precision, this integration filters out the noise (like quarry blasts) and delivers highly accurate, color-coded map pins for actual tectonic events anywhere on the globe.

---

## 📥 Installation

### Method 1: HACS (Recommended)
The most efficient deployment method is through **HACS** (Home Assistant Community Store):

1. Open **HACS** in your sidebar and navigate into the **Integrations** panel.
2. Click the three dots (`...`) located in the upper right quadrant and select **Custom repositories**.
3. Input the repository web link: `https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant`
4. Set the Category selector dropdown to **Integration** and hit **Add**.
5. Locate the newly added **Global Earthquakes** repository card and hit **Download**.
6. ⚠️ **Restart your Home Assistant instance**.
7. Navigate to **Settings > Devices & Services > Add Integration**, lookup **Global Earthquakes**, and configure your regions.

### Method 2: Manual Installation
1. Download the latest release from the [Releases page](https://github.com/DonTranQuiL/Global-Earthquake-Tracker-for-Home-Assistant/releases).
2. Extract the `global_earthquakes` folder into your Home Assistant's `custom_components` directory.
3. ⚠️ **Restart your Home Assistant instance**.
4. Configure via **Settings > Devices & Services > Add Integration**.

---

## 🌟 Core Features & Architecture

### 🎛️ Dual-Magnitude Smart Filtering
The USGS sensor network inside the United States is hyper-sensitive, capturing thousands of microscopic 1.0M rumbles, while global stations usually only guarantee detection at 4.5M. Our configuration flow allows you to set **two independent magnitude sliders**—one for the USA, and one for the Rest of the World. Filter out the North American noise while maintaining a strict, low-magnitude watch on Europe and beyond!

### 🧹 Dynamic Zero-Bloat Entity Lifecycle
Standard integrations spin up permanent entities for every event, destroying your Home Assistant database. This component enforces a strict **Dynamic Lifecycle Policy**:
* The integration acts as a smart manager, spawning a brand new, unique sensor only when a fresh earthquake appears in the API.
* When an earthquake ages out of the 7-day USGS feed, the manager hooks into the HA Core and applies an aggressive `force_remove`. 
* No lingering `Unknown` states. No empty placeholder entities. Just a pristine database.

### 🔬 Rich Scientific Telemetry
Every single earthquake sensor is packed with hidden attributes for dashboard extraction:
* **Tsunami Warnings:** Instant boolean flags if a tsunami is generated.
* **Alert Levels:** USGS PAGER system (Green, Yellow, Orange, Red) estimating human/economic impact.
* **Event Type:** Algorithmically filters out non-natural events, but clearly labels `Earthquake`, `Volcano`, or `Ice Quake`.
* **Depth & Coordinates:** Highly accurate telemetry for map mapping.

---

## 🗺️ Local Map Assets (Custom Icons)
Want beautiful, highly realistic icons on your Home Assistant map? The integration features a registered static web path that prioritizes your local files over standard Material Design Icons!

1. Navigate inside your core file system to `/config/custom_components/global_earthquakes/`
2. Create a folder named `www`
3. Drop transparent `.png` files inside that folder, named exactly:
   * `earthquake.png`
   * `tsunami.png`
   * `volcano.png`
   * `default.png`
4. **Restart Home Assistant.** Your Live Map will dynamically swap these icons based on the disaster type!

---

## ⚙️ Interactive Lovelace Dashboard Configurations
Build a complete, professional-grade seismic operations center directly inside your Lovelace dashboard using community cards.

### 📍 The Auto-Updating Live Map
*Requires [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) from HACS.* This card automatically hunts down newly spawned earthquakes and drops them onto the map, while hiding the anchor sensors.

<img width="379" height="448" alt="{35F81328-F96D-4ADB-91F1-B60E4CEF7227}" src="https://github.com/user-attachments/assets/f4c615d8-10ab-490c-8065-96168f19ace1" />


```yaml
type: custom:auto-entities
show_empty: false
card:
  type: map
  title: Live Epicenters
  default_zoom: 4
  dark_mode: true
  entities: []
filter:
  include:
    - entity_id: "sensor.earthquake_tracker_global_tracker_*"
  exclude:
    - entity_id: "sensor.earthquake_tracker_global_tracker"
    - entity_id: "*last_sync*"
    - entity_id: "*last_update*"
```
## 🌍 The Glassmorphism Seismic Log
Requires flex-table-card and card-mod from HACS. Pulls the history array from the anchor sensor to create a stunning, color-coded telemetry table that automatically cycles out old data.
<img width="744" height="189" alt="{FBD80937-754F-41F2-BD0A-C0B0CCE9DE3E}" src="https://github.com/user-attachments/assets/0093c8fe-59e6-46e9-be87-ce66eb25fd0a" />


```yaml
type: custom:flex-table-card
title: 🌍 Live Seismic Log
icon: mdi:pulse
strict: false
sort_by:
  - magnitude-
max_rows: 20
entities:
  include: sensor.earthquake_tracker_global_tracker
css:
  table+: |
    border-collapse: collapse;
    width: 100%;
  tbody tr:nth-child(even):
    background-color: rgba(255,255,255,0.02);
  tbody tr:hover:
    background-color: rgba(255,255,255,0.06);
  th:
    padding: 12px 6px;
    font-size: 12px;
    font-weight: 700;
    color: #94a3b8;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  td:
    padding: 10px 6px;
    vertical-align: middle;
    border-bottom: 1px solid rgba(255,255,255,0.04);
card_mod:
  style: |
    ha-card {
      border-radius: 18px;
      padding: 12px;
      background:
        linear-gradient(
          145deg,
          rgba(20,20,25,0.95),
          rgba(35,35,45,0.90)
        );
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.05);
    }
columns:
  - name: Mag
    data: history
    align: center
    modify: |
      var m = parseFloat(x.magnitude);
      var color = m >= 6.0 ? '#ef4444' : (m >= 4.5 ? '#f59e0b' : '#10b981');
      `<div style="background:${color}15; color:${color}; padding:4px 0px; border-radius:8px; font-weight:800; font-size:16px; border: 1px solid ${color}40; min-width:45px; display:inline-block; text-shadow: 0 0 8px ${color}40;">
        ${m.toFixed(1)}
      </div>`
  - name: Location & Type
    data: history
    modify: |
      ` <div style="line-height:1.4;">
        <div style="font-weight:700; font-size:14px; color:#f1f5f9;">
          ${x.location}
        </div>
        <div style="margin-top:4px;">
          <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; padding:2px 8px; border-radius:12px; font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">
            ${x.event_type || "Unknown"}
          </span>
        </div>
      </div> `
  - name: Telemetry
    data: history
    modify: |
      ` <div style="line-height:1.5;">
        <div style="font-size:12px; color:#38bdf8; font-weight:600;">
          📉 ${x.depth_km ? x.depth_km.toFixed(1) + " km" : "Surface"}
        </div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">
          ⏱️ ${x.time ? x.time.replace(' UTC', '') : "N/A"}
        </div>
      </div> `
  - name: Warning
    data: history
    align: center
    modify: |
      var alertHtml = "";
      if (x.alert_level && x.alert_level !== "None") {
        var al = x.alert_level.toLowerCase();
        var bg, txt, border;
        if (al === "red") { bg = "#7f1d1d"; txt = "#fca5a5"; border = "#ef4444"; }
        else if (al === "orange") { bg = "#7c2d12"; txt = "#fdba74"; border = "#f97316"; }
        else if (al === "yellow") { bg = "#713f12"; txt = "#fef08a"; border = "#eab308"; }
        else { bg = "#14532d"; txt = "#86efac"; border = "#22c55e"; }
        
        alertHtml = `<div style="background:${bg}; color:${txt}; border:1px solid ${border}60; padding:3px 8px; border-radius:12px; font-size:10px; font-weight:800; letter-spacing:0.05em; display:inline-block;">
          ${x.alert_level.toUpperCase()}
        </div>`;
      }
      var tsuHtml = x.tsunami_warning ? `<div style="background:#7f1d1d; color:#fca5a5; border:1px solid #ef444460; padding:3px 8px; border-radius:12px; font-size:10px; font-weight:800; margin-top:4px; display:inline-block; letter-spacing:0.05em;">🌊 TSUNAMI</div>` : "";
      (alertHtml || tsuHtml) ? `<div style="display:flex; flex-direction:column; gap:4px; align-items:center;">${alertHtml}${tsuHtml}</div>` : `<span style="color:rgba(255,255,255,0.2); font-size:11px; font-weight:600;">NO ALERT</span>`
```

## 🤝 Credits
A massive thank you to the United States Geological Survey (USGS) for providing open-access, real-time seismic telemetry to the public.
