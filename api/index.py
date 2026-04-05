from fastapi import FastAPI, Request
import requests
import hashlib

# FastAPI instance (Vercel isse hi dhund raha hai)
app = FastAPI()

AID = "100067"
RTK = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

# URLs
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
async def root():
    return {"status": "running", "msg": "API working in api/ folder"}

@app.get("/api/request")
async def req_otp(token: str, email: str, request: Request):
    p = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    return requests.post(U_OTP, data=p, headers=gh(request)).json()

@app.get("/api/confirm-new")
async def bind_new(token: str, email: str, otp: str, sc: str = "123456", request: Request):
    h = gh(request)
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v.get("verifier_token")
    if not vt: return {"status": "ERROR", "res": v}
    p = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": hs(sc)}
    return requests.post(U_BIND, data=p, headers=h).json()

@app.get("/api/info")
async def get_all_info(token: str, request: Request):
    # 2 functions ko 1 me merge kiya
    h = gh(request)
    try:
        bind = requests.get(U_INFO, params={"app_id": AID, "access_token": token}, headers=h).json()
        rank = requests.get(U_RANK, params={"access_token": token}, headers=h).json()
        return {"bind": bind, "rank": rank}
    except:
        return {"error": "Fetch failed"}

@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    h = gh(request)
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    it = i.get("identity_token")
    if not it: return i
    return requests.post(U_UNB, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=h).json()

@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    r = requests.get(U_LOG, params={"access_token": token, "refresh_token": RTK}, headers=gh(request))
    return {"res": r.text}
