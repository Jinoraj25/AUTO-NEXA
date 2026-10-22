"""
AutoNexa Catalog AI Conversational Chatbot Engine
==================================================
Empowers automotive professionals, retail counter staff, and vehicle owners (including uneducated mechanics)
to converse naturally in English, Hindi/Hinglish, slang/colloquialisms, or part numbers to diagnose,
filter by Fuel/Year, inspect Visual 3D Oriparts vehicle models, and discover OEM/OES parts with companion recommendations.
"""

import os
import re
import json
import sqlite3
import difflib

# Relatable / Companion Parts Knowledge Base
RELATABLE_COMPONENTS_MAP = {
    "BRAKE PAD": [
        {"component": "BRAKE DISC - FRONT", "label": "Front Brake Discs / Rotors", "icon": "💿", "why": "Inspect for surface grooves, minimum wear thickness & scoring during pad renewal"},
        {"component": "BRAKE FLUID", "label": "Brake Fluid DOT 4", "icon": "🧪", "why": "Recommended system flush & bleed during friction material change"},
        {"component": "BRAKE CALIPER - FRONT", "label": "Caliper Guide Pins & Hardware", "icon": "🔧", "why": "Lubricate sliding pins to avoid uneven pad taper wear & brake drag"},
        {"component": "BRAKE SHOE", "label": "Rear Brake Shoes / Drums", "icon": "🛑", "why": "Inspect rear axle braking friction simultaneously"}
    ],
    "BRAKE DISC": [
        {"component": "BRAKE PAD - FRONT", "label": "Front Brake Pads", "icon": "🛑", "why": "Always mate new rotors with brand-new pads to avoid premature grooving"},
        {"component": "BRAKE FLUID", "label": "Brake Fluid DOT 4", "icon": "🧪", "why": "Hydraulic brake bleeding mandatory after rotor replacement"},
        {"component": "WHEEL BEARING", "label": "Front Wheel Hub & Bearing", "icon": "⚙️", "why": "Check axial runout and bearing play while rotor is dismounted"}
    ],
    "OIL FILTER": [
        {"component": "ENGINE OIL", "label": "Engine Oil (5W-30 / 15W-40)", "icon": "🛢️", "why": "Standard Periodic Maintenance Service (PMS) mandatory pairing"},
        {"component": "AIR FILTER", "label": "Engine Air Filter", "icon": "💨", "why": "Renew air intake filtration during scheduled oil change"},
        {"component": "CABIN FILTER", "label": "Cabin / AC Pollen Filter", "icon": "❄️", "why": "Ensures clean allergen-free airflow inside vehicle cabin"},
        {"component": "DRAIN PLUG WASHER", "label": "Sump Drain Plug Crush Washer", "icon": "🔘", "why": "Fresh crush washer prevents oil sump bolt weeping and drips"}
    ],
    "AIR FILTER": [
        {"component": "OIL FILTER", "label": "Engine Oil Filter", "icon": "🛢️", "why": "Pair engine breathing and oil lubrication for optimal fuel mileage"},
        {"component": "CABIN FILTER", "label": "Cabin AC Pollen Filter", "icon": "❄️", "why": "Twin filtration service for cabin comfort and engine efficiency"},
        {"component": "SPARK PLUG", "label": "Spark Plugs (Set of 4)", "icon": "⚡", "why": "Complete combustion tune-up companion"}
    ],
    "CABIN FILTER": [
        {"component": "AIR FILTER", "label": "Engine Air Intake Filter", "icon": "💨", "why": "Seasonal PMS inspection standard pair"},
        {"component": "WIPER BLADE", "label": "Front Wiper Blades", "icon": "🌧️", "why": "Monsoon checkup companion"}
    ],
    "CLUTCH DISC": [
        {"component": "CLUTCH COVER", "label": "Clutch Pressure Plate", "icon": "⚙️", "why": "Always replace clutch disc and cover together to ensure balanced clamping"},
        {"component": "CLUTCH RELEASE BEARING", "label": "Clutch Release Bearing / CSC", "icon": "🔄", "why": "Prevents pedal vibration, squeal, and future gearbox drop rework"},
        {"component": "FLYWHEEL", "label": "Flywheel Surface Assembly", "icon": "💿", "why": "Inspect friction surface for hot spots and micro-cracks"},
        {"component": "CLUTCH SLAVE CYLINDER", "label": "Clutch Slave / Master Cylinder", "icon": "🔧", "why": "Hydraulic pedal actuation inspection"}
    ],
    "CLUTCH SET": [
        {"component": "CLUTCH RELEASE BEARING", "label": "Release Bearing / CSC", "icon": "🔄", "why": "Essential partner to clutch overhaul kit"},
        {"component": "FLYWHEEL", "label": "Flywheel Friction Assembly", "icon": "💿", "why": "Ensures smooth progressive clutch bite without judder"}
    ],
    "SHOCK ABSORBER": [
        {"component": "STRUT MOUNT", "label": "Strut Top Mount & Bearing", "icon": "🔩", "why": "Worn top mount causes steering stiffness and thumping noises over bumps"},
        {"component": "LOWER CONTROL ARM", "label": "Lower Control Arm (Chimta)", "icon": "📐", "why": "Inspect ball joint & silent rubber bushes while suspension is dismantled"},
        {"component": "FRONT STABILIZER LINK", "label": "Link Rod / Stabilizer Link", "icon": "🔗", "why": "Common culprit for rattling suspension noises over small bumps"},
        {"component": "COIL SPRING PAD", "label": "Spring Rubber Pad / Dust Bellows", "icon": "🛡️", "why": "Protects shocker chrome shaft from sand and dirt pitting"}
    ],
    "FRONT STRUT ASSEMBLY": [
        {"component": "STRUT MOUNT", "label": "Strut Mount Kit", "icon": "🔩", "why": "Pair strut renewal with fresh top bearing mount"},
        {"component": "FRONT STABILIZER LINK", "label": "Link Rod / Stabilizer Link", "icon": "🔗", "why": "Restores vehicle cornering stability"},
        {"component": "TIE ROD END", "label": "Tie Rod End (Outer)", "icon": "🎯", "why": "Wheel alignment and steering joint renewal"}
    ],
    "LOWER CONTROL ARM": [
        {"component": "FRONT STABILIZER LINK", "label": "Stabilizer Link Rod", "icon": "🔗", "why": "Replaces connected sway bar linkage during front-end suspension overhaul"},
        {"component": "TIE ROD END", "label": "Tie Rod End & Steering Rack Boot", "icon": "🎯", "why": "Complete front-end suspension tightness"}
    ],
    "TIMING BELT": [
        {"component": "TIMING BELT TENSIONER", "label": "Timing Belt Tensioner & Idler", "icon": "⚙️", "why": "Mandatory replacement to prevent timing jump and engine valve damage"},
        {"component": "WATER PUMP", "label": "Engine Water Pump", "icon": "💧", "why": "Driven by timing belt; replace now to save ₹2,500+ repeat labour"},
        {"component": "V-RIBBED BELT", "label": "Alternator & AC Drive Belts", "icon": "🎗️", "why": "Accessory belts must be removed during timing job"}
    ],
    "HEADLAMP ASSEMBLY": [
        {"component": "HEADLIGHT BULB", "label": "Halogen / LED Headlight Bulbs (H4/H7)", "icon": "💡", "why": "Install new bulbs with new reflector assembly"},
        {"component": "FOG LAMP", "label": "Bumper Fog Lamp Unit", "icon": "🔦", "why": "Front lighting restoration companion"},
        {"component": "WIPER BLADE", "label": "Premium Wiper Blades", "icon": "🌧️", "why": "All-weather front visibility package"}
    ],
    "WIPER BLADE": [
        {"component": "WINDSHIELD WASHER FLUID", "label": "Screenwash Concentrate", "icon": "💧", "why": "Cleans oily road film and extends wiper rubber blade life"},
        {"component": "CABIN FILTER", "label": "Cabin AC Pollen Filter", "icon": "❄️", "why": "Monsoon preparation service pair"}
    ],
    "SPARK PLUG": [
        {"component": "IGNITION COIL", "label": "Ignition Coil Boot / Pack", "icon": "⚡", "why": "Check HT spark leads and coil resistance"},
        {"component": "AIR FILTER", "label": "Engine Air Intake Filter", "icon": "💨", "why": "Optimize combustion air/fuel ratio for peak power"}
    ],
    "WATER PUMP": [
        {"component": "ENGINE COOLANT", "label": "Long Life Pre-Mix Coolant", "icon": "🧪", "why": "Complete coolant drain, flush and corrosion protection"},
        {"component": "THERMOSTAT VALVE", "label": "Thermostat Valve & Housing", "icon": "🌡️", "why": "Thermal regulation companion"}
    ]
}

