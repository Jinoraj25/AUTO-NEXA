import os
import sqlite3
import json
import csv
import io
import re
import difflib

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "overall_catalogue.db")

def get_db():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

_STATS_CACHE = None
_FILTERS_CACHE = None

def get_catalogue_stats():
    global _STATS_CACHE
    if _STATS_CACHE is not None:
        return _STATS_CACHE
    
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "catalogue_stats_cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                _STATS_CACHE = json.load(f)
                return _STATS_CACHE
        except Exception:
            pass

    conn = get_db()
    if not conn:
        return {
            "status": "ready",
            "totalRecords": 23671472,
            "totalParts": 416045,
            "totalBrands": 170,
            "totalMakes": 39,
            "totalModels": 504,
            "totalSegments": 4
        }
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM overall_catalogue")
        total_records = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT line_code_part_number) FROM overall_catalogue")
        total_parts = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT brand_name) FROM overall_catalogue")
        total_brands = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT vehicle_make) FROM overall_catalogue WHERE vehicle_make != ''")
        total_makes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT vehicle_model) FROM overall_catalogue WHERE vehicle_model != ''")
        total_models = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT vehicle_segment) FROM overall_catalogue WHERE vehicle_segment != ''")
        total_segments = cur.fetchone()[0]

        conn.close()
        _STATS_CACHE = {
            "status": "ready",
            "totalRecords": total_records,
            "totalParts": total_parts,
            "totalBrands": total_brands,
            "totalMakes": total_makes,
            "totalModels": total_models,
            "totalSegments": total_segments
        }
        return _STATS_CACHE
    except Exception as e:
        if conn: conn.close()
        return {
            "status": "ready",
            "totalRecords": 23671472,
            "totalParts": 416045,
            "totalBrands": 170,
            "totalMakes": 39,
            "totalModels": 504,
            "totalSegments": 4
        }

def get_catalogue_filters():
    global _FILTERS_CACHE
    if _FILTERS_CACHE is not None:
        return _FILTERS_CACHE

    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "catalogue_filters_cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                _FILTERS_CACHE = json.load(f)
                return _FILTERS_CACHE
        except Exception:
            pass

    conn = get_db()
    if not conn:
        return {"brands": [], "makes": [], "models": [], "segments": [], "aggregates": [], "sub_aggregates": [], "components": []}
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT DISTINCT brand_name FROM overall_catalogue WHERE brand_name IS NOT NULL AND brand_name != '' ORDER BY brand_name ASC")
        brands = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT vehicle_segment FROM overall_catalogue WHERE vehicle_segment IS NOT NULL AND vehicle_segment != '' ORDER BY vehicle_segment ASC")
        segments = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT vehicle_make FROM overall_catalogue WHERE vehicle_make IS NOT NULL AND vehicle_make != '' ORDER BY vehicle_make ASC")
        makes = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT aggregate FROM overall_catalogue WHERE aggregate IS NOT NULL AND aggregate != '' ORDER BY aggregate ASC")
        aggregates = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT sub_aggregate FROM overall_catalogue WHERE sub_aggregate IS NOT NULL AND sub_aggregate != '' ORDER BY sub_aggregate ASC")
        sub_aggregates = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT components FROM overall_catalogue WHERE components IS NOT NULL AND components != '' ORDER BY components ASC")
        components = [r[0] for r in cur.fetchall()]

        conn.close()
        _FILTERS_CACHE = {
            "brands": brands,
            "makes": makes,
            "segments": segments,
            "aggregates": aggregates,
            "sub_aggregates": sub_aggregates,
            "components": components
        }
        return _FILTERS_CACHE
    except Exception as e:
        if conn: conn.close()
        return {"brands": [], "makes": [], "models": [], "segments": [], "aggregates": [], "sub_aggregates": [], "components": [], "error": str(e)}

def get_vehicle_models(make=None):
    conn = get_db()
    if not conn: return []
    try:
        cur = conn.cursor()
        if make:
            cur.execute("SELECT DISTINCT vehicle_model FROM overall_catalogue WHERE vehicle_make = ? AND vehicle_model != '' ORDER BY vehicle_model ASC", (make,))
        else:
            cur.execute("SELECT DISTINCT vehicle_model FROM overall_catalogue WHERE vehicle_model != '' ORDER BY vehicle_model ASC LIMIT 200")
        models = [r[0] for r in cur.fetchall()]
        conn.close()
        return models
    except Exception:
        if conn: conn.close()
        return []

def get_sub_models(make=None, model=None, fuel_type=None, year=None):
    conn = get_db()
    if not conn: return []
    try:
        cur = conn.cursor()
        clauses = []
        params = []
        if make:
            clauses.append("vehicle_make = ?")
            params.append(make)
        if model:
            clauses.append("vehicle_model = ?")
            params.append(model)
        if fuel_type:
            clauses.append("(vehicle_fuel_type LIKE ? OR vehicle_sub_model LIKE ?)")
            params.append(f"%{fuel_type}%")
            params.append(f"%{fuel_type}%")
        if year:
            try:
                yr_val = int(year)
                clauses.append("((CAST(vehicle_from_year AS INTEGER) <= ? AND (CAST(vehicle_to_year AS INTEGER) >= ? OR vehicle_to_year = '' OR vehicle_to_year IS NULL)) OR vehicle_from_year = '' OR vehicle_from_year IS NULL)")
                params.append(yr_val)
                params.append(yr_val)
            except Exception:
                clauses.append("(vehicle_from_year LIKE ? OR vehicle_to_year LIKE ? OR vehicle_sub_model LIKE ?)")
                params.append(f"%{year}%")
                params.append(f"%{year}%")
                params.append(f"%{year}%")
        where_str = (" WHERE " + " AND ".join(clauses) + " AND vehicle_sub_model != ''") if clauses else " WHERE vehicle_sub_model != ''"
        cur.execute(f"SELECT DISTINCT vehicle_sub_model FROM overall_catalogue{where_str} ORDER BY vehicle_sub_model ASC LIMIT 250", params)
        sub_models = [r[0] for r in cur.fetchall()]
        conn.close()
        return sub_models
    except Exception:
        if conn: conn.close()
        return []

def get_sub_aggregates(aggregate=None):
    conn = get_db()
    if not conn: return []
    try:
        cur = conn.cursor()
        if aggregate:
            cur.execute("SELECT DISTINCT sub_aggregate FROM overall_catalogue WHERE aggregate = ? AND sub_aggregate != '' ORDER BY sub_aggregate ASC", (aggregate,))
        else:
            cur.execute("SELECT DISTINCT sub_aggregate FROM overall_catalogue WHERE sub_aggregate != '' ORDER BY sub_aggregate ASC LIMIT 300")
        sub_aggs = [r[0] for r in cur.fetchall()]
        conn.close()
        return sub_aggs
    except Exception:
        if conn: conn.close()
        return []

def get_components(aggregate=None, sub_aggregate=None):
    conn = get_db()
    if not conn: return []
    try:
        cur = conn.cursor()
        clauses = []
        params = []
        if aggregate:
            clauses.append("aggregate = ?")
            params.append(aggregate)
        if sub_aggregate:
            clauses.append("sub_aggregate = ?")
            params.append(sub_aggregate)
        
        where_str = (" WHERE " + " AND ".join(clauses) + " AND components != ''") if clauses else " WHERE components != ''"
        cur.execute(f"SELECT DISTINCT components FROM overall_catalogue{where_str} ORDER BY components ASC LIMIT 500", params)
        comps = [r[0] for r in cur.fetchall()]
        conn.close()
        return comps
    except Exception:
        if conn: conn.close()
        return []

# ==================== ORIPARTS VEHICLE IMAGE MAPPING & VISUAL NAVIGATOR ====================

_VEHICLE_IMAGES_INDEX = None

def get_vehicle_images_index():
    global _VEHICLE_IMAGES_INDEX
    if _VEHICLE_IMAGES_INDEX is not None:
        return _VEHICLE_IMAGES_INDEX
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "vehicles")
    index = {}
    if os.path.exists(base_dir):
        for make_folder in os.listdir(base_dir):
            mf_path = os.path.join(base_dir, make_folder)
            if os.path.isdir(mf_path) and not make_folder.startswith('.'):
                index[make_folder.upper()] = os.listdir(mf_path)
    _VEHICLE_IMAGES_INDEX = index
    return _VEHICLE_IMAGES_INDEX

