class InventoryManagerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
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
        .container {
          max-width: 800px;
          margin: 0 auto;
        }
        h1 {
          color: var(--primary-text-color, #212121);
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          gap: 12px;
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
        .btn-primary {
          background: var(--primary-color, #03a9f4);
          color: white;
        }
        .btn-secondary {
          background: var(--accent-color, #ff9800);
          color: white;
        }
        .products-table {
          background: var(--card-background-color, white);
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th {
          background: var(--primary-color, #03a9f4);
          color: white;
          padding: 12px;
          text-align: left;
        }
        td {
          padding: 12px;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        tr:hover {
          background: var(--secondary-background-color, #f5f5f5);
        }
        .status-ok { color: #4caf50; }
        .status-warning { color: #ff9800; }
        .status-danger { color: #f44336; }
        .btn-delete {
          background: #f44336;
          color: white;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 0.85em;
        }
        .empty-state {
          text-align: center;
          padding: 48px;
          color: var(--secondary-text-color, #757575);
        }
        .modal {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        .modal.open {
          display: flex;
        }
        .modal-content {
          background: var(--card-background-color, white);
          border-radius: 16px;
          padding: 24px;
          width: 90%;
          max-width: 400px;
        }
        .modal h2 {
          margin-top: 0;
        }
        .form-group {
          margin-bottom: 16px;
        }
        .form-group label {
          display: block;
          margin-bottom: 6px;
          font-weight: 500;
        }
        .form-group input {
          width: 100%;
          padding: 12px;
          border: 1px solid var(--divider-color, #e0e0e0);
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
        .btn-cancel {
          background: var(--secondary-background-color, #e0e0e0);
          color: var(--primary-text-color, #212121);
        }
      </style>
      
      <div class="container">
        <h1>🧊 Gestionnaire d'Inventaire</h1>
        
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
          <button class="btn-primary" id="btn-add">
            ➕ Ajouter manuellement
          </button>
          <button class="btn-secondary" id="btn-scan">
            📷 Scanner code-barres
          </button>
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
            <tbody id="products-list">
              <tr>
                <td colspan="5" class="empty-state">Chargement...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- Modal Ajouter -->
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
      
      <!-- Modal Scanner -->
      <div class="modal" id="scan-modal">
        <div class="modal-content">
          <h2>📷 Scanner un produit</h2>
          <div class="form-group">
            <label>Code-barres</label>
            <input type="text" id="scan-barcode" placeholder="Entrez ou scannez le code">
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

    // Event listeners
    this.shadowRoot.getElementById('btn-add').addEventListener('click', () => this._openAddModal());
    this.shadowRoot.getElementById('btn-scan').addEventListener('click', () => this._openScanModal());
    this.shadowRoot.getElementById('btn-cancel').addEventListener('click', () => this._closeModals());
    this.shadowRoot.getElementById('btn-scan-cancel').addEventListener('click', () => this._closeModals());
    this.shadowRoot.getElementById('btn-save').addEventListener('click', () => this._addProduct());
    this.shadowRoot.getElementById('btn-scan-save').addEventListener('click', () => this._scanProduct());
    
    // Set default date to 30 days from now
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 30);
    const dateStr = defaultDate.toISOString().split('T')[0];
    this.shadowRoot.getElementById('product-date').value = dateStr;
    this.shadowRoot.getElementById('scan-date').value = dateStr;
  }

  _updateData() {
    const freezerSensor = this._hass.states['sensor.gestionnaire_d_inventaire_congelateur'];
    const expiringSensor = this._hass.states['sensor.gestionnaire_d_inventaire_produits_perimant_bientot'];
    const expiredSensor = this._hass.states['sensor.gestionnaire_d_inventaire_produits_perimes'];

    // Update stats
    this.shadowRoot.getElementById('total-count').textContent = freezerSensor?.state || '0';
    this.shadowRoot.getElementById('expiring-count').textContent = expiringSensor?.state || '0';
    this.shadowRoot.getElementById('expired-count').textContent = expiredSensor?.state || '0';

    // Update products list
    const products = freezerSensor?.attributes?.products || [];
    const tbody = this.shadowRoot.getElementById('products-list');
    
    if (products.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">🎉 Aucun produit dans le congélateur</td></tr>';
    } else {
      tbody.innerHTML = products.map(p => {
        const days = p.days_until_expiry;
        let statusClass = 'status-ok';
        let statusIcon = '🟢';
        if (days < 0) { statusClass = 'status-danger'; statusIcon = '🔴'; }
        else if (days <= 3) { statusClass = 'status-danger'; statusIcon = '🟠'; }
        else if (days <= 7) { statusClass = 'status-warning'; statusIcon = '🟡'; }
        
        return `
          <tr data-product-id="${p.id}">
            <td>${p.name}</td>
            <td>${p.expiry_date}</td>
            <td class="${statusClass}">${statusIcon} ${days}j</td>
            <td>${p.quantity}</td>
            <td><button class="btn-delete" data-id="${p.id}" type="button">🗑️ Suppr.</button></td>
          </tr>
        `;
      }).join('');
      
      // Add delete handlers - use currentTarget to always get the button
      tbody.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const productId = e.currentTarget.getAttribute('data-id');
          if (productId) {
            this._deleteProduct(productId);
          }
        });
      });
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

  async _refreshData() {
    // Attendre un peu que HA mette à jour les entités
    await new Promise(resolve => setTimeout(resolve, 500));
    this._updateData();
  }

  async _addProduct() {
    const name = this.shadowRoot.getElementById('product-name').value;
    const date = this.shadowRoot.getElementById('product-date').value;
    const qty = this.shadowRoot.getElementById('product-qty').value;

    if (!name || !date) {
      alert('Veuillez remplir tous les champs');
      return;
    }

    try {
      await this._hass.callService('inventory_manager', 'add_product', {
        name: name,
        expiry_date: date,
        location: 'freezer',
        quantity: parseInt(qty)
      });

      this._closeModals();
      this.shadowRoot.getElementById('product-name').value = '';
      await this._refreshData();
    } catch (e) {
      console.error('Erreur ajout produit:', e);
      alert('Erreur lors de l\'ajout');
    }
  }

  async _scanProduct() {
    const barcode = this.shadowRoot.getElementById('scan-barcode').value;
    const date = this.shadowRoot.getElementById('scan-date').value;
    const qty = this.shadowRoot.getElementById('scan-qty').value;

    if (!barcode || !date) {
      alert('Veuillez remplir tous les champs');
      return;
    }

    try {
      await this._hass.callService('inventory_manager', 'scan_product', {
        barcode: barcode,
        expiry_date: date,
        location: 'freezer',
        quantity: parseInt(qty)
      });

      this._closeModals();
      this.shadowRoot.getElementById('scan-barcode').value = '';
      await this._refreshData();
    } catch (e) {
      console.error('Erreur scan produit:', e);
      alert('Erreur lors du scan');
    }
  }

  async _deleteProduct(productId) {
    if (confirm('Supprimer ce produit ?')) {
      try {
        await this._hass.callService('inventory_manager', 'remove_product', {
          product_id: productId
        });
        await this._refreshData();
      } catch (e) {
        console.error('Erreur suppression:', e);
        alert('Erreur lors de la suppression');
      }
    }
  }
}

customElements.define('inventory-manager-panel', InventoryManagerPanel);