# Automotive Coloquial / Vernacular / Typos / Hindi mapping dictionary
VERNACULAR_COMPONENTS = {
    # Brakes
    "brake pad": "BRAKE PAD", "brek ped": "BRAKE PAD", "break pad": "BRAKE PAD", "brek pad": "BRAKE PAD",
    "front brake pad": "BRAKE PAD", "rear brake pad": "BRAKE PAD", "brake pads": "BRAKE PAD", "pad kit": "BRAKE PAD",
    "brake disc": "BRAKE DISC", "break disc": "BRAKE DISC", "brek disc": "BRAKE DISC", "disc plate": "BRAKE DISC",
    "brake rotor": "BRAKE DISC", "front disc": "BRAKE DISC", "rear disc": "BRAKE DISC",
    "brake shoe": "BRAKE SHOE", "break shoe": "BRAKE SHOE", "brake liner": "BRAKE SHOE", "rear shoe": "BRAKE SHOE", "liner": "BRAKE SHOE",
    "caliper": "BRAKE CALIPER", "brake caliper": "BRAKE CALIPER", "caliper pin": "BRAKE CALIPER", "caliper kit": "BRAKE CALIPER",
    "brake fluid": "BRAKE FLUID", "break oil": "BRAKE FLUID", "brake oil": "BRAKE FLUID", "dot 4": "BRAKE FLUID",
    "brake master cylinder": "BRAKE MASTER CYLINDER", "brake booster": "BRAKE BOOSTER",

    # Clutch & Transmission
    "clutch": "CLUTCH DISC", "cluch": "CLUTCH DISC", "clutch plate": "CLUTCH DISC", "cluch plate": "CLUTCH DISC",
    "clutch disc": "CLUTCH DISC", "friction plate": "CLUTCH DISC",
    "pressure plate": "CLUTCH COVER", "clutch cover": "CLUTCH COVER", "cluch cover": "CLUTCH COVER",
    "clutch kit": "CLUTCH SET", "cluch kit": "CLUTCH SET", "clutch set": "CLUTCH SET", "clutch overhaul": "CLUTCH SET",
    "release bearing": "CLUTCH RELEASE BEARING", "clutch bearing": "CLUTCH RELEASE BEARING", "csc": "CLUTCH RELEASE BEARING",
    "clutch cylinder": "CLUTCH SLAVE CYLINDER", "slave cylinder": "CLUTCH SLAVE CYLINDER", "master cylinder": "CLUTCH MASTER CYLINDER",
    "flywheel": "FLYWHEEL",

    # Filters & Maintenance
    "oil filter": "OIL FILTER", "mobil filter": "OIL FILTER", "oilfilter": "OIL FILTER", "engine filter": "OIL FILTER",
    "air filter": "AIR FILTER", "air cleaner": "AIR FILTER", "filter hawa": "AIR FILTER",
    "cabin filter": "CABIN FILTER", "ac filter": "CABIN FILTER", "a/c filter": "CABIN FILTER", "pollen filter": "CABIN FILTER",
    "fuel filter": "FUEL FILTER", "diesel filter": "FUEL FILTER", "petrol filter": "FUEL FILTER",

    # Suspension & Steering
    "shocker": "SHOCK ABSORBER", "shock absorber": "SHOCK ABSORBER", "strut": "SHOCK ABSORBER", "front shocker": "SHOCK ABSORBER",
    "rear shocker": "SHOCK ABSORBER", "shock up": "SHOCK ABSORBER", "damper": "SHOCK ABSORBER", "shox": "SHOCK ABSORBER",
    "control arm": "LOWER CONTROL ARM", "lower arm": "LOWER CONTROL ARM", "suspension arm": "LOWER CONTROL ARM",
    "chimta": "LOWER CONTROL ARM", "lower control arm": "LOWER CONTROL ARM", "wishbone": "LOWER CONTROL ARM",
    "link rod": "FRONT STABILIZER LINK", "stabilizer link": "FRONT STABILIZER LINK", "balancing rod": "FRONT STABILIZER LINK", "sway bar link": "FRONT STABILIZER LINK",
    "tie rod": "TIE ROD END", "tie rod end": "TIE ROD END", "rack end": "TIE ROD END", "steering ball joint": "TIE ROD END",
    "ball joint": "LOWER BALL JOINT", "lower ball joint": "LOWER BALL JOINT",
    "strut mount": "STRUT MOUNT", "shocker bush": "STRUT MOUNT", "suspension bush": "SUSPENSION BUSH",
    "steering rack": "STEERING GEAR", "steering box": "STEERING GEAR",

    # Engine & Electrical
    "timing belt": "TIMING BELT", "timing kit": "TIMING BELT", "timing chain": "TIMING BELT",
    "fan belt": "V-RIBBED BELT", "alternator belt": "V-RIBBED BELT", "ac belt": "V-RIBBED BELT", "drive belt": "V-RIBBED BELT",
    "water pump": "WATER PUMP", "coolant pump": "WATER PUMP", "pani pump": "WATER PUMP",
    "radiator": "RADIATOR", "coolant tank": "EXPANSION TANK", "coolant": "ENGINE COOLANT",
    "thermostat": "THERMOSTAT VALVE",
    "alternator": "ALTERNATOR", "dynamo": "ALTERNATOR", "generator": "ALTERNATOR",
    "starter motor": "STARTER MOTOR", "self motor": "STARTER MOTOR", "starter": "STARTER MOTOR", "self": "STARTER MOTOR",
    "spark plug": "SPARK PLUG", "sparkplug": "SPARK PLUG", "plug": "SPARK PLUG",
    "glow plug": "GLOW PLUG", "heater plug": "GLOW PLUG",
    "ignition coil": "IGNITION COIL",
    "head gasket": "HEAD GASKET", "engine gasket": "ENGINE GASKET", "valve": "ENGINE VALVE", "piston": "PISTON",

    # Lighting & Body
    "headlamp": "HEADLAMP ASSEMBLY", "headlight": "HEADLAMP ASSEMBLY", "head lamp": "HEADLAMP ASSEMBLY", "front light": "HEADLAMP ASSEMBLY", "batti": "HEADLAMP ASSEMBLY",
    "taillamp": "TAILLAMP ASSEMBLY", "tail light": "TAILLAMP ASSEMBLY", "back light": "TAILLAMP ASSEMBLY",
    "fog lamp": "FOG LAMP", "fog light": "FOG LAMP",
    "bulb": "HEADLIGHT BULB", "headlight bulb": "HEADLIGHT BULB",
    "wiper": "WIPER BLADE", "wiper blade": "WIPER BLADE", "wiper rubber": "WIPER BLADE",
    "side mirror": "SIDE REAR VIEW MIRROR", "mirror": "SIDE REAR VIEW MIRROR", "sheesha": "SIDE REAR VIEW MIRROR", "orvm": "SIDE REAR VIEW MIRROR", "glass mirror": "SIDE REAR VIEW MIRROR",
    "bumper": "BUMPER", "front bumper": "BUMPER ASSY FRONT", "rear bumper": "BUMPER ASSY REAR",
    "bonnet": "BONNET / HOOD", "hood": "BONNET / HOOD",
    "fender": "FRONT FENDER", "mudguard": "FRONT FENDER",
    "door": "DOOR PANEL", "door pad": "DOOR PAD",
    "dicky lock": "TAILGATE LOCK / LATCH", "boot lock": "TAILGATE LOCK / LATCH", "trunk lock": "TAILGATE LOCK / LATCH",
    "horn": "HORN",
    "battery": "BATTERY"
}

