const AIRTABLE_TABLE = "tbl8hbsOvV2y2MnfN";
const AIRTABLE_BASE_URL = "https://api.airtable.com/v0";

// ─── Auto-setup credentials + badge khi khởi động ─────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  autoSaveCredentials();
  setBadge("active");
});
chrome.runtime.onStartup.addListener(() => {
  autoSaveCredentials();
  setBadge("active");
});

// Chạy ngay lập tức khi service worker khởi động
autoSaveCredentials();
setBadge("active");

function autoSaveCredentials() {
  chrome.storage.local.get(["airtableKey"], (data) => {
    if (!data.airtableKey) {
      chrome.storage.local.set({
        airtableKey: "",
        airtableBase: "",
      });
    }
  });
}

function setBadge(state) {
  const cfg = {
    active: { text: "ON", color: "#27ae60" },
    syncing: { text: "...", color: "#f39c12" },
    error: { text: "!", color: "#e74c3c" },
  };
  const s = cfg[state] || cfg.active;
  chrome.action.setBadgeText({ text: s.text });
  chrome.action.setBadgeBackgroundColor({ color: s.color });
}

// ─── Message handler ───────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "sync") {
    handleSync(msg.data, sender.tab?.id).then(sendResponse);
    return true;
  }
});

async function handleSync(data, tabId) {
  // Báo widget: đang sync
  notify(tabId, "syncing", data.name);
  setBadge("syncing");

  try {
    const cfg = await getConfig();
    if (!cfg.airtableKey || !cfg.airtableBase) {
      notify(tabId, "error", "Chưa có API key");
      setBadge("error");
      return {
        success: false,
        error: "Chưa nhập Airtable API key — click icon extension",
      };
    }

    const projectOptions = await loadProjectOptions(cfg);
    const fields = buildFields(data, projectOptions);
    const result = await upsertAirtable(cfg, fields);

    if (result.updated) {
      notify(tabId, "updated", data.name);
    } else if (result.skipped) {
      notify(tabId, "skipped", data.name);
    } else {
      notify(tabId, "success", data.name);
    }
    setBadge("active");
    return result;
  } catch (e) {
    notify(tabId, "error", e.message);
    setBadge("error");
    setTimeout(() => setBadge("active"), 5000);
    return { success: false, error: e.message };
  }
}

function notify(tabId, state, name) {
  if (!tabId) return;
  chrome.tabs
    .sendMessage(tabId, { action: "b24status", state, name })
    .catch(() => {});
}

// ─── Project name resolution ──────────────────────────────────────────────────
// Dự án quan tâm phải match option có sẵn trong Airtable, không tạo mới

let _projectOptions = null;

async function loadProjectOptions(cfg) {
  if (_projectOptions) return _projectOptions;
  try {
    const r = await fetch(
      `https://api.airtable.com/v0/meta/bases/${cfg.airtableBase}/tables`,
      { headers: { Authorization: `Bearer ${cfg.airtableKey}` } },
    );
    if (r.ok) {
      const d = await r.json();
      const tbl = d.tables?.find((t) => t.id === AIRTABLE_TABLE);
      const fld = tbl?.fields?.find((f) => f.name === "Dự án quan tâm");
      if (fld?.options?.choices?.length) {
        _projectOptions = fld.options.choices.map((c) => c.name);
        console.log(
          "[B24Sync] Project options from Airtable:",
          _projectOptions,
        );
        return _projectOptions;
      }
    }
  } catch (e) {}
  // Fallback cứng nếu meta API không có quyền
  _projectOptions = [
    "Sun Symphony 5",
    "Vinhomes Hải Vân Bay",
    "FourS Tower",
    "Sun Charmora City",
  ];
  return _projectOptions;
}

function resolveProject(raw, options) {
  if (!raw || !options.length) return null;
  const lower = raw.toLowerCase().trim();
  // 1. Exact match
  const exact = options.find((o) => o.toLowerCase() === lower);
  if (exact) return exact;
  // 2. Substring: raw chứa option hoặc ngược lại
  return (
    options.find((o) => lower.includes(o.toLowerCase())) ||
    options.find((o) => o.toLowerCase().includes(lower)) ||
    null
  );
}

// ─── Map DOM data → Airtable fields ──────────────────────────────────────

