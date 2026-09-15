import os

files = [
    'js/data-engine.js',
    'js/inventory-portal.js',
    'js/analytics-portal.js',
    'js/mapping-portal.js',
    'js/deviation-portal.js',
    'js/forecasting-portal.js',
    'js/app.js'
]

combined = []
for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            combined.append(f'/* --- {filepath} --- */\n' + f.read())

bundle_content = '\n\n'.join(combined)

with open('nexa-app.js', 'w', encoding='utf-8') as f:
    f.write(bundle_content)

print(f"Successfully generated nexa-app.js ({len(bundle_content)} bytes) from {len(files)} files.")