def match_vehicle_image(make, model, sub_model, from_yr='', to_yr=''):
    img_index = get_vehicle_images_index()
    if not img_index:
        return "images/home_menu_catalogue.jpg"
    
    make_clean = (make or "").upper().strip()
    if make_clean == 'MARUTI': make_clean = 'MARUTI SUZUKI'
    if make_clean == 'VOLKSWAGEN': make_clean = 'VW'
    
    make_folder = None
    if make_clean in img_index:
        make_folder = make_clean
    else:
        for k in img_index:
            if k in make_clean or make_clean in k:
                make_folder = k
                break
    
    if not make_folder:
        return "images/home_menu_catalogue.jpg"
        
    imgs = img_index.get(make_folder, [])
    if not imgs:
        return "images/home_menu_catalogue.jpg"
        
    model_str = (model or "").strip()
    sub_str = (sub_model or "").strip()
    full_str = f"{model_str} {sub_str} {from_yr} {to_yr}".upper()
    tokens = [t for t in re.findall(r'[A-Za-z0-9]+', full_str) if len(t) >= 2]
    
    gen_match = re.search(r'([1-9](?:ST|ND|RD|TH)\s+GEN)', full_str)
    gen_str = gen_match.group(1) if gen_match else ''
    
    model_clean = model_str.upper().replace(' ', '')
    
    best_img = None
    best_score = -1
    
    for img in imgs:
        img_upper = img.upper()
        img_no_ext = os.path.splitext(img_upper)[0]
        
        # Must relate to model
        if model_str.upper() not in img_upper and model_clean not in img_upper.replace(' ', ''):
            continue
            
        score = 10
        if gen_str and gen_str in img_upper:
            score += 25
        if 'F_L' in img_upper and ('F/L' in sub_str.upper() or 'FACELIFT' in sub_str.upper()):
            score += 15
        
        # Check year overlap
        yr_matches = re.findall(r'(\d{4})', img_upper)
        if yr_matches and from_yr:
            try:
                img_from = int(yr_matches[0])
                img_to = int(yr_matches[1]) if len(yr_matches) > 1 else 9999
                q_yr = int(from_yr)
                if img_from <= q_yr <= img_to:
                    score += 30
            except Exception:
                pass
                
        img_tokens = set(re.findall(r'[A-Za-z0-9]+', img_no_ext))
        score += len(set(tokens).intersection(img_tokens)) * 2
        
        if score > best_score:
            best_score = score
            best_img = f"images/vehicles/{make_folder}/{img}"
            
    if not best_img:
        for img in imgs:
            if model_str.upper() in img.upper():
                return f"images/vehicles/{make_folder}/{img}"
        if imgs:
            best_img = f"images/vehicles/{make_folder}/{imgs[0]}"
            
    return best_img or "images/home_menu_catalogue.jpg"

_MAKES_CATALOG_CACHE = None

def get_makes_catalog():
    global _MAKES_CATALOG_CACHE
    if _MAKES_CATALOG_CACHE is not None:
        return _MAKES_CATALOG_CACHE
    
    stats_data = [
        {"make": "MARUTI SUZUKI", "displayName": "Maruti Suzuki", "logo": "images/makes/maruti.png", "modelsCount": 45, "variantsCount": 1491, "popular": True, "segment": "PCV"},
        {"make": "HYUNDAI", "displayName": "Hyundai", "logo": "images/makes/hyundai.png", "modelsCount": 24, "variantsCount": 1590, "popular": True, "segment": "PCV"},
        {"make": "TATA", "displayName": "Tata Motors", "logo": "images/makes/tata.png", "modelsCount": 51, "variantsCount": 3584, "popular": True, "segment": "PCV/HCV"},
        {"make": "MAHINDRA", "displayName": "Mahindra", "logo": "images/makes/mahindra.png", "modelsCount": 67, "variantsCount": 1235, "popular": True, "segment": "SUV/LCV"},
        {"make": "TOYOTA", "displayName": "Toyota", "logo": "images/makes/toyota.png", "modelsCount": 24, "variantsCount": 619, "popular": True, "segment": "PCV"},
        {"make": "HONDA", "displayName": "Honda", "logo": "images/makes/honda.png", "modelsCount": 12, "variantsCount": 433, "popular": True, "segment": "PCV"},
        {"make": "FORD", "displayName": "Ford", "logo": "images/makes/ford.png", "modelsCount": 11, "variantsCount": 418, "popular": True, "segment": "PCV"},
        {"make": "VOLKSWAGEN", "displayName": "Volkswagen", "logo": "images/makes/volkswagen.jpg", "modelsCount": 14, "variantsCount": 157, "popular": True, "segment": "PCV"},
        {"make": "SKODA", "displayName": "Skoda", "logo": "images/makes/skoda.jpg", "modelsCount": 11, "variantsCount": 283, "popular": True, "segment": "PCV"},
        {"make": "RENAULT", "displayName": "Renault", "logo": "images/makes/renault.png", "modelsCount": 11, "variantsCount": 145, "popular": True, "segment": "PCV"},
        {"make": "NISSAN", "displayName": "Nissan", "logo": "images/makes/nissan.png", "modelsCount": 12, "variantsCount": 80, "popular": True, "segment": "PCV"},
        {"make": "KIA", "displayName": "Kia Motors", "logo": "images/makes/kia.png", "modelsCount": 7, "variantsCount": 159, "popular": True, "segment": "PCV"},
        {"make": "MORRIS GARAGES", "displayName": "MG Motors", "logo": "images/makes/mg.png", "modelsCount": 10, "variantsCount": 312, "popular": True, "segment": "PCV/EV"},
        {"make": "BMW", "displayName": "BMW", "logo": "images/makes/bmw.png", "modelsCount": 22, "variantsCount": 166, "popular": False, "segment": "Luxury"},
        {"make": "MERCEDES-BENZ", "displayName": "Mercedes-Benz", "logo": "images/makes/mercedes.jpg", "modelsCount": 24, "variantsCount": 330, "popular": False, "segment": "Luxury"},
        {"make": "AUDI", "displayName": "Audi", "logo": "images/makes/audi.png", "modelsCount": 17, "variantsCount": 359, "popular": False, "segment": "Luxury"},
        {"make": "FORCE", "displayName": "Force Motors", "logo": "images/makes/force.png", "modelsCount": 11, "variantsCount": 94, "popular": False, "segment": "LCV"},
        {"make": "JEEP", "displayName": "Jeep", "logo": "images/makes/jeep.png", "modelsCount": 4, "variantsCount": 55, "popular": False, "segment": "SUV"},
        {"make": "CHEVROLET", "displayName": "Chevrolet", "logo": "images/makes/chevrolet.png", "modelsCount": 15, "variantsCount": 78, "popular": False, "segment": "PCV"},
        {"make": "FIAT", "displayName": "Fiat", "logo": "images/makes/fiat.jpg", "modelsCount": 16, "variantsCount": 125, "popular": False, "segment": "PCV"},
        {"make": "ASHOK LEYLAND", "displayName": "Ashok Leyland", "logo": "images/makes/ashok_leyland.png", "modelsCount": 6, "variantsCount": 25, "popular": False, "segment": "CV"},
        {"make": "VOLVO", "displayName": "Volvo", "logo": "images/makes/volvo.png", "modelsCount": 9, "variantsCount": 30, "popular": False, "segment": "Luxury"},
        {"make": "ISUZU", "displayName": "Isuzu", "logo": "images/makes/isuzu.png", "modelsCount": 5, "variantsCount": 22, "popular": False, "segment": "LCV"},
        {"make": "DATSUN", "displayName": "Datsun", "logo": "images/makes/datsun.jpg", "modelsCount": 4, "variantsCount": 48, "popular": False, "segment": "PCV"}
    ]
    _MAKES_CATALOG_CACHE = stats_data
    return _MAKES_CATALOG_CACHE

def get_visual_variants(make, model=None, fuel_type=None, year=None, search=None, limit=120):
    conn = get_db()
    if not conn: return {"variants": [], "models": [], "totalCount": 0}
    try:
        cur = conn.cursor()
        
        # Model pills
        make_clauses = ["(vehicle_make = ? OR vehicle_make = ?)"]
        make_params = [make, make]
        if make == "MARUTI" or make == "MARUTI SUZUKI":
            make_clauses = ["(vehicle_make = 'MARUTI' OR vehicle_make = 'MARUTI SUZUKI')"]
            make_params = []
        elif make == "VOLKSWAGEN" or make == "VW":
            make_clauses = ["(vehicle_make = 'VOLKSWAGEN' OR vehicle_make = 'VW')"]
            make_params = []
            
        cur.execute(f"SELECT DISTINCT vehicle_model FROM overall_catalogue WHERE {' AND '.join(make_clauses)} AND vehicle_model != '' ORDER BY vehicle_model ASC", make_params)
        all_models = [r[0] for r in cur.fetchall()]
        
        # Build variant query with cascading filters
        clauses = list(make_clauses)
        params = list(make_params)
        
        if model:
            clauses.append("vehicle_model = ?")
            params.append(model)
            
        if fuel_type:
            clauses.append("(vehicle_fuel_type LIKE ? OR vehicle_sub_model LIKE ?)")
            params.append(f"%{fuel_type}%")
            params.append(f"%{fuel_type}%")
            
        if year:
            try:
                yr_int = int(year)
                clauses.append("((CAST(vehicle_from_year AS INTEGER) <= ? AND (CAST(vehicle_to_year AS INTEGER) >= ? OR vehicle_to_year = '' OR vehicle_to_year IS NULL)) OR vehicle_from_year = '' OR vehicle_from_year IS NULL)")
                params.append(yr_int)
                params.append(yr_int)
            except Exception:
                clauses.append("(vehicle_from_year LIKE ? OR vehicle_to_year LIKE ? OR vehicle_sub_model LIKE ?)")
                params.append(f"%{year}%")
                params.append(f"%{year}%")
                params.append(f"%{year}%")
                
        if search:
            clean_s = search.strip()
            if clean_s:
                clauses.append("(vehicle_sub_model LIKE ? OR vehicle_model LIKE ?)")
                params.append(f"%{clean_s}%")
                params.append(f"%{clean_s}%")
                
        clauses.append("vehicle_sub_model != ''")
        where_str = " WHERE " + " AND ".join(clauses)
        
        cur.execute(f"""
            SELECT DISTINCT vehicle_model, vehicle_sub_model, vehicle_fuel_type, vehicle_from_year, vehicle_to_year
            FROM overall_catalogue
            {where_str}
            ORDER BY vehicle_model ASC, vehicle_from_year DESC, vehicle_sub_model ASC
            LIMIT ?
        """, params + [limit])
        
        raw_rows = cur.fetchall()
        conn.close()
        
        variants = []
        for r in raw_rows:
            v_model = r["vehicle_model"] or ""
            v_sub = r["vehicle_sub_model"] or ""
            v_fuel = r["vehicle_fuel_type"] or "PETROL"
            from_yr = r["vehicle_from_year"] or ""
            to_yr = r["vehicle_to_year"] or ""
            
            yrs_str = ""
            if from_yr or to_yr:
                yrs_str = f"{from_yr} - {to_yr or 'Present'}".strip()
                
            img_url = match_vehicle_image(make, v_model, v_sub, from_yr, to_yr)
            
            variants.append({
                "make": make,
                "model": v_model,
                "subModel": v_sub,
                "fuelType": v_fuel,
                "fromYear": from_yr,
                "toYear": to_yr,
                "years": yrs_str,
                "image": img_url
            })
            
        return {
            "variants": variants,
            "models": all_models,
            "totalCount": len(variants)
        }
    except Exception as e:
        if conn: conn.close()
        return {"variants": [], "models": [], "totalCount": 0, "error": str(e)}

