/**
 * AutoNexa Catalog AI Conversational Chatbot
 * ==========================================
 * Interactive diagnostic and parts chatbot with multi-step vehicle identification,
 * fuel & year selection, visual 3D Oriparts vehicle cards, OEM & Tier-1 OES matrix,
 * and proactive relatable companion parts recommendations.
 */

const CatalogAiChat = {
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

  init() {
    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;

    // Attach Enter key to input
    const input = document.getElementById('cat-ai-chat-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.handleSend();
        }
      });
    }

    // If chat thread is empty, render initial greeting
    if (this.history.length === 0) {
      this.renderWelcomeGreeting();
    }
  },

  resetChat() {
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
    const thread = document.getElementById('cat-ai-chat-thread');
    if (thread) thread.innerHTML = '';
    this.renderWelcomeGreeting();
  },

  renderWelcomeGreeting() {
    const welcomeHtml = `
      <div class="chat-bot-bubble" style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 18px; padding: 1.4rem; box-shadow: 0 4px 16px rgba(0,0,0,0.03); max-width: 820px; margin-bottom: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
          <div style="width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #0284c7); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.2rem; box-shadow: 0 3px 10px rgba(139, 92, 246, 0.3);">
            🤖
          </div>
          <div>
            <div style="font-weight: 900; font-size: 1.05rem; color: #0f172a; font-family: 'Outfit', sans-serif;">
              AutoNexa Catalog AI Copilot
            </div>
            <div style="font-size: 0.78rem; color: #059669; font-weight: 750;">
              🟢 Active Diagnostic Assistant • 23.6M+ Parts Indexed
            </div>
          </div>
        </div>

        <div style="font-size: 0.92rem; color: #334155; line-height: 1.6; margin-bottom: 1.1rem;">
          Hello! I am your AI spare parts specialist. You can ask me naturally in <strong>English, Hindi/Hinglish, or mechanic terms</strong>, or enter any raw OEM part number.
          <br><br>
          For example, try searching:
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
          <button type="button" class="chat-prompt-pill" onclick="CatalogAiChat.quickSend('Grand i10 Nios brake pad')">
            🏎️ Grand i10 Nios brake pad
          </button>
          <button type="button" class="chat-prompt-pill" onclick="CatalogAiChat.quickSend('Swift diesel 2018 oil filter')">
            🛢️ Swift diesel 2018 oil filter
          </button>
          <button type="button" class="chat-prompt-pill" onclick="CatalogAiChat.quickSend('Innova clutch plate')">
            ⚙️ Innova clutch plate
          </button>
          <button type="button" class="chat-prompt-pill" onclick="CatalogAiChat.quickSend('Creta shocker kharab hai')">
            🔧 Creta shocker kharab hai
          </button>
          <button type="button" class="chat-prompt-pill" onclick="CatalogAiChat.quickSend('21658101B4A05')">
            🏷️ Part No: 21658101B4A05
          </button>
        </div>
      </div>
    `;

    const thread = document.getElementById('cat-ai-chat-thread');
    if (thread) {
      thread.innerHTML = welcomeHtml;
      this.scrollToBottom();
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
          state: this.state
        })
      });

      const data = await res.json();
      this.hideTypingIndicator();
      this.isWaiting = false;

      if (data.state) {
        this.state = Object.assign({}, this.state, data.state);
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

    const userHtml = `
      <div style="display: flex; justify-content: flex-end; margin-bottom: 1.1rem;">
        <div style="background: linear-gradient(135deg, #0284c7, #2563eb); color: #ffffff; padding: 0.85rem 1.25rem; border-radius: 18px 18px 4px 18px; max-width: 75%; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.2); font-weight: 650; font-size: 0.92rem; line-height: 1.45;">
          ${this.escapeHtml(text)}
        </div>
      </div>
    `;
    thread.insertAdjacentHTML('beforeend', userHtml);
    this.scrollToBottom();
  },

  showTypingIndicator() {
    const thread = document.getElementById('cat-ai-chat-thread');
    if (!thread) return;

    const indicatorHtml = `
      <div id="cat-ai-typing-indicator" style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.1rem;">
        <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #0284c7); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 0.95rem;">
          🤖
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
        <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #0284c7); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.1rem; flex-shrink: 0; box-shadow: 0 3px 10px rgba(139, 92, 246, 0.25);">
          🤖
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

        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 0.75rem; border-top: 1px solid #e2e8f0; padding-top: 0.75rem;">
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
        <div style="padding: 1.25rem; text-align: center; color: #64748b; background: #f8fafc; border-radius: 12px; margin-top: 0.9rem;">
          No exact variant photos found for this combination.
          <br>
          <button type="button" onclick="CatalogAiChat.chooseVariant('ALL')" style="margin-top: 0.6rem; padding: 0.45rem 1rem; background: #0284c7; color: #fff; border: none; border-radius: 8px; font-weight: 800; cursor: pointer;">
            Show All Verified Parts for ${action.model} ➔
          </button>
        </div>
      `;
    }

    return `
      <div style="margin-top: 1.1rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.9rem;">
          ${variants.map(v => `
            <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; transition: transform 0.15s, box-shadow 0.15s; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
              <div style="height: 130px; background: #f8fafc; display: flex; align-items: center; justify-content: center; padding: 0.5rem; border-bottom: 1px solid #f1f5f9;">
                <img src="${v.image || 'images/home_menu_catalogue.jpg'}" alt="${v.subModel}" style="max-height: 100%; max-width: 100%; object-fit: contain;" onerror="this.src='images/home_menu_catalogue.jpg';">
              </div>
              <div style="padding: 0.9rem; flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                  <div style="font-size: 0.84rem; font-weight: 850; color: #0f172a; line-height: 1.35; margin-bottom: 0.45rem;">
                    ${v.subModel}
                  </div>
                  <div style="display: flex; gap: 0.35rem; flex-wrap: wrap; margin-bottom: 0.75rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; background: #f0fdf4; color: #166534; padding: 0.15rem 0.5rem; border-radius: 6px; border: 1px solid #bbf7d0;">
                      ⛽ ${v.fuelType || 'All Fuels'}
                    </span>
                    <span style="font-size: 0.72rem; font-weight: 800; background: #eff6ff; color: #1e40af; padding: 0.15rem 0.5rem; border-radius: 6px; border: 1px solid #bfdbfe;">
                      📅 ${v.years || 'All Years'}
                    </span>
                  </div>
                </div>
                <button type="button" onclick="CatalogAiChat.chooseVariant('${v.subModel.replace(/'/g, "\\'")}')" style="width: 100%; padding: 0.55rem; background: #0284c7; color: #ffffff; font-weight: 850; font-size: 0.8rem; border: none; border-radius: 8px; cursor: pointer; transition: background 0.15s;">
                  Select This Variant ➔
                </button>
              </div>
            </div>
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

    let oemHtml = '';
    if (oem) {
      oemHtml = `
        <div style="background: linear-gradient(135deg, #f0fdf4, #ffffff); border: 2px solid #86efac; border-radius: 14px; padding: 1.15rem; margin-bottom: 1rem; position: relative;">
          <div style="position: absolute; top: -10px; left: 18px; background: #16a34a; color: #fff; font-size: 0.68rem; font-weight: 900; padding: 0.2rem 0.65rem; border-radius: 10px; letter-spacing: 0.5px;">
            ⭐ OEM GENUINE SPECIFICATION
          </div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-top: 0.35rem; flex-wrap: wrap; gap: 0.75rem;">
            <div>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                <span style="font-size: 0.75rem; font-weight: 900; color: #166534; background: #dcfce7; padding: 0.15rem 0.55rem; border-radius: 6px;">${oem.brand} OE</span>
                <span style="font-size: 0.72rem; color: #64748b; font-family: monospace;">Line Code ${oem.lineCode || 'OE'}</span>
              </div>
              <div style="font-family: monospace; font-size: 1.1rem; font-weight: 900; color: #0f172a; margin-bottom: 0.2rem;">
                ${oem.partNo}
              </div>
              <div style="font-size: 0.88rem; font-weight: 800; color: #334155;">
                ${oem.desc}
              </div>
              <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.35rem;">
                Fitment: <strong>${oem.make} ${oem.model}</strong> • ${oem.subModel || 'All trims'}
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 0.72rem; color: #64748b; font-weight: 750;">Official OE MRP</div>
              <div style="font-size: 1.45rem; font-weight: 900; color: #16a34a; font-family: 'Outfit', sans-serif;">
                ${oem.mrp && oem.mrp > 0 ? '₹' + Number(oem.mrp).toLocaleString('en-IN') : 'Price on Request'}
              </div>
              <button type="button" onclick="App.inspectPartInMaster('${oem.partNo}')" style="margin-top: 0.45rem; padding: 0.35rem 0.75rem; font-size: 0.74rem; font-weight: 800; background: #dcfce7; border: 1px solid #86efac; color: #166534; border-radius: 6px; cursor: pointer;">
                Inspect Fitment ↗
              </button>
            </div>
          </div>
        </div>
      `;
    }

    let oesHtml = '';
    if (oesList.length > 0) {
      oesHtml = `
        <div style="margin-bottom: 1.25rem;">
          <div style="font-size: 0.82rem; font-weight: 900; color: #334155; margin-bottom: 0.65rem; display: flex; align-items: center; gap: 0.4rem;">
            <span>🛡️ Verified Tier-1 OES Aftermarket Alternatives</span>
            <span style="font-size: 0.72rem; color: #64748b; font-weight: 700;">(${oesList.length} Options)</span>
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.75rem;">
            ${oesList.map(p => {
              const diffPercent = (oem && oem.mrp && p.mrp && oem.mrp > p.mrp)
                ? Math.round(((oem.mrp - p.mrp) / oem.mrp) * 100)
                : 0;
              return `
                <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 0.85rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                  <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                      <span style="font-size: 0.74rem; font-weight: 850; background: #eff6ff; color: #1e40af; padding: 0.15rem 0.5rem; border-radius: 6px;">
                        ${p.brand}
                      </span>
                      ${diffPercent > 0 ? `<span style="font-size: 0.7rem; font-weight: 850; background: #ecfdf5; color: #059669; padding: 0.15rem 0.45rem; border-radius: 6px;">Save ${diffPercent}%</span>` : ''}
                    </div>
                    <div style="font-family: monospace; font-size: 0.95rem; font-weight: 900; color: #0284c7;">
                      ${p.partNo}
                    </div>
                    <div style="font-size: 0.8rem; font-weight: 750; color: #1e293b; margin-top: 0.25rem;">
                      ${p.desc}
                    </div>
                  </div>
                  <div style="margin-top: 0.75rem; padding-top: 0.6rem; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1rem; font-weight: 900; color: #059669; font-family: 'Outfit', sans-serif;">
                      ${p.mrp && p.mrp > 0 ? '₹' + Number(p.mrp).toLocaleString('en-IN') : 'Check Stock'}
                    </span>
                    <button type="button" onclick="App.inspectPartInMaster('${p.partNo}')" style="padding: 0.3rem 0.65rem; font-size: 0.72rem; font-weight: 800; background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; border-radius: 6px; cursor: pointer;">
                      Details ↗
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

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
            Automotive maintenance best practice: when replacing <strong>${action.component || 'this part'}</strong>, technicians advise inspecting and pairing with:
          </p>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0.65rem;">
            ${relatable.map(r => `
              <div style="background: #ffffff; border: 1px solid #fde68a; border-radius: 10px; padding: 0.75rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                <div>
                  <div style="font-size: 0.84rem; font-weight: 850; color: #0f172a; margin-bottom: 0.25rem;">
                    ${r.icon || '🔧'} ${r.label}
                  </div>
                  <div style="font-size: 0.74rem; color: #64748b; line-height: 1.35;">
                    ${r.why}
                  </div>
                </div>
                <button type="button" onclick="CatalogAiChat.chooseCompanion('${r.component}')" style="margin-top: 0.65rem; width: 100%; padding: 0.4rem; background: #fef3c7; border: 1px solid #f59e0b; color: #b45309; font-weight: 850; font-size: 0.74rem; border-radius: 6px; cursor: pointer; transition: all 0.15s;">
                  Show ${r.label} ➔
                </button>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    return `
      <div style="margin-top: 1rem;">
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

    return `
      <div style="margin-top: 1rem; background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem;">
          <div>
            <div style="font-size: 0.75rem; font-weight: 850; color: #7c3aed; background: #f5f3ff; display: inline-block; padding: 0.2rem 0.55rem; border-radius: 6px; margin-bottom: 0.35rem;">
              ${p.brand || 'GENUINE'} • Line Code ${p.lineCode || 'N/A'}
            </div>
            <div style="font-family: monospace; font-size: 1.35rem; font-weight: 900; color: #0f172a;">
              ${p.partNo}
            </div>
            <div style="font-size: 0.95rem; font-weight: 800; color: #334155; margin-top: 0.2rem;">
              ${p.desc}
            </div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.35rem;">
              Aggregate: <strong>${p.aggregate || 'SPARE PARTS'}</strong> • Component: <strong>${p.components || 'SPARE PART'}</strong>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 750;">Official MRP</div>
            <div style="font-size: 1.6rem; font-weight: 900; color: #059669; font-family: 'Outfit', sans-serif;">
              ${p.mrp && p.mrp > 0 ? '₹' + Number(p.mrp).toLocaleString('en-IN') : 'Price on Request'}
            </div>
            <button type="button" onclick="App.inspectPartInMaster('${p.partNo}')" style="margin-top: 0.4rem; padding: 0.4rem 0.85rem; font-size: 0.78rem; font-weight: 850; background: #0284c7; color: #fff; border: none; border-radius: 6px; cursor: pointer;">
              Open in 3D Explorer ↗
            </button>
          </div>
        </div>

        ${oes.length > 0 ? `
          <div style="margin-top: 1.1rem; padding-top: 0.9rem; border-top: 1px solid #e2e8f0;">
            <div style="font-size: 0.8rem; font-weight: 850; color: #334155; margin-bottom: 0.5rem;">
              🛡️ Interchangeable OES Alternatives:
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
              ${oes.map(o => `
                <span class="tag-pill" onclick="App.inspectPartInMaster('${o.partNo}')" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 0.35rem 0.65rem; border-radius: 8px; font-size: 0.76rem; font-weight: 750; cursor: pointer;">
                  <strong>${o.brand}</strong> (${o.partNo}) - ₹${o.mrp}
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

  executeCommand(cmd) {
    this.showTypingIndicator();
    this.isWaiting = true;

    fetch('/api/catalog-ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: cmd,
        state: this.state
      })
    })
    .then(r => r.json())
    .then(data => {
      this.hideTypingIndicator();
      this.isWaiting = false;
      if (data.state) {
        this.state = Object.assign({}, this.state, data.state);
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
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
