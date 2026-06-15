// Chỉ hoạt động trong iframe SIDE_SLIDER của Bitrix24 (URL có IFRAME=Y).
// Khi click deal từ danh sách → iframe có IFRAME=Y.
// Khi navigate trực tiếp → Bitrix24 tự load iframe con có IFRAME=Y.
// Main frame không bao giờ có IFRAME=Y → tránh sync đôi.
if (location.href.includes("IFRAME=Y")) {
  chrome.storage.local.get(["syncEnabled"], ({ syncEnabled }) => {
    if (syncEnabled !== false) init();
  });
}

async function init() {
  const dealMatch = location.href.match(/\/crm\/deal\/details\/(\d+)/);
  const leadMatch = location.href.match(/\/crm\/lead\/details\/(\d+)/);
  if (!dealMatch && !leadMatch) return;

  const type = dealMatch ? "deal" : "lead";
  const id = (dealMatch || leadMatch)[1];

  await waitForDOM();

  const data = scrapeData(type, id);
  if (!data.phone) return; // SĐT bắt buộc — không có SĐT không lưu

  showToast("loading", `Đang lưu ${data.name || "#" + id}...`);

  let result;
  try {
    result = await chrome.runtime.sendMessage({ action: "sync", data });
  } catch (e) {
    showToast("error", "Extension lỗi: " + e.message);
    return;
  }

  if (result.updated) {
    showToast("success", `Đã cập nhật: ${data.name || "#" + id}`);
    autoClose();
  } else if (result.skipped) {
    showToast("success", `Đã có: ${data.name || "#" + id}`);
    autoClose();
  } else if (result.success) {
    showToast("success", `Đã lưu: ${data.name || "#" + id}`);
    autoClose();
  } else {
    showToast("error", result.error || "Lỗi không xác định");
  }
}

// Sau 3s navigate top frame về category/1 — bỏ qua dialog "Bước tiếp theo"
function autoClose() {
  setTimeout(() => {
    try {
      const top = window.top !== window ? window.top : window.parent;
      if (top && top !== window) {
        top.location.href = "https://iqi.bitrix24.vn/crm/deal/category/1/";
      }
    } catch (e) {}
  }, 3000);
}

// ─── Đợi DOM render xong ────────────────────────────────────────────────────

async function waitForDOM(maxMs = 8000) {
  const start = Date.now();
  while (Date.now() - start < maxMs) {
    const hasTitles =
      document.querySelectorAll(".ui-entity-editor-block-title").length > 3;
    const hasContact = !!document.querySelector(
      ".crm-entity-widget-content-block-inner-container",
    );
    if (hasTitles && hasContact) return;
    await sleep(400);
  }
}

// ─── Scrape dữ liệu từ DOM ─────────────────────────────────────────────────

const EMPTY_FIELD = "trường bị bỏ trống";

// Tìm value bằng label text: dùng direct text nodes (bỏ qua child elements như icon)
// để tránh false positive từ container. Walk up 6 ancestor levels để tìm sibling value.
function scrapeByLabel(labelText, wantLink = false) {
  for (const el of document.querySelectorAll("*")) {
    // Lấy text trực tiếp từ text nodes (không lấy từ child elements như icon/tooltip)
    let direct = "";
    for (const node of el.childNodes) {
      if (node.nodeType === 3) direct += node.textContent;
    }
    if (direct.trim() !== labelText) continue;

    let node = el;
    for (let lvl = 0; lvl < 6 && node; lvl++, node = node.parentElement) {
      const sib = node.nextElementSibling;
      if (!sib) continue;
      if (wantLink) {
        const sibText = (sib.innerText || sib.textContent || "").trim();
        if (sibText.length > 150) continue; // skip nav/container siblings
        const a = sib.tagName === "A" ? sib : sib.querySelector("a");
        if (!a) continue;
        const val = (a.innerText || a.textContent || "").trim();
        if (val) return val;
      } else {
        const raw = (sib.innerText || sib.textContent || "").trim();
        if (!raw || raw.includes(EMPTY_FIELD)) continue; // reject empty / multi-field containers
        const val = raw.replace(/,?\s*\n\s*/g, ", ").trim();
        if (val && val.length < 200) return val;
      }
    }
  }
  return null;
}

function scrapeData(type, id) {
  const data = { type, id };

  // Tên, SĐT, Email từ khối Liên lạc
  const contactBlock = document.querySelector(
    ".crm-entity-widget-content-block-inner-container",
  );
  if (contactBlock) {
    data.name = contactBlock
      .querySelector("a.crm-entity-widget-client-box-name")
      ?.innerText?.trim()
      ?.replace(/\s+/g, " ");

    const lines = contactBlock.innerText
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    let nextIsAddr = false;
    for (const line of lines) {
      if (
        !data.phone &&
        /^\+?\d[\d\s\-\.]{7,14}$/.test(line.replace(/\D/g, ""))
      ) {
        data.phone = line;
      }
      if (!data.email && line.includes("@") && line.split(" ").length === 1) {
        data.email = line;
      }
      if (line === "Địa chỉ:" || line === "Địa chỉ") {
        nextIsAddr = true;
        continue;
      }
      if (nextIsAddr && !data.address) {
        data.address = line;
        nextIsAddr = false;
        continue;
      }
      nextIsAddr = false;
    }
  }

  if (!data.name) data.name = document.title?.trim();

  // Địa chỉ fallback từ widget riêng
  if (!data.address) {
    const addrEl = document.querySelector(".crm-entity-widget-client-address");
    if (addrEl) {
      data.address = addrEl.innerText
        .split("\n")
        .map((l) => l.trim())
        .filter((l) => l && !l.startsWith("Địa chỉ"))
        .join(", ");
    }
  }

  // "Data thuộc dự án" → Dự án quan tâm
  // Label and link are DOM siblings — use nextElementSibling, not walk-up querySelector
  // Custom fields: label (.ui-entity-editor-block-title) + nextSibling = value
  for (const titleEl of document.querySelectorAll(
    ".ui-entity-editor-block-title",
  )) {
    const label = titleEl.innerText?.trim();
    const value = titleEl.nextElementSibling?.innerText?.trim();
    if (!label || !value || value === EMPTY_FIELD) continue;

    switch (label) {
      case "Giai đoạn":
        data.stage = value;
        break;
      case "Tạo vào":
        data.createdDate = value;
        break;
      case "Sống ở đâu / làm gì":
      case "Sống ở đâu":
      case "Nghề nghiệp":
        data.location = value;
        break;
      case "Mức tài chính":
      case "Tài chính":
      case "Ngân sách":
        data.budget = value;
        break;
    }
  }

  // Fallback: nếu không có field "Sống ở đâu" thì dùng địa chỉ liên lạc
  if (!data.location && data.address) data.location = data.address;

  return data;
}

// ─── Toast ─────────────────────────────────────────────────────────────────

function showToast(state, msg) {
  let el = document.getElementById("bx24-sync-toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "bx24-sync-toast";
    document.body.appendChild(el);
  }
  el.className = `bx24-toast--${state}`;
  el.textContent = msg;
  el.style.display = "block";

  if (state !== "loading") {
    setTimeout(() => {
      el.style.display = "none";
    }, 3500);
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