AGGREGATE_ICONS = {
    "BRAKE SYSTEM": "🛑",
    "ENGINE": "⚙️",
    "SUSPENSION": "🛞",
    "CLUTCH SYSTEM": "🔄",
    "ELECTRICALS AND ELECTRONICS": "⚡",
    "FILTERS": "🛢️",
    "HVAC/THERMAL": "❄️",
    "BODY PARTS": "🚗",
    "TRANSMISSION": "🔄",
    "STEERING": "🛞",
    "LIGHTING": "💡",
    "FLUIDS COOLANT AND GREASE": "🛢️",
    "CHILD PARTS": "🧩",
    "CABLES AND WIRES": "🔌",
    "BELTS AND TENSIONER": "🎗️",
    "BEARING": "⚙️",
    "BATTERY": "🔋",
    "ACCESSORIES": "✨",
    "PAINTS AND CONSUMABLES": "🎨",
    "RUBBERS HOSES AND MOUNTINGS": "〰️",
    "WHEELS AND TYRES": "🛞",
    "WIPER SYSTEM": "🌧️",
    "GLASS": "🪟",
    "HORNS": "📢",
    "FUEL SYSTEM": "⛽",
    "INTERIOR AND COMFORTS": "💺",
    "LUBES": "🛢️"
}

def get_taxonomy_hierarchy(make=None, model=None, sub_model=None, aggregate=None, sub_aggregate=None):
    conn = get_db()
    if not conn: return {"items": []}
    try:
        cur = conn.cursor()
        base_clauses = []
        base_params = []
        if make:
            if make in ("MARUTI", "MARUTI SUZUKI"):
                base_clauses.append("(vehicle_make = 'MARUTI' OR vehicle_make = 'MARUTI SUZUKI')")
            elif make in ("VOLKSWAGEN", "VW"):
                base_clauses.append("(vehicle_make = 'VOLKSWAGEN' OR vehicle_make = 'VW')")
            else:
                base_clauses.append("vehicle_make = ?")
                base_params.append(make)
        if model:
            base_clauses.append("vehicle_model = ?")
            base_params.append(model)
            
        clauses = list(base_clauses)
        params = list(base_params)
        if sub_model:
            sub_model_clean = sub_model.strip()
            if make and sub_model_clean.upper().startswith(make.upper()):
                sub_model_clean = sub_model_clean[len(make):].strip()
            clauses.append("(vehicle_sub_model = ? OR vehicle_sub_model = ?)")
            params.extend([sub_model.strip(), sub_model_clean])
            
        where_base = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        
        # Case 1: Components under sub-aggregate
        if sub_aggregate:
            sub_clauses = list(clauses)
            sub_params = list(params)
            if aggregate:
                sub_clauses.append("aggregate = ?")
                sub_params.append(aggregate)
            sub_clauses.append("sub_aggregate = ?")
            sub_params.append(sub_aggregate)
            sub_clauses.append("components != ''")
            
            cur.execute(f"""
                SELECT components, COUNT(*) as cnt
                FROM overall_catalogue
                WHERE {' AND '.join(sub_clauses)}
                GROUP BY components
                ORDER BY cnt DESC
                LIMIT 150
            """, sub_params)
            rows = cur.fetchall()

            # Platform fallback if specific submodel has 0 components for this sub-aggregate
            if not rows and sub_model and model:
                model_sub_clauses = list(base_clauses)
                model_sub_params = list(base_params)
                if aggregate:
                    model_sub_clauses.append("aggregate = ?")
                    model_sub_params.append(aggregate)
                model_sub_clauses.append("sub_aggregate = ?")
                model_sub_params.append(sub_aggregate)
                model_sub_clauses.append("components != ''")
                cur.execute(f"""
                    SELECT components, COUNT(*) as cnt
                    FROM overall_catalogue
                    WHERE {' AND '.join(model_sub_clauses)}
                    GROUP BY components
                    ORDER BY cnt DESC
                    LIMIT 150
                """, model_sub_params)
                rows = cur.fetchall()

            conn.close()
            return {
                "level": "component",
                "items": [{"name": r[0], "component": r[0], "count": r[1]} for r in rows]
            }
            
        # Case 2: Sub-aggregates under aggregate
        if aggregate:
            agg_clauses = list(clauses)
            agg_params = list(params)
            agg_clauses.append("aggregate = ?")
            agg_params.append(aggregate)
            agg_clauses.append("sub_aggregate != ''")
            
            cur.execute(f"""
                SELECT sub_aggregate, COUNT(*) as cnt
                FROM overall_catalogue
                WHERE {' AND '.join(agg_clauses)}
                GROUP BY sub_aggregate
                ORDER BY cnt DESC
                LIMIT 100
            """, agg_params)
            rows = cur.fetchall()

            # Platform fallback if specific submodel has 0 sub-aggregates for this aggregate
            if not rows and sub_model and model:
                model_agg_clauses = list(base_clauses)
                model_agg_params = list(base_params)
                model_agg_clauses.append("aggregate = ?")
                model_agg_params.append(aggregate)
                model_agg_clauses.append("sub_aggregate != ''")
                cur.execute(f"""
                    SELECT sub_aggregate, COUNT(*) as cnt
                    FROM overall_catalogue
                    WHERE {' AND '.join(model_agg_clauses)}
                    GROUP BY sub_aggregate
                    ORDER BY cnt DESC
                    LIMIT 100
                """, model_agg_params)
                rows = cur.fetchall()

            conn.close()
            return {
                "level": "sub_aggregate",
                "items": [{"name": r[0], "subAggregate": r[0], "count": r[1]} for r in rows]
            }
            
        # Case 3: Top-level Aggregates
        cur.execute(f"""
            SELECT aggregate, COUNT(*) as cnt
            FROM overall_catalogue
            {where_base} {'AND' if where_base else 'WHERE'} aggregate != ''
            GROUP BY aggregate
            ORDER BY cnt DESC
            LIMIT 40
        """, params)
        rows = cur.fetchall()
        
        items = []
        existing_aggs = set()
        for r in rows:
            agg_name = r[0]
            cnt = r[1]
            existing_aggs.add(agg_name)
            icon = AGGREGATE_ICONS.get(agg_name, "📦")
            items.append({
                "name": agg_name,
                "aggregate": agg_name,
                "count": cnt,
                "icon": icon,
                "exactTrim": True
            })

        # If submodel has fewer than 8 aggregates (like commercial fleet trims e.g. Tour S),
        # supplement with platform-level common aggregates (Brakes, Filters, Suspension, Engine, etc.)
        if len(items) < 8 and model:
            where_model = (" WHERE " + " AND ".join(base_clauses)) if base_clauses else ""
            cur.execute(f"""
                SELECT aggregate, COUNT(*) as cnt
                FROM overall_catalogue
                {where_model} {'AND' if where_model else 'WHERE'} aggregate != ''
                GROUP BY aggregate
                ORDER BY cnt DESC
                LIMIT 30
            """, base_params)
            for r in cur.fetchall():
                agg_name = r[0]
                if agg_name not in existing_aggs:
                    cnt = r[1]
                    existing_aggs.add(agg_name)
                    icon = AGGREGATE_ICONS.get(agg_name, "📦")
                    items.append({
                        "name": agg_name,
                        "aggregate": agg_name,
                        "count": cnt,
                        "icon": icon,
                        "sharedPlatform": True
                    })

        conn.close()
            
        return {
            "level": "aggregate",
            "items": items,
            "hasSharedPlatform": any(it.get("sharedPlatform") for it in items)
        }
    except Exception as e:
        if conn: conn.close()
        return {"level": "error", "items": [], "error": str(e)}

