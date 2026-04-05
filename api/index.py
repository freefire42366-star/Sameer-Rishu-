import requests
import hashlib
from fastapi import FastAPI, Request

# Vercel ko ye line sabse pehle chahiye
app = FastAPI()

# --- Full URLs Database ---
B_INFO = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
S_OTP = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
V_OTP = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
B_REQ = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
V_ID = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
RB_REQ = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
UB_REQ = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
C_REQ = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
PLAT = "https://100067.connect.garena.com/bind/app/platform/info/get"
LOGO = "https://100067.connect.garena.com/oauth/logout"
RANK = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
F_LST = "https://clientbp.ggwhitehawk.com/GetFriendRequestList"
F_ADD = "https://clientbp.ggwhitehawk.com/RequestAddingFriend"
F_REM = "https://clientbp.ggwhitehawk.com/RemoveFriend"
F_ACC = "https://clientbp.ggwhitehawk.com/ConfirmFriendRequest"
F_DEC = "https://clientbp.ggwhitehawk.com/DeclineFriendRequest"
PRIC = "https://100067.msdk.garena.com/api/msdk/v2/info/pricing"

AID = "100067"
RTK = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

def get_h(r: Request):
    ua = r.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded", "Accept-Encoding": "gzip"}

def hs(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
async def root():
    return {"status": "SUCCESS", "msg": "SAMEER-API-V10-LIVE"}

@app.get("/api/request")
async def req_otp(token: str, email: str, request: Request):
    d = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    r = requests.post(S_OTP, data=d, headers=get_h(request))
    return r.json()

@app.get("/api/confirm-new")
async def bind_new(token: str, email: str, otp: str, sc: str = "123456", request: Request):
    hdr = get_h(request)
    v = requests.post(V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=hdr).json()
    vt = v.get("verifier_token")
    if not vt: return {"status": "ERROR", "res": v}
    d = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": hs(sc)}
    r = requests.post(B_REQ, data=d, headers=hdr)
    return r.json()

@app.get("/api/rebind")
async def rebind(token: str, email: str, otp: str, sc: str, request: Request):
    hdr = get_h(request)
    v = requests.post(V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=hdr).json()
    vt = v.get("verifier_token")
    i = requests.post(V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=hdr).json()
    it = i.get("identity_token")
    if not vt or not it: return {"status": "ERROR", "vt": v, "it": i}
    d = {"app_id": AID, "access_token": token, "identity_token": it, "verifier_token": vt, "email": email}
    r = requests.post(RB_REQ, data=d, headers=hdr)
    return r.json()

@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    hdr = get_h(request)
    i = requests.post(V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=hdr).json()
    it = i.get("identity_token")
    if not it: return i
    r = requests.post(UB_REQ, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=hdr)
    return r.json()

@app.get("/api/info")
async def info(token: str, request: Request):
    hdr = get_h(request)
    b = requests.get(B_INFO, params={"app_id": AID, "access_token": token}, headers=hdr).json()
    r = requests.get(RANK, params={"access_token": token}, headers=hdr).json()
    return {"account": r, "bind": b}

@app.get("/api/friends")
async def friends(token: str, mode: str, target: str = None, request: Request):
    hdr = get_h(request)
    m_map = {"list": F_LST, "add": F_ADD, "remove": F_REM, "accept": F_ACC, "decline": F_DEC}
    url = m_map.get(mode)
    if not url: return {"err": "Invalid Mode"}
    p = {"access_token": token}
    if target: p["target_account_id"] = target
    r = requests.get(url, params=p, headers=hdr)
    return r.json()

@app.get("/api/utils")
async def utils(token: str, type: str, request: Request):
    hdr = get_h(request)
    if type == "plat": return requests.get(PLAT, params={"access_token": token}, headers=hdr).json()
    if type == "topup": return requests.get(PRIC, params={"access_token": token}, headers=hdr).json()
    if type == "cancel": return requests.post(C_REQ, data={"app_id": AID, "access_token": token}, headers=hdr).json()
    return {"err": "Invalid Type"}

@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    r = requests.get(LOGO, params={"access_token": token, "refresh_token": RTK}, headers=get_h(request))
    return {"res": r.text}

@app.get("/api/convert")
async def conv(eat: str):
    return {"url": f"https://api-otrss.garena.com/support/callback/?access_token={eat}"}
