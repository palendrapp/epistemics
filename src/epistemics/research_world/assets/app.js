"use strict";
const content = document.getElementById("content");
const error = document.getElementById("error");
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("access")) {
  sessionStorage.setItem("research-world-access", fragment.get("access"));
  history.replaceState(null, "", location.pathname);
}
const token = sessionStorage.getItem("research-world-access") || "";
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
function selectInput(form, name, title, options) {
  const label = node("label", title, form); const select = node("select", "", label);
  select.name = name; select.required = true;
  for (const [value, text] of [["", "Choose an option"], ...options]) node("option", text, select).value = value;
}
function percentage(form, name) {
  const text = form.elements.namedItem(name).value;
  if (!/^\d{1,3}$/.test(text) || Number(text) > 100) throw new Error("Enter a whole percentage from 0 to 100.");
  return Number(text) / 100;
}
function documents(trial, parent) {
  for (const line of trial.case.split("\n")) node("p", line, parent);
  for (const doc of trial.documents) {
    const article = node("article", "", parent);
    node("h3", `${doc.doc_id} · ${doc.kind} · ${doc.source} · ${doc.date}`, article);
    node("p", doc.text, article);
  }
  if (trial.structure_note) node("p", `Structure note: ${trial.structure_note}`, parent).className = "resolved";
}
async function render() {
  const state = await api("/api/state"); content.replaceChildren(); window.scrollTo(0, 0);
  const p = state.protocol;
  document.getElementById("progress").textContent = p.response_origin === "synthetic" ? "Synthetic preview" : "Private participation";
  if (!state.started) {
    node("p", `${p.cases} fictional companies. You can pause and resume using this private link. Answers stay local and private.`);
    node("p", p.instructions.replace("from 0 to 1 in increments of 0.01", "as a whole percentage"));
    if (p.independent_survey) node("p", p.independent_survey);
    button("I understand — begin", () => api("/api/begin", {instructions_accepted: true})); return;
  }
  if (state.current.complete) {
    node("h2", state.current.finished ? "Collection complete" : "All answers are saved");
    node("p", state.current.finished ? "Your answers are saved privately. Thank you." : "Finish to make the collection available for private analysis.");
    if (!state.current.finished) button("Finish collection", () => api("/api/finish", {}));
    return;
  }
  const trial = state.current.trial;
  document.getElementById("progress").textContent += ` · Case ${trial.case_number} of ${trial.cases}`;
  node("h2", trial.stage === "final" ? "Final answer after your survey" : "Assessment");
  node("p", trial.instruction);
  if (trial.check_price !== undefined) node("p", `Independent survey price: ${trial.check_price.toFixed(2)} points, charged whichever decision you make.`);
  if (trial.check_cost_charged !== undefined) node("p", `Survey cost charged: ${trial.check_cost_charged.toFixed(2)} points.`);
  documents(trial, node("section", ""));
  const form = node("form", ""); form.onsubmit = event => event.preventDefault();
  const label = node("label", "Probability of strong demand (%)", form); const input = node("input", "", label);
  Object.assign(input, {name: "probability", type: "number", min: "0", max: "100", step: "1", required: true});
  selectInput(form, "decision", "Your decision", [["invest", "Invest"], ["decline", "Decline"]]);
  if (trial.check_price !== undefined) selectInput(form, "check", "Independent survey", [["buy", "Buy the survey"], ["skip", "Skip it"]]);
  button("Commit these answers", async () => {
    const answer = {probability: percentage(form, "probability"), decision: form.elements.namedItem("decision").value};
    if (!answer.decision) throw new Error("Choose invest or decline.");
    if (trial.check_price !== undefined) {
      answer.check = form.elements.namedItem("check").value;
      if (!answer.check) throw new Error("Choose whether to buy the survey.");
    }
    await api("/api/answers", {trial_id: trial.trial_id, answer});
  }, form);
}
render().catch(e => { error.textContent = e.message; });
