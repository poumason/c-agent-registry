# SSO 登入（OIDC）

前置條件（全檔共用）：
- 後端 `.env` 已設定 `OIDC_ISSUER` / `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET`。
- 該 OIDC 應用程式的 Redirect/Callback URI 已註冊為
  `http://localhost:8000/api/v1/auth/sso/callback`（**不是**前端網址，IdP 導回的第一站是後端，
  後端換完 token 後才會再把使用者導去 `FRONTEND_SSO_REDIRECT_URL`，預設
  `http://localhost:5173/sso/callback`）。
- 有一組可用於該 OIDC 提供者的測試帳號。
- 可存取部署 pgAdmin（`http://localhost:5050`）或其他方式查詢 `users` 資料表，用來核對
  TC-1.7～1.9。

若目前環境沒有配置 SSO，本檔案全部案例可略過，不影響帳號密碼登入（見
[password-login.md](password-login.md)）持續可用。

## TC-1.7 從登入頁發起 SSO 登入

步驟：
1. 開啟 `/login`。
2. 點擊「使用 SSO 登入」按鈕。

預期結果：
- 瀏覽器被導向 OIDC 提供者的授權頁面（例如 GitLab 的登入/授權頁），網址帶有正確的
  `client_id`、`redirect_uri=http://localhost:8000/api/v1/auth/sso/callback`。

- [ ] Pass / Fail
備註：

## TC-1.8 完成授權後自動建立使用者並登入

前置條件：使用一個**第一次**用於這個系統的 OIDC 帳號（`users` 表中尚無對應 email）。

步驟：
1. 承 TC-1.7，在 IdP 頁面完成登入與授權同意。
2. 觀察瀏覽器最終落地的頁面。
3. 查詢 `users` 資料表，找出以該 OIDC 帳號 email 建立的資料列。

預期結果：
- 瀏覽器最終回到前端首頁（`/`），已是登入狀態，右上角顯示對應的使用者名稱。
- `users` 表新增一筆資料，且：
  - `email` 與 `name` 對應 OIDC 帳號的 email/name。
  - `role` = `member`（SSO 自動建立的帳號固定是 member，不會是 reviewer/admin）。
  - `status` = `active`。
  - `password`/`hashed_password` 是系統隨機產生的值（不是使用者在任何地方輸入過的密碼，
    無法拿來做密碼登入去猜）。

- [ ] Pass / Fail
備註：

## TC-1.9 同一個外部帳號第二次登入不會重複建立使用者

前置條件：已完成 TC-1.8。

步驟：
1. 登出。
2. 重複 TC-1.7～1.8 的步驟，用同一個 OIDC 帳號再次登入。
3. 再次查詢 `users` 資料表。

預期結果：
- 登入成功，回到首頁。
- `users` 表**沒有**新增第二筆資料，仍是原本那一筆（用 email 找到既有帳號並沿用，角色/狀態
  不會被重置）。

- [ ] Pass / Fail
備註：

## TC-1.10 SSO 建立的帳號權限與一般 member 一致

前置條件：已用 TC-1.8 建立的帳號登入。

步驟：
1. 觀察左側 sidebar 選單。
2. 嘗試訪問 `/review-queue` 與 `/admin/users`。

預期結果：
- 看不到 Admin 相關選單項目；`/admin/users` 無法進入（同一般 member 的權限邊界）。
- 若沒有被指派任何審核，`/review-queue` 顯示無權限或空清單（依目前角色為 member，非
  reviewer/admin）。
- 可以正常使用 Browse、My Agents 等一般功能（同 [02-agent-management](../02-agent-management/)）。

- [ ] Pass / Fail
備註：

## TC-1.11 SSO 帳號出現在 Admin 使用者管理，且可比照一般帳號調整

前置條件：admin 帳號登入；TC-1.8 已建立至少一個 SSO 帳號。

步驟：
1. 用 admin 帳號進入 **Admin > Users**。
2. 找到 TC-1.8 建立的帳號。

預期結果：
- 該帳號正常出現在使用者清單，欄位（Email、角色、狀態、建立時間）與一般透過 Admin 建立的
  帳號沒有差異。
- 可以比照 [04-admin/manage-reviewers-and-users.md](../04-admin/manage-reviewers-and-users.md)
  的步驟調整角色或停用。

- [ ] Pass / Fail
備註：

## TC-1.12 無效/過期的 state 參數

步驟：
1. 手動組一個網址呼叫 `http://localhost:8000/api/v1/auth/sso/callback?code=invalid&state=invalid`
   並在瀏覽器開啟。

預期結果：
- 回傳錯誤（400），不會核發 token，也不會建立/登入任何使用者。

- [ ] Pass / Fail
備註：
