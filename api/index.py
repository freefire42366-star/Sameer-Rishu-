from fastapi import FastAPI, Request
import requests
import hashlib

# Top-level entry point
app = FastAPI()

# --- Full URLs Database (A-Z) ---
U_INFO     = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
U_OTP      = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
U_V_OTP    = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
U_BIND     = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
U_V_ID     = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
U_REBIND   = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
U_UNBIND   = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
U_CANCEL   = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
U_PLAT     = "https://100067.connect.garena.com/bind/app/platform/info/get"
U_LOGOUT   = "https://100067.connect.garena.com/oauth/logout"
U_RANK     = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
U_F_LIST   = "https://clientbp.ggwhitehawk.com/GetFriendRequestList"
U_F_ADD    = "https://clientbp.ggwhitehawk.com/RequestAddingFriend"
U_F_REM    = "https://clientbp.ggwhitehawk.com/RemoveFriend"
U_F_ACC    = "https://clientbp.ggwhitehawk.com/ConfirmFriendRequest"
U_F_DEC    = "https://clientbp.ggwhitehawk.com/DeclineFriendRequest"
U_TOPUP    = "https://100067.msdk.garena.com/api/msdk/v2/info/pricing"

AID = "100067"
RTK = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

def gh(r: Request):
    ua = r.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded", "Accept-Encoding": "gzip"}

def hs(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
async def status():
    return {"status": "SUCCESS", "msg": "API Working from api/ folder"}

@app.get("/api/request")
async def req_otp(token: str, email: str, request: Request):
    p = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    r = requests.post(U_OTP, data=p, headers=gh(request))
    return r.json()

@app.get("/api/confirm-new")
async def bind_new(token: str, email: str, otp: str, sc: str = "123456", request: Request):
    h = gh(request)
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v.get("verifier_token")
    if not vt: return {"status": "ERROR", "res": v}
    p = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": hs(sc)}
    r = requests.post(U_BIND, data=p, headers=h)
    return r.json()

@app.get("/api/rebind")
async def bind_change(token: str, email: str, otp: str, sc: str, request: Request):
    h = gh(request)
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v.get("verifier_token")
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not vt or not it: return {"status": "FAIL", "vt": v, "it": i}
    p = {"app_id": AID, "access_token": token, "identity_token": it, "verifier_token": vt, "email": email}
    r = requests.post(U_REBIND, data=p, headers=h)
    return r.json()

@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    h = gh(request)
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not it: return i
    r = requests.post(U_UNBIND, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=h)
    return r.json()

@app.get("/api/friends")
async def friends(token: str, mode: str, target: str = None, request: Request):
    h = gh(request)
    m_map = {"list": U_F_LIST, "add": U_F_ADD, "remove": U_F_REM, "accept": U_F_ACC, "decline": U_F_DEC}
    url = m_map.get(mode)
    p = {"access_token": token}
    if target: p["target_account_id"] = target
    return requests.get(url, params=p, headers=h).json()

@app.get("/api/info")
async def info(token: str, request: Request):
    h = gh(request)
    b = requests.get(U_INFO, params={"app_id": AID, "access_token": token}, headers=h).json()
    r = requests.get(U_RANK, params={"access_token": token}, headers=h).json()
    return {"bind": b, "rank": r}

@app.get("/api/utils")
async def utils(token: str, type: str, request: Request):
    h = gh(request)
    if type == "plat": return requests.get(U_PLAT, params={"access_token": token}, headers=h).json()
    if type == "topup": return requests.get(U_TOPUP, params={"access_token": token}, headers=h).json()
    if type == "cancel": return requests.post(U_CANCEL, data={"app_id": AID, "access_token": token}, headers=h).json()
    return {"err": "Invalid"}

@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    r = requests.get(U_10, params={"access_token": token, "refresh_token": RTK}, headers=gh(request))
    return {"res": r.text}
