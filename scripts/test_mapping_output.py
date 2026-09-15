import pandas as pd

def simulate_data_engine(rawPartNo, description, brand):
    d = str(description or '').strip().upper()
    brand_upper = str(brand or '').strip().upper()

    if 'BRAKE SHOE' in d or 'DRUM BRAKE' in d:
        return {'agg': 'BRAKE SYSTEM', 'sub': 'DRUM BRAKE', 'comp': 'BRAKE SHOE', 'cat': 'Mechanical Parts'}
    if 'DISC PAD' in d or 'BRAKE PAD' in d:
        return {'agg': 'BRAKE SYSTEM', 'sub': 'DISC BRAKE', 'comp': 'BRAKE PAD', 'cat': 'Mechanical Parts'}
    if 'BRAKE ROTOR' in d or 'BRAKE DISC' in d:
        return {'agg': 'BRAKE SYSTEM', 'sub': 'DISC BRAKE', 'comp': 'BRAKE DISC / ROTOR', 'cat': 'Mechanical Parts'}
    if 'OIL SEAL' in d or 'WHEEL SEAL' in d:
        return {'agg': 'MECHANICAL AGGREGATES', 'sub': 'SEALS & GASKETS', 'comp': 'OIL SEAL', 'cat': 'Mechanical Parts'}
    if 'GASKET MAKER' in d or 'ANABOND' in d or 'GASKET' in d:
        return {'agg': 'MECHANICAL AGGREGATES', 'sub': 'SEALS & GASKETS', 'comp': 'GASKET & SEALANT', 'cat': 'Consumables'}
    if 'UNIVERSAL JOINT' in d or 'U JOINT' in d or 'U-JOINT' in d or 'U.J. KIT' in d:
        return {'agg': 'TRANSMISSION', 'sub': 'PROPELLER SHAFT', 'comp': 'UNIVERSAL JOINT KIT', 'cat': 'Mechanical Parts'}
    if 'HEATER HOSE' in d or 'HEATER OUTLET' in d or 'BOTTOM HOSE' in d or 'TOP HOSE' in d or 'HOSE' in d:
        return {'agg': 'COOLING SYSTEM', 'sub': 'RADIATOR & FLUIDS', 'comp': 'COOLANT & HEATER HOSE', 'cat': 'Consumables'}
    if 'RADIATOR' in d or 'COOLING FAN' in d:
        return {'agg': 'COOLING SYSTEM', 'sub': 'RADIATOR & FLUIDS', 'comp': 'RADIATOR ASSEMBLY', 'cat': 'Mechanical Parts'}
    if 'BALL JOINT' in d:
        return {'agg': 'SUSPENSION', 'sub': 'LINKAGE', 'comp': 'SUSPENSION BALL JOINT', 'cat': 'Mechanical Parts'}
    if 'STRUT' in d or 'SHOCK ABSORBER' in d:
        return {'agg': 'SUSPENSION', 'sub': 'STRUT ASSEMBLY', 'comp': 'FRONT SHOCK ABSORBER', 'cat': 'Mechanical Parts'}
    if 'HUB OUTER' in d or 'HUB INNER' in d or 'WHEEL HUB' in d or 'REAR HUB' in d:
        return {'agg': 'SUSPENSION', 'sub': 'WHEEL HUB', 'comp': 'WHEEL HUB ASSEMBLY', 'cat': 'Mechanical Parts'}
    if 'REAR WHEEL' in d or 'FRONT WHEEL' in d:
        return {'agg': 'SUSPENSION', 'sub': 'WHEEL HUB', 'comp': 'WHEEL BEARINGS & SEALS', 'cat': 'Mechanical Parts'}
    if 'STEERING BOOT' in d or 'STEERING RACK' in d:
        return {'agg': 'STEERING', 'sub': 'POWER STEERING', 'comp': 'STEERING RACK & BOOT', 'cat': 'Mechanical Parts'}
    if 'FOG LAMP' in d:
        return {'agg': 'ELECTRICALS AND ELECTRONICS', 'sub': 'LIGHTING', 'comp': 'FOG LAMP / LIGHT ASSEMBLY', 'cat': 'Electrical Parts'}
    if 'BULB' in d or 'LED' in d or 'W5W' in d:
        return {'agg': 'ELECTRICALS AND ELECTRONICS', 'sub': 'LIGHTING', 'comp': 'HEADLAMP BULB', 'cat': 'Electrical Parts'}
    if 'TUBE' in d or 'FLAP' in d or 'TYRE' in d:
        return {'agg': 'WHEELS & TIRES', 'sub': 'TUBES & FLAPS', 'comp': 'TIRE TUBE / FLAP', 'cat': 'Mechanical Parts'}
    if 'GEAR LEVER' in d or 'GEAR SHIFT' in d:
        return {'agg': 'TRANSMISSION', 'sub': 'CLUTCH ASSEMBLY', 'comp': 'GEAR SHIFT LEVER KIT', 'cat': 'Mechanical Parts'}
    if 'FUEL WATER SEPARATOR' in d or 'FUEL FILTER' in d:
        return {'agg': 'ENGINE', 'sub': 'FILTERS', 'comp': 'FUEL FILTER', 'cat': 'Consumables'}
    if 'OIL FILTER' in d:
        return {'agg': 'ENGINE', 'sub': 'FILTERS', 'comp': 'OIL FILTER', 'cat': 'Consumables'}
    if 'AIR FILTER' in d:
        return {'agg': 'ENGINE', 'sub': 'FILTERS', 'comp': 'AIR FILTER', 'cat': 'Consumables'}
    if 'FILTER' in d:
        return {'agg': 'ENGINE', 'sub': 'FILTERS', 'comp': 'OIL FILTER', 'cat': 'Consumables'}
    if 'PLUG' in d or 'SPARK' in d:
        return {'agg': 'ELECTRICALS AND ELECTRONICS', 'sub': 'IGNITION SYSTEM', 'comp': 'SPARK PLUG', 'cat': 'Electrical Parts'}
    if 'BELT' in d or 'TIMING' in d:
        return {'agg': 'BELTS AND TENSIONER', 'sub': 'TIMING BELT', 'comp': 'TIMING BELT', 'cat': 'Mechanical Parts'}

    return {'agg': 'CHILD PARTS', 'sub': 'BOLT & NUT', 'comp': 'HARDWARE & FASTENERS', 'cat': 'Mechanical Parts'}

df = pd.read_excel(r'C:\Users\SM0237\Downloads\Mapped_Catalogue_Output (5).xlsx')
print('=== SIMULATION VERIFICATION ===')
for idx, r in df.iterrows():
    m = simulate_data_engine(r['ManPart'], r['ItemDesc'], r['BRAND'])
    print(f"{idx+1:2d}. {str(r['ItemDesc']):<45} -> {m['agg']} / {m['sub']} / {m['comp']}")