def get_part_suggestions(q, limit=8):
    if not q or len(q.strip()) < 2:
        return []
    conn = get_db()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        raw_q = q.strip()
        clean_q = re.sub(r'[^A-Za-z0-9]', '', raw_q).upper()
        tokens = [t for t in re.findall(r'[A-Za-z0-9]+', raw_q) if len(t) >= 2]
        
        fts_terms = []
        if len(tokens) > 1:
            fts_terms.append(' '.join([f'{t}*' for t in tokens]))
        elif clean_q:
            fts_terms.append(f'{clean_q}*')
            for lc in ['216', '101', '103', '201', '419', '801', '190', '138']:
                fts_terms.append(f'{lc}{clean_q}*')
                
        match_query = ' OR '.join(fts_terms) if fts_terms else clean_q
        rows = []
        try:
            cur.execute(f"""
                SELECT c.id, c.line_code, c.line_code_part_number, c.part_description,
                       c.brand_name, c.aggregate, c.sub_aggregate, c.components,
                       c.mrp_price, c.list_price, c.vehicle_make, c.vehicle_model, c.vehicle_sub_model
                FROM overall_catalogue_fts f
                JOIN overall_catalogue c ON f.rowid = c.id
                WHERE overall_catalogue_fts MATCH ?
                GROUP BY c.line_code_part_number
                ORDER BY CASE WHEN c.mrp_price > 0 THEN 0 ELSE 1 END, c.id ASC
                LIMIT ?
            """, (match_query, limit))
            rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            rows = []
        
        if len(rows) < limit and clean_q:
            existing_parts = {r['line_code_part_number'] for r in rows}
            cur.execute("""
                SELECT id, line_code, line_code_part_number, part_description,
                       brand_name, aggregate, sub_aggregate, components,
                       mrp_price, list_price, vehicle_make, vehicle_model, vehicle_sub_model
                FROM overall_catalogue
                WHERE line_code_part_number LIKE ? OR line_code_part_number LIKE ?
                LIMIT ?
            """, (f"{clean_q}%", f"%{clean_q}%", limit - len(rows)))
            for r in cur.fetchall():
                dict_r = dict(r)
                if dict_r['line_code_part_number'] not in existing_parts:
                    rows.append(dict_r)
                    existing_parts.add(dict_r['line_code_part_number'])
                    
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "lineCode": r.get("line_code") or "",
                "partNo": r["line_code_part_number"],
                "desc": r.get("part_description") or "",
                "brand": r.get("brand_name") or "GENERIC",
                "aggregate": r.get("aggregate") or "SPARE PART",
                "subAggregate": r.get("sub_aggregate") or "",
                "component": r.get("components") or "",
                "mrp": float(r.get("mrp_price") or 0),
                "listPrice": float(r.get("list_price") or 0),
                "make": r.get("vehicle_make") or "",
                "model": r.get("vehicle_model") or "",
                "subModel": r.get("vehicle_sub_model") or ""
            })
        return results
    except Exception as e:
        if conn: conn.close()
        return []

def fuzzy_match_variant_in_db(cur, make, model, raw_variant="", fuel_type="", year=""):
    """
    Given a Vahan raw make, model, and variant string (e.g., 'THAR LX 4WD AT 2022' or 'SWIFT VXI BS6'),
    filters candidate variants in overall_catalogue.db under (make, model) and fuzzy matches
    to find the best existing vehicle_sub_model in our 22.7M catalogue database.
    """
    if not make or not model:
        return raw_variant, 0.0

    make_clean = make.strip().upper()
    model_clean = model.strip().upper()

    cur.execute("""
        SELECT DISTINCT vehicle_sub_model, vehicle_fuel_type, vehicle_from_year, vehicle_to_year
        FROM overall_catalogue 
        WHERE vehicle_make = ? AND vehicle_model = ? AND vehicle_sub_model != ''
    """, (make_clean, model_clean))
    
    candidates = cur.fetchall()
    if not candidates:
        cur.execute("""
            SELECT DISTINCT vehicle_sub_model, vehicle_fuel_type, vehicle_from_year, vehicle_to_year
            FROM overall_catalogue 
            WHERE vehicle_make LIKE ? AND vehicle_model LIKE ? AND vehicle_sub_model != ''
        """, (f"%{make_clean}%", f"%{model_clean}%"))
        candidates = cur.fetchall()

    if not candidates:
        return raw_variant, 0.0

    if not raw_variant:
        for c in candidates:
            if fuel_type and c[1] and fuel_type.upper() in c[1].upper():
                return c[0], 0.8
        return candidates[0][0], 0.5

    raw_clean = raw_variant.strip().upper()
    raw_tokens = set(re.findall(r'[A-Za-z0-9]+', raw_clean))

    best_variant = candidates[0][0]
    best_score = -1.0

    for cand_sub, cand_fuel, cand_from_yr, cand_to_yr in candidates:
        cand_clean = cand_sub.upper()
        cand_tokens = set(re.findall(r'[A-Za-z0-9]+', cand_clean))
        
        if not cand_tokens:
            continue

        common = raw_tokens.intersection(cand_tokens)
        token_score = len(common) / max(len(raw_tokens), len(cand_tokens))
        seq_score = difflib.SequenceMatcher(None, raw_clean, cand_clean).ratio()

        combined_score = (token_score * 0.6) + (seq_score * 0.4)

        if fuel_type and cand_fuel and fuel_type.upper() in cand_fuel.upper():
            combined_score += 0.12

        if year and cand_from_yr and cand_to_yr:
            try:
                y = int(year)
                f_yr = int(cand_from_yr) if str(cand_from_yr).isdigit() else 1990
                t_yr = int(cand_to_yr) if str(cand_to_yr).isdigit() else 2030
                if f_yr <= y <= t_yr:
                    combined_score += 0.08
            except ValueError:
                pass

        if combined_score > best_score:
            best_score = combined_score
            best_variant = cand_sub

    return best_variant, round(best_score, 3)

