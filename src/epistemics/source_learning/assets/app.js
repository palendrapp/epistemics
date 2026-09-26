"use strict";
const content = document.getElementById("content");
const error = document.getElementById("error");
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("access")) {
  sessionStorage.setItem("source-learning-access", fragment.get("access"));
  history.replaceState(null, "", location.pathname);
}
const token = sessionStorage.getItem("source-learning-access") || "";
const queryNames = {customer_panel: "Independent customer panel", selection_audit: "Audit panel selection", measurement_audit: "Audit measurement accuracy", stop: "Stop research"};
function node(tag, text, parent = content) {
  const element = document.createElement(tag); element.textContent = text; parent.append(element); return element;
}
async function api(path, body) {
  const response = await fetch(path, {method: body === undefined ? "GET" : "POST",
    headers: {Authorization: `Bearer ${token}`, "Content-Type": "application/json", "X-Epistemics-Request": "1"},
    ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  const data = await response.json(); if (!response.ok) throw new Error(data.error || "Request failed"); return data;
}
function button(label, action, parent = content) {
  const element = node("button", label, parent); element.type = "button";
  element.onclick = async () => {
    element.disabled = true; error.textContent = "";
    try { await action(); await render(); } catch (e) { error.textContent = e.message; }
    finally { element.disabled = false; }
  }; return element;
}
function percentInput(form, name, title) {
  const label = node("label", title, form); const input = node("input", "", label);
  Object.assign(input, {name, type: "number", min: "0", max: "100", step: "1", required: true});
}
function selectInput(form, name, title, options) {
  const label = node("label", title, form); const select = node("select", "", label);
  select.name = name; select.required = true;
  for (const [value, text] of [["", "Choose an option"], ...options]) node("option", text, select).value = value;
}
function percentage(form, name) {
  const text = form.elements.namedItem(name).value;
  if (!/^\d{1,3}$/.test(text) || Number(text) > 100) throw new Error("Enter a whole percentage from 0 to 100 for every probability.");
  return Number(text) / 100;
}
async function render() {
  const state = await api("/api/state"); content.replaceChildren(); window.scrollTo(0, 0);
  const p = state.protocol;
  document.getElementById("progress").textContent = `${p.response_origin === "synthetic" ? "Synthetic preview" : "Private participation"} · ${p.condition === "dense" ? "With source questions" : "Company forecasts and choices"}`;
  if (!state.started) {
    node("p", "24 fictional companies, six recurring sources and 36 checkpoints. You can pause and resume using this private link. Answers stay local and private.");
    node("p", p.instructions.replace("Reports use 0 to 1 in increments of 0.01 (whole percentages in the browser).", "Report whole percentages from 0 to 100."));
    node("p", p.diagnostics);
    button("I understand — begin", () => api("/api/begin", {instructions_accepted: true})); return;
  }
  if (state.current.complete) {
    node("h2", state.current.finished ? "Collection complete" : "All answers are saved");
    const last = state.history.at(-1);
    if (last) node("p", `The final company resolved: ${last.resolved_strong ? "strong" : "weak"} demand.`);
    node("p", state.current.finished ? "Your answers are saved privately. Thank you." : "Finish to make the collection available for private analysis.");
    if (!state.current.finished) button("Finish collection", () => api("/api/finish", {}));
    return;
  }
  const trial = state.current.trial;
  document.getElementById("progress").textContent += ` · Checkpoint ${trial.checkpoint} of 36`;
  const stage = {forecast: "Initial forecast", research: "Forecast and research", revision: "Revised forecast and decision"}[trial.stage];
  node("h2", `${trial.company_id.replace("company-", "Company ")} · ${stage}`);
  const last = state.history.at(-1);
  if (last && last.resolved_strong !== null) node("p", `${last.trial.company_id.replace("company-", "Company ")} resolved: ${last.resolved_strong ? "strong" : "weak"} demand. Its record is now available in source history.`).className = "resolved";
  const evidence = node("section", ""); node("h3", "Company evidence", evidence);
  for (const text of trial.documents) node("p", text, evidence);
  if (trial.known_selection) {
    const r = trial.known_selection;
    node("p", r.direction === "random" ? "Known from an audit: one random panel." : `Known from an audit: the ${r.direction} count among ${r.panels} panels.`, evidence);
  }
  if (trial.known_measurement_accuracy !== null) node("p", `Known from an audit: ${Math.round(trial.known_measurement_accuracy * 100)}% individual measurement accuracy.`, evidence);
  const archive = node("details", ""); archive.open = true;
  node("summary", `${trial.source_id}: resolved track record`, archive);
  node("p", "The first twelve records deliberately balance strong and weak companies. Later records come from completed companies in this collection.", archive);
  const scroll = node("div", "", archive); scroll.className = "scroll";
  const table = node("table", "", scroll); node("caption", "What the source reported and what was later resolved", table);
  const header = node("tr", "", node("thead", "", table));
  for (const text of ["Record", "Reported expansion", "Resolved demand"]) node("th", text, header).scope = "col";
  const body = node("tbody", "", table);
  trial.archive.forEach((record, i) => { const row = node("tr", "", body); for (const text of [String(i + 1), `${record.count} of 5`, record.resolved_strong ? "Strong" : "Weak"]) node("td", text, row); });
  if (state.history.length) {
    const details = node("details", ""); node("summary", "Earlier evidence and your accepted answers", details);
    for (const row of state.history) {
      node("h3", `${row.trial.company_id} · ${row.trial.stage}`, details);
      for (const text of row.trial.documents) node("p", text, details);
      node("p", `Your forecast: ${Math.round(row.answer.probability * 100)}%. Decision: ${row.answer.decision}.`, details);
      if (row.answer.query) node("p", `Research: ${queryNames[row.answer.query]}.`, details);
      if (row.answer.measurement_accuracy !== null) node("p", `Your source estimates: ${Math.round(row.answer.measurement_accuracy * 100)}% accuracy; ${Math.round(row.answer.random_selection_probability * 100)}% chance of random selection.`, details);
      if (row.resolved_strong !== null) node("p", `Resolved: ${row.resolved_strong ? "strong" : "weak"} demand.`, details);
    }
  }
  const form = node("form", ""); form.onsubmit = event => event.preventDefault();
  percentInput(form, "probability", "Probability of strong demand (%)");
  selectInput(form, "decision", trial.stage === "research" ? "Provisional decision before research" : "Your investment decision", [["invest", "Invest"], ["decline", "Decline"]]);
  if (trial.request_diagnostics) {
    percentInput(form, "measurement_accuracy", "Chance that an individual customer measurement is recorded correctly (%)");
    percentInput(form, "random_selection_probability", "Chance that this source reports a random panel, rather than selecting by the measured result (%)");
  }
  if (trial.stage === "research") {
    node("p", "Choose one check or stop. Customer research gives an accurate, independent random panel. A selection audit establishes how panels are chosen; a measurement audit establishes individual accuracy. Audits remain useful for later companies.", form);
    selectInput(form, "query", "Research purchase", Object.entries(trial.research_costs).map(([q, cost]) => [q, `${queryNames[q]} · ${cost.toFixed(3)} points`]));
  }
  button("Commit these answers", async () => {
    const answer = {probability: percentage(form, "probability"), decision: form.elements.namedItem("decision").value};
    if (!answer.decision) throw new Error("Choose invest or decline.");
    if (trial.request_diagnostics) for (const key of ["measurement_accuracy", "random_selection_probability"]) answer[key] = percentage(form, key);
    if (trial.stage === "research") { answer.query = form.elements.namedItem("query").value; if (!answer.query) throw new Error("Choose research or stop."); }
    await api("/api/answers", {trial_id: trial.trial_id, answer});
  }, form);
}
render().catch(e => { error.textContent = e.message; });
