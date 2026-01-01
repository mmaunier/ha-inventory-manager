class InventoryManagerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._initialized = false;
    this._pendingDelete = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      this._initialized = true;
    }
    this._updateData();
  }

  _initialize() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
          font-family: var(--primary-font-family, Roboto, sans-serif);
          background: var(--primary-background-color, #fafafa);
          min-height: 100vh;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 {
          color: var(--primary-text-color, #212121);
          margin-bottom: 24px;
        }
        .stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }
        .stat-card {
          background: var(--card-background-color, white);
          border-radius: 12px;
          padding: 16px;
          text-align: center;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .stat-value {
          font-size: 2em;
          font-weight: bold;
          color: var(--primary-color, #03a9f4);
        }
        .stat-label {
          color: var(--secondary-text-color, #757575);
          font-size: 0.9em;
        }
        .actions {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          margin-bottom: 24px;
        }
        button {
          padding: 16px 24px;
          border: none;
          border-radius: 12px;
          cursor: pointer;
          font-size: 1em;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        button:active {
          transform: translateY(0);
        }
        .btn-primary { background: #03a9f4; color: white; }
        .btn-secondary { background: #ff9800; color: white; }
        .products-table {
          background: var(--card-background-color, white);
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        table { width: 100%; border-collapse: collapse; }
        th {
          background: #03a9f4;
          color: white;
          padding: 12px;
          text-align: left;
        }
        td {
          padding: 12px;
          border-bottom: 1px solid #e0e0e0;
        }
        tr:hover { background: #f5f5f5; }
        .status-ok { color: #4caf50; }
        .status-warning { color: #ff9800; }
        .status-danger { color: #f44336; }
        .btn-delete {
          background: #f44336;
          color: white;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 0.9em;
          cursor: pointer;
          border: none;
        }
        .btn-delete:hover {
          background: #d32f2f;
        }
        .empty-state {
          text-align: center;
          padding: 48px;
          color: #757575;
        }
        .modal {
          display: none;
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0,0,0,0.5);
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        .modal.open { display: flex; }
        .modal-content {
          background: white;
          border-radius: 16px;
          padding: 24px;
          width: 90%;
          max-width: 400px;
        }
        .modal h2 { margin-top: 0; }
        .form-group { margin-bottom: 16px; }
        .form-group label {
          display: block;
          margin-bottom: 6px;
          font-weight: 500;
        }
        .form-group input {
          width: 100%;
          padding: 12px;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          font-size: 1em;
          box-sizing: border-box;
        }
        .modal-actions {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
          margin-top: 24px;
        }
        .btn-cancel { background: #e0e0e0; color: #212121; }
        .loading { opacity: 0.5; pointer-events: none; }
      </style>
      
      <div class="container">
        <h1>🧊 Gestionnaire d'Inventaire - Congélateur</h1>
        
        <div class="stats">
          <div class="stat-card">
            <div class="stat-value" id="total-count">0</div>
            <div class="stat-label">Produits</div>
          </div>
          <div class="stat-card">
            <div class="stat-value status-warning" id="expiring-count">0</div>
            <div class="stat-label">Bientôt périmés</div>
          </div>
          <div class="stat-card">
            <div class="stat-value status-danger" id="expired-count">0</div>
            <div class="stat-label">Périmés</div>
          </div>
        </div>
        
        <div class="actions">
          <button class="btn-primary" id="btn-add">➕ Ajouter manuellement</button>
          <button class="btn-secondary" id="btn-scan">📷 Scanner code-barres</button>
        </div>
        
        <div class="products-table">
          <table>
            <thead>
              <tr>
                <th>Produit</th>
                <th>Péremption</th>
                <th>Statut</th>
                <th>Qté</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="products-list"></tbody>
          </table>
        </div>
      </div>
      
      <div class="modal" id="add-modal">
        <div class="modal-content">
          <h2>➕ Ajouter un produit</h2>
          <div class="form-group">
            <label>Nom du produit</label>
            <input type="text" id="product-name" placeholder="Ex: Pizza 4 fromages">
          </div>
          <div class="form-group">
            <label>Date de péremption</label>
            <input type="date" id="product-date">
          </div>
          <div class="form-group">
            <label>Quantité</label>
            <input type="number" id="product-qty" value="1" min="1" max="99">
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" id="btn-cancel">Annuler</button>
            <button class="btn-primary" id="btn-save">Ajouter</button>
          </div>
        </div>
      </div>
      
      <div class="modal" id="scan-modal">
        <div class="modal-content">
          <h2>📷 Scanner un produit</h2>
          <div class="form-group">
            <label>Code-barres</label>
            <input type="text" id="scan-barcode" placeholder="Entrez le code-barres">
          </div>
          <div class="form-group">
            <label>Date de péremption</label>
            <input type="date" id="scan-date">
          </div>
          <div class="form-group">
            <label>Quantité</label>
            <input type="number" id="scan-qty" value="1" min="1" max="99">
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" id="btn-scan-cancel">Annuler</button>
            <button class="btn-secondary" id="btn-scan-save">Ajouter</button>
          </div>
        </div>
      </div>
    `;

    // Static event listeners (only once)
    this.shadowRoot.getElementById('btn-add').onclick = () => this._openAddModal();
    this.shadowRoot.getElementById('btn-scan').onclick = () => this._openScanModal();
    this.shadowRoot.getElementById('btn-cancel').onclick = () => this._closeModals();
    this.shadowRoot.getElementById('btn-scan-cancel').onclick = () => this._closeModals();
    this.shadowRoot.getElementById('btn-save').onclick = () => this._addProduct();
    this.shadowRoot.getElementById('btn-scan-save').onclick = () => this._scanProduct();
    
    // Event delegation for delete buttons - ONE listener on tbody
    this.shadowRoot.getElementById('products-list').onclick = (e) => {
      const btn = e.target.closest('.btn-delete');
      if (btn) {
        const productId = btn.dataset.id;
        if (productId) {
          this._deleteProduct(productId);
        }
      }
    };
    
    // Set default dates
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 30);
    const dateStr = defaultDate.toISOString().split('T')[0];
    this.shadowRoot.getElementById('product-date').value = dateStr;
    this.shadowRoot.getElementById('scan-date').value = dateStr;
  }

  _updateData() {
    if (!this._hass) return;
    
    const freezerSensor = this._hass.states['sensor.gestionnaire_d_inventaire_congelateur'];
    const expiringSensor = this._hass.states['sensor.gestionnaire_d_inventaire_produits_perimant_bientot'];
    const expiredSensor = this._hass.states['sensor.gestionnaire_d_inventaire_produits_perimes'];

    // Update stats
    const totalEl = this.shadowRoot.getElementById('total-count');
    const expiringEl = this.shadowRoot.getElementById('expiring-count');
    const expiredEl = this.shadowRoot.getElementById('expired-count');
    
    if (totalEl) totalEl.textContent = freezerSensor?.state || '0';
    if (expiringEl) expiringEl.textContent = expiringSensor?.state || '0';
    if (expiredEl) expiredEl.textContent = expiredSensor?.state || '0';

    // Update products list
    const products = freezerSensor?.attributes?.products || [];
    const tbody = this.shadowRoot.getElementById('products-list');
    if (!tbody) return;
    
    if (products.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">🎉 Aucun produit</td></tr>';
    } else {
      tbody.innerHTML = products.map(p => {
        const days = p.days_until_expiry;
        let statusClass = 'status-ok';
        let statusIcon = '🟢';
        if (days < 0) { statusClass = 'status-danger'; statusIcon = '🔴'; }
        else if (days <= 3) { statusClass = 'status-danger'; statusIcon = '🟠'; }
        else if (days <= 7) { statusClass = 'status-warning'; statusIcon = '🟡'; }
        
        return `<tr>
          <td>${p.name || 'Sans nom'}</td>
          <td>${p.expiry_date || '-'}</td>
          <td class="${statusClass}">${statusIcon} ${days}j</td>
          <td>${p.quantity || 1}</td>
          <td><button type="button" class="btn-delete" data-id="${p.id}">Supprimer</button></td>
        </tr>`;
      }).join('');
    }
  }

  _openAddModal() {
    this.shadowRoot.getElementById('add-modal').classList.add('open');
    this.shadowRoot.getElementById('product-name').focus();
  }

  _openScanModal() {
    this.shadowRoot.getElementById('scan-modal').classList.add('open');
    this.shadowRoot.getElementById('scan-barcode').focus();
  }

  _closeModals() {
    this.shadowRoot.getElementById('add-modal').classList.remove('open');
    this.shadowRoot.getElementById('scan-modal').classList.remove('open');
  }

  async _addProduct() {
    const nameEl = this.shadowRoot.getElementById('product-name');
    const dateEl = this.shadowRoot.getElementById('product-date');
    const qtyEl = this.shadowRoot.getElementById('product-qty');
    
    const name = nameEl.value.trim();
    const date = dateEl.value;
    const qty = parseInt(qtyEl.value) || 1;

    if (!name || !date) {
      alert('Veuillez remplir le nom et la date');
      return;
    }

    try {
      await this._hass.callService('inventory_manager', 'add_product', {
        name: name,
        expiry_date: date,
        location: 'freezer',
        quantity: qty
      });
      
      nameEl.value = '';
      this._closeModals();
      
      // Force refresh after delay
      setTimeout(() => this._updateData(), 1000);
    } catch (err) {
      console.error('Erreur ajout:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _scanProduct() {
    const barcodeEl = this.shadowRoot.getElementById('scan-barcode');
    const dateEl = this.shadowRoot.getElementById('scan-date');
    const qtyEl = this.shadowRoot.getElementById('scan-qty');
    
    const barcode = barcodeEl.value.trim();
    const date = dateEl.value;
    const qty = parseInt(qtyEl.value) || 1;

    if (!barcode || !date) {
      alert('Veuillez remplir le code-barres et la date');
      return;
    }

    try {
      await this._hass.callService('inventory_manager', 'scan_product', {
        barcode: barcode,
        expiry_date: date,
        location: 'freezer',
        quantity: qty
      });
      
      barcodeEl.value = '';
      this._closeModals();
      
      setTimeout(() => this._updateData(), 1000);
    } catch (err) {
      console.error('Erreur scan:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _deleteProduct(productId) {
    if (!productId) {
      console.error('No product ID');
      return;
    }
    
    if (!confirm('Supprimer ce produit ?')) {
      return;
    }

    try {
      await this._hass.callService('inventory_manager', 'remove_product', {
        product_id: productId
      });
      
      // Force refresh after delay
      setTimeout(() => this._updateData(), 1000);
    } catch (err) {
      console.error('Erreur suppression:', err);
      alert('Erreur: ' + err.message);
    }
  }
}

customElements.define('inventory-manager-panel', InventoryManagerPanel);
