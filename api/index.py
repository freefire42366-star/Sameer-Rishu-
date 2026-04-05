from fastapi import FastAPI, Request, Query
import requests
import hashlib

app = FastAPI()

# --- Config ---
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
U_LOGOUT   = "https://100067.connect.garena.com/oauth/logout"
U_RANK     = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
U_TOPUP    = "https://100067.msdk.garena.com/api/msdk/v2/info/pricing"

# Friend System URLs
F_MAP = {
    "list": "https://clientbp.ggwhitehawk.com/GetFriendRequestList",
    "add": "https://clientbp.ggwhitehawk.com/RequestAddingFriend",
    "remove": "https://clientbp.ggwhitehawk.com/RemoveFriend",
    "accept": "https://clientbp.ggwhitehawk.com/ConfirmFriendRequest",
    "decline": "https://clientbp.ggwhitehawk.com/DeclineFriendRequest"
}

def get_headers(r: Request):
    ua = r.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded"}

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
async def status():
    return {"status": "SUCCESS", "message": "Garena API is running on Vercel"}

@app.get("/api/request")
def req_otp(token: str, email: str, request: Request):
    p = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    return requests.post(U_OTP, data=p, headers=get_headers(request)).json()

@app.get("/api/confirm-new")
def bind_new(token: str, email: str, otp: str, sc: str = "123456", request: Request):
    h = get_headers(request)
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v.get("verifier_token")
    if not vt: return {"status": "ERROR", "details": v}
    
    p = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": sha256_hash(sc)}
    return requests.post(U_BIND, data=p, headers=h).json()

@app.get("/api/rebind")
def bind_change(token: str, email: str, otp: str, sc: str, request: Request):
    h = get_headers(request)
    # Step 1: Verify OTP
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    # Step 2: Verify ID
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": sha256_hash(sc)}, headers=h).json()
    
    vt, it = v.get("verifier_token"), i.get("identity_token")
    if not vt or not it: return {"status": "FAIL", "otp_res": v, "id_res": i}
    
    p = {"app_id": AID, "access_token": token, "identity_token": it, "verifier_token": vt, "email": email}
    return requests.post(U_REBIND, data=p, headers=h).json()

@app.get("/api/unbind")
def unbind(token: str, sc: str, request: Request):
    h = get_headers(request)
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": sha256_hash(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not it: return {"status": "ERROR", "msg": "Invalid Secondary Password", "res": i}
    
    return requests.post(U_UNBIND, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=h).json()

@app.get("/api/friends")
def friends_manager(token: str, mode: str, target: str = None, request: Request):
    url = F_MAP.get(mode)
    if not url: return {"error": "Invalid mode"}
    p = {"access_token": token}
    if target: p["target_account_id"] = target
    return requests.get(url, params=p, headers=get_headers(request)).json()

@app.get("/api/info")
def get_user_info(token: str, request: Request):
    # Combined both into one clean response
    h = get_headers(request)
    try:
        bind_data = requests.get(U_INFO, params={"app_id": AID, "access_token": token}, headers=h).json()
        rank_data = requests.get(U_RANK, params={"access_token": token}, headers=h).json()
        return {"status": "SUCCESS", "account_bind": bind_data, "player_rank": rank_data}
    except Exception as e:
        return {"status": "ERROR", "msg": str(e)}

@app.get("/api/utils")
def utils(token: str, action: str, request: Request):
    h = get_headers(request)
    if action == "plat": return requests.get(U_PLAT, params={"access_token": token}, headers=h).json()
    if action == "topup": return requests.get(U_TOPUP, params={"access_token": token}, headers=h).json()
    if action == "cancel": return requests.post(U_CANCEL, data={"app_id": AID, "access_token": token}, headers=h).json()
    return {"err": "Invalid action"}

@app.get("/api/revoke")
def revoke_token(token: str, request: Request):
    # Fixed U_10 error: replaced with U_LOGOUT
    r = requests.get(U_LOGOUT, params={"access_token": token, "refresh_token": RTK}, headers=get_headers(request))
    return {"status": "DONE", "response": r.text}
