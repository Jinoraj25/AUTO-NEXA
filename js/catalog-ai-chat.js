/**
 * AutoNexa Catalog AI Conversational Chatbot
 * ==========================================
 * Interactive diagnostic and parts chatbot with multi-step vehicle identification,
 * fuel & year stepper, 3D Oriparts visual cards, OEM & Tier-1 OES matrix,
 * proactive relatable companion parts recommendations, in-place fitment modal,
 * and persistent session storage (never vanishes on tab change).
 */

const CatalogAiChat = {
  toggleHistory() {
    const workspace = document.querySelector('.cat-ai-workspace');
    const sidebar = document.querySelector('.cat-ai-sidebar-panel');
    if (window.innerWidth <= 900) {
      if (sidebar) sidebar.classList.toggle('mobile-open');
    } else {
      if (workspace) workspace.classList.toggle('history-collapsed');
    }
  },

  toggleInspector() {
    const inspector = document.getElementById('cat-ai-side-inspector');
    if (inspector) {
      inspector.classList.toggle('collapsed');
    }
  },

  activeVehicleContext: null,
  state: {
    make: null,
    model: null,
    fuel: null,
    year: null,
    component: null,
    sub_model: null,
    part_no: null
  },
  history: [],
  isWaiting: false,

  _initialized: false,
  init() {
    if (this._initialized) {
      this.updateActiveVehicleBar();
      return;
    }
    this._initialized = true;

    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;

    // Attach Enter key to input if not already attached
    const input = document.getElementById('cat-ai-chat-input');
    if (input && !input.dataset.bound) {
      input.dataset.bound = 'true';
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.handleSend();
        }
      });
    }

    // Attach ESC key to close modal if open
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeFitmentModal();
      }
    });

    // Try restoring conversation and active vehicle from sessionStorage
    const restored = this.restoreState();
    if (!restored && this.history.length === 0) {
      this.renderWelcomeGreeting();
    }
    this.updateActiveVehicleBar();
    this.updateSideInspector(this.activeVehicleContext, null);

    // Auto-run query if passed via URL parameter (e.g. ?tab=catalogue-ai&ai_query=...)
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const queryParam = urlParams.get('ai_query');
      if (queryParam && queryParam.trim().length > 0) {
        window.history.replaceState({}, document.title, window.location.pathname + '?autologin=1&tab=catalogue-ai');
        setTimeout(() => this.quickSend(queryParam.trim()), 600);
      }
    } catch (e) {}
  },

  updateActiveVehicleBar() {
    const bar = document.getElementById('cat-ai-active-vehicle-bar');
    const nameEl = document.getElementById('cat-ai-vehicle-pill-name');
    const subEl = document.getElementById('cat-ai-vehicle-pill-sub');
    const clearBtn = document.getElementById('cat-ai-clear-vehicle-btn');
    if (!nameEl) return;

    if (this.activeVehicleContext && this.activeVehicleContext.make) {
      const v = this.activeVehicleContext;
      const vehStr = `${v.make} ${v.model || ''} ${v.variant || ''} ${v.fuel ? '(' + v.fuel + ')' : ''} ${v.year || ''}`.replace(/\s+/g, ' ').trim();
      nameEl.textContent = vehStr;
      if (subEl) subEl.textContent = '• Pinned Session Context (Subsequent queries inherit this automatically)';
      if (clearBtn) clearBtn.style.display = 'inline-block';
      if (bar) bar.classList.add('has-vehicle');
    } else {
      nameEl.textContent = 'None Pinned';
      if (subEl) subEl.textContent = '(Ask for any car part e.g. "Tata Indica Vista brake pad" to pin vehicle)';
      if (clearBtn) clearBtn.style.display = 'none';
      if (bar) bar.classList.remove('has-vehicle');
    }
  },

  updateSideInspector(veh, action) {
    const vehCard = document.getElementById('cat-ai-side-vehicle-content');
    const clearBtn = document.getElementById('cat-ai-side-clear-btn');
    if (vehCard) {
      if (veh && veh.make) {
        const vTitle = `${veh.make} ${veh.model || ''} ${veh.variant || veh.sub_model || ''}`.trim();
        const vMeta = `${veh.fuel || ''} ${veh.year ? '• ' + veh.year : ''}`.trim();
        const vImg = veh.image || 'images/oriparts_default_car.png';
        if (clearBtn) clearBtn.style.display = 'inline-block';
        vehCard.innerHTML = `
          <div style="display: flex; gap: 0.75rem; align-items: center;">
            <img src="${vImg}" alt="${this.escapeHtml(vTitle)}" style="width: 80px; height: 52px; object-fit: contain; border-radius: 8px; background: #f8fafc; border: 1.5px solid #e2e8f0; padding: 3px;" onerror="this.onerror=null; this.style.display='none';">
            <div>
              <div style="font-weight: 900; font-size: 0.95rem; color: #0f172a; font-family: 'Outfit', sans-serif;">${this.escapeHtml(vTitle)}</div>
              <div style="font-size: 0.76rem; font-weight: 750; color: #0284c7; margin-top: 0.15rem;">${this.escapeHtml(vMeta)}</div>
              <div style="font-size: 0.7rem; color: #059669; font-weight: 850; margin-top: 0.25rem;">● Active Vehicle Session</div>
            </div>
          </div>
        `;
      } else {
        if (clearBtn) clearBtn.style.display = 'none';
        vehCard.innerHTML = `
          <div style="font-size: 0.82rem; color: #64748b; line-height: 1.45;">
            No vehicle pinned yet. Enter a vehicle or part query (e.g. <em>"Grand i10 Nios brake pad"</em>) to lock vehicle context.
          </div>
        `;
      }
    }

    const partsCard = document.getElementById('cat-ai-side-parts-content');
    if (partsCard && action) {
      if ((action.type === 'parts_matrix' || action.type === 'parts_result') && action.oem) {
        const oem = action.oem;
        const oesList = action.oes || [];
        const oemPriceStr = (oem.mrp && oem.mrp > 0) ? `₹${Number(oem.mrp).toLocaleString('en-IN')}` : 'Price on Request';
        
        let oesTable = '';
        if (oesList.length > 0) {
          oesTable = `
            <div style="margin-top: 0.85rem;">
              <div style="font-size: 0.78rem; font-weight: 850; color: #0f172a; margin-bottom: 0.45rem;">
                🛡️ Verified Tier-1 OES Direct Equivalents (${oesList.length})
              </div>
              <div style="overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.78rem;">
                  <thead>
                    <tr style="border-bottom: 1.5px solid #e2e8f0; background: #f8fafc;">
                      <th style="padding: 6px 8px; text-align: left; font-weight: 850; color: #475569;">Brand</th>
                      <th style="padding: 6px 8px; text-align: left; font-weight: 850; color: #475569;">Part No</th>
                      <th style="padding: 6px 8px; text-align: right; font-weight: 850; color: #475569;">Price</th>
                      <th style="padding: 6px 8px; text-align: right; font-weight: 0.85; color: #059669;">Saving</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${oesList.map(p => {
                      const savePct = (oem.mrp && p.mrp && oem.mrp > p.mrp) ? Math.round(((oem.mrp - p.mrp) / oem.mrp) * 100) : 25;
                      const price = (p.mrp && p.mrp > 0) ? p.mrp : Math.round((oem.mrp || 1500) * 0.75);
                      return `
                        <tr style="border-bottom: 1px solid #f1f5f9;">
                          <td style="padding: 6px 8px; font-weight: 800; color: #0f172a;">${this.escapeHtml(p.brand)}</td>
                          <td style="padding: 6px 8px;">
                            <span style="font-family: monospace; font-weight: 850; color: #0284c7;">${this.escapeHtml(p.partNo)}</span>
                            <button type="button" onclick="CatalogAiChat.copyToClipboard('${this.escapeJs(p.partNo)}', this)" style="padding: 1px 5px; font-size: 0.65rem; border-radius: 4px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; margin-left: 3px;">📋</button>
                          </td>
                          <td style="padding: 6px 8px; text-align: right; font-weight: 900; color: #059669;">₹${Number(price).toLocaleString('en-IN')}</td>
                          <td style="padding: 6px 8px; text-align: right; font-weight: 850; color: #059669;">-${savePct}%</td>
                        </tr>
                      `;
                    }).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          `;
        }

        partsCard.innerHTML = `
          <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 10px; padding: 0.85rem; margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
              <div>
                <span style="font-size: 0.68rem; font-weight: 850; background: #166534; color: #ffffff; padding: 2px 6px; border-radius: 4px;">OEM DEALERSHIP GENUINE</span>
                <div style="font-size: 0.95rem; font-weight: 900; color: #0f172a; margin-top: 0.3rem;">${this.escapeHtml(oem.desc)}</div>
                <div style="display: flex; align-items: center; gap: 0.4rem; margin-top: 0.25rem;">
                  <span style="font-family: monospace; font-size: 0.88rem; font-weight: 900; color: #166534;">${this.escapeHtml(oem.partNo)}</span>
                  <button type="button" onclick="CatalogAiChat.copyToClipboard('${this.escapeJs(oem.partNo)}', this)" style="padding: 1px 6px; font-size: 0.68rem; border-radius: 4px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer;">📋 Copy</button>
                </div>
                <div style="font-size: 0.72rem; color: #475569; margin-top: 0.2rem;">${this.escapeHtml(oem.brand)} • ${this.escapeHtml(oem.vehicle || '')}</div>
                <div style="display: flex; gap: 0.35rem; margin-top: 0.45rem;">
                  <span style="background: #dcfce7; color: #166534; font-size: 0.68rem; font-weight: 800; padding: 2px 6px; border-radius: 4px;">✔ 100% Direct Match</span>
                  <span style="background: #e0f2fe; color: #0369a1; font-size: 0.68rem; font-weight: 800; padding: 2px 6px; border-radius: 4px;">🟢 Stock Ready</span>
                </div>
              </div>
              <div style="text-align: right; min-width: 80px;">
                <div style="font-size: 1.2rem; font-weight: 900; color: #166534; font-family: 'Outfit', sans-serif;">${oemPriceStr}</div>
                <div style="font-size: 0.65rem; color: #64748b; font-weight: 750;">OEM MRP</div>
              </div>
            </div>
          </div>
          ${oesTable}
        `;
      }
    }
  },

  clearActiveVehicleContext() {
    this.activeVehicleContext = null;
    try {
      sessionStorage.removeItem('auto_nexa_active_vehicle');
    } catch (e) {}
    this.state.make = null;
    this.state.model = null;
    this.state.sub_model = null;
    this.state.fuel = null;
    this.state.year = null;
    this.updateActiveVehicleBar();
    this.updateSideInspector(null, null);
    this.appendBotMessage("🔄 Active vehicle session context cleared. You can now search for any new car model or part number.");
  },

  addToOrder(partNo, brand, desc, mrp) {
    if (window.App && window.App.showToast) {
      window.App.showToast(`🛒 Staged to Enquiry / Order: ${brand} [${partNo}] - ${desc} (₹${Number(mrp || 0).toLocaleString('en-IN')})`, 'success');
    } else {
      alert(`Staged to Enquiry / Order:\n${brand} [${partNo}]\n${desc}\nPrice: ₹${Number(mrp || 0).toLocaleString('en-IN')}`);
    }
  },

  viewInDiagram(componentName, aggregateName) {
    if (window.App && window.App.switchTab) {
      window.App.switchTab('catalogue');
      if (window.OverallCataloguePortal) {
        if (this.activeVehicleContext && this.activeVehicleContext.make) {
          OverallCataloguePortal.selectedMake = this.activeVehicleContext.make;
          OverallCataloguePortal.selectedModel = this.activeVehicleContext.model;
          OverallCataloguePortal.selectedVariant = this.activeVehicleContext.variant;
        }
        OverallCataloguePortal.navGoToStep(4);
        if (aggregateName) {
          OverallCataloguePortal.selectAggregateVisual(aggregateName);
        }
      }
      if (window.App.showToast) {
        window.App.showToast(`Navigated to Catalogue Studio for ${componentName || 'component'} (${aggregateName || 'System'})`, 'info');
      }
    }
  },

  saveState() {
    try {
      const thread = document.getElementById('cat-ai-chat-thread');
      if (thread) {
        sessionStorage.setItem('auto_nexa_chat_html', thread.innerHTML);
      }
      sessionStorage.setItem('auto_nexa_chat_state', JSON.stringify(this.state));
      sessionStorage.setItem('auto_nexa_chat_history', JSON.stringify(this.history));
      if (this.activeVehicleContext) {
        sessionStorage.setItem('auto_nexa_active_vehicle', JSON.stringify(this.activeVehicleContext));
      } else {
        sessionStorage.removeItem('auto_nexa_active_vehicle');
      }
    } catch (e) {
      console.warn('Chat state storage error', e);
    }
  },

  restoreState() {
    try {
      const savedHtml = sessionStorage.getItem('auto_nexa_chat_html');
      const savedState = sessionStorage.getItem('auto_nexa_chat_state');
      const savedHist = sessionStorage.getItem('auto_nexa_chat_history');
      const savedVeh = sessionStorage.getItem('auto_nexa_active_vehicle');
      if (savedState) this.state = JSON.parse(savedState);
      if (savedHist) this.history = JSON.parse(savedHist);
      if (savedVeh) this.activeVehicleContext = JSON.parse(savedVeh);

      const thread = document.getElementById('cat-ai-chat-thread');
      if (thread && savedHtml && savedHtml.trim().length > 0) {
        thread.innerHTML = savedHtml;
        this.scrollToBottom();
        return true;
      }
    } catch (e) {
      console.warn('Restore chat error', e);
    }
    return false;
  },

  resetChat() {
    this.activeVehicleContext = null;
    this.state = {
      make: null,
      model: null,
      fuel: null,
      year: null,
      component: null,
      sub_model: null,
      part_no: null
    };
    this.history = [];
    try {
      sessionStorage.removeItem('auto_nexa_chat_html');
      sessionStorage.removeItem('auto_nexa_chat_state');
      sessionStorage.removeItem('auto_nexa_chat_history');
      sessionStorage.removeItem('auto_nexa_active_vehicle');
    } catch (e) {}
    this.updateActiveVehicleBar();
    this.updateSideInspector(null, null);
    const thread = document.getElementById('cat-ai-chat-thread');
    if (thread) thread.innerHTML = '';
    this.renderWelcomeGreeting();
  },

  renderWelcomeGreeting() {
    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;
    thread.innerHTML = '';
  },


  isListening: false,
  recognition: null,

  toggleSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micIcon = document.getElementById('cat-ai-mic-icon');
    const input = document.getElementById('cat-ai-chat-input');

    if (!SpeechRecognition) {
      alert("Voice speech recognition is not supported in this browser. Please use Google Chrome, Edge, or Safari.");
      return;
    }

    if (this.isListening && this.recognition) {
      this.recognition.stop();
      this.isListening = false;
      if (micIcon) micIcon.textContent = '🎙️';
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'en-IN';
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      if (micIcon) micIcon.textContent = '🔴';
      this.isListening = true;

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        if (input) input.value = transcript;
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        this.isListening = false;
        if (micIcon) micIcon.textContent = '🎙️';
      };

      this.recognition.onend = () => {
        this.isListening = false;
        if (micIcon) micIcon.textContent = '🎙️';
        if (input && input.value.trim().length > 0) {
          this.handleSend();
        }
      };

      this.recognition.start();
    } catch (err) {
      console.warn("Speech recognition initialization failed:", err);
      this.isListening = false;
      if (micIcon) micIcon.textContent = '🎙️';
    }
  },

  promptVinInput() {
    const vin = prompt("Enter 17-digit Chassis / VIN Number:\n(e.g. MALBB51BLHM123456 or MA3FBA21S00123456)");
    if (vin && vin.trim().length > 0) {
      this.quickSend("VIN: " + vin.trim().toUpperCase());
    }
  },

  quickSend(text) {
    const input = document.getElementById('cat-ai-chat-input');
    if (input) input.value = text;
    this.handleSend();
  },

  async handleSend() {
    if (this.isWaiting) return;
    const input = document.getElementById('cat-ai-chat-input');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    this.appendUserMessage(message);
    this.showTypingIndicator();

    try {
      this.isWaiting = true;
      const res = await fetch('/api/catalog-ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          state: this.state,
          vehicle_context: this.activeVehicleContext
        })
      });

      const data = await res.json();
      this.hideTypingIndicator();
      this.isWaiting = false;

      if (data.state) {
        this.state = Object.assign({}, this.state, data.state);
      }

      if (data.active_vehicle && data.active_vehicle.make) {
        this.activeVehicleContext = Object.assign({}, this.activeVehicleContext || {}, data.active_vehicle);
        try {
          sessionStorage.setItem('auto_nexa_active_vehicle', JSON.stringify(this.activeVehicleContext));
        } catch (e) {}
        this.updateActiveVehicleBar();
      }

      this.renderBotResponse(data);
    } catch (err) {
      console.error('Chat error:', err);
      this.hideTypingIndicator();
      this.isWaiting = false;
      this.appendBotMessage("⚠️ I encountered a temporary connection issue. Please verify your query or try again.");
    }
  },

  appendUserMessage(text) {
    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;

    this.history.push({ role: 'user', text });

    const userHtml = `
      <div style="display: flex; justify-content: flex-end; margin-bottom: 1.1rem;">
        <div style="background: linear-gradient(135deg, #0284c7, #2563eb); color: #ffffff; padding: 0.85rem 1.25rem; border-radius: 18px 18px 4px 18px; max-width: 75%; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.2); font-weight: 650; font-size: 0.92rem; line-height: 1.45;">
          ${this.escapeHtml(text)}
        </div>
      </div>
    `;
    thread.insertAdjacentHTML('beforeend', userHtml);
    this.scrollToBottom();
    this.saveState();
  },

  appendBotMessage(text) {
    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;

    this.history.push({ role: 'bot', text });

    const botHtml = `
      <div style="display: flex; gap: 0.75rem; margin-bottom: 1.4rem; align-items: flex-start;">
        <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #0284c7, #2563eb); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.1rem; flex-shrink: 0; box-shadow: 0 3px 10px rgba(2, 132, 199, 0.25);">
          ⚡
        </div>
        <div style="flex: 1; max-width: 900px;">
          <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 4px 18px 18px 18px; padding: 1.25rem 1.4rem; box-shadow: 0 4px 16px rgba(0,0,0,0.03); color: #0f172a; font-size: 0.92rem; line-height: 1.55;">
            ${this.formatMarkdown(text)}
          </div>
        </div>
      </div>
    `;
    thread.insertAdjacentHTML('beforeend', botHtml);
    this.scrollToBottom();
    this.saveState();
  },

  showTypingIndicator() {
    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;

    const indicatorHtml = `
      <div id="cat-ai-typing-indicator" style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.1rem;">
        <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #0284c7, #2563eb); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 0.95rem;">
          ⚡
        </div>
        <div style="background: #f1f5f9; padding: 0.65rem 1rem; border-radius: 14px; display: inline-flex; gap: 4px; align-items: center;">
          <span class="typing-dot" style="animation: pulseDot 1s infinite 0.1s;">•</span>
          <span class="typing-dot" style="animation: pulseDot 1s infinite 0.3s;">•</span>
          <span class="typing-dot" style="animation: pulseDot 1s infinite 0.5s;">•</span>
          <span style="font-size: 0.78rem; color: #64748b; font-weight: 700; margin-left: 6px;">Scanning 23.6M parts...</span>
        </div>
      </div>
    `;
    thread.insertAdjacentHTML('beforeend', indicatorHtml);
    this.scrollToBottom();
  },

  hideTypingIndicator() {
    const el = document.getElementById('cat-ai-typing-indicator');
    if (el) el.remove();
  },

  renderBotResponse(data) {
    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;

    this.history.push({ role: 'bot', data });

    const reply = data.reply || '';
    const action = data.action || {};
    let actionWidgetHtml = '';

    // 1. FUEL & YEAR PROMPT WIDGET
    if (action.type === 'fuel_year_prompt') {
      actionWidgetHtml = this.renderFuelYearWidget(action);
    }
    // 2. VISUAL VARIANT CARDS SELECTION (with Oriparts 3D images)
    else if (action.type === 'visual_variants_selection') {
      actionWidgetHtml = this.renderVisualVariantsWidget(action);
    }
    // 3. PARTS MATRIX (OEM + OES + Relatable Recommendations)
    else if (action.type === 'parts_matrix') {
      actionWidgetHtml = this.renderPartsMatrixWidget(action);
    }
    // 4. DIRECT PART LOOKUP
    else if (action.type === 'direct_part_lookup') {
      actionWidgetHtml = this.renderDirectPartWidget(action);
    }
    // 5. QUICK MAKES OR MODELS CHIPS
    else if (action.type === 'quick_makes' || action.type === 'model_chips') {
      actionWidgetHtml = this.renderQuickChipsWidget(action);
    }

    const formattedReply = this.formatMarkdown(reply);

    const botMessageHtml = `
      <div style="display: flex; gap: 0.75rem; margin-bottom: 1.4rem; align-items: flex-start;">
        <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #0284c7, #2563eb); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.1rem; flex-shrink: 0; box-shadow: 0 3px 10px rgba(2, 132, 199, 0.25);">
          ⚡
        </div>
        <div style="flex: 1; max-width: 900px;">
          <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 4px 18px 18px 18px; padding: 1.25rem 1.4rem; box-shadow: 0 4px 16px rgba(0,0,0,0.03); color: #0f172a; font-size: 0.92rem; line-height: 1.55;">
            <div>${formattedReply}</div>
            ${actionWidgetHtml}
          </div>
        </div>
      </div>
    `;

    thread.insertAdjacentHTML('beforeend', botMessageHtml);
    this.scrollToBottom();
    this.saveState();
    this.updateSideInspector(this.activeVehicleContext, action);
  },

  renderFuelYearWidget(action) {
    const fuels = action.fuel_options || ['Petrol', 'Diesel', 'CNG', 'Petrol/CNG'];
    const years = action.year_options || ['2024', '2023', '2022', '2021', '2020', '2019', '2018', 'All Years'];
    const selFuel = this.state.fuel || '';
    const selYear = this.state.year || '';

    return `
      <div style="margin-top: 1.1rem; padding: 1.1rem; background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 14px;">
        <div style="font-size: 0.8rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem;">
          ⛽ 1. Select Fuel Type:
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 1rem;">
          ${fuels.map(f => {
            const isSelected = selFuel.toUpperCase() === f.toUpperCase();
            return `
              <button type="button" class="chat-choice-pill ${isSelected ? 'active-pill' : ''}" onclick="CatalogAiChat.chooseFuel('${f}')">
                ${f}
              </button>
            `;
          }).join('')}
        </div>

        <div style="font-size: 0.8rem; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem;">
          📅 2. Select Manufacturing Year:
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 1.1rem;">
          ${years.map(y => {
            const isSelected = selYear === y;
            return `
              <button type="button" class="chat-choice-pill ${isSelected ? 'active-pill' : ''}" onclick="CatalogAiChat.chooseYear('${y}')">
                ${y}
              </button>
            `;
          }).join('')}
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; border-top: 1px solid #e2e8f0; padding-top: 0.75rem; flex-wrap: wrap;">
          <span style="font-size: 0.8rem; color: #64748b;">Current Filter: <strong>${this.state.fuel || 'Any Fuel'}</strong> • <strong>${this.state.year || 'Any Year'}</strong></span>
          <button type="button" onclick="CatalogAiChat.submitFuelYear()" style="padding: 0.55rem 1.25rem; background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; font-weight: 850; font-size: 0.82rem; border: none; border-radius: 10px; cursor: pointer; box-shadow: 0 3px 10px rgba(2, 132, 199, 0.25);">
            Explore Variants ➔
          </button>
        </div>
      </div>
    `;
  },

  chooseFuel(val) {
    this.state.fuel = val;
    this.executeCommand(`SET_FUEL: ${val}`);
  },

  chooseYear(val) {
    this.state.year = val;
    this.executeCommand(`SET_YEAR: ${val}`);
  },

  submitFuelYear() {
    this.executeCommand('SHOW_VARIANTS');
  },

  renderVisualVariantsWidget(action) {
    const variants = action.variants || [];
    if (variants.length === 0) {
      return `
        <div style="padding: 1rem; text-align: center; color: #64748b; background: #f8fafc; border-radius: 12px; margin-top: 0.75rem;">
          No exact variant photos found for this combination.
          <br>
          <button type="button" onclick="CatalogAiChat.chooseVariant('ALL')" style="margin-top: 0.5rem; padding: 0.4rem 0.95rem; background: #0284c7; color: #fff; border: none; border-radius: 8px; font-weight: 800; cursor: pointer;">
            Show All Verified Parts for ${action.model} ➔
          </button>
        </div>
      `;
    }

    return `
      <div style="margin-top: 0.85rem;">
        <div style="font-size: 0.78rem; font-weight: 850; color: #475569; margin-bottom: 0.55rem; display: flex; align-items: center; gap: 0.35rem;">
          <span>📋</span> <span>Select Vehicle Variant Trim:</span>
          <span style="font-size: 0.7rem; color: #64748b; font-weight: 700;">(${variants.length} available)</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.55rem;">
          ${variants.map(v => `
            <button type="button" onclick="CatalogAiChat.chooseVariant('${v.subModel.replace(/'/g, "\\'")}')" 
                    style="display: inline-flex; align-items: center; gap: 0.65rem; padding: 0.45rem 0.85rem; background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 10px; cursor: pointer; transition: all 0.18s ease; text-align: left; box-shadow: 0 1px 4px rgba(0,0,0,0.03);"
                    onmouseover="this.style.borderColor='#0284c7'; this.style.background='#eff6ff'; this.style.transform='translateY(-1px)';"
                    onmouseout="this.style.borderColor='#cbd5e1'; this.style.background='#ffffff'; this.style.transform='none';">
              <img src="${v.image || 'images/home_menu_catalogue.jpg'}" alt="${this.escapeHtml(v.subModel)}" style="width: 40px; height: 28px; object-fit: contain; border-radius: 4px; background: #f8fafc; padding: 2px; flex-shrink: 0;" onerror="this.style.display='none';">
              <div style="min-width: 0;">
                <div style="font-size: 0.8rem; font-weight: 850; color: #0f172a; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 220px;" title="${this.escapeHtml(v.subModel)}">
                  ${this.escapeHtml(v.subModel)}
                </div>
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; margin-top: 0.1rem;">
                  <span style="color: #0284c7; font-weight: 800;">${this.escapeHtml(v.fuelType || 'All Fuels')}</span>
                  ${v.years ? ' • ' + this.escapeHtml(v.years) : ''}
                </div>
              </div>
            </button>
          `).join('')}
        </div>
      </div>
    `;
  },

  chooseVariant(variantName) {
    this.executeCommand(`SELECT_VARIANT: ${variantName}`);
  },

  renderPartsMatrixWidget(action) {
    const oem = action.oem;
    const oesList = action.oes || [];
    const relatable = action.relatable || [];
    const diagNote = action.diagnostic_note || '';
    const compName = action.component || (oem && oem.desc) || 'Component';
    const aggName = action.aggregate || 'BRAKE SYSTEM';

    // 1. Diagnostic Note / Mechanic Translation Banner
    let diagNoteHtml = '';
    if (diagNote) {
      diagNoteHtml = `
        <div style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 0.75rem 1.1rem; border-radius: 0 10px 10px 0; margin-bottom: 0.95rem; font-size: 0.82rem; color: #334155; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
          <div style="font-weight: 850; color: #0284c7; display: flex; align-items: center; gap: 0.35rem; margin-bottom: 0.2rem;">
            <span>🔧 Diagnostic Note / Mechanic Translation:</span>
          </div>
          <div style="line-height: 1.45;">${this.escapeHtml(diagNote)}</div>
        </div>
      `;
    }

    // 2. OEM Structured Component Card
    let oemHtml = '';
    if (oem) {
      oemHtml = `
        <div class="cat-ai-comp-card oem-highlight" style="background: #ffffff; border: 1.5px solid #86efac; border-left: 5px solid #16a34a; border-radius: 14px; padding: 1.25rem 1.4rem; box-shadow: 0 2px 12px rgba(22, 101, 52, 0.06); margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 260px;">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; flex-wrap: wrap;">
                <span style="font-size: 0.72rem; font-weight: 900; background: #dcfce7; color: #166534; padding: 0.2rem 0.6rem; border-radius: 6px; border: 1px solid #bbf7d0; letter-spacing: 0.03em;">
                  ⭐ OEM DEALERSHIP GENUINE
                </span>
                <span style="font-size: 0.74rem; color: #475569; font-family: monospace; font-weight: 750;">
                  Line Code ${this.escapeHtml(oem.lineCode || 'OE')} • ${this.escapeHtml(oem.brand)} OE
                </span>
              </div>

              <div style="font-size: 1.15rem; font-weight: 900; color: #0f172a; margin-bottom: 0.35rem; font-family: 'Outfit', sans-serif;">
                ${this.escapeHtml(oem.desc)}
              </div>

              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem; flex-wrap: wrap;">
                <span style="font-size: 0.8rem; font-weight: 750; color: #475569;">Part No:</span>
                <span style="font-family: monospace; font-size: 1rem; font-weight: 900; color: #166534; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 0.2rem 0.6rem; border-radius: 6px; letter-spacing: 0.05em;">
                  ${this.escapeHtml(oem.partNo)}
                </span>
                <button type="button" onclick="CatalogAiChat.copyToClipboard('${this.escapeJs(oem.partNo)}', this)" style="padding: 0.2rem 0.6rem; font-size: 0.72rem; font-weight: 800; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; color: #334155; cursor: pointer; transition: all 0.15s;">
                  📋 Copy
                </button>
              </div>

              <!-- Quick Status Badges -->
              <div style="display: flex; flex-wrap: wrap; gap: 0.45rem;">
                <span style="display: inline-flex; align-items: center; gap: 0.35rem; background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 0.72rem; font-weight: 800; padding: 0.2rem 0.55rem; border-radius: 6px;">
                  ✔ 100% Direct Fitment (${this.escapeHtml(oem.make)} ${this.escapeHtml(oem.model)})
                </span>
                <span style="display: inline-flex; align-items: center; gap: 0.35rem; background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; font-size: 0.72rem; font-weight: 800; padding: 0.2rem 0.55rem; border-radius: 6px;">
                  🟢 In Stock (Dispatch Ready)
                </span>
              </div>
            </div>

            <!-- Price & Actions Column -->
            <div style="text-align: right; min-width: 180px;">
              <div style="font-size: 0.72rem; color: #64748b; font-weight: 750; text-transform: uppercase; letter-spacing: 0.03em;">Official Dealership MRP</div>
              <div style="font-size: 1.65rem; font-weight: 900; color: #166534; font-family: 'Outfit', sans-serif; margin-top: 0.1rem;">
                ${oem.mrp && oem.mrp > 0 ? '₹' + Number(oem.mrp).toLocaleString('en-IN') : 'Price on Request'}
              </div>
              <div style="display: flex; gap: 0.45rem; justify-content: flex-end; margin-top: 0.85rem; flex-wrap: wrap;">
                <button type="button" onclick="CatalogAiChat.viewInDiagram('${this.escapeJs(compName)}', '${this.escapeJs(aggName)}')" class="cat-ai-action-btn secondary">
                  <span>📐 View in 3D Diagram</span>
                </button>
                <button type="button" onclick="CatalogAiChat.showFitmentModal('${this.escapeJs(oem.partNo)}')" class="cat-ai-action-btn secondary">
                  <span>🔍 Fitment &amp; Specs</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    // 3. OES Conversion Alternatives Cards
    let oesHtml = '';
    if (oesList.length > 0) {
      oesHtml = `
        <div style="margin-top: 1rem; margin-bottom: 1.25rem;">
          <div style="background: linear-gradient(135deg, #f0fdf4, #ecfdf5); border: 1.5px solid #86efac; border-radius: 12px; padding: 0.85rem 1.15rem; margin-bottom: 0.85rem; display: flex; align-items: flex-start; gap: 0.75rem;">
            <span style="font-size: 1.4rem; flex-shrink: 0;">💡</span>
            <div>
              <div style="font-weight: 850; color: #166534; font-size: 0.86rem; font-family: 'Outfit', sans-serif;">
                OES Conversion Opportunity: Verified Tier-1 OES Available at ~25% Lower Cost!
              </div>
              <div style="font-size: 0.78rem; color: #15803d; margin-top: 0.15rem; line-height: 1.35;">
                OE supplier components (Bosch, TVS Girling, Valeo, LuK, Brembo) share identical physical tooling and OE quality with OEM dealership parts, providing ~25% direct savings with standard warranty.
              </div>
            </div>
          </div>

          <div style="font-size: 0.82rem; font-weight: 900; color: #334155; margin-bottom: 0.65rem; display: flex; align-items: center; gap: 0.4rem;">
            <span>🛡️ Verified Tier-1 OES Direct Equivalents</span>
            <span style="font-size: 0.72rem; color: #64748b; font-weight: 700;">(${oesList.length} Options)</span>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 0.75rem;">
            ${oesList.map(p => {
              const diffPercent = (oem && oem.mrp && p.mrp && oem.mrp > p.mrp)
                ? Math.round(((oem.mrp - p.mrp) / oem.mrp) * 100)
                : 25;
              const oesPrice = (p.mrp && p.mrp > 0) ? p.mrp : Math.round((oem?.mrp || 1500) * 0.75);
              return `
                <div class="cat-ai-comp-card" style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 6px rgba(0,0,0,0.02); transition: border-color 0.15s;">
                  <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                      <span style="font-size: 0.74rem; font-weight: 850; background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; padding: 0.15rem 0.5rem; border-radius: 6px;">
                        ${this.escapeHtml(p.brand)} (Tier-1 OES)
                      </span>
                      <span style="font-size: 0.7rem; font-weight: 850; background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 0.15rem 0.45rem; border-radius: 6px;">
                        Save ${diffPercent}% vs OEM
                      </span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.3rem;">
                      <span style="font-family: monospace; font-size: 0.98rem; font-weight: 900; color: #0284c7;">${this.escapeHtml(p.partNo)}</span>
                      <button type="button" onclick="CatalogAiChat.copyToClipboard('${this.escapeJs(p.partNo)}', this)" style="padding: 1px 6px; font-size: 0.68rem; border-radius: 4px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer;">📋 Copy</button>
                    </div>
                    <div style="font-size: 0.84rem; font-weight: 800; color: #1e293b; margin-top: 0.25rem;">
                      ${this.escapeHtml(p.desc)}
                    </div>
                    <div style="font-size: 0.72rem; color: #64748b; margin-top: 0.35rem;">
                      Line Code: <strong>${this.escapeHtml(p.lineCode || 'OES')}</strong> • Fitment: <strong>100% Direct Match</strong>
                    </div>
                  </div>

                  <div style="margin-top: 0.85rem; padding-top: 0.65rem; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <div style="font-size: 0.68rem; color: #64748b; font-weight: 750;">OES Unit MRP</div>
                      <div style="font-size: 1.2rem; font-weight: 900; color: #059669; font-family: 'Outfit', sans-serif;">
                        ₹${Number(oesPrice).toLocaleString('en-IN')}
                      </div>
                    </div>
                    <button type="button" onclick="CatalogAiChat.showFitmentModal('${this.escapeJs(p.partNo)}')" class="cat-ai-action-btn secondary" style="padding: 0.35rem 0.85rem; font-size: 0.76rem;">
                      🔍 View Fitment
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // 4. Relatable Technician Recommendations
    let relatableHtml = '';
    if (relatable.length > 0) {
      relatableHtml = `
        <div style="background: linear-gradient(135deg, #fef3c7, #fffbeb); border: 1.5px solid #fde68a; border-radius: 14px; padding: 1.1rem; margin-top: 1rem;">
          <div style="display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem;">💡</span>
            <div style="font-weight: 900; font-size: 0.88rem; color: #92400e; font-family: 'Outfit', sans-serif;">
              Technician & Relatable Parts Recommendation
            </div>
          </div>
          <p style="font-size: 0.82rem; color: #78350f; margin: 0 0 0.85rem 0; line-height: 1.45;">
            Automotive maintenance best practice: when servicing <strong>${this.escapeHtml(action.component || 'this part')}</strong>, technicians advise inspecting and pairing with:
          </p>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0.65rem;">
            ${relatable.map(r => `
              <div style="background: #ffffff; border: 1px solid #fde68a; border-radius: 10px; padding: 0.75rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                <div>
                  <div style="font-size: 0.84rem; font-weight: 850; color: #0f172a; margin-bottom: 0.25rem;">
                    ${r.icon || '🔧'} ${this.escapeHtml(r.label)}
                  </div>
                  <div style="font-size: 0.74rem; color: #64748b; line-height: 1.35;">
                    ${this.escapeHtml(r.why)}
                  </div>
                </div>
                <button type="button" onclick="CatalogAiChat.chooseCompanion('${this.escapeJs(r.component)}')" style="margin-top: 0.65rem; width: 100%; padding: 0.4rem; background: #fef3c7; border: 1px solid #f59e0b; color: #b45309; font-weight: 850; font-size: 0.74rem; border-radius: 6px; cursor: pointer; transition: all 0.15s;">
                  Show ${this.escapeHtml(r.label)} ➔
                </button>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    return `
      <div style="margin-top: 1rem;">
        ${diagNoteHtml}
        ${oemHtml}
        ${oesHtml}
        ${relatableHtml}
      </div>
    `;
  },

  chooseCompanion(compTarget) {
    this.executeCommand(`SELECT_COMPANION: ${compTarget}`);
  },

  renderDirectPartWidget(action) {
    const p = action.part || {};
    const oes = action.oes || [];
    const lineCodeAlertHtml = (p.crossLineCodeResolved || p.lineCodeAlert) ? `
      <div style="margin-bottom: 0.85rem; background: #fffbeb; border: 1.5px solid #fde68a; border-radius: 10px; padding: 0.55rem 0.85rem; display: flex; align-items: center; gap: 0.6rem;">
        <span style="font-size: 1.1rem;">⚡</span>
        <div>
          <strong style="color: #92400e; font-size: 0.8rem; display: block;">Line Code Auto-Resolved</strong>
          <span style="color: #b45309; font-size: 0.76rem;">${this.escapeHtml(p.lineCodeAlert || `Searched with Line Code '${p.inputLineCode || 'other'}', but verified active under Line Code ${p.lineCode} (${p.brand})`)}</span>
        </div>
      </div>
    ` : '';

    return `
      <div class="cat-ai-comp-card oem-highlight" style="background: #ffffff; border: 1.5px solid #86efac; border-left: 5px solid #16a34a; border-radius: 14px; padding: 1.25rem 1.4rem; box-shadow: 0 2px 12px rgba(22, 101, 52, 0.06); margin-top: 1rem;">
        ${lineCodeAlertHtml}
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.85rem;">
          <div style="flex: 1; min-width: 260px;">
            <div style="display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.35rem;">
              <span class="cat-ai-oem-pill">${this.escapeHtml(p.brand || 'GENUINE')}</span>
              <span style="font-size: 0.72rem; color: #64748b; font-family: monospace;">Line Code ${this.escapeHtml(p.lineCode || 'OE')}</span>
            </div>
            <div style="font-size: 1.15rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif;">
              ${this.escapeHtml(p.desc)}
            </div>
            <div style="font-family: monospace; font-size: 1.05rem; font-weight: 900; color: #166534; margin: 0.25rem 0;">
              Part No: <span style="background: #dcfce7; padding: 0.15rem 0.45rem; border-radius: 6px;">${this.escapeHtml(p.partNo)}</span>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.45rem;">
              <span class="cat-ai-badge-fitment">✔ Fitment Match: 100% Direct Specification</span>
              <span class="cat-ai-badge-stock">🟢 Stock Availability: In Stock</span>
            </div>
          </div>
          <div style="text-align: right; min-width: 190px;">
            <div style="font-size: 0.72rem; color: #64748b; font-weight: 750;">Official Dealership MRP</div>
            <div style="font-size: 1.45rem; font-weight: 900; color: #166534; font-family: 'Outfit', sans-serif;">
              ${p.mrp && p.mrp > 0 ? '₹' + Number(p.mrp).toLocaleString('en-IN') : 'Price on Request'}
            </div>
            <div style="display: flex; gap: 0.45rem; justify-content: flex-end; margin-top: 0.85rem; flex-wrap: wrap;">
              <button type="button" onclick="CatalogAiChat.viewInDiagram('${this.escapeJs(p.components || p.desc)}', '${this.escapeJs(p.aggregate || 'BRAKE SYSTEM')}')" class="cat-ai-action-btn secondary">
                <span>📐 View in Diagram</span>
              </button>
              <button type="button" onclick="CatalogAiChat.showFitmentModal('${this.escapeJs(p.partNo)}')" class="cat-ai-action-btn secondary">
                <span>🔍 Fitment &amp; Specs</span>
              </button>
            </div>
          </div>
        </div>

        ${oes.length > 0 ? `
          <div style="margin-top: 1.1rem; padding-top: 0.9rem; border-top: 1px solid #e2e8f0;">
            <div style="font-size: 0.8rem; font-weight: 850; color: #334155; margin-bottom: 0.5rem;">
              🛡️ Interchangeable OES Alternatives:
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
              ${oes.map(o => `
                <span class="tag-pill" onclick="CatalogAiChat.showFitmentModal('${this.escapeJs(o.partNo)}')" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 0.35rem 0.65rem; border-radius: 8px; font-size: 0.76rem; font-weight: 750; cursor: pointer; color: #0f172a;">
                  <strong>${this.escapeHtml(o.brand)}</strong> (${this.escapeHtml(o.partNo)}) - ₹${o.mrp} ➔
                </span>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  },

  renderQuickChipsWidget(action) {
    if (action.type === 'quick_makes') {
      const makes = action.makes || [];
      return `
        <div style="margin-top: 0.85rem; display: flex; flex-wrap: wrap; gap: 0.45rem;">
          ${makes.map(m => `
            <button type="button" class="chat-choice-pill" onclick="CatalogAiChat.quickSend('${m}')">
              🚗 ${m}
            </button>
          `).join('')}
        </div>
      `;
    }
    if (action.type === 'model_chips') {
      const models = action.models || [];
      return `
        <div style="margin-top: 0.85rem; display: flex; flex-wrap: wrap; gap: 0.45rem;">
          ${models.map(mdl => `
            <button type="button" class="chat-choice-pill" onclick="CatalogAiChat.quickSend('${mdl}')">
              ${mdl}
            </button>
          `).join('')}
        </div>
      `;
    }
    return '';
  },

  async showFitmentModal(partNo) {
    if (!partNo) return;
    const modal = document.getElementById('cat-ai-fitment-modal');
    const body = document.getElementById('cat-ai-modal-body');
    const title = document.getElementById('cat-ai-modal-title');
    const subtitle = document.getElementById('cat-ai-modal-subtitle');
    if (!modal || !body) return;

    modal.style.display = 'flex';
    if (title) title.innerHTML = `Fitment & Specs: <code>${partNo}</code>`;
    if (subtitle) subtitle.textContent = 'Querying live 23.6M multi-OEM catalogue database...';

    body.innerHTML = `
      <div style="text-align: center; padding: 3rem 1rem;">
        <div style="font-size: 2rem; margin-bottom: 0.8rem; animation: pulseDot 1s infinite;">🔍</div>
        <div style="font-size: 1rem; font-weight: 850; color: #0f172a;">Fetching Verified Vehicle Fitment for Part #${partNo}...</div>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.4rem;">Scanning OEM applications & interchangeable OES matrices</div>
      </div>
    `;

    try {
      const res = await fetch(`/api/overall-catalogue/part/${encodeURIComponent(partNo)}`);
      const data = await res.json();
      if (!data || data.error) {
        body.innerHTML = `
          <div style="padding: 2.5rem; text-align: center;">
            <div style="font-size: 2.2rem; color: #ea580c; margin-bottom: 0.5rem;">⚠️</div>
            <div style="font-size: 1.05rem; font-weight: 850; color: #0f172a;">Part Details Not Found</div>
            <div style="font-size: 0.84rem; color: #64748b; margin-top: 0.35rem;">Could not locate detailed record for part number <code>${this.escapeHtml(partNo)}</code></div>
          </div>
        `;
        return;
      }

      const p = data.part || {};
      const apps = data.applications || [];
      const oes = data.oesEquivalents || [];

      if (title) title.innerHTML = `<span style="color: #38bdf8;">${p.partNo || partNo}</span> • ${p.brand || 'OE'} Genuine`;
      if (subtitle) subtitle.textContent = `${p.desc || 'Automotive Component'} • ${p.components || ''} (${p.aggregate || ''})`;

      body.innerHTML = `
        <!-- Top Summary Bar -->
        <div style="background: linear-gradient(135deg, #f8fafc, #f1f5f9); border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 1.15rem; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
          <div>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem; flex-wrap: wrap;">
              <span class="cat-ai-fitment-badge" style="background: #eff6ff; color: #1e40af; border-color: #bfdbfe;">
                🏷️ Brand: <strong>${p.brand || 'OEM'}</strong>
              </span>
              <span class="cat-ai-fitment-badge">
                Line Code: <strong>${p.lineCode || 'N/A'}</strong>
              </span>
              <span class="cat-ai-fitment-badge">
                Aggregate: <strong>${p.aggregate || 'SPARE PARTS'}</strong>
              </span>
            </div>
            <div style="font-size: 1.1rem; font-weight: 900; color: #0f172a; font-family: 'Outfit', sans-serif;">
              ${p.desc || 'Automotive Component'}
            </div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">
              Sub-Aggregate: <strong>${p.sub_aggregate || 'N/A'}</strong> • Component: <strong>${p.components || 'N/A'}</strong>
            </div>
          </div>

          <div style="text-align: right;">
            <div style="font-size: 0.74rem; color: #64748b; font-weight: 750;">Official Maximum Retail Price</div>
            <div style="font-size: 1.7rem; font-weight: 900; color: #059669; font-family: 'Outfit', sans-serif;">
              ${p.mrp && p.mrp > 0 ? '₹' + Number(p.mrp).toLocaleString('en-IN') : '₹ ' + (p.listPrice || 'On Request')}
            </div>
            <button type="button" onclick="navigator.clipboard.writeText('${p.partNo}'); this.textContent='✓ Copied!';" style="margin-top: 0.35rem; padding: 0.3rem 0.75rem; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.72rem; font-weight: 800; color: #475569; cursor: pointer;">
              📋 Copy Part #
            </button>
          </div>
        </div>

        <!-- Section 1: Compatible Vehicle Fitment List -->
        <div style="margin-bottom: 1.4rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
            <div style="font-size: 0.88rem; font-weight: 900; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 0.45rem;">
              <span>🚗 Verified Vehicle Application Fitment</span>
              <span style="font-size: 0.72rem; background: #eff6ff; color: #0284c7; padding: 0.15rem 0.5rem; border-radius: 10px; font-weight: 850;">
                ${apps.length} Variants
              </span>
            </div>
          </div>

          ${apps.length > 0 ? `
            <div style="max-height: 240px; overflow-y: auto; border: 1.5px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
              <table class="cat-ai-fitment-table">
                <thead>
                  <tr>
                    <th>Make</th>
                    <th>Model</th>
                    <th>Trim / Variant Sub-Model</th>
                    <th>Component Verified</th>
                  </tr>
                </thead>
                <tbody>
                  ${apps.map(a => `
                    <tr>
                      <td style="font-weight: 850; color: #0f172a;">${a.make || 'GENERIC'}</td>
                      <td style="font-weight: 800; color: #0284c7;">${a.model || ''}</td>
                      <td style="color: #334155;">${a.subModel || 'Universal Trim'}</td>
                      <td><span style="background: #f1f5f9; padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.74rem; font-weight: 750;">${a.component || p.components || 'Direct Fit'}</span></td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : `
            <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 10px; padding: 1rem; text-align: center; color: #64748b; font-size: 0.84rem;">
              Universal application across platforms matching OEM ${p.brand || 'OE'} specifications.
            </div>
          `}
        </div>

        <!-- Section 2: Interchangeable OES Alternatives -->
        <div>
          <div style="font-size: 0.88rem; font-weight: 900; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.65rem; display: flex; align-items: center; gap: 0.45rem;">
            <span>🛡️ Interchangeable Tier-1 OES & Aftermarket Parts</span>
            <span style="font-size: 0.72rem; background: #f0fdf4; color: #16a34a; padding: 0.15rem 0.5rem; border-radius: 10px; font-weight: 850;">
              ${oes.length} Verified
            </span>
          </div>

          ${oes.length > 0 ? `
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 0.75rem;">
              ${oes.map(o => `
                <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 0.85rem; display: flex; flex-direction: column; justify-content: space-between;">
                  <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                      <span style="font-size: 0.72rem; font-weight: 850; background: #eff6ff; color: #1e40af; padding: 0.15rem 0.45rem; border-radius: 6px;">
                        ${o.brand || 'OES BRAND'}
                      </span>
                      <span style="font-size: 0.7rem; color: #64748b; font-family: monospace;">Line Code ${o.lineCode || 'OES'}</span>
                    </div>
                    <div style="font-family: monospace; font-size: 0.95rem; font-weight: 900; color: #0284c7;">
                      ${o.partNo}
                    </div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: #334155; margin-top: 0.2rem;">
                      ${o.desc || 'Equivalent OES replacement'}
                    </div>
                  </div>
                  <div style="margin-top: 0.75rem; padding-top: 0.5rem; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.05rem; font-weight: 900; color: #059669; font-family: 'Outfit', sans-serif;">
                      ${o.mrp && o.mrp > 0 ? '₹' + Number(o.mrp).toLocaleString('en-IN') : 'Check Price'}
                    </span>
                    <button type="button" onclick="CatalogAiChat.showFitmentModal('${o.partNo}')" style="padding: 0.25rem 0.6rem; font-size: 0.7rem; font-weight: 800; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; cursor: pointer; color: #0284c7;">
                      Inspect This ➔
                    </button>
                  </div>
                </div>
              `).join('')}
            </div>
          ` : `
            <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 10px; padding: 1rem; text-align: center; color: #64748b; font-size: 0.84rem;">
              No distinct cross-brand aftermarket SKUs recorded for this OE reference yet.
            </div>
          `}
        </div>
      `;
    } catch (err) {
      console.error(err);
      body.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: #dc2626;">
          ⚠️ Failed to load fitment details. Please check connection.
        </div>
      `;
    }
  },

  closeFitmentModal() {
    const modal = document.getElementById('cat-ai-fitment-modal');
    if (modal) modal.style.display = 'none';
  },

  executeCommand(cmd) {
    this.showTypingIndicator();
    this.isWaiting = true;

    fetch('/api/catalog-ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: cmd,
        state: this.state,
        vehicle_context: this.activeVehicleContext
      })
    })
    .then(r => r.json())
    .then(data => {
      this.hideTypingIndicator();
      this.isWaiting = false;
      if (data.state) {
        this.state = Object.assign({}, this.state, data.state);
      }
      if (data.active_vehicle && data.active_vehicle.make) {
        this.activeVehicleContext = Object.assign({}, this.activeVehicleContext || {}, data.active_vehicle);
        try {
          sessionStorage.setItem('auto_nexa_active_vehicle', JSON.stringify(this.activeVehicleContext));
        } catch (e) {}
        this.updateActiveVehicleBar();
      }
      this.renderBotResponse(data);
    })
    .catch(err => {
      console.error(err);
      this.hideTypingIndicator();
      this.isWaiting = false;
    });
  },

  formatMarkdown(text) {
    if (!text) return '';
    let html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code style="background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.88em; font-family: monospace;">$1</code>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    return html;
  },

  escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  },

  escapeJs(text) {
    if (text === null || text === undefined) return '';
    return String(text)
      .replace(/\\/g, '\\\\')
      .replace(/'/g, "\\'")
      .replace(/"/g, '&quot;')
      .replace(/\n/g, ' ')
      .replace(/\r/g, '');
  },

  copyToClipboard(text, btn) {
    if (!text) return;
    navigator.clipboard.writeText(String(text)).then(() => {
      if (btn) {
        const orig = btn.innerHTML;
        btn.innerHTML = '✓ Copied';
        btn.style.color = '#16a34a';
        setTimeout(() => {
          btn.innerHTML = orig;
          btn.style.color = '';
        }, 1500);
      }
      if (window.App && window.App.showToast) {
        window.App.showToast(`Copied to clipboard: ${text}`, 'success');
      }
    }).catch(err => {
      console.warn('Clipboard write error', err);
    });
  },

  scrollToBottom() {
    const container = document.getElementById('cat-ai-chat-thread');
    if (container) {
      setTimeout(() => {
        container.scrollTop = container.scrollHeight;
      }, 50);
    }
  }
};

window.CatalogAiChat = CatalogAiChat;
