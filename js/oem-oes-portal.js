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
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 2.5rem; text-align: center; color: #64748b; font-size: 0.92rem;">
          Please enter an OEM part number (e.g. <span style="font-family: monospace; font-weight: 700; color: #0284c7;">4110002857</span>, <span style="font-family: monospace; font-weight: 700; color: #0284c7;">16510M68K00</span>, <span style="font-family: monospace; font-weight: 700; color: #0284c7;">55810M68P00</span>) to search for verified OES alternatives.
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
      <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 2.5rem; text-align: center; color: #0284c7; font-weight: 750; font-size: 0.95rem;">
        🔄 Searching 23.6M live catalog records for OEM ➔ OES cross-references &amp; Brand Priority...
      </div>
    `;

    try {
      const res = await fetch(`/api/oem-to-oes/convert?query=${encodeURIComponent(query)}`);
      const data = await res.json();

      if (!data || data.found !== true || !data.oem) {
        container.innerHTML = `
          <div style="background: #ffffff; border: 1.5px solid #fecdd3; border-radius: 14px; padding: 2.5rem; text-align: center; color: #be123c; font-weight: 750; font-size: 0.95rem;">
            No OES alternative found for '${this.escapeHtml(query)}'.
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
        <div style="background: #ffffff; border: 1.5px solid #fecdd3; border-radius: 14px; padding: 2.5rem; text-align: center; color: #be123c; font-weight: 750; font-size: 0.95rem;">
          No OES alternative found for '${this.escapeHtml(query)}'.
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
    const oemPriceStr = (oem.mrp && oem.mrp > 0) ? `₹${Number(oem.mrp).toLocaleString('en-IN')}` : 'Price on Request';

    // Model filter logic
    if (this.activeFilterModel && this.activeFilterModel !== 'ALL') {
      const filtered = oesAlts.filter(alt => (alt.verified_for_model || '').toUpperCase() === this.activeFilterModel.toUpperCase());
      if (filtered.length > 0) {
        oesAlts = filtered;
      }
    }

    // Generate table rows
    let tableRows = '';
    if (oesAlts.length > 0) {
      tableRows = oesAlts.map(alt => {
        const priceStr = (alt.price && alt.price > 0) ? `₹${Number(alt.price).toLocaleString('en-IN')}` : (alt.mrp ? `₹${Number(alt.mrp).toLocaleString('en-IN')}` : '—');
        
        let savingBadge = '<span style="color: #64748b; font-size: 0.76rem;">—</span>';
        if (alt.saving_amount && alt.saving_amount > 0 && alt.saving_pct && alt.saving_pct > 0) {
          savingBadge = `<span style="background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 6px; font-weight: 850; font-size: 0.78rem;">Save ₹${Number(alt.saving_amount).toLocaleString('en-IN')} (${alt.saving_pct}%)</span>`;
        }

        // Tier badge styling
        let tierBadge = '';
        const tierStr = alt.tier || '';
        if (tierStr.includes('Primary') || tierStr.includes('Tier-1')) {
          tierBadge = `<span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 2px 7px; border-radius: 4px; font-size: 0.70rem; font-weight: 800;">⭐ TIER 1: PRIMARY OES</span>`;
        } else if (tierStr.includes('PL') || tierStr.includes('Private Label') || tierStr.includes('MYTVS')) {
          tierBadge = `<span style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; padding: 2px 7px; border-radius: 4px; font-size: 0.70rem; font-weight: 800;">🏷️ TIER 2: PL (MYTVS)</span>`;
        } else if (tierStr.includes('Secondary')) {
          tierBadge = `<span style="background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; padding: 2px 7px; border-radius: 4px; font-size: 0.70rem; font-weight: 800;">📦 TIER 3: SECONDARY</span>`;
        } else {
          tierBadge = `<span style="background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; padding: 2px 7px; border-radius: 4px; font-size: 0.70rem; font-weight: 750;">AFTERMARKET</span>`;
        }

        const modelFitStr = alt.verified_for_model ? `<div style="font-size: 0.72rem; color: #0284c7; margin-top: 0.2rem; font-weight: 700;">🚗 Fitment Cataloged: ${this.escapeHtml(alt.verified_for_model)}</div>` : '';

        return `
          <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
            <td style="padding: 0.85rem 1rem;">
              <div style="font-weight: 850; color: #0f172a; font-size: 0.90rem;">
                ${this.escapeHtml(alt.brand)}
              </div>
              <div style="margin-top: 0.25rem;">
                ${tierBadge}
              </div>
            </td>
            <td style="padding: 0.85rem 1rem;">
              <div style="display: flex; align-items: center; gap: 0.45rem;">
                <span style="font-family: monospace; font-size: 0.95rem; font-weight: 900; color: #0284c7;">${this.escapeHtml(alt.partNo)}</span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(alt.partNo)}', this)" style="padding: 2px 6px; font-size: 0.68rem; border-radius: 4px; border: 1px solid #cbd5e1; background: #ffffff; cursor: pointer;">📋 Copy</button>
              </div>
              <div style="font-size: 0.72rem; color: #64748b; margin-top: 0.15rem;">${this.escapeHtml(alt.desc || '')}</div>
              ${modelFitStr}
            </td>
            <td style="padding: 0.85rem 1rem; text-align: right; font-weight: 900; color: #059669; font-size: 1.05rem; font-family: 'Outfit', sans-serif;">
              ${priceStr}
            </td>
            <td style="padding: 0.85rem 1rem; text-align: center;">
              ${savingBadge}
            </td>
            <td style="padding: 0.85rem 1rem; text-align: center;">
              <span style="background: #f0fdf4; color: #166534; font-weight: 800; font-size: 0.76rem; padding: 2px 7px; border-radius: 4px;">In Stock</span>
            </td>
          </tr>
        `;
      }).join('');
    } else {
      tableRows = `
        <tr>
          <td colspan="5" style="padding: 2rem; text-align: center; color: #64748b; font-size: 0.85rem;">
            No direct OES alternatives currently listed for this part.
          </td>
        </tr>
      `;
    }

    // Model Filter Chips
    let modelChipsHtml = '';
    if (mappedModels.length > 0) {
      const allActive = this.activeFilterModel === 'ALL';
      modelChipsHtml = `
        <div style="background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 0.5rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap; gap: 0.5rem;">
            <div style="font-size: 0.82rem; font-weight: 850; color: #1e293b; display: flex; align-items: center; gap: 0.4rem;">
              <span>🚗</span>
              <span>Engineering Common Part — Mapped to <strong>${mappedModels.length} Models</strong> across ${this.escapeHtml(mappedModels[0]?.make || '')}</span>
            </div>
            <div style="font-size: 0.74rem; color: #64748b; font-style: italic;">
              OES alternatives have guaranteed inherited fitment across all mapped models
            </div>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center;">
            <button type="button" onclick="OemToOesPortal.filterByModel('ALL')" style="padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 800; border: 1px solid ${allActive ? '#0284c7' : '#cbd5e1'}; background: ${allActive ? '#0284c7' : '#ffffff'}; color: ${allActive ? '#ffffff' : '#334155'}; cursor: pointer;">
              All Models (${mappedModels.reduce((acc, m) => acc + (m.variant_count || 1), 0)} Variants)
            </button>
            ${mappedModels.map(m => {
              const isActive = this.activeFilterModel.toUpperCase() === m.model.toUpperCase();
              return `
                <button type="button" onclick="OemToOesPortal.filterByModel('${this.escapeJs(m.model)}')" style="padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 750; border: 1px solid ${isActive ? '#0284c7' : '#e2e8f0'}; background: ${isActive ? '#e0f2fe' : '#ffffff'}; color: ${isActive ? '#0369a1' : '#475569'}; cursor: pointer;">
                  ${this.escapeHtml(m.model)} <span style="font-size: 0.70rem; opacity: 0.8;">(${m.variant_count} trims)</span>
                </button>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // Brand Priority Banner
    let bpBanner = '';
    if (bp.primary_brands && bp.primary_brands.length > 0) {
      bpBanner = `
        <div style="display: flex; align-items: center; gap: 0.75rem; background: #fdf2f8; border: 1px solid #fbcfe8; border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.75rem; color: #831843; margin-top: 0.6rem; flex-wrap: wrap;">
          <strong style="white-space: nowrap;">⚡ Master Brand Priority Applied:</strong>
          <span>
            <strong style="color: #047857;">Priority 1 (PRIMARY):</strong> ${this.escapeHtml(bp.primary_brands.join(', '))} &nbsp;➔&nbsp;
            <strong style="color: #1d4ed8;">Priority 2 (PL):</strong> ${this.escapeHtml((bp.pl_brands || ['MYTVS', 'UCAP']).join(', '))} &nbsp;➔&nbsp;
            <strong style="color: #6b21a8;">Priority 3 (SECONDARY):</strong> 125 Secondary Brands (Purolator, Elofic, Sofima, Mahle, Delphi, Brakes India, etc.)
          </span>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.25rem;">
        
        <!-- OEM Part Info Card -->
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 1.5rem; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap;">
            <div>
              <span style="font-size: 0.7rem; font-weight: 850; background: #fef2f2; color: #dc2626; border: 1px solid #fecdd3; padding: 3px 8px; border-radius: 6px; letter-spacing: 0.4px;">
                DEALERSHIP OEM PART
              </span>
              <h3 style="font-size: 1.25rem; font-weight: 900; color: #0f172a; margin: 0.45rem 0 0.25rem; font-family: 'Outfit', sans-serif;">
                ${this.escapeHtml(oem.desc)}
              </h3>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="font-family: monospace; font-size: 1.05rem; font-weight: 900; color: #0f172a;">${this.escapeHtml(oem.partNo)}</span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(oem.partNo)}', this)" style="padding: 2px 7px; font-size: 0.7rem; border-radius: 4px; border: 1px solid #cbd5e1; background: #ffffff; cursor: pointer;">📋 Copy</button>
              </div>
              <div style="font-size: 0.8rem; color: #475569;">
                Brand: <strong style="color: #0f172a;">${this.escapeHtml(oem.brand)}</strong> • Component: <strong style="color: #0f172a;">${this.escapeHtml(oem.component || '')}</strong> • Application: <strong>${this.escapeHtml(oem.vehicle || 'All Compatible Models')}</strong>
              </div>
            </div>

            <div style="text-align: right; min-width: 160px;">
              <div style="font-size: 0.74rem; color: #64748b; font-weight: 750;">Official Dealership MRP</div>
              <div style="font-size: 1.6rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif;">
                ${oemPriceStr}
              </div>
            </div>
          </div>

          ${bpBanner}
        </div>

        <!-- Multi-Model Compatibility Chips -->
        ${modelChipsHtml}

        <!-- OES Alternatives Table Card -->
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);">
          <div style="padding: 1rem 1.25rem; background: #f8fafc; border-bottom: 1.5px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div style="font-size: 0.88rem; font-weight: 900; color: #0f172a;">
              Verified OES Equivalents &amp; Direct Interchanges (${oesAlts.length} Options)
            </div>
            <span style="font-size: 0.74rem; color: #059669; font-weight: 850;">
              ✓ 100% Form-Fit-Function Guaranteed
            </span>
          </div>

          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; min-width: 680px;">
              <thead>
                <tr style="border-bottom: 1.5px solid #e2e8f0; background: #ffffff;">
                  <th style="padding: 0.75rem 1rem; text-align: left; font-size: 0.78rem; font-weight: 850; color: #475569; width: 190px;">Brand &amp; Priority Tier</th>
                  <th style="padding: 0.75rem 1rem; text-align: left; font-size: 0.78rem; font-weight: 850; color: #475569;">OES Part No &amp; Description</th>
                  <th style="padding: 0.75rem 1rem; text-align: right; font-size: 0.78rem; font-weight: 850; color: #475569; width: 130px;">Price</th>
                  <th style="padding: 0.75rem 1rem; text-align: center; font-size: 0.78rem; font-weight: 850; color: #475569; width: 190px;">Saving vs OEM</th>
                  <th style="padding: 0.75rem 1rem; text-align: center; font-size: 0.78rem; font-weight: 850; color: #475569; width: 110px;">Availability</th>
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
        setTimeout(() => {
          btnElement.innerHTML = orig;
          btnElement.style.background = '';
          btnElement.style.color = '';
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
