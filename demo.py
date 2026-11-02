"""Run the isolated API experiment and write reproducible evidence."""
import asyncio
import html
import json
import statistics
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx
from app import create_app, issue_token

ROOT = Path(__file__).parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

REQUESTS = {
    "BOLA support ngoài ticket": "GET /support/accounts/acc-b; actor=sam; scope=support:read",
    "Support có ticket": "GET /support/accounts/acc-a; actor=sam; scope=support:read",
    "BOLA customer": "GET /accounts/acc-b; actor=alice",
    "Customer hợp lệ": "GET /accounts/acc-a; actor=alice",
    "Không có token": "GET /accounts/acc-a; Authorization absent",
    "Sửa hồ sơ hợp lệ": "PATCH /profile/alice; body={phone:000-009}",
    "BFLA support nâng role": "POST /admin/users/sam/role; actor=sam; body={role:admin}",
    "Admin hợp lệ": "POST /admin/users/bob/role; actor=admin; MFA=true",
    "Admin thiếu MFA": "POST /admin/users/bob/role; actor=admin; MFA=false",
    "Admin tự nâng quyền": "POST /admin/users/admin/role; actor=admin; MFA=true",
    "Mass assignment": "PATCH /profile/alice; body={role:admin}",
    "Chuyển từ tài khoản khác": "POST /transfers; actor=alice; source=acc-b; amount=10",
    "Gửi lặp giao dịch": "POST /transfers x5; same Idempotency-Key; amount=10",
    "Gửi song song cùng key": "POST /transfers x20 concurrent; same Idempotency-Key; amount=10",
    "Cùng key khác nội dung": "POST /transfers x2; same key; amount=10 then 20",
    "Chia nhỏ vượt hạn mức": "POST /transfers x4; distinct keys; amount=20 each",
    "Giới hạn đăng nhập": "POST /auth/login x5; synthetic invalid credentials",
    "Đăng nhập dưới ngưỡng": "POST /auth/login x3; synthetic invalid credentials",
    "Giới hạn page size": "GET /transfers?limit=1000000",
    "JWT sai audience": "GET /accounts/acc-a; signed lab JWT aud=other-service",
    "JWT hết hạn": "GET /accounts/acc-a; signed lab JWT exp in past",
    "Agent không được ghi": "POST /transfers; actor=agent; read-only scope",
    "Log có ID, không lộ token": "GET /accounts/acc-b; actor=alice; inspect X-Request-ID and log",
}


def auth(actor, role="customer", scope="accounts:read transfers:create profile:write", **kw):
    return {"Authorization": "Bearer " + issue_token(actor, role, scope, **kw)}