# Symptom to Component Diagnosis
SYMPTOMS_MAP = [
    {
        "patterns": [
            r"(break|brake).*(aawaz|noise|sound|awaz|squeak|grind|dabane|marne)",
            r"(aawaz|noise|sound|awaz|squeak|grind).*(break|brake)",
            r"(break|brake).*(fail|loose|pedal)"
        ],
        "diag": "Squeaking, screeching, or grinding noise when pressing the brake pedal typically indicates worn brake pad friction lining touching the rotor disc or glazed brake pads.",
        "component": "BRAKE PAD",
        "alt_components": ["BRAKE DISC", "BRAKE FLUID", "BRAKE CALIPER"]
    },
    {
        "patterns": [
            r"(clutch|cluch).*(hard|tight|slip|heavy|jam|sound|aawaz|awaz|kharab)",
            r"(aawaz|awaz|sound).*(clutch|cluch)",
            r"(gadi|car).*(race|pickup).*(nahi|kam|chhod)",
            r"gear.*(hard|tight|atak|shift.*nahi)"
        ],
        "diag": "A stiff clutch pedal or engine revving without vehicle speed acceleration points to clutch disc friction wear, diaphragm spring hardening, or clutch release bearing seizure.",
        "component": "CLUTCH SET",
        "alt_components": ["CLUTCH DISC", "CLUTCH COVER", "CLUTCH RELEASE BEARING"]
    },
    {
        "patterns": [
            r"(gadda|bump|khadda|khad khad|road).*(aawaz|awaz|sound|dhak dhak)",
            r"(aawaz|awaz|sound).*(gadda|bump|khadda)",
            r"(shocker|strut|chimta|suspension).*(kharab|leak|noise|aawaz|awaz|awaj)",
            r"(suspension).*(noise|aawaz|awaz|sound)"
        ],
        "diag": "Thumping, knocking, or rattling sounds over bumps/potholes indicates shock absorber fluid leakage, worn strut top mount bearings, or play in suspension stabilizer link rods.",
        "component": "SHOCK ABSORBER",
        "alt_components": ["LOWER CONTROL ARM", "FRONT STABILIZER LINK", "STRUT MOUNT"]
    },
    {
        "patterns": [
            r"(overheat|heating|garam|garm|temp|temperature)",
            r"coolant.*(leak|kam|khatam|drain)",
            r"engine.*(hot|garam)"
        ],
        "diag": "Engine temperature rising or overheating usually points to a failing water pump impeller, stuck thermostat valve, low coolant level, or radiator fin blockage.",
        "component": "WATER PUMP",
        "alt_components": ["ENGINE COOLANT", "THERMOSTAT VALVE", "RADIATOR"]
    },
    {
        "patterns": [
            r"(start|self).*(nahi|problem|band|issue)",
            r"battery.*(down|dead|weak|charge)",
            r"(crank|cranking).*(nahi|slow|fail)"
        ],
        "diag": "Slow cranking or clicking without engine start usually indicates a discharged battery, worn starter motor carbon brushes, or fouled spark plugs.",
        "component": "STARTER MOTOR",
        "alt_components": ["BATTERY", "SPARK PLUG", "ALTERNATOR"]
    },
    {
        "patterns": [
            r"(ac|cooling|a/c).*(nahi|kam|bad|problem)",
            r"(bad|foul).*(smell|odor|badboo)",
            r"(ac|cabin).*hawa.*(kam|slow)"
        ],
        "diag": "Weak AC cooling or restricted cabin air blower velocity indicates a clogged cabin pollen filter or evaporator core dirt accumulation.",
        "component": "CABIN FILTER",
        "alt_components": ["AIR FILTER", "WIPER BLADE"]
    }
]

