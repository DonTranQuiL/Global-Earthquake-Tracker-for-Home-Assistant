class EarthquakeHistoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.expandedEvents = new Set();
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define the history feed entity');
    }
    this.config = config;
  }

  set hass(hass) {
    const entityId = this.config.entity;
    const stateObj = hass.states[entityId];

    if (!stateObj) {
      this.shadowRoot.innerHTML = `<ha-card style="color: red; padding: 16px;">Entity not found: ${entityId}</ha-card>`;
      return;
    }

    const events = stateObj.attributes.events || [];
    const totalEvents = events.length;
    const dangerousEvents = events.filter(e => e.magnitude >= 5.0).length;

    const currentDataStr = JSON.stringify(events);
    if (this._oldDataStr === currentDataStr) return;
    this._oldDataStr = currentDataStr;

    this.render(events, totalEvents, dangerousEvents);
  }

  render(events, totalEvents, dangerousEvents) {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --card-bg: #0d1527;
          --panel-bg: #131e35;
          --accent-color: #00bcd4;
          --text-main: #ffffff;
          --text-muted: #7e8b9b;
          --mag-low: #00b894;
          --mag-mid: #e17055;
          --mag-high: #d63031;
          --crit-glow: rgba(214, 48, 49, 0.2);
        }

        ha-card {
          background: var(--card-bg);
          color: var(--text-main);
          padding: 24px;
          border-radius: 16px;
          font-family: 'Roboto', sans-serif;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6);
          overflow: hidden;
        }

        /* --- COMMAND CENTER ICON HEADER PRO BLOCK --- */
        .header-container {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          padding-bottom: 18px;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .icon-bay {
          background: rgba(0, 188, 212, 0.08);
          border: 1px solid rgba(0, 188, 212, 0.25);
          border-radius: 12px;
          width: 52px;
          height: 52px;
          display: flex;
          justify-content: center;
          align-items: center;
          color: var(--accent-color);
          box-shadow: 0 0 15px rgba(0, 188, 212, 0.15);
          animation: pulse-icon-border 2.5s infinite alternate ease-in-out;
        }

        .icon-bay ha-icon {
          --mdc-icon-size: 28px;
          animation: spin-radar 6s infinite linear;
        }

        .title-matrix {
          display: flex;
          flex-direction: column;
        }

        .title {
          font-size: 1.4rem;
          font-weight: 800;
          letter-spacing: 0.75px;
          text-transform: uppercase;
          color: var(--text-main);
          background: linear-gradient(125deg, #ffffff 60%, #a5b4fc);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .subtitle {
          font-size: 0.75rem;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 1.5px;
          margin-top: 2px;
          font-weight: 600;
        }

        .chips {
          display: flex;
          gap: 12px;
        }

        .chip {
          padding: 6px 14px;
          border-radius: 20px;
          font-size: 0.8rem;
          font-weight: bold;
          display: flex;
          align-items: center;
          background: rgba(255,255,255,0.03);
        }

        .chip.active-inventory {
          color: #2ecc71;
          border: 1px solid rgba(46, 204, 113, 0.25);
          background: rgba(46, 204, 113, 0.08);
        }

        .chip.danger-count {
          color: #e74c3c;
          border: 1px solid rgba(231, 76, 60, 0.3);
          background: rgba(231, 76, 60, 0.08);
          box-shadow: 0 0 10px rgba(231, 76, 60, 0.15);
        }

        /* --- EVENT LIST CONTAINERS --- */
        .events-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          max-height: 450px;
          overflow-y: auto;
          padding-right: 6px;
        }

        .events-list::-webkit-scrollbar {
          width: 6px;
        }
        .events-list::-webkit-scrollbar-thumb {
          background: var(--panel-bg);
          border-radius: 4px;
        }

        .event-item {
          background: var(--panel-bg);
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.03);
          overflow: hidden;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .event-item:hover {
          border-color: rgba(0, 188, 212, 0.35);
          box-shadow: 0 6px 18px rgba(0, 188, 212, 0.12);
          transform: translateY(-1px);
        }

        .event-item.critical-quake {
          border-left: 4px solid var(--mag-high);
          background: linear-gradient(90deg, rgba(214, 48, 49, 0.03) 0%, var(--panel-bg) 100%);
        }

        .event-main {
          display: flex;
          align-items: center;
          padding: 14px;
          cursor: pointer;
        }

        /* --- MAGNITUDE METERS --- */
        .mag-badge {
          width: 46px;
          height: 46px;
          border-radius: 10px;
          display: flex;
          justify-content: center;
          align-items: center;
          font-weight: 900;
          font-size: 1.15rem;
          margin-right: 16px;
          flex-shrink: 0;
          color: white;
          text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .mag-low { background: var(--mag-low); }
        .mag-mid { background: var(--mag-mid); }
        
        .mag-high { 
          background: var(--mag-high);
          box-shadow: 0 0 14px var(--mag-high);
          animation: rumble 0.35s infinite linear alternate;
        }

        .info-block {
          flex-grow: 1;
          min-width: 0;
        }

        .location {
          font-weight: 700;
          font-size: 1rem;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 3px;
          letter-spacing: 0.2px;
        }

        .time-stamp {
          font-size: 0.78rem;
          color: var(--text-muted);
        }

        .action-icon {
          color: var(--text-muted);
          transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          margin-left: 10px;
        }

        .event-item.expanded .action-icon {
          transform: rotate(180deg);
          color: var(--accent-color);
        }

        /* --- INTERACTIVE MATRICES PANEL --- */
        .details-panel {
          max-height: 0;
          overflow: hidden;
          transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          background: rgba(0, 0, 0, 0.25);
          font-size: 0.88rem;
          border-top: 1px solid rgba(255,255,255,0.03);
        }

        .event-item.expanded .details-panel {
          max-height: 250px;
        }

        .details-grid {
          padding: 16px;
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 10px 20px;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          padding-bottom: 6px;
        }

        .detail-label {
          color: var(--text-muted);
        }

        .detail-val {
          font-weight: bold;
        }

        .map-btn {
          grid-column: span 2;
          background: rgba(0, 188, 212, 0.12);
          color: var(--accent-color);
          text-align: center;
          padding: 8px;
          border-radius: 8px;
          text-decoration: none;
          font-weight: bold;
          font-size: 0.82rem;
          margin-top: 8px;
          border: 1px solid rgba(0, 188, 212, 0.25);
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 6px;
          transition: all 0.2s ease;
        }

        .map-btn:hover {
          background: rgba(0, 188, 212, 0.25);
          box-shadow: 0 0 10px rgba(0, 188, 212, 0.2);
        }

        /* --- TERMINAL STREAM FOOTER FIXED & POLISHED --- */
        .stream-footer {
          margin-top: 24px;
          background: #050810;
          border-radius: 10px;
          padding: 12px 16px;
          font-family: 'Courier New', Courier, monospace;
          font-size: 0.78rem;
          border-left: 3px solid var(--accent-color);
          box-shadow: inset 0 2px 8px rgba(0,0,0,0.9);
        }

        .stream-title-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          color: var(--text-muted);
          margin-bottom: 8px;
          font-weight: bold;
          letter-spacing: 0.5px;
        }

        .live-status-indicator {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .live-lens {
          width: 8px;
          height: 8px;
          background-color: var(--accent-color);
          border-radius: 50%;
          box-shadow: 0 0 10px var(--accent-color);
          animation: lens-glow 1.4s infinite alternate ease-in-out;
        }

        .stream-live-tag {
          color: var(--accent-color);
          font-weight: 900;
          letter-spacing: 1px;
        }

        .stream-line {
          color: #a5b4fc;
          margin: 3px 0;
          line-height: 1.4;
          word-break: break-all;
        }

        /* --- ADVANCED ANIMATIONS FLUX --- */
        @keyframes lens-glow {
          0% { transform: scale(0.9); opacity: 0.4; box-shadow: 0 0 4px var(--accent-color); }
          100% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 12px var(--accent-color), 0 0 20px rgba(0, 188, 212, 0.4); }
        }

        @keyframes pulse-icon-border {
          0% { border-color: rgba(0, 188, 212, 0.25); box-shadow: 0 0 8px rgba(0, 188, 212, 0.1); }
          100% { border-color: rgba(0, 188, 212, 0.6); box-shadow: 0 0 18px rgba(0, 188, 212, 0.3); }
        }

        @keyframes spin-radar {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        @keyframes rumble {
          0% { transform: translate(1px, 1px) rotate(0deg); }
          20% { transform: translate(-1px, -1px) rotate(-0.5deg); }
          40% { transform: translate(-1px, 1px) rotate(0.5deg); }
          60% { transform: translate(1px, -1px) rotate(0deg); }
          80% { transform: translate(-1px, 1px) rotate(-0.5deg); }
          100% { transform: translate(1px, 1px) rotate(0.5deg); }
        }
      </style>

      <ha-card>
        <!-- MASTER COMMAND BAY HEADER -->
        <div class="header-container">
          <div class="header-left">
            <div class="icon-bay">
              <ha-icon icon="mdi:radar"></ha-icon>
            </div>
            <div class="title-matrix">
              <div class="title">Seismic Command Center</div>
              <div class="subtitle">Global Real-time Telemetry Engine</div>
            </div>
          </div>
          <div class="chips">
            <div class="chip active-inventory">${totalEvents} Logged</div>
            ${dangerousEvents > 0 ? `<div class="chip danger-count">${dangerousEvents} Critical (=5M)</div>` : ''}
          </div>
        </div>

        <!-- TIMELINE FEED -->
        <div class="events-list">
          ${events.map(event => {
            const isExpanded = this.expandedEvents.has(event.id);
            const isCritical = event.magnitude >= 5.0;
            
            let magClass = 'mag-low';
            if (event.magnitude >= 4.5 && event.magnitude < 5.5) magClass = 'mag-mid';
            if (event.magnitude >= 5.5) magClass = 'mag-high';

            return `
              <div class="event-item ${isExpanded ? 'expanded' : ''} ${isCritical ? 'critical-quake' : ''}" data-id="${event.id}">
                <div class="event-main">
                  <div class="mag-badge ${magClass}">${event.magnitude}</div>
                  <div class="info-block">
                    <div class="location">${event.location}</div>
                    <div class="time-stamp">${event.time}</div>
                  </div>
                  <div class="action-icon">
                    <ha-icon icon="mdi:chevron-down"></ha-icon>
                  </div>
                </div>
                
                <div class="details-panel">
                  <div class="details-grid">
                    <div class="detail-row"><span class="detail-label">Type:</span><span class="detail-val">${event.event_type}</span></div>
                    <div class="detail-row"><span class="detail-label">Depth:</span><span class="detail-val">${event.depth_km} km</span></div>
                    <div class="detail-row"><span class="detail-label">Tsunami Warning:</span><span class="detail-val" style="color: ${event.tsunami_warning ? '#e74c3c' : '#2ecc71'}">${event.tsunami_warning ? 'YES' : 'NO'}</span></div>
                    <div class="detail-row"><span class="detail-label">Alert Level:</span><span class="detail-val">${event.alert_level}</span></div>
                    <a class="map-btn" href="https://maps.google.com/?q=${event.latitude},${event.longitude}" target="_blank">
                      <ha-icon icon="mdi:map-marker"></ha-icon> Open Location Map
                    </a>
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>

        <!-- MATRIX LIVE TERMINAL NODE -->
        <div class="stream-footer">
          <div class="stream-title-row">
            <span>SEISMIC EVENT STREAM</span>
            <div class="live-status-indicator">
              <span class="live-lens"></span>
              <span class="stream-live-tag">LIVE</span>
            </div>
          </div>
          ${events.slice(0, 2).map(e => `
            <div class="stream-line">[SUCCESS] Telemetry parsed: ${e.magnitude}M at depth ${e.depth_km}km near ${e.location.split('of ').pop() || e.location}</div>
          `).join('')}
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll('.event-main').forEach(element => {
      element.addEventListener('click', () => {
        const parent = element.parentElement;
        const id = parent.getAttribute('data-id');
        
        if (this.expandedEvents.has(id)) {
          this.expandedEvents.delete(id);
          parent.classList.remove('expanded');
        } else {
          this.expandedEvents.add(id);
          parent.classList.add('expanded');
        }
      });
    });
  }
}

customElements.define('earthquake-history-card', EarthquakeHistoryCard);