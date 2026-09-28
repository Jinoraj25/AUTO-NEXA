import os, pandas as pd, json, re

csv_path = r"C:\Users\SM0237\Downloads\Mapped_Catalogue_Export_2026-09-28.csv"
if not os.path.exists(csv_path):
    # Try finding any export file in Downloads
    import glob
    files = glob.glob(r"C:\Users\SM0237\Downloads\Mapped_Catalogue*.csv") + glob.glob(r"C:\Users\SM0237\Downloads\FOR MAPPING*.xlsx")
    csv_path = files[0]

print(f"Testing on file: {csv_path}")
if csv_path.endswith('.csv'):
    df = pd.read_csv(csv_path, low_memory=False)
else:
    df = pd.read_excel(csv_path)

records = df.to_dict(orient='records')
print(f"Loaded {len(records):,} records.")

# Load TVS Master
with open('data/aggregate_master_rules.json', 'r') as f:
    master_data = json.load(f)
master = master_data.get('aggregateMaster', [])

STOP_WORDS = {'LH', 'RH', 'SET', 'KIT', 'FOR', 'AND', 'WITH', 'TYPE', 'STD', 'ASSY', 'NO', 'OFF', 'PCS', 'BLK', 'RED', 'BLUE', 'TYPE1', 'TYPE2', 'ECO', 'NEW', 'OLD', 'GENUINE', 'OEN', 'OEM', 'CAR', 'BLACK', 'WHITE', 'SIDE', 'FRONT', 'REAR', 'INNER', 'OUTER', 'TOP', 'BOTTOM', 'UPPER', 'LOWER'}