function buildFields(data, projectOptions = []) {
  const f = {};

  if (data.name) f["Tên"] = data.name;
  if (data.phone) f["Số điện thoại"] = normalizePhone(data.phone);
  if (data.email) f["Email"] = data.email;
  if (data.location) f["Địa chỉ"] = data.location;
  if (data.createdDate) f["Ngày tiếp cận"] = parseViDate(data.createdDate);
  f["Dự án quan tâm"] = "Sun Symphony 5";

  const gender = detectGender(data.name);
  if (gender) f["Giới tính"] = gender;

  if (data.budget) f["Ngân sách"] = data.budget;

  f["Phase"] = "A";
  f["Nguồn"] = "Lead";
  f["Trạng thái"] = "Khách mới";

  return f;
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function normalizePhone(phone) {
  const digits = phone.replace(/\D/g, "");
  let core;
  if (digits.startsWith("84") && digits.length >= 11) {
    core = digits.slice(2); // bỏ 84 đầu
  } else if (digits.startsWith("0") && digits.length >= 9) {
    core = digits.slice(1); // bỏ 0 đầu
  } else {
    return phone; // không nhận ra → giữ nguyên
  }
  // Format: +84 XXX XXX XXX
  return `+84 ${core.slice(0, 3)} ${core.slice(3, 6)} ${core.slice(6)}`;
}

function parseViDate(str) {
  const m = str.match(/(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})/);
  if (!m) return str.split(" ")[0];
  const [, day, month, year] = m;
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
}

// ─── Airtable upsert ───────────────────────────────────────────────────────

