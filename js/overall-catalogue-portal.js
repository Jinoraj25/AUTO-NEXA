/* AUTO NEXA - Master Catalogue Intelligence Portal (23.6M+ Records) */

window.OverallCataloguePortal = {
  AGGREGATE_ICONS: {
    'ENGINE': '⚙️',
    'TRANSMISSION': '🔄',
    'CLUTCH SYSTEM': '⚙️',
    'SUSPENSION': '🔩',
    'BRAKE SYSTEM': '🛑',
    'STEERING': '🎯',
    'HVAC/THERMAL': '❄️',
    'FILTERS': '🛢️',
    'ELECTRICALS AND ELECTRONICS': '⚡',
    'BATTERY': '🔋',
    'WIPER SYSTEM': '🌧️',
    'GLASS': '🪟',
    'HORNS': '📢',
    'BELTS AND TENSIONER': '🎗️',
    'BODY PARTS': '🚗',
    'WHEELS AND TYRES': '🛞',
    'FUEL SYSTEM': '⛽',
    'EXHAUST SYSTEM': '💨',
    'BEARING': '🔘',
    'LUBES': '🛢️',
    'CABLES AND WIRES': '🔌',
    'FLUIDS COOLANT AND GREASE': '🧪',
    'INTERIOR AND COMFORTS': '🛋️',
    'PAINTS AND CONSUMABLES': '🎨',
    'RUBBERS HOSES AND MOUNTINGS': '🩹',
    'ACCESSORIES': '✨'
  },
  viewMode: 'grid', // 'grid' (Cards) or 'table' (Enterprise Grid)
  currentPage: 1,
  limit: 48,
  totalRecords: 0,
  totalPages: 1,
  searchDebounceTimer: null,
  suggestionDebounceTimer: null,
  variantFilterDebounceTimer: null,
  
  // Visual Navigator State
  visualCurrentStep: 1,
  visualMakes: [],
  visualModelsList: [],
  selectedMake: null,
  selectedModel: null,
  selectedVariant: null,
  selectedVariantFuel: null,
  selectedVariantYears: null,
  selectedVariantImage: null,
  selectedAggregate: null,
  selectedSubAggregate: null,
  selectedComponent: null,
  componentViewMode: 'cards',
  lastLoadedComponents: [],

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
  orderType: 'vehicle', // 'stock' or 'vehicle'

  // Vehicle Registration Number Master Mappings (AUTO NEXA Fitment Database)
  vrnDb: {
    'TN22BK1405': { make: 'TATA', model: 'INDICA', sub_model: 'INDICA VISTA 1.3L', fuel: 'DIESEL', year: '2010' },
    'DL3CCP1234': { make: 'HYUNDAI', model: 'CRETA', sub_model: '1.6 CRDI', fuel: 'DIESEL', year: '2018' },
    'MH02CD5678': { make: 'MARUTI SUZUKI', model: 'SWIFT', sub_model: '1.2 VXI', fuel: 'PETROL', year: '2020' },
    'KA03MG9999': { make: 'MAHINDRA', model: 'SCORPIO', sub_model: 'S11 2.2L', fuel: 'DIESEL', year: '2021' },
    'TN09BZ4321': { make: 'TOYOTA', model: 'INNOVA CRYSTA', sub_model: '2.4 VX', fuel: 'DIESEL', year: '2019' }
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

    this.loadStats();
    this.initCharts();
    await this.initVisualNavigator();
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
    
    // Check 17-digit VIN / Chassis Decoder
    let vinDecoded = null;
    if (cleanReg.length === 17) {
      const wmi = cleanReg.substring(0, 3);
      const yrCode = cleanReg.charAt(9);
      const WMI_MAP = {
        'MA3': { make: 'MARUTI SUZUKI', model: 'SWIFT' },
        'MAL': { make: 'HYUNDAI', model: 'GRAND I10 NIOS' },
        'MAT': { make: 'TATA', model: 'INDICA' },
        'MA1': { make: 'MAHINDRA', model: 'SCORPIO' },
        'MAK': { make: 'HONDA', model: 'CITY' },
        'MBJ': { make: 'TOYOTA', model: 'INNOVA CRYSTA' },
        'MAJ': { make: 'FORD', model: 'ECOSPORT' },
        'MEE': { make: 'RENAULT', model: 'KWID' },
        'MEX': { make: 'VOLKSWAGEN', model: 'POLO' },
        'MDH': { make: 'KIA', model: 'SELTOS' }
      };
      const YR_MAP = {
        'A':'2010', 'B':'2011', 'C':'2012', 'D':'2013', 'E':'2014', 'F':'2015',
        'G':'2016', 'H':'2017', 'J':'2018', 'K':'2019', 'L':'2020', 'M':'2021',
        'N':'2022', 'P':'2023', 'R':'2024', 'S':'2025', 'T':'2026'
      };
      if (WMI_MAP[wmi]) {
        vinDecoded = {
          make: WMI_MAP[wmi].make,
          model: WMI_MAP[wmi].model,
          sub_model: WMI_MAP[wmi].model,
          fuel: 'PETROL',
          year: YR_MAP[yrCode] || '2020'
        };
      }
    }

    // Check known database or VIN decode
    const found = vinDecoded || this.vrnDb[cleanReg];
    if (!found) {
      if (window.App && window.App.showToast) {
        window.App.showToast("Vehicle not found for this registration number", "error");
      } else {
        alert("Vehicle not found for this registration number");
      }
      return;
    }

    input.value = cleanReg;

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

  // ==================== VISUAL VEHICLE & ASSEMBLY NAVIGATOR ====================

  async initVisualNavigator() {
    try {
      const res = await fetch('/api/overall-catalogue/makes-catalog');
      if (res.ok) {
        const data = await res.json();
        this.visualMakes = Array.isArray(data) ? data : (data.makes || []);
        this.renderMakesGrid(this.visualMakes);
      }
    } catch (err) {
      console.error("Error loading visual makes:", err);
    }
  },

  renderMakesGrid(makesList) {
    const grid = document.getElementById('v-makes-grid');
    if (!grid) return;
    
    if (!makesList || makesList.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 2.5rem; color: #64748b;">No vehicle makes match the search query.</div>`;
      return;
    }
    
    grid.innerHTML = makesList.map(m => {
      const isSelected = this.selectedMake === m.make;
      const logoUrl = m.logo || 'images/brand_others.svg';
      const modelCount = m.modelsCount || m.models_count || 12;
      const variantCount = m.variantsCount || m.variants_count || 150;
      
      return `
        <div class="visual-make-card ${isSelected ? 'selected' : ''}" onclick="OverallCataloguePortal.selectMakeVisual('${this.escapeJs(m.make)}')">
          <img class="visual-make-logo" src="${logoUrl}" alt="${this.escapeHtml(m.displayName)}" onerror="this.onerror=null; this.src='images/brand_others.svg'">
          <div class="visual-make-name">${this.escapeHtml(m.displayName)}</div>
          <div class="visual-make-count">${modelCount} Models • ${variantCount.toLocaleString('en-IN')} Variants</div>
        </div>
      `;
    }).join('');
    
    const countBadge = document.getElementById('v-makes-total-badge');
    if (countBadge) {
      countBadge.textContent = `${makesList.length} Makes Live`;
    }
  },

  filterMakesGrid(searchVal) {
    const q = (searchVal || '').trim().toUpperCase();
    if (!q) {
      this.renderMakesGrid(this.visualMakes);
      return;
    }
    const filtered = this.visualMakes.filter(m => 
      m.make.toUpperCase().includes(q) || 
      (m.displayName && m.displayName.toUpperCase().includes(q))
    );
    this.renderMakesGrid(filtered);
  },

  filterMakeCategory(cat, btn) {
    document.querySelectorAll('#v-nav-step-1 .chip').forEach(c => c.classList.remove('active'));
    if (btn) btn.classList.add('active');
    
    if (cat === 'all') {
      this.renderMakesGrid(this.visualMakes);
    } else if (cat === 'popular') {
      this.renderMakesGrid(this.visualMakes.filter(m => m.popular));
    } else if (cat === 'SUV/LCV') {
      this.renderMakesGrid(this.visualMakes.filter(m => (m.segment || '').includes('SUV') || (m.segment || '').includes('LCV') || (m.segment || '').includes('HCV') || m.make === 'MAHINDRA' || m.make === 'TATA' || m.make === 'FORCE'));
    } else if (cat === 'Luxury') {
      this.renderMakesGrid(this.visualMakes.filter(m => m.segment === 'Luxury' || ['BMW', 'MERCEDES-BENZ', 'AUDI', 'VOLVO', 'JEEP'].includes(m.make)));
    }
  },

  async selectMakeVisual(makeName) {
    this.selectedMake = makeName;
    this.selectedModel = null;
    this.selectedVariant = null;
    
    // Update Step 2 (Model Selection) Header
    const makeObj = this.visualMakes.find(m => m.make === makeName) || { displayName: makeName, logo: 'images/brand_others.svg' };
    const step2Name = document.getElementById('v-step2-make-name');
    const step2Logo = document.getElementById('v-step2-make-logo');
    if (step2Name) step2Name.textContent = makeObj.displayName || makeName;
    if (step2Logo) step2Logo.src = makeObj.logo || 'images/brand_others.svg';

    const stepLabel2 = document.getElementById('v-step-label-2');
    if (stepLabel2) stepLabel2.textContent = 'Select Model';
    const stepLabel3 = document.getElementById('v-step-label-3');
    if (stepLabel3) stepLabel3.textContent = 'Choose Variant';
    
    const modelSearchInp = document.getElementById('v-model-search-input');
    if (modelSearchInp) modelSearchInp.value = '';

    // Step navigation to Step 2 (Select Model)
    this.navGoToStep(2);
    
    // Load models for this make
    await this.loadVisualModels(makeName);
  },

  async loadVisualModels(makeName) {
    if (!makeName) return;
    const grid = document.getElementById('v-models-grid');
    const countEl = document.getElementById('v-step2-models-count');
    
    if (grid) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #0284c7; font-weight: 700;">⚡ Loading vehicle models for ${this.escapeHtml(makeName)}...</div>`;
    }
    
    try {
      const res = await fetch(`/api/overall-catalogue/visual-variants?make=${encodeURIComponent(makeName)}&limit=150`);
      if (!res.ok) throw new Error("Models fetch failed");
      const data = await res.json();
      
      if (data.modelsMeta && data.modelsMeta.length > 0) {
        this.visualModelsList = data.modelsMeta.sort((a,b) => a.name.localeCompare(b.name));
      } else {
        const variants = data.variants || [];
        const models = data.models || [];
        
        const modelMap = {};
        variants.forEach(v => {
          const m = v.model || 'Other';
          if (!modelMap[m]) {
            modelMap[m] = {
              name: m,
              image: v.image || 'images/brand_others.svg',
              variantCount: 0,
              fuels: new Set(),
              minYear: 9999,
              maxYear: 0
            };
          }
          modelMap[m].variantCount++;
          if (v.fuelType) modelMap[m].fuels.add(v.fuelType);
        });

        models.forEach(m => {
          if (!modelMap[m]) {
            modelMap[m] = {
              name: m,
              image: 'images/brand_others.svg',
              variantCount: 1,
              fuels: new Set(),
              minYear: 9999,
              maxYear: 0
            };
          }
        });
        
        this.visualModelsList = Object.values(modelMap).sort((a,b) => a.name.localeCompare(b.name));
      }
      
      if (countEl) {
        countEl.textContent = `${this.visualModelsList.length} Models Available`;
      }
      
      this.renderModelsGrid(this.visualModelsList);
    } catch (err) {
      console.error("Error loading visual models:", err);
      if (grid) {
        grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 2.5rem; color: #f87171;">⚠️ Failed to load vehicle models: ${this.escapeHtml(err.message)}</div>`;
      }
    }
  },

  renderModelsGrid(modelsList) {
    const grid = document.getElementById('v-models-grid');
    if (!grid) return;
    
    if (!modelsList || modelsList.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #64748b;">No models match the search query.</div>`;
      return;
    }
    
    grid.innerHTML = modelsList.map(m => {
      const isSelected = this.selectedModel === m.name;
      const imgUrl = (m.image || '').trim();
      const fuelsArr = Array.from(m.fuels || []).filter(Boolean);
      const fuelsText = fuelsArr.length > 0 ? fuelsArr.slice(0, 2).join(' / ') : 'Multi-Fuel';
      
      const thumbHtml = imgUrl ? `
        <img class="visual-model-thumb" src="${imgUrl}" alt="${this.escapeHtml(m.name)}" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';">
        <div class="visual-model-thumb-blank" style="display: none; height: 110px; width: 100%; background: #f8fafc; border-radius: 8px; margin-bottom: 0.5rem; align-items: center; justify-content: center; border: 1px dashed #cbd5e1;">
          <span style="color: #94a3b8; font-size: 0.72rem; font-weight: 700;">No photo available</span>
        </div>
      ` : `
        <div class="visual-model-thumb-blank" style="height: 110px; width: 100%; background: #f8fafc; border-radius: 8px; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: center; border: 1px dashed #cbd5e1;">
          <span style="color: #94a3b8; font-size: 0.72rem; font-weight: 700;">No photo available</span>
        </div>
      `;

      return `
        <div class="visual-model-card ${isSelected ? 'selected' : ''}" onclick="OverallCataloguePortal.selectVisualModel('${this.escapeJs(m.name)}')">
          ${thumbHtml}
          <div>
            <div class="visual-model-name" title="${this.escapeHtml(m.name)}">${this.escapeHtml(m.name)}</div>
            <div class="visual-model-meta">
              <span class="badge" style="background: #eff6ff; color: #0284c7; border: 1px solid #bfdbfe; font-size: 0.68rem; font-weight: 800; border-radius: 4px; padding: 0.1rem 0.45rem;">${m.variantCount} Variant${m.variantCount === 1 ? '' : 's'}</span>
              <span style="font-size: 0.68rem; color: #64748b; font-weight: 700;">${this.escapeHtml(fuelsText)}</span>
            </div>
            <div style="font-size: 0.72rem; color: #0284c7; font-weight: 800; margin-top: 0.5rem; display: flex; align-items: center; justify-content: center; gap: 0.3rem;">
              <span>Select Model</span> <span>➔</span>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  filterModelsGrid(searchVal) {
    const q = (searchVal || '').trim().toUpperCase();
    if (!q) {
      this.renderModelsGrid(this.visualModelsList || []);
      return;
    }
    const filtered = (this.visualModelsList || []).filter(m => m.name.toUpperCase().includes(q));
    this.renderModelsGrid(filtered);
  },

  async selectVisualModel(modelName) {
    this.selectedModel = modelName;
    this.selectedVariant = null;
    
    // Update Step 3 Header
    const makeObj = this.visualMakes.find(m => m.make === this.selectedMake) || { displayName: this.selectedMake, logo: 'images/brand_others.svg' };
    const nameEl = document.getElementById('v-active-make-name');
    const logoEl = document.getElementById('v-active-make-logo');
    if (nameEl) nameEl.textContent = `${makeObj.displayName || this.selectedMake} • ${modelName}`;
    if (logoEl) logoEl.src = makeObj.logo || 'images/brand_others.svg';
    
    const stepLabel2 = document.getElementById('v-step-label-2');
    if (stepLabel2) stepLabel2.textContent = modelName;
    const stepLabel3 = document.getElementById('v-step-label-3');
    if (stepLabel3) stepLabel3.textContent = 'Choose Variant';

    // Reset filters in Step 3
    const fuelSel = document.getElementById('v-filter-fuel');
    const yrSel = document.getElementById('v-filter-year');
    const searchInp = document.getElementById('v-filter-search');
    if (fuelSel) fuelSel.value = '';
    if (yrSel) yrSel.value = '';
    if (searchInp) searchInp.value = '';
    
    // Step navigation to Step 3 (Choose Variant)
    this.navGoToStep(3);
    
    // Load variants for this model
    await this.loadVisualVariants();
  },

  async loadVisualVariants() {
    if (!this.selectedMake) return;
    const grid = document.getElementById('v-variants-grid');
    const countEl = document.getElementById('v-active-variants-count');
    const pillsWrap = document.getElementById('v-model-pills-wrap');
    
    if (grid) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #0284c7; font-weight: 700;">⚡ Loading variants for ${this.escapeHtml(this.selectedMake)}...</div>`;
    }
    
    const fuel = document.getElementById('v-filter-fuel')?.value || '';
    const year = document.getElementById('v-filter-year')?.value || '';
    const q = document.getElementById('v-filter-search')?.value || '';
    
    try {
      const params = new URLSearchParams({
        make: this.selectedMake,
        limit: 150
      });
      if (this.selectedModel) params.append('model', this.selectedModel);
      if (fuel) params.append('fuel_type', fuel);
      if (year) params.append('year', year);
      if (q) params.append('search', q);
      
      const res = await fetch(`/api/overall-catalogue/visual-variants?${params.toString()}`);
      if (!res.ok) throw new Error("Variant fetch failed");
      const data = await res.json();
      
      const variants = data.variants || [];
      const models = data.models || [];
      const availableFuels = data.availableFuels || [];
      const availableYears = data.availableYears || [];
      
      if (countEl) {
        countEl.textContent = `${variants.length} Variants Available`;
      }

      // Fetch live strict filter options from DB for selected vehicle
      try {
        const foParams = new URLSearchParams();
        if (this.selectedMake) foParams.append('make', this.selectedMake);
        if (this.selectedModel) foParams.append('model', this.selectedModel);
        if (this.selectedVariant) foParams.append('sub_model', this.selectedVariant);
        if (fuel) foParams.append('fuel', fuel);
        if (year) foParams.append('year', year);
        const foRes = await fetch(`/api/overall-catalogue/filter-options?${foParams.toString()}`);
        if (foRes.ok) {
          const foData = await foRes.json();
          const dbFuels = foData.fuels || [];
          const dbYears = foData.years || [];

          const fuelSel = document.getElementById('v-filter-fuel');
          if (fuelSel) {
            const curFuel = fuelSel.value;
            // If user hasn't selected a fuel, or if year filtered fuels, rebuild fuel options cleanly
            if (!fuel || year) {
              let fuelOpts = `<option value="">All Fuels</option>`;
              dbFuels.forEach(f => {
                const isSel = (curFuel.toUpperCase() === f.toUpperCase()) ? 'selected' : '';
                fuelOpts += `<option value="${this.escapeHtml(f)}" ${isSel}>${this.escapeHtml(f)}</option>`;
              });
              fuelSel.innerHTML = fuelOpts;
              if (curFuel && !dbFuels.some(f => f.toUpperCase() === curFuel.toUpperCase())) {
                fuelSel.value = '';
              }
            }
          }

          const yrSel = document.getElementById('v-filter-year');
          if (yrSel) {
            const curYr = yrSel.value;
            // Always rebuild year options based on strict valid years for this model and fuel
            let yrOpts = `<option value="">All Years</option>`;
            dbYears.forEach(y => {
              const isSel = (curYr === y) ? 'selected' : '';
              yrOpts += `<option value="${this.escapeHtml(y)}" ${isSel}>${this.escapeHtml(y)}</option>`;
            });
            yrSel.innerHTML = yrOpts;
            if (curYr && !dbYears.includes(curYr)) {
              yrSel.value = '';
            }
          }
        }
      } catch (errFo) {
        console.warn("Could not load dynamic filter options:", errFo);
      }
      
      // Render Model Pills
      if (pillsWrap && models.length > 0) {
        let pillsHtml = `
          <button type="button" class="chip ${!this.selectedModel ? 'active' : ''}" onclick="OverallCataloguePortal.filterByModelPill('', this)" style="padding: 0.35rem 0.8rem; font-size: 0.74rem; font-weight: 800; border-radius: 6px; cursor: pointer; white-space: nowrap;">
            All Models (${models.length})
          </button>
        `;
        models.forEach(md => {
          const isActive = this.selectedModel === md;
          pillsHtml += `
            <button type="button" class="chip ${isActive ? 'active' : ''}" onclick="OverallCataloguePortal.filterByModelPill('${this.escapeJs(md)}', this)" style="padding: 0.35rem 0.8rem; font-size: 0.74rem; font-weight: 800; border-radius: 6px; cursor: pointer; white-space: nowrap;">
              ${this.escapeHtml(md)}
            </button>
          `;
        });
        pillsWrap.innerHTML = pillsHtml;
      }
      
      this.renderVisualVariants(variants);
    } catch (err) {
      console.error("Error loading visual variants:", err);
      if (grid) {
        grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 2.5rem; color: #f87171;">⚠️ Failed to load vehicle variants: ${this.escapeHtml(err.message)}</div>`;
      }
    }
  },

  onFuelFilterSelect() {
    // When fuel changes, reset year to cascade strictly
    const yrSel = document.getElementById('v-filter-year');
    if (yrSel) yrSel.value = '';
    return this.loadVisualVariants();
  },

  onYearFilterSelect() {
    return this.loadVisualVariants();
  },

  renderVisualVariants(variants) {
    const grid = document.getElementById('v-variants-grid');
    if (!grid) return;
    
    if (variants.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem; color: #64748b;">
          <span style="font-size: 2.2rem; display: block; margin-bottom: 0.5rem;">🚗</span>
          No vehicle variants found for the selected combination of Fuel (${document.getElementById('v-filter-fuel')?.value || 'Any'}) and Year (${document.getElementById('v-filter-year')?.value || 'Any'}).<br>
          <button type="button" onclick="OverallCataloguePortal.resetVisualVariantFilters()" style="margin-top: 0.85rem; padding: 0.5rem 1rem; background: #0284c7; color: #ffffff; border: none; border-radius: 6px; font-weight: 800; cursor: pointer;">
            Clear Filters
          </button>
        </div>
      `;
      return;
    }
    
    grid.innerHTML = variants.map(v => {
      const isSelected = this.selectedVariant === v.subModel;
      const imgUrl = (v.image || '').trim();
      const subTitle = v.subModel || v.model;
      const fuel = v.fuelType || 'PETROL';
      const yrs = v.years || '';

      const thumbHtml = imgUrl ? `
        <img class="visual-variant-thumb" src="${imgUrl}" alt="${this.escapeHtml(subTitle)}" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';">
        <div class="visual-variant-thumb-blank" style="display: none; height: 90px; width: 100%; background: #f8fafc; border-radius: 8px; margin-bottom: 0.5rem; align-items: center; justify-content: center; border: 1px dashed #cbd5e1;">
          <span style="color: #94a3b8; font-size: 0.72rem; font-weight: 700;">No photo available</span>
        </div>
      ` : `
        <div class="visual-variant-thumb-blank" style="height: 90px; width: 100%; background: #f8fafc; border-radius: 8px; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: center; border: 1px dashed #cbd5e1;">
          <span style="color: #94a3b8; font-size: 0.72rem; font-weight: 700;">No photo available</span>
        </div>
      `;

      return `
        <div class="visual-variant-card ${isSelected ? 'selected' : ''}" onclick="OverallCataloguePortal.selectVariantVisual('${this.escapeJs(v.subModel)}', '${this.escapeJs(v.model)}', '${this.escapeJs(fuel)}', '${this.escapeJs(v.fromYear || '')}', '${this.escapeJs(v.toYear || '')}', '${this.escapeJs(imgUrl)}')">
          ${thumbHtml}
          <div>
            <div class="visual-variant-name" title="${this.escapeHtml(subTitle)}">${this.escapeHtml(subTitle)}</div>
            <div class="visual-variant-specs">
              <span class="visual-variant-fuel-badge">${this.escapeHtml(fuel)}</span>
              ${yrs ? `<span>${this.escapeHtml(yrs)}</span>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  onVisualFilterChange() {
    this.loadVisualVariants();
  },

  onVisualFilterDebounce() {
    if (this.variantFilterDebounceTimer) clearTimeout(this.variantFilterDebounceTimer);
    this.variantFilterDebounceTimer = setTimeout(() => {
      this.loadVisualVariants();
    }, 280);
  },

  filterByModelPill(modelName, pillElem) {
    this.selectedModel = modelName;
    document.querySelectorAll('#v-model-pills-wrap .chip').forEach(c => c.classList.remove('active'));
    if (pillElem) pillElem.classList.add('active');
    this.loadVisualVariants();
  },

  resetVisualVariantFilters() {
    const fuelSel = document.getElementById('v-filter-fuel');
    const yrSel = document.getElementById('v-filter-year');
    const searchInp = document.getElementById('v-filter-search');
    if (fuelSel) fuelSel.value = '';
    if (yrSel) yrSel.value = '';
    if (searchInp) searchInp.value = '';
    this.selectedModel = null;
    this.loadVisualVariants();
  },

  selectVariantVisual(subModel, model, fuelType, fromYr, toYr, imgUrl) {
    this.selectedVariant = subModel;
    this.selectedModel = model;
    this.selectedVariantFuel = fuelType;
    this.selectedVariantYears = (fromYr || toYr) ? `${fromYr} - ${toYr || 'Present'}` : '';
    this.selectedVariantImage = imgUrl;
    
    // Update filters on OverallCataloguePortal
    this.filters.make = this.selectedMake;
    this.filters.model = model;
    this.filters.sub_model = subModel;
    if (fuelType) this.filters.fuel_type = fuelType;
    if (fromYr) this.filters.year = fromYr;
    
    // Update UI in Step 4
    const thumbEl = document.getElementById('v-selected-veh-thumb');
    const titleEl = document.getElementById('v-selected-veh-title');
    const metaEl = document.getElementById('v-selected-veh-meta');
    if (thumbEl) {
      if (imgUrl) {
        thumbEl.src = imgUrl;
        thumbEl.style.display = 'block';
      } else {
        const makeLogo = this.getMakeLogo(this.selectedMake);
        if (makeLogo) {
          thumbEl.src = makeLogo;
          thumbEl.style.display = 'block';
        } else {
          thumbEl.style.display = 'none';
        }
      }
    }
    if (titleEl) titleEl.textContent = `${this.selectedMake} ${subModel}`;
    if (metaEl) metaEl.textContent = `Fuel: ${fuelType} • Applicable Years: ${this.selectedVariantYears || 'All Years'}`;
    
    // Update active fitment bar at bottom
    const fitmentBar = document.getElementById('v-active-fitment-bar');
    const fitmentText = document.getElementById('v-fitment-summary-text');
    if (fitmentBar) fitmentBar.style.display = 'flex';
    if (fitmentText) fitmentText.textContent = `${this.selectedMake} ${subModel} (${fuelType} ${this.selectedVariantYears})`;
    
    // Update stepper label
    const stepLabel3 = document.getElementById('v-step-label-3');
    if (stepLabel3) stepLabel3.textContent = subModel || 'Variant';
    
    // Navigate to Step 4 (Assembly & Component Selection)
    this.navGoToStep(4);
    
    // Load System Aggregates
    this.loadVisualAggregates();
  },

  async loadVisualAggregates() {
    const listEl = document.getElementById('v-agg-vertical-list') || document.getElementById('v-tax-agg-list');
    const countEl = document.getElementById('v-tax-agg-count');
    if (listEl) {
      listEl.innerHTML = `<div style="text-align: center; padding: 2rem; color: #0284c7; font-weight: 700;">⚡ Loading aggregates...</div>`;
    }
    
    // Clear sub-aggregate column
    const subList = document.getElementById('v-tax-subagg-list');
    const subCount = document.getElementById('v-tax-subagg-count');
    if (subList) subList.innerHTML = `<div style="text-align: center; padding: 3rem 1rem; color: #94a3b8; font-size: 0.85rem;">👈 Select a Primary System Aggregate on the left to view its Sub-Aggregates</div>`;
    if (subCount) subCount.textContent = 'Select Aggregate';
    
    try {
      const params = new URLSearchParams();
      if (this.selectedMake) params.append('make', this.selectedMake);
      if (this.selectedModel) params.append('model', this.selectedModel);
      if (this.selectedVariant) params.append('sub_model', this.selectedVariant);
      
      const res = await fetch(`/api/overall-catalogue/taxonomy-hierarchy?${params.toString()}`);
      if (!res.ok) throw new Error("Aggregates fetch failed");
      const data = await res.json();
      const items = data.items || [];
      this.loadedAggregatesList = items;
      
      if (countEl) countEl.textContent = `${items.length} Systems`;
      
      if (!listEl) return;
      if (items.length === 0) {
        listEl.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b;">No categories available for this vehicle.</div>`;
        return;
      }
      
      listEl.innerHTML = items.map(item => {
        const isSelected = (this.selectedAggregates || []).includes(item.name);
        const iconChar = (this.AGGREGATE_ICONS && this.AGGREGATE_ICONS[item.name]) || item.icon || '📦';
        return `
          <div class="agg-vertical-card ${isSelected ? 'active' : ''}" 
               data-agg-name="${this.escapeHtml(item.name)}"
               onclick="OverallCataloguePortal.selectAggregateVisual('${this.escapeJs(item.name)}', this, event)">
            <div style="display: flex; align-items: center; gap: 0.5rem; min-width: 0; flex: 1;">
              <span style="font-size: 1.15rem; flex-shrink: 0;">${iconChar}</span>
              <div style="min-width: 0; flex: 1;">
                <div class="agg-vcard-name" title="${this.escapeHtml(item.name)}">
                  ${this.escapeHtml(item.name)}
                </div>
                <div style="font-size: 0.66rem; color: #64748b; font-weight: 700; margin-top: 1px;">
                  ${Number(item.count || 0).toLocaleString('en-IN')} SKUs
                </div>
              </div>
            </div>
            <span class="agg-vcard-arrow" style="color: ${isSelected ? '#0284c7' : '#94a3b8'}; font-size: 0.85rem; font-weight: 900; transition: transform 0.15s; flex-shrink: 0;">${isSelected ? '✓' : '➔'}</span>
          </div>
        `;
      }).join('');

      // Auto-select initial aggregate if none selected
      if (!this.selectedAggregates || this.selectedAggregates.length === 0) {
        const targetAgg = (items.find(i => i.name === 'ENGINE' || i.name === 'BRAKE SYSTEM')?.name || (items[0] && items[0].name));
        if (targetAgg) {
          this.selectedAggregates = [targetAgg];
          this.selectedAggregate = targetAgg;
          this.filters.aggregate = targetAgg;
        }
      }
      this.updateAggregateVisualState();
      this.loadVisualSubAggregates();
    } catch (err) {
      console.error("Error loading visual aggregates:", err);
      if (listEl) listEl.innerHTML = `<div style="text-align: center; padding: 2rem; color: #f87171;">⚠️ ${this.escapeHtml(err.message)}</div>`;
    }
  },

  filterAggregatesList(q) {
    const listEl = document.getElementById('v-agg-vertical-list') || document.getElementById('v-tax-agg-list');
    if (!listEl) return;
    const cleanQ = (q || '').trim().toUpperCase();
    const cards = listEl.querySelectorAll('.agg-vertical-card, .taxonomy-item-pill');
    cards.forEach(card => {
      const name = (card.getAttribute('data-agg-name') || card.textContent || '').toUpperCase();
      if (!cleanQ || name.includes(cleanQ)) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  },

  fetchCatalogueData() {
    return this.fetchData();
  },

  selectedAggregates: [],
  selectedSubAggregates: [],

  inferBrand(lineCode, make) {
    const lc = String(lineCode || '').trim();
    const lcMap = {
      '217': 'MARUTI SUZUKI',
      '218': 'TOYOTA',
      '219': 'HONDA',
      '220': 'RENAULT',
      '221': 'NISSAN',
      '222': 'FORD',
      '224': 'TATA',
      '225': 'MAHINDRA',
      '226': 'HYUNDAI',
      '227': 'CHEVROLET',
      '228': 'VOLKSWAGEN',
      '229': 'FIAT',
      '001': 'BOSCH',
      '002': 'DELPHI',
      '004': 'DENSO',
      '015': 'VALEO',
      '034': 'LUCAS-TVS',
      '035': 'TVS GIRLING',
      '850': 'MYTVS'
    };
    if (lcMap[lc]) return lcMap[lc];
    const m = (make || '').trim().toUpperCase();
    if (m && m !== 'GENERIC') return m;
    return 'GENUINE';
  },

  showAllPartsForCurrentAggregate() {
    this.selectedSubAggregates = [];
    this.selectedSubAggregate = null;
    delete this.filters.sub_aggregate;
    delete this.filters.component;
    const subList = document.getElementById('v-tax-subagg-list');
    if (subList) {
      subList.querySelectorAll('.subagg-rect-card').forEach(p => p.classList.remove('active'));
    }
    this.currentPage = 1;
    this.fetchData();
  },

  async selectAggregateVisual(aggName, elem, event) {
    if (!this.selectedAggregates) this.selectedAggregates = [];
    
    const idx = this.selectedAggregates.indexOf(aggName);
    if (idx >= 0) {
      this.selectedAggregates.splice(idx, 1);
    } else {
      this.selectedAggregates.push(aggName);
    }
    
    this.selectedAggregate = this.selectedAggregates[0] || null;
    this.selectedSubAggregate = null;
    this.selectedSubAggregates = [];
    delete this.filters.sub_aggregate;
    delete this.filters.component;

    if (this.selectedAggregates.length > 0) {
      this.filters.aggregate = this.selectedAggregates.join(',');
    } else {
      delete this.filters.aggregate;
    }

    this.updateAggregateVisualState();
    this.loadVisualSubAggregates();
    this.currentPage = 1;
    this.fetchData();
  },

  updateAggregateVisualState() {
    const listEl = document.getElementById('v-agg-vertical-list') || document.getElementById('v-tax-agg-list');
    if (listEl) {
      listEl.querySelectorAll('.agg-vertical-card').forEach(card => {
        const name = card.getAttribute('data-agg-name');
        const isSel = (this.selectedAggregates || []).includes(name);
        card.classList.toggle('active', isSel);
        const arrow = card.querySelector('.agg-vcard-arrow');
        if (arrow) {
          arrow.textContent = isSel ? '✓' : '➔';
          arrow.style.color = isSel ? '#0284c7' : '#94a3b8';
        }
      });
    }

    const nameEl = document.getElementById('v-selected-agg-badge-name');
    const iconEl = document.getElementById('v-selected-agg-badge-icon');
    const selCount = (this.selectedAggregates || []).length;
    if (nameEl) {
      if (selCount === 0) nameEl.textContent = 'ALL SYSTEMS & AGGREGATES';
      else if (selCount === 1) nameEl.textContent = `${this.selectedAggregates[0]} ASSEMBLIES & SUB-SYSTEMS`;
      else nameEl.textContent = `${selCount} SYSTEMS SELECTED: ${this.selectedAggregates.join(', ')}`;
    }
    if (iconEl && selCount > 0) {
      iconEl.textContent = (this.AGGREGATE_ICONS && this.AGGREGATE_ICONS[this.selectedAggregates[0]]) || '⚙️';
    }
  },

  async loadVisualSubAggregates() {
    const subList = document.getElementById('v-tax-subagg-list');
    const subCount = document.getElementById('v-tax-subagg-count');
    const aggs = this.selectedAggregates || [];

    if (aggs.length === 0) {
      if (subList) subList.innerHTML = `<div style="text-align: center; padding: 2.5rem; color: #64748b; grid-column: 1 / -1;">All vehicle parts selected below in Master Catalogue. Click any system on the left to filter sub-assemblies.</div>`;
      if (subCount) subCount.textContent = 'All Systems';
      return;
    }

    if (subList) {
      subList.innerHTML = `<div style="text-align: center; padding: 2.5rem; color: #0284c7; font-weight: 700; grid-column: 1 / -1;">🔄 Loading sub-assemblies...</div>`;
    }

    try {
      const params = new URLSearchParams({ aggregate: aggs.join(',') });
      if (this.selectedMake) params.append('make', this.selectedMake);
      if (this.selectedModel) params.append('model', this.selectedModel);
      if (this.selectedVariant) params.append('sub_model', this.selectedVariant);

      const res = await fetch(`/api/overall-catalogue/taxonomy-hierarchy?${params.toString()}`);
      if (!res.ok) throw new Error("Sub-aggregates fetch failed");
      const data = await res.json();
      const items = data.items || [];
      this.loadedSubAggregatesList = items;

      if (subCount) subCount.textContent = `${items.length} Sub-Assemblies`;

      if (!subList) return;
      if (items.length === 0) {
        subList.innerHTML = `<div style="text-align: center; padding: 2.5rem; color: #64748b; grid-column: 1 / -1;">All parts directly mapped to selected system(s). Filtered below in Master Catalogue.</div>`;
      } else {
        subList.innerHTML = items.map(item => {
          const isSel = (this.selectedSubAggregates || []).includes(item.name);
          return `
            <button type="button" class="subagg-rect-card ${isSel ? 'active' : ''}" 
                    data-subagg-name="${this.escapeHtml(item.name)}"
                    onclick="OverallCataloguePortal.selectSubAggregateVisual('${this.escapeJs(item.name)}', this)"
                    title="${this.escapeHtml(item.name)}">
              <span class="subagg-rect-name">${this.escapeHtml(item.name)}</span>
              <span class="subagg-rect-count">${Number(item.count || 0).toLocaleString('en-IN')} SKUs</span>
            </button>
          `;
        }).join('');
      }
    } catch (err) {
      console.error("Error loading subaggregates:", err);
      if (subList) subList.innerHTML = `<div style="text-align: center; padding: 2rem; color: #f87171; grid-column: 1 / -1;">⚠️ ${this.escapeHtml(err.message)}</div>`;
    }
  },

  async selectSubAggregateVisual(subAggName, elem) {
    if (!this.selectedSubAggregates) this.selectedSubAggregates = [];
    const idx = this.selectedSubAggregates.indexOf(subAggName);
    if (idx >= 0) {
      this.selectedSubAggregates.splice(idx, 1);
    } else {
      this.selectedSubAggregates.push(subAggName);
    }

    const subList = document.getElementById('v-tax-subagg-list');
    if (subList) {
      subList.querySelectorAll('.subagg-rect-card').forEach(c => {
        const name = c.getAttribute('data-subagg-name') || c.getAttribute('title');
        const isSel = (this.selectedSubAggregates || []).includes(name);
        c.classList.toggle('active', isSel);
      });
    }

    const subCount = document.getElementById('v-tax-subagg-count');
    if (this.selectedSubAggregates.length > 0) {
      this.filters.sub_aggregate = this.selectedSubAggregates.join(',');
      this.selectedSubAggregate = this.selectedSubAggregates[0];
      if (subCount) subCount.textContent = `${this.selectedSubAggregates.length} Selected`;
    } else {
      delete this.filters.sub_aggregate;
      this.selectedSubAggregate = null;
      if (subCount) subCount.textContent = `${(this.loadedSubAggregatesList || []).length} Sub-Assemblies`;
    }

    this.currentPage = 1;
    this.fetchData();
  },

  getBrandLogo(brandName) {
    const b = (brandName || '').trim().toUpperCase();
    if (!b) return '';

    // Primary OES Brands (Authentic Logos)
    if (b.includes('BOSCH')) return 'images/brands/bosch.svg';
    if (b.includes('VALEO')) return 'images/brands/valeo.svg';
    if (b.includes('DENSO')) return 'images/brands/denso.svg';
    if (b.includes('ZF')) return 'images/brands/zf.svg';
    if (b.includes('LUK')) return 'images/brands/luk.png';
    if (b.includes('BREMBO')) return 'images/brands/brembo.svg';
    if (b.includes('SKF')) return 'images/brands/skf.svg';
    if (b.includes('CONTITECH')) return 'images/brands/contitech.svg';
    if (b.includes('MYTVS') || b === 'TVS' || b.includes('TVS MOBILITY')) return 'images/brands/mytvs.svg';
    if (b.includes('CASTROL')) return 'images/brands/castrol.svg';

    // Authentic OEM Logos (From images/makes/ - Real Manufacturer Logos)
    if (b.includes('MARUTI') || b.includes('SUZUKI') || b.includes('NEXA')) return 'images/makes/maruti.png';
    if (b.includes('HYUNDAI') || b.includes('MOBIS')) return 'images/makes/hyundai.png';
    if (b.includes('TATA')) return 'images/makes/tata.png';
    if (b.includes('MAHINDRA')) return 'images/makes/mahindra.png';
    if (b.includes('TOYOTA')) return 'images/makes/toyota.png';
    if (b.includes('HONDA')) return 'images/makes/honda.png';
    if (b.includes('KIA')) return 'images/makes/kia.png';
    if (b.includes('FORD')) return 'images/makes/ford.png';
    if (b.includes('VOLKSWAGEN') || b === 'VW') return 'images/makes/volkswagen.jpg';
    if (b.includes('SKODA')) return 'images/makes/skoda.jpg';
    if (b.includes('RENAULT')) return 'images/makes/renault.png';
    if (b.includes('NISSAN')) return 'images/makes/nissan.png';
    if (b.includes('MG') || b.includes('MORRIS')) return 'images/makes/mg.png';
    if (b.includes('BMW')) return 'images/makes/bmw.png';
    if (b.includes('MERCEDES')) return 'images/makes/mercedes.jpg';
    if (b.includes('AUDI')) return 'images/makes/audi.png';
    if (b.includes('CHEVROLET')) return 'images/makes/chevrolet.png';
    if (b.includes('FIAT')) return 'images/makes/fiat.jpg';
    if (b.includes('JEEP')) return 'images/makes/jeep.png';
    if (b.includes('FORCE')) return 'images/makes/force.png';
    if (b.includes('ASHOK') || b.includes('LEYLAND')) return 'images/makes/ashok_leyland.png';
    if (b.includes('VOLVO')) return 'images/makes/volvo.png';

    // Other Authentic Brand Logos
    if (b.includes('LUCAS')) return 'images/brands/lucas_tvs.svg';
    if (b.includes('TVS GIRLING')) return 'images/brands/tvs_girling.svg';
    if (b.includes('ELOFIC')) return 'images/brands/elofic.svg';
    if (b.includes('PUROLATOR')) return 'images/brands/purolator.svg';
    if (b.includes('MAHLE')) return 'images/brands/mahle.svg';
    if (b.includes('GABRIEL')) return 'images/brands/gabriel.svg';
    if (b.includes('TALBROS')) return 'images/brands/talbros.svg';
    if (b.includes('LUMAX')) return 'images/brands/lumax.svg';
    if (b.includes('MINDA')) return 'images/brands/minda.svg';
    if (b.includes('EXEDY')) return 'images/brands/exedy.svg';
    if (b.includes('NGK')) return 'images/brands/ngk.svg';
    if (b.includes('OSRAM')) return 'images/brands/osram.svg';
    if (b.includes('ROOTS')) return 'images/brands/roots.svg';
    if (b.includes('TRW')) return 'images/brands/trw.svg';

    return '';
  },

  getComponentImage(desc, comp, agg) {
    // All component images removed per user request - clean data-driven UI
    return '';
  },

  getBrandCategoryBadge(brand) {
    const b = (brand || '').trim().toUpperCase();
    
    // PL (Private Label)
    if (b === 'MYTVS' || b.includes('MYTVS') || b === 'UCAP') {
      return `<span class="badge" style="background: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; font-size: 0.65rem; font-weight: 850; padding: 0.15rem 0.45rem; border-radius: 4px;">⭐ myTVS PL</span>`;
    }
    
    // PRIMARY (Tier-1 OES)
    const primaryList = ['BOSCH', 'DELPHI TECH', 'DENSO', 'FILTRON', 'INA', 'JK TYRE', 'KK LIGHTINGS', 'LUK', 'MONROE', 'RANE MADRAS LIMITED', 'VALEO', 'ZF'];
    if (primaryList.some(p => b === p || b.includes(p))) {
      return `<span class="badge" style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 0.65rem; font-weight: 850; padding: 0.15rem 0.45rem; border-radius: 4px;">⚙️ Primary OES</span>`;
    }

    // OEM GENUINE
    const oemList = ['MARUTI', 'HYUNDAI', 'TATA', 'MAHINDRA', 'TOYOTA', 'HONDA', 'KIA', 'FORD', 'VOLKSWAGEN', 'SKODA', 'RENAULT', 'NISSAN', 'BMW', 'MERCEDES', 'AUDI', 'CHEVROLET', 'FIAT', 'JEEP', 'MORRIS', 'VOLVO', 'FORCE', 'ASHOK LEYLAND', 'MITSUBISHI', 'GENUINE', 'MOBIS'];
    if (oemList.some(o => b.includes(o))) {
      return `<span class="badge" style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 0.65rem; font-weight: 850; padding: 0.15rem 0.45rem; border-radius: 4px;">🛡️ OEM Genuine</span>`;
    }

    // LUBES & FLUIDS / CASTROL
    if (b.includes('CASTROL') || b.includes('SHELL') || b.includes('ADD LUB') || b.includes('MOBIL') || b.includes('LUBES')) {
      return `<span class="badge" style="background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; font-size: 0.65rem; font-weight: 850; padding: 0.15rem 0.45rem; border-radius: 4px;">🛢️ Lubes & Castrol</span>`;
    }

    // SECONDARY (Aftermarket)
    return `<span class="badge" style="background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-size: 0.65rem; font-weight: 850; padding: 0.15rem 0.45rem; border-radius: 4px;">💎 Secondary Aftermarket</span>`;
  },

  getQualityTierBadge(brand) {
    return this.getBrandCategoryBadge(brand);
  },

  getFitmentBadge(row) {
    return '';
  },

  selectComponentVisual(compName, elem) {
    this.selectedComponent = compName;
    document.querySelectorAll('#v-tax-comp-list .taxonomy-item-pill').forEach(p => p.classList.remove('active'));
    if (elem) elem.classList.add('active');
    
    // Set catalogue filters
    this.filters.aggregate = this.selectedAggregate || '';
    this.filters.sub_aggregate = this.selectedSubAggregate || '';
    this.filters.component = compName || '';
    
    this.navGoToStep(5);
    this.handleFilterChange();
    
    // Smooth scroll down to the Master Parts Information Table
    const tableContainer = document.querySelector('.cat-recent-activity-card');
    if (tableContainer) {
      tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  },

  launchAssemblyTable() {
    this.filters.aggregate = this.selectedAggregate || '';
    this.filters.sub_aggregate = this.selectedSubAggregate || '';
    this.filters.component = '';
    this.navGoToStep(5);
    this.handleFilterChange();
    const tableContainer = document.querySelector('.cat-recent-activity-card');
    if (tableContainer) {
      tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  },

  navGoToStep(stepNum) {
    this.visualCurrentStep = stepNum;
    
    // Stepper Pills (1 to 5)
    [1, 2, 3, 4, 5].forEach(n => {
      const pill = document.getElementById(`v-step-pill-${n}`);
      if (pill) {
        if (n === stepNum) {
          pill.className = 'visual-step-pill active';
        } else if (n < stepNum) {
          pill.className = 'visual-step-pill completed';
        } else {
          pill.className = 'visual-step-pill';
        }
      }
    });
    
    // Panes
    const p1 = document.getElementById('v-nav-step-1');
    const p2 = document.getElementById('v-nav-step-2');
    const p3 = document.getElementById('v-nav-step-3');
    const p4 = document.getElementById('v-nav-step-4');
    
    if (p1) p1.style.display = (stepNum === 1) ? 'block' : 'none';
    if (p2) p2.style.display = (stepNum === 2) ? 'block' : 'none';
    if (p3) p3.style.display = (stepNum === 3) ? 'block' : 'none';
    if (p4) p4.style.display = (stepNum === 4 || stepNum === 5) ? 'block' : 'none';
    
    if (stepNum >= 2 && stepNum <= 4) {
      const navContainer = document.getElementById('cat-visual-navigator');
      if (navContainer) {
        navContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
    
    if (stepNum === 5) {
      const tableContainer = document.querySelector('.cat-recent-activity-card');
      if (tableContainer) {
        tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  },

  clearVisualFitment() {
    this.selectedMake = null;
    this.selectedModel = null;
    this.selectedVariant = null;
    this.selectedAggregate = null;
    this.selectedSubAggregate = null;
    this.selectedComponent = null;
    
    this.filters.make = '';
    this.filters.model = '';
    this.filters.sub_model = '';
    this.filters.fuel_type = '';
    this.filters.year = '';
    this.filters.aggregate = '';
    this.filters.sub_aggregate = '';
    this.filters.component = '';

    const stepLabel2 = document.getElementById('v-step-label-2');
    if (stepLabel2) stepLabel2.textContent = 'Select Model';
    const stepLabel3 = document.getElementById('v-step-label-3');
    if (stepLabel3) stepLabel3.textContent = 'Choose Variant';
    
    const fitmentBar = document.getElementById('v-active-fitment-bar');
    if (fitmentBar) fitmentBar.style.display = 'none';
    
    this.navGoToStep(1);
    this.handleFilterChange();
  },

  async loadStats() {
    try {
      const res = await fetch('/api/overall-catalogue/analytics');
      if (!res.ok) throw new Error("Analytics API failed");
      const data = await res.json();
      const totals = data.totals || {};

      const records = totals.total_rows;
      const parts = totals.distinct_parts;
      const brands = totals.distinct_brands;
      const makes = totals.distinct_makes;
      const models = totals.distinct_models;
      const aggregates = totals.distinct_aggregates || 29;
      const subaggregates = totals.distinct_sub_aggregates || 213;
      const components = totals.distinct_components || 923;

      const elRecords = document.getElementById('cat-stat-records');
      const elParts = document.getElementById('cat-stat-parts');
      const elBrands = document.getElementById('cat-stat-brands');
      const elMakes = document.getElementById('cat-stat-makes');
      const elTaxonomy = document.getElementById('cat-stat-taxonomy');
      const elSubAgg = document.getElementById('cat-stat-subaggregates');
      const elComponents = document.getElementById('cat-stat-components');
      const elSidebarBadge = document.getElementById('cat-sidebar-badge');
      const elHeaderSkus = document.getElementById('header-stat-skus');
      const elHeroTotal = document.getElementById('cat-hero-total-skus');
      const elHeroChipSkus = document.getElementById('cat-hero-chip-skus');
      const elHeroChipMakes = document.getElementById('cat-hero-chip-makes');

      if (elRecords) elRecords.textContent = records ? Number(records).toLocaleString('en-IN') : '—';
      if (elParts) elParts.textContent = parts ? Number(parts).toLocaleString('en-IN') : '—';
      if (elBrands) elBrands.textContent = brands ? `${Number(brands)}+ Brands` : '—';
      if (elMakes) elMakes.textContent = (makes && models) ? `${makes} Makes • ${models} Models` : '—';
      if (elTaxonomy) elTaxonomy.textContent = aggregates ? String(aggregates) : '—';
      if (elSubAgg) elSubAgg.textContent = subaggregates ? String(subaggregates) : '—';
      if (elComponents) elComponents.textContent = components ? Number(components).toLocaleString('en-IN') : '923';

      const mCount = records ? (records / 1000000).toFixed(1) + 'M' : '—';
      if (elSidebarBadge) elSidebarBadge.textContent = mCount;
      if (elHeaderSkus) elHeaderSkus.textContent = records ? `${mCount} SKUs Live` : '—';
      if (elHeroTotal) elHeroTotal.textContent = records ? Number(records).toLocaleString('en-IN') : '—';
      if (elHeroChipSkus) elHeroChipSkus.textContent = records ? `${Number(records).toLocaleString('en-IN')} SKUs` : '—';
      if (elHeroChipMakes) elHeroChipMakes.textContent = (makes && models) ? `${makes} Makes • ${models} Models` : '—';

      // Update Category Split Block 3 with Database Record Totals
      if (data.category_split && data.category_split.categories) {
        const catMap = {};
        data.category_split.categories.forEach(c => { catMap[c.category] = c; });
        if (catMap['Mechanical']) {
          const el = document.getElementById('cat-split-val-mech');
          const elP = document.getElementById('cat-split-pct-mech');
          if (el) el.textContent = (catMap['Mechanical'].count / 1000000).toFixed(2) + 'M';
          if (elP) elP.textContent = catMap['Mechanical'].pct + '%';
        }
        if (catMap['Body Parts']) {
          const el = document.getElementById('cat-split-val-body');
          const elP = document.getElementById('cat-split-pct-body');
          if (el) el.textContent = (catMap['Body Parts'].count / 1000000).toFixed(2) + 'M';
          if (elP) elP.textContent = catMap['Body Parts'].pct + '%';
        }
        if (catMap['Accessories']) {
          const el = document.getElementById('cat-split-val-acc');
          const elP = document.getElementById('cat-split-pct-acc');
          if (el) el.textContent = (catMap['Accessories'].count / 1000000).toFixed(2) + 'M';
          if (elP) elP.textContent = catMap['Accessories'].pct + '%';
        }
        if (catMap['Lubes & Fluids']) {
          const el = document.getElementById('cat-split-val-lubes');
          const elP = document.getElementById('cat-split-pct-lubes');
          if (el) el.textContent = (catMap['Lubes & Fluids'].count / 1000000).toFixed(2) + 'M';
          if (elP) elP.textContent = catMap['Lubes & Fluids'].pct + '%';
        }
      }
    } catch (err) {
      console.error("Error loading catalogue stats:", err);
      ['cat-stat-records', 'cat-stat-parts', 'cat-stat-brands', 'cat-stat-makes', 'cat-stat-taxonomy', 'cat-stat-subaggregates', 'cat-stat-components', 'cat-sidebar-badge', 'header-stat-skus', 'cat-hero-total-skus', 'cat-hero-chip-skus', 'cat-hero-chip-makes'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '—';
      });
    }
  },

  catMakesChart: null,
  catAggregatesChart: null,
  catBrandsChart: null,
  catMrpChart: null,

  async initCharts() {
    if (typeof Chart === 'undefined') return;

    const showUnavailable = (wrapperId) => {
      const w = document.getElementById(wrapperId);
      if (w) w.innerHTML = '<div class="cat-chart-unavailable">⚠️ Data unavailable</div>';
    };

    let dbAnalytics = null;
    try {
      const res = await fetch('/api/overall-catalogue/analytics');
      if (res.ok) {
        dbAnalytics = await res.json();
      }
    } catch (e) {
      console.warn("Could not fetch /api/overall-catalogue/analytics:", e);
    }

    if (!dbAnalytics || !dbAnalytics.top_makes || dbAnalytics.top_makes.length === 0) {
      showUnavailable('cat-chart-makes-wrapper');
      showUnavailable('cat-chart-aggregates-wrapper');
      showUnavailable('cat-chart-brands-wrapper');
      showUnavailable('cat-chart-mrp-wrapper');
      return;
    }

    const topMakesData = dbAnalytics.top_makes || [];
    const topAggregatesData = dbAnalytics.top_aggregates || [];
    const topBrandsData = dbAnalytics.top_brands || [];
    const mrpData = dbAnalytics.mrp_bands || [];

    // 1. Top Vehicle Makes Bar Chart
    const ctxMakes = document.getElementById('cat-chart-makes')?.getContext('2d');
    if (ctxMakes) {
      if (this.catMakesChart) this.catMakesChart.destroy();
      const gradMakes = ctxMakes.createLinearGradient(0, 0, 0, 150);
      gradMakes.addColorStop(0, '#0284c7');
      gradMakes.addColorStop(1, '#38bdf8');

      this.catMakesChart = new Chart(ctxMakes, {
        type: 'bar',
        data: {
          labels: topMakesData.map(m => (m.make || '').replace('MARUTI SUZUKI', 'MARUTI')),
          datasets: [{
            label: 'SKUs (Millions)',
            data: topMakesData.map(m => +((m.count || 0) / 1000000).toFixed(2)),
            backgroundColor: gradMakes,
            borderRadius: 4,
            barThickness: 16
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#0f172a',
              callbacks: {
                label: (ctx) => ` ${ctx.raw}M Records (${topMakesData[ctx.dataIndex]?.pct || 0}%)`
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#64748b', font: { size: 9, weight: '700' } }
            },
            y: {
              grid: { color: '#f1f5f9' },
              ticks: {
                color: '#64748b',
                font: { size: 9, weight: '600' },
                callback: (val) => `${val}M`
              },
              min: 0
            }
          }
        }
      });
    }

    // 2. Major System Aggregates Doughnut Chart
    const ctxAggregates = document.getElementById('cat-chart-aggregates')?.getContext('2d');
    if (ctxAggregates) {
      if (this.catAggregatesChart) this.catAggregatesChart.destroy();
      this.catAggregatesChart = new Chart(ctxAggregates, {
        type: 'doughnut',
        data: {
          labels: topAggregatesData.map(a => (a.aggregate || '').replace(' AND ', ' & ').replace('PAINTS & CONSUMABLES', 'CONSUMABLES')),
          datasets: [{
            data: topAggregatesData.map(a => a.pct),
            backgroundColor: [
              '#0284c7', '#ea580c', '#f59e0b', '#10b981', '#8b5cf6',
              '#ec4899', '#06b6d4', '#64748b', '#6366f1', '#14b8a6'
            ],
            borderWidth: 1.5,
            borderColor: '#ffffff',
            hoverOffset: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '62%',
          plugins: {
            legend: {
              position: 'right',
              labels: {
                boxWidth: 8,
                boxHeight: 8,
                usePointStyle: true,
                pointStyle: 'circle',
                color: '#334155',
                font: { size: 9, weight: '700' },
                padding: 6
              }
            },
            tooltip: {
              backgroundColor: '#0f172a',
              callbacks: {
                label: (ctx) => ` ${ctx.label}: ${ctx.raw}% (${((topAggregatesData[ctx.dataIndex]?.count || 0) / 1000000).toFixed(2)}M)`
              }
            }
          }
        }
      });
    }

    // 3. Top Mapped Brands Bar Chart
    const ctxBrands = document.getElementById('cat-chart-brands')?.getContext('2d');
    if (ctxBrands) {
      if (this.catBrandsChart) this.catBrandsChart.destroy();
      const gradBrands = ctxBrands.createLinearGradient(0, 0, 0, 150);
      gradBrands.addColorStop(0, '#7c3aed');
      gradBrands.addColorStop(1, '#a78bfa');

      this.catBrandsChart = new Chart(ctxBrands, {
        type: 'bar',
        data: {
          labels: topBrandsData.slice(0, 8).map(b => b.brand),
          datasets: [{
            label: 'Indexed SKUs (M)',
            data: topBrandsData.slice(0, 8).map(b => +((b.count || 0) / 1000000).toFixed(2)),
            backgroundColor: gradBrands,
            borderRadius: 4,
            barThickness: 18
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#0f172a',
              callbacks: {
                label: (ctx) => ` ${ctx.raw}M Indexed SKUs (${topBrandsData[ctx.dataIndex]?.pct || 0}%)`
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#64748b', font: { size: 9, weight: '700' } }
            },
            y: {
              grid: { color: '#f1f5f9' },
              ticks: {
                color: '#64748b',
                font: { size: 9, weight: '600' },
                callback: (val) => `${val}M`
              },
              min: 0
            }
          }
        }
      });
    }

    // 4. Parts MRP Spectrum Doughnut Chart
    const ctxMrp = document.getElementById('cat-chart-mrp')?.getContext('2d');
    if (ctxMrp) {
      if (this.catMrpChart) this.catMrpChart.destroy();
      this.catMrpChart = new Chart(ctxMrp, {
        type: 'doughnut',
        data: {
          labels: mrpData.map(m => (m.band || '').replace('< 500', '< ₹500').replace('500-1499', '₹500-1.5K').replace('1500-4999', '₹1.5K-5K').replace('>= 5000', '> ₹5,000')),
          datasets: [{
            data: mrpData.map(m => m.pct),
            backgroundColor: ['#10b981', '#0284c7', '#f59e0b', '#ef4444'],
            borderWidth: 1.5,
            borderColor: '#ffffff',
            hoverOffset: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '66%',
          plugins: {
            legend: {
              position: 'right',
              labels: {
                boxWidth: 8,
                boxHeight: 8,
                usePointStyle: true,
                pointStyle: 'circle',
                color: '#334155',
                font: { size: 9, weight: '700' },
                padding: 6
              }
            },
            tooltip: {
              backgroundColor: '#0f172a',
              callbacks: {
                label: (ctx) => ` ${ctx.label}: ${ctx.raw}% (${((mrpData[ctx.dataIndex]?.count || 0) / 1000000).toFixed(1)}M SKUs)`
              }
            }
          }
        }
      });
    }

    // Fill MRP Bands summary text
    if (mrpData && mrpData.length >= 4) {
      const el0 = document.getElementById('cat-mrp-band-0');
      const el1 = document.getElementById('cat-mrp-band-1');
      const el2 = document.getElementById('cat-mrp-band-2');
      const el3 = document.getElementById('cat-mrp-band-3');
      if (el0) el0.innerHTML = `&lt;₹500: <strong>${mrpData[0].pct}%</strong>`;
      if (el1) el1.innerHTML = `₹500-1.5K: <strong>${mrpData[1].pct}%</strong>`;
      if (el2) el2.innerHTML = `₹1.5K-5K: <strong>${mrpData[2].pct}%</strong>`;
      if (el3) el3.innerHTML = `&gt;₹5K: <strong>${mrpData[3].pct}%</strong>`;
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
      this.selectedSuggestionIndex = -1;
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
              <div class="cat-suggestion-item" data-part-no="${this.escapeHtml(pNo)}" onmousedown="event.preventDefault(); event.stopPropagation(); OverallCataloguePortal.selectSuggestion('${this.escapeJs(pNo)}')" onclick="OverallCataloguePortal.selectSuggestion('${this.escapeJs(pNo)}')" style="padding: 0.65rem 0.85rem; border-radius: 8px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background 0.15s; background: #ffffff;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">
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

  selectedSuggestionIndex: -1,

  handleSearchKeydown(event) {
    const dropdown = document.getElementById('cat-suggestions-dropdown');
    const isDropdownVisible = dropdown && dropdown.style.display !== 'none';
    const items = dropdown ? dropdown.querySelectorAll('.cat-suggestion-item') : [];

    if (event.key === 'Escape') {
      this.hideSuggestions();
      event.preventDefault();
      return;
    }

    if (event.key === 'ArrowDown') {
      if (isDropdownVisible && items.length > 0) {
        event.preventDefault();
        this.selectedSuggestionIndex = (this.selectedSuggestionIndex + 1) % items.length;
        this.updateSelectedSuggestion(items);
      }
      return;
    }

    if (event.key === 'ArrowUp') {
      if (isDropdownVisible && items.length > 0) {
        event.preventDefault();
        this.selectedSuggestionIndex = (this.selectedSuggestionIndex - 1 + items.length) % items.length;
        this.updateSelectedSuggestion(items);
      }
      return;
    }

    if (event.key === 'Enter') {
      event.preventDefault();
      if (isDropdownVisible && this.selectedSuggestionIndex >= 0 && this.selectedSuggestionIndex < items.length) {
        const selPartNo = items[this.selectedSuggestionIndex].getAttribute('data-part-no');
        if (selPartNo) {
          this.selectSuggestion(selPartNo);
          return;
        }
      }
      this.triggerSearch();
    }
  },

  updateSelectedSuggestion(items) {
    items.forEach((item, idx) => {
      if (idx === this.selectedSuggestionIndex) {
        item.style.background = '#e0f2fe';
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.style.background = '#ffffff';
      }
    });
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
    this.showPartDetails(partNo);
  },

  hideSuggestions() {
    this.selectedSuggestionIndex = -1;
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

  async updateFilteredVariants() {
    const makeVal = this.filters.make || document.getElementById('cat-filter-make')?.value || '';
    const modelVal = this.filters.model || document.getElementById('cat-filter-model')?.value || '';
    const fuelVal = this.filters.fuel_type || document.getElementById('cat-filter-fuel')?.value || '';
    const yearVal = this.filters.year || document.getElementById('cat-filter-year')?.value || '';

    const subSel = document.getElementById('cat-filter-submodel');
    const variantSel = document.getElementById('cat-filter-variant-select');

    if (!makeVal && !modelVal) {
      if (subSel) subSel.innerHTML = `<option value="">All Variants</option>`;
      return;
    }

    if (subSel) {
      subSel.innerHTML = `<option value="">Filtering Variants...</option>`;
    }

    try {
      const params = new URLSearchParams();
      if (makeVal) params.append('make', makeVal);
      if (modelVal) params.append('model', modelVal);
      if (fuelVal) params.append('fuel_type', fuelVal);
      if (yearVal) params.append('year', yearVal);

      const res = await fetch(`/api/overall-catalogue/sub-models?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        const subModels = data.sub_models || [];
        this.populateSelect('cat-filter-submodel', subModels, 'All Variants');
        if (variantSel) this.populateSelect('cat-filter-variant-select', subModels, 'Select Variant');
      }
    } catch (err) {
      console.error("Error updating filtered submodels:", err);
    }
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

    await this.updateFilteredVariants();
    this.handleFilterChange();
  },

  handleSubModelChange() {
    this.filters.sub_model = document.getElementById('cat-filter-submodel')?.value || '';
    this.handleFilterChange();
  },

  async handleFuelChange() {
    this.filters.fuel_type = document.getElementById('cat-filter-fuel')?.value || '';
    await this.updateFilteredVariants();
    this.handleFilterChange();
  },

  async handleYearChange() {
    this.filters.year = document.getElementById('cat-filter-year')?.value || '';
    await this.updateFilteredVariants();
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
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 3rem; color: #0284c7; font-weight: 700;">⚡ Querying 23.6M+ Master Catalogue Database...</td></tr>`;
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
      const qVal = (this.q || '').trim();
      const emptyMsg = qVal 
        ? `No parts found for '<strong>${this.escapeHtml(qVal)}</strong>'. Try the part number without dashes, or pick Make → Model below.`
        : `No catalogue parts found matching the selected filters. Try adjusting your filters or pick Make → Model below.`;

      gridWrapper.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem 1.5rem; color: #475569; font-weight: 600; background: #f8fafc; border: 1.5px dashed #cbd5e1; border-radius: 12px; margin: 1rem 0;">
          <span style="font-size: 2.2rem; display: block; margin-bottom: 0.65rem;">🔍</span>
          <div style="font-size: 0.95rem; color: #0f172a; margin-bottom: 0.85rem; max-width: 600px; margin-left: auto; margin-right: auto; line-height: 1.5;">${emptyMsg}</div>
          <button type="button" onclick="OverallCataloguePortal.resetFilters()" style="padding: 0.6rem 1.25rem; background: #0284c7; border: none; border-radius: 8px; color: #fff; font-weight: 800; cursor: pointer;">
            🔄 Clear All Filters
          </button>
        </div>
      `;
      return;
    }

    gridWrapper.innerHTML = rows.map(r => {
      const partNo = r.partNo ?? r.part_number ?? '';
      const lineCode = r.lineCode ?? (partNo.length > 3 ? partNo.substring(0, 3) : '');
      const make = r.make ?? r.vehicle_make ?? '';
      let brand = (r.brand || r.brand_name || '').trim();
      if (!brand || brand.toUpperCase() === 'GENERIC' || brand.toUpperCase() === 'UNKNOWN') {
        brand = this.inferBrand(lineCode, make);
      }
      const desc = r.desc ?? r.part_description ?? '';
      const listVal = r.listPrice ?? r.list_price;
      const mrpVal = r.mrp ?? r.mrp_price;
      const segment = r.segment ?? 'PCV';
      const model = r.model ?? '';
      const subModel = r.subModel ?? r.sub_model ?? '';
      const aggregate = r.aggregate ?? r.aggregate_name ?? 'SPARE PART';

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

      const brandLogoUrl = this.getBrandLogo(brand);

      return `
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.15rem; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s; position: relative; box-shadow: 0 2px 8px rgba(15,23,42,0.04);" onmouseover="this.style.borderColor='#cbd5e1'; this.style.boxShadow='0 8px 24px rgba(15,23,42,0.08)'; this.style.transform='translateY(-3px)'" onmouseout="this.style.borderColor='#e2e8f0'; this.style.boxShadow='0 2px 8px rgba(15,23,42,0.04)'; this.style.transform='none'">
          
          <div>
            <!-- Header: Category Badge + Line Code on Left, Brand Logo on Right -->
            <div style="display: flex; justify-content: space-between; align-items: center; min-height: 28px; margin-bottom: 0.75rem;">
              <div style="display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap;">
                ${this.getBrandCategoryBadge(brand)}
                ${lineCode ? `<span style="background: #f1f5f9; color: #475569; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.68rem; font-family: monospace; font-weight: 800; border: 1px solid #e2e8f0;">LC ${this.escapeHtml(lineCode)}</span>` : ''}
              </div>
              <div style="display: flex; align-items: center; justify-content: flex-end; min-width: 80px; height: 26px;">
                ${brandLogoUrl ? `
                  <img src="${brandLogoUrl}" alt="${this.escapeHtml(brand)}" style="max-height: 24px; max-width: 85px; object-fit: contain;" title="${this.escapeHtml(brand)}" onerror="this.onerror=null; this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='inline-block';">
                  <span style="display: none; font-size: 0.72rem; font-weight: 850; color: #1e293b; background: #f8fafc; border: 1.2px solid #cbd5e1; padding: 0.15rem 0.45rem; border-radius: 5px;">${this.escapeHtml(brand)}</span>
                ` : (brand ? `
                  <span style="font-size: 0.72rem; font-weight: 850; color: #1e293b; background: #f8fafc; border: 1.2px solid #cbd5e1; padding: 0.15rem 0.45rem; border-radius: 5px;">${this.escapeHtml(brand)}</span>
                ` : '')}
              </div>
            </div>

            <!-- Part Number & Description -->
            <div style="font-family: monospace; font-size: 1rem; font-weight: 900; color: #0284c7; margin-bottom: 0.35rem; letter-spacing: -0.2px;">
              ${this.escapeHtml(partNo)}
            </div>
            ${r.crossLineCodeResolved ? `
              <div style="font-size: 0.68rem; font-weight: 850; color: #92400e; background: #fef3c7; border: 1px solid #fde68a; border-radius: 4px; padding: 0.15rem 0.4rem; margin-bottom: 0.45rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                <span>⚡</span>
                <span>Avl in LC ${this.escapeHtml(r.lineCode || '')} (${this.escapeHtml(brand)})</span>
              </div>
            ` : ''}
            <div style="font-size: 0.86rem; font-weight: 700; color: #0f172a; line-height: 1.4; height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 0.85rem;">
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
      const qVal = (this.q || '').trim();
      const emptyMsg = qVal 
        ? `No parts found for '<strong>${this.escapeHtml(qVal)}</strong>'. Try the part number without dashes, or pick Make → Model below.`
        : `No catalogue parts found matching the selected filters. Try adjusting your filters or pick Make → Model below.`;

      tbody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; padding: 3.5rem 1.5rem; color: #475569; font-weight: 600; background: #f8fafc;">
            <span style="font-size: 2.2rem; display: block; margin-bottom: 0.65rem;">🔍</span>
            <div style="font-size: 0.95rem; color: #0f172a; margin-bottom: 0.85rem; max-width: 600px; margin-left: auto; margin-right: auto; line-height: 1.5;">${emptyMsg}</div>
            <button type="button" onclick="OverallCataloguePortal.resetFilters()" style="padding: 0.6rem 1.25rem; background: #0284c7; border: none; border-radius: 8px; color: #fff; font-weight: 800; cursor: pointer;">
              🔄 Clear All Filters
            </button>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = rows.map(r => {
      const partNo = r.partNo ?? r.part_number ?? '';
      const lineCode = r.lineCode ?? (partNo.length > 3 ? partNo.substring(0, 3) : '');
      const make = r.make ?? r.vehicle_make ?? '';
      let brand = (r.brand || r.brand_name || '').trim();
      if (!brand || brand.toUpperCase() === 'GENERIC' || brand.toUpperCase() === 'UNKNOWN') {
        brand = this.inferBrand(lineCode, make);
      }
      const desc = r.desc ?? r.part_description ?? '';
      const listVal = r.listPrice ?? r.list_price;
      const mrpVal = r.mrp ?? r.mrp_price;
      const segment = r.segment ?? 'PCV';
      const model = r.model ?? '';
      const subModel = r.subModel ?? r.sub_model ?? '';
      const fuelType = r.fuelType ?? r.fuel_type ?? '';
      const aggregate = r.aggregate ?? r.aggregate_name ?? 'SPARE PART';
      const compName = r.canonical_component ?? r.components ?? r.component ?? desc ?? aggregate;
      
      let years = r.applicable_years || '';
      if (!years && (r.fromYear || r.toYear)) {
        years = `${r.fromYear || ''} - ${r.toYear || ''}`.trim();
      }

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

      const brandLogoUrl = this.getBrandLogo(brand);

      return `
        <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
          <td style="font-weight: 850; color: #0284c7; font-family: monospace; font-size: 0.88rem; padding: 0.85rem 1rem; width: 140px; word-break: break-all;">
            ${this.escapeHtml(partNo)}
            ${r.crossLineCodeResolved ? `
              <span title="${this.escapeHtml(r.lineCodeAlert || '')}" style="display: block; font-size: 0.66rem; font-weight: 850; color: #92400e; background: #fef3c7; border: 1px solid #fde68a; border-radius: 4px; padding: 0.12rem 0.35rem; margin-top: 0.3rem; line-height: 1.2;">
                ⚡ LC ${this.escapeHtml(r.lineCode || '')}
              </span>
            ` : ''}
          </td>
          <td style="padding: 0.75rem 0.95rem; width: 145px; vertical-align: middle;">
            <div style="display: flex; flex-direction: column; gap: 0.35rem;">
              <div style="display: flex; align-items: center; gap: 0.45rem;">
                ${brandLogoUrl ? `
                  <div style="width: 44px; height: 26px; background: #ffffff; border: 1.2px solid #e2e8f0; border-radius: 6px; display: flex; align-items: center; justify-content: center; padding: 2px 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); flex-shrink: 0;">
                    <img src="${brandLogoUrl}" alt="${this.escapeHtml(brand)}" style="max-width: 100%; max-height: 20px; object-fit: contain;">
                  </div>
                ` : ''}
                <strong style="font-size: 0.76rem; color: #0f172a; font-family: 'Outfit', sans-serif; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;" title="${this.escapeHtml(brand)}">
                  ${this.escapeHtml(brand)}
                </strong>
              </div>
              <div>${this.getQualityTierBadge(brand)}</div>
            </div>
          </td>
          <td style="padding: 0.75rem 0.85rem; width: 175px;">
            <div style="min-width: 0;">
              <span style="font-weight: 850; font-size: 0.82rem; color: #0f172a; display: block; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${this.escapeHtml(compName)}">
                ${this.escapeHtml(compName)}
              </span>
              <span style="font-size: 0.68rem; color: #64748b; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">
                ${this.escapeHtml(aggregate)}
              </span>
            </div>
          </td>
          <td style="font-weight: 600; color: #1e293b; font-size: 0.82rem; width: 250px; white-space: normal; line-height: 1.35; padding: 0.85rem 1rem; word-break: break-word;">${this.escapeHtml(desc)}</td>
          <td style="font-weight: 850; color: #059669; font-size: 0.88rem; text-align: right; font-family: 'Outfit', sans-serif; padding: 0.85rem 1rem; width: 110px;">${mrpPrice}</td>
          <td style="font-weight: 600; color: #64748b; font-size: 0.8rem; text-align: right; padding: 0.85rem 1rem; width: 100px;">${listPrice}</td>
          <td style="font-weight: 700; color: #7c3aed; font-size: 0.8rem; text-align: center; padding: 0.85rem 1rem; width: 90px;"><span class="badge" style="background: #ede9fe; color: #7c3aed; border: 1px solid #ddd6fe; padding: 0.2rem 0.45rem; border-radius: 6px;">${this.escapeHtml(segment)}</span></td>
          <td style="font-size: 0.8rem; color: #334155; padding: 0.85rem 1rem; width: 180px; word-break: break-word;">
            <div style="font-weight: 750; color: #0f172a;">${this.escapeHtml(vehicleInfo)}</div>
            ${fuelYears ? `<div style="font-size: 0.72rem; color: #64748b; margin-top: 0.15rem;">${this.escapeHtml(fuelYears)}</div>` : ''}
          </td>
          <td style="font-weight: 700; color: #0284c7; font-size: 0.8rem; padding: 0.85rem 1rem; width: 120px; word-break: break-word;">${this.escapeHtml(aggregate)}</td>
          <td style="text-align: center; padding: 0.85rem 1rem; width: 90px;">
            <button type="button" class="btn btn-secondary" onclick="OverallCataloguePortal.showPartDetails('${this.escapeJs(partNo)}')" style="padding: 0.35rem 0.65rem; font-size: 0.76rem; font-weight: 850; background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; border-radius: 7px; cursor: pointer; display: inline-flex; align-items: center; gap: 0.25rem;">
              <span>🔍</span> <span>Fitment</span>
            </button>
          </td>
        </tr>
      `;}).join('');
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
      const oesParts = data.oesParts || data.oes_parts || [];

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

      const brandLogoUrl = this.getBrandLogo(brand);

      modalBody.innerHTML = `
        <div style="background: #f8fafc; border-radius: 14px; padding: 1.35rem; border: 1px solid #e2e8f0; margin-bottom: 1.5rem;">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Part Number</span>
              <strong style="font-size: 1.15rem; color: #0284c7; font-family: monospace;">${this.escapeHtml(pNo)}</strong>
            </div>
            <div>
              <span style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 850; display: block;">Brand Manufacturer</span>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; flex-wrap: wrap;">
                ${brandLogoUrl ? `
                  <div style="width: 52px; height: 28px; background: #ffffff; border: 1.2px solid #e2e8f0; border-radius: 6px; display: flex; align-items: center; justify-content: center; padding: 2px 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); flex-shrink: 0;">
                    <img src="${brandLogoUrl}" alt="${this.escapeHtml(brand)}" style="max-width: 100%; max-height: 22px; object-fit: contain;">
                  </div>
                ` : ''}
                <strong style="font-size: 1.05rem; color: #0f172a;">${this.escapeHtml(brand)}</strong>
                ${this.getQualityTierBadge(brand)}
              </div>
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

        <!-- Smart Repair Overhaul Bundle ("Whistle-Stop" Kit) -->
        <div style="background: linear-gradient(135deg, #f0fdf4, #ecfdf5); border: 1.5px solid #86efac; border-radius: 14px; padding: 1.1rem 1.35rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
          <div style="display: flex; align-items: center; gap: 0.85rem;">
            <span style="font-size: 2rem;">📦</span>
            <div>
              <div style="display: flex; align-items: center; gap: 0.45rem;">
                <span class="badge" style="background: #10b981; color: #ffffff; font-size: 0.68rem; font-weight: 900; padding: 0.15rem 0.45rem; border-radius: 4px;">SMART OVERHAUL BUNDLE</span>
                <strong style="font-size: 0.95rem; color: #065f46; font-family: 'Outfit', sans-serif;">Complete Service & Repair Kit</strong>
              </div>
              <div style="font-size: 0.78rem; color: #166534; font-weight: 650; margin-top: 0.2rem;">
                Companion parts included: Primary Part + OEM Gaskets & Hardware + Service Consumables (15% Bundle Savings)
              </div>
            </div>
          </div>
          <button type="button" onclick="alert('Smart Overhaul Bundle: 1x ' + OverallCataloguePortal.escapeJs(pNo) + ' + 1x Hardware Mounting Kit + 1x Lubricant Companion added to order staging!')" style="padding: 0.55rem 1.15rem; background: #059669; color: #ffffff; border: none; border-radius: 8px; font-size: 0.82rem; font-weight: 850; cursor: pointer; display: flex; align-items: center; gap: 0.4rem; box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);">
            <span>Add Overhaul Kit</span> <span>➔</span>
          </button>
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

        <!-- Respective OES / OEM Interchangeable Parts Matrix -->
        <div style="margin-top: 1.75rem; border-top: 2px dashed #e2e8f0; padding-top: 1.25rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem; flex-wrap: wrap; gap: 0.5rem;">
            <h4 style="margin: 0; font-size: 1.05rem; font-weight: 900; color: #0f172a; display: flex; align-items: center; gap: 0.45rem; font-family: 'Outfit', sans-serif;">
              <span>🔄</span> <span>Respective OES / OEM Interchangeable Parts Matrix</span>
            </h4>
            <span style="font-size: 0.74rem; font-weight: 800; color: #059669; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 0.25rem 0.65rem; border-radius: 6px;">
              ${oesParts.length} Cross-Referenced OES Parts
            </span>
          </div>

          <div style="max-height: 320px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 12px;">
            <table class="data-table" style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr style="background: #f8fafc; position: sticky; top: 0; z-index: 2; border-bottom: 1px solid #e2e8f0;">
                  <th style="padding: 0.75rem; text-align: left; color: #b45309; font-weight: 850;">Brand / Tier</th>
                  <th style="padding: 0.75rem; text-align: left; color: #0284c7; font-weight: 850;">Part Number</th>
                  <th style="padding: 0.75rem; text-align: left; color: #0f172a; font-weight: 850;">Description</th>
                  <th style="padding: 0.75rem; text-align: right; color: #059669; font-weight: 850;">Catalogue MRP</th>
                  <th style="padding: 0.75rem; text-align: left; color: #334155; font-weight: 850;">Vehicle Match</th>
                  <th style="padding: 0.75rem; text-align: center; color: #64748b; font-weight: 850;">Action</th>
                </tr>
              </thead>
              <tbody>
                ${oesParts.length === 0 ? `
                  <tr>
                    <td colspan="6" style="text-align: center; color: #64748b; padding: 2rem; font-size: 0.85rem;">
                      ℹ️ This SKU is a single-source OEM assembly or primary proprietary component without direct cross-line aftermarket matches in the current index.
                    </td>
                  </tr>
                ` : oesParts.map(o => {
                  const oBrand = o.brand || 'GENERIC';
                  const oLogo = this.getBrandLogo(oBrand);
                  const oPartNo = o.partNo || '';
                  const oDesc = o.desc || '';
                  const oMrp = o.mrp > 0 ? `₹${Number(o.mrp).toLocaleString('en-IN', {minimumFractionDigits: 2})}` : 'Price on Request';
                  const oVehicle = [o.make, o.model, o.subModel].filter(Boolean).join(' ') || 'Cross-Platform Fitment';

                  return `
                    <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
                      <td style="padding: 0.75rem; vertical-align: middle;">
                        <div style="display: flex; align-items: center; gap: 0.4rem;">
                          ${oLogo ? `
                            <div style="width: 40px; height: 22px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 5px; display: flex; align-items: center; justify-content: center; padding: 2px 3px; flex-shrink: 0;">
                              <img src="${oLogo}" alt="${this.escapeHtml(oBrand)}" style="max-width: 100%; max-height: 16px; object-fit: contain;">
                            </div>
                          ` : ''}
                          <span class="badge" style="background: #fef3c7; color: #b45309; border: 1px solid #fde68a; padding: 0.15rem 0.45rem; border-radius: 5px; font-size: 0.72rem; font-weight: 850;">${this.escapeHtml(oBrand)}</span>
                        </div>
                      </td>
                      <td style="font-weight: 850; color: #0284c7; font-family: monospace; font-size: 0.88rem; padding: 0.75rem; cursor: pointer;" onclick="OverallCataloguePortal.showPartDetails('${this.escapeJs(oPartNo)}')">
                        ${this.escapeHtml(oPartNo)} 🔗
                      </td>
                      <td style="color: #1e293b; font-weight: 600; font-size: 0.82rem; padding: 0.75rem; max-width: 260px;">
                        ${this.escapeHtml(oDesc)}
                      </td>
                      <td style="font-weight: 850; color: #059669; font-size: 0.88rem; text-align: right; font-family: 'Outfit', sans-serif; padding: 0.75rem;">
                        ${oMrp}
                      </td>
                      <td style="color: #475569; font-size: 0.8rem; padding: 0.75rem; font-weight: 600;">
                        ${this.escapeHtml(oVehicle)}
                      </td>
                      <td style="text-align: center; padding: 0.75rem;">
                        <button type="button" class="btn btn-primary" onclick="OverallCataloguePortal.selectSuggestion('${this.escapeJs(oPartNo)}')" style="padding: 0.35rem 0.65rem; font-size: 0.75rem; font-weight: 800; border-radius: 6px; cursor: pointer; background: #0284c7; color: #ffffff; border: none;">
                          Select Part
                        </button>
                      </td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
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

  exportToExcel() {
    return this.exportExcel();
  },

  async exportExcel() {
    if (window.App && window.App.showToast) {
      window.App.showToast("Preparing Master Catalogue Excel export...", "info");
    }

    try {
      const params = new URLSearchParams({
        page: 1,
        limit: 2500
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
        if (window.App && window.App.showToast) {
          window.App.showToast("No records to export with current filters.", "warning");
        } else {
          alert("No records to export with current filters.");
        }
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
