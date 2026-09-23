"use strict";
const content = document.getElementById("content");
const error = document.getElementById("error");
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("access")) {
  sessionStorage.setItem("diagnostic-access", fragment.get("access"));
  history.replaceState(null, "", location.pathname);
}
const token = sessionStorage.getItem("diagnostic-access") || "";
function node(tag, text, parent = content) {
  const el = document.createElement(tag); el.textContent = text; parent.append(el); return el;
}
async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: {Authorization: `Bearer ${token}`, "Content-Type": "application/json", "X-Epistemics-Request": "1"},
    ...(body === undefined ? {} : {body: JSON.stringify(body)})
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function percent(value) {
  if (!/^\d{1,3}$/.test(value) || Number(value) > 100) throw new Error("Enter a whole percentage from 0 to 100 for every question.");
  return Number(value) / 100;
}
function button(label, action, parent = content) {
  const el = node("button", label, parent); el.type = "button";
  el.onclick = async () => {
    el.disabled = true; error.textContent = "";
    try { await action(); await render(); } catch (e) { error.textContent = e.message; }
    finally { el.disabled = false; }
  }; return el;
}
async function render() {
  const state = await api("/api/state"); content.replaceChildren();
  window.scrollTo(0, 0);
  document.getElementById("progress").textContent = `Case ${state.case_number} of ${state.case_count}${state.synthetic ? " · Synthetic preview" : " · Private participation"}`;
  if (state.complete) { node("h2", "All eight cases are complete"); node("p", "Your answers are saved privately. The evaluator can now prepare the diagnostic report. Thank you."); return; }
  if (!state.started) {
    node("p", state.protocol.instructions.replace("Report probabilities from 0 to 1 in increments of 0.01 (whole percentages in the browser).", "Report probabilities as whole percentages from 0 to 100."));
    node("p", "There are eight cases, each with four checkpoints and ten probability judgments. Results stay local and private. You can close this page and resume using the private link.");
    button("I understand — begin", () => api("/api/begin", {instructions_accepted: true})); return;
  }
  if (state.current.complete) {
    node("h2", "Case complete");
    button("Save this case and continue", () => api("/api/finish", {assignment_id: state.assignment_id})); return;
  }
  const trial = state.current.trial;
  node("h2", `${trial.company} · ${trial.stage}`);
  node("p", `Related event: ${trial.auxiliary_event}.`);
  const evidence = node("section", "");
  for (const text of trial.documents) node("p", text, evidence);
  const table = node("table", "", evidence); const head = node("tr", "", table);
  for (const text of ["Growth above 10%", "Related event occurred", "Companies"]) node("th", text, head);
  for (const row of trial.archive) {
    const tr = node("tr", "", table);
    for (const value of [row.growth_above_10_percent ? "Yes" : "No", row.auxiliary_event ? "Yes" : "No", row.companies]) node("td", String(value), tr);
  }
  const form = node("form", ""); form.onsubmit = e => e.preventDefault();
  const questions = {growth_probability: "Probability that revenue growth exceeded 10%", auxiliary_probability: "Probability that the related event occurred"};
  if (trial.request_conditionals) Object.assign(questions, {
    auxiliary_if_growth: "If an audit established growth above 10%, probability of the related event",
    auxiliary_if_no_growth: "If an audit established growth of 10% or less, probability of the related event"
  });
  node("p", "Enter whole percentages (0–100).", form);
  for (const [name, text] of Object.entries(questions)) {
    const label = node("label", text, form); const input = document.createElement("input");
    Object.assign(input, {name, type: "number", min: "0", max: "100", step: "1", required: true}); label.append(input);
  }
  button("Commit these answers", async () => {
    const answer = Object.fromEntries(Object.keys(questions).map(k => [k, percent(form.elements.namedItem(k).value)]));
    await api("/api/answers", {assignment_id: state.assignment_id, trial_id: trial.trial_id, answer});
  }, form);
  if (state.history.length) {
    const details = node("details", ""); node("summary", "Your accepted answers", details);
    for (const row of state.history) {
      node("p", row.trial.stage, details);
      node("pre", Object.entries(row.answer).filter(([,v]) => v !== null).map(([k,v]) => `${k.replaceAll("_", " ")}: ${Math.round(v * 100)}%`).join("\n"), details);
    }
  }
}
render().catch(e => { error.textContent = e.message; });