async function upsertAirtable(cfg, fields) {
  const baseUrl = `${AIRTABLE_BASE_URL}/${cfg.airtableBase}/${AIRTABLE_TABLE}`;
  const headers = {
    Authorization: `Bearer ${cfg.airtableKey}`,
    "Content-Type": "application/json",
  };

  // Tìm record trùng — trả về { id, fields } nếu có
  const existing = await findExisting(baseUrl, headers, fields);

  if (existing) {
    return patchMissingFields(baseUrl, headers, existing, fields);
  }

  // Chưa có → tạo mới
  const cleanFields = Object.fromEntries(
    Object.entries(fields).filter(([, v]) => v !== "" && v != null),
  );

  const r = await fetch(baseUrl, {
    method: "POST",
    headers,
    body: JSON.stringify({
      records: [{ fields: cleanFields }],
      typecast: true,
    }),
  });

  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP ${r.status}`);
  }

  return { success: true };
}

// Tìm record trùng, trả về { id, fields } hoặc null
async function findExisting(baseUrl, headers, fields) {
  const phone = fields["Số điện thoại"];

  if (phone) {
    // Cách 1: exact variants
    const variants = [
      ...new Set([
        phone,
        phone.replace(/^0/, "+84"),
        "+" + phone.replace(/\D/g, ""),
        phone.replace(/^0/, "+84 "),
      ]),
    ];
    for (const v of variants) {
      const rec = await findRecordFull(baseUrl, headers, "Số điện thoại", v);
      if (rec) return rec;
    }

    // Cách 2: 4 số cuối + tên
    if (fields["Tên"]) {
      const last4 = phone.replace(/\D/g, "").slice(-4);
      if (last4.length === 4) {
        const formula = encodeURIComponent(
          `AND(SEARCH("${last4}", SUBSTITUTE({Số điện thoại}, " ", "")) > 0, {Tên} = "${fields["Tên"]}")`,
        );
        const r = await fetch(
          `${baseUrl}?filterByFormula=${formula}&maxRecords=1`,
          { headers },
        );
        if (r.ok) {
          const d = await r.json();
          if (d.records?.[0])
            return { id: d.records[0].id, fields: d.records[0].fields };
        }
      }
    }
  }

  // Cách 3: fallback theo tên
  if (fields["Tên"]) {
    const rec = await findRecordFull(baseUrl, headers, "Tên", fields["Tên"]);
    if (rec) return rec;
  }

  return null;
}

// Patch những field còn trống trong Airtable nhưng có giá trị từ Bitrix24
async function patchMissingFields(baseUrl, headers, existing, newFields) {
  const patch = {};
  for (const [key, val] of Object.entries(newFields)) {
    if (!val && val !== 0) continue;
    const cur = existing.fields[key];
    if (!cur && cur !== 0) patch[key] = val;
  }

  if (Object.keys(patch).length === 0) {
    return { success: true, skipped: true };
  }

  const r = await fetch(`${baseUrl}/${existing.id}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({ fields: patch, typecast: true }),
  });

  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP ${r.status}`);
  }

  return { success: true, updated: true };
}

async function findRecordFull(baseUrl, headers, fieldName, value) {
  const formula = encodeURIComponent(`{${fieldName}}="${value}"`);
  const r = await fetch(`${baseUrl}?filterByFormula=${formula}&maxRecords=1`, {
    headers,
  });
  if (!r.ok) return null;
  const data = await r.json();
  const rec = data.records?.[0];
  return rec ? { id: rec.id, fields: rec.fields } : null;
}

// ─── Config ────────────────────────────────────────────────────────────────

function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["airtableKey", "airtableBase"], resolve);
  });
}

// ─── Gender detection từ tên tiếng Việt ───────────────────────────────────────

function detectGender(name) {
  if (!name) return null;
  const parts = name.trim().split(/\s+/);
  if (parts.length < 2) return null;

  // Họ phổ biến — dùng để xác định đúng vị trí tên
  const ho = new Set([
    "nguyễn",
    "trần",
    "lê",
    "phạm",
    "hoàng",
    "huỳnh",
    "phan",
    "vũ",
    "võ",
    "đặng",
    "bùi",
    "đỗ",
    "hồ",
    "ngô",
    "dương",
    "lý",
    "đinh",
    "lâm",
    "phùng",
    "trịnh",
    "đoàn",
    "vương",
    "mai",
    "hà",
    "tô",
    "tạ",
    "thái",
    "châu",
    "vi",
    "quách",
    "tiêu",
    "nông",
    "thạch",
    "cao",
    "đào",
    "trương",
    "từ",
    "liêu",
    "giáp",
  ]);

  // Nếu parts[0] không phải họ nhưng parts[1] là họ → tên đặt kiểu Tây, đảo lại
  let ordered = parts;
  if (
    parts.length === 2 &&
    !ho.has(parts[0].toLowerCase()) &&
    ho.has(parts[1].toLowerCase())
  ) {
    ordered = [parts[1], parts[0]];
  }

  // Đệm là các phần giữa (bỏ họ và tên cuối)
  const middles = ordered.slice(1, -1).map((p) => p.toLowerCase());
  if (middles.includes("thị")) return "Nữ";
  if (middles.includes("văn") || middles.includes("việt")) return "Nam";

  // Tên cuối (dùng ordered để xử lý đúng khi tên kiểu Tây)
  const given = ordered[ordered.length - 1].toLowerCase();

  const female = new Set([
    "hương",
    "lan",
    "mai",
    "hoa",
    "linh",
    "ngọc",
    "phương",
    "thanh",
    "thu",
    "trang",
    "xuân",
    "yến",
    "ánh",
    "bích",
    "chi",
    "diễm",
    "giang",
    "hà",
    "hiền",
    "hồng",
    "lệ",
    "lý",
    "my",
    "nhi",
    "nhung",
    "oanh",
    "quỳnh",
    "tâm",
    "thảo",
    "thùy",
    "tuyết",
    "uyên",
    "vân",
    "vy",
    "loan",
    "hạnh",
    "hằng",
    "huệ",
    "kim",
    "liên",
    "na",
    "trâm",
    "trúc",
    "huyền",
    "đào",
    "thục",
    "tiên",
    "tố",
    "dung",
    "nữ",
    "như",
    "ni",
    "thơ",
    "ly",
    "ngân",
    "thư",
    "khanh",
    "ân",
    "an",
    "em",
    "điệp",
    "phụng",
    "trinh",
    "tuyền",
  ]);

  const male = new Set([
    "hùng",
    "dũng",
    "cường",
    "tuấn",
    "minh",
    "nam",
    "đức",
    "hải",
    "huy",
    "khoa",
    "long",
    "mạnh",
    "phúc",
    "quang",
    "sơn",
    "thành",
    "trung",
    "việt",
    "bình",
    "đạt",
    "hào",
    "hiệp",
    "hiếu",
    "hoàng",
    "khang",
    "khiêm",
    "kiên",
    "lâm",
    "lực",
    "nhân",
    "phong",
    "quân",
    "quốc",
    "tài",
    "tân",
    "thắng",
    "thịnh",
    "thọ",
    "toàn",
    "tùng",
    "vương",
    "duy",
    "gia",
    "giáp",
    "hậu",
    "khải",
    "khoa",
    "lộc",
    "nghĩa",
    "nghị",
    "phát",
    "phước",
    "sang",
    "tấn",
    "thái",
    "thiện",
    "thức",
    "tiến",
    "tín",
    "trọng",
    "trực",
    "tú",
    "vũ",
    "vương",
    "xuân",
    "yên",
  ]);

  // Tên 2 chữ không có họ rõ ràng: kiểm tra cả 2 chữ — nếu trái chiều thì không đoán
  const noHoDetected =
    !ho.has(parts[0].toLowerCase()) && !ho.has(parts[1]?.toLowerCase());
  if (ordered.length === 2 && noHoDetected) {
    const first = ordered[0].toLowerCase();
    const firstF = female.has(first),
      firstM = male.has(first);
    const givenF = female.has(given),
      givenM = male.has(given);
    if (firstF && givenM) return null; // xung đột → không đoán
    if (firstM && givenF) return null;
  }

  if (female.has(given)) return "Nữ";
  if (male.has(given)) return "Nam";

  return null; // không chắc → không điền, tránh sai
}
