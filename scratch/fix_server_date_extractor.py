import re

with open('server.py', 'r', encoding='utf-8') as f:
    code = f.read()

extractor_py = '''def extract_stock_date(filename):
    if not filename:
        return '16-Sep-2026'
    month_map = {
        'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
        'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'
    }
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    m1 = re.search(r'(\\d{1,2})[\\s_\\-\\.\\']*([A-Za-z]{3})[\\s_\\-\\.\\']*\\'?(\\d{2,4})', filename)
    if m1:
        day = int(m1.group(1))
        day_str = f'{day:02d}'
        mon = month_map.get(m1.group(2).upper(), 'Sep')
        yr = m1.group(3)
        if len(yr) == 2:
            yr = '20' + yr
        return f'{day_str}-{mon}-{yr}'

    m2 = re.search(r'(\\d{1,2})[\\s_\\-\\.]+(\\d{1,2})[\\s_\\-\\.]+(\\d{2,4})', filename)
    if m2:
        day = int(m2.group(1))
        day_str = f'{day:02d}'
        mon_idx = int(m2.group(2)) - 1
        mon = month_names[mon_idx] if 0 <= mon_idx < 12 else 'Sep'
        yr = m2.group(3)
        if len(yr) == 2:
            yr = '20' + yr
        return f'{day_str}-{mon}-{yr}'

    m3 = re.search(r'\\d{2}-[A-Za-z]{3}-\\d{4}', filename)
    if m3:
        return m3.group(0)

    return '16-Sep-2026'\n\n'''

# Insert extract_stock_date at top of server.py
code_updated = code.replace("def insert_daily_stock_db(stock_date, filename, items):", extractor_py + "def insert_daily_stock_db(stock_date, filename, items):")

# Replace date_match in do_POST
old_match_py = '''                date_match = re.search(r'\\d{2}-[A-Za-z]{3}-\\d{4}', filename)
                date_str = date_match.group(0) if date_match else filename'''

new_match_py = '''                date_str = extract_stock_date(filename)'''

code_updated = code_updated.replace(old_match_py, new_match_py)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Updated server.py with extract_stock_date!")
