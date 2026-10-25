import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDS_DIR = os.path.join(BASE_DIR, "images", "brands")
os.makedirs(BRANDS_DIR, exist_ok=True)

BRAND_SVGS = {
    "luk.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40">
  <rect width="100" height="40" rx="4" fill="#FFCC00" stroke="#000000" stroke-width="2"/>
  <text x="50" y="27" font-family="Arial Black, Impact, sans-serif" font-weight="900" font-size="22" text-anchor="middle" fill="#000000" letter-spacing="-1">LuK</text>
</svg>''',

    "sachs.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 40">
  <circle cx="20" cy="20" r="14" fill="none" stroke="#004B93" stroke-width="3"/>
  <path d="M14 20 L26 20 M20 14 L26 20 L20 26" fill="none" stroke="#004B93" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="42" y="27" font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="20" fill="#004B93" letter-spacing="1">SACHS</text>
</svg>''',

    "bosch.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 150 40">
  <circle cx="20" cy="20" r="14" fill="none" stroke="#334155" stroke-width="2.5"/>
  <line x1="12" y1="20" x2="28" y2="20" stroke="#EA1D25" stroke-width="4" stroke-linecap="round"/>
  <text x="44" y="27" font-family="Helvetica, Arial, sans-serif" font-weight="900" font-size="22" fill="#EA1D25" letter-spacing="0.5">BOSCH</text>
</svg>''',

    "trw.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40">
  <text x="10" y="29" font-family="Arial Black, Impact, sans-serif" font-style="italic" font-weight="900" font-size="26" fill="#DC2626" letter-spacing="1">TRW</text>
</svg>''',

    "ceekay.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 40">
  <text x="10" y="28" font-family="Arial Black, sans-serif" font-weight="900" font-size="21" fill="#1E3A8A" letter-spacing="1">CEEKAY</text>
</svg>''',

    "exedy.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 40">
  <text x="10" y="28" font-family="Arial Black, sans-serif" font-weight="900" font-size="22" letter-spacing="0.5">
    <tspan fill="#DC2626">E</tspan><tspan fill="#0284C7">XEDY</tspan>
  </text>
</svg>''',

    "valeo.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 130 40">
  <text x="10" y="28" font-family="Arial Black, sans-serif" font-weight="900" font-size="22" fill="#059669" letter-spacing="0.5">Valeo</text>
</svg>''',

    "purolator.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 40">
  <rect x="5" y="6" width="150" height="28" rx="4" fill="#1D4ED8"/>
  <text x="80" y="26" font-family="Arial Black, sans-serif" font-weight="900" font-size="15" text-anchor="middle" fill="#FFFFFF" letter-spacing="1">PUROLATOR</text>
</svg>''',

    "mahle.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 130 40">
  <text x="10" y="27" font-family="Arial Black, sans-serif" font-weight="900" font-size="20" fill="#0284C7" letter-spacing="1">MAHLE</text>
</svg>''',

    "brembo.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 40">
  <circle cx="18" cy="20" r="10" fill="#DC2626"/>
  <text x="36" y="27" font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="20" fill="#DC2626" letter-spacing="0.5">brembo</text>
</svg>''',

    "tvs_girling.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 40">
  <text x="5" y="27" font-family="Arial Black, sans-serif" font-weight="900" font-size="16" fill="#0F172A">TVS <tspan fill="#DC2626">GIRLING</tspan></text>
</svg>''',

    "mytvs.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 130 40">
  <text x="5" y="27" font-family="Arial Black, sans-serif" font-weight="900" font-size="18" fill="#EA580C">my<tspan fill="#1E40AF">TVS</tspan></text>
</svg>''',

    "elofic.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 130 40">
  <text x="5" y="27" font-family="Arial Black, sans-serif" font-weight="900" font-size="19" fill="#15803D" letter-spacing="0.5">ELOFIC</text>
</svg>'''
}

for fname, svg in BRAND_SVGS.items():
    fpath = os.path.join(BRANDS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(svg)
    # Also save as .png alias path if requested by frontend
    png_path = os.path.join(BRANDS_DIR, fname.replace(".svg", ".png"))
    with open(png_path, "w", encoding="utf-8") as f:
        f.write(svg)

print(f"Generated {len(BRAND_SVGS)} brand SVGs successfully in {BRANDS_DIR}")
