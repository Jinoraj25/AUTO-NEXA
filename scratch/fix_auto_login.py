import re

# 1. Update index.html to clear mytvs_logged_in on page load
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_head_script = '''<head>
  <script>
    if (window.location.search) {
      try { window.history.replaceState({}, document.title, window.location.pathname); } catch(e) {}
    }'''

new_head_script = '''<head>
  <script>
    try {
      sessionStorage.removeItem('mytvs_logged_in');
      localStorage.removeItem('mytvs_logged_in');
    } catch(e) {}

    if (window.location.search) {
      try { window.history.replaceState({}, document.title, window.location.pathname); } catch(e) {}
    }'''

html_updated = html.replace(old_head_script, new_head_script)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_updated)

print("Updated index.html: Cleared auto-login tokens on page load.")

# 2. Update js/app.js checkAuth method
with open('js/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

old_check_auth = '''  checkAuth() {
    if (window.location.search) {
      try { window.history.replaceState({}, document.title, window.location.pathname); } catch(e) {}
    }

    const isLoggedIn = sessionStorage.getItem('mytvs_logged_in') === 'true' || localStorage.getItem('mytvs_logged_in') === 'true';
    const loginOverlay = document.getElementById('mytvs-login-screen');
    const header = document.getElementById('app-header');
    const mainContent = document.getElementById('main-app-content');
    const footer = document.querySelector('footer.app-footer');
    const userCode = sessionStorage.getItem('mytvs_user_code') || localStorage.getItem('mytvs_user_code') || 'SM0237';
    const userName = sessionStorage.getItem('mytvs_user_name') || localStorage.getItem('mytvs_user_name') || 'Jino George';

    if (isLoggedIn) {
      document.body.classList.add('is-authenticated');
      if (loginOverlay) loginOverlay.remove();
      if (header) header.style.setProperty('display', 'flex', 'important');
      if (mainContent) mainContent.style.setProperty('display', 'block', 'important');
      if (footer) footer.style.setProperty('display', 'block', 'important');
      this.updateHeaderProfile(userCode, userName);
    } else {
      document.body.classList.remove('is-authenticated');
      if (loginOverlay) loginOverlay.style.setProperty('display', 'flex', 'important');
    }
  },'''

new_check_auth = '''  checkAuth() {
    if (window.location.search) {
      try { window.history.replaceState({}, document.title, window.location.pathname); } catch(e) {}
    }

    // Always require explicit Sign In on page refresh/load!
    try {
      sessionStorage.removeItem('mytvs_logged_in');
      localStorage.removeItem('mytvs_logged_in');
    } catch(e) {}

    document.body.classList.remove('is-authenticated');
    const loginOverlay = document.getElementById('mytvs-login-screen');
    if (loginOverlay) {
      loginOverlay.style.setProperty('display', 'flex', 'important');
    }
  },'''

app_js_updated = app_js.replace(old_check_auth, new_check_auth)

with open('js/app.js', 'w', encoding='utf-8') as f:
    f.write(app_js_updated)

print("Updated js/app.js: Require explicit Sign In button click on page load.")