# Vehicle Make to Models Dictionary with Aliases
MAKE_MODELS = {
    "HYUNDAI": [
        "GRAND I10 NIOS", "GRAND I10", "I10", "I20", "CRETA", "VENUE", "VERNA", "AURA", "ALCAZAR",
        "TUCSON", "SANTRO", "EXTER", "KONA", "IONIQ 5", "ELANTRA", "XCENT", "GETZ", "ACCENT"
    ],
    "MARUTI SUZUKI": [
        "SWIFT", "SWIFT DZIRE", "DZIRE", "BALENO", "ERTIGA", "BREZZA", "VITARA BREZZA", "WAGON R",
        "ALTO", "ALTO K10", "CELERIO", "CIAZ", "IGNIS", "S-CROSS", "XL6", "FRONX", "JIMNY",
        "GRAND VITARA", "INVICTO", "RITZ", "ZEN", "ESTEEM", "OMNI", "EECO", "S-PRESSO"
    ],
    "TATA": [
        "NEXON", "PUNCH", "ALTROZ", "HARRIER", "SAFARI", "TIAGO", "TIGOR", "HEXA", "INDICA",
        "INDIGO", "SUMO", "NANO", "ARIA", "ZEST", "BOLT"
    ],
    "MAHINDRA": [
        "SCORPIO", "SCORPIO-N", "SCORPIO CLASSIC", "BOLERO", "BOLERO NEO", "XUV700", "XUV500",
        "XUV300", "THAR", "MARAZZO", "XYLO", "KUV100", "TUV300", "ALTURAS G4"
    ],
    "TOYOTA": [
        "INNOVA", "INNOVA CRYSTA", "INNOVA HYCROSS", "FORTUNER", "COROLLA", "COROLLA ALTIS",
        "ETIOS", "ETIOS LIVA", "GLANZA", "URBAN CRUISER", "YARIS", "CAMRY", "HILUX", "VELLFIRE", "QUALIS"
    ],
    "HONDA": [
        "CITY", "AMAZE", "CIVIC", "JAZZ", "WR-V", "BR-V", "CR-V", "ELEVATE", "BRIO", "ACCORD", "MOBILIO"
    ],
    "FORD": [
        "ECOSPORT", "ENDEAVOUR", "FIGO", "ASPIRE", "FIESTA", "IKON", "FREESTYLE", "FUSION"
    ],
    "RENAULT": [
        "KWID", "DUSTER", "TRIBER", "KIGER", "LODGY", "PULSE", "SCALA"
    ],
    "VOLKSWAGEN": [
        "POLO", "VENTO", "TAIGUN", "VIRTUS", "TIGUAN", "JETTA", "PASSAT", "AMEA"
    ],
    "SKODA": [
        "RAPID", "OCTAVIA", "SUPERB", "KUSHAQ", "SLAVIA", "KODIAQ", "LAURA", "FABIA"
    ],
    "KIA": [
        "SELTOS", "SONET", "CARENS", "CARNIVAL", "EV6"
    ],
    "MORRIS GARAGES": [
        "HECTOR", "HECTOR PLUS", "ASTOR", "ZS EV", "GLOSTER", "COMET"
    ],
    "NISSAN": [
        "MAGNITE", "KICKS", "MICRA", "SUNNY", "TERRANO"
    ]
}

# Aliases for makes
MAKE_ALIASES = {
    "MARUTI": "MARUTI SUZUKI",
    "SUZUKI": "MARUTI SUZUKI",
    "MSIL": "MARUTI SUZUKI",
    "HYUNDAI": "HYUNDAI",
    "TATA": "TATA",
    "MAHINDRA": "MAHINDRA",
    "M&M": "MAHINDRA",
    "TOYOTA": "TOYOTA",
    "HONDA": "HONDA",
    "FORD": "FORD",
    "VW": "VOLKSWAGEN",
    "VOLKSWAGEN": "VOLKSWAGEN",
    "SKODA": "SKODA",
    "RENAULT": "RENAULT",
    "NISSAN": "NISSAN",
    "KIA": "KIA",
    "MG": "MORRIS GARAGES",
    "MORRIS GARAGES": "MORRIS GARAGES",
    "BMW": "BMW",
    "MERCEDES": "MERCEDES-BENZ",
    "MERCEDES-BENZ": "MERCEDES-BENZ",
    "BENZ": "MERCEDES-BENZ",
    "AUDI": "AUDI",
    "CHEVROLET": "CHEVROLET",
    "CHEVY": "CHEVROLET",
    "DATSUN": "DATSUN",
    "FIAT": "FIAT",
    "FORCE": "FORCE MOTORS",
    "ISUZU": "ISUZU",
    "JEEP": "JEEP",
    "VOLVO": "VOLVO"
}

