import json
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path

from test_investigation3 import PARTICIPANT
from test_live_web import BrowserClient

from epistemics.investigation3.models import Trial
from epistemics.investigation3.service import InvestigationService, create
from epistemics.investigation3.simulation import response
from epistemics.investigation3.web import LocalServer


@contextmanager
def running(tmp_path, *, collection=False):
    directory = tmp_path / "browser"
    manifest = create(directory, PARTICIPANT, seed=219, synthetic=True)
    a = (
        manifest.assignments[0]
        if collection
        else next(a for a in manifest.assignments if a.family == "research")
    )
    service = InvestigationService(directory, a.assignment_id)
    server = LocalServer(0, service, collection=collection)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_browser_capability_same_service_retry_and_no_operator_routes(tmp_path):
    with running(tmp_path) as (base, server):
        client = BrowserClient(base)
        assert client.request("/api/state")[0] == 403
        assert client.request("/api/open", {"access": "wrong"})[0] == 403
        assert client.json("/api/open", {"access": server.access}) == {"opened": True}
        state = client.json("/api/state")
        assert state["synthetic"] and not state["started"] and state["current"] is None
        assert client.request("/api/begin", {"instructions_accepted": False})[0] == 400
        client.json("/api/begin", {"instructions_accepted": True})
        for _ in range(4):
            state = client.json("/api/state")
            t = Trial.model_validate(state["current"]["trial"])
            body = {"trial_id": t.trial_id, "answer": response(t).model_dump()}
            receipt = client.json("/api/answers", body)
            assert receipt == client.json("/api/answers", body)
            # Browser and MCP are thin views of the identical accepted state.
            assert server.service.get_history()["history"][-1]["receipt"] == receipt
        assert client.json("/api/finish", {})["report_stored"]
        visible = json.dumps(client.json("/api/state"))
        for key in ('"truth"', '"seed"', '"private_world"', '"focused_query"'):
            assert key not in visible
        for route in (
            "/manifest.json",
            "/responses.sqlite3",
            "/download/report.json",
            "/api/export",
            "/../service.py",
        ):
            assert client.request(route)[0] == 404
        assert BrowserClient(base).request("/api/state")[0] == 403
        assert client.request("/api/state", headers={"Host": "attacker.example"})[0] == 403
        assert (
            client.request("/api/finish", {}, headers={"Origin": "https://attacker.example"})[0]
            == 403
        )
        assert client.request("/api/finish", {}, headers={"X-Epistemics-Request": "0"})[0] == 403
        assert client.request("/api/begin", [])[0] == 400
        code, headers, body = client.request("/")
        assert code == 200 and b"Company investigation" in body
        assert "frame-ancestors" in headers["Content-Security-Policy"]
        assert headers["Cache-Control"] == "no-store"


def test_browser_probability_contract_blank_endpoints_and_prospective_answers():
    result = subprocess.run(
        [
            "node",
            "--input-type=commonjs",
            "-e",
            r"""
const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const source=fs.readFileSync("src/epistemics/investigation3/assets/app.js","utf8").replace(/init\(\);\s*$/,"");
const context=vm.createContext({});vm.runInContext(source,context);
context.values={growth_probability:"64",audit_understatement_probability:"0",backlog_high_probability:"100",decision:"invest",query:"source_audit",explanation:""};
context.form={elements:{namedItem:n=>({value:context.values[n]})}};
context.t={options:[{query:"source_audit"}],expectation_queries:["source_audit","operations_check","segment_check"]};
for(const q of context.t.expectation_queries) for(const k of ["yes_probability","growth_if_yes","growth_if_no"])context.values[q+"_"+k]="25";
const answer=JSON.parse(vm.runInContext("JSON.stringify(buildAnswer(form,t))",context));
assert.equal(answer.growth_probability,.64);assert.equal(answer.audit_understatement_probability,0);assert.equal(answer.backlog_high_probability,1);
assert.deepEqual(answer.expectations.segment_check,{yes_probability:.25,growth_if_yes:.25,growth_if_no:.25});
for(const value of [""," ","0.5","NaN","Infinity","-1","101"]){context.values.growth_probability=value;assert.throws(()=>vm.runInContext("buildAnswer(form,t)",context));}
""",
        ],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_whole_human_battery_next_case_retries_never_skip(tmp_path):
    with running(tmp_path, collection=True) as (base, server):
        client = BrowserClient(base)
        client.json("/api/open", {"access": server.access})
        client.json("/api/begin", {"instructions_accepted": True})
        assert server.service.manifest.context_policy == "human_continuous_separate_company_cases"
        for case in range(12):
            state = client.json("/api/state")
            assert state["case_number"] == case + 1 and state["case_count"] == 12
            assert state["history"] == []
            case_id = state["assignment_id"]
            assert client.request("/api/next", {"from_assignment": case_id})[0] == 400
            for _ in range(4):
                state = client.json("/api/state")
                t = Trial.model_validate(state["current"]["trial"])
                client.json(
                    "/api/answers", {"trial_id": t.trial_id, "answer": response(t).model_dump()}
                )
            client.json("/api/finish", {"assignment_id": case_id})
            advanced = client.json("/api/next", {"from_assignment": case_id})
            assert advanced == client.json("/api/next", {"from_assignment": case_id})
        from epistemics.investigation3.service import status

        assert status(server.service.directory)["completed"] == 12
        assert client.json("/api/state")["current"]["complete"]
