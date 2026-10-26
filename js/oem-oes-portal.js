/**
 * AutoNexa OEM to OES Converter
 * =============================
 * Connects directly to /api/oem-to-oes/convert
 * Resolves dealership OEM part numbers against live verified Tier-1 OES alternatives
 * Strictly enforcing Brand Priority: Primary Brands > PL (MyTVS) > Secondary Brands
 * Handles Multi-Model fitment and cross-model inherited compatibility.
 */

const OemToOesPortal = {
  currentData: null,
  activeFilterModel: 'ALL',

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
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 16px; padding: 3rem 2rem; text-align: center; color: #64748b; font-size: 0.95rem; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.02);">
          <div style="font-size: 2.2rem; margin-bottom: 0.75rem;">🔍</div>
          <div style="font-weight: 800; color: #1e293b; font-size: 1.1rem; margin-bottom: 0.35rem;">Enter an OEM Part Number to Convert</div>
          <div style="color: #64748b; font-size: 0.85rem;">
            Try: <span style="font-family: monospace; font-weight: 800; color: #0284c7; cursor: pointer;" onclick="OemToOesPortal.search('4110002857')">4110002857</span> (Hyundai Clutch), 
            <span style="font-family: monospace; font-weight: 800; color: #0284c7; cursor: pointer;" onclick="OemToOesPortal.search('16510M68K00')">16510M68K00</span> (Maruti Oil Filter), or 
            <span style="font-family: monospace; font-weight: 800; color: #0284c7; cursor: pointer;" onclick="OemToOesPortal.search('58510C4930')">58510-C4930</span> (Brake Master Cyl)
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
        <div>Searching 23.6M Live Catalog Records for OEM ➔ OES Alternatives...</div>
      </div>
    `;

    try {
      const res = await fetch(`/api/oem-to-oes/convert?query=${encodeURIComponent(query)}`);
      const data = await res.json();

      if (!data || data.found !== true || !data.oem) {
        container.innerHTML = `
          <div style="background: #fff5f5; border: 1.5px solid #fed7d7; border-radius: 16px; padding: 2.5rem; text-align: center; color: #c53030; font-weight: 750; font-size: 0.95rem;">
            ⚠️ No OEM or OES alternative found matching '${this.escapeHtml(query)}' in the database.
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

    const oem = data.oem;
    let oesAlts = data.oes_alternatives || [];
    const mappedModels = data.mapped_models || [];
    const bp = data.brand_priority_applied || {};
    const oemMrp = Number(oem.mrp || 0);
    const oemPriceStr = oemMrp > 0 ? `₹${oemMrp.toLocaleString('en-IN')}` : 'Price on Request';

    // Model filter logic
    if (this.activeFilterModel && this.activeFilterModel !== 'ALL') {
      const filtered = oesAlts.filter(alt => (alt.verified_for_model || '').toUpperCase() === this.activeFilterModel.toUpperCase());
      if (filtered.length > 0) {
        oesAlts = filtered;
      }
    }

    // Generate table rows without Availability column and with clear Price vs OEM badges
    let tableRows = '';
    if (oesAlts.length > 0) {
      tableRows = oesAlts.map(alt => {
        const altPrice = Number(alt.mrp || alt.price || 0);
        const priceStr = altPrice > 0 ? `₹${altPrice.toLocaleString('en-IN')}` : '—';
        
        // Comprehensive Price vs OEM Comparison Pill
        let savingBadge = '';
        const priceStatus = alt.price_status || (oemMrp > 0 && altPrice > 0 ? (oemMrp > altPrice ? 'cheaper' : (oemMrp < altPrice ? 'premium' : 'equal')) : 'no_oem_price');
        const diffAmount = alt.price_diff !== undefined && alt.price_diff !== null ? alt.price_diff : (oemMrp > 0 && altPrice > 0 ? (oemMrp - altPrice) : null);
        const diffPct = alt.saving_pct !== undefined && alt.saving_pct !== null ? alt.saving_pct : (oemMrp > 0 && diffAmount ? Math.round((Math.abs(diffAmount) / oemMrp) * 100) : 0);

        if (priceStatus === 'cheaper' && diffAmount > 0) {
          savingBadge = `
            <span style="background: #ecfdf5; color: #047857; border: 1.5px solid #a7f3d0; padding: 4px 12px; border-radius: 9999px; font-weight: 850; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 1px 3px rgba(4, 120, 87, 0.08);">
              <span style="font-size: 0.85rem;">✓</span>
              <span>Save ₹${Math.abs(diffAmount).toLocaleString('en-IN')} (${diffPct}% OFF)</span>
            </span>
          `;
        } else if (priceStatus === 'premium' && diffAmount < 0) {
          savingBadge = `
            <span style="background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 1px 3px rgba(29, 78, 216, 0.08);">
              <span style="font-size: 0.85rem;">⭐</span>
              <span>+₹${Math.abs(diffAmount).toLocaleString('en-IN')} (+${diffPct}% Premium OE)</span>
            </span>
          `;
        } else if (priceStatus === 'equal') {
          savingBadge = `
            <span style="background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; padding: 4px 10px; border-radius: 9999px; font-weight: 750; font-size: 0.76rem;">
              Direct OEM Price Match
            </span>
          `;
        } else {
          savingBadge = `
            <span style="background: #f8fafc; color: #64748b; border: 1px dashed #cbd5e1; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">
              Competitive OE Grade
            </span>
          `;
        }

        // Tier badge styling
        let tierBadge = '';
        const tierStr = alt.tier || '';
        if (tierStr.includes('Primary') || tierStr.includes('Tier-1')) {
          tierBadge = `<span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 6px; font-size: 0.69rem; font-weight: 850; letter-spacing: 0.3px;">⭐ TIER 1: PRIMARY OES</span>`;
        } else if (tierStr.includes('PL') || tierStr.includes('Private Label') || tierStr.includes('MYTVS')) {
          tierBadge = `<span style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; padding: 2px 8px; border-radius: 6px; font-size: 0.69rem; font-weight: 850; letter-spacing: 0.3px;">🏷️ TIER 2: PL (MYTVS)</span>`;
        } else if (tierStr.includes('Secondary')) {
          tierBadge = `<span style="background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; padding: 2px 8px; border-radius: 6px; font-size: 0.69rem; font-weight: 850; letter-spacing: 0.3px;">📦 TIER 3: SECONDARY</span>`;
        } else {
          tierBadge = `<span style="background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; padding: 2px 8px; border-radius: 6px; font-size: 0.69rem; font-weight: 750;">AFTERMARKET</span>`;
        }

        const modelFitStr = alt.verified_for_model ? `
          <div style="font-size: 0.72rem; color: #0284c7; margin-top: 0.25rem; font-weight: 750; display: flex; align-items: center; gap: 0.3rem;">
            <span>🚗</span>
            <span>Fitment Verified: <strong>${this.escapeHtml(alt.verified_for_model)}</strong></span>
          </div>
        ` : '';

        return `
          <tr style="border-bottom: 1px solid #f1f5f9; transition: all 0.15s ease;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
            <td style="padding: 1rem 1.25rem; vertical-align: middle;">
              <div style="font-weight: 900; color: #0f172a; font-size: 0.95rem; font-family: 'Outfit', sans-serif;">
                ${this.escapeHtml(alt.brand)}
              </div>
              <div style="margin-top: 0.35rem;">
                ${tierBadge}
              </div>
            </td>
            <td style="padding: 1rem 1.25rem; vertical-align: middle;">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-family: monospace; font-size: 1rem; font-weight: 900; color: #0284c7; background: #f0f9ff; padding: 3px 8px; border-radius: 6px; border: 1px solid #bae6fd;">
                  ${this.escapeHtml(alt.partNo)}
                </span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(alt.partNo)}', this)" style="padding: 3px 8px; font-size: 0.70rem; font-weight: 750; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #475569; cursor: pointer; transition: all 0.15s;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">📋 Copy</button>
              </div>
              <div style="font-size: 0.76rem; color: #475569; margin-top: 0.3rem; font-weight: 500;">
                ${this.escapeHtml(alt.desc || '')}
              </div>
              ${modelFitStr}
            </td>
            <td style="padding: 1rem 1.25rem; text-align: right; vertical-align: middle;">
              <div style="font-weight: 900; color: #0f172a; font-size: 1.2rem; font-family: 'Outfit', sans-serif;">
                ${priceStr}
              </div>
              <div style="font-size: 0.70rem; color: #94a3b8; font-weight: 600;">OES MRP</div>
            </td>
            <td style="padding: 1rem 1.25rem; text-align: center; vertical-align: middle;">
              ${savingBadge}
            </td>
          </tr>
        `;
      }).join('');
    } else {
      tableRows = `
        <tr>
          <td colspan="4" style="padding: 3rem; text-align: center; color: #64748b; font-size: 0.9rem;">
            No direct OES alternatives currently listed for this specific filter.
          </td>
        </tr>
      `;
    }

    // Model Filter Chips
    let modelChipsHtml = '';
    if (mappedModels.length > 0) {
      const allActive = this.activeFilterModel === 'ALL';
      modelChipsHtml = `
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.25rem; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
            <div style="font-size: 0.85rem; font-weight: 850; color: #0f172a; display: flex; align-items: center; gap: 0.45rem;">
              <span style="font-size: 1rem;">🚗</span>
              <span>Engineering Common Part — Mapped Across <strong>${mappedModels.length} Models</strong> (${this.escapeHtml(mappedModels[0]?.make || '')})</span>
            </div>
            <div style="font-size: 0.75rem; color: #059669; font-weight: 750;">
              ✓ 100% Guaranteed Inherited Fitment Across All Mapped Models
            </div>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
            <button type="button" onclick="OemToOesPortal.filterByModel('ALL')" style="padding: 5px 12px; border-radius: 8px; font-size: 0.78rem; font-weight: 850; border: 1.5px solid ${allActive ? '#0284c7' : '#cbd5e1'}; background: ${allActive ? '#0284c7' : '#ffffff'}; color: ${allActive ? '#ffffff' : '#334155'}; cursor: pointer; transition: all 0.15s; box-shadow: ${allActive ? '0 2px 6px rgba(2, 132, 199, 0.25)' : 'none'};">
              All Mapped Models (${mappedModels.reduce((acc, m) => acc + (m.variant_count || 1), 0)} Variants)
            </button>
            ${mappedModels.map(m => {
              const isActive = this.activeFilterModel.toUpperCase() === m.model.toUpperCase();
              return `
                <button type="button" onclick="OemToOesPortal.filterByModel('${this.escapeJs(m.model)}')" style="padding: 5px 12px; border-radius: 8px; font-size: 0.78rem; font-weight: 800; border: 1.5px solid ${isActive ? '#0284c7' : '#e2e8f0'}; background: ${isActive ? '#e0f2fe' : '#ffffff'}; color: ${isActive ? '#0369a1' : '#475569'}; cursor: pointer; transition: all 0.15s;" onmouseover="if(!${isActive}) this.style.background='#f8fafc'" onmouseout="if(!${isActive}) this.style.background='#ffffff'">
                  ${this.escapeHtml(m.model)} <span style="font-size: 0.70rem; opacity: 0.75; font-weight: 600;">(${m.variant_count} trims)</span>
                </button>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // Master Brand Priority Banner
    let bpBanner = '';
    if (bp.primary_brands && bp.primary_brands.length > 0) {
      bpBanner = `
        <div style="background: linear-gradient(135deg, #fdf2f8 0%, #f8fafc 100%); border: 1px solid #fbcfe8; border-radius: 10px; padding: 0.75rem 1rem; font-size: 0.76rem; color: #831843; margin-top: 0.85rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <strong style="background: #f43f5e; color: #ffffff; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; letter-spacing: 0.3px;">BRAND PRIORITY</strong>
            <span>
              <strong style="color: #047857;">Priority 1 (PRIMARY):</strong> ${this.escapeHtml(bp.primary_brands.join(', '))} &nbsp;➔&nbsp;
              <strong style="color: #1d4ed8;">Priority 2 (PL):</strong> ${this.escapeHtml((bp.pl_brands || ['MYTVS', 'UCAP']).join(', '))} &nbsp;➔&nbsp;
              <strong style="color: #7e22ce;">Priority 3 (SECONDARY):</strong> 125 Aftermarket Brands
            </span>
          </div>
          <span style="font-size: 0.70rem; color: #9d174d; font-weight: 700;">Source: unique_brand_names_Category Updated.xlsx</span>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.25rem;">
        
        <!-- Dealership OEM Part Card -->
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 16px; padding: 1.75rem; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1.5rem; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 280px;">
              <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem;">
                <span style="font-size: 0.72rem; font-weight: 850; background: #fef2f2; color: #dc2626; border: 1px solid #fecdd3; padding: 3px 9px; border-radius: 6px; letter-spacing: 0.4px;">
                  DEALERSHIP OEM PART
                </span>
                <span style="font-size: 0.72rem; font-weight: 800; background: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 6px;">
                  ${this.escapeHtml(oem.brand)}
                </span>
              </div>
              <h3 style="font-size: 1.35rem; font-weight: 900; color: #0f172a; margin: 0 0 0.4rem; font-family: 'Outfit', sans-serif; letter-spacing: -0.2px;">
                ${this.escapeHtml(oem.desc)}
              </h3>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem;">
                <span style="font-family: monospace; font-size: 1.1rem; font-weight: 900; color: #0f172a; background: #f8fafc; padding: 3px 10px; border-radius: 6px; border: 1px solid #cbd5e1;">
                  ${this.escapeHtml(oem.partNo)}
                </span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(oem.partNo)}', this)" style="padding: 3px 9px; font-size: 0.72rem; font-weight: 750; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #334155; cursor: pointer; transition: all 0.15s;" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">📋 Copy</button>
              </div>
              <div style="font-size: 0.82rem; color: #475569; line-height: 1.4;">
                Component: <strong style="color: #0f172a;">${this.escapeHtml(oem.component || '')}</strong> &nbsp;•&nbsp; 
                Application: <strong style="color: #0f172a;">${this.escapeHtml(oem.vehicle || 'All Compatible Models')}</strong>
              </div>
            </div>

            <div style="text-align: right; min-width: 170px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.25rem;">
              <div style="font-size: 0.74rem; color: #64748b; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Dealership MRP</div>
              <div style="font-size: 1.75rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif; margin-top: 0.15rem;">
                ${oemPriceStr}
              </div>
              <div style="font-size: 0.68rem; color: #059669; font-weight: 750; margin-top: 0.2rem;">Official OEM Benchmark</div>
            </div>
          </div>

          ${bpBanner}
        </div>

        <!-- Multi-Model Compatibility Chips -->
        ${modelChipsHtml}

        <!-- Verified OES Alternatives Table (4 Clean Columns - Availability Removed) -->
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);">
          <div style="padding: 1.1rem 1.5rem; background: #f8fafc; border-bottom: 1.5px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div style="font-size: 0.95rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif;">
              Verified OES Equivalents &amp; Direct Interchanges (${oesAlts.length} Options)
            </div>
            <span style="font-size: 0.75rem; color: #059669; font-weight: 850; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 3px 9px; border-radius: 6px;">
              ✓ 100% Form-Fit-Function Guaranteed
            </span>
          </div>

          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; min-width: 650px;">
              <thead>
                <tr style="border-bottom: 1.5px solid #e2e8f0; background: #ffffff;">
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.78rem; font-weight: 900; color: #475569; width: 220px; text-transform: uppercase; letter-spacing: 0.4px;">Brand &amp; Priority Tier</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: left; font-size: 0.78rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.4px;">OES Part No &amp; Fitment</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: right; font-size: 0.78rem; font-weight: 900; color: #475569; width: 140px; text-transform: uppercase; letter-spacing: 0.4px;">OES Price</th>
                  <th style="padding: 0.85rem 1.25rem; text-align: center; font-size: 0.78rem; font-weight: 900; color: #475569; width: 240px; text-transform: uppercase; letter-spacing: 0.4px;">Price vs Dealership OEM</th>
                </tr>
              </thead>
              <tbody>
                ${tableRows}
              </tbody>
            </table>
          </div>
        </div>

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
          btnElement.style.color = '#334155';
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

  // Backward compatibility stubs
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