async def one(mode, case):
    app = create_app(mode)
    lab = app.state.lab
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1") as c:
        if case == "BOLA support ngoài ticket":
            r = await c.get("/support/accounts/acc-b", headers=auth("sam", "support", "support:read"))
            safe = r.status_code == 403 and lab.accounts["acc-b"]["balance"] == 100
        elif case == "Support có ticket":
            r = await c.get("/support/accounts/acc-a", headers=auth("sam", "support", "support:read"))
            safe = r.status_code == 200 and r.json().get("balance") == "MASKED"
        elif case == "BOLA customer":
            r = await c.get("/accounts/acc-b", headers=auth("alice"))
            safe = r.status_code == 403
        elif case == "Customer hợp lệ":
            r = await c.get("/accounts/acc-a", headers=auth("alice"))
            safe = r.status_code == 200
        elif case == "Không có token":
            r = await c.get("/accounts/acc-a")
            safe = r.status_code == 401
        elif case == "Sửa hồ sơ hợp lệ":
            r = await c.patch("/profile/alice", json={"phone": "000-009"}, headers=auth("alice"))
            safe = r.status_code == 200 and lab.profiles["alice"]["phone"] == "000-009"
        elif case == "BFLA support nâng role":
            r = await c.post("/admin/users/sam/role", json={"role": "admin"}, headers=auth("sam", "support", "support:read"))
            safe = r.status_code == 403 and lab.profiles["sam"]["role"] == "support"
        elif case == "Admin hợp lệ":
            r = await c.post("/admin/users/bob/role", json={"role": "support"}, headers=auth("admin", "admin", "admin:users", mfa=True))
            safe = r.status_code == 200 and lab.profiles["bob"]["role"] == "support"
        elif case == "Admin thiếu MFA":
            r = await c.post("/admin/users/bob/role", json={"role": "support"}, headers=auth("admin", "admin", "admin:users"))
            safe = r.status_code == 403 and lab.profiles["bob"]["role"] == "customer"
        elif case == "Admin tự nâng quyền":
            r = await c.post("/admin/users/admin/role", json={"role": "support"}, headers=auth("admin", "admin", "admin:users", mfa=True))
            safe = r.status_code == 403 and lab.profiles["admin"]["role"] == "admin"
        elif case == "Mass assignment":
            r = await c.patch("/profile/alice", json={"role": "admin"}, headers=auth("alice"))
            safe = r.status_code == 400 and lab.profiles["alice"]["role"] == "customer"
        elif case == "Chuyển từ tài khoản khác":
            r = await c.post("/transfers", json={"source": "acc-b", "destination": "acc-a", "amount": 10}, headers={**auth("alice"), "Idempotency-Key": "cross"})
            safe = r.status_code == 403 and lab.accounts["acc-b"]["balance"] == 100
        elif case == "Gửi lặp giao dịch":
            responses = [await c.post("/transfers", json={"source": "acc-a", "destination": "acc-b", "amount": 10}, headers={**auth("alice"), "Idempotency-Key": "same"}) for _ in range(5)]
            r = responses[-1]
            safe = len(lab.transfers) == 1 and lab.accounts["acc-a"]["balance"] == 90
        elif case == "Gửi song song cùng key":
            h = {**auth("alice"), "Idempotency-Key": "parallel"}
            payload = {"source": "acc-a", "destination": "acc-b", "amount": 10}
            responses = await asyncio.gather(*[c.post("/transfers", json=payload, headers=h) for _ in range(20)])
            r = responses[-1]
            safe = len(lab.transfers) == 1 and lab.accounts["acc-a"]["balance"] == 90
        elif case == "Cùng key khác nội dung":
            h = {**auth("alice"), "Idempotency-Key": "conflict"}
            await c.post("/transfers", json={"source": "acc-a", "destination": "acc-b", "amount": 10}, headers=h)
            r = await c.post("/transfers", json={"source": "acc-a", "destination": "acc-b", "amount": 20}, headers=h)
            safe = r.status_code == 409 and len(lab.transfers) == 1
        elif case == "Chia nhỏ vượt hạn mức":
            h = auth("alice")
            for i in range(3):
                r = await c.post("/transfers", json={"source": "acc-a", "destination": "acc-b", "amount": 20}, headers={**h, "Idempotency-Key": f"split-{i}"})
            r = await c.post("/transfers", json={"source": "acc-a", "destination": "acc-b", "amount": 20}, headers={**h, "Idempotency-Key": "split-3"})
            safe = r.status_code == 403 and len(lab.transfers) == 3
        elif case == "Giới hạn đăng nhập":
            for _ in range(5): r = await c.post("/auth/login", json={"user": "lab", "password": "fake"})
            safe = r.status_code == 429 and r.headers.get("Retry-After") == "60"
        elif case == "Đăng nhập dưới ngưỡng":
            for _ in range(3): r = await c.post("/auth/login", json={"user": "lab", "password": "fake"})
            safe = r.status_code == 401
        elif case == "Giới hạn page size":
            r = await c.get("/transfers?limit=1000000", headers=auth("alice"))
            safe = r.status_code == 400
        elif case == "JWT sai audience":
            r = await c.get("/accounts/acc-a", headers=auth("alice", aud="other-service"))
            safe = r.status_code == 401
        elif case == "JWT hết hạn":
            r = await c.get("/accounts/acc-a", headers=auth("alice", ttl=-1))
            safe = r.status_code == 401
        elif case == "Agent không được ghi":
            r = await c.post("/transfers", json={"source":"acc-a","destination":"acc-b","amount":10},
                             headers={**auth("agent", "agent", "accounts:read"), "Idempotency-Key":"agent-write"})
            safe = r.status_code == 403 and not lab.transfers
        elif case == "Log có ID, không lộ token":
            token = issue_token("alice")
            r = await c.get("/accounts/acc-b", headers={"Authorization": "Bearer " + token})
            rid = r.headers.get("X-Request-ID")
            safe = bool(rid) and any(x["request_id"] == rid for x in lab.logs) and token not in json.dumps(lab.logs)
        else:
            raise ValueError(case)
        return {"case": case, "request": REQUESTS[case], "status": r.status_code, "safe": safe,
                "request_id": r.headers.get("X-Request-ID"), "response": r.json(),
                "db": {"balances": {k: v["balance"] for k,v in lab.accounts.items()}, "transfer_count": len(lab.transfers),
                       "sam_role": lab.profiles["sam"]["role"]}, "log": lab.logs[-1] if lab.logs else None}