def get_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "overall_catalogue.db")
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def extract_entities_from_text(text):
    """
    Extracts Make, Model, Fuel, Year, Component, Part Number, Symptom from natural language input.
    """
    # Bypass command keywords
    raw_stripped = (text or "").strip()
    if raw_stripped.startswith(('SHOW_VARIANTS', 'SELECT_VARIANT:', 'SET_FUEL:', 'SET_YEAR:', 'SELECT_COMPANION:')):
        return {
            "make": None, "model": None, "fuel": None, "year": None,
            "component": None, "part_no": None, "symptom": None, "raw_query": raw_stripped
        }

    clean_text = " " + text.upper() + " "
    clean_text = re.sub(r'[\,\.\;\:\-\_\/]', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    extracted = {
        "make": None,
        "model": None,
        "fuel": None,
        "year": None,
        "component": None,
        "part_no": None,
        "symptom": None,
        "raw_query": text.strip()
    }

    # 1. Direct Part Number detection (e.g. 21658101B4A05, 04152-YZZA6, 00158101B4A05, 006-04152-YZZA6, 706F002H264478F8, 16510-M68K00)
    part_match = re.search(r'\b([A-Z0-9]{5,20}|[A-Z0-9]{2,6}[\-\s\/][A-Z0-9\-]{4,16})\b', text.strip(), re.IGNORECASE)
    if part_match:
        cand = part_match.group(1).upper()
        if any(c.isdigit() for c in cand) and len(cand) >= 5:
            import overall_catalogue_api
            cross_cands, cross_meta = overall_catalogue_api.build_cross_line_code_candidates(cand)
            test_cands = list(dict.fromkeys([cand, cand.replace('-', '').replace(' ', '')] + cross_cands))
            conn = get_db()
            if conn:
                try:
                    c = conn.cursor()
                    chunk_size = 350
                    for i in range(0, len(test_cands), chunk_size):
                        chk = test_cands[i:i+chunk_size]
                        pls = ','.join(['?'] * len(chk))
                        c.execute(f"SELECT line_code_part_number, line_code, brand_name, part_description FROM overall_catalogue WHERE line_code_part_number IN ({pls}) LIMIT 1", chk)
                        matched_row = c.fetchone()
                        if matched_row:
                            matched_no = matched_row["line_code_part_number"]
                            actual_lc = matched_row["line_code"]
                            meta = cross_meta.get(matched_no, {})
                            input_lc = meta.get("input_lc")
                            is_diff = bool(input_lc and actual_lc and (str(input_lc).strip().upper() != str(actual_lc).strip().upper()))
                            extracted["part_no"] = matched_no
                            extracted["input_line_code"] = input_lc
                            extracted["actual_line_code"] = actual_lc
                            extracted["actual_brand"] = matched_row["brand_name"]
                            extracted["cross_line_code_resolved"] = is_diff
                            break
                    conn.close()
                except Exception:
                    if conn: conn.close()

    # 2. Extract Year (e.g. 2019, 2021, '18, 2024)
    yr_match = re.search(r'\b(200[0-9]|201[0-9]|202[0-6])\b', clean_text)
    if yr_match:
        extracted["year"] = yr_match.group(1)
    else:
        yr_short = re.search(r"\'?(0[5-9]|1[0-9]|2[0-6])\b", text)
        if yr_short and ("MODEL" in clean_text or "YEAR" in clean_text or "'" in text):
            extracted["year"] = "20" + yr_short.group(1)

    # 3. Extract Fuel Type
    if "PETROL/CNG" in clean_text or "CNG/PETROL" in clean_text:
        extracted["fuel"] = "PETROL/CNG"
    elif "PETROL" in clean_text or "PETR" in clean_text:
        extracted["fuel"] = "PETROL"
    elif "DIESEL" in clean_text or "DISL" in clean_text or "DISEL" in clean_text:
        extracted["fuel"] = "DIESEL"
    elif "CNG" in clean_text:
        extracted["fuel"] = "CNG"
    elif "ELECTRIC" in clean_text or " EV " in clean_text:
        extracted["fuel"] = "ELECTRIC"
    elif "HYBRID" in clean_text:
        extracted["fuel"] = "HYBRID"

    # 4. Extract Make
    for alias, std_make in sorted(MAKE_ALIASES.items(), key=lambda x: -len(x[0])):
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, clean_text):
            extracted["make"] = std_make
            break

    # 5. Extract Model (Check models across all makes or selected make)
    model_candidates = []
    for mk, models in MAKE_MODELS.items():
        for mdl in sorted(models, key=lambda x: -len(x)):
            # Word boundary check for model name
            pattern = r'\b' + re.escape(mdl) + r'\b'
            if re.search(pattern, clean_text):
                model_candidates.append((mk, mdl))
            elif len(mdl) >= 5:
                # Substring match only for unique long model names
                cleaned_mdl = mdl.replace(" ", "")
                cleaned_q = clean_text.replace(" ", "")
                if cleaned_mdl in cleaned_q and len(cleaned_mdl) >= 5:
                    model_candidates.append((mk, mdl))

    if model_candidates:
        # Sort by longest model name match first
        model_candidates.sort(key=lambda x: -len(x[1]))
        chosen_make, chosen_model = model_candidates[0]
        extracted["model"] = chosen_model
        if not extracted["make"]:
            extracted["make"] = chosen_make

    # Special handling for popular Indian car aliases/typos
    if not extracted["model"]:
        low_text = text.lower()
        if "inova" in low_text or "innova" in low_text:
            extracted["make"] = "TOYOTA"; extracted["model"] = "INNOVA"
        elif "nios" in low_text:
            extracted["make"] = "HYUNDAI"; extracted["model"] = "GRAND I10 NIOS"
        elif "creta" in low_text or "creata" in low_text:
            extracted["make"] = "HYUNDAI"; extracted["model"] = "CRETA"
        elif "scorpio" in low_text or "skorpio" in low_text:
            extracted["make"] = "MAHINDRA"; extracted["model"] = "SCORPIO"
        elif "swift" in low_text:
            extracted["make"] = "MARUTI SUZUKI"
            extracted["model"] = "SWIFT DZIRE" if ("dzire" in low_text or "desire" in low_text) else "SWIFT"
        elif "ertiga" in low_text:
            extracted["make"] = "MARUTI SUZUKI"; extracted["model"] = "ERTIGA"
        elif "baleno" in low_text or "balino" in low_text:
            extracted["make"] = "MARUTI SUZUKI"; extracted["model"] = "BALENO"
        elif "nexon" in low_text:
            extracted["make"] = "TATA"; extracted["model"] = "NEXON"
        elif "altroz" in low_text:
            extracted["make"] = "TATA"; extracted["model"] = "ALTROZ"
        elif "seltos" in low_text:
            extracted["make"] = "KIA"; extracted["model"] = "SELTOS"

    # 6. Extract Component from Vernacular dictionary
    low_text = text.lower()
    for slang, std_comp in sorted(VERNACULAR_COMPONENTS.items(), key=lambda x: -len(x[0])):
        if slang in low_text:
            extracted["component"] = std_comp
            break

    # 7. Check Symptom Diagnosis if no direct component found
    if not extracted["component"]:
        for sym in SYMPTOMS_MAP:
            for pat in sym["patterns"]:
                if re.search(pat, low_text):
                    extracted["symptom"] = sym
                    extracted["component"] = sym["component"]
                    break
            if extracted["symptom"]:
                break

    return extracted

