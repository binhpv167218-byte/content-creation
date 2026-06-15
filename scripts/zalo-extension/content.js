(() => {
  const SERVER = "http://localhost:7788";
  const STORAGE_KEY = "za_known_customers";

  // ─── localStorage: nhớ mapping Zalo name → Airtable record ──────────────
  function getKnownCustomer(zaloName) {
    try {
      const map = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      return map[zaloName] || null;
    } catch {
      return null;
    }
  }

  function saveKnownCustomer(zaloName, match) {
    try {
      const map = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      map[zaloName] = {
        id: match.id,
        name: match.name,
        project: match.project || "",
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
    } catch {}
  }

  const PROJECT_PREFIXES = [
    "symphony 5",
    "fours tower",
    "fours",
    "four s",
    "vinhomes hai van bay",
    "vinhomes hvb",
    "vinhomes",
    "charmora",
    "sun charmora",
    "charmora onsen",
    "nobu",
    "m landmark",
    "masterise",
  ];

  function hasProjectPrefix(name) {
    const lower = name.toLowerCase().trim();
    return PROJECT_PREFIXES.some((p) => lower.startsWith(p));
  }

  let state = {
    customerName: "",
    analysis: null,
    matches: [],
    selectedMatch: null,
    saved: false,
  };

  // ─── Sidebar DOM ──────────────────────────────────────────────────────────
  function buildSidebar() {
    if (document.getElementById("za-root")) return;

    const root = document.createElement("div");
    root.id = "za-root";
    root.innerHTML = `
      <div id="za-tab"><span>A<br>I</span></div>
      <div id="za-panel">
        <div id="za-header">
          <span class="za-title">Sales Assistant</span>
          <button id="za-analyze-btn">Phân tích</button>
        </div>
        <div id="za-name-row" style="display:flex;align-items:center;gap:6px;padding:4px 12px;background:#f0f4ff;border-bottom:1px solid #dde3f5">
          <span style="font-size:10px;color:#666;white-space:nowrap">Tên:</span>
          <input id="za-name-input" type="text" placeholder="Tự nhập nếu không nhận diện được..."
            style="flex:1;font-size:11px;border:1px solid #c0caed;border-radius:4px;padding:2px 6px;outline:none;color:#1a3a5c"/>
          <button id="za-name-apply" style="font-size:10px;background:#1a3a5c;color:#fff;border:none;border-radius:4px;padding:2px 7px;cursor:pointer">OK</button>
        </div>
        <div id="za-note-row" style="padding:4px 12px 6px;background:#f0f4ff;border-bottom:1px solid #dde3f5">
          <div style="font-size:10px;color:#666;margin-bottom:2px">📞 Ghi chú điện thoại (ưu tiên):</div>
          <textarea id="za-phone-note" placeholder="Tóm tắt cuộc gọi để lưu ngay..."
            style="width:100%;box-sizing:border-box;font-size:11px;border:1px solid #c0caed;border-radius:4px;
                   padding:4px 6px;outline:none;color:#1a3a5c;resize:none;font-family:inherit;
                   min-height:50px;background:#fff"></textarea>
        </div>
        <div id="za-body">
          <div id="za-status">Mở chat → bấm <b>Phân tích</b></div>
        </div>
        <button id="za-save-btn" disabled>Lưu vào Airtable</button>
        <details id="za-debug-wrap" style="font-size:10px;color:#999;padding:6px 12px 8px">
          <summary style="cursor:pointer">🔍 Debug DOM</summary>
          <div id="za-debug-body" style="margin-top:4px;line-height:1.6;word-break:break-all"></div>
        </details>
      </div>
    `;
    document.body.appendChild(root);

    document.getElementById("za-tab").addEventListener("click", () => {
      root.classList.toggle("open");
      pushChatContent(root.classList.contains("open"));
    });
    document
      .getElementById("za-analyze-btn")
      .addEventListener("click", runAnalysis);
    document
      .getElementById("za-save-btn")
      .addEventListener("click", saveToAirtable);
    document.getElementById("za-name-apply").addEventListener("click", () => {
      const val = document.getElementById("za-name-input").value.trim();
      if (val) {
        state.customerName = val;
        runAnalysis();
      }
    });
    document
      .getElementById("za-name-input")
      .addEventListener("keydown", (e) => {
        if (e.key === "Enter") document.getElementById("za-name-apply").click();
      });

    watchChatChanges();
  }

  // ─── Get customer name ────────────────────────────────────────────────────
  function isStatusText(text) {
    const t = text.trim();
    return (
      /^\d+\s*(giờ|phút|giây|ngày|tuần)\s*(trước)?$/i.test(t) ||
      /^(đang hoạt động|online|offline|vừa xong|active|inactive)/i.test(t) ||
      /^\+?\d[\d\s\-]{7,}$/.test(t) ||
      /^\d{1,2}:\d{2}/.test(t) ||
      /^(hôm nay|hôm qua|yesterday|today)/i.test(t) ||
      t.toLowerCase() === "zalo" ||
      t.length <= 1
    );
  }

  function getCustomerName() {
    // Strategy 1: .header-title — class xác nhận từ DevTools 25/05/2026
    // Path: header.flx > div.threadChat > div.threadChat__title > ... > div.header-title
    const headerTitle = document.querySelector(".header-title");
    if (headerTitle) {
      const t = headerTitle.textContent.trim();
      if (t.length > 1 && t.length < 120 && !isStatusText(t)) return t;
    }

    // Strategy 2: threadChat__title — container của tên + subtitle
    const threadTitle = document.querySelector(".threadChat__title");
    if (threadTitle) {
      const el = threadTitle.querySelector("[class*='title'], [class*='name']");
      if (el) {
        const t = el.textContent.trim();
        if (t.length > 1 && t.length < 120 && !isStatusText(t)) return t;
      }
    }

    // Strategy 3: header element → tìm text node đầu tiên hợp lệ
    const header = document.querySelector("header");
    if (header) {
      const walker = document.createTreeWalker(header, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        const t = node.textContent.trim();
        if (t.length > 1 && t.length < 120 && !isStatusText(t)) return t;
      }
    }

    // Strategy 4: top-nav-floating-container (nếu Zalo dùng layout cũ)
    const topNav = document.querySelector(".top-nav-floating-container");
    if (topNav) {
      const avatarImg = topNav.querySelector("img[alt]");
      if (avatarImg) {
        const t = avatarImg.getAttribute("alt").trim();
        if (t.length > 1 && t.length < 120 && !isStatusText(t)) return t;
      }
      const walker = document.createTreeWalker(topNav, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        const t = node.textContent.trim();
        if (t.length > 1 && t.length < 120 && !isStatusText(t)) return t;
      }
    }

    // Strategy 5: page title — "Tên Khách - Zalo"
    const m = (document.title || "").match(/^(.+?)\s*[-–|]\s*Zalo/i);
    if (m) {
      const name = m[1].trim();
      if (name && !isStatusText(name)) return name;
    }

    return "";
  }

  // ─── Get messages ─────────────────────────────────────────────────────────
  // Confirmed from DevTools: messages are in div.chat-item
  // My messages: .chat-item has class "me"
  // Message text: [data-component="bubble-message"] inside each chat-item
  // Trích giờ phút từ text kiểu "14:35" hoặc "14h35"
  function parseZaloTimeText(t) {
    const m = t.match(/(\d{1,2})[h:](\d{2})/);
    return m ? { h: parseInt(m[1]), min: parseInt(m[2]) } : null;
  }

  // Tính hours_since_last dựa vào timestamp DOM (nếu có)
  // Trả về số giờ (float) hoặc null nếu không đọc được
  function getHoursSinceLastMessage() {
    // Zalo hiển thị time separator giữa các nhóm tin, dạng "14:35" hoặc "Hôm nay 14:35"
    // Selector thử các class có khả năng chứa time separator
    const timeSelectors = [
      '[class*="timeStamp"]',
      '[class*="timestamp"]',
      '[class*="time-stamp"]',
      '[class*="msgTime"]',
      '[class*="msg-time"]',
      '[class*="chatTime"]',
      '[class*="TimeGroup"]',
      '[class*="time-group"]',
      '[class*="divider"]',
      "time",
      '[class*="separator"]',
    ];
    const now = new Date();
    let lastTime = null;

    for (const sel of timeSelectors) {
      const els = document.querySelectorAll(sel);
      els.forEach((el) => {
        if (el.closest("#za-root")) return;
        const t = el.textContent.trim();
        const parsed = parseZaloTimeText(t);
        if (parsed) lastTime = parsed;
      });
      if (lastTime) break;
    }

    if (!lastTime) return null;
    // Giả sử timestamp thuộc hôm nay (Zalo chỉ hiện giờ nếu là hôm nay)
    const lastDate = new Date();
    lastDate.setHours(lastTime.h, lastTime.min, 0, 0);
    // Nếu thời gian đó trong tương lai thì là hôm qua
    if (lastDate > now) lastDate.setDate(lastDate.getDate() - 1);
    return (now - lastDate) / 3600000; // hours
  }

  function getMessages() {
    const msgs = [];

    // Primary: use confirmed class names from DevTools
    const items = document.querySelectorAll(".chat-item");
    if (items.length > 0) {
      items.forEach((el) => {
        const isMe = el.classList.contains("me");
        const bubble = el.querySelector('[data-component="bubble-message"]');
        const text = bubble ? bubble.textContent.trim() : el.textContent.trim();
        if (text && text.length > 0 && text.length < 3000) {
          msgs.push({ text, is_me: isMe });
        }
      });
      return msgs.slice(-30);
    }

    // Fallback: position-based detection
    const chatWidth = document.documentElement.clientWidth;
    const midX = chatWidth / 2;
    const chatArea = findChatScrollArea();
    if (!chatArea) return [];

    const allDivs = chatArea.querySelectorAll("div, p, span");
    for (const el of allDivs) {
      const text = el.textContent.trim();
      if (!text || text.length < 1 || text.length > 2000) continue;
      const rect = el.getBoundingClientRect();
      if (rect.width < 30 || rect.height < 10) continue;
      let childTextLen = 0;
      for (const child of el.children)
        childTextLen += child.textContent.trim().length;
      if (el.children.length > 0 && childTextLen >= text.length * 0.8) continue;
      msgs.push({ text, is_me: rect.left + rect.width / 2 > midX });
    }

    // Deduplicate consecutive identical messages
    const deduped = [];
    for (const m of msgs) {
      if (!deduped.length || deduped[deduped.length - 1].text !== m.text) {
        deduped.push(m);
      }
    }

    return deduped.slice(-30);
  }

  function findChatScrollArea() {
    // Try named selectors first
    const named = [
      "[class*='messageList']",
      "[class*='message-list']",
      "[class*='chatContent']",
      "[class*='chat-content']",
      "[class*='msgList']",
      "[class*='conversationContent']",
    ];
    for (const sel of named) {
      const el = document.querySelector(sel);
      if (el && el.scrollHeight > el.clientHeight) return el;
    }

    // Fallback: find the tallest scrollable div that's likely the chat
    let best = null,
      bestH = 0;
    document.querySelectorAll("div").forEach((el) => {
      if (el.scrollHeight > el.clientHeight && el.clientHeight > 300) {
        if (el.scrollHeight > bestH) {
          bestH = el.scrollHeight;
          best = el;
        }
      }
    });
    return best;
  }

  // ─── Debug info ───────────────────────────────────────────────────────────
  function updateDebug() {
    const name = getCustomerName();
    const msgs = getMessages();

    const headerTitleEl = document.querySelector(".header-title");
    const headerTitleText = headerTitleEl
      ? `"${headerTitleEl.textContent.trim()}"`
      : "(không tìm thấy .header-title)";
    const threadTitleEl = document.querySelector(".threadChat__title");
    const topNavEl = document.querySelector(".top-nav-floating-container");
    const chatItems = document.querySelectorAll(".chat-item");
    const meItems = document.querySelectorAll(".chat-item.me");
    const lastMsg = msgs.slice(-1)[0];

    document.getElementById("za-debug-body").innerHTML = [
      `<b>Title:</b> ${document.title}`,
      `<b>.header-title:</b> ${headerTitleText}`,
      `<b>.threadChat__title:</b> ${threadTitleEl ? "found" : "NO"}`,
      `<b>.top-nav-floating-container:</b> ${topNavEl ? "found" : "NO"}`,
      `<b>→ Tên detect:</b> <span style="color:${name ? "#16a34a" : "#ef4444"}">${name || "(không có)"}</span>`,
      `<b>.chat-item:</b> ${chatItems.length} (mine: ${meItems.length})`,
      `<b>Tin nhắn parse:</b> ${msgs.length}`,
      `<b>Tin cuối:</b> "${lastMsg ? lastMsg.text.slice(0, 50) : "none"}" [${lastMsg ? (lastMsg.is_me ? "tôi" : "khách") : "-"}]`,
    ].join("<br>");
  }

  // ─── Watch chat switches ──────────────────────────────────────────────────
  let lastChatKey = "";
  let lastCustomerMsg = "";
  let debounceTimer = null;
  let analysisRunning = false;
  let lastAnalysisTime = 0;
  const MIN_AUTO_INTERVAL = 8000; // ms giữa 2 lần tự phân tích

  function waitForMessagesAndAnalyze() {
    let attempts = 0;
    const poll = setInterval(() => {
      attempts++;
      if (getMessages().length > 0 || attempts >= 8) {
        clearInterval(poll);
        runAnalysis();
      }
    }, 200);
  }

  // ─── Auto-save logic ─────────────────────────────────────────────────────
  let autoSaveTimer = null;

  // Silent save không cần DOM button (dùng khi switch chat)
  async function silentSave() {
    if (!state.selectedMatch || !state.analysis || state.saved) return;
    try {
      const current_phase = state.selectedMatch.phase || "";
      await fetch(`${SERVER}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          record_id: state.selectedMatch.id,
          phase: state.analysis.phase,
          summary: state.analysis.summary,
          phone_note: "",
          current_phase,
        }),
      });
      saveKnownCustomer(state.customerName, state.selectedMatch);
      state.saved = true;
    } catch (_) {}
  }

  // Sau khi analyze xong: tự lưu nếu đủ điều kiện
  function triggerAutoSave(name, isKnown) {
    clearTimeout(autoSaveTimer);
    if (!state.selectedMatch) return;

    if (isKnown) {
      // Khách đã biết → lưu ngay, không hỏi
      autoSaveTimer = setTimeout(async () => {
        if (state.saved) return;
        await saveToAirtable({ silent: true });
      }, 800);
      return;
    }

    // Khách mới, match đơn, đủ tin cậy → đếm ngược 6s với nút Huỷ
    const topMatch = state.matches[0];
    if (state.matches.length === 1 && topMatch && topMatch.score >= 0.68) {
      let remaining = 6;
      const countdownId = setInterval(() => {
        remaining--;
        const el = document.getElementById("za-autosave-count");
        if (el) el.textContent = remaining;
        if (remaining <= 0) {
          clearInterval(countdownId);
          if (!state.saved && state.selectedMatch)
            saveToAirtable({ silent: true });
          const bar = document.getElementById("za-autosave-bar");
          if (bar) bar.remove();
        }
      }, 1000);

      // Thêm thanh đếm ngược vào đầu za-body
      const bar = document.createElement("div");
      bar.id = "za-autosave-bar";
      bar.style.cssText =
        "background:#fef9c3;border:1px solid #fde68a;border-radius:5px;padding:5px 8px;font-size:10px;color:#92400e;display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:6px";
      bar.innerHTML = `<span>💾 Tự lưu <b>${escHtml(topMatch.name)}</b> sau <b id="za-autosave-count">6</b>s</span>
        <button id="za-autosave-cancel" style="background:#ef4444;color:#fff;border:none;border-radius:3px;padding:2px 7px;font-size:10px;cursor:pointer">Huỷ</button>`;
      const body = document.getElementById("za-body");
      if (body) body.prepend(bar);

      document
        .getElementById("za-autosave-cancel")
        .addEventListener("click", () => {
          clearInterval(countdownId);
          bar.remove();
        });
    }
  }

  let lastMsgFingerprint = "";

  function getMsgFingerprint() {
    const items = document.querySelectorAll(".chat-item");
    return `${items.length}|${items[items.length - 1]?.textContent?.slice(0, 60) || ""}`;
  }

  function watchChatChanges() {
    const observer = new MutationObserver(() => {
      const name = getCustomerName();

      // ── Đổi chat ──────────────────────────────────────────────────────────
      if (name && name !== lastChatKey) {
        if (state.analysis && !state.saved && state.selectedMatch) silentSave();
        clearTimeout(autoSaveTimer);
        clearTimeout(debounceTimer);

        lastChatKey = name;
        lastCustomerMsg = "";
        lastMsgFingerprint = "";
        state = {
          customerName: name,
          analysis: null,
          matches: [],
          selectedMatch: null,
          saved: false,
        };

        const input = document.getElementById("za-name-input");
        if (input) input.value = name;

        if (!hasProjectPrefix(name)) {
          showStatus(
            `<span style="color:#bbb">Không nhận ra dự án.<br>Bấm <b>Phân tích</b> nếu đây là khách.</span>`,
          );
          return;
        }
        showStatus(
          `Khách: <b>${escHtml(name)}</b><br><small>Đang phân tích...</small>`,
        );
        debounceTimer = setTimeout(waitForMessagesAndAnalyze, 300);
        return;
      }

      // ── Tin nhắn mới trong chat hiện tại ──────────────────────────────────
      if (name && name === lastChatKey && hasProjectPrefix(name)) {
        const fp = getMsgFingerprint();
        if (fp !== lastMsgFingerprint) {
          lastMsgFingerprint = fp;
          const now = Date.now();
          // Debounce 4s, và không re-analyze nếu vừa analyze dưới 10s trước
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(() => {
            if (analysisRunning) return;
            if (now - lastAnalysisTime < 10000) return;
            state.saved = false; // nội dung thay đổi → cần lưu lại
            runAnalysis();
          }, 4000);
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  // ─── Push chat content khi sidebar mở/đóng ───────────────────────────────
  function pushChatContent(isOpen) {
    const target =
      document.getElementById("chatViewContainer") ||
      document.querySelector("main") ||
      document.querySelector(".main__center");
    if (target) {
      target.style.marginRight = isOpen ? "308px" : "";
      target.style.transition = "margin-right 0.2s ease";
    }
  }

  // ─── Analysis ────────────────────────────────────────────────────────────
  async function runAnalysis() {
    updateDebug();
    // Ưu tiên state.customerName (manual override) → fallback auto-detect
    const name = state.customerName || getCustomerName();
    const messages = getMessages();

    // Cập nhật input để user thấy tên đang dùng
    const input = document.getElementById("za-name-input");
    if (input && name && !input.value) input.value = name;

    if (!name) {
      showStatus(
        '<b style="color:#ef4444">Không đọc được tên.</b><br>Nhập tên vào ô bên trên rồi bấm OK, hoặc mở 🔍 Debug để kiểm tra.',
      );
      return;
    }
    if (messages.length === 0) {
      showStatus(
        '<b style="color:#ef4444">Không đọc được tin nhắn.</b><br>Thử cuộn lên rồi bấm lại.',
      );
      return;
    }

    if (analysisRunning) return;
    analysisRunning = true;
    lastAnalysisTime = Date.now();

    state.customerName = name;
    state.saved = false;
    showLoading(name);
    document.getElementById("za-analyze-btn").disabled = true;
    const saveBtn = document.getElementById("za-save-btn");
    saveBtn.disabled = true;
    saveBtn.textContent = "Lưu vào Airtable";
    saveBtn.style.background = "";

    try {
      const now = new Date();
      const timestamp = `${now.getHours()}h${String(now.getMinutes()).padStart(2, "0")} ${now.getDate()}/${now.getMonth() + 1}`;
      const hours_since_last = getHoursSinceLastMessage();
      const res = await fetch(`${SERVER}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          messages,
          timestamp,
          hours_since_last,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      state.analysis = data;
      state.matches = data.matches || [];

      // Kiểm tra đã từng xác nhận khách này chưa
      const known = getKnownCustomer(name);
      if (known) {
        // Tìm lại record đầy đủ từ matches, hoặc dùng thông tin đã lưu
        const fromMatches = state.matches.find((m) => m.id === known.id);
        state.selectedMatch = fromMatches || { ...known };
      } else {
        state.selectedMatch =
          state.matches.length === 1 ? state.matches[0] : null;
      }
      renderResults();
      // Auto-save sau khi phân tích xong
      triggerAutoSave(name, !!known);
    } catch (err) {
      showStatus(
        `<span style="color:#ef4444">Lỗi: ${escHtml(err.message)}<br>Server đang chạy chưa?</span>`,
      );
    } finally {
      analysisRunning = false;
      document.getElementById("za-analyze-btn").disabled = false;
    }
  }

  // ─── Save ────────────────────────────────────────────────────────────────
  async function saveToAirtable({ silent = false } = {}) {
    if (!state.selectedMatch || !state.analysis || state.saved) return;
    const btn = document.getElementById("za-save-btn");
    if (!silent && btn) {
      btn.disabled = true;
      btn.textContent = "Đang lưu...";
    }

    const phoneNoteEl = document.getElementById("za-phone-note");
    const phoneNoteRaw = phoneNoteEl ? phoneNoteEl.value.trim() : "";
    let phone_note = "";
    if (phoneNoteRaw) {
      const now = new Date();
      const ts = `${now.getHours()}h${String(now.getMinutes()).padStart(2, "0")} ${now.getDate()}/${now.getMonth() + 1}`;
      phone_note = `${ts} [Phone] ${phoneNoteRaw}`;
    }
    const current_phase = state.selectedMatch.phase || "";

    try {
      const res = await fetch(`${SERVER}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          record_id: state.selectedMatch.id,
          phase: state.analysis.phase,
          summary: state.analysis.summary,
          phone_note,
          current_phase,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        state.saved = true;
        saveKnownCustomer(state.customerName, state.selectedMatch);
        if (phoneNoteEl) phoneNoteEl.value = "";
        if (silent) {
          // Chỉ cập nhật nút lặng lẽ, không re-render
          const b = document.getElementById("za-save-btn");
          if (b) {
            b.textContent = "✓ Tự lưu";
            b.style.background = "#16a34a";
            b.disabled = true;
          }
          // Xóa countdown bar nếu còn
          document.getElementById("za-autosave-bar")?.remove();
        } else {
          if (btn) {
            btn.textContent = "✓ Đã lưu";
            btn.style.background = "#16a34a";
            btn.disabled = false;
          }
          renderResults();
          setTimeout(() => {
            const b = document.getElementById("za-save-btn");
            if (b) {
              b.textContent = "Lưu vào Airtable";
              b.style.background = "";
            }
          }, 2000);
        }
      } else {
        if (!silent && btn) {
          btn.textContent = "Lưu thất bại";
          btn.style.background = "#ef4444";
          btn.disabled = false;
        }
      }
    } catch {
      if (!silent && btn) {
        btn.textContent = "Lỗi kết nối";
        btn.disabled = false;
      }
    }
  }

  // ─── Render ───────────────────────────────────────────────────────────────
  function showStatus(html) {
    document.getElementById("za-body").innerHTML =
      `<div id="za-status">${html}</div>`;
  }
  function showLoading(name) {
    document.getElementById("za-body").innerHTML =
      `<div id="za-status"><div class="za-spinner"></div>Phân tích chat với<br><b>${escHtml(name)}</b>...</div>`;
  }

  function renderResults() {
    const { analysis, matches } = state;
    const phaseColor = {
      A: "#6366f1",
      B: "#3b82f6",
      C: "#10b981",
      D: "#f59e0b",
      E: "#ef4444",
      F: "#8b5cf6",
    };
    const typeColor = {
      ĐT: "#3b82f6",
      Ở: "#10b981",
      FOMO: "#f59e0b",
      "Hoài Nghi": "#6b7280",
    };
    const h = analysis.honorific || "anh/chị";
    const shortcutLabels = {
      ";ch": `Chào ${h} lần đầu`,
      ";nh": `Hỏi nhu cầu ${h}`,
      ";zl": `Nhắn Zalo ${h}`,
      ";bi": "Giới thiệu Bình",
      ";s5": "Tổng quan S5",
      ";ft": "Tổng quan FourS",
      ";vt": "Vị trí + Airbnb",
      ";dt": "Tính lợi nhuận",
      ";fu": `Follow up ${h}`,
      ";gi": "Bảng giá S5",
      ";td": `Mời ${h} xem thực địa`,
      ";cs": "Chính sách",
      ";50": "Objection 50 năm",
      ";sg": "Track record Sun",
      ";og": "Objection chờ",
      ";bk": `Thúc đẩy ${h} booking`,
      ";ck": "Thông tin CK",
      ";f2": `Follow up ${h} mới`,
      ";hn": `Hẹn gặp ${h}`,
      ";cm": `Cảm ơn ${h}`,
    };

    const matchItems = matches
      .map(
        (m, i) => `
      <div class="za-match" data-idx="${i}">
        <div style="flex:1">
          <b style="font-size:12px">${escHtml(m.name)}</b>
          ${m.project ? `<div style="font-size:10px;color:#e87722">${escHtml(m.project)}</div>` : ""}
        </div>
        <span style="font-size:10px;color:#aaa">${Math.round(m.score * 100)}%</span>
      </div>`,
      )
      .join("");

    const shortcuts = (analysis.shortcuts || [])
      .map(
        (s) =>
          `<div class="za-sc-row"><b style="color:#e87722;font-family:monospace;font-size:13px">${s}</b>
       <span style="color:#555;font-size:11px;margin-left:6px">${shortcutLabels[s] || ""}</span></div>`,
      )
      .join("");

    document.getElementById("za-body").innerHTML = `
      <div class="za-card" style="border-left:3px solid ${phaseColor[analysis.phase] || "#1a3a5c"}">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <div style="width:34px;height:34px;border-radius:8px;background:${phaseColor[analysis.phase] || "#1a3a5c"};
               color:#fff;font-size:20px;font-weight:900;display:flex;align-items:center;justify-content:center">
            ${analysis.phase}
          </div>
          <div>
            <div style="font-size:12px;font-weight:700;color:#1a3a5c">${escHtml(analysis.phase_desc)}</div>
            <div style="font-size:10px;color:#888">
              ${escHtml(state.customerName)}
              ${analysis.apt_type ? `<span style="background:#e87722;color:#fff;border-radius:3px;padding:0 4px;margin-left:4px;font-size:9px">${escHtml(analysis.apt_type)}</span>` : ""}
            </div>
          </div>
        </div>
        <div style="font-size:11px;color:#666;font-style:italic;margin-bottom:${analysis.customer_type ? "5px" : "0"}">${escHtml(analysis.reason)}</div>
        ${
          analysis.customer_type
            ? `
        <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap">
          <span style="font-size:10px;background:${typeColor[analysis.customer_type] || "#6b7280"};color:#fff;border-radius:3px;padding:1px 6px;font-weight:700">${escHtml(analysis.customer_type)}</span>
          ${analysis.technique ? `<span style="font-size:10px;color:#888">- ${escHtml(analysis.technique)}</span>` : ""}
        </div>`
            : ""
        }
      </div>

      ${(() => {
        const t = analysis.timing;
        if (!t || !t.urgency) return "";
        const ok = t.should_message !== false;
        const color = ok
          ? t.urgency.startsWith("ngay")
            ? "#16a34a"
            : t.urgency.startsWith("hôm nay")
              ? "#e87722"
              : "#3b82f6"
          : "#6b7280";
        const icon = ok
          ? t.urgency.startsWith("ngay")
            ? "🟢"
            : t.urgency.startsWith("hôm nay")
              ? "🟡"
              : "🔵"
          : "⏸";
        const calBadge = t.calendar_saved
          ? `<div style="margin-top:5px;text-align:center;background:#f0fdf4;color:#166534;
                         border:1px solid #bbf7d0;border-radius:4px;padding:4px;font-size:10px;font-weight:700">
               ✅ Đã lên lịch Calendar
             </div>`
          : t.calendar_deleted
            ? `<div style="margin-top:5px;text-align:center;background:#fef9c3;color:#92400e;
                         border:1px solid #fde68a;border-radius:4px;padding:4px;font-size:10px;font-weight:700">
               🔄 Đã xóa lịch cũ — khách vừa reply lại
             </div>`
            : "";
        return `<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:7px 10px">
          <div style="display:flex;align-items:flex-start;gap:7px">
            <span style="font-size:13px;line-height:1.4">${icon}</span>
            <div style="flex:1">
              <div style="font-size:11px;font-weight:700;color:${color}">${escHtml(t.urgency.charAt(0).toUpperCase() + t.urgency.slice(1))}</div>
              <div style="font-size:10px;color:#555;line-height:1.5;margin-top:1px">${escHtml(t.reason || "")}</div>
            </div>
          </div>
          ${calBadge}
        </div>`;
      })()}

      <div class="za-section-label">Gợi ý tin nhắn</div>
      <div class="za-card" style="padding:7px 9px">
        ${analysis.technique ? `<div style="font-size:10px;color:#888;margin-bottom:5px">Kỹ thuật: <b style="color:#e87722">${escHtml(analysis.technique)}</b>${analysis.customer_type ? ` · <b style="color:#555">${escHtml(analysis.customer_type)}</b>` : ""}</div>` : ""}
        <textarea id="za-intent-input" placeholder="Gõ ý định, hoặc click mẫu bên dưới để điền nhanh..."
          style="width:100%;box-sizing:border-box;font-size:11px;border:1px solid #c0caed;border-radius:4px;
                 padding:5px 7px;outline:none;color:#1a3a5c;resize:none;font-family:inherit;min-height:40px;background:#fff"></textarea>
        <button id="za-suggest-btn" style="width:100%;margin-top:5px;background:#1a3a5c;color:#fff;border:none;border-radius:4px;padding:7px;font-size:11px;font-weight:700;cursor:pointer">✨ Gợi ý tin nhắn + Điền chat</button>
        <div id="za-suggest-result" style="display:none;margin-top:7px">
          <div id="za-suggest-text" style="font-size:11.5px;color:#166534;white-space:pre-wrap;line-height:1.6;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:4px;padding:6px 8px;margin-bottom:5px"></div>
          <div style="display:flex;gap:4px">
            <button id="za-suggest-copy" style="flex:1;background:#f0f4ff;color:#1a3a5c;border:1px solid #c0caed;border-radius:4px;padding:4px;font-size:10px;font-weight:700;cursor:pointer">📋 Chép</button>
            <button id="za-suggest-insert" style="flex:1;background:#1a3a5c;color:#fff;border:none;border-radius:4px;padding:4px;font-size:10px;font-weight:700;cursor:pointer">⌨️ Điền chat</button>
          </div>
        </div>
      </div>

      <div class="za-section-label">Mẫu chat — Phase ${analysis.phase}</div>
      <div id="za-scripts-list">
        ${(analysis.scripts || [])
          .map(
            (s, i) => `
          <div class="za-sc-hint-card" data-idx="${i}"
               style="border:1px solid #e8ecf2;border-radius:5px;padding:6px 10px;margin-bottom:4px;
                      background:#fff;cursor:pointer;transition:background 0.12s"
               onmouseover="this.style.background='#f0f4ff'" onmouseout="this.style.background='#fff'">
            <div style="font-size:10px;font-weight:700;color:#1a3a5c">${escHtml(s.label)}</div>
            <div style="font-size:10px;color:#666;margin-top:1px">${escHtml(s.hint || "")}</div>
          </div>`,
          )
          .join("")}
      </div>

      ${
        state.selectedMatch && getKnownCustomer(state.customerName)
          ? `<div style="font-size:10px;color:#16a34a;padding:2px 0">
               ✓ ${escHtml(state.selectedMatch.name)}
               ${state.selectedMatch.project ? `· <span style="color:#e87722">${escHtml(state.selectedMatch.project)}</span>` : ""}
               <span style="color:#aaa;cursor:pointer;float:right" id="za-reset-match">đổi</span>
             </div>`
          : matches.length > 0
            ? `<div class="za-section-label">Khớp Airtable — chọn đúng người</div>
               <div id="za-matches">${matchItems}</div>`
            : `<div style="font-size:11px;color:#ef4444;padding:4px 0">Không tìm thấy trong Airtable</div>`
      }

      ${
        shortcuts
          ? `<div class="za-section-label">Espanso — Phase ${analysis.phase}</div>
      <div class="za-card">${shortcuts}</div>`
          : ""
      }

      <div class="za-section-label">Tài liệu — Phase ${analysis.phase}</div>
      <div class="za-card" style="padding:7px 9px">
        <div id="za-res-files" style="display:flex;flex-wrap:wrap;gap:5px;min-height:28px;margin-bottom:6px">
          <span style="color:#bbb;font-size:10px">Đang tải...</span>
        </div>
        <div id="za-drop-zone">📎 Kéo file vào đây · Phase ${analysis.phase}</div>
      </div>
    `;

    loadResources(analysis.phase);
    setupDropZone(analysis.phase);

    // Script hint cards: click → điền hint vào ô intent để gợi ý
    const scripts = analysis.scripts || [];
    document.querySelectorAll(".za-sc-hint-card").forEach((card) => {
      card.addEventListener("click", () => {
        const s = scripts[+card.dataset.idx];
        if (!s) return;
        const intentEl = document.getElementById("za-intent-input");
        if (intentEl) {
          intentEl.value = s.hint || s.label;
          intentEl.focus();
          // Highlight để user thấy đã điền
          intentEl.style.borderColor = "#e87722";
          setTimeout(() => (intentEl.style.borderColor = "#c0caed"), 1200);
        }
      });
    });

    // Gợi ý tin nhắn: đọc chat + context → Sonnet viết câu trả lời → điền vào ô chat
    document
      .getElementById("za-suggest-btn")
      .addEventListener("click", async () => {
        const intentEl = document.getElementById("za-intent-input");
        const intent = intentEl ? intentEl.value.trim() : "";
        const btn = document.getElementById("za-suggest-btn");
        btn.textContent = "⏳ Đang viết...";
        btn.disabled = true;

        // Lấy Airtable context từ match tốt nhất nếu có
        const topMatch =
          state.selectedMatch || (state.matches && state.matches[0]);
        const airtableCtx = topMatch ? topMatch.notes || "" : "";

        try {
          const res = await fetch(`${SERVER}/suggest`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              messages: getMessages(),
              customer_name: analysis.short_name || state.customerName,
              honorific: analysis.honorific || "",
              phase: analysis.phase,
              technique: analysis.technique || "",
              customer_type: analysis.customer_type || "",
              airtable_context: airtableCtx,
              project: analysis.project || "",
              intent,
            }),
          });
          const data = await res.json();
          if (data.reply) {
            const resultDiv = document.getElementById("za-suggest-result");
            const textDiv = document.getElementById("za-suggest-text");
            if (resultDiv && textDiv) {
              textDiv.textContent = data.reply;
              resultDiv.style.display = "block";
              // Điền vào chat luôn
              insertToChat(data.reply);
            }
          } else if (data.error) {
            btn.textContent = `Lỗi: ${data.error}`;
            setTimeout(() => {
              btn.textContent = "✨ Gợi ý tin nhắn + Điền chat";
            }, 3000);
          }
        } catch (err) {
          btn.textContent = "Lỗi kết nối";
          setTimeout(() => {
            btn.textContent = "✨ Gợi ý tin nhắn + Điền chat";
          }, 3000);
        }
        btn.textContent = "✨ Gợi ý tin nhắn + Điền chat";
        btn.disabled = false;
      });

    const sgCopy = document.getElementById("za-suggest-copy");
    if (sgCopy) {
      sgCopy.addEventListener("click", () => {
        const t = document.getElementById("za-suggest-text")?.textContent || "";
        navigator.clipboard.writeText(t).then(() => {
          sgCopy.textContent = "✓ Chép!";
          setTimeout(() => (sgCopy.textContent = "📋 Chép"), 1800);
        });
      });
    }
    const sgInsert = document.getElementById("za-suggest-insert");
    if (sgInsert) {
      sgInsert.addEventListener("click", () => {
        const t = document.getElementById("za-suggest-text")?.textContent || "";
        if (insertToChat(t)) {
          sgInsert.textContent = "✓ Điền!";
          setTimeout(() => (sgInsert.textContent = "⌨️ Điền chat"), 1800);
        } else {
          sgInsert.textContent = "Không thấy ô chat";
          sgInsert.style.background = "#ef4444";
          setTimeout(() => {
            sgInsert.textContent = "⌨️ Điền chat";
            sgInsert.style.background = "#1a3a5c";
          }, 2500);
        }
      });
    }

    document.querySelectorAll(".za-match").forEach((el, i) => {
      el.addEventListener("click", () => {
        state.selectedMatch = matches[i];
        document.querySelectorAll(".za-match").forEach((x, j) => {
          x.style.background = j === i ? "#1a3a5c" : "";
          x.style.color = j === i ? "#fff" : "";
        });
        document.getElementById("za-save-btn").disabled = false;
      });
    });

    // Nút "đổi" — xóa cache, hiện lại bảng chọn
    const resetBtn = document.getElementById("za-reset-match");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        try {
          const map = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
          delete map[state.customerName];
          localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
        } catch {}
        state.selectedMatch = null;
        renderResults();
      });
    }

    document.getElementById("za-save-btn").disabled = !state.selectedMatch;
  }

  // ─── Resources ───────────────────────────────────────────────────────────
  async function loadResources(phase) {
    const panel = document.getElementById("za-res-files");
    if (!panel) return;
    try {
      const res = await fetch(`${SERVER}/files?phase=${phase}`);
      const files = await res.json();
      if (!files.length) {
        panel.innerHTML =
          '<span style="color:#bbb;font-size:10px">Chưa có file nào</span>';
        return;
      }
      panel.innerHTML = files
        .map((f) => {
          if (f.mime.startsWith("image/")) {
            return `<div class="za-res-item" title="${escHtml(f.name)}">
              <img src="data:${f.mime};base64,${f.data}" class="za-res-thumb">
              <div class="za-res-name">${escHtml(f.name)}</div>
            </div>`;
          }
          const ext = f.name.split(".").pop().toUpperCase().slice(0, 4);
          return `<div class="za-res-item" title="${escHtml(f.name)}">
            <div class="za-res-icon">${escHtml(ext)}</div>
            <div class="za-res-name">${escHtml(f.name)}</div>
          </div>`;
        })
        .join("");
    } catch (err) {
      const p = document.getElementById("za-res-files");
      if (p)
        p.innerHTML = `<span style="color:#ef4444;font-size:10px">Lỗi tải file</span>`;
    }
  }

  async function uploadFile(file, phase) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const data = e.target.result.split(",")[1];
        try {
          await fetch(`${SERVER}/upload`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phase, filename: file.name, data }),
          });
        } catch {}
        resolve();
      };
      reader.readAsDataURL(file);
    });
  }

  function setupDropZone(phase) {
    const zone = document.getElementById("za-drop-zone");
    if (!zone) return;
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("za-dz-over");
    });
    zone.addEventListener("dragleave", () =>
      zone.classList.remove("za-dz-over"),
    );
    zone.addEventListener("drop", async (e) => {
      e.preventDefault();
      zone.classList.remove("za-dz-over");
      zone.textContent = "⏳ Đang upload...";
      for (const file of e.dataTransfer.files) {
        await uploadFile(file, phase);
      }
      zone.textContent = `📎 Kéo file vào đây · Phase ${phase}`;
      loadResources(phase);
    });
  }

  // ─── Personalize script templates ────────────────────────────────────────
  function personalizeScript(text, honorific, shortName) {
    if (!honorific || !shortName) return text;
    const cap = honorific.charAt(0).toUpperCase() + honorific.slice(1);
    return text
      .replace(/Anh\/chị/g, `${cap} ${shortName}`)
      .replace(/anh\/chị/g, `${honorific} ${shortName}`);
  }

  // ─── Insert to chat ───────────────────────────────────────────────────────
  function findChatInput() {
    // Thử các selector cụ thể trước
    const selectors = [
      '[data-testid="message-input"]',
      '[class*="compose"] [contenteditable]',
      '[class*="editor"] [contenteditable]',
      '[class*="input-container"] [contenteditable]',
      '[class*="chatInput"] [contenteditable]',
      '[class*="InputComponent"] [contenteditable]',
      '[class*="message-input"] [contenteditable]',
      "footer [contenteditable]",
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && !el.closest("#za-root")) return el;
    }
    // Fallback: tìm contenteditable lớn nhất không thuộc sidebar hoặc chat bubble
    let best = null;
    let bestArea = 0;
    for (const el of document.querySelectorAll("[contenteditable]")) {
      if (el.closest("#za-root")) continue;
      if (el.closest(".chat-item")) continue;
      if (el.closest('[data-component="bubble-message"]')) continue;
      const r = el.getBoundingClientRect();
      const area = r.width * r.height;
      if (r.width > 80 && r.height > 14 && area > bestArea) {
        bestArea = area;
        best = el;
      }
    }
    return best;
  }

  function insertToChat(text) {
    const input = findChatInput();
    if (!input) return false;
    input.focus();

    // Method 1: execCommand selectAll + insertText (works in some builds)
    document.execCommand("selectAll", false, null);
    if (document.execCommand("insertText", false, text)) {
      return true;
    }

    // Method 2: clipboard paste - most reliable for React contenteditable
    try {
      const dt = new DataTransfer();
      dt.setData("text/plain", text);
      input.dispatchEvent(
        new ClipboardEvent("paste", {
          clipboardData: dt,
          bubbles: true,
          cancelable: true,
        }),
      );
      // Check if paste worked
      if (input.innerText && input.innerText.trim()) return true;
    } catch (_) {}

    // Method 3: direct innerText + React-style synthetic input event
    input.innerText = text;
    // Move cursor to end
    const range = document.createRange();
    range.selectNodeContents(input);
    range.collapse(false);
    const sel = window.getSelection();
    if (sel) {
      sel.removeAllRanges();
      sel.addRange(range);
    }
    // Fire events React listens to
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function escHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Init
  const tryInit = setInterval(() => {
    if (document.body) {
      buildSidebar();
      clearInterval(tryInit);
    }
  }, 500);
})();