CASES = ["BOLA support ngoài ticket", "Support có ticket", "BOLA customer", "Customer hợp lệ",
         "Không có token", "Sửa hồ sơ hợp lệ", "BFLA support nâng role", "Admin hợp lệ", "Admin thiếu MFA", "Admin tự nâng quyền", "Mass assignment",
         "Chuyển từ tài khoản khác", "Gửi lặp giao dịch", "Gửi song song cùng key", "Cùng key khác nội dung", "Chia nhỏ vượt hạn mức",
         "Giới hạn đăng nhập", "Đăng nhập dưới ngưỡng", "Giới hạn page size", "JWT sai audience", "JWT hết hạn", "Agent không được ghi", "Log có ID, không lộ token"]


async def latency(mode):
    app = create_app(mode)
    timings = []
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1") as c:
        h = auth("alice")
        for _ in range(20): await c.get("/accounts/acc-a", headers=h)
        for _ in range(100):
            start = time.perf_counter()
            await c.get("/accounts/acc-a", headers=h)
            timings.append((time.perf_counter()-start)*1000)
    return {"median_ms": round(statistics.median(timings),3), "p95_ms": round(sorted(timings)[94],3),
            "note": "ASGI trong cùng tiến trình; chỉ minh họa chi phí lab, không suy ra hiệu năng triển khai thật"}


def html_report(data):
    rows=[]
    for b,a in zip(data["before"],data["after"]):
        rows.append(f"<tr><td>{html.escape(a['case'])}</td><td>{b['status']}</td><td>{a['status']}</td><td>{'ĐẠT' if a['safe'] else 'CHƯA ĐẠT'}</td></tr>")
    return """<!doctype html><html lang='vi'><meta charset='utf-8'><title>Demo đề tài 27</title>
<style>body{font:16px system-ui;max-width:1100px;margin:40px auto;color:#142538;background:#f5f8fb;padding:0 24px}h1{color:#123f70}section{background:white;padding:24px;border-radius:14px;margin:18px 0;box-shadow:0 3px 16px #dce5ee}table{border-collapse:collapse;width:100%}th,td{padding:10px;text-align:left;border-bottom:1px solid #dde5ed}th{background:#e5f1fb}.ok{color:#147246;font-weight:700}.warn{color:#a34b00}</style>
<h1>Đề tài 27 · Demo kiểm thử API</h1><p>MiniBank-Lab, dữ liệu và token giả, chạy cục bộ.</p>
<section><h2>Kết quả</h2><p class='ok'>Bản đã sửa: """+str(sum(x["safe"] for x in data["after"]))+"/"+str(len(data["after"]))+" ca đạt điều kiện kiểm tra.</p><p>Hai cột HTTP chỉ là tóm tắt; tệp JSON kèm trạng thái DB và log.</p><table><tr><th>Ca kiểm thử</th><th>HTTP v1</th><th>HTTP v2</th><th>Kết quả v2</th></tr>"+"".join(rows)+"</table></section><section><h2>Độ trễ mẫu</h2><p>p95 v1: "+str(data["latency"]["before"]["p95_ms"])+" ms · p95 v2: "+str(data["latency"]["after"]["p95_ms"])+" ms</p><p class='warn'>Đo trong cùng tiến trình, không dùng để kết luận hiệu năng production.</p></section><section><h2>Chạy lại</h2><p>Trong thư mục dự án: <code>python demo.py</code>. API riêng: <code>docker compose up --build</code>, chỉ mở tại 127.0.0.1:8000.</p></section></html>"