def fetch_variant_cards_for_chat(make, model, fuel_type=None, year=None):
    """
    Returns visual variant cards with real Oriparts 3D car render images.
    """
    import overall_catalogue_api
    clean_fuel = None if not fuel_type or str(fuel_type).strip().lower() in ["all fuels", "any fuel", "all", "any", "none"] else str(fuel_type).strip()
    clean_year = None if not year or str(year).strip().lower() in ["all years", "any year", "all", "any", "none"] else str(year).strip()
    res = overall_catalogue_api.get_visual_variants(make, model, fuel_type=clean_fuel, year=clean_year, limit=12)
    return res.get("variants", [])

def fetch_parts_for_component(make, model, sub_model=None, component=None, fuel_type=None, year=None):
    """
    Searches 23.6M catalogue for OEM genuine and Tier-1 OES parts matching vehicle and component.
    """
    conn = get_db()
    if not conn: return {"oem": None, "oes": []}

    try:
        cur = conn.cursor()
        
        # Build query clauses
        clauses = []
        params = []

        if make:
            if make in ["MARUTI", "MARUTI SUZUKI"]:
                clauses.append("(vehicle_make = 'MARUTI' OR vehicle_make = 'MARUTI SUZUKI')")
            elif make in ["VOLKSWAGEN", "VW"]:
                clauses.append("(vehicle_make = 'VOLKSWAGEN' OR vehicle_make = 'VW')")
            else:
                clauses.append("vehicle_make = ?")
                params.append(make)

        if model:
            clauses.append("vehicle_model = ?")
            params.append(model)

        if sub_model and sub_model != "ALL":
            clean_sub = sub_model.strip()
            clauses.append("(vehicle_sub_model = ? OR vehicle_sub_model LIKE ? OR vehicle_sub_model = '' OR vehicle_sub_model IS NULL)")
            params.extend([clean_sub, f"%{clean_sub[:10]}%"])

        # Component matching (handles FRONT/REAR, PAD KIT, TIE ROD, etc.)
        if component:
            clean_c = component.upper()
            if "BRAKE PAD" in clean_c:
                clauses.append("(components LIKE '%BRAKE PAD%' OR part_description LIKE '%PAD KIT%')")
            elif "BRAKE DISC" in clean_c:
                clauses.append("(components LIKE '%BRAKE DISC%' OR part_description LIKE '%BRAKE DISC%' OR part_description LIKE '%ROTOR%')")
            elif "CLUTCH" in clean_c:
                clauses.append("(components LIKE ? OR part_description LIKE ?)")
                params.extend([f"%{clean_c}%", f"%{clean_c}%"])
            elif "OIL FILTER" in clean_c:
                clauses.append("(components = 'OIL FILTER' OR part_description LIKE '%OIL FILTER%')")
            elif "AIR FILTER" in clean_c:
                clauses.append("(components = 'AIR FILTER' OR part_description LIKE '%AIR FILTER%')")
            elif "CABIN FILTER" in clean_c:
                clauses.append("(components = 'CABIN FILTER' OR part_description LIKE '%CABIN FILTER%' OR part_description LIKE '%POLLEN%')")
            elif "SHOCK ABSORBER" in clean_c:
                clauses.append("(components LIKE '%SHOCK ABSORBER%' OR components LIKE '%STRUT%' OR part_description LIKE '%SHOCK ABSORBER%' OR part_description LIKE '%STRUT%')")
            elif "CONTROL ARM" in clean_c:
                clauses.append("(components LIKE '%CONTROL ARM%' OR part_description LIKE '%CONTROL ARM%')")
            elif "TIE ROD" in clean_c or "RACK END" in clean_c:
                clauses.append("(components LIKE '%TIE ROD%' OR components LIKE '%INNER TIE ROD%' OR part_description LIKE '%TIE ROD%' OR part_description LIKE '%RACK END%')")
            else:
                clauses.append("(components LIKE ? OR part_description LIKE ?)")
                params.extend([f"%{clean_c}%", f"%{clean_c}%"])

        where_str = " WHERE " + " AND ".join(clauses) if clauses else ""

        # Determine primary component keyword for ranking (e.g. "TIE ROD END" -> "TIE ROD")
        comp_kw = component or 'PART'
        if "TIE ROD" in comp_kw.upper():
            comp_kw = "TIE ROD"
        elif "BRAKE PAD" in comp_kw.upper():
            comp_kw = "BRAKE PAD"
        elif "CLUTCH" in comp_kw.upper():
            comp_kw = "CLUTCH"
        elif "OIL FILTER" in comp_kw.upper():
            comp_kw = "OIL FILTER"
        elif "AIR FILTER" in comp_kw.upper():
            comp_kw = "AIR FILTER"

        sql = f"""
        SELECT line_code_part_number, brand_name, part_description, mrp_price, list_price,
               tax_rate, line_code, vehicle_make, vehicle_model, vehicle_sub_model,
               vehicle_fuel_type, vehicle_from_year, vehicle_to_year, components, aggregate
        FROM overall_catalogue
        {where_str}
        ORDER BY CASE WHEN UPPER(part_description) LIKE ? THEN 0 ELSE 1 END,
                 CASE WHEN UPPER(brand_name) = ? THEN 0 ELSE 1 END,
                 CASE WHEN UPPER(part_description) LIKE '%KIT%' OR UPPER(part_description) LIKE '%SET%' OR UPPER(part_description) LIKE '%ASSY%' THEN 0 ELSE 1 END,
                 CASE WHEN mrp_price >= 100 THEN 0 ELSE 1 END,
                 CASE WHEN mrp_price > 0 THEN 0 ELSE 1 END,
                 mrp_price ASC
        LIMIT 200
        """
        all_params = params + [f"%{comp_kw}%", (make or '').upper()]
        cur.execute(sql, all_params)
        rows = cur.fetchall()

        oem_part = None
        oes_parts = []
        seen_part_nos = set()

        for r in rows:
            p_no = r["line_code_part_number"]
            if p_no in seen_part_nos:
                continue
            seen_part_nos.add(p_no)

            item = {
                "partNo": p_no,
                "brand": r["brand_name"] or "GENERIC",
                "desc": r["part_description"] or component or "Automotive Part",
                "mrp": float(r["mrp_price"] or 0),
                "listPrice": float(r["list_price"] or 0),
                "lineCode": r["line_code"] or "",
                "make": r["vehicle_make"] or make,
                "model": r["vehicle_model"] or model,
                "subModel": r["vehicle_sub_model"] or "",
                "fuelType": r["vehicle_fuel_type"] or "",
                "years": f"{r['vehicle_from_year'] or ''} - {r['vehicle_to_year'] or ''}".strip(" -"),
                "component": r["components"] or component,
                "aggregate": r["aggregate"] or "PARTS"
            }

            # Check if this is the OEM Genuine part
            is_oem = (r["brand_name"] or "").upper() == (make or "").upper()
            if is_oem and not oem_part:
                item["isOem"] = True
                oem_part = item
            else:
                item["isOem"] = is_oem
                oes_parts.append(item)

        # If no specific OEM part branded with make name, take the first as reference OEM
        if not oem_part and oes_parts:
            oem_part = oes_parts.pop(0)
            oem_part["isOem"] = True

        conn.close()
        return {"oem": oem_part, "oes": oes_parts[:10]}
    except Exception as e:
        if conn: conn.close()
        print("fetch_parts_for_component error:", e)
        return {"oem": None, "oes": []}

