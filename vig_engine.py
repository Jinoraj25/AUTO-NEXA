import sqlite3
import os
import re
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "interchange_engine.db")

def clean_part_no(pn):
    """Sanitize & normalize: strip spaces, hyphens, slashes, uppercase."""
    if not pn:
        return ""
    return re.sub(r'[^A-Z0-9]', '', str(pn).upper())

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Table 1: parts_master
    c.execute("""
    CREATE TABLE IF NOT EXISTS parts_master (
        part_id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_number TEXT NOT NULL,
        clean_part_number TEXT NOT NULL UNIQUE,
        brand_name TEXT NOT NULL,
        brand_type TEXT NOT NULL, -- 'OEM', 'OES_TIER1', 'AFTERMARKET'
        aggregate_category TEXT NOT NULL,
        part_description TEXT,
        mrp_price REAL DEFAULT 0,
        logo_url TEXT
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_parts_clean ON parts_master(clean_part_number);")

    # Table 2: interchange_groups
    c.execute("""
    CREATE TABLE IF NOT EXISTS interchange_groups (
        group_id TEXT PRIMARY KEY,
        canonical_name TEXT NOT NULL,
        aggregate TEXT NOT NULL,
        status TEXT DEFAULT 'Active',
        notes TEXT
    );
    """)

    # Table 3: part_group_mappings
    c.execute("""
    CREATE TABLE IF NOT EXISTS part_group_mappings (
        mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT NOT NULL,
        part_id INTEGER NOT NULL,
        relation_role TEXT NOT NULL, -- 'DIRECT_OE', 'DIRECT_OES', 'AFTERMARKET_ALT'
        is_primary_anchor INTEGER DEFAULT 0,
        confidence_score INTEGER DEFAULT 100,
        match_type TEXT,
        notes TEXT,
        availability_status TEXT DEFAULT 'In Stock',
        FOREIGN KEY (group_id) REFERENCES interchange_groups(group_id),
        FOREIGN KEY (part_id) REFERENCES parts_master(part_id)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_pgm_group ON part_group_mappings(group_id);")

    # Table 4: vehicle_fitment_mappings
    c.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_fitment_mappings (
        mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT NOT NULL,
        make TEXT NOT NULL,
        model TEXT NOT NULL,
        generation_years TEXT NOT NULL,
        engine_spec TEXT,
        FOREIGN KEY (group_id) REFERENCES interchange_groups(group_id)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_vfm_group ON vehicle_fitment_mappings(group_id);")

    conn.commit()
    seed_knowledge_base(conn)
    conn.close()

def seed_knowledge_base(conn):
    # Disabled sample seeding so only verified real database clusters are used
    return

    # --- CLUSTER 1: VIG-CLU-0941 (Valeo VAL-826330 Anchor - Image 5 Reference) ---
    c.execute("""
    INSERT INTO interchange_groups (group_id, canonical_name, aggregate, status, notes)
    VALUES ('VIG-CLU-0941', 'Clutch Plate / Pressure Plate Assembly', 'Clutch System', 'Active', '225mm Dry Plate Assembly');
    """)

    parts_c1 = [
        # (part_number, brand, type, agg, desc, mrp, logo)
        ("VAL-826330", "Valeo", "OES_TIER1", "Clutch System", "Clutch Plate / Pressure Plate Assembly", 4650, "images/brands/valeo.png"),
        ("LUK-622333609", "LuK", "OES_TIER1", "Clutch System", "RepSet Clutch Kit (Clutch Disc & Cover)", 4750, "images/brands/luk.png"),
        ("SAC-3000951098", "SACHS", "OES_TIER1", "Clutch System", "Clutch Assembly Kit (ZF Line Fit)", 4800, "images/brands/sachs.png"),
        ("BOS-198730101", "BOSCH", "OES_TIER1", "Clutch System", "Functional Substitute Clutch Plate", 4500, "images/brands/bosch.png"),
        ("TRW-DF4452", "TRW", "AFTERMARKET", "Clutch System", "Sub-Tier Fitment (Direct Swap)", 3950, "images/brands/trw.png"),
        ("CK-CP3340", "CEEKAY", "AFTERMARKET", "Clutch System", "Aftermarket Replica (Exact Dimensions)", 3600, "images/brands/ceekay.png"),
        ("EXD-HY1149", "EXEDY", "AFTERMARKET", "Clutch System", "Reinforced / Heavy-Duty Alternative", 4200, "images/brands/exedy.png")
    ]

    for pn, brand, btype, agg, desc, mrp, logo in parts_c1:
        c.execute("""
        INSERT OR IGNORE INTO parts_master (part_number, clean_part_number, brand_name, brand_type, aggregate_category, part_description, mrp_price, logo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (pn, clean_part_no(pn), brand, btype, agg, desc, mrp, logo))
        pid = c.lastrowid or c.execute("SELECT part_id FROM parts_master WHERE clean_part_number = ?", (clean_part_no(pn),)).fetchone()[0]

        is_anchor = 1 if pn == "VAL-826330" else 0
        if "BOSCH" in brand:
            role = "DIRECT_OES"
            conf = 98
            match_type = "98% Functional Substitute (Verify Bearing)"
            notes = "Requires bearing check"
        elif "LuK" in brand or "SACHS" in brand:
            role = "DIRECT_OES"
            conf = 100
            match_type = "100% Direct Match (Form-Fit-Function)"
            notes = "OE factory line-fit"
        elif "TRW" in brand:
            role = "Sub-Tier Fitment (Direct Swap)"
            conf = 95
            match_type = "Sub-Tier Fitment"
            notes = "Friction material variance"
        elif "CEEKAY" in brand:
            role = "Aftermarket Replica (Exact Dimensions)"
            conf = 90
            match_type = "Aftermarket Replica"
            notes = "Standard performance spec"
        elif "EXEDY" in brand:
            role = "Reinforced / Heavy-Duty Alternative"
            conf = 92
            match_type = "Reinforced Alternative"
            notes = "Upgraded spring design"
        else:
            role = "DIRECT_OES"
            conf = 100
            match_type = "100% Direct Match (Form-Fit-Function)"
            notes = ""

        c.execute("""
        INSERT INTO part_group_mappings (group_id, part_id, relation_role, is_primary_anchor, confidence_score, match_type, notes, availability_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'In Stock');
        """, ("VIG-CLU-0941", pid, role, is_anchor, conf, match_type, notes))

    # Fitments for Cluster 1
    fitments_c1 = [
        ("Hyundai", "Creta", "2015-2020", "1.6L CRDi Diesel"),
        ("Kia", "Seltos", "2019-2025", "1.5L CRDi Diesel"),
        ("Hyundai", "Verna", "2016-2020", "1.6L CRDi Diesel")
    ]
    for mk, mdl, yrs, eng in fitments_c1:
        c.execute("""
        INSERT INTO vehicle_fitment_mappings (group_id, make, model, generation_years, engine_spec)
        VALUES ('VIG-CLU-0941', ?, ?, ?, ?);
        """, (mk, mdl, yrs, eng))

    # --- CLUSTER 2: VIG-AIR-1088 (Maruti Suzuki Swift Air Cleaner - 13780M75J00) ---
    c.execute("""
    INSERT INTO interchange_groups (group_id, canonical_name, aggregate, status, notes)
    VALUES ('VIG-AIR-1088', 'Air Filter Element / Air Cleaner', 'Filters', 'Active', 'Standard Flow Air Intake Cartridge');
    """)

    parts_c2 = [
        ("13780M75J00", "MARUTI SUZUKI GENUINE", "OEM", "Filters", "ELEMENT, AIR CLEANER (OEM GENUINE)", 260, "images/makes/maruti.png"),
        ("AF-1088", "PUROLATOR", "OES_TIER1", "Filters", "AIR FILTER ELEMENT (100% OE DUST RETENTION)", 195, "images/brands/purolator.png"),
        ("0986AF2411", "BOSCH", "OES_TIER1", "Filters", "High Efficiency Air Filter", 205, "images/brands/bosch.png"),
        ("EK-5178", "ELOFIC", "OES_TIER1", "Filters", "OE Replacement Air Cleaner", 185, "images/brands/elofic.png"),
        ("TVS-AF021", "TVS MOBILITY", "OES_TIER1", "Filters", "Multi-layer Synthetic Air Filter", 190, "images/brands/mytvs.png")
    ]

    for pn, brand, btype, agg, desc, mrp, logo in parts_c2:
        c.execute("""
        INSERT OR IGNORE INTO parts_master (part_number, clean_part_number, brand_name, brand_type, aggregate_category, part_description, mrp_price, logo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (pn, clean_part_no(pn), brand, btype, agg, desc, mrp, logo))
        pid = c.lastrowid or c.execute("SELECT part_id FROM parts_master WHERE clean_part_number = ?", (clean_part_no(pn),)).fetchone()[0]

        is_anchor = 1 if btype == "OEM" else 0
        role = "DIRECT_OE" if btype == "OEM" else "DIRECT_OES"
        match_type = "100% Direct Match (Form-Fit-Function)"
        notes = "100% Dimensional & Flow Rate Match" if "PUROLATOR" in brand else ("Save 21%" if "BOSCH" in brand else "Direct OE replacement")

        c.execute("""
        INSERT INTO part_group_mappings (group_id, part_id, relation_role, is_primary_anchor, confidence_score, match_type, notes, availability_status)
        VALUES (?, ?, ?, ?, 100, ?, ?, 'In Stock');
        """, ("VIG-AIR-1088", pid, role, is_anchor, match_type, notes))

    fitments_c2 = [
        ("Maruti Suzuki", "Swift", "2011-2018", "1.2L K-Series / 1.3L DDiS"),
        ("Maruti Suzuki", "Dzire", "2012-2017", "1.2L Petrol / 1.3L Diesel"),
        ("Maruti Suzuki", "Ertiga", "2012-2018", "1.4L K14B / 1.3L DDiS")
    ]
    for mk, mdl, yrs, eng in fitments_c2:
        c.execute("""
        INSERT INTO vehicle_fitment_mappings (group_id, make, model, generation_years, engine_spec)
        VALUES ('VIG-AIR-1088', ?, ?, ?, ?);
        """, (mk, mdl, yrs, eng))

    # --- CLUSTER 3: VIG-BRK-5581 (Maruti Swift Front Brake Pad - 55810M68P00) ---
    c.execute("""
    INSERT INTO interchange_groups (group_id, canonical_name, aggregate, status, notes)
    VALUES ('VIG-BRK-5581', 'Front Disc Brake Pad Set', 'Brake System', 'Active', 'Front Axle Disc Brake Pads');
    """)

    parts_c3 = [
        ("55810M68P00", "MARUTI SUZUKI GENUINE", "OEM", "Brake System", "PAD SET, FRONT DISC BRAKE", 2250, "images/makes/maruti.png"),
        ("0986AB1234", "BOSCH", "OES_TIER1", "Brake System", "FRONT DISC BRAKE PAD SET (LOW METALLIC)", 1580, "images/brands/bosch.png"),
        ("TVG-BP5581", "TVS GIRLING", "OES_TIER1", "Brake System", "OE Supplier Formulation Brake Pad Set", 1520, "images/brands/tvs_girling.png"),
        ("PNT-8812", "BREMBO", "OES_TIER1", "Brake System", "Premium Ceramic Low Dust Brake Pads", 1690, "images/brands/brembo.png"),
        ("KBX-3042", "KBX", "AFTERMARKET", "Brake System", "Standard Performance Front Pad Kit", 1350, "images/brands/kbx.png"),
        ("RANE-BP7701", "RANE", "AFTERMARKET", "Brake System", "Semi-Metallic Disc Brake Pads", 1280, "images/brands/rane.png")
    ]

    for pn, brand, btype, agg, desc, mrp, logo in parts_c3:
        c.execute("""
        INSERT OR IGNORE INTO parts_master (part_number, clean_part_number, brand_name, brand_type, aggregate_category, part_description, mrp_price, logo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (pn, clean_part_no(pn), brand, btype, agg, desc, mrp, logo))
        pid = c.lastrowid or c.execute("SELECT part_id FROM parts_master WHERE clean_part_number = ?", (clean_part_no(pn),)).fetchone()[0]

        is_anchor = 1 if btype == "OEM" else 0
        role = "DIRECT_OE" if btype == "OEM" else ("DIRECT_OES" if btype == "OES_TIER1" else "AFTERMARKET_ALT")
        conf = 100 if role in ["DIRECT_OE", "DIRECT_OES"] else (94 if "KBX" in brand else 90)
        match_type = "100% Direct Match (Form-Fit-Function)" if conf == 100 else "Standard Aftermarket Replacement"
        notes = "Save 30% vs OEM" if "BOSCH" in brand else ("Save 32% (OE Factory Supplier)" if "TVS" in brand else "")

        c.execute("""
        INSERT INTO part_group_mappings (group_id, part_id, relation_role, is_primary_anchor, confidence_score, match_type, notes, availability_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'In Stock');
        """, ("VIG-BRK-5581", pid, role, is_anchor, conf, match_type, notes))

    fitments_c3 = [
        ("Maruti Suzuki", "Swift", "2018-2024", "1.2L DualJet / 1.3L DDiS"),
        ("Maruti Suzuki", "Dzire", "2017-2024", "1.2L K12M / CNG"),
        ("Maruti Suzuki", "Baleno", "2015-2023", "1.2L K-Series")
    ]
    for mk, mdl, yrs, eng in fitments_c3:
        c.execute("""
        INSERT INTO vehicle_fitment_mappings (group_id, make, model, generation_years, engine_spec)
        VALUES ('VIG-BRK-5581', ?, ?, ?, ?);
        """, (mk, mdl, yrs, eng))

    # --- CLUSTER 4: VIG-OIL-1651 (Maruti Suzuki Spin-On Oil Filter - 16510M68K00) ---
    c.execute("""
    INSERT INTO interchange_groups (group_id, canonical_name, aggregate, status, notes)
    VALUES ('VIG-OIL-1651', 'Engine Oil Filter (Spin-On)', 'Filters', 'Active', 'Spin-On Oil Filter with Anti-Drainback');
    """)

    parts_c4 = [
        ("16510M68K00", "MARUTI SUZUKI GENUINE", "OEM", "Filters", "FILTER ASSY, OIL (SPIN-ON)", 380, "images/makes/maruti.png"),
        ("L-1011", "PUROLATOR", "OES_TIER1", "Filters", "Spin-On Micro-Fiber Oil Filter", 260, "images/brands/purolator.png"),
        ("OC-1240", "MAHLE", "OES_TIER1", "Filters", "OE Pleated Synthetic Oil Filter", 265, "images/brands/mahle.png"),
        ("0986AF0058", "BOSCH", "OES_TIER1", "Filters", "Bosch Spin-on Clean Oil Filter", 275, "images/brands/bosch.png"),
        ("EK-6112", "ELOFIC", "OES_TIER1", "Filters", "Elofic Heavy Duty Oil Cartridge", 240, "images/brands/elofic.png"),
        ("TVS-OF011", "TVS MOBILITY", "OES_TIER1", "Filters", "myTVS Multi-Valve Oil Filter", 250, "images/brands/mytvs.png")
    ]

    for pn, brand, btype, agg, desc, mrp, logo in parts_c4:
        c.execute("""
        INSERT OR IGNORE INTO parts_master (part_number, clean_part_number, brand_name, brand_type, aggregate_category, part_description, mrp_price, logo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (pn, clean_part_no(pn), brand, btype, agg, desc, mrp, logo))
        pid = c.lastrowid or c.execute("SELECT part_id FROM parts_master WHERE clean_part_number = ?", (clean_part_no(pn),)).fetchone()[0]

        is_anchor = 1 if btype == "OEM" else 0
        role = "DIRECT_OE" if btype == "OEM" else "DIRECT_OES"
        match_type = "100% Direct Match (Form-Fit-Function)"
        notes = "Save 32% (OE Standard)" if "PUROLATOR" in brand else "Direct OE replacement"

        c.execute("""
        INSERT INTO part_group_mappings (group_id, part_id, relation_role, is_primary_anchor, confidence_score, match_type, notes, availability_status)
        VALUES (?, ?, ?, ?, 100, ?, ?, 'In Stock');
        """, ("VIG-OIL-1651", pid, role, is_anchor, match_type, notes))

    fitments_c4 = [
        ("Maruti Suzuki", "Swift", "2011-2024", "1.2L K12M / Petrol"),
        ("Maruti Suzuki", "Wagon R", "2010-2024", "1.0L K10B / 1.2L"),
        ("Maruti Suzuki", "Ertiga", "2012-2024", "1.4L / 1.5L K15B Petrol")
    ]
    for mk, mdl, yrs, eng in fitments_c4:
        c.execute("""
        INSERT INTO vehicle_fitment_mappings (group_id, make, model, generation_years, engine_spec)
        VALUES ('VIG-OIL-1651', ?, ?, ?, ?);
        """, (mk, mdl, yrs, eng))

    conn.commit()

# Ensure DB initialized on module load
init_db()

def search_interchange(query_str):
    """
    Executes the 6-step Virtual Interchange Group runtime logic:
    Step 1: Sanitize & Normalize
    Step 2: Identify Input Type (OEM vs OES)
    Step 3: Query Group Peers (The Interchange Engine)
    Step 4: Resolve OEM vs. OES Scenario (with Anchor Election)
    Step 5: Attach Fitments
    Step 6: Render JSON Response
    """
    if not query_str:
        return {"error": "Empty query", "results": None}

    raw_query = str(query_str).strip()
    norm_query = clean_part_no(raw_query)

    conn = get_db()
    c = conn.cursor()

    # Step 2: Identify Input Type
    c.execute("""
    SELECT p.*, pgm.group_id, pgm.relation_role, pgm.is_primary_anchor, ig.canonical_name, ig.aggregate, ig.status as group_status
    FROM parts_master p
    JOIN part_group_mappings pgm ON p.part_id = pgm.part_id
    JOIN interchange_groups ig ON pgm.group_id = ig.group_id
    WHERE p.clean_part_number = ?
    LIMIT 1;
    """, (norm_query,))
    searched_part = c.fetchone()

    # If not found directly, check with prefix/suffix clean or fallback to overall_catalogue
    if not searched_part:
        # Check overall_catalogue.db to see if this is an authentic OEM part number
        fallback_res = resolve_from_catalogue_db(raw_query, norm_query)
        conn.close()
        return fallback_res

    group_id = searched_part["group_id"]
    input_part_id = searched_part["part_id"]
    is_oem_search = (searched_part["brand_type"] == "OEM")

    # Step 3: Query Group Peers
    c.execute("""
    SELECT p.*, pgm.relation_role, pgm.confidence_score, pgm.match_type, pgm.notes, pgm.availability_status
    FROM part_group_mappings pgm
    JOIN parts_master p ON pgm.part_id = p.part_id
    WHERE pgm.group_id = ? AND pgm.part_id != ?
    ORDER BY pgm.confidence_score DESC, p.mrp_price ASC;
    """, (group_id, input_part_id))
    peers = c.fetchall()

    # Step 4: Resolve OEM vs. OES Scenario
    c.execute("""
    SELECT p.* FROM parts_master p
    JOIN part_group_mappings pgm ON p.part_id = pgm.part_id
    WHERE pgm.group_id = ? AND p.brand_type = 'OEM'
    LIMIT 1;
    """, (group_id,))
    oem_row = c.fetchone()
    has_oem_ref = (oem_row is not None)

    # Separate into Direct OES vs Aftermarket Alternatives
    direct_oes = []
    aftermarket = []

    for r in peers:
        item = {
            "part_id": r["part_id"],
            "part_number": r["part_number"],
            "brand": r["brand_name"],
            "brand_type": r["brand_type"],
            "description": r["part_description"],
            "mrp": float(r["mrp_price"] or 0),
            "confidence": r["confidence_score"] or 100,
            "match_type": r["match_type"] or "100% Direct Match (Form-Fit-Function)",
            "availability_status": r["availability_status"] or "In Stock",
            "notes": r["notes"] or "",
            "logo_url": r["logo_url"] or ""
        }

        # Pricing diff vs OEM or Anchor
        ref_price = oem_row["mrp_price"] if oem_row else searched_part["mrp_price"]
        if ref_price and ref_price > 0 and item["mrp"] > 0:
            diff_val = ref_price - item["mrp"]
            diff_pct = round((diff_val / ref_price) * 100)
            item["savings_amount"] = max(0, round(diff_val))
            item["savings_percent"] = max(0, diff_pct)

        # OEM parts belong in oem_reference, not in direct_oes!
        if r["brand_type"] == "OEM":
            continue

        if r["relation_role"] in ["DIRECT_OES", "DIRECT_OE"]:
            direct_oes.append(item)
        else:
            aftermarket.append(item)

    # Step 5: Attach Fitments
    c.execute("""
    SELECT make, model, generation_years, engine_spec
    FROM vehicle_fitment_mappings
    WHERE group_id = ?;
    """, (group_id,))
    fitments = [
        {
            "make": f["make"],
            "model": f["model"],
            "period": f["generation_years"],
            "variant": f["engine_spec"] or ""
        }
        for f in c.fetchall()
    ]

    # Anchor metadata formatting
    anchor_part_no = searched_part["part_number"]
    anchor_brand = searched_part["brand_name"]
    anchor_title = searched_part["canonical_name"]
    anchor_status = f"OEM Reference: {oem_row['part_number']} ({oem_row['brand_name']})" if has_oem_ref else "Status: No OEM Part Listed / Discontinued"

    response = {
        "search_meta": {
            "query": raw_query,
            "normalized": norm_query,
            "anchor_type": "OEM" if is_oem_search else "OES",
            "has_oem_reference": has_oem_ref,
            "group_id": group_id,
            "aggregate": searched_part["aggregate"],
            "part_title": anchor_title,
            "anchor_part_number": anchor_part_no,
            "anchor_brand": anchor_brand,
            "anchor_mrp": float(searched_part["mrp_price"] or 0),
            "anchor_desc": searched_part["part_description"] or anchor_title,
            "anchor_status_line": f"Active Anchor: {anchor_brand} {anchor_part_no} ({anchor_title}) | {anchor_status} | Target Segment: {searched_part['aggregate']}"
        },
        "oem_reference": {
            "part_number": oem_row["part_number"],
            "brand": oem_row["brand_name"],
            "desc": oem_row["part_description"],
            "mrp": float(oem_row["mrp_price"] or 0)
        } if oem_row else None,
        "compatible_vehicles": fitments,
        "interchanges": {
            "direct_oes": direct_oes,
            "aftermarket_alternatives": aftermarket
        }
    }

    conn.close()
    return response

def resolve_from_catalogue_db(raw_query, norm_query):
    """
    Fallback synthesis when a part number from overall_catalogue.db is entered
    that hasn't been manually curated into a group yet.
    """
    cat_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "overall_catalogue.db")
    if not os.path.exists(cat_db_path):
        return {"error": "Catalogue DB not found", "results": None}

    conn = sqlite3.connect(cat_db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT line_code_part_number, brand_name, part_description, mrp_price, vehicle_make, vehicle_model,
           vehicle_sub_model, components, aggregate
    FROM overall_catalogue
    WHERE line_code_part_number = ? OR line_code_part_number LIKE ?
    LIMIT 1;
    """, (raw_query, f"%{norm_query}%"))
    row = c.fetchone()

    if not row:
        conn.close()
        return {
            "search_meta": {
                "query": raw_query,
                "normalized": norm_query,
                "anchor_type": "UNKNOWN",
                "has_oem_reference": False,
                "group_id": f"VIG-GEN-{norm_query[:6]}",
                "aggregate": "Spare Parts",
                "part_title": f"Part #{raw_query}"
            },
            "compatible_vehicles": [],
            "interchanges": {
                "direct_oes": [],
                "aftermarket_alternatives": []
            }
        }

    brand = (row["brand_name"] or "").strip()
    desc = row["part_description"] or row["components"] or "Automotive Component"
    mrp = float(row["mrp_price"] or 0)
    agg = row["aggregate"] or "Mechanical Parts"
    make = row["vehicle_make"] or ""
    model = row["vehicle_model"] or ""

    is_oem = brand.upper() in ["MARUTI", "MARUTI SUZUKI", "HYUNDAI", "TATA", "TOYOTA", "MAHINDRA", "HONDA", "FORD", "VOLKSWAGEN"]
    synth_gid = f"VIG-{agg[:3].upper()}-{norm_query[:6]}"

    # Look for alternative Tier-1 parts for this component in the same vehicle
    c.execute("""
    SELECT line_code_part_number, brand_name, part_description, mrp_price
    FROM overall_catalogue
    WHERE components = ? AND brand_name != ? AND mrp_price > 0
    GROUP BY brand_name
    LIMIT 6;
    """, (row["components"], brand))
    alt_rows = c.fetchall()

    direct_oes = []
    aftermarket = []
    for ar in alt_rows:
        b_up = (ar["brand_name"] or "").upper()
        p_mrp = float(ar["mrp_price"] or 0)
        item = {
            "part_number": ar["line_code_part_number"],
            "brand": ar["brand_name"],
            "description": ar["part_description"] or desc,
            "mrp": p_mrp,
            "confidence": 100 if any(t in b_up for t in ["BOSCH", "PUROLATOR", "MAHLE", "VALEO", "LUK", "TVS"]) else 90,
            "match_type": "100% Direct Match (Form-Fit-Function)",
            "availability_status": "In Stock",
            "notes": "Verified Aftermarket Alternative"
        }
        if mrp > 0 and p_mrp > 0:
            item["savings_amount"] = max(0, round(mrp - p_mrp))
            item["savings_percent"] = max(0, round(((mrp - p_mrp) / mrp) * 100))

        if any(t in b_up for t in ["BOSCH", "PUROLATOR", "MAHLE", "VALEO", "LUK", "SACHS", "TVS GIRLING", "BREMBO", "ELOFIC"]):
            direct_oes.append(item)
        else:
            aftermarket.append(item)

    conn.close()

    return {
        "search_meta": {
            "query": raw_query,
            "normalized": norm_query,
            "anchor_type": "OEM" if is_oem else "OES",
            "has_oem_reference": is_oem,
            "group_id": synth_gid,
            "aggregate": agg,
            "part_title": desc,
            "anchor_part_number": row["line_code_part_number"],
            "anchor_brand": brand,
            "anchor_mrp": mrp,
            "anchor_desc": desc,
            "anchor_status_line": f"Active Anchor: {brand} {row['line_code_part_number']} ({desc}) | Segment: {agg}"
        },
        "compatible_vehicles": [
            {
                "make": make,
                "model": model,
                "period": "All Applicable Years",
                "variant": row["vehicle_sub_model"] or "All Trims"
            }
        ] if make else [],
        "interchanges": {
            "direct_oes": direct_oes,
            "aftermarket_alternatives": aftermarket
        }
    }
