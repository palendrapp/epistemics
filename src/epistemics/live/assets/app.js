"use strict";

const app = document.querySelector("#app");
const status = document.querySelector("#status");
let protocol;
let current;

function el(tag, text, attrs = {}) {
  const node = document.createElement(tag);
  if (text !== null && text !== undefined) node.textContent = text;
  for (const [key, value] of Object.entries(attrs))
    node.setAttribute(key, value);
  return node;
}
function add(parent, ...children) {
  parent.append(...children);
  return parent;
}
function panel(title, parent) {
  const node = el("section", null, { class: "panel" });
  if (title) node.append(el("h2", title));
  parent.append(node);
  return node;
}
function details(parent, title, open = false) {
  const node = el("details");
  node.open = open;
  node.append(el("summary", title));
  parent.append(node);
  return node;
}
function field(parent, label, name, options = {}) {
  const wrapper = el("label", null, { class: "field" });
  const input = el("input", null, {
    name,
    id: name,
    type: "number",
    step: "any",
    required: "",
    ...options,
  });
  add(wrapper, el("span", label, { class: "field-title" }), input);
  parent.append(wrapper);
  return input;
}
function hint(parent, text) {
  parent.append(el("p", text, { class: "hint" }));
}
function table(parent, headings, rows) {
  const node = el("table");
  const head = el("tr");
  headings.forEach((h) => head.append(el("th", h, { scope: "col" })));
  node.append(add(el("thead"), head));
  const body = el("tbody");
  for (const row of rows)
    body.append(add(el("tr"), ...row.map((v) => el("td", String(v)))));
  node.append(body);
  parent.append(add(el("div", null, { class: "table-wrap" }), node));
}
function check(parent, text, name, value, required = false) {
  const input = el("input", null, { type: "checkbox", name, value });
  input.required = required;
  parent.append(
    add(el("label", null, { class: "check" }), input, el("span", text)),
  );
  return input;
}
function percent(form, name) {
  const input = form.elements.namedItem(name);
  if (!input || input.value.trim() === "")
    throw new Error("Enter each requested probability.");
  const value = Number(input.value);
  if (!Number.isFinite(value) || value < 0 || value > 100)
    throw new Error("Probabilities must be between 0 and 100%.");
  return value / 100;
}
function number(form, name) {
  const input = form.elements.namedItem(name);
  if (
    !input ||
    input.value.trim() === "" ||
    !Number.isFinite(Number(input.value))
  )
    throw new Error("Enter every requested numeric value.");
  return Number(input.value);
}
async function api(path, body) {
  const response = await fetch(
    path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Epistemics-Request": "1",
          },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
function failure(error) {
  status.textContent =
    error.message ||
    "Connection interrupted. Your accepted answers are saved. Try again.";
}
function demoBanner(parent) {
  if (protocol.synthetic_demo)
    parent.append(
      el(
        "p",
        "Synthetic demo — responses in this server are marked synthetic, including those entered through this browser.",
        { class: "banner" },
      ),
    );
}
function instructions(parent) {
  const list = el("ul", null, { class: "instructions" });
  protocol.guide.instructions.forEach((text) => list.append(el("li", text)));
  parent.append(list);
}
function declaration(parent, title, name) {
  const wrapper = el("label", null, { class: "field" });
  const select = el("select", null, { name });
  for (const [value, text] of [
    ["unknown", "Not declared"],
    ["none", "None"],
    ["declared", "I will use the following…"],
  ])
    select.append(el("option", text, { value }));
  add(wrapper, el("span", title, { class: "field-title" }), select);
  parent.append(wrapper);
  const input = field(
    parent,
    `List ${title.toLowerCase()} (separated by commas)`,
    `${name}_list`,
    { type: "text" },
  );
  input.closest("label").hidden = true;
  input.required = false;
  select.addEventListener("change", () => {
    input.closest("label").hidden = select.value !== "declared";
    input.required = select.value === "declared";
  });
  return () =>
    select.value === "unknown"
      ? null
      : select.value === "none"
        ? []
        : input.value
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);
}