def get_relatable_parts_list(component_name):
    """
    Fetches relatable/companion parts for a given component.
    """
    comp_clean = (component_name or "").upper()
    for key, related in RELATABLE_COMPONENTS_MAP.items():
        if key in comp_clean or comp_clean in key:
            return related
    return [
        {"component": "BRAKE FLUID", "label": "Brake Fluid DOT 4", "icon": "🧪", "why": "General periodic safety overhaul inspection"},
        {"component": "WIPER BLADE", "label": "All-Weather Wiper Blades", "icon": "🌧️", "why": "Front windshield visibility companion"}
    ]

def process_chat_message(user_message, session_state=None):
    """
    Main Conversational Chatbot Engine.
    Handles user prompts, state progression, entity extraction, interactive chips,
    visual variant cards with Oriparts images, OEM/OES parts matrix, and companion recommendations.
    """
    if session_state is None:
        session_state = {}

    user_text = (user_message or "").strip()
    entities = extract_entities_from_text(user_text)

    # Merge newly detected entities into current session state
    if entities["make"]: session_state["make"] = entities["make"]
    if entities["model"]: session_state["model"] = entities["model"]
    if entities["fuel"]: session_state["fuel"] = entities["fuel"]
    if entities["year"]: session_state["year"] = entities["year"]
    if entities["component"]: session_state["component"] = entities["component"]
    if entities["part_no"]: session_state["part_no"] = entities["part_no"]

    # 1. DIRECT PART NUMBER LOOKUP
    if session_state.get("part_no"):
        p_no = session_state["part_no"]
        import overall_catalogue_api
        details = overall_catalogue_api.get_part_details(p_no)
        if details:
            is_cross = entities.get("cross_line_code_resolved") or details.get("crossLineCodeResolved")
            input_lc = entities.get("input_line_code") or details.get("inputLineCode")
            actual_lc = details.get("lineCode")
            brand = details.get("brand")
            if is_cross:
                details["crossLineCodeResolved"] = True
                details["inputLineCode"] = input_lc
                details["lineCodeAlert"] = f"Searched with Line Code '{input_lc}', auto-resolved to Line Code {actual_lc} ({brand})"
                bot_reply = f"⚡ **Line Code Auto-Resolved**: You searched with Line Code **`{input_lc}`**, but this genuine part is indexed in the Master Catalogue under **Line Code `{actual_lc}` ({brand})**!\n\nShowing verified part specifications, OEM fitments, and OES alternatives for **`{details['partNo']}`**:"
            else:
                bot_reply = f"✅ **Direct Part Intelligence Found for `{details['partNo']}`** ({details['brand']})"
            return {
                "reply": bot_reply,
                "step": "part_details",
                "state": session_state,
                "action": {
                    "type": "direct_part_lookup",
                    "part": details,
                    "oes": details.get("oesParts", [])
                }
            }

    # 2. CHECK IF COMPONENT WAS SELECTED VIA COMPANION RECOMMENDATION
    if user_text.startswith("SELECT_COMPANION:"):
        comp_target = user_text.replace("SELECT_COMPANION:", "").strip()
        session_state["component"] = comp_target
        # Directly fetch parts for this vehicle variant
        parts_data = fetch_parts_for_component(
            session_state.get("make"), session_state.get("model"),
            sub_model=session_state.get("sub_model"), component=comp_target,
            fuel_type=session_state.get("fuel"), year=session_state.get("year")
        )
        relatable = get_relatable_parts_list(comp_target)
        bot_reply = f"Here are the companion parts for **{comp_target}** on your **{session_state.get('make')} {session_state.get('model')}**:"
        return {
            "reply": bot_reply,
            "step": "parts_result",
            "state": session_state,
            "action": {
                "type": "parts_matrix",
                "component": comp_target,
                "vehicle": f"{session_state.get('make')} {session_state.get('model')} {session_state.get('sub_model') or ''}",
                "oem": parts_data["oem"],
                "oes": parts_data["oes"],
                "relatable": relatable
            }
        }

    # 3. CHECK IF VARIANT WAS SELECTED VIA CHIP OR USER INPUT
    if user_text.startswith("SELECT_VARIANT:"):
        variant_name = user_text.replace("SELECT_VARIANT:", "").strip()
        session_state["sub_model"] = variant_name
        comp = session_state.get("component") or "BRAKE PAD"
        
        parts_data = fetch_parts_for_component(
            session_state.get("make"), session_state.get("model"),
            sub_model=variant_name, component=comp,
            fuel_type=session_state.get("fuel"), year=session_state.get("year")
        )
        relatable = get_relatable_parts_list(comp)

        oem_part = parts_data["oem"]
        oes_list = parts_data["oes"]
        variant_disp = variant_name if variant_name != "ALL" else f"{session_state.get('make')} {session_state.get('model')}"

        bot_reply = f"✨ Verified exact fitment for **{comp}** on **{session_state.get('make')} {session_state.get('model')}** (`{variant_disp}`). Showing OEM Genuine specification along with verified Tier-1 OES aftermarket alternatives:"

        return {
            "reply": bot_reply,
            "step": "parts_result",
            "state": session_state,
            "action": {
                "type": "parts_matrix",
                "component": comp,
                "variant": variant_disp,
                "vehicle": f"{session_state.get('make')} {session_state.get('model')}",
                "oem": oem_part,
                "oes": oes_list,
                "relatable": relatable
            }
        }

    # 4. IF MAKE & MODEL IDENTIFIED, CHECK FOR FUEL & YEAR
    curr_make = session_state.get("make")
    curr_model = session_state.get("model")
    curr_comp = session_state.get("component")

    # If symptom detected without vehicle, explain and ask for vehicle
    if entities.get("symptom") and not curr_model:
        sym = entities["symptom"]
        bot_reply = f"🔍 **Diagnostic Assessment**: {sym['diag']}\n\nTo identify the exact replacement parts and OEM specifications, **which car make & model do you drive?**"
        return {
            "reply": bot_reply,
            "step": "symptom_ask_vehicle",
            "state": session_state,
            "action": {
                "type": "quick_makes",
                "suggested_component": sym["component"],
                "alt_components": sym["alt_components"],
                "makes": ["HYUNDAI", "MARUTI SUZUKI", "TATA", "MAHINDRA", "TOYOTA", "HONDA"]
            }
        }

    if curr_make and curr_model:
        # Check if fuel or year missing
        curr_fuel = session_state.get("fuel")
        curr_year = session_state.get("year")

        # If user just gave Fuel or Year via quick chip click
        if user_text.startswith("SET_FUEL:"):
            session_state["fuel"] = user_text.replace("SET_FUEL:", "").strip()
            curr_fuel = session_state["fuel"]
        if user_text.startswith("SET_YEAR:"):
            session_state["year"] = user_text.replace("SET_YEAR:", "").strip()
            curr_year = session_state["year"]

        # If both Fuel AND Year are provided, or user chose to proceed with current filters:
        # Render the Visual Variant Cards with Oriparts 3D images!
        if (curr_fuel and curr_year) or user_text.startswith("SHOW_VARIANTS"):
            variants = fetch_variant_cards_for_chat(curr_make, curr_model, fuel_type=curr_fuel, year=curr_year)
            comp_display = curr_comp or "Parts Catalogue"
            bot_reply = f"🚗 I found **{len(variants)} matching {curr_make} {curr_model} generations/variants** for {curr_fuel or 'All Fuels'} ({curr_year or 'All Years'}).\n\nPlease select your exact vehicle variant below to see verified fitment for **{comp_display}**:"
            
            return {
                "reply": bot_reply,
                "step": "choose_variant",
                "state": session_state,
                "action": {
                    "type": "visual_variants_selection",
                    "make": curr_make,
                    "model": curr_model,
                    "component": curr_comp,
                    "fuel": curr_fuel,
                    "year": curr_year,
                    "variants": variants
                }
            }
        else:
            # Prompt user for Fuel Type and Year
            comp_display = f"**{curr_comp}**" if curr_comp else "parts"
            bot_reply = f"🚘 Identified **{curr_make} {curr_model}** for {comp_display}!\n\nTo ensure 100% precision fitment (OEM specifications and prices differ by engine & facelift year), please select your **Fuel Type** and **Manufacturing Year**:"
            
            fuel_options = ["Petrol", "Diesel", "CNG", "Petrol/CNG"]
            year_options = ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015", "All Years"]
            
            return {
                "reply": bot_reply,
                "step": "ask_fuel_year",
                "state": session_state,
                "action": {
                    "type": "fuel_year_prompt",
                    "make": curr_make,
                    "model": curr_model,
                    "component": curr_comp,
                    "selected_fuel": curr_fuel,
                    "selected_year": curr_year,
                    "fuel_options": fuel_options,
                    "year_options": year_options
                }
            }

    # 5. IF ONLY MAKE IS IDENTIFIED (NO MODEL)
    if curr_make and not curr_model:
        models = MAKE_MODELS.get(curr_make, ["SWIFT", "CRETA", "SCORPIO", "CITY", "INNOVA"])[:8]
        bot_reply = f"Great! You selected **{curr_make}**. Which model are you searching for?"
        return {
            "reply": bot_reply,
            "step": "ask_model",
            "state": session_state,
            "action": {
                "type": "model_chips",
                "make": curr_make,
                "models": models
            }
        }

    # 6. IF ONLY COMPONENT IS IDENTIFIED (NO VEHICLE)
    if curr_comp and not curr_model:
        bot_reply = f"🔧 Looking for **{curr_comp}**! Which vehicle make and model is this for? (e.g. *Hyundai Grand i10 Nios*, *Maruti Swift*, *Mahindra Scorpio*):"
        return {
            "reply": bot_reply,
            "step": "ask_vehicle_for_comp",
            "state": session_state,
            "action": {
                "type": "vehicle_quick_chips",
                "component": curr_comp,
                "suggested_vehicles": [
                    {"make": "HYUNDAI", "model": "GRAND I10 NIOS"},
                    {"make": "MARUTI SUZUKI", "model": "SWIFT"},
                    {"make": "HYUNDAI", "model": "CRETA"},
                    {"make": "MAHINDRA", "model": "SCORPIO"},
                    {"make": "TOYOTA", "model": "INNOVA"},
                    {"make": "TATA", "model": "NEXON"}
                ]
            }
        }

    # 7. DEFAULT / FALLBACK / GREETING
    bot_reply = (
        "👋 **Hello! I am AutoNexa Catalog AI** — your master spare parts and diagnostic assistant.\n\n"
        "You can ask me anything naturally, such as:\n"
        "• *'Grand i10 Nios brake pad'*\n"
        "• *'Swift diesel 2018 oil filter'*\n"
        "• *'Innova clutch plate'*\n"
        "• *'Creta shocker kharab hai / squeaking sound'* (Mechanic Hindi/English)\n"
        "• Or enter any raw part number like *'21658101B4A05'*\n\n"
        "How can I assist you with your vehicle today?"
    )
    return {
        "reply": bot_reply,
        "step": "welcome",
        "state": session_state,
        "action": {
            "type": "welcome_prompts",
            "prompts": [
                "Hyundai Grand i10 Nios Brake Pad",
                "Maruti Swift Diesel Oil Filter",
                "Toyota Innova Clutch Plate",
                "Mahindra Scorpio Front Shocker",
                "21658101B4A05"
            ]
        }
    }
