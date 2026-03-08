// Sub-components are lazy-loaded on first navigation
const _moduleMap = {
  home: './home.js',
  freezer: './freezer.js',
  fridge: './fridge.js',
  pantry: './pantry.js',
};

const _loaded = {};

class InventoryManagerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._currentView = 'home';
    this._initialized = false;
    this._currentComponent = null;
  }

  set hass(hass) {
    this._hass = hass;
    
    // Initialize once
    if (!this._initialized) {
      this._render();
      this._initialized = true;
    }
    
    // Update current component with new hass
    if (this._currentComponent) {
      this._currentComponent.hass = hass;
    }
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

  async _updateView() {
    const container = this.shadowRoot.getElementById('view-container');
    if (!container) return;

    // Clear current view
    container.innerHTML = '';
    this._currentComponent = null;

    // Lazy-load the module if not yet loaded
    const mod = _moduleMap[this._currentView];
    if (mod && !_loaded[this._currentView]) {
      await import(mod);
      _loaded[this._currentView] = true;
    }

    // Create and append appropriate component
    const tagMap = {
      home: 'inventory-manager-home',
      freezer: 'inventory-manager-freezer',
      fridge: 'inventory-manager-fridge',
      pantry: 'inventory-manager-pantry',
    };

    const tag = tagMap[this._currentView];
    if (tag) {
      const component = document.createElement(tag);
      if (this._hass) {
        component.hass = this._hass;
      }
      container.appendChild(component);
      this._currentComponent = component;
    }
  }

  set panel(panel) {
    this._panel = panel;
  }
}

customElements.define('inventory-manager-panel', InventoryManagerPanel);