def vahan_rc_lookup(reg_no, api_key=None, api_url=None):
    """
    Vahan RC Lookup engine supporting Live Vahan API (RapidAPI / Surepass / APISetu),
    RTO Resolver, and 22.7M Catalogue DB Fuzzy Variant Matcher.
    """
    if not reg_no:
        return {"status": "error", "message": "Registration number required"}
    
    clean_reg = re.sub(r'[^A-Za-z0-9]', '', reg_no).upper()
    if len(clean_reg) < 3:
        return {"status": "error", "message": "Please enter a valid vehicle number or model name (e.g. TN06AM1234, i10)"}

    conn = get_db()
    if not conn:
        return {"status": "error", "message": "Database offline"}

    try:
        cur = conn.cursor()
        
        # Check for external Vahan API credentials (passed in or set in environment)
        vahan_api_key = api_key or os.environ.get("VAHAN_API_KEY") or os.environ.get("SUREPASS_API_KEY") or os.environ.get("RAPIDAPI_KEY")
        vahan_api_url = api_url or os.environ.get("VAHAN_API_URL") or "https://api.surepass.io/api/v1/rc/rc-full"
        
        v_make = ""
        v_model = ""
        v_variant = ""
        v_fuel = ""
        v_year = ""
        v_source = "Smart RTO Resolver & Catalog Matcher"

        if vahan_api_key:
            try:
                import urllib.request, urllib.parse, ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                if "rapidapi.com" in vahan_api_url.lower():
                    req_url = f"{vahan_api_url}?reg_no={urllib.parse.quote(clean_reg)}"
                    headers = {
                        "x-rapidapi-key": vahan_api_key,
                        "x-rapidapi-host": urllib.parse.urlparse(vahan_api_url).netloc,
                        "User-Agent": "AUTO-NEXA/1.0"
                    }
                    req = urllib.request.Request(req_url, headers=headers, method="GET")
                else:
                    payload = json.dumps({"id_number": clean_reg, "vehicle_number": clean_reg}).encode('utf-8')
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {vahan_api_key}",
                        "User-Agent": "AUTO-NEXA/1.0"
                    }
                    req = urllib.request.Request(vahan_api_url, data=payload, headers=headers, method="POST")

                with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
                    api_res = json.loads(response.read().decode('utf-8'))
                    r_data = api_res.get("data", api_res)

                    v_make = r_data.get("maker_name") or r_data.get("make") or r_data.get("brand", "")
                    v_model = r_data.get("maker_model") or r_data.get("model", "")
                    v_variant = r_data.get("variant") or r_data.get("maker_description", "")
                    v_fuel = r_data.get("fuel_type") or r_data.get("fuel", "")
                    raw_yr = r_data.get("reg_date") or r_data.get("manufacture_date") or r_data.get("year", "")
                    v_year = str(raw_yr)[:4] if raw_yr else ""
                    v_source = "Live MoRTH Vahan API"
            except Exception as api_err:
                print("Live Vahan API request failed, falling back to Smart RTO Resolver:", api_err)

        # Smart Keyword & Model Detector (e.g. if input contains i10, creta, swift, baleno, thar, nexon, etc.)
        raw_upper = reg_no.upper()
        model_keywords = [
            ("GRAND I10 NIOS", "HYUNDAI", "GRAND I10 NIOS", "GRAND I10 NIOS 1ST GEN 1.2L SPORTZ AMT", "PETROL", "2021"),
            ("GRAND I10", "HYUNDAI", "GRAND I10", "GRAND I10 1ST GEN F/L 1.2L SPORTZ", "PETROL", "2018"),
            ("I10", "HYUNDAI", "I10", "I10 1ST GEN F/L 1.1L ERA", "PETROL", "2014"),
            ("I20", "HYUNDAI", "I20", "I20 3RD GEN 1.2L ASTA(O)", "PETROL", "2021"),
            ("CRETA", "HYUNDAI", "CRETA", "CRETA 1ST GEN 5DR 1.6 SX CRDI VGT", "DIESEL", "2020"),
            ("VENUE", "HYUNDAI", "VENUE", "VENUE 1.2L KAPPA S", "PETROL", "2021"),
            ("VERNA", "HYUNDAI", "VERNA", "VERNA 1.6L SX CRDI", "DIESEL", "2019"),
            ("SWIFT", "MARUTI SUZUKI", "SWIFT", "SWIFT 3RD GEN 1.2L VXI", "PETROL", "2020"),
            ("BALENO", "MARUTI SUZUKI", "BALENO", "BALENO 1.2L DELTA", "PETROL", "2021"),
            ("BREZZA", "MARUTI SUZUKI", "VITARA BREZZA", "VITARA BREZZA 1.3L VDI", "DIESEL", "2019"),
            ("ALTO", "MARUTI SUZUKI", "ALTO 800", "ALTO 800 LXI", "PETROL", "2018"),
            ("WAGON R", "MARUTI SUZUKI", "WAGON R", "WAGON R 1.2L VXI", "PETROL", "2020"),
            ("WAGONR", "MARUTI SUZUKI", "WAGON R", "WAGON R 1.2L VXI", "PETROL", "2020"),
            ("DZIRE", "MARUTI SUZUKI", "DZIRE", "DZIRE 3RD GEN 1.2L VXI", "PETROL", "2021"),
            ("ERTIGA", "MARUTI SUZUKI", "ERTIGA", "ERTIGA 1.5L VXI", "PETROL", "2021"),
            ("CELERIO", "MARUTI SUZUKI", "CELERIO", "CELERIO 1.0L VXI", "PETROL", "2019"),
            ("THAR", "MAHINDRA", "THAR", "THAR 2ND GEN 2.0L LX 4S HT 4WD AT", "PETROL", "2022"),
            ("SCORPIO", "MAHINDRA", "SCORPIO", "SCORPIO CLASSIC S11", "DIESEL", "2022"),
            ("XUV700", "MAHINDRA", "XUV 700", "XUV700 AX7 L DIESEL AT", "DIESEL", "2022"),
            ("XUV300", "MAHINDRA", "XUV 300", "XUV300 1.2L W8", "PETROL", "2021"),
            ("BOLERO", "MAHINDRA", "BOLERO", "BOLERO B6 OPTIONAL", "DIESEL", "2020"),
            ("NEXON", "TATA", "NEXON", "NEXON 1.5L DARK EDITION XZ+", "DIESEL", "2022"),
            ("HARRIER", "TATA", "HARRIER", "HARRIER 2.0L XZA+", "DIESEL", "2021"),
            ("SAFARI", "TATA", "SAFARI", "SAFARI 2.0L XZA+", "DIESEL", "2021"),
            ("TIAGO", "TATA", "TIAGO", "TIAGO 1.2L XZ+", "PETROL", "2020"),
            ("ALTROZ", "TATA", "ALTROZ", "ALTROZ 1.2L XZ", "PETROL", "2021"),
            ("INNOVA", "TOYOTA", "INNOVA CRYSTA", "INNOVA CRYSTA 3RD GEN 2.4L VX", "DIESEL", "2021"),
            ("FORTUNER", "TOYOTA", "FORTUNER", "FORTUNER 2.8L 4X4 AT", "DIESEL", "2022"),
            ("CITY", "HONDA", "CITY", "CITY 5TH GEN 1.5L V (GM)", "PETROL", "2020"),
            ("AMAZE", "HONDA", "AMAZE", "AMAZE 1.2L VX", "PETROL", "2020"),
            ("POLO", "VOLKSWAGEN", "POLO", "POLO 1.0L TSI HIGHLINE PLUS", "PETROL", "2020"),
            ("VENTO", "VOLKSWAGEN", "VENTO", "VENTO 1.0L TSI HIGHLINE", "PETROL", "2020"),
            ("OCTAVIA", "SKODA", "OCTAVIA", "OCTAVIA 2.0L TSI L&K", "PETROL", "2021"),
            ("RAPID", "SKODA", "RAPID", "RAPID 1.0L TSI RIDER PLUS", "PETROL", "2020"),
            ("KWID", "RENAULT", "KWID", "KWID 1.0L RXT", "PETROL", "2020"),
            ("DUSTER", "RENAULT", "DUSTER", "DUSTER 1.5L RXZ", "DIESEL", "2019"),
            ("SELTOS", "KIA", "SELTOS", "SELTOS 1.5L GTX PLUS", "PETROL", "2021"),
            ("SONET", "KIA", "SONET", "SONET 1.0L TURBO HTX", "PETROL", "2021"),
        ]

        for kw, mk, md, sub, fl, yr in model_keywords:
            if kw in raw_upper:
                v_make, v_model, v_variant, v_fuel, v_year = mk, md, sub, fl, yr
                break

        # Predefined RTO & Vehicle registry map for seamless demo & realistic lookup
        if not v_make:
            known_vehicles = {
                "TN06AM1234": ("MAHINDRA", "THAR", "THAR 2ND GEN 2.0L LX 4WD HT AT", "PETROL", "2022"),
                "TN30CA1499": ("HYUNDAI", "CRETA", "CRETA 1.6 SX CRDI DIESEL", "DIESEL", "2021"),
                "KA05EF9012": ("MARUTI SUZUKI", "SWIFT", "SWIFT 3RD GEN 1.2L VXI", "PETROL", "2020"),
                "MH02CD5678": ("TATA", "NEXON", "NEXON 1.5 REVOFORTE XZ+", "DIESEL", "2022"),
                "DL03GH3456": ("TOYOTA", "INNOVA CRYSTA", "INNOVA CRYSTA 2.4 VX 7 STR", "DIESEL", "2021"),
                "KL07CA1122": ("HONDA", "CITY", "CITY 5TH GEN 1.5 i-VTEC V", "PETROL", "2019"),
                "TN01AB1234": ("HYUNDAI", "I10", "I10 1ST GEN F/L 1.1L ERA", "PETROL", "2015"),
                "TN09AX5678": ("HYUNDAI", "GRAND I10", "GRAND I10 1ST GEN F/L 1.2L SPORTZ", "PETROL", "2018"),
            }
            
            if clean_reg in known_vehicles:
                v_make, v_model, v_variant, v_fuel, v_year = known_vehicles[clean_reg]
            else:
                conn.close()
                state_code = clean_reg[:2]
                rto_map = {
                    "TN": "Chennai RTO, Tamil Nadu",
                    "KA": "Bangalore RTO, Karnataka",
                    "MH": "Mumbai RTO, Maharashtra",
                    "DL": "New Delhi RTO, Delhi",
                    "KL": "Kerala RTO",
                    "AP": "Andhra Pradesh RTO",
                    "TS": "Telangana RTO",
                    "HR": "Haryana RTO",
                    "UP": "Uttar Pradesh RTO",
                    "GJ": "Gujarat RTO",
                    "WB": "West Bengal RTO"
                }
                rto_name = rto_map.get(state_code, f"{state_code} Regional Transport Office")
                return {
                    "status": "no_api_key",
                    "registrationNo": clean_reg,
                    "rto": rto_name,
                    "message": f"Vehicle number {clean_reg} detected ({rto_name}). Live MoRTH Vahan lookup requires an API key (e.g. Surepass or RapidAPI). You can select your Make & Model directly from the dropdowns below."
                }

        # PERFORM CATALOGUE DATABASE FUZZY VARIANT MATCHING
        matched_catalog_variant, match_score = fuzzy_match_variant_in_db(cur, v_make, v_model, v_variant, v_fuel, v_year)
        
        conn.close()

        # State / RTO mapping
        state_code = clean_reg[:2]
        rto_map = {
            "TN": "Chennai Central RTO, Tamil Nadu",
            "KA": "Bangalore Central RTO, Karnataka",
            "MH": "Mumbai West RTO, Maharashtra",
            "DL": "New Delhi RTO, Delhi",
            "KL": "Trivandrum RTO, Kerala",
            "AP": "Vijayawada RTO, Andhra Pradesh",
            "TS": "Hyderabad RTO, Telangana",
            "HR": "Gurugram RTO, Haryana",
            "UP": "Noida RTO, Uttar Pradesh",
            "GJ": "Ahmedabad RTO, Gujarat",
            "WB": "Kolkata South RTO, West Bengal"
        }
        rto_name = rto_map.get(state_code, f"{state_code} Regional Transport Office")

        return {
            "status": "success",
            "registrationNo": clean_reg,
            "make": v_make,
            "model": v_model,
            "subModel": matched_catalog_variant or v_variant,
            "rawVahanVariant": v_variant,
            "fuelType": v_fuel,
            "year": v_year,
            "rto": rto_name,
            "matchScore": match_score,
            "source": v_source,
            "message": "Vehicle found. Please review the details."
        }
    except Exception as e:
        if conn: conn.close()
        return {"status": "error", "message": str(e)}

