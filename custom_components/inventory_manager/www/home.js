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
        
        /* Reset buttons section */
        .reset-section {
          margin-top: 40px;
          padding-top: 30px;
          border-top: 1px solid var(--divider-color, #e0e0e0);
        }
        .reset-title {
          text-align: center;
          color: var(--secondary-text-color, #757575);
          font-size: 0.9em;
          margin-bottom: 16px;
        }
        .reset-buttons {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 12px;
        }
        .reset-btn {
          padding: 10px 20px;
          border: none;
          border-radius: 8px;
          font-size: 0.9em;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .reset-btn.location {
          background: var(--card-background-color, white);
          color: var(--primary-text-color, #333);
          border: 1px solid var(--divider-color, #ddd);
        }
        .reset-btn.location:hover {
          background: #fff3e0;
          border-color: #ff9800;
        }
        .reset-btn.danger {
          background: #ffebee;
          color: #c62828;
          border: 1px solid #ef9a9a;
        }
        .reset-btn.danger:hover {
          background: #ffcdd2;
          border-color: #c62828;
        }
        
        /* Backup section */
        .backup-section {
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid var(--divider-color, #e0e0e0);
        }
        .backup-title {
          text-align: center;
          color: var(--secondary-text-color, #757575);
          font-size: 0.9em;
          margin-bottom: 16px;
        }
        .backup-buttons {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 12px;
        }
        .backup-btn {
          padding: 10px 20px;
          border: none;
          border-radius: 8px;
          font-size: 0.9em;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .backup-btn.export {
          background: #e3f2fd;
          color: #1565c0;
          border: 1px solid #90caf9;
        }
        .backup-btn.export:hover {
          background: #bbdefb;
          border-color: #1565c0;
        }
        .backup-btn.import {
          background: #e8f5e9;
          color: #2e7d32;
          border: 1px solid #a5d6a7;
        }
        .backup-btn.import:hover {
          background: #c8e6c9;
          border-color: #2e7d32;
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
        
        <div class="reset-section">
          <p class="reset-title">⚙️ Gestion des données</p>
          <div class="reset-buttons">
            <button class="reset-btn location" id="btn-clear-freezer">🧊 Vider congélateur</button>
            <button class="reset-btn location" id="btn-clear-fridge">🧃 Vider réfrigérateur</button>
            <button class="reset-btn location" id="btn-clear-pantry">🥫 Vider réserve</button>
            <button class="reset-btn danger" id="btn-reset-all">🗑️ Tout réinitialiser</button>
          </div>
        </div>
        
        <div class="backup-section">
          <p class="backup-title">💾 Sauvegarde des données</p>
          <div class="backup-buttons">
            <button class="backup-btn export" id="btn-export">📤 Exporter</button>
            <button class="backup-btn import" id="btn-import">📥 Importer</button>
          </div>
          <input type="file" id="import-file" accept=".json" style="display: none;">
        </div>
        
        <div class="footer">
          <p>Version 2.1.1 • Inventory Manager</p>
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
    
    // Reset buttons event listeners
    this.shadowRoot.getElementById('btn-clear-freezer').onclick = () => this._clearLocation('freezer', 'congélateur');
    this.shadowRoot.getElementById('btn-clear-fridge').onclick = () => this._clearLocation('fridge', 'réfrigérateur');
    this.shadowRoot.getElementById('btn-clear-pantry').onclick = () => this._clearLocation('pantry', 'réserve');
    this.shadowRoot.getElementById('btn-reset-all').onclick = () => this._resetAll();
    
    // Backup buttons event listeners
    this.shadowRoot.getElementById('btn-export').onclick = () => this._exportData();
    this.shadowRoot.getElementById('btn-import').onclick = () => this.shadowRoot.getElementById('import-file').click();
    this.shadowRoot.getElementById('import-file').onchange = (e) => this._importData(e);
  }
  
  async _clearLocation(location, locationName) {
    if (!confirm(`⚠️ Voulez-vous vraiment vider le ${locationName} ?\n\nTous les produits de cet emplacement seront supprimés.`)) {
      return;
    }
    
    try {
      await this._hass.callService('inventory_manager', `clear_${location}`, {});
      alert(`✅ Le ${locationName} a été vidé.`);
    } catch (err) {
      console.error(`Erreur lors du vidage du ${locationName}:`, err);
      alert(`❌ Erreur: ${err.message}`);
    }
  }
  
  async _resetAll() {
    if (!confirm('⚠️ ATTENTION !\n\nVoulez-vous vraiment tout réinitialiser ?\n\n• Tous les produits seront supprimés\n• L\'historique de saisie sera effacé\n\nCette action est irréversible !')) {
      return;
    }
    
    // Double confirmation for safety
    if (!confirm('🚨 DERNIÈRE CONFIRMATION\n\nÊtes-vous absolument sûr de vouloir supprimer toutes les données ?')) {
      return;
    }
    
    try {
      await this._hass.callService('inventory_manager', 'reset_all', {});
      alert('✅ Toutes les données ont été réinitialisées.');
    } catch (err) {
      console.error('Erreur lors de la réinitialisation:', err);
      alert(`❌ Erreur: ${err.message}`);
    }
  }

  async _exportData() {
    try {
      // Obtenir une URL signée (authentifiée, valide 30s) depuis HA
      const result = await this._hass.callWS({
        type: 'auth/sign_path',
        path: '/inventory_manager/export',
      });

      // La navigation vers une URL avec Content-Disposition: attachment
      // déclenche le download manager Android — seule méthode fiable dans un WebView.
      window.location.href = result.path;
    } catch (err) {
      console.error('Erreur lors de l\'export:', err);
      alert(`❌ Erreur: ${err.message}`);
    }
  }

  async _importData(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!confirm('⚠️ Voulez-vous vraiment importer ces données ?\n\nLes données actuelles seront remplacées.')) {
      event.target.value = '';
      return;
    }
    
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      await this._hass.callService('inventory_manager', 'import_data', {
        data: JSON.stringify(data)
      });
      
      alert('✅ Import réussi ! Rechargement de la page...');
      location.reload();
    } catch (err) {
      console.error('Erreur lors de l\'import:', err);
      alert(`❌ Erreur: ${err.message}`);
    } finally {
      event.target.value = '';
    }
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