async def main():
    data = {"before": [await one("before", x) for x in CASES],
            "after": [await one("fixed", x) for x in CASES]}
    data["latency"] = {"before": await latency("before"), "after": await latency("fixed")}
    (OUT/"before_after.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT/"demo.html").write_text(html_report(data), encoding="utf-8")
    (OUT/"openapi.json").write_text(json.dumps(create_app("fixed").openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    suite = ET.Element("testsuite", name="MiniBank-Lab", tests=str(len(CASES)),
                       failures=str(sum(not x["safe"] for x in data["after"])))
    for item in data["after"]:
        case = ET.SubElement(suite, "testcase", name=item["case"])
        if not item["safe"]: ET.SubElement(case, "failure", message="Expected control failed")
    ET.ElementTree(suite).write(OUT/"junit.xml", encoding="utf-8", xml_declaration=True)
    lines = ["# Báo cáo thực nghiệm — Đề tài 27", "", "## Phạm vi", "",
             "MiniBank-Lab là API tự viết, dữ liệu và token giả, chạy cục bộ. Hai chế độ v1/v2 dùng cùng mã nguồn và dữ liệu khởi tạo. Không kết nối API thật.", "",
             "## Cơ sở lý thuyết", "",
             "- Xác thực trả lời ai đang gọi; phân quyền chức năng trả lời được gọi route nào; phân quyền đối tượng trả lời được thao tác trên bản ghi nào.",
             "- JWT đã ký chỉ xác nhận nội dung token không bị sửa theo khóa ký. API vẫn phải kiểm issuer, audience, thời hạn, scope và quan hệ của người dùng với tài nguyên.",
             "- BOLA liên quan tới owner hoặc ticket; BFLA liên quan tới chức năng admin; mass assignment xảy ra khi client đặt trường mà server phải tự quyết định.",
             "- Rate limit kiểm soát tần suất; idempotency bảo đảm gửi lại cùng lệnh không nhân đôi giao dịch; kiểm tra hạn mức phải cộng dồn theo luồng nghiệp vụ.", "",
             "## Kết quả từ lần chạy này", "",
             f"Bản v2 đạt **{sum(x['safe'] for x in data['after'])}/{len(CASES)}** ca. Các ca này là mẫu kiểm tra đã triển khai, không phải tuyên bố phủ mọi route hay mọi biến thể tấn công.", "",
             "| Ca kiểm thử | HTTP v1 | HTTP v2 | v2 đạt? |", "|---|---:|---:|---|"]
    lines += [f"| {a['case']} | {b['status']} | {a['status']} | {'Có' if a['safe'] else 'Không'} |" for b,a in zip(data["before"],data["after"])]
    lines += ["", "## Đo độ trễ mẫu", "",
              f"p95 v1: {data['latency']['before']['p95_ms']} ms; p95 v2: {data['latency']['after']['p95_ms']} ms. Mỗi chế độ có 20 request làm nóng và 100 request đo, chạy qua ASGI trong cùng tiến trình.",
              "Số này chỉ mô tả lần chạy trên máy lab; cần tải thật qua HTTP, nhiều lần lặp và phần cứng cố định để kết luận overhead triển khai.", "",
              "## Minh chứng", "",
              "- Mã lab: `app.py`, `compose.yaml`, `Dockerfile`.",
              "- Ma trận quyền: `permission_matrix.csv`.",
              "- Bộ test tự động: `demo.py`; báo cáo máy đọc: `results/junit.xml`.",
              "- Request/response đã bỏ token, trạng thái DB và log từ chối có correlation ID: `results/before_after.json`.",
              "- Đặc tả OpenAPI: `results/openapi.json`.",
              "- Hướng dẫn log và phạm vi đạo đức: `docs/LOGGING.md`, `docs/RULES_OF_ENGAGEMENT.md`.", "",
              "## Giới hạn", "",
              "Lab dùng dữ liệu trong bộ nhớ và issuer JWT giả; chưa tích hợp Keycloak, OPA, crAPI hoặc ZAP. Rate limit chỉ là bộ đếm trong tiến trình. Log chưa được đẩy tới kho append-only. JWT role có thể cũ sau khi đổi quyền; hành động admin đọc role hiện tại từ lab. Các giới hạn này phải được nêu khi bảo vệ, không thay bằng tuyên bố về hệ thống production."]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(f"v2: {sum(x['safe'] for x in data['after'])}/{len(CASES)} ca đạt; p95 v1={data['latency']['before']['p95_ms']}ms, v2={data['latency']['after']['p95_ms']}ms")
    for b,a in zip(data["before"],data["after"]): print(f"{a['case']}: {b['status']} -> {a['status']} | {'ĐẠT' if a['safe'] else 'CHƯA ĐẠT'}")
    if any(not x["safe"] for x in data["after"]): raise SystemExit(1)


if __name__ == "__main__": asyncio.run(main())
