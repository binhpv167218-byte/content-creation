// watcher.js — Chạy trên mọi trang Bitrix24

// ─── Floating status widget ──────────────────────────────────────────────────

function initWidget() {
  if (document.getElementById("b24sync-widget")) return;

  const widget = document.createElement("div");
  widget.id = "b24sync-widget";
  widget.style.cssText = `
    position: fixed; bottom: 20px; right: 20px; z-index: 2147483647;
    background: #1a3a5c; color: #fff;
    padding: 7px 14px; border-radius: 20px;
    font-size: 12px; font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    display: flex; align-items: center; gap: 7px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.35);
    cursor: default; user-select: none; transition: background 0.3s;
  `;

  widget.innerHTML = `
    <span id="b24sync-dot" style="width:8px;height:8px;border-radius:50%;background:#27ae60;flex-shrink:0;"></span>
    <span id="b24sync-label">B24 Sync</span>
    <span style="width:1px;height:14px;background:rgba(255,255,255,0.25);flex-shrink:0;"></span>
    <span id="b24sync-toggle" title="Bật/Tắt sync" style="
      cursor:pointer; font-size:13px; line-height:1; padding:0 2px; opacity:0.85;
    ">⏻</span>
  `;

  document.body.appendChild(widget);

  // Khởi tạo trạng thái từ storage
  chrome.storage.local.get(["syncEnabled"], ({ syncEnabled }) => {
    applyToggleState(syncEnabled !== false); // mặc định ON
  });

  document.getElementById("b24sync-toggle").addEventListener("click", () => {
    chrome.storage.local.get(["syncEnabled"], ({ syncEnabled }) => {
      const newState = syncEnabled === false ? true : false; // flip
      chrome.storage.local.set({ syncEnabled: newState });
      applyToggleState(newState);
    });
  });
}

function applyToggleState(enabled) {
  const dot = document.getElementById("b24sync-dot");
  const label = document.getElementById("b24sync-label");
  const widget = document.getElementById("b24sync-widget");
  const btn = document.getElementById("b24sync-toggle");
  if (!dot || !label || !widget || !btn) return;
  if (enabled) {
    dot.style.background = "#27ae60";
    label.textContent = "B24 Sync";
    widget.style.background = "#1a3a5c";
    btn.style.opacity = "0.85";
    btn.title = "Đang bật — nhấn để tắt";
  } else {
    dot.style.background = "#7f8c8d";
    label.textContent = "Đã tắt";
    widget.style.background = "#555";
    btn.style.opacity = "1";
    btn.title = "Đang tắt — nhấn để bật";
  }
}

function setWidgetState(state, name) {
  const dot = document.getElementById("b24sync-dot");
  const label = document.getElementById("b24sync-label");
  const widget = document.getElementById("b24sync-widget");
  if (!dot || !label || !widget) return;

  if (state === "syncing") {
    dot.style.background = "#f39c12";
    label.textContent = `Đang lưu ${name || ""}...`;
    widget.style.background = "#1a3a5c";
  } else if (state === "success") {
    dot.style.background = "#27ae60";
    label.textContent = `Đã lưu: ${name || ""}`;
    widget.style.background = "#1e6b3a";
    setTimeout(() => resetWidget(), 4000);
  } else if (state === "updated") {
    dot.style.background = "#27ae60";
    label.textContent = `Đã cập nhật: ${name || ""}`;
    widget.style.background = "#1e5c4a";
    setTimeout(() => resetWidget(), 4000);
  } else if (state === "skipped") {
    dot.style.background = "#27ae60";
    label.textContent = `Đã có: ${name || ""}`;
    widget.style.background = "#1a3a5c";
    setTimeout(() => resetWidget(), 3000);
  } else if (state === "error") {
    dot.style.background = "#e74c3c";
    label.textContent = `Lỗi sync`;
    widget.style.background = "#7b1a1a";
    setTimeout(() => resetWidget(), 5000);
  }
}

function resetWidget() {
  const dot = document.getElementById("b24sync-dot");
  const label = document.getElementById("b24sync-label");
  const widget = document.getElementById("b24sync-widget");
  if (!dot || !label || !widget) return;
  dot.style.background = "#27ae60";
  label.textContent = "B24 Sync";
  widget.style.background = "#1a3a5c";
}

