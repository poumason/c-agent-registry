# Admin 設定 Reviewer 與使用者管理

前置條件（全檔共用）：以 admin 帳號（bootstrap 帳號或任何系統角色為 `admin` 的使用者）登入。

## TC-4.1 建立新使用者

步驟：
1. 進入 **Admin > Users**，點擊「新增使用者」。
2. 填寫姓名、Email、初始密碼（至少 8 碼）、角色選 `member`。
3. 送出。

預期結果：
- 使用者清單新增一筆，角色 `member`、狀態 `active`。
- 用該帳號的 Email/初始密碼可以在 `/login` 成功登入
  （見 [01-authentication/password-login.md](../01-authentication/password-login.md) 的
  TC-1.1）。

- [ ] Pass / Fail
備註：

## TC-4.2 把 member 調整成 reviewer

前置條件：Carol 目前角色是 `member`（透過 TC-4.1 建立，或系統中既有帳號）。

步驟：
1. 在使用者清單找到 Carol，點擊「編輯」。
2. 角色下拉選單改選 `reviewer`。
3. 儲存。

預期結果：
- 清單即時顯示 Carol 的角色變成 `reviewer`。
- Carol 登入後，在送審流程的 Reviewer 候選清單中會出現（見
  [03-review-workflow/submit-for-review.md](../03-review-workflow/submit-for-review.md) 的
  TC-3.1）。
- Carol 現在可以進入 `/review-queue`（見
  [03-review-workflow/reviewer-decision.md](../03-review-workflow/reviewer-decision.md) 的
  TC-3.7）。

- [ ] Pass / Fail
備註：

## TC-4.3 把 reviewer 調回 member

前置條件：承 TC-4.2，Carol 目前是 `reviewer`。

步驟：
1. 同上，把 Carol 的角色改回 `member`。

預期結果：
- 角色更新成功。
- 之後新的送審流程，Carol 不再出現在 Reviewer 候選清單中；Carol 也無法再進入
  `/review-queue`。
- 註：Carol 先前已存在、狀態仍是 pending 的審核紀錄（若有）不受角色變更自動撤銷影響，
  這屬於既有資料的邊界情況，非本案例的驗證重點，測試時如觀察到相關行為請記錄在備註供
  後續確認。

- [ ] Pass / Fail
備註：

## TC-4.4 把使用者提升為 admin

步驟：
1. 選一個 member 或 reviewer 帳號，角色改成 `admin`。

預期結果：
- 更新成功，該帳號登入後可看到 Admin 選單，並具備管理任何 agent、建立/調整使用者的權限。

- [ ] Pass / Fail
備註：

## TC-4.5 停用（軟刪除）一個使用者

前置條件：有一個非目前登入帳號的測試使用者。

步驟：
1. 在使用者清單找到該帳號，點擊「刪除」，確認彈窗。

預期結果：
- 出現二次確認提示，確認後該帳號狀態變成 `disabled`（或從主要清單消失，依前端呈現方式為
  準，後端為軟刪除）。
- 該帳號無法再登入（見
  [01-authentication/password-login.md](../01-authentication/password-login.md) 的
  TC-1.4）。
- 若該帳號原本是 reviewer，停用後不應再出現在新的 Reviewer 候選清單中。

- [ ] Pass / Fail
備註：

## TC-4.6 Admin 不能停用/刪除自己

步驟：
1. 在使用者清單找到目前登入中的 admin 帳號自己那一列。

預期結果：
- 「編輯」「刪除」操作按鈕為 disabled 狀態，或勾選框不可選取（防止自己被鎖在系統外）。
- 若透過 API 直接嘗試刪除自己，應回傳衝突錯誤（409），操作被拒絕。

- [ ] Pass / Fail
備註：

## TC-4.7 批次刪除使用者

前置條件：至少建立 2 個測試用的一般帳號（非自己）。

步驟：
1. 在使用者清單勾選 2 個以上帳號的核取方塊。
2. 點擊「刪除選取」，確認彈窗。

預期結果：
- 出現確認提示，內容顯示選取的數量。
- 確認後所有選取帳號被停用，操作結果訊息顯示成功/失敗筆數。

- [ ] Pass / Fail
備註：

## TC-4.8 非 admin 無法存取使用者管理

前置條件：以 Alice（member）或 Carol（reviewer）登入。

步驟：
1. 嘗試訪問 `/admin/users`。

預期結果：
- 無法進入（導向無權限頁或首頁），左側選單也不會出現 Admin 相關項目。

- [ ] Pass / Fail
備註：

## TC-4.9 使用者清單搜尋與篩選

步驟：
1. 在 Admin > Users 頁面，用姓名或 Email 關鍵字搜尋。
2. 用角色篩選（例如只看 `reviewer`）。
3. 用狀態篩選（`active`/`disabled`）。

預期結果：
- 每種篩選條件都能正確縮小清單範圍，清單筆數/分頁跟著更新。

- [ ] Pass / Fail
備註：
