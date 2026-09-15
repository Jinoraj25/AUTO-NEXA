with open("styles.css", "r", encoding="utf-8") as f:
    css = f.read()

import re
keywords = ["tab-pane", "main-app-content", "mytvs-fullscreen-login-page", "app-header", "is-authenticated"]
for kw in keywords:
    matches = [m.start() for m in re.finditer(re.escape(kw), css)]
    print(f"Keyword '{kw}': {len(matches)} matches")
    for pos in matches[:3]:
        snippet = css[max(0, pos-40):min(len(css), pos+120)].replace('\n', ' ')
        print(f"   --> {snippet}")
