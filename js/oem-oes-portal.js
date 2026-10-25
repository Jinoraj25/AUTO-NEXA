/**
 * AutoNexa OEM to OES Converter
 * =============================
 * Connects directly to /api/oem-to-oes/convert
 * Resolves dealership OEM part numbers against live verified Tier-1 OES alternatives
 * (Bosch, Valeo, LuK, Purolator, Mahle, Brembo, TVS Girling) with real price savings.
 */

const OemToOesPortal = {
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
    const container = document.getElementById('oem-oes-results-container');
    if (container) {
      container.innerHTML = `
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 2.5rem; text-align: center; color: #64748b; font-size: 0.92rem;">
          Please enter an OEM part number or description to search for verified OES alternatives.
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
      container.innerHTML = `
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 2.5rem; text-align: center; color: #64748b; font-size: 0.92rem;">
          Please enter an OEM part number or description to search for verified OES alternatives.
        </div>
      `;
      return;
    }

    if (input && queryOverride) {
      input.value = queryOverride;
    }

    container.innerHTML = `
      <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 2.5rem; text-align: center; color: #0284c7; font-weight: 750; font-size: 0.95rem;">
        🔄 Searching live database for OEM ➔ OES cross-references...
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

  renderResults(data, query) {
    const container = document.getElementById('oem-oes-results-container');
    if (!container) return;

    const oem = data.oem;
    const oesAlts = data.oes_alternatives || [];
    const oemPriceStr = (oem.mrp && oem.mrp > 0) ? `₹${Number(oem.mrp).toLocaleString('en-IN')}` : 'Price on Request';

    let tableRows = '';
    if (oesAlts.length > 0) {
      tableRows = oesAlts.map(alt => {
        const priceStr = (alt.price && alt.price > 0) ? `₹${Number(alt.price).toLocaleString('en-IN')}` : (alt.mrp ? `₹${Number(alt.mrp).toLocaleString('en-IN')}` : '—');
        
        let savingBadge = '<span style="color: #64748b; font-size: 0.76rem;">—</span>';
        if (alt.saving_amount && alt.saving_amount > 0 && alt.saving_pct && alt.saving_pct > 0) {
          savingBadge = `<span style="background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 6px; font-weight: 850; font-size: 0.78rem;">Save ₹${Number(alt.saving_amount).toLocaleString('en-IN')} (${alt.saving_pct}%)</span>`;
        }

        const availBadge = `<span style="background: #f0fdf4; color: #166534; font-weight: 800; font-size: 0.76rem; padding: 2px 7px; border-radius: 4px;">${this.escapeHtml(alt.availability || 'In Stock')}</span>`;

        return `
          <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
            <td style="padding: 0.85rem 1rem; font-weight: 850; color: #0f172a; font-size: 0.88rem;">
              ${this.escapeHtml(alt.brand)}
            </td>
            <td style="padding: 0.85rem 1rem;">
              <div style="display: flex; align-items: center; gap: 0.45rem;">
                <span style="font-family: monospace; font-size: 0.95rem; font-weight: 900; color: #0284c7;">${this.escapeHtml(alt.partNo)}</span>
                <button type="button" onclick="OemToOesPortal.copy('${this.escapeJs(alt.partNo)}', this)" style="padding: 2px 6px; font-size: 0.68rem; border-radius: 4px; border: 1px solid #cbd5e1; background: #ffffff; cursor: pointer;">📋 Copy</button>
              </div>
              <div style="font-size: 0.72rem; color: #64748b; margin-top: 0.15rem;">${this.escapeHtml(alt.desc || '')}</div>
            </td>
            <td style="padding: 0.85rem 1rem; text-align: right; font-weight: 900; color: #059669; font-size: 1.05rem; font-family: 'Outfit', sans-serif;">
              ${priceStr}
            </td>
            <td style="padding: 0.85rem 1rem; text-align: center;">
              ${savingBadge}
            </td>
            <td style="padding: 0.85rem 1rem; text-align: center;">
              ${availBadge}
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

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.5rem;">
        
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
                Brand: <strong style="color: #0f172a;">${this.escapeHtml(oem.brand)}</strong> • Application: <strong>${this.escapeHtml(oem.vehicle || 'All Compatible Models')}</strong>
              </div>
            </div>

            <div style="text-align: right; min-width: 160px;">
              <div style="font-size: 0.74rem; color: #64748b; font-weight: 750;">Official Dealership MRP</div>
              <div style="font-size: 1.6rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif;">
                ${oemPriceStr}
              </div>
            </div>
          </div>
        </div>

        <!-- OES Alternatives Table Card -->
        <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);">
          <div style="padding: 1rem 1.25rem; background: #f8fafc; border-bottom: 1.5px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 0.88rem; font-weight: 900; color: #0f172a;">
              Verified Tier-1 OES Equivalents &amp; Direct Interchanges
            </div>
            <span style="font-size: 0.74rem; color: #059669; font-weight: 850;">
              100% Form-Fit-Function Guaranteed
            </span>
          </div>

          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; min-width: 680px;">
              <thead>
                <tr style="border-bottom: 1.5px solid #e2e8f0; background: #ffffff;">
                  <th style="padding: 0.75rem 1rem; text-align: left; font-size: 0.78rem; font-weight: 850; color: #475569; width: 180px;">Brand</th>
                  <th style="padding: 0.75rem 1rem; text-align: left; font-size: 0.78rem; font-weight: 850; color: #475569;">OES Part No</th>
                  <th style="padding: 0.75rem 1rem; text-align: right; font-size: 0.78rem; font-weight: 850; color: #475569; width: 140px;">Price</th>
                  <th style="padding: 0.75rem 1rem; text-align: center; font-size: 0.78rem; font-weight: 850; color: #475569; width: 200px;">Saving vs OEM</th>
                  <th style="padding: 0.75rem 1rem; text-align: center; font-size: 0.78rem; font-weight: 850; color: #475569; width: 130px;">Availability</th>
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
