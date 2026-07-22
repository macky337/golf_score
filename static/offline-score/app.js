const STORAGE_PREFIX = "golf-score-offline:";
const sections = [
  { id: "front", label: "アウト", score: "front_score", putt: "front_putt", game: "front_game_pt" },
  { id: "back", label: "イン", score: "back_score", putt: "back_putt", game: "back_game_pt" },
  { id: "extra", label: "エキストラ", score: "extra_score", putt: "extra_putt", game: "extra_game_pt" },
];
let packageData = null;
let activeSection = "front";

const status = document.querySelector("#status");
const editor = document.querySelector("#editor");
const tabs = document.querySelector("#tabs");
const players = document.querySelector("#players");
const totals = document.querySelector("#totals");
const exportButton = document.querySelector("#export-file");

function storageKey() { return `${STORAGE_PREFIX}${packageData?.round?.round_id || "draft"}`; }
function setStatus(message) { status.textContent = message; }
function readDraft(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function writeDraft(key, value) {
  try { localStorage.setItem(key, value); return true; } catch { return false; }
}

function saveLocal(checkpoint) {
  if (!packageData) return;
  packageData.updated_at = new Date().toISOString();
  packageData.checkpoints = packageData.checkpoints || {};
  if (checkpoint) packageData.checkpoints[checkpoint] = packageData.updated_at;
  const saved = writeDraft(storageKey(), JSON.stringify(packageData));
  setStatus(saved
    ? `${checkpoint || "全入力"}を端末に保存しました: ${new Date().toLocaleTimeString("ja-JP")}`
    : "このブラウザでは自動保存できないため、終了後に同期ファイルを必ず出力してください。");
}

function numberValue(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : 0;
}

function render() {
  if (!packageData) return;
  editor.hidden = false;
  exportButton.disabled = false;
  tabs.innerHTML = "";
  players.innerHTML = "";
  const section = sections.find((item) => item.id === activeSection);
  const isExtra = packageData.round?.has_extra === false && activeSection === "extra";

  sections.forEach((item) => {
    const button = document.createElement("button");
    button.textContent = item.label;
    button.className = item.id === activeSection ? "active" : "";
    button.onclick = () => { activeSection = item.id; render(); };
    tabs.appendChild(button);
  });

  if (isExtra) {
    players.innerHTML = "<div class='notice'>このラウンドはエキストラホールなしで設定されています。必要なら数値を入力できます。</div>";
  }

  packageData.players.forEach((player, index) => {
    const card = document.createElement("article");
    card.className = "player";
    card.innerHTML = `
      <div class="player-name">${escapeHtml(player.name)}</div>
      <div class="score-row">
        <label for="score-${index}">スコア</label>
        <input id="score-${index}" type="number" min="0" max="200" inputmode="numeric" value="${numberValue(player[section.score])}" />
      </div>
      <div class="score-row">
        <label for="putt-${index}">パット</label>
        <input id="putt-${index}" type="number" min="0" max="200" inputmode="numeric" value="${numberValue(player[section.putt])}" />
      </div>
      <div class="score-row">
        <label for="game-${index}">ゲームPt</label>
        <input id="game-${index}" type="number" min="-1000" max="1000" inputmode="text" value="${Number.parseInt(player[section.game], 10) || 0}" />
      </div>`;
    card.querySelector(`#score-${index}`).oninput = (event) => { player[section.score] = numberValue(event.target.value); updateTotals(); saveLocal(); };
    card.querySelector(`#putt-${index}`).oninput = (event) => { player[section.putt] = numberValue(event.target.value); updateTotals(); saveLocal(); };
    card.querySelector(`#game-${index}`).oninput = (event) => { player[section.game] = Number.parseInt(event.target.value, 10) || 0; updateTotals(); saveLocal(); };
    players.appendChild(card);
  });
  updateTotals();
  setStatus(`${packageData.round.date_played} / ${packageData.round.course_name} を入力中（端末保存対応）`);
}

function updateTotals() {
  const rows = packageData.players.map((player) => {
    const score = sections.reduce((sum, section) => sum + numberValue(player[section.score]), 0);
    const putt = sections.reduce((sum, section) => sum + numberValue(player[section.putt]), 0);
    const gamePoint = sections.reduce((sum, section) => sum + (Number.parseInt(player[section.game], 10) || 0), 0);
    return `<div>${escapeHtml(player.name)}：<strong>${score}</strong> 打 / ${putt} パット / ゲームPt ${gamePoint >= 0 ? "+" : ""}${gamePoint}</div>`;
  });
  totals.innerHTML = `<h2>合計</h2>${rows.join("")}`;
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

function loadPackage(parsed) {
  if (parsed?.format !== "golf-score-offline-v1" || !parsed.round?.round_id || !Array.isArray(parsed.players)) {
    throw new Error("format");
  }
  const saved = readDraft(`${STORAGE_PREFIX}${parsed.round.round_id}`);
  packageData = saved ? JSON.parse(saved) : parsed;
  render();
}

document.querySelector("#import-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const parsed = JSON.parse(await file.text());
    loadPackage(parsed);
  } catch {
    setStatus("ラウンドデータを読み込めませんでした。Webアプリから出力したJSONを選択してください。");
  }
});

document.querySelector("#save-checkpoint").onclick = () => saveLocal(sections.find((item) => item.id === activeSection).id);
document.querySelector("#save-all").onclick = () => saveLocal("round");
exportButton.onclick = () => {
  if (!packageData) return;
  packageData.sync_exported_at = new Date().toISOString();
  saveLocal("round");
  const blob = new Blob([JSON.stringify(packageData, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `golf-round-${packageData.round.round_id}-sync.json`;
  link.click();
  URL.revokeObjectURL(link.href);
};

if (window.__GOLF_SCORE_INITIAL_PACKAGE__) {
  try {
    loadPackage(window.__GOLF_SCORE_INITIAL_PACKAGE__);
    document.querySelector("#start-notice").textContent =
      "選択したラウンドを読み込みました。JSONを選び直さず、そのまま入力できます。";
  } catch {
    setStatus("ラウンドデータを読み込めませんでした。予備JSONを選択してください。");
  }
} else {
  setStatus("予備JSONを選択してください。");
}
