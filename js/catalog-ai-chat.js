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
    if (workspace) workspace.classList.toggle('history-collapsed');
  },

  triggerImageUpload() {
    const fileInput = document.getElementById('cat-ai-image-file-input');
    if (fileInput) fileInput.click();
  },

  handleImageSelected(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    this.attachedImageName = file.name;
    const reader = new FileReader();
    reader.onload = (evt) => {
      this.attachedImageDataUri = evt.target.result;
      const previewEl = document.getElementById('cat-ai-image-preview');
      if (previewEl) {
        previewEl.innerHTML = `
          <div style="display: inline-flex; align-items: center; gap: 0.45rem; background: #eff6ff; border: 1px solid #bfdbfe; padding: 0.25rem 0.65rem; border-radius: 8px; font-size: 0.75rem; font-weight: 800; color: #0284c7; margin-bottom: 0.4rem;">
            <span>📷 Image Attached: ${file.name}</span>
            <button type="button" onclick="CatalogAiChat.clearAttachedImage()" style="background: none; border: none; color: #dc2626; cursor: pointer; font-size: 0.85rem; font-weight: 900;">✕</button>
          </div>
        `;
        previewEl.style.display = 'block';
      }
    };
    reader.readAsDataURL(file);
  },

  clearAttachedImage() {
    this.attachedImageName = null;
    this.attachedImageDataUri = null;
    const fileInput = document.getElementById('cat-ai-image-file-input');
    if (fileInput) fileInput.value = '';
    const previewEl = document.getElementById('cat-ai-image-preview');
    if (previewEl) {
      previewEl.innerHTML = '';
      previewEl.style.display = 'none';
    }
  },

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

    // Check if thread already has rendered conversation in DOM
    if (thread.children && thread.children.length > 1) {
      this.scrollToBottom();
      return;
    }

    // Try restoring conversation from sessionStorage
    const restored = this.restoreState();
    if (!restored && this.history.length === 0) {
      this.renderWelcomeGreeting();
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
    } catch (e) {
      console.warn('Chat state storage error', e);
    }
  },

  restoreState() {
    try {
      const savedHtml = sessionStorage.getItem('auto_nexa_chat_html');
      const savedState = sessionStorage.getItem('auto_nexa_chat_state');
      const savedHist = sessionStorage.getItem('auto_nexa_chat_history');
      if (savedState) this.state = JSON.parse(savedState);
      if (savedHist) this.history = JSON.parse(savedHist);

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
    } catch (e) {}
    const thread = document.getElementById('cat-ai-chat-thread');
    if (thread) thread.innerHTML = '';
    this.renderWelcomeGreeting();
  },

  renderWelcomeGreeting() {
    const welcomeHtml = `
      <div class="chat-bot-bubble cat-ai-welcome-box" style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 18px; padding: 1.5rem; box-shadow: 0 4px 18px rgba(0,0,0,0.03); display: grid; grid-template-columns: 1.25fr 0.85fr; gap: 1.25rem; align-items: center;">
        <!-- Left Column: Title, Instructions, and 6 Styled Example Cards -->
        <div>
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.65rem;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #ea580c, #f97316); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.25rem; font-weight: 900; box-shadow: 0 4px 12px rgba(234, 88, 12, 0.3);">
              AN
            </div>
            <div>
              <div style="font-weight: 900; font-size: 1.15rem; color: #0f172a; font-family: 'Outfit', sans-serif;">
                AN Copilot
              </div>
              <div style="font-size: 0.75rem; color: #059669; font-weight: 800; display: flex; align-items: center; gap: 0.35rem;">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
                <span>Active Live Bot</span>
              </div>
            </div>
          </div>

          <div style="font-size: 0.86rem; color: #334155; line-height: 1.5; margin-bottom: 0.65rem;">
            Hello! I am your AI spare parts specialist. You can ask me naturally in <strong>English, Hindi/Hinglish</strong>, or <strong>mechanic terms</strong>, or enter any raw OEM part number.
          </div>

          <div style="font-size: 0.76rem; font-weight: 850; color: #64748b; margin-bottom: 0.5rem;">
            For example, try searching:
          </div>

          <!-- 6 Styled Example Diagnostic Cards (Matching Gemini_Generated_Image_4qh9lg4qh9lg4qh9.png) -->
          <div class="cat-ai-diag-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.65rem;">
            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Grand i10 Nios brake pad')" style="border: 1.5px solid #38bdf8; background: #f0f9ff; border-radius: 10px; padding: 0.65rem 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 0.65rem;">
              <div style="font-size: 1.35rem;">🛑</div>
              <div>
                <div style="font-size: 0.82rem; font-weight: 850; color: #0f172a;">Grand i10 Nios</div>
                <div style="font-size: 0.74rem; font-weight: 700; color: #0284c7;">brake pad</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Swift diesel 2018 oil filter')" style="border: 1.5px solid #fb923c; background: #fff7ed; border-radius: 10px; padding: 0.65rem 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 0.65rem;">
              <div style="font-size: 1.35rem;">🛢️</div>
              <div>
                <div style="font-size: 0.82rem; font-weight: 850; color: #0f172a;">Swift diesel 2018</div>
                <div style="font-size: 0.74rem; font-weight: 700; color: #ea580c;">oil filter</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Innova clutch plate')" style="border: 1.5px solid #c084fc; background: #faf5ff; border-radius: 10px; padding: 0.65rem 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 0.65rem;">
              <div style="font-size: 1.35rem;">⚙️</div>
              <div>
                <div style="font-size: 0.82rem; font-weight: 850; color: #0f172a;">Innova</div>
                <div style="font-size: 0.74rem; font-weight: 700; color: #9333ea;">clutch plate</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Tata Indica kharab hai')" style="border: 1.5px solid #60a5fa; background: #eff6ff; border-radius: 10px; padding: 0.65rem 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 0.65rem;">
              <div style="font-size: 1.35rem;">🔧</div>
              <div>
                <div style="font-size: 0.82rem; font-weight: 850; color: #0f172a;">Tata Indica</div>
                <div style="font-size: 0.74rem; font-weight: 700; color: #2563eb;">kharab hai</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Creta shocker kharab hai')" style="border: 1.5px solid #f87171; background: #fef2f2; border-radius: 10px; padding: 0.65rem 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 0.65rem;">
              <div style="font-size: 1.35rem;">⚡</div>
              <div>
                <div style="font-size: 0.82rem; font-weight: 850; color: #0f172a;">Creta shocker</div>
                <div style="font-size: 0.74rem; font-weight: 700; color: #dc2626;">kharab hai</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Part No: 21658101B4A05')" style="border: 1.5px solid #fbbf24; background: #fffbeb; border-radius: 10px; padding: 0.65rem 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 0.65rem;">
              <div style="font-size: 1.35rem;">🏷️</div>
              <div>
                <div style="font-size: 0.74rem; font-weight: 800; color: #b45309; text-transform: uppercase;">OEM Part:</div>
                <div style="font-family: monospace; font-size: 0.8rem; font-weight: 850; color: #0f172a;">21658101B4A05</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: 3D Technical Wireframe Car with Light Container Matching Gemini Reference -->
        <div class="cat-ai-wireframe-container" style="background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 16px; padding: 1.25rem 1rem; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; min-height: 220px; box-shadow: inset 0 2px 6px rgba(0,0,0,0.02);">
          <img src="images/wireframe_car_inspection.png" alt="3D Vehicle Wireframe Inspection" style="width: 100%; max-height: 180px; object-fit: contain; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.08));">
          <div style="margin-top: 0.75rem; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 999px; padding: 0.35rem 0.85rem; font-size: 0.74rem; font-weight: 850; color: #0f172a; box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 0.35rem;">
            <span>✨</span>
            <span>Identified: tie rod end for tata indica vista</span>
          </div>
        </div>
      </div>
    `;

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

    // Check if thread already has rendered conversation in DOM
    if (thread.children && thread.children.length > 1) {
      this.scrollToBottom();
      return;
    }

    // Try restoring conversation from sessionStorage
    const restored = this.restoreState();
    if (!restored && this.history.length === 0) {
      this.renderWelcomeGreeting();
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
    } catch (e) {
      console.warn('Chat state storage error', e);
    }
  },

  restoreState() {
    try {
      const savedHtml = sessionStorage.getItem('auto_nexa_chat_html');
      const savedState = sessionStorage.getItem('auto_nexa_chat_state');
      const savedHist = sessionStorage.getItem('auto_nexa_chat_history');
      if (savedState) this.state = JSON.parse(savedState);
      if (savedHist) this.history = JSON.parse(savedHist);

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
    } catch (e) {}
    const thread = document.getElementById('cat-ai-chat-thread');
    if (thread) thread.innerHTML = '';
    this.renderWelcomeGreeting();
  },

  renderWelcomeGreeting() {
    const welcomeHtml = `
      <div class="chat-bot-bubble cat-ai-welcome-box">
        <!-- Left Column: Title, Instructions, and 6 Styled Example Cards -->
        <div>
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
            <div style="width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #0284c7); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.2rem; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.35);">
              🤖
            </div>
            <div>
              <div style="font-weight: 900; font-size: 1.05rem; color: #0f172a; font-family: 'Outfit', sans-serif;">
                AutoNexa Catalog AI Copilot
              </div>
              <div style="font-size: 0.76rem; color: #059669; font-weight: 750;">
                🟢 Online • Universal Parts Diagnostic Engine
              </div>
            </div>
          </div>

          <div style="font-size: 0.88rem; color: #334155; line-height: 1.5; margin-bottom: 0.5rem;">
            Hello! Ask anything in <strong>English, Hindi/Hinglish</strong>, vehicle symptoms, or raw part number. Click any card below to launch:
          </div>

          <!-- 6 Styled Example Diagnostic Cards (Image 1 Mockup) -->
          <div class="cat-ai-diag-grid">
            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Grand i10 Nios brake pad')">
              <div class="cat-ai-diag-icon" style="background: #fef2f2; color: #dc2626;">🛑</div>
              <div>
                <div class="cat-ai-diag-text">Grand i10 Nios brake pad</div>
                <div class="cat-ai-diag-sub">Front Disc Pad Set</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Swift diesel 2018 oil filter')">
              <div class="cat-ai-diag-icon" style="background: #f0fdfa; color: #0d9488;">🛢️</div>
              <div>
                <div class="cat-ai-diag-text">Swift diesel 2018 oil filter</div>
                <div class="cat-ai-diag-sub">Spin-On Engine Filter</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Innova clutch plate')">
              <div class="cat-ai-diag-icon" style="background: #f5f3ff; color: #7c3aed;">⚙️</div>
              <div>
                <div class="cat-ai-diag-text">Innova clutch plate</div>
                <div class="cat-ai-diag-sub">Clutch Disc & Cover</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Tata Indica kharab hai')">
              <div class="cat-ai-diag-icon" style="background: #fff7ed; color: #ea580c;">🔧</div>
              <div>
                <div class="cat-ai-diag-text">Tata Indica kharab hai</div>
                <div class="cat-ai-diag-sub">Diagnostic Area Selection</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Creta shocker kharab hai')">
              <div class="cat-ai-diag-icon" style="background: #ecfdf5; color: #059669;">🌀</div>
              <div>
                <div class="cat-ai-diag-text">Creta shocker kharab hai</div>
                <div class="cat-ai-diag-sub">Front Strut & Damper</div>
              </div>
            </div>

            <div class="cat-ai-diag-card" onclick="CatalogAiChat.quickSend('Part No: 21658101B4A05')">
              <div class="cat-ai-diag-icon" style="background: #eff6ff; color: #2563eb;">🏷️</div>
              <div>
                <div class="cat-ai-diag-text">Part: 21658101B4A05</div>
                <div class="cat-ai-diag-sub">Cross Line Code Match</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: 3D Technical Wireframe Car with Neon Inspection Callout -->
        <div class="cat-ai-wireframe-container">
          <img src="images/wireframe_car_inspection.png" alt="3D Vehicle Wireframe Inspection" class="cat-ai-wireframe-img">
          <div class="cat-ai-inspection-callout">
            <span style="font-size: 0.9rem;">✨</span>
            <span>Identified: Tie Rod End for Tata Indica Vista</span>
          </div>
        </div>
      </div>
    `;

    const thread = document.getElementById('cat-ai-chat-thread');
    if (thread) {
      thread.innerHTML = welcomeHtml;
      this.scrollToBottom();
      this.saveState();
    }
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

    
    const oemRefPart = (oem && oem.partNo) || (oesList[0] && oesList[0].partNo) || '';
    const oesBannerHtml = `
      <div style="background: linear-gradient(135deg, #f0fdf4, #ecfdf5); border: 1.5px solid #86efac; border-radius: 12px; padding: 0.9rem 1.15rem; margin-bottom: 1rem; display: flex; align-items: flex-start; gap: 0.85rem; box-shadow: 0 2px 8px rgba(22, 163, 74, 0.08);">
        <span style="font-size: 1.5rem; flex-shrink: 0;">💡</span>
        <div style="flex: 1;">
          <div style="font-weight: 850; color: #166534; font-size: 0.86rem; font-family: 'Outfit', sans-serif;">
            Commercial Value Insight: Tier-1 OES Available at ~25% Lower Cost!
          </div>
          <div style="font-size: 0.78rem; color: #15803d; margin-top: 0.2rem; line-height: 1.35;">
            Verified Tier-1 OES parts (Bosch, TVS Girling, Brembo, Valeo, LuK) are identical in build quality and OE fitment, saving ~25% vs Dealership OEM price with full warranty.
          </div>
          <div style="margin-top: 0.6rem;">
            <button type="button" onclick="CatalogAiChat.showFitmentModal('${oemRefPart}')" 
                    style="background: #16a34a; color: #ffffff; border: none; border-radius: 8px; padding: 0.35rem 0.85rem; font-size: 0.76rem; font-weight: 850; cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem; box-shadow: 0 2px 8px rgba(22, 163, 74, 0.25);">
              <span>🔍 Do you want to know which are all variants and models this suits for?</span>
            </button>
          </div>
        </div>
      </div>
    `;

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
              <div style="font-family: monospace; font-size: 1.15rem; font-weight: 900; color: #0f172a; margin-bottom: 0.2rem;">
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
              <button type="button" onclick="CatalogAiChat.showFitmentModal('${oem.partNo}')" style="margin-top: 0.45rem; padding: 0.4rem 0.85rem; font-size: 0.76rem; font-weight: 850; background: #16a34a; color: #ffffff; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 2px 8px rgba(22, 163, 74, 0.25); display: inline-flex; align-items: center; gap: 0.35rem;">
                <span>Show Fitment Details</span> <span>➔</span>
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
          ${oesBannerHtml}
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
                    <button type="button" onclick="CatalogAiChat.showFitmentModal('${p.partNo}')" style="padding: 0.35rem 0.75rem; font-size: 0.74rem; font-weight: 800; background: #f8fafc; border: 1px solid #cbd5e1; color: #0284c7; border-radius: 6px; cursor: pointer;">
                      Show Fitment ➔
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
    const lineCodeAlertHtml = (p.crossLineCodeResolved || p.lineCodeAlert) ? `
      <div style="margin-bottom: 0.85rem; background: #fffbeb; border: 1.5px solid #fde68a; border-radius: 10px; padding: 0.55rem 0.85rem; display: flex; align-items: center; gap: 0.6rem;">
        <span style="font-size: 1.1rem;">⚡</span>
        <div>
          <strong style="color: #92400e; font-size: 0.8rem; display: block;">Line Code Auto-Resolved</strong>
          <span style="color: #b45309; font-size: 0.76rem;">${p.lineCodeAlert || `Searched with Line Code '${p.inputLineCode || 'other'}', but verified active under Line Code ${p.lineCode} (${p.brand})`}</span>
        </div>
      </div>
    ` : '';

    return `
      <div style="margin-top: 1rem; background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 1.25rem;">
        ${lineCodeAlertHtml}
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem;">
          <div>
            <div style="font-size: 0.75rem; font-weight: 850; color: #0284c7; background: #eff6ff; display: inline-block; padding: 0.2rem 0.55rem; border-radius: 6px; margin-bottom: 0.35rem;">
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
            <button type="button" onclick="CatalogAiChat.showFitmentModal('${p.partNo}')" style="margin-top: 0.4rem; padding: 0.45rem 0.95rem; font-size: 0.78rem; font-weight: 850; background: #0284c7; color: #fff; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 2px 8px rgba(2, 132, 199, 0.25);">
              Show Fitment Details ➔
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
                <span class="tag-pill" onclick="CatalogAiChat.showFitmentModal('${o.partNo}')" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 0.35rem 0.65rem; border-radius: 8px; font-size: 0.76rem; font-weight: 750; cursor: pointer; color: #0f172a;">
                  <strong>${o.brand}</strong> (${o.partNo}) - ₹${o.mrp} ➔
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