function landing() {
  app.replaceChildren();
  const root = add(
    el("div", null, { class: "intro" }),
    el("p", "Epistemic passport / core 0.1", { class: "eyebrow" }),
  );
  app.append(root);
  demoBanner(root);
  add(
    root,
    el("h1", protocol.guide.title),
    el("p", protocol.guide.description, { class: "lead" }),
  );
  const sections = el("div", null, { class: "sections" });
  for (const section of protocol.guide.sections) {
    const card = panel(null, sections);
    add(
      card,
      el("span", `${section.checkpoints} checkpoints`, { class: "eyebrow" }),
      el("h3", section.name),
      el("p", section.description),
    );
  }
  root.append(sections);
  const guide = panel("Before you begin", root);
  instructions(guide);
  hint(
    guide,
    "Your passport will describe responses in this battery. It is provisional and unsigned. Results are not a diagnosis or a certified identity. Keep this browser’s cookie to resume; other people with access to this local server may start their own sessions.",
  );
  const practice = panel("A quick practice", root);
  practice.append(el("p", protocol.guide.practice.prompt));
  const input = field(practice, "Practice probability (%)", "practice", {
    min: "0",
    max: "100",
    class: "numeric",
  });
  input.required = false;
  const feedback = el("p", null, { role: "status", class: "hint" });
  const checkPractice = el("button", "Check example", {
    type: "button",
    class: "secondary",
  });
  checkPractice.addEventListener("click", () => {
    feedback.textContent =
      (input.value.trim() !== "" &&
      Number(input.value) === protocol.guide.practice.answer_percent
        ? "Yes. "
        : "For this example: ") + protocol.guide.practice.explanation;
  });
  add(practice, checkPractice, feedback);
  const form = el("form");
  const setup = panel("Your private session", form);
  field(setup, "Pseudonym (optional)", "subject_id", {
    type: "text",
    maxlength: "256",
    autocomplete: "off",
  }).required = false;
  hint(
    setup,
    "A local pseudonym is generated if you leave this blank. You do not need to provide your name.",
  );
  const tools = declaration(setup, "Tools", "tools");
  const assistance = declaration(setup, "Assistance", "assistance");
  hint(
    setup,
    "Separate multiple items with commas. These declarations apply to the whole run; select tools and assistance before starting.",
  );
  check(
    setup,
    "I have read the instructions and agree to save my answers and results on this computer.",
    "consent",
    "yes",
    true,
  );
  const start = el("button", "Begin evaluation", { type: "submit" });
  setup.append(add(el("div", null, { class: "actions" }), start));
  let pending = null;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "";
    if (!form.reportValidity()) return;
    if (!pending)
      pending = {
        request_id: crypto.randomUUID(),
        subject_id: form.elements.subject_id.value.trim(),
        instructions_accepted: true,
        tools: tools(),
        assistance: assistance(),
      };
    start.disabled = true;
    try {
      await api("/api/sessions", pending);
      await refresh();
      window.scrollTo({ top: 0 });
    } catch (error) {
      failure(error);
      for (const control of form.querySelectorAll("input,select"))
        control.disabled = true;
      start.textContent = "Retry starting this session";
    } finally {
      start.disabled = false;
    }
  });
  root.append(form);
}

