import httpx
from fastapi import HTTPException
from app.core.config import settings


#Google

def get_google_auth_url() -> str:
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_url": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email form",
        "access_type": "offline"
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

async def get_google_user(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": "code",
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_url": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
        token_data = token_res.json()

        if "error" in token_data:
            raise HTTPException(status_code=400, detail=f"Google OAuth error: {token_data['error']}")

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        return user_res.json()
 
   
# Github

def get_github_auth_url() -> str:
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://github.com/login/oauth/authorize?{query}"
 
 
async def get_github_user(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
        )
        token_data = token_res.json()
 
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {token_data['error']}")
 
        access_token = token_data["access_token"]
 
        # Fetch user profile
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_res.json()
 
        # GitHub may not expose email publicly — fetch it separately
        if not user_data.get("email"):
            emails_res = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            emails = emails_res.json()
            primary = next((e["email"] for e in emails if e.get("primary") and e.get("verified")), None)
            user_data["email"] = primary
 
        return user_data