# Comprehensive Automotive Keyword Domain Map
DOMAIN_KEYWORDS = [
    # BRAKE SYSTEM
    ('BRAKE SHOE', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE SHOE'),
    ('DRUM BRAKE', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE SHOE'),
    ('BRAKE PAD', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD'),
    ('DISC PAD', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD'),
    ('BRAKE DISC', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE DISC / ROTOR'),
    ('BRAKE ROTOR', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE DISC / ROTOR'),
    ('BRAKE DRUM', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE DRUM'),
    ('BRAKE HOSE', 'BRAKE SYSTEM', 'HYDRAULIC LINES', 'BRAKE HOSE'),
    ('BRAKE PIPE', 'BRAKE SYSTEM', 'HYDRAULIC LINES', 'BRAKE PIPE LINE'),
    ('BRAKE LINING', 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE LINING'),
    ('BRAKE', 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD'),

    # ENGINE & FILTERS
    ('OIL FILTER', 'ENGINE', 'FILTERS', 'OIL FILTER'),
    ('AIR FILTER', 'ENGINE', 'FILTERS', 'AIR FILTER'),
    ('FUEL FILTER', 'ENGINE', 'FILTERS', 'FUEL FILTER'),
    ('CABIN FILTER', 'HVAC/THERMAL', 'FILTERS', 'CABIN AIR FILTER'),
    ('FILTER', 'ENGINE', 'FILTERS', 'OIL FILTER'),
    ('PISTON', 'ENGINE', 'BLOCK & HEAD', 'PISTON & RINGS'),
    ('CYLINDER HEAD', 'ENGINE', 'BLOCK & HEAD', 'CYLINDER HEAD'),
    ('VALVE', 'ENGINE', 'VALVE TRAIN', 'ENGINE VALVE'),
    ('CRANKSHAFT', 'ENGINE', 'BLOCK & HEAD', 'CRANKSHAFT'),
    ('CAMSHAFT', 'ENGINE', 'VALVE TRAIN', 'CAMSHAFT'),
    ('TURBOCHARGER', 'ENGINE', 'AIR INTAKE', 'TURBOCHARGER'),
    ('TURBO', 'ENGINE', 'AIR INTAKE', 'TURBOCHARGER'),
    ('SPARK PLUG', 'ELECTRICALS AND ELECTRONICS', 'IGNITION SYSTEM', 'SPARK PLUG'),
    ('GLOW PLUG', 'ELECTRICALS AND ELECTRONICS', 'IGNITION SYSTEM', 'GLOW PLUG'),

    # BODY PARTS & TRIM
    ('BUMPER', 'BODY PARTS', 'BODY TRIM', 'BUMPER TRIM'),
    ('GRILLE', 'BODY PARTS', 'BODY TRIM', 'FRONT GRILLE'),
    ('GRIL', 'BODY PARTS', 'BODY TRIM', 'FRONT GRILLE'),
    ('FENDER', 'BODY PARTS', 'PANELS', 'FENDER PANEL'),
    ('BONNET', 'BODY PARTS', 'PANELS', 'HOOD / BONNET'),
    ('HOOD', 'BODY PARTS', 'PANELS', 'HOOD / BONNET'),
    ('DOOR', 'BODY PARTS', 'PANELS', 'DOOR PANEL'),
    ('MIRROR', 'BODY PARTS', 'MIRRORS', 'REAR VIEW MIRROR'),
    ('REAR VIEW', 'BODY PARTS', 'MIRRORS', 'REAR VIEW MIRROR'),
    ('WINDSHIELD', 'GLASS', 'WINDSHIELD', 'FRONT WINDSHIELD GLASS'),
    ('GLASS', 'GLASS', 'WINDSHIELD', 'DOOR GLASS'),
    ('HANDLE', 'BODY PARTS', 'DOOR HARDWARE', 'DOOR HANDLE'),
    ('LOCK', 'BODY PARTS', 'LOCKS', 'DOOR LOCK ASSY'),
    ('LATCH', 'BODY PARTS', 'LOCKS', 'HOOD LATCH'),
    ('BRACKET', 'BODY PARTS', 'BODY TRIM', 'MOUNTING BRACKET'),
    ('BRACE', 'BODY PARTS', 'BODY TRIM', 'MOUNTING BRACKET'),
    ('HOLDER', 'BODY PARTS', 'BODY TRIM', 'MOUNTING BRACKET'),
    ('STAY', 'BODY PARTS', 'BODY TRIM', 'HOOD STAY / ROD'),
    ('GRIP', 'BODY PARTS', 'INTERIOR TRIM', 'GRIP HANDLE'),
    ('PANEL', 'BODY PARTS', 'PANELS', 'BODY PANEL'),
    ('COWL', 'BODY PARTS', 'PANELS', 'COWL PANEL'),
    ('EMBLEM', 'BODY PARTS', 'EMBLEMS', 'CAR EMBLEM / MONOGRAM'),

    # LIGHTING
    ('HEAD LAMP', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'),
    ('HEADLIGHT', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'),
    ('TAIL LAMP', 'LIGHTING', 'TAILLAMP', 'TAIL LAMP ASSEMBLY'),
    ('TAILLIGHT', 'LIGHTING', 'TAILLAMP', 'TAIL LAMP ASSEMBLY'),
    ('FOG LAMP', 'LIGHTING', 'FOGLAMP', 'FOG LAMP / LIGHT ASSEMBLY'),
    ('FOG LIGHT', 'LIGHTING', 'FOGLAMP', 'FOG LAMP / LIGHT ASSEMBLY'),
    ('INDICATOR', 'LIGHTING', 'SIGNAL LAMP', 'SIDE INDICATOR LAMP'),
    ('BULB', 'LIGHTING', 'BULBS', 'HEADLAMP BULB'),
    ('LAMP', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'),
    ('LIGHT', 'LIGHTING', 'HEADLAMP', 'HEAD LAMP ASSEMBLY'),

    # SUSPENSION & STEERING
    ('SHOCK ABSORBER', 'SUSPENSION', 'SHOCK ABSORBER', 'FRONT SHOCK ABSORBER'),
    ('STRUT', 'SUSPENSION', 'STRUT ASSEMBLY', 'FRONT STRUT ASSEMBLY'),
    ('LEAF SPRING', 'SUSPENSION', 'SPRINGS', 'LEAF SPRING ASSEMBLY'),
    ('COIL SPRING', 'SUSPENSION', 'SPRINGS', 'COIL SPRING'),
    ('BALL JOINT', 'SUSPENSION', 'LINKAGE', 'SUSPENSION BALL JOINT'),
    ('ARM CONTROL', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'),
    ('CONTROL ARM', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'),
    ('LOWER ARM', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'),
    ('UPPER ARM', 'SUSPENSION', 'LINKAGE', 'SUSPENSION CONTROL ARM'),
    ('BUSH', 'SUSPENSION', 'BUSHINGS', 'SUSPENSION BUSH'),
    ('BUSHING', 'SUSPENSION', 'BUSHINGS', 'SUSPENSION BUSH'),
    ('STABILIZER', 'SUSPENSION', 'LINKAGE', 'STABILIZER BAR LINK'),
    ('HUB', 'SUSPENSION', 'WHEEL HUB', 'WHEEL HUB ASSEMBLY'),
    ('BEARING', 'BEARING', 'WHEEL BEARING', 'WHEEL BEARING'),
    ('STEERING RACK', 'STEERING', 'POWER STEERING', 'STEERING RACK & BOOT'),
    ('STEERING GEAR', 'STEERING', 'GEARBOX', 'STEERING GEARBOX'),
    ('STEERING BOOT', 'STEERING', 'STEERING LINKAGE', 'STEERING BOOT'),
    ('STEERING', 'STEERING', 'STEERING LINKAGE', 'STEERING TIE ROD END'),

    # TRANSMISSION & CLUTCH
    ('CLUTCH DISC', 'CLUTCH SYSTEM', 'CLUTCH DISC', 'CLUTCH DISC & PLATE'),
    ('CLUTCH PLATE', 'CLUTCH SYSTEM', 'CLUTCH DISC', 'CLUTCH DISC & PLATE'),
    ('CLUTCH COVER', 'CLUTCH SYSTEM', 'CLUTCH COVER', 'CLUTCH COVER / PRESSURE PLATE'),
    ('PRESSURE PLATE', 'CLUTCH SYSTEM', 'CLUTCH COVER', 'CLUTCH COVER / PRESSURE PLATE'),
    ('CLUTCH KIT', 'CLUTCH SYSTEM', 'CLUTCH KIT', 'CLUTCH KIT COMPLETE'),
    ('CLUTCH CABLE', 'CLUTCH SYSTEM', 'CONTROLS', 'CLUTCH CABLE'),
    ('CLUTCH', 'CLUTCH SYSTEM', 'CLUTCH ASSEMBLY', 'CLUTCH DISC & PLATE'),
    ('GEARBOX', 'TRANSMISSION', 'GEARBOX', 'TRANSMISSION GEARBOX'),
    ('GEAR SHIFT', 'TRANSMISSION', 'CONTROLS', 'GEAR SHIFT LEVER KIT'),
    ('GEAR LEVER', 'TRANSMISSION', 'CONTROLS', 'GEAR SHIFT LEVER KIT'),
    ('GEAR', 'TRANSMISSION', 'GEARS', 'TRANSMISSION GEAR'),
    ('FLYWHEEL', 'TRANSMISSION', 'FLYWHEEL', 'FLYWHEEL ASSEMBLY'),
    ('UNIVERSAL JOINT', 'TRANSMISSION', 'PROPELLER SHAFT', 'UNIVERSAL JOINT KIT'),
    ('U JOINT', 'TRANSMISSION', 'PROPELLER SHAFT', 'UNIVERSAL JOINT KIT'),
    ('PROPELLER SHAFT', 'TRANSMISSION', 'PROPELLER SHAFT', 'PROPELLER SHAFT ASSY'),
    ('AXLE', 'TRANSMISSION', 'AXLE SHAFT', 'REAR AXLE SHAFT'),

    # COOLING SYSTEM & HOSES
    ('RADIATOR', 'COOLING SYSTEM', 'RADIATOR & FLUIDS', 'RADIATOR ASSEMBLY'),
    ('COOLANT', 'COOLING SYSTEM', 'RADIATOR & FLUIDS', 'ENGINE COOLANT'),
    ('WATER PUMP', 'COOLING SYSTEM', 'WATER PUMP', 'WATER PUMP ASSEMBLY'),
    ('THERMOSTAT', 'COOLING SYSTEM', 'THERMOSTAT', 'THERMOSTAT VALVE'),
    ('HOSE', 'RUBBERS HOSES AND MOUNTINGS', 'HOSES', 'COOLANT & HEATER HOSE'),
    ('PIPE', 'COOLING SYSTEM', 'PIPES', 'COOLANT PIPE'),

    # HVAC / THERMAL
    ('COMPRESSOR', 'HVAC/THERMAL', 'COMPRESSOR', 'AC COMPRESSOR'),
    ('CONDENSER', 'HVAC/THERMAL', 'CONDENSER', 'AC CONDENSER'),
    ('EVAPORATOR', 'HVAC/THERMAL', 'EVAPORATOR', 'AC EVAPORATOR CORE'),
    ('BLOWER', 'HVAC/THERMAL', 'BLOWER MOTOR', 'AC BLOWER MOTOR'),
    ('EXPANSION VALVE', 'HVAC/THERMAL', 'VALVE', 'AC EXPANSION VALVE'),

    # ELECTRICALS AND ELECTRONICS
    ('ALTERNATOR', 'ELECTRICALS AND ELECTRONICS', 'ROTATING MACHINE', 'ALTERNATOR ASSEMBLY'),
    ('STARTER MOTOR', 'ELECTRICALS AND ELECTRONICS', 'ROTATING MACHINE', 'STARTER MOTOR ASSEMBLY'),
    ('STARTER', 'ELECTRICALS AND ELECTRONICS', 'ROTATING MACHINE', 'STARTER MOTOR ASSEMBLY'),
    ('BATTERY', 'ELECTRICALS AND ELECTRONICS', 'BATTERY', 'CAR BATTERY'),
    ('SENSOR', 'ELECTRICALS AND ELECTRONICS', 'SENSORS', 'ENGINE SENSOR'),
    ('SWITCH', 'ELECTRICALS AND ELECTRONICS', 'SWITCHES', 'ELECTRICAL SWITCH'),
    ('RELAY', 'ELECTRICALS AND ELECTRONICS', 'RELAY AND FUSE', 'RELAY'),
    ('FUSE', 'ELECTRICALS AND ELECTRONICS', 'RELAY AND FUSE', 'FUSE'),
    ('HORN', 'ELECTRICALS AND ELECTRONICS', 'HORN', 'ELECTRIC HORN'),
    ('IGNITION COIL', 'ELECTRICALS AND ELECTRONICS', 'IGNITION SYSTEM', 'IGNITION COIL'),

    # WIPER SYSTEM
    ('WIPER BLADE', 'WIPER SYSTEM', 'WIPER BLADE', 'WIPER BLADE'),
    ('WIPER ARM', 'WIPER SYSTEM', 'WIPER ARM', 'WIPER ARM'),
    ('WIPER MOTOR', 'WIPER SYSTEM', 'WIPER MOTOR', 'WIPER MOTOR'),
    ('WIPER', 'WIPER SYSTEM', 'WIPER BLADE', 'WIPER BLADE'),

    # BELTS & TENSIONERS
    ('TIMING BELT', 'BELTS AND TENSIONER', 'TIMING BELT', 'TIMING BELT'),
    ('FAN BELT', 'BELTS AND TENSIONER', 'BELT', 'FAN BELT / V-BELT'),
    ('V BELT', 'BELTS AND TENSIONER', 'BELT', 'FAN BELT / V-BELT'),
    ('BELT', 'BELTS AND TENSIONER', 'BELT', 'SERPENTINE / DRIVE BELT'),
    ('TENSIONER', 'BELTS AND TENSIONER', 'TENSIONER', 'BELT TENSIONER PULLEY'),
    ('PULLEY', 'BELTS AND TENSIONER', 'PULLEY', 'ENGINE PULLEY'),

    # SEALS, GASKETS, CONSUMABLES, FASTENERS
    ('OIL SEAL', 'CHILD PARTS', 'SEALS & GASKETS', 'OIL SEAL'),
    ('GASKET', 'CHILD PARTS', 'SEALS & GASKETS', 'GASKET & SEALANT'),
    ('O-RING', 'CHILD PARTS', 'SEALS & GASKETS', 'O-RING SEAL'),
    ('ANABOND', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'GASKET & SEALANT'),
    ('SEALANT', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'GASKET & SEALANT'),
    ('GREASE', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'BEARING GREASE'),
    ('OIL', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'ENGINE OIL'),
    ('FLUID', 'PAINTS AND CONSUMABLES', 'CONSUMABLES', 'BRAKE FLUID'),
    ('BOLT', 'CHILD PARTS', 'BOLT & NUT', 'BOLT'),
    ('NUT', 'CHILD PARTS', 'BOLT & NUT', 'NUT'),
    ('WASHER', 'CHILD PARTS', 'BOLT & NUT', 'WASHER'),
    ('SCREW', 'CHILD PARTS', 'BOLT & NUT', 'SCREW'),
    ('FASTENER', 'CHILD PARTS', 'BOLT & NUT', 'HARDWARE & FASTENERS'),
    ('STUD', 'CHILD PARTS', 'BOLT & NUT', 'STUD')
]

# Build token lookup map excluding stop words
token_map = {}
for entry in master:
    comp = str(entry.get('component', '')).strip().upper()
    tokens = [t for t in re.findall(r'[A-Z0-9]{3,}', comp) if t not in STOP_WORDS]
    for tok in tokens:
        if tok not in token_map:
            token_map[tok] = entry

def map_single_row(pno, desc, brand):
    d_clean = re.sub(r'^[^\w]+', '', str(desc or '').upper()).strip()
    p_clean = re.sub(r'[^A-Z0-9]', '', str(pno or '').upper()).strip()

    # Priority 1: Domain Keyword Exact Match
    if d_clean:
        for kw, agg, sub_agg, comp in DOMAIN_KEYWORDS:
            if kw in d_clean:
                return (agg, sub_agg, comp, 'DOMAIN_KEYWORD_MATCH')

    # Priority 2: Token Index Matching (excluding stop words)
    if d_clean:
        tokens = [t for t in re.findall(r'[A-Z0-9]{3,}', d_clean) if t not in STOP_WORDS]
        for t in tokens:
            if t in token_map:
                m = token_map[t]
                return (m['aggregate'], m['subAggregate'], m['component'], 'TOKEN_MATCH')

    # Priority 3: General Spares Fallback (NO MORE BLIND BOLT FORCING!)
    return ('GENERAL SPARES', 'GENERAL', 'GENERAL SPARES', 'SMART_FALLBACK')

results = []
for r in records:
    # Try finding description column
    desc = r.get('Product_Description') or r.get('Item Name') or r.get('Description') or r.get('ItemDesc') or ''
    pno = r.get('Product_Number') or r.get('Item Code_rev') or r.get('Part Number') or r.get('ManPart') or ''
    brand = r.get('Brand_Name') or r.get('Brand') or r.get('Make') or ''

    if not desc:
        # Extract from object values
        vals = [str(v).strip() for k, v in r.items() if str(v).strip() and str(v).lower() != 'nan']
        desc_cand = next((v for v in vals if (' ' in v or len(v) > 8) and not v.isdigit()), None)
        if desc_cand: desc = desc_cand

    res = map_single_row(pno, desc, brand)
    results.append(res)

res_df = pd.DataFrame(results, columns=['Aggregate', 'SubAggregate', 'Component', 'Method'])

print("\n=== TOP 20 AGGREGATES ===")
print(res_df['Aggregate'].value_counts().head(20))

print("\n=== TOP 20 COMPONENTS ===")
print(res_df['Component'].value_counts().head(20))

print("\n=== METHOD BREAKDOWN ===")
print(res_df['Method'].value_counts())
