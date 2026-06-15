const FIELDS = ["airtableKey", "airtableBase"];

chrome.storage.local.get(FIELDS, (data) => {
  FIELDS.forEach((f) => {
    if (data[f]) document.getElementById(f).value = data[f];
  });
});

document.getElementById("save").addEventListener("click", () => {
  const data = {};
  FIELDS.forEach((f) => {
    data[f] = document.getElementById(f).value.trim();
  });

  chrome.storage.local.set(data, () => {
    const msg = document.getElementById("saved-msg");
    msg.style.display = "block";
    setTimeout(() => {
      msg.style.display = "none";
    }, 2000);
  });
});
