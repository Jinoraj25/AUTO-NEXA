with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace ?v=50.0.0 with ?v=51.0.0
html_updated = html.replace('?v=50.0.0', '?v=51.0.0')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_updated)

print("Bumped script cache versions in index.html to ?v=51.0.0!")
