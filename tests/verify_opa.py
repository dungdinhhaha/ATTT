"""Verify the running Compose lab and save redacted OPA evidence."""
import json
import subprocess
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import issue_token

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8000"


def decision(subject, owner):
    code = (
        "import httpx,json; "
        "r=httpx.post('http://opa:8181/v1/data/minibank/authz/allow',"
        f"json={{'input':{{'action':'account_read','subject':{subject!r},'owner':{owner!r}}}}}); "
        "r.raise_for_status(); print(json.dumps(r.json()))"
    )
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "minibank", "python", "-c", code],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)["result"]


def main():
    own = decision("alice", "alice")
    other = decision("alice", "bob")
    with httpx.Client(base_url=URL, timeout=5) as client:
        token = issue_token("alice")
        headers = {"Authorization": "Bearer " + token}
        allowed = client.get("/accounts/acc-a", headers=headers)
        denied = client.get("/accounts/acc-b", headers=headers)
        support = client.get("/admin/users", headers={
            "Authorization": "Bearer " + issue_token("sam", "support", "admin:users")})
    evidence = {
        "opa_data_api": {"alice_owns_account": own, "alice_reads_bob_account": other},
        "api_with_opa": {
            "own_account": {"status": allowed.status_code, "request_id": allowed.headers.get("X-Request-ID")},
            "other_account": {"status": denied.status_code, "detail": denied.json().get("detail"), "request_id": denied.headers.get("X-Request-ID")},
            "support_admin_scope_but_wrong_role": {"status": support.status_code, "detail": support.json().get("detail"), "request_id": support.headers.get("X-Request-ID")},
        },
        "note": "Synthetic lab identities. Authorization tokens omitted.",
    }
    assert own is True and other is False
    assert (allowed.status_code, denied.status_code, support.status_code) == (200, 403, 403)
    assert denied.json().get("detail") == "opa_denied"
    assert support.json().get("detail") == "opa_denied"
    path = ROOT / "tests" / "results" / "opa_runtime.json"
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OPA runtime verified: {path}")


if __name__ == "__main__":
    main()
