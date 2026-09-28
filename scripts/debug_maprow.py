import json, re

with open('data/aggregate_master_rules.json', 'r', encoding='utf-8') as f:
    master_rules = json.load(f)['aggregateMaster']

class DataEngineSim:
    def __init__(self, master_rules):
        self.db = {
            'aggregateMaster': master_rules,
            'tokenIndex': {},
            'partNoLookup': {}
        }
        self.buildFastTokenIndexes()

    def buildFastTokenIndexes(self):
        for entry in self.db['aggregateMaster']:
            comp = str(entry.get('component', '')).upper()
            tokens = [t for t in re.split(r'[^A-Z0-9]+', comp) if len(t) >= 3]
            for tok in tokens:
                if tok not in self.db['tokenIndex']:
                    self.db['tokenIndex'][tok] = entry['component']

    def mapRow(self, rawPartNo, description, brandInput=''):
        descUpper = str(description or '').strip().upper()
        brandUpper = str(brandInput or '').strip().upper()

        def findInMaster(compName):
            if not compName or not self.db['aggregateMaster']: return None
            target = str(compName).strip().upper()
            return next((m for m in self.db['aggregateMaster'] if str(m.get('component', '')).strip().upper() == target), None)

        if descUpper:
            d = descUpper
            if 'BRAKE SHOE' in d or 'DRUM BRAKE' in d: return 'BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE SHOE', 'DOMAIN'
            if 'DISC PAD' in d or 'BRAKE PAD' in d: return 'BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD', 'DOMAIN'

        # Strategy 3: TokenIndex
        if descUpper:
            tokens = [t for t in re.split(r'[^A-Z0-9]+', descUpper) if len(t) >= 4]
            for token in tokens:
                if token in self.db['tokenIndex']:
                    compMatch = self.db['tokenIndex'][token]
                    masterEntry = findInMaster(compMatch)
                    if masterEntry:
                        return masterEntry['aggregate'], masterEntry['subAggregate'], masterEntry['component'], 'STRATEGY_3'

        # Strategy 4: Fuzzy
        if descUpper and self.db['aggregateMaster']:
            descTokens = [t for t in re.split(r'[^A-Z0-9]+', descUpper) if len(t) >= 3]
            if descTokens:
                bestScore = 0
                bestEntry = None
                for entry in self.db['aggregateMaster']:
                    compUpper = str(entry.get('component', '')).upper()
                    subUpper = str(entry.get('subAggregate', '')).upper()
                    aggUpper = str(entry.get('aggregate', '')).upper()

                    score = 0
                    for dt in descTokens:
                        if dt in compUpper: score += 4
                        elif dt in subUpper: score += 2
                        elif dt in aggUpper: score += 1

                    if score > bestScore:
                        bestScore = score
                        bestEntry = entry

                if bestEntry and bestScore >= 1:
                    return bestEntry['aggregate'], bestEntry['subAggregate'], bestEntry['component'], 'STRATEGY_4'

        fb = findInMaster('BOLT') or {'aggregate': 'CHILD PARTS', 'subAggregate': 'BOLT & NUT', 'component': 'BOLT'}
        return fb['aggregate'], fb['subAggregate'], fb['component'], 'FALLBACK'

sim = DataEngineSim(master_rules)

test_descs = [
    'CED HOOD ASSEMBLY NEXON MCE',
    'HEADLAMP ASSY WITH CELAR LENS, LH',
    'FRONT BUMPER SKIN',
    'TOP FRILL FRONT BUMBER',
    'BOTTAM GRILL ASSY',
    'FENDER RH',
    'GRAINT_BLACK SIDE VALANCE COVER ASSY-RH',
    'BONNET HINGE LH',
    'BONNET HINGE RH',
    'BRACKET ASSY;FRONT BUMPER MTG;LH',
    '2214 GLASS HELLA TY M L',
    'SKD-RPD',
    'OIL SEAL REAR BEARING COVER'
]

for td in test_descs:
    agg, sub, comp, method = sim.mapRow('', td)
    print(f'"{td}" ==> {agg} | {sub} | {comp} ({method})')
