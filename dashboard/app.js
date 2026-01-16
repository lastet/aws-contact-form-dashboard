const SUBMISSIONS_ENDPOINT = "https://8ego95k5bc.execute-api.us-east-1.amazonaws.com/prod/submissions"; // <-- replace

function fmtUTC(ms) {
  const d = new Date(Number(ms));
  return isNaN(d.getTime()) ? "" : d.toISOString().replace("T", " ").replace("Z", " UTC");
}

function dayKeyUTC(ms) {
  const d = new Date(Number(ms));
  if (isNaN(d.getTime())) return "";
  return d.toISOString().slice(0,10); // YYYY-MM-DD
}

async function load() {
  const err = document.getElementById("error");
  err.textContent = "";

  const limit = Number(document.getElementById("limit").value || "50");
  document.getElementById("endpoint").value = `${SUBMISSIONS_ENDPOINT}?limit=${limit}`;

  const res = await fetch(`${SUBMISSIONS_ENDPOINT}?limit=${limit}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  const data = await res.json();

  const items = data.items || [];
  document.getElementById("count").textContent = String(items.length);

  // basic analytics: today + last 7 days (UTC)
  const now = Date.now();
  const todayKey = new Date(now).toISOString().slice(0,10);
  const weekAgo = now - 7*24*60*60*1000;

  let todayCount = 0;
  let weekCount = 0;

  const rows = items.map(it => {
    const createdAt = it.createdAt ?? "";
    const k = dayKeyUTC(createdAt);
    if (k === todayKey) todayCount++;
    if (Number(createdAt) >= weekAgo) weekCount++;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${fmtUTC(createdAt)}</td>
      <td>${escapeHtml(it.name || "")}</td>
      <td>${escapeHtml(it.email || "")}</td>
      <td>${escapeHtml(it.subject || "")}</td>
      <td>${escapeHtml((it.message || "")).replace(/\n/g,"<br>")}</td>
      <td>${escapeHtml(it.sourceIp || "")}</td>
    `;
    return tr;
  });

  document.getElementById("today").textContent = String(todayCount);
  document.getElementById("week").textContent = String(weekCount);

  const tbody = document.getElementById("rows");
  tbody.innerHTML = "";
  rows.forEach(r => tbody.appendChild(r));
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}

document.getElementById("reload").addEventListener("click", () => {
  load().catch(e => document.getElementById("error").textContent = String(e));
});

load().catch(e => document.getElementById("error").textContent = String(e));