def search_catalogue(q="", brand="", make="", model="", sub_model="", fuel_type="", year="", segment="", aggregate="", sub_aggregate="", component="", min_price=None, max_price=None, page=1, limit=25):
    conn = get_db()
    if not conn:
        return {"status": "error", "message": "Database not initialized", "items": [], "totalCount": 0, "page": 1, "totalPages": 0}

    try:
        page = max(1, int(page))
        limit = min(500, max(1, int(limit)))
        offset = (page - 1) * limit

        where_clauses = []
        params = []

        q = (q or "").strip()

        if q:
            clean_q = re.sub(r'[^A-Za-z0-9]', '', q).upper()
            part_candidates = list(dict.fromkeys([q, clean_q]))
            if len(clean_q) > 8:
                part_candidates.append(clean_q[:8] + '-' + clean_q[8:])
                part_candidates.append(clean_q[:3] + '-' + clean_q[3:])
            if len(clean_q) > 5 and clean_q[:5].isdigit():
                part_candidates.append(clean_q[:5] + '-' + clean_q[5:])

            cur_fast = conn.cursor()
            placeholders = ','.join(['?'] * len(part_candidates))
            cur_fast.execute(f"SELECT id FROM overall_catalogue WHERE line_code_part_number IN ({placeholders}) LIMIT 100", part_candidates)
            fast_ids = [r[0] for r in cur_fast.fetchall()]

            if not fast_ids and len(clean_q) >= 3:
                cur_fast.execute("SELECT id FROM overall_catalogue WHERE line_code_part_number LIKE ? LIMIT 100", (f"%{clean_q}%",))
                fast_ids = [r[0] for r in cur_fast.fetchall()]

            if fast_ids:
                id_placeholders = ','.join(['?'] * len(fast_ids))
                where_clauses.append(f"id IN ({id_placeholders})")
                params.extend(fast_ids)
            else:
                fts_tokens = [t for t in re.findall(r'[A-Za-z0-9]+', q) if len(t) >= 2]
                fts_ids = []
                if fts_tokens:
                    try:
                        safe_q = ' '.join([f'{t}*' for t in fts_tokens])
                        cur_fast.execute("SELECT rowid FROM overall_catalogue_fts WHERE overall_catalogue_fts MATCH ? LIMIT 150", (safe_q,))
                        fts_ids = [r[0] for r in cur_fast.fetchall()]
                    except Exception:
                        fts_ids = []

                if fts_ids:
                    id_placeholders = ','.join(['?'] * len(fts_ids))
                    where_clauses.append(f"id IN ({id_placeholders})")
                    params.extend(fts_ids)
                else:
                    where_clauses.append("(line_code_part_number LIKE ? OR part_description LIKE ? OR brand_name LIKE ?)")
                    params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

        if brand:
            where_clauses.append("brand_name = ?")
            params.append(brand)
        if make:
            where_clauses.append("vehicle_make = ?")
            params.append(make)
        if model:
            where_clauses.append("vehicle_model = ?")
            params.append(model)
        if sub_model:
            where_clauses.append("vehicle_sub_model = ?")
            params.append(sub_model)
        if fuel_type:
            where_clauses.append("vehicle_fuel_type LIKE ?")
            params.append(f"%{fuel_type}%")
        if year:
            where_clauses.append("(vehicle_from_year <= ? AND vehicle_to_year >= ?)")
            params.extend([str(year), str(year)])
        if segment:
            where_clauses.append("vehicle_segment = ?")
            params.append(segment)
        if aggregate:
            where_clauses.append("aggregate = ?")
            params.append(aggregate)
        if sub_aggregate:
            where_clauses.append("sub_aggregate = ?")
            params.append(sub_aggregate)
        if component:
            where_clauses.append("components = ?")
            params.append(component)
        if min_price is not None and str(min_price).replace('.','',1).isdigit():
            where_clauses.append("(mrp_price >= ? OR list_price >= ?)")
            params.extend([float(min_price), float(min_price)])
        if max_price is not None and str(max_price).replace('.','',1).isdigit():
            where_clauses.append("(mrp_price <= ? AND mrp_price > 0)")
            params.append(float(max_price))

        where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Count total matching records
        cur = conn.cursor()
        if not where_str:
            total_count = 23671472
            order_by_clause = "ORDER BY id ASC"
        else:
            count_sql = f"SELECT COUNT(*) FROM overall_catalogue{where_str}"
            cur.execute(count_sql, params)
            total_count = cur.fetchone()[0]
            order_by_clause = "ORDER BY id ASC"

        # Fetch page records
        data_sql = f"""
        SELECT id, line_code, brand_name, line_code_part_number, part_description, hsn_code,
               tax_rate, price_type, sales_uom, list_price, mrp_price, sales_price_group,
               vehicle_segment, vehicle_make, vehicle_model, vehicle_sub_model,
               vehicle_fuel_type, vehicle_from_year, vehicle_to_year, aggregate,
               sub_aggregate, components
        FROM overall_catalogue{where_str}
        {order_by_clause}
        LIMIT ? OFFSET ?
        """
        fetch_params = list(params) + [limit, offset]
        cur.execute(data_sql, fetch_params)
        rows = cur.fetchall()

        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "lineCode": r["line_code"],
                "brand": r["brand_name"],
                "partNo": r["line_code_part_number"],
                "desc": r["part_description"],
                "hsn": r["hsn_code"],
                "taxRate": r["tax_rate"],
                "priceType": r["price_type"],
                "uom": r["sales_uom"],
                "listPrice": r["list_price"],
                "mrp": r["mrp_price"],
                "priceGroup": r["sales_price_group"],
                "segment": r["vehicle_segment"],
                "make": r["vehicle_make"],
                "model": r["vehicle_model"],
                "subModel": r["vehicle_sub_model"],
                "fuelType": r["vehicle_fuel_type"],
                "fromYear": r["vehicle_from_year"],
                "toYear": r["vehicle_to_year"],
                "aggregate": r["aggregate"],
                "subAggregate": r["sub_aggregate"],
                "components": r["components"]
            })

        conn.close()
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

        return {
            "status": "success",
            "items": items,
            "totalCount": total_count,
            "page": page,
            "limit": limit,
            "totalPages": total_pages
        }
    except Exception as e:
        if conn: conn.close()
        return {"status": "error", "message": str(e), "items": [], "totalCount": 0, "page": 1, "totalPages": 0}

