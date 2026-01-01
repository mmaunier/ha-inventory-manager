// Import components
import './home.js';
import './freezer.js';

class InventoryManagerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._currentView = 'home';
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
          width: 100%;
          height: 100%;
        }
      </style>
      <div id="view-container"></div>
    `;

    this._updateView();
    
    // Listen for navigation events
    this.shadowRoot.addEventListener('navigate', (e) => {
      this._currentView = e.detail.view;
      this._updateView();
    });
  }

  _updateView() {
    const container = this.shadowRoot.getElementById('view-container');
    if (!container) return;

    // Clear current view
    container.innerHTML = '';

    // Create and append appropriate component
    let component;
    if (this._currentView === 'home') {
      component = document.createElement('inventory-manager-home');
    } else if (this._currentView === 'freezer') {
      component = document.createElement('inventory-manager-freezer');
    }

    if (component && this._hass) {
      component.hass = this._hass;
      container.appendChild(component);
    }
  }

  set panel(panel) {
    this._panel = panel;
  }
}

customElements.define('inventory-manager-panel', InventoryManagerPanel);
