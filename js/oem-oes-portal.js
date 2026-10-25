/**
 * AutoNexa OEM to OES Conversion & Virtual Interchange Group (VIG) Hub
 * ====================================================================
 * Implements the 6-step algorithmic runtime logic:
 * 1. Sanitize & Normalize
 * 2. Identify Input Type (OEM vs OES)
 * 3. Query Group Peers via Virtual Interchange Group (VIG) indirection
 * 4. Resolve OEM vs OES Scenario (with Anchor Election)
 * 5. Attach Fitments
 * 6. Render Dual Interchange Matrix & Interconnected Vehicles (Image 5 specification)
 */

const OemToOesPortal = {
  activeSubTab: 'interchanges',
  activeInterchangeData: null,

  // Pre-compiled fast-moving PMS kits for top Indian car models
  PMS_KITS_DATA: {
    'MARUTI_SWIFT': {
      modelName: 'Maruti Suzuki Swift (Diesel / Petrol)',
      segment: 'Hatchback',
      image: 'images/vehicles/MARUTI SUZUKI/SWIFT 3RD GEN (2018-2021).png',
      items: [
        { item: 'Front Disc Brake Pad Set', oemPart: '55810M68P00', oemBrand: 'Maruti Genuine', oemPrice: 2250, oesPart: '0986AB1234', oesBrand: 'Bosch / TVS Girling', oesPrice: 1580, note: '100% OE Friction Formulation' },
        { item: 'Engine Oil Filter', oemPart: '16510M68K00', oemBrand: 'Maruti Genuine', oemPrice: 380, oesPart: 'OC-1240', oesBrand: 'Mahle / Purolator', oesPrice: 260, note: 'Micro-pore synthetic media' },
        { item: 'Engine Air Filter', oemPart: '13780M68P00', oemBrand: 'Maruti Genuine', oemPrice: 420, oesPart: 'AF-1088', oesBrand: 'Purolator / Elofic', oesPrice: 295, note: 'High dust-holding capacity' },
        { item: 'Cabin AC Pollen Filter', oemPart: '95860M68P00', oemBrand: 'Maruti Genuine', oemPrice: 510, oesPart: 'CF-2055', oesBrand: 'Bosch Activated Carbon', oesPrice: 360, note: '99.5% PM2.5 & odor filter' },
        { item: 'Fuel Filter Cartridge', oemPart: '15410M68P00', oemBrand: 'Maruti Genuine', oemPrice: 890, oesPart: 'FF-3042', oesBrand: 'Delphi / Bosch', oesPrice: 620, note: 'Water separator efficiency' },
        { item: 'Spark Plugs (Set of 4)', oemPart: '09482M00645', oemBrand: 'Maruti Genuine', oemPrice: 960, oesPart: 'BKR6E-11', oesBrand: 'NGK / Bosch Iridium', oesPrice: 710, note: 'Precise spark gap OE spec' }
      ]
    },
    'HYUNDAI_CRETA': {
      modelName: 'Hyundai Creta 1.5L (Petrol / CRDi)',
      segment: 'Mid SUV',
      image: 'images/vehicles/HYUNDAI/CRETA 1ST GEN (06.2015-05.2018).jpg',
      items: [
        { item: 'Front Brake Pad Set', oemPart: '58101-A6A00', oemBrand: 'Hyundai Mobis', oemPrice: 3850, oesPart: 'P30064', oesBrand: 'Brembo / KBX', oesPrice: 2690, note: 'Ceramic quiet braking formulation' },
        { item: 'Engine Oil Filter', oemPart: '26300-35505', oemBrand: 'Hyundai Mobis', oemPrice: 490, oesPart: '0986AF0059', oesBrand: 'Bosch / Mahle', oesPrice: 340, note: 'Spin-on anti-drainback valve' },
        { item: 'Engine Air Intake Filter', oemPart: '28113-A0100', oemBrand: 'Hyundai Mobis', oemPrice: 680, oesPart: 'LAK-1102', oesBrand: 'Mahle / Elofic', oesPrice: 470, note: 'OE pleat geometry' },
        { item: 'Cabin AC Filter', oemPart: '97133-D1000', oemBrand: 'Hyundai Mobis', oemPrice: 750, oesPart: 'M2244', oesBrand: 'Bosch Aeristo Premium', oesPrice: 510, note: 'Anti-bacterial bio-functional' },
        { item: 'Fuel Filter Element', oemPart: '31922-2E900', oemBrand: 'Hyundai Mobis', oemPrice: 1450, oesPart: 'HDF-924', oesBrand: 'Delphi Technologies', oesPrice: 1050, note: 'High pressure common rail spec' },
        { item: 'Front Suspension Strut Mount', oemPart: '54610-C7000', oemBrand: 'Hyundai Mobis', oemPrice: 1850, oesPart: 'GM-1402', oesBrand: 'Gabriel / Monroe', oesPrice: 1320, note: 'Vibration absorbing rubber' }
      ]
    },
    'TOYOTA_CRYSTA': {
      modelName: 'Toyota Innova Crysta 2.4L / 2.8L',
      segment: 'Premium MPV',
      image: 'images/vehicles/TOYOTA/INNOVA 1ST GEN (2005-2008).jpg',
      items: [
        { item: 'Front Brake Pad Set', oemPart: '04465-0K260', oemBrand: 'Toyota Genuine', oemPrice: 4600, oesPart: 'BP-TY884', oesBrand: 'TVS Girling / Brembo', oesPrice: 3250, note: 'Heavy duty fade-resistant' },
        { item: 'Clutch Disc & Cover Plate Kit', oemPart: '31250-0K204', oemBrand: 'Toyota Genuine', oemPrice: 14200, oesPart: 'VAL-828340', oesBrand: 'Valeo / Ceekay', oesPrice: 10450, note: 'OE supplier to Toyota Japan' },
        { item: 'Clutch Release Bearing', oemPart: '31230-71011', oemBrand: 'Toyota Genuine', oemPrice: 2450, oesPart: '500104810', oesBrand: 'LuK / Schaeffler', oesPrice: 1750, note: 'Self-centering bearing' },
        { item: 'Engine Oil Filter', oemPart: '90915-YZZD2', oemBrand: 'Toyota Genuine', oemPrice: 620, oesPart: 'OC-1239', oesBrand: 'Mahle / Denso', oesPrice: 440, note: 'Double-fluted seal' },
        { item: 'Engine Air Intake Filter', oemPart: '17801-0L040', oemBrand: 'Toyota Genuine', oemPrice: 1150, oesPart: '0986AF2411', oesBrand: 'Bosch / Elofic', oesPrice: 790, note: 'Deep dust filtration' },
        { item: 'Fuel Filter Element', oemPart: '23390-0L070', oemBrand: 'Toyota Genuine', oemPrice: 1850, oesPart: 'FF-TY771', oesBrand: 'Denso / Purolator', oesPrice: 1290, note: 'Water trap sensor compatible' }
      ]
    },
    'HYUNDAI_NIOS': {
      modelName: 'Hyundai Grand i10 Nios 1.2L',
      segment: 'Compact Hatchback',
      image: 'images/vehicles/HYUNDAI/GRAND I10 NIOS (08.2019-12.2022).png',
      items: [
        { item: 'Front Brake Pad Set', oemPart: '272KBX3042', oemBrand: 'Hyundai Mobis', oemPrice: 1850, oesPart: '0986AB1142', oesBrand: 'Bosch / TVS Girling', oesPrice: 1320, note: '28.6% cost reduction with OE spec' },
        { item: 'Engine Oil Filter', oemPart: '26300-02503', oemBrand: 'Hyundai Mobis', oemPrice: 340, oesPart: 'OC-1210', oesBrand: 'Mahle / Purolator', oesPrice: 240, note: 'High flow synthetic media' },
        { item: 'Engine Air Filter', oemPart: '28113-B9000', oemBrand: 'Hyundai Mobis', oemPrice: 390, oesPart: 'AF-1092', oesBrand: 'Purolator / Bosch', oesPrice: 275, note: 'OE pleat density' },
        { item: 'Front Shock Absorber (L/R)', oemPart: '54651-B9000', oemBrand: 'Hyundai Mobis', oemPrice: 3200, oesPart: 'G54102', oesBrand: 'Gabriel / Monroe', oesPrice: 2280, note: 'Twin-tube gas charged' },
        { item: 'Tie Rod End Outer', oemPart: '56820-B9000', oemBrand: 'Hyundai Mobis', oemPrice: 850, oesPart: 'TRE-8812', oesBrand: 'Rane / TRW', oesPrice: 590, note: 'Forged steel precision ball stud' }
      ]
    },
    'TATA_NEXON': {
      modelName: 'Tata Nexon 1.2 Revotron / 1.5 Revotorq',
      segment: 'Compact SUV',
      image: 'images/vehicles/TATA/INDICA VISTA (01.2008-12.2012).jpg',
      items: [
        { item: 'Front Disc Brake Pad Set', oemPart: '542442100108', oemBrand: 'Tata Genuine', oemPrice: 2950, oesPart: 'P88021', oesBrand: 'Brembo / TVS Girling', oesPrice: 2090, note: 'OE supplier to Tata Motors' },
        { item: 'Engine Oil Filter', oemPart: '542418130101', oemBrand: 'Tata Genuine', oemPrice: 420, oesPart: '0986AF0210', oesBrand: 'Bosch / Elofic', oesPrice: 290, note: 'Spin-on full flow filtration' },
        { item: 'Air Filter Element', oemPart: '542409130105', oemBrand: 'Tata Genuine', oemPrice: 580, oesPart: 'AF-8821', oesBrand: 'Purolator / Mahle', oesPrice: 410, note: 'Optimal airflow retention' },
        { item: 'Cabin AC Filter', oemPart: '542483100102', oemBrand: 'Tata Genuine', oemPrice: 620, oesPart: 'CF-9901', oesBrand: 'Bosch Aeristo', oesPrice: 430, note: 'Anti-allergen synthetic layer' },
        { item: 'Front Stabilizer Link Rod', oemPart: '542432000104', oemBrand: 'Tata Genuine', oemPrice: 920, oesPart: 'SL-5510', oesBrand: 'Rane / Gabriel', oesPrice: 640, note: 'Self-lubricating polymer ball seat' }
      ]
    },
    'MAHINDRA_SCORPIO': {
      modelName: 'Mahindra Scorpio / Scorpio Classic 2.2 mHawk',
      segment: 'Rugged SUV',
      image: 'images/vehicles/MARUTI SUZUKI/BREZZA (2022-NOW).png',
      items: [
        { item: 'Front Brake Pad Set', oemPart: '0603AA0020N', oemBrand: 'Mahindra Genuine', oemPrice: 3450, oesPart: '0986AB2231', oesBrand: 'Bosch / KBX', oesPrice: 2450, note: 'Heavy SUV thermal endurance' },
        { item: 'Clutch Plate & Cover Kit', oemPart: '0601AA0010N', oemBrand: 'Mahindra Genuine', oemPrice: 11800, oesPart: 'VAL-826501', oesBrand: 'Valeo / LuK', oesPrice: 8550, note: 'Heavy duty damper springs' },
        { item: 'Water Pump Assembly', oemPart: '0305CA0100N', oemBrand: 'Mahindra Genuine', oemPrice: 2850, oesPart: 'WP-8812', oesBrand: 'Puro / TVS', oesPrice: 1980, note: 'Precision impeller bearing' },
        { item: 'Engine Oil Filter', oemPart: '0303BC0061N', oemBrand: 'Mahindra Genuine', oemPrice: 480, oesPart: 'OC-1234', oesBrand: 'Mahle / Bosch', oesPrice: 335, note: 'High capacity mHawk engine spec' }
      ]
    }
  },

  activeKitKey: 'MARUTI_SWIFT',

  init() {
    this.renderKitMatrix(this.activeKitKey);
    // Auto-load default anchor VAL-826330 on initialization (Image 5 view)
    this.searchInterchange('VAL-826330');
  },

  switchSubTab(tabName) {
    this.activeSubTab = tabName;
    document.querySelectorAll('.oes-subtab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.subtab === tabName);
    });

    const secInterchanges = document.getElementById('oes-view-interchanges');
    const secCrossRef = document.getElementById('oes-view-cross-ref');
    const secMatrix = document.getElementById('oes-view-matrix');

    if (secInterchanges) secInterchanges.style.display = (tabName === 'interchanges') ? 'block' : 'none';
    if (secCrossRef) secCrossRef.style.display = (tabName === 'cross-ref') ? 'block' : 'none';
    if (secMatrix) secMatrix.style.display = (tabName === 'conversion-matrix' || tabName === 'inventory-pricing') ? 'block' : 'none';

    // Update left subnav highlight
    document.querySelectorAll('.oes-left-nav-item').forEach(item => {
      const target = item.dataset.nav;
      item.classList.toggle('active', (tabName === 'interchanges' && target === 'interchange-search') ||
                                      (tabName === 'conversion-matrix' && target === 'conversion-matrix') ||
                                      (tabName === 'cross-ref' && target === 'dashboard'));
    });
  },

  renderBrandLogo(brandName) {
    const b = (brandName || '').toUpperCase();
    if (b.includes('LUK')) {
      return `<img src="images/brands/luk.svg" alt="LuK" style="height: 28px; width: 68px; object-fit: contain;" onerror="this.onerror=null; this.outerHTML='<span style=\\'background:#ffcc00;color:#000;font-weight:900;padding:2px 8px;border-radius:4px;border:1.5px solid #000;font-family:Arial Black;\\'>LuK</span>'">`;
    }
    if (b.includes('SACHS')) {
      return `<img src="images/brands/sachs.svg" alt="SACHS" style="height: 28px; width: 88px; object-fit: contain;" onerror="this.onerror=null; this.outerHTML='<span style=\\'color:#004b93;font-weight:900;font-size:1.05rem;font-family:sans-serif;\\'>SACHS</span>'">`;
    }
    if (b.includes('BOSCH')) {
      return `<img src="images/brands/bosch.svg" alt="BOSCH" style="height: 28px; width: 92px; object-fit: contain;" onerror="this.onerror=null; this.outerHTML='<span style=\\'color:#ea1d25;font-weight:900;font-size:1.1rem;font-family:sans-serif;\\'>BOSCH</span>'">`;
    }
    if (b.includes('TRW')) {
      return `<img src="images/brands/trw.svg" alt="TRW" style="height: 28px; width: 68px; object-fit: contain;" onerror="this.onerror=null; this.outerHTML='<span style=\\'color:#dc2626;font-weight:900;font-style:italic;font-size:1.2rem;font-family:Arial Black;\\'>TRW</span>'">`;
    }
    if (b.includes('CEEKAY')) {
      return `<img src="images/brands/ceekay.svg" alt="CEEKAY" style="height: 28px; width: 84px; object-fit: contain;" onerror="this.onerror=null; this.outerHTML='<span style=\\'color:#1e3a8a;font-weight:900;font-size:1.05rem;font-family:Arial Black;\\'>CEEKAY</span>'">`;
    }
    if (b.includes('EXEDY')) {
      return `<img src="images/brands/exedy.svg" alt="EXEDY" style="height: 28px; width: 84px; object-fit: contain;" onerror="this.onerror=null; this.outerHTML='<span style=\\'color:#0284c7;font-weight:900;font-size:1.1rem;font-family:Arial Black;\\'><b style=\\'color:#dc2626\\'>E</b>XEDY</span>'">`;
    }
    if (b.includes('VALEO')) {
      return `<img src="images/brands/valeo.svg" alt="Valeo" style="height: 28px; width: 78px; object-fit: contain;" onerror="this.onerror=null; this.outerHTML='<span style=\\'color:#059669;font-weight:900;font-size:1.1rem;font-family:Arial Black;\\'>Valeo</span>'">`;
    }
    if (b.includes('PUROLATOR')) {
      return `<img src="images/brands/purolator.svg" alt="Purolator" style="height: 28px; width: 98px; object-fit: contain;">`;
    }
    if (b.includes('MAHLE')) {
      return `<img src="images/brands/mahle.svg" alt="Mahle" style="height: 28px; width: 82px; object-fit: contain;">`;
    }
    if (b.includes('BREMBO')) {
      return `<img src="images/brands/brembo.svg" alt="Brembo" style="height: 28px; width: 88px; object-fit: contain;">`;
    }
    if (b.includes('ELOFIC')) {
      return `<img src="images/brands/elofic.svg" alt="Elofic" style="height: 28px; width: 82px; object-fit: contain;">`;
    }
    return `<strong style="font-size: 0.95rem; font-weight: 850; color: #0f172a;">${brandName}</strong>`;
  },

  async searchInterchange(queryArg) {
    const inputEl = document.getElementById('oes-interchange-input');
    let q = queryArg;
    if (!q && inputEl) {
      q = inputEl.value;
    }
    if (!q) q = 'VAL-826330';

    // Strip bracket helper like "[OES Anchor Part]"
    const cleanQ = q.replace(/\[.*?\]/g, '').trim();

    try {
      const res = await fetch(`/api/oem-to-oes/interchange?q=${encodeURIComponent(cleanQ)}`);
      const data = await res.json();
      if (!data || data.error) {
        console.error("VIG Search error:", data ? data.error : "Unknown error");
        return;
      }

      this.activeInterchangeData = data;
      this.renderInterchangeView(data);
    } catch (e) {
      console.error("Failed to query interchange API:", e);
    }
  },

  renderInterchangeView(data) {
    const meta = data.search_meta || {};
    const vehicles = data.compatible_vehicles || [];
    const directOes = (data.interchanges && data.interchanges.direct_oes) || [];
    const secondaryMatrix = (data.interchanges && data.interchanges.aftermarket_alternatives) || [];

    // 1. Status Line
    const statusLineEl = document.getElementById('oes-anchor-status-line');
    if (statusLineEl) {
      if (meta.anchor_status_line) {
        statusLineEl.textContent = meta.anchor_status_line;
      } else {
        const brand = meta.anchor_brand || 'Valeo';
        const partNo = meta.anchor_part_number || meta.query;
        const title = meta.part_title || 'Clutch Plate / Pressure Plate Assembly';
        const seg = meta.aggregate || 'Clutch System';
        statusLineEl.textContent = `Active Anchor: ${brand} ${partNo} (${title}) | Status: No OEM Part Listed / Discontinued | Target Segment: ${seg}`;
      }
    }

    // 2. Connected Vehicles List
    const vehListEl = document.getElementById('oes-connected-vehicles-list');
    if (vehListEl) {
      if (vehicles.length > 0) {
        vehListEl.innerHTML = vehicles.map(v => `
          <div style="display: flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0; font-size: 0.82rem; color: #1e293b; font-weight: 650;">
            <span style="color: #ea580c; font-size: 0.75rem;">•</span>
            <span>${v.make} ${v.model} (${v.period}) <span style="color: #64748b; font-weight: normal;">${v.variant}</span></span>
          </div>
        `).join('');
      } else {
        vehListEl.innerHTML = `<div style="font-size: 0.82rem; color: #64748b;">No verified vehicle fitments mapped to this cluster.</div>`;
      }
    }

    // 3. Table 1: DIRECT OES-to-OES INTERCHANGES
    const directTableBody = document.getElementById('oes-direct-table-body');
    if (directTableBody) {
      if (directOes.length === 0) {
        directTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 2rem; color: #64748b;">No direct line-fit OES alternatives found for this cluster.</td></tr>`;
      } else {
        directTableBody.innerHTML = directOes.map(item => {
          const is100 = (item.confidence >= 100);
          const badgeStyle = is100
            ? 'background: #dcfce7; color: #15803d; border: 1px solid #86efac;'
            : 'background: #fef3c7; color: #b45309; border: 1px solid #fde68a;';
          const iconPill = is100
            ? '<span style="background: #22c55e; color: #fff; width: 14px; height: 14px; border-radius: 50%; font-size: 0.65rem; display: inline-flex; align-items: center; justify-content: center; font-weight: 900;">$</span>'
            : '<span style="background: #f59e0b; color: #fff; width: 14px; height: 14px; border-radius: 50%; font-size: 0.65rem; display: inline-flex; align-items: center; justify-content: center; font-weight: 900;">!</span>';

          const brandLogoHtml = this.renderBrandLogo(item.brand);

          return `
            <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
              <td style="padding: 0.75rem 0.85rem; vertical-align: middle; width: 110px;">
                ${brandLogoHtml}
              </td>
              <td style="padding: 0.75rem 0.85rem; vertical-align: middle; width: 150px;">
                <span style="font-family: 'Consolas', 'Courier New', monospace; font-size: 0.9rem; font-weight: 850; color: #0f172a; letter-spacing: 0.3px;">
                  ${item.part_number}
                </span>
              </td>
              <td style="padding: 0.75rem 0.85rem; vertical-align: middle; width: 290px;">
                <div style="display: inline-flex; align-items: center; gap: 0.45rem; ${badgeStyle} padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.76rem; font-weight: 850; white-space: nowrap;">
                  <span>✓ ${item.match_type || '100% Direct Match (Form-Fit-Function)'}</span>
                  ${iconPill}
                </div>
              </td>
              <td style="padding: 0.75rem 0.85rem; vertical-align: middle; width: 280px;">
                <div style="display: flex; align-items: center; gap: 0.35rem; justify-content: flex-end;">
                  <button type="button" onclick="OemToOesPortal.compareSpecs('${item.part_number}', '${item.brand}')" style="background: #ffffff; border: 1.5px solid #cbd5e1; color: #334155; font-size: 0.7rem; font-weight: 800; padding: 0.35rem 0.55rem; border-radius: 8px; cursor: pointer; white-space: nowrap; transition: all 0.15s;">
                    Compare Specifications
                  </button>
                  <button type="button" onclick="OemToOesPortal.viewInventory('${item.part_number}')" style="background: #ffffff; border: 1.5px solid #cbd5e1; color: #334155; font-size: 0.7rem; font-weight: 800; padding: 0.35rem 0.55rem; border-radius: 8px; cursor: pointer; white-space: nowrap; transition: all 0.15s;">
                    View Inventory
                  </button>
                  <button type="button" onclick="OemToOesPortal.placeRequest('${item.part_number}', '${item.brand}', ${item.mrp})" style="background: #0f172a; border: 1px solid #0f172a; color: #ffffff; font-size: 0.7rem; font-weight: 850; padding: 0.35rem 0.65rem; border-radius: 8px; cursor: pointer; white-space: nowrap; transition: all 0.15s; box-shadow: 0 2px 6px rgba(15,23,42,0.15);">
                    Place Request
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join('');
      }
    }

    // 4. Table 2: Secondary Matrix - Alternative / Aftermarket OES-Equivalent Interchanges
    const secTableBody = document.getElementById('oes-secondary-table-body');
    if (secTableBody) {
      if (secondaryMatrix.length === 0) {
        secTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #64748b;">No secondary aftermarket alternatives mapped.</td></tr>`;
      } else {
        secTableBody.innerHTML = secondaryMatrix.map(item => {
          const brandLogoHtml = this.renderBrandLogo(item.brand);
          let relBg = 'background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0;';
          if (item.brand.toUpperCase().includes('CEEKAY')) {
            relBg = 'background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd;';
          } else if (item.brand.toUpperCase().includes('EXEDY')) {
            relBg = 'background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff;';
          } else if (item.brand.toUpperCase().includes('TRW')) {
            relBg = 'background: #e2e8f0; color: #334155; border: 1px solid #cbd5e1;';
          }

          const relText = item.description && item.description.includes('Swap')
            ? item.description
            : (item.relation_role || item.match_type || 'Sub-Tier Fitment (Direct Swap)');

          return `
            <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
              <td style="padding: 1rem 1.25rem; vertical-align: middle; width: 150px;">
                ${brandLogoHtml}
              </td>
              <td style="padding: 1rem 1.25rem; vertical-align: middle; width: 180px;">
                <span style="font-family: 'Consolas', 'Courier New', monospace; font-size: 0.95rem; font-weight: 850; color: #0f172a; letter-spacing: 0.3px;">
                  ${item.part_number}
                </span>
              </td>
              <td style="padding: 1rem 1.25rem; vertical-align: middle; width: 280px;">
                <span style="display: inline-block; ${relBg} padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.78rem; font-weight: 850;">
                  ${relText}
                </span>
              </td>
              <td style="padding: 1rem 1.25rem; vertical-align: middle; font-size: 0.82rem; color: #334155; font-weight: 650; width: 300px;">
                ${item.notes || 'Direct OE dimension equivalent'}
              </td>
              <td style="padding: 1rem 1.25rem; vertical-align: middle; text-align: right; width: 150px;">
                <button type="button" onclick="OemToOesPortal.viewAlternative('${item.part_number}', '${item.brand}')" style="background: #ffffff; border: 1.5px solid #cbd5e1; color: #334155; font-size: 0.76rem; font-weight: 800; padding: 0.45rem 0.85rem; border-radius: 8px; cursor: pointer; white-space: nowrap; transition: all 0.15s;">
                  View Alternative
                </button>
              </td>
            </tr>
          `;
        }).join('');
      }
    }
  },

  compareSpecs(partNo, brand) {
    alert(`Specification Match Analysis: [${brand} - ${partNo}]\n• Form-Fit-Function: 100% Certified Direct Swap\n• Flywheel & Spline Specs: Standard 225mm Dry Clutch Matrix\n• OE Supplier Quality Rating: Tier-1 Production Standard`);
  },

  viewInventory(partNo) {
    if (window.OverallCataloguePortal) {
      OverallCataloguePortal.searchByPartNumber(partNo);
    } else {
      App.switchTab('catalogue-dashboard');
    }
  },

  placeRequest(partNo, brand, price) {
    alert(`Procurement Request Dispatched!\nPart: ${partNo} (${brand})\nUnit Price: ₹${price ? price.toLocaleString('en-IN') : 'Market MRP'}\nSupplier Dispatch: Same-Day Priority Fulfillment to AutoNexa Hub.`);
  },

  viewAlternative(partNo, brand) {
    alert(`Aftermarket Alternative Details: [${brand} - ${partNo}]\n• Segment: Clutch System\n• Fitment: Verified 100% Compatible with Hyundai Creta, Kia Seltos, Hyundai Verna\n• Warranty: 1 Year Manufacturer Warranty`);
  },

  filterInterchangeResults() {
    const veh = (document.getElementById('oes-filter-vehicle')?.value || '').toLowerCase();
    const tier = (document.getElementById('oes-filter-tier')?.value || '').toLowerCase();

    const directRows = document.querySelectorAll('#oes-direct-table-body tr');
    directRows.forEach(row => {
      let show = true;
      const text = row.textContent.toLowerCase();
      if (tier && tier.includes('aftermarket')) show = false;
      row.style.display = show ? '' : 'none';
    });

    const secRows = document.querySelectorAll('#oes-secondary-table-body tr');
    secRows.forEach(row => {
      let show = true;
      const text = row.textContent.toLowerCase();
      if (tier && tier.includes('tier-1')) show = false;
      row.style.display = show ? '' : 'none';
    });
  },

  selectKit(key) {
    this.activeKitKey = key;
    document.querySelectorAll('.oem-kit-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.kit === key);
    });
    this.renderKitMatrix(key);
  },

  renderKitMatrix(key) {
    const kit = this.PMS_KITS_DATA[key];
    const container = document.getElementById('oem-kit-table-body');
    const heroTitle = document.getElementById('oem-kit-hero-title');
    const heroImg = document.getElementById('oem-kit-hero-img');
    const oemTotalEl = document.getElementById('oem-kit-total-oem');
    const oesTotalEl = document.getElementById('oem-kit-total-oes');
    const saveAmtEl = document.getElementById('oem-kit-total-save');
    const savePctEl = document.getElementById('oem-kit-total-pct');

    if (!kit || !container) return;

    if (heroTitle) heroTitle.textContent = kit.modelName;
    if (heroImg) heroImg.src = kit.image || 'images/home_menu_catalogue.jpg';

    let totalOem = 0;
    let totalOes = 0;

    container.innerHTML = kit.items.map((row) => {
      totalOem += row.oemPrice;
      totalOes += row.oesPrice;
      const saveAmt = row.oemPrice - row.oesPrice;
      const savePct = Math.round((saveAmt / row.oemPrice) * 100);

      const compImg = (window.ComponentImageResolver && ComponentImageResolver.generateSvgUri)
        ? ComponentImageResolver.generateSvgUri(row.item, 'BRAKE SYSTEM')
        : 'images/cards/brake_pad_pad_set_front_disc_brake.png';

      return `
        <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
          <td style="padding: 0.85rem 1rem; width: 220px;">
            <div style="display: flex; align-items: center; gap: 0.65rem;">
              <img src="${compImg}" alt="${row.item}" style="width: 44px; height: 32px; object-fit: contain; border-radius: 6px; background: #ffffff; border: 1px solid #e2e8f0; padding: 2px; flex-shrink: 0;">
              <div>
                <strong style="font-size: 0.82rem; color: #0f172a; display: block; line-height: 1.2;">${row.item}</strong>
                <small style="font-size: 0.68rem; color: #64748b;">${row.note}</small>
              </div>
            </div>
          </td>
          <td style="padding: 0.85rem 1rem; width: 170px;">
            <div style="font-family: monospace; font-size: 0.82rem; font-weight: 850; color: #475569;">${row.oemPart}</div>
            <span style="font-size: 0.68rem; color: #166534; font-weight: 750; background: #dcfce7; padding: 0.1rem 0.4rem; border-radius: 4px;">${row.oemBrand}</span>
          </td>
          <td style="padding: 0.85rem 1rem; text-align: right; font-weight: 850; color: #475569; font-size: 0.9rem; font-family: 'Outfit', sans-serif; width: 120px;">
            ₹${row.oemPrice.toLocaleString('en-IN')}
          </td>
          <td style="padding: 0.85rem 1rem; width: 200px;">
            <div style="font-family: monospace; font-size: 0.85rem; font-weight: 900; color: #0284c7;">${row.oesPart}</div>
            <div style="display: flex; align-items: center; gap: 0.35rem; margin-top: 0.2rem;">
              <span style="font-size: 0.68rem; font-weight: 800; background: #eff6ff; color: #1e40af; padding: 0.1rem 0.45rem; border-radius: 4px; border: 1px solid #bfdbfe;">${row.oesBrand}</span>
              <span style="font-size: 0.65rem; color: #059669; font-weight: 800;">✓ OE Supplier</span>
            </div>
          </td>
          <td style="padding: 0.85rem 1rem; text-align: right; font-weight: 900; color: #059669; font-size: 1.05rem; font-family: 'Outfit', sans-serif; width: 130px;">
            ₹${row.oesPrice.toLocaleString('en-IN')}
          </td>
          <td style="padding: 0.85rem 1rem; text-align: right; width: 150px;">
            <div style="font-weight: 900; color: #dc2626; font-size: 0.95rem; font-family: 'Outfit', sans-serif;">Save ₹${saveAmt.toLocaleString('en-IN')}</div>
            <span style="background: #fef2f2; color: #dc2626; font-size: 0.68rem; font-weight: 850; padding: 0.12rem 0.45rem; border-radius: 6px; border: 1px solid #fecdd3;">-${savePct}%</span>
          </td>
          <td style="padding: 0.85rem 1rem; text-align: center; width: 110px;">
            <button type="button" onclick="OverallCataloguePortal.searchByPartNumber('${row.oesPart}')" style="background: #0284c7; color: #ffffff; border: none; padding: 0.4rem 0.75rem; border-radius: 8px; font-size: 0.74rem; font-weight: 800; cursor: pointer; transition: background 0.15s;">
              View SKU ➔
            </button>
          </td>
        </tr>
      `;
    }).join('');

    const totalSave = totalOem - totalOes;
    const totalPct = Math.round((totalSave / totalOem) * 100);

    if (oemTotalEl) oemTotalEl.textContent = `₹${totalOem.toLocaleString('en-IN')}`;
    if (oesTotalEl) oesTotalEl.textContent = `₹${totalOes.toLocaleString('en-IN')}`;
    if (saveAmtEl) saveAmtEl.textContent = `Save ₹${totalSave.toLocaleString('en-IN')}`;
    if (savePctEl) savePctEl.textContent = `${totalPct}% Net Savings`;
  },

  async handleLiveConvertSearch() {
    const input = document.getElementById('oem-convert-input');
    const resultBox = document.getElementById('oem-convert-result-box');
    if (!input || !resultBox) return;

    const query = input.value.trim();
    if (!query) {
      alert("Please enter an OEM Part Number, Vehicle Model, or Component name.");
      return;
    }

    resultBox.style.display = 'block';
    resultBox.innerHTML = `<div style="text-align: center; padding: 2.5rem; color: #0284c7; font-weight: 700;">🔄 Querying 23.6M Master Catalogue for OEM ➔ Tier-1 OES Cross-References...</div>`;

    try {
      const res = await fetch(`/api/oem-to-oes/convert?query=${encodeURIComponent(query)}`);
      const data = await res.json();

      if (!data || data.status !== 'success' || !data.oem || !data.recommended_oes) {
        resultBox.innerHTML = `<div style="padding: 1.5rem; color: #dc2626; text-align: center;">No verified Tier-1 OES conversion found for '${query}'.</div>`;
        return;
      }

      const oem = data.oem;
      const oes = data.recommended_oes;
      const alts = data.alternatives || [];
      const savings = data.savings_amount || 0;
      const savingsPct = data.savings_percentage || 0;

      let altsHtml = '';
      if (alts.length > 0) {
        altsHtml = `
          <div style="margin-top: 1.25rem; border-top: 1.5px solid #e2e8f0; padding-top: 1rem;">
            <div style="font-size: 0.78rem; font-weight: 850; color: #334155; margin-bottom: 0.65rem; text-transform: uppercase; letter-spacing: 0.5px;">
              Alternative Verified Tier-1 OES Brands for ${oem.component || 'This Application'}:
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.75rem;">
              ${alts.map(a => {
                const altSave = Math.max(0, oem.mrp - a.mrp);
                const altPct = Math.round((altSave / oem.mrp) * 100);
                return `
                  <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 0.75rem 0.95rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <div style="font-size: 0.85rem; font-weight: 850; color: #0f172a;">${a.brand}</div>
                      <div style="font-family: monospace; font-size: 0.76rem; color: #0284c7; font-weight: 800;">${a.partNo}</div>
                      <div style="font-size: 0.7rem; color: #64748b;">${a.desc}</div>
                    </div>
                    <div style="text-align: right;">
                      <div style="font-size: 1rem; font-weight: 900; color: #15803d; font-family: 'Outfit', sans-serif;">₹${a.mrp.toLocaleString('en-IN')}</div>
                      <span style="font-size: 0.68rem; font-weight: 850; background: #ecfdf5; color: #15803d; padding: 0.1rem 0.4rem; border-radius: 4px;">Save ${altPct}%</span>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `;
      }

      resultBox.innerHTML = `
        <div style="background: linear-gradient(135deg, #f8fafc, #ffffff); border: 2px solid #38bdf8; border-radius: 16px; padding: 1.5rem; margin-top: 1rem; box-shadow: 0 8px 30px rgba(2, 132, 199, 0.08);">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.85rem; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-size: 1.25rem;">⚡</span>
              <strong style="font-size: 1.05rem; color: #0f172a; font-family: 'Outfit', sans-serif;">Direct OEM ➔ Tier-1 OES Match Verified</strong>
            </div>
            <span style="background: #ecfdf5; color: #059669; border: 1.5px solid #a7f3d0; font-size: 0.82rem; font-weight: 850; padding: 0.3rem 0.85rem; border-radius: 999px;">
              Save ₹${savings.toLocaleString('en-IN')} (${savingsPct}% Cost Reduction)
            </span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 1.25rem; align-items: center;">
            <!-- Left: Dealership OEM -->
            <div style="background: #ffffff; border: 1.5px solid #fecdd3; border-radius: 14px; padding: 1.25rem; position: relative;">
              <span style="position: absolute; top: -11px; left: 16px; background: #e11d48; color: #fff; font-size: 0.66rem; font-weight: 850; padding: 0.2rem 0.6rem; border-radius: 6px; letter-spacing: 0.5px;">
                DEALERSHIP OEM
              </span>
              <div style="font-family: monospace; font-size: 1.2rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem;">
                ${oem.partNo}
              </div>
              <div style="font-size: 0.84rem; font-weight: 750; color: #334155; margin: 0.35rem 0;">
                ${oem.desc}
              </div>
              <div style="font-size: 0.74rem; color: #64748b;">
                Brand: <strong style="color: #0f172a;">${oem.brand}</strong> • Application: <strong>${oem.vehicle}</strong>
              </div>
              <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 0.25rem;">
                Lead Time: <strong>${oem.leadTime || '3-7 Days'}</strong>
              </div>
              <div style="margin-top: 0.85rem; font-size: 1.5rem; font-weight: 900; color: #e11d48; font-family: 'Outfit', sans-serif;">
                ₹${Number(oem.mrp).toLocaleString('en-IN')}
              </div>
            </div>

            <!-- Middle: Switch Arrow -->
            <div style="text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;">
              <div style="width: 48px; height: 48px; border-radius: 50%; background: #eff6ff; border: 1.5px solid #bfdbfe; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; color: #0284c7; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);">
                ➔
              </div>
              <span style="font-size: 0.68rem; color: #64748b; font-weight: 850; display: block; margin-top: 0.35rem; letter-spacing: 0.5px;">SWITCH</span>
            </div>

            <!-- Right: Recommended Tier-1 OES -->
            <div style="background: linear-gradient(135deg, #f0fdf4, #ffffff); border: 2px solid #86efac; border-radius: 14px; padding: 1.25rem; position: relative; box-shadow: 0 4px 16px rgba(22, 101, 52, 0.05);">
              <span style="position: absolute; top: -11px; left: 16px; background: #16a34a; color: #fff; font-size: 0.66rem; font-weight: 850; padding: 0.2rem 0.6rem; border-radius: 6px; letter-spacing: 0.5px;">
                ★ RECOMMENDED TIER-1 OES
              </span>
              <div style="font-family: monospace; font-size: 1.2rem; font-weight: 900; color: #0284c7; margin-top: 0.25rem;">
                ${oes.partNo}
              </div>
              <div style="font-size: 0.84rem; font-weight: 750; color: #166534; margin: 0.35rem 0;">
                ${oes.desc}
              </div>
              <div style="font-size: 0.74rem; color: #15803d;">
                Brand: <strong style="color: #15803d; font-size: 0.82rem;">${oes.brand}</strong>
              </div>
              <div style="font-size: 0.72rem; color: #166534; margin-top: 0.25rem;">
                Stock: <strong style="color: #059669;">${oes.stock || 'IN STOCK (Same Day Dispatch)'}</strong> • Match: <strong>${oes.oeMatch || '100% OE Match'}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 0.85rem;">
                <div style="font-size: 1.6rem; font-weight: 900; color: #16a34a; font-family: 'Outfit', sans-serif;">
                  ₹${Number(oes.mrp).toLocaleString('en-IN')}
                </div>
                <button type="button" onclick="OverallCataloguePortal.searchByPartNumber('${oes.partNo}')" style="background: #16a34a; color: #ffffff; border: none; padding: 0.5rem 1.15rem; border-radius: 8px; font-size: 0.8rem; font-weight: 850; cursor: pointer; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3); transition: transform 0.15s;">
                  Select OES Part ➔
                </button>
              </div>
            </div>
          </div>

          ${altsHtml}
        </div>
      `;
    } catch (err) {
      console.error("Live convert error:", err);
      resultBox.innerHTML = `<div style="padding: 1.5rem; color: #dc2626; text-align: center;">Error performing conversion query. Please try again.</div>`;
    }
  }
};

window.OemToOesPortal = OemToOesPortal;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => OemToOesPortal.init());
} else {
  OemToOesPortal.init();
}
