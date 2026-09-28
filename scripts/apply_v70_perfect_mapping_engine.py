import re, os

print("=== Embedding v70 Perfect Mapping Engine into js/data-engine.js & js/mapping-portal.js ===")

# 1. Read js/data-engine.js
data_engine_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js"
with open(data_engine_path, "r", encoding="utf-8") as f:
    de_code = f.read()

# Replace mapRow implementation in js/data-engine.js
new_map_row_code = r"""  mapRow(rawPartNo, description, brandInput = "") {
    const normPart = this.cleanPartNo(rawPartNo);
    const descUpper = String(description || "").trim().toUpperCase();
    const brandUpper = String(brandInput || "").trim().toUpperCase();
    const cleanDesc = descUpper.replace(/^[^\w]+/, '').strip ? descUpper.replace(/^[^\w]+/, '').trim() : descUpper.replace(/^[^\w]+/, '');

    const findInMaster = (compName) => {
      if (!compName || !this.db || !this.db.aggregateMaster) return null;
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

    // Strategy 2: High-Precision Domain Keyword Engine
    if (cleanDesc) {
      const d = cleanDesc;
      const DOMAIN_KEYWORDS = [
        ['BRAKE SHOE', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE SHOE'],
        ['DRUM BRAKE', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE SHOE'],
        ['BRAKE PAD', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD'],
        ['DISC PAD', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD'],
        ['BRAKE DISC', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE DISC / ROTOR'],
        ['BRAKE ROTOR', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE DISC / ROTOR'],
        ['BRAKE DRUM', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE DRUM'],
        ['BRAKE HOSE', 'BRAKE SYSTEM', 'HYDRAULIC LINES', 'BRAKE HOSE'],
        ['BRAKE PIPE', 'BRAKE SYSTEM', 'HYDRAULIC LINES', 'BRAKE PIPE LINE'],
        ['BRAKE LINING', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE LINING'],
        ['BRAKE', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD'],

        ['OIL FILTER', 'ENGINE', 'FILTERS', 'OIL FILTER'],
        ['AIR FILTER', 'ENGINE', 'FILTERS', 'AIR FILTER'],
        ['FUEL FILTER', 'ENGINE', 'FILTERS', 'FUEL FILTER'],
        ['CABIN FILTER', 'HVAC/THERMAL', 'FILTERS', 'CABIN AIR FILTER'],
        ['FILTER', 'ENGINE', 'FILTERS', 'OIL FILTER'],
        ['PISTON', 'ENGINE', 'BLOCK & HEAD', 'PISTON & RINGS'],
        ['CYLINDER HEAD', 'ENGINE', 'BLOCK & HEAD', 'CYLINDER HEAD'],
        ['VALVE', 'ENGINE', 'VALVE TRAIN', 'ENGINE VALVE'],
        ['CRANKSHAFT', 'ENGINE', 'BLOCK & HEAD', 'CRANKSHAFT'],
        ['CAMSHAFT', 'ENGINE', 'VALVE TRAIN', 'CAMSHAFT'],
        ['TURBOCHARGER', 'ENGINE', 'AIR INTAKE', 'TURBOCHARGER'],
        ['TURBO', 'ENGINE', 'AIR INTAKE', 'TURBOCHARGER'],
        ['SPARK PLUG', 'ELECTRICALS AND ELECTRONICS', 'IGNITION SYSTEM', 'SPARK PLUG'],
        ['GLOW PLUG', 'ELECTRICALS AND ELECTRONICS', 'IGNITION SYSTEM', 'GLOW PLUG'],

        ['BUMPER', 'BODY PARTS', 'BODY TRIM', 'BUMPER TRIM'],
        ['GRILLE', 'BODY PARTS', 'BODY TRIM', 'FRONT GRILLE'],
        ['GRIL', 'BODY PARTS', 'BODY TRIM', 'FRONT GRILLE'],
        ['FENDER', 'BODY PARTS', 'PANELS', 'FENDER PANEL'],
        ['BONNET', 'BODY PARTS', 'PANELS', 'HOOD / BONNET'],
        ['HOOD', 'BODY PARTS', 'PANELS', 'HOOD / BONNET'],
        ['DOOR', 'BODY PARTS', 'PANELS', 'DOOR PANEL'],
        ['MIRROR', 'BODY PARTS', 'MIRRORS', 'REAR VIEW MIRROR'],
        ['REAR VIEW', 'BODY PARTS', 'MIRRORS', 'REAR VIEW MIRROR'],
        ['WINDSHIELD', 'GLASS', 'WINDSHIELD', 'FRONT WINDSHIELD GLASS'],
        ['GLASS', 'GLASS', 'WINDSHIELD', 'DOOR GLASS'],
        ['HANDLE', 'BODY PARTS', 'DOOR HARDWARE', 'DOOR HANDLE'],
        ['LOCK', 'BODY PARTS', 'LOCKS', 'DOOR LOCK ASSY'],
        ['LATCH', 'BODY PARTS', 'LOCKS', 'HOOD LATCH'],
        ['BRACKET', 'BODY PARTS', 'BODY TRIM', 'MOUNTING BRACKET'],
        ['BRACE', 'BODY PARTS', 'BODY TRIM', 'MOUNTING BRACKET'],
        ['HOLDER', 'BODY PARTS', 'BODY TRIM', 'MOUNTING BRACKET'],
        ['STAY', 'BODY PARTS', 'BODY TRIM', 'HOOD STAY / ROD'],
        ['GRIP', 'BODY PARTS', 'INTERIOR TRIM', 'GRIP HANDLE'],
        ['PANEL', 'BODY PARTS', 'PANELS', 'BODY PANEL'],
        ['COWL', 'BODY PARTS', 'PANELS', 'COWL PANEL'],
        ['EMBLEM', 'BODY PARTS', 'EMBLEMS', 'CAR EMBLEM / MONOGRAM'],

        ['HEAD LAMP', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'],
        ['HEADLIGHT', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'],
        ['TAIL LAMP', 'LIGHTING', 'TAILLAMP', 'TAIL LAMP ASSEMBLY'],
        ['TAILLIGHT', 'LIGHTING', 'TAILLAMP', 'TAIL LAMP ASSEMBLY'],
        ['FOG LAMP', 'LIGHTING', 'FOGLAMP', 'FOG LAMP / LIGHT ASSEMBLY'],
        ['FOG LIGHT', 'LIGHTING', 'FOGLAMP', 'FOG LAMP / LIGHT ASSEMBLY'],
        ['INDICATOR', 'LIGHTING', 'SIGNAL LAMP', 'SIDE INDICATOR LAMP'],
        ['BULB', 'LIGHTING', 'BULBS', 'HEADLAMP BULB'],
        ['LAMP', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'],
        ['LIGHT', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'],

        ['SHOCK ABSORBER', 'SUSPENSION', 'SHOCK ABSORBER', 'FRONT SHOCK ABSORBER'],
        ['STRUT', 'SUSPENSION', 'STRUT ASSEMBLY', 'FRONT STRUT ASSEMBLY'],
        ['LEAF SPRING', 'SUSPENSION', 'SPRINGS', 'LEAF SPRING ASSEMBLY'],
        ['COIL SPRING', 'SUSPENSION', 'SPRINGS', 'COIL SPRING'],
        ['BALL JOINT', 'SUSPENSION', 'LINKAGE', 'SUSPENSION BALL JOINT'],
        ['ARM CONTROL', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'],
        ['CONTROL ARM', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'],
        ['LOWER ARM', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'],
        ['UPPER ARM', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'],
        ['BUSH', 'SUSPENSION', 'BUSHINGS', 'SUSPENSION BUSH'],
        ['BUSHING', 'SUSPENSION', 'BUSHINGS', 'SUSPENSION BUSH'],
        ['STABILIZER', 'SUSPENSION', 'LINKAGE', 'STABILIZER BAR LINK'],
        ['HUB', 'SUSPENSION', 'WHEEL HUB', 'WHEEL HUB ASSEMBLY'],
        ['BEARING', 'BEARING', 'WHEEL BEARING', 'WHEEL BEARING'],
        ['STEERING RACK', 'STEERING', 'POWER STEERING', 'STEERING RACK & BOOT'],
        ['STEERING GEAR', 'STEERING', 'GEARBOX', 'STEERING GEARBOX'],
        ['STEERING BOOT', 'STEERING', 'STEERING LINKAGE', 'STEERING BOOT'],
        ['STEERING', 'STEERING', 'STEERING LINKAGE', 'STEERING TIE ROD END'],

        ['CLUTCH DISC', 'CLUTCH SYSTEM', 'CLUTCH DISC', 'CLUTCH DISC & PLATE'],
        ['CLUTCH PLATE', 'CLUTCH SYSTEM', 'CLUTCH DISC', 'CLUTCH DISC & PLATE'],
        ['CLUTCH COVER', 'CLUTCH SYSTEM', 'CLUTCH COVER', 'CLUTCH COVER / PRESSURE PLATE'],
        ['PRESSURE PLATE', 'CLUTCH SYSTEM', 'CLUTCH COVER', 'CLUTCH COVER / PRESSURE PLATE'],
        ['CLUTCH KIT', 'CLUTCH SYSTEM', 'CLUTCH KIT', 'CLUTCH KIT COMPLETE'],
        ['CLUTCH CABLE', 'CLUTCH SYSTEM', 'CONTROLS', 'CLUTCH CABLE'],
        ['CLUTCH', 'CLUTCH SYSTEM', 'CLUTCH ASSEMBLY', 'CLUTCH DISC & PLATE'],
        ['GEARBOX', 'TRANSMISSION', 'GEARBOX', 'TRANSMISSION GEARBOX'],
        ['GEAR SHIFT', 'TRANSMISSION', 'CONTROLS', 'GEAR SHIFT LEVER KIT'],
        ['GEAR LEVER', 'TRANSMISSION', 'CONTROLS', 'GEAR SHIFT LEVER KIT'],
        ['GEAR', 'TRANSMISSION', 'GEARS', 'TRANSMISSION GEAR'],
        ['FLYWHEEL', 'TRANSMISSION', 'FLYWHEEL', 'FLYWHEEL ASSEMBLY'],
        ['UNIVERSAL JOINT', 'TRANSMISSION', 'PROPELLER SHAFT', 'UNIVERSAL JOINT KIT'],
        ['U JOINT', 'TRANSMISSION', 'PROPELLER SHAFT', 'UNIVERSAL JOINT KIT'],
        ['PROPELLER SHAFT', 'TRANSMISSION', 'PROPELLER SHAFT', 'PROPELLER SHAFT ASSY'],
        ['AXLE', 'TRANSMISSION', 'AXLE SHAFT', 'REAR AXLE SHAFT'],

        ['RADIATOR', 'COOLING SYSTEM', 'RADIATOR & FLUIDS', 'RADIATOR ASSEMBLY'],
        ['COOLANT', 'COOLING SYSTEM', 'RADIATOR & FLUIDS', 'ENGINE COOLANT'],
        ['WATER PUMP', 'COOLING SYSTEM', 'WATER PUMP', 'WATER PUMP ASSEMBLY'],
        ['THERMOSTAT', 'COOLING SYSTEM', 'THERMOSTAT', 'THERMOSTAT VALVE'],
        ['HOSE', 'RUBBERS HOSES AND MOUNTINGS', 'HOSES', 'COOLANT & HEATER HOSE'],
        ['PIPE', 'COOLING SYSTEM', 'PIPES', 'COOLANT PIPE'],

        ['COMPRESSOR', 'HVAC/THERMAL', 'COMPRESSOR', 'AC COMPRESSOR'],
        ['CONDENSER', 'HVAC/THERMAL', 'CONDENSER', 'AC CONDENSER'],
        ['EVAPORATOR', 'HVAC/THERMAL', 'EVAPORATOR', 'AC EVAPORATOR CORE'],
        ['BLOWER', 'HVAC/THERMAL', 'BLOWER MOTOR', 'AC BLOWER MOTOR'],
        ['EXPANSION VALVE', 'HVAC/THERMAL', 'VALVE', 'AC EXPANSION VALVE'],

        ['ALTERNATOR', 'ELECTRICALS AND ELECTRONICS', 'ROTATING MACHINE', 'ALTERNATOR ASSEMBLY'],
        ['STARTER MOTOR', 'ELECTRICALS AND ELECTRONICS', 'ROTATING MACHINE', 'STARTER MOTOR ASSEMBLY'],
        ['STARTER', 'ELECTRICALS AND ELECTRONICS', 'ROTATING MACHINE', 'STARTER MOTOR ASSEMBLY'],
        ['BATTERY', 'ELECTRICALS AND ELECTRONICS', 'BATTERY', 'CAR BATTERY'],
        ['SENSOR', 'ELECTRICALS AND ELECTRONICS', 'SENSORS', 'ENGINE SENSOR'],
        ['SWITCH', 'ELECTRICALS AND ELECTRONICS', 'SWITCHES', 'ELECTRICAL SWITCH'],
        ['RELAY', 'ELECTRICALS AND ELECTRONICS', 'RELAY AND FUSE', 'RELAY'],
        ['FUSE', 'ELECTRICALS AND ELECTRONICS', 'RELAY AND FUSE', 'FUSE'],
        ['HORN', 'ELECTRICALS AND ELECTRONICS', 'HORN', 'ELECTRIC HORN'],
        ['IGNITION COIL', 'ELECTRICALS AND ELECTRONICS', 'IGNITION SYSTEM', 'IGNITION COIL'],

        ['WIPER BLADE', 'WIPER SYSTEM', 'WIPER BLADE', 'WIPER BLADE'],
        ['WIPER ARM', 'WIPER SYSTEM', 'WIPER ARM', 'WIPER ARM'],
        ['WIPER MOTOR', 'WIPER SYSTEM', 'WIPER MOTOR', 'WIPER MOTOR'],
        ['WIPER', 'WIPER SYSTEM', 'WIPER BLADE', 'WIPER BLADE'],

        ['TIMING BELT', 'BELTS AND TENSIONER', 'TIMING BELT', 'TIMING BELT'],
        ['FAN BELT', 'BELTS AND TENSIONER', 'BELT', 'FAN BELT / V-BELT'],
        ['V BELT', 'BELTS AND TENSIONER', 'BELT', 'FAN BELT / V-BELT'],
        ['BELT', 'BELTS AND TENSIONER', 'BELT', 'SERPENTINE / DRIVE BELT'],
        ['TENSIONER', 'BELTS AND TENSIONER', 'TENSIONER', 'BELT TENSIONER PULLEY'],
        ['PULLEY', 'BELTS AND TENSIONER', 'PULLEY', 'ENGINE PULLEY'],

        ['OIL SEAL', 'CHILD PARTS', 'SEALS & GASKETS', 'OIL SEAL'],
        ['GASKET', 'CHILD PARTS', 'SEALS & GASKETS', 'GASKET & SEALANT'],
        ['O-RING', 'CHILD PARTS', 'SEALS & GASKETS', 'O-RING SEAL'],
        ['ANABOND', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'GASKET & SEALANT'],
        ['SEALANT', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'GASKET & SEALANT'],
        ['GREASE', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'BEARING GREASE'],
        ['OIL', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'ENGINE OIL'],
        ['FLUID', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'BRAKE FLUID'],
        ['BOLT', 'CHILD PARTS', 'BOLT & NUT', 'BOLT'],
        ['NUT', 'CHILD PARTS', 'BOLT & NUT', 'NUT'],
        ['WASHER', 'CHILD PARTS', 'BOLT & NUT', 'WASHER'],
        ['SCREW', 'CHILD PARTS', 'BOLT & NUT', 'SCREW'],
        ['FASTENER', 'CHILD PARTS', 'BOLT & NUT', 'HARDWARE & FASTENERS'],
        ['STUD', 'CHILD PARTS', 'BOLT & NUT', 'STUD']
      ];

      for (let rule of DOMAIN_KEYWORDS) {
        if (d.includes(rule[0])) {
          return {
            aggregate: rule[1],
            subAggregate: rule[2],
            component: rule[3],
            category: "Mechanical Parts",
            make: brandUpper || "GENERIC",
            matchMethod: "DOMAIN_KEYWORD_MATCH",
            confidence: "HIGH",
            confidenceScore: 95,
            remarks: "Auto Mapped (Domain Rule)"
          };
        }
      }
    }

    // Strategy 3: Keyword Token Index Match (excluding stop words)
    const STOP_WORDS = new Set(['LH', 'RH', 'SET', 'KIT', 'FOR', 'AND', 'WITH', 'TYPE', 'STD', 'ASSY', 'NO', 'OFF', 'PCS', 'BLK', 'RED', 'BLUE', 'TYPE1', 'TYPE2', 'ECO', 'NEW', 'OLD', 'GENUINE', 'OEN', 'OEM', 'CAR', 'BLACK', 'WHITE', 'SIDE', 'FRONT', 'REAR', 'INNER', 'OUTER', 'TOP', 'BOTTOM', 'UPPER', 'LOWER']);

    if (cleanDesc) {
      const tokens = cleanDesc.split(/[^A-Z0-9]+/).filter(t => t.length >= 3 && !STOP_WORDS.has(t));
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

    # Strategy 4: Smart General Spares Fallback (NO MORE BLIND BOLT FORCING!)
    return {
      aggregate: "GENERAL SPARES",
      subAggregate: "GENERAL",
      component: "GENERAL SPARES",
      category: "Mechanical Parts",
      make: brandUpper || "GENERIC",
      matchMethod: "SMART_FALLBACK",
      confidence: "MEDIUM",
      confidenceScore: 65,
      remarks: "Auto Mapped (General Spare)"
    };
  },"""

