import json
import gzip
import re
import os

def sanitize_db():
    gz_path = os.path.join("data", "trained_mapping_db.json.gz")
    if not os.path.exists(gz_path):
        gz_path = "trained_mapping_db.json.gz"
    
    print(f"Loading database from {gz_path}...")
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        db = json.load(f)

    master = db.get("aggregateMaster", [])
    print(f"Total Aggregate Master entries: {len(master)}")

    # Map of UPPERCASE COMPONENT -> Official Master Dict
    master_comp_map = {}
    master_subagg_map = {}
    master_agg_map = {}

    for m in master:
        comp_upper = str(m.get("component", "")).strip().toUpperCase() if hasattr(str(m.get("component", "")), "toUpperCase") else str(m.get("component", "")).strip().upper()
        subagg_upper = str(m.get("subAggregate", "")).strip().upper()
        agg_upper = str(m.get("aggregate", "")).strip().upper()

        if comp_upper:
            master_comp_map[comp_upper] = m
        if subagg_upper and subagg_upper not in master_subagg_map:
            master_subagg_map[subagg_upper] = m
        if agg_upper and agg_upper not in master_agg_map:
            master_agg_map[agg_upper] = m

    lookup = db.get("partNoLookup", {})
    print(f"Total partNoLookup entries: {len(lookup)}")

    corrected_count = 0
    fuzzy_count = 0

    for pno, info in lookup.items():
        comp = str(info.get("comp", "")).strip().upper()
        
        # 1. Exact match in Master
        if comp in master_comp_map:
            m = master_comp_map[comp]
            info["comp"] = m["component"]
            info["agg"] = m["aggregate"]
            info["subAgg"] = m["subAggregate"]
            info["category"] = m["category"]
            continue

        # 2. Sanitization / Fuzzy matching for non-exact master components
        corrected_count += 1
        comp_clean = re.sub(r'\b(ASSY|ASSEMBLY|KIT|SET|RH|LH|REAR|FRONT)\b', '', comp).strip()
        
        match = None
        # Try substring match
        for m_comp, m_entry in master_comp_map.items():
            m_clean = re.sub(r'\b(ASSY|ASSEMBLY|KIT|SET|RH|LH|REAR|FRONT)\b', '', m_comp).strip()
            if comp_clean and (comp_clean in m_clean or m_clean in comp_clean):
                match = m_entry
                fuzzy_count += 1
                break
        
        if not match:
            sub = str(info.get("subAgg", "")).strip().upper()
            if sub in master_subagg_map:
                match = master_subagg_map[sub]

        if not match:
            agg = str(info.get("agg", "")).strip().upper()
            if agg in master_agg_map:
                match = master_agg_map[agg]

        if match:
            info["comp"] = match["component"]
            info["agg"] = match["aggregate"]
            info["subAgg"] = match["subAggregate"]
            info["category"] = match["category"]

    print(f"Sanitized {corrected_count} entries ({fuzzy_count} fuzzy matched).")
    
    # Save back to trained_mapping_db.json.gz and trained_mapping_db.json
    out_json = json.dumps(db, ensure_ascii=False)
    
    for target_dir in [".", "data"]:
        json_p = os.path.join(target_dir, "trained_mapping_db.json")
        gz_p = os.path.join(target_dir, "trained_mapping_db.json.gz")
        
        if os.path.exists(target_dir):
            with open(json_p, "w", encoding="utf-8") as f:
                f.write(out_json)
            with gzip.open(gz_p, "wt", encoding="utf-8") as f:
                f.write(out_json)
            print(f"Updated {json_p} and {gz_p}")

if __name__ == "__main__":
    sanitize_db()
