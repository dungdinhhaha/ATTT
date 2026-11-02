"""MiniBank API lab. All identities, balances, and tokens are synthetic."""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from collections import defaultdict

import httpx

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

SECRET = b"minibank-lab-only-fixed-demo-key"
ISSUER = "minibank-lab"
AUDIENCE = "minibank-api"


def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def issue_token(actor, role="customer", scope="accounts:read transfers:create profile:write", aud=AUDIENCE, ttl=300, mfa=False):
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _b64(json.dumps({"iss": ISSUER, "aud": aud, "sub": actor, "role": role,
                               "scope": scope, "mfa": mfa, "exp": int(time.time()) + ttl}, separators=(",", ":")).encode())
    body = header + "." + payload
    sig = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
    return body + "." + sig


def decode_token(token, fixed):
    try:
        h, p, sig = token.split(".")
        header = json.loads(_unb64(h))
        claims = json.loads(_unb64(p))
        if fixed:
            if header.get("alg") != "HS256": raise ValueError("algorithm")
            expected = _b64(hmac.new(SECRET, (h + "." + p).encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(sig, expected): raise ValueError("signature")
            if claims.get("iss") != ISSUER or claims.get("aud") != AUDIENCE: raise ValueError("issuer_or_audience")
            if int(claims.get("exp", 0)) <= time.time(): raise ValueError("expired")
        return claims
    except Exception as exc:
        raise HTTPException(401, "invalid_token") from exc


class ProfilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=20)


class TransferIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    destination: str
    amount: int = Field(gt=0, le=100)


class RoleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str


class Lab:
    def __init__(self):
        self.accounts = {"acc-a": {"owner": "alice", "balance": 100},
                         "acc-b": {"owner": "bob", "balance": 100}}
        self.profiles = {"alice": {"full_name": "Alice Lab", "phone": "000-001", "role": "customer"},
                         "bob": {"full_name": "Bob Lab", "phone": "000-002", "role": "customer"},
                         "sam": {"full_name": "Sam Support", "phone": "000-003", "role": "support"},
                         "admin": {"full_name": "Admin Lab", "phone": "000-004", "role": "admin"}}
        self.tickets = {("sam", "alice")}
        self.transfers = []
        self.idempotency = {}
        self.login_hits = defaultdict(int)
        self.logs = []
        self.lock = asyncio.Lock()


def create_app(mode="fixed"):
    fixed = mode == "fixed"
    app = FastAPI(title="MiniBank Lab", version="1.0", docs_url=None, redoc_url=None)
    lab = Lab()
    app.state.lab = lab

    @app.middleware("http")
    async def audit(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse({"detail": "internal_error"}, status_code=500)
        response.headers["X-Request-ID"] = rid
        route = request.scope.get("route")
        lab.logs.append({"request_id": rid, "subject": getattr(request.state, "subject", "anonymous"),
                         "method": request.method, "route": getattr(route, "path", request.url.path),
                         "decision": "deny" if response.status_code >= 400 else "allow",
                         "policy_id": getattr(request.state, "policy_id", "P-DEFAULT"),
                         "status": response.status_code,
                         "duration_ms": round((time.perf_counter()-start)*1000, 3)})
        return response

    def actor(request: Request, scope=None):
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "): raise HTTPException(401, "missing_token")
        claims = decode_token(authorization[7:], fixed)
        sub = claims.get("sub")
        if sub not in lab.profiles and sub != "agent": raise HTTPException(401, "unknown_subject")
        request.state.subject = sub
        if fixed and scope and scope not in claims.get("scope", "").split():
            raise HTTPException(403, "missing_scope")
        return claims

    async def opa_check(request: Request, action: str, claims: dict, **facts):
        """Optional OPA sidecar. Missing/error decisions deny when OPA is enabled."""
        if not fixed or not os.getenv("OPA_URL"):
            return
        request.state.policy_id = "OPA:" + action
        payload = {"input": {"action": action, "subject": claims["sub"],
                             "role": claims.get("role"), "mfa": bool(claims.get("mfa")), **facts}}
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.post(os.environ["OPA_URL"], json=payload)
                response.raise_for_status()
                allowed = response.json().get("result") is True
        except (httpx.HTTPError, ValueError, KeyError):
            allowed = False
        if not allowed:
            raise HTTPException(403, "opa_denied")

    @app.get("/accounts/{account_id}")
    async def get_account(account_id: str, request: Request):
        c = actor(request, "accounts:read")
        request.state.policy_id = "P02"
        a = lab.accounts.get(account_id)
        if not a: raise HTTPException(404, "not_found")
        await opa_check(request, "account_read", c, owner=a["owner"])
        if fixed and a["owner"] != c["sub"]: raise HTTPException(403, "forbidden")
        return {"id": account_id, "balance": a["balance"], "owner": a["owner"]}

    @app.get("/support/accounts/{account_id}")
    async def support_account(account_id: str, request: Request):
        c = actor(request, "support:read")
        request.state.policy_id = "P08/P14"
        a = lab.accounts.get(account_id)
        if not a: raise HTTPException(404, "not_found")
        await opa_check(request, "support_read", c, ticket=(c["sub"], a["owner"]) in lab.tickets)
        if fixed and (c.get("role") != "support" or (c["sub"], a["owner"]) not in lab.tickets):
            raise HTTPException(403, "ticket_required")
        if fixed: return {"id": account_id, "owner": a["owner"], "balance": "MASKED"}
        return {"id": account_id, **a}

    @app.patch("/profile/{user_id}")
    async def patch_profile(user_id: str, request: Request):
        c = actor(request, "profile:write")
        request.state.policy_id = "P06"
        if user_id not in lab.profiles: raise HTTPException(404, "not_found")
        await opa_check(request, "profile_write", c, target=user_id)
        if fixed and c["sub"] != user_id: raise HTTPException(403, "forbidden")
        data = await request.json()
        if fixed:
            try: data = ProfilePatch.model_validate(data).model_dump(exclude_none=True)
            except Exception as exc: raise HTTPException(400, "invalid_fields") from exc
        lab.profiles[user_id].update(data)
        return lab.profiles[user_id]

    @app.get("/admin/users")
    async def list_users(request: Request):
        c = actor(request, "admin:users")
        request.state.policy_id = "P07"
        await opa_check(request, "admin_list", c)
        if fixed and c.get("role") != "admin": raise HTTPException(403, "forbidden")
        return sorted(lab.profiles)

    @app.post("/admin/users/{user_id}/role")
    async def set_role(user_id: str, request: Request):
        c = actor(request, "admin:users")
        request.state.policy_id = "P10/P15/P17"
        if user_id not in lab.profiles: raise HTTPException(404, "not_found")
        await opa_check(request, "admin_role_write", c, target=user_id)
        if fixed:
            if lab.profiles[c["sub"]]["role"] != "admin" or c["sub"] == user_id or not c.get("mfa"):
                raise HTTPException(403, "forbidden")
            try: data = RoleIn.model_validate(await request.json())
            except Exception as exc: raise HTTPException(400, "invalid_fields") from exc
            role = data.role
        else:
            role = (await request.json()).get("role")
        if role not in {"customer", "support", "admin"}: raise HTTPException(400, "invalid_role")
        lab.profiles[user_id]["role"] = role
        return {"user_id": user_id, "role": role}

    @app.post("/transfers")
    async def transfer(request: Request, idempotency_key: str | None = Header(default=None)):
        c = actor(request, "transfers:create")
        request.state.policy_id = "P04/P05"
        raw = await request.json()
        if fixed:
            try: data = TransferIn.model_validate(raw).model_dump()
            except Exception as exc: raise HTTPException(400, "invalid_fields") from exc
            if not idempotency_key: raise HTTPException(400, "idempotency_key_required")
        else:
            data = raw
        source = lab.accounts.get(data.get("source"))
        dest = lab.accounts.get(data.get("destination"))
        amount = data.get("amount", 0)
        if not source or not dest or not isinstance(amount, int) or amount <= 0:
            raise HTTPException(400, "invalid_transfer")
        await opa_check(request, "transfer_create", c, owner=source["owner"])
        if fixed and source["owner"] != c["sub"]: raise HTTPException(403, "source_not_owned")
        if fixed and amount >= 50: raise HTTPException(403, "step_up_required")
        if not fixed and amount >= 50 and raw.get("require_step_up", True):
            raise HTTPException(403, "step_up_required")
        fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        async with lab.lock:
            key = (c["sub"], idempotency_key)
            if fixed and key in lab.idempotency:
                old_hash, old_result = lab.idempotency[key]
                if old_hash != fingerprint: raise HTTPException(409, "key_reused_with_different_body")
                return old_result
            if fixed and sum(x["amount"] for x in lab.transfers if x["source"] == data["source"]) + amount > 70:
                raise HTTPException(403, "daily_limit")
            if source["balance"] < amount: raise HTTPException(400, "insufficient_funds")
            source["balance"] -= amount
            dest["balance"] += amount
            result = {"id": "tr-" + str(len(lab.transfers)+1), "source": data["source"],
                      "destination": data["destination"], "amount": amount}
            lab.transfers.append(result)
            if fixed: lab.idempotency[key] = (fingerprint, result)
            return result

    @app.post("/auth/login")
    async def login(request: Request):
        request.state.policy_id = "P-RATE"
        lab.login_hits["local-lab"] += 1
        if fixed and lab.login_hits["local-lab"] > 3:
            return JSONResponse({"detail": "rate_limited"}, status_code=429, headers={"Retry-After": "60"})
        raise HTTPException(401, "invalid_credentials")

    @app.get("/transfers")
    async def list_transfers(request: Request, limit: int = 20):
        c = actor(request, "accounts:read")
        request.state.policy_id = "P-LIMIT"
        if fixed and (limit < 1 or limit > 100): raise HTTPException(400, "invalid_limit")
        return [t for t in lab.transfers if not fixed or lab.accounts[t["source"]]["owner"] == c["sub"]][:limit]

    return app


app = create_app(os.getenv("LAB_MODE", "fixed"))
