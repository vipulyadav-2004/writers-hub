# How to Setup Google Sign In

To make the "Sign in with Google" button work, you need to set up a project in Google Cloud Console and get your credentials.

## 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Search for "Google People API" or "Google Identity" and enable it. (Usually standard OAuth setup covers this).

## 2. Configure OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen**.
2. Select **External** (for testing) or Internal.
3. Fill in the required fields (App name, email).
4. Add scopes: `userinfo.email`, `userinfo.profile`, `openid`.
5. Add test users (your email) if using External/Testing mode.

## 3. Create Credentials
1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Application type: **Web application**.
4. Name: `Writer App` (or anything).
5. **Authorized redirect URIs**:
   - `http://127.0.0.1:5000/login/google/callback`
   - `http://localhost:5000/login/google/callback`
   (Make sure to add the one you use in your browser).

## 4. Add Credentials to Environment
1. Create a `.env` file in the root directory (c:\Users\HP\OneDrive\Desktop\writter_app\.env) if it doesn't exist.
2. Add the following lines:

```env
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
FLASK_SECRET_KEY=your-secret-key
OAUTHLIB_INSECURE_TRANSPORT=1
```

> Note: `OAUTHLIB_INSECURE_TRANSPORT=1` is needed for local testing with HTTP. Remove it in production (HTTPS).

## 5. Restart Application
After updating `.env`, restart your Flask server.

```bash
# In your terminal
Ctrl+C (to stop)
python app.py
```
