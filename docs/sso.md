# SSO（Generic OIDC）設計

對應 Claude.md 第 3 點：「加入 SSO 登入的機制，預設登入的使用者使用 member 角色」。

## 為什麼是「通用 OIDC」而不是接特定廠商

不綁定單一 IdP（不是寫死 Google 或某家公司的 Azure AD），只要對方支援 OpenID Connect
（Keycloak、Okta、Azure AD/Entra ID、GitLab、Google Workspace 都算），設定
`OIDC_ISSUER` + `OIDC_CLIENT_ID` + `OIDC_CLIENT_SECRET` 就能接上，不用改程式碼。

## 兩種登入方式並存

- **密碼登入**（`POST /api/v1/auth/login`）完全沒有因為加了 SSO 而受影響，對所有使用者永遠可用。
  這是刻意的設計決定：不新增「這個帳號只能用 SSO 登入」的旗標，任何帳號（不管是 admin 建的還是
  SSO 自動建立的）只要有設密碼就能用密碼登入。
- **SSO 登入**是額外的一條路，兩者最後都是呼叫同一個 `create_access_token()`
  （`backend/app/core/security.py`），所以下游（`get_current_user`、角色檢查……）完全不用區分
  使用者是怎麼登入的。

## 流程：Authorization Code + PKCE

```
1. GET /auth/sso/login
     -> 產生 PKCE code_verifier + nonce，包進簽章過的 state JWT，302 導去 IdP

2. 使用者在 IdP 登入、同意授權

3. IdP 導回 GET /auth/sso/callback?code=...&state=...
     -> 解開/驗證 state JWT（過期或被竄改就 400）
     -> 用 code + code_verifier 跟 IdP 換 token（含 PKCE）
     -> 驗證 id_token：簽章（用 IdP 的 JWKS）、iss、aud、exp、nonce
     -> 取 email/name，找不到 email_verified=false 就拒絕
     -> 依 email 找/建 User，狀態不是 active 就拒絕（跟密碼登入同一條規則）
     -> 發我們自己的 JWT
```

### 為什麼 `state` 是簽章 JWT，不是存 server-side session

OAuth2 的 `state` 參數本來就只是「原樣繞一圈回來給你」的不透明字串，用途是防 CSRF。這裡直接把
PKCE 的 `code_verifier` 跟 OIDC 的 `nonce` 編碼進一個短效期（5 分鐘）、有簽章的 JWT 裡當
`state` 送出去，callback 收到後解碼驗證——不需要 server-side session/cache，多個 worker/replica
也不會有「登入請求落在 A 台、callback 落在 B 台」的問題。這個 token 帶了獨立的 `purpose:
"sso_state"` claim（`backend/app/core/security.py` `create_sso_state_token`），確保一般的 access
token 不能被拿來冒充 `state`（反之亦然）。

### 自動建立帳號的規則

`backend/app/crud/user.py` 的 `get_or_create_by_sso`：

- email 找不到對應使用者 → 自動建立，角色固定 `member`、狀態 `active`、密碼是隨機字串（使用者
  沒辦法用密碼登入，除非 admin 之後手動幫他設一個——密碼登入本身不會被停用）
- email 找得到 → 直接讓他登入，**不會**改動既有的角色/狀態（SSO 只負責認證身份，不負責授權）

### 沒有前端時怎麼測試

`GET /auth/sso/callback` 在 `.env` 沒設 `FRONTEND_SSO_REDIRECT_URL` 時，會直接回傳跟
`POST /auth/login` 一樣格式的 `{"access_token": ..., "token_type": "bearer"}` JSON，方便現在
（還沒有前端）用瀏覽器或 curl 直接測。等前端做出來、設定了 `FRONTEND_SSO_REDIRECT_URL`，就會改成
302 導去該網址，token 放在 URL **fragment**（`#access_token=...`）——fragment 不會被送到 server
端（不會進 access log），也不會經過中間的 proxy/CDN。

## 設定

見 `.env.example`：

```
OIDC_ISSUER=              # 例如 https://gitlab.com、https://your-keycloak/realms/xxx
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
BACKEND_BASE_URL=http://localhost:8000   # 用來組 redirect_uri
FRONTEND_SSO_REDIRECT_URL=               # 留空 = callback 直接回 JSON
```

IdP 那邊要註冊 `{BACKEND_BASE_URL}/api/v1/auth/sso/callback` 為允許的 redirect URI，兩邊必須
**完全一致**（協定/host/port/path），這是 OIDC 規範要求，不一致 IdP 會直接拒絕，不會進到我們的
callback。

## 測試涵蓋範圍

真的走一次 IdP 登入需要人互動（輸入帳密、按同意），沒辦法在 CI 裡穩定重現，所以
`backend/tests/test_sso.py` 分兩層：

- 純邏輯的單元測試（不碰網路）：`state` token 的簽章往返、過期、被竄改、以及「一般 access token
  不能拿來當 state」；`get_or_create_by_sso` 的自動建立角色/既有帳號不被覆蓋。
- Endpoint 測試：把 `app.services.sso.exchange_code`（真正打 IdP 的那一段）mock 掉，驗證
  callback 收到 code/state 之後的邏輯——新帳號自動建立、既有帳號角色不變、停用帳號被拒絕、
  壞掉/過期的 state 被拒絕。

實作過程中有拿使用者提供的 GitLab OAuth app 憑證實際打過 `/auth/sso/login`，確認
`redirect_uri`/`client_id`/PKCE 參數都被 GitLab 接受（正常導到 GitLab 的登入頁，沒有
`invalid_redirect_uri` 之類的錯誤）；完整登入+換 token 的部分因為需要人工在瀏覽器輸入帳密，
留給有前端、或需要時再手動走一次驗證。
