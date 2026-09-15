import os

js_files = [
    "js/data-engine.js",
    "js/inventory-portal.js",
    "js/analytics-portal.js",
    "js/mapping-portal.js",
    "js/deviation-portal.js",
    "js/forecasting-portal.js",
    "js/app.js"
]

combined = []
for file_path in js_files:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            combined.append(f"/* ==================== {file_path} ==================== */\n(function() {{\n{content}\n}})();")
    else:
        print(f"WARNING: File {file_path} not found!")

# Clean global helpers
global_helpers = """
/* ==================== GLOBAL FAILSAFE HELPERS ==================== */
window.loginDirect = function(e) {
  if (e && e.preventDefault) e.preventDefault();
  try {
    sessionStorage.setItem('mytvs_logged_in', 'true');
    localStorage.setItem('mytvs_logged_in', 'true');
  } catch(err) {}
  document.body.classList.add('is-authenticated');
  var overlay = document.getElementById('mytvs-login-screen');
  if (overlay) {
    try { overlay.remove(); } catch(err) { overlay.style.display = 'none'; }
  }
  var header = document.getElementById('app-header');
  if (header) header.style.setProperty('display', 'flex', 'important');
  var main = document.getElementById('main-app-content');
  if (main) main.style.setProperty('display', 'block', 'important');
  var footer = document.querySelector('footer.app-footer');
  if (footer) footer.style.setProperty('display', 'block', 'important');
  document.body.style.overflow = 'auto';
  if (window.App && window.App.handleLogin) {
    try { window.App.handleLogin(e); } catch(err) {}
  } else if (window.App && window.App.switchTab) {
    window.App.switchTab('home');
  }
  return false;
};
"""

combined.append(global_helpers)

final_js = "\n\n".join(combined)
with open("nexa-app.js", "w", encoding="utf-8") as f:
    f.write(final_js)

print("nexa-app.js rebundled with IIFE scope isolation successfully. Total length:", len(final_js))
