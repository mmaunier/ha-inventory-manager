class InventoryManagerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._initialized = false;
    this._localProducts = []; // État local des produits
    this._deletedIds = new Set(); // IDs supprimés à ignorer lors des syncs
    this._tempProducts = []; // Produits temporaires (ajouts en attente de confirmation)
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      this._initialized = true;
    }
    this._syncFromHass();
  }

  // Synchronise depuis HA avec fusion intelligente
  _syncFromHass() {
    if (!this._hass) return;
    
    const freezerSensor = this._hass.states['sensor.gestionnaire_d_inventaire_congelateur'];
    const serverProducts = freezerSensor?.attributes?.products || [];
    
    // Filtrer les produits serveur : exclure ceux qu'on a supprimé localement
    const filteredServerProducts = serverProducts.filter(p => !this._deletedIds.has(p.id));
    
    // Chercher les produits temp qui ont maintenant un vrai ID sur le serveur
    // (on les matche par nom + date OU par barcode + date)
    const matchedTempIds = new Set();
    for (const serverProd of filteredServerProducts) {
      const matchingTemp = this._tempProducts.find(temp => {
        if (matchedTempIds.has(temp.id)) return false;
        // Match par barcode (pour les scans)
        if (temp.barcode && serverProd.barcode && temp.barcode === serverProd.barcode && temp.expiry_date === serverProd.expiry_date) {
          return true;
        }
        // Match par nom exact (pour les ajouts manuels)
        if (temp.name === serverProd.name && temp.expiry_date === serverProd.expiry_date) {
          return true;
        }
        return false;
      });
      if (matchingTemp) {
        matchedTempIds.add(matchingTemp.id);
      }
    }
    
    // Retirer les produits temp qui ont été confirmés par le serveur
    this._tempProducts = this._tempProducts.filter(t => !matchedTempIds.has(t.id));
    
    // Fusionner : produits temp restants + produits serveur filtrés
    this._localProducts = [...this._tempProducts, ...filteredServerProducts];
    
    // Nettoyer les IDs supprimés qui ne sont plus sur le serveur (évite accumulation)
    const serverIds = new Set(serverProducts.map(p => p.id));
    this._deletedIds = new Set([...this._deletedIds].filter(id => serverIds.has(id)));
    
    // Mettre à jour les stats (utiliser notre compte local)
    const expiringSensor = this._hass.states['sensor.gestionnaire_d_inventaire_produits_perimant_bientot'];
    const expiredSensor = this._hass.states['sensor.gestionnaire_d_inventaire_produits_perimes'];
    
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

  _renderProducts() {
    const tbody = this.shadowRoot.getElementById('products-list');
    if (!tbody) return;
    
    if (this._localProducts.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">🎉 Aucun produit dans le congélateur</td></tr>';
    } else {
      tbody.innerHTML = this._localProducts.map(p => {
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
        .col-name { width: 45%; }
        .col-date { width: 30%; white-space: nowrap; }
        .col-qty { width: 10%; text-align: center; }
        .col-action { width: 15%; text-align: center; }
        tr:hover { background: #f5f5f5; }
        @media (max-width: 500px) {
          th, td { padding: 8px 4px; font-size: 0.8em; }
          .col-name { width: 40%; }
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
                <th class="col-name">Produit</th>
                <th class="col-date">Péremption</th>
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
          <div class="modal-actions">
            <button class="btn-cancel" id="btn-edit-cancel">Annuler</button>
            <button class="btn-primary" id="btn-edit-save">Enregistrer</button>
          </div>
        </div>
      </div>
    `;

    // Event listeners
    this.shadowRoot.getElementById('btn-add').onclick = () => this._openAddModal();
    this.shadowRoot.getElementById('btn-scan').onclick = () => this._openScanModal();
    this.shadowRoot.getElementById('btn-cancel').onclick = () => this._closeModals();
    this.shadowRoot.getElementById('btn-scan-cancel').onclick = () => this._closeScanModal();
    this.shadowRoot.getElementById('btn-edit-cancel').onclick = () => this._closeModals();
    this.shadowRoot.getElementById('btn-save').onclick = () => this._addProduct();
    this.shadowRoot.getElementById('btn-scan-save').onclick = () => this._scanProduct();
    this.shadowRoot.getElementById('btn-edit-save').onclick = () => this._saveEditProduct();
    this.shadowRoot.getElementById('btn-start-camera').onclick = () => this._startCamera();
    this.shadowRoot.getElementById('btn-lookup').onclick = () => this._lookupBarcode();
    
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
    
    // Set default dates
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 30);
    const dateStr = defaultDate.toISOString().split('T')[0];
    this.shadowRoot.getElementById('product-date').value = dateStr;
    this.shadowRoot.getElementById('scan-date').value = dateStr;
  }

  _openAddModal() {
    this.shadowRoot.getElementById('add-modal').classList.add('open');
    this.shadowRoot.getElementById('product-name').focus();
  }

  _openScanModal() {
    this.shadowRoot.getElementById('scan-modal').classList.add('open');
    // Reset form
    this.shadowRoot.getElementById('scan-barcode').value = '';
    this.shadowRoot.getElementById('scan-name').value = '';
    this.shadowRoot.getElementById('product-info-box').style.display = 'none';
    // Reset camera state
    this.shadowRoot.getElementById('camera-container').style.display = 'none';
    this.shadowRoot.getElementById('camera-status').textContent = '';
    this.shadowRoot.getElementById('btn-start-camera').style.display = 'flex';
  }

  _openEditModal(productId) {
    const product = this._localProducts.find(p => p.id === productId);
    if (!product) return;
    
    this.shadowRoot.getElementById('edit-id').value = productId;
    this.shadowRoot.getElementById('edit-name').value = product.name || '';
    this.shadowRoot.getElementById('edit-date').value = product.expiry_date || '';
    this.shadowRoot.getElementById('edit-qty').value = product.quantity || 1;
    this.shadowRoot.getElementById('edit-modal').classList.add('open');
  }

  _closeModals() {
    this.shadowRoot.getElementById('add-modal').classList.remove('open');
    this.shadowRoot.getElementById('scan-modal').classList.remove('open');
    this.shadowRoot.getElementById('edit-modal').classList.remove('open');
  }

  _closeScanModal() {
    this._stopCamera();
    this.shadowRoot.getElementById('scan-modal').classList.remove('open');
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
    infoBox.innerHTML = '🔍 Recherche en cours...';
    
    try {
      const response = await fetch(`https://world.openfoodfacts.org/api/v2/product/${barcode}.json`);
      const data = await response.json();
      
      if (data.status === 1 && data.product) {
        const product = data.product;
        const name = product.product_name_fr || product.product_name || product.generic_name || '';
        const brand = product.brands || '';
        const fullName = brand ? `${name} (${brand})` : name;
        
        if (fullName) {
          nameEl.value = fullName;
          infoBox.className = 'product-info';
          infoBox.innerHTML = `✅ <strong>${fullName}</strong>`;
        } else {
          infoBox.className = 'product-info not-found';
          infoBox.innerHTML = '⚠️ Produit trouvé mais sans nom. Saisissez le nom manuellement.';
          nameEl.focus();
        }
      } else {
        infoBox.className = 'product-info not-found';
        infoBox.innerHTML = '⚠️ Produit non trouvé dans la base. Saisissez le nom manuellement.';
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
        quantity: qty
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

    // Générer un ID temporaire
    const tempId = 'temp_' + Date.now();
    
    // Créer le produit temporaire
    const newProduct = {
      id: tempId,
      name: name,
      expiry_date: date,
      quantity: qty,
      days_until_expiry: this._calculateDaysUntilExpiry(date),
      location: 'freezer'
    };
    
    // Ajouter aux produits temp ET à la liste locale
    this._tempProducts.unshift(newProduct);
    this._localProducts.unshift(newProduct);
    
    // Mettre à jour le compteur et rendre immédiatement
    const totalEl = this.shadowRoot.getElementById('total-count');
    totalEl.textContent = this._localProducts.length;
    this._renderProducts();
    
    // Fermer le modal et reset
    nameEl.value = '';
    this._closeModals();

    // Appeler le service en arrière-plan (pas de blocage)
    try {
      await this._hass.callService('inventory_manager', 'add_product', {
        name: name,
        expiry_date: date,
        location: 'freezer',
        quantity: qty
      });
      // Le produit sera remplacé automatiquement par syncFromHass quand HA confirmera
    } catch (err) {
      console.error('Erreur ajout:', err);
      // Rollback en cas d'erreur
      this._tempProducts = this._tempProducts.filter(p => p.id !== tempId);
      this._localProducts = this._localProducts.filter(p => p.id !== tempId);
      totalEl.textContent = this._localProducts.length;
      this._renderProducts();
      alert('Erreur: ' + err.message);
    }
  }

  async _scanProduct() {
    const barcodeEl = this.shadowRoot.getElementById('scan-barcode');
    const nameEl = this.shadowRoot.getElementById('scan-name');
    const dateEl = this.shadowRoot.getElementById('scan-date');
    const qtyEl = this.shadowRoot.getElementById('scan-qty');
    
    const barcode = barcodeEl.value.trim();
    const name = nameEl.value.trim();
    const date = dateEl.value;
    const qty = parseInt(qtyEl.value) || 1;

    if (!name || !date) {
      alert('Veuillez remplir le nom du produit et la date de péremption');
      return;
    }

    // Générer un ID temporaire
    const tempId = 'temp_' + Date.now();
    
    // Créer le produit temporaire avec le vrai nom
    const newProduct = {
      id: tempId,
      name: name,
      expiry_date: date,
      quantity: qty,
      days_until_expiry: this._calculateDaysUntilExpiry(date),
      location: 'freezer',
      barcode: barcode
    };
    
    // Ajouter aux produits temp ET à la liste locale
    this._tempProducts.unshift(newProduct);
    this._localProducts.unshift(newProduct);
    
    // Mettre à jour le compteur et rendre immédiatement
    const totalEl = this.shadowRoot.getElementById('total-count');
    totalEl.textContent = this._localProducts.length;
    this._renderProducts();
    
    // Fermer le modal et reset
    barcodeEl.value = '';
    nameEl.value = '';
    this.shadowRoot.getElementById('product-info-box').style.display = 'none';
    this._closeModals();

    // Appeler le service en arrière-plan
    // Toujours utiliser add_product car on a déjà le nom (évite les doublons)
    try {
      await this._hass.callService('inventory_manager', 'add_product', {
        name: name,
        expiry_date: date,
        location: 'freezer',
        quantity: qty,
        barcode: barcode || undefined
      });
    } catch (err) {
      console.error('Erreur scan:', err);
      // Rollback en cas d'erreur
      this._tempProducts = this._tempProducts.filter(p => p.id !== tempId);
      this._localProducts = this._localProducts.filter(p => p.id !== tempId);
      totalEl.textContent = this._localProducts.length;
      this._renderProducts();
      alert('Erreur: ' + err.message);
    }
  }

  async _deleteProduct(productId) {
    if (!productId) return;
    
    if (!confirm('Supprimer ce produit ?')) return;

    // Trouver le produit dans la liste locale
    const productIndex = this._localProducts.findIndex(p => p.id === productId);
    if (productIndex === -1) return;
    
    // Supprimer immédiatement de la liste locale
    this._localProducts = this._localProducts.filter(p => p.id !== productId);
    
    // Aussi des produits temp si c'en était un
    this._tempProducts = this._tempProducts.filter(p => p.id !== productId);
    
    // Ajouter à la liste des IDs supprimés (pour ignorer si HA le renvoie)
    this._deletedIds.add(productId);
    
    // Mettre à jour le compteur et rendre immédiatement
    const totalEl = this.shadowRoot.getElementById('total-count');
    totalEl.textContent = this._localProducts.length;
    this._renderProducts();

    // Appeler le service en arrière-plan (pas de blocage)
    try {
      await this._hass.callService('inventory_manager', 'remove_product', {
        product_id: productId
      });
      // Succès - rien à faire, l'élément est déjà supprimé visuellement
    } catch (err) {
      console.error('Erreur suppression:', err);
      // En cas d'erreur, on ne peut pas vraiment rollback car on ne sait plus où était le produit
      // On laisse l'utilisateur réessayer via la sync
      this._deletedIds.delete(productId);
      alert('Erreur: ' + err.message + '. Rafraîchissez la page.');
    }
  }
}

customElements.define('inventory-manager-panel', InventoryManagerPanel);
