# 帳號密碼登入

前置條件（全檔共用）：後端、前端皆已啟動，瀏覽器開啟 `http://localhost:5173`。

## TC-1.1 使用正確帳密登入成功

前置條件：已知一組有效帳密（例如 bootstrap admin：`admin@example.com` / `change-me-admin`）。

步驟：
1. 開啟 `/login`，輸入正確 Email 與密碼。
2. 點擊登入按鈕。

預期結果：
- 成功導向首頁（Browse，`/`）。
- 右上角顯示登入使用者的名稱/角色。
- 重新整理頁面（F5）後仍維持登入狀態，不會被導回 `/login`。

- [ ] Pass / Fail
備註：

## TC-1.2 Email 不存在

步驟：
1. 開啟 `/login`，輸入一個系統中不存在的 Email，密碼任意輸入。
2. 點擊登入按鈕。

預期結果：
- 停留在登入頁，顯示帳號或密碼錯誤的提示訊息。
- 不會導向首頁，也不會在瀏覽器留下有效的登入憑證。

- [ ] Pass / Fail
備註：

## TC-1.3 密碼錯誤

前置條件：使用一組存在的 Email（例如 admin 帳號）。

步驟：
1. 開啟 `/login`，輸入正確 Email、錯誤密碼。
2. 點擊登入按鈕。

預期結果：
- 停留在登入頁，顯示帳號或密碼錯誤的提示訊息（訊息內容應與 TC-1.2 一致，不可透露「密碼錯誤」
  而洩漏該 Email 確實存在）。

- [ ] Pass / Fail
備註：

## TC-1.4 使用已停用（disabled）帳號登入

前置條件：先用 admin 帳號在 **Admin > Users** 建立一個測試帳號並設定密碼，再把該帳號狀態
改成 `disabled`（做法見 [04-admin/manage-reviewers-and-users.md](../04-admin/manage-reviewers-and-users.md) 的 TC-4.5）。

步驟：
1. 用該已停用帳號的 Email/密碼在 `/login` 登入。

預期結果：
- 登入被拒絕，顯示帳號已停用或無法登入的錯誤訊息。
- 不會取得有效 token、不會進入系統首頁。

- [ ] Pass / Fail
備註：

## TC-1.5 未登入直接訪問受保護頁面

步驟：
1. 若目前已登入，先登出（或用無痕視窗）。
2. 直接在網址列輸入 `http://localhost:5173/my-agents`。

預期結果：
- 被導回 `/login`，無法看到 My Agents 頁面內容。

- [ ] Pass / Fail
備註：

## TC-1.6 登出

前置條件：已登入任一帳號。

步驟：
1. 透過右上角使用者選單執行登出。

預期結果：
- 導回 `/login`。
- 再次訪問任何受保護頁面（如 `/my-agents`）會被導回登入頁（同 TC-1.5）。

- [ ] Pass / Fail
備註：