def get_part_details(part_no):
    conn = get_db()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT id, line_code, brand_name, line_code_part_number, part_description, hsn_code,
               tax_rate, price_type, sales_uom, list_price, mrp_price, sales_price_group,
               vehicle_segment, vehicle_make, vehicle_model, vehicle_sub_model,
               vehicle_fuel_type, vehicle_from_year, vehicle_to_year, aggregate,
               sub_aggregate, components
        FROM overall_catalogue
        WHERE line_code_part_number = ?
        ORDER BY CASE WHEN mrp_price > 0 THEN 0 ELSE 1 END, id ASC
        LIMIT 100
        """, (part_no,))
        rows = cur.fetchall()

        if not rows:
            clean_p = re.sub(r'[^A-Za-z0-9]', '', str(part_no)).upper()
            cur.execute("""
            SELECT id, line_code, brand_name, line_code_part_number, part_description, hsn_code,
                   tax_rate, price_type, sales_uom, list_price, mrp_price, sales_price_group,
                   vehicle_segment, vehicle_make, vehicle_model, vehicle_sub_model,
                   vehicle_fuel_type, vehicle_from_year, vehicle_to_year, aggregate,
                   sub_aggregate, components
            FROM overall_catalogue
            WHERE line_code_part_number LIKE ?
            ORDER BY CASE WHEN mrp_price > 0 THEN 0 ELSE 1 END, id ASC
            LIMIT 100
            """, (f"%{clean_p}%",))
            rows = cur.fetchall()

        if not rows:
            conn.close()
            return None

        first = rows[0]
        compat_list = []
        for r in rows:
            compat_list.append({
                "segment": r["vehicle_segment"],
                "make": r["vehicle_make"],
                "model": r["vehicle_model"],
                "subModel": r["vehicle_sub_model"],
                "fuelType": r["vehicle_fuel_type"],
                "fromYear": r["vehicle_from_year"],
                "toYear": r["vehicle_to_year"]
            })

        # Fetch Respective OES / OEM Interchangeable Equivalent Parts
        oes_parts = []
        part_comp = first["components"]
        part_make = first["vehicle_make"]
        part_model = first["vehicle_model"]
        
        if part_comp:
            try:
                cur_oes = conn.cursor()
                oes_clauses = ["components = ?", "line_code_part_number != ?"]
                oes_params = [part_comp, first["line_code_part_number"]]
                if part_make:
                    oes_clauses.append("(vehicle_make = ? OR vehicle_make = '')")
                    oes_params.append(part_make)
                if part_model:
                    oes_clauses.append("(vehicle_model = ? OR vehicle_model = '')")
                    oes_params.append(part_model)
                
                cur_oes.execute(f"""
                    SELECT line_code_part_number, brand_name, part_description, mrp_price, list_price,
                           vehicle_make, vehicle_model, vehicle_sub_model, components
                    FROM overall_catalogue
                    WHERE {' AND '.join(oes_clauses)}
                    GROUP BY line_code_part_number
                    ORDER BY CASE WHEN mrp_price > 0 THEN 0 ELSE 1 END, mrp_price ASC
                    LIMIT 20
                """, oes_params)
                for r in cur_oes.fetchall():
                    oes_parts.append({
                        "partNo": r["line_code_part_number"],
                        "brand": r["brand_name"] or "GENERIC",
                        "desc": r["part_description"] or "",
                        "mrp": float(r["mrp_price"] or 0),
                        "listPrice": float(r["list_price"] or 0),
                        "make": r["vehicle_make"] or "",
                        "model": r["vehicle_model"] or "",
                        "subModel": r["vehicle_sub_model"] or "",
                        "component": r["components"] or ""
                    })
            except Exception as oes_err:
                print("OES lookup notice:", oes_err)

        conn.close()

        return {
            "partNo": first["line_code_part_number"],
            "desc": first["part_description"],
            "brand": first["brand_name"],
            "lineCode": first["line_code"],
            "hsn": first["hsn_code"],
            "taxRate": first["tax_rate"],
            "uom": first["sales_uom"],
            "listPrice": first["list_price"],
            "mrp": first["mrp_price"],
            "priceGroup": first["sales_price_group"],
            "aggregate": first["aggregate"],
            "subAggregate": first["sub_aggregate"],
            "components": first["components"],
            "compatibilities": compat_list,
            "oesParts": oes_parts
        }
    except Exception:
        if conn: conn.close()
        return None

def map_single_part_ai_rule(part_no, desc, brand=""):
    """
    AI / Heuristic Rule Fallback based on COMPONENT_MAPPING_RULES_CONSOLIDATED.md
    """
    desc_upper = (desc or "").upper()
    brand_upper = (brand or "").upper()
    is_body = False

    # 1. Fasteners (Bolt, Screw, Nut, Washer, Clip, Pin, Stud, Rivet, Bracket)
    if re.search(r'\b(BOLT|SCREW|NUT|WASHER|CLIP|STUD|RIVET|FASTENER)\b', desc_upper):
        if 'BOLT' in desc_upper: comp = 'BOLT'
        elif 'SCREW' in desc_upper: comp = 'SCREW'
        elif 'NUT' in desc_upper: comp = 'NUT'
        elif 'WASHER' in desc_upper: comp = 'WASHER'
        elif 'CLIP' in desc_upper:
            comp = 'CLIP'
            if any(b in desc_upper for b in ['BUMPER', 'DOOR', 'PANEL', 'FENDER', 'TRIM']): is_body = True
        else: comp = 'FASTENER'
        return {
            "aggregate": "CHILD PARTS", "subAggregate": "FASTENERS", "component": comp,
            "category": "Body Parts" if is_body else "Mechanical Parts", "confidence": "HIGH",
            "matchMethod": "CONSOLIDATED_AI_RULE_P4", "remarks": f"Part Type: {comp} (Normalized fastener, prevented application override)"
        }

    # 2. Door Pad / Interior Pad vs Brake Pad (Semantic Contradiction Check)
    if 'PAD' in desc_upper and any(d in desc_upper for d in ['DOOR', 'GLASS', 'STOP', 'CRASH', 'INTERIOR', 'ROOF']):
        return {
            "aggregate": "BODY & TRIM", "subAggregate": "DOOR & INTERIOR",
            "component": "DOOR PAD" if 'DOOR' in desc_upper else "INTERIOR PAD",
            "category": "Body Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P15",
            "remarks": "Door/Interior Pad distinguished from Brake Pad (Semantic Contradiction Check)"
        }

    # 3. Brake System
    if re.search(r'\b(BRAKE PAD|BRAKE DISC|BRAKE SHOE|BRAKE ROTOR|CALIPER|MASTER CYLINDER|WHEEL CYLINDER)\b', desc_upper):
        if 'BRAKE PAD' in desc_upper or ('PAD' in desc_upper and 'BRAKE' in desc_upper):
            comp = 'BRAKE PAD - FRONT' if 'FRONT' in desc_upper else ('BRAKE PAD - REAR' if 'REAR' in desc_upper else 'BRAKE PAD')
            sub = 'DISC BRAKES'
        elif 'DISC' in desc_upper or 'ROTOR' in desc_upper:
            comp = 'BRAKE DISC - FRONT' if 'FRONT' in desc_upper else ('BRAKE DISC - REAR' if 'REAR' in desc_upper else 'BRAKE DISC')
            sub = 'DISC BRAKES'
        elif 'SHOE' in desc_upper: comp = 'BRAKE SHOE'; sub = 'DRUM BRAKES'
        elif 'CALIPER' in desc_upper: comp = 'BRAKE CALIPER'; sub = 'DISC BRAKES'
        elif 'CYLINDER' in desc_upper: comp = 'BRAKE MASTER CYLINDER' if 'MASTER' in desc_upper else 'WHEEL CYLINDER'; sub = 'HYDRAULIC ACTUATION'
        else: comp = 'BRAKE COMPONENT'; sub = 'BRAKE SYSTEM'
        return {
            "aggregate": "BRAKE SYSTEM", "subAggregate": sub, "component": comp,
            "category": "Mechanical Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P4",
            "remarks": f"Brake component identified: {comp}"
        }

    # 4. Filters (Oil, Air, Fuel, Cabin)
    if 'FILTER' in desc_upper or 'CLEANER ELEMENT' in desc_upper:
        if 'OIL' in desc_upper: comp = 'OIL FILTER'; sub = 'LUBRICATION'
        elif 'AIR' in desc_upper or 'CLEANER' in desc_upper: comp = 'AIR FILTER'; sub = 'AIR INTAKE'
        elif 'FUEL' in desc_upper: comp = 'FUEL FILTER'; sub = 'FUEL SYSTEM'
        elif 'CABIN' in desc_upper or 'AC' in desc_upper or 'POLLEN' in desc_upper: comp = 'CABIN FILTER'; sub = 'HVAC & CABIN'
        else: comp = 'FILTER'; sub = 'GENERAL FILTRATION'
        return {
            "aggregate": "FILTERS", "subAggregate": sub, "component": comp,
            "category": "Mechanical Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P4",
            "remarks": f"Filtration unit identified: {comp}"
        }

    # 5. Clutch & Transmission
    if re.search(r'\b(CLUTCH|TRANSMISSION|GEARBOX|FLYWHEEL|PRESSURE PLATE)\b', desc_upper):
        if 'DISC' in desc_upper or 'PLATE' in desc_upper: comp = 'CLUTCH DISC' if 'DISC' in desc_upper else 'CLUTCH COVER'
        elif 'BEARING' in desc_upper or 'RELEASE' in desc_upper: comp = 'CLUTCH RELEASE BEARING'
        elif 'SET' in desc_upper or 'KIT' in desc_upper: comp = 'CLUTCH SET'
        elif 'SLAVE' in desc_upper or 'CSC' in desc_upper: comp = 'CLUTCH SLAVE CYLINDER'
        elif 'MASTER' in desc_upper or 'CMC' in desc_upper: comp = 'CLUTCH MASTER CYLINDER'
        elif 'GEAR' in desc_upper: comp = 'TRANSMISSION GEAR'
        else: comp = 'CLUTCH SYSTEM COMPONENT'
        return {
            "aggregate": "TRANSMISSION", "subAggregate": "CLUTCH ASSEMBLY", "component": comp,
            "category": "Mechanical Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P4",
            "remarks": f"Transmission component identified: {comp}"
        }

    # 6. Suspension & Steering
    if re.search(r'\b(SHOCK ABSORBER|STRUT|DAMPER|SPRING|ARM|BUSH|BALL JOINT|TIE ROD|STABILIZER|LINK ROD)\b', desc_upper):
        if 'BUMPER' in desc_upper:
            return {
                "aggregate": "BODY & TRIM", "subAggregate": "BUMPERS", "component": "BUMPER BRACKET",
                "category": "Body Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P15",
                "remarks": "Bumper bracket identified (prevented misclassification into Strut/Suspension)"
            }
        if 'STRUT' in desc_upper or 'SHOCK' in desc_upper or 'DAMPER' in desc_upper:
            comp = 'FRONT STRUT ASSEMBLY' if 'FRONT' in desc_upper else ('REAR SHOCK ABSORBER' if 'REAR' in desc_upper else 'SHOCK ABSORBER')
            sub = 'DAMPING & STRUTS'
        elif 'ARM' in desc_upper: comp = 'LOWER CONTROL ARM'; sub = 'CONTROL ARMS'
        elif 'BALL JOINT' in desc_upper: comp = 'LOWER BALL JOINT'; sub = 'JOINTS & LINKAGES'
        elif 'TIE ROD' in desc_upper or 'RACK END' in desc_upper: comp = 'TIE ROD END'; sub = 'STEERING LINKAGE'
        elif 'STABILIZER' in desc_upper or 'LINK' in desc_upper: comp = 'FRONT STABILIZER LINK'; sub = 'ANTI-ROLL BARS'
        elif 'BUSH' in desc_upper: comp = 'SUSPENSION BUSH'; sub = 'BUSHINGS'
        else: comp = 'SUSPENSION COMPONENT'; sub = 'SUSPENSION'
        return {
            "aggregate": "SUSPENSION", "subAggregate": sub, "component": comp,
            "category": "Mechanical Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P4",
            "remarks": f"Suspension/Steering component: {comp}"
        }

    # 7. Engine Components, Gaskets, Belts, Pumps
    if re.search(r'\b(GASKET|SEAL|BELT|PUMP|ALTERNATOR|STARTER|PISTON|VALVE|CAMSHAFT|CRANKSHAFT|SPARK PLUG)\b', desc_upper):
        if 'GASKET' in desc_upper:
            comp = 'WATER PUMP GASKET' if 'WATER PUMP' in desc_upper else ('HEAD GASKET' if 'HEAD' in desc_upper else 'ENGINE GASKET')
            sub = 'GASKETS & SEALS'
        elif 'SEAL' in desc_upper:
            comp = 'OIL SEAL' if 'OIL' in desc_upper else ('AXLE SEAL' if 'AXLE' in desc_upper else 'SEAL')
            sub = 'GASKETS & SEALS'
        elif 'BELT' in desc_upper: comp = 'TIMING BELT' if 'TIMING' in desc_upper else 'V-RIBBED BELT'; sub = 'TIMING & DRIVE BELTS'
        elif 'WATER PUMP' in desc_upper: comp = 'WATER PUMP'; sub = 'COOLING SYSTEM'
        elif 'FUEL PUMP' in desc_upper: comp = 'FUEL PUMP'; sub = 'FUEL DELIVERY'
        elif 'SPARK PLUG' in desc_upper: comp = 'SPARK PLUG'; sub = 'IGNITION SYSTEM'
        elif 'ALTERNATOR' in desc_upper: comp = 'ALTERNATOR BEARING' if 'BEARING' in desc_upper else 'ALTERNATOR'; sub = 'CHARGING SYSTEM'
        elif 'STARTER' in desc_upper: comp = 'STARTER MOTOR'; sub = 'STARTING SYSTEM'
        else: comp = 'ENGINE COMPONENT'; sub = 'CORE ENGINE'
        return {
            "aggregate": "ENGINE", "subAggregate": sub, "component": comp,
            "category": "Mechanical Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P5",
            "remarks": f"Engine assembly component: {comp} (Specific beats generic)"
        }

    # 8. Body Panels, Mirrors, Lights, Bumpers
    if re.search(r'\b(BUMPER|FENDER|BONNET|HOOD|DOOR|MIRROR|HEADLAMP|TAILLAMP|GRILLE|WINDSHIELD|GLASS|WIPER)\b', desc_upper):
        if 'BUMPER' in desc_upper: comp = 'BUMPER ASSY FRONT' if 'FRONT' in desc_upper else ('BUMPER ASSY REAR' if 'REAR' in desc_upper else 'BUMPER'); sub = 'BUMPERS'
        elif 'FENDER' in desc_upper: comp = 'FRONT FENDER'; sub = 'FRONT SHEET METAL'
        elif 'BONNET' in desc_upper or 'HOOD' in desc_upper: comp = 'BONNET / HOOD'; sub = 'FRONT SHEET METAL'
        elif 'DOOR' in desc_upper: comp = 'DOOR PANEL'; sub = 'DOORS'
        elif 'MIRROR' in desc_upper: comp = 'SIDE REAR VIEW MIRROR'; sub = 'MIRRORS'
        elif 'HEADLAMP' in desc_upper or 'HEAD LIGHT' in desc_upper: comp = 'HEADLAMP ASSEMBLY'; sub = 'LIGHTING'
        elif 'TAILLAMP' in desc_upper or 'TAIL LIGHT' in desc_upper: comp = 'TAILLAMP ASSEMBLY'; sub = 'LIGHTING'
        elif 'WIPER' in desc_upper: comp = 'WIPER BLADE'; sub = 'WIPER SYSTEM'
        else: comp = 'BODY PANEL'; sub = 'EXTERIOR BODY'
        return {
            "aggregate": "BODY & TRIM", "subAggregate": sub, "component": comp,
            "category": "Body Parts", "confidence": "HIGH", "matchMethod": "CONSOLIDATED_AI_RULE_P4",
            "remarks": f"Body & Exterior component: {comp}"
        }

    # Fallback
    return {
        "aggregate": "CHILD PARTS", "subAggregate": "GENERAL", "component": "SPARE PART",
        "category": "Mechanical Parts", "confidence": "LOW", "matchMethod": "HEURISTIC_FALLBACK",
        "remarks": "Auto Mapped (Domain Rule)"
    }

def smart_map_parts(part_items):
    """
    Batch mapping tool: Maps a list of part numbers or part items to 23.6M catalogue DB + AI rules fallback.
    """
    conn = get_db()
    if not part_items:
        return {}
    
    results = {}
    db_items = []
    
    # Standardize input into objects with partNo, description, brand
    input_rows = []
    for item in part_items:
        if isinstance(item, dict):
            p_no = str(item.get("partNo") or item.get("part_no") or item.get("Part Number") or item.get("Part Number (Without Line Code)") or item.get("part_number") or item.get("Item Code") or "").strip()
            desc = str(item.get("description") or item.get("Description") or item.get("part_description") or item.get("desc") or "").strip()
            br = str(item.get("brand") or item.get("Brand") or item.get("brand_name") or item.get("make") or "").strip()
        else:
            p_no = str(item).strip()
            desc = ""
            br = ""
        if p_no:
            input_rows.append({"partNo": p_no, "description": desc, "brand": br})

    if not input_rows:
        return {}

    try:
        cur = conn.cursor() if conn else None
        
        # 1. Step 1: Lookup in 23.6M Database
        if cur:
            all_parts = list(set([r["partNo"] for r in input_rows]))
            chunk_size = 200
            for i in range(0, len(all_parts), chunk_size):
                chunk = all_parts[i:i+chunk_size]
                clean_chunk = [re.sub(r'[^A-Za-z0-9]', '', p).upper() for p in chunk]
                all_candidates = list(set(chunk + clean_chunk))
                placeholders = ",".join(["?"] * len(all_candidates))
                sql = f"""
                SELECT line_code_part_number, brand_name, part_description, mrp_price, list_price,
                       tax_rate, vehicle_segment, vehicle_make, vehicle_model, aggregate,
                       sub_aggregate, components
                FROM overall_catalogue
                WHERE line_code_part_number IN ({placeholders})
                ORDER BY CASE WHEN mrp_price > 0 THEN 0 ELSE 1 END, id ASC
                """
                cur.execute(sql, all_candidates)
                for r in cur.fetchall():
                    p_no = r["line_code_part_number"]
                    clean_db_no = re.sub(r'[^A-Za-z0-9]', '', p_no).upper()
                    
                    agg = r["aggregate"] or "CHILD PARTS"
                    comp = r["components"] or "SPARE PART"
                    is_body = any(b in agg.upper() or b in comp.upper() for b in ['BODY', 'BUMPER', 'FENDER', 'DOOR', 'MIRROR', 'GLASS', 'TRIM'])
                    category = "Body Parts" if is_body else "Mechanical Parts"

                    matched_data = {
                        "brand": r["brand_name"] or "GENERIC",
                        "description": r["part_description"] or "",
                        "mrp": float(r["mrp_price"] or 0),
                        "listPrice": float(r["list_price"] or 0),
                        "taxRate": r["tax_rate"],
                        "segment": r["vehicle_segment"],
                        "make": r["vehicle_make"],
                        "model": r["vehicle_model"],
                        "aggregate": agg,
                        "subAggregate": r["sub_aggregate"] or "GENERAL",
                        "component": comp,
                        "category": category,
                        "confidence": "HIGH",
                        "confidenceScore": 98,
                        "matchMethod": "DB_EXACT_CATALOGUE",
                        "remarks": "Exact Match from 23.6M Master Catalogue Database"
                    }
                    if p_no not in results: results[p_no] = matched_data
                    if clean_db_no not in results: results[clean_db_no] = matched_data
            conn.close()

        # 2. Step 2: Apply AI Rules Engine Fallback from COMPONENT_MAPPING_RULES_CONSOLIDATED.md for unmatched rows
        for row in input_rows:
            p_no = row["partNo"]
            clean_p = re.sub(r'[^A-Za-z0-9]', '', p_no).upper()
            if p_no in results:
                continue
            if clean_p in results:
                results[p_no] = results[clean_p]
                continue
            
            # Apply consolidated AI rule set
            rule_res = map_single_part_ai_rule(p_no, row["description"], row["brand"])
            results[p_no] = {
                "brand": row["brand"] or "GENERIC",
                "description": row["description"] or "Automotive Component",
                "mrp": 0,
                "listPrice": 0,
                "taxRate": 18,
                "segment": "PCV",
                "make": row["brand"] or "GENERIC",
                "model": "Universal",
                "aggregate": rule_res["aggregate"],
                "subAggregate": rule_res["subAggregate"],
                "component": rule_res["component"],
                "category": rule_res["category"],
                "confidence": rule_res["confidence"],
                "confidenceScore": 88 if rule_res["confidence"] == "HIGH" else 65,
                "matchMethod": rule_res["matchMethod"],
                "remarks": rule_res["remarks"]
            }

        return results
    except Exception as e:
        if conn: conn.close()
        return {"error": str(e)}

def export_catalogue_csv(q="", brand="", make="", model="", sub_model="", fuel_type="", year="", segment="", aggregate="", sub_aggregate="", component="", min_price=None, max_price=None, max_rows=50000):
    conn = get_db()
    if not conn: return ""

    try:
        where_clauses = []
        params = []

        q = (q or "").strip()
        if q:
            try:
                safe_q = '"' + q.replace('"', '""') + '"*'
                fts_sql = "SELECT rowid FROM overall_catalogue_fts WHERE overall_catalogue_fts MATCH ?"
                where_clauses.append(f"id IN ({fts_sql})")
                params.append(safe_q)
            except Exception:
                where_clauses.append("(line_code_part_number LIKE ? OR part_description LIKE ? OR brand_name LIKE ?)")
                params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

        if brand:
            where_clauses.append("brand_name = ?")
            params.append(brand)
        if make:
            where_clauses.append("vehicle_make = ?")
            params.append(make)
        if model:
            where_clauses.append("vehicle_model = ?")
            params.append(model)
        if sub_model:
            where_clauses.append("vehicle_sub_model = ?")
            params.append(sub_model)
        if fuel_type:
            where_clauses.append("vehicle_fuel_type LIKE ?")
            params.append(f"%{fuel_type}%")
        if year:
            where_clauses.append("(vehicle_from_year <= ? AND vehicle_to_year >= ?)")
            params.extend([str(year), str(year)])
        if segment:
            where_clauses.append("vehicle_segment = ?")
            params.append(segment)
        if aggregate:
            where_clauses.append("aggregate = ?")
            params.append(aggregate)
        if sub_aggregate:
            where_clauses.append("sub_aggregate = ?")
            params.append(sub_aggregate)
        if component:
            where_clauses.append("components = ?")
            params.append(component)
        if min_price is not None and str(min_price).replace('.','',1).isdigit():
            where_clauses.append("(mrp_price >= ? OR list_price >= ?)")
            params.extend([float(min_price), float(min_price)])
        if max_price is not None and str(max_price).replace('.','',1).isdigit():
            where_clauses.append("(mrp_price <= ? AND mrp_price > 0)")
            params.append(float(max_price))

        where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        sql = f"""
        SELECT line_code_part_number, brand_name, part_description, mrp_price, list_price, tax_rate,
               vehicle_segment, vehicle_make, vehicle_model, vehicle_sub_model, vehicle_fuel_type,
               vehicle_from_year, vehicle_to_year, aggregate, sub_aggregate, components
        FROM overall_catalogue{where_str}
        ORDER BY CASE WHEN mrp_price > 0 THEN 0 ELSE 1 END, id ASC
        LIMIT ?
        """
        params.append(max_rows)

        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Part Number", "Brand", "Description", "MRP Price", "List Price", "Tax %",
            "Segment", "Make", "Model", "Sub Model", "Fuel Type",
            "From Year", "To Year", "Aggregate", "Sub Aggregate", "Component"
        ])
        for r in rows:
            writer.writerow(list(r))

        return output.getvalue()
    except Exception:
        if conn: conn.close()
        return ""
