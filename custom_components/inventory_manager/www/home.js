class InventoryManagerHome extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
          font-family: var(--primary-font-family, Roboto, sans-serif);
          background: var(--primary-background-color, #fafafa);
          min-height: 100vh;
        }
        .container {
          max-width: 900px;
          margin: 0 auto;
          padding-top: 40px;
        }
        h1 {
          color: var(--primary-text-color, #212121);
          text-align: center;
          font-size: 2.5em;
          margin-bottom: 20px;
        }
        .subtitle {
          text-align: center;
          color: var(--secondary-text-color, #757575);
          font-size: 1.2em;
          margin-bottom: 60px;
        }
        .locations {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 24px;
          margin-bottom: 40px;
        }
        .location-card {
          background: var(--card-background-color, white);
          border-radius: 16px;
          padding: 40px 24px;
          text-align: center;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          cursor: pointer;
          transition: all 0.3s ease;
          border: 2px solid transparent;
        }
        .location-card:hover:not(.disabled) {
          transform: translateY(-4px);
          box-shadow: 0 8px 20px rgba(0,0,0,0.15);
          border-color: var(--primary-color, #03a9f4);
        }
        .location-card.disabled {
          opacity: 0.4;
          cursor: not-allowed;
          background: #f5f5f5;
        }
        .location-icon {
          font-size: 4em;
          margin-bottom: 16px;
        }
        .location-name {
          font-size: 1.5em;
          font-weight: 600;
          color: var(--primary-text-color, #212121);
          margin-bottom: 8px;
        }
        .location-status {
          font-size: 0.9em;
          color: var(--secondary-text-color, #757575);
        }
        .location-status.active {
          color: #4caf50;
          font-weight: 500;
        }
        .location-status.coming-soon {
          color: #ff9800;
          font-weight: 500;
        }
        .footer {
          text-align: center;
          color: var(--secondary-text-color, #757575);
          font-size: 0.9em;
          margin-top: 60px;
        }
      </style>
      
      <div class="container">
        <h1>🏠 Gestionnaire d'Inventaire</h1>
        <p class="subtitle">Gérez vos aliments et suivez leur péremption</p>
        
        <div class="locations">
          <div class="location-card" id="freezer-card">
            <div class="location-icon">🧊</div>
            <div class="location-name">Congélateur</div>
            <div class="location-status active">✓ Actif</div>
          </div>
          
          <div class="location-card" id="fridge-card">
            <div class="location-icon">🧃</div>
            <div class="location-name">Réfrigérateur</div>
            <div class="location-status active">✓ Actif</div>
          </div>
          
          <div class="location-card" id="pantry-card">
            <div class="location-icon">🥫</div>
            <div class="location-name">Réserve</div>
            <div class="location-status active">✓ Actif</div>
          </div>
        </div>
        
        <div class="footer">
          <p>Version 1.8.5 • Inventory Manager</p>
        </div>
      </div>
    `;

    // Event listeners
    const freezerCard = this.shadowRoot.getElementById('freezer-card');
    const fridgeCard = this.shadowRoot.getElementById('fridge-card');
    const pantryCard = this.shadowRoot.getElementById('pantry-card');
    
    freezerCard.onclick = () => this._navigate('freezer');
    fridgeCard.onclick = () => this._navigate('fridge');
    pantryCard.onclick = () => this._navigate('pantry');
  }

  _navigate(view) {
    // Dispatch event to navigate to specified view
    this.dispatchEvent(new CustomEvent('navigate', {
      detail: { view },
      bubbles: true,
      composed: true
    }));
  }
}

customElements.define('inventory-manager-home', InventoryManagerHome);
