"use strict";
const $ = selector => document.querySelector(selector);
const labels = {source_audit:"Source audit",operations_check:"Backlog check",segment_check:"Unaffected cohort",calculation:"Calculation",stop:"Stop researching"};
let trial = null;
let pending = null;
let completedCase = null;
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json","X-Epistemics-Request":"1"},body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) {const error=new Error(result.error || "The request did not complete.");error.status=response.status;throw error;}
  return result;
}
function failure(error) { $("#error").textContent=error.message; $("#error").hidden=false; }
function node(tag, text, parent) { const el=document.createElement(tag); el.textContent=text; if(parent) parent.append(el); return el; }
function percent(form, name) {
  const raw=form.elements.namedItem(name).value.trim();
  const value=Number(raw);
  if(raw==="" || !Number.isInteger(value) || value<0 || value>100) throw new Error("Enter whole percentages from 0 to 100.");
  return value/100;
}
function buildAnswer(form,t) {
  const answer={};
  for(const name of ["growth_probability","audit_understatement_probability","backlog_high_probability"]) answer[name]=percent(form,name);
  answer.decision=form.elements.namedItem("decision").value;
  if(!["invest","hold"].includes(answer.decision)) throw new Error("Choose invest or hold.");
  if(t.options.length) {
    answer.query=form.elements.namedItem("query").value;
    if(!t.options.some(o=>o.query===answer.query)) throw new Error("Choose one research option or stop.");
  }
  if(t.expectation_queries.length) {
    answer.expectations={};
    for(const q of t.expectation_queries) {
      answer.expectations[q]={};
      for(const key of ["yes_probability","growth_if_yes","growth_if_no"]) answer.expectations[q][key]=percent(form,`${q}_${key}`);
    }
  }
  answer.explanation=form.elements.namedItem("explanation").value.trim() || null;
  return answer;
}
function table(parent,headers,rows) {
  const wrap=node("div","",parent);wrap.className="table-wrap";
  const t=node("table","",wrap),head=node("tr","",node("thead","",t));
  headers.forEach(h=>node("th",h,head));
  const body=node("tbody","",t);
  rows.forEach(row=>{const tr=node("tr","",body);row.forEach(v=>node("td",String(v),tr));});
}
async function refresh() {
  const state=await api("/api/state");
  $("#synthetic").hidden=!state.synthetic;
  $("#instructions").textContent=state.protocol.instructions.replace("Use whole percentages (0 to 100), represented in the API as probabilities in increments of 0.01.","Use whole percentages from 0 to 100.") + ` This evaluation contains ${state.case_count} company case${state.case_count===1?"":"s"}. Each company has its own record; use the current company's evidence. You may pause between cases and resume using this private link.`;
  $("#welcome").hidden=state.started;
  $("#task").hidden=!state.started || state.current.complete;
  $("#complete").hidden=!state.started || !state.current.complete;
  if(!state.started) return;
  if(state.current.complete) {
    await api("/api/finish",{assignment_id:state.assignment_id}); completedCase=state.assignment_id;
    const more=state.case_number<state.case_count;
    $("#next-case").hidden=!more;
    $("#completion-text").textContent=more ? `Case ${state.case_number} of ${state.case_count} is complete. The next company has a separate record. You can continue now or return later.` : "Thank you. This evaluation is complete. Outcomes and analysis are available only through the evaluator's private export. You can close this page.";
    return;
  }
  trial=state.current.trial;
  $("#answer").reset(); pending=null;
  $("#progress").textContent=`CASE ${state.case_number} OF ${state.case_count} · STAGE ${trial.index+1} OF 4`;
  $("#stage").textContent=trial.stage;
  $("#payoff").textContent=`Invest: +${trial.gain} on success / −${trial.loss} otherwise · Hold: 0`;
  $("#decision-label").textContent=trial.index===2 ? "Committed decision — determines your payoff" : trial.index===3 ? "Diagnostic decision — does not change your payoff" : "Provisional decision";
  document.querySelectorAll(".steps li").forEach((el,i)=>{el.classList.toggle("active",i===trial.index);el.setAttribute("aria-current",i===trial.index?"step":"false");});
  $("#documents").replaceChildren();
  trial.documents.forEach(d=>{const item=node("article","",$("#documents")); if(d.status==="superseded") item.className="superseded"; node("p",d.text,item);});
  $("#archives").replaceChildren();
  node("h4","Resolved source reports",$("#archives"));
  table($("#archives"),["Case","Source report (%)","Audited value (%)"],trial.source_archive.map(r=>[r.case_id,r.reported_pct,r.audited_pct]));
  node("h4","Resolved business examples",$("#archives"));
  table($("#archives"),["Underlying growth (%)","Renewal growth (%)","Disruption","Backlog"],trial.analogues.map(r=>[r.underlying_growth_pct,r.renewal_growth_pct,r.rollout_disruption?"Yes":"No",r.backlog_score]));
  $("#assumptions").hidden=!trial.reference_assumptions;$("#model").replaceChildren();
  if(trial.reference_assumptions) for(const [key,value] of Object.entries(trial.reference_assumptions)) node("p",`${key}: ${typeof value === "string" ? value : JSON.stringify(value)}`,$("#model"));
  $("#research").hidden=!trial.options.length;$("#options").replaceChildren();
  trial.options.forEach(o=>{const label=node("label","",$("#options"));label.className="option";const radio=document.createElement("input");Object.assign(radio,{type:"radio",name:"query",value:o.query,required:true});label.append(radio);const text=node("span","",label);node("strong",`${labels[o.query]} · ${o.cost} points`,text);node("span",o.description,text);});
  $("#expectations").hidden=!trial.expectation_queries.length;$("#expectation-inputs").replaceChildren();
  trial.expectation_queries.forEach(q=>{const tr=node("tr","",$("#expectation-inputs"));node("th",labels[q],tr);for(const key of ["yes_probability","growth_if_yes","growth_if_no"]){const input=document.createElement("input");Object.assign(input,{type:"number",min:"0",max:"100",step:"1",required:true,name:`${q}_${key}`});input.setAttribute("aria-label",`${labels[q]}: ${key.replaceAll("_"," ")} in percent`);node("td","",tr).append(input);}});
  $("#history").replaceChildren();
  if(!state.history.length) node("p","No earlier answers yet.",$("#history"));
  state.history.forEach(o=>{const d=node("details","",$("#history"));node("summary",o.trial.stage,d);node("p",`Growth: ${Math.round(o.answer.growth_probability*100)}%; source: ${Math.round(o.answer.audit_understatement_probability*100)}%; backlog: ${Math.round(o.answer.backlog_high_probability*100)}%. Decision: ${o.answer.decision}.`,d);o.trial.documents.forEach(doc=>node("p",doc.text,d));if(o.answer.expectations) for(const [q,e] of Object.entries(o.answer.expectations)) node("p",`${labels[q]} — yes ${Math.round(e.yes_probability*100)}%; growth if yes ${Math.round(e.growth_if_yes*100)}%; growth if no ${Math.round(e.growth_if_no*100)}%.`,d);});
  $("#save").textContent=trial.index===3 ? "Save and finish" : "Save and continue";
}
async function init() {
  $("#next-case").addEventListener("click",async()=>{const button=$("#next-case");button.disabled=true;try{await api("/api/next",{from_assignment:completedCase});await refresh();window.scrollTo({top:0,behavior:"smooth"});}catch(e){failure(e);}finally{button.disabled=false;}});
  $("#begin").addEventListener("click",async()=>{try{if(!$("#consent").checked)throw new Error("Please acknowledge the instructions before starting.");await api("/api/begin",{instructions_accepted:true});$("#error").hidden=true;await refresh();}catch(e){failure(e);}});
  $("#answer").addEventListener("submit",async event=>{
    event.preventDefault();const button=$("#save");button.disabled=true;
    try {
      // Retain the exact request after an uncertain network response. A retry
      // cannot silently change an answer that may already have been accepted.
      pending ||= {trial_id:trial.trial_id,answer:buildAnswer(event.target,trial)};
      await api("/api/answers",pending);$("#error").hidden=true;await refresh();window.scrollTo({top:0,behavior:"smooth"});
    } catch(e) { if(e.status>=400 && e.status<500) pending=null; failure(e); } finally {button.disabled=false;}
  });
  try {const access=new URLSearchParams(location.hash.slice(1)).get("access");if(access){await api("/api/open",{access});history.replaceState(null,"",location.pathname);}await refresh();}catch(e){failure(e);}
}
init();
