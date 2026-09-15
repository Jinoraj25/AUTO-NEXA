import os

with open('js/data-engine.js', 'r', encoding='utf-8') as f:
    code = f.read()

new_map_row = '''  // Automated 1st Cut Component Mapping Algorithm
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

    // Strategy 2: Precision Domain Rules for Automotive Spare Parts (PRIORITY 1 FOR TEXT MATCHING)
    if (descUpper) {
      const d = descUpper;
      
      // 1. BRAKE SYSTEM
      if (d.includes("BRAKE SHOE") || d.includes("DRUM BRAKE")) {
        return { aggregate: "BRAKE SYSTEM", subAggregate: "DRUM BRAKE", component: "BRAKE SHOE", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 98, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("DISC PAD") || d.includes("BRAKE PAD")) {
        return { aggregate: "BRAKE SYSTEM", subAggregate: "DISC BRAKE", component: "BRAKE PAD", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 98, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("BRAKE ROTOR") || d.includes("BRAKE DISC")) {
        return { aggregate: "BRAKE SYSTEM", subAggregate: "DISC BRAKE", component: "BRAKE DISC / ROTOR", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 98, remarks: "Auto Mapped (Heuristic Match)" };
      }

      // 2. MECHANICAL AGGREGATES / GASKETS & SEALS
      if (d.includes("OIL SEAL") || d.includes("WHEEL SEAL")) {
        return { aggregate: "MECHANICAL AGGREGATES", subAggregate: "SEALS & GASKETS", component: "OIL SEAL", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("GASKET MAKER") || d.includes("ANABOND") || d.includes("GASKET")) {
        return { aggregate: "MECHANICAL AGGREGATES", subAggregate: "SEALS & GASKETS", component: "GASKET & SEALANT", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }

      // 3. TRANSMISSION & DRIVETRAIN
      if (d.includes("UNIVERSAL JOINT") || d.includes("U JOINT") || d.includes("U-JOINT") || d.includes("U.J. KIT")) {
        return { aggregate: "TRANSMISSION", subAggregate: "PROPELLER SHAFT", component: "UNIVERSAL JOINT KIT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("GEAR LEVER") || d.includes("GEAR SHIFT")) {
        return { aggregate: "TRANSMISSION", subAggregate: "CLUTCH ASSEMBLY", component: "GEAR SHIFT LEVER KIT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("CLUTCH DISC") || d.includes("CLUTCH PLATE") || d.includes("CLUTCH FACING")) {
        return { aggregate: "TRANSMISSION", subAggregate: "CLUTCH ASSEMBLY", component: "CLUTCH DISC & PLATE", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 98, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("CLUTCH COVER") || d.includes("PRESSURE PLATE") || d.includes("CLUTCH KIT")) {
        return { aggregate: "TRANSMISSION", subAggregate: "CLUTCH ASSEMBLY", component: "CLUTCH COVER / PRESSURE PLATE", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 98, remarks: "Auto Mapped (Heuristic Match)" };
      }

      // 4. COOLING SYSTEM & HOSES
      if (d.includes("HEATER HOSE") || d.includes("HEATER OUTLET") || d.includes("BOTTOM HOSE") || d.includes("TOP HOSE") || d.includes("HOSE")) {
        return { aggregate: "COOLING SYSTEM", subAggregate: "RADIATOR & FLUIDS", component: "COOLANT & HEATER HOSE", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("RADIATOR") || d.includes("COOLING FAN")) {
        return { aggregate: "COOLING SYSTEM", subAggregate: "RADIATOR & FLUIDS", component: "RADIATOR ASSEMBLY", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }

      // 5. SUSPENSION & STEERING
      if (d.includes("BALL JOINT")) {
        return { aggregate: "SUSPENSION", subAggregate: "LINKAGE", component: "SUSPENSION BALL JOINT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("STRUT") || d.includes("SHOCK ABSORBER")) {
        return { aggregate: "SUSPENSION", subAggregate: "STRUT ASSEMBLY", component: "FRONT SHOCK ABSORBER", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("HUB OUTER") || d.includes("HUB INNER") || d.includes("WHEEL HUB") || d.includes("REAR HUB")) {
        return { aggregate: "SUSPENSION", subAggregate: "WHEEL HUB", component: "WHEEL HUB ASSEMBLY", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("REAR WHEEL") || d.includes("FRONT WHEEL")) {
        return { aggregate: "SUSPENSION", subAggregate: "WHEEL HUB", component: "WHEEL BEARINGS & SEALS", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("STEERING BOOT") || d.includes("STEERING RACK")) {
        return { aggregate: "STEERING", subAggregate: "POWER STEERING", component: "STEERING RACK & BOOT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }

      // 6. ELECTRICALS & LIGHTING
      if (d.includes("FOG LAMP")) {
        return { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "LIGHTING", component: "FOG LAMP / LIGHT ASSEMBLY", category: "Electrical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("BULB") || d.includes("LED") || d.includes("W5W")) {
        return { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "LIGHTING", component: "HEADLAMP BULB", category: "Electrical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("SPARK PLUG") || d.includes("GLOW PLUG") || d.includes("SPARK") || d.includes("IGNITION")) {
        return { aggregate: "ELECTRICALS AND ELECTRONICS", subAggregate: "IGNITION SYSTEM", component: "SPARK PLUG", category: "Electrical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }

      // 7. WHEELS & TIRES / TUBES & FLAPS
      if (d.includes("TUBE") || d.includes("FLAP") || d.includes("TYRE")) {
        return { aggregate: "WHEELS & TIRES", subAggregate: "TUBES & FLAPS", component: "TIRE TUBE / FLAP", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }

      // 8. ENGINE & FILTERS
      if (d.includes("FUEL WATER SEPARATOR") || d.includes("FUEL FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "FUEL FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("OIL FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "OIL FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("AIR FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "AIR FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("FILTER")) {
        return { aggregate: "ENGINE", subAggregate: "FILTERS", component: "OIL FILTER", category: "Consumables", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
      if (d.includes("BELT") || d.includes("TIMING")) {
        return { aggregate: "BELTS AND TENSIONER", subAggregate: "TIMING BELT", component: "TIMING BELT", category: "Mechanical Parts", make: brandUpper || "GENERIC", matchMethod: "DOMAIN_RULE", confidence: "HIGH", confidenceScore: 95, remarks: "Auto Mapped (Heuristic Match)" };
      }
    }

    // Strategy 3: Keyword Token Matching against NLP Token Index
    if (descUpper) {
      const tokens = descUpper.split(/[^A-Z0-9]+/).filter(t => t.length >= 4);
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
          }
        }
      }
    }

    // Strategy 4: Fuzzy Token & Substring Similarity Matching
    if (descUpper && this.db.aggregateMaster && this.db.aggregateMaster.length > 0) {
      const descTokens = descUpper.split(/[^A-Z0-9]+/).filter(t => t.length >= 3);
      if (descTokens.length > 0) {
        let bestScore = 0;
        let bestEntry = null;

        for (let entry of this.db.aggregateMaster) {
          const compUpper = String(entry.component || "").toUpperCase();
          const subUpper = String(entry.subAggregate || "").toUpperCase();
          const aggUpper = String(entry.aggregate || "").toUpperCase();

          let score = 0;
          for (let dt of descTokens) {
            if (compUpper.includes(dt)) score += 4;
            else if (subUpper.includes(dt)) score += 2;
            else if (aggUpper.includes(dt)) score += 1;
          }

          if (score > bestScore) {
            bestScore = score;
            bestEntry = entry;
          }
        }

        if (bestEntry && bestScore >= 4) {
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
  }'''

start_idx = code.find('mapRow(rawPartNo')
end_idx = code.find('findColumn(row', start_idx)

if start_idx != -1 and end_idx != -1:
    new_code = code[:start_idx] + new_map_row + '\n\n  ' + code[end_idx:]
    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(new_code)
    print('Updated js/data-engine.js successfully!')
else:
    print('Could not find mapRow in js/data-engine.js', start_idx, end_idx)
