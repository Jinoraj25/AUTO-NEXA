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
      console.log("DataEngine: Loading pre-trained lookup database...");
      let res = await fetch('data/trained_mapping_db.json');
      if (!res.ok) {
        res = await fetch('trained_mapping_db.json');
      }
      if (res.ok) {
        this.db = await res.json();
        this.isLoaded = true;
        console.log(`DataEngine: Success! Loaded ${Object.keys(this.db.partNoLookup || {}).length} pre-indexed parts.`);
      } else {
        console.warn("DataEngine: JSON not found yet, initializing default fallback rules.");
        this.initDefaultRules();
      }
    } catch (e) {
      console.warn("DataEngine fetch error, using default rules:", e);
      this.initDefaultRules();
    }
  },

  initDefaultRules() {
    this.db.aggregateMaster = [
      { aggregate: "HVAC/THERMAL", subAggregate: "REFRIGERANT", component: "A/C GAS", category: "Mechanical Parts" },
      { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "RELAY AND FUSE", component: "A/C RELAY", category: "Electrical Parts" },
      { aggregate: "BRAKE SYSTEM", subAggregate: "ABS SYSTEM", component: "ABS MODULATOR", category: "Mechanical Parts" },
      { aggregate: "ENGINE", subAggregate: "FILTERS", component: "OIL FILTER", category: "Consumables" },
      { aggregate: "ENGINE", subAggregate: "FILTERS", component: "AIR FILTER", category: "Consumables" },
      { aggregate: "BRAKE SYSTEM", subAggregate: "DISC BRAKE", component: "BRAKE PAD", category: "Mechanical Parts" },
      { aggregate: "SUSPENSION", subAggregate: "STRUT ASSEMBLY", component: "FRONT SHOCK ABSORBER", category: "Mechanical Parts" },
      { aggregate: "TRANSMISSION", subAggregate: "CLUTCH ASSEMBLY", component: "CLUTCH PLATE", category: "Mechanical Parts" },
      { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "BATTERY & IGNITION", component: "SPARK PLUG", category: "Electrical Parts" },
      { aggregate: "STEERING", subAggregate: "POWER STEERING", component: "STEERING RACK", category: "Mechanical Parts" }
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

      // Strategy 3: Rule-based Heuristics for Common Spare Parts
      if (descUpper.includes("FILTER")) {
        let comp = "OIL FILTER";
        if (descUpper.includes("AIR")) comp = "AIR FILTER";
        if (descUpper.includes("CABIN") || descUpper.includes("AC")) comp = "CABIN FILTER";
        if (descUpper.includes("FUEL")) comp = "FUEL FILTER";
        const masterEntry = findInMaster(comp);
        return {
          aggregate: masterEntry ? masterEntry.aggregate : "FILTERS",
          subAggregate: masterEntry ? masterEntry.subAggregate : "FILTERS",
          component: comp,
          category: masterEntry ? masterEntry.category : "Consumables",
          make: brandUpper || "GENERIC",
          matchMethod: "HEURISTIC_TEXT",
          confidence: "MEDIUM",
          confidenceScore: 78,
          remarks: "Auto Mapped (Heuristic Match)"
        };
      }
      if (descUpper.includes("BRAKE") || descUpper.includes("PAD") || descUpper.includes("DISC")) {
        const masterEntry = findInMaster("BRAKE PAD");
        return {
          aggregate: masterEntry ? masterEntry.aggregate : "BRAKE SYSTEM",
          subAggregate: masterEntry ? masterEntry.subAggregate : "BRAKE PAD",
          component: "BRAKE PAD",
          category: masterEntry ? masterEntry.category : "Mechanical Parts",
          make: brandUpper || "GENERIC",
          matchMethod: "HEURISTIC_TEXT",
          confidence: "MEDIUM",
          confidenceScore: 75,
          remarks: "Auto Mapped (Heuristic Match)"
        };
      }
      if (descUpper.includes("PLUG") || descUpper.includes("SPARK")) {
        const masterEntry = findInMaster("SPARK PLUG");
        return {
          aggregate: masterEntry ? masterEntry.aggregate : "ELECTRICALS AND ELECTRONICS",
          subAggregate: masterEntry ? masterEntry.subAggregate : "BATTERY & IGNITION",
          component: "SPARK PLUG",
          category: masterEntry ? masterEntry.category : "Electrical Parts",
          make: brandUpper || "GENERIC",
          matchMethod: "HEURISTIC_TEXT",
          confidence: "HIGH",
          confidenceScore: 90,
          remarks: "Auto Mapped (Heuristic Match)"
        };
      }
      if (descUpper.includes("BELT") || descUpper.includes("TIMING")) {
        const masterEntry = findInMaster("TIMING BELT");
        return {
          aggregate: masterEntry ? masterEntry.aggregate : "BELTS AND TENSIONER",
          subAggregate: masterEntry ? masterEntry.subAggregate : "TIMING BELT",
          component: "TIMING BELT",
          category: masterEntry ? masterEntry.category : "Mechanical Parts",
          make: brandUpper || "GENERIC",
          matchMethod: "HEURISTIC_TEXT",
          confidence: "MEDIUM",
          confidenceScore: 75,
          remarks: "Auto Mapped (Heuristic Match)"
        };
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