# Replace mapRow in js/data-engine.js
maprow_start = de_code.find("mapRow(rawPartNo, description, brandInput = \"\") {")
if maprow_start != -1:
    maprow_end = de_code.find("inspectColumnsByContent(rawRows) {", maprow_start)
    if maprow_end != -1:
        de_code = de_code[:maprow_start] + new_map_row_code[2:] + "\n\n  " + de_code[maprow_end:]
        print("Successfully replaced mapRow in js/data-engine.js")

with open(data_engine_path, "w", encoding="utf-8") as f:
    f.write(de_code)

# 2. Also update applyInlineDomainRules in js/mapping-portal.js to delegate cleanly
mapping_portal_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\mapping-portal.js"
with open(mapping_portal_path, "r", encoding="utf-8") as f:
    mp_code = f.read()

new_inline_rules = """  applyInlineDomainRules(rawPartNo, description, brandInput = "") {
    if (window.DataEngine && typeof window.DataEngine.mapRow === 'function') {
      return window.DataEngine.mapRow(rawPartNo, description, brandInput);
    }
    return {
      aggregate: "GENERAL SPARES",
      subAggregate: "GENERAL",
      component: "GENERAL SPARES",
      category: "Mechanical Parts",
      make: String(brandInput || "GENERIC").trim().toUpperCase(),
      confidence: "MEDIUM",
      confidenceScore: 65,
      remarks: "Auto Mapped (General Spare)"
    };
  },"""

inline_start = mp_code.find("applyInlineDomainRules(rawPartNo, description, brandInput = \"\") {")
if inline_start != -1:
    inline_end = mp_code.find("exportMappedExcel() {", inline_start)
    if inline_end != -1:
        mp_code = mp_code[:inline_start] + new_inline_rules[2:] + "\n\n  " + mp_code[inline_end:]
        print("Successfully updated applyInlineDomainRules in js/mapping-portal.js")

with open(mapping_portal_path, "w", encoding="utf-8") as f:
    f.write(mp_code)

print("Done embedding v70 Perfect Mapping Engine!")
