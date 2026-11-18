"""Same-origin UI so Burp sees real MiniBank API requests."""
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import HTMLResponse

TEMPLATE = Path(__file__).with_name("demo_page.html").read_text(encoding="utf-8")


def install_demo_ui(app, issue_token, mode: str):
    @app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
    async def demo_page():
        title = "TRƯỚC KHI SỬA" if mode == "before" else "SAU KHI SỬA"
        return HTMLResponse(TEMPLATE.replace("{{MODE}}", title))

    @app.post("/demo/token/{actor}", include_in_schema=False)
    async def demo_token(actor: str):
        users = {
            "alice": ("customer", "accounts:read transfers:create profile:write", False),
            "sam": ("support", "support:read admin:users", False),
            "admin": ("admin", "admin:users", True),
        }
        if actor not in users:
            raise HTTPException(400, "unknown_demo_actor")
        role, scope, mfa = users[actor]
        return {"access_token": issue_token(actor, role, scope, mfa=mfa), "role": role}
