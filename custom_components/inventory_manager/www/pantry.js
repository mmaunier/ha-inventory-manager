class InventoryManagerPantry extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._initialized = false;
    this._localProducts = []; // État local des produits
    this._deletedIds = new Set(); // IDs supprimés à ignorer lors des syncs
    this._sortBy = 'date'; // 'date', 'name', 'category', 'zone'
    this._sortAsc = true; // true = ascendant
    this._categories = [
      "Conserves", "Pâtes/Riz/Céréales", "Farines/Sucres", "Huiles/Vinaigres",
      "Épices/Aromates", "Biscuits/Gâteaux secs", "Boissons", "Condiments/Sauces",
      "Produits d'épicerie", "Produits ménagers", "Hygiène & Cosmétiques",
      "Papeterie & Fournitures", "Médicaments & Santé", "Autre"
    ];
    this._zones = ["Zone 1", "Zone 2", "Zone 3"];
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      this._initialized = true;
    }
    this._syncFromHass();
  }

  // Synchronise depuis HA - simple et direct
  _syncFromHass() {
    if (!this._hass) return;
    
    const pantrySensor = this._hass.states['sensor.gestionnaire_d_inventaire_reserves'];
    const serverProducts = pantrySensor?.attributes?.products || [];
    
    // Synchroniser catégories et zones depuis le sensor
    if (pantrySensor?.attributes?.categories) {
      this._categories = pantrySensor.attributes.categories;
    }
    if (pantrySensor?.attributes?.zones) {
      this._zones = pantrySensor.attributes.zones;
    }
    
    // Filtrer les produits serveur : exclure ceux qu'on a supprimé localement (en attente de confirmation)
    this._localProducts = serverProducts.filter(p => !this._deletedIds.has(p.id));
    
    // Nettoyer les IDs supprimés qui ne sont plus sur le serveur (évite accumulation)
    const serverIds = new Set(serverProducts.map(p => p.id));
    this._deletedIds = new Set([...this._deletedIds].filter(id => serverIds.has(id)));
    
    // Mettre à jour les stats
    const expiringSensor = this._hass.states['sensor.gestionnaire_d_inventaire_produits_perimant_bientot'];
    const expiredSensor = this._hass.states['sensor.gestionnaire_d_inventaire_expired_pantry'];
    
    const totalEl = this.shadowRoot.getElementById('total-count');
    const expiringEl = this.shadowRoot.getElementById('expiring-count');
    const expiredEl = this.shadowRoot.getElementById('expired-count');
    
    if (totalEl) totalEl.textContent = this._localProducts.length;
    if (expiringEl) expiringEl.textContent = expiringSensor?.state || '0';
    if (expiredEl) expiredEl.textContent = expiredSensor?.state || '0';
    
    // Mettre à jour le tableau
    this._renderProducts();
  }

  // Rendu du tableau depuis l'état local
  // Formater une date YYYY-MM-DD en JJ/MM/AAAA
  _formatDateFR(dateStr) {
    if (!dateStr) return '-';
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateStr;
  }

  _toggleSort(column) {
    if (this._sortBy === column) {
      this._sortAsc = !this._sortAsc;
    } else {
      this._sortBy = column;
      this._sortAsc = true;
    }
    this._updateSortIcons();
    this._renderProducts();
  }

  _updateSortIcons() {
    const nameHeader = this.shadowRoot.getElementById('sort-name');
    const categoryHeader = this.shadowRoot.getElementById('sort-category');
    const zoneHeader = this.shadowRoot.getElementById('sort-zone');
    const dateHeader = this.shadowRoot.getElementById('sort-date');
    if (!nameHeader || !categoryHeader || !zoneHeader || !dateHeader) return;
    
    const nameIcon = nameHeader.querySelector('.sort-icon');
    const categoryIcon = categoryHeader.querySelector('.sort-icon');
    const zoneIcon = zoneHeader.querySelector('.sort-icon');
    const dateIcon = dateHeader.querySelector('.sort-icon');
    
    nameIcon.textContent = this._sortBy === 'name' ? (this._sortAsc ? '▲' : '▼') : '';
    categoryIcon.textContent = this._sortBy === 'category' ? (this._sortAsc ? '▲' : '▼') : '';
    zoneIcon.textContent = this._sortBy === 'zone' ? (this._sortAsc ? '▲' : '▼') : '';
    dateIcon.textContent = this._sortBy === 'date' ? (this._sortAsc ? '▲' : '▼') : '';
  }

  _getSortedProducts() {
    return [...this._localProducts].sort((a, b) => {
      let comparison = 0;
      if (this._sortBy === 'name') {
        const nameA = (a.name || '').toLowerCase();
        const nameB = (b.name || '').toLowerCase();
        comparison = nameA.localeCompare(nameB, 'fr');
      } else if (this._sortBy === 'category') {
        const catA = (a.category || 'Autre').toLowerCase();
        const catB = (b.category || 'Autre').toLowerCase();
        comparison = catA.localeCompare(catB, 'fr');
      } else if (this._sortBy === 'zone') {
        const zoneA = (a.zone || 'Zone 1').toLowerCase();
        const zoneB = (b.zone || 'Zone 1').toLowerCase();
        comparison = zoneA.localeCompare(zoneB, 'fr');
      } else {
        // Tri par date (days_until_expiry)
        const daysA = a.days_until_expiry ?? 999;
        const daysB = b.days_until_expiry ?? 999;
        comparison = daysA - daysB;
      }
      return this._sortAsc ? comparison : -comparison;
    });
  }

  _renderProducts() {
    const tbody = this.shadowRoot.getElementById('products-list');
    if (!tbody) return;
    
    if (this._localProducts.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-state">🎉 Aucun produit dans la réserve</td></tr>';
    } else {
      const sortedProducts = this._getSortedProducts();
      tbody.innerHTML = sortedProducts.map(p => {
        const days = p.days_until_expiry;
        const isTemp = p.id.toString().startsWith('temp_');
        let statusClass = 'status-ok';
        let statusIcon = '🟢';
        
        if (days < 0) { statusClass = 'status-danger'; statusIcon = '🔴'; }
        else if (days <= 3) { statusClass = 'status-danger'; statusIcon = '🟠'; }
        else if (days <= 7) { statusClass = 'status-warning'; statusIcon = '🟡'; }
        
        // Produits temporaires ont un style légèrement différent
        const rowClass = isTemp ? 'temp-row' : '';
        
        return `<tr class="${rowClass}" data-product-id="${p.id}">
          <td class="col-name">${p.name || 'Sans nom'}</td>
          <td class="col-category">${p.category || 'Autre'}</td>
          <td class="col-zone">${p.zone || 'Zone 1'}</td>
          <td class="col-date">${this._formatDateFR(p.expiry_date)} <span class="${statusClass}">${statusIcon}${days !== undefined ? days + 'j' : ''}</span></td>
          <td class="col-qty">${p.quantity || 1}</td>
          <td class="col-action">
            <button type="button" class="btn-edit" data-id="${p.id}" title="Modifier">✏️</button>
            <button type="button" class="btn-delete" data-id="${p.id}" title="Supprimer">🗑️</button>
          </td>
        </tr>`;
      }).join('');
    }
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
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .btn-back {
          background: var(--secondary-background-color, #e0e0e0);
          color: var(--primary-text-color, #212121);
          padding: 8px 16px;
          border-radius: 8px;
          border: none;
          cursor: pointer;
          font-size: 1em;
        }
        .btn-back:hover {
          background: #d0d0d0;
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
        .actions #btn-add {
          grid-column: 1 / -1;
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
        button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        button:active:not(:disabled) {
          transform: translateY(0);
        }
        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .btn-primary { background: #03a9f4; color: white; }
        .btn-secondary { background: #ff9800; color: white; }
        .products-table {
          background: var(--card-background-color, white);
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          overflow-x: auto;
        }
        table { width: 100%; border-collapse: collapse; table-layout: fixed; }
        th {
          background: #03a9f4;
          color: white;
          padding: 10px 8px;
          text-align: left;
          font-size: 0.85em;
        }
        td {
          padding: 10px 8px;
          border-bottom: 1px solid #e0e0e0;
          font-size: 0.9em;
          word-wrap: break-word;
        }
        .col-name { width: 25%; }
        .col-category { width: 15%; }
        .col-zone { width: 10%; text-align: center; }
        .col-date { width: 25%; white-space: nowrap; }
        .col-qty { width: 10%; text-align: center; }
        .col-action { width: 15%; text-align: center; }
        tr:hover { background: #f5f5f5; }
        @media (max-width: 500px) {
          th, td { padding: 8px 4px; font-size: 0.8em; }
          .col-name { width: 35%; }
          .col-category { display: none; }
          .col-zone { display: none; }
          .col-date { width: 35%; }
        }
        tr.temp-row {
          background: #e3f2fd;
          border-left: 3px solid #2196f3;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .status-ok { color: #4caf50; }
        .status-warning { color: #ff9800; }
        .status-danger { color: #f44336; }
        .btn-edit, .btn-delete {
          padding: 6px 8px;
          border-radius: 6px;
          font-size: 1em;
          cursor: pointer;
          border: none;
          min-width: 32px;
        }
        .btn-edit {
          background: #2196f3;
          color: white;
          margin-right: 4px;
        }
        .btn-edit:hover { background: #1976d2; }
        .btn-delete {
          background: #f44336;
          color: white;
        }
        .btn-delete:hover:not(:disabled) {
          background: #d32f2f;
        }
        .btn-delete:disabled {
          background: #999;
        }
        .sortable {
          cursor: pointer;
          user-select: none;
        }
        .sortable:hover {
          background: #e0e0e0;
        }
        .sort-icon {
          font-size: 0.8em;
          margin-left: 4px;
        }
        .product-info {
          background: #e8f5e9;
          border: 1px solid #4caf50;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 16px;
          text-align: center;
        }
        .product-info.not-found {
          background: #fff3e0;
          border-color: #ff9800;
        }
        .product-info.loading {
          background: #e3f2fd;
          border-color: #2196f3;
        }
        .product-name-input {
          margin-top: 8px;
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
        .camera-container {
          position: relative;
          width: 100%;
          max-width: 100%;
          margin: 16px 0;
          border-radius: 12px;
          overflow: hidden;
          background: #000;
        }
        .camera-container video {
          width: 100%;
          display: block;
        }
        .camera-overlay {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 200px;
          height: 100px;
          border: 3px solid #03a9f4;
          border-radius: 8px;
          box-shadow: 0 0 0 9999px rgba(0,0,0,0.5);
        }
        .camera-status {
          text-align: center;
          padding: 8px;
          color: #666;
          font-size: 0.9em;
        }
        .btn-camera {
          background: #4caf50;
          color: white;
          width: 100%;
          margin-bottom: 12px;
        }
        .barcode-input-row {
          display: flex;
          gap: 8px;
        }
        .barcode-input-row input {
          flex: 1;
        }
        .btn-small {
          padding: 12px 16px;
          background: #4caf50;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 1.2em;
        }
        .btn-small:hover {
          background: #388e3c;
        }
        .list-manager {
          margin: 20px 0;
        }
        .list-manager ul {
          list-style: none;
          padding: 0;
          margin: 0 0 16px 0;
          max-height: 300px;
          overflow-y: auto;
        }
        .list-manager li {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px;
          background: #f5f5f5;
          border-radius: 8px;
          margin-bottom: 8px;
        }
        .list-manager li:hover {
          background: #eeeeee;
        }
        .list-manager .item-name {
          flex: 1;
          font-weight: 500;
        }
        .list-manager .item-actions {
          display: flex;
          gap: 8px;
        }
        .list-manager .form-group {
          display: flex;
          gap: 8px;
        }
        .list-manager input {
          flex: 1;
        }
      </style>
      
      <div class="container">
        <h1>
          <button class="btn-back" id="btn-back">← Retour</button>
          🥫 Gestionnaire d'Inventaire - Réserve
        </h1>
        
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
          <button class="btn-secondary" id="btn-manage-categories">🗂️ Gérer catégories</button>
          <button class="btn-secondary" id="btn-manage-zones">📍 Gérer zones</button>
          <button class="btn-primary" id="btn-add">➕ Ajouter un produit</button>
        </div>
        
        <div class="products-table">
          <table>
            <thead>
              <tr>
                <th class="col-name sortable" id="sort-name">Produit <span class="sort-icon"></span></th>
                <th class="col-category sortable" id="sort-category">Catégorie <span class="sort-icon"></span></th>
                <th class="col-zone sortable" id="sort-zone">Zone <span class="sort-icon"></span></th>
                <th class="col-date sortable" id="sort-date">Péremption <span class="sort-icon">▲</span></th>
                <th class="col-qty">Qté</th>
                <th class="col-action"></th>
              </tr>
            </thead>
            <tbody id="products-list"></tbody>
          </table>
        </div>
      </div>
      
      <div class="modal" id="add-modal">
        <div class="modal-content">
          <h2>📷 Scanner un produit</h2>
          
          <div class="camera-container" id="camera-container" style="display:none;">
            <video id="camera-video" autoplay playsinline></video>
            <div class="camera-overlay"></div>
          </div>
          <div id="html5-qrcode-scanner" style="display:none;"></div>
          <div class="camera-status" id="camera-status"></div>
          
          <button class="btn-camera" id="btn-start-camera">📸 Scanner avec la caméra</button>
          
          <div class="form-group">
            <label>Code-barres</label>
            <div class="barcode-input-row">
              <input type="text" id="scan-barcode" placeholder="Scannez ou entrez manuellement">
              <button class="btn-small" id="btn-lookup" title="Rechercher">🔍</button>
            </div>
          </div>
          
          <div id="product-info-box" class="product-info" style="display:none;"></div>
          
          <div class="form-group">
            <label>Nom du produit</label>
            <input type="text" id="scan-name" placeholder="Nom du produit (modifiable)">
          </div>
          <div class="form-group">
            <label>Date de péremption</label>
            <input type="date" id="scan-date">
          </div>
          <div class="form-group">
            <label>Quantité</label>
            <input type="number" id="scan-qty" value="1" min="1" max="99">
          </div>
          <div class="form-group">
            <label>Catégorie</label>
            <select id="scan-category">
              ${this._categories.map(c => `<option value="${c}">${c}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label>Zone</label>
            <select id="scan-zone">
              ${this._zones.map(z => `<option value="${z}">${z}</option>`).join('')}
            </select>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" id="btn-scan-cancel">Annuler</button>
            <button class="btn-secondary" id="btn-scan-save">Ajouter</button>
          </div>
        </div>
      </div>
      
      <div class="modal" id="edit-modal">
        <div class="modal-content">
          <h2>✏️ Modifier le produit</h2>
          <input type="hidden" id="edit-id">
          <div class="form-group">
            <label>Nom du produit</label>
            <input type="text" id="edit-name">
          </div>
          <div class="form-group">
            <label>Date de péremption</label>
            <input type="date" id="edit-date">
          </div>
          <div class="form-group">
            <label>Quantité</label>
            <input type="number" id="edit-qty" value="1" min="1" max="99">
          </div>
          <div class="form-group">
            <label>Catégorie</label>
            <select id="edit-category">
              ${this._categories.map(c => `<option value="${c}">${c}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label>Zone</label>
            <select id="edit-zone">
              ${this._zones.map(z => `<option value="${z}">${z}</option>`).join('')}
            </select>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" id="btn-edit-cancel">Annuler</button>
            <button class="btn-primary" id="btn-edit-save">Enregistrer</button>
          </div>
        </div>
      </div>
      
      <div class="modal" id="categories-modal">
        <div class="modal-content">
          <h2>🗂️ Gérer les catégories</h2>
          <div class="list-manager">
            <ul id="categories-list"></ul>
            <div class="form-group">
              <input type="text" id="new-category" placeholder="Nouvelle catégorie...">
              <button class="btn-primary" id="btn-add-category">Ajouter</button>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn-delete" id="btn-reset-categories">🔄 Réinitialiser</button>
            <button class="btn-primary" id="btn-categories-close">Fermer</button>
          </div>
        </div>
      </div>
      
      <div class="modal" id="zones-modal">
        <div class="modal-content">
          <h2>📍 Gérer les zones</h2>
          <div class="list-manager">
            <ul id="zones-list"></ul>
            <div class="form-group">
              <input type="text" id="new-zone" placeholder="Nouvelle zone...">
              <button class="btn-primary" id="btn-add-zone">Ajouter</button>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn-delete" id="btn-reset-zones">🔄 Réinitialiser</button>
            <button class="btn-primary" id="btn-zones-close">Fermer</button>
          </div>
        </div>
      </div>
    `;

    // Event listeners
    this.shadowRoot.getElementById('btn-back').onclick = () => this._navigateHome();
    this.shadowRoot.getElementById('btn-add').onclick = () => this._openAddModal();
    this.shadowRoot.getElementById('btn-manage-categories').onclick = () => this._openCategoriesModal();
    this.shadowRoot.getElementById('btn-manage-zones').onclick = () => this._openZonesModal();
    this.shadowRoot.getElementById('btn-scan-cancel').onclick = () => this._closeAddModal();
    this.shadowRoot.getElementById('btn-edit-cancel').onclick = () => this._closeModals();
    this.shadowRoot.getElementById('btn-scan-save').onclick = () => this._addProduct();
    this.shadowRoot.getElementById('btn-edit-save').onclick = () => this._saveEditProduct();
    this.shadowRoot.getElementById('btn-start-camera').onclick = () => this._startCamera();
    this.shadowRoot.getElementById('btn-lookup').onclick = () => this._lookupBarcode();
    this.shadowRoot.getElementById('btn-categories-close').onclick = () => this._closeCategoriesModal();
    this.shadowRoot.getElementById('btn-zones-close').onclick = () => this._closeZonesModal();
    this.shadowRoot.getElementById('btn-add-category').onclick = () => this._addCategory();
    this.shadowRoot.getElementById('btn-add-zone').onclick = () => this._addZone();
    this.shadowRoot.getElementById('btn-reset-categories').onclick = () => this._resetCategories();
    this.shadowRoot.getElementById('btn-reset-zones').onclick = () => this._resetZones();
    
    // Tri par colonnes
    this.shadowRoot.getElementById('sort-name').onclick = () => this._toggleSort('name');
    this.shadowRoot.getElementById('sort-category').onclick = () => this._toggleSort('category');
    this.shadowRoot.getElementById('sort-zone').onclick = () => this._toggleSort('zone');
    this.shadowRoot.getElementById('sort-date').onclick = () => this._toggleSort('date');
    
    // Auto-lookup when barcode is entered
    this.shadowRoot.getElementById('scan-barcode').addEventListener('change', () => this._lookupBarcode());
    
    // Event delegation for edit and delete buttons
    this.shadowRoot.getElementById('products-list').onclick = (e) => {
      const editBtn = e.target.closest('.btn-edit');
      const deleteBtn = e.target.closest('.btn-delete');
      
      if (editBtn) {
        const productId = editBtn.dataset.id;
        if (productId) this._openEditModal(productId);
      } else if (deleteBtn && !deleteBtn.disabled) {
        const productId = deleteBtn.dataset.id;
        if (productId) this._deleteProduct(productId);
      }
    };
    
    // Set default date
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 30);
    const dateStr = defaultDate.toISOString().split('T')[0];
    this.shadowRoot.getElementById('scan-date').value = dateStr;
    
    // Allow closing modals by clicking on backdrop
    ['add-modal', 'edit-modal', 'categories-modal', 'zones-modal'].forEach(modalId => {
      const modal = this.shadowRoot.getElementById(modalId);
      
      modal.addEventListener('click', (e) => {
        // Only close if clicking directly on the backdrop (not on content or its children)
        if (e.target === modal) {
          if (modalId === 'add-modal') {
            this._closeAddModal();
          } else if (modalId === 'edit-modal') {
            this._closeModals();
          } else if (modalId === 'categories-modal') {
            this._closeCategoriesModal();
          } else if (modalId === 'zones-modal') {
            this._closeZonesModal();
          }
        }
      });
    });
  }

  _openAddModal() {
    this.shadowRoot.getElementById('add-modal').classList.add('open');
    // Reset form
    this.shadowRoot.getElementById('scan-barcode').value = '';
    this.shadowRoot.getElementById('scan-name').value = '';
    this.shadowRoot.getElementById('product-info-box').style.display = 'none';
    // Reset camera state
    this.shadowRoot.getElementById('camera-container').style.display = 'none';
    this.shadowRoot.getElementById('camera-status').textContent = '';
    this.shadowRoot.getElementById('btn-start-camera').style.display = 'flex';
    // Reset date to +30 days
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 30);
    this.shadowRoot.getElementById('scan-date').value = defaultDate.toISOString().split('T')[0];
    this.shadowRoot.getElementById('scan-qty').value = 1;
  }

  _openEditModal(productId) {
    const product = this._localProducts.find(p => p.id === productId);
    if (!product) return;
    
    this.shadowRoot.getElementById('edit-id').value = productId;
    this.shadowRoot.getElementById('edit-name').value = product.name || '';
    this.shadowRoot.getElementById('edit-date').value = product.expiry_date || '';
    this.shadowRoot.getElementById('edit-qty').value = product.quantity || 1;
    this.shadowRoot.getElementById('edit-category').value = product.category || 'Autre';
    this.shadowRoot.getElementById('edit-zone').value = product.zone || 'Zone 1';
    this.shadowRoot.getElementById('edit-modal').classList.add('open');
  }

  _closeModals() {
    this._stopCamera();
    this.shadowRoot.getElementById('add-modal').classList.remove('open');
    this.shadowRoot.getElementById('edit-modal').classList.remove('open');
  }

  _closeAddModal() {
    this._stopCamera();
    this.shadowRoot.getElementById('add-modal').classList.remove('open');
  }

  // Recherche du produit via l'API Open Food Facts
  async _lookupBarcode() {
    const barcodeEl = this.shadowRoot.getElementById('scan-barcode');
    const nameEl = this.shadowRoot.getElementById('scan-name');
    const infoBox = this.shadowRoot.getElementById('product-info-box');
    
    const barcode = barcodeEl.value.trim();
    if (!barcode || barcode.length < 8) {
      infoBox.style.display = 'none';
      return;
    }
    
    infoBox.className = 'product-info loading';
    infoBox.style.display = 'block';
    infoBox.innerHTML = '🔍 Recherche en cours (cascade Open Food Facts → UPCitemdb → OpenGTINDB)...';
    
    try {
      // Utiliser le service Home Assistant pour éviter les erreurs CORS
      const result = await this._hass.callWS({
        type: 'call_service',
        domain: 'inventory_manager',
        service: 'lookup_product',
        service_data: {
          barcode: barcode
        },
        return_response: true
      });
      
      if (result && result.response && result.response.found) {
        const data = result.response;
        const name = data.name || '';
        const brand = data.brand || '';
        const source = data.source || 'Unknown';
        const fullName = brand ? `${brand} - ${name}` : name;
        
        if (fullName) {
          nameEl.value = fullName;
          infoBox.className = 'product-info';
          infoBox.innerHTML = `✅ <strong>${fullName}</strong><br><small>Source: ${source}</small>`;
        } else {
          infoBox.className = 'product-info not-found';
          infoBox.innerHTML = '⚠️ Produit trouvé mais sans nom. Saisissez le nom manuellement.';
          nameEl.focus();
        }
      } else {
        infoBox.className = 'product-info not-found';
        infoBox.innerHTML = '⚠️ Produit non trouvé dans les 3 bases de données. Saisissez le nom manuellement.';
        nameEl.focus();
      }
    } catch (err) {
      console.error('Erreur lookup:', err);
      infoBox.className = 'product-info not-found';
      infoBox.innerHTML = '❌ Erreur de recherche. Saisissez le nom manuellement.';
      nameEl.focus();
    }
  }

  async _saveEditProduct() {
    const productId = this.shadowRoot.getElementById('edit-id').value;
    const name = this.shadowRoot.getElementById('edit-name').value.trim();
    const date = this.shadowRoot.getElementById('edit-date').value;
    const qty = parseInt(this.shadowRoot.getElementById('edit-qty').value) || 1;
    const category = this.shadowRoot.getElementById('edit-category').value;
    const zone = this.shadowRoot.getElementById('edit-zone').value;

    if (!name || !date) {
      alert('Veuillez remplir le nom et la date');
      return;
    }

    // Mettre à jour localement immédiatement
    const productIndex = this._localProducts.findIndex(p => p.id === productId);
    if (productIndex !== -1) {
      this._localProducts[productIndex].name = name;
      this._localProducts[productIndex].expiry_date = date;
      this._localProducts[productIndex].quantity = qty;
      this._localProducts[productIndex].category = category;
      this._localProducts[productIndex].zone = zone;
      this._localProducts[productIndex].days_until_expiry = this._calculateDaysUntilExpiry(date);
      this._renderProducts();
    }

    this._closeModals();

    // Appeler le service en arrière-plan
    try {
      await this._hass.callService('inventory_manager', 'update_product', {
        product_id: productId,
        name: name,
        expiry_date: date,
        quantity: qty,
        category: category,
        zone: zone
      });
    } catch (err) {
      console.error('Erreur modification:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _startCamera() {
    const container = this.shadowRoot.getElementById('camera-container');
    const video = this.shadowRoot.getElementById('camera-video');
    const status = this.shadowRoot.getElementById('camera-status');
    const startBtn = this.shadowRoot.getElementById('btn-start-camera');
    
    try {
      status.textContent = '📷 Accès à la caméra...';
      startBtn.style.display = 'none';
      
      // Demander accès à la caméra (préférer caméra arrière)
      this._stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      
      video.srcObject = this._stream;
      await video.play();
      container.style.display = 'block';
      status.textContent = '🎯 Pointez vers un code-barres...';
      
      // Créer un canvas pour capturer les frames
      this._scanCanvas = document.createElement('canvas');
      this._scanCtx = this._scanCanvas.getContext('2d', { willReadFrequently: true });
      
      // Vérifier si BarcodeDetector est disponible (Chrome/Edge natif)
      this._useNativeDetector = false;
      if ('BarcodeDetector' in window) {
        try {
          this._barcodeDetector = new BarcodeDetector({
            formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'qr_code']
          });
          this._useNativeDetector = true;
          status.textContent = '🎯 Pointez vers un code-barres...';
        } catch (e) {
          console.log('BarcodeDetector non disponible:', e);
        }
      }
      
      // Si pas de détecteur natif, charger QuaggaJS pour les codes-barres 1D
      if (!this._useNativeDetector) {
        status.textContent = '📦 Chargement du scanner...';
        await this._loadQuaggaLibrary();
        
        if (window.Quagga) {
          status.textContent = '🎯 Pointez vers un code-barres...';
        } else {
          status.textContent = '⚠️ Scanner non disponible - saisissez le code manuellement';
          startBtn.style.display = 'flex';
          return;
        }
      }
      
      // Démarrer la détection
      this._scanInterval = setInterval(() => this._detectBarcode(), 300);
      
    } catch (err) {
      console.error('Erreur caméra:', err);
      let errorMsg = err.message;
      if (err.name === 'NotAllowedError') {
        errorMsg = 'Accès caméra refusé. Vérifiez les permissions.';
      } else if (err.name === 'NotFoundError') {
        errorMsg = 'Aucune caméra trouvée.';
      }
      status.textContent = '❌ ' + errorMsg;
      startBtn.style.display = 'flex';
    }
  }

  async _loadQuaggaLibrary() {
    return new Promise((resolve) => {
      if (window.Quagga) {
        resolve();
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@ericblade/quagga2@1.8.4/dist/quagga.min.js';
      script.onload = () => resolve();
      script.onerror = () => resolve(); // Continue sans la lib
      document.head.appendChild(script);
    });
  }

  async _detectBarcode() {
    const video = this.shadowRoot.getElementById('camera-video');
    const status = this.shadowRoot.getElementById('camera-status');
    const barcodeInput = this.shadowRoot.getElementById('scan-barcode');
    
    if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) return;
    if (this._isScanning) return; // Éviter les scans simultanés
    
    this._isScanning = true;
    
    try {
      let code = null;
      
      if (this._useNativeDetector && this._barcodeDetector) {
        // Utiliser BarcodeDetector natif (Chrome/Edge desktop)
        const barcodes = await this._barcodeDetector.detect(video);
        if (barcodes.length > 0) {
          code = barcodes[0].rawValue;
        }
      } else if (window.Quagga) {
        // Fallback: capturer le frame et décoder avec Quagga
        const canvas = this._scanCanvas;
        const ctx = this._scanCtx;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        
        // Convertir en data URL pour Quagga
        const imageData = canvas.toDataURL('image/png');
        
        // Décoder avec Quagga
        const result = await new Promise((resolve) => {
          Quagga.decodeSingle({
            src: imageData,
            numOfWorkers: 0,
            locate: true,
            decoder: {
              readers: ['ean_reader', 'ean_8_reader', 'upc_reader', 'upc_e_reader', 'code_128_reader', 'code_39_reader']
            }
          }, (res) => {
            if (res && res.codeResult) {
              resolve(res.codeResult.code);
            } else {
              resolve(null);
            }
          });
        });
        
        if (result) {
          code = result;
        }
      }
      
      if (code) {
        // Arrêter le scan
        this._stopCamera();
        
        // Remplir le champ
        barcodeInput.value = code;
        status.textContent = '✅ Code détecté : ' + code + ' - Recherche...';
        
        // Vibrer si possible
        if (navigator.vibrate) navigator.vibrate(200);
        
        // Lancer automatiquement la recherche du produit
        await this._lookupBarcode();
      }
    } catch (err) {
      console.error('Erreur détection:', err);
    } finally {
      this._isScanning = false;
    }
  }

  _stopCamera() {
    if (this._scanInterval) {
      clearInterval(this._scanInterval);
      this._scanInterval = null;
    }
    
    if (this._stream) {
      this._stream.getTracks().forEach(track => track.stop());
      this._stream = null;
    }
    
    const container = this.shadowRoot.getElementById('camera-container');
    const startBtn = this.shadowRoot.getElementById('btn-start-camera');
    
    if (container) container.style.display = 'none';
    if (startBtn) startBtn.style.display = 'flex';
  }

  // Calcul des jours jusqu'à expiration
  _calculateDaysUntilExpiry(expiryDate) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const expiry = new Date(expiryDate);
    expiry.setHours(0, 0, 0, 0);
    const diffTime = expiry - today;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  async _addProduct() {
    const barcodeEl = this.shadowRoot.getElementById('scan-barcode');
    const nameEl = this.shadowRoot.getElementById('scan-name');
    const dateEl = this.shadowRoot.getElementById('scan-date');
    const qtyEl = this.shadowRoot.getElementById('scan-qty');
    const categoryEl = this.shadowRoot.getElementById('scan-category');
    const zoneEl = this.shadowRoot.getElementById('scan-zone');
    const btnSave = this.shadowRoot.getElementById('btn-scan-save');
    
    const barcode = barcodeEl.value.trim();
    const name = nameEl.value.trim();
    const date = dateEl.value;
    const qty = parseInt(qtyEl.value) || 1;
    const category = categoryEl.value;
    const zone = zoneEl.value;

    if (!name || !date) {
      alert('Veuillez remplir le nom du produit et la date de péremption');
      return;
    }

    // Désactiver le bouton pendant l'ajout
    btnSave.disabled = true;
    btnSave.textContent = '⏳ Ajout...';

    try {
      // Appeler le service et attendre la confirmation
      await this._hass.callService('inventory_manager', 'add_product', {
        name: name,
        expiry_date: date,
        location: 'pantry',
        quantity: qty,
        category: category,
        zone: zone,
        barcode: barcode || undefined
      });
      
      // Fermer le modal et reset
      barcodeEl.value = '';
      nameEl.value = '';
      this.shadowRoot.getElementById('product-info-box').style.display = 'none';
      this._closeAddModal();
      
      // Le produit apparaîtra via _syncFromHass quand HA mettra à jour le sensor
      
    } catch (err) {
      console.error('Erreur ajout:', err);
      alert('Erreur: ' + err.message);
    } finally {
      btnSave.disabled = false;
      btnSave.textContent = 'Ajouter';
    }
  }

  async _deleteProduct(productId) {
    if (!productId) {
      console.error('Suppression: ID produit manquant');
      return;
    }
    
    console.log('Tentative suppression produit:', productId, 'type:', typeof productId);
    
    if (!confirm('Supprimer ce produit ?')) return;

    // Trouver le produit dans la liste locale
    const product = this._localProducts.find(p => p.id === productId);
    if (!product) {
      console.error('Produit non trouvé localement:', productId);
      return;
    }
    
    console.log('Produit trouvé:', product);

    // Appeler le service AVANT de supprimer visuellement
    try {
      console.log('Appel service remove_product avec ID:', productId);
      await this._hass.callService('inventory_manager', 'remove_product', {
        product_id: String(productId)  // Forcer en string
      });
      console.log('Service remove_product appelé avec succès');
      
      // Supprimer de la liste locale seulement après succès
      this._localProducts = this._localProducts.filter(p => p.id !== productId);
      this._deletedIds.add(productId);
      
      // Mettre à jour le compteur et rendre
      const totalEl = this.shadowRoot.getElementById('total-count');
      totalEl.textContent = this._localProducts.length;
      this._renderProducts();
      
    } catch (err) {
      console.error('Erreur suppression:', err);
      alert('Erreur lors de la suppression: ' + err.message);
    }
  }

  _openCategoriesModal() {
    this._renderCategoriesList();
    this.shadowRoot.getElementById('categories-modal').classList.add('open');
  }

  _closeCategoriesModal() {
    this.shadowRoot.getElementById('categories-modal').classList.remove('open');
    this.shadowRoot.getElementById('new-category').value = '';
  }

  _openZonesModal() {
    this._renderZonesList();
    this.shadowRoot.getElementById('zones-modal').classList.add('open');
  }

  _closeZonesModal() {
    this.shadowRoot.getElementById('zones-modal').classList.remove('open');
    this.shadowRoot.getElementById('new-zone').value = '';
  }

  _renderCategoriesList() {
    const list = this.shadowRoot.getElementById('categories-list');
    list.innerHTML = this._categories.map(cat => `
      <li>
        <span class="item-name">${cat}</span>
        <div class="item-actions">
          <button class="btn-secondary btn-rename-category" data-name="${cat}">✏️</button>
          <button class="btn-delete btn-remove-category" data-name="${cat}">🗑️</button>
        </div>
      </li>
    `).join('');

    // Ajouter event listeners
    list.querySelectorAll('.btn-rename-category').forEach(btn => {
      btn.onclick = () => this._renameCategory(btn.dataset.name);
    });
    list.querySelectorAll('.btn-remove-category').forEach(btn => {
      btn.onclick = () => this._removeCategory(btn.dataset.name);
    });
  }

  _renderZonesList() {
    const list = this.shadowRoot.getElementById('zones-list');
    list.innerHTML = this._zones.map(zone => `
      <li>
        <span class="item-name">${zone}</span>
        <div class="item-actions">
          <button class="btn-secondary btn-rename-zone" data-name="${zone}">✏️</button>
          <button class="btn-delete btn-remove-zone" data-name="${zone}">🗑️</button>
        </div>
      </li>
    `).join('');

    // Ajouter event listeners
    list.querySelectorAll('.btn-rename-zone').forEach(btn => {
      btn.onclick = () => this._renameZone(btn.dataset.name);
    });
    list.querySelectorAll('.btn-remove-zone').forEach(btn => {
      btn.onclick = () => this._removeZone(btn.dataset.name);
    });
  }

  async _addCategory() {
    const input = this.shadowRoot.getElementById('new-category');
    const name = input.value.trim();
    if (!name) return;

    try {
      await this._hass.callService('inventory_manager', 'add_category', { name, location: 'pantry' });
      this._categories.push(name);
      this._renderCategoriesList();
      input.value = '';
    } catch (err) {
      console.error('Erreur ajout catégorie:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _removeCategory(name) {
    if (!confirm(`Supprimer la catégorie "${name}" ?\nLes produits seront déplacés vers "Autre".`)) return;

    try {
      await this._hass.callService('inventory_manager', 'remove_category', { name, location: 'pantry' });
      this._categories = this._categories.filter(c => c !== name);
      this._renderCategoriesList();
      // Recharger les produits pour afficher les modifications
      this._syncFromHass();
    } catch (err) {
      console.error('Erreur suppression catégorie:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _renameCategory(oldName) {
    const newName = prompt(`Renommer la catégorie "${oldName}" :`, oldName);
    if (!newName || newName === oldName) return;

    try {
      await this._hass.callService('inventory_manager', 'rename_category', { old_name: oldName, new_name: newName, location: 'pantry' });
      const idx = this._categories.indexOf(oldName);
      if (idx !== -1) this._categories[idx] = newName;
      this._renderCategoriesList();
      // Recharger les produits pour afficher les modifications
      this._syncFromHass();
    } catch (err) {
      console.error('Erreur renommage catégorie:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _addZone() {
    const input = this.shadowRoot.getElementById('new-zone');
    const name = input.value.trim();
    if (!name) return;

    try {
      await this._hass.callService('inventory_manager', 'add_zone', { name, location: 'pantry' });
      this._zones.push(name);
      this._renderZonesList();
      input.value = '';
    } catch (err) {
      console.error('Erreur ajout zone:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _removeZone(name) {
    if (!confirm(`Supprimer la zone "${name}" ?\nLes produits seront déplacés vers la première zone.`)) return;

    try {
      await this._hass.callService('inventory_manager', 'remove_zone', { name, location: 'pantry' });
      this._zones = this._zones.filter(z => z !== name);
      this._renderZonesList();
      // Recharger les produits pour afficher les modifications
      this._syncFromHass();
    } catch (err) {
      console.error('Erreur suppression zone:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _renameZone(oldName) {
    const newName = prompt(`Renommer la zone "${oldName}" :`, oldName);
    if (!newName || newName === oldName) return;

    try {
      await this._hass.callService('inventory_manager', 'rename_zone', { old_name: oldName, new_name: newName, location: 'pantry' });
      const idx = this._zones.indexOf(oldName);
      if (idx !== -1) this._zones[idx] = newName;
      this._renderZonesList();
      // Recharger les produits pour afficher les modifications
      this._syncFromHass();
    } catch (err) {
      console.error('Erreur renommage zone:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _resetCategories() {
    if (!confirm('Réinitialiser les catégories aux valeurs par défaut ?\nCette action est irréversible.')) return;

    try {
      await this._hass.callService('inventory_manager', 'reset_categories', {
        location: 'pantry',
      });
      // Recharger les catégories par défaut
      this._categories = [
        "Conserves", "Pâtes/Riz/Céréales", "Farines/Sucres", "Huiles/Vinaigres",
        "Épices/Aromates", "Biscuits/Gâteaux secs", "Boissons", "Condiments/Sauces",
        "Produits d'épicerie", "Produits ménagers", "Hygiène & Cosmétiques",
        "Papeterie & Fournitures", "Médicaments & Santé", "Autre"
      ];
      this._renderCategoriesList();
      alert('Catégories réinitialisées !');
    } catch (err) {
      console.error('Erreur réinitialisation catégories:', err);
      alert('Erreur: ' + err.message);
    }
  }

  async _resetZones() {
    if (!confirm('Réinitialiser les zones aux valeurs par défaut ?\nCette action est irréversible.')) return;

    try {
      await this._hass.callService('inventory_manager', 'reset_zones', {
        location: 'pantry',
      });
      // Recharger les zones par défaut
      this._zones = ["Zone 1", "Zone 2", "Zone 3"];
      this._renderZonesList();
      alert('Zones réinitialisées !');
    } catch (err) {
      console.error('Erreur réinitialisation zones:', err);
      alert('Erreur: ' + err.message);
    }
  }

  _navigateHome() {
    this.dispatchEvent(new CustomEvent('navigate', {
      detail: { view: 'home' },
      bubbles: true,
      composed: true
    }));
  }
}

customElements.define('inventory-manager-pantry', InventoryManagerPantry);
