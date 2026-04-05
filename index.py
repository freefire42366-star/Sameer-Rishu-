import requests
import hashlib
from fastapi import FastAPI, Request, Query

app = FastAPI()

# --- FULL URL DATABASE (A to Z) ---
U_BIND_INFO = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
U_SEND_OTP  = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
U_VERIFY_OTP = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
U_BIND_NEW  = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
U_VERIFY_ID = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
U_REBIND    = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
U_UNBIND    = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
U_CANCEL    = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
U_PLATFORM  = "https://100067.connect.garena.com/bind/app/platform/info/get"
U_LOGOUT    = "https://100067.connect.garena.com/oauth/logout"
U_RANK      = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
U_F_LIST    = "https://clientbp.ggwhitehawk.com/GetFriendRequestList"
U_F_ADD     = "https://clientbp.ggwhitehawk.com/RequestAddingFriend"
U_F_REM     = "https://clientbp.ggwhitehawk.com/RemoveFriend"
U_F_ACC     = "https://clientbp.ggwhitehawk.com/ConfirmFriendRequest"
U_F_DEC     = "https://clientbp.ggwhitehawk.com/DeclineFriendRequest"
U_TOPUP     = "https://100067.msdk.garena.com/api/msdk/v2/info/pricing"

AID = "100067"
REF = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

def gh(r: Request):
    ua = r.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded", "Accept-Encoding": "gzip"}

def hash_pw(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
async def home():
    return {"status": "SUCCESS", "engine": "Sameer-V11-Pro", "folder": "api/"}

# --- 1. SEND OTP ---
@app.get("/api/send-otp")
async def send_otp(token: str, email: str, request: Request):
    p = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    r = requests.post(U_SEND_OTP, data=p, headers=gh(request))
    return r.json()

# --- 2. BIND NEW EMAIL (Fresh Account) ---
@app.get("/api/confirm-fresh")
async def confirm_fresh(token: str, email: str, otp: str, sc: str = "123456", request: Request):
    h = gh(request)
    v_res = requests.post(U_VERIFY_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v_res.get("verifier_token")
    if not vt: return {"status": "ERROR", "msg": "Invalid OTP", "garena": v_res}
    p = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": hash_pw(sc)}
    r = requests.post(U_BIND_NEW, data=p, headers=h)
    return r.json()

# --- 3. REBIND EMAIL (Change Email) ---
@app.get("/api/rebind")
async def rebind_email(token: str, email: str, otp: str, sc: str, request: Request):
    h = gh(request)
    v = requests.post(U_VERIFY_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v.get("verifier_token")
    i = requests.post(U_VERIFY_ID, data={"app_id": AID, "access_token": token, "secondary_password": hash_pw(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not vt or not it: return {"status": "AUTH_FAILED", "verify_otp": v, "verify_id": i}
    p = {"app_id": AID, "access_token": token, "identity_token": it, "verifier_token": vt, "email": email}
    r = requests.post(U_REBIND, data=p, headers=h)
    return r.json()

# --- 4. UNBIND (Remove Email) ---
@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    h = gh(request)
    i = requests.post(U_VERIFY_ID, data={"app_id": AID, "access_token": token, "secondary_password": hash_pw(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not it: return {"status": "ERROR", "id_res": i}
    r = requests.post(U_UNBIND, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=h)
    return r.json()

# --- 5. ACCOUNT & BIND INFO ---
@app.get("/api/info")
async def account_info(token: str, request: Request):
    h = gh(request)
    bind = requests.get(U_BIND_INFO, params={"app_id": AID, "access_token": token}, headers=h).json()
    rank = requests.get(U_RANK, params={"access_token": token}, headers=h).json()
    return {"bind_info": bind, "rank_info": rank}

# --- 6. FRIENDS SYSTEM ---
@app.get("/api/friends")
async def friends_manager(token: str, mode: str, target: str = None, request: Request):
    h = gh(request)
    m_map = {"list": U_F_LIST, "add": U_F_ADD, "remove": U_F_REM, "accept": U_F_ACC, "decline": U_F_DEC}
    url = m_map.get(mode)
    p = {"access_token": token}
    if target: p["target_account_id"] = target
    r = requests.get(url, params=p, headers=h)
    return r.json()

# --- 7. UTILS (Platform, Topup, Cancel) ---
@app.get("/api/utils")
async def utils_manager(token: str, type: str, request: Request):
    h = gh(request)
    if type == "platforms": return requests.get(U_PLATFORM, params={"access_token": token}, headers=h).json()
    if type == "topup": return requests.get(U_TOPUP, params={"access_token": token}, headers=h).json()
    if type == "cancel": return requests.post(U_CANCEL, data={"app_id": AID, "access_token": token}, headers=h).json()
    return {"error": "Invalid Type"}

# --- 8. LOGOUT & EAT CONVERTER ---
@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    r = requests.get(U_LOGOUT, params={"access_token": token, "refresh_token": REF}, headers=gh(request))
    return {"status": "Revoked", "raw": r.text}

@app.get("/api/convert")
async def converter(eat: str):
    return {"eat_token": eat, "access_token_url": f"https://api-otrss.garena.com/support/callback/?access_token={eat}"}
