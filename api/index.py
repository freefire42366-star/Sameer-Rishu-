from fastapi import FastAPI, Request
import requests
import hashlib

# Top-level entry point (Isse mat badalna)
app = FastAPI()

# --- Configuration ---
AID = "100067"
RTK = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
SEC_CODE = "123456"

# --- URLs ---
U_OTP   = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
U_V_OTP = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
U_BIND  = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
U_V_ID  = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
U_REB   = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
U_UNB   = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
U_INFO  = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
U_RANK  = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
U_LOG   = "https://100067.connect.garena.com/oauth/logout"

def gh(r: Request):
    ua = r.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded"}

def hs(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
async def home():
    return {"status": "SUCCESS", "msg": "Sameer Bind Engine Active"}

# 1. SEND OTP
@app.get("/api/request")
async def req_otp(token: str, email: str, request: Request):
    p = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    return requests.post(U_OTP, data=p, headers=gh(request)).json()

# 2. CONFIRM BIND (Fresh Logic)
@app.get("/api/confirm")
async def confirm(token: str, email: str, otp: str, request: Request):
    h = gh(request)
    v_res = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v_res.get("verifier_token")
    if not vt: return {"status": "ERROR", "res": v_res}
    
    p = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": hs(SEC_CODE)}
    final = requests.post(U_BIND, data=p, headers=h).json()
    return {"status": "Process Finished", "garena_raw": final}

# 3. INFO + RANK (Merged into 1 Function)
@app.get("/api/info")
async def get_info(token: str, request: Request):
    h = gh(request)
    try:
        bind = requests.get(U_INFO, params={"app_id": AID, "access_token": token}, headers=h).json()
        rank = requests.get(U_RANK, params={"access_token": token}, headers=h).json()
        return {"account_status": bind, "player_rank": rank}
    except:
        return {"error": "Failed to fetch data"}

# 4. UNBIND
@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    h = gh(request)
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not it: return {"error": "Invalid SC", "res": i}
    return requests.post(U_UNB, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=h).json()

# 5. REVOKE
@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    r = requests.get(U_LOG, params={"access_token": token, "refresh_token": RTK}, headers=gh(request))
    return {"res": r.text}