// Tạo widget sau khi body sẵn sàng
if (document.body) {
  initWidget();
} else {
  document.addEventListener("DOMContentLoaded", initWidget);
}

// ─── Proactive dialog watcher ─────────────────────────────────────────────────
// Bắt dialog "Bước tiếp theo" ngay khi xuất hiện, không chờ b24status

function startDialogWatcher() {
  new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (node.nodeType !== 1) continue;
        const text = node.innerText || node.textContent || "";
        if (text.includes("HỦY BỎ") || text.includes("HUỶ BỎ")) {
          setTimeout(() => tryDismissTaskDialog(), 150);
        }
      }
    }
  }).observe(document.body, { childList: true, subtree: true });
}

if (document.body) {
  startDialogWatcher();
} else {
  document.addEventListener("DOMContentLoaded", startDialogWatcher);
}

// ─── Nhận status từ background.js ───────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "b24status") {
    initWidget();
    setWidgetState(msg.state, msg.name);
    if (
      msg.state === "success" ||
      msg.state === "skipped" ||
      msg.state === "updated"
    ) {
      scheduleDialogDismiss();
    }
  }
});

// ─── Auto-dismiss dialog "Bước tiếp theo" sau khi sync ───────────────────────

let _dismissTimer = null;

function scheduleDialogDismiss() {
  if (_dismissTimer) clearInterval(_dismissTimer);
  let attempts = 0;
  _dismissTimer = setInterval(() => {
    attempts++;
    if (attempts > 20 || tryDismissTaskDialog()) {
      clearInterval(_dismissTimer);
      _dismissTimer = null;
    }
  }, 300);
}

function tryDismissTaskDialog() {
  const TARGETS = ["HỦY BỎ", "HUỶ BỎ"];

  // Tìm trong toàn bộ element — kể cả div, span, a, button
  for (const el of document.querySelectorAll("a, button, span, div")) {
    if (!isVisible(el)) continue;
    const t = (el.innerText || "")
      .normalize("NFC")
      .replace(/\s+/g, " ")
      .trim()
      .toUpperCase();
    if (TARGETS.includes(t)) {
      console.log("[B24Sync] Dismiss dialog:", el.tagName, t);
      el.click();
      return true;
    }
  }

  // Fallback: Escape key
  document.dispatchEvent(
    new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
  );
  return false;
}

function isVisible(el) {
  return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
}

// ─── Nhận config qua postMessage (để set credentials từ DevTools) ────────────

window.addEventListener("message", (e) => {
  if (e.data?.type === "b24sync-config" && e.data.config) {
    chrome.storage.local.set(e.data.config);
    setWidgetState("success", "Config đã lưu");
  }
});

// ─── Notification watcher ────────────────────────────────────────────────────

// Pattern 1: "chịu trách nhiệm cho giao dịch "Tên""
const PATTERN1 = /chịu trách nhiệm cho giao dịch\s+["""']([^"""']+)["""']/;
// Pattern 2: "data khách hàng mới Tên, nhớ liên hệ"
const PATTERN2 = /data khách hàng mới\s+([^,\n.]+)/;
// Pattern 3: "chịu trách nhiệm cho liên lạc "Tên""
const PATTERN3 = /chịu trách nhiệm cho liên lạc\s+["""']([^"""']+)["""']/;

const seen = new Map();

function extractName(text) {
  const m =
    text.match(PATTERN1) || text.match(PATTERN2) || text.match(PATTERN3);
  return m ? m[1].trim() : null;
}

const observer = new MutationObserver((mutations) => {
  for (const m of mutations) {
    for (const node of m.addedNodes) {
      const text =
        node.nodeType === 3
          ? node.textContent
          : node.textContent || node.innerText || "";

      // Bỏ qua thông báo XÓA trách nhiệm
      if (text.includes("không còn chịu trách nhiệm")) continue;

      const relevant =
        text.includes("trách nhiệm") || text.includes("data khách hàng mới");
      if (!relevant) continue;

      const name = extractName(text);
      if (!name) continue;

      const now = Date.now();
      if (seen.has(name) && now - seen.get(name) < 15000) continue;
      seen.set(name, now);

      console.log("[B24Sync] Khách mới:", name);
      setTimeout(() => openDeal(name), 1200);
    }
  }
});