function materials(parent, payload) {
  const background = details(
    parent,
    "Company background and task instructions",
    payload.index === 0,
  );
  add(background, el("p", payload.background), el("p", payload.instructions));
  const sources = details(
    parent,
    "Sources and their audited track records",
    payload.index === 0,
  );
  for (const source of payload.sources) {
    const section = details(sources, source.name, payload.index === 0);
    section.append(el("p", source.profile));
    table(
      section,
      ["Case", "Reported (%)", "Audited (%)"],
      source.archive.map((r) => [r.case_id, r.reported_pct, r.audited_pct]),
    );
  }
  const analogues = details(
    parent,
    "Historical company analogues",
    payload.index === 0,
  );
  table(
    analogues,
    [
      "Case",
      "Underlying growth (%)",
      "Disruption",
      "Backlog",
      "Renewal growth (%)",
    ],
    payload.analogues.map((r) => [
      r.case_id,
      r.underlying_growth_pct,
      r.rollout_disruption ? "Yes" : "No",
      r.backlog_score,
      r.renewal_growth_pct,
    ]),
  );
  const documents = panel("Available documents", parent);
  if (!payload.documents.length)
    documents.append(
      el(
        "p",
        "No company documents yet. Make your initial assessment from the background, sources and analogues.",
      ),
    );
  payload.documents.forEach((doc, index) => {
    const node = details(
      documents,
      `${index === payload.documents.length - 1 ? "New · " : ""}${doc.title}`,
      index === payload.documents.length - 1,
    );
    add(
      node,
      el("p", `${doc.document_id} · ${doc.source} · ${doc.published_at}`, {
        class: "document-id",
      }),
      el("p", doc.text, { class: "document-body" }),
    );
  });
}
function discoveryForm(form, payload) {
  const event =
    payload.target_event === "growth_above_12"
      ? "exceeds 12%"
      : "is at or below 12%";
  field(
    form,
    `Probability next-year revenue growth ${event} (%)`,
    "target_probability",
    { min: "0", max: "100" },
  );
  form.append(el("h3", "Your revenue growth forecast"));
  hint(
    form,
    "Enter growth values in percent. For example, a median of 8 means 8% growth. Negative growth is allowed. These describe growth itself, whichever event appears above.",
  );
  const quantiles = el("div", null, { class: "quantiles" });
  for (const q of [10, 50, 90]) field(quantiles, `${q}th percentile`, `q${q}`);
  form.append(quantiles);
  hint(form, "Use increasing values: 10th ≤ 50th ≤ 90th percentile.");
  const actionLabel = el("label", null, { class: "field" });
  const action = el("select", null, { name: "decision", required: "" });
  for (const [value, label] of [
    ["", "Choose an action"],
    ["invest", "Invest"],
    ["hold", "Hold"],
  ])
    action.append(el("option", label, { value }));
  add(
    actionLabel,
    el("span", "Your decision", { class: "field-title" }),
    action,
  );
  add(form, actionLabel);
  hint(
    form,
    "Invest: +2 if growth exceeds 12%, −1 otherwise. Hold: 0. Choose the highest expected payoff; hold on a tie. No switching costs.",
  );
  for (const sourceId of payload.source_probe_ids) {
    const source = payload.sources.find((s) => s.source_id === sourceId);
    field(
      form,
      `${source.name}: chance the next raw estimate is within 2 percentage points of a later audit (%)`,
      `source_${sourceId}`,
      { min: "0", max: "100" },
    );
  }
  if (payload.source_probe_ids.length)
    hint(
      form,
      "Judge the raw estimate’s accuracy without correcting its bias.",
    );
  if (payload.conditional_probe) {
    field(
      form,
      "Chance growth exceeds 12% if a reliable inspection establishes no implementation disruption (%)",
      "conditional",
      { min: "0", max: "100" },
    );
  }
  const extractionLabels = {
    renewal_estimate_pct:
      "Copy Morrow Analytics’ stated renewal-supported growth estimate from its document (%)",
    model_projection_pct:
      "Copy the stated model projection from the broker’s Inspectable scenario model (%)",
  };
  for (const key of payload.extraction_keys)
    field(form, extractionLabels[key] || key, `extract_${key}`);
  if (payload.documents.length) {
    form.append(el("h3", "Which documents did you use?"));
    for (const doc of payload.documents)
      check(form, doc.title, "evidence", doc.document_id);
    hint(
      form,
      "Select any documents that informed this answer. Selecting none is allowed.",
    );
  }
  const explanation = el("label", null, { class: "field" });
  add(
    explanation,
    el("span", "Alternative explanation (optional)", { class: "field-title" }),
    el("textarea", null, { name: "alternative", rows: "2", maxlength: "1200" }),
  );
  form.append(explanation);
}
function buildAnswer(form, trial) {
  if (trial.module === "calibration")
    return { probability: percent(form, "probability") };
  const payload = trial.payload;
  const quantiles = {
    p10: number(form, "q10"),
    p50: number(form, "q50"),
    p90: number(form, "q90"),
  };
  if (quantiles.p10 > quantiles.p50 || quantiles.p50 > quantiles.p90)
    throw new Error("Growth percentiles must be ordered: 10th ≤ 50th ≤ 90th.");
  return {
    target_probability: percent(form, "target_probability"),
    growth_quantiles_pct: quantiles,
    decision: form.elements.decision.value,
    evidence_ids: [
      ...form.querySelectorAll('input[name="evidence"]:checked'),
    ].map((i) => i.value),
    source_accuracy: Object.fromEntries(
      payload.source_probe_ids.map((id) => [id, percent(form, `source_${id}`)]),
    ),
    conditional_growth_probability: payload.conditional_probe
      ? percent(form, "conditional")
      : null,
    extracted_values: Object.fromEntries(
      payload.extraction_keys.map((key) => [
        key,
        number(form, `extract_${key}`),
      ]),
    ),
    alternative_explanation: form.elements.alternative.value.trim() || null,
  };
}
function history(parent) {
  if (!current.history.length) return;
  const node = details(
    parent,
    `Review ${current.history.length} accepted answer${current.history.length === 1 ? "" : "s"}`,
  );
  hint(
    node,
    "Accepted answers cannot be edited. Probabilities below use the stored 0–1 scale.",
  );
  const list = el("div", null, { class: "history" });
  current.history.forEach((item, i) => {
    const answer = item.answer;
    const probability = answer.target_probability ?? answer.probability;
    const row = details(
      list,
      `${i + 1}. ${item.module} · ${(probability * 100).toFixed(1)}% reported probability`,
    );
    row.append(el("pre", JSON.stringify(answer, null, 2)));
  });
  node.append(list);
}
function checkpoint() {
  app.replaceChildren();
  demoBanner(app);
  const trial = current.trial;
  const payload = trial.payload;
  const heading = el("div", null, { class: "session-head" });
  add(
    heading,
    add(
      el("div"),
      el(
        "p",
        `Checkpoint ${trial.index + 1} of 34 · ${trial.module === "discovery" ? "Company discovery" : "Probability calibration"}`,
        { class: "eyebrow" },
      ),
      el(
        "h1",
        trial.module === "discovery"
          ? payload.company
          : "One observation. Your assessment.",
      ),
    ),
  );
  heading.append(
    el(
      "p",
      `${current.answered} answer${current.answered === 1 ? "" : "s"} saved · No time limit`,
      {
        class: "muted",
      },
    ),
  );
  add(
    app,
    heading,
    el("progress", null, {
      class: "progress",
      max: "34",
      value: String(current.answered),
      "aria-label": "Evaluation progress",
    }),
  );
  const workspace = el("div", null, { class: "workspace" });
  const evidence = el("div");
  const response = el("div", null, { class: "response" });
  add(workspace, evidence, response);
  app.append(workspace);
  if (trial.module === "discovery") materials(evidence, payload);
  else {
    const card = panel(
      `Independent case ${trial.module_index + 1} of 24`,
      evidence,
    );
    card.append(el("p", payload.instructions));
    const s = payload.stimulus;
    for (const [value, label] of [
      [`${s.prior_h * 100}%`, "Starting probability H is true"],
      [`${s.sensor_accuracy * 100}%`, "Sensor accuracy for either true state"],
      [
        s.signal === 1 ? "H is true (1)" : "H is false (0)",
        "Observed sensor signal",
      ],
    ]) {
      card.append(
        add(
          el("div", null, { class: "stat" }),
          el("strong", value),
          el("span", label),
        ),
      );
    }
  }
  history(evidence);
  const guide = details(evidence, "Instructions and your session");
  instructions(guide);
  hint(
    guide,
    `Subject: ${current.context.participant.subject_id}. Tools: ${JSON.stringify(current.context.conditions.tools)}. Assistance: ${JSON.stringify(current.context.conditions.assistance)}. null means not declared. Pause by closing this tab; return in this browser to resume. Unsubmitted answers are not saved.`,
  );
  const form = el("form");
  const fields = el("fieldset");
  fields.style.border = "0";
  fields.style.padding = "0";
  fields.style.margin = "0";
  fields.style.minWidth = "0";
  const card = panel("Your assessment", fields);
  if (trial.module === "discovery") discoveryForm(card, payload);
  else
    field(card, "Probability H is true after this signal (%)", "probability", {
      min: "0",
      max: "100",
    });
  hint(
    card,
    "Submitting makes this answer final. Results appear after all 34 checkpoints.",
  );
  const submit = el("button", "Save answer & continue", { type: "submit" });
  card.append(submit);
  form.append(fields);
  response.append(form);
  let pending = null;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "";
    try {
      if (!pending) {
        if (!form.reportValidity()) return;
        pending = {
          trial_id: trial.trial_id,
          answer: buildAnswer(form, trial),
        };
      }
      fields.disabled = true;
      await api("/api/answers", pending);
      await refresh();
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch (error) {
      failure(error);
      fields.disabled = false;
      if (pending) {
        // Freeze the submitted snapshot: a failed response may already have been accepted.
        for (const control of fields.querySelectorAll("input,select,textarea"))
          control.disabled = true;
        submit.textContent = "Retry saving this answer";
      }
    }
  });
}
function complete() {
  app.replaceChildren();
  const root = el("div", null, { class: "complete" });
  app.append(root);
  demoBanner(root);
  add(
    root,
    el("p", "34 / 34 checkpoints complete", { class: "eyebrow" }),
    el("h1", "Your evidence profile is ready."),
    el(
      "p",
      "Your passport brings together six dimensions, concrete examples from your answers, and the limits of what this run can tell us.",
      { class: "lead" },
    ),
  );
  add(
    root,
    el(
      "p",
      "This is a provisional, unsigned profile from one company case and 24 calibration questions. Participant identity and execution are declared, not independently verified. Any suggested support is untested.",
    ),
  );
  const actions = el("div", null, { class: "actions" });
  for (const [url, text, cls] of [
    ["/passport", "View your passport", "link-button"],
    ["/download/passport.md", "Markdown", ""],
    ["/download/passport.json", "Passport JSON", ""],
    ["/download/report.json", "Full report", ""],
  ])
    actions.append(el("a", text, { href: url, class: cls }));
  root.append(actions);
  hint(
    root,
    "Your full report contains all answers and the resolved case. It stays on this computer unless you choose to share it. No blockchain record has been published.",
  );
  history(root);
  const again = el("button", "Start another session", {
    type: "button",
    class: "secondary",
  });
  again.addEventListener("click", () => {
    status.textContent = "";
    landing();
    window.scrollTo({ top: 0 });
  });
  hint(
    root,
    "Download this passport before starting another session. Previous runs remain in the local database.",
  );
  root.append(again);
}
async function refresh() {
  const result = await api("/api/session");
  current = result.session;
  if (!current) landing();
  else if (current.complete) complete();
  else checkpoint();
}
async function init() {
  try {
    protocol = await api("/api/protocol");
    await refresh();
  } catch (error) {
    app.replaceChildren(
      el("h1", "Your session is unavailable."),
      el(
        "p",
        "Accepted answers are saved. Check that the original evaluator is running, then reload this page.",
      ),
    );
    failure(error);
  }
}
init();
