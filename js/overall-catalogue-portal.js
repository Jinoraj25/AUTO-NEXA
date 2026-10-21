/* AUTO NEXA - AutoDukan Master Catalogue Intelligence Portal (23.6M+ Records) */

window.OverallCataloguePortal = {
  viewMode: 'grid', // 'grid' (AutoDukan Cards) or 'table' (Enterprise Grid)
  currentPage: 1,
  limit: 48,
  totalRecords: 0,
  totalPages: 1,
  searchDebounceTimer: null,
  suggestionDebounceTimer: null,
  filters: {
    brand: '',
    segment: '',
    make: 'TATA',
    model: 'INDICA',
    sub_model: 'INDICA VISTA 1.3L',
    fuel_type: 'DIESEL',
    year: '2010',
    aggregate: '',
    sub_aggregate: '',
    component: '',
    min_price: '',
    max_price: ''
  },
  q: '',
  orderType: 'vehicle', // 'stock' or 'vehicle'

  // Vehicle Registration Number Master Mappings (AUTO NEXA Fitment Database)
  vrnDb: {
    'TN22BK1405': { make: 'TATA', model: 'INDICA', sub_model: 'INDICA VISTA 1.3L', fuel: 'DIESEL', year: '2010', owner: 'Jino George' },
    'DL3CCP1234': { make: 'HYUNDAI', model: 'CRETA', sub_model: '1.6 CRDI', fuel: 'DIESEL', year: '2018', owner: 'Corporate Fleet' },
    'MH02CD5678': { make: 'MARUTI SUZUKI', model: 'SWIFT', sub_model: '1.2 VXI', fuel: 'PETROL', year: '2020', owner: 'AUTO NEXA Hub' },
    'KA03MG9999': { make: 'MAHINDRA', model: 'SCORPIO', sub_model: 'S11 2.2L', fuel: 'DIESEL', year: '2021', owner: 'Enterprise Logistics' },
    'TN09BZ4321': { make: 'TOYOTA', model: 'INNOVA CRYSTA', sub_model: '2.4 VX', fuel: 'DIESEL', year: '2019', owner: 'VIP Prime' }
  },

  async init() {
    console.log("⚡ Initializing Master Catalogue Portal (AUTO NEXA 23.6M+ DB)...");
    
    // Close suggestions dropdown when clicking outside
    document.addEventListener('click', (e) => {
      const searchBox = document.getElementById('cat-search-q');
      const dropdown = document.getElementById('cat-suggestions-dropdown');
      if (dropdown && searchBox) {
        if (!searchBox.contains(e.target) && !dropdown.contains(e.target)) {
          this.hideSuggestions();
        }
      }
    });

    await this.loadStats();
    await this.loadFilterOptions();
    await this.fetchData();
  },

  showCartToast() {
    if (window.App && window.App.showToast) {
      window.App.showToast("AUTO NEXA Order Staging: 1 Staged Item (TATA Indica Oil Filter SKU 21611404)", "info");
    } else {
      alert("AUTO NEXA Order Staging: 1 Staged Item");
    }
  },

  showOrdersToast() {
    if (window.App && window.App.showToast) {
      window.App.showToast("AUTO NEXA Dispatch Orders: 3 Active Work Orders processing.", "info");
    } else {
      alert("AUTO NEXA Dispatch Orders: 3 Active Work Orders");
    }
  },

  setOrderType(type) {
    this.orderType = type;
    const switchKnob = document.querySelector('.nexa-switch-knob, .dearo-switch-knob');
    const switchPill = document.getElementById('order-toggle-switch');
    const labelStock = document.getElementById('order-type-stock');
    const labelVehicle = document.getElementById('order-type-vehicle');

    if (type === 'vehicle') {
      if (switchKnob) switchKnob.style.transform = 'translateX(0)';
      if (switchPill) switchPill.style.background = '#2563eb';
      if (labelStock) labelStock.className = 'nexa-toggle-label-inactive dearo-toggle-label-inactive';
      if (labelVehicle) labelVehicle.className = 'nexa-toggle-label-active dearo-toggle-label-active';
      if (window.App && window.App.showToast) window.App.showToast("Order Mode: VEHICLE FITMENT ORDER (Linked to Job Card / Reg)", "info");
    } else {
      if (switchKnob) switchKnob.style.transform = 'translateX(-20px)';
      if (switchPill) switchPill.style.background = '#64748b';
      if (labelStock) labelStock.className = 'nexa-toggle-label-active dearo-toggle-label-active';
      if (labelVehicle) labelVehicle.className = 'nexa-toggle-label-inactive dearo-toggle-label-inactive';
      if (window.App && window.App.showToast) window.App.showToast("Order Mode: DIRECT STOCK ORDER (Bulk Replenishment)", "info");
    }
  },

  toggleOrderType() {
    this.setOrderType(this.orderType === 'vehicle' ? 'stock' : 'vehicle');
  },

  searchByRegNo() {
    const input = document.getElementById('vrn-search-input');
    if (!input) return;
    const cleanReg = input.value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    // Check known database or fallback to Tata Indica Vista
    const found = this.vrnDb[cleanReg] || {
      make: 'TATA',
      model: 'INDICA',
      sub_model: 'INDICA VISTA 1.3L',
      fuel: 'DIESEL',
      year: '2010'
    };

    input.value = cleanReg || 'TN22BK1405';

    // Update filters
    this.filters.make = found.make;
    this.filters.model = found.model;
    this.filters.sub_model = found.sub_model;
    this.filters.fuel_type = found.fuel;
    this.filters.year = found.year;

    // Update Pill chips in AUTO NEXA Fitment card
    this.updatePillChip('make', found.make);
    this.updatePillChip('model', found.model);
    this.updatePillChip('sub_model', found.sub_model);

    // Update dropdown select elements
    const fuelSel = document.getElementById('nexa-filter-fuel') || document.getElementById('dearo-filter-fuel');
    if (fuelSel) fuelSel.value = found.fuel;
    const yearSel = document.getElementById('nexa-filter-year') || document.getElementById('dearo-filter-year');
    if (yearSel) yearSel.value = found.year;

    if (window.App && window.App.showToast) {
      window.App.showToast(`Vehicle Identified: ${found.make} ${found.model} (${found.sub_model} ${found.year})`, "success");
    }

    this.currentPage = 1;
    this.fetchData();
  },

  applyRegNo(reg) {
    const input = document.getElementById('vrn-search-input');
    if (input) input.value = reg;
    this.searchByRegNo();
  },

  updatePillChip(field, val) {
    const containerKey = field === 'sub_model' ? 'variant' : field;
    const container = document.getElementById(`nexa-pill-${containerKey}-container`) ||
                      document.getElementById(`dearo-pill-${containerKey}-container`);
    if (!container) return;

    if (val) {
      container.innerHTML = `<span class="nexa-pill-chip">${this.escapeHtml(val)} <span class="nexa-pill-remove" onclick="event.stopPropagation(); OverallCataloguePortal.clearFitmentFilter('${field}')">✕</span></span>`;
    } else {
      let placeholder = field === 'make' ? 'Select Make' : (field === 'model' ? 'Select Model' : 'Select Variant');
      container.innerHTML = `<span style="color: #94a3b8; font-size: 0.88rem; font-weight: 600;">${placeholder}</span>`;
    }
  },

  clearFitmentFilter(field) {
    if (field === 'make') {
      this.filters.make = '';
      this.filters.model = '';
      this.filters.sub_model = '';
      this.updatePillChip('make', '');
      this.updatePillChip('model', '');
      this.updatePillChip('sub_model', '');
    } else if (field === 'model') {
      this.filters.model = '';
      this.filters.sub_model = '';
      this.updatePillChip('model', '');
      this.updatePillChip('sub_model', '');
    } else if (field === 'sub_model') {
      this.filters.sub_model = '';
      this.updatePillChip('sub_model', '');
    }
    this.currentPage = 1;
    this.fetchData();
  },

  clearAllFitmentFilters() {
    const vrnInput = document.getElementById('vrn-search-input');
    if (vrnInput) vrnInput.value = '';

    this.filters.make = '';
    this.filters.model = '';
    this.filters.sub_model = '';
    this.filters.fuel_type = '';
    this.filters.year = '';
    this.filters.aggregate = '';
    this.filters.sub_aggregate = '';
    this.filters.brand = '';
    this.filters.component = '';
    this.filters.min_price = '';
    this.filters.max_price = '';
    this.q = '';

    this.updatePillChip('make', '');
    this.updatePillChip('model', '');
    this.updatePillChip('sub_model', '');

    const fuelSel = document.getElementById('nexa-filter-fuel') || document.getElementById('dearo-filter-fuel');
    if (fuelSel) fuelSel.value = '';
    const yearSel = document.getElementById('nexa-filter-year') || document.getElementById('dearo-filter-year');
    if (yearSel) yearSel.value = '';
    const catSel = document.getElementById('nexa-filter-aggregate') || document.getElementById('dearo-filter-aggregate');
    if (catSel) catSel.value = '';
    const subCatSel = document.getElementById('nexa-filter-sub-aggregate') || document.getElementById('dearo-filter-sub-aggregate');
    if (subCatSel) subCatSel.value = '';
    const qInput = document.getElementById('cat-search-q');
    if (qInput) qInput.value = '';

    if (window.App && window.App.showToast) {
      window.App.showToast("All filters and vehicle registration cleared.", "info");
    }

    this.currentPage = 1;
    this.fetchData();
  },

  clearAllDearoFilters() {
    return this.clearAllFitmentFilters();
  },

  toggleDropdown(selectId) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.style.display = sel.style.display === 'none' ? 'block' : 'none';
  },

  onMakeSelectChange(val) {
    this.filters.make = val;
    this.updatePillChip('make', val);
    const sel = document.getElementById('cat-filter-make-select');
    if (sel) sel.style.display = 'none';
    this.handleMakeChange();
  },

  onModelSelectChange(val) {
    this.filters.model = val;
    this.updatePillChip('model', val);
    const sel = document.getElementById('cat-filter-model-select');
    if (sel) sel.style.display = 'none';
    this.handleModelChange();
  },

  onVariantSelectChange(val) {
    this.filters.sub_model = val;
    this.updatePillChip('sub_model', val);
    const sel = document.getElementById('cat-filter-variant-select');
    if (sel) sel.style.display = 'none';
    this.handleFilterChange();
  },

  onFuelSelectChange(val) {
    this.filters.fuel_type = val;
    this.handleFilterChange();
  },

  onYearSelectChange(val) {
    this.filters.year = val;
    this.handleFilterChange();
  },

  onAggregateSelectChange(val) {
    this.filters.aggregate = val;
    this.handleAggregateChange();
  },

  onSubAggregateSelectChange(val) {
    this.filters.sub_aggregate = val;
    this.handleFilterChange();
  },

  triggerExploreProducts() {
    this.currentPage = 1;
    this.fetchData();
    const resultsContainer = document.querySelector('.cat-recent-activity-card');
    if (resultsContainer) {
      resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    if (window.App && window.App.showToast) {
      window.App.showToast(`Exploring products for ${this.filters.make || 'All Makes'} ${this.filters.model || ''}`, "success");
    }
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
      const elTaxonomy = document.getElementById('cat-stat-taxonomy');

      const records = data.totalRecords ?? data.total_records ?? 23671472;
      const parts = data.totalParts ?? data.unique_parts ?? 416045;
      const brands = data.totalBrands ?? data.unique_brands ?? 170;
      const makes = data.totalMakes ?? data.unique_makes ?? 39;
      const models = data.totalModels ?? data.unique_models ?? 504;
      const aggregates = data.totalAggregates ?? data.unique_aggregates ?? 29;

      if (elRecords) elRecords.textContent = Number(records).toLocaleString('en-IN');
      if (elParts) elParts.textContent = Number(parts).toLocaleString('en-IN');
      if (elBrands) elBrands.textContent = `${Number(brands)}+ Brands`;
      if (elMakes) elMakes.textContent = `${makes} Makes • ${models} Models`;
      if (elTaxonomy) elTaxonomy.textContent = `${aggregates} Aggregates`;
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
      this.populateSelect('cat-filter-make-select', data.makes || [], 'Select Make');
      this.populateSelect('cat-filter-aggregate', data.aggregates || [], 'All Aggregates');
      this.populateSelect('nexa-filter-aggregate', data.aggregates || [], 'Select Categories');
      this.populateSelect('dearo-filter-aggregate', data.aggregates || [], 'Select Categories');
      this.populateSelect('cat-filter-sub-aggregate', data.sub_aggregates || [], 'All Sub-Aggregates');
      this.populateSelect('nexa-filter-sub-aggregate', data.sub_aggregates || [], 'Select Sub Categories');
      this.populateSelect('dearo-filter-sub-aggregate', data.sub_aggregates || [], 'Select Sub Categories');
      this.populateSelect('cat-filter-component', data.components || [], 'All Components');
    } catch (err) {
      console.error("Error loading filter options:", err);
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

  // ==================== AUTOCOMPLETE SUGGESTIONS & SEARCH ====================

  handleSearchInput(val) {
    const clearBtn = document.getElementById('cat-search-clear-btn');
    if (clearBtn) {
      clearBtn.style.display = val.trim().length > 0 ? 'inline-flex' : 'none';
    }

    if (this.suggestionDebounceTimer) clearTimeout(this.suggestionDebounceTimer);

    const query = val.trim();
    if (query.length < 2) {
      this.hideSuggestions();
      return;
    }

    this.suggestionDebounceTimer = setTimeout(async () => {
      await this.fetchSuggestions(query);
    }, 220);
  },

  async fetchSuggestions(query) {
    const dropdown = document.getElementById('cat-suggestions-dropdown');
    if (!dropdown) return;

    dropdown.innerHTML = `<div style="padding: 0.85rem; color: #0284c7; font-size: 0.82rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;"><span>⚡</span><span>Scanning 23.6M+ Catalogue Database for '${this.escapeHtml(query)}'...</span></div>`;
    dropdown.style.display = 'block';

    try {
      const res = await fetch(`/api/overall-catalogue/suggestions?q=${encodeURIComponent(query)}&limit=8`);
      if (!res.ok) throw new Error("Suggestion fetch failed");
      const data = await res.json();
      const suggestions = data.suggestions || [];

      if (suggestions.length === 0) {
        dropdown.innerHTML = `
          <div style="padding: 1rem; color: #64748b; font-size: 0.82rem; text-align: center;">
            No direct part match found for "<strong>${this.escapeHtml(query)}</strong>".<br>
            <span style="font-size: 0.75rem; color: #94a3b8;">Press Enter or click Search for fuzzy keyword exploration.</span>
          </div>
        `;
        return;
      }

      dropdown.innerHTML = `
        <div style="padding: 0.35rem 0.65rem 0.5rem; font-size: 0.72rem; font-weight: 850; color: #0284c7; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between;">
          <span>⚡ LIVE DB MATCHES (LINE CODE & RAW PART NUMBER)</span>
          <span style="color: #64748b;">${suggestions.length} Top Suggestions</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.25rem; margin-top: 0.35rem;">
          ${suggestions.map(s => {
            const pNo = s.partNo || '';
            const brand = s.brand || 'GENERIC';
            const desc = s.desc || '';
            const mrp = s.mrp && Number(s.mrp) > 0 ? `₹${Number(s.mrp).toLocaleString('en-IN')}` : '';
            const vehicle = [s.make, s.model].filter(Boolean).join(' ') || s.aggregate || '';
            const lineCode = s.lineCode || (pNo.length > 3 ? pNo.substring(0, 3) : '');

            return `
              <div onclick="OverallCataloguePortal.selectSuggestion('${this.escapeJs(pNo)}')" style="padding: 0.65rem 0.85rem; border-radius: 8px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background 0.15s; background: #ffffff;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">
                <div style="display: flex; align-items: center; gap: 0.75rem; min-width: 0;">
                  <span style="background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd; padding: 0.15rem 0.45rem; border-radius: 4px; font-family: monospace; font-size: 0.74rem; font-weight: 900; white-space: nowrap;">
                    ${this.escapeHtml(lineCode ? 'LC ' + lineCode : 'SKU')}
                  </span>
                  <div style="min-width: 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                      <strong style="color: #0f172a; font-family: monospace; font-size: 0.88rem; font-weight: 850;">${this.escapeHtml(pNo)}</strong>
                      <span style="background: #fef3c7; color: #b45309; border: 1px solid #fde68a; padding: 0.05rem 0.4rem; border-radius: 4px; font-size: 0.7rem; font-weight: 800;">${this.escapeHtml(brand)}</span>
                    </div>
                    <div style="color: #475569; font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 520px; margin-top: 0.15rem;">
                      ${this.escapeHtml(desc)}
                    </div>
                  </div>
                </div>
                <div style="text-align: right; margin-left: 1rem; flex-shrink: 0;">
                  ${mrp ? `<div style="color: #059669; font-weight: 900; font-size: 0.88rem; font-family: 'Outfit', sans-serif;">${mrp}</div>` : ''}
                  <div style="color: #64748b; font-size: 0.72rem; font-weight: 700;">${this.escapeHtml(vehicle)}</div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } catch (err) {
      console.error("Suggestions error:", err);
      dropdown.innerHTML = `<div style="padding: 0.75rem; color: #dc2626; font-size: 0.8rem;">⚠️ Failed to load suggestions from backend.</div>`;
    }
  },

  selectSuggestion(partNo) {
    const input = document.getElementById('cat-search-q');
    if (input) input.value = partNo;
    const clearBtn = document.getElementById('cat-search-clear-btn');
    if (clearBtn) clearBtn.style.display = 'inline-flex';
    this.hideSuggestions();
    this.q = partNo;
    this.currentPage = 1;
    this.fetchData();
  },

  hideSuggestions() {
    const dropdown = document.getElementById('cat-suggestions-dropdown');
    if (dropdown) dropdown.style.display = 'none';
  },

  triggerSearch() {
    const input = document.getElementById('cat-search-q');
    this.q = input ? input.value.trim() : '';
    this.hideSuggestions();
    this.currentPage = 1;
    this.fetchData();
  },

  clearSearchInput() {
    const input = document.getElementById('cat-search-q');
    if (input) input.value = '';
    const clearBtn = document.getElementById('cat-search-clear-btn');
    if (clearBtn) clearBtn.style.display = 'none';
    this.hideSuggestions();
    this.q = '';
    this.currentPage = 1;
    this.fetchData();
  },

  setQuickSearch(val) {
    const input = document.getElementById('cat-search-q');
    if (input) input.value = val;
    const clearBtn = document.getElementById('cat-search-clear-btn');
    if (clearBtn) clearBtn.style.display = 'inline-flex';
    this.hideSuggestions();
    this.q = val;
    this.currentPage = 1;
    this.fetchData();
  },

  // ==================== CASCADING FITMENT & TAXONOMY FILTERS ====================

  handleSegmentChange() {
    this.filters.segment = document.getElementById('cat-filter-segment')?.value || '';
    this.handleFilterChange();
  },

  async handleMakeChange() {
    const makeVal = document.getElementById('cat-filter-make')?.value || '';
    this.filters.make = makeVal;
    this.filters.model = '';
    this.filters.sub_model = '';

    const modelSel = document.getElementById('cat-filter-model');
    const subSel = document.getElementById('cat-filter-submodel');

    if (!makeVal) {
      if (modelSel) modelSel.innerHTML = `<option value="">All Vehicle Models</option>`;
      if (subSel) subSel.innerHTML = `<option value="">All Variants</option>`;
      this.handleFilterChange();
      return;
    }

    if (modelSel) {
      modelSel.innerHTML = `<option value="">Loading Models...</option>`;
    }

    try {
      const res = await fetch(`/api/overall-catalogue/models?make=${encodeURIComponent(makeVal)}`);
      if (res.ok) {
        const data = await res.json();
        const models = Array.isArray(data) ? data : (data.models || []);
        this.populateSelect('cat-filter-model', models, 'All Vehicle Models');
        this.populateSelect('cat-filter-model-select', models, 'Select Model');
      }
    } catch (err) {
      console.error("Error loading models for make:", err);
    }

    if (subSel) subSel.innerHTML = `<option value="">All Variants</option>`;
    const nexaVariantSel = document.getElementById('cat-filter-variant-select');
    if (nexaVariantSel) nexaVariantSel.innerHTML = `<option value="">Select Variant</option>`;
    this.handleFilterChange();
  },

  async handleModelChange() {
    const makeVal = this.filters.make || document.getElementById('cat-filter-make')?.value || '';
    const modelVal = document.getElementById('cat-filter-model')?.value || this.filters.model || '';
    this.filters.model = modelVal;
    this.filters.sub_model = '';

    const subSel = document.getElementById('cat-filter-submodel');

    if (!modelVal) {
      if (subSel) subSel.innerHTML = `<option value="">All Variants</option>`;
      this.handleFilterChange();
      return;
    }

    if (subSel) {
      subSel.innerHTML = `<option value="">Loading Variants...</option>`;
    }

    try {
      const res = await fetch(`/api/overall-catalogue/sub-models?make=${encodeURIComponent(makeVal)}&model=${encodeURIComponent(modelVal)}`);
      if (res.ok) {
        const data = await res.json();
        const subModels = data.sub_models || [];
        this.populateSelect('cat-filter-submodel', subModels, 'All Variants');
        this.populateSelect('cat-filter-variant-select', subModels, 'Select Variant');
      }
    } catch (err) {
      console.error("Error loading submodels:", err);
    }

    this.handleFilterChange();
  },

  handleSubModelChange() {
    this.filters.sub_model = document.getElementById('cat-filter-submodel')?.value || '';
    this.handleFilterChange();
  },

  handleFuelChange() {
    this.filters.fuel_type = document.getElementById('cat-filter-fuel')?.value || '';
    this.handleFilterChange();
  },

  handleYearChange() {
    this.filters.year = document.getElementById('cat-filter-year')?.value || '';
    this.handleFilterChange();
  },

  handleBrandChange() {
    this.filters.brand = document.getElementById('cat-filter-brand')?.value || '';
    this.handleFilterChange();
  },

  async handleAggregateChange() {
    const aggVal = document.getElementById('cat-filter-aggregate')?.value || '';
    this.filters.aggregate = aggVal;
    this.filters.sub_aggregate = '';
    this.filters.component = '';

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
    const aggVal = this.filters.aggregate || document.getElementById('cat-filter-aggregate')?.value || '';
    const subAggVal = document.getElementById('cat-filter-sub-aggregate')?.value || '';
    this.filters.sub_aggregate = subAggVal;
    this.filters.component = '';

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

  handleComponentChange() {
    this.filters.component = document.getElementById('cat-filter-component')?.value || '';
    this.handleFilterChange();
  },

  handlePriceChange() {
    this.filters.min_price = document.getElementById('cat-price-min')?.value || '';
    this.filters.max_price = document.getElementById('cat-price-max')?.value || '';
    this.handleFilterChange();
  },

  handleFilterChange() {
    this.currentPage = 1;
    this.renderActiveFilterChips();
    this.fetchData();
  },

  filterCategory(catName) {
    const aggSel = document.getElementById('cat-filter-aggregate');
    if (aggSel) {
      let matched = false;
      for (let opt of aggSel.options) {
        if (opt.value.toUpperCase().includes(catName) || catName.includes(opt.value.toUpperCase())) {
          aggSel.value = opt.value;
          this.filters.aggregate = opt.value;
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
        return;
      }
    }
    this.currentPage = 1;
    this.renderActiveFilterChips();
    this.fetchData();
  },

  // ==================== ACTIVE FILTER CHIPS ====================

  renderActiveFilterChips() {
    const container = document.getElementById('cat-active-chips-container');
    const list = document.getElementById('cat-active-chips-list');
    if (!container || !list) return;

    const chips = [];

    if (this.q) {
      chips.push({ key: 'q', label: `Search: "${this.q}"` });
    }
    if (this.filters.segment) {
      chips.push({ key: 'segment', label: `Segment: ${this.filters.segment}` });
    }
    if (this.filters.make) {
      chips.push({ key: 'make', label: `Make: ${this.filters.make}` });
    }
    if (this.filters.model) {
      chips.push({ key: 'model', label: `Model: ${this.filters.model}` });
    }
    if (this.filters.sub_model) {
      chips.push({ key: 'sub_model', label: `Variant: ${this.filters.sub_model}` });
    }
    if (this.filters.fuel_type) {
      chips.push({ key: 'fuel_type', label: `Fuel: ${this.filters.fuel_type}` });
    }
    if (this.filters.year) {
      chips.push({ key: 'year', label: `Year: ${this.filters.year}` });
    }
    if (this.filters.brand) {
      chips.push({ key: 'brand', label: `Brand: ${this.filters.brand}` });
    }
    if (this.filters.aggregate) {
      chips.push({ key: 'aggregate', label: `Category: ${this.filters.aggregate}` });
    }
    if (this.filters.sub_aggregate) {
      chips.push({ key: 'sub_aggregate', label: `Sub-Cat: ${this.filters.sub_aggregate}` });
    }
    if (this.filters.component) {
      chips.push({ key: 'component', label: `Component: ${this.filters.component}` });
    }
    if (this.filters.min_price || this.filters.max_price) {
      chips.push({ key: 'price', label: `Price: ₹${this.filters.min_price || 0} - ₹${this.filters.max_price || '∞'}` });
    }

    if (chips.length === 0) {
      container.style.display = 'none';
      list.innerHTML = '';
      return;
    }

    container.style.display = 'flex';
    list.innerHTML = chips.map(c => `
      <span style="display: inline-flex; align-items: center; gap: 0.35rem; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 6px; padding: 0.2rem 0.6rem; font-size: 0.76rem; font-weight: 750; color: #38bdf8;">
        <span>${this.escapeHtml(c.label)}</span>
        <button type="button" onclick="OverallCataloguePortal.removeFilter('${c.key}')" style="background: none; border: none; color: #f87171; cursor: pointer; font-size: 0.8rem; line-height: 1; padding: 0;">✕</button>
      </span>
    `).join('');
  },

  removeFilter(key) {
    if (key === 'q') {
      this.clearSearchInput();
      return;
    }
    if (key === 'price') {
      this.filters.min_price = '';
      this.filters.max_price = '';
      const minEl = document.getElementById('cat-price-min');
      const maxEl = document.getElementById('cat-price-max');
      if (minEl) minEl.value = '';
      if (maxEl) maxEl.value = '';
    } else {
      this.filters[key] = '';
      const mapElemId = {
        segment: 'cat-filter-segment',
        make: 'cat-filter-make',
        model: 'cat-filter-model',
        sub_model: 'cat-filter-submodel',
        fuel_type: 'cat-filter-fuel',
        year: 'cat-filter-year',
        brand: 'cat-filter-brand',
        aggregate: 'cat-filter-aggregate',
        sub_aggregate: 'cat-filter-sub-aggregate',
        component: 'cat-filter-component'
      };
      const el = document.getElementById(mapElemId[key]);
      if (el) el.value = '';
    }

    this.handleFilterChange();
  },

  resetFilters() {
    this.clearSearchInput();

    [
      'cat-filter-brand', 'cat-filter-segment', 'cat-filter-make', 'cat-filter-model',
      'cat-filter-submodel', 'cat-filter-fuel', 'cat-filter-year', 'cat-filter-aggregate',
      'cat-filter-sub-aggregate', 'cat-filter-component', 'cat-price-min', 'cat-price-max'
    ].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });

    const modelSel = document.getElementById('cat-filter-model');
    if (modelSel) modelSel.innerHTML = `<option value="">All Vehicle Models</option>`;
    const subSel = document.getElementById('cat-filter-submodel');
    if (subSel) subSel.innerHTML = `<option value="">All Variants</option>`;

    this.filters = {
      brand: '', segment: '', make: '', model: '', sub_model: '',
      fuel_type: '', year: '', aggregate: '', sub_aggregate: '', component: '',
      min_price: '', max_price: ''
    };

    this.currentPage = 1;
    this.renderActiveFilterChips();
    this.fetchData();
  },

  // ==================== VIEW MODES & DATA FETCHING ====================

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

  changeLimit(newLimit) {
    this.limit = parseInt(newLimit, 10) || 48;
    this.currentPage = 1;
    this.fetchData();
  },

  async fetchData() {
    const gridWrapper = document.getElementById('cat-grid-wrapper');
    const tbody = document.getElementById('cat-table-body');
    const countText = document.getElementById('cat-results-count-text');

    if (countText) {
      countText.textContent = "⚡ Querying 23.6M+ master database records...";
    }

    if (gridWrapper && this.viewMode === 'grid') {
      gridWrapper.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem; color: #38bdf8; font-weight: 700; font-size: 1.05rem;">
          <span style="font-size: 2rem; display: block; margin-bottom: 0.6rem;">⚡</span>
          Querying 23.6M+ Master Catalogue Database with FTS Indexation...
        </div>
      `;
    }
    if (tbody && this.viewMode === 'table') {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 3rem; color: #38bdf8; font-weight: 700;">⚡ Querying 23.6M+ Master Catalogue Database...</td></tr>`;
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
      if (this.filters.year) params.append('year', this.filters.year);
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

      if (countText) {
        if (this.totalRecords > 0) {
          countText.innerHTML = `Found <strong style="color: #38bdf8;">${this.totalRecords.toLocaleString('en-IN')}</strong> matching parts (Page ${this.currentPage} of ${this.totalPages.toLocaleString('en-IN')})`;
        } else {
          countText.textContent = "No catalogue parts match the applied criteria.";
        }
      }

      if (this.viewMode === 'grid') {
        this.renderGrid(items);
      } else {
        this.renderTable(items);
      }
      this.renderPagination();
    } catch (err) {
      console.error("Fetch catalogue data error:", err);
      if (countText) countText.textContent = "Error loading catalogue records.";
      if (gridWrapper) {
        gridWrapper.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 2.5rem; color: #f87171; font-weight: 700;">⚠️ Connection error querying catalogue database. Please ensure backend server is active.</div>`;
      }
    }
  },

  // ==================== CARD GRID VIEW ====================

  renderGrid(rows) {
    const gridWrapper = document.getElementById('cat-grid-wrapper');
    if (!gridWrapper) return;

    if (rows.length === 0) {
      gridWrapper.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem; color: #94a3b8; font-weight: 600;">
          <span style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem;">🔍</span>
          No catalogue parts found matching the selected query or filters.<br>
          <button type="button" onclick="OverallCataloguePortal.resetFilters()" style="margin-top: 1rem; padding: 0.6rem 1.25rem; background: #0284c7; border: none; border-radius: 8px; color: #fff; font-weight: 800; cursor: pointer;">
            🔄 Clear All Filters
          </button>
        </div>
      `;
      return;
    }

    gridWrapper.innerHTML = rows.map(r => {
      const partNo = r.partNo ?? r.part_number ?? '';
      const brand = r.brand ?? r.brand_name ?? 'GENERIC';
      const desc = r.desc ?? r.part_description ?? '';
      const listVal = r.listPrice ?? r.list_price;
      const mrpVal = r.mrp ?? r.mrp_price;
      const segment = r.segment ?? 'PCV';
      const make = r.make ?? '';
      const model = r.model ?? '';
      const subModel = r.subModel ?? r.sub_model ?? '';
      const aggregate = r.aggregate ?? r.aggregate_name ?? 'SPARE PART';
      const lineCode = r.lineCode ?? (partNo.length > 3 ? partNo.substring(0, 3) : '');

      let mrpPrice = 'Price on Request';
      if (mrpVal != null && Number(mrpVal) > 0) {
        mrpPrice = `₹${Number(mrpVal).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      } else if (listVal != null && Number(listVal) > 0) {
        mrpPrice = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      }

      const vehicleInfo = [make, model, subModel].filter(Boolean).join(' ') || 'Universal Fitment';

      // Pick system icon based on aggregate
      let sysIcon = '📦';
      const aggUpper = aggregate.toUpperCase();
      if (aggUpper.includes('BRAKE')) sysIcon = '🛑';
      else if (aggUpper.includes('ENGINE') || aggUpper.includes('TIMING')) sysIcon = '⚙️';
      else if (aggUpper.includes('SUSPENSION') || aggUpper.includes('STEERING')) sysIcon = '🛞';
      else if (aggUpper.includes('ELECTRICAL') || aggUpper.includes('RELAY')) sysIcon = '⚡';
      else if (aggUpper.includes('HVAC') || aggUpper.includes('COOLING')) sysIcon = '❄️';
      else if (aggUpper.includes('FILTER') || aggUpper.includes('LUB') || aggUpper.includes('OIL')) sysIcon = '🛢️';
      else if (aggUpper.includes('CLUTCH')) sysIcon = '🔄';
      else if (aggUpper.includes('BODY')) sysIcon = '🚗';

      return `
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.15rem; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s; position: relative; box-shadow: 0 2px 8px rgba(15,23,42,0.04);" onmouseover="this.style.borderColor='#cbd5e1'; this.style.boxShadow='0 8px 24px rgba(15,23,42,0.08)'; this.style.transform='translateY(-3px)'" onmouseout="this.style.borderColor='#e2e8f0'; this.style.boxShadow='0 2px 8px rgba(15,23,42,0.04)'; this.style.transform='none'">
          
          <div>
            <!-- Header Badges -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
              <div style="display: flex; align-items: center; gap: 0.4rem;">
                <span class="badge" style="background: #fef3c7; color: #b45309; border: 1px solid #fde68a; padding: 0.2rem 0.55rem; border-radius: 6px; font-size: 0.72rem; font-weight: 800;">
                  ${this.escapeHtml(brand)}
                </span>
                ${lineCode ? `<span style="background: #e0f2fe; color: #0284c7; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.68rem; font-family: monospace; font-weight: 800;">LC ${this.escapeHtml(lineCode)}</span>` : ''}
              </div>
              <span style="font-size: 1.35rem;" title="${this.escapeHtml(aggregate)}">${sysIcon}</span>
            </div>

            <!-- Part Number & Description -->
            <div style="font-family: monospace; font-size: 0.96rem; font-weight: 900; color: #0284c7; margin-bottom: 0.3rem; letter-spacing: -0.2px;">
              ${this.escapeHtml(partNo)}
            </div>
            <div style="font-size: 0.84rem; font-weight: 700; color: #0f172a; line-height: 1.35; height: 2.7em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 0.75rem;">
              ${this.escapeHtml(desc || aggregate)}
            </div>
          </div>

          <!-- Bottom: MRP Price, Fitment & Modal Trigger -->
          <div>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.6rem; margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.7rem; color: #64748b; font-weight: 800; text-transform: uppercase;">Catalogue MRP</span>
                <span style="font-size: 0.7rem; color: #7c3aed; font-weight: 800; background: #ede9fe; padding: 0.1rem 0.4rem; border-radius: 4px;">${this.escapeHtml(segment)}</span>
              </div>
              <div style="font-size: 1.25rem; font-weight: 900; color: #059669; font-family: 'Outfit', sans-serif; margin-top: 0.1rem;">
                ${mrpPrice}
              </div>
            </div>

            <div style="font-size: 0.75rem; color: #475569; margin-bottom: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 0.35rem;">
              <span>🚗</span>
              <strong style="color: #1e293b;">${this.escapeHtml(vehicleInfo)}</strong>
            </div>

            <button type="button" onclick="OverallCataloguePortal.showPartDetails('${this.escapeJs(partNo)}')" style="width: 100%; padding: 0.55rem; font-size: 0.8rem; font-weight: 850; background: #eff6ff; border: 1.5px solid #bfdbfe; color: #1d4ed8; border-radius: 8px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 0.4rem;" onmouseover="this.style.background='#2563eb'; this.style.color='#ffffff'; this.style.borderColor='#2563eb'" onmouseout="this.style.background='#eff6ff'; this.style.color='#1d4ed8'; this.style.borderColor='#bfdbfe'">
              <span>🔍</span> <span>Spec & Fitment List</span>
            </button>
          </div>

        </div>
      `;
    }).join('');
  },

  // ==================== ENTERPRISE TABLE VIEW ====================

  renderTable(rows) {
    const tbody = document.getElementById('cat-table-body');
    if (!tbody) return;

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 3rem; color: #94a3b8; font-weight: 600;">No catalogue parts found matching the selected query and filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = rows.map(r => {
      const partNo = r.partNo ?? r.part_number ?? '';
      const brand = r.brand ?? r.brand_name ?? 'GENERIC';
      const desc = r.desc ?? r.part_description ?? '';
      const listVal = r.listPrice ?? r.list_price;
      const mrpVal = r.mrp ?? r.mrp_price;
      const segment = r.segment ?? 'PCV';
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
        mrpPrice = `₹${Number(mrpVal).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      } else if (listVal != null && Number(listVal) > 0) {
        mrpPrice = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      }

      let listPrice = 'N/A';
      if (listVal != null && Number(listVal) > 0) {
        listPrice = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      }

      const vehicleInfo = [make, model, subModel].filter(Boolean).join(' ') || 'Universal / Multi-fit';
      const fuelYears = [fuelType, years].filter(Boolean).join(' | ');

      return `
        <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
          <td style="font-weight: 850; color: #0284c7; font-family: monospace; font-size: 0.88rem; padding: 0.85rem;">${this.escapeHtml(partNo)}</td>
          <td style="font-weight: 750; color: #b45309; font-size: 0.82rem; padding: 0.85rem;"><span class="badge" style="background: #fef3c7; color: #b45309; border: 1px solid #fde68a; padding: 0.2rem 0.5rem; border-radius: 6px;">${this.escapeHtml(brand)}</span></td>
          <td style="font-weight: 600; color: #1e293b; font-size: 0.82rem; max-width: 280px; white-space: normal; line-height: 1.35; padding: 0.85rem;">${this.escapeHtml(desc)}</td>
          <td style="font-weight: 850; color: #059669; font-size: 0.88rem; text-align: right; font-family: 'Outfit', sans-serif; padding: 0.85rem;">${mrpPrice}</td>
          <td style="font-weight: 600; color: #64748b; font-size: 0.8rem; text-align: right; padding: 0.85rem;">${listPrice}</td>
          <td style="font-weight: 700; color: #7c3aed; font-size: 0.8rem; padding: 0.85rem;"><span class="badge" style="background: #ede9fe; color: #7c3aed; border: 1px solid #ddd6fe; padding: 0.2rem 0.45rem; border-radius: 6px;">${this.escapeHtml(segment)}</span></td>
          <td style="font-size: 0.8rem; color: #334155; padding: 0.85rem;">
            <div style="font-weight: 750; color: #0f172a;">${this.escapeHtml(vehicleInfo)}</div>
            ${fuelYears ? `<div style="font-size: 0.72rem; color: #64748b; margin-top: 0.15rem;">${this.escapeHtml(fuelYears)}</div>` : ''}
          </td>
          <td style="font-weight: 700; color: #0284c7; font-size: 0.8rem; padding: 0.85rem;">${this.escapeHtml(aggregate)}</td>
          <td style="text-align: center; padding: 0.85rem;">
            <button type="button" class="btn btn-secondary" onclick="OverallCataloguePortal.showPartDetails('${this.escapeJs(partNo)}')" style="padding: 0.35rem 0.75rem; font-size: 0.76rem; font-weight: 800; background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; border-radius: 7px; cursor: pointer; display: inline-flex; align-items: center; gap: 0.3rem;">
              <span>🔍</span> <span>Fitment</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  },

  // ==================== PAGINATION ====================

  renderPagination() {
    const infoEl = document.getElementById('cat-pagination-info');
    const buttonsEl = document.getElementById('cat-pagination-buttons');

    const start = Math.min((this.currentPage - 1) * this.limit + 1, this.totalRecords);
    const end = Math.min(this.currentPage * this.limit, this.totalRecords);

    if (infoEl) {
      infoEl.textContent = `Showing ${start.toLocaleString('en-IN')} to ${end.toLocaleString('en-IN')} of ${this.totalRecords.toLocaleString('en-IN')} records`;
    }

    if (!buttonsEl) return;

    let html = '';
    const total = this.totalPages;
    const curr = this.currentPage;

    // Previous Button
    html += `<button type="button" class="btn btn-secondary" style="padding: 0.4rem 0.85rem; font-size: 0.78rem; font-weight: 800; border-radius: 7px; cursor: pointer;" ${curr <= 1 ? 'disabled' : ''} onclick="OverallCataloguePortal.goToPage(${curr - 1})">◀ Prev</button>`;

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
        html += `<span style="padding: 0.4rem 0.5rem; color: #64748b; font-size: 0.8rem;">...</span>`;
      } else {
        const isActive = p === curr;
        html += `<button type="button" class="btn ${isActive ? 'btn-primary' : 'btn-secondary'}" style="padding: 0.4rem 0.75rem; font-size: 0.78rem; font-weight: 850; border-radius: 7px; cursor: pointer; ${isActive ? 'background: #38bdf8; color: #0f172a;' : ''}" onclick="OverallCataloguePortal.goToPage(${p})">${p}</button>`;
      }
    });

    // Next Button
    html += `<button type="button" class="btn btn-secondary" style="padding: 0.4rem 0.85rem; font-size: 0.78rem; font-weight: 800; border-radius: 7px; cursor: pointer;" ${curr >= total ? 'disabled' : ''} onclick="OverallCataloguePortal.goToPage(${curr + 1})">Next ▶</button>`;

    buttonsEl.innerHTML = html;
  },

  goToPage(p) {
    if (p < 1 || p > this.totalPages) return;
    this.currentPage = p;
    this.fetchData();
  },

  // ==================== PART SPECIFICATIONS & FITMENT MODAL ====================

  async showPartDetails(partNo) {
    const modal = document.getElementById('cat-part-modal');
    const modalBody = document.getElementById('cat-modal-body');
    const modalTitle = document.getElementById('cat-modal-title');
    const modalSub = document.getElementById('cat-modal-subtitle');
    if (!modal || !modalBody) return;

    if (modalTitle) modalTitle.textContent = `Part Specifications: ${partNo}`;
    if (modalSub) modalSub.textContent = `Cross-Compatibility & Technical Specs`;

    modalBody.innerHTML = `<div style="text-align: center; padding: 3.5rem; color: #38bdf8; font-weight: 700; font-size: 1rem;"><span style="font-size: 1.8rem; display: block; margin-bottom: 0.5rem;">⚡</span>Loading part specifications & vehicle fitments from 23.6M DB...</div>`;
    modal.style.display = 'flex';

    try {
      const res = await fetch(`/api/overall-catalogue/part/${encodeURIComponent(partNo)}`);
      if (!res.ok) throw new Error("Part details not found");
      const data = await res.json();

      const spec = data.specifications || data.part || data || {};
      const fitments = data.fitments || data.compatibilities || [];

      const pNo = spec.partNo ?? spec.part_number ?? partNo;
      const brand = spec.brand ?? spec.brand_name ?? 'GENERIC';
      const desc = spec.desc ?? spec.part_description ?? '';
      const mrpVal = spec.mrp ?? spec.mrp_price;
      const listVal = spec.listPrice ?? spec.list_price;
      const segment = spec.segment ?? 'PCV';
      const aggregate = spec.aggregate ?? spec.aggregate_name ?? 'SPARE PART';
      const subAggregate = spec.subAggregate ?? spec.sub_aggregate ?? '';
      const component = spec.components ?? spec.component ?? '';

      let mrp = 'Price on Request';
      if (mrpVal != null && Number(mrpVal) > 0) {
        mrp = `₹${Number(mrpVal).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      } else if (listVal != null && Number(listVal) > 0) {
        mrp = `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      }

      let list = listVal != null && Number(listVal) > 0 ? `₹${Number(listVal).toLocaleString('en-IN', {minimumFractionDigits: 2})}` : 'N/A';

      modalBody.innerHTML = `
        <div style="background: #f8fafc; border-radius: 14px; padding: 1.35rem; border: 1px solid #e2e8f0; margin-bottom: 1.5rem;">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Part Number</span>
              <strong style="font-size: 1.15rem; color: #0284c7; font-family: monospace;">${this.escapeHtml(pNo)}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Brand Manufacturer</span>
              <strong style="font-size: 1.05rem; color: #b45309;">${this.escapeHtml(brand)}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Catalogue MRP</span>
              <strong style="font-size: 1.1rem; color: #059669; font-family: 'Outfit', sans-serif;">${mrp}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">List Price</span>
              <strong style="font-size: 1.05rem; color: #475569; font-family: 'Outfit', sans-serif;">${list}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Segment & Aggregate</span>
              <strong style="font-size: 0.95rem; color: #7c3aed;">${this.escapeHtml(segment)} • ${this.escapeHtml(aggregate)}</strong>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; border-top: 1px solid #e2e8f0; padding-top: 0.85rem;">
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Sub-Aggregate</span>
              <strong style="font-size: 0.92rem; color: #0284c7;">${this.escapeHtml(subAggregate || 'Standard')}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Component Category</span>
              <strong style="font-size: 0.92rem; color: #0f172a;">${this.escapeHtml(component || 'Direct Replacement')}</strong>
            </div>
          </div>

          <div style="margin-top: 1rem; border-top: 1px solid #e2e8f0; padding-top: 0.85rem;">
            <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Catalogue Description</span>
            <div style="font-size: 0.95rem; color: #0f172a; font-weight: 700; margin-top: 0.25rem;">${this.escapeHtml(desc || 'Genuine Multi-Brand Automotive Component')}</div>
          </div>
        </div>

        <h4 style="font-size: 1.05rem; font-weight: 900; color: #0f172a; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.45rem; font-family: 'Outfit', sans-serif;">
          <span>🚗 Compatible Vehicle Applications (${fitments.length} Mappings)</span>
        </h4>

        <div style="max-height: 360px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 12px;">
          <table class="data-table" style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr style="background: #f8fafc; position: sticky; top: 0; z-index: 2; border-bottom: 1px solid #e2e8f0;">
                <th style="padding: 0.75rem; text-align: left; color: #b45309; font-weight: 850;">Vehicle Make</th>
                <th style="padding: 0.75rem; text-align: left; color: #0f172a; font-weight: 850;">Model</th>
                <th style="padding: 0.75rem; text-align: left; color: #475569; font-weight: 850;">Sub-Model / Variant</th>
                <th style="padding: 0.75rem; text-align: left; color: #0284c7; font-weight: 850;">Fuel Type</th>
                <th style="padding: 0.75rem; text-align: left; color: #059669; font-weight: 850;">Applicable Years</th>
                <th style="padding: 0.75rem; text-align: left; color: #7c3aed; font-weight: 850;">Segment</th>
              </tr>
            </thead>
            <tbody>
              ${fitments.length === 0 ? `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 2rem;">Universal OEM / Multi-Fit Component (Compatible with listed makes & aggregates).</td></tr>` : 
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
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                      <td style="font-weight: 850; color: #b45309; padding: 0.75rem;">${this.escapeHtml(fMake)}</td>
                      <td style="font-weight: 800; color: #0f172a; padding: 0.75rem;">${this.escapeHtml(fModel)}</td>
                      <td style="color: #475569; padding: 0.75rem;">${this.escapeHtml(fSubModel)}</td>
                      <td style="color: #0284c7; font-weight: 750; padding: 0.75rem;">${this.escapeHtml(fFuel)}</td>
                      <td style="color: #059669; font-weight: 800; padding: 0.75rem;">${this.escapeHtml(fYears)}</td>
                      <td style="color: #7c3aed; font-weight: 750; padding: 0.75rem;">${this.escapeHtml(fSegment)}</td>
                    </tr>
                  `;
                }).join('')
              }
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      console.error("Error displaying part details:", err);
      modalBody.innerHTML = `<div style="text-align: center; padding: 2.5rem; color: #f87171; font-weight: 700;">⚠️ Failed to load part details. ${this.escapeHtml(err.message)}</div>`;
    }
  },

  closeModal() {
    const modal = document.getElementById('cat-part-modal');
    if (modal) modal.style.display = 'none';
  },

  // ==================== EXPORTS (EXCEL & CSV) ====================

  async exportExcel() {
    if (window.App && window.App.showToast) {
      window.App.showToast("Preparing Master Catalogue Excel export...", "info");
    }

    try {
      const params = new URLSearchParams({
        page: 1,
        limit: 500
      });
      if (this.q) params.append('q', this.q);
      if (this.filters.brand) params.append('brand', this.filters.brand);
      if (this.filters.segment) params.append('segment', this.filters.segment);
      if (this.filters.make) params.append('make', this.filters.make);
      if (this.filters.model) params.append('model', this.filters.model);
      if (this.filters.sub_model) params.append('sub_model', this.filters.sub_model);
      if (this.filters.fuel_type) params.append('fuel_type', this.filters.fuel_type);
      if (this.filters.year) params.append('year', this.filters.year);
      if (this.filters.aggregate) params.append('aggregate', this.filters.aggregate);
      if (this.filters.sub_aggregate) params.append('sub_aggregate', this.filters.sub_aggregate);
      if (this.filters.component) params.append('component', this.filters.component);
      if (this.filters.min_price) params.append('min_price', this.filters.min_price);
      if (this.filters.max_price) params.append('max_price', this.filters.max_price);

      const res = await fetch(`/api/overall-catalogue/search?${params.toString()}`);
      if (!res.ok) throw new Error("Export search failed");
      const data = await res.json();
      const items = data.items || data.results || [];

      if (items.length === 0) {
        alert("No records to export with current filters.");
        return;
      }

      if (typeof XLSX !== 'undefined') {
        const rows = items.map(r => ({
          "Part Number": r.partNo ?? r.part_number ?? '',
          "Line Code": r.lineCode ?? '',
          "Brand": r.brand ?? r.brand_name ?? '',
          "Description": r.desc ?? r.part_description ?? '',
          "MRP Price (INR)": r.mrp ?? r.mrp_price ?? 0,
          "List Price (INR)": r.listPrice ?? r.list_price ?? 0,
          "Segment": r.segment ?? '',
          "Vehicle Make": r.make ?? '',
          "Vehicle Model": r.model ?? '',
          "Sub Model / Variant": r.subModel ?? r.sub_model ?? '',
          "Aggregate": r.aggregate ?? r.aggregate_name ?? '',
          "Sub-Aggregate": r.subAggregate ?? r.sub_aggregate ?? '',
          "Component": r.component ?? r.components ?? ''
        }));

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(rows);
        XLSX.utils.book_append_sheet(wb, ws, "Master Catalogue");
        XLSX.writeFile(wb, `AUTO_NEXA_Master_Catalogue_${Date.now()}.xlsx`);

        if (window.App && window.App.showToast) {
          window.App.showToast(`Exported ${items.length} catalogue records to Excel!`, "success");
        }
      } else {
        this.exportCSV();
      }
    } catch (err) {
      console.error("Excel export error:", err);
      this.exportCSV();
    }
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
    if (this.filters.year) params.append('year', this.filters.year);
    if (this.filters.aggregate) params.append('aggregate', this.filters.aggregate);
    if (this.filters.sub_aggregate) params.append('sub_aggregate', this.filters.sub_aggregate);
    if (this.filters.component) params.append('component', this.filters.component);
    if (this.filters.min_price) params.append('min_price', this.filters.min_price);
    if (this.filters.max_price) params.append('max_price', this.filters.max_price);

    const exportUrl = `/api/overall-catalogue/export?${params.toString()}`;
    window.open(exportUrl, '_blank');
  },

  // ==================== UTILITY ESCAPERS ====================

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
