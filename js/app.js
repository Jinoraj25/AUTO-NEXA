/* AUTO NEXA - PCV Intelligence Core Controller */

window.App = {
  activeTab: 'home',

  async init() {
    console.log("Initializing AUTO NEXA Intelligence Platform...");
    const savedTheme = localStorage.getItem('auto-nexa-theme');
    if (savedTheme === 'light' || savedTheme === 'dark') {
      document.documentElement.setAttribute('data-theme', savedTheme);
      document.body.setAttribute('data-theme', savedTheme);
    }
    this.bindEvents();
    
    // Step 1: Initialize Data Engine (Loads pre-trained DB)
    await window.DataEngine.init();

    // Step 2: Initialize Sub-Portals
    window.MappingPortal.init();
    window.InventoryPortal.init();
    window.AnalyticsPortal.init();
    window.DeviationPortal.init();
    window.ForecastingPortal.init();

    // Step 3: Default to Home Landing Page on initialization / refresh
    this.switchTab('home');

    this.showToast("AUTO NEXA Ready — Intelligence workspace online.", "success");
  },

  bindEvents() {
    // Navigation Menu Link Switching
    const menuItems = document.querySelectorAll('.nav-menu-item');
    menuItems.forEach(item => {
      item.addEventListener('click', () => {
        const targetTab = item.getAttribute('data-tab');
        if (targetTab) {
          this.switchTab(targetTab);
        }
      });
    });

    // Brand Logo Home Link
    const brandBtn = document.getElementById('brand-home-btn');
    if (brandBtn) {
      brandBtn.addEventListener('click', () => this.switchTab('home'));
    }

    // Theme Toggle
    const themeBtn = document.getElementById('btn-theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => this.toggleTheme());
    }
  },

  switchTab(tabId) {
    this.activeTab = tabId;

    // Update Nav Menu Active Highlight
    document.querySelectorAll('.nav-menu-item').forEach(link => {
      if (link.getAttribute('data-tab') === tabId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Update Visible Tab Content Pane
    document.querySelectorAll('.tab-pane').forEach(pane => {
      if (pane.id === `tab-${tabId}`) {
        pane.classList.add('active');
      } else {
        pane.classList.remove('active');
      }
    });

    // Scroll smoothly to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Trigger tab specific refresh actions
    if (tabId === 'inventory') {
      window.InventoryPortal.fetchInventoryData();
    } else if (tabId === 'analytics') {
      window.AnalyticsPortal.updateDashboard();
    } else if (tabId === 'deviation') {
      window.DeviationPortal.updateDeviationAnalysis();
    } else if (tabId === 'forecasting') {
      window.ForecastingPortal.updateForecasting();
    }
  },

  toggleTheme() {
    const body = document.body;
    const root = document.documentElement;
    const currentTheme = body.getAttribute('data-theme') || root.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    root.setAttribute('data-theme', newTheme);
    localStorage.setItem('auto-nexa-theme', newTheme);
    this.syncChartTheme();
    this.showToast(`Switched to ${newTheme.toUpperCase()} theme mode`, "info");
    if (window.AnalyticsPortal) window.AnalyticsPortal.updateDashboard();
    setTimeout(() => this.syncChartTheme(), 40);
  },

  syncChartTheme() {
    if (typeof Chart === 'undefined') return;
    const dark = (document.body.getAttribute('data-theme') || document.documentElement.getAttribute('data-theme') || 'dark') === 'dark';
    const styles = getComputedStyle(document.body);
    const text = styles.getPropertyValue('--nx-ink').trim() || (dark ? '#f5f8fd' : '#101b2d');
    const muted = styles.getPropertyValue('--nx-muted').trim() || (dark ? '#9baac0' : '#64748b');
    const grid = dark ? 'rgba(160,181,207,.13)' : 'rgba(100,116,139,.13)';
    Chart.defaults.color = muted;
    Chart.defaults.plugins.legend.labels.color = text;
    Chart.defaults.plugins.tooltip.titleColor = dark ? '#ffffff' : '#ffffff';
    Chart.defaults.plugins.tooltip.bodyColor = '#dbe5ef';
    Chart.defaults.plugins.tooltip.backgroundColor = dark ? 'rgba(8,17,29,.96)' : 'rgba(15,27,45,.96)';
    Chart.defaults.plugins.tooltip.borderColor = dark ? 'rgba(255,255,255,.12)' : 'rgba(15,27,45,.16)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Object.values(window.AnalyticsPortal?.charts || {}).forEach(chart => {
      if (!chart || !chart.options) return;
      const scales = chart.options.scales || {};
      Object.values(scales).forEach(scale => {
        scale.grid = scale.grid || {};
        scale.grid.color = grid;
        scale.ticks = scale.ticks || {};
        scale.ticks.color = muted;
        if (scale.title) scale.title.color = text;
      });
      chart.options.plugins = chart.options.plugins || {};
      chart.options.plugins.legend = chart.options.plugins.legend || {};
      chart.options.plugins.legend.labels = chart.options.plugins.legend.labels || {};
      chart.options.plugins.legend.labels.color = text;
      chart.update('none');
    });
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    
    const iconMap = {
      success: '✅',
      error: '❌',
      info: 'ℹ️',
      warning: '⚠️'
    };

    toast.innerHTML = `
      <span>${iconMap[type] || 'ℹ️'}</span>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  togglePasswordVisibility() {
    const pwInput = document.getElementById('login-password');
    if (pwInput) {
      pwInput.type = pwInput.type === 'password' ? 'text' : 'password';
    }
  },

  checkAuth() {
    const isLoggedIn = sessionStorage.getItem('mytvs_logged_in') === 'true';
    const loginOverlay = document.getElementById('mytvs-login-screen');
    const header = document.getElementById('app-header');
    const mainContent = document.getElementById('main-app-content');
    const footer = document.querySelector('footer.app-footer');
    const userCode = sessionStorage.getItem('mytvs_user_code') || localStorage.getItem('mytvs_user_code') || 'SM0237';
    const userName = sessionStorage.getItem('mytvs_user_name') || localStorage.getItem('mytvs_user_name') || 'Jino George';

    if (!isLoggedIn) {
      document.body.classList.remove('is-authenticated');
      if (loginOverlay) loginOverlay.style.display = 'grid';
      if (header) header.style.display = 'none';
      if (mainContent) mainContent.style.display = 'none';
      if (footer) footer.style.display = 'none';
      document.body.style.overflow = 'hidden';
    } else {
      document.body.classList.add('is-authenticated');
      if (loginOverlay) loginOverlay.style.display = 'none';
      if (header) header.style.display = 'flex';
      if (mainContent) mainContent.style.display = 'block';
      if (footer) footer.style.display = 'block';
      document.body.style.overflow = '';
      this.updateHeaderProfile(userCode, userName);
    }
  },

  updateHeaderProfile(code, name) {
    const elName = document.getElementById('header-user-name');
    const elCode = document.getElementById('header-user-code');
    const elAvatar = document.getElementById('header-user-avatar');

    if (elName) elName.innerText = name;
    if (elCode) elCode.innerText = `${code} • myTVS`;
    if (elAvatar) {
      const parts = name.split(' ');
      const initials = parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.slice(0, 2).toUpperCase();
      elAvatar.innerText = initials;
    }
  },

  handleLogin(e) {
    if (e) e.preventDefault();
    const userCode = (document.getElementById('login-username')?.value || 'SM0237').trim().toUpperCase();
    const password = document.getElementById('login-password')?.value || '';
    const btn = document.getElementById('btn-login-submit');

    if (password !== 'Catalog@2026') {
      alert("Invalid password! Please use password: Catalog@2026");
      return;
    }

    let displayName = "Jino George";
    if (userCode === "SM0216") {
      displayName = "Prasanna";
    } else if (userCode === "SM0237") {
      displayName = "Jino George";
    } else {
      displayName = `Employee ${userCode}`;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span>⏳</span> Authenticating with myTVS...';
    }

    setTimeout(() => {
      sessionStorage.setItem('mytvs_logged_in', 'true');
      sessionStorage.setItem('mytvs_user_code', userCode);
      sessionStorage.setItem('mytvs_user_name', displayName);
      localStorage.setItem('mytvs_logged_in', 'true');

      document.body.classList.add('is-authenticated');

      const loginOverlay = document.getElementById('mytvs-login-screen');
      const header = document.getElementById('app-header');
      const mainContent = document.getElementById('main-app-content');
      const footer = document.querySelector('footer.app-footer');

      if (loginOverlay) loginOverlay.style.display = 'none';
      if (header) header.style.display = 'flex';
      if (mainContent) mainContent.style.display = 'block';
      if (footer) footer.style.display = 'block';
      document.body.style.overflow = '';

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span>Sign In</span> <span class="arrow-icon">→</span>';
      }

      this.updateHeaderProfile(userCode, displayName);
      this.switchTab('home');

      // Trigger 1.5-second Auto-fading Welcome Pop-Up Notification
      const welcomePopup = document.getElementById('mytvs-welcome-popup');
      const welcomeHead = document.getElementById('welcome-user-heading');

      if (welcomeHead) welcomeHead.innerText = `Welcome ${displayName}`;
      if (welcomePopup) {
        welcomePopup.style.display = 'flex';
        setTimeout(() => welcomePopup.classList.add('show'), 20);

        setTimeout(() => {
          welcomePopup.classList.remove('show');
          setTimeout(() => {
            welcomePopup.style.display = 'none';
          }, 400);
        }, 1500);
      }
    }, 300);
  },

  closeWelcomePopup() {
    const welcomePopup = document.getElementById('mytvs-welcome-popup');
    if (welcomePopup) {
      welcomePopup.classList.remove('show');
      welcomePopup.style.display = 'none';
    }
  },

  logout() {
    sessionStorage.removeItem('mytvs_logged_in');
    sessionStorage.removeItem('mytvs_user_code');
    sessionStorage.removeItem('mytvs_user_name');
    localStorage.removeItem('mytvs_logged_in');
    document.body.classList.remove('is-authenticated');
    this.checkAuth();
    this.showToast("Signed out of myTVS Session", "info");
  }
};

// Initialize App on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  window.App.init();
  window.App.checkAuth();
});
