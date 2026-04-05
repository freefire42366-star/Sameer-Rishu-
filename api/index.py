from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

# --- Configuration ---
AID = "100067"
RTK = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

# --- URLs ---
U_OTP      = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
U_V_OTP    = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
U_BIND     = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
U_V_ID     = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
U_REBIND   = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
U_UNBIND   = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
U_CANCEL   = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
U_INFO     = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
U_PLAT     = "https://100067.connect.garena.com/bind/app/platform/info/get"
U_RANK     = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
U_LOGOUT   = "https://100067.connect.garena.com/oauth/logout"

F_MAP = {
    "list": "https://clientbp.ggwhitehawk.com/GetFriendRequestList",
    "add": "https://clientbp.ggwhitehawk.com/RequestAddingFriend",
    "remove": "https://clientbp.ggwhitehawk.com/RemoveFriend",
    "accept": "https://clientbp.ggwhitehawk.com/ConfirmFriendRequest",
    "decline": "https://clientbp.ggwhitehawk.com/DeclineFriendRequest"
}

def gh(r: Request):
    ua = r.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded"}

def hs(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
async def home():
    return {"status": "ONLINE", "msg": "API is working"}

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
    return requests.post(U_BIND, data=p, headers=h).json()

@app.get("/api/rebind")
async def bind_change(token: str, email: str, otp: str, sc: str, request: Request):
    h = gh(request)
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    vt, it = v.get("verifier_token"), i.get("identity_token")
    if not vt or not it: return {"status": "FAIL", "vt": v, "it": i}
    p = {"app_id": AID, "access_token": token, "identity_token": it, "verifier_token": vt, "email": email}
    return requests.post(U_REBIND, data=p, headers=h).json()

@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    h = gh(request)
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not it: return {"status": "ERROR", "msg": "Invalid SC", "res": i}
    return requests.post(U_UNBIND, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=h).json()

@app.get("/api/info")
async def get_info(token: str, request: Request):
    h = gh(request)
    # Dono ko ek sath return karega
    try:
        b = requests.get(U_INFO, params={"app_id": AID, "access_token": token}, headers=h).json()
        r = requests.get(U_RANK, params={"access_token": token}, headers=h).json()
        return {"bind_info": b, "rank_info": r}
    except:
        return {"error": "Failed to fetch info"}

@app.get("/api/friends")
async def friends(token: str, mode: str, target: str = None, request: Request):
    url = F_MAP.get(mode)
    if not url: return {"error": "Invalid mode"}
    p = {"access_token": token}
    if target: p["target_account_id"] = target
    return requests.get(url, params=p, headers=gh(request)).json()

@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    # Fixed U_10 error here
    r = requests.get(U_LOGOUT, params={"access_token": token, "refresh_token": RTK}, headers=gh(request))
    return {"status": "revoked", "res": r.text}
