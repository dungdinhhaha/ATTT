"""Vulnerable MiniBank API for isolated lab demonstrations."""
import asyncio
import base64
import hashlib
import hmac
import json
import time
import uuid
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
SECRET = b'minibank-lab-only-fixed-demo-key'
ISSUER = 'minibank-lab'
AUDIENCE = 'minibank-api'

def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _unb64(data):
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))

def issue_token(actor, role='customer', scope='accounts:read transfers:create profile:write', aud=AUDIENCE, ttl=300, mfa=False):
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _b64(json.dumps({'iss': ISSUER, 'aud': aud, 'sub': actor, 'role': role, 'scope': scope, 'mfa': mfa, 'exp': int(time.time()) + ttl}, separators=(',', ':')).encode())
    body = header + '.' + payload
    sig = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
    return body + '.' + sig

def decode_token(token):
    try:
        h, p, sig = token.split('.')
        header = json.loads(_unb64(h))
        claims = json.loads(_unb64(p))
        return claims
    except Exception as exc:
        raise HTTPException(401, 'invalid_token') from exc

class Lab:

    def __init__(self):
        self.accounts = {'acc-a': {'owner': 'alice', 'balance': 100}, 'acc-b': {'owner': 'bob', 'balance': 100}}
        self.profiles = {'alice': {'full_name': 'Alice Lab', 'phone': '000-001', 'role': 'customer'}, 'bob': {'full_name': 'Bob Lab', 'phone': '000-002', 'role': 'customer'}, 'sam': {'full_name': 'Sam Support', 'phone': '000-003', 'role': 'support'}, 'admin': {'full_name': 'Admin Lab', 'phone': '000-004', 'role': 'admin'}}
        self.tickets = {('sam', 'alice')}
        self.transfers = []
        self.idempotency = {}
        self.logs = []
        self.lock = asyncio.Lock()

def create_app():
    app = FastAPI(title='MiniBank Lab', version='1.0', docs_url=None, redoc_url=None)
    lab = Lab()
    app.state.lab = lab

    @app.middleware('http')
    async def audit(request: Request, call_next):
        rid = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse({'detail': 'internal_error'}, status_code=500)
        response.headers['X-Request-ID'] = rid
        route = request.scope.get('route')
        lab.logs.append({'request_id': rid, 'subject': getattr(request.state, 'subject', 'anonymous'), 'method': request.method, 'route': getattr(route, 'path', request.url.path), 'decision': 'deny' if response.status_code >= 400 else 'allow', 'policy_id': getattr(request.state, 'policy_id', 'P-DEFAULT'), 'status': response.status_code, 'duration_ms': round((time.perf_counter() - start) * 1000, 3)})
        return response

    def actor(request: Request, scope=None):
        authorization = request.headers.get('authorization', '')
        if not authorization.startswith('Bearer '):
            raise HTTPException(401, 'missing_token')
        claims = decode_token(authorization[7:])
        sub = claims.get('sub')
        if sub not in lab.profiles and sub != 'agent':
            raise HTTPException(401, 'unknown_subject')
        request.state.subject = sub
        return claims

    @app.get('/accounts/{account_id}')
    async def get_account(account_id: str, request: Request):
        c = actor(request, 'accounts:read')
        request.state.policy_id = 'P02'
        a = lab.accounts.get(account_id)
        if not a:
            raise HTTPException(404, 'not_found')
        return {'id': account_id, 'balance': a['balance'], 'owner': a['owner']}

    @app.get('/support/accounts/{account_id}')
    async def support_account(account_id: str, request: Request):
        c = actor(request, 'support:read')
        request.state.policy_id = 'P08/P14'
        a = lab.accounts.get(account_id)
        if not a:
            raise HTTPException(404, 'not_found')
        return {'id': account_id, **a}

    @app.patch('/profile/{user_id}')
    async def patch_profile(user_id: str, request: Request):
        c = actor(request, 'profile:write')
        request.state.policy_id = 'P06'
        if user_id not in lab.profiles:
            raise HTTPException(404, 'not_found')
        data = await request.json()
        lab.profiles[user_id].update(data)
        return lab.profiles[user_id]

    @app.get('/admin/users')
    async def list_users(request: Request):
        c = actor(request, 'admin:users')
        request.state.policy_id = 'P07'
        return sorted(lab.profiles)

    @app.post('/admin/users/{user_id}/role')
    async def set_role(user_id: str, request: Request):
        c = actor(request, 'admin:users')
        request.state.policy_id = 'P10/P15/P17'
        if user_id not in lab.profiles:
            raise HTTPException(404, 'not_found')
        role = (await request.json()).get('role')
        if role not in {'customer', 'support', 'admin'}:
            raise HTTPException(400, 'invalid_role')
        lab.profiles[user_id]['role'] = role
        return {'user_id': user_id, 'role': role}

    @app.post('/transfers')
    async def transfer(request: Request, idempotency_key: str | None=Header(default=None)):
        c = actor(request, 'transfers:create')
        request.state.policy_id = 'P04/P05'
        raw = await request.json()
        data = raw
        source = lab.accounts.get(data.get('source'))
        dest = lab.accounts.get(data.get('destination'))
        amount = data.get('amount', 0)
        if not source or not dest or (not isinstance(amount, int)) or (amount <= 0):
            raise HTTPException(400, 'invalid_transfer')
        if amount >= 50 and raw.get('require_step_up', True):
            raise HTTPException(403, 'step_up_required')
        async with lab.lock:
            if source['balance'] < amount:
                raise HTTPException(400, 'insufficient_funds')
            source['balance'] -= amount
            dest['balance'] += amount
            result = {'id': 'tr-' + str(len(lab.transfers) + 1), 'source': data['source'], 'destination': data['destination'], 'amount': amount}
            lab.transfers.append(result)
            return result

    @app.post('/auth/login')
    async def login(request: Request):
        request.state.policy_id = 'P-RATE'
        raise HTTPException(401, 'invalid_credentials')

    @app.get('/transfers')
    async def list_transfers(request: Request, limit: int=20):
        c = actor(request, 'accounts:read')
        request.state.policy_id = 'P-LIMIT'
        return lab.transfers[:limit]
    return app
app = create_app()