observer.observe(document.documentElement, { childList: true, subtree: true });

// ─── BX.PULL hook — bắt thông báo ngay cả khi panel đóng ────────────────────

function processPullText(text) {
  if (text.includes("không còn chịu trách nhiệm")) return;
  if (!text.includes("trách nhiệm") && !text.includes("data khách hàng mới"))
    return;
  const name = extractName(text);
  if (!name) return;
  const now = Date.now();
  if (seen.has(name) && now - seen.get(name) < 15000) return;
  seen.set(name, now);
  console.log("[B24Sync] PULL → Khách mới:", name);
  setTimeout(() => openDeal(name), 1200);
}

// Subscribe tất cả module liên quan — "im" chỉ bắt chat, CRM assign đi qua "crm" và "main"
const PULL_MODULES = ["im", "crm", "main"];

function hookBXPull() {
  const tryHook = () => {
    if (typeof BX === "undefined" || !BX.PULL?.subscribe) return false;
    for (const moduleId of PULL_MODULES) {
      BX.PULL.subscribe({
        moduleId,
        callback: (data) => processPullText(JSON.stringify(data)),
      });
    }
    console.log("[B24Sync] BX.PULL hooked:", PULL_MODULES.join(", "));
    return true;
  };
  if (!tryHook()) {
    let n = 0;
    const t = setInterval(() => {
      if (tryHook() || ++n > 20) clearInterval(t);
    }, 1500);
  }
}

hookBXPull();

// ─── BX event hooks — lớp thứ 3 bắt notification qua internal BX events ─────

function hookBXEvents() {
  if (typeof BX === "undefined" || !BX.addCustomEvent) return false;
  const events = [
    "onIMNotificationAdd",
    "onIMNotificationUpdate",
    "BX.Messenger.Notifier.View:onAdd",
  ];
  for (const ev of events) {
    BX.addCustomEvent(ev, (data) => processPullText(JSON.stringify(data)));
  }
  console.log("[B24Sync] BX events hooked");
  return true;
}

setTimeout(() => {
  if (!hookBXEvents()) {
    let n = 0;
    const t = setInterval(() => {
      if (hookBXEvents() || ++n > 20) clearInterval(t);
    }, 1500);
  }
}, 1000);

// ─── Polling định kỳ qua REST API — fallback khi BX.PULL và BX events miss ──

let _lastNotifId = 0;

async function pollNotifications() {
  try {
    const url =
      "https://iqi.bitrix24.vn/rest/im.notify.list.json?type=SYSTEM&limit=10&order%5BID%5D=desc";
    const resp = await fetch(url, { credentials: "include" });
    if (!resp.ok) return;
    const json = await resp.json();
    const raw = json.result;
    const items = Array.isArray(raw)
      ? raw
      : Array.isArray(raw?.items)
        ? raw.items
        : [];
    for (const item of items) {
      const id = parseInt(item.id || item.ID || 0);
      // Lần đầu poll: set baseline ID, không process để tránh false positive
      if (_lastNotifId === 0) {
        if (id > _lastNotifId) _lastNotifId = id;
        continue;
      }
      if (id <= _lastNotifId) continue;
      const text = item.message || item.MESSAGE || item.text || item.TEXT || "";
      processPullText(text);
      if (id > _lastNotifId) _lastNotifId = id;
    }
  } catch (e) {
    console.log("[B24Sync] Poll error:", e.message);
  }
}

// Poll lần đầu sau 5s để set baseline ID, sau đó mỗi 30s bắt cái mới
setTimeout(() => {
  pollNotifications();
  setInterval(pollNotifications, 30000);
}, 5000);

async function openDeal(name) {
  let link = findDealLink(name);
  if (link) {
    link.click();
    return;
  }

  await sleep(2000);
  link = findDealLink(name);
  if (link) {
    link.click();
    return;
  }

  if (!location.href.includes("/crm/deal/category/1")) {
    location.href = "https://iqi.bitrix24.vn/crm/deal/category/1/";
  }
}

function findDealLink(name) {
  return Array.from(
    document.querySelectorAll('a[href*="/crm/deal/details/"]'),
  ).find((a) => {
    const t = a.innerText.trim();
    return t === name || t.includes(name);
  });
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
