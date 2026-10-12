/* AUTO NEXA - AutoDukan Style Master Catalogue Portal (22.7M+ Records) */

window.OverallCataloguePortal = {
  viewMode: 'grid', // 'grid' (AutoDukan Cards) or 'table' (Enterprise Grid)
  currentPage: 1,
  limit: 48,
  totalRecords: 0,
  totalPages: 1,
  searchDebounceTimer: null,
  activeVahanReg: '',
  filters: {
    brand: '',
    segment: '',
    make: '',
    model: '',
    sub_model: '',
    fuel_type: '',
    year: '',
    aggregate: '',
    sub_aggregate: '',
    component: '',
    min_price: '',
    max_price: ''
  },
  q: '',

  async init() {
    console.log("Initializing AutoDukan Master Catalogue Portal (22.7M+ DB)...");
    await this.loadStats();
    await this.loadFilterOptions();
    await this.loadGarageMakes();
    await this.fetchData();
  },

  async loadStats() {
    try {
      const res = await fetch('/api/overall-catalogue/stats');
      if (!res.ok) return;
      const data = await res.json();
      
      const elRecords = document.getElementById('cat-stat-records');
      const elParts = document.getElementById('cat-stat-parts');
      const elBrands = document.getElementById('cat-stat-brands');
      const elMakes = document.getElementById('cat-stat-makes');

      const records = data.totalRecords ?? data.total_records ?? 0;
      const parts = data.totalParts ?? data.unique_parts ?? 0;
      const brands = data.totalBrands ?? data.unique_brands ?? 0;
      const makes = data.totalMakes ?? data.unique_makes ?? 0;

      if (elRecords) elRecords.textContent = records.toLocaleString();
      if (elParts) elParts.textContent = parts.toLocaleString();
      if (elBrands) elBrands.textContent = brands.toLocaleString();
      if (elMakes) elMakes.textContent = makes.toLocaleString();
    } catch (err) {
      console.error("Error loading catalogue stats:", err);
    }
  },

  async loadFilterOptions() {
    try {
      const res = await fetch('/api/overall-catalogue/filters');
      if (!res.ok) return;
      const data = await res.json();

      this.populateSelect('cat-filter-brand', data.brands || [], 'All Brands');
      this.populateSelect('cat-filter-segment', data.segments || [], 'All Segments');
      this.populateSelect('cat-filter-make', data.makes || [], 'All Vehicle Makes');
      this.populateSelect('cat-filter-aggregate', data.aggregates || [], 'All Aggregates');
      this.populateSelect('cat-filter-sub-aggregate', data.sub_aggregates || [], 'All Sub-Aggregates');
      this.populateSelect('cat-filter-component', data.components || [], 'All Components');
    } catch (err) {
      console.error("Error loading filter options:", err);
    }
  },

  async loadGarageMakes() {
    try {
      const res = await fetch('/api/overall-catalogue/filters');
      if (!res.ok) return;
      const data = await res.json();
      this.populateSelect('cat-garage-make', data.makes || [], 'Choose Vehicle Make');
    } catch (err) {
      console.error("Error loading garage makes:", err);
    }
  },

  populateSelect(elementId, items, defaultLabel) {
    const sel = document.getElementById(elementId);
    if (!sel) return;
    const currentVal = sel.value;
    sel.innerHTML = `<option value="">${defaultLabel}</option>` + 
      items.map(item => `<option value="${this.escapeHtml(item)}">${this.escapeHtml(item)}</option>`).join('');
    if (currentVal && items.includes(currentVal)) {
      sel.value = currentVal;
    }
  },

  ensureOption(selectId, value) {
    const sel = document.getElementById(selectId);
    if (!sel || !value) return;
    let found = false;
    for (let opt of sel.options) {
      if (opt.value === value) { found = true; break; }
    }
    if (!found) {
      const newOpt = document.createElement('option');
      newOpt.value = value;
      newOpt.textContent = value;
      sel.appendChild(newOpt);
    }
    sel.value = value;
  },

  setViewMode(mode) {
    this.viewMode = mode;
    const gridBtn = document.getElementById('cat-view-grid-btn');
    const tableBtn = document.getElementById('cat-view-table-btn');
    const gridWrapper = document.getElementById('cat-grid-wrapper');
    const tableWrapper = document.getElementById('cat-table-wrapper');

    if (mode === 'grid') {
      if (gridBtn) { gridBtn.style.background = '#38bdf8'; gridBtn.style.color = '#0f172a'; }
      if (tableBtn) { tableBtn.style.background = 'transparent'; tableBtn.style.color = '#cbd5e1'; }
      if (gridWrapper) gridWrapper.style.display = 'grid';
      if (tableWrapper) tableWrapper.style.display = 'none';
    } else {
      if (tableBtn) { tableBtn.style.background = '#38bdf8'; tableBtn.style.color = '#0f172a'; }
      if (gridBtn) { gridBtn.style.background = 'transparent'; gridBtn.style.color = '#cbd5e1'; }
      if (tableWrapper) tableWrapper.style.display = 'block';
      if (gridWrapper) gridWrapper.style.display = 'none';
    }
    this.fetchData();
  },

  setOrderType(type) {
    const btnStock = document.getElementById('btn-order-stock');
    const btnVehicle = document.getElementById('btn-order-vehicle');
    if (type === 'stock') {
      if (btnStock) {
        btnStock.style.background = '#ea580c';
        btnStock.style.color = '#ffffff';
        btnStock.style.boxShadow = '0 0 12px rgba(234, 88, 12, 0.4)';
      }
      if (btnVehicle) {
        btnVehicle.style.background = 'transparent';
        btnVehicle.style.color = '#94a3b8';
        btnVehicle.style.boxShadow = 'none';
      }
    } else {
      if (btnVehicle) {
        btnVehicle.style.background = '#ea580c';
        btnVehicle.style.color = '#ffffff';
        btnVehicle.style.boxShadow = '0 0 12px rgba(234, 88, 12, 0.4)';
      }
      if (btnStock) {
        btnStock.style.background = 'transparent';
        btnStock.style.color = '#94a3b8';
        btnStock.style.boxShadow = 'none';
      }
    }
  },

  toggleVahanKeyInput() {
    const container = document.getElementById('cat-vahan-key-container');
    const input = document.getElementById('cat-vahan-api-key');
    if (container) {
      const isHidden = container.style.display === 'none';
      container.style.display = isHidden ? 'block' : 'none';
      if (isHidden && input) {
        input.value = localStorage.getItem('vahan_api_key') || '';
      }
    }
  },

  saveVahanApiKey() {
    const input = document.getElementById('cat-vahan-api-key');
    const key = input ? input.value.trim() : '';
    if (key) {
      localStorage.setItem('vahan_api_key', key);
      alert("✓ Live Vahan API Key saved successfully! Future searches will query live Vahan endpoints.");
    } else {
      localStorage.removeItem('vahan_api_key');
      alert("Vahan API Key cleared. System will use Smart RTO Resolver.");
    }
    const container = document.getElementById('cat-vahan-key-container');
    if (container) container.style.display = 'none';
  },

  // AutoDukan Vahan Registration Number Search Engine
  async lookupVahan() {
    const input = document.getElementById('cat-vahan-input');
    const btnIcon = document.getElementById('cat-vahan-btn-icon');
    const btnText = document.getElementById('cat-vahan-btn-text');
    const btn = document.getElementById('cat-vahan-search-btn');

    const regNo = input ? input.value.trim() : '';
    if (!regNo) {
      alert("Please enter a vehicle registration number (e.g. TN06AM1234)");
      return;
    }

    if (btnText) btnText.textContent = 'Searching...';
    if (btnIcon) btnIcon.textContent = '⌛';
    if (btn) btn.disabled = true;

    try {
      const apiKey = localStorage.getItem('vahan_api_key') || '';
      let url = `/api/vahan/lookup?reg_no=${encodeURIComponent(regNo)}`;
      if (apiKey) url += `&api_key=${encodeURIComponent(apiKey)}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error("Vahan RC details not found");
      const data = await res.json();

      if (data.status === 'success') {
        this.activeVahanReg = data.registrationNo;
        this.filters.make = data.make || '';
        this.filters.model = data.model || '';
        this.filters.sub_model = data.subModel || '';
        this.filters.fuel_type = data.fuelType || '';
        this.filters.year = data.year || '';

        // Display Green Toast Banner at top right
        const pill = document.getElementById('cat-garage-active-pill');
        const text = document.getElementById('cat-garage-active-text');
        if (pill && text) {
          text.textContent = `✓ Vehicle found. Please review the details. (${data.make} ${data.model} - ${data.subModel})`;
          pill.style.display = 'inline-flex';
        }

        // Ensure make option exists and is selected
        this.ensureOption('cat-garage-make', data.make);
        this.ensureOption('cat-filter-make', data.make);

        // Load models for this make & sub-models
        await this.loadModelsForMake(data.make, data.model, data.subModel);

        // Set Fuel & Year dropdowns
        const fuelSel = document.getElementById('cat-garage-fuel');
        if (fuelSel && data.fuelType) {
          this.ensureOption('cat-garage-fuel', data.fuelType);
          fuelSel.value = data.fuelType;
        }

        const yearSel = document.getElementById('cat-garage-year');
        if (yearSel && data.year) {
          this.ensureOption('cat-garage-year', data.year);
          yearSel.value = data.year;
        }

        this.currentPage = 1;
        this.fetchData();
        if (window.App && window.App.showToast) {
          window.App.showToast(`Vehicle found. Please review the details.`, "success");
        }
      } else if (data.status === 'no_api_key') {
        const pill = document.getElementById('cat-garage-active-pill');
        const text = document.getElementById('cat-garage-active-text');
        if (pill && text) {
          text.textContent = `ℹ️ ${data.registrationNo} (${data.rto}) — Select Make & Model below, or add API Key.`;
          pill.style.display = 'inline-flex';
          pill.style.background = 'rgba(56, 189, 248, 0.15)';
          pill.style.borderColor = '#38bdf8';
        }
        if (window.App && window.App.showToast) {
          window.App.showToast(data.message, "info");
        } else {
          alert(data.message);
        }
      } else {
        alert(data.message || "Failed to resolve vehicle registration number.");
      }
    } catch (err) {
      console.error("Vahan lookup error:", err);
      alert("Error fetching Vahan RC details. Please verify backend server connection.");
    } finally {
      if (btnText) btnText.textContent = 'Search';
      if (btnIcon) btnIcon.textContent = '🔍';
      if (btn) btn.disabled = false;
    }
  },

  async loadModelsForMake(make, targetModel = null, targetSubModel = null) {
    if (!make) return;
    try {
      const res = await fetch(`/api/overall-catalogue/models?make=${encodeURIComponent(make)}`);
      if (res.ok) {
        const data = await res.json();
        const models = Array.isArray(data) ? data : (data.models || []);
        this.populateSelect('cat-garage-model', models, 'Select Model');
        this.populateSelect('cat-filter-model', models, 'All Vehicle Models');

        if (targetModel) {
          this.ensureOption('cat-garage-model', targetModel);
          this.ensureOption('cat-filter-model', targetModel);
        }

        if (targetModel && targetSubModel) {
          await this.loadSubModelsForMakeModel(make, targetModel, targetSubModel);
        }
      }
    } catch (err) {
      console.error("Error loading models for make:", err);
    }
  },

  async loadSubModelsForMakeModel(make, model, targetSubModel = null) {
    if (!make || !model) return;
    try {
      const res = await fetch(`/api/overall-catalogue/sub-models?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}`);
      if (res.ok) {
        const data = await res.json();
        const subModels = data.sub_models || [];
        this.populateSelect('cat-garage-submodel', subModels, 'Select Variant');
        if (targetSubModel) {
          this.ensureOption('cat-garage-submodel', targetSubModel);
        }
      }
    } catch (err) {
      console.error("Error loading sub-models:", err);
    }
  },

  async handleGarageMakeChange() {
    const makeVal = document.getElementById('cat-garage-make')?.value || '';
    this.filters.make = makeVal;
    this.ensureOption('cat-filter-make', makeVal);

    const modelSel = document.getElementById('cat-garage-model');
    const subSel = document.getElementById('cat-garage-submodel');

    if (!makeVal) {
      if (modelSel) modelSel.innerHTML = `<option value="">Select Model</option>`;
      if (subSel) subSel.innerHTML = `<option value="">Select Variant</option>`;
      this.filters.model = '';
      this.filters.sub_model = '';
      this.fetchData();
      return;
    }

    await this.loadModelsForMake(makeVal);
    this.fetchData();
  },

  async handleGarageModelChange() {
    const makeVal = document.getElementById('cat-garage-make')?.value || this.filters.make || '';
    const modelVal = document.getElementById('cat-garage-model')?.value || '';
    this.filters.model = modelVal;
    this.ensureOption('cat-filter-model', modelVal);

    const subSel = document.getElementById('cat-garage-submodel');
    if (!modelVal) {
      if (subSel) subSel.innerHTML = `<option value="">Select Variant</option>`;
      this.filters.sub_model = '';
      this.fetchData();
      return;
    }

    await this.loadSubModelsForMakeModel(makeVal, modelVal);
    this.fetchData();
  },

  handleGarageSubModelChange() {
    const subVal = document.getElementById('cat-garage-submodel')?.value || '';
    this.filters.sub_model = subVal;
    this.fetchData();
  },

  handleGarageFuelChange() {
    const fuelVal = document.getElementById('cat-garage-fuel')?.value || '';
    this.filters.fuel_type = fuelVal;
    this.currentPage = 1;
    this.fetchData();
  },

  handleGarageYearChange() {
    const yearVal = document.getElementById('cat-garage-year')?.value || '';
    this.filters.year = yearVal;
    this.currentPage = 1;
    this.fetchData();
  },

  exploreProducts() {
    const makeVal = document.getElementById('cat-garage-make')?.value || '';
    const modelVal = document.getElementById('cat-garage-model')?.value || '';
    const subVal = document.getElementById('cat-garage-submodel')?.value || '';
    const fuelVal = document.getElementById('cat-garage-fuel')?.value || '';
    const yearVal = document.getElementById('cat-garage-year')?.value || '';
    const aggVal = document.getElementById('cat-filter-aggregate')?.value || '';
    const subAggVal = document.getElementById('cat-filter-sub-aggregate')?.value || '';

    this.filters.make = makeVal;
    this.filters.model = modelVal;
    this.filters.sub_model = subVal;
    this.filters.fuel_type = fuelVal;
    this.filters.year = yearVal;
    this.filters.aggregate = aggVal;
    this.filters.sub_aggregate = subAggVal;

    this.currentPage = 1;
    this.fetchData();

    if (window.App && window.App.showToast) {
      window.App.showToast("Filtered products updated for selected vehicle & category.", "info");
    }
  },

  clearGarage() {
    this.activeVahanReg = '';
    const pill = document.getElementById('cat-garage-active-pill');
    if (pill) pill.style.display = 'none';

    ['cat-garage-make', 'cat-garage-model', 'cat-garage-submodel', 'cat-garage-fuel', 'cat-garage-year', 'cat-vahan-input'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });

    this.filters.make = '';
    this.filters.model = '';
    this.filters.sub_model = '';
    this.filters.fuel_type = '';
    this.filters.year = '';

    const filterMake = document.getElementById('cat-filter-make');
    if (filterMake) filterMake.value = '';
    const filterModel = document.getElementById('cat-filter-model');
    if (filterModel) filterModel.value = '';

    this.currentPage = 1;
    this.fetchData();
  },

  filterCategory(catName) {
    const aggSel = document.getElementById('cat-filter-aggregate');
    if (aggSel) {
      let matched = false;
      for (let opt of aggSel.options) {
        if (opt.value.toUpperCase().includes(catName) || catName.includes(opt.value.toUpperCase())) {
          aggSel.value = opt.value;
          matched = true;
          break;
        }
      }
      if (!matched) {
        const searchInput = document.getElementById('cat-search-q');
        if (searchInput) searchInput.value = catName;
        this.q = catName;
      } else {
        this.handleAggregateChange();
      }
    }
    this.currentPage = 1;
    this.fetchData();
  },

  async handleMakeChange() {
    const makeVal = document.getElementById('cat-filter-make')?.value || '';
    this.filters.make = makeVal;
    this.ensureOption('cat-garage-make', makeVal);
    const modelSel = document.getElementById('cat-filter-model');
    if (!modelSel) return;

    if (!makeVal) {
      modelSel.innerHTML = `<option value="">All Vehicle Models</option>`;
      this.handleFilterChange();
      return;
    }

    await this.loadModelsForMake(makeVal);
    this.handleFilterChange();
  },

  async handleAggregateChange() {
    const aggVal = document.getElementById('cat-filter-aggregate')?.value || '';
    
    try {
      const url = aggVal ? `/api/overall-catalogue/sub-aggregates?aggregate=${encodeURIComponent(aggVal)}` : '/api/overall-catalogue/sub-aggregates';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        this.populateSelect('cat-filter-sub-aggregate', data.sub_aggregates || [], 'All Sub-Aggregates');
      }
    } catch (err) {
      console.error("Error fetching sub-aggregates:", err);
    }

    try {
      const url = aggVal ? `/api/overall-catalogue/components?aggregate=${encodeURIComponent(aggVal)}` : '/api/overall-catalogue/components';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        this.populateSelect('cat-filter-component', data.components || [], 'All Components');
      }
    } catch (err) {
      console.error("Error fetching components:", err);
    }

    this.handleFilterChange();
  },

  async handleSubAggregateChange() {
    const aggVal = document.getElementById('cat-filter-aggregate')?.value || '';
    const subAggVal = document.getElementById('cat-filter-sub-aggregate')?.value || '';

    try {
      const params = new URLSearchParams();
      if (aggVal) params.append('aggregate', aggVal);
      if (subAggVal) params.append('sub_aggregate', subAggVal);

      const res = await fetch(`/api/overall-catalogue/components?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        this.populateSelect('cat-filter-component', data.components || [], 'All Components');
      }
    } catch (err) {
      console.error("Error fetching components:", err);
    }

    this.handleFilterChange();
  },

  handleSearchInput(val) {
    this.q = val.trim();
    if (this.searchDebounceTimer) clearTimeout(this.searchDebounceTimer);
    this.searchDebounceTimer = setTimeout(() => {
      this.currentPage = 1;
      this.fetchData();
    }, 300);
  },

  handleFilterChange() {
    this.filters.brand = document.getElementById('cat-filter-brand')?.value || '';
    this.filters.segment = document.getElementById('cat-filter-segment')?.value || '';
    this.filters.make = document.getElementById('cat-filter-make')?.value || this.filters.make || '';
    this.filters.model = document.getElementById('cat-filter-model')?.value || this.filters.model || '';
    this.filters.aggregate = document.getElementById('cat-filter-aggregate')?.value || '';
    this.filters.sub_aggregate = document.getElementById('cat-filter-sub-aggregate')?.value || '';
    this.filters.component = document.getElementById('cat-filter-component')?.value || '';
    this.filters.min_price = document.getElementById('cat-price-min')?.value || '';
    this.filters.max_price = document.getElementById('cat-price-max')?.value || '';

    this.currentPage = 1;
    this.fetchData();
  },

  resetFilters() {
    this.clearGarage();

    const searchInput = document.getElementById('cat-search-q');
    if (searchInput) searchInput.value = '';
    this.q = '';

    ['cat-filter-brand', 'cat-filter-segment', 'cat-filter-make', 'cat-filter-model', 'cat-filter-aggregate', 'cat-filter-sub-aggregate', 'cat-filter-component', 'cat-price-min', 'cat-price-max'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });

    this.filters = { brand: '', segment: '', make: '', model: '', sub_model: '', fuel_type: '', year: '', aggregate: '', sub_aggregate: '', component: '', min_price: '', max_price: '' };
    this.currentPage = 1;
    this.fetchData();
  },

  async fetchData() {
    const gridWrapper = document.getElementById('cat-grid-wrapper');
    const tbody = document.getElementById('cat-table-body');

    if (gridWrapper && this.viewMode === 'grid') {
      gridWrapper.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #38bdf8; font-weight: 700; font-size: 1rem;">⚡ Querying 22.7M+ AutoDukan Master Catalogue Database...</div>`;
    }
    if (tbody && this.viewMode === 'table') {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 2.5rem; color: #38bdf8; font-weight: 700;">⚡ Querying 22.7M+ Catalogue Master Records...</td></tr>`;
    }

    try {
      const params = new URLSearchParams({
        page: this.currentPage,
        limit: this.limit
      });
      if (this.q) params.append('q', this.q);
      if (this.filters.brand) params.append('brand', this.filters.brand);
      if (this.filters.segment) params.append('segment', this.filters.segment);
      if (this.filters.make) params.append('make', this.filters.make);
      if (this.filters.model) params.append('model', this.filters.model);
      if (this.filters.sub_model) params.append('sub_model', this.filters.sub_model);
      if (this.filters.fuel_type) params.append('fuel_type', this.filters.fuel_type);
      if (this.filters.aggregate) params.append('aggregate', this.filters.aggregate);
      if (this.filters.sub_aggregate) params.append('sub_aggregate', this.filters.sub_aggregate);
      if (this.filters.component) params.append('component', this.filters.component);
      if (this.filters.min_price) params.append('min_price', this.filters.min_price);
      if (this.filters.max_price) params.append('max_price', this.filters.max_price);

      const res = await fetch(`/api/overall-catalogue/search?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP Error ${res.status}`);

      const data = await res.json();
      const items = data.items || data.results || [];
      this.totalRecords = data.totalCount ?? data.total ?? 0;
      this.totalPages = data.totalPages ?? data.total_pages ?? 1;

      if (this.viewMode === 'grid') {
        this.renderGrid(items);
      } else {
        this.renderTable(items);
      }
      this.renderPagination();
    } catch (err) {
      console.error("Fetch catalogue data error:", err);
      if (gridWrapper) {
        gridWrapper.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: #f87171; font-weight: 700;">⚠️ Error fetching catalogue records. Please verify backend server.</div>`;
      }
    }
  },

  // AutoDukan E-Commerce Part Card View Renderer
  renderGrid(rows) {
    const gridWrapper = document.getElementById('cat-grid-wrapper');
    if (!gridWrapper) return;

    if (rows.length === 0) {
      gridWrapper.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #94a3b8; font-weight: 600;">No catalogue parts found matching the selected vehicle specification or filters.</div>`;
      return;
    }

    gridWrapper.innerHTML = rows.map(r => {
      const partNo = r.partNo ?? r.part_number ?? '';
      const brand = r.brand ?? r.brand_name ?? 'GENERIC';
      const desc = r.desc ?? r.part_description ?? '';
      const listVal = r.listPrice ?? r.list_price;
      const mrpVal = r.mrp ?? r.mrp_price;
      const segment = r.segment ?? '-';
      const make = r.make ?? '';
      const model = r.model ?? '';
      const subModel = r.subModel ?? r.sub_model ?? '';
      const aggregate = r.aggregate ?? r.aggregate_name ?? 'SPARE PART';

      let mrpPrice = 'Price on Request';
      if (mrpVal != null && Number(mrpVal) > 0) {
        mrpPrice = `₹${Number(mrpVal).toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
      } else if (listVal != null && Number(listVal) > 0) {
        mrpPrice = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
      }

      const vehicleInfo = [make, model, subModel].filter(Boolean).join(' ') || 'Multi-Vehicle Compatible';

      // Pick system icon based on aggregate
      let sysIcon = '📦';
      const aggUpper = aggregate.toUpperCase();
      if (aggUpper.includes('BRAKE')) sysIcon = '🛑';
      else if (aggUpper.includes('ENGINE') || aggUpper.includes('CLUTCH')) sysIcon = '⚙️';
      else if (aggUpper.includes('SUSPENSION') || aggUpper.includes('STEERING')) sysIcon = '🛞';
      else if (aggUpper.includes('ELECTRICAL') || aggUpper.includes('RELAY')) sysIcon = '⚡';
      else if (aggUpper.includes('HVAC') || aggUpper.includes('COOLING')) sysIcon = '❄️';
      else if (aggUpper.includes('LUB') || aggUpper.includes('OIL') || aggUpper.includes('FILTER')) sysIcon = '🛢️';
      else if (aggUpper.includes('BODY')) sysIcon = '🚗';

      return `
        <div style="background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85)); border: 1.5px solid rgba(56, 189, 248, 0.25); border-radius: 14px; padding: 1.1rem; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s; position: relative;" onmouseover="this.style.borderColor='#38bdf8'; this.style.transform='translateY(-3px)'" onmouseout="this.style.borderColor='rgba(56, 189, 248, 0.25)'; this.style.transform='none'">
          
          <!-- Card Header: Brand Badge & System Icon -->
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
              <span class="badge" style="background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.35); padding: 0.2rem 0.55rem; border-radius: 6px; font-size: 0.72rem; font-weight: 800;">
                ${this.escapeHtml(brand)}
              </span>
              <span style="font-size: 1.3rem;">${sysIcon}</span>
            </div>

            <!-- Part Number & Description -->
            <div style="font-family: monospace; font-size: 0.92rem; font-weight: 850; color: #38bdf8; margin-bottom: 0.25rem; letter-spacing: -0.2px;">
              ${this.escapeHtml(partNo)}
            </div>
            <div style="font-size: 0.83rem; font-weight: 700; color: #ffffff; line-height: 1.35; height: 2.7em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 0.75rem;">
              ${this.escapeHtml(desc)}
            </div>
          </div>

          <!-- Card Bottom: MRP Price, Fitment Tag & Modal Trigger -->
          <div>
            <div style="background: rgba(8, 15, 30, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0.6rem; margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.7rem; color: #94a3b8; font-weight: 800; text-transform: uppercase;">AutoDukan MRP</span>
                <span style="font-size: 0.7rem; color: #a78bfa; font-weight: 800; background: rgba(167, 139, 250, 0.12); padding: 0.1rem 0.4rem; border-radius: 4px;">${this.escapeHtml(segment)}</span>
              </div>
              <div style="font-size: 1.25rem; font-weight: 900; color: #34d399; font-family: 'Outfit', sans-serif; margin-top: 0.1rem;">
                ${mrpPrice}
              </div>
            </div>

            <div style="font-size: 0.72rem; color: #cbd5e1; margin-bottom: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 0.3rem;">
              <span>🚗</span>
              <strong style="color: #ffffff;">${this.escapeHtml(vehicleInfo)}</strong>
            </div>

            <button type="button" onclick="OverallCataloguePortal.showPartDetails('${this.escapeJs(partNo)}')" style="width: 100%; padding: 0.5rem; font-size: 0.78rem; font-weight: 850; background: rgba(56, 189, 248, 0.15); border: 1.5px solid rgba(56, 189, 248, 0.4); color: #38bdf8; border-radius: 8px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#38bdf8'; this.style.color='#0f172a'" onmouseout="this.style.background='rgba(56, 189, 248, 0.15)'; this.style.color='#38bdf8'">
              🔍 Spec & Fitment List
            </button>
          </div>

        </div>
      `;
    }).join('');
  },

  renderTable(rows) {
    const tbody = document.getElementById('cat-table-body');
    if (!tbody) return;

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 2.5rem; color: #94a3b8; font-weight: 600;">No catalogue parts found matching the selected query and filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = rows.map(r => {
      const partNo = r.partNo ?? r.part_number ?? '';
      const brand = r.brand ?? r.brand_name ?? 'GENERIC';
      const desc = r.desc ?? r.part_description ?? '';
      const listVal = r.listPrice ?? r.list_price;
      const mrpVal = r.mrp ?? r.mrp_price;
      const taxRate = r.taxRate ?? r.tax_pct;
      const segment = r.segment ?? '-';
      const make = r.make ?? '';
      const model = r.model ?? '';
      const subModel = r.subModel ?? r.sub_model ?? '';
      const fuelType = r.fuelType ?? r.fuel_type ?? '';
      
      let years = r.applicable_years || '';
      if (!years && (r.fromYear || r.toYear)) {
        years = `${r.fromYear || ''} - ${r.toYear || ''}`.trim();
      }

      const aggregate = r.aggregate ?? r.aggregate_name ?? '-';

      let mrpPrice = 'Price on Request';
      if (mrpVal != null && Number(mrpVal) > 0) {
        mrpPrice = `₹${Number(mrpVal).toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
      } else if (listVal != null && Number(listVal) > 0) {
        mrpPrice = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
      }

      let listPrice = 'N/A';
      if (listVal != null && Number(listVal) > 0) {
        listPrice = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
      }

      const taxPct = (taxRate != null && Number(taxRate) > 0) ? `${taxRate}%` : 'N/A';

      const vehicleInfo = [make, model, subModel].filter(Boolean).join(' ') || 'Universal / Multi-fit';
      const fuelYears = [fuelType, years].filter(Boolean).join(' | ');

      return `
        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); transition: background 0.15s;" onmouseover="this.style.background='rgba(56, 189, 248, 0.06)'" onmouseout="this.style.background='transparent'">
          <td style="font-weight: 850; color: #38bdf8; font-family: monospace; font-size: 0.88rem;">${this.escapeHtml(partNo)}</td>
          <td style="font-weight: 750; color: #fbbf24; font-size: 0.82rem;"><span class="badge" style="background: rgba(251, 191, 36, 0.12); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); padding: 0.2rem 0.5rem; border-radius: 6px;">${this.escapeHtml(brand)}</span></td>
          <td style="font-weight: 600; color: #e2e8f0; font-size: 0.82rem; max-width: 260px; white-space: normal; line-height: 1.35;">${this.escapeHtml(desc)}</td>
          <td style="font-weight: 800; color: #34d399; font-size: 0.85rem; text-align: right;">${mrpPrice}</td>
          <td style="font-weight: 600; color: #94a3b8; font-size: 0.8rem; text-align: right;">${listPrice}</td>
          <td style="font-weight: 600; color: #cbd5e1; font-size: 0.8rem; text-align: center;">${taxPct}</td>
          <td style="font-weight: 700; color: #a78bfa; font-size: 0.8rem;"><span class="badge" style="background: rgba(167, 139, 250, 0.12); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.3); padding: 0.2rem 0.45rem; border-radius: 6px;">${this.escapeHtml(segment)}</span></td>
          <td style="font-size: 0.8rem; color: #f1f5f9;">
            <div style="font-weight: 750; color: #ffffff;">${this.escapeHtml(vehicleInfo)}</div>
            ${fuelYears ? `<div style="font-size: 0.72rem; color: #94a3b8;">${this.escapeHtml(fuelYears)}</div>` : ''}
          </td>
          <td style="font-weight: 700; color: #38bdf8; font-size: 0.8rem;">${this.escapeHtml(aggregate)}</td>
          <td style="text-align: center;">
            <button type="button" class="btn btn-secondary" onclick="OverallCataloguePortal.showPartDetails('${this.escapeJs(partNo)}')" style="padding: 0.35rem 0.65rem; font-size: 0.75rem; font-weight: 750; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; border-radius: 7px; cursor: pointer; display: inline-flex; align-items: center; gap: 0.3rem;">
              <span>🔍 Fitment</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  },

  renderPagination() {
    const infoEl = document.getElementById('cat-pagination-info');
    const buttonsEl = document.getElementById('cat-pagination-buttons');

    const start = Math.min((this.currentPage - 1) * this.limit + 1, this.totalRecords);
    const end = Math.min(this.currentPage * this.limit, this.totalRecords);

    if (infoEl) {
      infoEl.textContent = `Showing ${start.toLocaleString()} to ${end.toLocaleString()} of ${this.totalRecords.toLocaleString()} records`;
    }

    if (!buttonsEl) return;

    let html = '';
    const total = this.totalPages;
    const curr = this.currentPage;

    // Previous Button
    html += `<button type="button" class="btn btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.78rem; border-radius: 7px; cursor: pointer;" ${curr <= 1 ? 'disabled' : ''} onclick="OverallCataloguePortal.goToPage(${curr - 1})">◀ Prev</button>`;

    // Page range logic
    let pages = [];
    if (total <= 7) {
      for (let i = 1; i <= total; i++) pages.push(i);
    } else {
      pages.push(1);
      if (curr > 3) pages.push('...');
      const startP = Math.max(2, curr - 1);
      const endP = Math.min(total - 1, curr + 1);
      for (let i = startP; i <= endP; i++) pages.push(i);
      if (curr < total - 2) pages.push('...');
      pages.push(total);
    }

    pages.forEach(p => {
      if (p === '...') {
        html += `<span style="padding: 0.35rem 0.5rem; color: #64748b; font-size: 0.8rem;">...</span>`;
      } else {
        const isActive = p === curr;
        html += `<button type="button" class="btn ${isActive ? 'btn-primary' : 'btn-secondary'}" style="padding: 0.35rem 0.65rem; font-size: 0.78rem; font-weight: 800; border-radius: 7px; cursor: pointer; ${isActive ? 'background: #38bdf8; color: #0f172a;' : ''}" onclick="OverallCataloguePortal.goToPage(${p})">${p}</button>`;
      }
    });

    // Next Button
    html += `<button type="button" class="btn btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.78rem; border-radius: 7px; cursor: pointer;" ${curr >= total ? 'disabled' : ''} onclick="OverallCataloguePortal.goToPage(${curr + 1})">Next ▶</button>`;

    buttonsEl.innerHTML = html;
  },

  goToPage(p) {
    if (p < 1 || p > this.totalPages) return;
    this.currentPage = p;
    this.fetchData();
  },

  changeLimit(newLimit) {
    this.limit = parseInt(newLimit, 10) || 48;
    this.currentPage = 1;
    this.fetchData();
  },

  async showPartDetails(partNo) {
    const modal = document.getElementById('cat-part-modal');
    const modalBody = document.getElementById('cat-modal-body');
    if (!modal || !modalBody) return;

    modalBody.innerHTML = `<div style="text-align: center; padding: 3rem; color: #38bdf8; font-weight: 700;">Loading part specifications & fitment compatibility...</div>`;
    modal.style.display = 'flex';

    try {
      const res = await fetch(`/api/overall-catalogue/part/${encodeURIComponent(partNo)}`);
      if (!res.ok) throw new Error("Part details not found");
      const data = await res.json();

      const spec = data.specifications || data.part || data || {};
      const fitments = data.fitments || data.compatibilities || [];

      const pNo = spec.partNo ?? spec.part_number ?? partNo;
      const brand = spec.brand ?? spec.brand_name ?? 'N/A';
      const desc = spec.desc ?? spec.part_description ?? '';
      const mrpVal = spec.mrp ?? spec.mrp_price;
      const listVal = spec.listPrice ?? spec.list_price;
      const taxRate = spec.taxRate ?? spec.tax_pct;
      const segment = spec.segment ?? '';
      const aggregate = spec.aggregate ?? spec.aggregate_name ?? '';
      const subAggregate = spec.subAggregate ?? spec.sub_aggregate ?? '';
      const component = spec.components ?? spec.component ?? '';

      let mrp = 'Price on Request';
      if (mrpVal != null && Number(mrpVal) > 0) {
        mrp = `₹${Number(mrpVal).toLocaleString('en-IN', {minimumFractionDigits:2})}`;
      } else if (listVal != null && Number(listVal) > 0) {
        mrp = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits:2})}`;
      }

      let list = listVal != null && Number(listVal) > 0 ? `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits:2})}` : 'N/A';

      let html = `
        <div style="background: rgba(15, 23, 42, 0.95); border-radius: 12px; padding: 1.25rem; border: 1px solid rgba(56, 189, 248, 0.25); margin-bottom: 1.5rem;">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">Part Number</span>
              <strong style="font-size: 1.1rem; color: #38bdf8; font-family: monospace;">${this.escapeHtml(pNo)}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">Brand</span>
              <strong style="font-size: 1rem; color: #fbbf24;">${this.escapeHtml(brand)}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">MRP Price</span>
              <strong style="font-size: 1rem; color: #34d399;">${mrp}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">List Price</span>
              <strong style="font-size: 1rem; color: #cbd5e1;">${list}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">Tax Rate</span>
              <strong style="font-size: 1rem; color: #e2e8f0;">${taxRate != null && Number(taxRate) > 0 ? taxRate + '%' : 'N/A'}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">Segment / Aggregate</span>
              <strong style="font-size: 0.95rem; color: #a78bfa;">${this.escapeHtml(segment)} / ${this.escapeHtml(aggregate)}</strong>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.85rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.75rem;">
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">Sub-Aggregate</span>
              <strong style="font-size: 0.92rem; color: #38bdf8;">${this.escapeHtml(subAggregate || 'N/A')}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">Component</span>
              <strong style="font-size: 0.92rem; color: #ffffff;">${this.escapeHtml(component || 'N/A')}</strong>
            </div>
          </div>

          <div style="margin-top: 0.85rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.75rem;">
            <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 800; display: block;">Part Description</span>
            <div style="font-size: 0.92rem; color: #ffffff; font-weight: 600; margin-top: 0.2rem;">${this.escapeHtml(desc)}</div>
          </div>
        </div>

        <h4 style="font-size: 1rem; font-weight: 800; color: #38bdf8; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.4rem;">
          <span>🚗 Compatible Vehicle Applications (${fitments.length} Models)</span>
        </h4>

        <div style="max-height: 340px; overflow-y: auto; border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;">
          <table class="data-table" style="width: 100%;">
            <thead>
              <tr style="background: rgba(8, 15, 30, 0.95); position: sticky; top: 0;">
                <th>Vehicle Make</th>
                <th>Model</th>
                <th>Sub-Model / Variant</th>
                <th>Fuel Type</th>
                <th>Applicable Years</th>
                <th>Segment</th>
              </tr>
            </thead>
            <tbody>
              ${fitments.length === 0 ? `<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 1.5rem;">No specific vehicle mappings attached.</td></tr>` : 
                fitments.map(f => {
                  const fMake = f.make ?? '-';
                  const fModel = f.model ?? '-';
                  const fSubModel = f.subModel ?? f.sub_model ?? '-';
                  const fFuel = f.fuelType ?? f.fuel_type ?? '-';
                  let fYears = f.applicable_years || '';
                  if (!fYears && (f.fromYear || f.toYear)) {
                    fYears = `${f.fromYear || ''} - ${f.toYear || ''}`.trim();
                  }
                  if (!fYears) fYears = '-';
                  const fSegment = f.segment ?? '-';

                  return `
                    <tr>
                      <td style="font-weight: 850; color: #fbbf24;">${this.escapeHtml(fMake)}</td>
                      <td style="font-weight: 750; color: #ffffff;">${this.escapeHtml(fModel)}</td>
                      <td style="color: #cbd5e1;">${this.escapeHtml(fSubModel)}</td>
                      <td style="color: #38bdf8; font-weight: 700;">${this.escapeHtml(fFuel)}</td>
                      <td style="color: #34d399; font-weight: 700;">${this.escapeHtml(fYears)}</td>
                      <td style="color: #a78bfa;">${this.escapeHtml(fSegment)}</td>
                    </tr>
                  `;
                }).join('')
              }
            </tbody>
          </table>
        </div>
      `;

      modalBody.innerHTML = html;
    } catch (err) {
      console.error("Error displaying part details:", err);
      modalBody.innerHTML = `<div style="text-align: center; padding: 2rem; color: #f87171; font-weight: 700;">Failed to load part details. ${this.escapeHtml(err.message)}</div>`;
    }
  },

  closeModal() {
    const modal = document.getElementById('cat-part-modal');
    if (modal) modal.style.display = 'none';
  },

  exportCSV() {
    const params = new URLSearchParams();
    if (this.q) params.append('q', this.q);
    if (this.filters.brand) params.append('brand', this.filters.brand);
    if (this.filters.segment) params.append('segment', this.filters.segment);
    if (this.filters.make) params.append('make', this.filters.make);
    if (this.filters.model) params.append('model', this.filters.model);
    if (this.filters.sub_model) params.append('sub_model', this.filters.sub_model);
    if (this.filters.fuel_type) params.append('fuel_type', this.filters.fuel_type);
    if (this.filters.aggregate) params.append('aggregate', this.filters.aggregate);
    if (this.filters.sub_aggregate) params.append('sub_aggregate', this.filters.sub_aggregate);
    if (this.filters.component) params.append('component', this.filters.component);
    if (this.filters.min_price) params.append('min_price', this.filters.min_price);
    if (this.filters.max_price) params.append('max_price', this.filters.max_price);

    const exportUrl = `/api/overall-catalogue/export?${params.toString()}`;
    window.open(exportUrl, '_blank');
  },

  escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  escapeJs(str) {
    if (str == null) return '';
    return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  }
};
