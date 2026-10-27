/**
 * AutoNexa OEM ⇄ OES Conversion Portal
 * =====================================
 * Bidirectional automotive conversion engine:
 * 1. Supports OEM part number input -> Displays OEM Benchmark + Verified OES Alternatives
 * 2. Supports OES part number input -> Displays Searched OES Part + Respective Other OES Alternatives + Dealership OEM Part at the end
 * 3. Enforces Master Brand Classification: Primary (Tier 1) > PL (Tier 2) > Secondary (Tier 3)
 * 4. Displays official Brand SVG Logos, vehicle fitment scope, and technical specifications.
 */

const OemToOesPortal = {
  currentData: null,
  activeFilterModel: 'ALL',

  // Master Brand to SVG Logo Mapping
  brandLogos: {
    'BOSCH': '/images/brands/bosch.svg',
    'DELPHI TECH': '/images/brands/delphi.svg',
    'DELPHI': '/images/brands/delphi.svg',
    'DENSO': '/images/brands/denso.svg',
    'FILTRON': '/images/brands/filtron.svg',
    'INA': '/images/brands/ina.svg',
    'JK TYRE': '/images/brands/jk_tyre.svg',
    'KK LIGHTINGS': '/images/brands/kk_lightings.svg',
    'LUK': '/images/brands/luk.svg',
    'MONROE': '/images/brands/monroe.svg',
    'RANE MADRAS LIMITED': '/images/brands/rane.svg',
    'RANE': '/images/brands/rane.svg',
    'VALEO': '/images/brands/valeo.svg',
    'PHC VALEO': '/images/brands/valeo.svg',
    'ZF': '/images/brands/zf.svg',
    'AUTONEXA': '/images/icons/menu_home.jpg',
    'MYTVS': '/images/brands/mytvs.svg',
    'MYTVS MOUNTING': '/images/brands/mytvs.svg',
    'TVS MOBILITY': '/images/brands/mytvs.svg',
    'UCAP': '/images/brands/ucap.svg',
    'PUROLATOR': '/images/brands/purolator.svg',
    'ELOFIC': '/images/brands/elofic.svg',
    'MAHLE': '/images/brands/mahle.svg',
    'BREMBO': '/images/brands/brembo.svg',
    'GABRIEL': '/images/brands/gabriel.svg',
    'TALBROS': '/images/brands/talbros.svg',
    'SOFIMA': '/images/brands/sofima.svg',
    'ZIP': '/images/brands/zip.svg',
    'FAG': '/images/brands/fag.svg',
    'BRAKES INDIA': '/images/brands/brakes_india.svg',
    'FERODO': '/images/brands/ferodo.svg',
    'CONTITECH': '/images/brands/contitech.svg',
    'BANDO': '/images/brands/bando.svg',
    'SKF': '/images/brands/skf.svg',
    'LUMAX': '/images/brands/lumax.svg',
    'MINDA': '/images/brands/minda.svg',
    'UNO MINDA': '/images/brands/minda.svg',
    'EXEDY': '/images/brands/exedy.svg',
    'CEEKAY': '/images/brands/ceekay.svg',
    'HELLA': '/images/brands/hella.svg',
    'NGK': '/images/brands/ngk.svg',
    'OSRAM': '/images/brands/osram.svg',
    'ROOTS': '/images/brands/roots.svg',
    'SACHS': '/images/brands/sachs.svg',
    'TRW': '/images/brands/trw.svg',
    'TVS GIRLING': '/images/brands/tvs_girling.svg',
    'WURTH': '/images/brands/wurth.svg',
    'CASTROL': '/images/brands/castrol.svg',
    'MARUTI SUZUKI': 'images/makes/maruti.png',
    'MARUTI': 'images/makes/maruti.png',
    'HYUNDAI': 'images/makes/hyundai.png',
    'TATA': 'images/makes/tata.png',
    'MAHINDRA': 'images/makes/mahindra.png',
    'HONDA': 'images/makes/honda.png',
    'TOYOTA': 'images/makes/toyota.png',
    'VOLKSWAGEN': 'images/makes/volkswagen.jpg',
    'SKODA': 'images/makes/skoda.jpg',
    'FORD': 'images/makes/ford.png',
    'RENAULT': 'images/makes/renault.png',
    'NISSAN': 'images/makes/nissan.png',
    'KIA': 'images/makes/kia.png',
    'MG': 'images/makes/mg.png',
    'MORRIS GARAGES': 'images/makes/mg.png',
    'BMW': 'images/makes/bmw.png',
    'AUDI': 'images/makes/audi.png',
    'MERCEDES': 'images/makes/mercedes.jpg',
    'MERCEDES BENZ': 'images/makes/mercedes.jpg',
    'CHEVROLET': 'images/makes/chevrolet.png',
    'FIAT': 'images/makes/fiat.jpg',
    'JEEP': 'images/makes/jeep.png',
    'FORCE': 'images/makes/force.png',
    'FORCE MOTORS': 'images/makes/force.png',
    'ASHOK LEYLAND': 'images/makes/ashok_leyland.png',
    'VOLVO': 'images/makes/volvo.png'
  },

  getBrandLogoUrl(brandName) {
    if (!brandName) return '';
    const clean = String(brandName).toUpperCase().trim();
    if (this.brandLogos[clean]) return this.brandLogos[clean];
    for (const [k, url] of Object.entries(this.brandLogos)) {
      if (clean === k || clean.includes(k) || k.includes(clean)) {
        return url;
      }
    }
    return '';
  },

  init() {
    const input = document.getElementById('oem-oes-search-input');
    if (input && input.value.trim().length > 0) {
      this.search();
    }
  },

  clear() {
    const input = document.getElementById('oem-oes-search-input');
    if (input) {
      input.value = '';
      input.focus();
    }
    this.currentData = null;
    this.activeFilterModel = 'ALL';
    const container = document.getElementById('oem-oes-results-container');
    if (container) {
      container.innerHTML = `
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 16px; padding: 3.5rem 2rem; text-align: center; color: #64748b; font-size: 0.95rem; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.02);">
          <div style="font-size: 2.4rem; margin-bottom: 0.75rem;">⇄</div>
          <div style="font-weight: 800; color: #1e293b; font-size: 1.15rem; margin-bottom: 0.4rem;">Enter an OEM or OES Part Number to Convert</div>
          <div style="color: #64748b; font-size: 0.85rem; max-width: 600px; margin: 0 auto; line-height: 1.6;">
            <strong>OEM Part Examples:</strong> 
            <span style="font-family: monospace; font-weight: 800; color: #0284c7; cursor: pointer; text-decoration: underline;" onclick="OemToOesPortal.search('4110002857')">4110002857</span> (Hyundai Clutch), 
            <span style="font-family: monospace; font-weight: 800; color: #0284c7; cursor: pointer; text-decoration: underline;" onclick="OemToOesPortal.search('16510M68K00')">16510M68K00</span> (Maruti Oil Filter), or 
            <span style="font-family: monospace; font-weight: 800; color: #0284c7; cursor: pointer; text-decoration: underline;" onclick="OemToOesPortal.search('58510C4930')">58510-C4930</span> (Master Cylinder)<br>
            <strong>OES Part Examples:</strong> 
            <span style="font-family: monospace; font-weight: 800; color: #059669; cursor: pointer; text-decoration: underline;" onclick="OemToOesPortal.search('AM13001')">AM13001</span> (Filtron Air Filter), 
            <span style="font-family: monospace; font-weight: 800; color: #059669; cursor: pointer; text-decoration: underline;" onclick="OemToOesPortal.search('TAF90143MV')">TAF90143MV</span> (Talbros Air Filter), or 
            <span style="font-family: monospace; font-weight: 800; color: #059669; cursor: pointer; text-decoration: underline;" onclick="OemToOesPortal.search('0986AB8552E7A')">0986AB8552E7A</span> (Bosch Brake Cylinder)
          </div>
        </div>
      `;
    }
  },

  async search(queryOverride) {
    const input = document.getElementById('oem-oes-search-input');
    const container = document.getElementById('oem-oes-results-container');
    if (!container) return;

    const query = (queryOverride || (input ? input.value : '')).trim();
    if (!query) {
      this.clear();
      return;
    }

    if (input && queryOverride) {
      input.value = queryOverride;
    }

    container.innerHTML = `
      <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 16px; padding: 3rem; text-align: center; color: #0284c7; font-weight: 800; font-size: 1rem; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.02);">
        <div style="display: inline-block; animation: spin 1s linear infinite; font-size: 1.8rem; margin-bottom: 0.5rem;">⚡</div>
        <div>Searching 23.6M Live Catalog Records for OEM ⇄ OES Interchanges...</div>
      </div>
    `;

    try {
      const res = await fetch(`/api/oem-to-oes/convert?query=${encodeURIComponent(query)}`);
      const data = await res.json();

      if (!data || data.found !== true) {
        container.innerHTML = `
          <div style="background: #fff5f5; border: 1.5px solid #fed7d7; border-radius: 16px; padding: 2.5rem; text-align: center; color: #c53030; font-weight: 750; font-size: 0.95rem;">
            ⚠️ No OEM or OES part found matching '${this.escapeHtml(query)}' in the database.
          </div>
        `;
        return;
      }

      this.currentData = data;
      this.activeFilterModel = 'ALL';
      this.renderResults(data, query);
    } catch (err) {
      console.error('OemToOes search error:', err);
      container.innerHTML = `
        <div style="background: #fff5f5; border: 1.5px solid #fed7d7; border-radius: 16px; padding: 2.5rem; text-align: center; color: #c53030; font-weight: 750; font-size: 0.95rem;">
          ⚠️ Error connecting to catalog service: ${this.escapeHtml(err.message)}
        </div>
      `;
    }
  },

  filterByModel(modelName) {
    this.activeFilterModel = modelName;
    if (this.currentData) {
      this.renderResults(this.currentData, this.currentData.query);
    }
  },

  renderResults(data, query) {
    const container = document.getElementById('oem-oes-results-container');
    if (!container) return;

    const isOesInput = data.is_oes_input === true || data.query_type === 'OES';
    const inputPart = data.input_part || {};
    const oem = data.oem || {};
    const respectiveOemParts = data.respective_oem_parts || [];
    let oesAlts = data.oes_alternatives || [];
    const mappedModels = data.mapped_models || [];

    const oemMrp = Number(oem.mrp || 0);
    const oemPriceStr = oemMrp > 0 ? `₹${oemMrp.toLocaleString('en-IN')}` : 'Price on Request';

    // Model filter logic
    if (this.activeFilterModel && this.activeFilterModel !== 'ALL') {
      const filtered = oesAlts.filter(alt => (alt.verified_for_model || '').toUpperCase() === this.activeFilterModel.toUpperCase());
      if (filtered.length > 0) {
        oesAlts = filtered;
      }
    }

    // 1. TOP CARD GENERATION
    let topCardHtml = '';
    if (isOesInput) {
      // Searched OES Part Input Card
      const inBrand = inputPart.brand || '';
      const inLogoUrl = this.getBrandLogoUrl(inBrand);
      const inPrice = Number(inputPart.mrp || 0);
      const inPriceStr = inPrice > 0 ? `₹${inPrice.toLocaleString('en-IN')}` : '—';
      
      let inTierBadge = '';
      const bCat = inputPart.brand_category || '';
      if (bCat === 'PRIMARY') {
        inTierBadge = `<span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 3px 8px; border-radius: 6px; font-size: 0.70rem; font-weight: 850;">⭐ TIER 1: PRIMARY OE</span>`;
      } else if (bCat === 'PL') {
        inTierBadge = `<span style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; padding: 3px 8px; border-radius: 6px; font-size: 0.70rem; font-weight: 850;">🏷️ TIER 2: PL (CERTIFIED OES)</span>`;
      } else {
        inTierBadge = `<span style="background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; padding: 3px 8px; border-radius: 6px; font-size: 0.70rem; font-weight: 850;">📦 TIER 3: SECONDARY AFTERMARKET</span>`;
      }

      const inLogoHtml = inLogoUrl ? `
        <div style="width: 80px; height: 38px; background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 3px 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); flex-shrink: 0;">
          <img src="${inLogoUrl}" alt="${this.escapeHtml(inBrand)}" style="max-width: 100%; max-height: 30px; object-fit: contain;">
        </div>
      ` : `
        <div style="width: 80px; height: 38px; background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 2px 4px; flex-shrink: 0;">
          <span style="font-weight: 900; font-size: 0.75rem; color: #334155;">${this.escapeHtml(inBrand.substring(0, 8))}</span>
        </div>
      `;

      topCardHtml = `
        <div style="background: #ffffff; border: 1.5px solid #c7d2fe; border-radius: 16px; padding: 1.75rem; box-shadow: 0 4px 20px -2px rgba(99, 102, 241, 0.08);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1.5rem; flex-wrap: wrap;">
            
            <div style="flex: 1; min-width: 280px;">
              <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; flex-wrap: wrap;">
                <span style="font-size: 0.72rem; font-weight: 850; background: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; padding: 3px 9px; border-radius: 6px; letter-spacing: 0.4px;">
                  🔍 SEARCHED OES PART INPUT
                </span>
                ${inTierBadge}
                <div style="display: flex; align-items: center; gap: 0.4rem;">
                  ${inLogoHtml}
                  <span style="font-weight: 900; font-size: 0.95rem; color: #1e293b;">${this.escapeHtml(inBrand)}</span>
                </div>
              </div>
              <h3 style="font-size: 1.35rem; font-weight: 900; color: #0f172a; margin: 0 0 0.4rem; font-family: 'Outfit', sans-serif; letter-spacing: -0.2px;">
                ${this.escapeHtml(inputPart.desc || 'Aftermarket OES Component')}
              </h3>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem; flex-wrap: wrap;">
                <span style="font-family: monospace; font-size: 1.15rem; font-weight: 900; color: #4338ca; background: #eef2ff; padding: 3px 10px; border-radius: 6px; border: 1px solid #c7d2fe;">
                  ${this.escapeHtml(inputPart.partNo)}
                </span>
                ${inputPart.mfg_part_no && inputPart.mfg_part_no !== inputPart.partNo ? `
                  <span style="font-size: 0.82rem; color: #475569; font-weight: 750; background: #f8fafc; border: 1px solid #e2e8f0; padding: 3px 8px; border-radius: 6px;">
                    Mfr SKU: <strong style="font-family: monospace; color: #0f172a;">${this.escapeHtml(inputPart.mfg_part_no)}</strong>
                  </span>
                ` : ''}
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(inputPart.mfg_part_no || inputPart.partNo)}', this)" style="padding: 3px 9px; font-size: 0.72rem; font-weight: 750; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #334155; cursor: pointer; transition: all 0.15s;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">📋 Copy</button>
              </div>
              <div style="font-size: 0.82rem; color: #475569; line-height: 1.4;">
                Component: <strong style="color: #0f172a;">${this.escapeHtml(inputPart.component || '')}</strong> &nbsp;•&nbsp; 
                System: <strong style="color: #0f172a;">${this.escapeHtml(inputPart.aggregate || '')}</strong> &nbsp;•&nbsp; 
                Application: <strong style="color: #0f172a;">${this.escapeHtml(inputPart.vehicle || 'Compatible Models')}</strong>
              </div>
            </div>

            <div style="text-align: right; min-width: 170px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.25rem;">
              <div style="font-size: 0.74rem; color: #64748b; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">OES Retail MRP</div>
              <div style="font-size: 1.75rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif; margin-top: 0.15rem;">
                ${inPriceStr}
              </div>
              <div style="font-size: 0.68rem; color: #4338ca; font-weight: 750; margin-top: 0.2rem;">Aftermarket Retail Reference</div>
            </div>

          </div>
        </div>
      `;
    } else {
      // Dealership OEM Benchmark Card
      const oemBrandClean = oem.brand ? oem.brand.replace(' GENUINE', '').trim() : '';
      const oemLogoUrl = this.getBrandLogoUrl(oemBrandClean);
      const oemLogoHtml = oemLogoUrl ? `
        <div style="width: 80px; height: 38px; background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 3px 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); flex-shrink: 0;">
          <img src="${oemLogoUrl}" alt="${this.escapeHtml(oemBrandClean)}" style="max-width: 100%; max-height: 30px; object-fit: contain;">
        </div>
      ` : '';

      topCardHtml = `
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 16px; padding: 1.75rem; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1.5rem; flex-wrap: wrap;">
            
            <div style="flex: 1; min-width: 280px;">
              <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; flex-wrap: wrap;">
                <span style="font-size: 0.72rem; font-weight: 850; background: #fef2f2; color: #dc2626; border: 1px solid #fecdd3; padding: 3px 9px; border-radius: 6px; letter-spacing: 0.4px;">
                  DEALERSHIP OEM BENCHMARK
                </span>
                ${oemLogoHtml}
                <span style="font-size: 0.72rem; font-weight: 800; background: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 6px;">
                  ${this.escapeHtml(oem.brand)}
                </span>
              </div>
              <h3 style="font-size: 1.35rem; font-weight: 900; color: #0f172a; margin: 0 0 0.4rem; font-family: 'Outfit', sans-serif; letter-spacing: -0.2px;">
                ${this.escapeHtml(oem.desc)}
              </h3>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem;">
                <span style="font-family: monospace; font-size: 1.15rem; font-weight: 900; color: #0f172a; background: #f8fafc; padding: 3px 10px; border-radius: 6px; border: 1px solid #cbd5e1;">
                  ${this.escapeHtml(oem.partNo)}
                </span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(oem.partNo)}', this)" style="padding: 3px 9px; font-size: 0.72rem; font-weight: 750; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #334155; cursor: pointer; transition: all 0.15s;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">📋 Copy</button>
              </div>
              <div style="font-size: 0.82rem; color: #475569; line-height: 1.4;">
                Component: <strong style="color: #0f172a;">${this.escapeHtml(oem.component || '')}</strong> &nbsp;•&nbsp; 
                System: <strong style="color: #0f172a;">${this.escapeHtml(oem.aggregate || '')}</strong> &nbsp;•&nbsp; 
                Application: <strong style="color: #0f172a;">${this.escapeHtml(oem.vehicle || 'All Compatible Models')}</strong>
              </div>
            </div>

            <div style="text-align: right; min-width: 170px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.25rem;">
              <div style="font-size: 0.74rem; color: #64748b; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Official Dealership MRP</div>
              <div style="font-size: 1.75rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif; margin-top: 0.15rem;">
                ${oemPriceStr}
              </div>
              <div style="font-size: 0.68rem; color: #059669; font-weight: 750; margin-top: 0.2rem;">Authentic Dealership Reference</div>
            </div>

          </div>
        </div>
      `;
    }

    // 2. MULTI-MODEL COMPATIBILITY CHIPS
    let modelChipsHtml = '';
    if (mappedModels.length > 0) {
      const allActive = this.activeFilterModel === 'ALL';
      modelChipsHtml = `
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.25rem; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
            <div style="font-size: 0.85rem; font-weight: 850; color: #0f172a; display: flex; align-items: center; gap: 0.45rem;">
              <span style="font-size: 1rem;">🚗</span>
              <span>Application Fitment — Mapped Across <strong>${mappedModels.length} Models</strong> (${this.escapeHtml(mappedModels[0]?.make || '')})</span>
            </div>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
            <button type="button" onclick="OemToOesPortal.filterByModel('ALL')" style="padding: 6px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 850; border: 1.5px solid ${allActive ? '#0284c7' : '#cbd5e1'}; background: ${allActive ? '#0284c7' : '#ffffff'}; color: ${allActive ? '#ffffff' : '#334155'}; cursor: pointer; transition: all 0.15s; box-shadow: ${allActive ? '0 2px 6px rgba(2, 132, 199, 0.25)' : 'none'};">
              All Mapped Models (${mappedModels.reduce((acc, m) => acc + (m.variant_count || 1), 0)} Variants)
            </button>
            ${mappedModels.map(m => {
              const isActive = this.activeFilterModel.toUpperCase() === m.model.toUpperCase();
              return `
                <button type="button" onclick="OemToOesPortal.filterByModel('${this.escapeJs(m.model)}')" style="padding: 6px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 800; border: 1.5px solid ${isActive ? '#0284c7' : '#e2e8f0'}; background: ${isActive ? '#e0f2fe' : '#ffffff'}; color: ${isActive ? '#0369a1' : '#475569'}; cursor: pointer; transition: all 0.15s;" onmouseover="if(!${isActive}) this.style.background='#f8fafc'" onmouseout="if(!${isActive}) this.style.background='#ffffff'">
                  ${this.escapeHtml(m.model)} <span style="font-size: 0.70rem; opacity: 0.75; font-weight: 600;">(${m.variant_count} trims)</span>
                </button>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // 3. TABLE ROWS FOR OES ALTERNATIVES
    let tableRows = '';
    if (oesAlts.length > 0) {
      tableRows = oesAlts.map(alt => {
        const altPrice = Number(alt.mrp || alt.price || 0);
        const priceStr = altPrice > 0 ? `₹${altPrice.toLocaleString('en-IN')}` : '—';
        const brandClean = alt.brand || '';
        const logoUrl = this.getBrandLogoUrl(brandClean);

        const logoHtml = logoUrl ? `
          <div style="width: 76px; height: 36px; background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 3px 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); flex-shrink: 0;">
            <img src="${logoUrl}" alt="${this.escapeHtml(brandClean)}" style="max-width: 100%; max-height: 28px; object-fit: contain;">
          </div>
        ` : `
          <div style="width: 76px; height: 36px; background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 2px 4px; flex-shrink: 0;">
            <span style="font-weight: 900; font-size: 0.72rem; color: #334155;">${this.escapeHtml(brandClean.substring(0, 8))}</span>
          </div>
        `;

        let tierBadge = '';
        const tierStr = alt.tier || '';
        if (tierStr.includes('Primary') || tierStr.includes('Tier-1')) {
          tierBadge = `<span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 2px 7px; border-radius: 6px; font-size: 0.68rem; font-weight: 850; letter-spacing: 0.3px;">⭐ TIER 1: PRIMARY OE</span>`;
        } else if (tierStr.includes('PL') || tierStr.includes('Private Label') || tierStr.includes('MYTVS') || tierStr.includes('AUTONEXA')) {
          tierBadge = `<span style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; padding: 2px 7px; border-radius: 6px; font-size: 0.68rem; font-weight: 850; letter-spacing: 0.3px;">🏷️ TIER 2: PL (CERTIFIED OES)</span>`;
        } else if (tierStr.includes('Secondary')) {
          tierBadge = `<span style="background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; padding: 2px 7px; border-radius: 6px; font-size: 0.68rem; font-weight: 850; letter-spacing: 0.3px;">📦 TIER 3: SECONDARY</span>`;
        } else {
          tierBadge = `<span style="background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; padding: 2px 7px; border-radius: 6px; font-size: 0.68rem; font-weight: 750;">AFTERMARKET</span>`;
        }

        let prodClassHtml = '';
        if (tierStr.includes('Primary') || tierStr.includes('Tier-1')) {
          prodClassHtml = `
            <div>
              <div style="font-weight: 800; font-size: 0.82rem; color: #0f172a; display: flex; align-items: center; gap: 4px;">
                <span style="color: #047857;">⭐</span> Factory OE Supplier Grade
              </div>
              <div style="font-size: 0.72rem; color: #64758b; margin-top: 2px;">
                Exact engineering formulation certified to automotive new-car standards.
              </div>
            </div>
          `;
        } else if (tierStr.includes('PL') || tierStr.includes('Private Label') || tierStr.includes('MYTVS') || tierStr.includes('AUTONEXA')) {
          prodClassHtml = `
            <div>
              <div style="font-weight: 800; font-size: 0.82rem; color: #1d4ed8; display: flex; align-items: center; gap: 4px;">
                <span style="color: #1d4ed8;">🏷️</span> Enterprise Quality Benchmark
              </div>
              <div style="font-size: 0.72rem; color: #64758b; margin-top: 2px;">
                Private label engineered for durability with high retail workshop margins.
              </div>
            </div>
          `;
        } else {
          prodClassHtml = `
            <div>
              <div style="font-weight: 800; font-size: 0.82rem; color: #475569; display: flex; align-items: center; gap: 4px;">
                <span style="color: #7e22ce;">📦</span> Certified Aftermarket Replacement
              </div>
              <div style="font-size: 0.72rem; color: #64748b; margin-top: 2px;">
                Standard aftermarket alternative meeting OE form-fit-function criteria.
              </div>
            </div>
          `;
        }

        const fitmentScope = alt.fitment_scope || alt.verified_for_model || 'All Compatible Variants';

        return `
          <tr style="border-bottom: 1px solid #f1f5f9; transition: all 0.15s ease;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
            
            <!-- Col 1: Brand & Logo -->
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle;">
              <div style="display: flex; align-items: center; gap: 0.85rem;">
                ${logoHtml}
                <div>
                  <div style="font-weight: 900; color: #0f172a; font-size: 0.95rem; font-family: 'Outfit', sans-serif;">
                    ${this.escapeHtml(brandClean)}
                  </div>
                  <div style="margin-top: 0.25rem;">
                    ${tierBadge}
                  </div>
                </div>
              </div>
            </td>

            <!-- Col 2: OES Part Number & Specifications -->
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle;">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-family: monospace; font-size: 1rem; font-weight: 900; color: #0284c7; background: #f0f9ff; padding: 3px 8px; border-radius: 6px; border: 1px solid #bae6fd;">
                  ${this.escapeHtml(alt.partNo)}
                </span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(alt.partNo)}', this)" style="padding: 3px 8px; font-size: 0.70rem; font-weight: 750; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #475569; cursor: pointer; transition: all 0.15s;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">📋 Copy</button>
              </div>
              <div style="font-size: 0.78rem; color: #1e293b; margin-top: 0.35rem; font-weight: 600;">
                ${this.escapeHtml(alt.desc || '')}
              </div>
              <div style="font-size: 0.70rem; color: #64748b; margin-top: 0.2rem;">
                Category: <span style="color: #475569; font-weight: 700;">${this.escapeHtml(alt.component || oem.component || '')}</span>
                ${alt.aggregate ? ` &nbsp;•&nbsp; System: <span style="color: #475569; font-weight: 700;">${this.escapeHtml(alt.aggregate)}</span>` : ''}
              </div>
            </td>

            <!-- Col 3: Vehicle Fitment Scope -->
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle;">
              <div style="font-size: 0.80rem; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 0.35rem;">
                <span>🚗</span>
                <span>${this.escapeHtml(fitmentScope)}</span>
              </div>
            </td>

            <!-- Col 4: Product Classification -->
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle;">
              ${prodClassHtml}
            </td>

            <!-- Col 5: OES MRP Price -->
            <td style="padding: 1.1rem 1.25rem; text-align: right; vertical-align: middle;">
              <div style="font-weight: 900; color: #0f172a; font-size: 1.3rem; font-family: 'Outfit', sans-serif;">
                ${priceStr}
              </div>
              <div style="font-size: 0.68rem; color: #94a3b8; font-weight: 750; text-transform: uppercase;">Retail MRP</div>
            </td>

          </tr>
        `;
      }).join('');
    } else {
      tableRows = `
        <tr>
          <td colspan="5" style="padding: 3rem; text-align: center; color: #64748b; font-size: 0.9rem;">
            No direct OES alternatives currently listed for this specific filter.
          </td>
        </tr>
      `;
    }

    // 4. AT LAST: RESPECTIVE DEALERSHIP OEM GENUINE PART(S) SECTION
    let oemSectionHtml = '';
    if (isOesInput) {
      let oemRowsHtml = '';
      if (respectiveOemParts.length > 0) {
        oemRowsHtml = respectiveOemParts.map(op => {
          const opPrice = Number(op.mrp || 0);
          const opPriceStr = opPrice > 0 ? `₹${opPrice.toLocaleString('en-IN')}` : 'Price on Request';
          const opBrand = op.brand || '';
          const opLogoUrl = this.getBrandLogoUrl(opBrand);
          const opLogoHtml = opLogoUrl ? `
            <div style="width: 76px; height: 36px; background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 3px 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); flex-shrink: 0;">
              <img src="${opLogoUrl}" alt="${this.escapeHtml(opBrand)}" style="max-width: 100%; max-height: 28px; object-fit: contain;">
            </div>
          ` : `
            <div style="width: 76px; height: 36px; background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 2px 4px; flex-shrink: 0;">
              <span style="font-weight: 900; font-size: 0.72rem; color: #0f172a;">${this.escapeHtml(opBrand.substring(0, 10))}</span>
            </div>
          `;

          return `
            <tr style="border-bottom: 1px solid #f1f5f9; background: #ffffff; transition: all 0.15s ease;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='#ffffff'">
              
              <!-- OEM Brand & Logo -->
              <td style="padding: 1.1rem 1.25rem; vertical-align: middle; width: 230px;">
                <div style="display: flex; align-items: center; gap: 0.85rem;">
                  ${opLogoHtml}
                  <div>
                    <div style="font-weight: 900; color: #0f172a; font-size: 0.95rem; font-family: 'Outfit', sans-serif;">
                      ${this.escapeHtml(opBrand)} GENUINE
                    </div>
                    <div style="margin-top: 0.25rem;">
                      <span style="background: #fef2f2; color: #dc2626; border: 1px solid #fecdd3; padding: 2px 7px; border-radius: 6px; font-size: 0.68rem; font-weight: 850; letter-spacing: 0.3px;">
                        🏭 OEM BENCHMARK
                      </span>
                    </div>
                  </div>
                </div>
              </td>

              <!-- OEM Part Number & Description -->
              <td style="padding: 1.1rem 1.25rem; vertical-align: middle;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  <span style="font-family: monospace; font-size: 1rem; font-weight: 900; color: #0f172a; background: #f8fafc; padding: 3px 8px; border-radius: 6px; border: 1px solid #cbd5e1;">
                    ${this.escapeHtml(op.partNo)}
                  </span>
                  <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(op.partNo)}', this)" style="padding: 3px 8px; font-size: 0.70rem; font-weight: 750; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #475569; cursor: pointer; transition: all 0.15s;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">📋 Copy</button>
                </div>
                <div style="font-size: 0.78rem; color: #1e293b; margin-top: 0.35rem; font-weight: 600;">
                  ${this.escapeHtml(op.desc || '')}
                </div>
                <div style="font-size: 0.70rem; color: #64748b; margin-top: 0.2rem;">
                  Category: <span style="color: #475569; font-weight: 700;">${this.escapeHtml(op.component || '')}</span>
                  ${op.aggregate ? ` &nbsp;•&nbsp; System: <span style="color: #475569; font-weight: 700;">${this.escapeHtml(op.aggregate)}</span>` : ''}
                </div>
              </td>

              <!-- Vehicle Fitment -->
              <td style="padding: 1.1rem 1.25rem; vertical-align: middle; width: 220px;">
                <div style="font-size: 0.80rem; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 0.35rem;">
                  <span>🚗</span>
                  <span>${this.escapeHtml(op.model || '')} ${op.fuel_type ? `(${op.fuel_type})` : ''}</span>
                </div>
                <div style="font-size: 0.70rem; color: #64748b; margin-top: 0.25rem;">
                  ${op.year_range ? `Model Years: ${op.year_range}` : 'Factory Genuine Fitment'}
                </div>
              </td>

              <!-- Classification -->
              <td style="padding: 1.1rem 1.25rem; vertical-align: middle; width: 220px;">
                <div style="font-weight: 800; font-size: 0.82rem; color: #0f172a; display: flex; align-items: center; gap: 4px;">
                  <span style="color: #dc2626;">🏛️</span> Authorized Dealership Genuine
                </div>
                <div style="font-size: 0.72rem; color: #64748b; margin-top: 2px;">
                  Authentic vehicle manufacturer part number cross-referenced to this OES component.
                </div>
              </td>

              <!-- OEM Dealership MRP -->
              <td style="padding: 1.1rem 1.25rem; text-align: right; vertical-align: middle; width: 140px;">
                <div style="font-weight: 900; color: #0f172a; font-size: 1.3rem; font-family: 'Outfit', sans-serif;">
                  ${opPriceStr}
                </div>
                <div style="font-size: 0.68rem; color: #94a3b8; font-weight: 750; text-transform: uppercase;">Dealership MRP</div>
              </td>

            </tr>
          `;
        }).join('');
      } else if (oem && (oem.mrp > 0 || oem.brand)) {
        const oemBrandClean = oem.brand ? oem.brand.replace(' GENUINE', '').trim() : '';
        const oemLogoUrl = this.getBrandLogoUrl(oemBrandClean);
        const oemLogoHtml = oemLogoUrl ? `
          <div style="width: 76px; height: 36px; background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 3px 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); flex-shrink: 0;">
            <img src="${oemLogoUrl}" alt="${this.escapeHtml(oemBrandClean)}" style="max-width: 100%; max-height: 28px; object-fit: contain;">
          </div>
        ` : `
          <div style="width: 76px; height: 36px; background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; display: flex; align-items: center; justify-content: center; padding: 2px 4px; flex-shrink: 0;">
            <span style="font-weight: 900; font-size: 0.72rem; color: #0f172a;">${this.escapeHtml(oemBrandClean.substring(0, 10))}</span>
          </div>
        `;

        oemRowsHtml = `
          <tr style="border-bottom: 1px solid #f1f5f9; background: #ffffff; transition: all 0.15s ease;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='#ffffff'">
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle; width: 230px;">
              <div style="display: flex; align-items: center; gap: 0.85rem;">
                ${oemLogoHtml}
                <div>
                  <div style="font-weight: 900; color: #0f172a; font-size: 0.95rem; font-family: 'Outfit', sans-serif;">
                    ${this.escapeHtml(oem.brand)}
                  </div>
                  <div style="margin-top: 0.25rem;">
                    <span style="background: #fef2f2; color: #dc2626; border: 1px solid #fecdd3; padding: 2px 7px; border-radius: 6px; font-size: 0.68rem; font-weight: 850; letter-spacing: 0.3px;">
                      🏭 OEM BENCHMARK
                    </span>
                  </div>
                </div>
              </div>
            </td>
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle;">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-family: monospace; font-size: 1rem; font-weight: 900; color: #0f172a; background: #f8fafc; padding: 3px 8px; border-radius: 6px; border: 1px solid #cbd5e1;">${this.escapeHtml(oem.partNo)}</span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(oem.partNo)}', this)" style="padding: 3px 8px; font-size: 0.70rem; font-weight: 750; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #475569; cursor: pointer;">📋 Copy</button>
              </div>
              <div style="font-size: 0.78rem; color: #1e293b; margin-top: 0.35rem; font-weight: 600;">${this.escapeHtml(oem.desc)}</div>
            </td>
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle; width: 220px;">
              <div style="font-size: 0.80rem; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 0.35rem;">
                <span>🚗</span> <span>${this.escapeHtml(oem.vehicle)}</span>
              </div>
            </td>
            <td style="padding: 1.1rem 1.25rem; vertical-align: middle; width: 220px;">
              <div style="font-weight: 800; font-size: 0.82rem; color: #0f172a; display: flex; align-items: center; gap: 4px;">
                <span style="color: #dc2626;">🏛️</span> Authorized Dealership Genuine
              </div>
            </td>
            <td style="padding: 1.1rem 1.25rem; text-align: right; vertical-align: middle; font-weight: 900; font-size: 1.25rem; width: 140px;">${oemPriceStr}</td>
          </tr>
        `;
      } else {
        oemRowsHtml = `
          <tr>
            <td colspan="5" style="padding: 2.5rem; text-align: center; color: #64748b; font-size: 0.88rem;">
              Dealership OEM benchmark part directly cross-referenced via vehicle assembly specification.
            </td>
          </tr>
        `;
      }

      oemSectionHtml = `
        <!-- AT LAST: Respective Dealership OEM Genuine Part(s) -->
        <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);">
          <div style="padding: 1.1rem 1.5rem; background: linear-gradient(135deg, #0f172a, #1e293b); color: #ffffff; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <div style="font-size: 1.05rem; font-weight: 900; font-family: 'Outfit', sans-serif; display: flex; align-items: center; gap: 0.5rem;">
                <span>🏭</span>
                <span>Corresponding Dealership OEM Genuine Part(s)</span>
              </div>
              <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">
                Official OEM Genuine part numbers cross-referenced to the searched OES component
              </div>
            </div>
            <span style="font-size: 0.72rem; color: #ffffff; font-weight: 850; background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.25); padding: 4px 10px; border-radius: 6px;">
              AUTHENTIC DEALERSHIP SPECIFICATION
            </span>
          </div>

          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; min-width: 800px;">
              <thead>
                <tr style="border-bottom: 1.5px solid #e2e8f0; background: #f8fafc;">
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.74rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.4px;">Dealership OEM Brand</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.74rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.4px;">OEM Part No &amp; Description</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.74rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.4px;">Vehicle Application</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.74rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.4px;">Classification</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: right; font-size: 0.74rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.4px;">Dealership MRP</th>
                </tr>
              </thead>
              <tbody>
                ${oemRowsHtml}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    // 5. ASSEMBLE COMPLETE VIEW
    const altTableTitle = isOesInput 
      ? `Verified Respective Other OES Alternatives & Interchanges (${oesAlts.length} Options)`
      : `Verified OES Equivalents & Direct Interchanges (${oesAlts.length} Options)`;

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.25rem;">
        
        <!-- Top Card: Searched OES Input OR Dealership OEM Benchmark -->
        ${topCardHtml}

        <!-- Multi-Model Compatibility Chips -->
        ${modelChipsHtml}

        <!-- Verified OES Equivalents Table (5 Informative Columns) -->
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);">
          <div style="padding: 1.1rem 1.5rem; background: #f8fafc; border-bottom: 1.5px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div style="font-size: 0.95rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif;">
              ${altTableTitle}
            </div>
          </div>

          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; min-width: 800px;">
              <thead>
                <tr style="border-bottom: 1.5px solid #e2e8f0; background: #ffffff;">
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.76rem; font-weight: 900; color: #475569; width: 230px; text-transform: uppercase; letter-spacing: 0.4px;">Brand &amp; Logo</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.76rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.4px;">OES Part No &amp; Specifications</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.76rem; font-weight: 900; color: #475569; width: 200px; text-transform: uppercase; letter-spacing: 0.4px;">Vehicle Application</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.76rem; font-weight: 900; color: #475569; width: 240px; text-transform: uppercase; letter-spacing: 0.4px;">Product Classification</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: right; font-size: 0.76rem; font-weight: 900; color: #475569; width: 130px; text-transform: uppercase; letter-spacing: 0.4px;">OES MRP</th>
                </tr>
              </thead>
              <tbody>
                ${tableRows}
              </tbody>
            </table>
          </div>
        </div>

        <!-- AT LAST: Respective Dealership OEM Genuine Part(s) Section -->
        ${oemSectionHtml}

      </div>
    `;
  },

  copy(text, btnElement) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      if (btnElement) {
        const orig = btnElement.innerHTML;
        btnElement.innerHTML = '✓ Copied';
        btnElement.style.background = '#059669';
        btnElement.style.color = '#ffffff';
        btnElement.style.borderColor = '#059669';
        setTimeout(() => {
          btnElement.innerHTML = orig;
          btnElement.style.background = '#ffffff';
          btnElement.style.color = '#475569';
          btnElement.style.borderColor = '#cbd5e1';
        }, 1500);
      }
      if (window.App && window.App.showToast) {
        window.App.showToast(`Copied part number ${text}`, 'success');
      }
    }).catch(err => {
      console.warn('Copy failed:', err);
    });
  },

  switchSubTab() {},
  searchInterchange(query) { this.search(query); },
  handleLiveConvertSearch() { this.search(); },

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  },

  escapeJs(text) {
    if (!text) return '';
    return String(text).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
  }
};

window.OemToOesPortal = OemToOesPortal;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => OemToOesPortal.init());
} else {
  OemToOesPortal.init();
}
