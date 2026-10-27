/* AUTO NEXA - Enterprise Intelligence Core Controller (Left Sidebar Layout) */

window.App = {
  activeTab: 'home',
  _initialized: false,

  async init() {
    if (this._initialized) return;
    this._initialized = true;
    console.log("⚡ Initializing AUTO NEXA Enterprise Platform...");
    
    localStorage.setItem('auto-nexa-theme', 'light');
    document.documentElement.setAttribute('data-theme', 'light');
    document.body.setAttribute('data-theme', 'light');

    this.bindEvents();

    // Expand Catalogue sidebar group by default
    const catGroup = document.getElementById('sb-group-catalogue');
    if (catGroup) catGroup.classList.add('is-open');
    
    // Wrap sub-portal inits
    try {
      if (window.DataEngine && window.DataEngine.init) await window.DataEngine.init();
    } catch (e) { console.warn("DataEngine init warning:", e); }

    try {
      if (window.MappingPortal && window.MappingPortal.init) window.MappingPortal.init();
      if (window.OverallCataloguePortal && window.OverallCataloguePortal.init) window.OverallCataloguePortal.init();
      if (window.CatalogAiChat && window.CatalogAiChat.init) window.CatalogAiChat.init();
      if (window.InventoryPortal && window.InventoryPortal.init) window.InventoryPortal.init();
      if (window.AnalyticsPortal && window.AnalyticsPortal.init) window.AnalyticsPortal.init();
      if (window.ForecastingPortal && window.ForecastingPortal.init) window.ForecastingPortal.init();
    } catch (e) { console.warn("Sub-portal init warning:", e); }

    this.initHomeVideo();
    const urlParams = new URLSearchParams(window.location.search);
    const initialTab = window._initialTab || urlParams.get('tab') || window.location.hash.replace('#', '') || 'home';
    this.switchTab(initialTab);
    this.showToast("AUTO NEXA Online — Automotive Parts Intelligence loaded.", "success");
  },

  bindEvents() {
    document.addEventListener('click', (e) => {
      if (document.body.classList.contains('sidebar-mobile-open')) {
        if (!e.target.closest('#app-sidebar') && !e.target.closest('#sidebar-toggle-btn')) {
          document.body.classList.remove('sidebar-mobile-open');
        }
      }
      const tabBtn = e.target.closest('[data-tab]');
      if (tabBtn) {
        const targetTab = tabBtn.getAttribute('data-tab');
        if (targetTab) {
          e.preventDefault();
          this.switchTab(targetTab);
        }
      }
    });

    const themeBtn = document.getElementById('btn-theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => this.toggleTheme());
    }
  },

  toggleSidebar() {
    if (window.innerWidth <= 900) {
      document.body.classList.toggle('sidebar-mobile-open');
    } else {
      document.body.classList.toggle('sidebar-collapsed');
    }
  },

  toggleSidebarGroup(groupId) {
    const group = document.getElementById(groupId);
    if (!group) return;
    const isCurrentlyOpen = group.classList.contains('is-open');
    
    // Close other groups optionally or keep accordion behavior
    document.querySelectorAll('.sb-group').forEach(g => {
      if (g.id !== groupId) g.classList.remove('is-open');
    });

    if (isCurrentlyOpen) {
      group.classList.remove('is-open');
    } else {
      group.classList.add('is-open');
    }
  },

  switchTab(tabId) {
    if (window.innerWidth <= 900) {
      document.body.classList.remove('sidebar-mobile-open');
    }
    this.activeTab = tabId || 'home';

    // Route target tab and determine matching DOM section ID
    let targetSectionId = 'tab-home';
    let breadcrumbSec = 'WORKSPACE';
    let breadcrumbPg = 'Home Overview';

    switch (this.activeTab) {
      case 'home':
        targetSectionId = 'tab-home';
        breadcrumbSec = 'WORKSPACE';
        breadcrumbPg = 'Home Overview';
        break;

      case 'catalogue':
      case 'catalogue-dashboard':
        targetSectionId = 'tab-catalogue';
        breadcrumbSec = 'CATALOGUE';
        breadcrumbPg = 'Master DB Dashboard (23.6M)';
        break;

      case 'catalogue-mapping':
        targetSectionId = 'tab-catalogue-mapping';
        breadcrumbSec = 'CATALOGUE';
        breadcrumbPg = 'TVS Aggregate Master & Mapping Studio';
        break;

      case 'catalogue-ai':
        targetSectionId = 'tab-catalogue-ai';
        breadcrumbSec = 'CATALOGUE';
        breadcrumbPg = 'Catalog AI Assistant';
        break;

      case 'catalogue-oem-to-oes':
      case 'catalogue-oem-oes':
      case 'oem-to-oes':
      case 'oem-oes':
        targetSectionId = 'tab-catalogue-oem-to-oes';
        breadcrumbSec = 'CATALOGUE';
        breadcrumbPg = 'OEM ➔ OES Conversion Intelligence';
        if (window.OemToOesPortal && window.OemToOesPortal.init) {
          window.OemToOesPortal.init();
        }
        break;

      case 'inventory':
      case 'inventory-dashboard':
        targetSectionId = 'tab-inventory';
        breadcrumbSec = 'INVENTORY';
        breadcrumbPg = 'Good Stock Intelligence';
        break;

      case 'sales-rf':
        targetSectionId = 'tab-analytics';
        breadcrumbSec = 'SALES';
        breadcrumbPg = 'Retail Franchisee (RF) Sales';
        break;

      case 'sales-cf':
        targetSectionId = 'tab-analytics';
        breadcrumbSec = 'SALES';
        breadcrumbPg = 'Corporate Franchisee (CF) Sales';
        break;

      case 'analytics':
      case 'sales-overall':
        targetSectionId = 'tab-analytics';
        breadcrumbSec = 'SALES';
        breadcrumbPg = 'Overall Sales Performance';
        break;

      default:
        targetSectionId = `tab-${this.activeTab}`;
        breadcrumbSec = 'WORKSPACE';
        breadcrumbPg = this.activeTab.toUpperCase();
    }

    // Update Top Breadcrumb
    const elSec = document.getElementById('breadcrumb-section');
    const elPg = document.getElementById('breadcrumb-page');
    if (elSec) elSec.textContent = breadcrumbSec;
    if (elPg) elPg.textContent = breadcrumbPg;

    // Update Sidebar Item Active States
    document.querySelectorAll('.sb-nav-item, .sb-sub-item').forEach(el => el.classList.remove('active'));
    
    const activeEl = document.querySelector(`[data-tab="${this.activeTab}"]`);
    if (activeEl) {
      activeEl.classList.add('active');
      const parentGroup = activeEl.closest('.sb-group');
      if (parentGroup) {
        parentGroup.classList.add('is-open');
      }
    }

    // Show Matching Pane, Hide Others
    document.querySelectorAll('.tab-pane').forEach(pane => {
      if (pane.id === targetSectionId) {
        pane.classList.add('active');
        pane.style.setProperty('display', 'block', 'important');
      } else {
        pane.classList.remove('active');
        pane.style.setProperty('display', 'none', 'important');
      }
    });

    // Close mobile sidebar on navigation
    if (window.innerWidth <= 900) {
      document.body.classList.remove('sidebar-mobile-open');
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Trigger Portal-Specific Refresh Logic
    setTimeout(() => {
      try {
        if (targetSectionId === 'tab-catalogue' && window.OverallCataloguePortal) {
          if (window.OverallCataloguePortal.loadStats) window.OverallCataloguePortal.loadStats();
          window.OverallCataloguePortal.fetchData();
          if (window.OverallCataloguePortal.initCharts) window.OverallCataloguePortal.initCharts();
        } else if (targetSectionId === 'tab-home') {
          this.initHomeVideo();
        } else if (targetSectionId === 'tab-catalogue-mapping' && window.MappingPortal) {
          window.MappingPortal.renderAggregateMasterTable();
        } else if (targetSectionId === 'tab-catalogue-ai' && window.CatalogAiChat) {
          window.CatalogAiChat.init();
        } else if (targetSectionId === 'tab-inventory' && window.InventoryPortal) {
          window.InventoryPortal.renderAll();
        } else if (targetSectionId === 'tab-analytics' && window.AnalyticsPortal) {
          const uploadGrid = document.getElementById('sales-upload-grid');
          const rfCard = document.getElementById('rf-upload-card-wrapper');
          const cfCard = document.getElementById('cf-upload-card-wrapper');
          if (this.activeTab === 'sales-rf') {
            window.AnalyticsPortal.setChannel('RF');
            if (uploadGrid) uploadGrid.style.display = 'grid';
            if (rfCard) rfCard.style.display = 'block';
            if (cfCard) cfCard.style.display = 'none';
          } else if (this.activeTab === 'sales-cf') {
            window.AnalyticsPortal.setChannel('CF');
            if (uploadGrid) uploadGrid.style.display = 'grid';
            if (rfCard) rfCard.style.display = 'none';
            if (cfCard) cfCard.style.display = 'block';
          } else {
            window.AnalyticsPortal.setChannel('ALL');
            if (uploadGrid) uploadGrid.style.display = 'none';
          }
          window.AnalyticsPortal.updateDashboard();
        } else if (targetSectionId === 'tab-forecasting' && window.ForecastingPortal) {
          window.ForecastingPortal.updateForecasting();
        }
      } catch (tabErr) {
        console.warn("Tab switch callback notice:", tabErr);
      }
    }, 50);
  },

  // ==================== CATALOG AI ASSISTANT ====================

  setAiPrompt(prompt) {
    this.switchTab('catalogue-ai');
    setTimeout(() => {
      if (window.CatalogAiChat) {
        window.CatalogAiChat.quickSend(prompt);
      }
    }, 100);
  },

  runCatalogAiQuery() {
    this.switchTab('catalogue-ai');
    setTimeout(() => {
      const input = document.getElementById('cat-ai-chat-input');
      const query = input ? input.value.trim() : '';
      if (window.CatalogAiChat) {
        if (query) window.CatalogAiChat.quickSend(query);
        else window.CatalogAiChat.handleSend();
      }
    }, 100);
  },

  inspectPartInMaster(partNo) {
    if (this.activeTab === 'catalogue-ai' && window.CatalogAiChat && window.CatalogAiChat.showFitmentModal) {
      window.CatalogAiChat.showFitmentModal(partNo);
      return;
    }
    this.switchTab('catalogue-dashboard');
    setTimeout(() => {
      if (window.OverallCataloguePortal) {
        window.OverallCataloguePortal.setQuickSearch(partNo);
      }
    }, 100);
  },

  // ==================== THEME & UTILITIES ====================

  toggleTheme() {
    const body = document.body;
    const root = document.documentElement;
    body.setAttribute('data-theme', 'light');
    root.setAttribute('data-theme', 'light');
    localStorage.setItem('auto-nexa-theme', 'light');
    this.syncChartTheme();
    this.showToast("AUTO NEXA Light Studio Theme Active", "info");
    if (window.AnalyticsPortal) window.AnalyticsPortal.updateDashboard();
  },

  syncChartTheme() {
    if (typeof Chart === 'undefined') return;
    const text = '#0f172a';
    const muted = '#64748b';
    Chart.defaults.color = muted;
    Chart.defaults.plugins.legend.labels.color = text;
    Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
    Chart.defaults.plugins.tooltip.bodyColor = '#f8fafc';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.95)';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(15, 23, 42, 0.15)';
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    const iconMap = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    toast.innerHTML = `<span>${iconMap[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  checkAuth() {
    const isLoggedIn = (sessionStorage.getItem('autonexa_logged_in') === 'true') || (sessionStorage.getItem('mytvs_logged_in') === 'true');
    const loginOverlay = document.getElementById('autonexa-login-screen') || document.getElementById('mytvs-login-screen');
    const header = document.getElementById('app-header');
    const sidebar = document.getElementById('app-sidebar');
    const mainContent = document.getElementById('main-app-content');
    const footer = document.querySelector('footer.app-footer');

    if (isLoggedIn) {
      document.body.classList.add('is-authenticated');
      if (loginOverlay) loginOverlay.remove();
      if (sidebar) sidebar.style.setProperty('display', 'flex', 'important');
      if (header) header.style.setProperty('display', 'flex', 'important');
      if (mainContent) mainContent.style.setProperty('display', 'block', 'important');
      if (footer) footer.style.setProperty('display', 'block', 'important');
      document.body.style.overflow = '';
    } else {
      document.body.classList.remove('is-authenticated');
      if (loginOverlay) loginOverlay.style.setProperty('display', 'flex', 'important');
      if (sidebar) sidebar.style.setProperty('display', 'none', 'important');
      if (header) header.style.setProperty('display', 'none', 'important');
      if (mainContent) mainContent.style.setProperty('display', 'none', 'important');
      if (footer) footer.style.setProperty('display', 'none', 'important');
      document.body.style.overflow = 'hidden';
    }
  },

  handleLogin(e) {
    if (e && e.preventDefault) e.preventDefault();
    const userCodeInput = document.getElementById('login-username');
    const userCode = (userCodeInput && userCodeInput.value ? userCodeInput.value : 'DEMO').trim().toUpperCase();

    let displayName = "Jino George";
    if (userCode === "DEMO" || userCode === "DEMOGUEST" || userCode === "GUEST") {
      displayName = "Guest Recruiter";
    }

    sessionStorage.setItem('autonexa_logged_in', 'true');
    sessionStorage.setItem('autonexa_user_code', userCode);
    sessionStorage.setItem('autonexa_user_name', displayName);
    sessionStorage.setItem('mytvs_logged_in', 'true');

    document.body.classList.add('is-authenticated');
    const loginOverlay = document.getElementById('autonexa-login-screen') || document.getElementById('mytvs-login-screen');
    const sidebar = document.getElementById('app-sidebar');
    const header = document.getElementById('app-header');
    const mainContent = document.getElementById('main-app-content');
    const footer = document.querySelector('footer.app-footer');

    if (loginOverlay) loginOverlay.remove();
    if (sidebar) sidebar.style.setProperty('display', 'flex', 'important');
    if (header) header.style.setProperty('display', 'flex', 'important');
    if (mainContent) mainContent.style.setProperty('display', 'block', 'important');
    if (footer) footer.style.setProperty('display', 'block', 'important');
    document.body.style.overflow = '';

    this.switchTab('home');
    this.showToast(`Welcome back, ${displayName}! Logged into AUTO NEXA Hub.`, "success");
  },

  initHomeVideo() {
    const video = document.getElementById("explodedHeroVideo");
    if (video) {
      video.muted = true;
      video.play().catch((err) => console.log("Hero video autoplay status:", err));
    }

    const loginVideo = document.getElementById("loginHeroVideo");
    if (loginVideo) {
      loginVideo.muted = true;
      loginVideo.play().catch((err) => console.log("Login video autoplay status:", err));
    }
  },

  handleHomeSearch() {
    const input = document.getElementById('home-hero-search-input');
    const val = input ? input.value.trim() : '';
    this.switchTab('catalogue');
    if (val && window.OverallCataloguePortal) {
      setTimeout(() => {
        const catInput = document.getElementById('cat-search-q');
        if (catInput) catInput.value = val;
        OverallCataloguePortal.setQuickSearch(val);
      }, 120);
    }
  },

  filterAssembly(aggName) {
    this.switchTab('catalogue');
    if (window.OverallCataloguePortal) {
      setTimeout(() => {
        OverallCataloguePortal.resetFilters();
        const aggSelect = document.getElementById('cat-filter-aggregate');
        if (aggSelect) {
          OverallCataloguePortal.ensureOption('cat-filter-aggregate', aggName);
          aggSelect.value = aggName;
          OverallCataloguePortal.handleAggregateChange();
        }
      }, 120);
    }
  },

  logout() {
    sessionStorage.removeItem('autonexa_logged_in');
    sessionStorage.removeItem('autonexa_user_code');
    sessionStorage.removeItem('autonexa_user_name');
    sessionStorage.removeItem('mytvs_logged_in');
    sessionStorage.removeItem('mytvs_user_code');
    sessionStorage.removeItem('mytvs_user_name');
    try { localStorage.removeItem('autonexa_logged_in'); } catch(e) {}
    try { localStorage.removeItem('mytvs_logged_in'); } catch(e) {}
    document.body.classList.remove('is-authenticated');
    window.location.reload();
  }
};

window.switchTab = function(tabId) {
  if (window.App && window.App.switchTab) {
    window.App.switchTab(tabId);
  }
};

function autoInitApp() {
  try {
    if (window.App) {
      window.App.checkAuth();
      window.App.init();
    }
  } catch(e) {
    console.error("AutoInit error:", e);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', autoInitApp);
} else {
  autoInitApp();
}

window.loginDirect = function(e) {
  if (e && e.preventDefault) e.preventDefault();
  try {
    sessionStorage.setItem('autonexa_logged_in', 'true');
    sessionStorage.setItem('mytvs_logged_in', 'true');
  } catch(err) {}
  document.body.classList.add('is-authenticated');
  var overlay = document.getElementById('autonexa-login-screen') || document.getElementById('mytvs-login-screen');
  if (overlay) {
    try { overlay.remove(); } catch(err) { overlay.style.display = 'none'; }
  }
  var sidebar = document.getElementById('app-sidebar');
  if (sidebar) sidebar.style.setProperty('display', 'flex', 'important');
  var header = document.getElementById('app-header');
  if (header) header.style.setProperty('display', 'flex', 'important');
  var main = document.getElementById('main-app-content');
  if (main) main.style.setProperty('display', 'block', 'important');
  var footer = document.querySelector('footer.app-footer');
  if (footer) footer.style.setProperty('display', 'block', 'important');
  document.body.style.overflow = '';
  if (window.App && typeof window.App.handleLogin === 'function') {
    try { window.App.handleLogin(e); } catch(err) {
      if (window.App.switchTab) window.App.switchTab('home');
    }
  } else if (window.App && window.App.switchTab) {
    window.App.switchTab('home');
  }
  return false;
};

window.togglePasswordDirect = function() {
  var pwInput = document.getElementById('login-password');
  if (pwInput) {
    pwInput.type = pwInput.type === 'password' ? 'text' : 'password';
  }
};

window.loginDemo = function(e) {
  if (e && e.preventDefault) e.preventDefault();
  var u = document.getElementById('login-username');
  var p = document.getElementById('login-password');
  if (u) u.value = 'DemoGuest';
  if (p) p.value = '••••••••';
  return window.loginDirect(e);
};

window.loginSubmit = function(e) {
  if (e && e.preventDefault) e.preventDefault();
  var u = document.getElementById('login-username');
  var p = document.getElementById('login-password');
  var userVal = (u && u.value ? u.value : '').trim();
  var passVal = (p && p.value ? p.value : '').trim();
  if (!userVal || !passVal) {
    if (window.App && window.App.showToast) {
      window.App.showToast('Please click "1-Click Live Demo" below to explore the platform.', 'info');
    } else {
      alert('Please click "1-Click Live Demo" below to explore the platform.');
    }
    return false;
  }
  return window.loginDirect(e);
};