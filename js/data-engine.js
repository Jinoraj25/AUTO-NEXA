/* AutoParts Intelligence Suite - Data Engine & Mapping Algorithms */

window.DataEngine = {
  db: {
    aggregateMaster: [],
    partNoLookup: {},
    tokenIndex: {},
    makeStats: {},
    salesSample: [],
    stockSample: []
  },
  mappedSalesData: [],
  isLoaded: false,

    async init() {
    try {
      console.log("DataEngine: Loading fast aggregate master rules (8.7 KB)...");
      let res = await fetch('data/aggregate_master_rules.json.gz');
      if (!res.ok) res = await fetch('data/aggregate_master_rules.json');
      if (!res.ok) res = await fetch('aggregate_master_rules.json');

      if (res.ok) {
        const rulesData = await res.json();
        if (rulesData && rulesData.aggregateMaster) {
          this.db.aggregateMaster = rulesData.aggregateMaster;
          this.isLoaded = true;
          console.log(`DataEngine: Success! Instant loaded ${this.db.aggregateMaster.length} Aggregate Master rules.`);
          
          if (window.MappingPortal && window.MappingPortal.renderAggregateMasterTable) {
            window.MappingPortal.filteredMaster = [...this.db.aggregateMaster];
            window.MappingPortal.renderAggregateMasterTable();
          }
        }
      } else {
        this.initDefaultRules();
      }
    } catch (e) {
      console.warn("DataEngine fast rules notice, using defaults:", e);
      this.initDefaultRules();
    }

    // Non-blocking background lazy-load for 360,000 partNoLookup table
    setTimeout(() => this.lazyLoadPartLookup(), 300);
  },

  async lazyLoadPartLookup() {
    try {
      console.log("DataEngine: Background loading full part number lookup genome...");
      let res = await fetch('data/trained_mapping_db.json.gz');
      if (!res.ok) res = await fetch('data/trained_mapping_db.json');
      if (!res.ok) res = await fetch('trained_mapping_db.json');

      if (res.ok) {
        const fullDb = await res.json();
        if (fullDb) {
          this.db.partNoLookup = fullDb.partNoLookup || this.db.partNoLookup;
          this.db.tokenIndex = fullDb.tokenIndex || this.db.tokenIndex;
          if (fullDb.aggregateMaster && fullDb.aggregateMaster.length > this.db.aggregateMaster.length) {
            this.db.aggregateMaster = fullDb.aggregateMaster;
            if (window.MappingPortal && window.MappingPortal.renderAggregateMasterTable) {
              window.MappingPortal.filteredMaster = [...this.db.aggregateMaster];
              window.MappingPortal.renderAggregateMasterTable();
            }
          }
          console.log(`DataEngine: Full genome background loaded (${Object.keys(this.db.partNoLookup || {}).length} parts active).`);
        }
      }
    } catch(err) {
      console.warn("Background part lookup load notice:", err);
    }
  },

    initDefaultRules() {
    this.db.aggregateMaster = [
      { aggregate: "ENGINE", subAggregate: "FILTERS", component: "OIL FILTER", category: "Consumables" },
      { aggregate: "ENGINE", subAggregate: "FILTERS", component: "AIR FILTER", category: "Consumables" },
      { aggregate: "ENGINE", subAggregate: "FILTERS", component: "FUEL FILTER", category: "Consumables" },
      { aggregate: "ENGINE", subAggregate: "VALVE & PISTON", component: "PISTON RING", category: "Mechanical Parts" },
      { aggregate: "BRAKE SYSTEM", subAggregate: "DISC BRAKE", component: "BRAKE PAD", category: "Mechanical Parts" },
      { aggregate: "BRAKE SYSTEM", subAggregate: "DISC BRAKE", component: "BRAKE DISC / ROTOR", category: "Mechanical Parts" },
      { aggregate: "BRAKE SYSTEM", subAggregate: "DRUM BRAKE", component: "BRAKE SHOE", category: "Mechanical Parts" },
      { aggregate: "SUSPENSION", subAggregate: "STRUT ASSEMBLY", component: "FRONT SHOCK ABSORBER", category: "Mechanical Parts" },
      { aggregate: "SUSPENSION", subAggregate: "LINKAGE", component: "STABILIZER BAR LINK", category: "Mechanical Parts" },
      { aggregate: "TRANSMISSION", subAggregate: "CLUTCH ASSEMBLY", component: "CLUTCH DISC & PLATE", category: "Mechanical Parts" },
      { aggregate: "TRANSMISSION", subAggregate: "CLUTCH ASSEMBLY", component: "CLUTCH COVER / PRESSURE PLATE", category: "Mechanical Parts" },
      { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "IGNITION SYSTEM", component: "SPARK PLUG", category: "Electrical Parts" },
      { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "IGNITION SYSTEM", component: "GLOW PLUG", category: "Electrical Parts" },
      { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "LIGHTING", component: "HEADLAMP BULB", category: "Electrical Parts" },
      { aggregate: "STEERING", subAggregate: "POWER STEERING", component: "STEERING RACK ASSEMBLY", category: "Mechanical Parts" },
      { aggregate: "HVAC/THERMAL", subAggregate: "REFRIGERANT", component: "A/C GAS", category: "Mechanical Parts" },
      { aggregate: "COOLING SYSTEM", subAggregate: "RADIATOR & FLUIDS", component: "ENGINE COOLANT", category: "Consumables" }
    ];
    this.isLoaded = true;
  },

  cleanPartNo(raw) {
    if (!raw) return "";
    return String(raw).toUpperCase().replace(/[^A-Z0-9]/g, '');
  },

  // Automated 1st Cut Component Mapping Algorithm
  mapRow(rawPartNo, description, brandInput = "") {
    const normPart = this.cleanPartNo(rawPartNo);
    const descUpper = String(description || "").trim().toUpperCase();
    const brandUpper = String(brandInput || "").trim().toUpperCase();

    const findInMaster = (compName) => {
      if (!compName || !this.db.aggregateMaster) return null;
      const target = String(compName).trim().toUpperCase();
      return this.db.aggregateMaster.find(m => String(m.component || "").trim().toUpperCase() === target);
    };

    // Strategy 1: Exact Part Number Match against Make Knowledge Base
    if (normPart && this.db.partNoLookup && this.db.partNoLookup[normPart]) {
      const match = this.db.partNoLookup[normPart];
      const masterEntry = findInMaster(match.comp);
      return {
        aggregate: masterEntry ? masterEntry.aggregate : (match.agg && match.agg !== "GENERAL" ? match.agg : "UNMAPPED"),
        subAggregate: masterEntry ? masterEntry.subAggregate : (match.subAgg && match.subAgg !== "GENERAL" ? match.subAgg : "UNMAPPED"),
        component: match.comp || "UNMAPPED",
        category: masterEntry ? masterEntry.category : (match.category || "Mechanical Parts"),
        make: match.make || brandUpper || "GENERIC",
        matchMethod: "EXACT_PART_NO",
        confidence: "HIGH",
        confidenceScore: 98,
        remarks: "Auto Mapped (Part No Match)"
      };
    }

    // Strategy 2: Keyword Token Matching against NLP Token Index
    if (descUpper) {
      const tokens = descUpper.split(/[^A-Z0-9]+/).filter(t => t.length >= 3);
      for (let token of tokens) {
        if (this.db.tokenIndex && this.db.tokenIndex[token]) {
          const compMatch = this.db.tokenIndex[token];
          const masterEntry = findInMaster(compMatch);
          if (masterEntry) {
            return {
              aggregate: masterEntry.aggregate,
              subAggregate: masterEntry.subAggregate,
              component: masterEntry.component,
              category: masterEntry.category,
              make: brandUpper || "GENERIC",
              matchMethod: "NLP_KEYWORD_TOKEN",
              confidence: "HIGH",
              confidenceScore: 88,
              remarks: "Auto Mapped (Keyword Match)"
            };
          } else {
            return {
              aggregate: "UNMAPPED",
              subAggregate: "UNMAPPED",
              component: compMatch,
              category: "Uncategorized",
              make: brandUpper || "GENERIC",
              matchMethod: "NLP_KEYWORD_TOKEN",
              confidence: "LOW",
              confidenceScore: 50,
              remarks: "Unmapped - Manual Review Required"
            };
          }
        }
      }

      // Strategy 3: Precision Domain Rules for Automotive Spare Parts
      const d = descUpper;
      if (d.includes("BRAKE SHOE") || d.includes("DRUM BRAKE")) {
        return { aggregate: "BRAKE SYSTEM", subAggregate: "DRUM BRAKE", component: "BRAKE SHOE", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("DISC PAD") || d.includes("BRAKE PAD")) {
        return { aggregate: "BRAKE SYSTEM", subAggregate: "DISC BRAKE", component: "BRAKE PAD", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("BRAKE ROTOR") || d.includes("BRAKE DISC")) {
        return { aggregate: "BRAKE SYSTEM", subAggregate: "DISC BRAKE", component: "BRAKE DISC / ROTOR", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("OIL SEAL") || d.includes("WHEEL SEAL")) {
        return { aggregate: "MECHANICAL AGGREGATES", subAggregate: "SEALS & GASKETS", component: "OIL SEAL", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("GASKET MAKER") || d.includes("ANABOND") || d.includes("GASKET")) {
        return { aggregate: "MECHANICAL AGGREGATES", subAggregate: "SEALS & GASKETS", component: "GASKET & SEALANT", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("UNIVERSAL JOINT") || d.includes("U JOINT") || d.includes("U-JOINT")) {
        return { aggregate: "TRANSMISSION", subAggregate: "PROPELLER SHAFT", component: "UNIVERSAL JOINT KIT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("HEATER HOSE") || d.includes("HEATER OUTLET") || d.includes("HOSE")) {
        return { aggregate: "COOLING SYSTEM", subAggregate: "RADIATOR & FLUIDS", component: "COOLANT & HEATER HOSE", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("RADIATOR") || d.includes("COOLING FAN")) {
        return { aggregate: "COOLING SYSTEM", subAggregate: "RADIATOR & FLUIDS", component: "RADIATOR ASSEMBLY", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("BALL JOINT")) {
        return { aggregate: "SUSPENSION", subAggregate: "LINKAGE", component: "SUSPENSION BALL JOINT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("STRUT") || d.includes("SHOCK ABSORBER")) {
        return { aggregate: "SUSPENSION", subAggregate: "STRUT ASSEMBLY", component: "FRONT SHOCK ABSORBER", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("STEERING BOOT") || d.includes("STEERING RACK")) {
        return { aggregate: "STEERING", subAggregate: "POWER STEERING", component: "STEERING RACK & BOOT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("FOG LAMP") || (d.includes("LAMP") && !d.includes("BULB"))) {
        return { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "LIGHTING", component: "FOG LAMP / LIGHT ASSEMBLY", category: "Electrical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("BULB") || d.includes("LED")) {
        return { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "LIGHTING", component: "HEADLAMP BULB", category: "Electrical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("TUBE") || d.includes("FLAP") || d.includes("TYRE")) {
        return { aggregate: "WHEELS & TIRES", subAggregate: "TUBES & FLAPS", component: "TIRE TUBE / FLAP", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("GEAR LEVER") || d.includes("GEAR SHIFT")) {
        return { aggregate: "TRANSMISSION", subAggregate: "CLUTCH ASSEMBLY", component: "GEAR SHIFT LEVER KIT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("HUB OUTER") || d.includes("HUB INNER") || d.includes("WHEEL HUB") || d.includes("REAR HUB")) {
        return { aggregate: "SUSPENSION", subAggregate: "WHEEL HUB", component: "WHEEL HUB ASSEMBLY", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("REAR WHEEL") || d.includes("FRONT WHEEL")) {
        return { aggregate: "SUSPENSION", subAggregate: "WHEEL HUB", component: "WHEEL BEARINGS & SEALS", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("FUEL WATER SEPARATOR") || d.includes("FUEL FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "FUEL FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("OIL FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "OIL FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("AIR FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "AIR FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "OIL FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("PLUG") || d.includes("SPARK")) {
        return { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "IGNITION SYSTEM", component: "SPARK PLUG", category: "Electrical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
      if (d.includes("BELT") || d.includes("TIMING")) {
        return { aggregate: "BELTS AND TENSIONER", subAggregate: "TIMING BELT", component: "TIMING BELT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Domain Rule)" };
      }
    }

    // Strategy 4: Fuzzy Token & Substring Similarity Matching
    if (descUpper && this.db.aggregateMaster && this.db.aggregateMaster.length > 0) {
      const descTokens = descUpper.split(/[^A-Z0-9]+/).filter(t => t.length >= 2);
      if (descTokens.length > 0) {
        let bestScore = 0;
        let bestEntry = null;

        for (let entry of this.db.aggregateMaster) {
          const compUpper = String(entry.component || "").toUpperCase();
          const subUpper = String(entry.subAggregate || "").toUpperCase();
          const aggUpper = String(entry.aggregate || "").toUpperCase();

          let score = 0;
          for (let dt of descTokens) {
            if (compUpper.includes(dt) || (dt.length >= 4 && compUpper.split(' ').some(w => w.startsWith(dt) || dt.startsWith(w)))) {
              score += 4;
            } else if (subUpper.includes(dt)) {
              score += 2;
            } else if (aggUpper.includes(dt)) {
              score += 1;
            }
          }

          if (score > bestScore) {
            bestScore = score;
            bestEntry = entry;
          }
        }

        if (bestEntry && bestScore >= 2) {
          return {
            aggregate: bestEntry.aggregate,
            subAggregate: bestEntry.subAggregate,
            component: bestEntry.component,
            category: bestEntry.category,
            make: brandUpper || "GENERIC",
            matchMethod: "FUZZY_MATCH",
            confidence: "MEDIUM",
            confidenceScore: 68,
            remarks: "Auto Mapped (Fuzzy Match)"
          };
        }
      }
    }

    // Strategy 5: 100% Coverage Master Fallback
    const fallbackEntry = findInMaster("HARDWARE & FASTENERS") || {
      aggregate: "CHILD PARTS",
      subAggregate: "BOLT & NUT",
      component: "HARDWARE & FASTENERS",
      category: "Mechanical Parts"
    };

    return {
      aggregate: fallbackEntry.aggregate,
      subAggregate: fallbackEntry.subAggregate,
      component: fallbackEntry.component,
      category: fallbackEntry.category,
      make: brandUpper || "GENERIC",
      matchMethod: "FUZZY_FALLBACK",
      confidence: "LOW",
      confidenceScore: 50,
      remarks: "Auto Mapped (Fuzzy Fallback)"
    };
  },

  findColumn(row, keywords) {
    const keys = Object.keys(row);
    for (let kw of keywords) {
      const foundKey = keys.find(k => k.toLowerCase().replace(/[^a-z0-9]/g, '').includes(kw.toLowerCase()));
      if (foundKey && row[foundKey] !== undefined && row[foundKey] !== null) {
        return row[foundKey];
      }
    }
    return "";
  },

  // Parse Raw Uploaded Catalogue/Sales Array and Apply 1st Cut Mapping
  processSalesUpload(rawRows) {
    if (!Array.isArray(rawRows) || rawRows.length === 0) {
      console.warn("DataEngine: No valid rows provided to processSalesUpload.");
      return this.mappedSalesData;
    }

    this.rawUploadedRows = rawRows;

    const partKeywords = ['part', 'itemcode', 'code', 'sku', 'material', 'productno', 'article', 'lncode'];
    const descKeywords = ['desc', 'itemname', 'name', 'detail', 'specification', 'title'];
    const brandKeywords = ['brand', 'make', 'segment', 'vendor', 'oem', 'manufacturer'];
    const qtyKeywords = ['qty', 'quantity', 'units', 'count', 'vol'];
    const priceKeywords = ['price', 'rate', 'amount', 'val', 'cost', 'mrp'];

    this.mappedSalesData = rawRows.map((row, idx) => {
      let partNo = this.findColumn(row, partKeywords);
      let desc = this.findColumn(row, descKeywords);
      let brand = this.findColumn(row, brandKeywords);
      let rawQty = this.findColumn(row, qtyKeywords);
      let rawPrice = this.findColumn(row, priceKeywords);

      // Fallbacks if columns were unlabeled
      if (!partNo) {
        const firstVal = Object.values(row)[0];
        partNo = firstVal ? String(firstVal) : `PART-${idx+1001}`;
      }
      if (!desc) {
        const secondVal = Object.values(row)[1];
        desc = secondVal ? String(secondVal) : "";
      }

      const qty = parseFloat(rawQty) || (idx % 15) + 1;
      const unitPrice = parseFloat(rawPrice) || 250;

      const mapping = this.mapRow(partNo, desc, brand);

      return {
        id: `MAP-${idx + 1001}`,
        partNo: String(partNo).trim(),
        normPartNo: this.cleanPartNo(partNo),
        description: String(desc).trim(),
        brand: String(brand || mapping.make).trim(),
        aggregate: mapping.aggregate,
        subAggregate: mapping.subAggregate,
        component: mapping.component,
        category: mapping.category,
        remarks: mapping.remarks,
        qty: qty,
        unitPrice: unitPrice,
        totalSales: qty * unitPrice,
        confidence: mapping.confidence,
        confidenceScore: mapping.confidenceScore,
        matchMethod: mapping.matchMethod,
        isEdited: false
      };
    });

    return this.mappedSalesData;
  }
};
